# Terraform Plan/Apply Pipeline Architecture

## Q1: Command to Context

### Overview
The CLI plan command delegates to the backend, which creates and invokes the Terraform context's Plan() method. The execution flow is:
1. **PlanCommand.Run()** (internal/command/plan.go:22-118)
2. Delegates to **backend.RunOperation()** with operation request
3. Backend calls **Context.Plan()** (internal/terraform/context_plan.go:155-158)

### Key Components

#### PlanCommand.Run() - CLI Entry Point
Located in `internal/command/plan.go:22-118`:
- Parses command-line flags and arguments
- Calls `c.PrepareBackend()` to load the backend
- Builds operation request with `c.OperationRequest()`
- Calls `c.RunOperation(be, opReq)` to delegate to backend

#### OperationRequest Construction
In `internal/command/plan.go:145-190`, the operation request is built with:
- **Type**: `backendrun.OperationTypePlan`
- **PlanMode**: Normal, Destroy, or RefreshOnly (from args.PlanMode)
- **PlanRefresh**: Whether to refresh state (from args.Refresh)
- **Targets**: Resource targeting addresses (args.Targets)
- **ForceReplace**: Resources to force replacement (args.ForceReplace)
- **Hooks**: Plan view hooks for visualization
- **DeferralAllowed**: Experimental deferral support flag

#### Context.Plan() Method
In `internal/terraform/context_plan.go:155-158`:
```go
func (c *Context) Plan(config *configs.Config, prevRunState *states.State, opts *PlanOpts) (*plans.Plan, tfdiags.Diagnostics)
```
- Delegates to **PlanAndEval()** (internal/terraform/context_plan.go:169-372)

#### Context.PlanAndEval() - Core Planning
In `internal/terraform/context_plan.go:169-372`:
- Validates and normalizes inputs
- Checks external provider configurations
- Routes to operation-specific plan methods based on `opts.Mode`:
  - `plans.NormalMode` → `c.plan()`
  - `plans.DestroyMode` → `c.destroyPlan()`
  - `plans.RefreshOnlyMode` → `c.refreshOnlyPlan()`
- All routes call **c.planWalk()** to perform the actual planning

### PlanOpts Structure
In `internal/terraform/context_plan.go:30-138`, key fields controlling plan behavior:

| Field | Purpose |
|-------|---------|
| `Mode` | Planning mode (Normal/Destroy/RefreshOnly) |
| `SkipRefresh` | Skip refreshing managed resources |
| `Targets` | Resource instances to limit planning to |
| `ForceReplace` | Resource instances to force replacement |
| `DeferralAllowed` | Allow deferred changes for external dependencies |
| `SetVariables` | Root module input variable values |
| `ExternalProviders` | Pre-configured provider instances from caller |
| `Forget` | Forget all resources (destroy mode only) |
| `ExternalReferences` | References to preserve during graph pruning |

---

## Q2: Graph Construction Pipeline

### Overview
The graph construction pipeline transforms a flat configuration into a directed acyclic graph (DAG) of resource instances with proper dependency ordering. The pipeline is orchestrated by **PlanGraphBuilder**.

### PlanGraphBuilder.Build() and Steps()
In `internal/terraform/graph_builder_plan.go:112-277`:

```go
func (b *PlanGraphBuilder) Build(path addrs.ModuleInstance) (*Graph, tfdiags.Diagnostics) {
    return (&BasicGraphBuilder{
        Steps: b.Steps(),
        Name:  "PlanGraphBuilder",
    }).Build(path)
}

func (b *PlanGraphBuilder) Steps() []GraphTransformer
```

#### Sequence of Graph Transformers
The `Steps()` method returns an ordered list of transformers that progressively build the graph:

### Phase 1: Core Node Creation
**Lines 137-146**: Foundational node creation
- **ConfigTransformer** (line 137-146): Creates resource nodes from configuration
  - Adds all managed, data, and ephemeral resources
  - Handles import targets with config generation capability
  - File: `internal/terraform/transform_config.go`

**Lines 149-176**: Variable and output nodes
- **RootVariableTransformer**: Adds root module input variable nodes
- **ModuleVariableTransformer**: Adds module variable nodes
- **variableValidationTransformer**: Adds validation nodes for variables
- **LocalTransformer**: Adds local value nodes
- **OutputTransformer**: Adds output value nodes

### Phase 2: State and Configuration Attachment
**Lines 185-215**: Attaching state and configuration to nodes

- **OrphanResourceInstanceTransformer** (line 186-191): Adds orphan resource nodes (state-only)
- **StateTransformer** (line 198-202): Attaches deposed and state-only instances
  - File: `internal/terraform/transform_state.go`

- **AttachStateTransformer** (line 205): Attaches prior state objects to resource instances
  - Location: `internal/terraform/transform_attach_state.go:29-71`
  - Matches state resources to graph nodes by address
  - Copies state from sync wrapper to individual instance nodes

- **OrphanOutputTransformer**: Removes output nodes no longer in configuration
- **AttachResourceConfigTransformer**: Links configuration to resource nodes

### Phase 3: Provider Setup
**Lines 218-225**: Provider initialization and schema attachment

- **transformProviders()** (line 218): Multi-step provider transformer
  - Handles external provider configs
  - Creates provider config nodes from configuration
  - Adds missing provider nodes
  - Connects resources to providers
  - Prunes unused providers
  - File: `internal/terraform/transform_provider.go:18-41`

- **AttachSchemaTransformer** (line 225): Attaches provider schemas to nodes
  - Required before reference analysis for type validation

### Phase 4: Module Expansion and References
**Lines 227-243**: Module expansion and dependency analysis

- **ModuleExpansionTransformer** (line 230): Creates module expansion nodes
- **ExternalReferenceTransformer** (line 233-235): Preserves external references
- **ReferenceTransformer** (line 237): **Core dependency edge creation**

### ReferenceTransformer: Dependency Edge Analysis
Location: `internal/terraform/transform_reference.go:108-156`

**Purpose**: Analyzes references in expressions and creates directed graph edges

**How it Works** (lines 112-156):
```go
func (t *ReferenceTransformer) Transform(g *Graph) error {
    vs := g.Vertices()
    m := NewReferenceMap(vs)  // Build reference lookup map

    for _, v := range vs {
        // For each node, find what it references
        parents := m.References(v)  // Nodes that v depends on

        // Create edges from v to parents
        for _, parent := range parents {
            g.Connect(dag.BasicEdge(v, parent))
        }
    }
}
```

**Key Reference Types**:
1. **GraphNodeReferencer**: Implements References() to declare what addresses it references
2. **GraphNodeReferenceable**: Implements ReferenceableAddrs() to declare what it can be referenced as
3. Reference resolution uses langrefs package to parse HCL expressions

**Example Dependencies**:
- Resource B referencing resource A's output creates edge: B → A
- Data source referencing resource attribute creates edge: datasource → resource
- Module variable referencing resource creates edge: module_var → resource

### AttachStateTransformer: State Association
Location: `internal/terraform/transform_attach_state.go:29-71`

**Purpose**: Associates stored state with resource instance nodes for refresh/plan

**Mechanism** (lines 35-71):
1. Iterates over all graph vertices
2. For nodes implementing GraphNodeAttachResourceState interface
3. Looks up corresponding state in sync.State by resource address
4. Attaches deep copy of state to node
5. Enables nodes to access prior values during planning

### Phase 5: Validation and Ordering
**Lines 239-273**: Dependency edge refinement and validation

- **AttachDependenciesTransformer** (line 239): Records all dependencies for state
- **attachDataResourceDependsOnTransformer**: Handles depends_on for data resources
- **DestroyEdgeTransformer** (line 247-249): Adds destroy dependency edges
- **pruneUnusedNodesTransformer**: Removes unreferenced nodes
- **TargetsTransformer** (line 256): Filters graph to targeted resources
- **ForcedCBDTransformer** (line 260): Handles create_before_destroy requirements
- **ephemeralResourceCloseTransformer**: Closes ephemeral resources
- **CloseProviderTransformer** (line 266): Adds provider close nodes
- **CloseRootModuleTransformer**: Closes root module context
- **TransitiveReductionTransformer** (line 273): Removes redundant edges for clarity

### Complete Graph Transformer Pipeline for Normal Plan
```
ConfigTransformer
  ↓
RootVariableTransformer
ModuleVariableTransformer
variableValidationTransformer
LocalTransformer
OutputTransformer
checkTransformer
  ↓
OrphanResourceInstanceTransformer
StateTransformer
AttachStateTransformer
OrphanOutputTransformer
AttachResourceConfigTransformer
  ↓
transformProviders (5 sub-transformers)
RemovedModuleTransformer
AttachSchemaTransformer
  ↓
ModuleExpansionTransformer
ExternalReferenceTransformer
ReferenceTransformer ← Adds dependency edges
AttachDependenciesTransformer
attachDataResourceDependsOnTransformer
  ↓
DestroyEdgeTransformer
pruneUnusedNodesTransformer
TargetsTransformer
ForcedCBDTransformer
ephemeralResourceCloseTransformer
CloseProviderTransformer
CloseRootModuleTransformer
TransitiveReductionTransformer
```

---

## Q3: Provider Resolution and Configuration

### Overview
Providers are resolved by the graph builder, initialized during graph walk via EvalContext methods, and configured with provider configuration blocks before resources access them.

### Provider Resolution - ProviderTransformer
Location: `internal/terraform/transform_provider.go:90-249`

**Process** (lines 97-249):
1. Collects provider requests from all GraphNodeProviderConsumer nodes
2. For each request:
   - Resolves provider address considering provider inheritance
   - Maps to actual provider configuration in module hierarchy
   - Creates edges from resources to provider nodes
3. Provider configuration addresses follow inheritance chain up to root module

**Provider Inheritance Mechanism** (lines 189-201):
- Resources specify providers via local addresses
- Transformer resolves to absolute provider configuration in ancestor modules
- If no provider found at current level, walks up module path
- Respects provider aliases for multiple provider instances

### Provider Initialization via EvalContext

#### InitProvider() Method
Location: `internal/terraform/eval_context_builtin.go:138-186`

**Signature**:
```go
func (ctx *BuiltinEvalContext) InitProvider(
    addr addrs.AbsProviderConfig,
    config *configs.Provider,
) (providers.Interface, error)
```

**Execution Flow**:
1. **Cache Check** (line 140): Return error if provider already initialized
2. **Lock Acquisition** (line 146): Thread-safe provider cache access
3. **External Provider Check** (lines 151-163):
   - If provider is externally-configured (root module only)
   - Wrap in externalProviderWrapper (no-op on configure/close)
   - Store in cache and return
4. **Plugin Instance Creation** (line 166):
   - `ctx.Plugins.NewProviderInstance(addr.Provider)` instantiates provider plugin
   - Plugin communication via gRPC protocol
5. **Mock Provider Wrapping** (lines 175-181):
   - If provider config specifies Mock: true
   - Wrap provider in mocking provider (for testing)
6. **Cache Storage** (line 183): Store provider in ProviderCache
7. **Return** (line 185): Return initialized provider interface

**Key Points**:
- Only initializes, does not configure
- Caches provider for reuse
- Lazy-loaded on first reference
- Respects external pre-configured providers

### Provider Configuration via EvalContext

#### ConfigureProvider() Method
Location: `internal/terraform/eval_context_builtin.go:213-237`

**Signature**:
```go
func (ctx *BuiltinEvalContext) ConfigureProvider(
    addr addrs.AbsProviderConfig,
    cfg cty.Value,
) tfdiags.Diagnostics
```

**Execution Flow**:
1. **Validation** (line 215): Assert provider is in correct module
2. **Retrieval** (line 221): Get cached provider instance
3. **Request Creation** (lines 227-233):
   ```go
   req := providers.ConfigureProviderRequest{
       TerraformVersion: version.String(),
       Config:           cfg,
       ClientCapabilities: providers.ClientCapabilities{
           DeferralAllowed: ctx.Deferrals().DeferralAllowed(),
       },
   }
   ```
4. **Provider RPC Call** (line 235): `provider.ConfigureProvider(req)`
5. **Return Diagnostics** (line 236): Return provider's response diagnostics

#### NodeApplyableProvider.ConfigureProvider()
Location: `internal/terraform/node_provider.go:103-190`

**High-Level Flow**:
1. **Build Provider Config** (line 106): Construct HCL body from provider config blocks
2. **Get Provider Schema** (line 108): Provider.GetProviderSchema() RPC call
3. **Evaluate Config Block** (line 115): EvaluateBlock converts HCL to cty.Value
4. **Validate Configuration** (line 153): ValidateProviderConfig RPC call
5. **Call ConfigureProvider** (line 177): ctx.ConfigureProvider() RPC call
6. **Return Diagnostics** (line 178): Return any errors/warnings

### Timing of Provider Operations

**During Graph Walk**:
1. **Graph Construction**: Provider nodes created by transformProviders
2. **Node Execution Order**: DAG walk ensures providers executed before resources
3. **Graph Edges**: Resources have edges to provider nodes (created by ProviderTransformer)
4. **Execution Sequence**:
   - Provider node executes first (no incoming edges from resources)
   - NodeApplyableProvider.Execute() calls InitProvider() and ConfigureProvider()
   - Resource nodes execute after provider (have edge to provider)
   - Resource nodes call getProvider() to retrieve already-configured provider

### CloseProviderTransformer
Location: `internal/terraform/transform_provider.go:251-309`

**Purpose**: Add graph nodes that close provider connections after use

**Mechanism** (lines 257-309):
1. **Create Close Nodes** (lines 262-281): For each provider, create graphNodeCloseProvider
2. **Add Provider Dependency** (line 281): Close node depends on provider node
   - Ensures provider initialized before close attempt
3. **Connect Consumers to Close** (lines 284-309): Each resource connected to appropriate close node
   - Close node has edges FROM all resource nodes that use provider
   - Ensures all resources finish before provider closes
4. **Transitive Reduction**: Removes redundant edges in final pass

**Graph Structure**:
```
Provider Node
    ↑
    ├─ Resource A
    ├─ Resource B
    └─ Resource C
        ↓
  Close Provider Node
```

**Execution**: Provider closed only after all resources complete

---

## Q4: Diff Computation per Resource

### Overview
Resource planning involves three phases: reading current state (refresh), comparing with configuration, and computing the planned change via provider RPC.

### Node Execution: NodePlannableResourceInstance.Execute()
Location: `internal/terraform/node_resource_plan_instance.go:70-84`

**Entry Point**:
```go
func (n *NodePlannableResourceInstance) Execute(ctx EvalContext, op walkOperation) tfdiags.Diagnostics {
    addr := n.ResourceInstanceAddr()
    switch addr.Resource.Resource.Mode {
    case addrs.ManagedResourceMode:
        return n.managedResourceExecute(ctx)
    case addrs.DataResourceMode:
        return n.dataResourceExecute(ctx)
    case addrs.EphemeralResourceMode:
        return n.ephemeralResourceExecute(ctx)
    }
}
```

Routes to **managedResourceExecute()** for regular resources

### Phase 1: Import (if applicable)
Location: `internal/terraform/node_resource_plan_instance.go:203-260`

**Process**:
1. **Check if Importing** (line 203): `importing := n.importTarget != cty.NilVal`
2. **Call importState()** (line 213): Provider.ImportResourceState() RPC
   - Retrieves resource state from external ID
   - Provider plugin implements import logic
3. **Store Imported State** (line 213): Result stored in instanceRefreshState

### Phase 2: Refresh (State Synchronization)
Location: `internal/terraform/node_resource_abstract_instance.go:580-742`

**Method Signature**:
```go
func (n *NodeAbstractResourceInstance) refresh(
    ctx EvalContext,
    deposedKey states.DeposedKey,
    state *states.ResourceInstanceObject,
    deferralAllowed bool,
) (*states.ResourceInstanceObject, *providers.Deferred, tfdiags.Diagnostics)
```

**Execution Flow** (lines 580-742):
1. **Early Return** (lines 594-596): Skip if no prior state exists
2. **Get Provider** (lines 589-592): Retrieve provider schema and instance
3. **Get Schema** (lines 599-604): Get resource schema from provider
4. **Call Pre-Refresh Hook** (lines 613-618): UI notification before refresh

#### ReadResource RPC Call
Location: `internal/terraform/node_resource_abstract_instance.go:635-643`

```go
var resp providers.ReadResourceResponse
resp = provider.ReadResource(providers.ReadResourceRequest{
    TypeName:     n.Addr.Resource.Resource.Type,
    PriorState:   priorVal,           // Current state value
    Private:      state.Private,       // Provider-managed private data
    ProviderMeta: metaConfigVal,       // Provider meta values
    ClientCapabilities: providers.ClientCapabilities{
        DeferralAllowed: deferralAllowed,
    },
})
```

**Provider Responsibilities**:
- Check if resource still exists in remote system
- Fetch current attribute values
- Return null state if resource deleted
- Return deferred status if operation cannot complete

**Result Processing** (lines 664-741):
1. Validate response (check for unknown values)
2. Conform to schema (NormalizeObjectFromLegacySDK)
3. Apply marks (sensitivity markers)
4. Return updated state object

### Phase 3: Planning (Diff Computation)
Location: `internal/terraform/node_resource_abstract_instance.go:744-1224`

**Plan() Method - High Level Overview**:
```go
func (n *NodeAbstractResourceInstance) plan(
    ctx EvalContext,
    plannedChange *plans.ResourceInstanceChange,
    currentState *states.ResourceInstanceObject,
    createBeforeDestroy bool,
    forceReplace []addrs.AbsResourceInstance,
) (*plans.ResourceInstanceChange, *states.ResourceInstanceObject, ...)
```

#### Configuration Evaluation
**Lines 796-826**: Parse and evaluate resource configuration

```go
origConfigVal, _, configDiags := ctx.EvaluateBlock(
    config.Config,
    schema,
    nil,
    keyData,  // for/each and count repetition data
)
```

**Precondition Checks** (lines 801-810):
- Evaluate precondition blocks
- Block planning if preconditions fail

#### Proposed New State Computation
**Lines 896**: `objchange.ProposedNew(schema, priorVal, configVal)`
- Merges prior state with desired config
- Computed-only attributes become unknown
- Sets structure for provider to plan against

#### PlanResourceChange RPC Call
**Primary RPC** (lines 927-937):
```go
resp = provider.PlanResourceChange(providers.PlanResourceChangeRequest{
    TypeName:         n.Addr.Resource.Resource.Type,
    Config:           unmarkedConfigVal,                // Desired config
    PriorState:       unmarkedPriorVal,                // Current state
    ProposedNewState: proposedNewVal,                  // Proposed next state
    PriorPrivate:     priorPrivate,                    // Provider private data
    ProviderMeta:     metaConfigVal,
    ClientCapabilities: providers.ClientCapabilities{
        DeferralAllowed: deferralAllowed,
    },
})
```

**Provider Responsibilities**:
1. **Determine Changes**: Compare prior and proposed state
2. **Mark Required Replacements**: Set `RequiresReplace` for attributes needing delete+create
3. **Return Planned State**: Result after applying changes
4. **Return Private Data**: Updated provider-specific metadata
5. **Optional Deferral**: Return Deferred if change cannot be planned

#### Replace Planning (if needed)
**Lines 1056-1141**: If action is Replace

Provider may need second plan call:
1. Call PlanResourceChange with **null prior state**
2. Compute new planned state from scratch
3. Result shows created resource with computed values unknown

#### Action Determination
**Line 1054**: `action, actionReason := getAction(...)`

This critical function determines the action type based on:
```go
getAction(
    addr,
    unmarkedPriorVal,        // Prior state
    unmarkedPlannedNewVal,   // Planned new state
    createBeforeDestroy,     // CBD configuration
    forceReplace,            // User force-replace
    reqRep,                  // RequiresReplace from provider
)
```

**Action Determination Logic**:
1. **No Prior State** (prior == null):
   - If config present → **Create**
   - If config absent → Skip (no action)

2. **Prior State Exists**:
   - Compare prior to planned using requiresReplace:
     - Any attribute in RequiresReplace changes → **Replace**
     - Other changes → **Update**
     - No changes → **NoOp**

3. **Force Replace Override**:
   - If in forceReplace list and action is Update/NoOp:
     - Force to **Replace** (CreateThenDelete or DeleteThenCreate)

4. **CreateBeforeDestroy Handling**:
   - If replacing and createBeforeDestroy: **CreateThenDelete**
   - If replacing and !createBeforeDestroy: **DeleteThenCreate**

5. **Tainted Resource**:
   - If prior marked tainted: Always **Replace**

**Action Types**:
- `plans.Create`: Resource doesn't exist, will be created
- `plans.Update`: Resource exists, will be modified
- `plans.DeleteThenCreate`: Replace by destroying then creating (default)
- `plans.CreateThenDelete`: Replace by creating then destroying (CBD)
- `plans.Delete`: Resource exists, will be destroyed
- `plans.NoOp`: No changes needed
- `plans.Forget`: Remove from state without destroying

#### Sensitivity Tracking
**Lines 1164-1166**: Mark changes in sensitivity as Update

```go
if action == plans.NoOp && !valueMarksEqual(plannedNewVal, priorVal) {
    action = plans.Update  // Sensitivity change counts as update
}
```

### Change Object Creation
**Lines 1192-1208**: Package results into plans.ResourceInstanceChange

```go
plan := &plans.ResourceInstanceChange{
    Addr:         n.Addr,
    PrevRunAddr:  n.prevRunAddr(ctx),
    Private:      plannedPrivate,
    ProviderAddr: n.ResolvedProvider,
    Change: plans.Change{
        Action: action,
        Before: priorVal,      // Current state
        After:  plannedNewVal, // Planned state
    },
    ActionReason:    actionReason,
    RequiredReplace: reqRep,
}
```

### State Persistence
**Lines 1211-1221**: Create planned state object

```go
state := &states.ResourceInstanceObject{
    Status:  states.ObjectPlanned,  // Marks as incomplete
    Value:   plannedNewVal,
    Private: plannedPrivate,
}
```

**Key Points**:
- Status.ObjectPlanned indicates plan-only, not yet applied
- Expression evaluators prefer plan over planned state
- Applied plan replaces this with actual state

### Change Recording
**Line 424** (in managedResourceExecute): `n.writeChange(ctx, change, "")`
- Writes computed change to sync.Changes plan object
- Accessible for UI display and apply phase

**Line 428**: `n.writeResourceInstanceState(ctx, instancePlanState, workingState)`
- Writes planned state to working state for downstream references

---

## Evidence

### File Locations and Key Functions

**Command Layer**:
- `internal/command/plan.go:22-118` - PlanCommand.Run()
- `internal/command/plan.go:145-190` - OperationRequest construction with PlanOpts fields

**Context/Planning**:
- `internal/terraform/context_plan.go:155-158` - Context.Plan()
- `internal/terraform/context_plan.go:169-372` - Context.PlanAndEval()
- `internal/terraform/context_plan.go:30-138` - PlanOpts structure definition
- `internal/terraform/context_plan.go:412-422` - plan() method routing
- `internal/terraform/context_plan.go:673-855` - planWalk() orchestration
- `internal/terraform/context_plan.go:887-952` - planGraph() builder instantiation

**Graph Construction**:
- `internal/terraform/graph_builder_plan.go:112-277` - PlanGraphBuilder.Steps() with all transformers
- `internal/terraform/transform_config.go:17-71` - ConfigTransformer (adds resource nodes)
- `internal/terraform/transform_reference.go:108-156` - ReferenceTransformer (adds dependency edges)
- `internal/terraform/transform_attach_state.go:29-71` - AttachStateTransformer (attaches prior state)

**Provider Handling**:
- `internal/terraform/transform_provider.go:18-41` - transformProviders() multi-transformer
- `internal/terraform/transform_provider.go:90-249` - ProviderTransformer (maps resources to providers)
- `internal/terraform/transform_provider.go:251-309` - CloseProviderTransformer (adds close nodes)
- `internal/terraform/eval_context_builtin.go:138-186` - InitProvider() (instantiates plugin)
- `internal/terraform/eval_context_builtin.go:213-237` - ConfigureProvider() (RPC call)
- `internal/terraform/node_provider.go:28-52` - NodeApplyableProvider.Execute()
- `internal/terraform/node_provider.go:103-190` - NodeApplyableProvider.ConfigureProvider()

**Resource Planning/Diff**:
- `internal/terraform/node_resource_plan_instance.go:70-84` - NodePlannableResourceInstance.Execute()
- `internal/terraform/node_resource_plan_instance.go:179-536` - managedResourceExecute() (main planning logic)
- `internal/terraform/node_resource_abstract_instance.go:580-742` - refresh() (ReadResource RPC)
- `internal/terraform/node_resource_abstract_instance.go:744-1224` - plan() (PlanResourceChange RPC)
- `internal/terraform/node_resource_plan_instance.go:203-260` - Import phase handling

**Supporting Types**:
- `internal/terraform/eval_context.go:45-95` - EvalContext interface definitions
- `internal/terraform/node_resource_plan_instance.go:29-84` - NodePlannableResourceInstance type
- `internal/terraform/node_resource_abstract_instance.go:1-100` - NodeAbstractResourceInstance base

### Provider RPC Signatures

**From internal/providers/interface.go** (implied):
1. `provider.ReadResource(ReadResourceRequest) ReadResourceResponse`
   - Called during refresh phase
   - Input: current state
   - Output: refreshed state

2. `provider.PlanResourceChange(PlanResourceChangeRequest) PlanResourceChangeResponse`
   - Called during plan phase
   - Input: prior state, config, proposed state
   - Output: planned state, required replacements, deferred status

3. `provider.ConfigureProvider(ConfigureProviderRequest) ConfigureProviderResponse`
   - Called after initialization
   - Input: configuration values, terraform version, capabilities
   - Output: diagnostics

4. `provider.ValidateProviderConfig(ValidateProviderConfigRequest) ValidateProviderConfigResponse`
   - Called during provider configuration
   - Input: configuration values
   - Output: diagnostics, prepared config

### Key Data Structures

**Plan Objects**:
- `internal/plans/plan.go:Plan` - Complete plan for entire configuration
- `internal/plans/changes.go:ResourceInstanceChange` - Change for single resource
- `internal/plans/changes.go:Change` - Contains Action, Before, After values

**State Objects**:
- `internal/states/state.go:State` - Current state storage
- `internal/states/resource_instance.go:ResourceInstanceObject` - Single instance state
- `internal/states/status.go:ObjectStatus` - ObjectPlanned, ObjectReady, ObjectTainted

**Graph Objects**:
- `internal/dag/graph.go:Graph` - DAG with vertices and edges
- `internal/terraform/graph.go:Graph` - Terraform-specific graph wrapper
- GraphNodeExecutable interface - Nodes that execute during walk

