# Kafka Contributor Guide

## 1. Build Prerequisites

### Java
Kafka requires Java to build and run. Supported versions are **Java 8, 11, 17, and 21**.

- Java 8 and Java 11 support are **deprecated** and targeted for removal in Kafka 4.0.
- The build sets `-release 8` in javac/scalac so binaries are compatible with Java 8+ regardless of which JDK you compile with.
- For `spotlessApply` and `spotlessCheck` (import ordering), use **JDK 11 or 17** — there is a known issue with Java 21.

### Scala
Kafka supports Scala **2.12** and **2.13**. Scala 2.13 is the default. Scala 2.12 is deprecated and will be removed in Kafka 4.0.

The Scala version used for compilation is controlled by the `-PscalaVersion` Gradle flag.

### Other Tools
- **Git** — for source control.
- **Gradle Wrapper** (`./gradlew`) — bundled in the repo; no separate Gradle installation needed.
- **Maven** — only needed for the Kafka Streams quickstart archetype (`streams/quickstart`).
- **Docker** — optional, needed to run system tests locally via `tests/docker/run_tests.sh`.
- **Python 3 + ducktape** — needed for system/integration test infrastructure (see `tests/README.md`).

### Version Summary
| Tool    | Requirement                         |
|---------|-------------------------------------|
| Java    | 8, 11, 17, or 21 (21 recommended)  |
| Scala   | 2.13 (default), 2.12 (deprecated)  |
| Gradle  | Provided via `./gradlew` wrapper    |
| Docker  | For system tests (optional)         |

---

## 2. Gradle Build System

Kafka uses **Gradle** as its primary build system. Always use the wrapper script `./gradlew` (or `./gradlewAll` for multi-Scala builds) rather than a system-installed Gradle.

### Module Structure

The project is a multi-module Gradle build. All modules are declared in `settings.gradle`. Key modules include:

| Module                    | Description                                     |
|---------------------------|-------------------------------------------------|
| `clients`                 | Kafka client library (producer, consumer, admin) |
| `core`                    | Kafka broker (Scala)                            |
| `connect:api`             | Kafka Connect API                               |
| `connect:runtime`         | Kafka Connect runtime                           |
| `streams`                 | Kafka Streams                                   |
| `server`                  | Server-side logic                               |
| `server-common`           | Shared server utilities                         |
| `metadata`                | Metadata management                             |
| `raft`                    | KRaft consensus module                          |
| `storage`                 | Tiered storage                                  |
| `tools`                   | Command-line tools                              |
| `group-coordinator`       | Group coordination logic                        |
| `transaction-coordinator` | Transaction coordination logic                  |
| `jmh-benchmarks`          | JMH microbenchmarks                             |

### Key Build Commands

```bash
# Build all JARs
./gradlew jar

# Build source JARs
./gradlew srcJar

# Build a specific module's JAR
./gradlew core:jar
./gradlew clients:jar

# Clean the build
./gradlew clean

# List all available Gradle tasks
./gradlew tasks

# Build with a specific Scala version
./gradlew -PscalaVersion=2.12 jar

# Build for ALL supported Scala versions
./gradlewAll jar

# Generate IDE project files (optional; IntelliJ has built-in Gradle support)
./gradlew idea
./gradlew eclipse

# Rebuild auto-generated RPC message classes (useful after branch switches)
./gradlew processMessages processTestMessages

# Build a binary release tarball (output in core/build/distributions/)
./gradlew clean releaseTarGz
```

### Common Build Options (via `-P`)

| Option               | Description                                                  |
|----------------------|--------------------------------------------------------------|
| `scalaVersion`       | Scala version to use, e.g. `-PscalaVersion=2.12`            |
| `maxParallelForks`   | Number of parallel test JVM processes                        |
| `ignoreFailures`     | Continue build even if tests fail                            |
| `enableTestCoverage` | Enable JaCoCo test coverage (adds ~15-20% overhead)         |
| `skipSigning`        | Skip artifact signing                                        |
| `xmlSpotBugsReport`  | Produce XML (instead of HTML) SpotBugs reports              |

---

## 3. Running Tests

### Test Frameworks
- **JUnit 5** — used for unit and integration tests in Java modules.
- **ScalaTest** — used for Scala tests in the `core` module.
- **ducktape** — Python-based framework for system/end-to-end tests (`tests/` directory).

### Unit and Integration Tests

```bash
# Run all tests (unit + integration) across the entire project
./gradlew test

# Run only unit tests
./gradlew unitTest

# Run only integration tests
./gradlew integrationTest

# Force re-run even if no code changed (Gradle caches test results)
./gradlew test --rerun

# Run tests for a specific module
./gradlew clients:test
./gradlew core:test

# Run all Streams tests (Streams has multiple sub-projects)
./gradlew :streams:testAll

# Run a specific test class
./gradlew clients:test --tests RequestResponseTest

# Run a specific test method (fully-qualified)
./gradlew core:test --tests kafka.api.ProducerFailureHandlingTest.testCannotSendToInternalTopic
./gradlew clients:test --tests org.apache.kafka.clients.MetadataTest.testTimeToNextUpdate

# Repeatedly run a test until it fails (useful for flaky test detection)
I=0; while ./gradlew clients:test --tests RequestResponseTest --rerun --fail-fast; do (( I=$I+1 )); echo "Completed run: $I"; sleep 1; done

# Adjust test retries
./gradlew test -PmaxTestRetries=1 -PmaxTestRetryFailures=5
```

### Logging During Tests

To see more detailed logs, edit the module's `src/test/resources/log4j.properties` file before running. For example, in `clients/src/test/resources/log4j.properties`, change the relevant log level line to:

```
log4j.logger.org.apache.kafka=INFO
```

Then run with `cleanTest` to force re-execution:

```bash
./gradlew cleanTest clients:test --tests NetworkClientTest
```

Test result XML files are written to `<module>/build/test-results/test/`.

### Test Coverage Reports

```bash
# Full project coverage report
./gradlew reportCoverage -PenableTestCoverage=true -Dorg.gradle.parallel=false

# Single-module coverage report
./gradlew clients:reportCoverage -PenableTestCoverage=true -Dorg.gradle.parallel=false
```

### System Tests (End-to-End)

System tests use **ducktape** and run against a cluster of Docker containers or VMs.

```bash
# Build system test libraries first
./gradlew clean systemTestLibs

# Run all system tests via Docker
bash tests/docker/run_tests.sh

# Run a specific test file
TC_PATHS="tests/kafkatest/tests/client/pluggable_test.py" bash tests/docker/run_tests.sh

# Run a specific test class
TC_PATHS="tests/kafkatest/tests/client/pluggable_test.py::PluggableConsumerTest" bash tests/docker/run_tests.sh

# Run a specific test method
TC_PATHS="tests/kafkatest/tests/client/pluggable_test.py::PluggableConsumerTest.test_start_stop" bash tests/docker/run_tests.sh

# Run tests with a different JVM
bash tests/docker/ducker-ak up -j 'openjdk:11'; tests/docker/run_tests.sh
```

---

## 4. CI Pipeline

### CI Systems

Kafka uses **two CI systems**:

1. **Jenkins** — primary CI for Java/Scala builds and tests.
   - Config file: `/workspace/Jenkinsfile`
   - Hosted at the Apache Software Foundation Jenkins instance.

2. **GitHub Actions** — used for Docker image build, test, scanning, and stale PR management.
   - Config files: `.github/workflows/`

### Jenkins Pipeline (`Jenkinsfile`)

The Jenkins pipeline runs **four parallel build stages**, one per supported JDK version:

| Stage                    | JDK | Scala | What runs                               |
|--------------------------|-----|-------|-----------------------------------------|
| JDK 8 and Scala 2.12    | 8   | 2.12  | Validation + full tests + Streams archetype |
| JDK 11 and Scala 2.13   | 11  | 2.13  | Validation + tests (on dev branch only) |
| JDK 17 and Scala 2.13   | 17  | 2.13  | Validation + tests (on dev branch only) |
| JDK 21 and Scala 2.13   | 21  | 2.13  | Validation + full tests                 |

Each stage has an **8-hour timeout**.

**Validation step** runs:
```bash
./retry_zinc ./gradlew -PscalaVersion=$SCALA_VERSION clean check -x test \
    --profile --continue -PxmlSpotBugsReport=true -PkeepAliveMode="session"
```
This runs all `check` tasks **except** `test`, which includes Checkstyle, SpotBugs, Spotless, and compilation.

**Test step** runs:
```bash
./gradlew -PscalaVersion=$SCALA_VERSION test \
    --profile --continue -PkeepAliveMode="session" \
    -PtestLoggingEvents=started,passed,skipped,failed \
    -PignoreFailures=true -PmaxParallelForks=2 \
    -PmaxTestRetries=1 -PmaxTestRetryFailures=10
```

JUnit XML results are collected from `**/build/test-results/**/TEST-*.xml`.

Build notifications (for dev branch failures) are emailed to `dev@kafka.apache.org`.

### GitHub Actions (`.github/workflows/`)

| Workflow file                              | Purpose                                       |
|--------------------------------------------|-----------------------------------------------|
| `docker_build_and_test.yml`               | Build and test Docker images                  |
| `docker_official_image_build_and_test.yml`| Build/test Docker Hub official images         |
| `docker_promote.yml`                      | Promote Docker images                         |
| `docker_rc_release.yml`                   | Docker release candidate builds               |
| `docker_scan.yml`                         | Security scanning of Docker images            |
| `prepare_docker_official_image_source.yml`| Prepare Docker source for official images     |
| `stale.yml`                               | Auto-labels PRs stale after 90 days of inactivity |

### Code Quality Checks

Run these locally before submitting a PR:

```bash
# Checkstyle (Java style enforcement)
./gradlew checkstyleMain checkstyleTest

# Spotless (import ordering — use JDK 11 or 17, NOT 21)
./gradlew spotlessCheck       # check only
./gradlew spotlessApply       # auto-fix imports

# SpotBugs (static bug analysis)
./gradlew spotbugsMain spotbugsTest -x test

# Run all checks at once (mirrors CI validation step)
./gradlew checkstyleMain checkstyleTest spotlessCheck
```

Checkstyle configuration lives in `checkstyle/checkstyle.xml`. Reports are written to `<module>/reports/checkstyle/` and `<module>/reports/spotbugs/`.

---

## 5. Code Review Process

### Finding and Claiming a JIRA Ticket

1. Browse open issues at **https://issues.apache.org/jira/browse/KAFKA**.
2. Filter by `Status = Open` and look for issues tagged `newbie` or `newbie++` if you are just getting started.
3. Comment on the issue to express interest, then ask a committer to assign it to you (or self-assign if you have permissions).
4. There are no strict branch naming conventions enforced by tooling — use descriptive names like `fix/KAFKA-12345-some-description` or `feature/KAFKA-XXXXX-description` by convention.

### Submitting a Pull Request

1. Fork the Apache Kafka repository on GitHub (or work from your own branch on a fork).
2. Make your changes in a feature branch.
3. Before opening the PR:
   - Run `./gradlew spotlessApply` (with JDK 11 or 17) to fix import ordering.
   - Run `./gradlew checkstyleMain checkstyleTest spotlessCheck` to catch style issues.
   - Run the relevant tests (`./gradlew <module>:test`).
4. Open a pull request against the `trunk` branch (the main development branch) on GitHub.
5. The PR title and description become the squashed commit message — make them clear and informative.
6. Fill in the PR template (`PULL_REQUEST_TEMPLATE.md`), which asks for:
   - A description of the change.
   - A summary of the testing strategy.

### Code Review Expectations

- **Reviewers**: Any community member can review, but a **committer** must approve and merge.
- **Committer Checklist** (from `PULL_REQUEST_TEMPLATE.md`):
  - Verify design and implementation.
  - Verify test coverage and CI build status.
  - Verify documentation (including upgrade notes).
- **Tests**: Unit and/or integration tests are expected for any behavior change. System tests should be considered for larger changes.
- **Stale PRs**: PRs with no activity for 90 days are automatically labeled `stale` by a GitHub Actions bot. If no activity occurs within 30 more days, the PR may be closed.
- **Formatting**: Import ordering is enforced via Spotless. Run `./gradlew spotlessApply` before every PR.
- **Communication**: Ping reviewers with a comment on the PR (not in the PR description, which becomes the commit message).

### Key Resources
- Contributing guide: https://kafka.apache.org/contributing.html
- Contributing code changes (wiki): https://cwiki.apache.org/confluence/display/KAFKA/Contributing+Code+Changes
- JIRA: https://issues.apache.org/jira/browse/KAFKA
- Mailing lists: https://kafka.apache.org/contact.html

---

## 6. Developer Workflow Example

Here is a complete step-by-step example for fixing a bug in the `clients` module.

### Step 1: Find a JIRA Issue

1. Go to https://issues.apache.org/jira/browse/KAFKA.
2. Filter by `newbie` label to find beginner-friendly issues.
3. Comment: "I'd like to work on this" and wait for assignment, or self-assign if you have JIRA permissions.

### Step 2: Set Up Your Environment

```bash
# Fork the repo on GitHub, then clone your fork
git clone https://github.com/<your-username>/kafka.git
cd kafka

# Add the upstream remote
git remote add upstream https://github.com/apache/kafka.git

# Verify Java version (use 17 for best compatibility)
java -version

# Verify the build works before making changes
./gradlew clients:jar
```

### Step 3: Create a Feature Branch

```bash
git fetch upstream
git checkout -b fix/KAFKA-12345-fix-metadata-timeout upstream/trunk
```

### Step 4: Make Your Change

Edit the relevant source files in the `clients/src/main/java/` directory.

### Step 5: Run Code Quality Checks

```bash
# Fix import ordering (requires JDK 11 or 17)
./gradlew spotlessApply

# Check style
./gradlew clients:checkstyleMain clients:checkstyleTest
```

### Step 6: Write or Update Tests

Add or update tests in `clients/src/test/java/`. Run the tests to confirm they pass:

```bash
# Run all tests in the clients module
./gradlew clients:test

# Run just your specific test class
./gradlew clients:test --tests org.apache.kafka.clients.MetadataTest

# Run a specific method
./gradlew clients:test --tests org.apache.kafka.clients.MetadataTest.testTimeToNextUpdate
```

### Step 7: Run a Broader Check

```bash
# Run all check tasks (mirrors CI validation), excluding tests for speed
./gradlew clients:check -x test

# Or run the full check suite
./gradlew checkstyleMain checkstyleTest spotlessCheck
```

### Step 8: Push and Open a Pull Request

```bash
git add <changed files>
git commit -m "KAFKA-12345: Fix metadata timeout in clients"
git push origin fix/KAFKA-12345-fix-metadata-timeout
```

Open a PR on GitHub against the `trunk` branch. In the PR description:

```
Fix metadata timeout when broker is unreachable.

Previously, the client would hang indefinitely due to missing timeout
handling in MetadataUpdater. This commit adds a configurable timeout
and throws TimeoutException after the deadline is exceeded.

Testing: Added unit test `MetadataTest.testTimeToNextUpdate` to cover
the new timeout path.
```

### Step 9: Address Review Feedback

- Monitor the PR for CI results and reviewer comments.
- Push additional commits to address feedback — do not squash until a committer asks.
- A committer will squash and merge your PR once it is approved.

### Step 10: After Merge

- Close the JIRA issue if it was not auto-closed.
- Sync your fork:

```bash
git fetch upstream
git checkout trunk
git merge upstream/trunk
```

---

*Generated from the Apache Kafka 3.9.0 source tree at `/workspace`.*
