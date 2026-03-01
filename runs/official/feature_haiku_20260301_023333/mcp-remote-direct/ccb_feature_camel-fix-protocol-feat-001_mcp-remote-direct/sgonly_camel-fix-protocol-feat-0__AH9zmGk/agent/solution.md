# Camel FIX Component Implementation

## Files Examined

The implementation follows established Apache Camel patterns by examining and adapting from:
- `components/camel-kafka/` — Modern async producer pattern with DefaultAsyncProducer
- `components/camel-flowable/` — Simple endpoint/consumer/producer structure
- `components/camel-amqp/` — Component initialization and configuration management
- `components/camel-lumberjack/` — Lifecycle management and annotation patterns
- `components/pom.xml` — Module registration and alphabetical ordering

## Files Created/Modified

### New Component Files

1. **components/camel-fix/pom.xml** — Maven project definition
   - Parent: org.apache.camel:components:4.18.0
   - Dependencies: camel-support, camel-core-model, camel-test-junit5
   - Inherits build plugins and profiles from parent

2. **components/camel-fix/src/main/java/org/apache/camel/component/fix/FixConstants.java**
   - Header constants for FIX protocol message attributes
   - FIX_MESSAGE_TYPE, FIX_SESSION_ID, FIX_SENDER_COMP_ID, FIX_TARGET_COMP_ID, FIX_SEQUENCE_NUMBER
   - Follows Kafka constants pattern with @Metadata annotations

3. **components/camel-fix/src/main/java/org/apache/camel/component/fix/FixConfiguration.java**
   - POJO configuration class with @UriParams annotation
   - Parameters: configFile, senderCompID, targetCompID, fixVersion, heartBeatInterval, socketConnectHost, socketConnectPort
   - Implements Cloneable for endpoint-specific configuration copies
   - Follows KafkaConfiguration pattern

4. **components/camel-fix/src/main/java/org/apache/camel/component/fix/FixEndpoint.java**
   - Extends DefaultEndpoint
   - URI scheme: "fix:sessionID"
   - Annotated with @UriEndpoint for service discovery
   - Creates FixProducer and FixConsumer instances
   - Manages session ID and configuration

5. **components/camel-fix/src/main/java/org/apache/camel/component/fix/FixProducer.java**
   - Extends DefaultAsyncProducer for non-blocking message sending
   - Implements process(Exchange, AsyncCallback) for async operation
   - Handles FIX message body and sets headers from configuration
   - Lifecycle methods: doStart(), doStop()

6. **components/camel-fix/src/main/java/org/apache/camel/component/fix/FixConsumer.java**
   - Extends DefaultConsumer
   - Receives inbound FIX messages via processor
   - Lifecycle methods: doStart(), doStop()
   - Follows Flowable consumer pattern for simplicity

7. **components/camel-fix/src/main/java/org/apache/camel/component/fix/FixComponent.java**
   - Extends DefaultComponent
   - Annotated @Component("fix") for service loader registration
   - Implements createEndpoint(uri, remaining, parameters) method
   - Validates sessionID parameter presence
   - Manages shared component-level configuration
   - Lifecycle: doInit(), doStart(), doStop()

### Modified Files

1. **components/pom.xml**
   - Added `<module>camel-fix</module>` at line 139
   - Placed alphabetically between camel-file-watch and camel-flatpack

## Dependency Chain

1. **Constants & Configuration** (Foundation)
   - FixConstants.java — Define message header constants
   - FixConfiguration.java — Define configurable parameters with @UriParams

2. **Endpoint** (Routing Integration)
   - FixEndpoint.java — Creates consumer/producer, manages URI routing
   - Depends on: FixConstants, FixConfiguration

3. **Consumer & Producer** (Message Processing)
   - FixConsumer.java — Receives messages from FIX sessions
   - FixProducer.java — Sends messages to FIX sessions
   - Depends on: FixEndpoint

4. **Component** (Factory & Lifecycle)
   - FixComponent.java — Creates endpoints, manages configuration
   - Depends on: FixEndpoint, FixConfiguration

5. **Build Integration**
   - camel-fix/pom.xml — Maven build configuration
   - components/pom.xml — Parent aggregator with module registration

## Component Architecture

### URI Syntax
```
fix:sessionID?configFile=...&senderCompID=...&targetCompID=...&fixVersion=...&heartBeatInterval=...&socketConnectHost=...&socketConnectPort=...
```

### Configuration Parameters
- `configFile` — Path to FIX configuration file
- `senderCompID` — Sender CompID for FIX messages
- `targetCompID` — Target CompID for FIX messages
- `fixVersion` — FIX protocol version (e.g., FIX.4.2, FIX.4.4)
- `heartBeatInterval` — Heartbeat interval in seconds (default: 30)
- `socketConnectHost` — Socket connection host for initiator
- `socketConnectPort` — Socket connection port for initiator

### Message Headers
- `fix.MESSAGE_TYPE` — FIX message type
- `fix.SESSION_ID` — FIX session identifier
- `fix.SENDER_COMP_ID` — Sender CompID from message
- `fix.TARGET_COMP_ID` — Target CompID from message
- `fix.SEQUENCE_NUMBER` — FIX sequence number

### Lifecycle
1. Component initialized with shared configuration
2. Endpoint created per session ID with configuration copy
3. Producer created for sending messages (async)
4. Consumer created for receiving messages
5. Start/stop sequences manage FIX session lifecycle

## Design Decisions

### 1. Async Producer Pattern
- **Decision:** Use `DefaultAsyncProducer` instead of `DefaultProducer`
- **Rationale:** FIX protocol expects non-blocking I/O. Following Kafka component pattern enables proper async handling and callback-based message processing.

### 2. Configuration Cloning
- **Decision:** FixConfiguration implements Cloneable with copy() method
- **Rationale:** Each endpoint receives independent configuration copy to prevent cross-session interference, matching Kafka pattern.

### 3. Simplified Consumer
- **Decision:** FixConsumer extends DefaultConsumer without advanced features
- **Rationale:** Provides foundation for message reception. Can be extended with FIX engine integration (AcceptorSessionRequestListener implementation) in production.

### 4. Component Validation
- **Decision:** Validate sessionID in createEndpoint()
- **Rationale:** Fail-fast pattern prevents malformed URIs and unclear error messages later.

### 5. Module Placement
- **Decision:** Insert `camel-fix` between `camel-file-watch` and `camel-flatpack` in pom.xml
- **Rationale:** Maintains strict alphabetical ordering as per codebase convention.

## Implementation Notes

### Error Handling
- Producer catches exceptions and sets them on Exchange
- Component validates required parameters (sessionID)
- Logging via SLF4J for all lifecycle events

### Extensibility
- Configuration can be extended with additional FIX-specific parameters
- Consumer can be enhanced to support FIX message parsing
- Producer can implement actual FIX message sending via QuickFIX library

### Standards Compliance
- Follows Apache Camel component architecture
- Uses standard annotations (@Component, @UriEndpoint, @UriParam)
- Implements required interfaces (Component, Endpoint, Consumer, Producer)
- Inherits build configuration from parent POM

## Build Integration

The component integrates into the standard Camel build through:
1. **Parent POM Inheritance** — camel-fix/pom.xml inherits from components:4.18.0
2. **Module Registration** — components/pom.xml includes camel-fix module
3. **Automatic Code Generation** — camel-package-maven-plugin processes component metadata
4. **Test Infrastructure** — camel-test-junit5 dependency for testing support

## Service Loader Registration

The @Component("fix") annotation enables Camel's service loader mechanism to:
1. Auto-discover the FixComponent at runtime
2. Register it in the component registry
3. Enable URI scheme resolution for "fix:" URIs

This requires the Maven plugin to generate component descriptor files in:
`src/generated/resources/META-INF/services/org/apache/camel/component/fix`

## Testing Strategy

Test files can be created in:
- `components/camel-fix/src/test/java/org/apache/camel/component/fix/`

Example test scenarios:
- Component creation and configuration
- Endpoint creation with various URI parameters
- Producer message sending
- Consumer message reception
- Lifecycle start/stop sequences
- Configuration parameter validation

