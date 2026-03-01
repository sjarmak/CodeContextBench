# CRD Lifecycle Architecture Across Kubernetes Ecosystem

## Files Examined

### Foundation Layer (apimachinery)
- `staging/src/k8s.io/apimachinery/pkg/runtime/types.go` — TypeMeta (APIVersion, Kind), RawExtension for embedded objects
- `staging/src/k8s.io/apimachinery/pkg/runtime/scheme.go` — Scheme: type registry mapping GVK↔Go types, conversion, and defaulting
- `staging/src/k8s.io/apimachinery/pkg/runtime/schema/group_version.go` — GroupVersionKind (GVK) and GroupVersionResource (GVR) identifiers
- `staging/src/k8s.io/apimachinery/pkg/apis/meta/v1/unstructured/unstructured.go` — Unstructured: generic map-based object for CRD instances

### CRD Type Definitions (apiextensions-apiserver)
- `staging/src/k8s.io/apiextensions-apiserver/pkg/apis/apiextensions/types.go` — Internal hub version of CustomResourceDefinition
- `staging/src/k8s.io/apiextensions-apiserver/pkg/apis/apiextensions/v1/types.go` — External v1 version of CustomResourceDefinition
- `staging/src/k8s.io/apiextensions-apiserver/pkg/apis/apiextensions/register.go` — Scheme registration for CRD types (GVK→Go type mapping)
- `staging/src/k8s.io/apiextensions-apiserver/pkg/apis/apiextensions/install/` — Installation functions for registering CRD types into schemes

### Server-Side Storage & Validation (apiextensions-apiserver)
- `staging/src/k8s.io/apiextensions-apiserver/pkg/registry/customresource/etcd.go` — CustomResourceStorage: generic etcd backend using Unstructured
- `staging/src/k8s.io/apiextensions-apiserver/pkg/registry/customresource/strategy.go` — Storage strategy for create/update/delete operations
- `staging/src/k8s.io/apiextensions-apiserver/pkg/apiserver/validation/` — Schema validation using OpenAPI/JSONSchema
- `staging/src/k8s.io/apiextensions-apiserver/pkg/apiserver/customresource_handler.go` — HTTP handler: routes API requests to storage layer (lines 86-100 show crdHandler routing)

### Client-Side Access (client-go)
- `staging/src/k8s.io/client-go/dynamic/simple.go` — DynamicClient: generic REST client for any GVR, works with Unstructured
- `staging/src/k8s.io/client-go/dynamic/dynamicinformer/informer.go` — DynamicSharedInformerFactory & dynamicInformer: watches and caches Unstructured objects
- `staging/src/k8s.io/client-go/dynamic/dynamiclister/lister.go` — dynamicLister: queries local cache using indexer
- `staging/src/k8s.io/client-go/informers/factory.go` — SharedInformerFactory: base factory for typed informers (similar pattern)
- `staging/src/k8s.io/client-go/tools/cache/` — SharedIndexInformer: watch→cache→indexer foundation

---

## Dependency Chain

### 1. Foundation: apimachinery Types (Everything Depends On This)

**Core Types:**
- **TypeMeta** (`runtime/types.go`): Holds `apiVersion` and `kind` strings for all API objects
- **Scheme** (`runtime/scheme.go`): Central type registry
  - Maps `GroupVersionKind` ↔ Go types (e.g., `apiextensions.k8s.io/v1.CustomResourceDefinition` ↔ `*apiextensionsv1.CustomResourceDefinition`)
  - Maps `reflect.Type` ↔ `GroupVersionKind` (reverse lookup)
  - Manages conversion and defaulting functions
- **GroupVersionKind / GroupVersionResource** (`runtime/schema/group_version.go`):
  - **GVK** = `(Group, Version, Kind)` — identifies a type
  - **GVR** = `(Group, Version, Resource)` — identifies a REST endpoint
  - Conversion methods: `gvk.GroupVersion()`, `gvr.GroupResource()`, etc.
- **Unstructured** (`apis/meta/v1/unstructured/unstructured.go`):
  - Generic object: `Object map[string]interface{}`
  - Implements `runtime.Object` interface (has GVK/ObjectMeta)
  - Enables working with types without Go structs (critical for CRDs)

---

### 2. Type Definitions: CRD Types (apiextensions-apiserver)

**Two-Version Pattern:**
- **Internal Hub** (`pkg/apis/apiextensions/types.go`):
  - `CustomResourceDefinition` struct with `TypeMeta`, `ObjectMeta`, `Spec`, `Status`
  - Hub version for conversion (never exposed on wire)
  - Registered in internal scheme via `register.go:addKnownTypes()`

- **External v1** (`pkg/apis/apiextensions/v1/types.go`):
  - Public `CustomResourceDefinition` struct (mirrors internal structure)
  - Exposed on wire as `apiextensions.k8s.io/v1`
  - Conversion functions between internal ↔ v1 registered in scheme

**Scheme Registration** (`register.go`):
```go
SchemeGroupVersion = schema.GroupVersion{Group: "apiextensions.k8s.io", Version: runtime.APIVersionInternal}
SchemeBuilder.AddToScheme() // Registers CRD types in scheme
```
This allows the Scheme to:
1. Decode `apiextensions.k8s.io/v1.CustomResourceDefinition` YAML/JSON → internal Hub struct → Go object
2. Encode Go objects → internal Hub struct → wire format
3. Convert between versions if multiple exist

---

### 3. Server-Side Lifecycle: Request → Validation → Storage → Etcd

**HTTP Handler Entry Point** (`customresource_handler.go`):
```go
type crdHandler struct {
    versionDiscoveryHandler *versionDiscoveryHandler
    groupDiscoveryHandler   *groupDiscoveryHandler
    customStorageLock       sync.Mutex
    customStorage           atomic.Value  // crdStorageMap
    crdLister               listers.CustomResourceDefinitionLister
    delegate                http.Handler
    restOptionsGetter       generic.RESTOptionsGetter
}
```
- Acts as filter for `/apis` endpoint
- Routes requests to custom resource handlers based on GVR

**Validation** (`apiserver/validation/`):
- OpenAPI schema validation using JSONSchema
- Structural pruning: removes fields not in CRD spec
- Managed fields tracking

**Storage Layer** (`registry/customresource/etcd.go`):
```go
type CustomResourceStorage struct {
    CustomResource *REST
    Status         *StatusREST
    Scale          *ScaleREST
}

// NewStorage creates generic registry.Store with Unstructured
store := &genericregistry.Store{
    NewFunc: func() runtime.Object {
        ret := &unstructured.Unstructured{}
        ret.SetGroupVersionKind(kind)
        return ret
    },
    CreateStrategy: strategy,
    UpdateStrategy: strategy,
    DeleteStrategy: strategy,
}
```
- Uses `unstructured.Unstructured` for all CRD instances
- No Go struct needed—Unstructured is "structurally typed" via JSONPath
- Etcd stores JSON; Unstructured wraps it in `map[string]interface{}`
- Strategies handle validation, conflict detection, field updates

**Serialization Bridge:**
- TypeMeta + ObjectMeta embedded in Unstructured.Object map
- When stored: `Unstructured` → JSON → etcd
- When fetched: etcd JSON → `Unstructured` → REST response

---

### 4. Client-Side Lifecycle: Discovery → Watch → Cache → Lister

**Dynamic Client** (`dynamic/simple.go`):
```go
type DynamicClient struct {
    client rest.Interface
}

func (c *dynamicResourceClient) Create(ctx context.Context,
    obj *unstructured.Unstructured, ...) (*unstructured.Unstructured, error)
```
- Takes `schema.GroupVersionResource` → constructs URL path
- Works with `unstructured.Unstructured` (no typed client)
- REST operations: Get, List, Watch, Create, Update, Delete, Patch
- Handles `Unstructured` ↔ JSON encoding/decoding

**Informer (Watch & Cache)** (`dynamic/dynamicinformer/informer.go`):
```go
type DynamicSharedInformerFactory interface {
    ForResource(gvr schema.GroupVersionResource) informers.GenericInformer
}

type dynamicSharedInformerFactory struct {
    client        dynamic.Interface
    informers     map[schema.GroupVersionResource]informers.GenericInformer
    startedInformers map[schema.GroupVersionResource]bool
}

// NewFilteredDynamicInformer constructs informer using:
cache.NewSharedIndexInformerWithOptions(
    client.Resource(gvr).Watch(...),  // Uses DynamicClient to watch
    cache.Indexers{cache.NamespaceIndex: cache.MetaNamespaceIndexFunc},
)
```
- Factory creates informers per GVR
- Each informer watches API server: `client.Resource(gvr).Watch()`
- Updates go to `SharedIndexInformer` → local cache (in-memory)
- Indexer allows fast lookups: by namespace, by name, custom predicates

**Lister (Cache Query)** (`dynamic/dynamiclister/lister.go`):
```go
type dynamicLister struct {
    indexer cache.Indexer
    gvr     schema.GroupVersionResource
}

func (l *dynamicLister) List(selector labels.Selector) ([]*unstructured.Unstructured, error) {
    cache.ListAll(l.indexer, selector, func(m interface{}) {
        ret = append(ret, m.(*unstructured.Unstructured))
    })
}

func (l *dynamicLister) Get(name string) (*unstructured.Unstructured, error) {
    obj, exists, err := l.indexer.GetByKey(name)  // O(1) local lookup
    return obj.(*unstructured.Unstructured), nil
}
```
- Queries the in-memory indexer (no API calls)
- Returns `Unstructured` for any GVR
- Namespace-scoped and cluster-scoped aware

---

## Architectural Analysis

### Cross-Project Integration

**How the Four Projects Work Together:**

1. **apimachinery** provides the protocol:
   - All K8s objects inherit TypeMeta/ObjectMeta (metadata protocol)
   - Scheme is the central type registry
   - GVK/GVR are the coordinate system
   - Unstructured enables "schema-free" objects

2. **apiextensions-apiserver** uses apimachinery to define CRD type itself:
   - CustomResourceDefinition is just another Kubernetes object (uses TypeMeta, ObjectMeta)
   - Registered in Scheme like any other type
   - BUT: the *instances* of a CRD (what users create) are stored as Unstructured

3. **apiextensions-apiserver** storage layer:
   - HTTP handler receives requests for CRD instances
   - Validation: JSON schema check against CRD spec
   - Storage: wraps instance JSON in Unstructured, stores in etcd
   - Response: Unstructured → JSON → client

4. **client-go** provides generic access:
   - DynamicClient: Takes GVR, sends REST requests (no code generation)
   - DynamicInformer: Watches any GVR via DynamicClient, caches as Unstructured
   - DynamicLister: Queries cache (same pattern as typed listers)

### The Scheme: Binding Layer

The **Scheme** is the critical checkpoint between server and client:

**Server side:**
- Scheme decodes incoming YAML/JSON using GVK information
- If type is registered (built-in like Pod) → uses Go struct
- If type is NOT registered (CRD instance) → falls through to Unstructured
- Unstructured validation happens in apiextensions handler, not Scheme

**Client side:**
- Typed client: generated code uses Scheme to decode responses → typed structs
- Dynamic client: Scheme not used; decoding is hardcoded to Unstructured via `unstructured.UnstructuredJSONScheme`

### Why Unstructured is the CRD Solution

**Problem:** CRDs are user-defined; server can't pre-generate Go structs
**Solution:** Unstructured = `map[string]interface{}`
- No struct needed; purely schema-free
- Implements `runtime.Object` → can be stored, serialized, cached
- Schema validation happens in apiextensions handler, not codec layer
- Works with any tool that speaks the K8s Object interface (informers, listers, etc.)

### Data Flow: From Write to Read

**Write Path (Client → etcd):**
1. Client creates `Unstructured` object with `apiVersion`, `kind`, `metadata`, custom fields
2. DynamicClient.Create() → encodes to JSON
3. HTTP POST to `/apis/GROUP/VERSION/RESOURCE` (custom_resource_handler.go)
4. crdHandler routes to customResourceDefinition-specific handler
5. Validation: JSON schema check against CRD spec
6. Storage strategy: Validation, conflict resolution, managed fields
7. GenericStore wraps JSON in `Unstructured`, stores in etcd as JSON

**Read Path (etcd → Client Informer):**
1. Client creates DynamicSharedInformerFactory for a GVR
2. Informer watches `client.Resource(gvr).Watch()`
3. DynamicClient.Watch() → HTTP GET with ?watch=true
4. Server streams events (ADDED, MODIFIED, DELETED)
5. Informer receives events → caches each object as Unstructured
6. Lister queries cache: O(1) by key, O(n) with label selector
7. Application calls `lister.Get(name)` → returns Unstructured

---

## Cross-Project Dependency Visualization

```
                         apimachinery (Foundation)
                         ├─ Scheme: GVK↔Type registry
                         ├─ TypeMeta/ObjectMeta: metadata protocol
                         ├─ GVK/GVR: coordinate system
                         └─ Unstructured: schema-free object
                                  ↑
                    ┌─────────────┼─────────────┐
                    ↓             ↓             ↓
            apiextensions-apiserver   client-go    (api)
             (Server/Storage)         (Client)     (Type defs)
            ┌──────────────────┐    ┌──────────┐   ┌─────────┐
            │ CRD Definition   │    │ Dynamic  │   │ Built-in│
            │ (TypeMeta+Spec)  │    │ Client   │   │ Types   │
            ├──────────────────┤    ├──────────┤   └─────────┘
            │ HTTP Handler     │    │ Informer │
            │ (customresource) │    │ (Watch+  │
            ├──────────────────┤    │  Cache)  │
            │ Validation       │    ├──────────┤
            │ (JSON Schema)    │    │ Lister   │
            ├──────────────────┤    │ (Query   │
            │ Storage (etcd)   │←→→ │  Cache)  │
            │ (Unstructured)   │    └──────────┘
            └──────────────────┘
```

---

## Summary

The CRD lifecycle is a masterpiece of separation of concerns:

1. **apimachinery** provides the universal object model (TypeMeta, Scheme, GVK, Unstructured) that enables schema-independent type handling.

2. **apiextensions-apiserver** implements the CRD concept: it stores CRD *definitions* (which are normal K8s objects) and uses their schemas to validate and store CRD *instances* as Unstructured JSON.

3. **client-go** provides generic watch/cache/lister for any GVR via the Dynamic client family, reusing the same informer/lister patterns as typed clients but with Unstructured.

4. **api** holds built-in type definitions; CRDs extend this without code generation.

The checkpoint between server and client is the **Scheme and Unstructured**: on the server, validation is explicit (JSON schema in apiextensions); on the client, it's implicit (tools consume Unstructured generically). This enables users to define new resources at runtime without recompiling the apiserver—a key feature of Kubernetes extensibility.
