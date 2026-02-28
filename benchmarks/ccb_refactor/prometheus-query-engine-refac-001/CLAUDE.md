# prometheus-query-engine-refac-001: Rename QueryEngine

## Task Type: Cross-File Refactoring (Rename)

Rename QueryEngine → PromQLEvaluator across Prometheus.

## Key Reference Files
- `promql/engine.go` — struct definition
- `web/api/v1/api.go` — API usage
- `cmd/prometheus/main.go` — initialization

## Search Strategy
- Search for `type QueryEngine struct` for definition
- Search for `QueryEngine` across all Go files for references
- Search for `NewQueryEngine` for constructor usage
