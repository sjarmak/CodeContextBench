# Envoy Request Routing Flow

This document traces the complete path of an HTTP request from TCP accept through upstream connection establishment.

## Q1: Listener Accept to Network Filter Chain

### TCP Connection Accept

When a downstream client TCP connection arrives at Envoy:

1. **Socket Accept**: The TCP listener accepts the socket in the event loop
   - `source/common/network/tcp_listener_impl.cc:TcpListenerImpl::onAccept()` - libevent-based socket accept
   - Socket is wrapped and passed to `ActiveTcpListener::onAccept()`

2. **ActiveTcpListener Processing** (`source/common/listener_manager/active_tcp_listener.cc`)
   - `ActiveTcpListener::onAccept(Network::ConnectionSocketPtr&& socket)` (line 80)
   - Checks connection limits via `listenerConnectionLimitReached()`
   - Calls `onAcceptWorker()` which handles connection balancing across worker threads
   - Creates `ActiveTcpSocket` (line 126)

3. **Listener Filter Chain** (`source/common/listener_manager/active_tcp_socket.cc`)
   - `ActiveTcpSocket` constructor (line 11) initializes the accepted socket
   - Listener filters are processed in `continueFilterChain()` (line 111)
   - Each listener filter's `onAccept()` is called; filters can pause and request more data
   - `createListenerFilterBuffer()` (line 73) manages buffered data for listener filters

4. **Network Filter Chain Selection** (`source/common/listener_manager/active_stream_listener_base.cc`)
   - After listener filters complete, socket transitions to `ActiveTcpConnection`
   - Filter chain is selected based on the `FilterChain::matchTransportSocket()` matching
   - The matching criteria (e.g., TLS SNI, source IP) determine which filter chain to use
   - Network filter factory creates the HTTP Connection Manager (HCM)

5. **Hand-off to Network Filter Manager**
   - `OwnedActiveStreamListenerBase::onSocketAccepted()` processes the filter chain
   - For HTTP, the HTTP Connection Manager is instantiated as a Network::Filter
   - The established TCP connection calls the HCM's `onNewConnection()` method
   - HCM initializes and prepares to receive data

### Data Arrival and HCM Invocation

6. **onData() Triggering**
   - Socket receives bytes → dispatcher triggers `onData()` callback
   - `ConnectionManagerImpl::onData(Buffer::Instance& data, bool)` (source/common/http/conn_manager_impl.cc:486)
   - HCM creates codec lazily on first `onData()` call (line 488-496)

## Q2: HTTP Parsing and Filter Chain Iteration

### Codec Creation and Header Parsing

1. **Codec Instantiation** (`source/common/http/conn_manager_impl.cc`)
   - `ConnectionManagerImpl::createCodec(Buffer::Instance& data)` creates HTTP codec
   - Codec type (HTTP/1.1, HTTP/2, HTTP/3) determined from data
   - Supports load shedding via `hcm_ondata_creating_codec_` overload point

2. **Codec Dispatch** (line 503)
   - `codec_->dispatch(data)` parses incoming bytes
   - Codec invokes `ServerConnectionCallbacks::newStream()` when headers are complete
   - Returns HTTP status; errors trigger immediate connection closure

### ActiveStream Creation

3. **Stream Instantiation** (`source/common/http/conn_manager_impl.cc:387`)
   - `ConnectionManagerImpl::newStream(ResponseEncoder& response_encoder, bool is_internally_created)`
   - Creates new `ActiveStream` - wraps a single HTTP request/response pair
   - Initializes stream with `buffer_limit` and accounting information
   - Returns `RequestDecoder` interface for codec to deliver parsed data

4. **Stream Structure** (`source/common/http/conn_manager_impl.h:141`)
   - `ActiveStream` is `LinkedObject<ActiveStream>` - maintains list of concurrent streams
   - Implements `RequestDecoder` interface to receive parsed headers/data/trailers
   - Contains embedded `FilterManager` for managing downstream filters

### HTTP Filter Chain Processing

5. **Filter Chain Initialization** (`source/common/http/filter_manager.cc`)
   - `FilterManager::decodeHeaders()` is called by codec via `RequestDecoder::decodeHeaders()`
   - Decoder filters are created from route configuration
   - Filter chain factories instantiate actual filters and insert into filter chain

6. **Decoder Filter Iteration** (`source/common/http/filter_manager.h:237-246`)
   - `ActiveStreamDecoderFilter` wrapper for each decoder filter
   - `FilterManager::decodeHeaders(ActiveStreamDecoderFilter* filter, ...)` iterates through filters
   - Each filter's `decodeHeaders()` returns:
     - `Continue` - proceed to next filter
     - `StopIteration` - buffer data, wait for resumption
     - `StopAllIteration` - stop all downstream processing

7. **Filter State Management** (`source/common/http/filter_manager.h:108-113`)
   - `ActiveStreamFilterBase` tracks `iteration_state_` (Continue/StopIteration)
   - `parent_` reference allows filters to access stream info, send local replies, etc.
   - Filters can be chained with custom processing at each stage

## Q3: Route Resolution and Upstream Selection

### Route Matching and Cluster Resolution

1. **Router Filter Invocation** (`source/common/router/router.cc:445`)
   - `Router::Filter::decodeHeaders(Http::RequestHeaderMap& headers, bool end_stream)`
   - Router filter is typically the last decoder filter in the chain
   - Called when all prior filters have completed header processing

2. **Route Lookup** (line 468)
   - `callbacks_->route()` queries the route configuration manager
   - Route matching uses request headers (path, method, domain, etc.)
   - Returns `Route` object containing route entry and directives
   - If no route found, sends 404 immediately

3. **Route Entry and Cluster Resolution** (line 506-530)
   - `route_->routeEntry()` extracts the actual routing rule
   - `route_entry_->clusterName()` specifies the upstream cluster
   - `config_->cm_.getThreadLocalCluster(route_entry_->clusterName())` retrieves cluster info
   - Validates cluster exists; if not, sends 404

### Host Selection

4. **Load Balancing and Host Choice** (line 664)
   - `cluster->chooseHost(this)` - router filter implements `LoadBalancerContext` interface
   - Load balancer selects upstream host based on:
     - Load balancing algorithm (Round Robin, Least Request, Ring Hash, etc.)
     - Health status
     - Metadata matching criteria (from route config)
   - Returns `HostSelectionResponse` containing selected host and cancellation handle

5. **Async Host Selection Support** (line 665-703)
   - If async host selection is enabled and supported, returns `Cancelable` handle
   - Router registers callback `on_host_selected_` for async completion
   - On completion, `continueDecodeHeaders()` is called

### Connection Pool Creation

6. **Connection Pool Acquisition** (`source/common/router/router.cc:714-728`)
   - `createConnPool(*cluster, selected_host)` in `continueDecodeHeaders()`
   - Requests connection pool from cluster manager for specific upstream host
   - Connection pool implements `GenericConnPool` interface
   - Pool is responsible for TCP/HTTP connection lifecycle
   - Returns `nullptr` if pool creation fails (e.g., invalid config)

## Q4: Upstream Connection and Data Flow

### Upstream Request Creation

1. **UpstreamRequest Instantiation** (`source/common/router/router.cc:845-848`)
   - `std::make_unique<UpstreamRequest>(*this, std::move(generic_conn_pool), can_send_early_data, can_use_http3, enable_half_close_)`
   - Router creates upstream request with the connection pool
   - `UpstreamRequest` constructor (`source/common/router/upstream_request.cc:80-155`):
     - Stores parent router filter reference
     - Initializes stream info for upstream
     - Sets up tracing spans
     - Creates `UpstreamFilterManager` for upstream HTTP filters

2. **Upstream Request Linking** (line 848)
   - `LinkedList::moveIntoList(std::move(upstream_request), upstream_requests_)`
   - Router maintains linked list of active upstream requests (for retries, hedging)

### Connection Pool Interaction

3. **Requesting Upstream Connection** (`source/common/router/upstream_request.cc:380-434`)
   - `UpstreamRequest::acceptHeadersFromRouter(bool end_stream)`
   - Called by router after setup (line 849 in router.cc)
   - `conn_pool_->newStream(this)` (line 404) - requests stream from connection pool
   - UpstreamRequest implements `GenericConnectionPoolCallbacks` interface
   - Pool either:
     - Returns existing connection via `onPoolReady()` callback (immediate)
     - Asynchronously creates new connection and calls `onPoolReady()` when ready

4. **Connection Establishment** (`source/common/router/upstream_request.cc:onPoolReady`)
   - Pool callback: `void onPoolReady(std::unique_ptr<GenericUpstream>&& upstream, ...)`
   - `GenericUpstream` wraps the upstream HTTP connection/codec
   - Called when TCP connection exists and HTTP negotiation (TLS, ALPN) complete
   - UpstreamRequest stores upstream reference for later use

### Request Encoding to Upstream

5. **Upstream Filter Chain** (line 433)
   - `filter_manager_->decodeHeaders(*parent_.downstreamHeaders(), end_stream)`
   - Passes downstream headers through upstream filter chain
   - Last filter: `UpstreamCodecFilter` - encodes to upstream codec
   - `UpstreamCodecFilter::decodeHeaders()` calls:
     - `upstream_->newStream(response_decoder)` - creates upstream stream
     - `request_encoder->encodeHeaders()` - writes HTTP headers to socket

6. **Data Forwarding**
   - `UpstreamRequest::acceptDataFromRouter()` (line 436)
   - Router passes request body through upstream filter chain
   - Eventually reaches `UpstreamCodecFilter::decodeData()`
   - `request_encoder->encodeData()` - writes body to socket

### Response Reception

7. **Upstream Response Path** (`source/common/router/upstream_codec_filter.h`)
   - Upstream codec receives response via `CodecBridge` (line 54-66)
   - `CodecBridge` implements `UpstreamToDownstream` interface
   - Callbacks triggered:
     - `onCodecDecodeHeaders()` → `UpstreamCodecFilter::decodeHeaders()`
     - `onCodecDecodeData()` → `UpstreamCodecFilter::decodeData()`

8. **Response Through Upstream Filter Chain** (`source/common/router/upstream_request.cc:256-307`)
   - Response headers flow through upstream filter chain
   - `UpstreamRequest::decodeHeaders()` (line 267) receives filtered response headers
   - Calls `parent_.onUpstreamHeaders()` to pass to router filter

9. **Router to Downstream Encoder Chain** (`source/common/router/router.cc`)
   - Router filter's `onUpstreamHeaders()` receives response
   - Router filter invokes `encodeHeaders()` on encoder callbacks
   - Downstream encoder filter chain processes response headers
   - Last filter: HTTP Connection Manager writes response to downstream socket

10. **Encoder Filter Chain Execution** (`source/common/http/filter_manager.h`)
    - `ActiveStreamEncoderFilter` wrappers for each encoder filter
    - Filter iteration mirrors decoder pattern (Continue/StopIteration)
    - Response headers and body traverse chain from upstream to downstream
    - HCM codec writes final HTTP response to downstream connection

### Flow Control and Backpressure

11. **Watermark Management**
    - Upstream high/low watermark events trigger downstream pause/resume
    - Router implements `DownstreamWatermarkCallbacks`
    - Prevents memory exhaustion during slow upstream/fast downstream scenarios

## Evidence

### Critical File Paths and Methods

**Listener Accept Path:**
- `source/common/listener_manager/active_tcp_listener.cc:80` - `ActiveTcpListener::onAccept()`
- `source/common/listener_manager/active_tcp_socket.cc:111` - `ActiveTcpSocket::continueFilterChain()`
- `source/common/listener_manager/active_stream_listener_base.cc` - Filter chain matching

**HTTP Parsing and Codec:**
- `source/common/http/conn_manager_impl.cc:486` - `ConnectionManagerImpl::onData()`
- `source/common/http/conn_manager_impl.cc:387` - `ConnectionManagerImpl::newStream()`
- `source/common/http/conn_manager_impl.h:141` - `ActiveStream` definition

**Filter Chain Management:**
- `source/common/http/filter_manager.h:237-246` - `ActiveStreamDecoderFilter`
- `source/common/http/filter_manager.cc:638` - `FilterManager::decodeData()`

**Router Filter and Route Resolution:**
- `source/common/router/router.cc:445` - `Router::Filter::decodeHeaders()`
- `source/common/router/router.cc:468` - Route lookup via `callbacks_->route()`
- `source/common/router/router.cc:664` - Host selection via `cluster->chooseHost()`
- `source/common/router/router.cc:714` - Connection pool creation in `continueDecodeHeaders()`

**Upstream Request and Connection Pool:**
- `source/common/router/router.cc:845-849` - UpstreamRequest creation and initialization
- `source/common/router/upstream_request.cc:80-155` - `UpstreamRequest` constructor
- `source/common/router/upstream_request.cc:380-434` - `UpstreamRequest::acceptHeadersFromRouter()`
- `source/common/router/upstream_request.cc:404` - `conn_pool_->newStream(this)`

**Upstream Response Path:**
- `source/common/router/upstream_codec_filter.h:54-66` - `CodecBridge` interface
- `source/common/router/upstream_request.cc:267` - `UpstreamRequest::decodeHeaders()` receives response
- `source/common/router/upstream_request.cc:306` - `parent_.onUpstreamHeaders()` calls router

**Downstream Response Encoding:**
- `source/common/http/filter_manager.h` - Encoder filter chain management
- `source/common/http/conn_manager_impl.cc` - HCM writes to downstream codec
