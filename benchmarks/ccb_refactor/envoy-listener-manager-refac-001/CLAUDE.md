# envoy-listener-manager-refac-001: Rename ListenerManagerImpl

## Task Type: Cross-File Refactoring (Rename)

Rename ListenerManagerImpl → ListenerOrchestrator in Envoy.

## Key Reference Files
- `source/common/listener_manager/listener_manager_impl.h` — declaration
- `source/common/listener_manager/listener_manager_impl.cc` — implementation
- `source/server/server.h` — usage

## Search Strategy
- Search for `ListenerManagerImpl` across the codebase
- Search for `listener_manager_impl` for file references
