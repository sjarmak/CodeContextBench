# Terraform Plan/Apply Pipeline Architecture

## Q1: Command to Context

### CLI Command Parsing and Backend Delegation

**File:** `internal/command/plan.go`

The `PlanCommand.Run()` method (line 22) is the entry point for the `terraform plan` CLI command. The command processing flow:

1. **Argument Parsing** (lines 24-44):
   - `arguments.ParseView()` - parses global view arguments
   - `arguments.ParsePlan()` - parses plan-specific flags
   - Creates a `views.Plan` to render diagnostics

2. **Backend Preparation** (line 68):
   - `PrepareBackend()` loads the backend and returns a `backendrun.OperationsBackend` interface

3. **Operation Request Building** (line 82):
   - `OperationRequest()` constructs the operation request with:
     - `args.PlanMode` → `opReq.PlanMode`
     - `args.Targets` → `opReq.Targets`
     - `args.ForceReplace` → `opReq.ForceReplace`
     - `args.Refresh` → `opReq.PlanRefresh`
     - `args.DeferralAllowed` → `opReq.DeferralAllowed`

4. **Variable Collection** (line 90):
   - `GatherVariables()` collects user-supplied variable values

5. **Backend Operation Execution** (line 103):
   - `RunOperation()` delegates to the backend which implements the operation protocol

### Backend to Context Delegation

**File:** `internal/backend/local/backend_plan.go`

The backend's plan operation (`opPlan`, line 23) manages the overall plan process:

1. **Context Creation** (line 80):
   - `localRun()` prepares a `backendrun.LocalRun` which contains:
     - The `terraform.Context` instance
     - The loaded configuration
     - The input state
     - The `PlanOpts` (prepared in `localRunDirect`, lines 142-222)

2. **Plan Options Construction** (`localRunDirect`, lines 200-209):
   - Creates `terraform.PlanOpts` with:
     - `Mode`: Normal, Destroy, or RefreshOnly mode (from `op.PlanMode`)
     - `Targets`: Targeted resource instances to plan for
     - `ForceReplace`: Resource instances to force replacement
     - `SetVariables`: Parsed variable values
     - `SkipRefresh`: Determines if refresh phase is skipped
     - `GenerateConfigPath`: Path to write generated config for imports
     - `DeferralAllowed`: Whether deferral is supported

3. **Context Plan Invocation** (backend_plan.go, line 108):
   - Calls `lr.Core.Plan(lr.Config, lr.InputState, lr.PlanOpts)`
   - This delegates to `Context.Plan()` in `internal/terraform/context_plan.go`

### PlanOpts Structure

**File:** `internal/terraform/context_plan.go`

**Type:** `PlanOpts` (lines 30-138)

Key fields controlling plan behavior:

- **`Mode`** (line 36): `plans.Mode` - selects between NormalMode, DestroyMode, RefreshOnlyMode
- **`SkipRefresh`** (line 42): Boolean - disables remote state refresh step
- **`PreDestroyRefresh`** (line 52): Boolean - special flag for refresh immediately before destroy
- **`Targets`** (line 68): `[]addrs.Targetable` - limits planning to specific resources
- **`ForceReplace`** (line 79): `[]addrs.AbsResourceInstance` - forces replacement of specific instances
- **`DeferralAllowed`** (line 90): Boolean - enables deferred action support
- **`SetVariables`** (line 58): `InputValues` - root module variable assignments
- **`ExternalProviders`** (line 125): Pre-configured provider instances from external caller
- **`GenerateConfigPath`** (line 113): Path for generated import configuration

## Q2: Graph Construction Pipeline

### Graph Builder Architecture

**File:** `internal/terraform/graph_builder.go`

**Type:** `BasicGraphBuilder` (lines 26-68)

The `BasicGraphBuilder.Build()` method orchestrates graph construction:

```
Build(path) → for each step in Steps[] → step.Transform(g) → return g
```

Each step is a `GraphTransformer` that mutates the graph by adding nodes and edges.

### PlanGraphBuilder Steps Sequence

**File:** `internal/terraform/graph_builder_plan.go`

**Type:** `PlanGraphBuilder` (lines 30-108)

The `Steps()` method (lines 121-277) returns an ordered sequence of transformers:

#### Configuration and State Phase (lines 135-203):
1. **ConfigTransformer** (line 137): Adds all resources from configuration to the graph
2. **RootVariableTransformer** (line 149): Adds root module input variables
3. **ModuleVariableTransformer** (line 155): Adds module-local variables
4. **variableValidationTransformer** (line 160): Validates variables
5. **LocalTransformer** (line 163): Adds local values
6. **OutputTransformer** (line 164): Adds output values
7. **checkTransformer** (line 180): Adds check block assertions
8. **OrphanResourceInstanceTransformer** (line 186): Adds resources in state but not in config
9. **StateTransformer** (line 198): Adds deposed instances from state

#### State Attachment Phase (lines 204-215):
10. **AttachStateTransformer** (line 205): Attaches state objects to resource instance nodes
11. **AttachResourceConfigTransformer** (line 215): Attaches configuration to resource nodes

#### Provider and Schema Phase (lines 217-225):
12. **transformProviders** (line 218): Adds provider configuration nodes
13. **RemovedModuleTransformer** (line 221): Removes modules no longer in config
14. **AttachSchemaTransformer** (line 225): Loads and attaches provider schemas

#### Module and Reference Resolution Phase (lines 227-244):
15. **ModuleExpansionTransformer** (line 230): Creates expansion nodes for module calls
16. **ExternalReferenceTransformer** (line 233): Adds external references
17. **ReferenceTransformer** (line 237): **Analyzes references and adds dependency edges**
18. **AttachDependenciesTransformer** (line 239): Attaches explicit depends_on dependencies
19. **attachDataResourceDependsOnTransformer** (line 243): Attaches depends_on for data sources

#### Lifecycle and Cleanup Phase (lines 245-273):
20. **DestroyEdgeTransformer** (line 247): Adds destroy ordering edges
21. **pruneUnusedNodesTransformer** (line 251): Removes unused nodes
22. **TargetsTransformer** (line 256): Filters to targeted resources
23. **ForcedCBDTransformer** (line 260): Handles create_before_destroy forcing
24. **ephemeralResourceCloseTransformer** (line 263): Closes ephemeral resources
25. **CloseProviderTransformer** (line 266): Adds provider cleanup nodes
26. **CloseRootModuleTransformer** (line 269): Adds root module cleanup
27. **TransitiveReductionTransformer** (line 273): Reduces graph complexity

### ConfigTransformer Details

**File:** `internal/terraform/transform_config.go`

**Type:** `ConfigTransformer` (lines 28-53)

Responsibility: Adds resource nodes from configuration tree

Method: `Transform(g *Graph)` (lines 55-67)
- Recursively traverses the config module hierarchy
- Calls `ConcreteResourceNodeFunc` to create resource node instances
- Creates nodes for all managed and data resources in the config
- Does NOT create provider or variable nodes (those come from other transformers)

### ReferenceTransformer Details

**File:** `internal/terraform/transform_reference.go`

**Type:** `ReferenceTransformer` (lines 108-156)

Responsibility: **Analyzes references between nodes and creates dependency edges**

Method: `Transform(g *Graph)` (lines 112-156):

1. **Reference Map Construction** (line 115):
   - `NewReferenceMap(vs)` analyzes all vertices to build reference relationships
   - Maps referenceable addresses (from `GraphNodeReferenceable.ReferenceableAddrs()`)
   - Maps node references (from `GraphNodeReferencer.References()`)

2. **Edge Addition** (lines 118-149):
   - For each vertex `v` in the graph:
     - Call `m.References(v)` to get all parents that `v` references
     - For each parent, create a directed edge: `Connect(v → parent)`
     - This ensures parent nodes execute before dependent nodes

3. **Reference Resolution Logic**:
   - Uses `langrefs` package to parse references in configuration expressions
   - Matches references against referenceable addresses in the graph
   - Respects module boundaries (handles inter-module references correctly)
   - Skips destroy node references (destroy operations use state only)

The resulting edges establish the dependency ordering: if resource A references resource B, then B executes before A.

### AttachStateTransformer Details

**File:** `internal/terraform/transform_attach_state.go`

**Type:** `AttachStateTransformer` (lines 29-71)

Responsibility: Attaches state objects to resource instance nodes

Method: `Transform(g *Graph)` (lines 35-71):

1. **State Lookup** (line 42-68):
   - For each vertex implementing `GraphNodeAttachResourceState`
   - Calls `t.State.Resource(addr.ContainingResource())` to lookup the resource state
   - Retrieves the specific instance state from the resource state
   - Deep copies the state before attaching (line 67)

2. **Purpose**: Provides each resource instance node access to its current state during planning and execution

## Q3: Provider Resolution and Configuration

### Provider Initialization Flow

**File:** `internal/terraform/eval_context_builtin.go`

**Method:** `InitProvider()` (lines 138-186)

Instantiation flow:

1. **Cache Check** (line 140): Returns error if provider already initialized

2. **External Provider Check** (lines 151-163):
   - For root module providers, checks `ExternalProviderConfigs`
   - If found, wraps in `externalProviderWrapper` (pre-configured by caller)
   - No ConfigureProvider call needed for external providers

3. **Plugin Instantiation** (line 166):
   - `ctx.Plugins.NewProviderInstance(addr.Provider)` loads the provider plugin
   - Communicates with provider via RPC/gRPC

4. **Mock Provider Support** (lines 175-180):
   - If provider config has `Mock: true`, wraps in `providers.Mock`
   - Enables test mocking of provider behavior

5. **Cache Storage** (line 183):
   - Stores initialized provider in `ctx.ProviderCache[key]`

### Provider Configuration

**File:** `internal/terraform/node_provider.go`

**Type:** `NodeApplyableProvider`

**Method:** `ConfigureProvider()` (lines 100-190)

Configuration flow during plan graph walk:

1. **Schema Retrieval** (line 108):
   - Calls `provider.GetProviderSchema()`
   - Returns provider's configuration schema

2. **Configuration Evaluation** (line 115):
   - `ctx.EvaluateBlock(configBody, configSchema, ...)` evaluates the provider block
   - Resolves expressions against the eval context

3. **Validation** (line 153):
   - `provider.ValidateProviderConfig()` validates configuration values
   - Provider can insert defaults

4. **Actual Configuration** (line 177):
   - Calls `ctx.ConfigureProvider(n.Addr, unmarkedConfigVal)`
   - This invokes the provider's `ConfigureProvider` RPC

**File:** `internal/terraform/eval_context_builtin.go`

**Method:** `ConfigureProvider()` (lines 213-237)

RPC call:

```go
resp := p.ConfigureProvider(req)  // line 235
```

Request includes:
- `TerraformVersion`: Current Terraform version
- `Config`: Provider configuration values
- `ClientCapabilities.DeferralAllowed`: Whether deferrals are supported

### Provider Lifecycle Timing

**Graph Execution Order** (via CloseProviderTransformer):

1. **Initialization**: `NodeApplyableProvider.Execute()` calls `InitProvider()` and `ConfigureProvider()`
2. **Usage**: Resource planning/application uses configured provider
3. **Closure**: `graphNodeCloseProvider` nodes execute after all resources using that provider

### CloseProviderTransformer

**File:** `internal/terraform/transform_provider.go`

**Type:** `CloseProviderTransformer` (lines 255-310)

Responsibility: Ensures providers are closed after all usage

Method: `Transform(g *Graph)` (lines 257-310):

1. **Close Node Creation** (lines 262-276):
   - For each provider node in the graph, creates a `graphNodeCloseProvider`
   - Adds it to the graph

2. **Dependency Edges** (lines 277-282):
   - Close node depends on the provider node itself
   - Ensures provider stays open during its initialization

3. **Consumer Dependencies** (lines 284-307):
   - For each resource using a provider, adds edge:
     - Close node → Resource node
   - Ensures provider closes after all resources finish

Result: Provider closure happens after all dependent resources complete.

## Q4: Diff Computation per Resource

### Resource Planning Entry Point

**File:** `internal/terraform/node_resource_plan_instance.go`

**Type:** `NodePlannableResourceInstance`

**Method:** `Execute()` (lines 70-84)

Delegates based on resource mode:

```go
case addrs.ManagedResourceMode:
    return n.managedResourceExecute(ctx)  // line 76
```

### Managed Resource Execution

**Method:** `managedResourceExecute()` (lines 179-430+)

Complete planning flow for a single managed resource instance:

#### Phase 1: Import (if applicable, lines 210-252)

If importing:
- Calls `n.importState()` to get initial resource state
- Otherwise, reads existing state with `n.readResourceInstanceState()` (line 255)

#### Phase 2: Refresh (lines 294-323)

Unless `skipRefresh` is true:

**File:** `internal/terraform/node_resource_abstract_instance.go`

**Method:** `refresh()` (lines 580-743)

Refresh flow:

1. **Provider Retrieval** (line 589):
   - `getProvider(ctx, n.ResolvedProvider)` gets configured provider instance

2. **Pre-refresh Hook** (line 613):
   - Calls `ctx.Hook()` for UI feedback

3. **Provider ReadResource RPC** (lines 635-643):
   ```go
   resp = provider.ReadResource(providers.ReadResourceRequest{
       TypeName: n.Addr.Resource.Resource.Type,
       PriorState: priorVal,
       Private: state.Private,
       ProviderMeta: metaConfigVal,
       ClientCapabilities: { DeferralAllowed: deferralAllowed }
   })
   ```
   - Reads current remote state to detect out-of-band changes
   - Provider returns new state value and diagnostics

4. **Deferral Handling** (lines 651-653):
   - If provider defers, captures `resp.Deferred`

Returns refreshed state reflecting remote reality.

#### Phase 3: Planning (lines 336-430+)

Unless `skipPlanChanges` is true:

**Method:** `plan()` (lines 744-1191+)

Planning flow:

1. **Provider and Schema** (lines 758-768):
   - `getProvider()` retrieves configured provider
   - Gets provider schema for the resource type

2. **Configuration Evaluation** (lines 819-832):
   - `ctx.EvaluateBlock()` evaluates resource configuration
   - Resolves all variable references and function calls
   - Validates against provider schema

3. **ignore_changes Processing** (lines 884-888):
   - Applies `ignore_changes` to prevent spurious diffs
   - Removes configured attributes from comparison

4. **Value Preparation** (lines 890-896):
   - Unmarked values for sending to provider
   - Creates `proposedNewVal` from prior state + config
   - Uses `objchange.ProposedNew()` logic

5. **Pre-diff Hook** (lines 899-904):
   - Calls UI hook with prior/proposed values

6. **Provider PlanResourceChange RPC** (lines 927-937):
   ```go
   resp = provider.PlanResourceChange(providers.PlanResourceChangeRequest{
       TypeName: n.Addr.Resource.Resource.Type,
       Config: unmarkedConfigVal,
       PriorState: unmarkedPriorVal,
       ProposedNewState: proposedNewVal,
       PriorPrivate: priorPrivate,
       ProviderMeta: metaConfigVal,
       ClientCapabilities: { DeferralAllowed: deferralAllowed }
   })
   ```
   - Provider compares prior state with proposed new state
   - Returns `PlannedState` (what the provider expects after apply)
   - Returns `RequiresReplace` paths (attributes requiring destruction)
   - Returns deferral if applicable

7. **Planned Value Validation** (lines 960-1015):
   - Validates provider's response conforms to schema
   - Checks `objchange.AssertPlanValid()` invariants
   - Handles legacy provider type system differences

8. **Replace Determination** (lines 1048-1141):

   **Helper Function:** `getAction()` (defined in file, used line 1054)

   ```go
   action, actionReason := getAction(
       n.Addr, unmarkedPriorVal, unmarkedPlannedNewVal,
       createBeforeDestroy, forceReplace, reqRep
   )
   ```

   Determines action based on:
   - Prior state is null → **Create**
   - Planned state equals prior state → **NoOp**
   - Provider's `RequiresReplace` paths differ → **Replace**
   - User's `-replace=` matches instance → **Replace** (overrides)
   - create_before_destroy flag → **CreateThenDelete** or **DeleteThenCreate**

   If action is **Replace**:
   - Calls `provider.PlanResourceChange()` again with null prior state
   - Gets clean creation plan without computed fields from destroyed instance
   - Merges with actual prior for accurate before/after representation

9. **Tainted Resource Handling** (lines 1146-1154):
   - If prior state was tainted, converts Create to Replace

10. **Sensitivity Marking Changes** (lines 1164-1166):
    - If only sensitivity marks change, converts NoOp to Update

11. **Post-diff Hook** (lines 1184-1189):
    - Calls UI hook with final action and values

12. **Change Object Creation** (lines 1191+):
    - Creates `plans.ResourceInstanceChange` with:
      - `Addr`: Resource address
      - `Action`: Determined action
      - `Before`: Prior state value
      - `After`: Planned state value
      - Marks and metadata

### Action Determination Logic

**File:** `internal/terraform/node_resource_abstract_instance.go`

**Function:** `getAction()` (line 2736)

Pseudo-algorithm:

```
if priorVal.IsNull():
    return Create
elif plannedNewVal.Equal(priorVal):
    if forceReplace contains this instance:
        return Replace
    elif requiredReplaces is not empty:
        return Replace
    else:
        return NoOp
else:
    if requiredReplaces is not empty:
        return Replace
    else:
        return Update
```

The `requiredReplaces` set comes from provider's `RequiresReplace` response, indicating which attributes changed in a way requiring deletion.

## Evidence

### Key File Paths and Line References

**Command Layer:**
- `internal/command/plan.go:22` - PlanCommand.Run() entry point
- `internal/command/plan.go:82` - OperationRequest() builds operation
- `internal/command/plan.go:103` - RunOperation() delegates to backend

**Backend Layer:**
- `internal/backend/local/backend_plan.go:23` - opPlan() backend operation
- `internal/backend/local/backend_plan.go:108` - Context.Plan() invocation
- `internal/backend/local/backend_local.go:142` - localRunDirect() prepares context
- `internal/backend/local/backend_local.go:200` - PlanOpts construction

**Terraform Core - Plan Execution:**
- `internal/terraform/context_plan.go:140` - Plan() public entry point
- `internal/terraform/context_plan.go:169` - PlanAndEval() with evaluation scope
- `internal/terraform/context_plan.go:274` - Context.plan() delegates to planWalk()
- `internal/terraform/context_plan.go:673` - planWalk() orchestrates walk
- `internal/terraform/context_plan.go:887` - planGraph() builds execution graph
- `internal/terraform/context_plan.go:901` - PlanGraphBuilder.Build() constructs graph

**Graph Construction:**
- `internal/terraform/graph_builder.go:32` - BasicGraphBuilder.Build() runs transformers
- `internal/terraform/graph_builder_plan.go:121` - PlanGraphBuilder.Steps() defines transformer sequence
- `internal/terraform/transform_config.go:55` - ConfigTransformer.Transform() adds resources
- `internal/terraform/transform_reference.go:112` - ReferenceTransformer.Transform() adds edges
- `internal/terraform/transform_attach_state.go:35` - AttachStateTransformer.Transform() attaches state

**Provider Management:**
- `internal/terraform/eval_context_builtin.go:138` - InitProvider() instantiates provider
- `internal/terraform/eval_context_builtin.go:213` - ConfigureProvider() sends config to provider
- `internal/terraform/node_provider.go:103` - NodeApplyableProvider.ConfigureProvider() evaluates config
- `internal/terraform/transform_provider.go:257` - CloseProviderTransformer.Transform() adds cleanup

**Resource Planning:**
- `internal/terraform/node_resource_plan_instance.go:70` - NodePlannableResourceInstance.Execute() entry
- `internal/terraform/node_resource_plan_instance.go:179` - managedResourceExecute() main flow
- `internal/terraform/node_resource_abstract_instance.go:580` - refresh() reads remote state
- `internal/terraform/node_resource_abstract_instance.go:635` - provider.ReadResource() RPC call
- `internal/terraform/node_resource_abstract_instance.go:744` - plan() main planning method
- `internal/terraform/node_resource_abstract_instance.go:927` - provider.PlanResourceChange() RPC call
- `internal/terraform/node_resource_abstract_instance.go:1054` - getAction() determines plan action
- `internal/terraform/node_resource_abstract_instance.go:2736` - getAction() implementation

**Type Definitions:**
- `internal/terraform/context_plan.go:32` - PlanOpts struct with control fields
- `internal/terraform/graph_builder_plan.go:30` - PlanGraphBuilder struct
- `internal/terraform/graph_builder.go:26` - BasicGraphBuilder executor
- `internal/terraform/node_resource_plan_instance.go:32` - NodePlannableResourceInstance
- `internal/terraform/node_resource_abstract_instance.go:36` - NodeAbstractResourceInstance
