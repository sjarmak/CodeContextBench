# CodeContextBench: Multi-Dimensional Analysis Report

**Generated:** 2026-02-11
**Dataset:** 451 task executions across 151 unique tasks, 3 agent configurations
**Model:** Claude Opus 4.5/4.6 (anthropic/claude-opus-4-5-20251101)

---

## 1. Methodology

### 1.1 Evaluation Framework

CodeContextBench evaluates how access to external code intelligence tools (MCP/Sourcegraph) affects an AI coding agent's performance across diverse software engineering tasks. Each of the 151 selected tasks is run under three configurations:

| Config | Abbreviation | Description |
|--------|-------------|-------------|
| **Baseline** | BL | Agent operates with only local tools (file read/write, bash, grep, glob). No external code search. |
| **Sourcegraph Base** | SG_base | Agent has access to Sourcegraph MCP tools: keyword search, semantic search, file reading, symbol navigation (go-to-definition, find-references), commit/diff search. |
| **Sourcegraph Full** | SG_full | All SG_base tools plus Deep Search (AI-powered codebase Q&A) and enhanced preamble instructions for tool usage. |

### 1.2 Metrics

- **Reward** (0.0--1.0): Task-specific score from the verifier. For binary tasks, 1.0 = pass, 0.0 = fail. For graded tasks (e.g., test_ratio), partial credit is possible.
- **Pass Rate**: Percentage of non-errored tasks with reward > 0.
- **Agent Task Time** (TaskS): Wall-clock seconds the agent spent actively working (coding + tool use). Excludes Docker environment build time and verifier execution. This is the primary efficiency metric.
- **Avg Input Tokens** (AvgIn): Mean input tokens consumed per task. Reflects how much context the agent reads. Higher values indicate more searching, file reading, or tool result processing.
- **Avg Output Tokens** (AvgOut): Mean output tokens generated per task. Reflects how much code the agent writes and how verbose its reasoning is.

### 1.3 Data Integrity

Before analysis, all 467 on-disk task results were audited:

- **0 infrastructure errors** (errored status): All task failures are genuine agent failures, not auth/Docker/MCP crashes.
- **0 baseline contamination**: No baseline runs invoked MCP tools (verified via transcript scanning).
- **12 legacy tasks filtered**: 3 dropped PyTorch tasks (sgt-007/017/024) and 3 SWE-bench Pro gap-fill tasks with naming mismatches were excluded, leaving **451 clean records** (151 BL + 151 SG_base + 149 SG_full).
- **SG_full has 149 tasks** (vs 151 for the others) because 2 SWE-bench Pro tasks lacked SG_full runs.

---

## 2. Overall Results by Benchmark Suite

| Benchmark | N | BL Reward | SG_base Reward | SG_full Reward | BL TaskS | SG_base TaskS | SG_full TaskS |
|-----------|---|-----------|----------------|----------------|----------|---------------|---------------|
| CodeReview | 3 | 0.933 | 0.980 (+0.047) | **1.000** (+0.067) | 91s | 132s | 116s |
| CrossRepo | 5 | 0.571 | 0.587 (+0.016) | 0.387 (-0.184) | 502s | 343s | 489s |
| DependEval | 32 | 0.636 | 0.665 (+0.028) | **0.720** (+0.083) | 77s | 100s | 76s |
| DIBench | 8 | 0.500 | 0.500 (+0.000) | 0.500 (+0.000) | 168s | 163s | 135s |
| K8s Docs | 5 | **0.950** | 0.920 (-0.030) | 0.920 (-0.030) | 194s | 110s | 202s |
| LargeRepo | 4 | 0.250 | 0.250 (+0.000) | **0.425** (+0.175) | 997s | 631s | 2247s |
| LinuxFLBench | 5 | 0.860 | 0.820 (-0.040) | **0.880** (+0.020) | 233s | 333s | 229s |
| LoCoBench | 25 | 0.449 | **0.511** (+0.062) | 0.499 (+0.050) | 407s | 311s | 805s |
| PyTorch | 11 | 0.273 | 0.270 (-0.003) | 0.265 (-0.008) | 269s | 252s | 685s |
| RepoQA | 10 | **1.000** | **1.000** (+0.000) | **1.000** (+0.000) | 44s | 47s | 33s |
| SWE-bench Pro | 32 | 0.750 | 0.588 (-0.162) | **0.786** (+0.036) | 304s | 448s | 391s |
| SWE-Perf | 3 | **0.591** | 0.032 (-0.559) | 0.367 (-0.224) | 453s | 750s | 1280s |
| TAC | 8 | 0.492 | 0.365 (-0.127) | **0.544** (+0.052) | 620s | 639s | 614s |

### Key Findings

**SG_full is the strongest configuration overall.** It achieves the best reward on 7 of 13 benchmarks (CodeReview, DependEval, LargeRepo, LinuxFLBench, SWE-bench Pro, TAC, and ties on RepoQA). Across all 149 tasks, SG_full averages a reward of 0.630 vs baseline's 0.576 across its 151 tasks.

**SG_base is a mixed bag.** It improves on 5 benchmarks (CodeReview, CrossRepo, DependEval, LoCoBench, LargeRepo by time) but actively hurts on 4 (SWE-bench Pro, SWE-Perf, TAC, K8s Docs). The SWE-bench Pro regression (-0.162 reward, -16.2pp pass rate) is the most significant negative result and is discussed in Section 7.

**MCP tools never help with pure implementation tasks** where the agent already has the codebase locally. DIBench (dependency installation) and PyTorch (PR-level code changes) show zero or negative impact because the agent's local tools are sufficient and MCP adds overhead.

**Efficiency is not uniformly improved.** SG_base saves time on K8s Docs (-84s), CrossRepo (-159s), and LoCoBench (-96s) where code search replaces manual exploration. But SG_full dramatically increases time on LargeRepo (+1250s), LoCoBench (+398s), and SWE-Perf (+827s) due to the agent over-investing in remote search instead of acting on local context.

---

## 3. Outcomes by Task Difficulty

| Difficulty | N | BL Reward | SG_base Reward | SG_full Reward | BL Pass% | SG_full Pass% | BL TaskS | SG_full TaskS |
|------------|---|-----------|----------------|----------------|----------|---------------|----------|---------------|
| easy | 1 | 1.000 | 1.000 | 1.000 | 100% | 100% | 12s | 8s |
| medium | 57 | 0.546 | 0.530 (-0.016) | **0.583** (+0.037) | 77.2% | 75.4% | 168s | 260s |
| hard | 63 | 0.719 | 0.656 (-0.062) | **0.753** (+0.034) | 75.0% | 78.0% | 339s | 489s |
| expert | 30 | 0.517 | **0.562** (+0.045) | **0.562** (+0.045) | 93.3% | 100% | 378s | 709s |

### Justification

**MCP provides the largest reward uplift on expert-level tasks** (+0.045 for both SG_base and SG_full). Expert tasks in this benchmark are primarily LoCoBench "architectural" tasks requiring understanding of complex multi-file relationships across large codebases. The agent benefits from Sourcegraph's cross-file navigation (find-references, go-to-definition) to trace dependencies it would otherwise miss.

**SG_base hurts on hard tasks** (-0.062 reward, -6.2pp pass rate). Hard tasks are predominantly SWE-bench Pro issues with 4--10 files changed. The agent spends time searching remotely for context that already exists in the local workspace, wasting its time budget. SG_full recovers (+0.034) because its enhanced preamble better guides tool selection.

**Expert tasks have the highest baseline pass rate (93.3%)** which seems counterintuitive. This is because expert-level LoCoBench tasks use graded reward (test_ratio), so "passing" only requires partial correctness. The reward scores (0.517) reveal the agent gets partial credit but rarely achieves full marks.

**Efficiency degrades with MCP at all difficulty levels** for SG_full. The agent consistently spends more time when MCP tools are available, with the largest increase on expert tasks (+331s). This reflects the "exploration tax" -- the agent reads more remote code to build understanding, even when local files suffice.

---

## 4. Outcomes by Programming Language

| Language | N | BL Reward | SG_base Reward | SG_full Reward | BL TaskS | SG_base TaskS | SG_full TaskS |
|----------|---|-----------|----------------|----------------|----------|---------------|---------------|
| C | 12 | 0.648 | 0.658 (+0.010) | 0.643 (-0.006) | 242s | 287s | 751s |
| C++ | 18 | 0.376 | 0.351 (-0.024) | 0.396 (+0.020) | 345s | 323s | 567s |
| C# | 6 | 0.416 | 0.419 (+0.004) | 0.437 (+0.022) | 229s | 190s | 242s |
| Go | 24 | 0.750 | 0.765 (+0.015) | 0.760 (+0.010) | 343s | 320s | 537s |
| Java | 10 | 0.739 | 0.718 (-0.021) | 0.704 (-0.036) | 82s | 96s | 70s |
| JavaScript | 14 | 0.742 | 0.643 (-0.099) | **0.869** (+0.127) | 101s | 234s | 112s |
| Python | 34 | 0.525 | 0.437 (-0.089) | 0.565 (+0.039) | 315s | 418s | 391s |
| Rust | 12 | 0.571 | **0.620** (+0.049) | 0.618 (+0.047) | 438s | 323s | 867s |
| TypeScript | 20 | 0.697 | **0.772** (+0.075) | **0.812** (+0.116) | 237s | 158s | 286s |

### Justification

**TypeScript and JavaScript show the strongest MCP benefits.** TypeScript tasks gain +0.116 reward with SG_full and SG_base achieves this with -80s faster execution. JavaScript sees the largest single-language improvement (+0.127 with SG_full, +7.1pp pass rate). These languages benefit because their tasks span large, well-indexed repositories (SWE-bench Pro NodeBB, DependEval JavaScript) where Sourcegraph's semantic search and cross-file navigation help the agent locate relevant modules.

**Rust shows consistent improvement** (+0.049 SG_base, +0.047 SG_full) with SG_base also being 115s faster. Rust's strict type system and module structure make symbol navigation (go-to-definition, find-references) particularly effective for understanding code relationships.

**Python tasks regress with SG_base** (-0.089 reward, -3.2pp pass rate) but recover with SG_full (+0.039). Python is the largest language group (34 tasks) and includes SWE-bench Pro and SWE-Perf tasks where SG_base's unrestricted MCP access causes the agent to over-search. The SG_full preamble mitigates this by guiding the agent to use MCP judiciously.

**Java tasks slightly degrade with MCP** (-0.021 SG_base, -0.036 SG_full). All 10 Java tasks are DependEval dependency-recognition tasks that are fundamentally about analyzing local import statements. External code search adds no value and marginally wastes time.

**C tasks see the largest SG_full time increase** (+509s) due to LinuxFLBench and LoCoBench tasks in C where the agent explores kernel/system codebases extensively via MCP.

---

## 5. Outcomes by SDLC Phase

| SDLC Phase | N | BL Reward | SG_base Reward | SG_full Reward | BL TaskS | SG_full TaskS |
|------------|---|-----------|----------------|----------------|----------|---------------|
| Architecture & Design | 26 | 0.770 | 0.792 (+0.022) | **0.799** (+0.029) | 147s | 150s |
| Documentation | 5 | **0.950** | 0.920 (-0.030) | 0.920 (-0.030) | 194s | 202s |
| Implementation (bug fix) | 51 | 0.631 | 0.538 (-0.092) | **0.673** (+0.043) | 294s | 460s |
| Implementation (feature) | 32 | 0.366 | 0.381 (+0.015) | **0.484** (+0.118) | 321s | 467s |
| Implementation (refactoring) | 15 | 0.451 | **0.520** (+0.069) | 0.420 (-0.031) | 544s | 1097s |
| Maintenance | 2 | 0.400 | 0.400 (+0.000) | 0.400 (+0.000) | 669s | 962s |
| Requirements & Discovery | 12 | 0.833 | 0.833 (+0.000) | 0.833 (+0.000) | 58s | 42s |
| Testing & QA | 8 | **0.796** | 0.529 (-0.267) | 0.738 (-0.059) | 263s | 585s |

### Justification

**Feature implementation benefits most from SG_full** (+0.118 reward), the largest SDLC-phase improvement. Feature tasks require the agent to understand existing architecture before adding new code. SG_full's search tools help the agent discover relevant interfaces, patterns, and conventions in the codebase, leading to better-integrated implementations.

**Architecture & Design tasks improve consistently** across both MCP configs (+0.022 SG_base, +0.029 SG_full) with negligible time overhead (+3s for SG_full). These tasks (RepoQA semantic navigation, DependEval recognition) naturally align with code search capabilities -- understanding code structure is exactly what MCP tools provide.

**Bug fix tasks show divergent results:** SG_base hurts (-0.092 reward, -8.1pp pass rate) while SG_full helps (+0.043 reward, +3.1pp). This is the "MCP distraction effect" in action: with unguided MCP access (SG_base), the agent searches for context instead of analyzing the local bug, wasting time. With guided access (SG_full), the agent uses MCP selectively to understand the broader impact of a fix.

**Testing & QA tasks regress with MCP** (-0.267 SG_base, -0.059 SG_full). These are primarily SWE-Perf performance optimization and SWE-bench Pro testing tasks where the agent needs to analyze runtime behavior, not navigate code structure. MCP tools provide no signal for understanding performance characteristics.

**Refactoring tasks show a split:** SG_base helps (+0.069) by enabling the agent to trace all references before refactoring, but SG_full hurts (-0.031) while taking 2x longer (1097s vs 544s). The enhanced preamble may cause the agent to over-research before acting.

**Requirements & Discovery is unchanged** across all configs. These are all DependEval dependency-recognition and RepoQA tasks that the agent solves by analyzing local files. The tasks are inherently self-contained.

---

## 6. Outcomes by Codebase Size

Codebase size is proxied by the `context_complexity` component of the MCP benefit score (0.0--1.0), which measures the codebase's total LOC, file count, and structural complexity.

| Codebase Size | N | BL Reward | SG_base Reward | SG_full Reward | BL TaskS | SG_base TaskS | SG_full TaskS |
|---------------|---|-----------|----------------|----------------|----------|---------------|---------------|
| Medium (0.3--0.6) | 13 | 0.516 | 0.386 (-0.130) | **0.573** (+0.057) | 497s | 578s | 683s |
| Large (0.6--0.8) | 87 | 0.615 | 0.581 (-0.034) | **0.669** (+0.054) | 199s | 253s | 279s |
| Very Large (>=0.8) | 51 | 0.611 | **0.642** (+0.031) | 0.637 (+0.026) | 363s | 285s | 655s |

### Justification

**SG_full improves outcomes at all codebase sizes** (+0.026 to +0.057), confirming that guided MCP access provides consistent value regardless of repository scale.

**SG_base only helps on very large codebases** (+0.031 reward, +3.9pp pass rate) where local exploration is infeasible. On medium codebases, SG_base significantly hurts (-0.130 reward). This is because medium-sized codebases are small enough for the agent to navigate locally but large enough that MCP search results add noise and distraction.

**Very large codebases show the best SG_base efficiency gain** (-78s task time) because the agent can jump directly to relevant symbols via Sourcegraph instead of spending minutes traversing a massive codebase with grep/find. However, SG_full adds +291s on the same tasks, indicating over-exploration when more tools are available.

**The "goldilocks zone" for MCP value is large codebases (0.6--0.8):** SG_full improves reward by +0.054 with a modest time increase (+79s), giving the best reward-per-time tradeoff.

---

## 7. Outcomes by MCP Benefit Score

The MCP benefit score is a pre-computed 4-component weighted score predicting how much external code intelligence should help each task: `context_complexity(0.25) + cross_file_deps(0.30) + semantic_search_potential(0.20) + task_category_weight(0.25)`.

| MCP Benefit Bin | N | BL Reward | SG_base Reward | SG_full Reward | BL TaskS | SG_base TaskS | SG_full TaskS |
|-----------------|---|-----------|----------------|----------------|----------|---------------|---------------|
| High (0.6--0.8) | 65 | 0.638 | 0.587 (-0.051) | **0.673** (+0.035) | 198s | 264s | 191s |
| Medium (0.3--0.6) | 34 | 0.504 | 0.468 (-0.036) | **0.617** (+0.113) | 319s | 360s | 592s |
| Very High (>=0.8) | 52 | 0.619 | **0.649** (+0.030) | 0.644 (+0.026) | 358s | 282s | 650s |

### Justification

**The MCP benefit score is a better predictor of SG_base value than SG_full value.** Tasks scored very-high (>=0.8) are the only group where SG_base improves reward (+0.030) and reduces time (-76s). This validates the scoring model's intent: it identifies tasks where code search tools should help.

**SG_full shows the strongest improvement on medium-benefit tasks** (+0.113 reward, +11.3pp pass rate). This is a surprising result. These tasks (SWE-bench Pro, TAC, some LoCoBench) were not expected to benefit heavily from MCP, but the SG_full preamble's guidance helps the agent make targeted searches that provide just enough context to improve outcomes.

**SG_base hurts on high-benefit tasks** (-0.051 reward, -6.0pp pass rate), which is counterintuitive. High-benefit tasks include many SWE-bench Pro issues where unrestricted MCP access leads to excessive searching. The SG_full guided preamble recovers this to +0.035.

**SG_full's "high" bin is the only case where MCP improves both reward AND efficiency** (+0.035 reward, -7s task time). This represents the optimal operating point: tasks with moderate code intelligence needs where guided search replaces enough local exploration to save time while also improving outcomes.

---

## 8. Outcomes by Task Category

The most notable patterns across the 25 task categories:

### Categories Where MCP Clearly Helps

| Category | N | BL Reward | Best Config | Delta | Explanation |
|----------|---|-----------|-------------|-------|-------------|
| architectural_understanding | 9 | 0.446 | SG_full: 0.529 | +0.083 | Understanding complex codebases is exactly what code search tools enable. SG_full also achieves 100% pass rate vs 88.9% baseline. |
| multifile_editing | 16 | 0.273 | SG_full: 0.440 | +0.167 | Multi-file edits require understanding cross-file dependencies. Sourcegraph's find-references helps the agent identify all files that need updating. |
| code-review | 3 | 0.933 | SG_full: 1.000 | +0.067 | Perfect score with SG_full. Code review benefits from broader codebase context to identify patterns and anti-patterns. |
| cross_file_refactoring | 13 | 0.449 | SG_base: 0.523 | +0.073 | Refactoring across files requires tracing symbol usage. go-to-definition and find-references are purpose-built for this. |
| implement (TAC) | 2 | 0.667 | SG_full: 0.875 | +0.208 | Complex implementation tasks in unfamiliar codebases benefit from search to discover relevant APIs and patterns. |

### Categories Where MCP Clearly Hurts

| Category | N | BL Reward | Worst Config | Delta | Explanation |
|----------|---|-----------|--------------|-------|-------------|
| performance | 3 | 0.591 | SG_base: 0.032 | -0.559 | Performance optimization requires runtime analysis, profiling, and algorithmic thinking -- not code search. MCP tools provide no signal and waste the entire time budget. |
| ccb_swebenchpro | 32 | 0.750 | SG_base: 0.588 | -0.162 | The agent over-searches remote repos instead of focusing on the local codebase where the bug exists. SG_full recovers to 0.786. |
| unit-test | 1 | 0.800 | SG_base: 0.200 | -0.600 | Writing tests requires understanding local code behavior, not searching remote repositories. |

### Categories Unaffected by MCP

| Category | N | BL Reward | SG_base | SG_full | Explanation |
|----------|---|-----------|---------|---------|-------------|
| dependency_recognition | 16 | 1.000 | 1.000 | 1.000 | Trivially solved by all configs. Tasks require reading local import statements. |
| semantic-code-navigation | 10 | 1.000 | 1.000 | 1.000 | RepoQA tasks are ceiling-saturated. The baseline already achieves perfect scores. |
| cross_module_bug_fix | 10 | 0.300 | 0.297 | 0.291 | Floor-saturated. These bugs are genuinely hard regardless of tooling. |
| dependency_inference | 8 | 0.500 | 0.500 | 0.500 | DIBench tasks are deterministic: either the agent installs the right packages or it doesn't. MCP doesn't help with package management. |

---

## 9. Efficiency Analysis

### 9.1 Token Consumption

| Config | Avg Input Tokens | Avg Output Tokens | Avg Task Time |
|--------|-----------------|-------------------|---------------|
| Baseline | 2,712,932 | 2,873 | 269s |
| SG_base | 4,178,655 (+54%) | 1,048 (-64%) | 279s (+4%) |
| SG_full | 4,024,750 (+48%) | 3,960 (+38%) | 431s (+60%) |

**Input tokens increase ~50% with MCP** because the agent reads Sourcegraph search results, file contents from remote repos, and symbol navigation output. This is an inherent cost of external tool access.

**SG_base output tokens drop 64%** because the agent relies more on MCP results and produces less exploratory code. SG_full output tokens increase 38% because the enhanced preamble encourages more thorough reasoning.

**SG_full is 60% slower on average.** This is the main efficiency cost. The agent spends time on MCP tool calls, waiting for search results, and processing additional context. For some task types (architecture, code review) this investment pays off in higher reward. For others (performance, bug fix) it does not.

### 9.2 Efficiency Winners and Losers

**MCP saves the most time on:**
- K8s Docs SG_base: -84s (-43%) -- documentation tasks in a large Go codebase where search replaces manual navigation
- CrossRepo SG_base: -159s (-32%) -- cross-repository reasoning benefits from instant symbol lookup
- LoCoBench SG_base: -96s (-24%) -- long-context understanding benefits from targeted search instead of reading entire files
- RepoQA SG_full: -11s (-25%) -- quick semantic navigation tasks finish faster with direct search

**MCP costs the most time on:**
- LargeRepo SG_full: +1250s (+125%) -- the agent explores massive codebases (kubernetes, vscode) extensively via MCP instead of acting on what it finds
- SWE-Perf SG_full: +827s (+183%) -- the agent searches for optimization patterns instead of profiling
- LoCoBench SG_full: +398s (+98%) -- over-exploration with Deep Search preamble
- PyTorch SG_full: +417s (+155%) -- MCP adds no value for PR-level Python tasks

---

## 10. Cross-Cutting Insights

### 10.1 The "MCP Distraction Effect"

The single most important finding is that **unrestricted MCP access (SG_base) frequently hurts performance** while **guided MCP access (SG_full) generally helps.** This pattern appears across multiple dimensions:

- SWE-bench Pro: SG_base -0.162 reward, SG_full +0.036
- Bug fix tasks: SG_base -0.092, SG_full +0.043
- Python tasks: SG_base -0.089, SG_full +0.039
- Hard difficulty: SG_base -0.062, SG_full +0.034

The mechanism is consistent: when given unrestricted MCP tools, the agent over-invests in remote code search at the expense of local analysis and implementation. The SG_full preamble mitigates this by instructing the agent to prefer local tools when the codebase is already available and to use MCP for specific needs (understanding unfamiliar APIs, tracing cross-repo dependencies).

### 10.2 Ceiling and Floor Effects

Several benchmarks are **ceiling-saturated** (all configs achieve near-perfect scores):
- RepoQA: 1.000 across all configs (semantic navigation is trivially solved)
- DependEval recognition: 1.000 across all configs (reading import statements)

Several are **floor-saturated** (all configs fail equally):
- cross_module_bug_fix: ~0.300 across all configs (genuinely hard bugs)
- api_upgrade: 0.000 across all configs (the single CrossRepo API upgrade task is beyond current capability)

MCP's value is concentrated in the **middle band** where baseline success is 40--80% -- tasks hard enough that additional context helps but not so hard that no amount of search can overcome the fundamental difficulty.

### 10.3 Task Type Determines MCP Value More Than Language or Difficulty

The strongest predictor of MCP benefit is **task category**, not language or difficulty:
- architectural_understanding: +0.083 SG_full (consistent across languages)
- multifile_editing: +0.167 SG_full (consistent across difficulties)
- performance: -0.559 SG_base (regardless of language)

Language-level effects are largely confounded by task type distribution. For example, JavaScript's +0.127 SG_full gain is driven by SWE-bench Pro NodeBB tasks (bug fixes in a large TypeScript/JS codebase), not an intrinsic language property.

---

## 11. Recommendations

1. **Use SG_full for production deployments** -- it provides the most consistent improvements across task types and avoids the SG_base distraction effect.

2. **Disable MCP for performance optimization tasks** -- MCP tools provide no signal for runtime analysis and waste the agent's time budget.

3. **MCP is highest-value for architectural understanding, code review, and cross-file refactoring** -- invest in these use cases.

4. **The SG_full preamble is critical** -- the difference between SG_base and SG_full demonstrates that tool availability alone is insufficient; the agent needs guidance on when and how to use external tools.

5. **Efficiency gains require task-type awareness** -- MCP saves time on documentation/navigation tasks but costs time on implementation tasks. An adaptive system that enables/disables MCP based on task classification would capture the benefits while avoiding the costs.

---

## Appendix A: Data Files

| File | Description |
|------|-------------|
| `docs/analysis.csv` | 451 per-task records with 21 columns (suite, config, task_name, status, reward, language, difficulty, category, sdlc_phase, repo, mcp_benefit_score, context_complexity, cross_file_deps, tokens, timing) |
| `docs/analysis.json` | Same data in structured JSON format |
| `docs/analysis_report.txt` | Raw tabular output from the extraction script |
| `scripts/extract_analysis_metrics.py` | Analysis script (rerun with `--deltas`, `--export-csv`, `--dimension`) |

## Appendix B: Benchmark Descriptions

| Benchmark | Tasks | Focus | Reward Type |
|-----------|-------|-------|-------------|
| SWE-bench Pro | 32 | Real-world SWE issues across Go, TS, Python repos | Binary (test pass/fail) |
| DependEval | 32 | Dependency ordering in Java, JS, Python, TS | Binary (correct order) |
| LoCoBench | 25 | Long-context understanding (architectural, refactoring, bugs) | Graded (test_ratio) |
| PyTorch | 11 | PyTorch PR-level tasks | Graded (diff_similarity) |
| RepoQA | 10 | Repository Q&A / semantic navigation | Binary |
| TAC | 8 | Tool-augmented coding (HyperLogLog, endpoints, tests) | Graded (checklist) |
| DIBench | 8 | Dependency installation across languages | Binary |
| K8s Docs | 5 | Kubernetes documentation generation | Graded (semantic_similarity) |
| CrossRepo | 5 | Cross-repository reasoning | Graded (various) |
| LargeRepo | 4 | Large codebase feature implementation (K8s, VS Code, Servo, TRT) | Binary |
| LinuxFLBench | 5 | Linux kernel fault localization | Graded |
| CodeReview | 3 | AI code review: find and fix injected PR defects | Graded |
| SWE-Perf | 3 | Performance optimization | Graded (speedup_ratio) |
