# Kafka Contributor Guide

## 1. Build Prerequisites

**Java** is the primary requirement. Kafka is built and tested with Java 8, 11, 17, and 21. The build targets Java 8 bytecode compatibility (`release=8` in javac/scalac). Deprecation notes:
- Java 8 support is deprecated since Kafka 3.0 (removal planned in Kafka 4.0 per KIP-750)
- Java 11 broker/tools support deprecated since Kafka 3.7 (removal planned in Kafka 4.0 per KIP-1013)
- **Recommended**: Use Java 11 or 17 for development (Java 21 has a known issue with `spotlessApply`/`spotlessCheck`)

**Scala** is required for certain modules (the `core` broker, `streams`, etc.):
- Scala 2.13 is the default (version `2.13.14` as of 3.9.0)
- Scala 2.12 is still supported but deprecated since Kafka 3.0 (removal planned in Kafka 4.0 per KIP-751)
- Scala itself does **not** need to be installed separately — Gradle downloads it automatically

**Gradle** is the build tool, invoked via the `./gradlew` wrapper — no separate Gradle installation needed.

**Maven** is only needed for the Kafka Streams quickstart archetype (`streams/quickstart`) — not for the main build.

**Git** is required for cloning the repository.

Summary of required tools:

| Tool | Version |
|------|---------|
| Java (JDK) | 11 or 17 recommended; 8, 11, 17, 21 all supported |
| Scala | Not needed separately; downloaded by Gradle |
| Gradle | Not needed separately; use `./gradlew` wrapper |
| Maven | Only for Streams quickstart archetype |
| Git | Any modern version |

---

## 2. Gradle Build System

Kafka uses Gradle as its build system. The `./gradlew` wrapper script handles downloading the correct Gradle version automatically — just invoke it directly from the repository root.

### Module Structure

The project is a multi-module Gradle build. All modules are declared in `settings.gradle`. Key modules:

| Module | Description |
|--------|-------------|
| `clients` | Java client library |
| `core` | Scala broker core |
| `connect:api`, `connect:runtime`, etc. | Kafka Connect framework |
| `streams` | Kafka Streams library |
| `storage`, `storage:api` | Storage layer |
| `raft` | Raft consensus implementation |
| `metadata` | Metadata management |
| `server`, `server-common` | Server-side components |
| `group-coordinator` | Consumer group coordination |
| `transaction-coordinator` | Transaction management |
| `tools`, `tools:tools-api` | Admin/CLI tools |
| `jmh-benchmarks` | JMH microbenchmarks |
| `trogdor` | Distributed fault injection framework |

### Key Gradle Commands

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

# Clean and build a release tar.gz
./gradlew clean releaseTarGz
# Output: ./core/build/distributions/

# List all available Gradle tasks
./gradlew tasks

# Build IDE project files (usually not needed; IntelliJ supports Gradle natively)
./gradlew idea    # IntelliJ IDEA
./gradlew eclipse # Eclipse

# Build auto-generated RPC message code (useful when switching branches)
./gradlew processMessages processTestMessages

# Use a specific Scala version (default is 2.13)
./gradlew -PscalaVersion=2.12 jar

# Build/test against ALL supported Scala versions
./gradlewAll jar
./gradlewAll test
```

### Key Build Options (`-P` flags)

| Option | Description |
|--------|-------------|
| `maxParallelForks=N` | Number of parallel test JVM processes (default: CPU count) |
| `scalaVersion=2.12` | Override Scala version |
| `ignoreFailures=true` | Continue even if tests fail |
| `showStandardStreams=true` | Print test stdout/stderr to console |
| `testLoggingEvents=started,passed,skipped,failed` | Control test event logging |
| `maxTestRetries=N` | Max retries per failing test (default: 1) |
| `maxTestRetryFailures=N` | Max failures before disabling retries (default: 5) |
| `enableTestCoverage=true` | Enable JaCoCo test coverage (~15-20% overhead) |
| `xmlSpotBugsReport=true` | Generate XML SpotBugs report instead of HTML |

---

## 3. Running Tests

Kafka uses JUnit as the test framework. Tests are split into **unit tests** and **integration tests**, and there are also Python-based **system tests** for end-to-end scenarios.

### Run All Tests (Unit + Integration)

```bash
./gradlew test
```

### Run Only Unit Tests or Only Integration Tests

```bash
./gradlew unitTest
./gradlew integrationTest
```

### Force Re-run Without Code Changes

```bash
./gradlew test --rerun
./gradlew unitTest --rerun
./gradlew integrationTest --rerun
```

### Run Tests for a Specific Module

```bash
./gradlew clients:test
./gradlew core:test
./gradlew :streams:testAll   # Streams has multiple sub-projects
```

### Run a Single Test Class

```bash
./gradlew clients:test --tests RequestResponseTest
```

### Run a Single Test Method

```bash
./gradlew core:test --tests kafka.api.ProducerFailureHandlingTest.testCannotSendToInternalTopic
./gradlew clients:test --tests org.apache.kafka.clients.MetadataTest.testTimeToNextUpdate
```

### Repeatedly Run a Test (for Flakiness Detection)

```bash
I=0; while ./gradlew clients:test --tests RequestResponseTest --rerun --fail-fast; do (( I=$I+1 )); echo "Completed run: $I"; sleep 1; done
```

### Run Tests With Verbose Logging

Edit the module's `src/test/resources/log4j.properties` to increase log level, then:

```bash
./gradlew cleanTest clients:test --tests NetworkClientTest
```

Logs appear under `clients/build/test-results/test/`.

### Test Coverage Reports

```bash
# Whole project
./gradlew reportCoverage -PenableTestCoverage=true -Dorg.gradle.parallel=false

# Single module
./gradlew clients:reportCoverage -PenableTestCoverage=true -Dorg.gradle.parallel=false
```

### System Tests (Python-based, end-to-end)

System tests live in the `tests/` directory and use the Ducktape framework. They require running Kafka clusters and are **not** part of the standard Gradle test run. See `tests/README.md` for setup instructions.

### Code Quality Checks

These run as part of CI and must pass before submitting a PR:

```bash
# Checkstyle + Spotless import order check (use JDK 11 or 17, NOT 21)
./gradlew checkstyleMain checkstyleTest spotlessCheck

# Fix import ordering automatically (use JDK 11 or 17, NOT 21)
./gradlew spotlessApply

# SpotBugs static analysis
./gradlew spotbugsMain spotbugsTest -x test
```

Reports are written to `reports/checkstyle/` and `reports/spotbugs/` under each subproject's `build/` directory.

---

## 4. CI Pipeline

### Jenkins (Primary CI)

Kafka's main CI pipeline is **Jenkins**, configured in `Jenkinsfile` at the repository root. It runs on the Apache Software Foundation's Jenkins infrastructure.

The pipeline runs **4 parallel build stages**, each on an Ubuntu agent with a different JDK/Scala combination:

| Stage | JDK | Scala | Full Tests |
|-------|-----|-------|------------|
| JDK 8 and Scala 2.12 | JDK 8 | 2.12 | Yes (+ Streams archetype) |
| JDK 11 and Scala 2.13 | JDK 11 | 2.13 | On trunk only |
| JDK 17 and Scala 2.13 | JDK 17 | 2.13 | On trunk only |
| JDK 21 and Scala 2.13 | JDK 21 | 2.13 | Yes |

Each stage runs two phases:
1. **Validation** — `./gradlew clean check -x test` (Checkstyle, SpotBugs, Spotless, compilation)
2. **Tests** — `./gradlew test` with `maxParallelForks=2`, retries enabled, results published as JUnit XML

For PR builds, the JDK 11 and JDK 17 stages skip the test run and only run validation. Full tests run on trunk commits.

The JDK 8 stage also verifies the Kafka Streams quickstart Maven archetype compiles end-to-end.

Each stage has an **8-hour timeout**. Concurrent builds for the same PR are automatically aborted in favor of the newest push.

On trunk build failures, an email notification is sent to `dev@kafka.apache.org`.

### GitHub Actions (Docker Only)

GitHub Actions workflows under `.github/workflows/` are used exclusively for Docker image tasks:
- `docker_build_and_test.yml` — Build and test Docker images
- `docker_official_image_build_and_test.yml` — Official Docker Hub image builds
- `docker_scan.yml` — Security scanning of Docker images
- `docker_promote.yml`, `docker_rc_release.yml` — Release promotion

GitHub Actions is **not** used for code compilation or JVM test runs.

### Gradle Enterprise

Build scans are published to `https://ge.apache.org` for every build, providing detailed diagnostics for troubleshooting failures.

---

## 5. Code Review Process

### Finding and Claiming a JIRA Ticket

1. Go to the Apache Kafka JIRA: https://issues.apache.org/jira/browse/KAFKA
2. Browse open issues. Filter by label `newbie` or `starter` for good first contributions
3. Comment on the ticket to express your intent to work on it (this informally "claims" it — there is no formal assignment for external contributors)

### Branch Naming

Kafka does not enforce a specific branch naming convention. Common practice is to use a descriptive name that includes the JIRA ticket ID:

```
fix/KAFKA-12345-describe-the-bug
feature/KAFKA-12345-short-description
KAFKA-12345
```

### Creating a Pull Request

1. Fork `apache/kafka` on GitHub
2. Create a branch from the `trunk` branch (the main development branch)
3. Make your changes and push to your fork
4. Open a pull request against `apache/kafka:trunk`
5. The PR title and description become the **squashed commit message** — write them carefully

**Before opening a PR**, review:
- https://kafka.apache.org/contributing.html
- https://cwiki.apache.org/confluence/display/KAFKA/Contributing+Code+Changes

### PR Template

The PR template (`PULL_REQUEST_TEMPLATE.md`) asks for:
- A detailed description of the change
- A testing strategy summary (unit, integration, and/or system tests expected for any behavior change)

The **Committer Checklist** is for reviewers only (not part of the commit message):
- [ ] Verify design and implementation
- [ ] Verify test coverage and CI build status
- [ ] Verify documentation (including upgrade notes)

### Code Review Expectations

- Unit and/or integration tests are **expected for any behavior change**
- System tests should be considered for larger changes
- Code must pass **Checkstyle**, **SpotBugs**, and **Spotless** (CI enforces this)
- Run `./gradlew spotlessApply` (with JDK 11 or 17) before submitting to fix import ordering
- Kafka committers will review; iterate on feedback until approved
- Once approved, a committer squash-merges the PR
- For major changes, a KIP (Kafka Improvement Proposal) on the Confluence wiki and discussion on the mailing list is required first

---

## 6. Developer Workflow Example

Here is a complete end-to-end workflow for fixing a bug in the `clients` module:

```bash
# 1. Clone your fork (or the upstream repo for read access)
git clone https://github.com/YOUR_GITHUB_USER/kafka.git
cd kafka
git remote add upstream https://github.com/apache/kafka.git

# 2. Ensure you have JDK 11 or 17 installed and JAVA_HOME set
java -version

# 3. Sync with upstream and create a branch for your fix
git fetch upstream
git checkout trunk
git reset --hard upstream/trunk
git checkout -b fix/KAFKA-XXXXX-fix-metadata-timeout

# 4. Build the relevant module to confirm everything compiles
./gradlew clients:jar

# 5. (If needed) Regenerate auto-generated RPC messages
./gradlew processMessages processTestMessages

# 6. Make your code changes in the relevant source files

# 7. Run the specific failing test to verify your fix works
./gradlew clients:test --tests org.apache.kafka.clients.MetadataTest.testTimeToNextUpdate

# 8. Run the full module test suite to check for regressions
./gradlew clients:test

# 9. Fix import ordering before submitting (requires JDK 11 or 17)
./gradlew spotlessApply

# 10. Run all code quality checks locally
./gradlew checkstyleMain checkstyleTest spotlessCheck -x test
./gradlew spotbugsMain spotbugsTest -x test

# 11. Commit your changes with a clear message referencing the JIRA ticket
git add -p   # Stage changes selectively
git commit -m "KAFKA-XXXXX: Fix metadata refresh timeout when broker is unavailable"

# 12. Push to your fork
git push origin fix/KAFKA-XXXXX-fix-metadata-timeout

# 13. Open a pull request on GitHub:
#     Base: apache/kafka:trunk
#     Compare: YOUR_GITHUB_USER/kafka:fix/KAFKA-XXXXX-fix-metadata-timeout
#     - Write a clear title: "KAFKA-XXXXX: Fix metadata refresh timeout..."
#     - Describe what you changed, why, and how you tested it
#     - Mention the JIRA ticket URL

# 14. Wait for CI (Jenkins) to run — it checks validation + tests
#     Monitor results and fix any CI failures

# 15. Respond to reviewer feedback with additional commits
git add -p
git commit -m "Address review: improve error message clarity"
git push origin fix/KAFKA-XXXXX-fix-metadata-timeout

# 16. A committer will squash-merge the PR once approved
#     The PR title + description become the final commit message
```

### Tips for Success

- **Keep PRs small and focused** — one fix or one feature per PR makes review easier
- **Reference the JIRA ticket** in the PR title (e.g., `KAFKA-12345: ...`)
- **Check the JIRA for existing discussion** — there may be design context that shapes the right approach
- **Write tests** — reviewers will always ask for them if missing
- **Run quality checks locally** before pushing to avoid avoidable CI failures:
  ```bash
  ./gradlew checkstyleMain checkstyleTest spotlessCheck spotbugsMain -x test
  ./gradlew clients:test   # or whichever module you changed
  ```
- **Subscribe to `dev@kafka.apache.org`** to follow ongoing design discussions
- **For large features**, start a KIP (Kafka Improvement Proposal) discussion on the mailing list before writing code — this avoids wasted effort on designs that may not be accepted
