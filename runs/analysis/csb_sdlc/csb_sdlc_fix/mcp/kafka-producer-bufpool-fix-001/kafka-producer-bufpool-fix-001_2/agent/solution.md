## Files Examined
- clients/src/main/java/org/apache/kafka/clients/producer/internals/Sender.java — entry point for tracing bug, contains sendProducerData() and failBatch() methods
- clients/src/main/java/org/apache/kafka/clients/producer/internals/RecordAccumulator.java — manages batch lifecycle and buffer allocation/deallocation
- clients/src/main/java/org/apache/kafka/clients/producer/internals/BufferPool.java — pooled ByteBuffer management
- clients/src/main/java/org/apache/kafka/clients/NetworkClient.java — network request handling, where Send is actually built
- clients/src/main/java/org/apache/kafka/common/protocol/SendBuilder.java — builds Send objects with zero-copy buffer references

## Dependency Chain
1. **Symptom observed in**: Users report messages from topic A appearing on topic B (rare, bursts during network disruption)
2. **Called from**: Sender.java `sendProducerData()` (line 357-443)
3. **Critical section 1**: Lines 395-396 - Batches are drained from accumulator and added to inflight batches
4. **Critical section 2**: Lines 406-408 - Expired inflight batches are identified
5. **Critical section 3**: Lines 418-422 - `failBatch()` is called for expired batches, triggering deallocation
6. **Bug triggered by**: RecordAccumulator.java `deallocate()` (line 1027-1033) and BufferPool.java `deallocate()` (line 260-275)
7. **Race occurs during**: NetworkClient.java `doSend()` (line 601-618), specifically at line 608 where `request.toSend()` is called
8. **Buffer reuse happens in**: BufferPool.java `allocate()` (line 107-175), at lines 124-125 where free buffers are immediately reused

## Root Cause

### File: clients/src/main/java/org/apache/kafka/clients/producer/internals/Sender.java
### Function: sendProducerData() and failBatch()
### Lines: ~418 (in sendProducerData) → ~835 (in failBatch) → line 174 (in maybeRemoveAndDeallocateBatch)

### Explanation

**The Bug:**
When an in-flight `ProducerBatch` (one that has been sent to the network but hasn't received a response) expires due to delivery timeout, the batch's pooled `ByteBuffer` is immediately deallocated and returned to the `BufferPool`. The deallocation happens BEFORE the network Send object is fully constructed and transmitted. This creates a race condition where:

1. At line 395-396 of `sendProducerData()`: A batch is drained from the accumulator and immediately added to `inFlightBatches`
2. At line 442: `sendProduceRequests()` enqueues the request with the batch's `MemoryRecords`
3. Between sendProducerData() return and the NEXT client.poll() call: The batch is checked for expiration
4. At line 406: `getExpiredInflightBatches()` returns batches that have exceeded delivery timeout
5. At line 418: `failBatch()` is called for the expired batch
6. In `failBatch()` at line 835: `maybeRemoveAndDeallocateBatch()` is called
7. In `maybeRemoveAndDeallocateBatch()` at line 174: `accumulator.deallocate(batch)` is called
8. In `RecordAccumulator.deallocate()` at line 1032: `free.deallocate(batch.buffer(), ...)` returns the buffer to `BufferPool`
9. At `BufferPool.deallocate()` line 264-265: The buffer is cleared and added back to the free list
10. **Critical Race**: Before the client.poll() call completes, when `NetworkClient.doSend()` finally processes the queued request:
    - At line 608: `request.toSend(header)` is called
    - This calls `SendBuilder.buildRequestSend()` → `buildSend()` (line 208-225)
    - At line 223: `apiMessage.write()` serializes the ProduceRequestData
    - This eventually calls `SendBuilder.writeRecords()` (line 137-148)
    - At line 140: `addBuffer(((MemoryRecords) records).buffer())` gets the batch's buffer reference
    - **BUT** the buffer has already been deallocated and reused by a NEW batch for a different topic!

11. **The Corruption**: The Send object now contains a reference to a buffer that:
    - Was originally allocated for batch A on topic X
    - Has been deallocated and is now being used by batch B on topic Y
    - Contains data for topic Y instead of topic X
    - The request header still says "topic X", but the record data is from "topic Y"

12. When the Send is written to the network, the broker receives a Produce request with:
    - Header: Topic X, Partition N
    - Records: Data from Topic Y
    - Result: Messages intended for topic X are persisted to topic Y

### Why Topic Name Is Corrupted (Not Just Data)

The critical issue is in `SendBuilder.writeRecords()`. It stores a **reference** to the buffer, not a copy. When `ProduceRequestData` is serialized during `buildSend()`, the `MemoryRecords.buffer()` is accessed at line 140. If the buffer has been reused, it contains different data AND possibly has been reset to position 0 with new record content, so even the record structure itself may have changed.

## Proposed Fix

The fix is to **prevent deallocating in-flight batches that are still pending transmission**. There are two approaches:

### Approach 1: Don't deallocate pending inflight batches when they expire (RECOMMENDED)

In `Sender.failBatch()`, check if the batch has a pending request in the network layer. If so, don't deallocate it immediately - let the response handler deallocate it instead.

```diff
private void failBatch(
    ProducerBatch batch,
    RuntimeException topLevelException,
    Function<Integer, RuntimeException> recordExceptions,
    boolean adjustSequenceNumbers
) {
    this.sensors.recordErrors(batch.topicPartition.topic(), batch.recordCount);

    if (batch.completeExceptionally(topLevelException, recordExceptions)) {
        if (transactionManager != null) {
            try {
                // This call can throw an exception in the rare case that there's an invalid state transition
                // attempted. Catch these so as not to interfere with the rest of the logic.
                transactionManager.handleFailedBatch(batch, topLevelException, adjustSequenceNumbers);
            } catch (Exception e) {
                log.debug(\"Encountered error when transaction manager was handling a failed batch\", e);
            }
        }
-       maybeRemoveAndDeallocateBatch(batch);
+       // Don't deallocate inflight batches immediately - their buffer may still be referenced by
+       // a Send object that hasn't been fully transmitted. Wait for the response handler to deallocate.
+       maybeRemoveFromInflightBatches(batch);
    }
}
```

### Approach 2: Don't expire inflight batches in sendProducerData() - let them timeout at the request level

In `sendProducerData()`, skip expiring batches that are in the inflight set. They will eventually timeout at the request timeout level and be cleaned up by `handleProduceResponse()` with appropriate errors.

```diff
List<ProducerBatch> expiredBatches = this.accumulator.expiredBatches(now);
expiredBatches.addAll(expiredInflightBatches);

// Reset the producer id if an expired batch has previously been sent to the broker. Also update the metrics
// for expired batches. see the documentation of @TransactionState.resetIdempotentProducerId to understand why
// we need to reset the producer id here.
if (!expiredBatches.isEmpty())
    log.trace(\"Expired {} batches in accumulator\", expiredBatches.size());
for (ProducerBatch expiredBatch : expiredBatches) {
+   // Don't fail/deallocate inflight batches - they will be cleaned up when their response arrives
+   // or when the request times out in NetworkClient
+   if (inFlightBatches.containsValue(expiredBatch))
+       continue;
+
    String errorMessage = \"Expiring \" + expiredBatch.recordCount + \" record(s) for \" + expiredBatch.topicPartition
        + \":\" + (now - expiredBatch.createdMs) + \" ms has passed since batch creation\";
    failBatch(expiredBatch, new TimeoutException(errorMessage), false);
    if (transactionManager != null && expiredBatch.inRetry()) {
        // This ensures that no new batches are drained until the current in flight batches are fully resolved.
        transactionManager.markSequenceUnresolved(expiredBatch);
    }
}
```

**Approach 1 is recommended** because:
- It's simpler and more direct
- It only changes the deallocation path, not the expiration logic
- It maintains consistent error handling (the batch is still marked as failed)
- The batch will eventually be deallocated when the response arrives

## Analysis

### Detailed Trace from Symptom to Root Cause

1. **User Observation (Symptom)**: "Messages published to topic A occasionally appear on topic B"
   - CRC checksum passes because it covers key/value/headers, not topic name
   - Occurs in bursts during broker restarts/network disruptions
   - Indicates buffer content corruption at the Produce request level

2. **System Behavior**:
   - Producer has `linger.ms > 0` configured
   - Network experiences delays or broker becomes slow to respond
   - Some batches timeout before their request is fully transmitted

3. **sendProducerData() Execution (Lines 357-443)**:
   - Line 395: `accumulator.drain()` gets batches ready to send (removes them from accumulator)
   - Line 396: `addToInflightBatches(batches)` adds them to tracking map with topic/partition keys
   - Line 442: `sendProduceRequests()` enqueues the request (but doesn't wait for transmission)
   - Function returns

4. **Buffer State After sendProducerData()**:
   - Batch is in `inFlightBatches` (tracked but not yet transmitted)
   - Batch's `MemoryRecords` holds the data in a pooled `ByteBuffer`
   - Request is queued in `NetworkClient` but not yet converted to Send

5. **Expiration Check (Lines 406-408)**:
   - `getExpiredInflightBatches()` scans `inFlightBatches` for timeouts
   - A batch that was added in step 1 now exceeds `deliveryTimeoutMs`
   - It's returned as expired

6. **Batch Failure & Deallocation (Line 418-835)**:
   - `failBatch()` is called with the expired inflight batch
   - `batch.completeExceptionally()` marks it as failed
   - `maybeRemoveAndDeallocateBatch()` is called
   - `accumulator.deallocate(batch)` removes it from incomplete set and frees the buffer
   - `BufferPool.deallocate()` clears the buffer and adds it to the free list

7. **Buffer Reuse (BufferPool.allocate, line 124-125)**:
   - Next batch (for topic B) calls `allocate()`
   - Free list has a buffer of matching size available
   - `this.free.pollFirst()` returns the same buffer that was just deallocated
   - New batch writes its records to this buffer

8. **Send Object Construction (NetworkClient.doSend, line 608)**:
   - The queued request from step 4 is finally processed
   - `request.toSend(header)` is called
   - `SendBuilder.buildSend()` serializes the request data
   - `SendBuilder.writeRecords()` is called with the original MemoryRecords
   - `((MemoryRecords) records).buffer()` returns the reference to the buffer
   - This is the buffer that is NOW BEING USED by the topic B batch
   - The Send object holds a reference to this contaminated buffer

9. **Network Transmission**:
   - Send is written to socket
   - Request header says "Topic A, Partition X"
   - Buffer content is from "Topic B, Partition Y"
   - Broker processes as topic A but persists records to topic B

### Timeline

```
Thread: Sender.run()
Time T0:    sendProducerData()
T0.1:       - drain batch A (topic X) into inFlightBatches
T0.2:       - enqueue request to NetworkClient
T0.3:       - return from sendProducerData()

Time T1:    client.poll()
T1.1:       - (request not yet processed by NetworkClient)
T1.2:       - return from client.poll()

Time T2:    sendProducerData() (next iteration)
T2.1:       - batch A has now exceeded deliveryTimeout
T2.2:       - getExpiredInflightBatches() returns batch A
T2.3:       - failBatch(batch A)
T2.4:       - accumulator.deallocate(batch A)
T2.5:       - BufferPool.deallocate(bufferA) → added to free list

Time T3:    New batch B (topic Y) created
T3.1:       - allocate() gets bufferA from free list
T3.2:       - Write topic Y records to bufferA

Time T4:    client.poll()
T4.1:       - NetworkClient processes queued request for batch A
T4.2:       - doSend() calls request.toSend()
T4.3:       - SendBuilder gets reference to bufferA ← NOW CONTAINS TOPIC Y DATA
T4.4:       - Send object is created with corrupted buffer reference
T4.5:       - Send is transmitted with header="Topic X" data="Topic Y"

Time T5:    Broker receives request
T5.1:       - Header indicates Topic X
T5.2:       - Records are from Topic Y
T5.3:       - Records are appended to Topic X ← CORRUPTION OBSERVED
```

### Why This Is a Critical Race Condition

The bug exploits the **asynchronous nature of the Send object construction**:
- Request enqueuing (in sendProduceRequests) is synchronous
- Request transmission (in NetworkClient.doSend) is asynchronous
- Buffer deallocation happens between these two points
- Send object construction happens during transmission, after deallocation

The window is small but guaranteed to exist under certain conditions:
- High throughput (many batches cycling through)
- Network latency (requests stay queued longer)
- Delivery timeout < request processing time
- Pool reuse (new batches immediately reuse freed buffers)

### Why Tests Might Not Catch This

- Tests typically use in-memory networks (no delay)
- Timeouts are usually generous relative to processing time
- Race conditions are timing-dependent and may not reproduce reliably
- The window between deallocation and Send construction is microseconds

