Trace the Pod creation request flow from HTTP handler to validation

Document the complete call chain from HTTP POST to Pod validation logic



Search hints:
- Start at createHandler in apiserver/pkg/endpoints/handlers/create.go
- Follow Store.Create() calls
- Look for PrepareForCreate and Validate methods
- Find pod-specific strategy in pkg/registry/core/pod/strategy.go
