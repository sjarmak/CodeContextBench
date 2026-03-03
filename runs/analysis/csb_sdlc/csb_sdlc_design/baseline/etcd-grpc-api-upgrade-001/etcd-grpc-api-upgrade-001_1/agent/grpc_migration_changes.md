# gRPC Dial Migration - Change Documentation

This document describes all necessary changes to migrate from deprecated `grpc.Dial()` and `grpc.DialContext()` calls to `grpc.NewClient()`.

## Summary
- **Total Files to Modify**: 18
- **Total Changes**: 22
- **Affected Projects**: kubernetes, etcd, containerd

## Changes Required

### kubernetes/pkg/kubelet/apis/podresources/client.go (2 changes)

**Function: GetV1alpha1Client (lines 37-53)**
```go
// BEFORE
ctx, cancel := context.WithTimeout(context.TODO(), connectionTimeout)
defer cancel()

conn, err := grpc.DialContext(ctx, addr,

// AFTER
conn, err := grpc.NewClient(addr,
```

**Function: GetV1Client (lines 56-72)**
```go
// BEFORE
ctx, cancel := context.WithTimeout(context.TODO(), connectionTimeout)
defer cancel()

conn, err := grpc.DialContext(ctx, addr,

// AFTER
conn, err := grpc.NewClient(addr,
```

### kubernetes/pkg/kubelet/cm/devicemanager/plugin/v1beta1/client.go (1 change)

**Function: dial (line 135)**
```go
// BEFORE
c, err := grpc.DialContext(ctx, unixSocketPath,

// AFTER
c, err := grpc.NewClient(unixSocketPath,
```

### kubernetes/pkg/kubelet/cm/devicemanager/plugin/v1beta1/stub.go (1 change)

**Function: Register (line 296)**
```go
// BEFORE
//nolint:staticcheck // SA1019: grpc.DialContext is deprecated: use NewClient instead.
conn, err := grpc.DialContext(ctxDial, kubeletEndpoint,

// AFTER
conn, err := grpc.NewClient(kubeletEndpoint,
```

Remove the nolint comment as it's no longer needed.

### kubernetes/pkg/kubelet/pluginmanager/operationexecutor/operation_generator.go (1 change)

**Function: dial (line 196)**
```go
// BEFORE
c, err := grpc.DialContext(ctx, unixSocketPath,

// AFTER
c, err := grpc.NewClient(unixSocketPath,
```

### kubernetes/pkg/kubelet/pluginmanager/pluginwatcher/example_handler.go (1 change)

**Function: dial (line 143)**
```go
// BEFORE
c, err := grpc.DialContext(ctx, unixSocketPath,

// AFTER
c, err := grpc.NewClient(unixSocketPath,
```

### kubernetes/pkg/probe/grpc/grpc.go (1 change)

**Function: Probe (line 70)**
```go
// BEFORE
conn, err := grpc.DialContext(ctx, addr, opts...)

// AFTER
conn, err := grpc.NewClient(addr, opts...)
```

### kubernetes/pkg/volume/csi/csi_client.go (1 change)

**Function: newGrpcConn (line 536)**
```go
// BEFORE
return grpc.Dial(

// AFTER
return grpc.NewClient(
```

### kubernetes/pkg/serviceaccount/externaljwt/plugin/plugin.go (1 change)

**Function: New (line 53)**
```go
// BEFORE
conn, err := grpc.Dial(

// AFTER
conn, err := grpc.NewClient(
```

### kubernetes/pkg/serviceaccount/externaljwt/plugin/keycache_test.go (3 changes)

**Function: TestCache (line 198)**
**Function: TestCacheSync (line 280)**
**Function: TestCacheTokenUpdate (line 345)**
```go
// BEFORE
clientConn, err := grpc.DialContext(

// AFTER
clientConn, err := grpc.NewClient(
```

### kubernetes/pkg/serviceaccount/externaljwt/plugin/plugin_test.go (1 change)

**Function: TestExternalTokenGenerator (line 311)**
```go
// BEFORE
clientConn, err := grpc.DialContext(

// AFTER
clientConn, err := grpc.NewClient(
```

### kubernetes/staging/src/k8s.io/apiserver/pkg/storage/value/encrypt/envelope/grpc_service.go (1 change)

**Function: NewGRPCService (line 64)**
```go
// BEFORE
s.connection, err = grpc.Dial(

// AFTER
s.connection, err = grpc.NewClient(
```

### kubernetes/staging/src/k8s.io/apiserver/pkg/storage/value/encrypt/envelope/kmsv2/grpc_service.go (1 change)

**Function: NewGRPCService (line 59)**
```go
// BEFORE
s.connection, err = grpc.Dial(

// AFTER
s.connection, err = grpc.NewClient(
```

### kubernetes/staging/src/k8s.io/cri-client/pkg/remote_image.go (1 change)

**Function: NewRemoteImageService (line 89)**
```go
// BEFORE
conn, err := grpc.DialContext(ctx, addr, dialOpts...)

// AFTER
conn, err := grpc.NewClient(addr, dialOpts...)
```

### kubernetes/staging/src/k8s.io/cri-client/pkg/remote_runtime.go (1 change)

**Function: NewRemoteRuntimeService (line 121)**
```go
// BEFORE
conn, err := grpc.DialContext(ctx, addr, dialOpts...)

// AFTER
conn, err := grpc.NewClient(addr, dialOpts...)
```

### kubernetes/staging/src/k8s.io/kms/pkg/service/grpc_service_test.go (1 change)

**Function: newClient (line 143)**
```go
// BEFORE
cnn, err := grpc.Dial(

// AFTER
cnn, err := grpc.NewClient(
```

### etcd/server/embed/etcd.go (1 change)

**Function: startClientListeners (line 835)**
```go
// BEFORE
conn, err := grpc.DialContext(ctx, addr, opts...) //nolint:staticcheck // TODO: remove for a supported version

// AFTER
conn, err := grpc.NewClient(addr, opts...) //nolint:staticcheck // TODO: remove for a supported version
```

### etcd/client/v3/client.go (1 change)

**Function: dialSetupOpts (line 334)**
```go
// BEFORE
conn, err := grpc.DialContext(dctx, target, opts...) //nolint:staticcheck // TODO: remove for a supported version

// AFTER
conn, err := grpc.NewClient(target, opts...) //nolint:staticcheck // TODO: remove for a supported version
```

### etcd/tests/integration/clientv3/naming/resolver_test.go (1 change)

**Function: testEtcdGRPCResolver (line 78)**
```go
// BEFORE
conn, err := grpc.Dial("etcd:///foo", grpc.WithTransportCredentials(insecure.NewCredentials()), grpc.WithResolvers(b), //nolint:staticcheck // TODO: remove for a supported version

// AFTER
conn, err := grpc.NewClient("etcd:///foo", grpc.WithTransportCredentials(insecure.NewCredentials()), grpc.WithResolvers(b), //nolint:staticcheck // TODO: remove for a supported version
```

## Migration Pattern

The migration follows these simple rules:

1. **Remove context.WithTimeout setup**: When `grpc.DialContext` is used with a context created via `context.WithTimeout`, remove the timeout setup:
   ```go
   // Remove these lines
   ctx, cancel := context.WithTimeout(...)
   defer cancel()
   ```

2. **Replace the dial call**:
   ```go
   // Change from
   grpc.DialContext(ctx, target, opts...)
   // To
   grpc.NewClient(target, opts...)

   // Or change from
   grpc.Dial(target, opts...)
   // To
   grpc.NewClient(target, opts...)
   ```

3. **Keep all options**: All `grpc.WithX` options are preserved exactly as they were.

4. **No API changes needed**: The `grpc.NewClient` function returns the same `*grpc.ClientConn` type, so no downstream code needs modification.

## Notes

- The `grpc.NewClient()` API handles context management internally, making timeout configuration automatic
- All nolint comments referencing the deprecation can be removed (already done in etcd files)
- No changes are needed to proto definitions or generated code (`*.pb.go` or `*.pb.gw.go` files)
- All error handling remains exactly the same
