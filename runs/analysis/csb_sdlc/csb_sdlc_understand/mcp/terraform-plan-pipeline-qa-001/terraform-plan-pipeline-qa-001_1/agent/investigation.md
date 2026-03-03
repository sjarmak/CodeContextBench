# Terraform Plan/Apply Pipeline Architecture

## Q1: Command to Context

When a user runs `terraform plan`, the execution flow is:

1. **PlanCommand.Run()** (`internal/command/plan.go:22`)
   - Parses CLI arguments and view configuration
   - Calls `PrepareBackend()` to initialize the backend with configuration

2. **PrepareBackend()** (`internal/command/plan.go:120`)
   - Loads backend configuration
   - Calls `Backend()` to instantiate the backend (typically `local.Local`)
   - Returns the backend instance

3. **OperationRequest()** (`internal/command/plan.go:145`)
   - Creates a `backendrun.Operation` struct with critical fields:
     - **PlanMode** (`opts.PlanMode`): Normal, Destroy, or RefreshOnly mode
     - **Targets** (`opts.Targets`): Resource targeting filters
     - **ForceReplace** (`opts.ForceReplace`): Addresses to force replacement
     - **PlanRefresh** (`opts.Refresh`): Whether to refresh before planning
     - **ConfigDir**: Directory containing Terraform configuration
     - **ConfigLoader**: Configuration loader for parsing `.tf` files

4. **RunOperation()** → Backend.Operation() → opPlan()
   - `PlanCommand.Run()` calls `c.RunOperation(be, opReq)` to delegate to the backend
   - Backend's `Operation()` method (local backend: `internal/backend/local/backend.go:280`) dispatches based on operation type
   - For `OperationTypePlan`, dispatches to `opPlan()`

5. **opPlan()** (`internal/backend/local/backend_plan.go:23`)
   - Calls `b.localRun(op)` to create the planning context
   - Returns `LocalRun` struct containing `terraform.Context` and `PlanOpts`

6. **localRun()** → terraform.Context Creation (`internal/backend/local/backend_local.go:42`)
   - Loads state from backend
   - Locks state for operation duration
   - Loads configuration using `ConfigLoader`
   - Parses variables and creates `terraform.PlanOpts`:

   ```go
   planOpts := &terraform.PlanOpts{
       Mode:               op.PlanMode,
       Targets:            op.Targets,
       ForceReplace:       op.ForceReplace,
       SetVariables:       variables,
       SkipRefresh:        !op.PlanRefresh,
       GenerateConfigPath: op.GenerateConfigOut,
       DeferralAllowed:    op.DeferralAllowed,
   }
   ```

   - Calls `terraform.NewContext(coreOpts)` to create context with provider plugins

7. **Context.Plan()** (`internal/terraform/context_plan.go:155`)
   - Delegates to `PlanAndEval()` which validates options and dispatches based on `PlanOpts.Mode`
   - For NormalMode: calls `c.plan()` → `c.planWalk()`
   - For DestroyMode: calls `c.destroyPlan()` → `c.planWalk()`
   - For RefreshOnlyMode: calls `c.refreshOnlyPlan()` → `c.planWalk()`

---

## Q2: Graph Construction Pipeline

The dependency graph is built by `PlanGraphBuilder` (`internal/terraform/graph_builder_plan.go:30`).

1. **PlanGraphBuilder.Build()** (`internal/terraform/graph_builder_plan.go:112`)
   - Instantiated with configuration, state, providers, and planning options
   - Calls `Steps()` to get the sequence of `GraphTransformer` stages

2. **Steps()** returns the transformation pipeline (`internal/terraform/graph_builder_plan.go:121`):

   **Phase 1: Node Creation**
   - **ConfigTransformer** (line 137): Creates nodes for all resources in configuration
     - Iterates through config resources and creates `NodePlannableResource` nodes
     - Handles import targets and forgotten resources

   - **RootVariableTransformer** (line 149): Adds root module input variables
   - **ModuleVariableTransformer** (line 155): Adds module-level variables
   - **LocalTransformer** (line 163): Adds local values
   - **OutputTransformer** (line 164): Adds output values

   - **OrphanResourceInstanceTransformer** (line 186): Adds nodes for resources in state but not config
   - **StateTransformer** (line 198): Adds nodes for deposed instances and state-only resources

   **Phase 2: Resource Configuration and State Attachment**
   - **AttachStateTransformer** (line 205): Attaches current state to resource nodes
     - Each resource node gets its corresponding state from `prevRunState`

   - **AttachResourceConfigTransformer** (line 215): Attaches configuration to resource nodes
   - **AttachSchemaTransformer** (line 225): Attaches provider schemas needed for planning

   **Phase 3: Module Expansion and Provider Setup**
   - **ModuleExpansionTransformer** (line 230): Creates expansion nodes for module calls
   - **transformProviders()** (line 218): Creates provider nodes (`NodeApplyableProvider`)
     - Maps providers to configuration and instantiates provider plugin instances

   - **RemovedModuleTransformer** (line 221): Removes modules no longer in config

   **Phase 4: Dependency Analysis**
   - **ReferenceTransformer** (line 237): **Core dependency graph construction**
     - Analyzes node references to identify inter-node dependencies
     - For each node that implements `GraphNodeReferencer`:
       - Extracts references from resource configuration via `node.References()`
       - Finds referenced nodes using a reference map built from all referenceable nodes
       - Creates DAG edges: `graph.Connect(dag.BasicEdge(node, referencedNode))`
     - This creates edges showing "A depends on B", ensuring B executes before A
     - Example: If a resource references `aws_instance.foo.id`, an edge is created from the referencing resource to `aws_instance.foo`

   - **AttachDependenciesTransformer** (line 239): Processes explicit `depends_on` relationships
   - **attachDataResourceDependsOnTransformer** (line 243): Tracks dependencies for data source evaluation

   **Phase 5: Target and Destroy Edge Processing**
   - **DestroyEdgeTransformer** (line 247): Adds destroy edges for create_before_destroy
   - **pruneUnusedNodesTransformer** (line 251): Removes unreferenced nodes
   - **TargetsTransformer** (line 256): Filters graph to only included targeted resources
   - **ForcedCBDTransformer** (line 260): Enforces create_before_destroy where needed

   **Phase 6: Finalization**
   - **CloseProviderTransformer** (line 266): Adds provider cleanup nodes
   - **CloseRootModuleTransformer** (line 269): Adds root module cleanup
   - **TransitiveReductionTransformer** (line 273): Simplifies graph by removing redundant edges

3. **Graph Walking** (`internal/terraform/context_plan.go:719`)
   - After building the graph, `c.walk()` is called to execute all nodes
   - Graph nodes execute in dependency order (topological sort respects edges)
   - Resource planning happens during this walk via `NodePlannableResourceInstance.Execute()`

---

## Q3: Provider Resolution and Configuration

Providers are resolved, initialized, and configured during the graph walk:

1. **Provider Instantiation** (`internal/backend/local/backend_local.go:215`)
   - `terraform.NewContext(coreOpts)` is called with context options including provider factory
   - The context stores a reference to available plugins (`contextPlugins`)

2. **Provider Node Creation** (`internal/terraform/graph_builder_plan.go:218`)
   - `transformProviders()` creates `NodeApplyableProvider` nodes for each provider in configuration
   - Maps provider configurations to actual provider plugin instances
   - For external providers (pre-configured), wraps them in `externalProviderWrapper`

3. **Provider Initialization** (`internal/terraform/node_provider.go:30`)
   - When `NodeApplyableProvider` executes during graph walk:
     - Calls `GetSchema()` to fetch provider schema
     - Validates provider configuration against schema
     - Calls `ConfigureProvider()` with the evaluated configuration

4. **ConfigureProvider Execution** (`internal/terraform/node_provider.go:103` & `internal/terraform/eval_context_builtin.go:213`)
   - `NodeApplyableProvider.ConfigureProvider()` is called during graph execution
   - Creates `ConfigureProviderRequest` with:
     - Provider configuration values (evaluated from HCL)
     - Terraform version
   - Calls provider's RPC: `provider.ConfigureProvider(req)`
   - Provider returns configuration errors or warnings

5. **Provider Usage in Resource Planning**
   - Resource planning nodes retrieve the configured provider via `getProvider(ctx, n.ResolvedProvider)`
   - Each resource instance's planned node has `ResolvedProvider` field pointing to its provider configuration
   - The provider instance is obtained from the context's provider store

6. **Provider Cleanup** (`internal/terraform/graph_builder_plan.go:266`)
   - **CloseProviderTransformer** adds cleanup nodes at the end of execution
   - These nodes call `provider.Stop()` to gracefully shut down provider plugin processes
   - Ensures provider RPC connections are properly closed after planning completes

---

## Q4: Diff Computation per Resource

For a single managed resource instance, the planning process follows this path:

### Execution Entry Point

**NodePlannableResourceInstance.Execute()** (`internal/terraform/node_resource_plan_instance.go:70`)
- Dispatches based on resource mode:
  - Managed resource → `managedResourceExecute()` (line 76)
  - Data source → `dataResourceExecute()` (line 78)
  - Ephemeral resource → `ephemeralResourceExecute()` (line 80)

### Managed Resource Planning Flow

**managedResourceExecute()** (`internal/terraform/node_resource_plan_instance.go:179`)

1. **Phase 1: State Acquisition**
   - Retrieves provider and provider schema: `getProvider(ctx, n.ResolvedProvider)` (line 190)
   - If importing: calls `n.importState()` (line 213) to fetch remote resource via provider's `ImportResourceState()` RPC
   - Otherwise: calls `n.readResourceInstanceState()` (line 255) to deserialize state from backend
   - Result stored in `instanceRefreshState`

2. **Phase 2: Refresh (Sync Remote State)**
   - If `!skipRefresh` and not importing: calls `n.refresh()` (line 298)
   - Refresh process:
     - Calls provider's `ReadResource()` RPC with current state
     - Updates `instanceRefreshState` with live remote state
     - Detects out-of-band changes (modifications outside Terraform)
   - Result stored in `refreshState` for comparison with config
   - If refresh is deferred (provider returns `Deferred`), planning is aborted with deferral status

3. **Phase 3: Compute Planned Changes**
   - If not in refresh-only mode: calls `n.plan()` (line 354)

   **plan()** (`internal/terraform/node_resource_abstract_instance.go:750`)

   a. **Configuration Validation**
      - Calls `provider.ValidateResourceConfig()` RPC (line 866)
      - Re-validates configuration after all variables are known

   b. **Proposed New State Computation**
      - Applies `ignore_changes` policy to configuration (line 884)
      - Removes attributes that shouldn't trigger changes
      - Creates proposed new state: `objchange.ProposedNew(schema, priorVal, configVal)` (line 896)
        - Merges prior state values with config values
        - Uses provider schema to determine which config values override state

   c. **Provider Planning (PlanResourceChange RPC)**
      - Calls `provider.PlanResourceChange()` (line 927) with:
        ```
        {
          TypeName: "aws_instance",
          Config: unmarkedConfigVal,          // Final configuration
          PriorState: unmarkedPriorVal,       // Current state from refresh
          ProposedNewState: proposedNewVal,   // Config merged with state
          PriorPrivate: priorPrivate,         // Provider's private metadata
          ProviderMeta: metaConfigVal,        // Provider meta block values
          ClientCapabilities: {
            DeferralAllowed: deferralAllowed  // Whether deferral is permitted
          }
        }
        ```
      - Provider responds with:
        ```
        {
          PlannedState: plannedVal,           // Final planned state
          PlannedPrivate: plannedPrivate,     // Updated private metadata
          Diagnostics: diags,                 // Validation errors/warnings
          Deferred: deferred                  // If operation is deferred
        }
        ```

   d. **Change Determination**
      - Provider's returned `PlannedState` determines the action:
        - If `PlannedState == PriorState` → **NoOp** (no change)
        - If `PlannedState == null` → **Delete** (only for destroy operations)
        - If `PriorState == null && PlannedState != null` → **Create** (new resource)
        - If `PriorState != null && PlannedState != PriorState` → **Update** (modify in place)
      - If resource is in `ForceReplace` list: upgrade **Update** to **Replace**
      - If `replace_triggered_by` matched: upgrade **Update** or **NoOp** to **Replace**

4. **Phase 4: State and Change Recording**
   - Writes the planned change to the plan via `n.writeChange(ctx, change, "")` (line 376)
   - Planned change contains:
     ```go
     &plans.ResourceInstanceChange{
       Addr: address,
       Action: plans.Create | plans.Update | plans.Delete | plans.NoOp,
       Before: priorValue,                    // State before apply
       After: plannedValue,                   // State after apply
       Private: plannedPrivate,               // Provider metadata for apply
       GeneratedConfig: generatedConfigHCL,   // Config generated from import
       Importing: &plans.Importing{ID: id},   // Import metadata if importing
     }
     ```

5. **Phase 5: Deferral Handling**
   - If planning or refresh was deferred: reports deferral reason
   - Plan includes deferral information for later retry
   - Deferred resources don't block subsequent operations

### Data Source Planning (Simplified)

**dataResourceExecute()** (`internal/terraform/node_resource_plan_instance.go:86`)
- Calls `n.planDataSource()` instead of `n.plan()`
- Data sources use provider's `ReadDataSource()` RPC rather than `PlanResourceChange()`
- No state comparison; data sources always represent current remote state
- Changes reflect differences in computed values or filtering logic

---

## Evidence

### Critical File References

**CLI Command Parsing & Backend Delegation:**
- `internal/command/plan.go:22` - PlanCommand.Run()
- `internal/command/plan.go:120` - PrepareBackend()
- `internal/command/plan.go:145` - OperationRequest()
- `internal/backend/backendrun/operation.go:69` - Operation struct with PlanOpts fields

**Backend Operation Execution:**
- `internal/backend/local/backend.go:280` - Local.Operation()
- `internal/backend/local/backend_plan.go:23` - opPlan() dispatcher
- `internal/backend/local/backend_local.go:42` - localRun() context creation
- `internal/backend/local/backend_local.go:200` - PlanOpts construction

**Context & Planning Entry Points:**
- `internal/terraform/context_plan.go:155` - Context.Plan()
- `internal/terraform/context_plan.go:169` - Context.PlanAndEval()
- `internal/terraform/context_plan.go:673` - planWalk() graph execution
- `internal/terraform/context_plan.go:887` - planGraph() builder instantiation

**Graph Construction:**
- `internal/terraform/graph_builder_plan.go:30` - PlanGraphBuilder struct
- `internal/terraform/graph_builder_plan.go:112` - PlanGraphBuilder.Build()
- `internal/terraform/graph_builder_plan.go:121` - Steps() transformer sequence
- `internal/terraform/graph_builder_plan.go:137-273` - GraphTransformer pipeline

**Reference Analysis & Dependency Edges:**
- `internal/terraform/transform_reference.go:108` - ReferenceTransformer
- `internal/terraform/transform_reference.go:112` - ReferenceTransformer.Transform()
- `internal/terraform/transform_reference.go:125` - m.References(v) lookup
- `internal/terraform/transform_reference.go:144` - g.Connect(dag.BasicEdge(...))

**Provider Resolution & Configuration:**
- `internal/terraform/graph_builder_plan.go:218` - transformProviders()
- `internal/terraform/node_provider.go:30` - NodeApplyableProvider
- `internal/terraform/node_provider.go:103` - NodeApplyableProvider.ConfigureProvider()
- `internal/terraform/eval_context_builtin.go:213` - BuiltinEvalContext.ConfigureProvider()

**Resource Planning & Provider RPC Calls:**
- `internal/terraform/node_resource_plan_instance.go:70` - NodePlannableResourceInstance.Execute()
- `internal/terraform/node_resource_plan_instance.go:179` - managedResourceExecute()
- `internal/terraform/node_resource_plan_instance.go:298` - refresh() call
- `internal/terraform/node_resource_plan_instance.go:354` - plan() call
- `internal/terraform/node_resource_abstract_instance.go:750` - plan() method
- `internal/terraform/node_resource_abstract_instance.go:866` - ValidateResourceConfig() RPC
- `internal/terraform/node_resource_abstract_instance.go:927` - PlanResourceChange() RPC

**Key Data Structures:**
- `internal/terraform/context_plan.go:32` - PlanOpts struct definition
- `internal/backend/backendrun/operation.go:69` - Operation struct definition
- `internal/plans/changes.go` - plans.Plan and plans.ResourceInstanceChange
