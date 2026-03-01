# Kubernetes CRD Lifecycle: Cross-Repo Architectural Analysis

## Files Examined

### Foundation (apimachinery)
- **staging/src/k8s.io/apimachinery/pkg/runtime/scheme.go** — Type registry for mapping GVK to Go structs; central for dynamic type dispatch
- **staging/src/k8s.io/apimachinery/pkg/runtime/types.go** — Runtime type interfaces (Object, List)
- **staging/src/k8s.io/apimachinery/pkg/apis/meta/v1/group_version.go** — GroupVersionKind (GVK), GroupVersionResource (GVR), GroupKind types
- **staging/src/k8s.io/apimachinery/pkg/apis/meta/v1/types.go** — TypeMeta, ObjectMeta standard metadata
- **staging/src/k8s.io/apimachinery/pkg/apis/meta/v1/unstructured/unstructured.go** — Unstructured generic object wrapper (map[string]interface{})
- **staging/src/k8s.io/apimachinery/pkg/apis/meta/v1/unstructured/unstructured_list.go** — UnstructuredList generic list wrapper

### CRD Type Definitions & Server-Side (apiextensions-apiserver)
- **staging/src/k8s.io/apiextensions-apiserver/pkg/apis/apiextensions/types.go** — Internal hub types for CustomResourceDefinition, CustomResourceDefinitionSpec
- **staging/src/k8s.io/apiextensions-apiserver/pkg/apis/apiextensions/v1/types.go** — External v1 API types for CRDs
- **staging/src/k8s.io/apiextensions-apiserver/pkg/apis/apiextensions/v1beta1/types.go** — External v1beta1 API types for CRDs
- **staging/src/k8s.io/apiextensions-apiserver/pkg/apis/apiextensions/install/install.go** — Scheme registration for CRD types
- **staging/src/k8s.io/apiextensions-apiserver/pkg/apiserver/customresource_handler.go** — Dynamic HTTP handler routing requests for custom resources
- **staging/src/k8s.io/apiextensions-apiserver/pkg/registry/customresource/etcd.go** — etcd storage layer using Unstructured objects
- **staging/src/k8s.io/apiextensions-apiserver/pkg/apiserver/validation/validation.go** — Schema validation engine for custom resource payloads
- **staging/src/k8s.io/apiextensions-apiserver/pkg/apiserver/schema/validation.go** — Structural schema validation for CRD properties
- **staging/src/k8s.io/apiextensions-apiserver/pkg/registry/customresource/strategy.go** — Create/update/delete strategies for custom resources

### Client-Side Access (client-go)
- **staging/src/k8s.io/client-go/dynamic/simple.go** — DynamicClient for unstructured resource manipulation via REST
- **staging/src/k8s.io/client-go/dynamic/dynamicinformer/informer.go** — DynamicSharedInformerFactory for watching unstructured resources
- **staging/src/k8s.io/client-go/dynamic/dynamicinformer/interface.go** — DynamicSharedInformerFactory interface definition
- **staging/src/k8s.io/client-go/dynamic/dynamiclister/lister.go** — UnstructuredLister for querying cached resources
- **staging/src/k8s.io/client-go/informers/factory.go** — SharedInformerFactory for typed resources with generic informer support
- **staging/src/k8s.io/client-go/informers/generic.go** — GenericInformer interface (Informer + Lister) and ForResource pattern
- **staging/src/k8s.io/client-go/rest/request.go** — REST client request builder for HTTP API communication

### API Group Registration (api)
- **staging/src/k8s.io/api/admission/v1/types.go** — Example of external API types
- **staging/src/k8s.io/api/apps/v1/types.go** — Example of external API types for Deployments, StatefulSets, etc.

## Dependency Chain

### 1. Foundation Layer: apimachinery

The foundation is built on core abstractions in apimachinery:

**Scheme (runtime/scheme.go):**
- Central type registry mapping `GroupVersionKind → reflect.Type`
- Enables serialization/deserialization of any registered type
- Stores converters between internal and external versions
- Thread-safe after registration phase (read-only at runtime)

**GVK/GVR (meta/v1/group_version.go):**
- `GroupVersionKind`: Uniquely identifies a type (e.g., `apiextensions.k8s.io/v1/CustomResourceDefinition`)
- `GroupVersionResource`: Uniquely identifies a resource (e.g., `apiextensions.k8s.io/v1/customresourcedefinitions`)
- Provides parsing and string serialization for API versioning

**Standard Metadata (meta/v1/types.go):**
- `TypeMeta`: Holds APIVersion and Kind (present in every Kubernetes object)
- `ObjectMeta`: Standard metadata (name, namespace, labels, annotations, ownerReferences, etc.)
- Enables consistent operations across all object types

**Unstructured (meta/v1/unstructured.go):**
- Generic representation as `map[string]interface{}` wrapping arbitrary JSON
- Implements `runtime.Unstructured` and `metav1.Object` interfaces
- Allows CRDs to be manipulated without Go struct registration
- Critical bridge enabling dynamic resource handling

### 2. Type Definition Layer: apiextensions-apiserver

**Internal Hub Types (apis/apiextensions/types.go):**
- `CustomResourceDefinition`: Describes how a CRD is defined
- `CustomResourceDefinitionSpec`: Specifies group, names, scope, versions, validation schema
- Acts as the internal hub type for API versioning
- Contains the JSON Schema validator and conversion strategy

**External API Versions (apis/apiextensions/v1*, v1beta1/):**
- v1 and v1beta1 expose the CRD API to users
- Generated conversion code translates between versions
- Registered in Scheme via `install/install.go`

**Scheme Registration (crdserverscheme/scheme.go):**
```
// Registers both internal and external CRD types
// Adds conversion functions for version migrations
// Makes Scheme aware of all CRD-related types
scheme.AddTypes(apiextensions.SchemeGroupVersion, ...)
scheme.AddTypes(apiextensionsv1.SchemeGroupVersion, ...)
```

### 3. Server-Side Lifecycle: Validation → Storage → HTTP Handler

**Validation Layer (apiserver/validation/):**
1. **Request Validation**: Custom resource payloads validated against CRD's OpenAPI schema
2. **Schema Enforcement**: `validation.go` uses structural schema validation
3. **CEL Rules**: Support for custom validation expressions (in schema/cel/)
4. **Defaulting**: Schema-based default value application (schema/defaulting/)
5. **Pruning**: Removal of unknown fields per schema (schema/pruning/)

**etcd Storage Layer (registry/customresource/etcd.go):**
```go
// CustomResourceStorage creates the actual storage backend
NewStorage(resource, kind, strategy, optsGetter, ...)
  // NewFunc creates Unstructured objects for storage
  // NewListFunc creates UnstructuredList for queries
  // store.CompleteWithOptions connects to generic.Store
  // generic.Store handles etcd operations
```

**Dynamic HTTP Handler (apiserver/customresource_handler.go):**
```
crdHandler {
  versionDiscoveryHandler     // /apis endpoint
  groupDiscoveryHandler       // /apis/{group} endpoint
  customStorageLock           // protects storage updates
  customStorage (atomic)      // crdStorageMap: GVR → REST storage
  crdLister                   // informs on CRD changes
}
```

- Intercepts HTTP requests for custom resources
- Routes requests to the correct storage backend based on GVR
- Handles CRUD operations through the storage strategy
- Supports watch streams for real-time updates

### 4. Client-Side Access Layer: REST → Informer → Lister

**REST Client (rest/request.go):**
```go
Request {
  c *RESTClient      // HTTP client with config
  verb               // GET, POST, PUT, DELETE, PATCH, WATCH
  URL params         // Group, Version, Resource, Name, Namespace
  body               // For create/update operations
  ...
}
// Chains operations: Do().Into(result)
```

**Dynamic Client (dynamic/simple.go):**
```go
DynamicClient {
  client rest.Interface  // Configured REST client
}
// Methods return *unstructured.Unstructured
// Get, List, Create, Update, Delete, Watch on GroupVersionResource
```

**Typed Clientset** (generated by code-generator):
```go
// Example structure for built-in resources
kubernetes.Clientset {
  CoreV1()    → corev1.CoreV1Interface
  AppsV1()    → appsv1.AppsV1Interface
  BatchV1()   → batchv1.BatchV1Interface
}
// Each returns group client with resource interfaces
// e.g., corev1.CoreV1Interface.Pods(ns).Get(name)
```

**Informers (informers/factory.go & informers/generic.go):**
```go
SharedInformerFactory {
  InformerFor(obj)           // typed informers
  ForResource(gvr)           // generic informer for CRDs
}

GenericInformer {
  Informer() cache.SharedIndexInformer  // watch + cache
  Lister() cache.GenericLister          // query cache
}
```

**Dynamic Informer (dynamic/dynamicinformer/informer.go):**
```go
DynamicSharedInformerFactory {
  client dynamic.Interface    // Dynamic client
  informers map[GVR]GenericInformer
}
// ForResource(gvr) returns GenericInformer for any CRD
// Uses SharedIndexInformer with Unstructured objects
```

**Listers (dynamic/dynamiclister/):**
```go
UnstructuredLister {
  List(selector labels.Selector)
  Get(name string)
  // Operates on cache populated by informer
}
```

### Checkpoint: Server-Side to Client-Side

The critical transition point is the **watch stream**:

1. **Server**: customresource_handler watches etcd for changes to custom resources
2. **Etcd**: Stores custom resources as Unstructured objects
3. **Watch**: Transmits events (Added, Modified, Deleted) to client
4. **Informer**: Receives watch events, updates cache (SharedIndexInformer)
5. **Lister**: Reads from cache via GenericLister interface

The cycle repeats: CRD resource → etcd → watch stream → informer cache → lister queries

## Analysis

### Cross-Project Dependency Flow

**apimachinery ← all other projects**
- Every project imports `k8s.io/apimachinery` for:
  - Scheme for type registration
  - GVK/GVR for resource identification
  - ObjectMeta/TypeMeta for standard metadata
  - Unstructured for dynamic access
  - runtime.Object interface

**api ← client-go, apiextensions-apiserver**
- Defines external types for all built-in resources
- code-generator uses these to generate typed clients
- apiextensions-apiserver uses api types in generic handlers

**apiextensions-apiserver ← client-go**
- Exposes CRD API as both typed and unstructured
- Registers CRD types in shared Scheme
- Uses informers to watch CRD changes

**client-go ← everything**
- Dynamic client abstracts any Unstructured type
- Typed clients generated for built-in resources
- Informers watch any resource via DynamicSharedInformerFactory
- GenericInformer bridges typed and unstructured access

### Role of Scheme and GVK in Type Registration

**Scheme Registration Process:**
1. Each API package (api/{group}/v1/) registers its types
2. `install.go` functions register both internal (hub) and external versions
3. Conversion functions enable migration between versions
4. Scheme.AddTypes(gv, types...) maps GVK → struct type
5. Serializers use Scheme to encode/decode objects

**GVK Usage:**
- **Server side**: customresource_handler uses GVR to route HTTP requests
- **Client side**: Clients use GVK to deserialize JSON into typed structs
- **Informers**: Watch returns events tagged with GVK
- **Storage**: etcd keys include GVR for efficient queries

### How Unstructured Enables Dynamic Custom Resource Access

**Without Unstructured:**
- Each CRD would require a Go struct
- Client-go would need code generation for every CRD
- Would break the entire extensibility model

**With Unstructured:**
- CRDs handled as `map[string]interface{}`
- DynamicClient works for any GVR
- DynamicSharedInformerFactory watches without pre-registration
- Schema validation enforces correctness server-side
- No code generation needed for custom resources

**The Bridge:**
- `runtime.Unstructured` interface provides standard Object behavior
- `metav1.Object` accessor methods navigate the map
- `TypeMeta` stored in reserved `"apiVersion"` and `"kind"` keys
- `ObjectMeta` stored in reserved `"metadata"` key
- All other fields available as generic nested maps/lists

### Checkpoint Between Server-Side Storage and Client-Side Caching

**Server-Side Checkpoint (customresource_handler.go):**
- Receives HTTP request for custom resource
- Looks up CRD definition to validate schema
- Calls storage backend (etcd.go) to persist Unstructured object
- Broadcasts watch event with GVK + object state

**Watch Stream (cache.go in client-go/tools/):**
- Server sends `watch.Event{Type: "ADDED"/"MODIFIED"/"DELETED", Object: *Unstructured}`
- Client informer receives event on watch channel
- Informer updates cache index: `indexer.Add(obj)` or `indexer.Update(obj)` or `indexer.Delete(obj)`

**Client-Side Checkpoint (tools/cache/):**
- SharedIndexInformer maintains in-memory cache
- Supports multiple indices: namespace, labels, owner references
- Lister queries cache without network overhead
- OnAdd/OnUpdate/OnDelete handlers trigger user callbacks

**Consistency Model:**
- etcd → watch stream → informer cache is **eventually consistent**
- Large objects or network delays mean cache slightly lags
- `WaitForCacheSync` blocks until initial list is synced
- Continues to receive incremental updates via watch

## Summary

The Kubernetes CRD lifecycle spans four coordinated sub-projects: **apimachinery** provides foundational type abstractions (Scheme, GVK, Unstructured); **apiextensions-apiserver** defines CRD types and implements dynamic HTTP routing, validation, and etcd storage using Unstructured objects; **api** registers all built-in resource types; **client-go** exposes both typed clients (via code generation) and a dynamic client (for unstructured access), with SharedInformerFactory and DynamicSharedInformerFactory providing cached, watched access to resources. The critical insight is that Unstructured enables CRDs to flow through this entire ecosystem without pre-registration, while the Scheme provides type-safe access for built-in resources, all unified by GVK/GVR identifiers that route requests from client REST calls through the server's HTTP handler to etcd storage and back through watch streams to local informer caches.
