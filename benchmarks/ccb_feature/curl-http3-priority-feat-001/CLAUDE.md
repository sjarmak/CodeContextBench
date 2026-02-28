# curl-http3-priority-feat-001: HTTP/3 Extensible Priorities

## Task Type: Feature Implementation (Protocol Extension)

Implement RFC 9218 HTTP/3 stream priorities in curl.

## Key Reference Files
- `include/curl/curl.h` — CURLOPT definitions
- `lib/setopt.c` — option implementation
- `lib/urldata.h` — data structures (has RFC 9218 TODO at ~line 1242)
- `lib/vquic/curl_ngtcp2.c` — HTTP/3 backend
- `src/tool_getparam.c` — CLI parsing

## Search Strategy
- Search for `CURLOPT_HTTP` to find HTTP option definition patterns
- Search for `ngtcp2` or `nghttp3` for HTTP/3 backend
- Search for `tool_getparam` for CLI option patterns
- Search for `RFC 9218` or `priority` in vquic/ for existing TODOs
