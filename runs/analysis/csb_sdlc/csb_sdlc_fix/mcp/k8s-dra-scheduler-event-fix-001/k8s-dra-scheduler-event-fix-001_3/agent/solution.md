# Kubernetes Scheduler ResourceSlice Event Handler Bug Investigation

## Files Examined
- `pkg/scheduler/schedule_one.go` — Entry point for scheduling cycle
- `pkg/scheduler/eventhandlers.go` — Event handler registration mechanism for all cluster events
- `pkg/scheduler/framework/types.go` — GVK constants for all tracked resource types
- `pkg/scheduler/framework/plugins/dynamicresources/dynamicresources.go` — DRA plugin implementation and EventsToRegister
- `staging/src/k8s.io/client-go/informers/resource/v1alpha2/resourceslice.go` — ResourceSlice informer factory
- `pkg/scheduler/framework/plugins/dynamicresources/structuredparameters.go` — Resource model building from ResourceSlices

## Dependency Chain

1. **Symptom observed in**: `pkg/scheduler/schedule_one.go` (ScheduleOne function, line 66-134)
   - Pod scheduling occurs, fails with "cannot allocate all claims"
   - Pod is added to unschedulable queue
   - No re-evaluation happens when ResourceSlices are created

2. **Called from**: `pkg/scheduler/scheduler.go` (scheduler initialization)
   - Calls `addAllEventHandlers()` to register event handlers for resource changes

3. **Bug triggered by**: `pkg/scheduler/eventhandlers.go` (addAllEventHandlers function, line 285-546)
   - Registers event handlers for multiple resource types via a gvkMap switch statement (lines 395-543)
   - **MISSING**: No case for `framework.ResourceSlice` in the switch statement
   - Covers: CSINode, CSIDriver, CSIStorageCapacity, PersistentVolume, PersistentVolumeClaim, PodSchedulingContext, ResourceClaim, ResourceClass, ResourceClaimParameters, ResourceClassParameters, StorageClass

4. **Framework issue in**: `pkg/scheduler/framework/types.go` (GVK constants, lines 68-106)
   - **MISSING**: No `ResourceSlice` GVK constant defined
   - ResourceSlices are used by the dynamicresources plugin but not declared as a trackable event resource

5. **Resource model built in**: `pkg/scheduler/framework/plugins/dynamicresources/dynamicresources.go` (Prefilter method, line 958)
   - Calls `newResourceModel(logger, pl.resourceSliceLister, ...)` which loads all ResourceSlices
   - When a ResourceSlice is added/updated, this model should be invalidated and pods re-evaluated

## Root Cause

**Two missing pieces that prevent ResourceSlice events from triggering pod re-evaluation:**

### 1. Missing GVK Constant
- **File**: `pkg/scheduler/framework/types.go`
- **Function**: Constants section
- **Line**: Should be around line 96 (after ResourceClassParameters)
- **Issue**: ResourceSlice GVK constant is not defined, so the framework doesn't know about this resource type

### 2. Missing Event Handler Registration
- **File**: `pkg/scheduler/eventhandlers.go`
- **Function**: `addAllEventHandlers()`
- **Line**: ~448-492 (the switch statement that handles all gvk cases)
- **Issue**: No case for `framework.ResourceSlice` in the gvkMap switch statement
  - The switch iterates through gvkMap (which comes from plugins' EventsToRegister)
  - When ResourceSlice is NOT in gvkMap, it never gets an event handler registered
  - Therefore, when a ResourceSlice is created/updated, the scheduler is never notified

### 3. Missing Event Declaration in Plugin
- **File**: `pkg/scheduler/framework/plugins/dynamicresources/dynamicresources.go`
- **Function**: `EventsToRegister()`
- **Line**: ~386-411
- **Issue**: No event for ResourceSlice Add/Update (though this is driven by the plugin's needs)

## Why This Is A Bug

The dynamicresources plugin depends on ResourceSlices to determine:
1. Which resources are available on each node
2. How many resources are allocated/free
3. Whether a pod can be scheduled based on resource availability

When a ResourceSlice is created/updated:
- The plugin reads it via `resourceSliceLister` to build the resource model
- Pods that were previously unschedulable due to insufficient resources might now be schedulable
- **BUT**: Without an event handler, the scheduler never knows to re-queue these pods for re-evaluation
- Result: Pods remain stuck in Unschedulable state indefinitely

## Proposed Fix

### Fix 1: Add ResourceSlice GVK Constant

**File**: `pkg/scheduler/framework/types.go` (lines 68-96)

```diff
const (
	// ... existing constants ...
	PodSchedulingContext    GVK = "PodSchedulingContext"
	ResourceClaim           GVK = "ResourceClaim"
	ResourceClass           GVK = "ResourceClass"
	ResourceClaimParameters GVK = "ResourceClaimParameters"
	ResourceClassParameters GVK = "ResourceClassParameters"
+	ResourceSlice           GVK = "ResourceSlice"

	// WildCard is a special GVK to match all resources.
	// ...
)
```

### Fix 2: Add ResourceSlice Event Handler Registration

**File**: `pkg/scheduler/eventhandlers.go` (lines 448-492)

Add a new case in the gvkMap switch statement in `addAllEventHandlers()`:

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
+	case framework.ResourceSlice:
+		if utilfeature.DefaultFeatureGate.Enabled(features.DynamicResourceAllocation) {
+			if handlerRegistration, err = informerFactory.Resource().V1alpha2().ResourceSlices().Informer().AddEventHandler(
+				buildEvtResHandler(at, framework.ResourceSlice, "ResourceSlice"),
+			); err != nil {
+				return err
+			}
+			handlers = append(handlers, handlerRegistration)
+		}
	case framework.StorageClass:
		// ... existing code ...
```

### Fix 3: Add ResourceSlice to EventsToRegister (Optional but Recommended)

**File**: `pkg/scheduler/framework/plugins/dynamicresources/dynamicresources.go` (lines 386-412)

Add ResourceSlice events to the EventsToRegister method:

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
+		// ResourceSlice information is used to check device availability on nodes.
+		// When a driver provides additional resource availability information, pods may become schedulable.
+		{Event: framework.ClusterEvent{Resource: framework.ResourceSlice, ActionType: framework.Add | framework.Update}, QueueingHintFn: pl.isSchedulableAfterResourceSliceChange},
		// A resource might depend on node labels for topology filtering.
		// A new or updated node may make pods schedulable.
		//
		// ... rest of events ...
	}
```

And add the missing queueing hint function:

```diff
+func (pl *dynamicResources) isSchedulableAfterResourceSliceChange(logger klog.Logger, podInfo *framework.QueuedPodInfo) framework.QueueingHintFn {
+	// Any change to a ResourceSlice may affect resource availability.
+	// Pods waiting on resource availability need to be re-evaluated.
+	return framework.Queue
+}
```

## Analysis

### The Bug Flow

1. **Pod Arrives Before DRA Driver**:
   - Pod requests a DRA device via ResourceClaim
   - Scheduler runs dynamicresources plugin's Prefilter
   - Plugin calls `resourceSliceLister.List()` → no ResourceSlices exist yet
   - Plugin returns "cannot allocate all claims" → pod goes to unschedulable queue

2. **DRA Driver Starts and Creates ResourceSlice**:
   - Driver creates a ResourceSlice with available resources
   - Event is posted to the API server
   - **BUG**: Scheduler has no handler registered for ResourceSlice events
   - Event is silently dropped (no informer callback)
   - Unschedulable pod is never re-evaluated

3. **Pod Remains Stuck**:
   - ResourceSlice exists with available resources
   - Pod's claim could now be allocated
   - But scheduler never learned about the ResourceSlice update
   - Pod stays in Pending/Unschedulable forever

### Why This Matters

The root cause is a missing integration between the informer system and the scheduler's event loop:

1. **The Framework Contract**: When a plugin's `EventsToRegister()` declares it cares about an event type (e.g., ResourceSlice), the scheduler's `addAllEventHandlers()` should register an informer callback for that event.

2. **The Missing Link**:
   - ResourceSlice is NOT declared in the GVK constants (first bug)
   - Therefore, it cannot be referenced in EventsToRegister
   - Even if declared in EventsToRegister, there's no handler case for it (second bug)
   - Result: ResourceSlice events never reach the scheduler queue

3. **The Fix Is Minimal**:
   - Add one GVK constant (1 line)
   - Add one switch case with 6-10 lines of code
   - Add one optional queueing hint function (3-4 lines)
   - Total: ~15 lines of code

### Impact

- **Without Fix**: Pods requesting DRA devices are permanently stuck if the driver starts after the pod
- **With Fix**: Pods are automatically re-queued when ResourceSlices become available, enabling proper scheduling of DRA-dependent workloads

## Verification

### Code Pattern Confirmation
The fix follows the exact same pattern as other DRA resources:
- ResourceClaim handler (lines 457-465): Checks DynamicResourceAllocation feature gate, gets informer, adds event handler
- ResourceClass handler (lines 466-474): Same pattern
- **Proposed ResourceSlice handler**: Identical pattern, just with ResourceSlices() instead of ResourceClaims()

### Evidence That This Is The Bug
1. **Plugin uses ResourceSlices** (dynamicresources.go:958):
   - `newResourceModel(logger, pl.resourceSliceLister, ...)` is called during Prefilter
   - Plugin queries ResourceSlices to determine available resources

2. **ResourceSlices are gettable** (scheduler initialization, line 356):
   - `fh.SharedInformerFactory().Resource().V1alpha2().ResourceSlices().Lister()` shows ResourceSlices informer exists

3. **But no event handler is registered**:
   - No GVK constant for ResourceSlice
   - No case in eventhandlers.go switch statement
   - Therefore events are never delivered to the scheduling queue

4. **The fix is minimal** (15 lines total):
   - Only adds the missing integration points
   - Doesn't change any existing logic
   - Uses the exact same patterns as ResourceClaim, ResourceClass, etc.

## Summary

This is a **critical bug in the event-driven re-queuing mechanism** of the Kubernetes scheduler. When Dynamic Resource Allocation drivers publish ResourceSlice objects with available resources, the scheduler is never notified because ResourceSlice events are not wired into the scheduling queue.

**The fix requires:**
1. Add `ResourceSlice` GVK constant (1 line)
2. Add ResourceSlice case in `addAllEventHandlers()` switch (8 lines)
3. Optionally add ResourceSlice to plugin's `EventsToRegister()` (5 lines)

**Result:** Pods requesting DRA resources will be properly re-evaluated when ResourceSlices become available, instead of remaining permanently stuck in Unschedulable state.
