# Kubernetes Scheduler Architecture Analysis

## Files Examined

### Core Scheduler Files
- **pkg/scheduler/scheduler.go** — Main Scheduler struct that orchestrates the scheduling loop, initializes frameworks, queues, and cache; implements the Run() method that starts the scheduling process
- **pkg/scheduler/schedule_one.go** — Contains ScheduleOne() entry point and the two-phase scheduling pipeline (schedulingCycle and bindingCycle); implements findNodesThatFitPod, prioritizeNodes, selectHost

### Framework Architecture
- **pkg/scheduler/framework/interface.go** — Defines all plugin interfaces (PreFilter, Filter, PostFilter, PreScore, Score, Reserve, Permit, PreBind, Bind, PostBind), Framework interface, CycleState, Status codes, and extension points
- **pkg/scheduler/framework/runtime/framework.go** — frameworkImpl implementation that instantiates and orchestrates plugins; implements all Run* methods (RunPreFilterPlugins, RunFilterPlugins, RunScorePlugins, etc.)
- **pkg/scheduler/framework/cycle_state.go** — CycleState passes mutable data between plugins within a scheduling cycle

### Internal Components
- **pkg/scheduler/internal/cache/interface.go** — Cache interface defining pod/node state management with Assume/Forget/Add/Remove operations and snapshot semantics
- **pkg/scheduler/internal/cache/cache.go** — Cache implementation tracking assumed pods and node information with expiration policy
- **pkg/scheduler/internal/cache/snapshot.go** — Snapshot provides read-only view of cache state at beginning of scheduling cycle
- **pkg/scheduler/internal/queue/scheduling_queue.go** — SchedulingQueue manages pods to be scheduled with activeQ, backoffQ, and unschedulableQ; handles pod lifecycle

## Dependency Chain

### Entry Point: Main Scheduling Loop
1. **Scheduler.Run(ctx)** (scheduler.go:435)
   - Calls `sched.SchedulingQueue.Run()` to start queue processor
   - Spawns goroutine calling `sched.ScheduleOne()` in a loop

### Phase 1: Per-Pod Scheduling (ScheduleOne)
2. **Scheduler.ScheduleOne(ctx)** (schedule_one.go:66)
   - Pops next pod from queue via `sched.NextPod()`
   - Calls `sched.SchedulePod()` which routes to `sched.schedulePod()`
   - If **schedulingCycle** succeeds, spawns async goroutine for **bindingCycle**

3. **Scheduler.schedulePod()** (schedule_one.go:390)
   - **Scheduling Cycle** orchestration:
     - Calls `sched.findNodesThatFitPod()` to filter nodes
     - Calls `prioritizeNodes()` to score and rank nodes
     - Returns ScheduleResult with suggested node

### Scheduling Cycle: Finding Best Node
4. **Scheduler.findNodesThatFitPod()** (schedule_one.go:442)
   - Updates cache snapshot: `sched.Cache.UpdateSnapshot()`
   - **Runs PreFilter plugins** via `fwk.RunPreFilterPlugins()`
     - Returns PreFilterResult (may reduce candidate nodes to a subset)
   - **Runs Filter plugins** via `findNodesThatPassFilters()` (in parallel)
     - Filters nodes based on framework and extender filters
   - Returns list of feasible nodes

5. **Framework.RunPreFilterPlugins()** (runtime/framework.go:679)
   - Iterates through preFilterPlugins in order
   - Each plugin can:
     - Return Success with optional PreFilterResult (NodeNames subset)
     - Return Skip (coupled Filter plugins are skipped)
     - Return Unschedulable/UnschedulableAndUnresolvable (stops immediately on latter)
   - Merges PreFilterResults via intersection if multiple plugins filter nodes

6. **Scheduler.findNodesThatPassFilters()** (schedule_one.go:573)
   - **Runs Filter plugins** in parallel via parallelize framework
   - For each node: `fwk.RunFilterPlugins()` (all filter plugins run sequentially per node)
   - Stops early if numFeasibleNodesToFind reached (based on percentageOfNodesToScore)

7. **Framework.RunFilterPlugins()** (runtime/framework.go:842)
   - Iterates through filterPlugins sequentially
   - Each plugin returns Success or Unschedulable for a given node
   - First failed plugin rejects the node; framework records plugin status

### Scoring Phase: Ranking Feasible Nodes
8. **prioritizeNodes()** (schedule_one.go:745)
   - **Runs PreScore plugins** via `fwk.RunPreScorePlugins()`
   - **Runs Score plugins** via `fwk.RunScorePlugins()`
   - **Runs extenders** (parallel) if configured
   - Combines all scores into NodePluginScores with TotalScore

9. **Framework.RunScorePlugins()** (runtime/framework.go:1089+)
   - For each score plugin:
     - Calls Score() for each feasible node (parallel across nodes)
     - Calls NormalizeScore() to normalize all scores for that plugin (0-100)
   - Aggregates scores from all plugins weighted by plugin weights

10. **selectHost()** (schedule_one.go:863)
    - Uses reservoir sampling from highest-scored nodes
    - Returns top node and optionally top-N nodes for reporting

### Assumption Phase: Optimistic Concurrency
11. **Scheduler.schedulingCycle()** (schedule_one.go:138)
    - After SchedulePod succeeds, calls `sched.assume()` to mark pod on chosen node
    - **Runs Reserve plugins** via `fwk.RunReservePluginsReserve()`
    - **Runs Permit plugins** via `fwk.RunPermitPlugins()`
    - If any plugin fails:
      - Calls `fwk.RunReservePluginsUnreserve()` to cleanup
      - Calls `sched.Cache.ForgetPod()` to undo assumption
    - Returns on success or moves pod to next phase

12. **Scheduler.assume()** (schedule_one.go:870+)
    - Calls `sched.Cache.AssumePod()` to assume pod on node
    - Cache updates nodeInfo with pod's resources

13. **Framework.RunReservePluginsReserve()** (runtime/framework.go:1149)
    - Iterates through reservePlugins
    - Each plugin can reserve resources or perform setup for the pod
    - Failure stops immediately and triggers Unreserve on all prior plugins

14. **Framework.RunPermitPlugins()** (runtime/framework.go:1169)
    - Each plugin returns Status and optional timeout
    - Success: proceed immediately
    - Wait: pod enters waiting pod map (framework tracks waiting state)
    - Reject/Error: trigger cleanup (Unreserve + ForgetPod)

### Phase 2: Binding Cycle (Async)
15. **Scheduler.bindingCycle()** (schedule_one.go:264)
    - **WaitOnPermit()**: If pod was permitted to wait, blocks here
    - **RunPreBindPlugins()**: Pre-binding setup plugins
    - **bind()**: Calls Bind plugins to actually bind pod
    - **RunPostBindPlugins()**: Post-binding cleanup plugins

16. **Framework.WaitOnPermit()** (runtime/framework.go:1186)
    - Waits on permit.WaitingPods map for pod's UID
    - Returns Success (approved) or Rejected (denied)

17. **Scheduler.bind()** (schedule_one.go:958)
    - **RunBindPlugins()**: Calls Bind plugins
    - First plugin to return non-Skip binds pod (sets NodeName)
    - Default Bind plugin writes binding to API server

18. **Framework.RunPostBindPlugins()** (runtime/framework.go:1304)
    - Informational only; no failure handling
    - Plugins can perform cleanup after binding succeeds

### Failure Handling
19. **Scheduler.handleSchedulingFailure()** (schedule_one.go:1012)
    - Called when schedulingCycle fails
    - If PostFilterPlugins exist, runs preemption to evict lower-priority pods
    - Calls failure handler which may requeue pod with backoff

20. **Scheduler.handleBindingCycleError()** (schedule_one.go:324)
    - Called when bindingCycle fails
    - Cleans up: RunReservePluginsUnreserve() + ForgetPod()
    - Moves related pods from unschedulable queue back to active/backoff queue

## Architecture Analysis

### Design Pattern: Two-Phase Scheduling with Optimistic Concurrency

**Problem Solved:**
- Binding is slow (API server write) and can fail
- Blocking scheduling on binding would be inefficient
- Need to continue scheduling other pods while binding completes

**Solution:**
1. **Scheduling Cycle** (synchronous): Find node and assume pod on it in cache
2. **Binding Cycle** (asynchronous): Actually bind pod to cluster, with failure recovery

**Key Insight:** Cache assumption creates optimistic lock
- Pod is considered scheduled in cache immediately
- Other pods can't use same resources (Assume adds pod to nodeInfo)
- If binding fails, Forget removes pod and resources are returned to unschedulable queue
- Other pods scheduled during binding period already see reserved resources

### Plugin Framework: Extension Points

The framework defines **13 extension points** where plugins can hook in:

**Scheduling Cycle (Synchronous):**
- **PreFilter**: Early filtering (can skip Filter plugins entirely)
- **Filter**: Feasibility check per node
- **PostFilter**: Preemption/remediation if pod unschedulable
- **PreScore**: Preparation before scoring (informational)
- **Score**: Rank nodes 0-100 (parallel per plugin, serial per node)
- **Reserve**: Resource booking after node chosen

**Permit/Waiting:**
- **Permit**: Gate before binding (can wait for external events)

**Binding Cycle (Async):**
- **PreBind**: Pre-binding setup (can still reject)
- **Bind**: Actually bind pod (default writes to API server)
- **PostBind**: Cleanup after successful binding (no failures)

**Queue Management:**
- **PreEnqueue**: Pre-enqueue filtering
- **QueueSort**: Pod priority ordering
- **EnqueueExtensions**: Event-driven requeuing hints

### Component Interactions

**1. SchedulingQueue ↔ Scheduler**
- Queue holds unscheduled pods in activeQ, backoffQ, unschedulableQ
- Scheduler.NextPod() pops highest-priority pod
- Queue.Done(uid) marks pod done after binding
- Queue.Activate() moves pods between queues on cluster events

**2. Cache ↔ Framework**
- Cache maintains assumed pod state and node information
- UpdateSnapshot() captures cache state at scheduling cycle start
- Framework.SnapshotSharedLister() provides read-only view to plugins
- AssumePod() is called after Reserve plugins pass
- ForgetPod() reverts assumption on failure

**3. CycleState ↔ Plugins**
- CycleState is thread-safe mutable map passed to each plugin
- PreFilter plugins write initial computed state
- Filter/Score plugins read and optionally update state
- Reserve/Permit plugins register cleanup actions
- PreFilterExtensions use state for incremental updates during preemption

**4. Framework ↔ Extenders**
- Legacy extensibility mechanism (pre-plugin era)
- Extenders participate in Filter and Prioritize phases
- Extenders run after framework plugins
- Integration: DefaultPreemption plugin can coordinate with extenders

### Data Flow: Pod Perspective

```
Pod → SchedulingQueue (activeQ)
   ↓
Pod.Pop() → ScheduleOne()
   ↓
Scheduling Cycle:
   - PreFilter plugins: Extract pod requirements, filter nodes
   - Filter plugins: Test pod feasibility on remaining nodes (parallel)
   - PreScore plugins: Setup scoring state (informational)
   - Score plugins: Rank feasible nodes (parallel per plugin)
   ↓
   Find best node via selectHost() → Assume pod on node in cache
   ↓
   Reserve plugins: Book resources
   Permit plugins: Gate binding
   ↓ (if all pass)
   Binding Cycle (async goroutine):
   - WaitOnPermit(): Wait for permit plugin approval
   - PreBind plugins: Final checks
   - Bind plugins: Write binding to API server
   - PostBind plugins: Cleanup
   ↓
Pod is scheduled (NodeName set, binding recorded)
```

### Parallelization Strategy

**Parallel Operations:**
- **Filter plugins**: Parallelized across nodes (via parallelize.Parallelizer)
  - Each node tests all filter plugins sequentially
  - Early termination stops other nodes if numFeasibleNodesToFind reached
- **Score plugins**: Parallelized across nodes
  - Each score plugin evaluates all nodes in parallel
  - NormalizeScore is sequential per plugin
- **Extenders**: Parallelized across extenders (via goroutines)
  - Each extender runs independently with mutex for aggregating scores

**Sequential Operations:**
- Filter plugins per node (can't parallelize within single node)
- PreFilter and PostFilter plugins (must run sequentially, early termination possible)
- Reserve, Permit, PreBind plugins (state dependencies)

### Error Handling Strategy

**Success Paths:**
- All PreFilter, Filter, Score, Reserve, Permit plugins return Success → pod assigned

**Failure Paths:**

1. **PreFilter or Filter Failure:**
   - Triggers PostFilter plugins (preemption)
   - PostFilter plugins can attempt to make pod schedulable
   - If PostFilter returns Success + NominatingInfo, pod saved for retry
   - If PostFilter returns Unschedulable, pod goes to unschedulableQ + backoff

2. **Reserve Failure:**
   - Immediately triggers Unreserve on all prior Reserve plugins
   - Cache.ForgetPod() removes assumption
   - Pod requeued to backoffQ

3. **Permit Failure:**
   - Same cleanup as Reserve failure
   - If rejected, pod marked and won't be re-tried immediately

4. **Binding Cycle Failure:**
   - Reserve plugins Unreserved
   - Cache.ForgetPod() removes assumption
   - Pod moved to unschedulableQ or backoffQ based on failure reason
   - Cluster events may trigger requeuing

### Status Codes and Their Meanings

- **Success**: Plugin succeeded, pod can continue or is OK
- **Error**: Unexpected internal error; pod requeued to activeQ/backoffQ
- **Unschedulable**: Pod can't fit but may fit after cluster changes (e.g., node capacity increases); pod backed off
- **UnschedulableAndUnresolvable**: Pod fundamentally unschedulable; pod backed off but PostFilter won't help
- **Wait** (Permit only): Pod waiting for external event; entered waiting pod map
- **Skip**: PreFilter/PreScore can skip coupled Filter/Score plugins; BindPlugin can skip binding
- **Pending** (Reserve/PreBind only): Scheduling succeeded but waiting for external component (e.g., DRA device driver)

### Snapshot Design: Read-Consistency Guarantee

**Why Snapshots?**
- Plugins run over many milliseconds; cluster state changes during scheduling
- Without snapshot, plugins could see inconsistent state
- Snapshot provides frozen view at cycle start

**When Taken:**
- At start of schedulePod(): `sched.Cache.UpdateSnapshot(nodeInfoSnapshot)`
- Snapshot remains unchanged through PreFilter → Filter → PreScore → Score

**Snapshot Guarantees:**
- All Filter decisions based on same node state
- Score plugins see same node state
- If pod preempted nodes before score phase, preemption not reflected in snapshot

**Binding Phase:**
- Can't use snapshot (cluster state has changed during scoring)
- Plugins use live informers instead

## Summary

The Kubernetes scheduler implements a sophisticated two-phase architecture combining **synchronous scheduling (find + assume) with asynchronous binding**. This decouples slow API operations from scheduling throughput.

The **plugin framework** provides 13 extension points with clear separation of concerns: filtering (feasibility), scoring (preference), reservation (resource booking), and binding (commitment). Plugins are orchestrated via a state machine with careful failure handling and recovery mechanisms.

**Key architectural decisions:**
1. **Optimistic concurrency**: Assume in cache, recover on binding failure
2. **Snapshot consistency**: Frozen cache view for scheduling decisions
3. **Progressive filtering**: Early termination when enough feasible nodes found
4. **Parallel scoring**: Independent plugin evaluation across nodes
5. **Permit gating**: External control over binding start (DRA, etc.)
6. **Error recovery**: Unreserve cleanup on any phase failure

This design achieves high scheduling throughput while maintaining correctness and allowing extensibility via plugins.
