# prometheus-silence-bulk-api-feat-001: Bulk Silence API

## Task Type: Feature Implementation (API Endpoint)

Add a bulk silence creation endpoint following Prometheus API patterns.

## Key Reference Files
- `web/api/v1/api.go` — API router and handler registration
- `web/api/v1/api_test.go` — test patterns
- `silence/silence.go` — silence model

## Search Strategy
- Search for `silences` in `web/api/v1/` to find existing silence handlers
- Search for `router.Post` or `r.Post` to find route registration pattern
- Search for `apiError` to understand error response format
