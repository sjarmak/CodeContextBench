# Kafka-Flink Streaming Data Flow Architecture

## Files Examined

### Apache Kafka (clients/src/main/java/org/apache/kafka/clients/)
- **Producer.java** — Public interface for KafkaProducer with send(), flush(), close() methods
- **ProducerRecord.java** — Data container with topic, partition, key, value, headers, timestamp
- **Consumer.java** — Public interface for KafkaConsumer with poll(), commitSync(), subscribe() methods
- **ConsumerRecord.java** — Data container with topic, partition, offset, key, value, timestamp, leaderEpoch
- **OffsetAndMetadata.java** — Offset commit wrapper containing offset, metadata, and leaderEpoch

### Kafka Serialization (clients/src/main/java/org/apache/kafka/common/serialization/)
- **Serializer.java** — Interface for T → byte[] (topic-aware, header-aware)
- **Deserializer.java** — Interface for byte[] → T (supports topic, headers, ByteBuffer)
- **Serde.java** — Wrapper combining Serializer + Deserializer

### Apache Flink Core (flink-core/src/main/java/org/apache/flink/api/connector/source/)
- **Source.java** — Factory interface creating SplitEnumerator, SourceReader, serializers
- **SourceReader.java** — Interface for reading records with pollNext(), snapshotState(), addSplits()
- **SplitEnumerator.java** — Interface for discovering and assigning splits to readers
- **SourceSplit.java** — Marker interface for split units

### Flink Connector Base (flink-connectors/flink-connector-base/src/main/java/)
- **SourceReaderBase.java** — Abstract implementation providing synchronization, state management, fetcher management
- **SplitReader.java** — Interface for synchronous/polling-based reads: fetch(), handleSplitsChanges(), wakeUp()
- **RecordEmitter.java** — Interface for converting intermediate elements to output records
- **SplitFetcherManager.java** — Manages fetcher threads that run SplitReaders

### Flink Runtime (flink-runtime/src/main/java/org/apache/flink/streaming/api/operators/)
- **SourceOperator.java** — Runtime integration class implementing OperatorEventHandler, PushingAsyncDataInput
- **SourceOperatorFactory.java** — Factory creating SourceOperator instances

### Flink Serialization (flink-core/src/main/java/org/apache/flink/api/common/serialization/)
- **DeserializationSchema.java** — Interface for byte[] → T with type information
- **AbstractDeserializationSchema.java** — Base implementation handling type extraction

---

## Dependency Chain: Data Flow from Kafka → Flink

### **Phase 1: Kafka Producer API (Output Path)**

```
User Code
    ↓
ProducerRecord<K, V> {
    topic: String
    partition: Integer
    timestamp: Long
    key: K
    value: V
    headers: Headers
}
    ↓
Producer<K, V>.send(record, callback) [Non-blocking via NetworkClient]
    ↓
Serializer<K>.serialize(topic, key) → byte[]
Serializer<V>.serialize(topic, value) → byte[]
    ↓
KafkaProducer [internal]
    ├─ ProducerRecord → ProducerBatch (batching)
    ├─ Sender thread → Broker via NetworkClient
    └─ RecordMetadata callback (offset, partition, timestamp)
```

**Key Contract:**
- Topic-aware serialization (enables custom serialization per topic)
- Header support (metadata transport alongside data)
- Async send with callback or blocking flush()

### **Phase 2: Kafka Consumer API (Input Path)**

```
KafkaConsumer<K, V>
    ├─ subscribe(Collection<String>) or assign(Collection<TopicPartition>)
    ├─ poll(Duration timeout) → ConsumerRecords<K, V>
    │   └─ for each TopicPartition:
    │       └─ Fetcher [internal] reads batches from broker
    │           ↓
    │           Deserializer<K>.deserialize(topic, key_bytes) → K
    │           Deserializer<V>.deserialize(topic, value_bytes) → V
    │           ↓
    │           ConsumerRecord<K, V> {
    │               topic, partition, offset, timestamp,
    │               key, value, headers, leaderEpoch
    │           }
    ├─ commitSync(Map<TopicPartition, OffsetAndMetadata>)
    │   └─ OffsetAndMetadata { offset, metadata, leaderEpoch }
    │   └─ Sent to __consumer_offsets topic (log-compacted)
    └─ seek(TopicPartition, offset)
```

**Key Contract:**
- Consumer group coordination (automatic rebalancing)
- Manual offset commits with metadata
- Partition-aware consumption tracking

### **Phase 3: Flink Source API (Split Enumeration)**

```
Source<T, SplitT, EnumChkT> [Factory]
    ├─ createEnumerator(SplitEnumeratorContext) → SplitEnumerator<SplitT, EnumChkT>
    ├─ getSplitSerializer() → SimpleVersionedSerializer<SplitT>
    ├─ getEnumeratorCheckpointSerializer() → SimpleVersionedSerializer<EnumChkT>
    └─ createSourceReader(SourceReaderContext) → SourceReader<T, SplitT>

SplitEnumerator<SplitT, EnumChkT>
    ├─ start()
    ├─ handleSplitRequest(subtaskId, hostname) → SplitEnumeratorContext.assignSplit()
    ├─ addSplitsBack(splits, subtaskId) [on reader failure]
    ├─ snapshotState(checkpointId) → EnumChkT [coordinator checkpoint]
    └─ notifyCheckpointComplete(checkpointId) [ACK from coordinator]

    [For Kafka: SplitT = KafkaTopicPartition { topic, partition }]
```

**Key Contract:**
- Splits represent independent work units (Kafka: TopicPartition)
- Dynamic assignment via SourceOperator → Coordinator → SplitEnumerator
- Separate checkpoint state (enumerator may track unassigned splits)

### **Phase 4: Flink SourceReader API**

```
SourceReader<T, SplitT>
    ├─ start()
    ├─ pollNext(ReaderOutput<T>) → InputStatus
    │   └─ emit records non-blockingly
    ├─ snapshotState(checkpointId) → List<SplitT>
    │   └─ returns currently assigned splits (state to restore on recovery)
    ├─ addSplits(List<SplitT>) [from SplitEnumerator via SourceOperator]
    ├─ notifyNoMoreSplits()
    ├─ isAvailable() → CompletableFuture<Void>
    │   └─ signals when data is ready to poll
    ├─ handleSourceEvents(SourceEvent) [custom events]
    └─ notifyCheckpointComplete(checkpointId) [checkpoint committed in cluster]
```

**Key Contract:**
- Non-blocking pollNext() in task thread
- snapshotState() returns immutable split state (replayed on recovery)
- notifyCheckpointComplete() signals external system (e.g., commit offsets to Kafka)

### **Phase 5: Flink Connector-Base Framework (SplitReader Pattern)**

```
SourceReaderBase<E, T, SplitT, SplitStateT> [abstract]
    ├─ Composition:
    │   ├─ SplitFetcherManager<E, SplitT>
    │   │   ├─ manages N fetcher threads
    │   │   ├─ creates SplitReader<E, SplitT> per fetcher
    │   │   └─ hand-off queue: FutureCompletingBlockingQueue<RecordsWithSplitIds<E>>
    │   └─ RecordEmitter<E, T, SplitStateT>
    │       └─ converts E (raw element) → T (output type)
    ├─ Abstract methods (subclass implements):
    │   └─ createSplitState(SplitT) → SplitStateT [mutable state per split]
    ├─ Checkpoint flow:
    │   ├─ snapshotState(checkpointId) → List<SplitT>
    │   │   └─ iterates splitStates, extracts SplitT from each
    │   └─ notifyCheckpointComplete(checkpointId)
    │       └─ propagates to RecordEmitter (for offset commits)
    └─ Non-blocking emit:
        ├─ pollNext(output) → InputStatus
        ├─ getNextFetch() from elementsQueue (handed off by fetchers)
        └─ recordEmitter.emitRecord(E, output, SplitStateT)

SplitFetcherManager<E, SplitT>
    ├─ SplitFetcher (per thread)
    │   └─ runs in background thread:
    │       while true:
    │           E[] fetch() via SplitReader
    │           → RecordsWithSplitIds<E>
    │           → put in elementsQueue (non-blocking handoff)
    └─ handleSplitChanges() distributes splits to fetchers

SplitReader<E, SplitT> [high-level API for connectors]
    ├─ fetch() → RecordsWithSplitIds<E>
    │   └─ blocking call, can be interrupted by wakeUp()
    ├─ handleSplitsChanges(SplitsChange<SplitT>)
    │   └─ add/remove splits (non-blocking)
    ├─ wakeUp()
    │   └─ unblock fetch() if sleeping
    └─ pauseOrResumeSplits(pause, resume)
        └─ for watermark alignment

RecordEmitter<E, T, SplitStateT>
    └─ emitRecord(E element, SourceOutput<T> output, SplitStateT splitState)
        └─ convert E → T, update SplitStateT, emit to output
        └─ splitState tracks offset, position, etc. for checkpointing
```

**Key Contract:**
- Hand-off pattern: fetcher threads produce RecordsWithSplitIds → queue → main thread consumes
- Main thread (SourceOperator) never blocks on I/O (fetchers handle blocking)
- SplitState is mutable, updated per record, returned immutable in snapshotState()

### **Phase 6: Flink Runtime Integration (SourceOperator)**

```
SourceOperator<OUT, SplitT> [runtime operator]
    ├─ Initialization:
    │   ├─ initializeState(StateInitializationContext)
    │   │   └─ readerState = ListState<byte[]> (split serialization)
    │   └─ open()
    │       ├─ create SourceReader from factory
    │       ├─ restore readerState (splits to reader)
    │       └─ reader.start()
    │
    ├─ Main streaming loop:
    │   └─ emitNext(DataOutput<OUT>)
    │       └─ sourceReader.pollNext(output) → InputStatus
    │
    ├─ Checkpoint flow:
    │   ├─ snapshotState(StateSnapshotContext)
    │   │   ├─ sourceReader.snapshotState(checkpointId) → List<SplitT>
    │   │   ├─ serialize via splitSerializer
    │   │   └─ write to readerState ListState
    │   │
    │   └─ notifyCheckpointComplete(checkpointId) [after cluster confirms]
    │       ├─ sourceReader.notifyCheckpointComplete(checkpointId)
    │       │   └─ propagates to SourceReaderBase
    │       │       └─ propagates to RecordEmitter
    │       │           └─ (Kafka connector calls consumer.commitSync() here)
    │       └─ SplitEnumerator.notifyCheckpointComplete() [via coordinator]
    │
    └─ Event handling:
        ├─ AddSplitEvent → sourceReader.addSplits()
        ├─ NoMoreSplitsEvent → sourceReader.notifyNoMoreSplits()
        ├─ SourceEventWrapper → sourceReader.handleSourceEvents()
        └─ WatermarkAlignmentEvent → checkSplitWatermarkAlignment()
```

**State Snapshots:**
- Operator state: `SPLITS_STATE_DESC = ListState<byte[]>` (serialized splits)
- Each split contains offset/position in its SplitState
- On recovery: deserialize splits → restore to reader → continue from checkpoint

### **Phase 7: Serialization Boundary (Dual Serialization)**

```
Kafka Layer (Type-Unknown):
    ├─ Kafka Serializer<K>: K → byte[]
    ├─ Kafka Deserializer<V>: byte[] → V
    └─ Topic-aware, header-aware

Flink Connector Layer (Type-Aware):
    ├─ Input: ConsumerRecord<byte[], byte[]> from Kafka
    ├─ deserialize via Kafka Deserializer
    │   └─ ConsumerRecord<K, V> (intermediate)
    │
    ├─ SplitReader.fetch() → E (intermediate element)
    │   └─ E contains ConsumerRecord + offsets + metadata
    │
    └─ RecordEmitter.emitRecord(E, output, SplitState) → T (output type)
        └─ may transform, filter, deserialize further (e.g., JSON → POJO)
        └─ calls output.collect(T)

Flink Schema Layer (Optional):
    ├─ DeserializationSchema<T>: byte[] → T
    ├─ May be applied in RecordEmitter
    └─ Type information for type system (TypeInformation<T>)
```

**Key Insight:**
- Kafka handles raw serialization (key/value bytes)
- Flink's RecordEmitter applies additional deserialization if needed
- SplitState remains typed (contains offset, partition, etc.)

### **Phase 8: Checkpoint-Offset Integration (Capital Markets Trade Ingestion)**

```
Trade Ingestion Pipeline:
    Kafka Topic: "trading.events" (partitions by venue)
    ├─ ProducerRecord: venue_id, order_id, execution_price, timestamp, trade_legs[]
    ├─ Serialize: JSON → Avro bytes
    └─ Kafka Offset: [partition=0, offset=1000]

Flink Job (5 parallel SourceReaders):
    ├─ SplitEnumerator.start()
    │   └─ discover 5 partitions, assign 1 per reader
    │
    ├─ SourceOperator.open()
    │   └─ register 5 readers with coordinator
    │
    ├─ Streaming loop (every ms):
    │   ├─ SourceOperator.emitNext()
    │   │   ├─ reader[0].pollNext(output)
    │   │   │   ├─ SplitReader fetches from Kafka partition 0
    │   │   │   │   └─ KafkaConsumer.poll() → ConsumerRecord batch
    │   │   │   ├─ RecordEmitter deserializes Avro → Trade POJO
    │   │   │   └─ Emits Trade with offset=1000 in split state
    │   │   ├─ Watermark emitted (event time from Trade.timestamp)
    │   │   └─ OUT → downstream operators (risk calc, pricing)
    │
    ├─ Checkpoint triggered (every 30s):
    │   ├─ JobManager.triggerCheckpoint(checkpointId=42)
    │   ├─ SourceOperator.snapshotState()
    │   │   ├─ reader[0].snapshotState(42)
    │   │   │   └─ [KafkaTopicPartition(0, 1000), KafkaTopicPartition(1, 2000), ...]
    │   │   ├─ splitSerializer serializes splits → byte[]
    │   │   └─ readerState.addAll([serialized splits...])
    │   │
    │   ├─ Downstream operators snapshot state
    │   └─ JobManager collects all snapshots → checkpoint store
    │
    ├─ Checkpoint confirmed:
    │   ├─ JobManager notifies all operators: checkpointId=42 completed
    │   │   (once all operators + all sinks acknowledged)
    │   ├─ SourceOperator.notifyCheckpointComplete(42)
    │   │   ├─ sourceReader.notifyCheckpointComplete(42)
    │   │   │   ├─ SourceReaderBase.notifyCheckpointComplete(42)
    │   │   │   │   ├─ splitStates.forEach(context -> context.notifyCheckpointComplete(42))
    │   │   │   │   └─ recordEmitter.notifyCheckpointComplete(42) [if applicable]
    │   │   │   │
    │   │   │   └─ Kafka Connector's RecordEmitter:
    │   │   │       ├─ onCheckpointComplete(checkpointId=42)
    │   │   │       │   └─ kafkaConsumer.commitSync(
    │   │   │       │       {
    │   │   │       │           TopicPartition(0): OffsetAndMetadata(offset=1000),
    │   │   │       │           TopicPartition(1): OffsetAndMetadata(offset=2000),
    │   │   │           ...
    │   │   │       })
    │   │   │       └─ Broker: update __consumer_offsets topic
    │   │   │           └─ consumer group "flink-trading" → checkpoint 42
    │   │   │
    │   │   └─ SplitEnumerator.notifyCheckpointComplete(42) [via coordinator]
    │   │       └─ coordinator may rebalance if needed
    │   └─ Downstream processors similarly acknowledge
    │
    └─ Recovery scenario (job crashed):
        ├─ Restart job
        ├─ JobManager restores checkpoint 42
        ├─ SourceOperator.open() → initializeState()
        │   ├─ readerState.get() → [serialized splits]
        │   ├─ splitSerializer.deserialize() → [KafkaTopicPartition(0, 1000), ...]
        │   └─ sourceReader.addSplits([...])
        ├─ Kafka Connector:
        │   ├─ KafkaConsumer.seek(TopicPartition(0), 1000)
        │   ├─ poll() → resume from offset 1000 (not 0!)
        │   └─ (trades 0-999 already processed and persisted)
        └─ Downstream: restore their state, continue
```

**Guarantees:**
- **At-least-once:** Offsets only committed after checkpoint confirmed (no loss)
- **Exactly-once (with sinks):** Combined with 2PC or idempotent writes
- **Consumer Group Rebalancing:** If reader fails, rebalancer assigns partitions to other readers
- **Durability:** Offsets in Kafka (log-compacted), state in state backend (RocksDB/S3)

---

## Architecture Analysis

### 1. How Kafka's Consumer API is Wrapped by Flink's SplitReader

**Kafka's model:**
- `KafkaConsumer.poll()` → blocks, returns ConsumerRecords
- Single thread (user thread must be single-threaded for KafkaConsumer)
- Rebalance listeners on subscribed topics

**Flink's SplitReader wrapper:**
- `SplitReader.fetch()` → blocking call, interruptible via `wakeUp()`
- Runs in dedicated fetcher thread (not main task thread)
- Handles `handleSplitsChanges()` for dynamic reassignment
- No rebalance listeners (Flink coordinator handles reassignment)

**Integration (in Kafka Connector):**
```java
public class KafkaSplitReader implements SplitReader<ConsumerRecord<K, V>, KafkaTopicPartition> {
    private final KafkaConsumer<K, V> consumer;

    public RecordsWithSplitIds<ConsumerRecord<K, V>> fetch() {
        // consumer is already seek() to the split's offset
        ConsumerRecords<K, V> records = consumer.poll(Duration.ofMillis(100));
        return new RecordsWithSplitIds<>(records, splitId, finished);
    }

    public void handleSplitsChanges(SplitsChange<KafkaTopicPartition> change) {
        for (KafkaTopicPartition split : change.newSplits()) {
            consumer.assign(change.newSplits());
            // seek to each split's starting offset
        }
    }
}
```

### 2. The Dual Serialization Boundary

**Layer 1: Kafka Serializer/Deserializer**
- Location: `org.apache.kafka.common.serialization`
- Purpose: Transport layer (topic → wire format)
- Input: Typed object (K, V)
- Output: byte[]
- Topic-aware: can use different serdes per topic
- Example: `StringSerializer`, `IntegerDeserializer`, `ByteArrayDeserializer`

**Layer 2: Flink DeserializationSchema**
- Location: `org.apache.flink.api.common.serialization`
- Purpose: Application layer (wire format → business object)
- Input: byte[] from Kafka
- Output: Typed object (T) for downstream
- Type-aware: carries TypeInformation<T>
- Example: `JsonDeserializationSchema<Trade>`, `AvroDeserializationSchema<Order>`

**Typical Flow:**
```
Kafka wire format (Avro bytes)
    ↓
Kafka Deserializer<V> (configured per topic)
    → ConsumerRecord<String, MyAvroClass>
    ↓
Flink RecordEmitter (delegates to DeserializationSchema if needed)
    → may apply further transformations
    → Emit T to downstream
```

**Why two layers?**
- Kafka layer: handles protocol, knows topic configuration
- Flink layer: handles business logic, type coercion, watermark extraction

### 3. How Checkpoint Completion Triggers Kafka Offset Commits

**State Snapshot Path:**
```
SourceOperator.snapshotState(StateSnapshotContext context)
├─ sourceReader.snapshotState(checkpointId) → List<SplitT>
├─ serialize splits (including current offsets)
└─ write to operatorState (ListState<byte[]>)
```

**Post-Checkpoint Callback:**
```
SourceOperator.notifyCheckpointComplete(checkpointId)
├─ sourceReader.notifyCheckpointComplete(checkpointId)
│   └─ SourceReaderBase.notifyCheckpointComplete(checkpointId)
│       ├─ splitStates.forEach(context -> {
│       │   context.notifyCheckpointComplete(checkpointId)
│       │   // SplitState might update internal tracking
│       │ })
│       └─ recordEmitter.notifyCheckpointComplete(checkpointId)
│           └─ Kafka Connector's implementation:
│               kafkaConsumer.commitSync(
│                   buildCommitMap(splitStates.getOffsets())
│               )
│
└─ coordinator also notified (via SourceCoordinator) for SplitEnumerator state
```

**Why not commit during snapshotState()?**
- snapshotState() is per-task, runs in parallel
- notifyCheckpointComplete() is cluster-wide, happens after all tasks + sinks confirm
- Ensures commit only after guarantee of persistence (exactly-once)

**Atomicity:**
- Flink checkpoint = atomic snapshot of entire job
- Offset commit only after all downstream operators have also checkpointed
- If job crashes between snapshot and commit, offsets not advanced (at-least-once)

### 4. Consumer Group Coordination Model

**Kafka side:**
- Consumer group: "flink-job-xyz" (configured in KafkaConsumer)
- Coordinator broker: elected by partition
- Rebalance: triggered on join, leave, or timeout
- Assignment: Flink Kafka connector can use custom assignor (e.g., sticky)

**Flink side:**
- SourceCoordinator: coordinator in JobManager (not in Kafka)
- SplitEnumerator: runs in coordinator, owns split discovery
- Operator events: SourceOperator ↔ SourceCoordinator (ReaderRegistrationEvent, AddSplitEvent)
- No interaction with Kafka coordinator (Kafka offset tracking only)

**Flow:**
```
Job start:
├─ Flink SourceCoordinator.start()
│   └─ SplitEnumerator.start()
│       ├─ discover Kafka TopicPartitions
│       └─ assign to SplitEnumeratorContext
│
├─ SourceOperator.open()
│   ├─ register with coordinator (ReaderRegistrationEvent)
│   └─ wait for AddSplitEvent
│
├─ SourceCoordinator handles registration
│   ├─ SplitEnumerator.addReader(subtask_id)
│   ├─ SplitEnumerator.handleSplitRequest()
│   └─ send AddSplitEvent to SourceOperator
│
└─ SourceOperator receives splits
    └─ reader.addSplits(splits)

Rebalance (if reader fails):
├─ SourceCoordinator detects failure
├─ SplitEnumerator.addSplitsBack(splits, failed_subtask)
├─ SplitEnumerator.handleSplitRequest(active_subtask)
└─ send AddSplitEvent to remaining readers
```

### 5. Thread Architecture: Kafka's Fetcher vs Flink's SplitFetcherManager

**Kafka's model:**
```
User thread (single-threaded constraint):
├─ poll() → blocks
├─ commitSync() → blocks
└─ subscribe() / seek() → non-blocking

Internal threads (managed by KafkaConsumer):
├─ Fetcher thread (per consumer): fetches from brokers
│   └─ reads into per-partition queue
├─ Sender thread (if producer): sends batches
└─ Heartbeat thread: maintains group membership
```

**Flink's model:**
```
Task thread (SourceOperator, non-blocking):
├─ emitNext(output) → non-blocking
│   ├─ if no fetch: poll elementsQueue (timeout 0 ms)
│   └─ if fetch: emit records
├─ notifyCheckpointComplete() → non-blocking
└─ handleOperatorEvent() → non-blocking

Fetcher threads (per SplitFetcher, configurable):
├─ run in background (pool size: default N = parallelism)
├─ SplitReader.fetch() → blocking (Kafka poll, file read, etc.)
├─ RecordsWithSplitIds → put in elementsQueue
└─ main task thread polls queue every ms
```

**Advantage:**
- Flink task thread never blocks on I/O
- Scaling: fetcher threads scale with parallelism (not hardcoded)
- Latency: main thread always responsive (timeouts, watermarks, barriers)
- Backpressure: if downstream slow, queue fills, fetchers sleep

---

## Summary

**Kafka-Flink streaming data flow is a sophisticated multi-layer architecture:**

1. **Kafka layer** produces ProducerRecords (key, value, partition, timestamp) and serializes via pluggable Serializers. Consumers deserialize via Deserializers, tracking offsets per partition and committing to __consumer_offsets via commitSync().

2. **Flink Source API** abstracts data discovery (SplitEnumerator) from data consumption (SourceReader), enabling dynamic split reassignment and independent checkpointing of splits and enumerator state.

3. **Connector-Base framework** bridges the gap with SourceReaderBase providing hand-off queues, state management, and non-blocking record emission via RecordEmitter. SplitReader interface hides source-specific I/O (Kafka, files, databases) behind a consistent polling API.

4. **SourceOperator runtime** integrates readers with Flink's checkpoint barrier mechanism, snapshotting split state per task and broadcasting notifyCheckpointComplete to trigger external commits (e.g., Kafka consumer offset commits) only after cluster-wide guarantee.

5. **Serialization boundary** spans two layers: Kafka's transport serialization (topic-aware, low-level) and Flink's schema deserialization (type-aware, business logic). The Kafka Connector's RecordEmitter consumes Kafka's deserialized objects and applies Flink's DeserializationSchema if needed.

6. **For capital markets trade ingestion**, this enables exactly-once processing: each trade is consumed once (Kafka offset tracking), processed once (stateful operators), and written once (idempotent sinks), with recovery resuming from the last committed checkpoint's offset without reprocessing or data loss.

