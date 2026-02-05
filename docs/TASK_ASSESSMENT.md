# CodeContextBench Task Assessment

## Overview

CodeContextBench comprises 116 tasks across 10 benchmarks, designed to evaluate AI coding agents on software engineering tasks that benefit from rich code context (e.g., via MCP-based tools like Sourcegraph). Tasks span 10 programming languages, 8 SDLC phases, and 6 difficulty tiers.

| Benchmark | Tasks | Languages | Difficulty Range | Evaluation Method |
|-----------|-------|-----------|-----------------|-------------------|
| ccb_swebenchpro | 36 | Python, Go, TypeScript, JavaScript | hard -- very_hard | Real test suites with partial credit |
| ccb_locobench | 25 | Python (synthetic) | hard -- expert | Deterministic keyword verification |
| ccb_pytorch | 12 | Python, C++ | medium -- critical | PyTorch CI test suite (with partial credit) |
| ccb_repoqa | 10 | C++, Java, Python, Rust, TypeScript | medium -- hard | Function name exact match |
| ccb_dibench | 8 | Python, Rust, JavaScript, C# | medium | Syntax + dependency validation |
| ccb_tac | 8 | C++, Python, TypeScript | medium -- hard | Framework-specific (compilation, test, search) |
| ccb_k8sdocs | 5 | Go | medium -- hard | Keyword checks (10-point scale) |
| ccb_crossrepo | 5 | Go, Python | easy -- hard | Patch pattern matching |
| ccb_largerepo | 4 | Go, Rust, Python/C++, TypeScript | hard | Compilation gate + keyword scoring |
| ccb_sweperf | 3 | Python | medium -- hard | SWE-bench-style test execution |

---

## Difficulty Distribution

| Tier | Count | % | Definition |
|------|-------|---|-----------|
| easy | 1 | 0.9% | Smoke test / connectivity verification |
| medium | 22 | 19.0% | Focused single-concern tasks (<50 LOC, <100 source files, or dependency-only changes) |
| hard | 58 | 50.0% | Multi-file tasks requiring cross-module understanding (4-10 files, 50-200 LOC, or >100 source files) |
| very_hard | 24 | 20.7% | Large-scale multi-file changes (10+ files changed, >200 LOC) |
| critical | 2 | 1.7% | Release-engineering-scale changes (800+ LOC, 100+ files); no time limit |
| expert | 9 | 7.8% | Full-codebase architectural analysis (>1M tokens context) |

Calibration methodology varies by benchmark: SWE-bench Pro uses files changed, PyTorch uses LOC, LoCoBench uses task category, RepoQA uses repository size. Benchmarks with uniform native difficulty (dibench, tac, k8sdocs, largerepo, sweperf, crossrepo) retain their original labels where appropriate.

---

## SDLC Phase Distribution

| Phase | Tasks | % | Primary Benchmarks |
|-------|-------|---|--------------------|
| Implementation (bug fix) | 54 | 47% | swebenchpro (36), pytorch (11), locobench (3), sweperf (3), crossrepo (1) |
| Implementation (refactoring) | 15 | 13% | locobench (13), crossrepo (2) |
| Requirements & Discovery | 12 | 10% | repoqa (10), tac (2) |
| Maintenance | 10 | 9% | dibench (8), tac (2) |
| Architecture & Design | 10 | 9% | locobench (9), crossrepo (1) |
| Implementation (feature) | 8 | 7% | largerepo (4), tac (3), pytorch (1) |
| Documentation | 5 | 4% | k8sdocs (5) |
| Testing & QA | 2 | 2% | tac (1), crossrepo (1) |

The distribution is heavily weighted toward implementation tasks (67%). Maintenance is now better represented (9%) after reclassifying dibench tasks from "Implementation (feature)".

---

## Language Distribution

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

## MCP Benefit Scores

Each task has an MCP benefit score (0-1) estimating how much an agent would benefit from MCP-based context tools. The score is computed as:

`0.25 * context_complexity + 0.30 * cross_file_deps + 0.20 * semantic_search_potential + 0.25 * task_category_weight`

Components are derived from per-task features (files changed, context length, repository size, code ratio) rather than benchmark-level defaults.

| Benchmark | Min | Max | Mean | StdDev |
|-----------|-----|-----|------|--------|
| ccb_crossrepo | 0.655 | 0.910 | 0.836 | 0.113 |
| ccb_dibench | 0.534 | 0.847 | 0.643 | 0.125 |
| ccb_k8sdocs | 0.378 | 0.894 | 0.663 | 0.219 |
| ccb_largerepo | 0.730 | 0.876 | 0.793 | 0.064 |
| ccb_locobench | 0.717 | 0.931 | 0.820 | 0.055 |
| ccb_pytorch | 0.552 | 0.807 | 0.593 | 0.073 |
| ccb_repoqa | 0.597 | 0.953 | 0.727 | 0.114 |
| ccb_swebenchpro | 0.547 | 0.757 | 0.651 | 0.065 |
| ccb_sweperf | 0.433 | 0.525 | 0.475 | 0.047 |
| ccb_tac | 0.350 | 0.603 | 0.491 | 0.103 |

Overall average: 0.6852. Scores are formula-based and have not been empirically validated against actual MCP usage data.

---

## Per-Benchmark Assessment

### 1. ccb_swebenchpro (36 tasks)

**Source:** SWE-bench Pro (ScaleAI). Real bug fixes across 11 repositories.

| Repository | Language | Tasks | Difficulty |
|-----------|----------|-------|-----------|
| ansible/ansible | Python | 5 | 2 hard, 3 very_hard |
| flipt-io/flipt | Go | 4 | 4 very_hard |
| gravitational/teleport | Go | 4 | 4 very_hard |
| internetarchive/openlibrary | Python | 4 | 2 hard, 2 very_hard |
| qutebrowser/qutebrowser | Python | 4 | 4 hard |
| protonmail/webclients | TypeScript | 4 | 4 very_hard |
| NodeBB/NodeBB | JavaScript | 3 | 3 very_hard |
| future-architect/vuls | Go | 3 | 1 hard, 2 very_hard |
| navidrome/navidrome | Go | 2 | 2 hard |
| element-hq/element-web | TypeScript | 2 | 2 hard |
| tutao/tutanota | TypeScript | 1 | 1 very_hard |

**Evaluation:** Most rigorous in the benchmark suite. Uses the standard SWE-bench framework: all fail-to-pass tests must pass AND all pass-to-pass tests must still pass. Now includes partial credit scoring -- when tests fail, the fraction of passed tests is reported (pytest summary parsing for Python, `--- PASS`/`--- FAIL` counting for Go).

**Strengths:**
- Real test suites, real patches, real CI validation
- Reproducible evaluation
- Well-established SWE-bench format
- Partial credit captures progress even on incomplete fixes

**Weaknesses:**
- All instructions use identical boilerplate ("Analyze issue -> Explore codebase -> Implement fix -> Ensure tests pass") with no task-specific guidance

---

### 2. ccb_locobench (25 tasks)

**Source:** Synthetic codebases with 70+ files and 700K-1.16M tokens of context. Three task categories.

| Category | Count | Difficulty | SDLC Phase |
|----------|-------|-----------|------------|
| architectural_understanding | 9 | expert | Architecture & Design |
| cross_file_refactoring | 13 | hard | Implementation (refactoring) |
| bug_investigation | 3 | hard | Implementation (bug fix) |

**Evaluation:** Deterministic keyword-based verification (`verify.py`) scores agent output against ground truth criteria in `ground_truth.json`. **Note:** Previously mischaracterized as an LLM judge; evaluation is fully deterministic and reproducible.

**Strengths:**
- Well-defined evaluation criteria with detailed expected answers
- Good category diversity testing different agent capabilities
- Large context windows stress-test agent comprehension
- Deterministic, reproducible scoring (not LLM-judge based)

**Weaknesses:**
- Synthetic codebases use `module_1.py` through `module_73.py` naming, lacking organic structure and semantic filename hints
- `repo` field is empty for all tasks, preventing MCP Sourcegraph indexing
- Narrow metadata ranges (context_length 975K-1.16M, files 73-86) mean tasks are more homogeneous than the category split suggests

---

### 3. ccb_pytorch (12 tasks)

**Source:** Real PyTorch pull requests. Each provides a ground-truth commit.

| Task ID | Description | LOC | Difficulty |
|---------|------------|-----|-----------|
| sgt-001 | NCCL thread safety | 94 | hard |
| sgt-002 | Revert Inductor ReLU/GELU(Addmm) fusions | 180 | hard |
| sgt-003 | Cleanup graph reference cycles | 38 | medium |
| sgt-005 | ROCm shared memory pruning | 22 | medium |
| sgt-008 | Release 2.10 branch changes | 808 | critical |
| sgt-009 | HOP print functionalize | 87 | hard |
| sgt-010 | cuDNN runtime version exposure | 52 | hard |
| sgt-012 | Invalid grid config generation | 25 | medium |
| sgt-014 | Dynamo resume KeyError fix | 242 | very_hard |
| sgt-016 | Graph partition memory plan | 93 | hard |
| sgt-021 | Allgather/scatter contiguity | 59 | hard |
| sgt-025 | CUDA 12.9 nightly build | 3526 | critical |

**Evaluation:** `make test` against real PyTorch CI test suite with partial credit scoring (parses pytest summary for pass/fail ratios). sgt-001 is an exception with a custom 81-line pattern-based validator.

**Strengths:**
- Ground truth anchored to real commits with known diffs
- Test suites are the actual PyTorch CI tests
- Good difficulty spread from 22-LOC fixes to 3526-LOC infrastructure changes
- Partial credit scoring captures progress even when not all tests pass

**Weaknesses:**
- The two critical tasks (sgt-008: 110 files, sgt-025: 3526 LOC) are release-engineering scale and test fundamentally different capabilities than the bug-fix tasks
- Evaluation inconsistency: sgt-001 uses pattern matching while all others use make test

---

### 4. ccb_repoqa (10 tasks)

**Source:** RepoQA benchmark. Semantic code navigation -- find a function from a natural-language behavioral description without knowing its name.

| Language | Repositories | Difficulty |
|----------|-------------|-----------|
| C++ | log4cxx, uvw | hard, medium |
| Java | gson, retrofit | hard, hard |
| Python | black, poetry | hard, hard |
| Rust | nom, helix | medium, hard |
| TypeScript | transformers.js, express | hard, hard |

**Evaluation:** `SemanticRetrievalQAVerifier` compares agent's `solution.json` against ground truth. Correct function path + name = 1.0, partial matches = 0.3-0.9, wrong function = 0.0.

**Strengths:**
- Clean experimental design with unambiguous ground truth
- Naturally suited to testing MCP semantic search vs. local grep
- Good language diversity (5 languages, 2 tasks each)

**Weaknesses:**
- Two difficulty tiers (medium for repos with <100 files, hard for >100) is coarse; actual search difficulty depends on code structure beyond file count

---

### 5. ccb_dibench (8 tasks)

**Source:** DI-Bench. Dependency inference -- add missing dependencies to build files so code compiles.

| Language | Tasks | Repos |
|----------|-------|-------|
| Python | 2 | inducer/cgen, RhinoSecurityLabs/IAMActionHunter |
| Rust | 2 | mitsuhiko/similar-asserts, rusticata/pcap-parser |
| JavaScript | 2 | eslint/markdown, motdotla/dotenv-expand |
| C# | 2 | irongut/CodeCoverageSummary, DotNetKoans/DotNetKoans |

All tasks are difficulty **medium**, SDLC phase **Maintenance**.

**Evaluation:** Syntax validation + dependency-presence checks. Build file must be valid and contain required dependencies with reasonable version constraints.

**Strengths:**
- Well-scoped with clear success criteria
- Multi-language coverage (4 languages, 2 each)
- Real repositories
- SDLC phase correctly reflects maintenance/configuration nature of the work

**Weaknesses:**
- MCP benefit is questionable: import statements are already in local code, so the agent can infer dependencies without external search tools
- All tasks are "medium" with no variation, despite repos ranging from 20-82 files

---

### 6. ccb_tac (8 tasks)

**Source:** TAC (Tool-Augmented Coding) benchmark. Diverse task types.

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

**Evaluation:** Framework-specific. Find-in-codebase checks correct file/function identification. Implementation tasks verify compilation and tests. Dependency tasks check correct package versions.

**Strengths:**
- Best SDLC phase diversity of any benchmark (5 phases represented)
- Tasks test genuinely different agent capabilities (implementation, search, troubleshooting, testing)
- Good difficulty variation matching actual complexity

**Weaknesses:**
- Small task count (8) limits statistical power
- Two find-in-codebase tasks on the same repo (llama.cpp) reduces repo diversity

---

### 7. ccb_k8sdocs (5 tasks)

**Source:** Kubernetes documentation generation. The agent writes `doc.go` files for packages where existing documentation has been stripped.

| Task ID | Package | Difficulty | Ground Truth Size |
|---------|---------|-----------|-------------------|
| apiserver-doc-001 | k8s.io/apiserver | hard | 75 lines |
| applyconfig-doc-001 | applyconfigurations | hard | 150 lines |
| client-go-doc-001 | client-go | hard | 110 lines |
| fairqueuing-doc-001 | queueset (fair queuing) | hard | 119 lines |
| pkg-doc-001 | kubelet/cm | medium | 113 lines |

**Evaluation:** Keyword-based checks (grep for domain-specific terms) on a 10-point scale. A richer LLM-judge evaluation is defined in `reward.json` / `evaluate_docs.py` but is not automatically invoked.

**Strengths:**
- Well-crafted instructions with clear requirements
- Ground truths are proportionate (75-150 lines each) and high quality
- Stripped-documentation approach is a clean experimental design

**Weaknesses:**
- Two-tier evaluation is not integrated -- the keyword test and LLM judge can diverge
- `fairqueuing-doc-001` requires understanding WFQ algorithms and mathematical formulas, making it substantially harder than the other "hard" tasks; it could justify a separate tier
- Single language (Go) limits generalizability of documentation-writing assessment

---

### 8. ccb_crossrepo (5 tasks)

**Source:** Cross-repository tasks requiring understanding across multiple codebases.

| Task ID | Category | Repos | Difficulty |
|---------|----------|-------|-----------|
| api_upgrade_01 | api_upgrade | etcd, kubernetes, containerd | hard |
| bug_localization_01 | bug_localization | numpy, pandas, scikit-learn | hard |
| cross_file_reasoning_01 | cross_file_reasoning | kubernetes, containerd | hard |
| refactor_rename_01 | refactor_rename | Django, Flask, requests | hard |
| simple_test_01 | smoke_test | -- | easy |

**Evaluation:** `validate_patch.py` checks expected files modified, expected patterns present (removed/added regex), and expected content strings.

**Strengths:**
- Unique multi-repository requirement tests cross-codebase reasoning
- Good category diversity (API upgrade, bug localization, reasoning, refactoring)
- Pattern-matching evaluation is more targeted than keyword grep

**Weaknesses:**
- `simple_test_01` is a smoke test for MCP connectivity, not a substantive coding task (now marked `exclude_from_aggregate`)
- Pattern-matching evaluation doesn't verify semantic correctness beyond regex presence
- Only 4 substantive tasks is too small for statistical significance
- Two tasks use Python repos and two use Go repos, but the benchmark's value proposition is cross-repo reasoning -- language matters less than the multi-repo aspect

---

### 9. ccb_largerepo (4 tasks)

**Source:** Feature implementation in massive real-world repositories (1-1.6GB codebases).

| Task ID | Repo | Language | What It Asks |
|---------|------|----------|-------------|
| big-code-k8s-001 | kubernetes | Go | Implement `NoScheduleNoTraffic` taint effect |
| big-code-servo-001 | servo | Rust | Implement `scrollend` DOM event |
| big-code-trt-001 | tensorrt-llm | Python/C++ | Add `W4A8_MXFP4_INT8` quantization mode |
| big-code-vsc-001 | vscode | TypeScript | Fix stale diagnostics after git branch switch |

All tasks are difficulty **hard**, SDLC phase **Implementation (feature)** (though big-code-vsc-001 is arguably a bug fix).

**Evaluation:** Three-stage pipeline:
1. Compilation gate (go build / cargo check / py_compile / tsc --noEmit) -- failure sets score to 0.0
2. Unit test execution where feasible (best-effort, non-fatal)
3. Keyword-based scoring for feature completeness

**Strengths:**
- Authentic complexity from real massive codebases
- Compilation gates ensure syntactically valid code
- Well-prepared MCP infrastructure for code navigation
- Good language diversity (Go, Rust, Python/C++, TypeScript)

**Weaknesses:**
- Only 4 tasks limits statistical power
- `reward.json` "rating" criteria (architecture_understanding, etc.) are defined but never automatically evaluated
- Keyword scoring after compilation is still a weak proxy for functional correctness
- big-code-trt-001 C++ syntax check is informational-only (CUDA headers unavailable in Docker), so C++ changes are not truly validated

---

### 10. ccb_sweperf (3 tasks)

**Source:** Performance optimization tasks from SWE-bench.

| Task ID | Repo | Difficulty |
|---------|------|-----------|
| sweperf-001 | numpy | medium |
| sweperf-002 | scikit-learn | hard |
| sweperf-003 | pandas | medium |

All labeled SDLC phase **Implementation (bug fix)**.

**Evaluation:** SWE-bench-style test execution (fail-to-pass / pass-to-pass lists).

**Strengths:**
- Tests a distinct capability (performance optimization) not covered elsewhere
- SWE-bench evaluation format is rigorous and reproducible
- SDLC phase correctly reflects that these are performance regression fixes

**Weaknesses:**
- Only 3 tasks -- too few for meaningful statistics
- Evaluation verifies functional correctness but does not measure whether performance actually improved
- Single language (Python) limits scope

---

## Evaluation Rigor Ranking

Benchmarks vary significantly in how rigorously they verify agent output. From most to least rigorous:

| Rank | Benchmark | Method | Key Limitation |
|------|-----------|--------|---------------|
| 1 | ccb_swebenchpro | Real test suites, fail-to-pass (with partial credit) | Generic instruction template |
| 2 | ccb_pytorch | Real PyTorch CI tests (with partial credit) | Inconsistent (sgt-001 differs) |
| 3 | ccb_largerepo | Compilation gate + keyword scoring | Keywords are weak correctness proxy |
| 4 | ccb_k8sdocs | Keyword checks (10-point scale) | Single language (Go) |
| 5 | ccb_locobench | Deterministic keyword verification | Synthetic codebases |
| 6 | ccb_repoqa | Function name exact match | Partial match scoring is opaque |
| 7 | ccb_crossrepo | Patch pattern matching | No semantic correctness check |
| 8 | ccb_dibench | Syntax + dependency presence | No build/import verification |

**Note:** LoCoBench evaluation was previously mischaracterized as an LLM judge. It uses deterministic keyword-based verification (`verify.py`), making it reproducible and more rigorous than previously assessed.

A score of 1.0 in ccb_swebenchpro (all tests pass) represents substantially more verification than a score of 1.0 in ccb_locobench (keyword matching). Cross-benchmark score comparisons should account for this gap.

---

## Assessment Summary

**Well-constructed tasks:** SWE-bench Pro provides the gold standard with real test suites. TAC offers the best SDLC diversity. RepoQA has a clean experimental design with unambiguous ground truth. K8sDocs has proportionate ground truth exemplars.

**Resolved concerns:**
- Partial credit scoring added to SWE-bench Pro (731 files) and PyTorch (24 files)
- LoCoBench evaluation confirmed as deterministic keyword-based (not LLM judge)
- SDLC phase labels corrected: sweperf → "Implementation (bug fix)", dibench → "Maintenance"
- `simple_test_01` marked as `exclude_from_aggregate`
- RepoQA `model_hint = "requires-mcp"` removed
- PyTorch instruction issues fixed: sgt-002 rewritten, sgt-003 completed, sgt-021 expanded

**Remaining concerns:**
- The benchmark heavily favors implementation tasks (67%) with minimal representation of Testing & QA (2%)
- Three benchmarks have 3-5 tasks each (sweperf, crossrepo, largerepo), limiting per-benchmark statistical power
- MCP benefit scores are formula-based and not empirically validated
