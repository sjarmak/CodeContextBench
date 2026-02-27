# Kubernetes Scheduler Architecture Analysis

## Files Examined

### Core Scheduler Files
- `pkg/scheduler/scheduler.go` — Main Scheduler struct, coordination of cache, queue, and scheduling
- `pkg/scheduler/schedule_one.go` — ScheduleOne() entry point, scheduling and binding cycles, pod filtering/prioritization
- `pkg/scheduler/eventhandlers.go` — Pod event handlers for adding pods to scheduling queue

### Framework and Plugin System
- `pkg/scheduler/framework/interface.go` — Plugin interfaces, extension points (PreFilter, Filter, PostFilter, PreScore, Score, Reserve, Permit, PreBind, Bind, PostBind), Framework interface, Status/Code definitions, CycleState structure definitions
- `pkg/scheduler/framework/cycle_state.go` — CycleState implementation with thread-safe storage (sync.Map) for plugin state
- `pkg/scheduler/framework/types.go` — NodeInfo, PodInfo, NodeScore, Status, QueuedPodInfo types
- `pkg/scheduler/framework/runtime/framework.go` — frameworkImpl with plugin management, RunXxxPlugins methods
- `pkg/scheduler/framework/runtime/registry.go` — Plugin registry for loading and managing plugins
- `pkg/scheduler/framework/runtime/waiting_pods_map.go` — Manages pods waiting in Permit phase

### Scheduling Queue
- `pkg/scheduler/internal/queue/scheduling_queue.go` — SchedulingQueue interface with activeQ, backoffQ, unschedulablePods
- `pkg/scheduler/internal/queue/events.go` — ClusterEvent types and enqueue extensions

### Cache/Scheduler State
- `pkg/scheduler/internal/cache/cache.go` — Cache implementation managing assumed pods, node state, TTL expiration
- `pkg/scheduler/internal/cache/snapshot.go` — Node snapshot for consistent view during scheduling cycle
- `pkg/scheduler/internal/cache/node_tree.go` — Tree structure for efficient node lookup by zone/node

### Example Plugin Implementations
- `pkg/scheduler/framework/plugins/defaultbinder/default_binder.go` — BindPlugin implementation that calls APIServer binding
- `pkg/scheduler/framework/plugins/noderesources/fit.go` — PreFilter, Filter, PreScore, Score, EnqueueExtensions plugin for resource constraints
- `pkg/scheduler/framework/plugins/registry.go` — Central plugin registry

---

## Dependency Chain

### 1. **Entry Point: Scheduler.ScheduleOne()**
`pkg/scheduler/schedule_one.go:66` — Main loop of the scheduler

```
ScheduleOne()
  ├─ NextPod(logger) — Blocks until next pod from SchedulingQueue
  ├─ frameworkForPod(pod) — Gets scheduler framework for pod
  └─ skipPodSchedule(ctx, fwk, pod) — Skip if pod is deleted or assumed
```

### 2. **Scheduling Cycle: sched.schedulingCycle()**
`pkg/scheduler/schedule_one.go:139` — Synchronous phase that finds best node for pod

```
schedulingCycle(ctx, state, fwk, podInfo, start, podsToActivate)
  │
  ├─ (NEW) state := framework.NewCycleState()
  │  └─ Provides plugin-scoped state storage (sync.Map based)
  │
  ├─ sched.SchedulePod(ctx, fwk, state, pod)
  │  └─ schedulePod() at line 390
  │     │
  │     ├─ sched.Cache.UpdateSnapshot() — Creates snapshot of current node state
  │     │
  │     ├─ sched.findNodesThatFitPod(ctx, fwk, state, pod)
  │     │  ├─ fwk.RunPreFilterPlugins(ctx, state, pod)
  │     │  │  └─ Calls all PreFilterPlugin.PreFilter() in sequence
  │     │  │     (NodeResourcesFit, PodTopologySpread, InterPodAffinity, etc.)
  │     │  │
  │     │  ├─ sched.findNodesThatPassFilters(ctx, fwk, state, pod, diagnosis, nodes)
  │     │  │  └─ Parallel FilterPlugin execution via parallelize.Parallelizer
  │     │  │     (NodeResourcesFit.Filter, NodeAffinity.Filter, etc.)
  │     │  │
  │     │  └─ findNodesThatPassExtenders() — Legacy extender filtering
  │     │
  │     └─ prioritizeNodes() — Scoring phase (only if multiple feasible nodes)
  │        ├─ fwk.RunPreScorePlugins(ctx, state, pod, feasibleNodes)
  │        ├─ fwk.RunScorePlugins() with parallel execution
  │        └─ Extender scoring if configured
  │
  ├─ assume(logger, pod, nodeName) — Mark pod as running in cache
  │  └─ sched.Cache.AssumePod(logger, pod)
  │
  ├─ fwk.RunReservePluginsReserve(ctx, state, pod, nodeName)
  │  └─ Reserve plugins update internal state (network allocation, etc.)
  │     On failure: Unreserve plugins called to rollback
  │
  ├─ fwk.RunPermitPlugins(ctx, state, pod, nodeName)
  │  └─ Permit plugins can return Wait (blocks binding) or Success
  │     If Wait: pod added to waiting_pods_map
  │
  └─ Activate waiting pods via SchedulingQueue.Activate()
```

### 3. **Binding Cycle: sched.bindingCycle()** (Async goroutine)
`pkg/scheduler/schedule_one.go:265` — Asynchronous phase that binds pod to API server

```
bindingCycle(ctx, state, fwk, scheduleResult, assumedPodInfo, start, podsToActivate)
  │
  ├─ fwk.WaitOnPermit(ctx, pod) — Wait for Permit plugins if needed
  │
  ├─ fwk.RunPreBindPlugins(ctx, state, pod, nodeName)
  │  └─ PreBindPlugin.PreBind() called before binding
  │
  ├─ sched.bind(ctx, fwk, pod, nodeName, state)
  │  └─ fwk.RunBindPlugins(ctx, state, pod, nodeName)
  │     └─ First BindPlugin that doesn't Skip handles binding
  │        (DefaultBinder calls APIServer: pods.Bind())
  │
  └─ fwk.RunPostBindPlugins(ctx, state, pod, nodeName)
     └─ PostBindPlugin.PostBind() called after successful binding (informational)
```

---

## Plugin Framework Architecture

### Extension Points (Ordered Execution)

The scheduler provides **13 extension points** where plugins can intercede:

1. **PreEnqueue** — Before pod enters activeQ (lightweight, event-triggered)
2. **QueueSort** — Sorting pods in scheduling queue (only one plugin)
3. **PreFilter** — Before filtering nodes; can return reduced NodeNames set
4. **Filter** — Synchronous check if pod fits node (replaces old "predicates")
5. **PostFilter** — Called if pod unschedulable (preemption, etc.)
6. **PreScore** — Before scoring; informational, can record state
7. **Score** — Rank feasible nodes (replaces old "priorities")
8. **Reserve** — Mark resources as reserved; has Unreserve rollback
9. **Permit** — Final gate before binding; can delay (Wait) or reject
10. **PreBind** — Last sync check before binding
11. **Bind** — Actually bind pod to node (only one plugin handles it)
12. **PostBind** — After binding (informational cleanup)
13. **EnqueueExtensions** — Efficient requeue hints for PreFilter/Filter/Reserve/Permit failures

### Plugin Interface Pattern

All plugins implement the `framework.Plugin` interface:
```go
type Plugin interface {
    Name() string
}
```

Plugins optionally implement specific extension interfaces, e.g.:
```go
type FilterPlugin interface {
    Plugin
    Filter(ctx context.Context, state *CycleState, pod *v1.Pod, nodeInfo *NodeInfo) *Status
}

type ScorePlugin interface {
    Plugin
    Score(ctx context.Context, state *CycleState, p *v1.Pod, nodeName string) (int64, *Status)
    ScoreExtensions() ScoreExtensions
}
```

### Status Codes

Plugins return `framework.Status` with Code:
- **Success** — Plugin ran successfully, action succeeded
- **Unschedulable** — Pod doesn't fit (may retry via preemption)
- **UnschedulableAndUnresolvable** — Pod can't fit on this node, skip preemption
- **Error** — Unexpected error (triggers retry)
- **Wait** — Permit plugins: delay binding, not final rejection
- **Skip** — PreFilter/PreScore: skip coupled Filter/Score plugins
- **Pending** — Pod can be scheduled but external work needed (DRA)

### Framework Implementation

`pkg/scheduler/framework/runtime/framework.go` — **frameworkImpl** struct:

- Maintains plugin lists for each extension point
- Implements `RunXxxPlugins()` methods that:
  - Execute plugins in registered order (usually sequential for sync points)
  - Parallelize where possible (Filter, Score)
  - Handle context cancellation
  - Record metrics (plugin execution latency)
  - Skip plugins based on CycleState.SkipFilterPlugins, SkipScorePlugins

Example: `RunFilterPlugins()` at line 603+ executes each FilterPlugin.Filter() in parallel with parallelize.Parallelizer

---

## Component Interactions: CycleState, Cache, SchedulingQueue

### CycleState — Plugin State Container
`pkg/scheduler/framework/cycle_state.go` — Per-scheduling-cycle state:

```go
type CycleState struct {
    storage              sync.Map        // Plugin data (write-once, read-many)
    recordPluginMetrics  bool            // Sample metrics
    SkipFilterPlugins    sets.Set[string]
    SkipScorePlugins     sets.Set[string]
}
```

**Usage Pattern:**
1. **PreFilter phase**: PreFilterPlugin stores computed state
   - Example: NodeResourcesFit computes remaining resources per node
2. **Filter/Score phases**: Subsequent plugins Read() CycleState
   - Example: Plugins check if node has sufficient resources already computed
3. **Thread Safety**: sync.Map allows concurrent reads from different goroutines (parallel filtering)

**Key Methods:**
- `Write(key, value)` — Store plugin state (once per cycle)
- `Read(key)` — Retrieve plugin state (read many)
- `Clone()` — Create copy for PreFilter AddPod/RemovePod incremental updates

### Cache — Cluster State Snapshot
`pkg/scheduler/internal/cache/cache.go` — Maintains view of cluster:

```go
type cacheImpl struct {
    assumedPods map[string]*podState    // Pods marked as scheduled (assume)
    podStates   map[string]*podState    // Pod→deadline for expiration
    nodes       map[string]*nodeInfoListItem  // Node→NodeInfo
    nodeTree    *nodeTree               // Zone/node hierarchy for efficient lookup
    imageStates map[string]*framework.ImageStateSummary
    ttl         time.Duration           // How long to keep assumed pods (0 = no expiry)
}
```

**Interaction with Scheduling:**
1. **UpdateSnapshot()** called at start of scheduling cycle
   - Creates snapshot from current cache state
   - Ensures consistent view across filtering/scoring
2. **AssumePod()** called after finding node but before binding
   - Marks pod as "running" on node in cache
   - Allows next scheduling cycle to see reserved resources
3. **ForgetPod()** called if binding fails
   - Removes assumed pod, frees resources
4. **Expiration goroutine** (`run()`)
   - Periodically removes expired assumed pods (if pod still not bound after TTL)
   - Allows rescheduling if binding hangs

### SchedulingQueue — Pod Queue Management
`pkg/scheduler/internal/queue/scheduling_queue.go` — Three-queue system:

```
┌─────────────────────────────────────────────────┐
│         SCHEDULING QUEUE STRUCTURE               │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌──────────────┐   ┌──────────────┐            │
│  │  activeQ     │   │  backoffQ    │            │
│  │  (priority   │   │  (waiting    │            │
│  │   heap)      │   │   backoff)   │            │
│  └──────────────┘   └──────────────┘            │
│         │                   │                   │
│         └───────┬───────────┘                   │
│                 │                               │
│         ┌───────▼──────────┐                   │
│         │ unschedulablePods│ (map)              │
│         │  with timers     │                   │
│         └──────────────────┘                   │
│                                                 │
└─────────────────────────────────────────────────┘
```

**Queue Dynamics:**
1. **Add(pod)** — Pod enters activeQ via PreEnqueue plugins
2. **NextPod()** — Scheduler.ScheduleOne() pops from activeQ
3. **AddUnschedulableIfNotPresent()** — Failed pod moved to unschedulablePods with:
   - Backoff timer (1s initial, 10s max)
   - EnqueueExtensions hints (what cluster events can unblock it)
4. **Activate(pods)** — Pods moved from unschedulablePods/backoffQ to activeQ when:
   - Cluster events trigger (node added, pod evicted, etc.)
   - Backoff timer expires

**EnqueueExtensions Integration:**
- Each plugin can specify `EventsToRegister()` → ClusterEventWithHint
- When a cluster event occurs, scheduler calls plugin's predicate to check if pod now schedulable
- Only relevant pods moved back to activeQ (more efficient than global requeue)

---

## Data Flow: Pod Scheduling End-to-End

```
1. POD ENTERS SCHEDULER
   └─ Informer detects Pod creation/update
      └─ eventhandlers.go: AddPod() → PreEnqueuePlugins
         └─ SchedulingQueue.Add(pod) → activeQ

2. SCHEDULER LOOP: ScheduleOne()
   ├─ Pop pod from activeQ (via NextPod)
   │
   ├─ SCHEDULING CYCLE (Synchronous)
   │  ├─ Create CycleState (fresh for this pod)
   │  ├─ Snapshot cache: UpdateSnapshot()
   │  │
   │  ├─ FILTER PHASE
   │  │  ├─ RunPreFilterPlugins
   │  │  │  └─ Plugins store computed state in CycleState
   │  │  │  └─ May return NodeNames to consider (reduced set)
   │  │  │
   │  │  ├─ RunFilterPlugins (parallel over nodes)
   │  │  │  ├─ NodeResourcesFit.Filter — Check CPU/memory available
   │  │  │  ├─ NodeAffinity.Filter — Check affinity rules
   │  │  │  ├─ InterPodAffinity.Filter — Check pod-to-pod affinity
   │  │  │  └─ ... other plugins
   │  │  │
   │  │  └─ feasibleNodes = [nodes that passed all filters]
   │  │
   │  ├─ PREEMPTION (if no feasible nodes)
   │  │  └─ RunPostFilterPlugins
   │  │     └─ Default preemption plugin tries to evict pods
   │  │        to make room (retry scheduling next cycle)
   │  │
   │  ├─ SCORING PHASE (if multiple feasible nodes)
   │  │  ├─ RunPreScorePlugins
   │  │  ├─ RunScorePlugins (parallel over nodes)
   │  │  │  ├─ NodeResourcesFit.Score — Prefer less/more allocated
   │  │  │  ├─ ImageLocality.Score — Prefer nodes with image cached
   │  │  │  └─ ... other plugins
   │  │  └─ Extender scoring (legacy)
   │  │
   │  ├─ SELECT HOST
   │  │  └─ Choose node with highest score
   │  │
   │  ├─ ASSUMPTION
   │  │  └─ Cache.AssumePod(pod, nodeName)
   │  │     └─ Pod added to cache.assumedPods
   │  │        Other schedulers see pod's resources as reserved
   │  │
   │  ├─ RESERVE PHASE
   │  │  └─ RunReservePluginsReserve
   │  │     └─ Plugins allocate resources (network port, device, etc.)
   │  │
   │  ├─ PERMIT PHASE
   │  │  └─ RunPermitPlugins
   │  │     ├─ May return Wait → pod added to waitingPodsMap
   │  │     └─ May return Success → proceed to binding
   │  │
   │  └─ schedulingCycle() returns with pod assumed, node selected
   │
   ├─ BINDING CYCLE (Asynchronous, in separate goroutine)
   │  ├─ WaitOnPermit() — Block if Permit returned Wait
   │  │
   │  ├─ RunPreBindPlugins
   │  │  └─ Final validation before binding
   │  │
   │  ├─ RunBindPlugins
   │  │  └─ DefaultBinder.Bind(pod, nodeName)
   │  │     └─ APIServer call: POST /api/v1/pods/{ns}/{name}/binding
   │  │        └─ APIServer writes pod.spec.nodeName = nodeName
   │  │
   │  ├─ RunPostBindPlugins
   │  │  └─ Cleanup (informational)
   │  │
   │  └─ SchedulingQueue.Done(pod.UID) — Remove from queue
   │
   └─ POD BOUND TO NODE ✓
      └─ Pod controller sees nodeName, creates container
```

---

## Summary

The Kubernetes scheduler implements a **two-phase plugin-driven architecture**:

1. **Scheduling Cycle** (synchronous, scheduler goroutine): Pod + Cache snapshot → PreFilter/Filter/Score plugins determine best Node and assume pod in cache
2. **Binding Cycle** (asynchronous, separate goroutine): Assumed pod → Reserve/Permit/PreBind/Bind/PostBind plugins complete pod binding to APIServer

The **plugin framework** provides 13 extension points with well-defined interfaces; plugins store per-cycle state in **CycleState** (sync.Map for thread safety during parallel filtering). The **Cache** maintains an optimistic view of cluster state (assumed pods occupy resources), backed by a **SchedulingQueue** that sorts pods (activeQ, backoffQ, unschedulablePods) with efficient requeue via **EnqueueExtensions** cluster event hints. This design decouples scheduling (finding best node) from binding (persisting to APIServer), allowing multiple pods to be scheduled in parallel without waiting for slow network I/O.
