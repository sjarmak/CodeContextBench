# Kubernetes CRD Lifecycle: Cross-Repo Architectural Analysis

## Files Examined

### **Apimachinery (Foundation Layer)**
- `staging/src/k8s.io/apimachinery/pkg/runtime/scheme.go` — Core Scheme implementation mapping GVK↔Type, registry for serialization
- `staging/src/k8s.io/apimachinery/pkg/runtime/types.go` — TypeMeta definition (APIVersion, Kind)
- `staging/src/k8s.io/apimachinery/pkg/runtime/schema/group_version.go` — GroupVersionKind and GroupVersionResource definitions
- `staging/src/k8s.io/apimachinery/pkg/apis/meta/v1/types.go` — ObjectMeta, ListMeta, TypeMeta
- `staging/src/k8s.io/apimachinery/pkg/apis/meta/v1/unstructured/unstructured.go` — Unstructured generic object representation
- `staging/src/k8s.io/apimachinery/pkg/apis/meta/v1/unstructured/unstructured_list.go` — UnstructuredList for collection serialization

### **Apiextensions-apiserver (Server-side CRD)**
- `staging/src/k8s.io/apiextensions-apiserver/pkg/apis/apiextensions/types.go` — Internal hub CustomResourceDefinitionSpec type
- `staging/src/k8s.io/apiextensions-apiserver/pkg/apis/apiextensions/register.go` — Hub type registration (internal version)
- `staging/src/k8s.io/apiextensions-apiserver/pkg/apis/apiextensions/v1/types.go` — External v1 CRD type definition
- `staging/src/k8s.io/apiextensions-apiserver/pkg/apis/apiextensions/v1/register.go` — v1 type registration and Scheme builder
- `staging/src/k8s.io/apiextensions-apiserver/pkg/apis/apiextensions/v1beta1/types.go` — Legacy v1beta1 CRD type
- `staging/src/k8s.io/apiextensions-apiserver/pkg/apis/apiextensions/install/install.go` — Unified Scheme registration for all CRD versions
- `staging/src/k8s.io/apiextensions-apiserver/pkg/apiserver/validation/` — Schema validation during create/update
- `staging/src/k8s.io/apiextensions-apiserver/pkg/registry/customresource/strategy.go` — Custom resource validation and conversion strategy
- `staging/src/k8s.io/apiextensions-apiserver/pkg/registry/customresource/etcd.go` — Etcd storage backend with unstructured.Unstructured
- `staging/src/k8s.io/apiextensions-apiserver/pkg/apiserver/customresource_handler.go` — Dynamic HTTP handler for CR Create/Read/Update/Delete/List/Watch
- `staging/src/k8s.io/apiextensions-apiserver/pkg/crdserverscheme/unstructured.go` — UnstructuredObjectTyper for dynamic GVK resolution
- `staging/src/k8s.io/apiextensions-apiserver/pkg/apiserver/apiserver.go` — APIServer initialization and Scheme setup

### **Client-go (Client-side Access)**
- `staging/src/k8s.io/client-go/dynamic/interface.go` — Dynamic client interface (Resource, Create, Update, Delete, List, Watch)
- `staging/src/k8s.io/client-go/dynamic/simple.go` — DynamicClient implementation using REST interface
- `staging/src/k8s.io/client-go/dynamic/scheme.go` — Serialization schemes for dynamic clients (watch, delete, parameter codecs)
- `staging/src/k8s.io/client-go/dynamic/dynamicinformer/informer.go` — DynamicSharedInformerFactory for watching/caching resources
- `staging/src/k8s.io/client-go/dynamic/dynamiclister/lister.go` — DynamicLister for querying cached resources
- `staging/src/k8s.io/client-go/informers/generic.go` — GenericInformer factory for all resource types
- `staging/src/k8s.io/client-go/informers/internalinterfaces/factory_interfaces.go` — SharedInformerFactory interface

### **API (Hub Types)**
- `staging/src/k8s.io/api/core/v1/types.go` — Core API types (Pod, Service, Volume, etc.) that CRDs must align with

---

## Dependency Chain

### **Layer 1: Foundation — Apimachinery**

The foundation of the entire CRD system rests on apimachinery's runtime package:

1. **Scheme** (`runtime.Scheme`)
   - Bidirectional mappings: `gvkToType map[schema.GroupVersionKind]reflect.Type` and `typeToGVK map[reflect.Type][]schema.GroupVersionKind`
   - Enables serialization/deserialization by mapping Go types to API group/version/kind
   - Conversion functions registered for versioned API objects
   - **Critical**: CRDs don't register themselves in the Scheme—they use Unstructured

2. **GroupVersionKind (GVK) and GroupVersionResource (GVR)**
   - GVK: Triple {Group, Version, Kind} uniquely identifying object types (e.g., "deployment.apps/v1/Deployment")
   - GVR: Triple {Group, Version, Resource} for REST endpoints (e.g., "deployment.apps/v1/deployments")
   - Conversion: GVK→GVR (Kind→Resource), GVR→GVK (Resource→Kind)
   - Used for routing HTTP requests and identifying resource types

3. **TypeMeta and ObjectMeta**
   - **TypeMeta**: Contains `APIVersion` and `Kind` fields (stored in JSON)
   - **ObjectMeta**: Contains metadata like `Name`, `Namespace`, `Labels`, `Annotations`, `ResourceVersion` (for optimistic locking)
   - Embedded in all Kubernetes objects (both built-in and custom)
   - CRDs inherit the same TypeMeta/ObjectMeta structure

4. **Unstructured**
   - Generic map[string]interface{} representation for objects without registered Go types
   - Implements `runtime.Object` and `runtime.Unstructured` interfaces
   - Provides metadata accessors (GetName, GetNamespace, GetLabels, etc.)
   - **Key insight**: Unstructured is how CRs are stored and transmitted without needing compiled Go types

---

### **Layer 2: Server-side Type Definitions & Registration — Apiextensions-apiserver**

The apiextensions-apiserver defines and manages CustomResourceDefinition (CRD) types:

1. **Internal Hub Type** (`apiextensions/types.go`)
   - `CustomResourceDefinition` struct with internal version (apiVersion: "apiextensions")
   - Hub version for conversion between external versions
   - Contains spec: `CustomResourceDefinitionSpec` defining the CR schema

2. **External v1 Type** (`apiextensions/v1/types.go`)
   - User-facing versioned CRD type (apiVersion: "apiextensions.k8s.io/v1")
   - Generated from hub through conversion functions
   - Includes JSONSchema validation, subresources (status, scale), storage versions

3. **v1beta1 Type** (`apiextensions/v1beta1/types.go`)
   - Legacy version for backward compatibility
   - Same structure but marked as deprecated

4. **Scheme Registration** (`apiextensions/register.go`, `v1/register.go`, `install/install.go`)
   - Hub version: `addKnownTypes(scheme)` registers `CustomResourceDefinition` and `CustomResourceDefinitionList`
   - v1 version: `addKnownTypes(scheme)` and `metav1.AddToGroupVersion(scheme, SchemeGroupVersion)`
   - Conversion functions registered for v1 ↔ hub transformations
   - Install pattern: `Install(scheme)` registers all versions and sets version priority

5. **Checkpoint**: After registration, CRD types are in the Scheme, but **custom resources themselves are not**

---

### **Layer 3: Server-side Lifecycle — Apiextensions-apiserver**

#### **3a. Validation**
- `apiserver/validation/` validates incoming CR requests against the CRD's OpenAPI schema
- `registry/customresource/strategy.go` contains `customResourceStrategy` implementing validation
- Schema validation, defaulting, pruning, and CEL validation rules applied

#### **3b. Etcd Storage**
- `registry/customresource/etcd.go` defines `CustomResourceStorage`
- Creates `*genericregistry.Store` with:
  - `NewFunc()` returns `&unstructured.Unstructured{}` (no compiled type)
  - `NewListFunc()` returns `&unstructured.UnstructuredList{}`
  - Pre-allocates GVK on new objects for versioning decoder
- **Critical**: CRs stored as Unstructured in etcd—schema comes from CRD, not Go types

#### **3c. Dynamic HTTP Handler**
- `apiserver/customresource_handler.go` implements the main CRD request router
- `crdHandler` struct holds:
  - `customStorage atomic.Value` maps GVK→storage per CRD
  - `crdLister` watches CRD changes to hot-reload schemas
- Request flow:
  1. HTTP request arrives (e.g., POST /apis/example.com/v1/namespaces/default/widgets)
  2. Handler extracts GVR from URL
  3. Looks up CRD by GVR
  4. Retrieves `CustomResourceStorage` for that GVR
  5. Delegates to generic storage REST handler
- Handles versioning, conversion, validation middleware
- Unstructured representation flows through—no type assertion needed

#### **3d. Scheme Setup in APIServer**
- `apiserver/apiserver.go` creates `var Scheme = runtime.NewScheme()` and `Codecs = serializer.NewCodecFactory(Scheme)`
- Registers standard Kubernetes types and CRD types
- `crdserverscheme/unstructured.go` provides `UnstructuredObjectTyper` for dynamic typing
- Serializers (JSON, Protobuf) handle Unstructured encoding/decoding

---

### **Layer 4: Client-side Access — Client-go**

#### **4a. Dynamic Client**
- `dynamic/interface.go` defines `Interface` with `Resource(schema.GroupVersionResource)` method
- Returns `NamespaceableResourceInterface` supporting CRUD operations on Unstructured objects
- `dynamic/simple.go` implements `DynamicClient`:
  - Uses REST client with `ConfigFor()` setting JSON serialization
  - No type registration needed—all objects treated as Unstructured
  - Methods: `Create()`, `Update()`, `Delete()`, `List()`, `Watch()` returning Unstructured

#### **4b. Scheme for Serialization**
- `dynamic/scheme.go` creates minimal schemes for watch, delete, parameter encoding
- Uses `unstructuredCreater` and `unstructuredTyper` for Unstructured-aware serialization
- Always returns Unstructured—no typed client needed

#### **4c. SharedIndexInformer (Caching)**
- `dynamic/dynamicinformer/informer.go` provides `DynamicSharedInformerFactory`
- Creates `NewFilteredDynamicSharedInformerFactory()` for watching resources by GVR
- Behind the scenes:
  1. Calls `DynamicClient.Watch()` to stream events
  2. Stores Unstructured objects in `cache.Indexer` (in-memory cache)
  3. Syncs periodically via resync interval
- **Checkpoint**: This is where etcd data meets client-side state management

#### **4d. Lister (Cached Query)**
- `dynamic/dynamiclister/lister.go` provides `Lister` interface
- `dynamicLister` wraps the `cache.Indexer` from informer
- Methods: `List(selector)`, `Get(name)`, `NamespaceLister(namespace)`
- Returns Unstructured objects from local cache (no API call)
- Low-latency reads from informer's in-memory cache

---

## Analysis

### **How the Four Sub-Projects Integrate**

1. **Apimachinery as Foundation**
   - Every object in Kubernetes contains TypeMeta (from runtime) and ObjectMeta (from metav1)
   - Scheme is the central registry for all type→serialization mappings
   - Unstructured solves the chicken-egg problem: types can't be compiled into client-go, but we need to serialize/deserialize them
   - GroupVersionKind provides the address space for distinguishing any object type

2. **Apiextensions-apiserver: Bridge Between Definition and Runtime**
   - CRD types are themselves Kubernetes objects (registered in Scheme)
   - Each CRD defines a new Kind (e.g., "Widget") that lives in the apiextensions system
   - Custom Resources (instances of the CRD) are **not** pre-registered—they're validated against the CRD schema at runtime
   - The customresource_handler acts as a universal interpreter:
     - Reads incoming Unstructured JSON
     - Validates against CRD's JSONSchema (apiserver/validation)
     - Converts to internal representation if needed (apiextensions/conversion)
     - Stores as Unstructured in etcd (registry/customresource/etcd.go)
   - crdserverscheme/UnstructuredObjectTyper extracts GVK from the object itself (TypeMeta fields), not from registered types

3. **Client-go: Type-Agnostic Access Layer**
   - The dynamic client deliberately avoids the Scheme's type registry
   - Uses minimal serializer schemes (scheme.go) that only handle basic Kubernetes types (TypeMeta, ListMeta)
   - All CR objects flow through as Unstructured maps
   - Informers cache by GroupVersionResource (not registered types)
   - Listers query from cache—no type assertion needed
   - Example workflow:
     ```
     client.Resource(gvr).Namespace("default").Create(ctx, unstructuredObj, ...)
     // gvr = schema.GroupVersionResource{Group: "example.com", Version: "v1", Resource: "widgets"}
     // unstructuredObj = &unstructured.Unstructured{Object: map[string]interface{}{...}}
     ```

4. **API Hub Types: What CRDs Must Respect**
   - Core types like ObjectMeta provide the common vocabulary
   - CRDs don't inherit from core types but must conform to the same metadata structure
   - All CRs must have TypeMeta (APIVersion, Kind) and ObjectMeta (Name, Namespace, etc.)
   - Subresources (status, scale) inherit patterns from built-in resources

### **Cross-Project Data Flow: CRD Lifecycle**

**User defines a CRD:**
```yaml
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: widgets.example.com
spec:
  group: example.com
  names:
    kind: Widget
    resource: widgets
  scope: Namespaced
  versions:
  - name: v1
    schema:
      openAPIV3Schema:
        type: object
        properties:
          spec: {...}
```

**Flow through the system:**

1. **API Server → Apiextensions-apiserver**
   - Incoming CRD POST request hits apiserver
   - Routed to apiextensions-apiserver (registered API)
   - CRD type resolution: Scheme knows "apiextensions.k8s.io/v1/CustomResourceDefinition"
   - Validated against CRD schema (itself defined by Kubernetes)
   - Stored in etcd

2. **Apiextensions-apiserver → Dynamic Handler**
   - `customresource_handler` watches CRDs via informer
   - On new CRD: creates `CustomResourceStorage` for that GVR
   - Storage registers validators from CRD schema
   - Now accepts requests like `/apis/example.com/v1/widgets`

3. **User creates a Custom Resource:**
   ```yaml
   apiVersion: example.com/v1
   kind: Widget
   metadata:
     name: my-widget
   spec:
     color: blue
   ```

4. **HTTP Request → Validation → Storage**
   - POST `/apis/example.com/v1/namespaces/default/widgets`
   - customresource_handler routes by GVR {example.com, v1, widgets}
   - Looks up CRD → retrieves schema + validation rules
   - Validates incoming JSON against schema (apiservervalidation)
   - Creates `Unstructured{Object: {...}}` in etcd via `registry/customresource/etcd.go`
   - **Key point**: No compiled Go type exists for Widget

5. **Client-go Access**
   ```go
   // Get dynamic client
   dc, _ := dynamic.NewForConfig(config)
   gvr := schema.GroupVersionResource{
       Group: "example.com", Version: "v1", Resource: "widgets",
   }

   // Fetch widget
   widget, _ := dc.Resource(gvr).Namespace("default").Get(ctx, "my-widget", metav1.GetOptions{})
   // widget is *unstructured.Unstructured

   // Query from cache (if using informers)
   informerFactory := dynamicinformer.NewDynamicSharedInformerFactory(dc, 30*time.Second)
   informer := informerFactory.ForResource(gvr)
   lister := dynamiclister.New(informer.GetIndexer(), gvr)

   // Get from cache (no API call)
   cachedWidget, _ := lister.Namespace("default").Get("my-widget")
   ```

### **The Critical Checkpoint: Scheme vs. Unstructured**

| Aspect | Built-in Resources | Custom Resources |
|--------|---|---|
| **Type Registration** | Pre-compiled Go types in Scheme | Not in Scheme—discovered at runtime |
| **Serialization** | Typed serializer (e.g., `&v1.Pod{}`) | Unstructured serializer (map-based) |
| **Validation** | Compiled type + validation code | CRD schema + JSONSchema validator |
| **Client Access** | Typed clientset (e.g., `podsClient.Create(&pod)`) | Dynamic client (always `*unstructured.Unstructured`) |
| **Caching** | Informers[T] generic over type | DynamicInformer keyed by GVR |

**Why Unstructured?**
- CRD schemas are user-defined—can't pre-compile types
- Schema changes at runtime—need flexibility
- Multiple versions of same CR coexist—versioning decoder handles conversion
- Enables zero-dependency custom resources—no need for generated client code

### **Scheme Role Across Projects**

1. **Apimachinery Scheme**: Core registry
   - Maps GVK ↔ Go Type for anything with compiled representation
   - Used by apiserver for built-in types
   - Not used for CRs (they're dynamic)

2. **Apiextensions-apiserver Scheme**: CRD type registry
   - Registers CustomResourceDefinition itself
   - Does NOT register individual CRs
   - crdserverscheme provides Unstructured typing for CRs

3. **Client-go Scheme**: Minimal for dynamics
   - dynamic/scheme.go only includes basic types for protocol handling
   - Unstructured objects bypass the Scheme entirely
   - Informers work with GVR keys, not registered types

---

## Summary

The Kubernetes CRD lifecycle spans four integrated sub-projects: **apimachinery** provides the foundational type system (Scheme, GVK, TypeMeta, ObjectMeta, Unstructured), **apiextensions-apiserver** defines and validates CRDs and routes custom resource requests through a universal dynamic HTTP handler storing Unstructured objects in etcd, **client-go** exposes type-agnostic dynamic clients that work with any GVR and cache resources via informers and listers without requiring type registration, and **api** provides the hub types that all resources (built-in and custom) must conform to. The key innovation is **Unstructured**: it decouples object definition (CRD schema) from type definition (compiled Go), allowing CRDs to be created and accessed without pre-compiled code, making Kubernetes infinitely extensible. The checkpoint between server and client occurs at the **etcd boundary**: the server validates and stores Unstructured objects according to CRD schemas, and the client retrieves and caches them without ever touching the Scheme's type registry.

