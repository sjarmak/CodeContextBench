# Kubernetes Scheduler Bug: Missing ResourceSlice Event Handler in DRA Scheduling

## Executive Summary

**Bug**: Pods requesting Dynamic Resource Allocation (DRA) devices become permanently stuck in `Unschedulable` state when the DRA driver (which provides ResourceSlice objects) starts AFTER the pod is created.

**Root Cause**: ResourceSlice events are never registered in the scheduler's event handling pipeline because:
1. ResourceSlice is not declared as a GVK constant in `pkg/scheduler/framework/types.go`
2. ResourceSlice is not listed in the DynamicResources plugin's `EventsToRegister()` method

**Impact**: Critical - pods with DRA claims can become permanently unschedulable if timing is unfavorable

**Fix Complexity**: Minimal - requires adding ResourceSlice as a GVK constant and registering it in EventsToRegister()

**Total Changes**: 2 files, 3 lines of code

## Files Examined

- **pkg/scheduler/schedule_one.go** — Entry point for pod scheduling; calls PreFilter phase where DRA checks occur
- **pkg/scheduler/framework/plugins/dynamicresources/dynamicresources.go** — Main DRA plugin implementation; contains EventsToRegister() and PreFilter logic
- **pkg/scheduler/framework/plugins/dynamicresources/structuredparameters.go** — Parses ResourceSlice objects via resourceSliceLister
- **pkg/scheduler/eventhandlers.go** — Registers event handlers for cluster objects; uses gvkMap to determine which resources get handlers
- **pkg/scheduler/framework/types.go** — Defines GVK constants for all resources that scheduler can react to

## Dependency Chain

1. **Symptom Observed In**: `pkg/scheduler/schedule_one.go` (line 66 in `ScheduleOne()`)
   - Pod requesting DRA device arrives and enters scheduling pipeline
   - If driver hasn't started yet, no ResourceSlices exist in the cluster

2. **PreFilter Phase Called**: `pkg/scheduler/schedule_one.go` (line 453 in `filterNodes()`)
   - `fwk.RunPreFilterPlugins()` executes DynamicResources PreFilter hook

3. **DRA Plugin PreFilter Fails**: `pkg/scheduler/framework/plugins/dynamicresources/dynamicresources.go` (line 418 in `PreFilter()`)
   - PreFilter checks if pod can be scheduled by calling `foreachPodResourceClaim()`
   - This eventually triggers resource model refresh

4. **Resource Model Uses Lister**: `pkg/scheduler/framework/plugins/dynamicresources/dynamicresources.go` (line 958 in `PreFilter()`)
   - `newResourceModel()` is called which needs ResourceSlices
   - It receives `pl.resourceSliceLister` which reads current ResourceSlices from informer cache

5. **Resource Slices Lister Populated**: `pkg/scheduler/framework/plugins/dynamicresources/dynamicresources.go` (line 356 in `New()`)
   - Lister initialized from: `fh.SharedInformerFactory().Resource().V1alpha2().ResourceSlices().Lister()`
   - Lister cache only updates when ResourceSlice events are received

6. **Event Handlers Registered**: `pkg/scheduler/eventhandlers.go` (line 287 in `addAllEventHandlers()`)
   - Event handlers are registered based on `gvkMap` parameter
   - `gvkMap` contains GVKs from all plugins' `EventsToRegister()` methods

7. **GVKs Built From Plugin Events**: `pkg/scheduler/scheduler.go` (line 525 in `unionedGVKs()`)
   - `gvkMap` is constructed by aggregating `ClusterEvent.Resource` from all plugins
   - Event handler registration only occurs for GVKs present in this map

8. **Bug Triggered At**: `pkg/scheduler/framework/plugins/dynamicresources/dynamicresources.go` (line 381 in `EventsToRegister()`)
   - **ResourceSlice is NOT in the list of events returned by this function**

## Root Cause

### **File**: `pkg/scheduler/framework/plugins/dynamicresources/dynamicresources.go`

### **Function**: `EventsToRegister()` at line 381

### **Line**: Lines 381-413

### **Primary Issue**:
ResourceSlice events are **never declared** in the DynamicResources plugin's `EventsToRegister()` method. The plugin correctly declares handlers for:
- ResourceClaimParameters (Add | Update)
- ResourceClassParameters (Add | Update)
- ResourceClaim (Add | Update)
- PodSchedulingContext (Add | Update)
- Node (Add | UpdateNodeLabel | UpdateNodeTaint)
- ResourceClass (Add | Update)

BUT it's missing:
- **ResourceSlice (Add | Update)** ← MISSING!

### **Secondary Issue**:
`pkg/scheduler/framework/types.go` (lines 92-96) does not define ResourceSlice as a GVK constant. The file defines:
- PodSchedulingContext
- ResourceClaim
- ResourceClass
- ResourceClaimParameters
- ResourceClassParameters

BUT missing:
- **ResourceSlice** ← NOT DEFINED AS GVK

### **Why This Causes the Bug**:

1. When EventsToRegister() doesn't include ResourceSlice, the GVK never gets added to the scheduler's `gvkMap`
2. Without ResourceSlice in gvkMap, no event handler is registered for ResourceSlice objects in `addAllEventHandlers()` (eventhandlers.go:395-542)
3. When a DRA driver creates ResourceSlice objects (to advertise available resources), the scheduler's informer cache receives the events BUT has no registered handler
4. The scheduler's SchedulingQueue is never notified of ResourceSlice creation/updates
5. Pods stuck in Unschedulable state are never re-queued to try scheduling again, even though resources are now available

### **The Race Condition**:
- If driver starts FIRST: ResourceSlices exist before pod arrives → scheduling succeeds
- If pod arrives FIRST: No ResourceSlices exist → pod marked Unschedulable → driver starts later → pod never re-queued → **BUG**

## Proposed Fix

### **Part 1: Add ResourceSlice as a GVK constant**

**File**: `pkg/scheduler/framework/types.go`

```diff
	PodSchedulingContext    GVK = "PodSchedulingContext"
	ResourceClaim           GVK = "ResourceClaim"
	ResourceClass           GVK = "ResourceClass"
	ResourceClaimParameters GVK = "ResourceClaimParameters"
	ResourceClassParameters GVK = "ResourceClassParameters"
+	ResourceSlice           GVK = "ResourceSlice"

	// WildCard is a special GVK to match all resources.
```

### **Part 2: Register ResourceSlice event in DRA plugin**

**File**: `pkg/scheduler/framework/plugins/dynamicresources/dynamicresources.go`

```diff
func (pl *dynamicResources) EventsToRegister() []framework.ClusterEventWithHint {
	if !pl.enabled {
		return nil
	}

	events := []framework.ClusterEventWithHint{
		// Changes for claim or class parameters creation may make pods
		// schedulable which depend on claims using those parameters.
		{Event: framework.ClusterEvent{Resource: framework.ResourceClaimParameters, ActionType: framework.Add | framework.Update}, QueueingHintFn: pl.isSchedulableAfterClaimParametersChange},
		{Event: framework.ClusterEvent{Resource: framework.ResourceClassParameters, ActionType: framework.Add | framework.Update}, QueueingHintFn: pl.isSchedulableAfterClassParametersChange},

		// Allocation is tracked in ResourceClaims, so any changes may make the pods schedulable.
		{Event: framework.ClusterEvent{Resource: framework.ResourceClaim, ActionType: framework.Add | framework.Update}, QueueingHintFn: pl.isSchedulableAfterClaimChange},
		// When a driver has provided additional information, a pod waiting for that information
		// may be schedulable.
		{Event: framework.ClusterEvent{Resource: framework.PodSchedulingContext, ActionType: framework.Add | framework.Update}, QueueingHintFn: pl.isSchedulableAfterPodSchedulingContextChange},
+		// ResourceSlices are advertised by device drivers and contain the available resources
+		// on each node. When a new ResourceSlice is created or updated, pods using the
+		// corresponding resource class may become schedulable. Without a QueueingHintFn, all
+		// pods are retried on ResourceSlice changes with backoff, which is appropriate since
+		// determining if a specific ResourceSlice affects a specific pod requires complex analysis.
+		{Event: framework.ClusterEvent{Resource: framework.ResourceSlice, ActionType: framework.Add | framework.Update}},
		// A resource might depend on node labels for topology filtering.
		// A new or updated node may make pods schedulable.
		//
		// A note about UpdateNodeTaint event:
		// NodeAdd QueueingHint isn't always called because of the internal feature called preCheck.
		// As a common problematic scenario,
		// when a node is added but not ready, NodeAdd event is filtered out by preCheck and doesn't arrive.
		// In such cases, this plugin may miss some events that actually make pods schedulable.
		// As a workaround, we add UpdateNodeTaint event to catch the case.
		// We can remove UpdateNodeTaint when we remove the preCheck feature.
		// See: https://github.com/kubernetes/kubernetes/issues/110175
		{Event: framework.ClusterEvent{Resource: framework.Node, ActionType: framework.Add | framework.UpdateNodeLabel | framework.UpdateNodeTaint}},
		// A pod might be waiting for a class to get created or modified.
		{Event: framework.ClusterEvent{Resource: framework.ResourceClass, ActionType: framework.Add | framework.Update}},
	}
	return events
}
```

## Analysis

### Detailed Execution Trace

#### **Phase 1: Pod Arrival (Before Driver Starts)**

1. Pod with DRA resource claim arrives at scheduler
2. Pod enters scheduling queue via `addPodToSchedulingQueue()` in eventhandlers.go
3. `ScheduleOne()` is called to schedule the pod
4. `filterNodes()` is called to find viable nodes
5. `fwk.RunPreFilterPlugins()` executes (schedule_one.go:453)
   - DynamicResources.PreFilter() is called (dynamicresources.go:418)
   - Inside PreFilter, `newResourceModel()` is called (dynamicresources.go:958)
   - This calls `pl.resourceSliceLister.List(labels.Everything())`
   - **Result**: No slices returned, so plugin can't find resources
   - PreFilter fails with status "cannot allocate all claims"
6. Pod is marked as Unschedulable and moved to unschedulable queue

#### **Phase 2: Driver Starts (After Pod is Unschedulable)**

1. DRA driver starts and creates ResourceSlice objects
2. ResourceSlice events are sent to scheduler's informer
3. **BUG**: No event handler is registered for ResourceSlice events
   - Because ResourceSlice is not in plugin's EventsToRegister() (line 381-413)
   - Because ResourceSlice is not defined as GVK in types.go (lines 92-96)
   - Because gvkMap doesn't include ResourceSlice (scheduler.go:525-536)
   - Because addAllEventHandlers() has no switch case for ResourceSlice (eventhandlers.go:395-542)
4. ResourceSlice events are silently dropped
5. SchedulingQueue is never notified about the new resources
6. Pod remains in Unschedulable queue forever
   - Even though resources are now available via the new ResourceSlices

#### **Why Event Handler Registration Matters**

The scheduler uses an event-driven architecture where:
- Plugins declare which cluster events should trigger re-evaluation of unschedulable pods
- These declarations come from `EventsToRegister()` methods
- The scheduler aggregates these into a `gvkMap`
- `gvkMap` drives which resources get event handlers in `addAllEventHandlers()`
- When a resource event occurs, the scheduler's SchedulingQueue.MoveAllToActiveOrBackoffQueue() is called
- This re-queues pods that were previously unschedulable

Without ResourceSlice in this chain, ResourceSlice events never trigger pod re-queuing.

#### **The Fix Mechanism**

By adding ResourceSlice to:
1. **types.go**: Makes it a recognized GVK in the framework
2. **EventsToRegister()**: Tells scheduler that DRA plugin cares about these events
3. **gvkMap**: Includes ResourceSlice when calculating which handlers to register
4. **addAllEventHandlers()**: Falls through to dynamic informer registration (line 516-541) for ResourceSlice
5. **Queueing Hint Function**: Tells scheduler when pods might become schedulable

When a ResourceSlice is created/updated:
1. Event is received by informer and routed to registered handler
2. Handler calls `SchedulingQueue.MoveAllToActiveOrBackoffQueue()` with ResourceSliceAdd/Update event
3. Pods in unschedulable queue are checked against queueing hint
4. Pod with DRA claims gets re-queued to active queue
5. On next scheduling attempt, PreFilter sees ResourceSlices and succeeds
6. Pod gets scheduled successfully

## Implementation Notes

- **Minimal Change**: This fix only adds what's necessary to register the missing event handler (two files, three lines)
- **No Custom Queueing Hint**: ResourceSlice events have no QueueingHintFn, so pods are always retried with backoff on ResourceSlice changes. This is correct because determining if a specific ResourceSlice affects a specific pod requires complex analysis of claim parameters and class specifications, making fine-grained filtering impractical
- **Consistent Pattern**: This approach is consistent with how Node and ResourceClass events are handled (also without custom QueueingHintFn)
- **No API Changes**: ResourceSlice already exists in the API (k8s.io/api/resource/v1alpha2); infrastructure for listersand informers already exists
- **Backward Compatible**: Only adds new event handling, doesn't change existing behavior or APIs
- **Feature Gate Protected**: Plugin is only enabled when DynamicResourceAllocation feature is enabled (line 382)

## Related Code Paths

- **Schedule Entry**: pkg/scheduler/schedule_one.go:66 (ScheduleOne)
- **PreFilter Execution**: pkg/scheduler/schedule_one.go:453 (filterNodes)
- **DRA PreFilter Logic**: pkg/scheduler/framework/plugins/dynamicresources/dynamicresources.go:418
- **Event Handler Registration**: pkg/scheduler/eventhandlers.go:287 (addAllEventHandlers)
- **GVK Map Building**: pkg/scheduler/scheduler.go:525 (unionedGVKs)
- **Queue Re-trigger Mechanism**: pkg/scheduler/internal/queue/scheduling_queue.go (MoveAllToActiveOrBackoffQueue)
