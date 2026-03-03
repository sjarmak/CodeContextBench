# Flink Checkpoint Coordination Architecture

## Files Examined

### JobManager-Side Checkpoint Coordination
- `/workspace/flink-runtime/src/main/java/org/apache/flink/runtime/checkpoint/CheckpointCoordinator.java` — Central coordinator orchestrating checkpoint lifecycle; manages PendingCheckpoint tracking, RPC dispatch to tasks, and aggregation of acknowledgments
- `/workspace/flink-runtime/src/main/java/org/apache/flink/runtime/checkpoint/PendingCheckpoint.java` — In-progress checkpoint state holder; tracks which tasks have acknowledged, manages operator state collection, and validates completion conditions
- `/workspace/flink-runtime/src/main/java/org/apache/flink/runtime/checkpoint/CompletedCheckpoint.java` — Finalized checkpoint containing all metadata and state handles; persisted to CheckpointStore and used for recovery

### Barrier Propagation & Reception
- `/workspace/flink-runtime/src/main/java/org/apache/flink/runtime/io/network/api/CheckpointBarrier.java` — Network event injected at sources that triggers checkpoint at downstream tasks; carries checkpoint ID, timestamp, and options
- `/workspace/flink-runtime/src/main/java/org/apache/flink/streaming/runtime/io/checkpointing/CheckpointedInputGate.java` — Integrates CheckpointBarrierHandler into input gate; intercepts barriers from network channels and dispatches to barrier handler
- `/workspace/flink-runtime/src/main/java/org/apache/flink/streaming/runtime/io/checkpointing/CheckpointBarrierHandler.java` — Abstract base class for barrier processors; defines interface for barrier reception and coordinates checkpoint notification to task

### Aligned vs Unaligned Checkpoint Handling
- `/workspace/flink-runtime/src/main/java/org/apache/flink/streaming/runtime/io/checkpointing/SingleCheckpointBarrierHandler.java` — Handles both aligned and unaligned barriers using state machine (WaitingForFirstBarrier, CollectingBarriers); blocks channels on aligned barriers or buffers data on unaligned
- `/workspace/flink-runtime/src/main/java/org/apache/flink/streaming/runtime/io/checkpointing/CheckpointBarrierTracker.java` — Tracks barrier receipt without blocking (at-least-once semantics); maintains pending checkpoint queue and notifies when all barriers received

### Task-Side Checkpoint Execution
- `/workspace/flink-runtime/src/main/java/org/apache/flink/streaming/runtime/tasks/StreamTask.java` — Runtime streaming task; receives barrier notifications and coordinates state snapshot via SubtaskCheckpointCoordinator
- `/workspace/flink-runtime/src/main/java/org/apache/flink/streaming/runtime/tasks/SubtaskCheckpointCoordinator.java` — Task-level checkpoint coordinator; manages state snapshots, channel state writing, and task-side acknowledgment notifications

### Execution & RPC
- `/workspace/flink-runtime/src/main/java/org/apache/flink/runtime/executiongraph/Execution.java` — Represents a task execution; routes triggerCheckpoint() to TaskManagerGateway for RPC dispatch

## Dependency Chain

### Phase 1: Checkpoint Trigger
1. **Entry point**: `CheckpointCoordinator.triggerCheckpoint(boolean isPeriodic)` — Public API
   - Converts to internal `triggerCheckpoint(CheckpointProperties props, String externalSavepointLocation, boolean isPeriodic)`

2. **Request queuing**: `CheckpointCoordinator.chooseRequestToExecute()` — Deduplicates/prioritizes requests
   - Calls `startTriggeringCheckpoint(CheckpointTriggerRequest request)`

3. **Planning & initialization**: `startTriggeringCheckpoint()` initiates async chain:
   - Calls `CheckpointPlanCalculator.calculateCheckpointPlan()` — Determines tasks to trigger/wait-for
   - Obtains checkpoint ID from `CheckpointIDCounter.getAndIncrement()`
   - Creates `PendingCheckpoint` via `createPendingCheckpoint()` with execution plan

4. **Storage setup**: `initializeCheckpointLocation()` prepares storage target
   - Configures `CheckpointStorageLocation` for metadata/state persistence

5. **Coordinator snapshots**: `OperatorCoordinatorCheckpoints.triggerAndAcknowledgeAllCoordinatorCheckpointsWithCompletion()`
   - Snapshots operator coordinators before task triggering (order matters for ExternallyInducedSource)

6. **Master state snapshots**: `snapshotMasterState()` snapshots MasterTriggerRestoreHooks

### Phase 2: Barrier Injection to Tasks
7. **Task triggering**: `triggerCheckpointRequest()` → `triggerTasks()` → **RPC dispatch**
   - For each task in `CheckpointPlan.getTasksToTrigger()`:
   - Calls `Execution.triggerCheckpoint(checkpointId, timestamp, checkpointOptions)`
   - Routes to `TaskManagerGateway.triggerCheckpoint()` (RPC)
   - Task manager receives RPC and invokes `StreamTask.triggerCheckpointAsync()`

### Phase 3: Barrier Propagation
8. **Source task reception**: StreamTask receives RPC at TaskManager
   - Calls `StreamTask.triggerCheckpointAsync()` on SourceStreamTask/SourceOperatorStreamTask
   - Injects `CheckpointBarrier` events into source output channels

9. **Barrier flow through network**: CheckpointBarrier propagates through partitions
   - Flows through NetworkEnvironment channels with explicit ordering

10. **Downstream reception**: Non-source tasks receive CheckpointBarrier via network
    - `InputGate.getNext()` → `CheckpointedInputGate.pollNext()`
    - Identifies CheckpointBarrier event among data buffers

### Phase 4: Barrier Alignment/Processing
11. **Barrier handler dispatch**: `CheckpointedInputGate.pollNext()` → `CheckpointBarrierHandler.processBarrier()`
    - **For aligned checkpoints**: `SingleCheckpointBarrierHandler.aligned()`
      - Uses `WaitingForFirstBarrier` → `CollectingBarriers` state machine
      - **Blocks aligned channels** to enforce alignment until all barriers received
      - State: `BarrierHandlerState` manages blocked channels via `CheckpointableInput.blockChannel()`
    - **For unaligned checkpoints**: `SingleCheckpointBarrierHandler.unaligned()`
      - Uses `AlternatingWaitingForFirstBarrierUnaligned` state machine
      - **Buffers data** from faster channels while waiting for slower ones
      - Tolerance determined by `alignedCheckpointTimeout`
    - **At-least-once** (no blocking): `CheckpointBarrierTracker`
      - Tracks barrier receipt with `CheckpointBarrierCount` in queue
      - Notifies on completion without blocking

### Phase 5: State Snapshot
12. **Checkpoint notification**: `CheckpointBarrierHandler.notifyCheckpoint()`
    - Calls `CheckpointableTask.triggerCheckpointOnBarrier()`
    - Passes `CheckpointMetaData`, `CheckpointOptions`, `CheckpointMetrics`

13. **Task state snapshot**: `StreamTask.triggerCheckpointOnBarrier()` → `SubtaskCheckpointCoordinator.checkpointState()`
    - Initiates `OperatorChain.snapshotState()` for all operators
    - Snapshots:
      - **Operator state** via `StreamOperator.snapshotState()`
      - **Channel state** via `ChannelStateWriter.writeChannelStateAndWait()` (for unaligned only)
      - **Input gate state** (partial data buffered during alignment)
    - Executes async operations and collects state handles

### Phase 6: Acknowledgment
14. **Acknowledgment message**: `StreamTask` → `TaskManagerGateway` → JobManager RPC
    - Prepares `AcknowledgeCheckpoint` containing:
      - Checkpoint ID
      - Task execution attempt ID
      - `TaskStateSnapshot` (serialized operator + channel states)
      - `CheckpointMetrics` (alignment duration, processed bytes)

15. **JobManager reception**: `CheckpointCoordinator.receiveAcknowledgeMessage(AcknowledgeCheckpoint message)`
    - Locks checkpoint state
    - Retrieves `PendingCheckpoint` from `pendingCheckpoints` map (keyed by checkpoint ID)

### Phase 7: Pending Checkpoint Completion
16. **Task acknowledgment recording**: `PendingCheckpoint.acknowledgeTask()`
    - Removes task from `notYetAcknowledgedTasks` set
    - Registers shared state via `SharedStateRegistry.registerReference()`
    - Updates `operatorStates` with received state handles
    - Increments `numAcknowledgedTasks` counter
    - Returns `TaskAcknowledgeResult` (SUCCESS, DUPLICATE, UNKNOWN, DISCARDED)

17. **Completion check**: `CheckpointCoordinator.receiveAcknowledgeMessage()`
    - If `PendingCheckpoint.isFullyAcknowledged()`:
      - All tasks in `CheckpointPlan.getTasksToWaitFor()` have acknowledged
      - All operator coordinators acknowledged
      - All master states received
      - Calls `completePendingCheckpoint(PendingCheckpoint)`

### Phase 8: Finalization
18. **Checkpoint finalization**: `completePendingCheckpoint()`
    - Calls `SharedStateRegistry.checkpointCompleted()` — transitions shared state refs
    - Calls `PendingCheckpoint.finalizeCheckpoint()`
      - Serializes checkpoint metadata via `CheckpointMetadataOutputStream`
      - Creates `CompletedCheckpoint` object with all collected state
      - Persists metadata to `CheckpointStorageLocation`
      - Returns finalized `CompletedCheckpoint`

19. **Store addition**: `addCompletedCheckpointToStoreAndSubsumeOldest()`
    - Adds `CompletedCheckpoint` to `CompletedCheckpointStore`
    - Subsumes older checkpoints (removes retained state)
    - Removes `PendingCheckpoint` from `pendingCheckpoints` map

### Phase 9: Commitment & Notification
20. **Commit phase**: `sendAcknowledgeMessages()`
    - For each task in `CheckpointPlan.getTasksToCommitTo()`:
      - Calls `Execution.notifyCheckpointOnComplete()` RPC
      - Sends `NotifyCheckpointComplete` message to task
    - For each operator coordinator:
      - Calls `OperatorCoordinatorCheckpointContext.notifyCheckpointComplete()`

21. **Task completion callback**: StreamTask receives checkpoint complete notification
    - Calls `SubtaskCheckpointCoordinator.notifyCheckpointComplete()`
    - Notifies operators via `StreamOperator.notifyCheckpointComplete()`
    - Allows operators to release resources held during checkpoint

## Analysis

### Design Patterns

#### 1. **Two-Phase Distributed Commit**
The checkpoint protocol implements a distributed two-phase commit pattern:
- **Phase 1 (Propose)**: Coordinator triggers checkpoint by injecting barriers and requesting state snapshots from all tasks
- **Phase 2 (Commit)**: Upon receiving all acknowledgments, coordinator finalizes checkpoint and notifies all tasks of successful commit

This ensures atomic semantics across the distributed system.

#### 2. **Barrier-Based Ordering**
Checkpoints leverage the barrier abstraction to enforce ordering:
- Barriers flow through the same network channels as data, ensuring **data-aware coordination**
- Barriers act as "watermarks" that partition the data stream into pre- and post-checkpoint data
- **In-order delivery** of barriers with respect to upstream data is guaranteed

#### 3. **State Machine for Barrier Handling**
`SingleCheckpointBarrierHandler` uses a state machine pattern with multiple states:
- `WaitingForFirstBarrier` → `CollectingBarriers` → (end state when all barriers received)
- `AlternatingWaitingForFirstBarrier(Unaligned)` → `AlternatingCollectingBarriers(Unaligned)`
- Each state encapsulates behavior for channel blocking/buffering decisions

#### 4. **Async Coordination with Futures**
Extensive use of `CompletableFuture` chains for non-blocking coordination:
- Checkpoint trigger creates async pipeline: `calculatePlan → getId → createPending → initStorage → triggerCoordinators → triggerMasterHooks → triggerTasks`
- Allows scheduler to handle many concurrent checkpoints without blocking threads

#### 5. **Lock-Based Synchronization**
Both `CheckpointCoordinator` and `PendingCheckpoint` use object monitors:
- `CheckpointCoordinator.lock` — protects `pendingCheckpoints` map and global state
- `PendingCheckpoint.lock` — protects acknowledgment tracking
- Coarse-grained locking prevents complexity of fine-grained synchronization

### Component Responsibilities

#### **CheckpointCoordinator** (JobManager, per-job)
- **Orchestrates** checkpoint lifecycle end-to-end
- **Manages** PendingCheckpoint instances (map keyed by checkpoint ID)
- **Dispatches** RPC trigger messages to task managers
- **Aggregates** task acknowledgments into completed checkpoint
- **Persists** metadata and manages retention policy

#### **PendingCheckpoint** (JobManager, per-checkpoint)
- **Tracks** which tasks have acknowledged (set difference)
- **Accumulates** operator state from task acknowledgments
- **Validates** completion (all tasks acked + all operators acked + all master states received)
- **Produces** CompletedCheckpoint upon finalization

#### **CheckpointBarrierHandler** (TaskManager, per-input)
- **Receives** CheckpointBarrier events from input channels
- **Decides** blocking/buffering strategy (aligned vs unaligned)
- **Notifies** StreamTask when barrier alignment complete
- **Manages** channel state for recovery

#### **SingleCheckpointBarrierHandler** (TaskManager, per-input)
- **Implements** aligned barrier processing:
  - Blocks faster input channels on aligned barriers
  - Allows slower channels to catch up
  - When all barriers received, initiates state snapshot
- **Implements** unaligned barrier processing:
  - Buffers data from faster channels up to size limit
  - Immediately initiates state snapshot when first barrier received
  - Tolerates late barriers up to `alignedCheckpointTimeout`

#### **SubtaskCheckpointCoordinator** (TaskManager, per-task)
- **Invokes** operator snapshotting via `OperatorChain.snapshotState()`
- **Manages** async state persistence and handle collection
- **Writes** channel state for unaligned checkpoints
- **Constructs** `TaskStateSnapshot` for transmission

#### **CheckpointedInputGate** (TaskManager, per-gate)
- **Intercepts** `BufferOrEvent` stream from `InputGate`
- **Extracts** CheckpointBarrier events
- **Routes** barriers to `CheckpointBarrierHandler`
- **Filters** barriers out of data stream (barriers don't reach operators)

### Data Flow

#### **Trigger Flow** (Coordinator → Task)
```
CheckpointCoordinator
  ↓ (RPC: triggerCheckpoint)
TaskManagerGateway
  ↓
StreamTask (or SourceStreamTask)
  ↓ (injects barriers)
OutputBuffer/ChannelWriters
  ↓ (network transport)
InputChannels
```

#### **Barrier Flow** (Source → Sink)
```
SourceTask (injects barriers)
  ↓ (data & barriers in output buffers)
NetworkChannels (FIFO per channel)
  ↓
DownstreamTask.InputGate
  ↓ (getNext())
CheckpointedInputGate
  ↓
CheckpointBarrierHandler (process barrier, block/buffer channels)
  ↓ (when all barriers received)
StreamTask.triggerCheckpointOnBarrier()
```

#### **Ack Flow** (Task → Coordinator)
```
StreamTask (state snapshot complete)
  ↓ (RPC: acknowledgeCheckpoint)
JobManager.CheckpointCoordinator
  ↓ (add to PendingCheckpoint)
PendingCheckpoint.acknowledgeTask()
  ↓ (if fully acked)
CheckpointCoordinator.completePendingCheckpoint()
```

### Aligned vs Unaligned Checkpoint Handling

#### **Aligned Checkpoints** (`SingleCheckpointBarrierHandler.aligned()`)
**Mechanism**: Barriers must arrive at approximately the same time across all input channels.
```
Before all barriers received:
  Channel 1: BLOCKED (after barrier)
  Channel 2: [data] [barrier]  (still receiving)

After all barriers received:
  → Snapshot state
  → Unblock channels
  → Resume processing
```

**Properties**:
- **Exactly-once**: Consistent checkpoint across all operators
- **Overhead**: Slow channels delay fast channels (skew can increase latency)
- **Use case**: Exactly-once semantics required

#### **Unaligned Checkpoints** (`SingleCheckpointBarrierHandler.unaligned()`)
**Mechanism**: Checkpoint initiated immediately upon first barrier; subsequent data buffered if needed.
```
Channel 1: [barrier received]
  → Snapshot state immediately
  → Continue processing

Channel 2: [buffered data] [barrier]
  → Buffer data until barrier consumed
  → Channel state persists buffered data
```

**Properties**:
- **At-least-once**: Buffered data may be replayed on recovery
- **Low latency**: No cross-channel synchronization
- **Overhead**: May require significant buffering if channels skewed
- **Use case**: Low-latency requirements, acceptable replay

#### **Barrier Tracker** (`CheckpointBarrierTracker`)
**Mechanism**: No input blocking; just tracks barrier receipt.
```
Channel 1: [barrier]  [data continues]
Channel 2: [barrier]  [data continues]

When all barriers seen → notify (no state snapshot triggered here)
```

**Properties**:
- **At-least-once**: No ordering guarantees
- **Minimal overhead**: No blocking or buffering
- **Use case**: Legacy mode, debugging

### PendingCheckpoint Lifecycle

```
Creation:
  new PendingCheckpoint(jobId, checkpointId, checkpointTimestamp,
                        checkpointPlan, operatorCoordinators,
                        masterStateIdentifiers, props)
  ↓
  pendingCheckpoints.put(checkpointId, pending)

Tracking:
  For each task in notYetAcknowledgedTasks:
    - pending.acknowledgeTask(executionId, stateSnapshot, metrics)
    - Removes from notYetAcknowledgedTasks
    - Adds to operatorStates

Completion condition:
  pending.isFullyAcknowledged() iff:
    - notYetAcknowledgedTasks.isEmpty()
    - notYetAcknowledgedOperatorCoordinators.isEmpty()
    - notYetAcknowledgedMasterStates.isEmpty()

Finalization:
  if isFullyAcknowledged():
    - pending.finalizeCheckpoint(checkpointsCleaner, executor)
    - → CompletedCheckpoint (with serialized metadata)

Cleanup:
  - pendingCheckpoints.remove(checkpointId)
  - pendingCheckpoint.dispose()
```

### Ack-Based Completion Protocol

The checkpoint completion protocol uses an **implicit ack model** where:

1. **Ack collection**: Each task independently sends `AcknowledgeCheckpoint` containing state snapshot
2. **State aggregation**: `PendingCheckpoint.acknowledgeTask()` collects state from ack message
3. **Completion trigger**: `CheckpointCoordinator` checks `isFullyAcknowledged()` after each ack
4. **Deterministic finalization**: Once all acks collected, `finalizeCheckpoint()` is idempotent (already have all state)
5. **Timeout fallback**: `ScheduledFuture cancellerHandle` in `PendingCheckpoint` aborts if timeout exceeded

This design ensures:
- **No explicit completion message** needed from coordinator (implicit in full ack set)
- **Asymmetric protocol**: Trigger is 1→N, ack collection is N→1 aggregation
- **Fault-tolerant**: Late acks still processed correctly (registered in shared state)

## Summary

Flink's checkpoint coordination implements a **barrier-based, distributed two-phase commit** protocol where the CheckpointCoordinator (JobManager) orchestrates state snapshots across tasks by (1) injecting CheckpointBarrier events into the data stream at sources, (2) having downstream tasks process barriers via state machine-based handlers that enforce alignment or buffer data depending on mode, and (3) collecting acknowledgments that aggregate operator state into a CompletedCheckpoint once all tasks confirm. The design leverages barriers as both coordination triggers and ordering markers in the data stream, enabling consistent exactly-once checkpoints (aligned mode) or lower-latency at-least-once snapshots (unaligned mode), with channel state providing recovery of in-flight data for the latter.

