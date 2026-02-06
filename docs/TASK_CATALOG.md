# CodeContextBench Task Catalog

A detailed reference for every benchmark task in CodeContextBench. This document covers all 13 benchmark suites totaling 156 tasks.

**Selection methodology:** Tasks were chosen via stratified sampling across benchmarks, covering all SDLC phases. Each task is scored for MCP benefit using a weighted combination of context complexity (0.25), cross-file dependencies (0.30), semantic search potential (0.20), and tool-chain weight (0.25). See `docs/TASK_SELECTION.md` for full scoring methodology.

---

## Table of Contents

1. [K8s Docs (5 tasks)](#1-k8s-docs--kubernetes-documentation-generation)
2. [LargeRepo (4 tasks)](#2-largerepo--large-codebase-feature-implementation)
3. [LoCoBench (25 tasks)](#3-locobench--long-context-understanding)
4. [PyTorch (12 tasks)](#4-pytorch--pytorch-pr-level-tasks)
5. [SWE-bench Pro (36 tasks)](#5-swe-bench-pro--real-world-software-engineering)
6. [SWE-Perf (3 tasks)](#6-swe-perf--performance-optimization)
7. [TAC (6 tasks)](#7-tac--the-agent-company)
8. [CrossRepo (5 tasks)](#8-crossrepo--cross-repository-reasoning)
9. [RepoQA (10 tasks)](#9-repoqa--semantic-code-retrieval)
10. [DIBench (8 tasks)](#10-dibench--dependency-installation)
11. [CodeReview (3 tasks)](#11-codereview--ai-code-review)
12. [DependEval (32 tasks)](#12-dependeval--dependency-ordering)
13. [LinuxFLBench (5 tasks)](#13-linuxflbench--linux-kernel-fault-localization)

---

## 1. K8s Docs -- Kubernetes Documentation Generation

**Focus:** Generate accurate `doc.go` package documentation by reading and inferring from Kubernetes source code.
**Language:** Go | **Repository:** kubernetes/kubernetes | **Time Limit:** 15 min per task

| Task | Difficulty | MCP Score |
|------|-----------|-----------|
| apiserver-doc-001 | hard | 0.925 |
| applyconfig-doc-001 | hard | 0.657 |
| client-go-doc-001 | hard | 0.829 |
| fairqueuing-doc-001 | hard | 0.340 |
| pkg-doc-001 | medium | 0.390 |

### apiserver-doc-001

Generate comprehensive package documentation for `staging/src/k8s.io/apiserver`. The agent must explain the machinery for building Kubernetes-style API servers, covering extension API servers, GenericAPIServer, and key sub-packages (`pkg/server`, `pkg/admission`, `pkg/authentication`, `pkg/authorization`, `pkg/endpoints`, `pkg/registry`). Must also describe preferred alternatives like CRDs and webhooks. Key source files include `pkg/server/genericapiserver.go`, `pkg/admission/interfaces.go`, `pkg/endpoints/installer.go`, and `pkg/registry/generic/registry.go`.

### applyconfig-doc-001

Generate documentation for `staging/src/k8s.io/client-go/applyconfigurations`. Must explain type-safe apply configuration types for Server-Side Apply (SSA), the zero-value problem with standard Go structs, `With*` builder functions, and controller support mechanisms (extract/modify/apply workflow). Should include code examples showing the problem and solution, and explain field managers and conflict resolution patterns.

### client-go-doc-001

Generate documentation for `staging/src/k8s.io/client-go`, the official Kubernetes Go client library. Must document 6+ sub-packages (`kubernetes`, `dynamic`, `discovery`, `rest`, `tools/cache`, `tools/clientcmd`), explain configuration patterns (in-cluster vs out-of-cluster), interacting with API objects, and the controller pattern (informers, listers, workqueues, leader election).

### fairqueuing-doc-001

Generate documentation for `staging/src/k8s.io/apiserver/pkg/util/flowcontrol/fairqueuing/queueset`. Requires understanding the fair queuing algorithm adapted from networking to server request context. Must explain virtual time concepts, mathematical formulas, service time estimation, and divergence bounds. Should include mathematical notation and reference academic fair queuing papers.

### pkg-doc-001

Generate documentation for `pkg/kubelet/cm` (Container Manager). Must explain its purpose, key responsibilities (cgroup management, QoS enforcement, resource allocation), important interfaces (`ContainerManager`), subpackages (`cpumanager`, `memorymanager`, `topologymanager`, `devicemanager`), and platform-specific considerations (Linux vs Windows, cgroup v1 vs v2).

---

## 2. LargeRepo -- Large Codebase Feature Implementation

**Focus:** Implement new features in 1GB+ open-source repositories, requiring deep navigation of distributed code patterns.
**MCP Score:** 0.895 (all tasks) | **Difficulty:** hard (all tasks)

| Task | Language | Repository | Time Limit |
|------|----------|------------|------------|
| big-code-k8s-001 | Go | kubernetes/kubernetes (1.4GB) | 15 min |
| big-code-servo-001 | Rust | servo/servo (1.6GB) | 25 min |
| big-code-trt-001 | Python, C++ | NVIDIA/TensorRT-LLM (1.6GB) | 25 min |
| big-code-vsc-001 | TypeScript | microsoft/vscode (1GB+) | 20 min |

### big-code-k8s-001 -- NoScheduleNoTraffic Taint Effect

Implement a new Node taint effect called `NoScheduleNoTraffic` in Kubernetes that combines two behaviors: (1) prevents new pods from being scheduled on the node (like `NoSchedule`), and (2) removes the node from Service EndpointSlices so it stops receiving traffic. Unlike `NoExecute`, it must NOT evict existing pods. Implementation touches taint effect constants/enums, pod admission logic in the scheduler, endpoint slice controller update logic, and node controller logic. Tests must verify scheduling is blocked, traffic is redirected, and existing pods remain running. The challenge is that taint effect logic is distributed across scheduler, admission controllers, endpoint controller, and node controller packages.

### big-code-servo-001 -- scrollend DOM Event

Add support for the `scrollend` DOM event in the Servo browser engine. The event must fire when scrolling stops on scrollable DOM elements and the window, covering: user-initiated scrolling (with debouncing, e.g. 150ms of no scroll activity), compositor-driven async scrolling (fire on animation completion), and programmatic scrolling (`scrollTo`/`scrollBy`/`scroll` methods). The event must not fire if the scroll position did not actually change. Implementation requires understanding scroll architecture across the browser engine, DOM event system integration, and compositor handling. Must include WPT tests for wheel, keyboard, and programmatic scrolling, with no performance regression.

### big-code-trt-001 -- W4A8_MXFP4_INT8 Quantization Mode

Add support for `W4A8_MXFP4_INT8` quantization mode (4-bit MXFP4 weights with INT8 activations targeting Blackwell GPUs) to TensorRT-LLM. Follow the patterns of the existing `W4A8_MXFP4_FP8` mode. Changes span both Python and C++: add the mode to Python quantization enums, mirror it in C++ enums, update kernel selection logic to route to Blackwell GPU kernels, update validation and constraints (attention backends, KV cache compatibility), update pybind11 bindings, and add tests for model creation, kernel selection, validation, and build-time error handling.

### big-code-vsc-001 -- Fix Stale TypeScript Diagnostics After Git Branch Switch

Fix an issue where VSCode shows stale TypeScript diagnostics in the Problems panel after switching Git branches. Files that no longer have errors still show old errors until manually opened and edited, because the diagnostics pipeline only refreshes on in-editor changes and misses file-on-disk changes from Git operations. The agent must trace the full diagnostics flow from file changes through the extension host to the Problems view, add file system change listeners to the diagnostics pipeline, trigger diagnostics refresh for changed files, clear stale diagnostics for files that no longer exist, and re-run TypeScript/language server analysis for affected files.

---

## 3. LoCoBench -- Long-Context Understanding

**Focus:** Expert-level tasks on synthetically generated codebases with 1M+ tokens across 75-85 files. Tests architectural reasoning, cross-file refactoring, and bug investigation at scale.
**Difficulty:** expert (all tasks) | **Agent Timeout:** 20 min | **Verifier Timeout:** 10 min

| Task Type | Count | MCP Score | SDLC Phase |
|-----------|-------|-----------|------------|
| Architectural Understanding | 9 | 0.940 | Architecture & Design |
| Cross-File Refactoring | 14 | 0.908-0.915 | Implementation (refactoring) |
| Bug Investigation | 2 | 0.865 | Implementation (bug fix) |

### Task Type: Architectural Understanding

These tasks present a large codebase and ask the agent to produce a detailed architectural analysis or migration plan. The agent must identify components, trace data flows, diagnose architectural flaws, and propose redesigns with phased rollout strategies.

**c_api_graphql_expert_079** -- Produce an architectural migration plan from custom IPC to gRPC across a C-based API/GraphQL system. Requires component identification across 84 files (1M tokens), data flow analysis from API Gateway through microservices, migration strategy with phased rollout, and risk assessment.

**c_api_microservice_expert_080** -- Architectural analysis of a C microservice system. Identify service boundaries, communication patterns, and propose improvements.

**c_blockchain_nft_expert_071** -- Analyze the architecture of a C-based blockchain/NFT system. Map consensus mechanisms, transaction processing, and storage layers.

**csharp_data_warehouse_expert_012** -- Analyze a C# data warehouse system architecture. Identify ETL pipelines, storage patterns, and query optimization strategies.

**python_data_streaming_expert_085** -- Analyze a Python data streaming architecture. Map producer-consumer patterns, buffering strategies, and fault tolerance.

**python_desktop_development_expert_021** -- Analyze a Python desktop application architecture. Identify UI framework patterns, event handling, and state management.

**python_game_engine_expert_032** -- Analyze a Python game engine architecture. Map rendering pipelines, physics systems, and entity-component patterns.

**rust_api_microservice_expert_008** -- Diagnose a stale data issue in a Rust API microservice. The agent must identify the root cause (missing cache invalidation on writes), trace the read/write paths through obfuscated filenames, and design an explicit invalidation strategy with specific module modifications.

**rust_data_streaming_expert_013** -- Analyze a Rust data streaming system architecture. Map async processing patterns, backpressure mechanisms, and error recovery.

### Task Type: Cross-File Refactoring

These tasks require the agent to create new abstractions, extract common patterns, and refactor code across many files while maintaining all existing tests.

**c_api_graphql_expert_079** -- Refactor service-level error handling into a unified common library. Create `sc_error_t` abstraction with structured error type, `sc_service_domain_t` enum, factory functions (`sc_error_create`, `sc_error_destroy`). Refactor palette-service and texture-service, update API Gateway, ensure memory safety.

**c_api_microservice_expert_080** -- Extract common microservice patterns into shared libraries across C codebase.

**c_blockchain_nft_expert_071** -- Refactor blockchain consensus code to support pluggable consensus strategies.

**cpp_web_blog_expert_040** -- Refactor a C++ web/blog platform across multiple files.

**csharp_data_warehouse_expert_012** -- Refactor data warehouse ETL pipeline code for better modularity.

**python_data_streaming_expert_085** -- Refactor streaming pipeline to use abstract interfaces.

**python_desktop_development_expert_021** -- Refactor desktop app to decouple UI from business logic.

**python_game_engine_expert_032** -- Abstract the physics engine for pluggability. Create `AbstractPhysicsSimulator` interface, decouple game loop from concrete physics implementation, implement dependency injection, maintain all existing functionality.

**rust_api_microservice_expert_008** -- Refactor Rust API microservice for better separation of concerns.

**rust_data_streaming_expert_013** -- Refactor Rust data streaming for pluggable transport layers.

**rust_ml_computer_vision_expert_054** -- Refactor ML/computer vision pipeline in Rust.

**rust_web_social_expert_073** -- Refactor a Rust web/social platform.

**typescript_system_monitoring_expert_061** -- Centralize dispersed alerting logic into a unified `NotificationService`. Create `NotificationChannel` interface with `EmailChannel`, `WebhookChannel`, `LogChannel` implementations. Extract hardcoded config to centralized config file, remove legacy code, ensure TypeScript compilation.

### Task Type: Bug Investigation

These tasks present a codebase with a subtle bug and require the agent to find the root cause, identify the exact file and line number, and explain why the bug manifests under specific conditions.

**c_blockchain_nft_expert_071** -- Find root cause of intermittent `INVALID_BLOCK_SIZE` consensus failures that only occur with Delegated Authority (DA) consensus on large governance proposals. The bug is a subtle C error: `sizeof(pointer)` used instead of buffer size in `da_strategy.c` block builder, which doesn't manifest in Proof-of-Stake because it uses a different code path.

**csharp_data_warehouse_expert_012** -- Investigate a data warehouse bug manifesting under specific query patterns.

**rust_web_social_expert_073** -- Investigate a bug in a Rust web/social platform.

---

## 4. PyTorch -- PyTorch PR-Level Tasks

**Focus:** Reproduce actual PyTorch pull request changes -- bug fixes, feature additions, and reverts in the compiler, runtime, and distributed systems.
**Language:** C++ (PyTorch internals) | **Repository:** pytorch/pytorch | **Time Limit:** 10 min per task

| Task | Difficulty | Category | Files | LOC | MCP Score |
|------|-----------|----------|-------|-----|-----------|
| sgt-001 | medium | bug fix | 3 | 94 | 0.536 |
| sgt-002 | medium | bug fix | 4 | 180 | 0.572 |
| sgt-003 | hard | bug fix | 5 | 172 | 0.562 |
| sgt-005 | medium | feature | 4 | 22 | 0.528 |
| sgt-007 | medium | feature | 3 | 393 | 0.584 |
| sgt-009 | medium | bug fix | 3 | 87 | 0.535 |
| sgt-010 | hard | bug fix | 7 | 52 | 0.601 |
| sgt-014 | medium | bug fix | 4 | 242 | 0.584 |
| sgt-016 | medium | bug fix | 3 | 129 | 0.543 |
| sgt-017 | medium | bug fix | 3 | 93 | 0.536 |
| sgt-021 | medium | bug fix | 4 | 59 | 0.548 |
| sgt-024 | medium | bug fix | 3 | 58 | 0.529 |

### sgt-001 -- Thread Safety for ncclCommGetAsyncError

Add thread safety mechanisms (mutexes, locks) to protect `ncclCommGetAsyncError` calls in PyTorch's NCCL process group. Changes span `NCCLUtils.cpp`, `NCCLUtils.hpp`, and `ProcessGroupNCCL.cpp` to prevent concurrent access race conditions (fixes #169484).

### sgt-002 -- Revert Inductor ReLU/GELU Fusion

Revert PR #168157 which added `Activation(Addmm) -> _addmm_activation` pattern replacement in Inductor's lowering pass. The fusion caused regressions in certain model configurations. Remove `_addmm_activation` pattern replacement, pattern matcher registrations for `ReLU(Addmm)` and `GELU(Addmm)`, and cuBLASLt epilogue fusion paths. 93 additions, 87 deletions across 4 files.

### sgt-003 -- Fix Reference Cycles in Failed Dynamo Tracer Outputs

Fix reference cycles in failed dynamo tracer outputs to enable immediate memory reclamation via Python's reference counting instead of requiring full garbage collection. Two cycles must be broken: (1) graph nodes' doubly-linked list cycling back to the graph, and (2) `FakeTensorMode -> ShapeEnv -> TrackedFake -> FakeTensor -> FakeTensorMode` cycle. Must pass 5 specific tests including `test_gc_not_needed_after_cleanup` and `test_repeated_failure_no_leak`.

### sgt-005 -- Enable Shared Memory Pruning for ROCm Triton Configs

Expose `shared_memory_per_block` property for ROCm builds and update Triton template heuristics to use fallback from `shared_memory_per_block_optin`. Enables ROCm GPU config pruning to match existing NVIDIA GPU functionality. 17 additions, 5 deletions across 4 files.

### sgt-007 -- Add Documentation for Symmetric Memory

Add comprehensive documentation for PyTorch's Symmetric Memory feature. This is a large documentation task (386 additions) spread across 3 files, covering the symmetric memory API and its usage patterns in distributed training.

### sgt-009 -- Add Functionalize and Side Effect to HOP Print

Add functionalize and side effect handling to Higher-Order Primitive (HOP) print operations in TorchDynamo. Fixes #167368. 74 additions, 13 deletions across 3 files.

### sgt-010 -- Expose cuDNN Runtime Version in CUDA Hooks

Expose cuDNN runtime version checks (not just compile-time) to dispatching heuristics for SDPA attention and convolution operations. Allows users to resolve version-related issues by updating cuDNN locally. Adds test for 3D convolution performance with cuDNN 9.15+. Touches 7 files (the most in this benchmark set) with 43 additions and 9 deletions.

### sgt-014 -- Fix KeyError in resume_execution and store_attr

Fix `resume_execution` KeyError and `store_attr` issues in TorchDynamo. Fixes #166176, related to stack PR #166036. 153 additions, 89 deletions across 4 files.

### sgt-016 -- Fix Graph Partition Memory Plan Reuse

Fix graph partition memory plan reuse handling. Resolves undefined variable reference errors in generated partition code. Adds `test_graph_partition_with_memory_plan_reuse` test. 126 additions across 3 files.

### sgt-017 -- Move Custom Partition Rules to Inductor Config

Add `custom_should_partition_ops: list[str]` config parameter for graph partitioning on custom ops, moving hardcoded rules into Inductor configuration. Fixes #165341 (cherry-picked from #166458). Net reduction of 9 lines across 3 files.

### sgt-021 -- Revert Relaxed Contiguity for Collective Operations

Revert PR #163712 which relaxed contiguity requirements for allgather/scatter inputs/outputs. The optimization caused regressions in distributed training correctness. Re-adds `.contiguous()` calls for collective operations. 12 additions, 47 deletions across 4 files.

### sgt-024 -- Apply Build Fix for aarch64+cu129

Apply CUDA 12.9 build configuration fix for aarch64 architecture, discovered during aarch64+cu129 build testing (PR #163029). 29 additions, 29 deletions across 3 files.

---

## 5. SWE-bench Pro -- Real-World Software Engineering

**Focus:** Fix real bugs from production open-source repositories. Each task corresponds to an actual GitHub issue and its resolution.
**Difficulty:** hard (all tasks) | **SDLC Phase:** Implementation (bug fix)

### By Repository

| Repository | Language | Tasks | MCP Score Range |
|------------|----------|-------|-----------------|
| NodeBB/NodeBB | JavaScript | 3 | 0.573 - 0.938 |
| ansible/ansible | Python | 5 | 0.476 - 0.698 |
| element-hq/element-web | TypeScript | 2 | 0.493 - 0.805 |
| flipt-io/flipt | Go | 4 | 0.634 - 0.819 |
| future-architect/vuls | Go | 3 | 0.509 - 0.650 |
| gravitational/teleport | Go | 4 | 0.439 - 0.763 |
| internetarchive/openlibrary | Python | 4 | 0.635 - 0.719 |
| navidrome/navidrome | Go | 2 | 0.600 - 0.671 |
| protonmail/webclients | TypeScript | 4 | 0.779 - 0.938 |
| qutebrowser/qutebrowser | Python | 4 | 0.403 - 0.588 |
| tutao/tutanota | TypeScript | 1 | 0.514 |

### NodeBB (JavaScript -- Forum Software)

**NodeBB-76c6e30** (MCP: 0.938) -- Plugin activation accepts invalid plugin identifiers without validation. The plugin system allows malformed identifiers through, requiring validation against naming patterns and clear error messages.

**NodeBB-eb49a64** (MCP: 0.573) -- Bug fix in NodeBB forum software.

**NodeBB-f1a80d4** (MCP: 0.741) -- Bug fix in NodeBB forum software.

### ansible/ansible (Python -- IT Automation)

**ansible-379058e** (MCP: 0.476) -- Bug fix in Ansible automation framework.

**ansible-4c5ce5a** (MCP: 0.698) -- Bug fix in Ansible automation framework.

**ansible-811093f** (MCP: 0.654) -- Bug fix in Ansible automation framework.

**ansible-e40889e** (MCP: 0.654) -- Bug fix in Ansible automation framework.

**ansible-eea46a0** (MCP: 0.633) -- Bug fix in Ansible automation framework.

### element-hq/element-web (TypeScript -- Matrix Chat Client)

**element-web-cf3c899** (MCP: 0.493) -- Bug fix in Element Matrix chat client.

**element-web-f14374a** (MCP: 0.805) -- Bug fix in Element Matrix chat client.

### flipt-io/flipt (Go -- Feature Flag Platform)

**flipt-3d5a345** (MCP: 0.634) -- Bug fix in Flipt feature flag service.

**flipt-9f8127f** (MCP: 0.675) -- Bug fix in Flipt feature flag service.

**flipt-b433bd0** (MCP: 0.819) -- Bug fix in Flipt feature flag service.

**flipt-c188284** (MCP: 0.686) -- Bug fix in Flipt feature flag service.

### future-architect/vuls (Go -- Vulnerability Scanner)

**vuls-1832b4e** (MCP: 0.619) -- Bug fix in Vuls vulnerability scanner.

**vuls-4c04acb** (MCP: 0.509) -- Bug fix in Vuls vulnerability scanner.

**vuls-d18e7a7** (MCP: 0.650) -- Bug fix in Vuls vulnerability scanner.

### gravitational/teleport (Go -- Infrastructure Access)

**teleport-3587cca** (MCP: 0.763) -- Bug fix in Teleport infrastructure access platform.

**teleport-7744f72** (MCP: 0.676) -- Bug fix in Teleport infrastructure access platform.

**teleport-8302d46** (MCP: 0.544) -- Bug fix in Teleport infrastructure access platform.

**teleport-c1b1c6a** (MCP: 0.439) -- Bug fix in Teleport infrastructure access platform.

### internetarchive/openlibrary (Python -- Digital Library)

**openlibrary-7f6b722** (MCP: 0.719) -- Bug fix in Open Library digital catalog.

**openlibrary-92db345** (MCP: 0.676) -- Bug fix in Open Library digital catalog.

**openlibrary-c506c1b** (MCP: 0.635) -- Bug fix in Open Library digital catalog.

**openlibrary-d109cc7** (MCP: 0.654) -- Bug fix in Open Library digital catalog.

### navidrome/navidrome (Go -- Music Server)

**navidrome-9c3b456** (MCP: 0.671) -- Bug fix in Navidrome music streaming server.

**navidrome-d0dceae** (MCP: 0.600) -- Bug fix in Navidrome music streaming server.

### protonmail/webclients (TypeScript -- Encrypted Email)

**webclients-369fd37** (MCP: 0.938) -- Bug fix in Proton Mail web client.

**webclients-8be4f6c** (MCP: 0.869) -- Bug fix in Proton Mail web client.

**webclients-c6f65d2** (MCP: 0.779) -- Bug fix in Proton Mail web client.

**webclients-caf10ba** (MCP: 0.938) -- Bug fix in Proton Mail web client.

### qutebrowser/qutebrowser (Python -- Keyboard-Driven Browser)

**qutebrowser-233cb1c** (MCP: 0.403) -- Bug fix in qutebrowser keyboard-driven web browser.

**qutebrowser-394bfae** (MCP: 0.588) -- Bug fix in qutebrowser keyboard-driven web browser.

**qutebrowser-3fd8e12** (MCP: 0.460) -- Bug fix in qutebrowser keyboard-driven web browser.

**qutebrowser-e5340c4** (MCP: 0.459) -- Bug fix in qutebrowser keyboard-driven web browser.

### tutao/tutanota (TypeScript -- Encrypted Email)

**tutanota-f3ffe17** (MCP: 0.514) -- Bug fix in Tutanota encrypted email platform.

---

## 6. SWE-Perf -- Performance Optimization

**Focus:** Optimize specific functions in major Python scientific computing libraries. Agents must profile, identify bottlenecks, and apply targeted optimizations while preserving correctness.
**Language:** Python | **Agent Timeout:** 60 min | **Verifier Timeout:** 10 min
**Resources:** 4 CPUs, 16GB RAM, 20GB storage
**Status:** Scaffolding stage -- Dockerfiles create empty workspaces. Needs repo clones and benchmark infrastructure.

| Task | Repository | Target Function | Baseline Runtime | Difficulty | MCP Score |
|------|-----------|----------------|-----------------|-----------|-----------|
| sweperf-001 | NumPy | `numpy.core.multiarray.array_sum` | 0.045s | medium | 0.458 |
| sweperf-002 | scikit-learn | `sklearn.cluster._k_means._kmeans_single_elkan` | 0.182s | hard | 0.458 |
| sweperf-003 | Pandas | `pandas.core.groupby.ops.GroupBy._aggregate_series_fast` | 0.095s | medium | 0.458 |

**Scoring:** `runtime_reduction = 1 - (optimized_runtime / baseline_runtime)`. A score of 0.5 means 2x speedup. Correctness is mandatory -- optimization that breaks correctness scores 0.

### sweperf-001 -- NumPy Array Summation

Optimize array summation for large multi-dimensional arrays in `numpy/core/src/multiarray/calculation.c`. Hints: use SIMD instructions via NumPy's ufunc mechanism, evaluate memory access patterns for cache efficiency. Reference solution replaces naive loop with vectorized operations using `np.einsum`.

### sweperf-002 -- Scikit-Learn K-Means Elkan

Optimize K-Means clustering single iteration using Elkan's algorithm in `sklearn/cluster/_k_means_elkan.pyx` (Cython). Hints: use triangle inequality to skip redundant distance calculations, maintain upper/lower bounds for cluster assignments, apply Cython optimizations for inner loops. Reference solution reduces complexity from O(nkd) to O(nkd/b) where b is the pruning factor.

### sweperf-003 -- Pandas GroupBy Aggregation

Optimize series aggregation in groupby operations in `pandas/_libs/groupby.pyx` (Cython). Hints: leverage pandas' internal Cython-based hash tables, minimize Python object creation in tight loops, consider memory alignment for cache performance. Reference solution replaces Python dictionary-based aggregation with Cython-optimized hash table lookup using pandas' internal khash implementation.

---

## 7. TAC -- The Agent Company

**Focus:** Tasks from The Agent Company (TAC) benchmark, requiring agents to use external tools, navigate unfamiliar repositories, and interact with services (GitLab, RocketChat) beyond just editing code.
**Prerequisites:** TAC server infrastructure (GitLab, RocketChat, API server). See `benchmarks/ccb_tac/README.md` for setup.

| Task | Language | Difficulty | Category | MCP Score |
|------|----------|-----------|----------|-----------|
| tac-buffer-pool-manager | C++ | hard | implement | 0.490 |
| tac-dependency-change | Python | medium | dependency | 0.440 |
| tac-find-in-codebase-1 | C++ | medium | find-in-codebase | 0.575 |
| tac-find-in-codebase-2 | C++ | medium | find-in-codebase | 0.575 |
| tac-implement-hyperloglog | C++ | hard | implement | 0.490 |
| tac-write-unit-test | Python | medium | unit-test | 0.465 |

**Excluded tasks (2):**
- `tac-copilot-arena-endpoint` -- copilot-arena-server repo not present in TAC GitLab backup data
- `tac-troubleshoot-dev-setup` -- same repo dependency; task fails at clone

### tac-buffer-pool-manager

Implement a buffer pool manager for the bustub database system (from TheAgentCompany GitLab). This is the core component managing in-memory page cache and disk coordination. The component interacts with disk manager, page guard, and LRU-K replacer -- understanding the dependency graph and existing patterns is critical.

### tac-dependency-change

Update dependency versions in a Python project and ensure compatibility. Tests maintenance workflow of upgrading libraries while keeping everything working.

### tac-find-in-codebase-1

Search the llama.cpp codebase to find which specific PR improved context window support for llama3.1 models. The agent must navigate the codebase, identify the relevant change, and communicate the result via RocketChat.

### tac-find-in-codebase-2

Similar codebase search task in llama.cpp. Find a specific improvement or PR through code navigation and search.

### tac-implement-hyperloglog

Implement the HyperLogLog algorithm for approximate cardinality estimation in C++. Requires understanding the probabilistic data structure and implementing it correctly within the existing codebase.

### tac-write-unit-test

Navigate to the OpenHands repository, find the `search_file` function in `/workspace/openhands/openhands/runtime/plugins/agent_skills/file_ops/file_ops.py`, and write comprehensive unit tests in `/workspace/openhands/tests/unit/test_agent_skill.py`. Tests the agent's ability to understand existing code and write meaningful test coverage.

---

## 8. CrossRepo -- Cross-Repository Reasoning

**Focus:** Tasks that span multiple repositories, testing the ability to trace interactions, APIs, and data flows across codebases.

| Task | Repositories | Description |
|------|-------------|-------------|
| api_upgrade_01 | etcd, kubernetes, containerd | gRPC API migration |
| bug_localization_01 | numpy, pandas, scikit-learn | Cross-library dtype bug |
| cross_file_reasoning_01 | kubernetes, containerd | CRI interface tracing |
| refactor_rename_01 | Django, Flask, requests | HTTP class standardization |
| simple_test_01 | N/A | Pipeline smoke test |

### api_upgrade_01 -- Migrate gRPC Dial Calls

Migrate deprecated `grpc.Dial()` and `grpc.DialContext()` calls to `grpc.NewClient()` across etcd, kubernetes, and containerd codebases under `/ccb_crossrepo/src/`. Must preserve existing dial options and error handling, and must not modify proto definitions or generated code. Output: unified diff to `/logs/agent/patch.diff`.

### bug_localization_01 -- NumPy Dtype Compatibility Issue

Trace a NumPy dtype compatibility issue that manifests when pandas nullable integers flow into scikit-learn preprocessing. The trace path crosses three repositories: (1) scikit-learn preprocessing (`sklearn/preprocessing/_data.py`), (2) input validation (`sklearn/utils/validation.py`), (3) pandas nullable integer conversion (`pandas/core/arrays/masked.py`), (4) NumPy dtype handling (`numpy/_core/_methods.py`). Output: `BUG_ANALYSIS.md` with exact file and line range of root cause.

### cross_file_reasoning_01 -- Kubernetes CRI to containerd

Trace the Kubernetes Container Runtime Interface (CRI) from gRPC service definition to containerd's implementation. Find the `RuntimeService` gRPC definition in kubernetes repo (`staging/src/k8s.io/cri-api/`), identify key RPC methods (`RunPodSandbox`, `StopPodSandbox`, etc.), find where containerd implements these methods, and document how kubernetes vendors containerd's API types. Output: `REASONING.md`.

### refactor_rename_01 -- Standardize HTTP Request Class Naming

Rename HTTP Request classes to a consistent `HTTPRequest` name across three web frameworks: Django (`HttpRequest` in `django/django/http/request.py`), Flask (`Request` in `flask/src/flask/wrappers.py`), and requests (`Request` in `requests/src/requests/models.py`). Update all imports, type annotations, and docstrings referencing old names. Output: unified diff to `/logs/agent/patch.diff`.

### simple_test_01 -- Pipeline Smoke Test

Create a marker file `test_marker.txt` containing exactly `MARKER_CREATED`. This task verifies the Harbor task pipeline works end-to-end.

---

## 9. RepoQA -- Semantic Code Retrieval

**Focus:** Find functions by behavioral description alone (no name given). Tests semantic search capability -- the agent must read a description of what a function does and locate it in the repository.
**Difficulty:** hard (all tasks) | **Agent Timeout:** 10 min | **Verifier Timeout:** 5 min
**Output:** JSON to `/app/solution.json` with `function_path`, `function_name`, `justification`.
**Scoring:** 1.0 (perfect match), 0.7-0.9 (good), 0.3-0.6 (partial), 0.0 (wrong).

| Task | Language | Repository |
|------|----------|------------|
| repoqa-cpp-apache-logging-log4cxx-03 | C++ | apache/logging-log4cxx |
| repoqa-cpp-skypjack-uvw-00 | C++ | skypjack/uvw |
| repoqa-java-google-gson-03 | Java | google/gson |
| repoqa-java-square-retrofit-04 | Java | square/retrofit |
| repoqa-python-psf-black-01 | Python | psf/black |
| repoqa-python-python-poetry-poetry-08 | Python | python-poetry/poetry |
| repoqa-rust-helix-editor-helix-03 | Rust | helix-editor/helix |
| repoqa-rust-rust-bakery-nom-06 | Rust | rust-bakery/nom |
| repoqa-typescript-expressjs-express-07 | TypeScript | expressjs/express |
| repoqa-typescript-xenova-transformers.js-08 | TypeScript | xenova/transformers.js |

### repoqa-cpp-apache-logging-log4cxx-03

Find a function that decodes UTF-16 encoded characters into Unicode scalar values, handling surrogate pairs. It checks for high-surrogates (0xD800-0xDBFF), verifies low-surrogate follow-up (0xDC00-0xDFFF), calculates combined scalar values, and returns error code 0xFFFF for invalid sequences.

### repoqa-cpp-skypjack-uvw-00

Find a function that reads data using a provided function with dynamic buffer sizing. It initially uses a fixed-size buffer, and if too small (indicated by a specific error code), dynamically allocates a larger buffer and retries.

### repoqa-java-google-gson-03

Find a method that retrieves the current element as a null type representation. It checks if the current element is null type using a type-checking method, casts it if valid, or throws an exception if the check fails.

### repoqa-java-square-retrofit-04

Find a method that appends a query parameter to a URL being constructed, with optional URL encoding. It checks if a URL has been previously set, combines relative URLs with base URLs, and handles encoding based on a boolean parameter.

### repoqa-python-psf-black-01

Find a function that transforms unchanged lines of code into special comment format to preserve original formatting during selective formatting. Operates in two phases: converts top-level unchanged statements into special comment types, then processes individual unchanged lines normalizing comment prefixes and indentation.

### repoqa-python-python-poetry-poetry-08

Find a function that verifies the existence of README files referenced in a project configuration. It checks if each README file exists in the config file's directory and returns a list of error messages for missing files.

### repoqa-rust-helix-editor-helix-03

Find a function that determines language injection details for a query match within source code. Takes a query object, match result, and source code slice; returns a tuple of optional language marker, optional content node, and child node inclusion setting.

### repoqa-rust-rust-bakery-nom-06

Find a function that verifies parsing of specific bit segments from a byte array (extracting 4, 8, and 4 bits respectively) and correctly tracks remaining unconsumed bytes.

### repoqa-typescript-expressjs-express-07

Find a constructor function that initializes and manages a specific path within a web application, handling different HTTP methods. Sets up path, middleware handler list, debugging, and matches incoming requests to extract parameters.

### repoqa-typescript-xenova-transformers.js-08

Find a function that rearranges multi-dimensional array elements based on specified new axis orders. Takes a multi-dimensional array, current dimensions, and new axis order; returns tuple of rearranged array and new shape.

---

## 10. DIBench -- Dependency Installation

**Focus:** Infer and add missing dependencies to build files by analyzing source code imports. The agent must not modify source code -- only edit dependency configuration files.
**Difficulty:** medium (all tasks) | **Agent Timeout:** 15 min | **Verifier Timeout:** 15 min

| Task | Language | Project | Build File |
|------|----------|---------|------------|
| dibench-csharp-dotnetkoans | C# | DotNetKoans | `DotNetKoans.csproj` |
| dibench-csharp-irongut-codecoveragesummary | C# | irongut/CodeCoverageSummary | `CodeCoverageSummary.csproj` |
| dibench-js-eslint-markdown | JavaScript | eslint/markdown | `package.json` |
| dibench-js-motdotla-dotenv-expand | JavaScript | motdotla/dotenv-expand | `package.json` |
| dibench-python-inducer-cgen | Python | inducer/cgen | `pyproject.toml` |
| dibench-python-rhinosec-iamactionhunter | Python | RhinoSecurityLabs/IAMActionHunter | `pyproject.toml` |
| dibench-rust-mitsuhiko-similar-asserts | Rust | mitsuhiko/similar-asserts | `Cargo.toml` |
| dibench-rust-rusticata-pcap-parser | Rust | rusticata/pcap-parser | `Cargo.toml` |

Each task follows the same pattern: the agent must analyze the project's source code to identify all external library imports, then edit the specified build file to declare the correct dependencies (with appropriate versions) so that the project builds and passes tests. The constraint is that only the build file may be edited -- source code must remain untouched.

---

## 11. CodeReview -- AI Code Review

**Focus:** Review real pull requests with injected defects -- find bugs, compliance violations, and fix them. Tests both detection accuracy and fix quality using hybrid scoring.
**Languages:** JavaScript, C#, TypeScript | **Time Limit:** 20 min per task

| Task | Difficulty | MCP Score |
|------|-----------|-----------|
| cr-ghost-001 | hard | 0.820 |
| cr-aspnetcore-001 | hard | 0.840 |
| cr-calcom-001 | hard | 0.830 |

Each task clones a real open-source repository at a pinned PR merge commit, then injects 3-4 realistic defects (functional bugs and compliance violations) across multiple source files. The agent must:

1. **Detect** defects by producing a structured `/workspace/review.json` with file, line, severity, and description for each finding
2. **Fix** defects by committing corrected code to the workspace

**Scoring:** Hybrid formula -- `0.5 * detection_F1 + 0.5 * fix_score`. Detection uses precision/recall against ground truth `expected_defects.json`. Fix scoring checks for defect-specific code patterns in modified files against `expected_patches/`.

### cr-ghost-001

Review Ghost PR #26260 (comment likes feature) targeting `TryGhost/Ghost` at merge commit `b43bfc85`. Four injected defects across 3 backend JavaScript files (`comments-service.js`, `comments-controller.js`, `comment-likes.js`): missing error guard for non-existent comments, incorrect parameter reference in frame options, missing cache invalidation after like creation, and missing member relation in like query. Three functional bugs (critical/high) and one compliance violation (medium).

### cr-aspnetcore-001

Review ASP.NET Core PR #64636 (Blazor DisplayName feature) targeting `dotnet/aspnetcore` at merge commit `8752557`. Four injected defects across 2 C# source files (`DisplayName.cs`, `ExpressionMemberAccessor.cs`): reversed attribute precedence (DisplayNameAttribute checked before DisplayAttribute), removed null check for the `For` parameter, broken cache invalidation that only clears one of two caches, and removed expression equality optimization causing unnecessary re-renders. Three functional bugs (critical/high) and one compliance violation (medium).

### cr-calcom-001

Review cal.com PR #26801 (feature opt-in scope configuration) targeting `calcom/cal.com` at merge commit `4b99072b`. Four injected defects across 3 TypeScript files (`FeatureOptInService.ts`, `config.ts`, `_router.ts`): inverted filter condition returning only disabled features, removed scope fallback rejecting all scoped features, removed allowlist validation accepting any feature slug, and hardcoded permissive policy ignoring feature config. Three functional bugs (critical/high) and one compliance violation (medium).

---

## 12. DependEval -- Dependency Ordering

**Focus:** Identify and correctly order dependencies in real-world repositories. Two task types: recognizing dependencies from source code, and editing multiple files to fix dependency issues.
**Languages:** Java, JavaScript, Python, TypeScript | **Difficulty:** medium | **Time Limit:** 10 min per task
**Source:** [DependEval benchmark](https://github.com/nicholasgasior/dependeval)

### Task Types

| Task Type | Count | Description |
|-----------|-------|-------------|
| Dependency Recognition | 16 | Analyze source code to identify and list all dependency relationships |
| Multifile Editing | 16 | Edit multiple files to resolve dependency ordering issues |

### Dependency Recognition Tasks (16)

| Task | Language | Repository |
|------|----------|------------|
| dependency_recognition-java-488d70a0 | Java | ProviGen |
| dependency_recognition-java-a06aa17b | Java | iceberg |
| dependency_recognition-java-a6bb8222 | Java | iceberg |
| dependency_recognition-java-c7138508 | Java | oracle-r2dbc |
| dependency_recognition-javascript-6940aa7b | JavaScript | Next-GraphQL-Blog |
| dependency_recognition-javascript-d52503a0 | JavaScript | place-to-stay |
| dependency_recognition-javascript-dafb5116 | JavaScript | cls-rtracer |
| dependency_recognition-javascript-ef7ab7e5 | JavaScript | better-onetab |
| dependency_recognition-python-58e6c2b0 | Python | MLOS |
| dependency_recognition-python-7c0ee37f | Python | semi-supervised-music-tagging-transformer |
| dependency_recognition-python-83d51f82 | Python | xos |
| dependency_recognition-python-bb854fc4 | Python | alexa-apis-for-python |
| dependency_recognition-typescript-a36bf7a5 | TypeScript | Rankings-Backend |
| dependency_recognition-typescript-b512c0c8 | TypeScript | predicates |
| dependency_recognition-typescript-b8647ec9 | TypeScript | rules |
| dependency_recognition-typescript-d13f8f68 | TypeScript | installer-gui |

### Multifile Editing Tasks (16)

| Task | Language | Repository |
|------|----------|------------|
| multifile_editing-java-2e96d995 | Java | kafka-webview |
| multifile_editing-java-5edcbb0d | Java | RadioDroid |
| multifile_editing-java-8d0d378a | Java | NuProcess |
| multifile_editing-java-e1c422ed | Java | PowerTutor |
| multifile_editing-javascript-460fab96 | JavaScript | winston-logstash |
| multifile_editing-javascript-86e61c71 | JavaScript | NFT-Marketplace-Tutorial |
| multifile_editing-javascript-beeb2c66 | JavaScript | three.bas |
| multifile_editing-javascript-bf306859 | JavaScript | type-to-reducer |
| multifile_editing-python-37688cee | Python | PiGlow |
| multifile_editing-python-6e11aa67 | Python | Codex-CLI |
| multifile_editing-python-85970e74 | Python | Magisk_Manager_Recovery_Tool |
| multifile_editing-python-ea840a03 | Python | modAL |
| multifile_editing-typescript-01b00e0e | TypeScript | akello |
| multifile_editing-typescript-1469d2cc | TypeScript | stromjs |
| multifile_editing-typescript-4253968d | TypeScript | Day59-Angular-Practice |
| multifile_editing-typescript-73e7d1bc | TypeScript | event-sourcing-demo-app |

---

## 13. LinuxFLBench -- Linux Kernel Fault Localization

**Focus:** Locate the root cause of real Linux kernel bugs from Bugzilla reports. The agent must identify the exact source file(s) and function(s) responsible for hardware/driver failures across kernel subsystems.
**Language:** C | **Difficulty:** expert (all tasks) | **Time Limit:** 30 min per task
**Repository:** linux (kernel source tree) | **Build Timeout:** 30 min (kernel partial clone ~2GB)

| Task | Subsystem | Description |
|------|-----------|-------------|
| lfl-acpi-207835 | ACPI | Backlight brightness control does not work on Acer TravelMate 5735Z -- ACPI video backlight control non-functional by default |
| lfl-nfs-117651 | NFS | Root NFS and autofs mount disappears due to inode revalidate failure in sunrpc |
| lfl-sata-203475 | SATA | Samsung 860 EVO queued TRIM causes timeout errors in libata |
| lfl-sound-53441 | Sound | HDA Intel sound stops working after suspend to RAM due to missing runtime PM disable |
| lfl-wifi-206661 | WiFi | iwlwifi missing PCI subdevice entries for 0x2526 causing firmware load failure |

Each task provides:
- A Bugzilla-style bug report describing the symptoms
- The full Linux kernel source tree at a relevant commit
- A test script that validates the agent correctly identifies the faulty file(s) and function(s)

---

## Appendix: Summary Statistics

| Benchmark | Tasks | Difficulty Range | Language(s) | Avg MCP Score |
|-----------|-------|-----------------|-------------|---------------|
| K8s Docs | 5 | medium - hard | Go | 0.628 |
| LargeRepo | 4 | hard | Go, Rust, Python/C++, TS | 0.895 |
| LoCoBench | 25 | expert | C, C++, C#, Python, Rust, TS | 0.914 |
| PyTorch | 12 | medium - hard | C++ | 0.555 |
| SWE-bench Pro | 36 | hard | Go, TS, Python, JS | 0.660 |
| DependEval | 32 | medium | Java, JS, Python, TS | -- |
| SWE-Perf | 3 | medium - hard | Python | 0.458 |
| TAC | 6 | medium - hard | C++, Python | 0.506 |
| CrossRepo | 5 | medium - hard | Go, Python | -- |
| RepoQA | 10 | hard | C++, Java, Python, Rust, TS | -- |
| DIBench | 8 | medium | C#, JS, Python, Rust | -- |
| CodeReview | 3 | hard | JS, C#, TS | 0.830 |
| LinuxFLBench | 5 | expert | C | -- |

**Total tasks:** 156
**Languages covered:** C, C++, C#, Go, Java, JavaScript, Python, Rust, TypeScript
**SDLC phases covered:** Requirements & Discovery, Architecture & Design, Implementation (feature), Implementation (bug fix), Implementation (refactoring), Testing & QA, Documentation, Maintenance, Dependency Management, Fault Localization
