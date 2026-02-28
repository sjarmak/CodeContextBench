# cilium-endpoint-manager-refac-001: Extract EndpointRegenerator

## Task Type: Cross-File Refactoring (Extract)

Extract regeneration logic into EndpointRegenerator struct.

## Key Reference Files
- `pkg/endpoint/manager.go` — source of extraction
- `pkg/endpoint/endpoint.go` — Endpoint struct

## Search Strategy
- Search for `Regenerat` in `pkg/endpoint/` for regeneration methods
- Search for `endpointManager` for manager references
