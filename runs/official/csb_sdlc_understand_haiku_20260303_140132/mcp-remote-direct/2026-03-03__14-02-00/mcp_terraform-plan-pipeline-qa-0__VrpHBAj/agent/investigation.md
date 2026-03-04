# Terraform Plan/Apply Pipeline Architecture

## Q1: Command to Context

When a user runs `terraform plan`, the CLI command delegates to the backend through the following steps:

### PlanCommand.Run() Entry Point
- **File**: `internal/command/plan.go:22-101`
- **Method**: `PlanCommand.Run(rawArgs []string) int`
- Parses command-line arguments via `arguments.ParsePlan(rawArgs)`
- Calls `c.PrepareBackend()` to initialize the backend (line 68)
- Calls `c.OperationRequest()` to build the operation request (line 82)
- Calls `c.GatherVariables()` to collect variable values (line 90)

### Backend Delegation
- **File**: `internal/backend/local/backend_plan.go:23-120`
- **Function**: `Local.opPlan(stopCtx, cancelCtx, op *backendrun.Operation, runningOp *backendrun.RunningOperation)`
- Gets local run context via `b.localRun(op)` (line 80)
- Calls **`lr.Core.Plan(lr.Config, lr.InputState, lr.PlanOpts)`** on line 108
  - `lr.Core` is a `terraform.Context` instance
  - `lr.Config` is the parsed Terraform configuration
  - `lr.InputState` is the prior/current state
  - `lr.PlanOpts` contains planning options

### terraform.Context.Plan() Method
- **File**: `internal/terraform/context_plan.go:155-158`
- **Method**: `Context.Plan(config *configs.Config, prevRunState *states.State, opts *PlanOpts) (*plans.Plan, tfdiags.Diagnostics)`
- Delegates to `c.PlanAndEval()` (line 156)
- `PlanAndEval()` (lines 169-350) contains the core logic:
  - Validates options (lines 206-247)
  - Routes to `c.plan()`, `c.destroyPlan()`, or `c.refreshOnlyPlan()` based on `opts.Mode` (lines 272-281)
  - Populates final plan with variable values and metadata (lines 288-350)

### PlanOpts Key Fields
- **File**: `internal/terraform/types.go` / `internal/backend/backendrun/local_run.go:69-73`
- **Mode**: `plans.NormalMode`, `plans.DestroyMode`, or `plans.RefreshOnlyMode`
- **Targets**: Resource addresses to target (`[]addrs.Targetable`)
- **ForceReplace**: Resource instances to force replace (`[]addrs.AbsResourceInstance`)
- **SkipRefresh**: Whether to skip the refresh phase
- **SetVariables**: Input variable values (`InputValues` map)
- **ExternalProviders**: Pre-initialized providers for external caller injection

---

## Q2: Graph Construction Pipeline

### PlanGraphBuilder.Steps() Method
- **File**: `internal/terraform/graph_builder_plan.go:121-277`
- **Method**: `PlanGraphBuilder.Steps() []GraphTransformer`
- Returns an ordered list of `GraphTransformer` stages that build the execution graph
- Called by `Build()` (line 112) via `BasicGraphBuilder.Build()`

### ConfigTransformer - Creates Configuration Nodes
- **File**: `internal/terraform/graph_builder_plan.go:137-146`
- **Lines**: 137-146 in Steps() method
- Creates DAG nodes for all resources, data sources, modules, and outputs defined in the configuration
- Called with configuration tree and resource concretization function
- Produces nodes that represent planned resource/data source instances

### ReferenceTransformer - Analyzes Dependencies
- **File**: `internal/terraform/graph_builder_plan.go:237`
- **Lines**: 237 in Steps() method
- Analyzes references between configuration resources, data sources, outputs, and variables
- Examines configuration expressions to identify dependency references
- Adds dependency edges to the graph:
  - Resource A → Data Source B if A references B
  - Resource C → Resource D if C references D's attributes
  - Output → Resource if output references resource
- Implementation examines HCL expressions in configuration blocks for variable/resource references

### AttachStateTransformer - Synchronizes Existing State
- **File**: `internal/terraform/graph_builder_plan.go:205`
- **Lines**: 205 in Steps() method
- Attaches the current state to each graph node
- Provides each node with:
  - Current resource instance objects from prior state
  - Current deposed objects (previous generation of instances marked for destruction)
  - Ephemeral values from state
- Enables nodes to compare desired state (config) with current state during evaluation

### Additional Key Transformers in Sequence
1. **AttachResourceConfigTransformer** (line 215): Attaches config blocks to resource nodes
2. **ModuleExpansionTransformer** (line 230): Creates nodes for module calls and expansion
3. **AttachSchemaTransformer** (line 225): Attaches provider schemas for type checking
4. **DestroyEdgeTransformer** (line 247): Creates destroy edges for resource dependencies
5. **TargetsTransformer** (line 256): Filters graph to only include targeted resources
6. **CloseProviderTransformer** (line 266): Creates nodes to close provider connections

### Graph Building Flow
1. Config nodes created with resource/data source/module instances
2. Root variables and module variables injected
3. State from prior run attached
4. Provider nodes added and dependency edges created
5. Module expansion handled
6. Reference transformer analyzes all expressions and creates dependency edges
7. Schema attached for validation
8. Target filtering applied
9. Provider closure nodes added at end
10. Final graph returned for concurrent execution via `Graph.Walk()`

---

## Q3: Provider Resolution and Configuration

### EvalContext.InitProvider() Interface
- **File**: `internal/terraform/eval_context.go:49-55`
- **Interface method**: `InitProvider(addr addrs.AbsProviderConfig, configs *configs.Provider) (providers.Interface, error)`
- Must be called once per provider configuration before any resource operations
- Panics if provider is already initialized or module context doesn't match

### BuiltinEvalContext.InitProvider() Implementation
- **File**: `internal/terraform/eval_context_builtin.go:138-186`
- **Method**: `BuiltinEvalContext.InitProvider(addr addrs.AbsProviderConfig, config *configs.Provider) (providers.Interface, error)`
- **Lines 156-163**: Handles external/pre-initialized providers from caller
  - For root module providers, checks if `ExternalProviderConfigs` contains provider
  - If found, wraps in `externalProviderWrapper` to make config/close operations no-op
  - Returns wrapped provider without instantiating new process
- **Lines 166-169**: Instantiates provider plugin process
  - Calls `ctx.Plugins.NewProviderInstance(addr.Provider)`
  - Creates new provider process/plugin instance via plugin system
- **Lines 175-181**: Applies provider mocking if configured
  - If provider config has `Mock` flag, wraps provider in `providers.Mock` wrapper
  - Allows test framework to override computed values
- **Line 183**: Caches provider instance in `ctx.ProviderCache[key]`
- **Return**: Returns initialized provider instance or error

### Provider.() Retrieval Method
- **File**: `internal/terraform/eval_context_builtin.go:188-193`
- Gets cached provider instance without re-initialization
- Returns nil if provider not yet initialized

### ConfigureProvider() Method
- **File**: `internal/terraform/node_provider.go:100-160`
- **Method**: `NodeApplyableProvider.ConfigureProvider(ctx EvalContext, provider providers.Interface, verifyConfigIsKnown bool) tfdiags.Diagnostics`
- Called during graph walk to configure an already-initialized provider
- **Steps**:
  - Line 106: Builds provider configuration from HCL via `buildProviderConfig()`
  - Line 108: Gets provider schema via `provider.GetProviderSchema()` RPC
  - Line 115: Evaluates configuration block via `ctx.EvaluateBlock()` with provider schema
  - Line 153: Validates provider config via `provider.ValidateProviderConfig()` RPC
  - Line 213+ (ConfigureProvider in eval_context_builtin.go): Calls provider's `ConfigureProvider()` RPC
- Provider RPC is called **after** initialization during graph walk, before resource operations

### CloseProviderTransformer - Provider Lifecycle End
- **File**: `internal/terraform/graph_builder_plan.go:266`
- **Lines**: 266 in Steps() method
- Transformer creates nodes that close provider connections at end of graph walk
- Called in graph builder for plan, apply, destroy, and validate operations
- Ensures all provider processes are cleanly shut down after operations complete
- Provider.Close() RPC called for each provider at end

### Provider Initialization Timeline
1. **ConfigTransformer** creates provider config nodes
2. **Graph walk begins**: `context.walk(graph, operation, opts)`
3. **NodeEvalableProvider.Execute()** (for schema fetch): Calls `ctx.InitProvider()` (line 20 in node_provider_eval.go)
4. **NodeApplyableProvider.Execute()** (during plan/apply): Calls `ctx.InitProvider()` then `ConfigureProvider()`
5. **Graph execution**: Resources use `ctx.Provider()` to get initialized providers
6. **CloseProviderTransformer nodes execute**: Calls `ctx.CloseProvider()` to shut down

---

## Q4: Diff Computation per Resource

### NodePlannableResourceInstance.Execute() Entry Point
- **File**: `internal/terraform/node_resource_plan_instance.go:70-84`
- **Method**: `NodePlannableResourceInstance.Execute(ctx EvalContext, op walkOperation) tfdiags.Diagnostics`
- Routes based on resource mode:
  - **Line 76**: Managed resources → `managedResourceExecute()`
  - **Line 78**: Data sources → `dataResourceExecute()`
  - **Line 80**: Ephemeral resources → `ephemeralResourceExecute()`

### managedResourceExecute() - Core Planning Logic
- **File**: `internal/terraform/node_resource_plan_instance.go:179-430+`
- **Lines 190-194**: Gets provider instance via `getProvider(ctx, n.ResolvedProvider)`

### Refresh Phase - Synchronize with Remote State
- **Lines 294-323**: Conditional refresh phase execution
- **Line 296**: Skipped if `skipRefresh` is true or during import
- **Line 298**: Calls `n.refresh(ctx, states.NotDeposed, instanceRefreshState, ctx.Deferrals().DeferralAllowed())`
- **File**: `internal/terraform/node_resource_abstract_instance.go:580-700`
  - **Lines 589-604**: Gets provider and schema
  - **Lines 620-643**: Calls provider's **`ReadResource()` RPC** (not PlanResourceChange)
    - Line 635: `resp = provider.ReadResource(providers.ReadResourceRequest{...})`
    - Sends current state and provider metadata
    - Receives updated state reflecting remote system's actual state
  - **Lines 664-700**: Processes response and handles deferral
- **Purpose**: Detects out-of-band changes (resource was modified outside Terraform)
- **Result**: Updated `instanceRefreshState` object with current remote values

### Plan Phase - Compute Desired Changes
- **Lines 335-430+**: Planning phase (if not `skipPlanChanges`)
- **Line 354**: Calls `n.plan(ctx, nil, instanceRefreshState, createBeforeDestroy, forceReplace)`
- **File**: `internal/terraform/node_resource_abstract_instance.go:744-1050`

#### plan() Method - PlanResourceChange RPC Call
- **Lines 744-850**: Setup phase
  - Evaluates configuration expressions to get proposed new state
  - Merges with prior state for missing/computed attributes
  - Unmarkes configuration (removes marks for provider)
- **Lines 900-937**: **Provider PlanResourceChange RPC Call**
  - **Line 927**: Main RPC call:
    ```
    resp = provider.PlanResourceChange(providers.PlanResourceChangeRequest{
      TypeName:         resource type,
      Config:           configuration values,
      PriorState:       current state before refresh,
      ProposedNewState: proposed new state from config,
      PriorPrivate:     provider-stored private data,
      ProviderMeta:     provider metadata from config,
      ClientCapabilities: deferral support,
    })
    ```
  - Provider receives:
    - **Config**: Desired configuration from HCL
    - **PriorState**: Current state before this plan
    - **ProposedNewState**: State computed from applying config + defaults
  - Provider returns:
    - **PlannedState**: Final planned state (may differ from proposed)
    - **PlannedPrivate**: Private data to store with plan
    - **Deferred**: Optional deferral if resource depends on unknown values
    - **Diagnostics**: Warnings/errors

#### Determining Action Type
- **Lines 1025-1100**: Action determination
- **Line 1025**: Compares `priorVal` with `plannedVal`
- **Lines 1026-1050**: Determines action:
  - **Create**: Prior state is null, planned state is not null
  - **Update**: Both are non-null but values differ
  - **Delete**: Prior state is non-null, planned state is null
  - **Replace**: Update action when `forceReplace` includes resource or schema change requires replacement
  - **NoOp**: Both states are equal (no changes)

#### Change Object Creation
- **Lines 1100-1150**: Creates `plans.ResourceInstanceChange` object
- Records:
  - **Addr**: Resource instance address
  - **Action**: Create/Update/Delete/NoOp/Replace
  - **Before**: Prior state value
  - **After**: Planned state value
  - **Private**: Provider-stored private data
  - **Reason**: Why replacement occurred (if applicable)
  - **Importing**: Import metadata (if importing)

### Deferred Changes Handling
- **Lines 313-314**: If refresh is deferred, defer is captured
- **Lines 382-383**: If plan is deferred, defer is captured
- **Lines 397-410**: If deferral reported, resource marked as deferred
  - Change stored with deferral reason
  - Change not included in initial plan
  - Deferral re-evaluated during apply

### State Writing
- **Lines 318**: Refreshed state written to `refreshState`
- **Lines 426-430+**: Planned change written to plan via `n.writeChange(ctx, change, "")`
- Changes accumulated in `ctx.Changes()` sync object for final plan

### Summary of Execution Path
1. Node receives `Execute()` call from graph walk
2. Refresh phase: `provider.ReadResource()` syncs current remote state
3. Plan phase: `provider.PlanResourceChange()` computes diff
4. Action determined: Create/Update/Delete/Replace/NoOp
5. `ResourceInstanceChange` object created with before/after values
6. Change written to plan's change set
7. Plan includes all resource changes for user review before apply

---

## Evidence

### Core Planning Entry Points
- `internal/command/plan.go:22` - PlanCommand.Run()
- `internal/backend/local/backend_plan.go:23` - Backend plan operation
- `internal/backend/local/backend_plan.go:108` - Context.Plan() call

### Context and Options
- `internal/terraform/context_plan.go:155` - Context.Plan() signature
- `internal/terraform/context_plan.go:169` - PlanAndEval() full logic
- `internal/backend/backendrun/local_run.go:69-73` - PlanOpts fields
- `internal/terraform/types.go` - PlanOpts, Mode, targets, etc.

### Graph Construction
- `internal/terraform/graph_builder_plan.go:121` - Steps() method
- `internal/terraform/graph_builder_plan.go:137` - ConfigTransformer
- `internal/terraform/graph_builder_plan.go:237` - ReferenceTransformer
- `internal/terraform/graph_builder_plan.go:205` - AttachStateTransformer
- `internal/terraform/graph_builder_plan.go:266` - CloseProviderTransformer

### Provider Initialization
- `internal/terraform/eval_context.go:49-55` - InitProvider interface
- `internal/terraform/eval_context_builtin.go:138` - InitProvider implementation
- `internal/terraform/node_provider.go:100` - ConfigureProvider method
- `internal/terraform/node_provider_eval.go:19-20` - NodeEvalableProvider.Execute()

### Resource Planning
- `internal/terraform/node_resource_plan_instance.go:70` - Execute() entry
- `internal/terraform/node_resource_plan_instance.go:179` - managedResourceExecute()
- `internal/terraform/node_resource_plan_instance.go:298` - refresh() call
- `internal/terraform/node_resource_plan_instance.go:354` - plan() call
- `internal/terraform/node_resource_abstract_instance.go:580` - refresh() implementation
- `internal/terraform/node_resource_abstract_instance.go:635` - provider.ReadResource() RPC
- `internal/terraform/node_resource_abstract_instance.go:744` - plan() implementation
- `internal/terraform/node_resource_abstract_instance.go:927` - provider.PlanResourceChange() RPC

### Provider Protocols
- `docs/plugin-protocol/tfplugin6.0.proto:156` - ConfigureProvider RPC
- `docs/plugin-protocol/tfplugin6.0.proto:170` - PlanResourceChange RPC
- `internal/plugin6/grpc_provider.go:435` - GRPCProvider.PlanResourceChange()

### State and Change Management
- `internal/terraform/context_walk.go:28-41` - graphWalkOpts structure
- `internal/terraform/eval_context_builtin.go:76-95` - BuiltinEvalContext fields (provider cache, state, changes)
