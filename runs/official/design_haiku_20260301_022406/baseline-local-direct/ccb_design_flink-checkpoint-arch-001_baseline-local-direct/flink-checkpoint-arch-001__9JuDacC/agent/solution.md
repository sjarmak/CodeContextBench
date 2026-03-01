# Flink Checkpoint Coordination Architecture Analysis

## Files Examined

### JobManager-Side Checkpoint Coordination
- **CheckpointCoordinator.java** — Central orchestrator managing distributed checkpoints; coordinates barrier propagation, state collection, acknowledgment handling
- **PendingCheckpoint.java** — Represents in-flight checkpoint awaiting task acknowledgments; tracks task ack status with state aggregation
- **CompletedCheckpoint.java** — Final checkpoint state after all tasks acknowledged; contains operator states, timestamps, metadata handles
- **CheckpointPlan.java** / **CheckpointPlanCalculator.java** — Determines which tasks must participate in checkpoint
- **CheckpointCoordinatorGateway.java** — RPC interface for task→JobManager communication
- **CheckpointStorage.java** — Abstract storage layer; provides checkpoint location initialization and metadata persistence
- **CheckpointOptions.java** — Configuration for each checkpoint (alignment mode, checkpoint type, savepoint flags)
- **CheckpointProperties.java** — Checkpoint properties (periodic, synchronized, external)

### Barrier Events & Stream Injection
- **CheckpointBarrier.java** — Event flowing through data stream marking checkpoint boundary; contains checkpoint ID, timestamp, options
- **OperatorChain.java** — Contains chained operators; coordinates barrier broadcasting via `broadcastEvent()`
- **RecordWriter.java** — Network-level writer that emits barriers into output streams via events
- **BufferOrEvent.java** — Union type representing data records or checkpoint events

### Task-Side Checkpoint Coordination
- **StreamTask.java** — Main streaming task execution container; receives checkpoint trigger, initiates barrier injection, coordinates state snapshots
- **SourceStreamTask.java** — Source-specific task; overrides checkpoint trigger for source-based checkpoints
- **SubtaskCheckpointCoordinator.java** — Interface defining task-level checkpoint orchestration protocol
- **SubtaskCheckpointCoordinatorImpl.java** — Concrete implementation coordinating: barrier broadcasting, state snapshotting, async finalization

### Barrier Reception & Alignment
- **CheckpointedInputGate.java** — Wrapper around InputGate adding checkpoint barrier handling; integrates CheckpointBarrierHandler
- **CheckpointBarrierHandler.java** — Abstract base for barrier processing strategies; handles barrier arrival logic
- **SingleCheckpointBarrierHandler.java** — Aligned checkpoint handler (exactly-once); blocks input channels until all barriers received; maintains BarrierHandlerState
- **CheckpointBarrierTracker.java** — Unaligned checkpoint tracker (at-least-once); tracks barriers without blocking via ArrayDeque<CheckpointBarrierCount>
- **BarrierHandlerState.java** — State machine for barrier alignment (WaitingForFirstBarrier → CollectingBarriers transitions)
- **AbstractAlignedBarrierHandlerState.java** / **AbstractAlternatingAlignedBarrierHandlerState.java** — State implementations for aligned and unaligned modes

### Channel State Management
- **ChannelStateWriter.java** / **ChannelStateWriterImpl.java** — Writes in-flight data from input/output channels during unaligned checkpoints
- **InputChannelInfo.java** / **ResultSubpartitionInfo.java** — Identifies specific channels in network partition
- **ChannelState.java** — Persisted in-flight data state for unaligned checkpoints

### State Snapshotting
- **StateSnapshotContext.java** — Context provided to operators during snapshotting; contains checkpoint ID, factory for state streams
- **OperatorSnapshotFutures.java** — Encapsulates async snapshot futures (keyed state, operator state, channel state)
- **OperatorSnapshotFinalizer.java** — Finalizes snapshot futures into OperatorSubtaskState; creates replicas for JM and task-local recovery
- **AbstractStreamOperator.java** — Base class for streaming operators; implements `snapshotState()` called during checkpoint
- **StreamOperatorStateHandler.java** — Manages state backend interactions for operators
- **OperatorState.java** — Aggregated state of operator across all parallel subtasks in CompletedCheckpoint

### State Backends
- **AbstractKeyedStateBackend.java** — Manages operator keyed state snapshots
- **AsyncKeyedStateBackend.java** — Async keyed state backend
- **DefaultOperatorStateBackend.java** — Manages operator non-keyed state
- **DefaultOperatorStateBackendSnapshotStrategy.java** — Snapshot strategy for operator state

### Task Execution & RPC
- **Task.java** — Low-level task execution wrapper; receives checkpoint messages from JobManager
- **RpcCheckpointResponder.java** — Task-side RPC endpoint sending acknowledgments to JobManager
- **CheckpointResponder.java** — Interface defining task→JM ack protocol
- **AcknowledgeCheckpoint.java** — Message sent from tasks containing TaskStateSnapshot and metrics
- **DeclineCheckpoint.java** — Failure notification message

### Metrics & Statistics
- **CheckpointMetrics.java** — Per-task metrics (alignment duration, bytes buffered, async time)
- **CheckpointStatsTracker.java** — Tracks and reports checkpoint statistics
- **CompletedCheckpointStats.java** — Statistics for completed checkpoint
- **PendingCheckpointStats.java** — Statistics for in-flight checkpoint

### Failure & Lifecycle
- **CheckpointFailureManager.java** — Handles checkpoint failures with failure counting/thresholds
- **CheckpointFailureReason.java** — Enumeration of failure reasons (timeout, decline, task failure)
- **CheckpointsCleaner.java** — Cleans up old checkpoint data

---

## Dependency Chain

### 1. Checkpoint Trigger Initiation (JobManager)
**Entry point:** `CheckpointCoordinator.triggerCheckpoint(CheckpointProperties, String, boolean)`
- Called by: Periodic checkpoint scheduler or external REST/CLI trigger
- Creates: `CheckpointTriggerRequest` wrapped in future chain

### 2. Planning Phase
**Calls:** `CheckpointPlanCalculator.calculateCheckpointPlan()`
- Determines which ExecutionVertices (tasks) must participate
- Returns: `CheckpointPlan` specifying tasks to trigger and tasks to commit to

### 3. PendingCheckpoint Creation
**Delegates to:** `CheckpointCoordinator.createPendingCheckpoint()`
- Allocates unique checkpoint ID via `checkpointIdCounter.getAndIncrement()`
- Creates: `PendingCheckpoint` with:
  - CheckpointPlan
  - notYetAcknowledgedTasks map (ExecutionAttemptID → ExecutionVertex)
  - Empty operatorStates map (filled on acks)
- Adds to: `pendingCheckpoints` map indexed by checkpointId

### 4. Storage Location Initialization
**Calls:** `CheckpointStorage.initializeLocationForCheckpoint(checkpointID)`
- Prepares file system or database location for metadata persistence
- Updates: `PendingCheckpoint.setCheckpointTargetLocation()`

### 5. Coordinator & Master State Snapshots (Optional)
**Calls:** `OperatorCoordinatorCheckpoints.triggerAndAcknowledgeAllCoordinatorCheckpointsWithCompletion()`
- Triggers operator coordinator (external source) checkpoints
- Waits for completion before proceeding to task checkpoint

### 6. Master Hooks Snapshotting (Optional)
**Calls:** `CheckpointCoordinator.snapshotMasterState(PendingCheckpoint)`
- Invokes registered MasterHook instances for job-level state

### 7. Barrier Injection to Tasks
**Entry point:** `CheckpointCoordinator.triggerCheckpointRequest()`
- **For each task in checkpointPlan.getTasksToTrigger():**
  - Calls: `Execution.triggerCheckpoint(checkpointId, timestamp, checkpointOptions)`
  - RPC: Sends `RpcCheckpointCoordinationRequest` to TaskExecutor
  - Awaits: `CompletableFuture<Acknowledge>` confirmation

### 8. Task-Side Checkpoint Trigger Reception
**RPC endpoint:** `TaskExecutor.handleCheckpointCoordinationRequest()`
- Calls: `Task.triggerCheckpointBarrier()`
- Which calls: `StreamTask.triggerCheckpointAsync()` (or sync variant)

### 9. Source Barrier Injection
**In SourceStreamTask (if source):**
```
triggerCheckpointAsync()
  → super.triggerCheckpointAsync()
    → StreamTask.triggerCheckpointAsyncInMailbox()
      → SubtaskCheckpointCoordinator.initInputsCheckpoint() // Initialize unaligned state
      → StreamTask.performCheckpoint()
```

**In regular StreamTask:**
```
triggerCheckpointAsyncInMailbox()
  → SubtaskCheckpointCoordinator.initInputsCheckpoint()
  → SubtaskCheckpointCoordinator.checkpointState()
    → Step 1: OperatorChain.prepareSnapshotPreBarrier() // Pre-barrier work
    → Step 2: OperatorChain.broadcastEvent(CheckpointBarrier) // **BARRIER INJECTION**
    → Step 3: registerAlignmentTimer() // Setup alignment timeout
    → Step 4: channelStateWriter.finishOutput() // Spill output channel state
    → Step 5: takeSnapshotSync() // Synchronous operator state snapshot
    → Step 6: finishAndReportAsync() // Async finalization & RPC ack
```

### 10. Barrier Propagation Through Operators
**Data flow:**
1. **Barrier emitted by:** `OperatorChain.broadcastEvent(CheckpointBarrier, isPriorityEvent)`
   - If priority: jumps queue in RecordWriter
   - If unaligned: included with regular data

2. **Barrier received by:** `CheckpointedInputGate.getNext()`
   - Extracts barrier from `BufferOrEvent`
   - Delegates to: `CheckpointBarrierHandler.processBarrier(barrier, channelInfo, isRpcTriggered)`

### 11. Barrier Alignment/Tracking - Two Paths

#### Path A: Aligned Checkpoints (Exactly-Once)
**Handler:** `SingleCheckpointBarrierHandler`
```
processBarrier(barrier, channelInfo, isRpcTriggered)
  → Check currentState (BarrierHandlerState state machine)
  → If WaitingForFirstBarrier:
      → Transition to CollectingBarriers
      → Store barrier options
      → Block input channels (except barrier sender)
  → If CollectingBarriers:
      → Record barrier received from channelInfo
      → If all barriers received:
          → Transition to CheckpointDone
          → Call: SubtaskCheckpointCoordinator.triggerCheckpointOnBarrier()
          → Unblock input channels
```

#### Path B: Unaligned Checkpoints (At-Least-Once)
**Handler:** `CheckpointBarrierTracker`
```
processBarrier(barrier, channelInfo, isRpcTriggered)
  → Lookup or create CheckpointBarrierCount for barrier.getId()
  → Add channelInfo to received set
  → If all channels received:
      → Remove from pendingCheckpoints
      → Call: CheckpointableTask.triggerCheckpointOnBarrier()
  → Allow data to flow (no blocking)
```

### 12. Task State Snapshot Execution
**Entry point:** `SubtaskCheckpointCoordinator.takeSnapshotSync()`
- Calls: `OperatorChain.snapshotState(StateSnapshotContext, List<OperatorSnapshotFutures>)`
- For each operator in chain:
  - Calls: `StreamOperator.snapshotState(StateSnapshotContext, CheckpointStreamFactory)`
  - Operator snapshots: keyed state, operator state, custom state
  - Returns: `OperatorSnapshotFutures` with async futures

**Async completion:**
- Calls: `SubtaskCheckpointCoordinator.finishAndReportAsync()`
- Submits: `AsyncCheckpointRunnable` to async executor
- Finalizes: `OperatorSnapshotFutures` → `OperatorSubtaskState`
  - Via: `OperatorSnapshotFinalizer.finalize()`
  - Creates two replicas: jobManagerOwnedState, taskLocalState

### 13. Task Acknowledgment to JobManager
**In AsyncCheckpointRunnable:**
```
run()
  → Finalize all operator snapshot futures
  → Collect TaskStateSnapshot from all operators
  → Call: RpcCheckpointResponder.acknowledgeCheckpoint(
      checkpointId,
      taskExecutionId,
      TaskStateSnapshot,  // OperatorSubtaskStates + channel state
      CheckpointMetrics   // alignment duration, bytes, etc.
    )
```

**RPC message:** `AcknowledgeCheckpoint` sent to JobManager

### 14. JobManager Checkpoint Acknowledgment Reception
**Entry point:** `CheckpointCoordinator.receiveAcknowledgeMessage(AcknowledgeCheckpoint)`
```
receiveAcknowledgeMessage()
  → Register shared state in SharedStateRegistry
  → Lookup: PendingCheckpoint by checkpointId
  → Call: PendingCheckpoint.acknowledgeTask(
      taskExecutionId,
      TaskStateSnapshot,
      CheckpointMetrics
    )
      → Remove from notYetAcknowledgedTasks
      → Update operatorStates map with OperatorSubtaskState
      → Increment numAcknowledgedTasks
      → Report metrics to CheckpointStatsTracker
      → Return: TaskAcknowledgeResult (SUCCESS/DUPLICATE/UNKNOWN/DISCARDED)
  → If isFullyAcknowledged():
      → Call: CheckpointCoordinator.completePendingCheckpoint()
```

### 15. Checkpoint Completion - Two-Phase Commit
**Entry point:** `CheckpointCoordinator.completePendingCheckpoint(PendingCheckpoint)`

**Phase 1 - Finalization:**
```
→ Call: PendingCheckpoint.finalizeCheckpoint()
    → Create CheckpointMetadata from operatorStates map
    → Write metadata to CheckpointMetadataOutputStream
    → Persist via CheckpointStorageLocation
    → Return: CompletedCheckpoint with:
        - Job ID, checkpoint ID, timestamps
        - Map<OperatorID, OperatorState> from PendingCheckpoint
        - Reference to storage location
        - metadataHandle (serialized metadata)

→ Add to CompletedCheckpointStore
    → Persist to file system or database
    → Subsume old checkpoints (retain only latest N)
    → Update SharedStateRegistry

→ Report completion to CheckpointStatsTracker
```

**Phase 2 - Notification:**
```
→ Call: CheckpointCoordinator.sendAcknowledgeMessages()
    → For each task in checkpointPlan.getTasksToCommitTo():
        → RPC: Send NotifyCheckpointComplete(checkpointId)
        → Task calls: StreamTask.notifyCheckpointComplete()
          → Calls: OperatorChain.notifyCheckpointComplete()
          → Operators: OnCheckpointComplete hooks (cleanup, side effects)
```

### 16. Checkpoint Completion Result
**Returns:** `CompletedCheckpoint` via completion futures
- Listeners updated (JobGraph, REST API, etc.)
- Checkpoint available for recovery
- Old checkpoints cleaned up based on retention policy

---

## Analysis

### Design Patterns Identified

#### 1. **Two-Phase Distributed Commit**
The checkpoint coordination implements a classic two-phase commit protocol:
- **Phase 1 (Prepare):** CheckpointCoordinator triggers all tasks; tasks snapshot state asynchronously
- **Phase 2 (Commit):** JobManager collects acknowledgments; once all received, finalizes metadata and notifies tasks
- **Abort Path:** If timeout or task failure, CheckpointCoordinator broadcasts CancelCheckpointMarker to abort

#### 2. **State Machine Pattern**
Barrier alignment uses a pluggable state machine (BarrierHandlerState) with states:
- `WaitingForFirstBarrier`: Initial state awaiting first barrier on any channel
- `CollectingBarriers`: Collecting barriers from all channels (aligned mode blocks; unaligned doesn't)
- `CheckpointDone`: All barriers received, checkpoint triggered
- Alternating states support multiple concurrent checkpoints (e.g., `AlternatingCollectingBarriers`)

#### 3. **Strategy Pattern**
Checkpoint barrier handling uses interchangeable strategies:
- `SingleCheckpointBarrierHandler`: Aligned checkpoint strategy (blocking, exactly-once)
- `CheckpointBarrierTracker`: Unaligned checkpoint strategy (non-blocking, at-least-once)
- Both implement abstract `CheckpointBarrierHandler` interface

#### 4. **Futures-Based Async Coordination**
Checkpoint lifecycle uses CompletableFutures for async composition:
- Futures chain: plan → pending → coordinator snapshots → master snapshots → barrier injection → task acks → completion
- Enables concurrent execution: JobManager initialization, task state snapshots, and ack collection happen in parallel
- Failure propagation via exception handlers in future chains

#### 5. **Async/Sync Separation**
State snapshots split into phases:
- **Sync phase:** Snapshot operator state synchronously (in mailbox), emit barriers
- **Async phase:** Finalize snapshot futures asynchronously without blocking mailbox
- Minimizes impact on operator progress

#### 6. **RPC Boundary Crossing**
Communication between JobManager and TaskExecutor spans RPC:
- **Request:** Execution.triggerCheckpoint() sends RPC to TaskExecutor
- **Response:** RpcCheckpointResponder sends AcknowledgeCheckpoint RPC back
- Each direction decoupled via RPC futures

### Component Responsibilities

#### JobManager-Side (CheckpointCoordinator)
1. **Orchestration:** Triggers checkpoints on schedule or external request
2. **Planning:** Determines which tasks participate via CheckpointPlan
3. **Coordination:** Sends trigger messages to tasks, collects acknowledgments
4. **Finalization:** Creates CompletedCheckpoint from aggregated state, persists metadata
5. **Notification:** Notifies tasks of completion for cleanup
6. **Failure Management:** Tracks and counts checkpoint failures; fails job on threshold

#### TaskExecutor-Side (StreamTask + SubtaskCheckpointCoordinator)
1. **Reception:** Receives checkpoint trigger from JobManager via RPC
2. **Barrier Injection:** Broadcasts checkpoint barrier into operator chain
3. **State Snapshot:** Coordinates operator state snapshots (sync + async phases)
4. **Channel State:** Captures in-flight data state (unaligned mode)
5. **Acknowledgment:** Sends TaskStateSnapshot and metrics back to JobManager
6. **Notification:** Receives and propagates completion notifications to operators

#### Barrier Handlers (SingleCheckpointBarrierHandler / CheckpointBarrierTracker)
1. **Reception:** Extract barriers from incoming BufferOrEvent stream
2. **Tracking:** Track barrier arrival from all input channels
3. **Alignment:** Implement alignment semantics (blocking vs non-blocking)
4. **Triggering:** Notify task when all barriers received
5. **Metrics:** Report alignment duration, bytes buffered

### Data Flow Description

#### Checkpoint Trigger Flow
```
1. Periodic scheduler (every N ms) calls CheckpointCoordinator.triggerCheckpoint()
2. CheckpointCoordinator:
   - Calculates CheckpointPlan (which tasks participate)
   - Creates PendingCheckpoint (tracks acks)
   - Sends RPC trigger to each task
   - Awaits task ack futures
3. Task receives RPC:
   - StreamTask.triggerCheckpointAsync()
   - Calls SubtaskCheckpointCoordinator.checkpointState()
   - Broadcasts CheckpointBarrier into data stream
   - Snapshots operator state asynchronously
   - Sends AcknowledgeCheckpoint RPC with state
4. JobManager receives ack:
   - CheckpointCoordinator.receiveAcknowledgeMessage()
   - PendingCheckpoint.acknowledgeTask() aggregates state
   - When all tasks acked: completePendingCheckpoint()
5. Checkpoint completed:
   - Creates CompletedCheckpoint
   - Persists metadata to external storage
   - Sends NotifyCheckpointComplete RPC to tasks
```

#### Barrier Propagation Flow
```
1. Source/Task broadcasts CheckpointBarrier event
2. Barrier flows through RecordWriter → network layer → input channels
3. Task's CheckpointedInputGate receives barrier:
   - Extracts from BufferOrEvent
   - Routes to CheckpointBarrierHandler.processBarrier()
4. Handler processes barrier:
   Aligned mode:
     - Blocks input channels
     - Waits for barriers from all channels
     - Calls triggerCheckpointOnBarrier() when complete
   Unaligned mode:
     - Tracks barrier receipt without blocking
     - Calls triggerCheckpointOnBarrier() immediately when all received
5. Task performs checkpoint:
   - Snapshots operators
   - Sends ack with state
```

#### State Aggregation Flow
```
1. Task snapshots operator states → OperatorSnapshotFutures (async)
2. AsyncCheckpointRunnable finalizes futures:
   - Waits for all async snapshot futures
   - Creates OperatorSubtaskState
   - Collects metrics
3. Task sends AcknowledgeCheckpoint RPC with TaskStateSnapshot:
   {
     operatorSubtaskStates: Map<OperatorID, OperatorSubtaskState>,
     channelState: ChannelStateSnapshot (if unaligned),
     metrics: CheckpointMetrics
   }
4. JobManager receives ack:
   - PendingCheckpoint.acknowledgeTask() stores state
   - Updates operatorStates map with OperatorSubtaskState
5. All tasks acked → aggregated in PendingCheckpoint.operatorStates
6. CompletedCheckpoint created with aggregated state
```

### Interface Contracts Between Components

#### CheckpointCoordinator → Task (RPC)
- **Message:** `RpcCheckpointCoordinationRequest(checkpointId, timestamp, checkpointOptions)`
- **Contract:** Task must snapshot state and send AcknowledgeCheckpoint within timeout
- **Failure:** Task sends DeclineCheckpoint; Coordinator aborts checkpoint

#### Task → CheckpointCoordinator (RPC)
- **Message:** `AcknowledgeCheckpoint(taskId, checkpointId, TaskStateSnapshot, metrics)`
- **Contract:** JobManager collects from all tasks; completes checkpoint when all received
- **Late Message:** Handled gracefully (discarded or logged); doesn't fail checkpoint

#### CheckpointBarrierHandler → SubtaskCheckpointCoordinator
- **Contract:** Handler calls `triggerCheckpointOnBarrier()` when barriers complete
- **Aligned:** Only after all barriers received (with blocking)
- **Unaligned:** When barrier count complete (no blocking)

#### StreamOperator → StateSnapshotContext
- **Contract:** Operator implements `snapshotState(StateSnapshotContext, CheckpointStreamFactory)`
- **Provides:** Context with checkpoint ID, stream factory, state backend access
- **Returns:** OperatorSnapshotFutures with keyed/operator state snapshots

#### CompletedCheckpointStore → JobManager
- **Contract:** Store persists metadata; provides recovery source
- **Lifecycle:** Adds on completion; subsumed old checkpoints; discards on job termination

### Aligned vs Unaligned Checkpoints

#### Aligned Checkpoints (Exactly-Once Guarantee)
```
SingleCheckpointBarrierHandler:
  - Blocks input channels when first barrier received
  - Waits for barriers from ALL channels
  - Ensures: No new records after barrier until all barriers received
  - Result: Operator state snapshot is "aligned" — safe point in stream
  - Latency: Higher (waits for slowest channel)
  - Example: All channels must reach barrier N before operator processes
```

#### Unaligned Checkpoints (At-Least-Once Guarantee)
```
CheckpointBarrierTracker:
  - No blocking; data flows continuously
  - Tracks barrier arrival count
  - Snapshot captures: Operator state + in-flight data (channel state)
  - Result: May re-process records after restart (hence at-least-once)
  - Latency: Lower (no blocking overhead)
  - Example: Snapshot includes buffered records in flight, replayed on recovery
```

**Configuration:**
- `CheckpointOptions.alignment`: ALIGNED, UNALIGNED, or FORCED_ALIGNED
- `StreamExecutionEnvironment.getCheckpointConfig().setAlignedCheckpointTimeout()`: Auto-switch unaligned after timeout

### PendingCheckpoint Lifecycle

```
States:
  1. Created: Added to CheckpointCoordinator.pendingCheckpoints map
     - notYetAcknowledgedTasks: All tasks in CheckpointPlan
     - operatorStates: Empty map
  2. Collecting: Tasks send acknowledgments
     - PendingCheckpoint.acknowledgeTask() called per task
     - notYetAcknowledgedTasks: Decremented per ack
     - operatorStates: Built up with OperatorSubtaskState
  3. FullyAcknowledged: All tasks acked
     - notYetAcknowledgedTasks: Empty
     - numAcknowledgedTasks == all tasks count
  4. Finalizing: Metadata written to storage
     - PendingCheckpoint.finalizeCheckpoint() converts to CompletedCheckpoint
  5. Disposed: Removed from pendingCheckpoints map
     - operatorStates persisted in CompletedCheckpoint

Timeout Path:
  - CheckpointCoordinator schedules timeout future
  - If not fully acked by deadline: abort
    - Send CancelCheckpointMarker to tasks
    - Release in-flight state handles
    - Move to next checkpoint
```

### Ack-Based Completion Protocol

```
1. JobManager sends trigger RPC
2. Task sends acknowledgment RPC (may arrive out of order)
3. JobManager processes ack:
   - Lock: synchronized (lock) prevents concurrent ack processing
   - Lookup: Find PendingCheckpoint by checkpoint ID
   - Validate: Check task execution ID is expected
   - State Merge: Add OperatorSubtaskState to PendingCheckpoint
   - Completion Check: if (checkpoint.isFullyAcknowledged())
       → completePendingCheckpoint()
4. Race Conditions Handled:
   - Duplicate ack: Idempotent, returns TaskAcknowledgeResult.DUPLICATE
   - Unknown task: Logged, state discarded (TaskAcknowledgeResult.UNKNOWN)
   - Late ack (checkpoint disposed): Ignored, state released (TaskAcknowledgeResult.DISCARDED)
   - Concurrent acks: Protected by lock in PendingCheckpoint and CheckpointCoordinator
```

---

## Summary

Flink's checkpoint coordination implements a **distributed two-phase commit** where the JobManager orchestrates barrier injection into the task graph, tasks snapshot state asynchronously, and acknowledgments are collected to form a complete checkpoint. Barriers propagate through operators either **aligned** (blocking, exactly-once) or **unaligned** (non-blocking, at-least-once), with handler strategies pluggable via the state machine pattern. The architecture decouples trigger (RPC request), execution (async state snapshots), and completion (RPC acknowledgment collection) using futures, enabling efficient distributed checkpointing while supporting both synchronous and asynchronous state backends. The PendingCheckpoint aggregates operator states from all tasks via the ack-based protocol, converting to a CompletedCheckpoint only when all tasks have acknowledged with their state snapshots, ensuring durability and recovery correctness.
