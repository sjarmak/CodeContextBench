# istio-discovery-server-refac-001: Rename DiscoveryServer

## Task Type: Cross-File Refactoring (Rename)

Rename DiscoveryServer → XDSServer across Istio pilot.

## Key Reference Files
- `pilot/pkg/xds/discovery.go` — definition
- `pilot/pkg/bootstrap/server.go` — initialization
- `pilot/pkg/xds/ads.go` — usage

## Search Strategy
- Search for `DiscoveryServer` across pilot/ for all references
- Search for `NewDiscoveryServer` for constructor calls
