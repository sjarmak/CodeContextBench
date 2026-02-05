# CodeContextBench Task Review: Formulation, Difficulty, and Ground Truth Assessment

## Revision History

| Date | Summary |
|------|---------|
| 2026-02-04 (v2) | Post-remediation review reflecting fixes US-001 through US-022. Crossrepo ground truth corrected, difficulty labels calibrated, MCP scores recalculated with per-task discrimination, compilation checks added to LargeRepo, metadata errors fixed. |
| 2026-02-03 (v1) | Initial review identifying systemic issues across all 10 benchmarks. |

---

## Executive Summary

This document reviews all 116 selected benchmark tasks across 10 benchmarks in CodeContextBench. It assesses whether each task is well-formulated, whether difficulty and SDLC phase labels are appropriate, and whether ground truth / evaluation criteria are sound.

**Status after remediation (US-001 through US-022):**
- **Crossrepo ground truth fixed**: All three mismatched tasks (api_upgrade_01, bug_localization_01, refactor_rename_01) now have expected_changes.json files aligned with their instruction.md content
- **Difficulty labels calibrated**: Six tiers (easy/medium/hard/very_hard/critical/expert) applied per-benchmark using objective metrics (files changed, LOC, context size). Distribution: easy 1, medium 22, hard 58, very_hard 24, critical 2, expert 9
- **MCP benefit scores recalculated**: Per-task feature extraction replaces benchmark-level defaults. All benchmarks with 5+ tasks now have score standard deviation > 0.05
- **LargeRepo evaluation strengthened**: All four test scripts now include compilation/syntax checks (go build, cargo check, py_compile, tsc --noEmit) that gate keyword scoring
- **Metadata errors fixed**: Placeholder issue numbers replaced, truncated descriptions completed, language labels corrected, copy-paste error in test script resolved

**Remaining concerns:**
- **Evaluation rigor still varies significantly** across benchmarks (real test suites vs. keyword checks)
- **LoCoBench synthetic codebases** with `module_N.py` naming may not reflect real-world navigation challenges
- **MCP benefit scores** are formula-based and not empirically validated against actual MCP usage data

**Resolved in this pass:**
- **Partial credit scoring** added to SWE-bench Pro (731 files) and PyTorch (24 files) -- no longer binary pass/fail
- **SDLC phase labels corrected**: sweperf moved from "Testing & QA" to "Implementation (bug fix)"; dibench moved from "Implementation (feature)" to "Maintenance"
- **`simple_test_01`** marked as `exclude_from_aggregate` so it no longer dilutes benchmark statistics
- **sgt-002 ground truth mismatch** discovered and fixed: instruction now correctly describes Inductor ReLU/GELU(Addmm) fusions revert (PR #168157) instead of the incorrect annotation/export metadata hook revert
- **sgt-003 truncated description** completed with benchmark results and test plan
- **sgt-021 minimal description** expanded with context from PR #163712 and issue #163483
- **RepoQA `model_hint`** removed from template to avoid biasing evaluation toward MCP agents
- **NodeBB service dependencies**: Handled by pre-built base Docker image (`jefzda/sweap-images`); no fix needed
- **LoCoBench evaluation**: Confirmed to be deterministic keyword-based (`verify.py`), NOT an LLM judge as previously documented
- **LargeRepo reward.json**: Test scripts now document the existence of unused manual evaluation criteria

---

## 1. ccb_largerepo (4 tasks, all "hard")

### Overview
Four feature-implementation tasks in massive real-world repositories (Kubernetes, Servo, TensorRT-LLM, VS Code). Each asks the agent to implement a substantial new capability.

### Task-by-Task Analysis

| Task ID | Repo | Language | What It Asks |
|---------|------|----------|-------------|
| big-code-k8s-001 | kubernetes | Go | Implement `NoScheduleNoTraffic` taint effect |
| big-code-servo-001 | servo | Rust | Implement `scrollend` DOM event |
| big-code-trt-001 | tensorrt-llm | Python/C++ | Add `W4A8_MXFP4_INT8` quantization mode |
| big-code-vsc-001 | vscode | TypeScript | Fix stale diagnostics after git branch switch |

### Difficulty Assessment
All labeled **hard** -- justified by the scale of these codebases (1-1.6GB) and the cross-module nature of each task. The agent must navigate hundreds of thousands of files to find all relevant integration points.

### SDLC Phase
All labeled **Implementation (feature)** -- mostly accurate, though `big-code-vsc-001` is arguably a **bug fix** (stale diagnostics) rather than a new feature.

### Evaluation Assessment

**RESOLVED: Test scripts now include compilation checks (US-012 through US-015).**

All four tasks now follow a consistent three-stage evaluation pattern:
1. **Compilation gate** -- build/syntax check must pass or score is 0.0
   - big-code-k8s-001: `go build ./pkg/apis/core/...`, `./pkg/scheduler/...`, `./pkg/kubelet/...`
   - big-code-servo-001: `cargo check`
   - big-code-trt-001: `python -m py_compile` on all modified `.py` files; informational `g++ -fsyntax-only` for C++ (CUDA headers unavailable in Docker)
   - big-code-vsc-001: `npx tsc --noEmit` targeting relevant tsconfig files
2. **Unit test execution** -- best-effort test runs where feasible (e.g., `go test ./pkg/apis/core/taint/...`, `cargo test scrollend`, `npm test`)
3. **Keyword-based scoring** -- retained as secondary signal for feature completeness

**RESOLVED: Copy-paste error in VS Code test script fixed (US-011).**
Comment now correctly references "stale diagnostics after git branch switch" instead of "scrollend event implementation."

**Remaining concern:** The `reward.json` files define subjective "rating" criteria (e.g., "architecture_understanding" on 0-1 scale) that are never automatically evaluated. These remain unused.

**Strength:** Real repository clones provide authentic complexity. MCP infrastructure is well-prepared. Compilation gates prevent syntactically broken code from scoring.

### MCP Benefit Scores
**RESOLVED: Scores now vary per task (US-021).** Range: 0.730--0.876 (stddev 0.064), driven by per-codebase LOC estimates and expected files touched. Previously all four tasks had identical 0.895.

---

## 2. ccb_pytorch (12 tasks, 3 "medium" / 6 "hard" / 1 "very_hard" / 2 "critical")

### Overview
Cross-module bug fixes mined from real PyTorch pull requests. Each task provides a ground-truth commit and uses `make test` for evaluation.

### Task-by-Task Analysis

| Task ID | Description | LOC Changed | Difficulty | Status |
|---------|------------|-------------|-----------|--------|
| sgt-001 | NCCL thread safety | 94 | hard | Has sophisticated pattern-based eval (unique) |
| sgt-002 | Revert Inductor ReLU/GELU(Addmm) fusions | 180 | hard | **FIXED**: Instruction rewritten to match ground truth (PR #168157) |
| sgt-003 | Cleanup graph reference cycles | 38 | medium | **FIXED**: Truncated description completed with benchmark results and test plan |
| sgt-005 | ROCm shared memory pruning | 22 | medium | **FIXED (US-008)**: Truncated description completed with full PR content |
| sgt-008 | Release 2.10 branch changes | 808 | critical | **FIXED (US-005)**: Time limit removed, difficulty set to "critical" |
| sgt-009 | HOP print functionalize | 87 | hard | **FIXED (US-007)**: Placeholder replaced with PR #167368 |
| sgt-010 | cuDNN runtime version exposure | 52 | hard | **FIXED (US-008)**: Truncated URL completed |
| sgt-012 | Invalid grid config generation | 25 | medium | Good context with PR references |
| sgt-014 | Dynamo resume KeyError fix | 242 | very_hard | **FIXED (US-018)**: Reclassified from "medium" to "very_hard" based on LOC |
| sgt-016 | Graph partition memory plan | 93 | hard | **Note**: sgt-016 did not have #ISSUE_NUMBER despite being named in the original review |
| sgt-021 | Allgather/scatter contiguity | 59 | hard | **FIXED**: Description expanded with context from PR #163712 and issue #163483 |
| sgt-025 | CUDA 12.9 nightly build | 3526 | critical | **FIXED (US-006)**: Time limit removed, difficulty set to "critical" |

### Difficulty Assessment

**RESOLVED: Difficulty labels calibrated using LOC thresholds (US-018).**

Classification: <50 LOC = medium, 50-200 LOC = hard, >200 LOC = very_hard, release-engineering scale = critical.

- **critical** (2 tasks): sgt-008 (808 LOC, 110 files) and sgt-025 (3526 LOC) -- time limits removed to acknowledge their release-engineering scope
- **very_hard** (1 task): sgt-014 (242 LOC) -- previously under-rated as "medium"
- **hard** (6 tasks): sgt-001 (94), sgt-002 (180), sgt-009 (87), sgt-010 (52), sgt-016 (93), sgt-021 (59)
- **medium** (3 tasks): sgt-003 (38), sgt-005 (22), sgt-012 (25)

### SDLC Phase
11 of 12 labeled **Implementation (bug fix)** -- appropriate for genuine bug-fix PRs. sgt-005 is labeled **Implementation (feature)** -- correct, it's adding ROCm support.

### Evaluation Assessment

**Inconsistent evaluation sophistication** remains an open issue:
- sgt-001 has a custom 81-line test script with pattern-based validation (checks for `std::lock_guard`, `mutex`, etc.)
- All other tasks use a simple "run `make test`, report pass/fail" approach

**RESOLVED: Placeholder issue numbers fixed (US-007).** All `#ISSUE_NUMBER` placeholders across the benchmark have been replaced with actual PyTorch PR numbers (sgt-002: #169497, sgt-004: #170499, sgt-009: #167368, sgt-012: #164048). Grep confirms zero remaining placeholders.

**RESOLVED: Truncated descriptions fixed (US-008).** sgt-005 and sgt-010 now have complete descriptions sourced from the original PR bodies.

**RESOLVED: Remaining description issues fixed.**
- sgt-003 description completed with GC time benchmark results and test plan listing 5 `test_parametrization` tests
- sgt-021 description expanded with context about PR #163712 relaxing contiguity requirements and subsequent regression
- sgt-002 instruction rewritten to match ground truth commit `40fb4145` (Inductor fusions revert, not metadata hook revert)

**RESOLVED: Partial credit scoring added.** All 24 non-sgt-001 test scripts now capture `make test` output and parse pytest summary lines for pass/fail ratios instead of binary 1/0.

**Strength:** Ground truth is anchored to real commits with known diffs. Test suites are the actual PyTorch CI tests.

---

## 3. ccb_k8sdocs (5 tasks, 4 "hard" / 1 "medium")

### Overview
Documentation generation tasks: the agent must write `doc.go` files for Kubernetes packages where existing documentation has been stripped.

### Task-by-Task Analysis

| Task ID | Package | Difficulty | Ground Truth Size |
|---------|---------|-----------|-------------------|
| apiserver-doc-001 | k8s.io/apiserver | hard | 75 lines, comprehensive |
| applyconfig-doc-001 | applyconfigurations | hard | 150 lines, excellent with code examples |
| client-go-doc-001 | client-go | hard | 110 lines, well-structured |
| fairqueuing-doc-001 | queueset (fair queuing) | hard | 119 lines, mathematically rigorous |
| pkg-doc-001 | kubelet/cm | medium | **113 lines, comprehensive** |

### Difficulty Assessment
- The four "hard" tasks are genuinely complex, requiring synthesis across multiple sub-packages
- `fairqueuing-doc-001` is arguably the hardest (requires understanding WFQ algorithms, virtual time, mathematical formulas)
- `pkg-doc-001` as "medium" is reasonable -- simpler scope, fewer sub-packages

### SDLC Phase
All labeled **Documentation** -- correct and appropriate.

### Evaluation Assessment

**RESOLVED: Ground truth disparity for pkg-doc-001 fixed (US-016).**
The ground truth has been expanded from 21 lines to 113 lines, now covering:
- ContainerManager interface and methods
- Cgroup management (v1/v2 support, hierarchy)
- QoS enforcement (Guaranteed, Burstable, BestEffort)
- Resource allocation coordination
- All four subpackages (cpumanager, memorymanager, topologymanager, devicemanager)
- Platform differences (Linux, Windows, unsupported stubs)

All 8 test script keyword checks pass with the expanded ground truth (10/10 score).

**Remaining concern:** Two-tier evaluation not integrated. The `test.sh` scripts perform keyword-based checks worth up to 10 points. The `reward.json` defines a richer LLM-judge evaluation (`evaluate_docs.py`) that is not automatically invoked. The automated scoring may diverge significantly from the intended quality assessment.

**Strength:** Well-crafted instructions with clear requirements. All ground truths now provide proportionate exemplars (75-150 lines). The stripped-documentation approach is a clean experimental design.

---

## 4. ccb_locobench (25 tasks, 9 "expert" / 16 "hard")

### Overview
Tasks on synthetic but realistic codebases with 70+ files and 700K+ tokens of context. Three categories: architectural_understanding (9), cross_file_refactoring (13), bug_investigation (3).

### Structural Patterns

All tasks follow a templated structure:
- Instruction in `instruction.md` with detailed scenario
- Ground truth in `tests/ground_truth.json` with expected answer and evaluation criteria
- Evaluation via `test.sh` that runs a deterministic keyword-based verifier (`verify.py`)
- Codebases are generated/synthetic (module_1.py through module_70+.py)

### Difficulty Assessment
**RESOLVED: Difficulty labels calibrated by category (US-019).**

- **expert** (9 tasks): Architectural understanding tasks with >1M tokens of context. These require comprehension and synthesis across the entire codebase.
- **hard** (16 tasks): Cross-file refactoring (13) and bug investigation (3). These require code modifications or diagnosis but within more bounded scope.

This provides two distinct difficulty tiers that reflect the genuine difference between "analyze the whole architecture" and "fix/refactor specific modules."

### SDLC Phase Assessment

| Category | SDLC Phase | Count | Assessment |
|----------|-----------|-------|------------|
| architectural_understanding | Architecture & Design | 9 | Reasonable -- these are analysis tasks |
| cross_file_refactoring | Implementation (refactoring) | 13 | Correct |
| bug_investigation | Implementation (bug fix) | 3 | Correct |

### Evaluation Issues

**CORRECTED: Evaluation is deterministic, not LLM-judge based.** The `test.sh` scripts run `verify.py`, which performs deterministic keyword-based matching against ground truth criteria in `ground_truth.json`. Scores are reproducible across runs. This is a significant strength that was previously mischaracterized.

**Synthetic codebases may not reflect real-world patterns** -- unchanged:
Files named `module_1.py` through `module_73.py` lack the organic naming and structure of real projects. This could make tasks artificially harder (no semantic hints from filenames) or easier (simpler structure).

**repo field is empty for all tasks** -- unchanged:
The `repo` field in selected_benchmark_tasks.json is `""` for all LoCoBench tasks. While understandable (synthetic), this prevents MCP tools from having a Sourcegraph index to search.

**Strength:** Well-defined evaluation criteria in ground_truth.json. Detailed, specific expected answers. Good category diversity.

### MCP Benefit Scores
**RESOLVED: Scores now vary per task (US-021).** Range: 0.717--0.931 (stddev 0.055), driven by actual `context_length` (975K--1.16M) and `files_count` (73--86) from task.toml metadata. Previously scores were flat within categories (0.94/0.915/0.865).

---

## 5. ccb_swebenchpro (36 tasks, 13 "hard" / 23 "very_hard")

### Overview
Adapted from SWE-bench Pro (ScaleAI). Real bug fixes across 11 repositories in Go, Python, TypeScript, and JavaScript. Uses the standard SWE-bench evaluation framework with fail-to-pass and pass-to-pass test lists.

### Repository Distribution

| Repository | Language | Tasks |
|-----------|----------|-------|
| ansible/ansible | Python | 5 |
| flipt-io/flipt | Go | 4 |
| gravitational/teleport | Go | 4 |
| internetarchive/openlibrary | Python | 4 |
| qutebrowser/qutebrowser | Python | 4 |
| protonmail/webclients | TypeScript | 4 |
| NodeBB/NodeBB | JavaScript | 3 |
| future-architect/vuls | Go | 3 |
| navidrome/navidrome | Go | 2 |
| element-hq/element-web | TypeScript | 2 |
| tutao/tutanota | TypeScript | 1 |

### Difficulty Assessment
**RESOLVED: Difficulty labels calibrated by file count (US-017).**

Classification: 1-3 files = medium, 4-10 files = hard, 10+ files = very_hard.

- **hard** (13 tasks): 4-10 files changed. Includes focused fixes in qutebrowser (6-7 files), navidrome, and some ansible tasks.
- **very_hard** (23 tasks): 11+ files changed. Includes protonmail/webclients tasks (30-84 files), teleport, and most multi-module fixes.
- No tasks qualified for "medium" -- all SWE-bench Pro tasks modify at least 6 files.

### SDLC Phase
All labeled **Implementation (bug fix)** -- correct for SWE-bench tasks, which are bug/issue resolutions.

### Evaluation Assessment

**RESOLVED: Language metadata errors fixed (US-009, US-010).**
- element-hq/element-web: corrected from `python` to `typescript` (56 task.toml files updated)
- qutebrowser: corrected from `typescript` to `python` (79 task.toml files updated)
- nodebb: corrected from `python` to `javascript` (44 task.toml files updated)
- navidrome: corrected from `python` to `go` (57 task.toml files updated)
- Both `language` fields and `tags` arrays in task.toml files updated in sync

**RESOLVED: Partial credit scoring added.** All 731 test scripts now parse test output for pass/fail ratios (pytest summary lines for Python, `--- PASS`/`--- FAIL` for Go) instead of binary 1/0. Full pass still scores 1.0; partial passes score the fraction of tests passed.

**Remaining concerns:**

- **Generic instruction template.** All instructions follow identical boilerplate: "Analyze issue -> Explore codebase -> Implement fix -> Ensure tests pass." No task-specific guidance.

**RESOLVED: NodeBB service dependencies.** NodeBB tasks use pre-built base Docker images (`jefzda/sweap-images`) that bundle Redis and MongoDB. No additional infrastructure setup needed.

**Strength:** This is the most rigorous evaluation framework in the benchmark. Real test suites, real patches, real CI validation. The SWE-bench format is well-established and reproducible.

---

## 6. ccb_sweperf (3 tasks, 1 "hard" / 2 "medium")

### Overview
Performance optimization tasks in numpy, scikit-learn, and pandas. The agent must find and fix performance regressions.

| Task ID | Repo | Difficulty |
|---------|------|-----------|
| sweperf-001 | numpy | medium |
| sweperf-002 | scikit-learn | hard |
| sweperf-003 | pandas | medium |

### SDLC Phase
**RESOLVED: Relabeled from "Testing & QA" to "Implementation (bug fix)".** Performance optimization tasks are bug fixes (fixing performance regressions), not test-writing tasks.

### Evaluation
Uses SWE-bench-style test execution (fail-to-pass / pass-to-pass lists). This is appropriate for verifying that the performance fix doesn't break functionality, though it doesn't directly measure whether performance actually improved.

---

## 7. ccb_tac (8 tasks, 3 "hard" / 5 "medium")

### Overview
Diverse task types from the TAC (Tool-Augmented Coding) benchmark: feature implementation, dependency management, codebase search, troubleshooting, and test writing.

| Task ID | Category | Repo | Difficulty | SDLC Phase |
|---------|----------|------|-----------|------------|
| tac-buffer-pool-manager | implement | bustub | hard | Implementation (feature) |
| tac-copilot-arena-endpoint | endpoint | copilot-arena-server | medium | Implementation (feature) |
| tac-dependency-change | dependency | OpenHands | medium | Maintenance |
| tac-find-in-codebase-1 | find-in-codebase | llama.cpp | medium | Requirements & Discovery |
| tac-find-in-codebase-2 | find-in-codebase | llama.cpp | medium | Requirements & Discovery |
| tac-implement-hyperloglog | implement | bustub | hard | Implementation (feature) |
| tac-troubleshoot-dev-setup | troubleshoot | copilot-arena-server | medium | Maintenance |
| tac-write-unit-test | unit-test | OpenHands | medium | Testing & QA |

### Difficulty Assessment
Good variation. The "hard" tasks (buffer pool manager, HyperLogLog) require implementing data structures from specification -- genuinely complex. The "medium" tasks (find-in-codebase, dependency change) are more focused.

### SDLC Phase Assessment
Appropriate diversity. This is the only benchmark contributing **Requirements & Discovery** (find-in-codebase) and **Maintenance** (dependency change, troubleshoot) tasks.

### Evaluation
TAC uses its own evaluation framework. The find-in-codebase tasks check whether the agent identifies the correct file/function. Implementation tasks verify compilation and test passage.

**Strength:** Best SDLC phase diversity of any benchmark. Tasks genuinely test different agent capabilities.

---

## 8. ccb_repoqa (10 tasks, 8 "hard" / 2 "medium")

### Overview
Semantic code navigation tasks from the RepoQA benchmark. The agent is given a natural-language description of a function and must find it in a repository -- without being told the function name.

### Structure
- 2 tasks per language: C++, Java, Python, Rust, TypeScript
- Repositories: log4cxx, uvw, gson, retrofit, black, poetry, nom, helix, transformers.js, express

### Difficulty Assessment
**RESOLVED: Difficulty labels calibrated by repository size (US-019).**

- **hard** (8 tasks): Repositories with >100 source files (log4cxx, gson, retrofit, black, poetry, helix, transformers.js, express)
- **medium** (2 tasks): Smaller repositories -- uvw (78 source files) and nom (65 source files)

The agent must use semantic understanding to match a behavioral description to source code. This cannot be solved by keyword search alone (the function name is withheld). Larger repositories make the search space proportionally harder.

### SDLC Phase
All labeled **Requirements & Discovery** -- appropriate. These are pure code navigation/comprehension tasks.

### Evaluation
Uses a custom `SemanticRetrievalQAVerifier` that compares the agent's `solution.json` against ground truth:
- Correct function path AND name: 1.0
- Partial matches: 0.3-0.9
- Wrong function: 0.0

**Strength:** Clean experimental design. The task is naturally suited to testing MCP search tools (semantic search should outperform grep for behavioral descriptions). Ground truth is unambiguous (specific function name and path).

**RESOLVED: `model_hint = "requires-mcp"` removed** from the template `task.toml`. Tasks are now neutral between MCP and baseline agents.

### MCP Benefit Scores
**RESOLVED: Scores now vary per task (US-021).** Range: 0.597--0.953 (stddev 0.114), driven by per-repo source file counts (65--559) and code ratio (0.0--0.79). Previously all 10 tasks had identical 0.85.

---

## 9. ccb_crossrepo (5 tasks, 4 "hard" / 1 "easy")

### Overview
Cross-repository tasks requiring understanding of code across multiple codebases.

| Task ID | Category | Task Description | Difficulty |
|---------|----------|-----------------|-----------|
| api_upgrade_01 | api_upgrade | Migrate `grpc.Dial()`/`grpc.DialContext()` to `grpc.NewClient()` across etcd, kubernetes, containerd | hard |
| bug_localization_01 | bug_localization | Locate NumPy dtype compatibility issue when pandas nullable integers flow into scikit-learn preprocessing | hard |
| cross_file_reasoning_01 | cross_file_reasoning | Trace Pod creation flow, document call chain | hard |
| refactor_rename_01 | refactor_rename | Standardize HTTP Request class naming to `HTTPRequest` across Django, Flask, and requests | hard |
| simple_test_01 | smoke_test | Basic MCP connectivity test | easy |

### Ground Truth Assessment

**RESOLVED: All three ground truth mismatches fixed (US-001, US-002, US-003).**

The original expected_changes.json files were templated from Kubernetes examples and never updated to match the actual task instructions. All three have been corrected:

- **api_upgrade_01 (US-001)**: Expected changes now reference grpc.Dial/DialContext removal and grpc.NewClient addition across etcd, kubernetes, and containerd source paths. Previously checked for pointer.Int32 -> ptr.To migration.
- **bug_localization_01 (US-002)**: Expected changes now reference NumPy/pandas/scikit-learn dtype compatibility (ExtensionArray, nullable Int64, check_array, StandardScaler). Previously checked for Kubernetes EventedPLEG/evented.go.
- **refactor_rename_01 (US-003)**: Expected changes now reference Django HttpRequest, Flask Request, and requests library Request class renaming to HTTPRequest. Previously checked for Kubernetes ProxierHealthServer -> ProxyHealthServer.

**RESOLVED: Repo field metadata corrected (US-004).**
- api_upgrade_01: `repo = "etcd,kubernetes,containerd"`
- bug_localization_01: `repo = "numpy,pandas,scikit-learn"`
- refactor_rename_01: `repo = "Django,Flask,requests"`
- cross_file_reasoning_01: `repo = "kubernetes,containerd"`

**RESOLVED: Language metadata corrected (US-010).**
- bug_localization_01: corrected from `language = "go"` to `language = "python"`
- refactor_rename_01: corrected from `language = "go"` to `language = "python"`

**RESOLVED: `simple_test_01` marked as `exclude_from_aggregate: true`** in `selected_benchmark_tasks.json`. The smoke test remains in the dataset for connectivity verification but is excluded from aggregate benchmark statistics.

### Evaluation Assessment

**RESOLVED: Evaluation infrastructure rebuilt to match task types.**

The original evaluation had three critical bugs discovered during the first rerun (all tasks scored 0.0 despite agents performing well):

1. **Missing `validate_patch.py`**: The test scripts referenced `/ccb_crossrepo/scripts/validate_patch.py` which did not exist in the repository. The Docker base image's bundled validator had a different CLI interface (`--output`, `--timeout`) than what the test scripts expected (`--expected`).

2. **No patch collection**: Instructions told agents to modify files but never mentioned saving output to `/logs/agent/patch.diff`. Agents made correct changes but the verifier couldn't find them.

3. **Wrong evaluation type for analysis tasks**: `bug_localization_01` (writes BUG_ANALYSIS.md) and `cross_file_reasoning_01` (writes REASONING.md) are analysis/documentation tasks, not code modification tasks. Their test scripts incorrectly expected a unified diff patch.

**Fixes applied:**

- **Patch tasks** (api_upgrade_01, refactor_rename_01):
  - Instructions updated to explicitly request `/logs/agent/patch.diff` output
  - Test scripts rewritten with two-stage approach: (a) check for explicit patch.diff, (b) fallback auto-collection via `git diff HEAD` across all source repos
  - Validation uses `validate_patch.py` (newly created in `benchmarks/ccb_crossrepo/scripts/`) checking file coverage (40% weight) + pattern matching (60% weight) against `expected_changes.json`
  - Inline Python fallback validator embedded in test.sh for environments where the standalone script is unavailable

- **Analysis tasks** (bug_localization_01, cross_file_reasoning_01):
  - Test scripts completely rewritten to validate markdown output
  - Searches multiple candidate paths (e.g., `/workspace/BUG_ANALYSIS.md`, `/workspace/REASONING.md`, any `.md` in workspace)
  - Validates against `expected_changes.json` using: content keywords (40-50%), file path references (30%), pattern references (20-30%)

- **Previous broken results**: Renamed to `crossrepo_opus_*__broken_verifier/` with README documenting the infrastructure bugs

**Remaining concern:** The `set -e` interaction with fallback logic caused a second round of failures (RewardFileNotFoundError) — fixed by removing `set -e` from test scripts to allow graceful fallback. Crossrepo tasks require a third rerun with this fix.

### SDLC Phase Assessment
- api_upgrade_01: **Implementation (refactoring)** -- correct
- bug_localization_01: **Implementation (bug fix)** -- correct
- cross_file_reasoning_01: **Architecture & Design** -- correct (comprehension/documentation task)
- refactor_rename_01: **Implementation (refactoring)** -- correct
- simple_test_01: **Testing & QA** -- debatable, this is a connectivity test

---

## 10. ccb_dibench (8 tasks, all "medium")

### Overview
Dependency inference tasks from DI-Bench: the agent must add missing dependencies to a project's build file so the code compiles/passes validation.

| Task ID | Language | Repo |
|---------|----------|------|
| dibench-python-inducer-cgen | Python | inducer/cgen |
| dibench-python-rhinosec-iamactionhunter | Python | RhinoSecurityLabs/IAMActionHunter |
| dibench-rust-mitsuhiko-similar-asserts | Rust | mitsuhiko/similar-asserts |
| dibench-rust-rusticata-pcap-parser | Rust | rusticata/pcap-parser |
| dibench-js-eslint-markdown | JavaScript | eslint/markdown |
| dibench-js-motdotla-dotenv-expand | JavaScript | motdotla/dotenv-expand |
| dibench-csharp-irongut-codecoveragesummary | C# | irongut/CodeCoverageSummary |
| dibench-csharp-dotnetkoans | C# | DotNetKoans/DotNetKoans |

### Difficulty Assessment
All labeled **medium** -- appropriate. These are focused tasks (modify a build file to add dependencies) that don't require understanding the full codebase, just the dependency relationships.

### SDLC Phase
**RESOLVED: Relabeled from "Implementation (feature)" to "Maintenance".** Adding missing dependencies is build system maintenance, not feature implementation.

### Evaluation
Uses syntax validation and dependency-presence checks rather than full CI/CD execution. Checks that:
1. Build file is syntactically valid
2. Required dependencies are present
3. Version constraints are reasonable

**Strength:** Well-scoped tasks with clear success criteria. Multi-language coverage (Python, Rust, JS, C#). Real repositories.

**Remaining concern:** The MCP benefit is unclear for these tasks. Sourcegraph can search for package names, but the imports are already in local code. Agents can infer dependencies from import statements without external tools.

---

## Cross-Benchmark Assessment

### 1. Difficulty Distribution (Post-Calibration)

**RESOLVED: Difficulty labels calibrated per-benchmark using objective metrics (US-005, US-006, US-017, US-018, US-019).**

| Difficulty | Count | % | Benchmarks |
|-----------|-------|---|------------|
| easy | 1 | 0.9% | crossrepo (smoke test) |
| medium | 22 | 19.0% | dibench (8), tac (5), pytorch (3), sweperf (2), repoqa (2), k8sdocs (1), crossrepo (0), swebenchpro (0) |
| hard | 58 | 50.0% | swebenchpro (13), locobench (16), repoqa (8), pytorch (6), k8sdocs (4), crossrepo (4), tac (3), largerepo (4), sweperf (1) |
| very_hard | 24 | 20.7% | swebenchpro (23), pytorch (1) |
| critical | 2 | 1.7% | pytorch (sgt-008, sgt-025) |
| expert | 9 | 7.8% | locobench (architectural_understanding) |

Calibration methodology per benchmark:
- **SWE-bench Pro**: Files changed (4-10 = hard, 11+ = very_hard)
- **PyTorch**: LOC changed (<50 = medium, 50-200 = hard, >200 = very_hard, release-engineering = critical)
- **LoCoBench**: Category-based (architectural_understanding = expert, refactoring/bug = hard)
- **RepoQA**: Source file count (<100 = medium, >100 = hard)
- Others: Unchanged from original labels (already had appropriate granularity or uniform complexity)

### 2. MCP Benefit Scores (Post-Recalculation)

**RESOLVED: Scores recalculated with per-task feature extraction (US-021).**

The formula `0.25*context_complexity + 0.30*cross_file_deps + 0.20*semantic_search_potential + 0.25*task_category_weight` now uses per-task features rather than benchmark-level defaults:

| Benchmark | Min | Max | Mean | StdDev | Features Used |
|-----------|-----|-----|------|--------|--------------|
| ccb_crossrepo | 0.655 | 0.910 | 0.836 | 0.113 | Number of repos, cross-repo complexity |
| ccb_dibench | 0.534 | 0.847 | 0.643 | 0.125 | Per-repo file counts (20-82) |
| ccb_k8sdocs | 0.378 | 0.894 | 0.663 | 0.219 | Per-package source file counts (25-450) |
| ccb_largerepo | 0.730 | 0.876 | 0.793 | 0.064 | Codebase LOC, expected files touched |
| ccb_locobench | 0.717 | 0.931 | 0.820 | 0.055 | context_length, files_count from task.toml |
| ccb_pytorch | 0.552 | 0.807 | 0.593 | 0.073 | File counts from ground truth |
| ccb_repoqa | 0.597 | 0.953 | 0.727 | 0.114 | Source file count, code_ratio |
| ccb_swebenchpro | 0.547 | 0.757 | 0.651 | 0.065 | Files changed from patch |
| ccb_sweperf | 0.433 | 0.525 | 0.475 | 0.047 | Baseline runtime for complexity scaling |
| ccb_tac | 0.350 | 0.603 | 0.491 | 0.103 | Per-category resource scaling |

Overall average: 0.6852. All benchmarks with 5+ tasks have stddev > 0.05.

**Remaining concern:** Scores are still formula-based rather than empirically calibrated against actual MCP usage data from pilot runs. The formulas produce plausible relative rankings but absolute values are not validated.

### 3. Evaluation Rigor Spectrum

From most to least rigorous:
1. **ccb_swebenchpro**: Real test suites, fail-to-pass validation (now with partial credit)
2. **ccb_pytorch**: Real PyTorch test suite (now with partial credit)
3. **ccb_largerepo**: Compilation gate + keyword scoring (upgraded from keyword-only)
4. **ccb_k8sdocs**: Keyword checks (10-point deterministic scale)
5. **ccb_locobench**: Deterministic keyword-based verification (`verify.py`) -- **CORRECTED: previously mischaracterized as LLM judge**
6. **ccb_repoqa**: Exact-match function name comparison
7. **ccb_crossrepo**: Pattern-matching on expected changes
8. **ccb_dibench**: Syntax + dependency presence validation

Notable improvements: ccb_largerepo moved from position 8 to position 3 after US-012 through US-015. ccb_locobench moved from position 8 to position 5 after correcting the evaluation method characterization. SWE-bench Pro and PyTorch now support partial credit scoring.

This variation means benchmark-to-benchmark score comparisons are not directly meaningful. A 1.0 in SWE-bench Pro (all tests pass) represents far more verification than a 1.0 in LoCoBench (keyword matching).

### 4. Metadata Status

**All previously identified metadata errors have been resolved:**

| Issue | Resolution |
|-------|-----------|
| Placeholder issue numbers `#ISSUE_NUMBER` | US-007: Replaced with actual PR numbers in sgt-002, sgt-004, sgt-009, sgt-012 |
| Truncated descriptions in sgt-005, sgt-010 | US-008: Completed from original PR bodies |
| Wrong language labels in SWE-bench Pro task.toml | US-009: 236 files corrected (element-web->TS, qutebrowser->Python, nodebb->JS, navidrome->Go) |
| Wrong language labels in selected_benchmark_tasks.json | US-010: crossrepo bug_localization_01 and refactor_rename_01 corrected from "go" to "python" |
| Wrong repo fields in crossrepo | US-004: All 4 non-smoke crossrepo tasks verified correct |
| Instruction/evaluation mismatch in crossrepo | US-001, US-002, US-003: All three expected_changes.json files rewritten |
| Copy-paste error in VSCode test script | US-011: Comment corrected from "scrollend" to "stale diagnostics" |

**RESOLVED: All remaining metadata issues fixed.**
- sgt-003 description completed with benchmark results and test plan
- sgt-021 description expanded with context from reverted PR #163712
- sgt-002 instruction rewritten to match ground truth (Inductor fusions revert, PR #168157)

### 5. SDLC Phase Coverage

The distribution remains heavily skewed toward implementation tasks, though SDLC phase labels are now more accurate:

| Phase | Tasks | % | Change |
|-------|-------|---|--------|
| Implementation (bug fix) | 54 | 47% | +3 (sweperf moved from Testing & QA) |
| Implementation (refactoring) | 15 | 13% | |
| Implementation (feature) | 8 | 7% | -8 (dibench moved to Maintenance) |
| Architecture & Design | 10 | 9% | |
| Requirements & Discovery | 12 | 10% | |
| Maintenance | 10 | 9% | +8 (dibench moved from Implementation) |
| Documentation | 5 | 4% | |
| Testing & QA | 2 | 2% | -3 (sweperf moved to Implementation) |

Bug fixes dominate. The Maintenance category is now better represented (9%) after reclassifying dibench's dependency inference tasks. Testing & QA has only 2 tasks (tac-write-unit-test and simple_test_01).

### 6. Language Distribution (Corrected)

| Language | Tasks | % |
|----------|-------|---|
| Python | 32 | 27.6% |
| Go | 22 | 19.0% |
| C++ | 19 | 16.4% |
| Rust | 12 | 10.3% |
| TypeScript | 11 | 9.5% |
| C | 7 | 6.0% |
| JavaScript | 5 | 4.3% |
| C# | 5 | 4.3% |
| Java | 2 | 1.7% |
| Python/C++ | 1 | 0.9% |

---

## Remaining Recommendations

The following issues from the original review remain open:

1. ~~**Add partial credit to binary evaluations**~~: **RESOLVED.** SWE-bench Pro (731 files) and PyTorch (24 files) now parse test output for pass/fail ratios.

2. ~~**Reconsider SDLC phase labels for sweperf and dibench**~~: **RESOLVED.** sweperf relabeled to "Implementation (bug fix)"; dibench relabeled to "Maintenance".

3. ~~**Address LoCoBench non-determinism**~~: **NON-ISSUE.** LoCoBench evaluation is deterministic keyword-based (`verify.py`), not an LLM judge. Previously mischaracterized.

4. **Validate MCP benefit scores empirically**: Replace the formula-based scores with scores calibrated against actual MCP usage patterns from pilot runs. *(Still open)*

5. ~~**Remove or reclassify simple_test_01**~~: **RESOLVED.** Marked as `exclude_from_aggregate: true` in `selected_benchmark_tasks.json`.

6. ~~**Complete remaining PyTorch metadata**~~: **RESOLVED.** sgt-003, sgt-021, and sgt-002 all fixed.

7. ~~**Address NodeBB service dependencies**~~: **NON-ISSUE.** NodeBB tasks use pre-built base Docker images (`jefzda/sweap-images`) that include Redis/MongoDB.
