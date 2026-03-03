# Kubernetes Scheduler ResourceSlice Event Handler Bug - Analysis

## Files Examined

- `pkg/scheduler/schedule_one.go` — Entry point for scheduling cycle; calls `ScheduleOne()` which invokes `schedulingCycle()` that calls `SchedulePod()`, which eventually checks resource allocation status
- `pkg/scheduler/eventhandlers.go` — Registers event handlers for cluster resources; examined the `addAllEventHandlers()` function that sets up handlers for various resource types including Dynamic Resource Allocation resources
- `pkg/scheduler/framework/types.go` — Defines GVK (Group/Version/Kind) constants for all supported resource types and the `UnrollWildCardResource()` function
- `pkg/scheduler/framework/plugins/dynamicresources/dynamicresources.go` — DRA plugin that checks resource availability; examined the `EventsToRegister()` method that returns events that should trigger pod rescheduling
- `pkg/scheduler/scheduler.go` — Scheduler initialization (referenced for context)
- `staging/src/k8s.io/api/resource/v1alpha2/types.go` — ResourceSlice API type definition (confirmed it exists)

## Dependency Chain

1. **Symptom observed in**: `pkg/scheduler/schedule_one.go:111` — `schedulingCycle()` calls `SchedulePod()` which executes the plugin chain
2. **Plugin evaluation**: `pkg/scheduler/framework/plugins/dynamicresources/dynamicresources.go:418-423` — `PreEnqueue()` checks if all resource claims can be allocated
3. **Filter execution**: `pkg/scheduler/framework/plugins/dynamicresources/dynamicresources.go` — Filter phase checks if resources are available on nodes
4. **Event registration**: `pkg/scheduler/framework/plugins/dynamicresources/dynamicresources.go:381-413` — `EventsToRegister()` specifies which cluster events should trigger pod rescheduling
5. **Event handler setup**: `pkg/scheduler/eventhandlers.go:287-546` — `addAllEventHandlers()` registers informer handlers for cluster resource events
6. **GVK definition missing**: `pkg/scheduler/framework/types.go:64-106` — ResourceSlice is not defined as a framework GVK
7. **Bug triggered**: When a ResourceSlice is created/updated after a pod fails scheduling, **no event handler exists to notify the scheduler queue**

## Root Cause

**File**: `pkg/scheduler/framework/types.go`
**Function**: GVK constant definitions and `UnrollWildCardResource()`
**Line**: ~92-106 and ~177-193
**Explanation**:

The framework is missing a GVK constant for ResourceSlice. Although ResourceSlice objects exist in the Kubernetes API and are used by the DRA plugin to track available resources, they are not registered as a recognized cluster event type. This causes two downstream problems:

1. **Missing GVK constant** (line 92-96): The following GVK constants are defined for DRA:
   - `PodSchedulingContext`
   - `ResourceClaim`
   - `ResourceClass`
   - `ResourceClaimParameters`
   - `ResourceClassParameters`
   - **But NOT `ResourceSlice`**

2. **Missing in UnrollWildCardResource()** (line 187-191): The function that expands wildcard events includes ResourceClaim, ResourceClass, etc., but **NOT ResourceSlice**.

This cascades into two additional files where ResourceSlice events cannot be properly handled:

**Secondary Issue**: `pkg/scheduler/eventhandlers.go:395-543`
- The `addAllEventHandlers()` function has a switch statement that handles GVK types
- It has cases for ResourceClass, ResourceClaimParameters, ResourceClassParameters, etc.
- **But no case for ResourceSlice** — so even if ResourceSlice was a valid GVK, no informer handler would be registered

**Tertiary Issue**: `pkg/scheduler/framework/plugins/dynamicresources/dynamicresources.go:381-413`
- The `EventsToRegister()` method returns events that should trigger pod rescheduling
- It includes: ResourceClaimParameters, ResourceClassParameters, ResourceClaim, PodSchedulingContext, Node, ResourceClass
- **But NOT ResourceSlice** — so the plugin never signals the scheduler queue to retry pods when ResourceSlices are created/updated

## Proposed Fix

### Fix 1: Add ResourceSlice GVK constant

**File**: `pkg/scheduler/framework/types.go`

```diff
const (
	Pod GVK = "Pod"
	Node                    GVK = "Node"
	PersistentVolume        GVK = "PersistentVolume"
	PersistentVolumeClaim   GVK = "PersistentVolumeClaim"
	CSINode                 GVK = "storage.k8s.io/CSINode"
	CSIDriver               GVK = "storage.k8s.io/CSIDriver"
	CSIStorageCapacity      GVK = "storage.k8s.io/CSIStorageCapacity"
	StorageClass            GVK = "storage.k8s.io/StorageClass"
	PodSchedulingContext    GVK = "PodSchedulingContext"
	ResourceClaim           GVK = "ResourceClaim"
	ResourceClass           GVK = "ResourceClass"
	ResourceClaimParameters GVK = "ResourceClaimParameters"
	ResourceClassParameters GVK = "ResourceClassParameters"
+	ResourceSlice           GVK = "ResourceSlice"

	WildCard GVK = "*"
)
```

### Fix 2: Add ResourceSlice to UnrollWildCardResource()

**File**: `pkg/scheduler/framework/types.go`

```diff
func UnrollWildCardResource() []ClusterEventWithHint {
	return []ClusterEventWithHint{
		{Event: ClusterEvent{Resource: Pod, ActionType: All}},
		{Event: ClusterEvent{Resource: Node, ActionType: All}},
		{Event: ClusterEvent{Resource: PersistentVolume, ActionType: All}},
		{Event: ClusterEvent{Resource: PersistentVolumeClaim, ActionType: All}},
		{Event: ClusterEvent{Resource: CSINode, ActionType: All}},
		{Event: ClusterEvent{Resource: CSIDriver, ActionType: All}},
		{Event: ClusterEvent{Resource: CSIStorageCapacity, ActionType: All}},
		{Event: ClusterEvent{Resource: StorageClass, ActionType: All}},
		{Event: ClusterEvent{Resource: PodSchedulingContext, ActionType: All}},
		{Event: ClusterEvent{Resource: ResourceClaim, ActionType: All}},
		{Event: ClusterEvent{Resource: ResourceClass, ActionType: All}},
		{Event: ClusterEvent{Resource: ResourceClaimParameters, ActionType: All}},
		{Event: ClusterEvent{Resource: ResourceClassParameters, ActionType: All}},
+		{Event: ClusterEvent{Resource: ResourceSlice, ActionType: All}},
	}
}
```

### Fix 3: Add ResourceSlice event handler registration

**File**: `pkg/scheduler/eventhandlers.go`

```diff
	for gvk, at := range gvkMap {
		switch gvk {
		case framework.Node, framework.Pod:
			// Do nothing.
		case framework.CSINode:
			// ... handle CSINode ...
		// ... other cases ...
		case framework.ResourceClassParameters:
			if utilfeature.DefaultFeatureGate.Enabled(features.DynamicResourceAllocation) {
				if handlerRegistration, err = informerFactory.Resource().V1alpha2().ResourceClassParameters().Informer().AddEventHandler(
					buildEvtResHandler(at, framework.ResourceClassParameters, "ResourceClassParameters"),
				); err != nil {
					return err
				}
				handlers = append(handlers, handlerRegistration)
			}
+		case framework.ResourceSlice:
+			if utilfeature.DefaultFeatureGate.Enabled(features.DynamicResourceAllocation) {
+				if handlerRegistration, err = informerFactory.Resource().V1alpha2().ResourceSlices().Informer().AddEventHandler(
+					buildEvtResHandler(at, framework.ResourceSlice, "ResourceSlice"),
+				); err != nil {
+					return err
+				}
+				handlers = append(handlers, handlerRegistration)
+			}
		case framework.StorageClass:
			// ... handle StorageClass ...
```

### Fix 4: Register ResourceSlice events in DRA plugin

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
		// A resource might depend on node labels for topology filtering.
		// A new or updated node may make pods schedulable.
		{Event: framework.ClusterEvent{Resource: framework.Node, ActionType: framework.Add | framework.UpdateNodeLabel | framework.UpdateNodeTaint}},
		// A pod might be waiting for a class to get created or modified.
		{Event: framework.ClusterEvent{Resource: framework.ResourceClass, ActionType: framework.Add | framework.Update}},
+		// ResourceSlices published by drivers contain available resources.
+		// A new or updated ResourceSlice may make pods schedulable.
+		{Event: framework.ClusterEvent{Resource: framework.ResourceSlice, ActionType: framework.Add | framework.Update}, QueueingHintFn: pl.isSchedulableAfterResourceSliceChange},
	}
	return events
}
```

(Additionally, implement `pl.isSchedulableAfterResourceSliceChange()` method with similar logic to other change detection methods.)

## Analysis

### The Bug's Lifecycle

1. **Pod Creation**: A pod requesting DRA resources is created before the DRA driver starts
2. **Initial Scheduling Attempt** (line ~111 in schedule_one.go):
   - The scheduler calls `schedulingCycle()`
   - The DRA plugin's PreEnqueue/Filter phases check for available ResourceSlices
   - No ResourceSlices exist yet → pod marked as Unschedulable
3. **Pod Queuing**: The pod is added to the unschedulable queue with the reason "cannot allocate all claims"
4. **Driver Starts**: The DRA driver boots up and creates ResourceSlice objects to advertise available resources
5. **ResourceSlice Events (BUG HERE)**:
   - The ResourceSlice informer detects Add/Update events
   - But there is **NO event handler registered** for ResourceSlice (missing from eventhandlers.go)
   - Even if a handler existed, the **DRA plugin doesn't register for ResourceSlice events** (missing from EventsToRegister())
6. **Pod Stuck**: The scheduler never re-evaluates the pod because no one told the scheduler queue that something relevant changed
7. **Result**: Pod remains permanently in Unschedulable state despite resources now being available

### Why This Happens

The scheduler uses an event-driven architecture where cluster resources can trigger re-evaluation of unschedulable pods. The mechanism works like this:

1. When a pod fails scheduling, it's added to the `unschedulablePods` pool
2. When relevant cluster events occur (e.g., Node resource changes), the scheduler queue is notified
3. The queue calls `MoveAllToActiveOrBackoffQueue()` to retry unschedulable pods
4. For this to work, each plugin must register which events are relevant to it via `EventsToRegister()`
5. The scheduler framework must have event handlers that listen to those events and signal the queue

ResourceSlice events are critical for DRA scheduling because:
- ResourceSlices advertise node-local resources available to a driver
- When a driver starts, it publishes ResourceSlices showing what resources it manages
- Pods waiting for those resources need to be retried when the ResourceSlices appear
- Without this wiring, pods become permanently stuck

The fix is to add ResourceSlice to all three layers of event handling in the scheduler.
