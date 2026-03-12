# Apache Kafka Codebase Orientation

## 1. Build System and Broker Startup

### Build System
Kafka uses **Gradle** as its build system. The main build files are:
- `build.gradle` — root-level build configuration, shared settings for all subprojects
- `settings.gradle` — declares all included subproject modules
- `gradle.properties` — global Gradle properties
- `gradlew` / `gradlewAll` — Gradle wrapper scripts for reproducible builds

Common build commands:
```
./gradlew build            # Build all modules
./gradlew :core:test       # Run core module tests
./gradlew :clients:jar     # Build clients jar
```

### Main Entry Point
The broker entry point is `kafka.Kafka` object in `core/src/main/scala/kafka/Kafka.scala`. Its `main()` method:
1. Parses command-line arguments (first arg is `server.properties` path; `--override key=value` allows property overrides)
2. Calls `buildServer(props)` which creates either a `KafkaServer` (ZooKeeper mode) or `KafkaRaftServer` (KRaft mode) based on `config.requiresZookeeper`
3. Registers a JVM shutdown hook calling `server.shutdown()`
4. Calls `server.startup()`
5. Calls `server.awaitShutdown()` to block until done

### Key Classes in Broker Initialization

**ZooKeeper mode (`KafkaServer`)** — `core/src/main/scala/kafka/server/KafkaServer.scala`:
- Implements `KafkaBroker` and `Server` traits
- `startup()` initializes components in order: ZooKeeper client, LogManager, ReplicaManager, GroupCoordinator, TransactionCoordinator, KafkaController, SocketServer, KafkaRequestHandlerPool
- `LogManager.startup()` recovers existing log segments from disk
- `ReplicaManager.startup()` begins ISR shrink/expand background threads
- The controller election happens via ZooKeeper ephemeral nodes

**KRaft mode (`KafkaRaftServer`)** — `core/src/main/scala/kafka/server/KafkaRaftServer.scala`:
- Wraps optional `BrokerServer` and `ControllerServer` components (a node can be a broker, controller, or both based on `process.roles` config)
- Startup order: controller first, then broker (so controller endpoints are available to the Raft manager)
- Uses `SharedServer` for shared Raft infrastructure between broker and controller roles

**`BrokerServer`** — `core/src/main/scala/kafka/server/BrokerServer.scala`:
- KRaft broker component; `startup()` creates LogManager, ReplicaManager, GroupCoordinator, etc.

**`ControllerServer`** — `core/src/main/scala/kafka/server/ControllerServer.scala`:
- KRaft controller component; manages cluster metadata via Raft consensus

**`SharedServer`** — `core/src/main/scala/kafka/server/SharedServer.scala`:
- Hosts the Raft manager (`KafkaRaftManager`) shared between controller and broker in combined-mode nodes

---

## 2. Module Structure

Kafka is organized as a multi-project Gradle build. Core modules (from `settings.gradle`):

| Module | Path | Responsibility |
|--------|------|----------------|
| `core` | `core/` | Main broker implementation: `KafkaServer`, `KafkaRaftServer`, `KafkaApis`, `KafkaController`, `ReplicaManager`, `LogManager`. Written primarily in Scala. |
| `clients` | `clients/` | Java client libraries: `KafkaProducer`, `KafkaConsumer`, `AdminClient`. Network protocol layer, serialization. |
| `server` | `server/` | Broker configuration (`AbstractKafkaConfig`, `ServerConfigs`, `KRaftConfigs`, `ReplicationConfigs`), metrics, fault handling. Being extracted from `core` (KAFKA-15853). |
| `server-common` | `server-common/` | Shared server utilities used across modules. |
| `storage` | `storage/` | Log storage engine: `UnifiedLog`, `LogSegment`, `LogConfig`, `LogCleaner`. |
| `storage:api` | `storage/api/` | Public storage API interfaces. |
| `metadata` | `metadata/` | Metadata management: `KafkaConfigSchema`, image/snapshot handling for KRaft. |
| `raft` | `raft/` | Raft consensus implementation (`KafkaRaftClient`) used by the KRaft controller. |
| `group-coordinator` | `group-coordinator/` | Consumer group and share-group coordinator logic (`GroupCoordinator`). |
| `transaction-coordinator` | `transaction-coordinator/` | Transaction coordinator logic (`TransactionCoordinator`, `TransactionStateManager`). |
| `connect` | `connect/` | Kafka Connect framework (runtime, API, transforms, file/mirror connectors). |
| `streams` | `streams/` | Kafka Streams DSL and processor API. |
| `tools` | `tools/` | CLI tools (`kafka-topics.sh`, `kafka-consumer-groups.sh`, etc.). |
| `shell` | `shell/` | Interactive shell utilities. |
| `generator` | `generator/` | Code generator for message schemas (produces Java classes from JSON schema files in `clients/src/main/resources/common/message/`). |
| `trogdor` | `trogdor/` | Distributed fault injection and performance testing framework. |
| `jmh-benchmarks` | `jmh-benchmarks/` | JMH microbenchmarks for performance testing. |

---

## 3. Topic Creation Flow

Topic creation follows this end-to-end path (ZooKeeper mode):

### Step 1 — Client sends CreateTopics request
A client (e.g., `AdminClient`) sends a `CreateTopicsRequest` over the Kafka binary protocol to a broker. If the broker is not the controller, it can forward the request.

### Step 2 — SocketServer / RequestChannel
The broker's `SocketServer` receives the raw bytes and enqueues a `RequestChannel.Request` object.

### Step 3 — KafkaRequestHandler → KafkaApis
`KafkaRequestHandler` threads dequeue requests and dispatch to `KafkaApis.handle()`:
```
// core/src/main/scala/kafka/server/KafkaApis.scala:208
case ApiKeys.CREATE_TOPICS => maybeForwardToController(request, handleCreateTopicsRequest)
```
`maybeForwardToController` ensures only the active controller processes the request. If this broker is not the controller, it forwards the request.

### Step 4 — KafkaApis.handleCreateTopicsRequest()
`core/src/main/scala/kafka/server/KafkaApis.scala` (line ~2002):
1. Extracts `CreateTopicsRequest` from the `RequestChannel.Request`
2. Checks if the current broker is the active controller; returns `NOT_CONTROLLER` error if not
3. Performs authorization checks (requires `CREATE` ACL on `CLUSTER` or `TOPIC` resource)
4. Filters out unauthorized topics and the internal `__cluster_metadata` topic
5. Calls `zkSupport.adminManager.createTopics(...)` with a callback

### Step 5 — ZkAdminManager.createTopics()
`core/src/main/scala/kafka/server/ZkAdminManager.scala` (line ~159):
1. Gets alive brokers from `metadataCache`
2. For each topic:
   - Checks topic doesn't already exist
   - Resolves partition count and replication factor (from request or broker defaults)
   - Computes replica-to-broker assignment via `AdminUtils.assignReplicasToBrokers()`
   - Validates the topic config via `adminZkClient.validateTopicCreate()`
   - Calls `adminZkClient.createTopicWithAssignment()` to write to ZooKeeper
3. If `timeout > 0` and topics were created, wraps in a `DelayedCreatePartitions` purgatory operation to wait for partition leaders to be elected

### Step 6 — AdminZkClient / KafkaZkClient writes to ZooKeeper
`adminZkClient.createTopicWithAssignment()` writes:
- `/brokers/topics/<topic-name>` — partition assignments
- `/config/topics/<topic-name>` — topic-level configs

### Step 7 — KafkaController reacts via ZooKeeper watch
The `KafkaController` watches `/brokers/topics` in ZooKeeper. When a new topic node appears, it:
1. Elects partition leaders using the leader election algorithm
2. Updates the ISR
3. Sends `LeaderAndIsr` and `UpdateMetadata` requests to all affected brokers

### Step 8 — Response sent to client
Once partition leaders are confirmed (or timeout expires), the callback fires, `sendResponseCallback` sends `CreateTopicsResponse` back to the client.

**KRaft mode** differs: `CREATE_TOPICS` is always forwarded to the active controller, which uses `ReplicationControlManager` in the `QuorumController` to atomically create topics via Raft log entries.

---

## 4. Testing Framework

### Frameworks Used
Kafka uses a mix of frameworks depending on the test type:

- **JUnit 5** (`@Test`, `@BeforeEach`, `@AfterEach`, `@Timeout`) — primary test runner for both Scala and Java tests
- **ScalaTest** — some older tests use ScalaTest, but JUnit 5 is preferred for new tests
- **Mockito** — mocking framework for unit tests (used extensively in `KafkaApisTest`)

### Unit Test Patterns

**Pure unit tests** mock dependencies with Mockito:
```scala
// core/src/test/scala/unit/kafka/server/KafkaApisTest.scala
private val groupCoordinator: GroupCoordinator = mock(classOf[GroupCoordinator])
private val adminManager: ZkAdminManager = mock(classOf[ZkAdminManager])
```

**Scala unit tests** live under `core/src/test/scala/unit/` and Java unit tests under `core/src/test/java/`.

### Integration Test Patterns

**Pattern 1 — QuorumTestHarness (base for ZK/KRaft tests)**
`core/src/test/scala/integration/kafka/server/QuorumTestHarness.scala`:
- Abstract base class that sets up a ZooKeeper or KRaft quorum
- Extend `QuorumTestHarness` for controller/broker integration tests

**Pattern 2 — KafkaServerTestHarness**
`core/src/test/scala/unit/kafka/integration/KafkaServerTestHarness.scala`:
- Extends `QuorumTestHarness`; also starts full broker nodes
- Use for tests that need live broker(s)

**Pattern 3 — ClusterTestExtensions / @ClusterTest annotation**
Kafka's custom JUnit 5 extension for parameterized cluster tests:
```scala
@ExtendWith(value = Array(classOf[ClusterTestExtensions]))
@ClusterTestDefaults(types = Array(Type.KRAFT))
class MyTest(cluster: ClusterInstance) {
  @ClusterTest(types = Array(Type.ZK, Type.KRAFT))
  def testSomething(): Unit = { ... }
}
```
- `kafka.test.annotation.ClusterTest` — configures the cluster (type, brokers, controllers, server properties)
- `kafka.test.junit.ClusterTestExtensions` — JUnit 5 extension that provisions cluster instances
- Tests run against ZK, KRaft, or both depending on `types` annotation
- `ClusterInstance` provides access to broker addresses, admin clients, etc.

**Pattern 4 — KafkaClusterTestKit**
`core/src/test/java/kafka/testkit/KafkaClusterTestKit.java`:
- Programmatic API for spinning up in-process KRaft clusters in Java tests

### Key Test Utilities
- `kafka.utils.TestUtils` — rich set of helpers: `createTopic()`, `waitUntilTrue()`, `assertFutureExceptionTypeEquals()`, `createServer()`
- `EmbeddedKafkaCluster` (`streams/src/test/java`) — embedded cluster for Kafka Streams integration tests

---

## 5. Configuration System

### Architecture Overview
Kafka's configuration system is built on `ConfigDef` (from `clients/`) which defines the schema for each configuration parameter including type, default value, importance, documentation, and validation rules.

### Configuration Registry Location
The master broker `ConfigDef` is assembled in:
**`server/src/main/java/org/apache/kafka/server/config/AbstractKafkaConfig.java`**:
```java
public static final ConfigDef CONFIG_DEF = Utils.mergeConfigs(Arrays.asList(
    RemoteLogManagerConfig.configDef(),
    ZkConfigs.CONFIG_DEF,
    ServerConfigs.CONFIG_DEF,
    KRaftConfigs.CONFIG_DEF,
    SocketServerConfigs.CONFIG_DEF,
    ReplicationConfigs.CONFIG_DEF,
    GroupCoordinatorConfig.GROUP_COORDINATOR_CONFIG_DEF,
    CleanerConfig.CONFIG_DEF,
    LogConfig.SERVER_CONFIG_DEF,
    TransactionLogConfigs.CONFIG_DEF,
    QuorumConfig.CONFIG_DEF,
    MetricConfigs.CONFIG_DEF,
    QuotaConfigs.CONFIG_DEF,
    BrokerSecurityConfigs.CONFIG_DEF,
    ...
));
```
Each functional area has its own `CONFIG_DEF` in the `server/` module (e.g., `ServerConfigs.java`, `KRaftConfigs.java`, `ReplicationConfigs.java`).

### KafkaConfig
`core/src/main/scala/kafka/server/KafkaConfig.scala` — the main config class used by all broker components:
- `KafkaConfig.configDef` delegates to `AbstractKafkaConfig.CONFIG_DEF`
- Instantiated via `KafkaConfig.fromProps(props)` at startup
- Provides typed getters for all config values (e.g., `config.numNetworkThreads`, `config.logRetentionMs`)

### Defining a Config Parameter (Pattern from ServerConfigs.java)
Each config module follows this pattern:
```java
// 1. Constants for the config key, default, and doc string
public static final String NUM_IO_THREADS_CONFIG = "num.io.threads";
public static final int NUM_IO_THREADS_DEFAULT = 8;
public static final String NUM_IO_THREADS_DOC = "The number of threads...";

// 2. Register in the ConfigDef
public static final ConfigDef CONFIG_DEF = new ConfigDef()
    .define(NUM_IO_THREADS_CONFIG, INT, NUM_IO_THREADS_DEFAULT, atLeast(1), HIGH, NUM_IO_THREADS_DOC)
    ...
```

### Dynamic Configuration
`core/src/main/scala/kafka/server/DynamicBrokerConfig.scala` manages configs that can be updated at runtime without restart:
```scala
val AllDynamicConfigs = DynamicSecurityConfigs ++
    LogCleaner.ReconfigurableConfigs ++
    DynamicLogConfig.ReconfigurableConfigs ++
    DynamicThreadPool.ReconfigurableConfigs ++
    ...
```
- Components implement the `Reconfigurable` interface and register themselves with `DynamicBrokerConfig`
- Dynamic updates arrive via `AlterConfigs` / `IncrementalAlterConfigs` API requests
- `DynamicConfig.Broker.validate()` validates proposed dynamic config changes before applying them

### Config Validation
- `ConfigDef.parse()` validates types, ranges, and required values at parse time
- `KafkaConfig` constructor calls `AbstractConfig` (parent) which runs the validation
- For dynamic updates, `DynamicBrokerConfig.validateConfigs()` enforces which configs are actually dynamic

---

## 6. Adding a New Broker Config

Here is the step-by-step process to add a new broker configuration parameter, using `num.io.threads` style as a model:

### Step 1 — Choose the right config module
Pick the appropriate class in `server/src/main/java/org/apache/kafka/server/config/` based on the config's domain:
- `ServerConfigs.java` — general broker settings
- `ReplicationConfigs.java` — replication settings
- `KRaftConfigs.java` — KRaft-specific settings
- Or create a new file for a new domain

### Step 2 — Define constants and register in ConfigDef
In the chosen file (e.g., `ServerConfigs.java`):
```java
// Add constants
public static final String MY_NEW_CONFIG = "my.new.config";
public static final int MY_NEW_CONFIG_DEFAULT = 42;
public static final String MY_NEW_CONFIG_DOC = "Description of what this config does.";

// Add to CONFIG_DEF (inside the existing .define() chain)
public static final ConfigDef CONFIG_DEF = new ConfigDef()
    // ... existing entries ...
    .define(MY_NEW_CONFIG, INT, MY_NEW_CONFIG_DEFAULT, atLeast(0), MEDIUM, MY_NEW_CONFIG_DOC);
```

The `AbstractKafkaConfig.CONFIG_DEF` merges all sub-`ConfigDef`s automatically, so it is available to `KafkaConfig`.

### Step 3 — Add a typed getter to KafkaConfig
In `core/src/main/scala/kafka/server/KafkaConfig.scala`, add a getter:
```scala
def myNewConfig: Int = getInt(ServerConfigs.MY_NEW_CONFIG)
```

### Step 4 — Use the config in broker code
Reference `config.myNewConfig` wherever the feature is implemented.

### Step 5 — Support dynamic updates (if needed)
If the config should be changeable without restart:

a) Add the config name to `AllDynamicConfigs` in `DynamicBrokerConfig.scala`:
```scala
val AllDynamicConfigs = ...
    ++ Set(ServerConfigs.MY_NEW_CONFIG)
```

b) Make the consuming component implement `Reconfigurable`:
```scala
class MyComponent extends Reconfigurable {
  override def reconfigurableConfigs(): java.util.Set[String] =
    Set(ServerConfigs.MY_NEW_CONFIG).asJava

  override def reconfigure(configs: java.util.Map[String, _]): Unit = {
    // Apply the new config value
  }
}
```

c) Register the component in `KafkaServer.startup()` or `BrokerServer.startup()`:
```scala
config.dynamicConfig.addReconfigurables(myComponent)
```

### Step 6 — Add validation (if needed)
For cross-field validation (e.g., config A must be less than config B), override `KafkaConfig.validateValues()` in `core/src/main/scala/kafka/server/KafkaConfig.scala` where existing cross-field validation lives.

### Step 7 — Write tests

**Unit test** — verify the config parses correctly and the default is applied:
```scala
// In core/src/test/scala/unit/kafka/server/KafkaConfigTest.scala
@Test
def testMyNewConfig(): Unit = {
  val props = TestUtils.createBrokerConfig(0, "localhost:2181")
  val config = KafkaConfig.fromProps(props)
  assertEquals(42, config.myNewConfig)

  props.put(ServerConfigs.MY_NEW_CONFIG, "100")
  val config2 = KafkaConfig.fromProps(props)
  assertEquals(100, config2.myNewConfig)
}
```

**Dynamic config test** — if dynamic, add a test to `DynamicBrokerReconfigurationTest`:
```scala
// core/src/test/scala/integration/kafka/server/DynamicBrokerReconfigurationTest.scala
@Test
def testMyNewConfigDynamic(): Unit = {
  // Use AdminClient.incrementalAlterConfigs() to change the value
  // Assert the new value is applied without restart
}
```

### Summary of Files to Modify

| Step | File |
|------|------|
| Define constant + register in ConfigDef | `server/src/main/java/org/apache/kafka/server/config/ServerConfigs.java` (or domain-specific file) |
| Add typed getter | `core/src/main/scala/kafka/server/KafkaConfig.scala` |
| Enable dynamic updates | `core/src/main/scala/kafka/server/DynamicBrokerConfig.scala` |
| Add cross-field validation | `core/src/main/scala/kafka/server/KafkaConfig.scala` (`validateValues`) |
| Unit test | `core/src/test/scala/unit/kafka/server/KafkaConfigTest.scala` |
| Dynamic reconfiguration test | `core/src/test/scala/integration/kafka/server/DynamicBrokerReconfigurationTest.scala` |
