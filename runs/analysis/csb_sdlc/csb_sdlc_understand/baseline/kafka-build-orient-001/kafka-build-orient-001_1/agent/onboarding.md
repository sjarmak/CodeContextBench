# Apache Kafka Codebase Orientation

## 1. Build System and Broker Startup

### Build System
Kafka uses **Gradle** as its build system. Key build files:
- **Root:** `/workspace/build.gradle` - Main build configuration
- **Gradle wrapper:** `/workspace/gradle/wrapper/` - Gradle wrapper scripts
- **Settings:** `/workspace/settings.gradle` - Project structure definition

Key build commands:
```bash
./gradlew jar                 # Build broker JAR
./gradlew test               # Run unit and integration tests
./gradlew unitTest           # Run unit tests only
./gradlew integrationTest    # Run integration tests only
```

### Broker Startup Entry Point
**Main Entry Point:** `/workspace/core/src/main/scala/kafka/Kafka.scala`

The broker is started via:
1. **Shell Script:** `/workspace/bin/kafka-server-start.sh`
2. **Main Class:** `kafka.Kafka` (object extending Logging)
3. **Method:** `main(args: Array[String]): Unit` (line 87)

### Broker Startup Flow

```
kafka-server-start.sh
    ↓
kafka-run-class.sh kafka.Kafka <properties-file> [--override property=value]*
    ↓
kafka.Kafka.main(args)
    ├─ getPropsFromArgs(args) - Load server.properties and overrides
    ├─ buildServer(serverProps) - Create broker instance
    │   ├─ KafkaConfig.fromProps(props, doLog=false) - Parse configuration
    │   ├─ Check config.requiresZookeeper (Zk mode vs KRaft mode)
    │   ├─ If Zk mode: new KafkaServer(config, Time.SYSTEM, threadNamePrefix=None, ...)
    │   └─ If KRaft mode: new KafkaRaftServer(config, Time.SYSTEM)
    ├─ LoggingSignalHandler.register() - Install signal handlers
    ├─ Exit.addShutdownHook() - Register graceful shutdown
    ├─ server.startup() - Start the server
    └─ server.awaitShutdown() - Block until shutdown
```

### Key Classes Involved in Broker Initialization

#### 1. **KafkaConfig** (Configuration Facade)
- **File:** `/workspace/core/src/main/scala/kafka/server/KafkaConfig.scala`
- **Extends:** `AbstractKafkaConfig` from `/workspace/server/src/main/java/org/apache/kafka/server/config/AbstractKafkaConfig.java`
- **Responsibility:** Parse and validate all broker configuration parameters
- **Key Method:** `fromProps(props: Properties, doLog: Boolean): KafkaConfig`
- **ConfigDef:** Line 91 - Aggregates all configuration definitions from multiple modules

#### 2. **KafkaServer** (ZooKeeper-based Broker)
- **File:** `/workspace/core/src/main/scala/kafka/server/KafkaServer.scala`
- **Traits:** Implements `Server` interface
- **Key Initialization Steps (startup() method):**
  1. Initialize broker metadata (broker ID, endpoints, etc.)
  2. Connect to ZooKeeper
  3. Create and start RequestChannel for handling client requests
  4. Initialize SocketServer (network listeners)
  5. Create KafkaController instance
  6. Create GroupCoordinator and TransactionCoordinator
  7. Initialize LogManager (manages on-disk partition logs)
  8. Register with ZooKeeper and wait for controller election
  9. Start metadata cache synchronization
  10. Start log recovery and data plane
  11. Advertise broker endpoints to clients

#### 3. **KafkaRaftServer** (KRaft/Controller Mode Broker)
- **File:** `/workspace/core/src/main/scala/kafka/server/KafkaRaftServer.scala`
- **Alternative to KafkaServer** for KRaft consensus mode
- **Purpose:** Simplified broker for KRaft clusters (no separate controller)
- **Key Feature:** Eliminates ZooKeeper dependency

#### 4. **LogManager** (Partition Log Management)
- **File:** `/workspace/core/src/main/scala/kafka/log/LogManager.scala`
- **Key Responsibility:** Create, manage, and recover partition logs on disk
- **Initialization:**
  - Scans configured log directories
  - Recovers unflushed messages
  - Initializes cleaner thread for log compaction
  - Creates LogDirFailureChannel for monitoring

#### 5. **SocketServer** (Network Handler)
- **File:** `/workspace/core/src/main/scala/kafka/network/SocketServer.scala`
- **Responsibility:** Accept client connections and route requests
- **Components:**
  - ControlPlaneAcceptor - For broker-to-broker and admin requests
  - DataPlaneAcceptor - For producer/consumer requests
  - RequestChannel - Queues requests for processing

#### 6. **RequestChannel & KafkaApis** (Request Processing)
- **RequestChannel:** `/workspace/core/src/main/scala/kafka/network/RequestChannel.scala` - Queues requests
- **KafkaApis:** `/workspace/core/src/main/scala/kafka/server/KafkaApis.scala` - Routes and handles protocol requests
- **Architecture:** Thread-based processing with separate I/O and handler threads

---

## 2. Module Structure

Kafka is organized into multiple interdependent modules:

### Core Modules

#### **core** - Main Broker Implementation
- **Location:** `/workspace/core/`
- **Language:** Scala + Java
- **Responsibility:** Broker startup, request handling, coordination
- **Key Packages:**
  - `kafka.server.*` - Server/broker logic
  - `kafka.network.*` - Network and socket handling
  - `kafka.log.*` - Log and partition management
  - `kafka.controller.*` - Cluster controller (ZK mode only)
  - `kafka.admin.*` - Admin operations
  - `kafka.cluster.*` - Broker and replica metadata
  - `kafka.coordinator.*` - Group and transaction coordinators
  - `kafka.zk.*` - ZooKeeper interaction

#### **clients** - Client Libraries
- **Location:** `/workspace/clients/`
- **Language:** Java
- **Responsibility:** Producer and Consumer implementations
- **Exports:** Client JAR consumed by applications
- **Key Classes:** ProducerImpl, NetworkClient, MetadataUpdater

#### **server** - Server Configuration and Utilities
- **Location:** `/workspace/server/`
- **Language:** Java
- **Responsibility:** Server-side configuration definitions and common server code
- **Key Classes:**
  - `ServerConfigs` - Broker config definitions
  - `AbstractKafkaConfig` - Configuration merging logic
  - `NodeToControllerChannelManager` - Broker-to-controller communication

#### **server-common** - Shared Server Code
- **Location:** `/workspace/server-common/`
- **Language:** Java
- **Responsibility:** Shared code between broker and controller
- **Key Classes:**
  - `ServerLogConfigs` - Log configuration definitions
  - `MetadataVersion` - Supported protocol versions

#### **metadata** - Metadata Management (KRaft)
- **Location:** `/workspace/metadata/`
- **Language:** Java
- **Responsibility:** Metadata log, metadata image, and state machine for KRaft clusters
- **Key Classes:** MetadataRecordSerde, MetadataImage, MetadataLog

#### **raft** - Raft Consensus Implementation
- **Location:** `/workspace/raft/`
- **Language:** Java
- **Responsibility:** Raft protocol implementation for KRaft consensus
- **Alternative to:** ZooKeeper for cluster coordination

#### **storage** - Log Storage and Persistence
- **Location:** `/workspace/storage/`
- **Language:** Java
- **Responsibility:** Low-level log file management, index, and segment handling
- **Key Classes:** Log, LogSegment, OffsetIndex, TimeIndex

#### **group-coordinator** - Group Coordination
- **Location:** `/workspace/group-coordinator/`
- **Language:** Java
- **Responsibility:** Consumer group coordination (extracted from core)
- **Replaces:** Legacy GroupCoordinator implementation

#### **transaction-coordinator** - Transaction Coordination
- **Location:** `/workspace/transaction-coordinator/`
- **Language:** Java
- **Responsibility:** Transactional guarantee implementation
- **Manages:** Producer ID allocation, transaction state

### Supporting Modules

#### **connect** - Kafka Connect Framework
- Location: `/workspace/connect/`
- Integration platform for external systems
- Includes source and sink connectors

#### **streams** - Kafka Streams Library
- Location: `/workspace/streams/`
- Stream processing framework

#### **tools** - Administrative and Diagnostic Tools
- Location: `/workspace/tools/`
- Includes: Topic management, ACLs, configs, performance testing

#### **tests** - Test Utilities and Fixtures
- Location: `/workspace/tests/`
- Shared test frameworks
- Key Class: `IntegrationTestHarness`

#### **config** - Default Configuration Files
- Location: `/workspace/config/`
- Contains: `server.properties`, `log4j.properties`, etc.

### Dependency Graph (Simplified)
```
Applications
    ↓
clients (Producer/Consumer APIs)
    ↓
server-common (Shared server utilities)
    ↓
core (Broker Implementation)
    ├─ Depends on: storage, raft, metadata, group-coordinator, transaction-coordinator
    ├─ For ZK mode: Uses kafka.zk.* for ZooKeeper
    └─ For KRaft mode: Uses raft/* and metadata/* for consensus
    ↓
storage (Log file I/O)
```

---

## 3. Topic Creation Flow

### End-to-End Topic Creation Process

Topic creation involves three layers:
1. **API Layer (KafkaApis)** - Protocol handling
2. **Admin Layer (ZkAdminManager)** - Business logic and validation
3. **Storage Layer (LogManager)** - Physical log creation

### Detailed Flow

#### Step 1: Client Sends CreateTopicsRequest
Client calls `AdminClient.createTopics()` which sends `CreateTopicsRequest` protocol request to broker.

#### Step 2: Request Arrives at KafkaApis
- **File:** `/workspace/core/src/main/scala/kafka/server/KafkaApis.scala`
- **Method:** `handleCreateTopicsRequest(request: RequestChannel.Request): Unit` (line 2002)
- **Handler Logic:**
  ```scala
  case ApiKeys.CREATE_TOPICS =>
    maybeForwardToController(request, handleCreateTopicsRequest)
  ```
- **Validation:**
  - Extracts CreateTopicsRequest body
  - Authorizes requesting principal (authorizationManager.authorize)
  - Checks if controller is available
  - Filters out unauthorized topics

#### Step 3: Forward to Controller (ZK mode)
- In ZK mode, CreateTopics request is forwarded to active controller
- Controller is elected and runs `KafkaController` instance
- Request is sent via `ControllerRequestForwarding` mechanism

#### Step 4: Admin Logic (ZkAdminManager)
- **File:** `/workspace/core/src/main/scala/kafka/server/ZkAdminManager.scala`
- **Method:** `createTopics(...)` (line 159-258)

**4a. Resolve Topic Parameters:**
```scala
// If user didn't specify numPartitions/replicationFactor, use broker defaults
if (topic.numPartitions == null)
  topic.numPartitions = config.numPartitions
if (topic.replicationFactor == null)
  topic.replicationFactor = config.defaultReplicationFactor

// If user provided explicit assignments, use those instead
val assignments = if (topic.assignments.isEmpty)
  AdminUtils.assignReplicasToBrokers(topic.numPartitions, topic.replicationFactor, ...)
else
  topic.assignments
```

**4b. Validate Topic Configuration:**
```scala
// Check topic doesn't already exist
if (topicsToCreate.contains(topicName)) throw TopicExistsException

// Check partition count and replication factor
if (topic.numPartitions <= 0) throw InvalidPartitionsException
if (topic.replicationFactor <= 0) throw InvalidReplicationFactorException

// Check assigned replicas are valid
validateTopicCreatePolicy(topic) // Applies topic creation policy plugins
```

**4c. Apply Topic Creation Policy (if configured):**
- **Config:** `create.topic.policy.class.name`
- **Interface:** `org.apache.kafka.server.policy.CreateTopicPolicy`
- **Purpose:** Custom validation rules (min replicas, allowed partition counts, etc.)
- **Exception:** `PolicyViolationException` if policy rejects

**4d. Create in ZooKeeper (or Metadata Log in KRaft):**
```scala
// For ZK mode:
adminZkClient.createTopicWithAssignment(
  topic = topicName,
  partitionReplicaAssignment = assignments,
  topicConfig = topic.configs
)

// This creates two ZK entries:
// 1. /brokers/topics/{topic-name} - Replica assignments
// 2. /config/topics/{topic-name} - Topic configuration
```

**4e. Wait for Partitions to be Created:**
```scala
if (timeout > 0) {
  // Create DelayedCreatePartitions operation
  // Wait for all brokers to create their assigned partitions
  // Timeout after specified duration
}
```

**4f. Return Response:**
```scala
CreateTopicsResponse with:
  - TopicErrorCode for each topic (OK, EXISTS, INVALID_CONFIG, etc.)
  - ErrorMessage with details if failed
```

### Step 5: Brokers React to ZK Changes (ZK mode)
- **Watcher:** `/workspace/core/src/main/scala/kafka/server/KafkaController.scala`
- **Trigger:** ZK path `/brokers/topics/` is watched
- Controller detects new topic entry
- Triggers replica assignment and leader election
- Broadcasts LeaderAndIsrRequest to all brokers

### Step 6: Broker Creates Partition Logs
- **File:** `/workspace/core/src/main/scala/kafka/log/LogManager.scala`
- **Trigger:** LeaderAndIsrRequest from controller
- **Method:** `getOrCreateLog(topicPartition: TopicPartition, ...): UnifiedLog`

**6a. Determine Log Directory:**
```scala
// For each TopicPartition, determine where to store logs on disk
val assignedDirs = logDirsByLogDirId.get(targetLogDirId)
if (assignedDirs is preferred log dir) {
  use preferred log dir
} else {
  select log dir with fewest partitions (load balance)
}
```

**6b. Create Partition Directory:**
```scala
// Creates directory structure:
// {log.dir}/{topic}-{partition}/
// Example: /var/kafka-logs/my-topic-0/

val logPath = Paths.get(logDir, s"${topicPartition.topic}-${topicPartition.partition}")
Files.createDirectories(logPath)
```

**6c. Create UnifiedLog Instance:**
```scala
val log = UnifiedLog(
  dir = logPath,
  config = LogConfig(topicConfig), // Topic-specific config
  recoveryPoint = lastOffsetCheckpoint,
  scheduler = logCleanerScheduler,
  time = Time.SYSTEM,
  ...
)

// UnifiedLog initialization creates:
// - {logPath}/00000000000000000000.log (first segment)
// - {logPath}/00000000000000000000.index (offset index)
// - {logPath}/00000000000000000000.timeindex (timestamp index)
// - {logPath}/producer-state-snapshot (for transactional support)
```

**6d. Register Log:**
```scala
// Store in LogManager's in-memory cache
currentLogs.put(topicPartition, log)

// Also maintain TopicId mapping
topicIds.put(topicId, topicPartition)
```

### Error Scenarios and Exceptions

| Error | Exception Class | When Thrown | Handling |
|-------|-----------------|-------------|----------|
| Topic already exists | `TopicExistsException` | In ZkAdminManager.createTopics() | Return error in response |
| Invalid partition count | `InvalidPartitionsException` | partition count <= 0 | Validate before ZK creation |
| Invalid replication | `InvalidReplicationFactorException` | replication <= 0 or > brokers | Validate before ZK creation |
| Invalid topic name | `InvalidTopicException` | Topic name doesn't match regex | Check in KafkaApis |
| Policy violation | `PolicyViolationException` | Custom policy rejects | Throw if policy plugin fails |
| Log directory full | `IOException` | Can't create partition dir | Retry on different dir |
| ZK connection failed | `ZooKeeperClientException` | ZK unavailable | Bubble up to client |

### Key Configuration Parameters

| Parameter | Default | Meaning |
|-----------|---------|---------|
| `num.partitions` | 1 | Default partition count if not specified |
| `default.replication.factor` | 1 | Default replication if not specified |
| `create.topic.policy.class.name` | "" | Custom validation plugin |
| `log.dirs` | /tmp/kafka-logs | Where partition logs are stored |
| `auto.create.topics.enable` | true | Auto-create on first write |
| `min.insync.replicas` | 1 | Min replicas for acks=all |

### Key Classes and Files

| Component | File | Key Method |
|-----------|------|-----------|
| API Handler | `/workspace/core/src/main/scala/kafka/server/KafkaApis.scala` | handleCreateTopicsRequest() |
| Admin Logic | `/workspace/core/src/main/scala/kafka/server/ZkAdminManager.scala` | createTopics() |
| Log Manager | `/workspace/core/src/main/scala/kafka/log/LogManager.scala` | getOrCreateLog() |
| Controller | `/workspace/core/src/main/scala/kafka/server/KafkaController.scala` | onNewTopicCreation() |
| Broker Client | `/workspace/core/src/main/scala/kafka/network/SocketServer.scala` | sendRequest() |

---

## 4. Testing Framework

### Testing Frameworks and Patterns

Kafka uses **JUnit 5** (Jupiter) with **Scala and Java** implementations.

#### Testing Dependencies
- **JUnit:** Jupiter (JUnit 5) for test execution
- **Mocking:** Mockito for mocking dependencies
- **Assertions:** JUnit assertions + custom helpers
- **Utilities:** `kafka.utils.TestUtils` for test fixtures
- **Test Harness:** `KafkaServerTestHarness` for integration tests

### Unit Tests

**Framework:** JUnit 5 with Scala test classes

**Example Test Structure:**
```scala
// File: /workspace/core/src/test/scala/unit/kafka/log/LogManagerTest.scala
class LogManagerTest {
  val time = new MockTime()
  var logDir: File = _
  var logManager: LogManager = _

  @BeforeEach
  def setUp(): Unit = {
    logDir = TestUtils.tempDir()
    logManager = createLogManager()
  }

  @AfterEach
  def tearDown(): Unit = {
    logManager.shutdown()
    Utils.delete(logDir)
  }

  @Test
  def testCreateLog(): Unit = {
    val topicPartition = new TopicPartition("test", 0)
    val log = logManager.getOrCreateLog(topicPartition, ...)

    assertEquals(topicPartition, log.topicPartition)
    assertTrue(logDir.exists())
  }
}
```

**Key Patterns:**
1. **@BeforeEach / @AfterEach** - Setup and teardown per test
2. **TestUtils.tempDir()** - Create temporary directories
3. **Mockito.mock()** - Create mock objects
4. **ArgumentCaptor** - Capture method arguments
5. **Time.MOCK_TIME** - Controlled time progression

**Example Unit Test Files:**
- `/workspace/core/src/test/scala/unit/kafka/log/LogManagerTest.scala`
- `/workspace/core/src/test/scala/unit/kafka/server/KafkaServerTest.scala`
- `/workspace/core/src/test/scala/unit/kafka/server/DynamicBrokerConfigTest.scala`

### Integration Tests

**Framework:** JUnit 5 with cluster setup

**Test Harness:** `KafkaServerTestHarness`
- **File:** `/workspace/core/src/test/scala/unit/kafka/integration/KafkaServerTestHarness.scala`
- **Purpose:** Start multiple brokers and ZooKeeper for integration tests
- **Provides:** `brokers`, `zkUtils`, `AdminClient` for testing

**Example Integration Test:**
```scala
// File: /workspace/core/src/test/scala/integration/kafka/api/BaseAdminIntegrationTest.scala
class MyIntegrationTest extends KafkaServerTestHarness {

  override def brokerCount: Int = 3
  override def serverProperties(): Properties = {
    val props = new Properties()
    props.put("auto.create.topics.enable", "false")
    props
  }

  @Test
  def testTopicCreation(): Unit = {
    val admin = AdminClientUtils.createAdminClient(brokers)

    admin.createTopics(
      Arrays.asList(new NewTopic("test", 1, 1.toShort))
    ).all().get(10, TimeUnit.SECONDS)

    val metadata = admin.describeTopics(Arrays.asList("test"))
      .allTopicNames().get()

    assertEquals(1, metadata.get("test").partitions().size())
  }
}
```

**Integration Test Files:**
- `/workspace/core/src/test/scala/integration/kafka/api/BaseAdminIntegrationTest.scala`
- `/workspace/core/src/test/scala/integration/kafka/api/CreateTopicsRequestTest.scala`
- `/workspace/core/src/test/scala/integration/kafka/api/ConsumerTopicCreationTest.scala`

### Parameterized Tests

**Pattern:** Test same logic with multiple configurations

```scala
@ParameterizedTest
@MethodSource("testCases")
def testWithParams(zkMode: Boolean): Unit = {
  // Setup broker in ZK or KRaft mode based on parameter
  // Run test
}

companion object {
  @Parameters(name = "zkMode={0}")
  def data(): Stream[Arguments] = Stream(
    arguments(true),   // ZK mode
    arguments(false)   // KRaft mode
  )
}
```

### Topic Creation Tests

**Location:** `/workspace/core/src/test/scala/unit/kafka/server/AbstractCreateTopicsRequestTest.scala`

**Base Test Class:** `AbstractCreateTopicsRequestTest`
- Provides: `sendCreateTopicsRequest()`, `validateTopicCreation()` helpers
- Runs against both ZK and KRaft brokers

**Concrete Test Classes:**
1. `CreateTopicsRequestTest` - Valid topic creation
2. `CreateTopicsRequestWithPolicyTest` - Policy enforcement
3. `InvalidTopicsTest` - Error handling

**Test Patterns:**
```scala
@Test
def testValidTopicCreation(): Unit = {
  // Send CreateTopicsRequest
  val result = sendCreateTopicsRequest(
    topicReq("test-topic",
      numPartitions = 3,
      replicationFactor = 2)
  )

  // Validate no errors
  assertEquals(Errors.NONE, result.errors.get("test-topic"))

  // Verify metadata reflects creation
  val metadata = admin.describeTopics(Arrays.asList("test-topic"))
  assertEquals(3, metadata.partitions.size())
}

@Test
def testTopicAlreadyExists(): Unit = {
  // Create topic
  sendCreateTopicsRequest(topicReq("test-topic", 1, 1))

  // Try to create again
  val result = sendCreateTopicsRequest(topicReq("test-topic", 1, 1))

  // Should get error
  assertEquals(Errors.TOPIC_ALREADY_EXISTS, result.errors.get("test-topic"))
}

@Test
def testInvalidPartitionCount(): Unit = {
  val result = sendCreateTopicsRequest(
    topicReq("test-topic",
      numPartitions = 0,  // Invalid!
      replicationFactor = 1)
  )

  assertEquals(Errors.INVALID_PARTITIONS, result.errors.get("test-topic"))
}
```

### Test Utilities

**File:** `/workspace/core/src/test/scala/kafka/utils/TestUtils.scala`

**Key Methods:**
```scala
// File system
TestUtils.tempDir()                          // Create temp directory
TestUtils.tempFile()                         // Create temp file
TestUtils.delete(file)                       // Delete recursively

// Server setup
TestUtils.brokerListStrFromServers(servers)  // Format broker list
TestUtils.createNewProperties()               // Default config properties

// Network
TestUtils.findFreePort()                      // Find unused port
TestUtils.getLocalHost()                      // Get localhost IP

// Time
new MockTime()                                 // Controllable time
time.sleep(ms)                                 // Advance time
time.setCurrentTimeMs(ms)                      // Set time
```

### Running Tests

```bash
# Run all tests
./gradlew test

# Run specific module
./gradlew core:test

# Run specific test class
./gradlew core:test --tests LogManagerTest

# Run specific test method
./gradlew core:test --tests LogManagerTest.testCreateLog

# Run integration tests only
./gradlew integrationTest

# Run unit tests only
./gradlew unitTest

# Continuously run a test
I=0; while ./gradlew core:test --tests LogManagerTest --rerun --fail-fast; do (( I=$I+1 )); echo "Completed run: $I"; sleep 1; done
```

---

## 5. Configuration System

### Configuration Architecture

Kafka's configuration system is hierarchical and supports both static and dynamic configurations:

```
ConfigDef (Configuration Schema)
    ↓
AbstractKafkaConfig (Aggregates all ConfigDefs)
    ↓
KafkaConfig (Broker configuration wrapper)
    ↓
DynamicBrokerConfig (Dynamic update handler)
```

### Configuration Definition Files

Configuration is defined in multiple Java files in the `org.apache.kafka.server.config` package:

| File | Purpose | Located In |
|------|---------|-----------|
| `ServerConfigs` | General broker config | `/workspace/server/src/main/java/` |
| `ServerLogConfigs` | Log and topic config | `/workspace/server-common/src/main/java/` |
| `KRaftConfigs` | KRaft-specific config | `/workspace/metadata/src/main/java/` |
| `ZkConfigs` | ZooKeeper config | `/workspace/core/src/main/scala/kafka/server/` |
| `SocketServerConfigs` | Network listener config | `/workspace/core/src/main/scala/kafka/network/` |
| `ReplicationConfigs` | Replication settings | `/workspace/server/src/main/java/` |
| `TransactionLogConfigs` | Transaction settings | `/workspace/transaction-coordinator/` |
| `GroupCoordinatorConfig` | Group coordination | `/workspace/group-coordinator/` |

### ServerConfigs Configuration Parameters

**File:** `/workspace/server/src/main/java/org/apache/kafka/server/config/ServerConfigs.java`

**Key Broker Configuration Parameters:**

```java
// Broker Identity
public static final String BROKER_ID_CONFIG = "broker.id";
public static final int BROKER_ID_DEFAULT = -1;
public static final String BROKER_ID_DOC = "The broker id for this server...";

// Request Processing
public static final String NUM_IO_THREADS_CONFIG = "num.io.threads";
public static final int NUM_IO_THREADS_DEFAULT = 8;

public static final String BACKGROUND_THREADS_CONFIG = "background.threads";
public static final int BACKGROUND_THREADS_DEFAULT = 10;

// Broker Behavior
public static final String DELETE_TOPIC_ENABLE_CONFIG = "delete.topic.enable";
public static final boolean DELETE_TOPIC_ENABLE_DEFAULT = true;

public static final String COMPRESSION_TYPE_CONFIG = "compression.type";
public static final String COMPRESSION_TYPE_DOC = "Specify the final compression...";

// Timeouts
public static final String REQUEST_TIMEOUT_MS_CONFIG = "request.timeout.ms";
public static final int REQUEST_TIMEOUT_MS_DEFAULT = 30000;

// Rack Awareness
public static final String BROKER_RACK_CONFIG = "broker.rack";
```

**Configuration Definition Pattern:**
```java
public static final ConfigDef CONFIG_DEF = new ConfigDef()
    .define(BROKER_ID_CONFIG, INT, BROKER_ID_DEFAULT, HIGH, BROKER_ID_DOC)
    .define(MESSAGE_MAX_BYTES_CONFIG, INT, LogConfig.DEFAULT_MAX_MESSAGE_BYTES,
            atLeast(0), HIGH, MESSAGE_MAX_BYTES_DOC)
    .define(COMPRESSION_TYPE_CONFIG, STRING, LogConfig.DEFAULT_COMPRESSION_TYPE,
            ConfigDef.ValidString.in(BrokerCompressionType.names()),
            HIGH, COMPRESSION_TYPE_DOC)
    ...;
```

### ServerLogConfigs Configuration Parameters

**File:** `/workspace/server-common/src/main/java/org/apache/kafka/server/config/ServerLogConfigs.java`

**Key Log/Topic Configuration Parameters:**

```java
// Default Topic Settings
public static final String NUM_PARTITIONS_CONFIG = "num.partitions";
public static final int NUM_PARTITIONS_DEFAULT = 1;

// Log Directories
public static final String LOG_DIRS_CONFIG = "log.dirs";
public static final String LOG_DIR_CONFIG = "log.dir";
public static final String LOG_DIR_DEFAULT = "/tmp/kafka-logs";

// Log Segments
public static final String LOG_SEGMENT_BYTES_CONFIG = "log.segment.bytes";
public static final String LOG_ROLL_TIME_MILLIS_CONFIG = "log.roll.ms";

// Retention
public static final String LOG_RETENTION_TIME_MILLIS_CONFIG = "log.retention.ms";
public static final String LOG_RETENTION_BYTES_CONFIG = "log.retention.bytes";
public static final long LOG_RETENTION_BYTES_DEFAULT = -1L;

// Cleanup
public static final String LOG_CLEANUP_POLICY_CONFIG = "log.cleanup.policy";
public static final String LOG_CLEANUP_INTERVAL_MS_CONFIG = "log.retention.check.interval.ms";

// Topic Creation Policy
public static final String CREATE_TOPIC_POLICY_CLASS_NAME_CONFIG =
    "create.topic.policy.class.name";
```

### Configuration Loading and Merging

**File:** `/workspace/server/src/main/java/org/apache/kafka/server/config/AbstractKafkaConfig.java`

**Merging Order (Priority - highest to lowest):**
```
1. System Properties / JVM arguments
2. Command line overrides (--override property=value)
3. server.properties file
4. ConfigDef defaults
```

**Process:**
```java
// In AbstractKafkaConfig.CONFIG_DEF
public static final ConfigDef CONFIG_DEF = new ConfigDef()
    .define(...) // ServerConfigs
    .define(...) // ServerLogConfigs
    .define(...) // ReplicationConfigs
    .define(...) // SocketServerConfigs
    .define(...) // other component configs
    ...;

// In KafkaConfig.fromProps()
new KafkaConfig(AbstractConfig config)
```

### Dynamic Configuration Updates

**File:** `/workspace/core/src/main/scala/kafka/server/DynamicBrokerConfig.scala`

**Dynamic vs Static Configurations:**

```scala
// Line 88-100: Which configs can be dynamically updated
val AllDynamicConfigs = DynamicSecurityConfigs ++
    LogCleaner.ReconfigurableConfigs ++
    DynamicLogConfig.ReconfigurableConfigs ++
    DynamicThreadPool.ReconfigurableConfigs ++
    DynamicListenerConfig.ReconfigurableConfigs ++
    ...
```

**Configuration Precedence (for dynamic configs):**
```
1. DYNAMIC_BROKER_CONFIG      (per-broker, in ZK /configs/brokers/{brokerId})
2. DYNAMIC_DEFAULT_CONFIG     (cluster-wide, in ZK /configs/brokers/<default>)
3. STATIC_BROKER_CONFIG       (server.properties)
4. DEFAULT_CONFIG             (KafkaConfig defaults)
```

**Dynamic Update Mechanism:**
```scala
// When config changes in ZK:
// 1. ZKConfigHandler watches /configs/brokers/{brokerId}
// 2. Calls DynamicBrokerConfig.updateBrokerConfig()
// 3. For each changed config that is Reconfigurable:
//    - Call component.reconfigure(newConfigs)
//    - Component applies new config immediately (if it supports it)
```

**Reconfigurable Components (Interfaces):**
```
org.apache.kafka.common.Reconfigurable
    ├─ LogCleaner - Log compaction settings
    ├─ SocketServer - Listener configurations
    ├─ KafkaMetricsReporter - Metrics settings
    ├─ LoginManager - SASL/SSL settings
    ├─ Authorizer - Authorization policies
    └─ Other...
```

### Configuration Validation

**Process:**
```
1. Parse properties from server.properties
2. Apply command-line overrides
3. For each config key:
   a. Look up ConfigKey from ConfigDef
   b. Get validator (if any)
   c. Call validator.validate(value)
   d. If validation fails, throw ConfigException
4. Create KafkaConfig instance with validated values
```

**Example Validator:**
```java
// In ServerConfigs
.define(FETCH_MAX_BYTES_CONFIG, INT, FETCH_MAX_BYTES_DEFAULT,
        atLeast(1024), MEDIUM, FETCH_MAX_BYTES_DOC)
        //        ^^^^^^^^^^^^^^
        // Validator ensures value >= 1024
```

### Accessing Configuration in Code

**From KafkaConfig:**
```scala
val config = KafkaConfig.fromProps(properties)

// Access broker configs
val brokerId = config.brokerId
val numIoThreads = config.numIoThreads
val logDirs = config.logDirs

// Access log/topic configs
val numPartitions = config.numPartitions
val retentionMs = config.logRetentionTimeMillis
```

**From DynamicBrokerConfig:**
```scala
val dynamicConfig = new DynamicBrokerConfig(staticConfig)

// Get config (may be from ZK if dynamically updated)
val value = dynamicConfig.currentDynamicBrokerConfigs.get(propertyName)
```

---

## 6. Adding a New Broker Configuration Parameter

This guide explains how to add a new broker configuration parameter end-to-end.

### Example: Adding a New Parameter `broker.message.retention.ms`

### Step 1: Define Configuration in ConfigDef

**File:** Choose appropriate location based on config type:
- **General broker config:** `/workspace/server/src/main/java/org/apache/kafka/server/config/ServerConfigs.java`
- **Log/topic config:** `/workspace/server-common/src/main/java/org/apache/kafka/server/config/ServerLogConfigs.java`
- **Security config:** `/workspace/core/src/main/scala/kafka/server/KafkaConfig.scala`

**For our example (general broker config):**

```java
// In ServerConfigs.java, add constant definitions (around line 40-100):

public static final String BROKER_MESSAGE_RETENTION_MS_CONFIG = "broker.message.retention.ms";
public static final long BROKER_MESSAGE_RETENTION_MS_DEFAULT = -1L; // -1 = no limit
public static final String BROKER_MESSAGE_RETENTION_MS_DOC =
    "The default message retention time (in milliseconds) for all topics on this broker. " +
    "Topic-specific retention.ms config takes precedence. -1 means no limit.";

// In the CONFIG_DEF (around line 141):
public static final ConfigDef CONFIG_DEF = new ConfigDef()
    // ... existing configs ...
    .define(
        BROKER_MESSAGE_RETENTION_MS_CONFIG,
        LONG,
        BROKER_MESSAGE_RETENTION_MS_DEFAULT,
        atLeast(-1),  // Validator: must be >= -1
        MEDIUM,       // Importance level
        BROKER_MESSAGE_RETENTION_MS_DOC
    )
    // ... more configs ...
```

**ConfigDef.define() Parameters Explained:**
```java
.define(
    String configName,              // Key used in server.properties
    ConfigDef.Type type,           // Data type (INT, LONG, STRING, BOOLEAN, DOUBLE, LIST)
    Object defaultValue,           // Default value
    ConfigDef.Validator validator, // Optional: validation rule (atLeast, ValidString, etc.)
    ConfigDef.Importance importance, // LOW, MEDIUM, or HIGH (for documentation)
    String documentation           // Help text
)
```

### Step 2: Add Accessor Property to KafkaConfig

**File:** `/workspace/core/src/main/scala/kafka/server/KafkaConfig.scala`

**Pattern:**
```scala
// Add near other property definitions (after line 100)
val brokerMessageRetentionMs = getLong(ServerConfigs.BROKER_MESSAGE_RETENTION_MS_CONFIG)

// For topic-level config synonyms, add mapping:
// (Not needed for this broker-only config)
```

**Accessor Pattern (Scala):**
```scala
// For simple types
val someIntValue: Int = getInt(ConfigName)
val someLongValue: Long = getLong(ConfigName)
val someBoolValue: Boolean = getBoolean(ConfigName)
val someStringValue: String = getString(ConfigName)

// For complex types
val someList: List[String] = getList(ConfigName)
val someMap: Map[String, String] = getMap(ConfigName)
```

### Step 3: Mark as Dynamic if Applicable

If you want the parameter to be dynamically updatable without broker restart:

**File:** `/workspace/core/src/main/scala/kafka/server/DynamicBrokerConfig.scala`

**Add to Dynamic Configs (around line 92-100):**
```scala
object DynamicBrokerConfig {
  val AllDynamicConfigs = DynamicSecurityConfigs ++
    LogCleaner.ReconfigurableConfigs ++
    DynamicLogConfig.ReconfigurableConfigs ++
    DynamicThreadPool.ReconfigurableConfigs ++
    // ... existing ...
    Set(
      ServerConfigs.BROKER_MESSAGE_RETENTION_MS_CONFIG  // Add here
    ) ++
    // ... more ...
```

**Implement Reconfigurable Component:**

If your config affects a component, make that component implement `Reconfigurable`:

```scala
// In the component that uses the config (e.g., LogManager)
class LogManager(...) extends Reconfigurable {

  @volatile var brokerMessageRetentionMs = config.brokerMessageRetentionMs

  override def reconfigure(configs: Map[String, _]): Unit = {
    val updated = new KafkaConfig(configs, false)
    brokerMessageRetentionMs = updated.brokerMessageRetentionMs
    // Apply any necessary updates (e.g., update retention checker task)
  }

  override def validateReconfiguration(configs: Map[String, _]): Unit = {
    val updated = new KafkaConfig(configs, false)
    // Validate the new config value
    if (updated.brokerMessageRetentionMs < -1) {
      throw new ConfigException("must be >= -1")
    }
  }
}
```

### Step 4: Update Validation (if needed)

**Validation Happens In:**

1. **ConfigDef validator** (as shown in Step 1)
   ```java
   .define(CONFIG, LONG, DEFAULT, atLeast(-1), ...)
   ```

2. **Custom validation in KafkaConfig**:
   ```scala
   // In KafkaConfig.validateValues()
   if (brokerMessageRetentionMs < -1) {
     throw new ConfigException(
       ServerConfigs.BROKER_MESSAGE_RETENTION_MS_CONFIG,
       brokerMessageRetentionMs,
       "must be >= -1"
     )
   }
   ```

3. **Component-specific validation** (in reconfigure method)
   - Called when config is dynamically updated
   - Should validate interaction with other configs

### Step 5: Use Configuration in Broker Code

**Example: Using in LogManager**

```scala
// In LogManager or appropriate component
class LogManager(config: KafkaConfig, ...) {

  private var brokerMessageRetentionMs = config.brokerMessageRetentionMs

  def getOrCreateLog(topicPartition: TopicPartition, ...): UnifiedLog = {
    val logConfig = LogConfig(topicConfigs)

    // Override with broker-wide setting if topic doesn't specify
    val retentionMs =
      if (logConfig.retentionMs != -1L && logConfig.retentionMs < brokerMessageRetentionMs)
        logConfig.retentionMs
      else
        brokerMessageRetentionMs

    // Use retentionMs in log configuration...
  }
}
```

### Step 6: Update Documentation

**In code:**
- ConfigDef DOC_STR should be clear
- Include examples and constraints
- Note if parameter is dynamic or requires restart

**External documentation:**
- `/workspace/docs/` - User documentation
- Update broker config documentation
- Add migration notes if deprecating old parameter

### Step 7: Write Tests

#### Unit Test for Configuration

**File:** `/workspace/core/src/test/scala/unit/kafka/server/KafkaConfigTest.scala`

```scala
@Test
def testBrokerMessageRetentionMs(): Unit = {
  // Test default value
  val props = new Properties()
  val config = KafkaConfig.fromProps(props)
  assertEquals(-1, config.brokerMessageRetentionMs)

  // Test custom value
  props.put("broker.message.retention.ms", "86400000") // 1 day
  val config2 = KafkaConfig.fromProps(props)
  assertEquals(86400000L, config2.brokerMessageRetentionMs)

  // Test invalid value (if validator present)
  props.put("broker.message.retention.ms", "-2")
  assertThrows(classOf[ConfigException], () => {
    KafkaConfig.fromProps(props)
  })
}
```

#### Integration Test for Dynamic Update

**File:** `/workspace/core/src/test/scala/integration/kafka/server/DynamicBrokerConfigTest.scala`

```scala
@Test
def testDynamicBrokerMessageRetentionUpdate(): Unit = {
  // Start broker
  val config = new Properties()
  config.put("broker.id", "0")
  val broker = startBroker(config)

  // Initial value
  assertEquals(-1, broker.config.brokerMessageRetentionMs)

  // Update dynamically via AdminClient or ZK
  val newValue = "86400000"
  val configResource = new ConfigResource(ConfigResource.Type.BROKER, "0")
  val configEntry = new ConfigEntry("broker.message.retention.ms", newValue)

  adminClient.alterConfigs(
    Collections.singletonMap(configResource, new Config(Arrays.asList(configEntry)))
  ).all().get()

  // Verify update was applied (may require polling)
  TestUtils.waitUntilTrue(
    () => broker.config.brokerMessageRetentionMs == 86400000L,
    "Config not updated",
    10000
  )
}
```

### Step 8: Test Configuration Loading

```bash
# Create a test server.properties
cat > test.properties << EOF
broker.id=0
listeners=PLAINTEXT://localhost:9092
broker.message.retention.ms=86400000
EOF

# Test loading
./gradlew core:test --tests KafkaConfigTest.testBrokerMessageRetentionMs

# Test dynamic update
./gradlew core:test --tests DynamicBrokerConfigTest.testDynamicBrokerMessageRetentionUpdate
```

### Step 9: Run Full Test Suite

```bash
# Run all server tests
./gradlew core:test

# Run integration tests
./gradlew integrationTest

# Run all tests
./gradlew test
```

### Checklist for Adding New Broker Config

- [ ] Add ConfigDef constants in appropriate file (ServerConfigs, ServerLogConfigs, etc.)
- [ ] Add ConfigKey to CONFIG_DEF.define()
- [ ] Create validator for config (atLeast, ValidString, custom, etc.)
- [ ] Add accessor property to KafkaConfig.scala
- [ ] If dynamic: add to DynamicBrokerConfig.AllDynamicConfigs
- [ ] If dynamic: implement Reconfigurable in affected component
- [ ] Add validation logic (ConfigDef, custom, or component-level)
- [ ] Use config value in appropriate broker components
- [ ] Write unit tests for configuration loading
- [ ] Write integration tests if config affects behavior
- [ ] Update documentation (inline and external)
- [ ] Test startup with config file
- [ ] Test dynamic update (if applicable)
- [ ] Run full test suite
- [ ] Check for deprecation impacts (if replacing old config)

### Common Validator Patterns

```java
// Must be >= 1
.define(CONFIG, INT, DEFAULT, atLeast(1), ...)

// Must be between 0 and 100
.define(CONFIG, INT, DEFAULT,
    ConfigDef.Range.between(0, 100), ...)

// Must be one of these strings
.define(CONFIG, STRING, DEFAULT,
    ConfigDef.ValidString.in("value1", "value2", "value3"), ...)

// Custom validation function
.define(CONFIG, INT, DEFAULT,
    new ConfigDef.Validator() {
      public void validate(String name, Object value) {
        int v = (Integer) value;
        if (v < 0 || v > 1000) {
          throw new ConfigException(name, value, "must be between 0 and 1000");
        }
      }
    }, ...)

// List of valid strings (e.g., compression types)
.define(CONFIG, STRING, DEFAULT,
    ConfigDef.ValidString.in(
        BrokerCompressionType.names().toArray(new String[0])
    ), ...)
```

### Configuration Parameter Best Practices

1. **Naming:** Use dots for hierarchy: `log.retention.ms`, `broker.rack`, etc.
2. **Defaults:** Should be sensible for majority of deployments
3. **Documentation:** Be specific about units (ms, bytes, etc.)
4. **Validation:** Catch invalid values early at startup
5. **Dynamic vs Static:** Only make dynamic if component supports it
6. **Backwards Compatibility:** Add deprecation notices if replacing old config
7. **Topic Synonyms:** If applicable to topics, add mapping in ServerTopicConfigSynonyms
8. **Precedence:** Document how it interacts with topic-level configs

---

## Summary: Key Directories and Entry Points

| Task | Key Files/Directories |
|------|----------------------|
| **Broker Startup** | `/workspace/core/src/main/scala/kafka/Kafka.scala` (main) → `/workspace/core/src/main/scala/kafka/server/KafkaServer.scala` |
| **Request Handling** | `/workspace/core/src/main/scala/kafka/server/KafkaApis.scala` |
| **Configuration** | `/workspace/server/src/main/java/org/apache/kafka/server/config/ServerConfigs.java` (broker) + `/workspace/server-common/src/main/java/org/apache/kafka/server/config/ServerLogConfigs.java` (log) |
| **Topic Creation** | `/workspace/core/src/main/scala/kafka/server/ZkAdminManager.scala` |
| **Log Management** | `/workspace/core/src/main/scala/kafka/log/LogManager.scala` |
| **Testing** | `/workspace/core/src/test/scala/` (unit & integration tests) + `/workspace/core/src/test/scala/unit/kafka/integration/KafkaServerTestHarness.scala` (test harness) |
| **Build System** | `/workspace/build.gradle` (root) + `/workspace/gradle/dependencies.gradle` (versions) |

