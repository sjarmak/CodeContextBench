# Investigation Report: Remote-Write Queue Resharding Failure

## Summary

During remote-write queue resharding triggered by target discovery changes, samples pending in flight batches are lost when the resharding hard shutdown cancels the context mid-send. However, metric update logic still executes, incorrectly decrementing `prometheus_remote_storage_samples_pending` despite the samples never reaching the remote endpoint. This causes pending counters to become inaccurate and manifests as shards stalling with samples stuck in pending state.

---

## Root Cause

**File:** `storage/remote/queue_manager.go`
**Mechanism:** Context-cancellation race condition during batch sending in resharding

### The Bug

1. **Lines 1789-1792** in `sendSamplesWithBackoff()`: When the context is cancelled during resharding, the function returns early with `context.Canceled` error:
   ```go
   if errors.Is(err, context.Canceled) {
       // When there is resharding, we cancel the context for this queue,
       // which means the data is not sent.
       // So we exit early to not update the metrics.
       return accumulatedStats, err
   }
   ```

   The comment clearly states the intent: "exit early to not update the metrics"

2. **Lines 1645-1649** in `sendSamples()`: Despite the early return, the **calling function always updates metrics**:
   ```go
   func (s *shards) sendSamples(ctx context.Context, ...) error {
       begin := time.Now()
       rs, err := s.sendSamplesWithBackoff(ctx, ...)
       s.updateMetrics(ctx, err, sampleCount, ...)  // ALWAYS called
       return err
   }
   ```

3. **Lines 1687-1691** in `updateMetrics()`: Metrics are decremented **regardless of the error**:
   ```go
   // Pending samples/exemplars/histograms also should be subtracted, as an error means
   // they will not be retried.
   s.qm.metrics.pendingSamples.Sub(float64(sampleCount))
   s.qm.metrics.pendingExemplars.Sub(float64(exemplarCount))
   s.qm.metrics.pendingHistograms.Sub(float64(histogramCount))
   ```

### The Race Condition

When resharding occurs (**lines 1189-1194** in `reshardLoop()`):
```go
case numShards := <-t.reshardChan:
    t.shards.stop()        // Close softShutdown, start FlushAndShutdown
    t.shards.start(numShards)  // Create new shards
```

**Sequence of events:**

1. **Target discovery triggers resharding** - `updateShardsLoop()` sends new shard count to `reshardChan`
2. **`stop()` called** (lines 1269-1305):
   - Closes `softShutdown` to prevent new enqueues (line 1275)
   - Spawns `FlushAndShutdown()` goroutines for each queue (line 1284)
   - Waits up to `flushDeadline` for clean shutdown (line 1289)
   - If deadline expires, calls `hardShutdown()` to cancel context (line 1293)

3. **Context cancellation during in-flight sends**:
   - If a batch is currently being sent when `hardShutdown()` cancels the context:
     - `sendSamplesWithBackoff()` returns with `context.Canceled` (line 1792)
     - `sendSamples()` still calls `updateMetrics()` (line 1648)
     - `pendingSamples` counter is decremented (line 1689)
   - **But the batch was never sent to the remote endpoint**

4. **New shards created** (lines 1237-1266 in `start()`):
   - Fresh queues created with empty pending counts
   - New `runShard()` goroutines start with new context
   - Enqueued counters reset to 0 (line 1256)

5. **Partial batches lost**:
   - Partial batches in `queue.batch` never get sent
   - They're lost when `FlushAndShutdown()` fails to enqueue them before hard shutdown
   - Their samples were already decremented from `pendingSamples` (incorrectly)

---

## Evidence

### Code References

| Component | Location | Issue |
|-----------|----------|-------|
| Context cancellation handling | `queue_manager.go:1789-1792` | Early return with `context.Canceled` |
| Metrics always updated | `queue_manager.go:1645-1649` | `updateMetrics()` called unconditionally |
| Metrics decremented | `queue_manager.go:1687-1691` | No check for `context.Canceled` error |
| Resharding trigger | `queue_manager.go:1189-1194` | `stop()` then `start()` sequence |
| Hard shutdown | `queue_manager.go:1269-1305` | Context cancelled in `stop()` |
| Partial batch handling | `queue_manager.go:1422-1434` | `Batch()` returns partial and allocates new |
| Flush logic | `queue_manager.go:1447-1455` | `FlushAndShutdown()` tries to enqueue pending |

### Timing Window

The bug manifests only when:
1. **Resharding happens during active sends** - A batch must be in-flight when `hardShutdown()` is called
2. **Timeout expires before flush completes** - `flushDeadline` expires, triggering hard shutdown
3. **Context cancellation interrupts send** - The ongoing send operation is aborted

### Metric Behavior

- `prometheus_remote_storage_samples_pending` shows stuck value > 0
- Actual samples never received by remote endpoint (but metrics indicate they were processed)
- Over time, the counter becomes increasingly inaccurate
- New incoming samples are processed normally (adding to pending count)
- But total pending never decreases correctly

---

## Affected Components

1. **`storage/remote/queue_manager.go`**
   - `QueueManager.reshardLoop()` - Orchestrates resharding
   - `shards.stop()` / `shards.start()` - Shard lifecycle during resharding
   - `shards.sendSamples()` - Sends batches and updates metrics
   - `sendSamplesWithBackoff()` - Handles context cancellation
   - `updateMetrics()` - Updates pending sample counters

2. **`storage/remote/queue_manager_test.go`**
   - Test case `TestBlockingWriteClient` (line 1312-1316) shows context being used for cancellation
   - Potentially missing test for `context.Canceled` in `sendSamples()`

3. **Metrics Affected**
   - `prometheus_remote_storage_samples_pending`
   - `prometheus_remote_storage_exemplars_pending`
   - `prometheus_remote_storage_histograms_pending`
   - `prometheus_remote_storage_samples_failed_total` (might be double-counted)

---

## Why the Issue is Intermittent

The race condition only manifests when **all three conditions occur simultaneously**:

1. **Resharding is triggered** while targets are changing (target discovery events)
2. **Batches are in-flight** to the remote endpoint at the exact moment of resharding
3. **`flushDeadline` expires** before pending batches can be flushed (default 30s as per `MinBackoff` config)

Network latency and remote endpoint response time directly affect probability:
- Slow remote endpoint → higher likelihood of in-flight batches during resharding
- High resharding frequency → more opportunities for collision
- Partial failures/retries → increase timeout likelihood

---

## Diagnostic Steps to Confirm Root Cause

1. **Enable debug logging in queue_manager**:
   ```
   log level=debug
   ```
   Watch for "Resharding" and "Remote Send Batch" log entries timing alignment

2. **Monitor these metrics during target discovery changes**:
   - `prometheus_remote_storage_samples_pending` - should decrease as samples are sent
   - `prometheus_remote_storage_sent_bytes_total` - should increase while pending decreases
   - `prometheus_remote_storage_failed_samples_total` - track actual failures
   - `prometheus_remote_storage_samples_dropped_on_hard_shutdown` - non-zero indicates premature shutdown

3. **Correlate logs**:
   ```
   level=info msg="Resharding queues" from=? to=?
   level=info msg="Resharding done"
   # Check if any remote send errors occur between these lines
   ```

4. **Test with slow remote endpoint**:
   - Use `iptables tc` or proxy to add latency
   - Trigger target discovery changes
   - Observe if `samples_pending` gets stuck

5. **Check for partial sends**:
   - Enable remote write response parsing
   - Compare `samples_sent_total` vs actual samples received by endpoint

---

## Recommendation

**Fix Strategy**: Prevent `updateMetrics()` from being called when `sendSamplesWithBackoff()` returns `context.Canceled`.

**Change Required** in `sendSamples()` function (lines 1645-1649):

Instead of:
```go
rs, err := s.sendSamplesWithBackoff(ctx, samples, sampleCount, exemplarCount, histogramCount, 0, pBuf, buf, compr)
s.updateMetrics(ctx, err, sampleCount, exemplarCount, histogramCount, 0, rs, time.Since(begin))
return err
```

Should be:
```go
rs, err := s.sendSamplesWithBackoff(ctx, samples, sampleCount, exemplarCount, histogramCount, 0, pBuf, buf, compr)
// Don't update metrics if context was cancelled during resharding - data was not sent
if !errors.Is(err, context.Canceled) {
    s.updateMetrics(ctx, err, sampleCount, exemplarCount, histogramCount, 0, rs, time.Since(begin))
}
return err
```

This ensures:
1. Samples lost during resharding don't decrement pending counters
2. Counters remain accurate
3. Samples are properly retried on new shards post-resharding

**Additional Hardening**:
- Add metric tracking for samples dropped on hard shutdown
- Ensure `lastSendTimestamp` is updated correctly even on cancellation
- Consider implementing a pre-resharding check: don't reshard if batches are in-flight
