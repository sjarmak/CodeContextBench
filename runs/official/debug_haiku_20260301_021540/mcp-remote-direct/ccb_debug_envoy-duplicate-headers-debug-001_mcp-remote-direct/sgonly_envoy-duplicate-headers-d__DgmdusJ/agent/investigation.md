# Investigation Report: Duplicate Response Headers in Envoy Filter Pipeline

## Summary

Response headers configured via `response_headers_to_add` are duplicated in local reply responses (e.g., upstream timeout, connection failure) due to `finalizeResponseHeaders()` being called twice via different code paths in the filter manager's local reply handling.

## Root Cause

The root cause is that `finalizeResponseHeaders()` is now invoked WITHIN a modify_headers callback lambda defined in the filter manager (lines 1125 in `filter_manager.cc`), AND this lambda is passed to `Utility::sendLocalReply()` which applies header modifications during both the preparation AND encoding phases. The issue manifests specifically for local replies where response headers configured with `OVERWRITE_IF_EXISTS_OR_ADD` append_action are processed twice, causing duplication.

### Specific Mechanism

When a local reply is generated (e.g., upstream timeout):

1. **Router calls sendLocalReply** (router.cc:520):
   - Router passes `modify_headers_` callback to filter manager's sendLocalReply
   - `modify_headers_` was initialized at router.cc:444 to add attempt count headers only

2. **Filter Manager wraps callback** (filter_manager.cc:1123-1130 in `sendLocalReplyViaFilterChain`):
   - Creates a NEW lambda that calls:
     ```cpp
     route_entry_->finalizeResponseHeaders(headers, streamInfo());  // LINE 1125
     modify_headers_(headers);  // LINE 1128
     ```
   - This lambda is passed to `Utility::sendLocalReply()` as the modify_headers callback

3. **Utility::prepareLocalReply invokes callback** (utility.cc:718-720):
   - Calls `encode_functions.modify_headers_(*response_headers)` ONCE
   - The lambda executes, calling finalizeResponseHeaders

4. **Headers pass through filter chain** (filter_manager.cc:1138):
   - In `sendLocalReplyViaFilterChain`, the prepared headers are encoded via:
     ```cpp
     encodeHeaders(nullptr, filter_manager_callbacks_.responseHeaders().ref(), end_stream);
     ```
   - Headers iterate through encoder filters

5. **CRITICAL: For local replies generated during certain conditions**, if the headers are further processed or if route configs are re-evaluated, the header parser's `evaluateHeaders()` (header_parser.cc:139) may be invoked again through alternative code paths.

### The Double-Call Mechanism

The duplication specifically occurs because:

- **Line 1 of duplication**: `finalizeResponseHeaders` called in the lambda (filter_manager.cc:1125)
- **Line 2 of duplication**: For certain local reply scenarios (e.g., when `prepareLocalReplyViaFilterChain` is used instead of `sendLocalReplyViaFilterChain`), or when headers are re-finalized in the filter chain iteration, another call occurs

The header append_action `OVERWRITE_IF_EXISTS_OR_ADD` uses `setReferenceKey()` (header_map_impl.cc:321) which performs `remove(key)` then `addReferenceKey(key, value)`. When called twice on the same header, instead of overwriting, both calls add entries to the response, resulting in two header values in the access log.

## Evidence

### Code References

1. **Filter Manager Local Reply - sendLocalReplyViaFilterChain** (filter_manager.cc:1120-1145):
   - Lambda calling finalizeResponseHeaders at line 1125
   - Lambda passed to Utility::sendLocalReply

2. **Filter Manager Local Reply - prepareLocalReplyViaFilterChain** (filter_manager.cc:1055-1094):
   - Similar lambda also calling finalizeResponseHeaders at line 1074
   - Prepared reply later executed by executeLocalReplyIfPrepared (line 1102)

3. **Filter Manager Local Reply - sendDirectLocalReply** (filter_manager.cc:1147-1190):
   - Another lambda calling finalizeResponseHeaders at line 1158
   - Alternative path for local replies after response has partially started

4. **Router Filter Upstream Response** (router.cc:1792-1793):
   - Direct sequential calls:
     ```cpp
     route_entry_->finalizeResponseHeaders(*headers, callbacks_->streamInfo());
     modify_headers_(*headers);
     ```

5. **Router Calls sendLocalReply** (router.cc:520, 548, 748):
   - Multiple error scenarios pass `modify_headers_` callback
   - No finalizeResponseHeaders call before sendLocalReply in router

6. **Header Parser Evaluation** (header_parser.cc:139-213):
   - `evaluateHeaders()` processes headers_to_overwrite list
   - Calls `headers.setReferenceKey()` for OVERWRITE_IF_EXISTS_OR_ADD action

7. **Header Map Implementation** (header_map_impl.cc:321-324):
   - `setReferenceKey()` removes then adds: `remove(key); addReferenceKey(key, value);`

## Affected Components

1. **source/common/router/** - Router filter with modify_headers_ callback initialization
2. **source/common/http/filter_manager.cc** - Multiple local reply code paths with identical finalizeResponseHeaders calls
3. **source/common/router/header_parser.cc** - Header evaluation and append_action handling
4. **source/common/http/utility.cc** - Utility::sendLocalReply and Utility::prepareLocalReply
5. **api/envoy/config/core/v3/base.proto** - HeaderValueOption definition with append_action enum

## Causal Chain

1. **Symptom**: Duplicate headers in access log for local reply responses (e.g., "x-custom-trace: abc123\nx-custom-trace: abc123")

2. **Intermediate**: response_headers_to_add configured with `OVERWRITE_IF_EXISTS_OR_ADD` append_action

3. **Intermediate**: Router generates local reply (upstream timeout, cluster not found, etc.) and calls sendLocalReply with modify_headers_ callback

4. **Intermediate**: Filter manager's sendLocalReplyViaFilterChain wraps the callback in a lambda that calls finalizeResponseHeaders

5. **Intermediate**: Utility::prepareLocalReply calls the wrapped lambda, which executes finalizeResponseHeaders

6. **Intermediate**: HeaderParser::evaluateHeaders processes the header with OVERWRITE_IF_EXISTS_OR_ADD action

7. **Intermediate**: HeaderMapImpl::setReferenceKey removes and then adds the header

8. **Intermediate**: Headers encoded through filter chain (possibly going through second evaluation path)

9. **Root Cause**: finalizeResponseHeaders called multiple times on same headers, causing header parser to re-apply response_headers_to_add configuration

10. **Result**: OVERWRITE_IF_EXISTS_OR_ADD action creates two header entries instead of one overwrite

## Recommendation

### Fix Strategy

The issue requires ensuring that `finalizeResponseHeaders()` is called exactly once per response, regardless of the code path (upstream response vs local reply).

**Option 1: Remove duplicate finalizeResponseHeaders from filter manager lambdas** (Recommended)
- Remove finalizeResponseHeaders calls from the lambdas in sendLocalReplyViaFilterChain (line 1125), prepareLocalReplyViaFilterChain (line 1074), and sendDirectLocalReply (line 1158)
- Call finalizeResponseHeaders once before creating the EncodeFunctions struct
- Ensures single invocation pattern matches upstream response path

**Option 2: Track finalization state**
- Add a flag to ResponseHeaderMap or StreamInfo to track whether finalizeResponseHeaders has been called
- Skip subsequent calls if already finalized
- More defensive but adds runtime overhead

### Diagnostic Steps

To reproduce the issue:

1. Configure route with `response_headers_to_add`:
   ```yaml
   response_headers_to_add:
     - header:
         key: "x-custom-trace"
         value: "%REQ(x-request-id)%"
       append_action: OVERWRITE_IF_EXISTS_OR_ADD
   ```

2. Trigger local reply scenario:
   - Set upstream request timeout
   - Configure non-existent cluster
   - Send request larger than buffer limit

3. Examine access logs with `%RESPONSE_CODE_DETAILS%` and response headers

4. Verify header appears twice in HTTP response headers

### Related Code Paths

The fix should also review:
- AsyncStreamImpl::sendLocalReply (async_client_impl.cc:166) for similar patterns
- Other filter callbacks that may invoke sendLocalReply
- Integration of header mutations with route-level header additions
