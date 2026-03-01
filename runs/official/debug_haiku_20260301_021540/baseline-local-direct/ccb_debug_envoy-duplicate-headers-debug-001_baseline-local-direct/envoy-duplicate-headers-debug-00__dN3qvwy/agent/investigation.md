# Investigation Report: Duplicate Response Headers in Envoy Filter Pipeline

## Summary

Response headers configured via `response_headers_to_add` in route configuration are duplicated when the router filter generates local replies (upstream timeout, connection failure, etc.) because `sendLocalReplyViaFilterChain()` and `sendDirectLocalReply()` invoke `route_entry_->finalizeResponseHeaders()` twice: once directly in the encoder lambda, and again through the `modify_headers_` callback that already contains a call to `finalizeResponseHeaders()`.

## Root Cause

**Location**: Dual invocation of `finalizeResponseHeaders()` in the local reply response path

**Mechanism**:
1. **First invocation** (direct): `source/common/http/filter_manager.cc` lines 1125, 1158
   - `sendLocalReplyViaFilterChain()` and `sendDirectLocalReply()` create a lambda encoder function that directly calls `streamInfo().route()->routeEntry()->finalizeResponseHeaders(headers, streamInfo())`

2. **Second invocation** (indirect): `source/common/router/router.cc` line 453
   - The same `modify_headers_` callback passed to `sendLocalReply()` contains another invocation of `route_entry_->finalizeResponseHeaders(headers, callbacks_->streamInfo())`

Result: Route-configured response headers are added twice for local replies.

## Evidence

### Code Reference 1: Local Reply Path (Double Invocation)
**File**: `source/common/http/filter_manager.cc`

**Location**: `DownstreamFilterManager::sendLocalReplyViaFilterChain()` lines 1120-1144

```cpp
Utility::sendLocalReply(
    state_.destroyed_,
    Utility::EncodeFunctions{
        [this, modify_headers](ResponseHeaderMap& headers) -> void {
          if (streamInfo().route() && streamInfo().route()->routeEntry()) {
            streamInfo().route()->routeEntry()->finalizeResponseHeaders(headers, streamInfo());  // FIRST CALL
          }
          if (modify_headers) {
            modify_headers(headers);  // SECOND CALL (contains another finalizeResponseHeaders)
          }
        },
        // ... other encoder functions
    },
    Utility::LocalReplyData{...});
```

**Duplicate location**: `DownstreamFilterManager::sendDirectLocalReply()` lines 1156-1162 has the identical pattern.

**Prepared reply path**: `DownstreamFilterManager::prepareLocalReplyViaFilterChain()` lines 1072-1078 has the same issue.

### Code Reference 2: Router Filter's modify_headers_ Callback
**File**: `source/common/router/router.cc`

**Location**: `Filter::decodeHeaders()` lines 444-461

```cpp
modify_headers_ = [this](Http::ResponseHeaderMap& headers) {
  if (route_entry_ == nullptr) {
    return;
  }

  if (modify_headers_from_upstream_lb_) {
    modify_headers_from_upstream_lb_(headers);
  }

  route_entry_->finalizeResponseHeaders(headers, callbacks_->streamInfo());  // LINE 453
  // This invokes route entry header processing that applies response_headers_to_add

  if (attempt_count_ == 0 || !route_entry_->includeAttemptCountInResponse()) {
    return;
  }
  headers.setEnvoyAttemptCount(attempt_count_);
};
```

### Code Reference 3: Upstream Response Path (Single Invocation - Correct Behavior)
**File**: `source/common/router/router.cc`

**Location**: `Filter::onUpstreamHeaders()` lines 1794-1801

```cpp
// Modify response headers after we have set the final upstream info because we may need to
// modify the headers based on the upstream host.
modify_headers_(*headers);  // ONLY CALL - contains finalizeResponseHeaders internally

if (end_stream) {
  onUpstreamComplete(upstream_request);
}

callbacks_->encodeHeaders(std::move(headers), end_stream,
                          StreamInfo::ResponseCodeDetails::get().ViaUpstream);
```

For upstream responses, `finalizeResponseHeaders()` is called only ONCE through the `modify_headers_` callback.

### Code Reference 4: Header Addition Mechanism
**File**: `source/common/router/config_impl.cc`

**Location**: `RouteEntryImplBase::finalizeResponseHeaders()` lines 942-950

```cpp
void RouteEntryImplBase::finalizeResponseHeaders(Http::ResponseHeaderMap& headers,
                                                 const StreamInfo::StreamInfo& stream_info) const {
  for (const HeaderParser* header_parser : getResponseHeaderParsers(
           /*specificity_ascend=*/vhost_->globalRouteConfig().mostSpecificHeaderMutationsWins())) {
    // Later evaluated header parser wins.
    header_parser->evaluateHeaders(headers, {stream_info.getRequestHeaders(), &headers},
                                   stream_info);
  }
}
```

This method iterates through header parsers and calls `evaluateHeaders()` which applies the configured `response_headers_to_add` with the specified `append_action`.

### Code Reference 5: Header Evaluation and Append Action Handling
**File**: `source/common/router/header_parser.cc`

**Location**: `HeaderParser::evaluateHeaders()` lines 145-213

```cpp
void HeaderParser::evaluateHeaders(Http::HeaderMap& headers,
                                   const Formatter::HttpFormatterContext& context,
                                   const StreamInfo::StreamInfo* stream_info) const {
  // ... header removal phase ...

  for (const auto& [key, entry] : headers_to_add_) {
    // ... format value ...
    switch (entry->append_action_) {
      case HeaderValueOption::APPEND_IF_EXISTS_OR_ADD:
        headers_to_add.emplace_back(key, value);
        break;
      case HeaderValueOption::ADD_IF_ABSENT:
        if (auto header_entry = headers.get(key); header_entry.empty()) {
          headers_to_add.emplace_back(key, value);
        }
        break;
      case HeaderValueOption::OVERWRITE_IF_EXISTS:
        if (headers.get(key).empty()) {
          break;
        }
        FALLTHRU;
      case HeaderValueOption::OVERWRITE_IF_EXISTS_OR_ADD:
        headers_to_overwrite.emplace_back(key, value);
        break;
    }
  }

  // Apply accumulated header changes
  for (const auto& header : headers_to_overwrite) {
    headers.setReferenceKey(header.first, header.second);
  }
  for (const auto& header : headers_to_add) {
    headers.addReferenceKey(header.first, header.second);
  }
}
```

When called twice, headers with `OVERWRITE_IF_EXISTS_OR_ADD` get added once (overwriting), but headers with `APPEND_IF_EXISTS_OR_ADD` or `ADD_IF_ABSENT` get duplicated or added a second time.

### Code Reference 6: Proto Definition - append_action Field
**File**: `api/envoy/config/core/v3/base.proto`

**Location**: `HeaderValueOption` message definition

The `append_action` enum field with default value `APPEND_IF_EXISTS_OR_ADD` controls how headers are applied. Despite `OVERWRITE_IF_EXISTS_OR_ADD` being used in the configuration example, the default value and field semantics mean that headers configured to be appended get duplicated when `finalizeResponseHeaders()` is called twice.

## Affected Components

1. **source/common/http/filter_manager.cc** - `DownstreamFilterManager` class
   - `sendLocalReplyViaFilterChain()` - lines 1109-1145
   - `sendDirectLocalReply()` - lines 1147-1193
   - `prepareLocalReplyViaFilterChain()` - lines 1056-1094

2. **source/common/router/router.cc** - `Filter` class (router filter)
   - `Filter::decodeHeaders()` - initializes `modify_headers_` at line 444
   - `Filter::onUpstreamHeaders()` - correctly calls `modify_headers_()` once at line 1794
   - Multiple `sendLocalReply()` calls that pass `modify_headers_` callback

3. **source/common/router/config_impl.cc** - `RouteEntryImplBase` class
   - `finalizeResponseHeaders()` - lines 942-950

4. **source/common/router/header_parser.cc** - `HeaderParser` class
   - `evaluateHeaders()` - lines 145-213 - applies header modifications based on `append_action`

5. **api/envoy/config/core/v3/base.proto** - `HeaderValueOption` protobuf
   - Defines `append_action` enum and deprecated `append` field

## Causal Chain

1. **Symptom**: Response headers appear twice in local replies (router-generated error responses)
2. → Router operator configures `response_headers_to_add` with header key/value and `append_action: OVERWRITE_IF_EXISTS_OR_ADD`
3. → Request triggers upstream timeout → Router generates local reply via `Filter::sendLocalReply()`
4. → `Filter::sendLocalReply()` calls `callbacks_->sendLocalReply(... modify_headers_, ...)`
5. → `DownstreamFilterManager::sendLocalReply()` invokes either `sendLocalReplyViaFilterChain()` or `prepareLocalReplyViaFilterChain()`
6. → These methods create an encoder lambda that calls:
   - First: `route_entry_->finalizeResponseHeaders()` directly (line 1125, 1074)
   - Then: `modify_headers()` callback
7. → The `modify_headers_` callback (from router filter at line 444) internally calls `route_entry_->finalizeResponseHeaders()` again
8. → `finalizeResponseHeaders()` calls `header_parser->evaluateHeaders()` for all header parsers
9. → `evaluateHeaders()` applies the configured response headers based on their `append_action`
10. → **Root Cause**: When `evaluateHeaders()` runs twice on the same header map:
    - `OVERWRITE_IF_EXISTS_OR_ADD` actions: First call sets header, second call does nothing (already exists, overwrites with same value)
    - `APPEND_IF_EXISTS_OR_ADD` actions: First call adds header, second call appends duplicate
    - `ADD_IF_ABSENT` actions: First call adds header, second call skips (already exists)
    - **Result**: Headers appear twice in access logs and downstream responses

## Recommendation

**Fix Strategy**: The `sendLocalReplyViaFilterChain()`, `sendDirectLocalReply()`, and `prepareLocalReplyViaFilterChain()` methods should NOT independently call `route_entry_->finalizeResponseHeaders()`. Instead, they should rely entirely on the `modify_headers_` callback passed by the router filter to handle route-level header modifications.

**Implementation Approach**:
1. Remove the direct call to `route_entry_->finalizeResponseHeaders()` from the encoder lambda in all three methods
2. Ensure the router filter's `modify_headers_` callback (or a null check for cases where it's not provided) is always passed to these methods
3. Verify that the `modify_headers_` callback is properly initialized in all code paths that generate local replies

**Diagnostic Steps**:
1. Enable detailed access logging with `%RESPONSE_HEADERS%` formatter to capture the full response header map
2. Trigger a local reply scenario (upstream timeout, 503 service unavailable)
3. Compare response header counts between normal upstream responses (working correctly) and local replies (buggy)
4. Trace through the filter manager code to confirm double invocation of header modification callbacks
5. Add debug logging at line 1125 and line 453 to verify both are being called for the same request

**Alternative Quick Fix**: If maintaining backward compatibility, the router filter could track whether `finalizeResponseHeaders()` has already been called and skip the second invocation, but the primary fix is cleaner.

## Confidence Level

**High**: The code inspection clearly shows the double invocation pattern in `filter_manager.cc` vs. the single invocation in the correct upstream path. The proto definitions and header parsing logic confirm how repeated calls result in duplicate headers.
