# Kubernetes Scheduler ResourceSlice Event Handler Bug Analysis

## Files Examined
- `pkg/scheduler/schedule_one.go` — examined for entry point and failure handling mechanism
- `pkg/scheduler/eventhandlers.go` — examined for event handler registration
- `pkg/scheduler/scheduler.go` — examined for scheduler initialization and queue setup
- `pkg/scheduler/internal/queue/scheduling_queue.go` — examined for unschedulable pod re-evaluation mechanism
- `pkg/scheduler/framework/types.go` — examined for GVK constant definitions
- `pkg/scheduler/framework/plugins/dynamicresources/dynamicresources.go` — examined for DRA plugin event registration

## Dependency Chain

1. **Symptom observed in**: `pkg/scheduler/schedule_one.go` - `ScheduleOne()` method (line 66)
   - Pod with DRA device request cannot be scheduled because ResourceSlices don't exist yet
   - Pod is marked as Unschedulable and added to unschedulable queue

2. **Failure handling in**: `pkg/scheduler/schedule_one.go` - `handleSchedulingFailure()` method (line 1013)
   - Calls `sched.SchedulingQueue.AddUnschedulableIfNotPresent()` to add pod to unschedulable queue

3. **Pod re-evaluation triggered by**: `pkg/scheduler/internal/queue/scheduling_queue.go` - `MoveAllToActiveOrBackoffQueue()` (line 1120)
   - This method should be called when ResourceSlice events occur
   - It checks `isEventOfInterest()` to see if any plugin cares about the event

4. **Event interest check in**: `pkg/scheduler/internal/queue/scheduling_queue.go` - `isEventOfInterest()` (line 414)
   - Queries `p.queueingHintMap` to see if event is registered by any plugin
   - If event is not in map, returns false and unschedulable pods stay unscheduled

5. **Queueing hint map built from**: `pkg/scheduler/scheduler.go` - initialization (lines 315-320)
   - Built from `buildQueueingHintMap(profile.EnqueueExtensions())`
   - `EnqueueExtensions()` comes from plugins' `EventsToRegister()` methods

6. **Event handlers registered by**: `pkg/scheduler/eventhandlers.go` - `addAllEventHandlers()` (line 287)
   - Iterates through `gvkMap` and registers event handlers
   - Switch statement (line 396) handles known GVK types

## Root Cause

### **File**: `pkg/scheduler/framework/plugins/dynamicresources/dynamicresources.go`
### **Function**: `EventsToRegister()` (line 381)
### **Line**: ~410
### **Explanation**:
The dynamicresources plugin does not register ResourceSlice events in its `EventsToRegister()` method. The method registers events for:
- ResourceClaimParameters (line 389)
- ResourceClassParameters (line 390)
- ResourceClaim (line 393)
- PodSchedulingContext (line 396)
- Node (line 408)
- ResourceClass (line 410)

**But critically missing**: No registration for ResourceSlice events.

When a DRA driver starts AFTER a pod has been created and marked as unschedulable, the driver creates ResourceSlice objects. However, because ResourceSlice is not in the queueing hint map, the `isEventOfInterest()` check at `pkg/scheduler/internal/queue/scheduling_queue.go:171` returns false, causing `movePodsToActiveOrBackoffQueue()` to return early without re-evaluating unschedulable pods.

### **Secondary Issues**:

1. **File**: `pkg/scheduler/framework/types.go`
   - **Line**: ~96 (after ResourceClassParameters)
   - **Issue**: No `ResourceSlice` GVK constant is defined
   - All other DRA-related types are defined (ResourceClaim, ResourceClass, etc.) but ResourceSlice is missing

2. **File**: `pkg/scheduler/eventhandlers.go`
   - **Function**: `addAllEventHandlers()`
   - **Line**: ~515 (in the switch statement)
   - **Issue**: No case for handling ResourceSlice events
   - There's a case for each DRA type (PodSchedulingContext, ResourceClaim, ResourceClass, ResourceClaimParameters, ResourceClassParameters) but ResourceSlice is missing

## Proposed Fix

The fix requires three changes:

### 1. Add ResourceSlice GVK Constant
**File**: `pkg/scheduler/framework/types.go` (after line 96)

```diff
 	ResourceClaim           GVK = "ResourceClaim"
 	ResourceClass           GVK = "ResourceClass"
 	ResourceClaimParameters GVK = "ResourceClaimParameters"
 	ResourceClassParameters GVK = "ResourceClassParameters"
+	ResourceSlice           GVK = "ResourceSlice"
```

### 2. Register ResourceSlice Events in DRA Plugin
**File**: `pkg/scheduler/framework/plugins/dynamicresources/dynamicresources.go` (in EventsToRegister method, after line 410)

```diff
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
+		// ResourceSlices provide the actual resource availability on nodes.
+		// When a new ResourceSlice is available or updated, pods waiting for those resources
+		// may become schedulable.
+		{Event: framework.ClusterEvent{Resource: framework.ResourceSlice, ActionType: framework.Add | framework.Update}, QueueingHintFn: pl.isSchedulableAfterResourceSliceChange},
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
```

Also add the queueing hint function:

```diff
 // isSchedulableAfterPodSchedulingContextChange is invoked for add and update PodSchedulingContext events.
 // It checks whether that change made a previously unschedulable pod schedulable.
 func (pl *dynamicResources) isSchedulableAfterPodSchedulingContextChange(logger klog.Logger, pod *v1.Pod, oldObj, newObj interface{}) (framework.QueueingHint, error) {
 	// ... existing implementation
 }

+// isSchedulableAfterResourceSliceChange is invoked for add and update ResourceSlice events.
+// It checks whether that change made a previously unschedulable pod schedulable.
+// ResourceSlice changes are relevant for all pods using dynamic resources, as they may affect
+// which resources are available for allocation.
+func (pl *dynamicResources) isSchedulableAfterResourceSliceChange(logger klog.Logger, pod *v1.Pod, oldObj, newObj interface{}) (framework.QueueingHint, error) {
+	// If the pod doesn't use resource claims, it's not affected by ResourceSlice changes
+	if err := pl.foreachPodResourceClaim(pod, nil); err != nil {
+		// Pod has no resource claims, ResourceSlice change is not relevant
+		return framework.QueueSkip, nil
+	}
+	// ResourceSlice changes may affect available resources, so we queue the pod
+	// to re-evaluate scheduling. This is especially important when a DRA driver
+	// starts after the pod and publishes ResourceSlice objects.
+	return framework.Queue, nil
+}
```

### 3. Add Event Handler for ResourceSlice
**File**: `pkg/scheduler/eventhandlers.go` (in addAllEventHandlers switch statement, after ResourceClassParameters case at line 492)

```diff
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
```

## Analysis

### The Race Condition

The bug is a classic race condition in event-driven architectures:

1. **Working case (driver starts first)**:
   - Driver starts and creates ResourceSlice objects
   - Pod is created, requests DRA resources
   - Scheduler sees ResourceSlices exist and schedules pod successfully

2. **Broken case (pod created first)**:
   - Pod is created requesting DRA resources
   - Scheduler attempts scheduling, no ResourceSlices exist yet
   - Scheduling fails with "cannot allocate all claims" → pod marked Unschedulable
   - Pod added to unschedulable queue
   - Driver starts and creates ResourceSlice objects
   - ResourceSlice events are emitted BUT...
   - No event handler registered for ResourceSlice in the scheduler
   - `isEventOfInterest()` check returns false for ResourceSlice events
   - `movePodsToActiveOrBackoffQueue()` returns early at line 1171
   - Unschedulable pods are never re-evaluated
   - **Pod stuck in Pending/Unschedulable state forever**

### Why This Happened

The DynamicResourceAllocation feature was developed with multiple types of events:
- ResourceClaim: tracks allocation status
- ResourceClaimParameters: parameter changes
- ResourceClassParameters: parameter changes
- ResourceClass: class creation/modification
- PodSchedulingContext: driver status/resource hints

However, ResourceSlice (which actually advertises available resources on nodes) was not included in the event registration. This is a critical oversight because:

1. ResourceSlice is the actual signal that resources are available
2. Without it, the scheduler has no way to know that a DRA driver has started and made resources available
3. The unschedulable pod re-evaluation mechanism silently ignores ResourceSlice events because they're not in the queueing hint map

### The Fix

The fix adds ResourceSlice to the event handling pipeline at three levels:

1. **GVK definition**: Makes ResourceSlice a known resource type in the scheduler framework
2. **Plugin event registration**: The DRA plugin declares that it cares about ResourceSlice events (Add and Update actions)
3. **Event handler registration**: The scheduler registers informer event handlers to forward ResourceSlice events to the scheduling queue
4. **Queueing hint function**: Provides logic to determine if a ResourceSlice event should trigger pod re-scheduling

This ensures that when a DRA driver publishes ResourceSlices, the scheduler's scheduling queue is notified via `MoveAllToActiveOrBackoffQueue()`, checks `isEventOfInterest()` (which now returns true), and moves waiting unschedulable pods back to the active queue for re-evaluation.
