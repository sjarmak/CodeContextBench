# Kubernetes Scheduler Architecture Analysis

## Files Examined

### Core Scheduler
- `pkg/scheduler/scheduler.go` — Main scheduler struct, initialization, and Run loop. Orchestrates the entire scheduling process including queue setup and framework initialization
- `pkg/scheduler/schedule_one.go` — Entry point for scheduling a single pod; implements the two-phase scheduling and binding cycles with error handling

### Framework & Plugin System
- `pkg/scheduler/framework/interface.go` — Defines all plugin interfaces (PreFilter, Filter, Score, Reserve, Permit, Bind, PostFilter, etc.) and the Framework interface
- `pkg/scheduler/framework/types.go` — Core framework types including CycleState, Status, NodeInfo, and framework-level data structures
- `pkg/scheduler/framework/cycle_state.go` — CycleState implementation for storing plugin state during a scheduling cycle
- `pkg/scheduler/framework/runtime/framework.go` — Framework implementation (frameworkImpl) that runs plugins at each extension point

### Scheduling Queue
- `pkg/scheduler/internal/queue/scheduling_queue.go` — PriorityQueue implementation with activeQ, backoffQ, and unschedulablePods
- `pkg/scheduler/internal/queue/events.go` — Event types and cluster event handling for queue requeuing

### Scheduler Cache
- `pkg/scheduler/internal/cache/cache.go` — Cache implementation managing assumed pods and node information snapshots
- `pkg/scheduler/internal/cache/interface.go` — Cache interface defining operations (Assume, Add, Update, Remove, Forget)
- `pkg/scheduler/internal/cache/snapshot.go` — Snapshot of cache state provided to plugins during scheduling
- `pkg/scheduler/internal/cache/node_tree.go` — Tree structure for efficient node lookup

### Plugin Registry
- `pkg/scheduler/framework/plugins/registry.go` — Registry of built-in plugins
- `pkg/scheduler/framework/plugins/defaultbinder/` — Default bind plugin implementation
- `pkg/scheduler/framework/plugins/defaultpreemption/` — Default postfilter preemption plugin

### Supporting Components
- `pkg/scheduler/eventhandlers.go` — Event handlers for pod, node, and resource updates that feed events into the queue
- `pkg/scheduler/extender.go` — HTTP extender implementation for out-of-tree filtering and scoring

## Dependency Chain

### 1. Entry Point: ScheduleOne Loop (scheduler.go:435, schedule_one.go:66)
**Function**: `Scheduler.Run()` → `Scheduler.ScheduleOne()`
- Starts the main scheduling loop that runs continuously
- Blocks on `sched.NextPod()` which is set to `podQueue.Pop()` (scheduler.go:356)

### 2. Pod Retrieval from Queue (schedule_one.go:68)
**Function**: `podInfo, err := sched.NextPod(logger)` (calls `SchedulingQueue.Pop()`)
- Pulls the next pod from the scheduling queue (activeQ → backoffQ → unschedulablePods)
- Returns a `QueuedPodInfo` containing the pod and metadata

### 3. Framework Selection (schedule_one.go:86)
**Function**: `fwk, err := sched.frameworkForPod(pod)`
- Selects the appropriate scheduling profile based on `pod.Spec.SchedulerName`
- Returns a `Framework` instance implementing `frameworkImpl`

### 4. SCHEDULING CYCLE (schedule_one.go:111)
**Function**: `scheduleResult, assumedPodInfo, status := sched.schedulingCycle()`

#### 4a. Initialize Cycle State (schedule_one.go:101-106)
- Create new `CycleState` for this scheduling cycle
- Initialize `PodsToActivate` for plugins to nominate pods for activation

#### 4b. Call SchedulePod (schedule_one.go:149)
**Function**: `sched.SchedulePod(ctx, fwk, state, pod)` → `sched.schedulePod()`

##### PreFilter Phase (schedule_one.go:453)
**Function**: `fwk.RunPreFilterPlugins(ctx, state, pod)` (framework/runtime/framework.go)
- Runs all `PreFilterPlugin` implementations
- Can return `PreFilterResult` to filter down node candidate set
- If returns non-Success status: pod fails scheduling
- Returns: `PreFilterResult` + `Status`

##### Filter Phase (schedule_one.go:498)
**Function**: `sched.findNodesThatPassFilters()` → `fwk.RunFilterPlugins()`
- Runs `PreScorePlugins` on filtered nodes (schedule_one.go:452)
- For each node, runs all `FilterPlugin` implementations
- Filters out nodes that cannot run the pod
- Returns: list of `feasibleNodes` + `Diagnosis` with NodeToStatusMap

##### Score Phase (schedule_one.go:425)
**Function**: `prioritizeNodes()` → `fwk.RunScorePlugins()`
- Runs `PreScorePlugins` on feasible nodes
- For each feasible node, runs all `ScorePlugin.Score()` implementations
- Calls `ScorePlugin.NormalizeScore()` on each plugin's scores
- Combines scores via `selectHost()`
- Returns: selected `SuggestedHost` (node name)

#### 4c. Assume Pod (schedule_one.go:198)
**Function**: `sched.assume(logger, assumedPod, suggestedHost)`
- **Sets pod.Spec.NodeName** to the selected host
- Calls `Cache.AssumePod()` to update the cache
- This allows further scheduling without waiting for binding

#### 4d. Reserve Phase (schedule_one.go:209)
**Function**: `fwk.RunReservePluginsReserve(ctx, state, assumedPod, nodeName)`
- Runs all `ReservePlugin.Reserve()` implementations
- Plugins update their internal state for the assumed pod
- If any fail: trigger `Unreserve()` on all reserve plugins and forget the pod

#### 4e. Permit Phase - Scheduling Cycle (schedule_one.go:231)
**Function**: `fwk.RunPermitPlugins(ctx, state, assumedPod, nodeName)`
- Runs all `PermitPlugin.Permit()` implementations
- Can return:
  - **Success**: Continue to binding cycle
  - **Wait**: Pod moves to "waiting pods" map, will wait in binding cycle
  - **Reject**: Trigger Unreserve, forget pod, pod fails

#### 4f. Pod Activation (schedule_one.go:255-259)
**Function**: `sched.SchedulingQueue.Activate(logger, podsToActivate.Map)`
- Move pods nominated by plugins from unschedulablePods/backoffQ to activeQ
- Clear the PodsToActivate map

**Returns from scheduling cycle**: `ScheduleResult`, `assumedPodInfo`, `Status`

### 5. Binding Cycle - Async (schedule_one.go:118)
**Function**: `go sched.bindingCycle()` (runs in separate goroutine)

#### 5a. Wait on Permit (schedule_one.go:278)
**Function**: `fwk.WaitOnPermit(ctx, assumedPod)`
- If pod is in waiting pods map: wait until permit plugins allow or reject
- Blocking operation with timeout (maxTimeout = 15 minutes, framework.go)
- Returns Success or error

#### 5b. PreBind Phase (schedule_one.go:294)
**Function**: `fwk.RunPreBindPlugins(ctx, state, assumedPod, nodeName)`
- Runs all `PreBindPlugin.PreBind()` implementations
- Last chance to prevent binding (e.g., volume mounting)
- If any fail: binding fails, Unreserve triggered

#### 5c. Bind Phase (schedule_one.go:299)
**Function**: `sched.bind()` → `fwk.RunBindPlugins()`
- Runs all `BindPlugin.Bind()` implementations in order
- First plugin to handle binding (not return Skip) wins
- Typically calls `client.CoreV1().Pods(pod.Namespace).UpdateStatus()` with node binding
- Creates `Binding` object with pod and node name
- If any fail: binding fails, Unreserve triggered

#### 5d. PostBind Phase (schedule_one.go:312)
**Function**: `fwk.RunPostBindPlugins(ctx, state, assumedPod, nodeName)`
- Runs all `PostBindPlugin.PostBind()` implementations
- Informational only; failures are logged but don't affect result
- Used for cleanup and monitoring

#### 5e. Pod Activation - Binding Cycle (schedule_one.go:315-319)
**Function**: `sched.SchedulingQueue.Activate(logger, podsToActivate.Map)`
- Move nominated pods to activeQ

### 6. Error Handling
- **Scheduling cycle failure** (schedule_one.go:113): Call `FailureHandler` → retries via queue requeuing
- **Binding cycle failure** (schedule_one.go:127): Call `handleBindingCycleError` → Unreserve + requeue + update queue events

## Analysis

### Design Patterns Identified

#### 1. **Two-Phase Scheduling Architecture**
The scheduler separates concerns into:
- **Scheduling Cycle**: Determination phase where plugins decide feasibility and score nodes (runs synchronously in main loop)
- **Binding Cycle**: Commitment phase where the pod is actually bound to a node (runs asynchronously to avoid blocking)

This design allows the scheduler to continue scheduling other pods while binding operations complete, improving throughput.

#### 2. **Plugin Framework with Extension Points**
The scheduler uses a **chain-of-responsibility pattern** with extension points:
- **PreEnqueue**: Before pod enters queue (PreEnqueuePlugin)
- **PreFilter**: Before filtering (PreFilterPlugin) — can reduce node candidates
- **Filter**: Remove infeasible nodes (FilterPlugin)
- **PostFilter**: Preemption logic if no nodes fit (PostFilterPlugin)
- **PreScore**: Pre-processing before scoring (PreScorePlugin)
- **Score**: Rank feasible nodes (ScorePlugin)
- **Reserve**: Update plugin state post-selection (ReservePlugin)
- **Permit**: Final gating before binding (PermitPlugin) — can wait or reject
- **PreBind**: Final preparation before binding (PreBindPlugin)
- **Bind**: Actually bind pod to node (BindPlugin)
- **PostBind**: Cleanup after binding (PostBindPlugin)

Each extension point is a list of plugins; all must succeed (except Bind which uses first-match).

#### 3. **CycleState Pattern**
A `CycleState` struct is created at the start of each scheduling cycle and passed through all plugins. Plugins can:
- Store computed state via `State.Write(key, data)`
- Retrieve previous plugin results via `State.Read(key)`
- Avoid redundant computation across plugins

Example: PreFilter plugin computes which nodes are viable → stores in CycleState → Filter plugins read this.

#### 4. **Cache + Snapshot Optimization**
The scheduler uses:
- **Cache**: Maintains real-time state of pods/nodes with assumed pod support
- **Snapshot**: A point-in-time read-only copy taken at cycle start, used by plugins
  - Updates are safe during cycle (cache is separate)
  - Provides consistent view across all plugins in the cycle

The **Assume** mechanism is critical: after scheduling but before binding, the pod's assumption is added to cache so subsequent pods don't get scheduled to the same resources.

#### 5. **Scheduling Queue with Multiple Sub-Queues**
The `PriorityQueue` maintains:
- **activeQ**: Heap of high-priority pending pods (normal scheduling)
- **backoffQ**: Pods waiting for backoff period to expire
- **unschedulablePods**: Pods that failed; moved back to activeQ/backoffQ on cluster events

This prevents thrashing: failed pods exponentially backoff (1s → 10s → 1s when cluster event occurs).

#### 6. **Event-Driven Requeuing**
When cluster events occur (node added, taint updated, etc.):
- Plugins implement `EnqueueExtensions` to register interest in cluster events
- Queue receives events via event handlers from informers
- Queue uses plugin-provided `QueueingHint` functions to decide if a pod should move from unschedulablePods
- Reduces unnecessary retries of pods that still can't be scheduled

#### 7. **Nominated Node Optimization**
If a pod fails scheduling due to preemption:
- PostFilter plugin sets `pod.Status.NominatedNodeName` to the node where preemption will occur
- Next scheduling attempt: try nominated node first (schedule_one.go:474)
- If nominated node still can't fit pod: try all nodes
- Avoids wasted cycles trying unsuitable nodes

### Component Responsibilities

#### **Scheduler** (pkg/scheduler/scheduler.go)
- Owns the main scheduling loop
- Manages lifecycle (Run, Stop)
- Holds references to Cache, Queue, Profiles
- Implements default SchedulePod and FailureHandler

#### **SchedulingQueue** (pkg/scheduler/internal/queue/)
- Maintains pods in different scheduling states (active, backoff, unschedulable)
- Enforces priority ordering and backoff timing
- Implements pod nomination tracking
- Receives cluster events and requeues pods intelligently
- Thread-safe with condition variables for synchronization

#### **Cache** (pkg/scheduler/internal/cache/)
- Maintains assumed pod state (before binding completes)
- Aggregates pod information per node (resource usage, pod antiaffinity, etc.)
- Provides snapshots for plugin consumption
- State machine: Initial → Assumed → Added → (Update/Remove) → Deleted
- Supports expiration of assumed pods if not added within timeout

#### **Framework/frameworkImpl** (pkg/scheduler/framework/runtime/)
- Registry of all configured plugins
- Executes plugins at each extension point
- Manages waiting pods (for Permit phase)
- Tracks plugin metrics and scores
- Provides Handle interface to plugins (listers, client, recorder, etc.)

#### **CycleState** (pkg/scheduler/framework/cycle_state.go)
- Per-cycle data structure shared across plugins
- Type-safe storage via StateKey (string literal)
- Supports Clone for pass-by-value semantics in concurrent contexts
- Holds PodsToActivate for plugin-driven queue updates

### Data Flow During Scheduling

```
1. Pod: Unscheduled Pod created in API Server
   ↓
2. Queue: Event handlers detect Pod → Add to activeQ
   ↓
3. ScheduleOne: Pop pod from queue
   ↓
4. CycleState: Create new state for this pod + cycle
   ↓
5. PreFilter: Plugins preprocess, possibly filter nodes via NodeNames
   ↓
6. Snapshot: Cache.UpdateSnapshot() creates point-in-time NodeInfo view
   ↓
7. Filter: For each node, run filter plugins to check feasibility
   ↓
8. Score: For feasible nodes, run score plugins to rank them
   ↓
9. Select: Pick highest-scored node (selectHost)
   ↓
10. Assume: Cache.AssumePod() — pod.NodeName set, cache updated
    ↓
11. Reserve: ReservePlugins update internal state for assumed pod
    ↓
12. Permit: PermitPlugins allow/wait/reject
    ↓
13. [Success] SchedulingCycle returns → ScheduleOne starts async bindingCycle
    ↓
14. WaitOnPermit: If permit returned Wait, block until allowed
    ↓
15. PreBind: PreBindPlugins do final checks
    ↓
16. Bind: BindPlugin creates Binding and updates API Server (actual binding)
    ↓
17. PostBind: PostBindPlugins cleanup/monitoring
    ↓
18. Queue.Done: Mark pod as complete in queue
    ↓
19. Pod: Assigned Pod with .spec.nodeName set in API Server

[On Failure at any step]
↓
20. FailureHandler: Unreserve plugins called, Cache.ForgetPod removes assumption
↓
21. Queue.AddUnschedulableIfNotPresent: Pod moved to unschedulablePods or backoffQ
↓
22. Wait for cluster events or backoff timeout
↓
23. Requeue based on EnqueueExtensions hints
```

### Interface Contracts

#### **Plugin Interface** (framework/interface.go)
All plugins implement base `Plugin` interface:
```go
type Plugin interface {
    Name() string
}
```

#### **Framework Interface** (framework/interface.go)
Plugins receive a `Handle` interface providing:
- `SnapshotSharedLister()` → read-only node/pod view
- `ClientSet()` → Kubernetes API client
- `EventRecorder()` → emit events
- `SharedInformerFactory()` → watch resources
- `Parallelizer()` → run operations in parallel
- `PodNominator` → manage nominated pods
- `PluginsRunner` → call other plugins (for preemption)

#### **PreFilterPlugin.PreFilterExtensions** (framework/interface.go:386-393)
Optional extension allowing incremental updates:
- `AddPod(...)` → impact of adding pod to node
- `RemovePod(...)` → impact of removing pod from node
- Used during preemption evaluation to avoid full re-filtering

#### **EnqueueExtensions** (framework/interface.go:369-381)
Plugins can implement to optimize requeuing:
- `EventsToRegister()` → list cluster events that may make this pod schedulable
- `QueueingHintFn` → given event and pod, hint whether to requeue
- Framework uses hints to intelligently move pods between queue sub-queues

### Concurrency Model

1. **Main Loop Thread**: Runs `ScheduleOne` in a tight loop
   - Blocks on `Queue.Pop()`
   - Runs scheduling cycle synchronously
   - Launches async binding cycle goroutine

2. **Event Handler Threads**: Informer goroutines
   - Watch Pod/Node/other resources
   - Call event handlers that enqueue pods in thread-safe queue
   - Trigger condition variable to wake blocked `Pop()`

3. **Binding Goroutines**: Per-pod async binding
   - One goroutine per pod in binding cycle
   - Don't block main scheduling loop
   - Call `Queue.Done()` when complete

4. **Queue Requeuing**: Background goroutine
   - `PriorityQueue.Run()` periodically moves backoffQ items to activeQ
   - Processes cluster events and moves unschedulable pods using EnqueueExtensions hints

Thread safety achieved via:
- Mutex on PriorityQueue for pod lists
- Mutex on Cache for node/pod state
- Mutex on CycleState (not normally shared across threads)
- Read-only Snapshot provided to plugins (safe concurrent reads)

## Summary

The Kubernetes scheduler uses a **two-phase design** (scheduling cycle for finding the best node + binding cycle for committing) with an **extensible plugin framework** that runs plugins at 12 extension points. Pods flow through a **priority queue** (activeQ → backoffQ → unschedulablePods) that intelligently requeues based on cluster events via plugin hints. The **Cache** maintains pod assumptions during the gap between scheduling and binding, while a **Snapshot** provides a consistent point-in-time view to plugins. A **CycleState** allows plugins to share computed results. This architecture balances throughput (async binding), correctness (two-phase atomicity via assumptions), and extensibility (plugin framework).
