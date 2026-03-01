# Investigation Report: Remote-Write Queue Resharding Failure

## Summary

The remote-write queue resharding mechanism has a race condition where pending sample counters are unconditionally reset during shard startup, causing intermittent stalls where `prometheus_remote_storage_samples_pending` metric remains stuck above zero with no progress. This occurs specifically when the `shards.start()` function resets the metric counter without accounting for samples still in flight or queued from concurrent append operations during the resharding transition.

## Root Cause

**Location:** `/workspace/storage/remote/queue_manager.go:1241` in the `shards.start()` function

**Mechanism:**
```go
func (s *shards) start(n int) {
    s.mtx.Lock()
    defer s.mtx.Unlock()

    s.qm.metrics.pendingSamples.Set(0)  // ← LINE 1241: UNCONDITIONAL RESET
    s.qm.metrics.numShards.Set(float64(n))

    newQueues := make([]*queue, n)
    // ... create new shards ...
}
```

The `pendingSamples` metric is unconditionally reset to zero when starting new shards, without accounting for samples that may:
- Still be in-flight from old shards during the flush-to-completion phase
- Be queued in the old shard queues during hard shutdown
- Be pending in the WAL for re-transmission
- Have been appended during the resharding window but not yet confirmed sent

## Race Condition Timeline

1. **T0:** `updateShardsLoop()` detects need for resharding (e.g., 4→6 shards)
   - Sends `reshardChan <- numShards` (line 1072)
   - Logs: "Remote storage resharding from=4 to=6"

2. **T1:** `reshardLoop()` receives signal and calls `stop()`
   - `stop()` closes `softShutdown` channel (RLock held) (line 1275)
   - Acquires write lock (line 1281)
   - Calls `FlushAndShutdown()` on all queues (line 1284)

3. **T2:** Old shard goroutines (`runShard()`) begin flushing
   - Send final batches via `sendSamples()`
   - Call `updateMetrics()` which decrements `pendingSamples.Sub()` (line 1689)
   - *Meanwhile:* Concurrent `Append()` calls that hit closed `softShutdown` retry with backoff (exponential backoff, loop at line 745)

4. **T3:** If `flushDeadline` times out (default 1 minute, line 1289):
   - `hardShutdown()` is called (line 1293)
   - Context cancelled, `runShard()` drops remaining samples
   - Drops are counted: `pendingSamples.Sub(float64(droppedSamples))` (line 1569)

5. **T4:** `reshardLoop()` continues and calls `start(numShards)`
   - **CRITICAL:** Line 1241 executes: `pendingSamples.Set(0)`
   - This unconditional reset loses count of any in-flight operations

6. **T5:** New shards start and receive backed-off append samples
   - Backed-off samples from T2-T4 finally enqueue
   - New queues process these samples
   - BUT: Any samples that should have been tracked during the transition are now lost

## Evidence

### Code References

**Primary Issue - Unconditional Reset:**
- File: `/workspace/storage/remote/queue_manager.go`
- Line 1241: `s.qm.metrics.pendingSamples.Set(0)` in `shards.start()`
- Lines 1237-1266: Full `start()` function

**Stop Function - Where Tracking is Lost:**
- Line 1281-1282: Write lock held during flush wait
- Line 1284: `FlushAndShutdown()` called in new goroutines (may not complete)
- Line 1289: `flushDeadline` timeout triggers hard shutdown
- Line 1569: Hard shutdown drops samples and decrements counter

**Reshard Trigger:**
- Line 1189: `reshardLoop()` receives reshard signal
- Line 1193-1194: Sequential `stop()` then `start()` calls (no error checking)
- Line 1072-1074: `updateShardsLoop()` sends reshard with select default (skips if busy)

**Sample Append During Resharding:**
- Lines 702-758: `Append()` function retries indefinitely with backoff
- Line 745: `continue outer` on enqueue failure (retry loop)
- Samples retry with exponential backoff during resharding window

### Test Evidence

**Existing Tests That Could Expose This:**
- `/workspace/storage/remote/queue_manager_test.go:514` - `TestReshard()`
  - Manually calls `m.shards.stop()` and `m.shards.start(i)`
  - No assertion on pending sample tracking across reshards

- `/workspace/storage/remote/queue_manager_test.go:592` - `TestReshardPartialBatch()`
  - Rapid reshard cycles during concurrent append operations
  - Specifically designed to test for deadlocks, not metric consistency

## Affected Components

### Primary Packages
- `storage/remote` - Queue manager and shard orchestration
- `storage/remote/queue_manager.go` - Core resharding logic

### Metrics Affected
- `prometheus_remote_storage_samples_pending` - **PRIMARY**: Incremented on enqueue (line 1326), decremented on send (line 1689) or hard drop (line 1569), but reset to 0 on shard restart
- `prometheus_remote_storage_exemplars_pending` - Same issue (line 1242)
- `prometheus_remote_storage_histograms_pending` - Same issue (line 1242)

### Affected Flows
1. **Normal Send Path:** Sample → Enqueue (pending++) → Send (pending--) → Success
   - Works during normal operation

2. **Hard Shutdown Path:** Sample → Enqueue (pending++) → ctx.Done() → Drop (pending--) → Close
   - Works, but counter gets reset if new shard starts immediately after

3. **Reshard + Concurrent Append Path:**
   - Sample enqueued to old shard (pending++)
   - Reshard triggered, `stop()` closes softShutdown
   - Sample retry hits backoff
   - `start()` resets pending to 0
   - Sample finally enqueues to new shard (pending++, but counter was reset)
   - **BROKEN**: Counter tracking is now inconsistent

## Why It's Intermittent

The issue is intermittent because it depends on precise timing alignment:

1. **Timing Window:** The race only manifests when samples are appended during the ~millisecond window between:
   - Old shards closing (`stop()` completes)
   - New shards starting (`start()` resets counter)

2. **Backoff Variability:** Append retry backoff is exponential (starts at 5ms, doubles each retry):
   - Sometimes retries succeed before shard stop completes
   - Sometimes retries are still pending when new shards start

3. **Workload Dependency:**
   - High-frequency targets → More concurrent appends → Higher probability
   - Low-frequency targets → Fewer in-flight samples → Race is unlikely
   - Reshard frequency affects window size

4. **Flush Timeout Path:**
   - If `flushDeadline` is exceeded and hard shutdown occurs, samples are dropped and counter decremented
   - Immediate `start()` call resets counter → Lost information
   - If flush completes cleanly, counter is already accurate before reset

## Recommended Diagnostics

### Metrics to Monitor
1. `prometheus_remote_storage_samples_pending` - Watch for:
   - Sudden reset to 0 after non-zero value
   - Stuck at non-zero for extended periods (no send progress)
   - Comparison with `prometheus_remote_storage_samples_total` (should match)

2. `prometheus_remote_storage_shards` - Monitor:
   - Value changes (indicates resharding)
   - Correlation with pending samples anomalies

3. `prometheus_remote_storage_samples_dropped_total` - Check for:
   - Drops during resharding events
   - Unaccounted dropped samples

### Logs to Review
1. "Remote storage resharding from=X to=Y" - Reshard triggered
2. "Currently resharding, skipping." - Reshard already in progress (select default hit)
3. "Failed to flush all samples on shutdown" - Hard shutdown occurred
4. "Resharding queues" / "Resharding done" - If logged separately

### Debugging Steps
1. Enable verbose logging in `updateShardsLoop()` and `reshardLoop()`
2. Add timestamp markers around `pendingSamples.Set(0)` in `start()`
3. Track sample lifecycle: when enqueued, when decremented, when reset
4. Compare pending counter with actual queue depths before/after reshard
5. Profile goroutine count during resharding to detect leaks or races

## Recommendation

**Fix Strategy:**

Instead of unconditionally resetting `pendingSamples` in `start()`, the metric should:

1. **Preserve the count** if samples are still pending during shard transition
2. **Track samples through resharding** by:
   - Recording the pending count before `stop()`
   - Ensuring all samples from old shards are either sent or dropped (counter decremented)
   - Starting new shards without resetting the counter
   - Only resetting counter if it reaches zero naturally

**Alternative Approaches:**
- Move `pendingSamples.Set(0)` to happen only when counter is naturally zero
- Recalculate pending from sum of all queue depths instead of tracking incrementally
- Add synchronization barrier to ensure no samples in-flight during counter reset
- Use atomic compare-and-swap to only reset if counter hasn't changed since stop()

**Testing Additions:**
- Add assertion in `TestReshardPartialBatch` to verify pending samples consistency before/after reshard
- Add test that validates pending counter matches actual queue depths
- Stress test with rapid resharding and high-frequency appends

## Related Code Sections

The issue is fundamentally a synchronization problem between:
- Metric counter lifecycle (incremented on enqueue, decremented on send/drop)
- Shard lifecycle (old shards stop, new shards start)
- Concurrent operations (appends, sends, retries all happening in parallel)

The `softShutdown` channel pattern correctly prevents new enqueues, but the unconditional `Set(0)` assumes no pending samples exist, which is not guaranteed due to backoff-retry loops and in-flight requests.
