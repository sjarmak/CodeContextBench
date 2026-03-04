# Apache Kafka Codebase Orientation

## 1. Build System and Broker Startup

### Build System
Kafka uses **Gradle** as its build system. The root build file is `/workspace/build.gradle` which orchestrates a multi-module build.

**Build Configuration Details:**
- Main Gradle file: `/workspace/build.gradle`
- Gradle plugins: Java-library, Spotbugs, Spotless, Swagger, JaCoCo, Apache RAT
- Minimum Java version: Java 8
- Default JVM args: `-Xss4m -XX:+UseParallelGC` with additional JVM flags for Java 16+ (`--add-opens` for internal APIs)
- Dependency management: `/workspace/gradle/dependencies.gradle`

### Broker Startup Entry Point

**Main Entry Class:**
- File: `/workspace/core/src/main/scala/kafka/Kafka.scala`
- Main method: `Kafka.main(args: Array[String])`
- Startup flow:
  1. Parses command-line arguments via `OptionParser` from jopt-simple library
  2. Expects first argument: path to `server.properties` file
  3. Optional `--override` arguments for property overrides
  4. Loads properties via `Utils.loadProps(args(0))`
  5. Creates configuration: `KafkaConfig.fromProps(props, doLog = false)`
  6. Builds server based on mode: `buildServer(serverProps)` (line 70)

### Server Implementation Classes

**Server Factory (line 70-85):**
```
buildServer() dispatches to:
├─ KafkaServer (ZooKeeper mode) - for broker.quorum.voters NOT set
│  File: /workspace/core/src/main/scala/kafka/server/KafkaServer.scala
│  Mode: ZooKeeper-based replication (requires ZooKeeper ensemble)
│
└─ KafkaRaftServer (KRaft mode) - for Kafka Raft Quorum
   File: /workspace/core/src/main/scala/kafka/server/KafkaRaftServer.scala
   Mode: Kraft-based consensus (built-in quorum)
```

**KafkaServer Key Classes** (lines 1-100 of KafkaServer.scala):
- Class: `kafka.server.KafkaServer` - main broker lifecycle
- Imports key coordinator classes:
  - `kafka.controller.KafkaController` - cluster controller
  - `kafka.coordinator.group.GroupCoordinatorAdapter` - consumer group coordination
  - `kafka.coordinator.transaction.TransactionCoordinator` - transaction management
  - `kafka.log.LogManager` - log storage and management
  - `kafka.network.SocketServer` - network I/O
  - `kafka.raft.KafkaRaftManager` - KRaft consensus implementation
  - `kafka.zk.KafkaZkClient` - ZooKeeper client for metadata

**Startup Sequence:**
1. Register signal handlers for graceful shutdown (line 93)
2. Attach shutdown hook via `Exit.addShutdownHook()` (line 102)
3. Call `server.startup()` (line 112)
4. Call `server.awaitShutdown()` (line 120) - blocks until shutdown signal
5. Graceful shutdown triggers `server.shutdown()`

### Configuration Loading
- File: `/workspace/core/src/main/scala/kafka/server/KafkaConfig.scala`
- Configuration registry: `AbstractKafkaConfig.CONFIG_DEF` (merged from multiple config sources)
- Validation and type conversion happens during `KafkaConfig` instantiation

---

## 2. Module Structure

Kafka 3.9.0 is organized into the following core modules:

| Module | Path | Primary Responsibility |
|--------|------|----------------------|
| **clients** | `/workspace/clients` | Kafka clients library including Producer, Consumer, and Admin API. Core client protocols and request/response handling. |
| **core** | `/workspace/core` | Broker server implementation, including KafkaServer, KafkaApis request handling, admin operations, and log management. Main broker logic. |
| **server** | `/workspace/server` | Server common utilities and configuration infrastructure. Base classes for config management (`AbstractKafkaConfig`), policy interfaces, and server utility functions. |
| **server-common** | `/workspace/server-common` | Shared server utilities, request handlers, and common components used across broker and clients. |
| **streams** | `/workspace/streams` | Kafka Streams topology framework for stream processing applications. High-level DSL and low-level Processor API. |
| **connect** | `/workspace/connect` | Kafka Connect framework for data integration. Source and sink connector implementations. |
| **group-coordinator** | `/workspace/group-coordinator` | Group coordination implementation for consumer group management and offset tracking. |
| **transaction-coordinator** | `/workspace/transaction-coordinator` | Transactional messaging coordination and exactly-once semantics implementation. |
| **storage** | `/workspace/storage` | Log storage, segment management, index structures, and disk I/O abstraction layer. |
| **raft** | `/workspace/raft` | KRaft (Kafka Raft) consensus algorithm implementation for broker-to-broker replication without ZooKeeper. |
| **metadata** | `/workspace/metadata` | Metadata management, schema definition, and serialization for KRaft mode metadata log. |
| **shell** | `/workspace/shell` | Interactive CLI shells for Kafka operations (kafka-shell). |
| **tools** | `/workspace/tools` | Administrative tools: config manager, topic tool, reassignment tool, etc. Command-line utilities. |
| **log4j-appender** | `/workspace/log4j-appender` | Log4j integration for Kafka application logging. Custom appender implementation. |
| **jmh-benchmarks** | `/workspace/jmh-benchmarks` | JMH-based performance benchmarks for measuring Kafka performance characteristics. |

**Module Dependencies:**
- `/workspace/settings.gradle` - contains `include()` statements listing all modules
- Each module has its own `/build.gradle` for module-specific build configuration
- `core` module depends on: `clients`, `server`, `group-coordinator`, `transaction-coordinator`, `storage`, `raft`, `metadata`
- `clients` module is independent (no broker dependencies)
- `streams` module depends on `clients` but not `core`
- `connect` module depends on `clients` but not `core`

---

## 3. Topic Creation Flow

Topic creation is a multi-stage process involving client requests, broker routing, policy validation, and metadata updates.

### Client-Side Request (Producer/Admin API)

**Request Class:**
- File: `/workspace/clients/src/main/java/org/apache/kafka/common/requests/CreateTopicsRequest.java`
- Request protocol: `CreateTopicsRequest` with `CreateTopicsRequestData`
- Contains: topic names, replica assignments, configurations, timeout, validation-only flag

### Server-Side Request Processing

**Entry Point - KafkaApis Handler:**
- File: `/workspace/core/src/main/scala/kafka/server/KafkaApis.scala`
- Class: `KafkaApis extends ApiRequestHandler`
- Handler method: `handleCreateTopicsRequest()` (approximately line 2002)
- Request routing: `handle()` method dispatches by API key (line 171)
- API key dispatch: matches `CREATE_TOPICS` enum to handler method (lines 188-270)

**Forwarding Logic (line 208):**
```scala
maybeForwardToController(request, requestLocal) {
  // In ZooKeeper mode: forwards to active controller
  // In KRaft mode: handles directly
}
```

**API Handler Dispatch Pattern:**
- Central `handle()` method in `KafkaApis` receives all requests
- Pattern-matches on `request.header.apiKey`
- Examples:
  - `CREATE_TOPICS` → `handleCreateTopicsRequest()`
  - `FETCH` → `handleFetchRequest()`
  - `PRODUCE` → `handleProduceRequest()`
  - `ALTER_CONFIGS` → `handleAlterConfigsRequest()`

### ZooKeeper Mode - Admin Manager

**Administrator Manager:**
- File: `/workspace/core/src/main/scala/kafka/server/ZkAdminManager.scala`
- Class: `ZkAdminManager` (extends `Logging`)
- Constructor parameters (lines 71-74):
  - `config: KafkaConfig` - broker configuration
  - `metrics: Metrics` - metrics registry
  - `metadataCache: MetadataCache` - cluster metadata
  - `zkClient: KafkaZkClient` - ZooKeeper client

**Topic Creation Method:**
- Method: `createTopics()` (approximately line 159)
- Input: `topics: Map[String, CreatableTopic]`, `ctx: RequestContext`
- Output: `Map[String, ApiError]` for each topic

**Creation Steps:**

1. **Topic Configuration Resolution** (lines 173-187):
   - Parse provided topic config into `LogConfig` objects
   - Handle per-topic config validation
   - Merge with broker defaults

2. **Replica Assignment** (lines 188-198):
   - For manual assignment: validate provided assignments
   - For auto-assignment: use `AdminUtils.assignReplicasToBrokers()`
   - Ensure proper rack awareness and broker availability

3. **Policy Validation** (line 204):
   ```scala
   validateTopicCreatePolicy(topic, resolvedNumPartitions,
                             resolvedReplicationFactor, assignments)
   ```
   - File: `/workspace/core/src/main/scala/kafka/server/ZkAdminManager.scala` (line 102)
   - Uses configured `CreateTopicPolicy` class from `ServerLogConfigs.CREATE_TOPIC_POLICY_CLASS_NAME_CONFIG`
   - Policy can reject topic creation with validation errors

4. **Authorization Check** (lines 2027-2068 in KafkaApis):
   - Checks `ALTER` permission on `CLUSTER` resource
   - Can deny topic creation if insufficient permissions

5. **ZooKeeper Metadata Write:**
   - Creates topic metadata nodes in ZooKeeper at `/brokers/topics/{topicName}`
   - Calls `AdminZkClient.createTopicWithAssignment()` to persist metadata
   - Triggers metadata update event: `tryCompleteDelayedTopicOperations(topic)`

### KRaft Mode - Controller Handler

**Controller API Handler:**
- File: `/workspace/core/src/main/scala/kafka/server/ControllerApis.scala`
- Class: `ControllerApis`
- Handler method: `handleCreateTopics()` (approximately line 361)
- Writes to metadata log instead of ZooKeeper

### Response Generation

**Response Classes:**
- File: `/workspace/clients/src/main/java/org/apache/kafka/common/requests/CreateTopicsResponse.java`
- Response data: `CreateTopicsResponseData` containing:
  - `CreatableTopicResult` for each topic with status/error
  - Topic ID (UUID) for successfully created topics
  - Error codes and messages for failures

### Topic Creation Flow Diagram

```
Client Request (Admin API or Producer)
       ↓
CreateTopicsRequest (protocol serialization)
       ↓
Network Layer → SocketServer
       ↓
RequestChannel.Request (enqueue)
       ↓
KafkaRequestHandler thread pool (dequeue)
       ↓
KafkaApis.handle() (API dispatch)
       ├─ Auth check: ALTER permission on CLUSTER
       ├─ ZooKeeper mode:
       │  └─ maybeForwardToController()
       │     └─ ZkAdminManager.createTopics()
       │        ├─ Validate topic configs
       │        ├─ Resolve replica assignments
       │        ├─ Apply CreateTopicPolicy
       │        └─ AdminZkClient.createTopicWithAssignment()
       │           └─ Write to /brokers/topics/{topicName}
       │
       └─ KRaft mode:
          └─ ControllerApis.handleCreateTopics()
             └─ Write to metadata log
       ↓
CreateTopicsResponse (serialization)
       ↓
Client receives response with success/error per topic
```

---

## 4. Testing Framework

### Test Organization

**Directory Structure:**
- `/workspace/core/src/test/scala/unit/` - Unit tests
- `/workspace/core/src/test/scala/integration/` - Integration tests
- Test organization mirrors source structure: `kafka/server/` → test `/kafka/server/`

### Integration Test Base Class

**IntegrationTestHarness:**
- File: `/workspace/core/src/test/scala/integration/kafka/api/IntegrationTestHarness.scala`
- Class: `IntegrationTestHarness extends KafkaServerTestHarness` (line 43)
- Purpose: Base class for end-to-end testing with full broker instances

**Key Features:**
- Manages multiple broker instances (configurable count)
- Automatic broker startup and teardown
- Provides producer, consumer, and admin client factories
- Listener and security configuration support
- Before/After hooks for test setup/cleanup

**Methods:**
- `generateConfigs(): Seq[KafkaConfig]` - generates broker configs
- `modifyConfigs(configs: Seq[KafkaConfig]): Seq[KafkaConfig]` - override for custom config
- `configureListeners()` - setup network listeners
- `createProducer()` - creates KafkaProducer
- `createConsumer()` - creates KafkaConsumer
- `adminClient` - provides AdminClient instance
- `anySocketServer` - returns live broker socket server for direct protocol testing

### Request-Level Test Base Class

**BaseRequestTest:**
- File: `/workspace/core/src/test/scala/unit/kafka/server/BaseRequestTest.scala`
- Extends: `IntegrationTestHarness`
- Purpose: Test request/response handling via socket connections
- Default broker count: 3 brokers

**Direct Protocol Testing Methods:**
- `connect(host: String, port: Int): SocketChannel` - establishes socket connection
- `anySocketServer: SocketServer` - gets any live broker socket
- `controllerSocketServer: SocketServer` - gets controller broker socket
- `adminSocketServer: SocketServer` - gets admin-capable broker socket

**Usage Pattern:**
```scala
// Direct socket connection for protocol testing
val socketChannel = connect(host, port)
// Send raw protocol bytes, receive responses
val response = NetworkClient.readResponse(socket)
```

### Additional Specialized Test Base Classes

**BaseFetchRequestTest:**
- File: `/workspace/core/src/test/scala/unit/kafka/server/BaseFetchRequestTest.scala`
- Extends: `BaseRequestTest`
- Specialization: Fetch request testing patterns
- Common patterns for produce-then-fetch test flows

**BaseClientQuotaManagerTest:**
- File: `/workspace/core/src/test/scala/unit/kafka/server/BaseClientQuotaManagerTest.scala`
- Specialization: Client quota management testing
- Throttling behavior verification

### Test Patterns

**Common Integration Test Pattern:**
```scala
class MyIntegrationTest extends IntegrationTestHarness {
  def testSomething(): Unit = {
    // Test code using brokers, producers, consumers
  }
}
```

**Common Unit Test Pattern:**
```scala
class MyTest extends BaseRequestTest {
  def testProtocolHandling(): Unit = {
    val socket = connect(localhost, brokerPort)
    // Send request, verify response
  }
}
```

### Testing Frameworks Used

**Test Runners:**
- JUnit 4 (org.junit.Test annotation)
- ScalaTest (for Scala tests)
- JUnit Jupiter (JUnit 5) for some newer tests

**Mocking:**
- Mockito (org.mockito.*)
- EasyMock (for legacy tests)

**Assertion Libraries:**
- ScalaTest assertions
- JUnit assertions

**Utilities:**
- `TestUtils` - common test utilities
- `KafkaServerTestHarness` - base harness for full cluster tests
- `EmbeddedKafkaCluster` - lightweight test cluster

### Test Categories

**Unit Tests** (core/src/test/scala/unit/):
- Test individual components in isolation
- Mock dependencies
- Fast execution
- Organized by component: server/, controller/, log/, etc.

**Integration Tests** (core/src/test/scala/integration/):
- Test multiple components working together
- Real broker instances
- Slower execution but realistic
- Organized by feature: admin/, api/, cluster/, etc.

**Example Integration Test Files:**
- `/workspace/core/src/test/scala/integration/kafka/admin/AdminFenceProducersIntegrationTest.scala`
- `/workspace/core/src/test/scala/integration/kafka/api/AdminClientWithPoliciesIntegrationTest.scala`
- `/workspace/core/src/test/scala/integration/kafka/api/AbstractConsumerTest.scala`

---

## 5. Configuration System

### Configuration Architecture

Kafka's configuration system is built on Apache Kafka's `ConfigDef` framework with additional broker-specific enhancements.

### Configuration Definition and Registry

**Master Configuration Definition:**
- File: `/workspace/server/src/main/java/org/apache/kafka/server/config/AbstractKafkaConfig.java`
- Class: `AbstractKafkaConfig extends AbstractConfig`
- Central Registry: `AbstractKafkaConfig.CONFIG_DEF` (lines 45-68)

**CONFIG_DEF Composition:**
The master ConfigDef merges configs from multiple sources:
```java
CONFIG_DEF = Utils.mergeConfigs(Arrays.asList(
    RemoteLogManagerConfig.configDef(),
    ZkConfigs.CONFIG_DEF,
    ServerConfigs.CONFIG_DEF,
    KRaftConfigs.CONFIG_DEF,
    SocketServerConfigs.CONFIG_DEF,
    ReplicationConfigs.CONFIG_DEF,
    GroupCoordinatorConfig.GROUP_COORDINATOR_CONFIG_DEF,
    // ... 10+ more config sources
    QuotaConfigs.CONFIG_DEF,
    BrokerSecurityConfigs.CONFIG_DEF,
    DelegationTokenManagerConfigs.CONFIG_DEF,
    PasswordEncoderConfigs.CONFIG_DEF
));
```

### Individual Configuration Modules

**ServerConfigs (General Broker Configs):**
- File: `/workspace/server/src/main/java/org/apache/kafka/server/config/ServerConfigs.java`
- Defines: Broker ID, message size, thread counts, compression, deletion settings
- Configuration Definition: `ServerConfigs.CONFIG_DEF` (line 141)

**Example Config Definition Pattern** (lines 142-176):
```java
.define(CONFIG_NAME, TYPE, DEFAULT_VALUE, VALIDATOR, IMPORTANCE, DOC_STRING)
// Example:
.define(BROKER_ID_CONFIG, INT, BROKER_ID_DEFAULT, HIGH, BROKER_ID_DOC)
.define(NUM_IO_THREADS_CONFIG, INT, NUM_IO_THREADS_DEFAULT, atLeast(1), HIGH, NUM_IO_THREADS_DOC)
```

**Configuration Elements:**
- `CONFIG_NAME` (String) - configuration key
- `TYPE` (ConfigDef.Type) - BOOLEAN, INT, LONG, STRING, LIST, DOUBLE
- `DEFAULT_VALUE` - default if not specified
- `VALIDATOR` - validation function (e.g., `atLeast(1)`, `ValidString.in(...)`)
- `IMPORTANCE` (HIGH, MEDIUM, LOW) - for documentation
- `DOC_STRING` - documentation shown in config output

**Other Config Modules:**
- `ZkConfigs` - ZooKeeper connection settings
- `KRaftConfigs` - KRaft quorum configuration
- `SocketServerConfigs` - Network listeners and ports
- `ReplicationConfigs` - Replication parameters
- `LogConfig` - Log segment and retention settings
- `QuotaConfigs` - Client quota configuration
- `CleanerConfig` - Log compaction settings

### Dynamic Configuration System

**Dynamic Broker Configuration Manager:**
- File: `/workspace/core/src/main/scala/kafka/server/DynamicBrokerConfig.scala`
- Class: `DynamicBrokerConfig` (line 204)
- Purpose: Manages broker configuration updates at runtime without restart

**Key Methods:**

**1. Configuration Validation:**
```scala
def validateConfigs(props: Properties, perBrokerConfig: Boolean): Unit (line 142)
```
- Validates that configs are valid and dynamically updatable (if perBrokerConfig=false)
- Checks security config format
- Validates config types match ConfigDef

**2. Per-Broker Configuration Update:**
```scala
def updateBrokerConfig(brokerId: Int, configs: Properties): Unit (line 333)
```
- Updates configuration specific to individual broker
- Stored at ZooKeeper path: `/configs/brokers/{brokerId}`
- Triggers reconfiguration callbacks

**3. Cluster-Wide Default Configuration:**
```scala
def updateDefaultConfig(configs: Properties): Unit (line 344)
```
- Updates default configuration for all brokers
- Stored at ZooKeeper path: `/configs/brokers/<default>`
- Applies to all brokers unless per-broker override exists

**Thread Safety:**
- Uses `ReentrantReadWriteLock` (line 215) for concurrent access
- Read locks for getting configs
- Write locks for updating configs

### Reconfigurable Component Pattern

**Reconfigurable Trait:**
- File: `/workspace/core/src/main/scala/kafka/server/DynamicBrokerConfig.scala` (line 655)
- Used by components that support dynamic reconfiguration
- Implemented by: DynamicLogConfig, DynamicListenerConfig, DynamicThreadPool, etc.

**Trait Methods:**
```scala
trait BrokerReconfigurable {
  def reconfigurableConfigs: Set[String]  // which configs can be reconfigured
  def validateReconfiguration(newConfig: KafkaConfig): Unit  // validate before applying
  def reconfigure(oldConfig: KafkaConfig, newConfig: KafkaConfig): Unit  // apply changes
}
```

**Implementation Example - DynamicLogConfig:**
- File: `/workspace/core/src/main/scala/kafka/server/DynamicBrokerConfig.scala` (line 685)
- Manages: log retention, segment size, cleanup policy, etc.
- Reconfigurable configs: retention.ms, retention.bytes, cleanup.policy, etc.
- `reconfigure()` method (line 719): calls `updateLogsConfig()` to apply changes to all logs
- `validateReconfiguration()` method: validates retention policy compatibility

**Other Reconfigurable Components:**
1. **DynamicListenerConfig** (line 1048) - Per-listener SSL/SASL settings
2. **DynamicThreadPool** - Thread pool sizes (num.io.threads, etc.)
3. **DynamicProducerStateManagerConfig** - Producer state retention
4. **DynamicRemoteLogConfig** - Remote log storage settings

### Configuration Storage Locations

**ZooKeeper Paths:**
- `/configs/brokers/{brokerId}` - per-broker configuration overrides
- `/configs/brokers/<default>` - cluster-wide default configuration
- `/configs/topics/{topicName}` - per-topic configuration

**Configuration Files:**
- `server.properties` - static configuration loaded at startup
- Properties can be overridden with command-line `--override` flag

### Configuration Validation in Practice

**When Configs Are Validated:**
1. **At Startup:** `KafkaConfig.fromProps(props, doLog)` validates all configs
2. **On Dynamic Update:** `DynamicBrokerConfig.validateConfigs()` checks updatable flag
3. **Per Component:** Each reconfigurable component validates in `validateReconfiguration()`
4. **Type Checking:** `ConfigDef` validates types match expectations

**Validation Errors:**
- Thrown as `ConfigException` with descriptive message
- Include config name, invalid value, and reason
- Validation failures prevent config application

### Configuration Hierarchy

```
Client Properties → server.properties → --override args
        ↓
    KafkaConfig
        ↓
AbstractKafkaConfig.CONFIG_DEF (merged from all sources)
        ↓
Individual Component Configs:
  ├─ ServerConfigs (broker settings)
  ├─ LogConfig (log settings)
  ├─ SocketServerConfigs (network settings)
  ├─ ZkConfigs (ZooKeeper settings)
  ├─ KRaftConfigs (Raft settings)
  └─ ... 15+ other config modules
        ↓
DynamicBrokerConfig (runtime updates)
        ↓
Reconfigurable Components (apply changes):
  ├─ DynamicLogConfig
  ├─ DynamicListenerConfig
  └─ ... other components
```

---

## 6. Adding a New Broker Config

If you need to add a new broker configuration parameter, follow these steps:

### Step 1: Define the Configuration

**Location:** Choose appropriate config module based on category:
- General broker settings: `/workspace/server/src/main/java/org/apache/kafka/server/config/ServerConfigs.java`
- Log-related: `/workspace/storage/src/main/java/org/apache/kafka/storage/internals/log/LogConfig.java`
- Network/Socket: `/workspace/network/src/main/java/org/apache/kafka/network/SocketServerConfigs.java`
- Replication: `/workspace/server/src/main/java/org/apache/kafka/server/config/ReplicationConfigs.java`
- ZooKeeper: `/workspace/server/src/main/java/org/apache/kafka/server/config/ZkConfigs.java`

**File Location Example** (for a broker config):
`/workspace/server/src/main/java/org/apache/kafka/server/config/ServerConfigs.java`

**Add Configuration Constants** (following existing pattern):
```java
// 1. Configuration name constant
public static final String MY_NEW_CONFIG = "my.new.config";

// 2. Default value constant (optional)
public static final int MY_NEW_CONFIG_DEFAULT = 100;

// 3. Documentation constant
public static final String MY_NEW_CONFIG_DOC = "Description of what this config does. " +
    "Explain valid values, constraints, and effects.";

// 4. Register in CONFIG_DEF (add to .define() chain)
public static final ConfigDef CONFIG_DEF = new ConfigDef()
    // ... existing configs ...
    .define(MY_NEW_CONFIG, INT, MY_NEW_CONFIG_DEFAULT, atLeast(1), HIGH, MY_NEW_CONFIG_DOC)
    // ... more configs ...
```

**Configuration Definition Parameters:**
- **Type:** `BOOLEAN`, `INT`, `LONG`, `STRING`, `LIST`, `DOUBLE`
- **Validator:** `atLeast(value)`, `atMost(value)`, `in(options)`, `ValidString.in(values)`
- **Importance:** `HIGH` (documented, important), `MEDIUM` (less critical), `LOW` (internal)
- **Default:** Must match type or be `null`

### Step 2: Create Configuration Getter in KafkaConfig

**Location:** `/workspace/core/src/main/scala/kafka/server/KafkaConfig.scala`

**Add Getter Method:**
```scala
def myNewConfig: Int = getInt(ServerConfigs.MY_NEW_CONFIG)

// Or for non-Java int types:
def myNewConfig: String = getString(ServerConfigs.MY_NEW_CONFIG)
```

**Location Details:**
- Getters are added as methods in the `KafkaConfig` class
- Follow naming convention: snake_case config becomes camelCase getter
- Use appropriate `get*()` method: `getInt()`, `getString()`, `getBoolean()`, `getLong()`, `getList()`

### Step 3: Mark as Dynamic (if applicable)

If your config should be updatable without broker restart:

**Location:** `/workspace/core/src/main/scala/kafka/server/DynamicBrokerConfig.scala`

**Add to Dynamic Config List:**
```scala
// Around line 480-500 in DynamicBrokerConfig.scala, find the reconfigurableConfigs set

private val reconfigurableConfigs = mutable.Set[String](
  // ... existing configs ...
  ServerConfigs.MY_NEW_CONFIG,  // Add this line if dynamic
  // ... more configs ...
)
```

**Note:** Not all configs should be dynamic. Only those that can be safely changed at runtime without data corruption or consistency issues.

### Step 4: Add Validation Logic (if needed)

**For Complex Validation:**

If your config requires complex validation beyond type checking, implement custom validator:

**Option A: ConfigDef Validator (at definition time):**
```java
.define(MY_NEW_CONFIG, INT, MY_NEW_CONFIG_DEFAULT, new ConfigDef.Validator() {
    @Override
    public void ensureValid(String name, Object value) {
        int val = (Integer) value;
        if (val < 0) {
            throw new ConfigException(name, value, "Must be non-negative");
        }
        // Additional validation logic
    }
}, HIGH, MY_NEW_CONFIG_DOC)
```

**Option B: Reconfigurable Component (at reconfiguration time):**

If validation depends on other configs, implement in reconfigurable component:
```scala
// In DynamicBrokerConfig.scala, in appropriate reconfigurable component:
override def validateReconfiguration(newConfig: KafkaConfig): Unit = {
  val newValue = newConfig.myNewConfig
  val otherValue = newConfig.someOtherConfig

  if (newValue < 0) {
    throw new ConfigException(s"my.new.config must be non-negative, got: $newValue")
  }
  if (newValue > otherValue) {
    throw new ConfigException(s"my.new.config ($newValue) cannot exceed " +
      s"some.other.config ($otherValue)")
  }
}
```

### Step 5: Implement Configuration Application Logic

**In KafkaServer:**

If your config affects broker behavior, implement application in appropriate component:

**Example: Log-related Config**
- File: `/workspace/core/src/main/scala/kafka/server/DynamicBrokerConfig.scala`
- Class: `DynamicLogConfig`
- Method: `reconfigure()` - applies config to LogManager and all logs

**Example: Thread Pool Config**
- File: `DynamicThreadPool` class (referenced in DynamicBrokerConfig)
- Method: `reconfigure()` - resizes thread pools with new value

**Example: Listener/Network Config**
- File: `DynamicListenerConfig` class
- Method: `reconfigure()` - updates listener configurations

**Implementation Pattern:**
```scala
override def reconfigure(oldConfig: KafkaConfig, newConfig: KafkaConfig): Unit = {
  val oldValue = oldConfig.myNewConfig
  val newValue = newConfig.myNewConfig

  if (oldValue != newValue) {
    // Apply change to components
    myComponent.updateConfig(newValue)
    info(s"Updated my.new.config from $oldValue to $newValue")
  }
}
```

### Step 6: Write Tests

**Unit Tests:**

File: `/workspace/core/src/test/scala/unit/kafka/server/KafkaConfigTest.scala`

```scala
class MyNewConfigTest extends BaseRequestTest {
  def testMyNewConfigValidation(): Unit = {
    // Test valid values
    val validProps = new Properties()
    validProps.put(ServerConfigs.MY_NEW_CONFIG, "100")
    val config = KafkaConfig.fromProps(validProps)
    assertEquals(100, config.myNewConfig)
  }

  def testMyNewConfigInvalid(): Unit = {
    // Test invalid values throw exception
    val invalidProps = new Properties()
    invalidProps.put(ServerConfigs.MY_NEW_CONFIG, "-1")
    assertThrows[ConfigException] {
      KafkaConfig.fromProps(invalidProps)
    }
  }
}
```

**Integration Tests (if dynamic config):**

File: `/workspace/core/src/test/scala/integration/kafka/api/DynamicConfigTest.scala`

```scala
class MyNewConfigDynamicTest extends IntegrationTestHarness {
  def testDynamicConfigUpdate(): Unit = {
    // Test dynamic update via AlterConfigs API
    val oldValue = brokerConfigs(0).myNewConfig

    // Change config dynamically
    val newValue = oldValue + 50
    val configResource = new ConfigResource(ConfigResource.Type.BROKER, "0")
    adminClient.alterConfigs(
      Map(configResource -> new ConfigEntry(ServerConfigs.MY_NEW_CONFIG, newValue.toString)).asJava
    ).all().get()

    // Verify change applied
    val updatedConfig = brokerConfigs(0).myNewConfig
    assertEquals(newValue, updatedConfig)
  }
}
```

### Step 7: Update Configuration Documentation

**HTML Documentation Generation:**

The config is automatically included in generated HTML by:
```
KafkaConfig.main() - File: /workspace/core/src/main/scala/kafka/server/KafkaConfig.scala (line 62)
```

Run to generate HTML:
```bash
cd /workspace
./gradlew -p core run -c main --args "Server > docs/generated_brokerconfigs.html"
```

### Step 8: Update Breaking Changes (if applicable)

**For Major Version Changes:**

If removing or changing config semantics:
- Add migration notes to release notes
- Add deprecation warnings if replacing old config
- Maintain backward compatibility if possible

**Migration Patterns:**
```scala
// Support old config name for backwards compatibility
private val newConfigValue =
  config.getString(NEW_CONFIG_NAME) match {
    case null => config.getString(OLD_CONFIG_NAME) // fallback
    case x => x
  }
```

### Step 9: Integration Testing with Multiple Scenarios

**Test dynamic config updates:**
```scala
def testDynamicConfigWithProducerConsumer(): Unit = {
  // Start producer/consumer
  // Update config dynamically
  // Verify behavior changes immediately
  // Verify no data loss or corruption
}
```

### Complete Example: Adding `my.batch.size` Config

**1. ServerConfigs.java:**
```java
public static final String MY_BATCH_SIZE_CONFIG = "my.batch.size";
public static final int MY_BATCH_SIZE_DEFAULT = 1000;
public static final String MY_BATCH_SIZE_DOC =
  "The size of batches for my new feature. Higher values improve throughput.";

// In CONFIG_DEF:
.define(MY_BATCH_SIZE_CONFIG, INT, MY_BATCH_SIZE_DEFAULT, atLeast(1), MEDIUM, MY_BATCH_SIZE_DOC)
```

**2. KafkaConfig.scala:**
```scala
def myBatchSize: Int = getInt(ServerConfigs.MY_BATCH_SIZE_CONFIG)
```

**3. DynamicBrokerConfig.scala (if dynamic):**
```scala
private val reconfigurableConfigs = mutable.Set[String](
  // ... existing ...
  ServerConfigs.MY_BATCH_SIZE_CONFIG,
)
```

**4. Test (KafkaConfigTest.scala):**
```scala
def testMyBatchSize(): Unit = {
  val props = new Properties()
  props.put(ServerConfigs.MY_BATCH_SIZE_CONFIG, "2000")
  val config = KafkaConfig.fromProps(props)
  assertEquals(2000, config.myBatchSize)
}
```

### Configuration Best Practices

1. **Choose Correct Importance:** HIGH for critical settings, MEDIUM for tuning, LOW for internal
2. **Use Validators:** Always validate ranges and constraints
3. **Document Thoroughly:** Doc string should explain effects and trade-offs
4. **Default Values:** Provide sensible defaults
5. **Dynamic vs Static:** Only mark as dynamic if truly safe to update at runtime
6. **Test Thoroughly:** Test both valid and invalid values
7. **Backward Compatibility:** Support old config names when possible
8. **Performance:** Document performance implications of different values
9. **Security:** Mark sensitive configs (passwords, keys) appropriately
10. **Deprecation:** Use deprecated config names with clear migration path

---

## Summary

Kafka's architecture uses:
- **Gradle** for multi-module builds
- **Main entry:** `kafka.Kafka.scala` with `KafkaServer` or `KafkaRaftServer`
- **14+ modules** organized by responsibility
- **Request handling:** Central `KafkaApis.handle()` dispatches to specific handlers
- **Topic creation:** Complex flow through authorization, validation, and metadata updates
- **Testing:** Integration test harness with base classes for different test types
- **Configuration:** Modular ConfigDef system with dynamic reconfiguration support
- **Adding configs:** Define in appropriate module, register in ConfigDef, implement validation and application logic
