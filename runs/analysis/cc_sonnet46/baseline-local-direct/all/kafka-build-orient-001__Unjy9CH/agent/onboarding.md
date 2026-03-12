# Apache Kafka Codebase Orientation

## 1. Build System and Broker Startup

### Build System
Kafka uses **Gradle** as its build system. The root `build.gradle` defines the overall build configuration, plugins, and subproject dependencies. The `settings.gradle` declares all included subprojects. Key build commands:
- `./gradlew build` — full build
- `./gradlew test` — run all tests
- `./gradlew :core:test` — run tests for a specific module

Gradle plugins used include `java-library`, `com.github.spotbugs`, `org.scoverage` (Scala coverage), and `com.github.johnrengelman.shadow` for fat JARs.

### Broker Startup Entry Point
The main entry point is `kafka.Kafka` object in `core/src/main/scala/kafka/Kafka.scala`.

The startup script `bin/kafka-server-start.sh` calls:
```
bin/kafka-run-class.sh kafka.Kafka server.properties
```

**Key classes in broker initialization:**

1. **`kafka.Kafka`** (`core/src/main/scala/kafka/Kafka.scala`)
   - `main()` parses config properties from the command line
   - `buildServer()` decides which server implementation to instantiate based on `process.roles` config
   - If ZooKeeper mode: creates `KafkaServer`
   - If KRaft mode: creates `KafkaRaftServer`
   - Registers shutdown hook, calls `server.startup()`, then `server.awaitShutdown()`

2. **`KafkaRaftServer`** (`core/src/main/scala/kafka/server/KafkaRaftServer.scala`)
   - Implements KRaft (Kafka Raft) mode — the modern, ZooKeeper-free mode
   - Initializes log directories and bootstrap metadata via `KafkaRaftServer.initializeLogDirs()`
   - Creates a `SharedServer` (shared resources like metrics, Raft manager)
   - Creates optional `BrokerServer` (if `process.roles` includes `broker`)
   - Creates optional `ControllerServer` (if `process.roles` includes `controller`)
   - `startup()` starts the controller first, then the broker

3. **`BrokerServer`** (`core/src/main/scala/kafka/server/BrokerServer.scala`)
   - Implements a KRaft-mode broker
   - `startup()` initializes in order:
     - `KafkaScheduler` (background threads)
     - `BrokerTopicStats`, `QuotaFactory`, `LogDirFailureChannel`
     - `MetadataCache` (KRaft variant)
     - `LogManager` (manages on-disk log segments)
     - `BrokerLifecycleManager` (handles broker registration with controller)
     - `SocketServer` (network layer)
     - `KafkaApis` (request handler dispatch)
     - `KafkaRequestHandlerPool` (thread pool for request processing)

4. **`KafkaServer`** (`core/src/main/scala/kafka/server/KafkaServer.scala`)
   - Legacy ZooKeeper-based broker implementation
   - Follows the same general pattern but uses ZooKeeper for metadata

5. **`KafkaApis`** (`core/src/main/scala/kafka/server/KafkaApis.scala`)
   - Central request dispatcher; maps `ApiKeys` enum values to handler methods
   - Every Kafka protocol API (Produce, Fetch, CreateTopics, etc.) has a corresponding `handle*` method

---

## 2. Module Structure

Kafka is organized as a multi-project Gradle build. Key modules declared in `settings.gradle`:

### Core Modules

| Module | Location | Responsibility |
|--------|----------|----------------|
| `clients` | `clients/` | Java client library (Producer, Consumer, Admin, Streams interfaces). The public API surface for all Kafka clients. |
| `core` | `core/` | The main broker implementation in Scala. Contains `KafkaApis`, `KafkaServer`, `BrokerServer`, `KafkaRaftServer`, `LogManager`, `ReplicaManager`, controllers, coordinators, and the `kafka.Kafka` main entry point. |
| `server` | `server/` | Broker server configuration classes (`AbstractKafkaConfig`, `ServerConfigs`, `KRaftConfigs`, `ReplicationConfigs`, etc.). Being extracted from `core` as part of KAFKA-15853. |
| `server-common` | `server-common/` | Shared utilities used across broker and controller. |
| `metadata` | `metadata/` | KRaft metadata layer: `QuorumController`, `ReplicationControlManager`, `ConfigurationControlManager`, snapshot handling, and image-based metadata propagation. |
| `raft` | `raft/` | The Raft consensus implementation (`KafkaRaftClient`) used in KRaft mode. |
| `storage` | `storage/` | Low-level log storage: `UnifiedLog`, `LogSegment`, `LogManager` internals, index files. |
| `storage:api` | `storage/api/` | Public storage API interfaces. |
| `connect` | `connect/` | Kafka Connect framework (API, runtime, transforms, file/JSON connectors, mirror maker). |
| `streams` | `streams/` | Kafka Streams DSL and processor API for stream processing. |
| `group-coordinator` | `group-coordinator/` | Consumer group coordinator logic (group membership, offset management). |
| `transaction-coordinator` | `transaction-coordinator/` | Transaction coordinator (producer ID management, transaction state). |
| `tools` | `tools/` | CLI tools (kafka-topics.sh, kafka-consumer-groups.sh, etc.). |
| `shell` | `shell/` | Interactive Kafka shell utilities. |
| `generator` | `generator/` | Code generator for Kafka protocol message schemas. |
| `jmh-benchmarks` | `jmh-benchmarks/` | JMH microbenchmarks. |
| `trogdor` | `trogdor/` | Distributed test framework for fault injection and workload generation. |

### Dependency Flow
```
clients  <--  server-common  <--  server  <--  core
                                   ^
                               metadata
                               raft
                               storage
```

The `core` module pulls together all other modules and implements the runnable broker binary.

---

## 3. Topic Creation Flow

Topic creation follows a multi-step path through the network layer, request handler, and controller.

### Step 1: Client sends CreateTopics request
The Kafka Admin client (in `clients/`) constructs a `CreateTopicsRequest` and sends it to the broker's socket server.

### Step 2: Network layer receives request
**`SocketServer`** (`core/src/main/scala/kafka/network/SocketServer.scala`) accepts the TCP connection via `DataPlaneAcceptor`. The request is queued into the request channel.

### Step 3: Request dispatched to KafkaApis
**`KafkaRequestHandler`** (`core/src/main/scala/kafka/server/KafkaRequestHandler.scala`) pulls the request from the queue and calls `KafkaApis.handle()`.

**`KafkaApis.handle()`** (`core/src/main/scala/kafka/server/KafkaApis.scala:208`) dispatches based on API key:
```scala
case ApiKeys.CREATE_TOPICS => maybeForwardToController(request, handleCreateTopicsRequest)
```

### Step 4: Forwarding to controller (KRaft mode)
In KRaft mode, `maybeForwardToController()` forwards the request to the active controller node via `ControllerApis`.

**`ControllerApis.handleCreateTopics()`** (`core/src/main/scala/kafka/server/ControllerApis.scala:361`):
- Parses `CreateTopicsRequest`
- Applies controller mutation quota
- Calls `createTopics()` (`ControllerApis.scala:389`) which:
  - Filters duplicate topic names
  - Checks authorization (CREATE on CLUSTER or TOPIC resource)
  - Calls `controller.createTopics(context, effectiveRequest, describableTopicNames)`

### Step 5: QuorumController processes the request
**`QuorumController.createTopics()`** (`metadata/src/main/java/org/apache/kafka/controller/QuorumController.java:2047`):
```java
return appendWriteEvent("createTopics", context.deadlineNs(),
    () -> replicationControl.createTopics(context, request, describable));
```
This enqueues a write event to the Raft log. The event is linearized through the Raft consensus layer.

### Step 6: ReplicationControlManager creates the topic
**`ReplicationControlManager.createTopics()`** (`metadata/src/main/java/org/apache/kafka/controller/ReplicationControlManager.java:587`):
1. `validateNewTopicNames()` — checks topic naming rules
2. Checks for duplicate/existing topics
3. `computeConfigChanges()` — validates topic-level configs
4. For each valid topic, calls `createTopic()` which:
   - Assigns partitions to brokers (rack-aware assignment)
   - Creates `TopicRecord`, `PartitionRecord`, config records
   - Returns `ControllerResult<CreateTopicsResponseData>` containing metadata records to append

### Step 7: Records committed to Raft log
The generated metadata records (`TopicRecord`, `PartitionRecord`) are appended to the Raft log via `KafkaRaftClient`. Once committed by a quorum of controllers, they are applied to the in-memory metadata image.

### Step 8: Brokers receive metadata update
Brokers subscribe to metadata updates via `BrokerMetadataPublisher`. When the new topic records are replicated to brokers, `LogManager` creates the local partition directories and `ReplicaManager` starts partition leadership/follower handling.

### Key classes summary:
- `KafkaApis` — routes request
- `ControllerApis.createTopics()` — authorization + controller call
- `QuorumController.createTopics()` — enqueues write event to Raft
- `ReplicationControlManager.createTopics()` — actual topic creation logic
- `ConfigurationControlManager.incrementalAlterConfig()` — handles topic config records

---

## 4. Testing Framework

### Test Frameworks Used
Kafka uses **JUnit 5** (Jupiter) as the primary test framework for both Java and Scala tests:
- Annotations: `@Test`, `@BeforeEach`, `@AfterEach`, `@ParameterizedTest`, `@Timeout`
- Assertions: `org.junit.jupiter.api.Assertions.*`

For mocking, Kafka uses **Mockito**:
- `org.mockito.Mockito.mock()`, `when()`, `verify()`
- `org.mockito.ArgumentCaptor`

### Unit Test Patterns
Unit tests live in `core/src/test/scala/unit/` and `*/src/test/java/` or `*/src/test/scala/`.

**Typical unit test** (e.g., `KafkaApisTest.scala`):
```scala
class KafkaApisTest extends Logging {
  @Test
  def testSomeMethod(): Unit = {
    val mockReplicaManager = mock(classOf[ReplicaManager])
    when(mockReplicaManager.someMethod()).thenReturn(someValue)
    // exercise the code
    verify(mockReplicaManager).someMethod()
  }
}
```
Tests use `TestUtils` (`core/src/test/scala/unit/kafka/utils/TestUtils.scala`) for helper methods:
- `TestUtils.createBrokerConfig(nodeId, zkConnect)` — create broker properties
- `TestUtils.waitUntilTrue(condition, msg)` — poll until condition is true
- `TestUtils.createTopicWithAdmin(...)` — create a topic via Admin client

### Integration Test Patterns
Integration tests live in `core/src/test/scala/integration/`. They extend base harnesses:

1. **`KafkaServerTestHarness`** (`core/src/test/scala/unit/kafka/integration/KafkaServerTestHarness.scala`): Starts real broker(s) for in-process integration testing. Extends this for single-cluster tests.

2. **`IntegrationTestHarness`** (`core/src/test/scala/integration/kafka/api/IntegrationTestHarness.scala`): Extends `KafkaServerTestHarness`; provides pre-built producer/consumer/admin client instances.

```scala
class MyIntegrationTest extends IntegrationTestHarness {
  override def brokerCount = 3
  @Test
  def testTopicCreation(): Unit = {
    createTopic("my-topic", numPartitions = 3, replicationFactor = 2)
    // use client, producer, consumer
  }
}
```

### ClusterTest Framework
For parameterized cluster tests across ZK/KRaft modes, Kafka provides a custom JUnit 5 extension:
- `@ExtendWith(classOf[ClusterTestExtensions])`
- `@ClusterTest(types = Array(Type.KRAFT, Type.CO_KRAFT))`
- `@ClusterTestDefaults(types = Array(Type.KRAFT))`

Example:
```scala
@ExtendWith(value = Array(classOf[ClusterTestExtensions]))
@ClusterTestDefaults(types = Array(Type.KRAFT))
class AllocateProducerIdsRequestTest {
  @ClusterTest
  def testAllocate(): Unit = { ... }

  @ClusterTest(controllers = 3)
  def testWithThreeControllers(): Unit = { ... }
}
```

### Running Tests
```bash
# Run a specific test class
./gradlew :core:test --tests kafka.server.KafkaApisTest

# Run all tests in a module
./gradlew :core:test

# Run with specific JVM args
./gradlew :metadata:test --tests "*.ReplicationControlManagerTest"
```

---

## 5. Configuration System

### Overview
Kafka's configuration system is built on `org.apache.kafka.common.config.ConfigDef` — a registry that defines each config's name, type, default value, validator, importance, and documentation.

### Configuration Registry Location
The master config registry is assembled in **`AbstractKafkaConfig.CONFIG_DEF`** (`server/src/main/java/org/apache/kafka/server/config/AbstractKafkaConfig.java`):

```java
public static final ConfigDef CONFIG_DEF = Utils.mergeConfigs(Arrays.asList(
    RemoteLogManagerConfig.configDef(),
    ZkConfigs.CONFIG_DEF,
    ServerConfigs.CONFIG_DEF,        // general broker configs
    KRaftConfigs.CONFIG_DEF,         // KRaft-specific configs
    SocketServerConfigs.CONFIG_DEF,  // network configs
    ReplicationConfigs.CONFIG_DEF,   // replication configs
    GroupCoordinatorConfig.GROUP_COORDINATOR_CONFIG_DEF,
    CleanerConfig.CONFIG_DEF,
    LogConfig.SERVER_CONFIG_DEF,     // log/topic configs
    TransactionLogConfigs.CONFIG_DEF,
    QuorumConfig.CONFIG_DEF,
    MetricConfigs.CONFIG_DEF,
    QuotaConfigs.CONFIG_DEF,
    BrokerSecurityConfigs.CONFIG_DEF,
    // ...and more
));
```

Each domain-specific config class (e.g., `ServerConfigs`, `ReplicationConfigs`, `KRaftConfigs`) declares constants and builds its own `ConfigDef.CONFIG_DEF`.

### Config Definition Pattern
Configs are defined using a fluent builder in `ConfigDef`:
```java
// In ServerConfigs.java:
public static final String NUM_IO_THREADS_CONFIG = "num.io.threads";
public static final int NUM_IO_THREADS_DEFAULT = 8;
public static final String NUM_IO_THREADS_DOC = "The number of threads...";

public static final ConfigDef CONFIG_DEF = new ConfigDef()
    .define(NUM_IO_THREADS_CONFIG, INT, NUM_IO_THREADS_DEFAULT,
            atLeast(1), HIGH, NUM_IO_THREADS_DOC)
    // ...
```

Parameters: `(name, type, default, validator, importance, documentation)`

### KafkaConfig — The Runtime Config Object
**`KafkaConfig`** (`core/src/main/scala/kafka/server/KafkaConfig.scala`) extends `AbstractKafkaConfig` and provides typed accessors for all broker configs:
```scala
val zkConnect: String = getString(ZkConfigs.ZK_CONNECT_CONFIG)
val numIoThreads: Int = getInt(ServerConfigs.NUM_IO_THREADS_CONFIG)
```

It also manages dynamic config via `DynamicBrokerConfig`.

### Dynamic Configuration
**`DynamicBrokerConfig`** (`core/src/main/scala/kafka/server/DynamicBrokerConfig.scala`) manages configs that can be updated without broker restart:

- **`AllDynamicConfigs`** — set of all dynamically updatable config names
- **`PerBrokerConfigs`** — configs that must be set per-broker (e.g., SSL keystores)
- **Cluster-wide** — configs applied to all brokers (e.g., `num.network.threads`)

Precedence order (highest to lowest):
1. `DYNAMIC_BROKER_CONFIG` — stored in ZK at `/configs/brokers/{brokerId}` or KRaft metadata
2. `DYNAMIC_DEFAULT_BROKER_CONFIG` — stored at `/configs/brokers/<default>`
3. `STATIC_BROKER_CONFIG` — from `server.properties`
4. `DEFAULT_CONFIG` — hardcoded defaults in `ConfigDef`

Validation happens in `DynamicBrokerConfig.validateConfigs()` which checks:
- That only known dynamic configs are in the update
- That per-broker configs aren't applied cluster-wide without a broker ID
- Type validation via `ConfigDef`

---

## 6. Adding a New Broker Config

Here is a step-by-step guide to adding a new broker configuration parameter (e.g., `my.new.feature.enabled`):

### Step 1: Choose the right config class
Determine which domain the config belongs to and add it to the appropriate file under `server/src/main/java/org/apache/kafka/server/config/`:
- General broker behavior → `ServerConfigs.java`
- Replication behavior → `ReplicationConfigs.java`
- KRaft-specific → `KRaftConfigs.java`

### Step 2: Declare constants and add to ConfigDef
In the chosen file (e.g., `ServerConfigs.java`), add:
```java
// Constants
public static final String MY_NEW_FEATURE_ENABLED_CONFIG = "my.new.feature.enabled";
public static final boolean MY_NEW_FEATURE_ENABLED_DEFAULT = false;
public static final String MY_NEW_FEATURE_ENABLED_DOC =
    "Enable the new feature. When true, ...";

// In the CONFIG_DEF definition:
.define(MY_NEW_FEATURE_ENABLED_CONFIG, BOOLEAN,
        MY_NEW_FEATURE_ENABLED_DEFAULT, MEDIUM,
        MY_NEW_FEATURE_ENABLED_DOC)
```

Available types: `BOOLEAN`, `INT`, `LONG`, `DOUBLE`, `STRING`, `LIST`, `CLASS`, `PASSWORD`.
Validators: `atLeast(n)`, `atMost(n)`, `between(lo, hi)`, `ValidString.in(...)`, custom `ConfigDef.Validator`.
Importance levels: `HIGH`, `MEDIUM`, `LOW`.

### Step 3: Add a typed accessor in KafkaConfig
In `core/src/main/scala/kafka/server/KafkaConfig.scala`, add a `val` accessor:
```scala
val myNewFeatureEnabled: Boolean =
  getBoolean(ServerConfigs.MY_NEW_FEATURE_ENABLED_CONFIG)
```

### Step 4: Support dynamic updates (if applicable)
If the config should be updatable without restart:

a. Add it to the appropriate `ReconfigurableConfigs` set in `DynamicBrokerConfig.scala`:
```scala
// In the relevant DynamicXxxConfig object
val ReconfigurableConfigs = Set(
  ServerConfigs.MY_NEW_FEATURE_ENABLED_CONFIG,
  // ...
)
```
And include it in `AllDynamicConfigs`:
```scala
val AllDynamicConfigs = DynamicSecurityConfigs ++
  // ... existing sets ...
  Set(ServerConfigs.MY_NEW_FEATURE_ENABLED_CONFIG)
```

b. Implement the reconfiguration handler in the appropriate `BrokerReconfigurable` class (e.g., `DynamicThreadPool`, `DynamicLogConfig`).

c. If it's per-broker only (not cluster-wide), add it to `PerBrokerConfigs`.

### Step 5: Use the config in broker code
Reference the typed accessor from `KafkaConfig`:
```scala
if (config.myNewFeatureEnabled) {
  // enable the feature
}
```

### Step 6: Add documentation
Update `config/server.properties` and/or `docs/` if the config should appear in the default config template.

### Step 7: Write tests

**Unit test for config validation** (add to `KafkaConfigTest.scala`):
```scala
@Test
def testMyNewFeatureEnabled(): Unit = {
  val props = TestUtils.createBrokerConfig(0, "")
  props.put(ServerConfigs.MY_NEW_FEATURE_ENABLED_CONFIG, "true")
  val config = KafkaConfig.fromProps(props)
  assertTrue(config.myNewFeatureEnabled)
}

@Test
def testMyNewFeatureInvalidValue(): Unit = {
  val props = TestUtils.createBrokerConfig(0, "")
  props.put(ServerConfigs.MY_NEW_FEATURE_ENABLED_CONFIG, "not-a-boolean")
  assertThrows(classOf[ConfigException], () => KafkaConfig.fromProps(props))
}
```

**Integration test for dynamic config update** (if dynamic):
```scala
@Test
def testDynamicUpdate(): Unit = {
  val admin = createAdminClient()
  val config = new ConfigEntry(ServerConfigs.MY_NEW_FEATURE_ENABLED_CONFIG, "true")
  admin.incrementalAlterConfigs(Map(
    new ConfigResource(ConfigResource.Type.BROKER, "") ->
      List(new AlterConfigOp(config, AlterConfigOp.OpType.SET)).asJava
  ).asJava).all().get()
  // verify the change took effect
}
```

### Summary of files to modify:
1. `server/src/main/java/org/apache/kafka/server/config/ServerConfigs.java` (or appropriate config class) — declare constant and add to `CONFIG_DEF`
2. `core/src/main/scala/kafka/server/KafkaConfig.scala` — add typed accessor `val`
3. `core/src/main/scala/kafka/server/DynamicBrokerConfig.scala` — add to `AllDynamicConfigs` / `PerBrokerConfigs` (if dynamic)
4. The relevant component class — use the new config value
5. `core/src/test/scala/unit/kafka/server/KafkaConfigTest.scala` — add validation tests
6. `config/server.properties` — optionally document the new config
