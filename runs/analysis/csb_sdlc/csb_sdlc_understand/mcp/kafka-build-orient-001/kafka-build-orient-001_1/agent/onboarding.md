# Apache Kafka Codebase Orientation

## 1. Build System and Broker Startup

### Build System
Apache Kafka uses **Gradle** as its build system. The main configuration files are:
- `build.gradle`: Root build configuration with plugins and global settings
- `settings.gradle`: Defines all submodules/projects that Gradle should build
- `gradle/dependencies.gradle`: Version management for all dependencies

### Broker Startup Entry Point
The main entry point for starting a Kafka broker is:
**File**: `core/src/main/scala/kafka/Kafka.scala`

**Key Methods**:
- `main(args: Array[String])`: Entry point that parses command-line arguments and properties file
- `getPropsFromArgs()`: Parses broker properties from file and command-line overrides
- `buildServer(props: Properties)`: Creates either a ZooKeeper-based or KRaft-based broker instance

**Key Classes Involved in Broker Initialization**:
1. **`kafka.server.KafkaServer`** (`core/src/main/scala/kafka/server/KafkaServer.scala`) - ZooKeeper mode broker
   - Constructor takes `KafkaConfig`, `Time`, optional thread name prefix, and forwarding flag
   - `startup()` method orchestrates the entire broker initialization process (lines 216-500+)

2. **`kafka.server.KafkaRaftServer`** - KRaft (Kafka Raft) mode broker

3. **`kafka.server.KafkaConfig`** (`core/src/main/scala/kafka/server/KafkaConfig.scala`) - Configuration container
   - Extends `AbstractKafkaConfig` which merges configurations from multiple sources
   - Manages broker ID, log directories, listeners, ZooKeeper settings, etc.

### Broker Startup Sequence (KafkaServer)
The `KafkaServer.startup()` method (lines 216+) performs these steps:
1. Initialize ZooKeeper client and get cluster ID
2. Load metadata properties ensemble from log directories
3. Generate or retrieve broker ID
4. Initialize metrics and Yammer metrics
5. Start KafkaScheduler for background tasks
6. Create quota managers
7. **Start LogManager** - manages all log files and partitions
8. Create MetadataCache - in-memory cluster metadata representation
9. Initialize feature change listeners
10. Create SocketServer - handles network connections
11. Create AlterPartitionManager
12. Create ReplicaManager - handles replication
13. Create KafkaController (if this broker is the controller)
14. Create GroupCoordinator and TransactionCoordinator
15. Initialize KafkaApis - handles client requests
16. Create and start RequestHandlerPools
17. Start all components (socket server, coordinators, etc.)
18. Register broker in ZooKeeper
19. Set broker state to `RUNNING`

---

## 2. Module Structure

Kafka is organized into the following core modules:

### **core/** - Core broker and server implementation
- `src/main/scala/kafka/server/` - Broker request handling and coordination
  - `KafkaServer.scala` - Main broker class
  - `KafkaApis.scala` - Handles all client API requests
  - `ReplicaManager.scala` - Manages replicas and partition leadership
  - `DynamicBrokerConfig.scala` - Dynamic configuration management
  - `KafkaController.scala` - Cluster controller logic (in ZK mode)
- `src/main/scala/kafka/log/` - Log storage and management
  - `LogManager.scala` - Manages all log segments and partitions
  - `UnifiedLog.scala` - Single partition log abstraction
- `src/main/scala/kafka/controller/` - ZooKeeper-based controller
- `src/main/scala/kafka/zk/` - ZooKeeper client and utilities
- `src/main/scala/kafka/coordinator/` - Consumer group and transaction coordinators
- `src/test/` - Unit and integration tests

### **server/** - Server-specific configuration and utilities
- Java-based server utilities and configurations
- Network and socket server implementations
- Configuration classes for broker settings

### **server-common/** - Shared configuration classes
- `org.apache.kafka.server.config.AbstractKafkaConfig` - Base configuration class
- `org.apache.kafka.server.config.ServerConfigs` - Broker-level configurations
- `org.apache.kafka.server.config.ServerLogConfigs` - Log-related configurations

### **clients/** - Kafka client implementations
- `org.apache.kafka.clients.producer.*` - Producer implementation
- `org.apache.kafka.clients.consumer.*` - Consumer implementation
- `org.apache.kafka.clients.admin.*` - AdminClient implementation
- Protocol and serialization utilities

### **metadata/** - KRaft metadata controller
- `org.apache.kafka.controller.QuorumController` - KRaft mode controller
- Metadata log and replication control

### **raft/** - Kafka Raft implementation
- `org.apache.kafka.raft.*` - Raft consensus algorithm

### **group-coordinator/** - Consumer group coordination
- Group coordination logic independent of broker

### **transaction-coordinator/** - Transaction coordination
- Transaction state management

### **storage/** - Storage layer abstraction
- Log storage implementations
- Tiered storage support

### **streams/** - Kafka Streams applications
- Stream processing API and implementation

### **connect/** - Kafka Connect framework
- Source/sink connectors
- Distributed workers

### **tests/** - System and integration tests

---

## 3. Topic Creation Flow

Topic creation follows this end-to-end path:

### Request Path
**1. Client sends CreateTopicsRequest**
- Client: `org.apache.kafka.clients.admin.KafkaAdminClient.createTopics()`
- Contains topic names, partitions, replication factor, and configs

**2. Broker receives and routes request**
- **File**: `core/src/main/scala/kafka/server/KafkaApis.scala`
- **Method**: `handleCreateTopicsRequest()` (lines 2002-2098)
- Handles authorization checks:
  - Verifies CREATE permission on CLUSTER or individual TOPICs
  - Filters topics by authorization
  - Validates topic names (prevents internal topic creation)

**3. Delegate to admin manager**
- Routes to `ZkAdminManager.createTopics()` in ZK mode
- Routes to controller in KRaft mode

### Topic Creation in ZooKeeper Mode
**File**: `core/src/main/scala/kafka/server/ZkAdminManager.scala`
**Method**: `createTopics()` (lines 159-258)

**Key Processing Steps**:
1. **Validation Phase** (lines 167-205)
   - Check if topic already exists via `metadataCache.contains(topic.name)`
   - Validate that configs don't have null values
   - Check that either numPartitions/replicationFactor OR replicasAssignment is set (not both)
   - Validate topic creation policy if configured (from `ServerLogConfigs.CREATE_TOPIC_POLICY_CLASS_NAME_CONFIG`)

2. **Assignment Phase** (lines 188-200)
   - If no explicit replica assignment provided:
     - Call `AdminUtils.assignReplicasToBrokers()` to auto-assign replicas
     - Parameters: broker list, resolved partition count, resolved replication factor
   - Otherwise parse provided assignments

3. **Configuration Validation** (line 204)
   - Call `adminZkClient.validateTopicCreate()` to validate topic configs
   - Validates against `LogConfig.SERVER_CONFIG_DEF`

4. **Policy Validation** (line 205)
   - Invoke create topic policy plugin if configured
   - Validates topic name, partition count, replication factor, assignments, and configs

5. **ZooKeeper Persistence** (line 216)
   - Call `adminZkClient.createTopicWithAssignment(topic.name, configs, assignments, validate = false)`
   - This persists topic metadata to ZooKeeper under `/config/topics/{topicName}` and `/brokers/topics/{topicName}`
   - Creates the topic with cluster metadata if `config.usesTopicId` is true

6. **Delayed Operation** (lines 251-256)
   - Wraps successful creations in `DelayedCreatePartitions` operation
   - Waits for partition replica initialization to complete within timeout period
   - Uses `topicPurgatory` (operation purgatory) to track delayed operations

### Key Classes Involved
- **`kafka.server.KafkaApis`** - Request dispatcher
- **`kafka.server.ZkAdminManager`** - Admin operations for ZK mode
- **`kafka.zk.AdminZkClient`** - ZooKeeper interaction layer
- **`kafka.controller.KafkaController`** - Controller logic (if this broker is active controller)
- **`kafka.server.ReplicaManager`** - Manages partition replica creation and initialization
- **`kafka.log.LogManager`** - Creates log directories for partitions
- **`org.apache.kafka.server.policy.CreateTopicPolicy`** - Pluggable policy validator

### Response Flow
- Success: Returns topic metadata with partition assignments
- Validation errors: Returns `INVALID_CONFIG` or `INVALID_REQUEST` error codes
- Authorization failures: Returns `TOPIC_AUTHORIZATION_FAILED`
- Controller not active: Returns `NOT_CONTROLLER` (client retries on different broker)

---

## 4. Testing Framework

### Test Frameworks
Kafka uses the following testing frameworks:

**1. JUnit 5 (Jupiter)**
- Main testing framework using `@Test` annotations
- Located in `core/src/test/java/` and `core/src/test/scala/`
- Uses parameterized tests with `@ParameterizedTest` and `@ValueSource`

**2. ScalaTest (via JUnit)**
- For Scala-based tests using `@Test` from JUnit
- Mixin Scala assertions and utilities

**3. Mockito**
- For mocking objects: `mock(classOf[ClassName])`
- Used extensively for testing without real ZooKeeper/brokers

### Test Harness Classes

**QuorumTestHarness** (`core/src/test/scala/integration/kafka/server/QuorumTestHarness.scala`)
- Base class for cluster tests that work with both ZK and KRaft modes
- Manages cluster lifecycle (startup/shutdown)
- Methods:
  - `servers: mutable.Buffer[KafkaServer]` - Access to broker instances
  - `adminClient()` - Get AdminClient for cluster
  - `checkIsZKTest()` - Verify test is in ZK mode

**IntegrationTestHarness** (`core/src/test/scala/integration/kafka/api/IntegrationTestHarness.scala`)
- Extends `KafkaServerTestHarness`
- Provides producer and consumer helpers
- Methods:
  - `createProducer()` - Creates test producer with standard config
  - `createConsumer()` - Creates test consumer with standard config

**KafkaServerTestHarness** (`core/src/test/scala/unit/kafka/integration/KafkaServerTestHarness.scala`)
- Base test harness for broker tests
- Starts and manages KafkaServer instances
- Properties:
  - `instanceConfigs: Seq[KafkaConfig]` - Broker configurations
  - `servers: mutable.Buffer[KafkaServer]` - Broker instances

### Unit Testing Pattern
Example from `core/src/test/scala/unit/kafka/server/ServerGenerateBrokerIdTest.scala`:
```scala
val config1 = KafkaConfig.fromProps(props1)
val server1 = new KafkaServer(config1, threadNamePrefix = Option(this.getClass.getName))
server1.startup()
// ... test assertions ...
server1.shutdown()
```

### Integration Testing Pattern
Tests typically extend `QuorumTestHarness` with cluster annotation:
```scala
@Tag("integration")
class SomeIntegrationTest extends QuorumTestHarness {
  @ParameterizedTest
  @ValueSource(strings = Array("zk", "kraft"))
  def testSomething(quorum: String): Unit = {
    // test code
  }
}
```

### Test Configuration
- **JUnit 5 Extensions**: `kafka.test.junit.ClusterTestExtensions`
  - Automatically manages cluster lifecycle for `@ClusterTest` annotated methods
  - Supports both ZK and KRaft modes dynamically

- **Test Utils**: `core/src/test/scala/unit/kafka/utils/TestUtils.scala`
  - `TestUtils.createBrokerConfig()` - Creates broker configuration
  - `TestUtils.tempDir()` - Creates temporary directories
  - Utilities for common test setup

### Running Tests
```bash
# Unit tests in a module
gradle core:test

# Specific test class
gradle core:test --tests kafka.server.ServerGenerateBrokerIdTest

# Integration tests
gradle core:integrationTest
```

---

## 5. Configuration System

### Configuration Architecture

**Configuration Hierarchy** (from server-common):
1. **AbstractKafkaConfig** - Base configuration class
   - **File**: `server/src/main/java/org/apache/kafka/server/config/AbstractKafkaConfig.java`
   - **Static ConfigDef**: Merges all configuration sources via `Utils.mergeConfigs()`
   - Merges:
     - `RemoteLogManagerConfig.configDef()`
     - `ZkConfigs.CONFIG_DEF` - ZooKeeper configuration
     - `ServerConfigs.CONFIG_DEF` - Broker core configuration
     - `KRaftConfigs.CONFIG_DEF` - KRaft-specific configuration
     - `SocketServerConfigs.CONFIG_DEF` - Network configuration
     - `ReplicationConfigs.CONFIG_DEF` - Replication configuration
     - `GroupCoordinatorConfig.*` - Consumer group configuration
     - `LogConfig.SERVER_CONFIG_DEF` - Log storage configuration
     - `TransactionLogConfigs.CONFIG_DEF` - Transaction configuration
     - And many more...

2. **KafkaConfig** - Extends AbstractKafkaConfig
   - **File**: `core/src/main/scala/kafka/server/KafkaConfig.scala`
   - Adds broker-specific accessors and validation
   - Loads from properties file and provides typed access methods

### Configuration Classes

**Configuration Definition Classes** (in `server-common/src/main/java/org/apache/kafka/server/config/`):
- **`ServerConfigs`** - Core broker configs (broker.id, listeners, etc.)
- **`ServerLogConfigs`** - Log-related configs (log.dirs, log.retention.ms, etc.)
- **`ZkConfigs`** - ZooKeeper connection configs
- **`KRaftConfigs`** - KRaft mode configs
- **`ReplicationConfigs`** - Replication configs
- **`QuotaConfigs`** - Client quota configs

Each defines:
- `CONFIG_NAME` constants (e.g., `"broker.id"`)
- `DEFAULT_VALUE` constants
- `DOC` strings for documentation
- ConfigDef entries

### Configuration Loading

**Properties-based Loading**:
```scala
// In Kafka.scala
val props = Utils.loadProps(args(0))  // Load broker.properties file
val config = KafkaConfig.fromProps(props, doLog = false)
```

**Configuration Validation**:
- During `KafkaConfig` instantiation via `AbstractConfig.validate()`
- ConfigDef performs:
  - Type checking (INT, STRING, LONG, etc.)
  - Range validation
  - Enum value validation
  - Custom validators via ConfigDef entries

### Dynamic Configuration Management

**DynamicBrokerConfig** (`core/src/main/scala/kafka/server/DynamicBrokerConfig.scala`)
- Manages configurations that can be updated without broker restart
- **Key Methods**:
  - `validateConfigs(props: Properties, perBrokerConfig: Boolean)` (lines 142-155)
    - Prevents updating non-dynamic configs
    - Validates security configs have listener prefix
    - Validates config types
  - `addBrokerReconfigurable(reconfigurable: BrokerReconfigurable)` - Register handler for config changes
  - `updateBrokerConfig(clientId: String, brokerConfigs: Properties)` - Apply dynamic config changes

**Dynamic Configuration Sources**:
- ZooKeeper: `/config/brokers/{brokerId}` and `/config/brokers/default`
- Configuration changes trigger handlers registered via `addBrokerReconfigurable()`

**Dynamic Config Validation** (lines 142-155):
```scala
def validateConfigs(props: Properties, perBrokerConfig: Boolean): Unit = {
  checkInvalidProps(nonDynamicConfigs(props), "Cannot update these configs dynamically")
  checkInvalidProps(securityConfigsWithoutListenerPrefix(props),
    "These security configs can be dynamically updated only per-listener using the listener prefix")
  validateConfigTypes(props)
  if (!perBrokerConfig) {
    checkInvalidProps(perBrokerConfigs(props),
      "Cannot update these configs at default cluster level, broker id must be specified")
  }
}
```

### Configuration Registry Location

**Primary Registry**: `server/src/main/java/org/apache/kafka/server/config/AbstractKafkaConfig.java`
- Central `CONFIG_DEF` that merges all config sources
- All brokers must recognize and validate against this

**Broker-Specific Registry**: `core/src/main/scala/kafka/server/KafkaConfig.scala`
- Extends AbstractKafkaConfig for ZK-mode specific features

**Dynamic Configs**: `core/src/main/scala/kafka/server/DynamicConfig.scala`
- Defines which configs are dynamic: `object DynamicConfig.Broker`
- Non-dynamic configs: `nonDynamicProps` (all static configs)

---

## 6. Adding a New Broker Configuration Parameter

### Complete Step-by-Step Process

#### **Step 1: Define the Configuration in the Appropriate Config Class**

**Option A: If it's a general server config** → Add to `server/src/main/java/org/apache/kafka/server/config/ServerConfigs.java`

**Option B: If it's log-related** → Add to `server-common/src/main/java/org/apache/kafka/server/config/ServerLogConfigs.java`

**Example**:
```java
// In ServerLogConfigs.java
public static final String MY_NEW_CONFIG = "my.new.config";
public static final String MY_NEW_CONFIG_DEFAULT = "default_value";
public static final String MY_NEW_CONFIG_DOC = "Description of what this config does";

// In CONFIG_DEF (usually at end of file):
.define(
  MY_NEW_CONFIG,
  ConfigDef.Type.STRING,
  MY_NEW_CONFIG_DEFAULT,
  ConfigDef.Importance.MEDIUM,
  MY_NEW_CONFIG_DOC
)
```

#### **Step 2: Create a Getter in KafkaConfig**

**File**: `core/src/main/scala/kafka/server/KafkaConfig.scala`

```scala
def myNewConfig: String = getConfiguredInstance(ServerLogConfigs.MY_NEW_CONFIG, classOf[String])
// Or for simple types:
def myNewConfig: String = getString(ServerLogConfigs.MY_NEW_CONFIG)
```

#### **Step 3: Determine if Config is Dynamic or Static**

- **Dynamic Config** (can be updated without restart): Add to `DynamicConfig.Broker.brokerConfigs` list
- **Static Config** (requires restart): Leave out of dynamic configs (automatically excluded)

**File**: `core/src/main/scala/kafka/server/DynamicConfig.scala`

```scala
object Broker {
  private val brokerConfigs = AbstractKafkaConfig.CONFIG_DEF // if dynamic
  // Or explicitly list if only some are dynamic
}
```

#### **Step 4: Add Validation (if needed)**

**For Dynamic Configs**: Add validator in `DynamicBrokerConfig`

**File**: `core/src/main/scala/kafka/server/DynamicBrokerConfig.scala`

```scala
// In validateReconfiguration() method
if (newConfigs.containsKey(ServerLogConfigs.MY_NEW_CONFIG)) {
  val value = newConfigs.get(ServerLogConfigs.MY_NEW_CONFIG)
  if (value == null || value.toString.isEmpty) {
    throw new ConfigException(s"${ServerLogConfigs.MY_NEW_CONFIG} cannot be empty")
  }
}
```

**For Custom Type Validation**: Create a validator class

```java
public class MyNewConfigValidator implements ConfigDef.Validator {
  @Override
  public void ensureValid(String name, Object value) {
    if (value != null && !isValid((String) value)) {
      throw new ConfigException(name, value, "Invalid format");
    }
  }
}
```

Then register in ConfigDef:
```java
.define(
  MY_NEW_CONFIG,
  ConfigDef.Type.STRING,
  MY_NEW_CONFIG_DEFAULT,
  new MyNewConfigValidator(),
  ConfigDef.Importance.MEDIUM,
  MY_NEW_CONFIG_DOC
)
```

#### **Step 5: Use the Config in Broker Startup (if applicable)**

**File**: Where the config is used (e.g., `KafkaServer.scala`)

```scala
val myNewValue = config.myNewConfig
// Use the value in broker initialization
someComponent.initialize(myNewValue)
```

#### **Step 6: Handle Dynamic Updates (if dynamic)**

**File**: Create a handler in the appropriate component

```scala
class MyComponentReconfigurable extends BrokerReconfigurable {
  override def reconfigurableConfigs(): util.Set[String] = {
    util.Collections.singleton(ServerLogConfigs.MY_NEW_CONFIG)
  }

  override def validateReconfiguration(configs: KafkaConfig): Unit = {
    // Validation logic
  }

  override def reconfigure(oldConfig: KafkaConfig, newConfig: KafkaConfig): Unit = {
    val newValue = newConfig.myNewConfig
    // Update internal state with new value
  }
}
```

Register in KafkaServer.startup():
```scala
config.dynamicConfig.addBrokerReconfigurable(new MyComponentReconfigurable())
```

#### **Step 7: Write Unit Tests**

**File**: `core/src/test/scala/unit/kafka/server/KafkaConfigTest.scala` or `DynamicBrokerConfigTest.scala`

```scala
@Test
def testMyNewConfig(): Unit = {
  val props = new Properties()
  props.put(ServerLogConfigs.MY_NEW_CONFIG, "test_value")
  val config = KafkaConfig.fromProps(props)
  assertEquals("test_value", config.myNewConfig)
}

@Test
def testMyNewConfigValidation(): Unit = {
  val props = new Properties()
  props.put(ServerLogConfigs.MY_NEW_CONFIG, "invalid")
  assertThrows(classOf[ConfigException], () => KafkaConfig.fromProps(props))
}
```

**For Dynamic Config Updates**:
```scala
@Test
def testDynamicMyNewConfigUpdate(): Unit = {
  val updatedConfigs = new Properties()
  updatedConfigs.put(ServerLogConfigs.MY_NEW_CONFIG, "new_value")
  DynamicConfig.Broker.validate(updatedConfigs) // Should not throw

  // If static config
  assertThrows(classOf[ConfigException], () => DynamicConfig.Broker.validate(updatedConfigs))
}
```

#### **Step 8: Write Integration Tests (if applicable)**

**File**: `core/src/test/scala/integration/kafka/api/SomeIntegrationTest.scala`

```scala
@Test
def testMyNewConfigWithBroker(): Unit = {
  val brokerConfig = TestUtils.createBrokerConfig(0, "localhost")
  brokerConfig.put(ServerLogConfigs.MY_NEW_CONFIG, "test_value")
  val server = new KafkaServer(KafkaConfig.fromProps(brokerConfig))
  server.startup()
  try {
    // Test assertions
    assertEquals("test_value", server.config.myNewConfig)
  } finally {
    server.shutdown()
  }
}
```

#### **Step 9: Documentation**

- Update `docs/configuration.rst` with new config documentation
- Add example in broker.properties template
- Document if the config is dynamic or requires restart

#### **Step 10: Build and Test**

```bash
# Build the specific module
gradle core:build

# Run tests for the module
gradle core:test

# Run integration tests
gradle core:integrationTest

# Generate config documentation
gradle core:run --args 'kafka.server.KafkaConfig'
# This generates HTML documentation
```

### Complete Example: Adding `max.custom.requests`

**1. Add to ServerConfigs.java**:
```java
public static final String MAX_CUSTOM_REQUESTS_CONFIG = "max.custom.requests";
public static final int MAX_CUSTOM_REQUESTS_DEFAULT = 100;
public static final String MAX_CUSTOM_REQUESTS_DOC = "Maximum number of custom requests to allow per second";
```

**2. Add to ConfigDef in ServerConfigs.java**:
```java
.define(
  MAX_CUSTOM_REQUESTS_CONFIG,
  ConfigDef.Type.INT,
  MAX_CUSTOM_REQUESTS_DEFAULT,
  ConfigDef.Range.atLeast(1),
  ConfigDef.Importance.MEDIUM,
  MAX_CUSTOM_REQUESTS_DOC
)
```

**3. Add getter in KafkaConfig.scala**:
```scala
def maxCustomRequests: Int = getInt(ServerConfigs.MAX_CUSTOM_REQUESTS_CONFIG)
```

**4. Make it dynamic (add to dynamic configs)**

**5. Use in KafkaServer**:
```scala
val customRequestLimiter = new CustomRequestLimiter(config.maxCustomRequests)
kafkaScheduler.schedule(...) // Use in scheduler if needed
```

**6. Add tests**:
```scala
@Test
def testMaxCustomRequestsDefault(): Unit = {
  val props = new Properties()
  val config = KafkaConfig.fromProps(props)
  assertEquals(100, config.maxCustomRequests)
}

@Test
def testMaxCustomRequestsCustomValue(): Unit = {
  val props = new Properties()
  props.put(ServerConfigs.MAX_CUSTOM_REQUESTS_CONFIG, "200")
  val config = KafkaConfig.fromProps(props)
  assertEquals(200, config.maxCustomRequests)
}

@Test
def testMaxCustomRequestsValidation(): Unit = {
  val props = new Properties()
  props.put(ServerConfigs.MAX_CUSTOM_REQUESTS_CONFIG, "0") // Invalid
  assertThrows(classOf[ConfigException], () => KafkaConfig.fromProps(props))
}
```

---

## Summary of Key Insights

1. **Modular Architecture**: Kafka separates concerns into broker (core), clients, streams, connect, and coordination layers
2. **Flexible Configuration**: Multi-source config system allows static configs, dynamic configs, and pluggable policies
3. **Async Request Processing**: Request handlers are pooled and can be delayed via purgatory operations
4. **Metadata Management**: MetadataCache keeps an in-memory replica of cluster state for fast lookups
5. **Cluster Coordination**: Controller (ZK mode) or QuorumController (KRaft mode) manages cluster state and leader elections
6. **Log Abstraction**: LogManager abstracts storage with support for local and remote storage
7. **Comprehensive Testing**: Multiple levels of testing from unit to integration with harness classes supporting both ZK and KRaft modes
