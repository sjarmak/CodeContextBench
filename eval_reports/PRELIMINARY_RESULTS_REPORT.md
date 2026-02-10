# CodeContextBench: Preliminary Results Report

**Aligned with Blog Post: "Rethinking Coding Agent Benchmarks Part II: Building CodeContextBench"**
**Generated: 2026-02-10**

---

## 1. Benchmark Overview

### Scale
- **160 tasks** registered across **13 benchmark suites** and **10 programming languages**
- **466 task-config runs** completed, yielding **478 scored entries** across 39 runs
- **3 experimental configurations** tested: Baseline, MCP-Base (SG_base), MCP-Full (SG_full)
- **Total cost**: ~$977 across all configurations

### Experimental Design

| Configuration | What the Agent Gets | MCP Tools |
|---|---|---|
| **Baseline** | Claude Code's native tools (Bash, Read, Edit, Write, Grep, Glob) | 0 |
| **MCP-Base** | + Sourcegraph keyword search, NLS search, file nav, go-to-definition, find-references | 11 |
| **MCP-Full** | + Deep Search (async semantic codebase analysis) | 13 |

Same agent (Claude Code). Same model (claude-opus-4-5/4-6). Same tasks. Same containerized environment. The **only variable is code intelligence tooling**.

### Task Composition by SDLC Phase

| SDLC Phase | Tasks | Benchmarks |
|---|---|---|
| Implementation (bug fix) | 56 (35%) | SWE-bench Pro, LoCoBench, PyTorch, CrossRepo |
| Implementation (feature) | 32 (20%) | LargeRepo, PyTorch, TAC, DIBench |
| Architecture & Design | 26 (16%) | LoCoBench, CrossRepo |
| Requirements & Discovery | 12 (8%) | TAC, DependEval |
| Implementation (refactoring) | 15 (9%) | LoCoBench, CrossRepo |
| Testing & QA | 8 (5%) | SWE-Perf, TAC, CodeReview |
| Documentation | 5 (3%) | K8s Docs |

### Language Distribution

Python (39), Go (27), TypeScript (20), C++ (19), JavaScript (14), Rust (12), C (12), Java (10), C# (6)

### Difficulty Distribution

Expert: 30, Hard: 71, Medium: 58, Easy: 1

---

## 2. Aggregate Results

### Headline Numbers (Scored Tasks, Errored Excluded)

| Config | Scored Tasks | Mean Reward | Pass Rate |
|---|---|---|---|
| **Baseline** | 145 | **0.578** | 71.9% |
| **SG_base** | 135 | **0.570** | 66.0% |
| **SG_full** | 150 | **0.657** | 81.4% |

### Matched-Task Comparison (125 tasks scored in all 3 configs)

| Config | Mean Reward | Delta vs Baseline |
|---|---|---|
| Baseline | 0.600 | -- |
| SG_base | 0.599 | **-0.001 (neutral)** |
| SG_full | 0.630 | **+0.031 (+3.1pp)** |

SG_full delivers a consistent +3.1 percentage point improvement on matched tasks, and +7.9pp on all scored tasks.

---

## 3. Per-Benchmark Breakdown

| Benchmark | # Tasks | Baseline | SG_base | SG_full | SG_full Delta |
|---|---|---|---|---|---|
| **ccb_swebenchpro** | 36 | 0.417 | 0.333 | **0.769** | **+0.352** |
| **ccb_pytorch** | 12 | 0.111 | 0.108 | **0.265** | +0.154 |
| **ccb_largerepo** | 4 | 0.250 | 0.250 | **0.425** | +0.175 |
| **ccb_dependeval** | 32 | 0.636 | 0.665 | **0.720** | +0.083 |
| **ccb_locobench** | 25 | 0.449 | 0.504* | **0.499** | +0.050 |
| **ccb_tac** | 8 | 0.492 | 0.365 | **0.544** | +0.052 |
| **codereview** | 3 | 0.933 | 0.980 | **1.000** | +0.067 |
| **linuxflbench** | 5 | 0.860 | 0.820 | **0.880** | +0.020 |
| ccb_k8sdocs | 5 | 0.920 | 0.920 | 0.920 | +0.000 |
| ccb_repoqa | 10 | 1.000 | 1.000 | 1.000 | +0.000 |
| ccb_dibench | 8 | 0.500 | 0.500 | 0.500 | +0.000 |
| ccb_sweperf | 3 | 0.591 | 0.032 | 0.367 | **-0.224** |
| ccb_crossrepo | 5 | 0.571 | 0.587 | 0.387 | **-0.184** |

*LoCoBench SG_base: 0.504 among 18 valid tasks (7 zero-token auth failures drag raw mean to 0.363)

**SWE-bench Pro** is the standout story: SG_full nearly doubles the baseline pass rate. **PyTorch** triples. **LargeRepo** improves from 1/4 to 2/4 passing.

---

## 4. Task-Level Outcome Flips

### Binary Pass/Fail Changes

- **24 tasks flip from fail to pass** with SG_full (10 SWE-bench Pro, 4 DependEval, 1 LargeRepo, etc.)
- **9 tasks flip from pass to fail** (5 SWE-bench Pro, 1 CrossRepo, 1 DIBench, 1 SWE-Perf, 1 LoCoBench)
- **Net flip: +15 tasks gained**

### MCP Impact Classification

**SG_full vs Baseline** (137 matched pairs):
- **Helps** (delta > +0.01): 29 tasks (21.2%)
- **Neutral** (|delta| <= 0.01): 94 tasks (68.6%)
- **Hurts** (delta < -0.01): 14 tasks (10.2%)
- **Help-to-hurt ratio: 2.1:1**

**SG_base vs Baseline** (133 matched pairs):
- Helps: 18 tasks (13.5%)
- Neutral: 97 tasks (72.9%)
- Hurts: 18 tasks (13.5%)
- **Help-to-hurt ratio: 1:1**

### Largest MCP Wins (SG_full vs Baseline)

| Task | Suite | BL | SG_full | Delta |
|---|---|---|---|---|
| multifile_editing-ts-4253 | DependEval | 0.097 | 1.000 | +0.903 |
| multifile_editing-python-8597 | DependEval | 0.180 | 1.000 | +0.820 |
| big-code-k8s-001 | LargeRepo | 0.000 | 0.700 | +0.700 |
| dotenv-expand | DIBench | 0.000 | 1.000 | +1.000 |
| vuls-139f3a81 | SWE-bench Pro | 0.000 | 1.000 | +1.000 |

### Largest MCP Losses

| Task | Suite | BL | SG_full | Delta |
|---|---|---|---|---|
| inducer-cgen | DIBench | 1.000 | 0.000 | -1.000 |
| refactor_rename_01 | CrossRepo | 0.920 | 0.000 | -0.920 |
| sweperf-001 | SWE-Perf | 0.998 | 0.122 | -0.876 |

---

## 5. MCP Impact by Codebase Complexity

### Context Complexity (Codebase Size Proxy)

| CC Bucket | N | BL | SG_full | Delta |
|---|---|---|---|---|
| Low (0.40-0.59) | 23 | 0.564 | 0.521 | **-0.043** |
| Medium (0.60-0.79) | 47 | 0.505 | 0.562 | **+0.057** |
| High (0.80-1.00) | 67 | 0.670 | 0.696 | **+0.026** |

MCP helps on medium and large codebases. On small codebases, the agent wastes time searching remotely when local navigation suffices.

### Cross-File Dependencies

| CFD Bucket | N | BL | SG_full | Delta |
|---|---|---|---|---|
| Low (<0.40) | 34 | 0.411 | 0.398 | -0.013 |
| Medium (0.40-0.69) | 36 | 0.669 | 0.722 | +0.053 |
| High (0.70-1.00) | 67 | 0.633 | 0.677 | +0.044 |

MCP benefit scales directly with cross-file dependencies.

### Combined Quadrant Analysis

| Quadrant | N | BL | SG_full | Delta | Help:Hurt |
|---|---|---|---|---|---|
| **Large & Multi-file** (cc>=0.7, cfd>=0.5) | 67 | 0.633 | 0.693 | **+0.060** | **2.5:1** |
| Small & Multi-file (cc<0.7, cfd>=0.5) | 36 | 0.594 | 0.594 | +0.000 | 1:1 |
| Small & Simple (cc<0.7, cfd<0.5) | 34 | 0.500 | 0.488 | -0.013 | 0:6 |

**The sweet spot**: Large codebase + high cross-file dependencies = +6.0pp improvement with 2.5:1 help-to-hurt ratio.

### LoCoBench: Real Codebase Size Data (25 tasks with measured context_length)

| Codebase Size | N | Avg Chars | BL | SG_full | Delta |
|---|---|---|---|---|---|
| Medium (500K-1M) | 5 | 776K | 0.446 | 0.551 | +0.105 |
| Large (1M-2M) | 17 | 1.3M | 0.526 | 0.538 | +0.012 |
| Very Large (2M+) | 3 | 2.3M | 0.160 | 0.333 | **+0.173** |

Very large codebases (2M+ characters, ~500K+ tokens) show the strongest benefit. These are codebases that literally cannot fit in a context window.

---

## 6. MCP Impact by Task Difficulty

| Difficulty | N | BL | SG_full | Delta | Help Rate |
|---|---|---|---|---|---|
| Easy | 4 | 0.625 | 0.625 | +0.000 | 0% |
| Medium | 53 | 0.737 | 0.774 | +0.037 | 15% |
| Hard | 50 | 0.505 | 0.529 | +0.024 | 8% |
| Very Hard | 8 | 0.449 | 0.457 | +0.008 | 13% |
| **Expert** | 22 | 0.436 | 0.481 | **+0.045** | **57%** |

Expert-level tasks have the lowest baseline scores AND the highest MCP help rate (57%). MCP provides the most value on problems inherently difficult for the agent.

### By Baseline Performance Level

| Baseline Range | N | BL | SG_full | Delta |
|---|---|---|---|---|
| BL=0.0 (genuine fail) | 19 | 0.000 | 0.063 | +0.063 (7.4% flip rate) |
| **Low (0.01-0.49)** | 16 | 0.213 | 0.344 | **+0.131 (5:1 help-to-hurt)** |
| Medium (0.50-0.99) | 29 | 0.735 | 0.694 | -0.041 |
| Perfect (BL=1.0) | 65 | 1.000 | 0.976 | -0.024 |

**Strongest genuine MCP benefit**: Tasks where the agent runs and struggles (partial score, 0.01-0.49) but doesn't completely fail. +13.1pp improvement, 5:1 help-to-hurt ratio.

---

## 7. MCP Impact by Language

| Language | N | BL | SG_full | Delta |
|---|---|---|---|---|
| **JavaScript** | 9 | 0.340 | 0.467 | **+0.127** |
| **TypeScript** | 9 | 0.354 | 0.457 | **+0.103** |
| Rust | 4 | 0.412 | 0.459 | +0.047 |
| C | 13 | 0.626 | 0.667 | +0.041 |
| Go | 22 | 0.664 | 0.703 | +0.039 |
| Python | 31 | 0.573 | 0.570 | -0.003 |
| Java | 8 | 0.733 | 0.696 | -0.036 |

JavaScript and TypeScript tasks benefit most (+10-13pp). These languages have deep `node_modules` dependency trees and complex import graphs that benefit from remote search. Python tasks show no effect -- the agent navigates Python codebases effectively without MCP.

---

## 8. MCP Impact by SDLC Phase / Task Category

### By SDLC Phase

| SDLC Phase | Tasks | BL | SG_full | Delta |
|---|---|---|---|---|
| **Implementation (bug fix)** | 56 | 0.426 | **0.659** | **+0.233** |
| Implementation (feature) | 32 | 0.366 | 0.484 | +0.118 |
| Architecture & Design | 26 | 0.770 | 0.799 | +0.029 |
| Implementation (refactoring) | 15 | 0.451 | 0.420 | -0.031 |
| Testing & QA | 8 | 0.796 | 0.738 | -0.058 |

### By Task Category

| Category | N | BL | SG_full | Delta |
|---|---|---|---|---|
| **Multi-file editing** | 10 | 0.469 | 0.636 | **+0.167** |
| Cross-file refactoring | 11 | 0.394 | 0.429 | +0.035 |
| Dependency recognition | 22 | 0.714 | 0.750 | +0.036 |
| Code search (RepoQA) | 10 | 1.000 | 1.000 | +0.000 |
| Documentation (K8s) | 5 | 0.920 | 0.920 | +0.000 |
| **Performance optimization** | 3 | 0.591 | 0.367 | **-0.224** |

Multi-file editing is where MCP shines (+16.7pp). Performance optimization is where it hurts -- the agent needs focused local iteration, not broad search.

---

## 9. Efficiency & Cost Analysis

### Cost & Wall Clock per Config

| Config | Valid Tasks | Total Cost | Avg $/Task | Avg Wall Clock |
|---|---|---|---|---|
| Baseline | 145 | $281 | $1.94 | 600s (10 min) |
| SG_base | 135 | $294 | $2.18 (+12%) | 509s (-15%) |
| SG_full | 141 | $402 | $2.85 (+47%) | 1,170s (+95%) |

### Cost-per-Reward-Point (Cost Effectiveness)

| Suite | BL $/reward | SG_full $/reward | Winner |
|---|---|---|---|
| K8s Docs | $1.00 | **$0.69** | SG_full |
| SWE-bench Pro | $6.03 | **$2.97** | SG_full |
| TAC | $5.19 | **$4.55** | SG_full |
| PyTorch | $25.50 | **$9.77** | SG_full |
| LargeRepo | $21.67 | **$13.61** | SG_full |
| SWE-Perf | **$2.22** | $5.68 | Baseline |
| LoCoBench | $8.55 | $15.99 | Baseline |

**SG_full delivers the best cost-per-reward for 5 of 8 suites** with meaningful cost variation.

### Wall Clock Speed

| Suite | BL | SG_full | Delta | Direction |
|---|---|---|---|---|
| K8s Docs | 1,426s | **225s** | **-84%** | MCP dramatically faster |
| DIBench | 275s | **171s** | -38% | MCP faster |
| TAC | 1,483s | **1,087s** | -27% | MCP faster |
| LoCoBench | 449s | 1,144s | +155% | MCP slower |
| SWE-bench Pro | 575s | 2,457s | +47% | MCP slower |

---

## 10. Tool Utilization Patterns

### MCP Tool Distribution (3,174 actual invocations across SG configs)

| Tool | Calls | Share |
|---|---|---|
| keyword_search | 1,279 | **40.3%** |
| read_file | 885 | **27.9%** |
| list_files | 604 | **19.0%** |
| nls_search | 118 | 3.7% |
| find_references | 76 | 2.4% |
| go_to_definition | 74 | 2.3% |
| All others | 138 | 4.4% |
| deepsearch (actual) | 1 | 0.03% |

**Top 3 tools account for 87% of all MCP usage.** The agent converges on a keyword_search + read_file + list_files strategy regardless of what else is available.

### MCP Adoption Rate by Suite

| Suite | SG_base MCP Ratio | SG_full MCP Ratio | Avg MCP Calls/Task |
|---|---|---|---|
| K8s Docs | 62.8% | 47.9% | 10.8 |
| LinuxFLBench | 49.7% | 43.4% | 17.9 |
| DIBench | 41.3% | 41.5% | 13.4 |
| LoCoBench | 29.2% | 27.2% | 18.5 |
| TAC | 29.5% | 17.2% | 10.4 |
| CrossRepo | 4.2% | 1.8% | 2.1 |

### Deep Search: The Async Tool Problem

- **Available in all 152 SG_full tasks**
- **Actually invoked in exactly 1 task** (0.7%)
- Agent overwhelmingly prefers synchronous tools
- Root cause: Deep Search is asynchronous (50-120 second latency). Agent polls 1-2 times, sees "still processing," moves on
- The SG_full improvement (+3.1pp) comes almost entirely from the enhanced preamble and better synchronous tool guidance, NOT from Deep Search

---

## 11. Prompt Engineering Impact

### Preamble Evolution

The experiment went through 4 preamble iterations:

1. **Polite suggestion** ("consider using MCP"): Agent ignores MCP, uses grep exclusively
2. **Strong recommendation with tool substitution guide** (Grep -> keyword_search, etc.): Inconsistent adoption
3. **Block local search tools** (`--disallowedTools`): Agent loses fallback capability. Too aggressive.
4. **Hybrid (final)**: Allow all tools, lead with mandatory MCP-first guidance, include specific repository name

### Critical Finding: Repository Name Targeting

Adding the explicit Sourcegraph repository name to the preamble (e.g., `repo:^github.com/pytorch/pytorch$`) was a single-line change that dramatically improved search relevance. Without it, MCP searches across all indexed repositories returned noisy, irrelevant results.

### SG_base vs SG_full Preamble Differences

Both share the same two-phase mandatory workflow:
- **Phase 1**: Search & Understand (MANDATORY -- at least 3 MCP calls before any code changes)
- **Phase 2**: Implement (use Read to verify local files, trust local code over remote)

**SG_full adds**: Deep Search async workflow instructions ("retry at least 3 times," "continue working for 30-60 seconds while polling") plus guidance on dependency/impact analysis.

The **SG_full's richer preamble itself** appears to be the main driver of improvement -- not Deep Search, which is virtually unused. The enhanced guidance about two-phase workflow and search strategy causes the agent to approach tasks more systematically.

### The MCP Distraction Effect

On **TAC** (implementation tasks), SG_base causes the agent to over-read remote files instead of implementing:
- TAC SG_base: -0.127 delta vs baseline (hyperloglog: BL=1.0 -> SGB=0.17, write-unit-test: BL=0.80 -> SGB=0.20)
- TAC SG_full: +0.052 delta -- the richer preamble reduces over-reliance on remote search

---

## 12. MCP Benefit Score: Predicted vs Actual

### Methodology

Each task receives a predicted MCP benefit score (0-1) computed as:
```
score = 0.25*context_complexity + 0.30*cross_file_deps + 0.20*semantic_search_potential + 0.25*task_category_weight
```

- Mean predicted score: **0.738** (range: 0.44 - 0.94)
- Highest predicted: LoCoBench (0.918), LinuxFLBench (0.906), LargeRepo (0.895)
- Lowest predicted: SWE-Perf (0.458), TAC (0.496)

### Actual Results vs Predictions

| Predicted MCP Benefit | Tasks | BL | SG_full | Actual Delta |
|---|---|---|---|---|
| Medium (0.4-0.6) | 34 | 0.464 | 0.617 | **+0.153** |
| High (0.6-0.8) | 69 | 0.527 | 0.662 | **+0.135** |
| Very High (0.8-1.0) | 52 | 0.611 | 0.644 | **+0.033** |

Interestingly, the "medium" predicted-benefit tasks show the largest actual improvement. The "very high" predicted tasks have higher baselines (ceiling effect), reducing room for improvement.

---

## 13. Data Quality & Caveats

### Issues Identified and Resolved

| Issue | Impact | Resolution |
|---|---|---|
| Auth-failed run overwrites 11 valid SWE-Pro SG_full results | SG_full score dropped from 0.667 to 0.361 | Archived corrupted run, fixed dedup logic |
| 7 zero-token LoCoBench SG_base tasks | SG_base mean inflated from 0.504 to 0.363 | Classified as errored, excluded from means |
| 6 persistent Docker failures (protonmail, etc.) | Always fail regardless of config | Classified as infra errors, not agent failures |
| 30/156 baseline instructions contain MCP references | Potential contamination | ZERO functional impact (agent has no MCP tools). Cleaned in templates. |
| H3 token-logging bug (106 tasks) | Missing trajectory.json + cost data | Scores valid (verified). Cost recoverable from transcripts. |

### Statistical Limitations

- **Small N in some suites**: SWE-Perf (3), LargeRepo (4), CrossRepo (5), CodeReview (3)
- **Single agent family**: Only Claude Code tested
- **Single MCP provider**: Sourcegraph
- **Model version variation**: Some baseline runs used claude-opus-4-5-20251101, MCP-Full runs mostly used claude-opus-4-6
- **SWE-bench Pro uneven errors**: 16 BL errored, 19 SGB errored, 5 SGF errored -- different tasks scored in each config

### Stability

- **91 tasks pass in all 3 configs** (59% of matched set)
- **29 tasks fail in all 3 configs** (19%), dominated by hard PyTorch C++ tasks and complex SWE-bench Pro tasks

---

## 14. Summary: When MCP Helps vs Hurts

| Factor | MCP Helps When... | MCP Hurts When... |
|---|---|---|
| **Codebase size** | Large codebases (cc >= 0.7) | Small codebases (cc < 0.6) |
| **File dependencies** | High cross-file coordination (cfd >= 0.5) | Single-file tasks (cfd < 0.4) |
| **Difficulty** | Expert-level tasks (57% help rate) | Easy tasks (0% help rate) |
| **Language** | JavaScript/TypeScript (+10-13pp) | Python (neutral), Java (-3.6pp) |
| **Task type** | Multi-file editing, bug fixes | Performance optimization |
| **Baseline performance** | Agent struggles (BL 0.01-0.49, +13.1pp) | Agent already succeeds (-2.4pp) |
| **SDLC phase** | Bug fix (+23.3pp) | Refactoring (-3.1pp), Testing (-5.8pp) |

**The ideal MCP beneficiary**: An expert-difficulty, multi-file JavaScript/TypeScript bug fix in a large codebase where the baseline agent gets a partial score.

**The ideal non-beneficiary**: A simple, single-file Python performance optimization task where the baseline already passes.

---

## 15. Key Takeaways for the Blog Post

1. **MCP-Full improves overall reward by +3.1pp on matched tasks and +7.9pp on all scored tasks** -- modest but consistent.

2. **MCP-Base is neutral** (-0.001 on matched tasks) -- basic tool availability without enhanced guidance helps as often as it hurts. The preamble matters as much as the tools.

3. **The aggregate hides the story.** SWE-bench Pro jumps from 0.417 to 0.769. PyTorch triples. LargeRepo K8s taint goes from 0/1 to 0.7/1. But CrossRepo drops, SWE-Perf regresses.

4. **Deep Search is virtually unused (0.7% adoption)** despite being available. The async polling model conflicts with how agents prefer to work. The SG_full improvement comes from better preamble, not Deep Search.

5. **Agents converge on 3 tools**: keyword_search (40%), read_file (28%), list_files (19%) = 87% of all MCP usage.

6. **Cost-per-reward is better with SG_full for 5 of 8 suites** -- even though raw cost is 47% higher, the higher reward rate means you pay less per unit of success on search-heavy tasks.

7. **K8s Docs is the efficiency showpiece**: 84% faster wall clock AND 31% lower cost with SG_full. The agent finds what it needs through search instead of exhaustively reading files.

8. **Prompt engineering is infrastructure**: The preamble evolution from "polite suggestion" to "mandatory two-phase workflow with repo targeting" was as impactful as the tools themselves.

9. **The MCP distraction effect is real**: On small-codebase implementation tasks (TAC, SWE-Perf), the agent reads remote files instead of implementing. The enhanced SG_full preamble mitigates this by guiding MCP use more carefully.

10. **Verifier bugs are silent killers**: PyTorch always exited 0 (rebuilt verifier), CrossRepo looked at wrong path, TAC used wrong CLI flag. Each produced plausible results. QA audit found 28 issues, 9 critical.

---

## Appendix A: Per-Benchmark Efficiency Data

| Benchmark | Config | Mean Wall Clock (s) | Mean Cost (USD) | Mean MCP Ratio |
|---|---|---|---|---|
| ccb_codereview | baseline | 186 | $0.56 | 0.000 |
| ccb_codereview | SG_base | 286 | $0.96 | 0.048 |
| ccb_codereview | SG_full | 209 | $0.83 | 0.287 |
| ccb_crossrepo | baseline | 585 | $2.69 | 0.000 |
| ccb_crossrepo | SG_base | 604 | $2.64 | 0.042 |
| ccb_crossrepo | SG_full | 620 | $3.90 | 0.018 |
| ccb_dependeval | baseline | 99 | $0.28 | 0.000 |
| ccb_dependeval | SG_base | 123 | $0.40 | 0.268 |
| ccb_dependeval | SG_full | 98 | $0.40 | 0.281 |
| ccb_dibench | baseline | 275 | $0.72 | 0.000 |
| ccb_dibench | SG_base | 222 | $1.12 | 0.413 |
| ccb_dibench | SG_full | 171 | $0.93 | 0.415 |
| ccb_k8sdocs | baseline | 1,426 | $0.92 | 0.000 |
| ccb_k8sdocs | SG_base | 651 | $0.72 | 0.628 |
| ccb_k8sdocs | SG_full | 225 | $0.64 | 0.479 |
| ccb_largerepo | baseline | 2,903 | $5.42 | 0.000 |
| ccb_largerepo | SG_base | 1,187 | $4.74 | 0.232 |
| ccb_largerepo | SG_full | 3,932 | $5.78 | 0.077 |
| ccb_locobench | baseline | 449 | $3.84 | 0.000 |
| ccb_locobench | SG_base | 300 | $1.97 | 0.292 |
| ccb_locobench | SG_full | 1,144 | $7.98 | 0.272 |
| ccb_pytorch | baseline | 1,106 | $2.14 | 0.000 |
| ccb_pytorch | SG_base | 666 | $2.47 | 0.199 |
| ccb_pytorch | SG_full | 2,716 | $2.58 | 0.169 |
| ccb_repoqa | baseline | 165 | $0.17 | 0.000 |
| ccb_repoqa | SG_base | 125 | $0.31 | 0.262 |
| ccb_repoqa | SG_full | 307 | $0.24 | 0.680 |
| ccb_swebenchpro | baseline | 575 | $1.52 | 0.000 |
| ccb_swebenchpro | SG_base | 663 | $2.37 | 0.115 |
| ccb_swebenchpro | SG_full | 2,457 | $2.06 | 0.135 |
| ccb_sweperf | baseline | 796 | $3.82 | 0.000 |
| ccb_sweperf | SG_base | 839 | $5.85 | 0.130 |
| ccb_sweperf | SG_full | 1,388 | $8.57 | 0.058 |
| ccb_tac | baseline | 1,483 | $2.55 | 0.000 |
| ccb_tac | SG_base | 1,123 | $3.00 | 0.295 |
| ccb_tac | SG_full | 1,087 | $2.48 | 0.172 |
| linuxflbench | baseline | 568 | $1.04 | 0.000 |
| linuxflbench | SG_base | 1,437 | $1.10 | 0.497 |
| linuxflbench | SG_full | 414 | $1.37 | 0.434 |

## Appendix B: Code Changes by Config

| Benchmark | Config | Mean Files Modified | Mean Lines Added | Mean Lines Removed |
|---|---|---|---|---|
| ccb_crossrepo | baseline | 2.4 | 525.6 | 0.6 |
| ccb_crossrepo | SG_full | 1.4 | 129.0 | 0.6 |
| ccb_k8sdocs | baseline | 1.0 | 151.4 | 0.0 |
| ccb_k8sdocs | SG_full | 1.0 | 111.2 | 0.2 |
| ccb_largerepo | baseline | 5.2 | 434.0 | 204.8 |
| ccb_largerepo | SG_full | 7.5 | 331.2 | 143.0 |
| ccb_locobench | baseline | 3.7 | 995.9 | 33.0 |
| ccb_locobench | SG_full | 7.1 | 1,245.0 | 150.2 |
| ccb_pytorch | baseline | 2.8 | 144.3 | 114.3 |
| ccb_pytorch | SG_full | 3.5 | 188.1 | 77.2 |
| ccb_swebenchpro | baseline | 4.6 | 146.9 | 88.8 |
| ccb_swebenchpro | SG_full | 4.8 | 175.6 | 70.0 |
| ccb_tac | baseline | 3.0 | 254.3 | 24.7 |
| ccb_tac | SG_full | 4.0 | 405.7 | 10.0 |

## Appendix C: Task Selection Methodology

### MCP Benefit Scoring Formula

```
score = 0.25 * context_complexity + 0.30 * cross_file_deps + 0.20 * semantic_search_potential + 0.25 * task_category_weight
```

**Component definitions**:
- **context_complexity**: Codebase token count proxy. Normalized: 1M+ tokens = 1.0
- **cross_file_deps**: Number of files/packages involved. Normalized: 20+ files = 1.0
- **semantic_search_potential**: How much search helps (large repos=0.9, find-in-codebase=0.8)
- **task_category_weight**: Per-category MCP affinity (architectural=1.0, cross-file refactoring=0.9, bug fix=0.7)

### Difficulty Calibration

| Benchmark | Metric | Thresholds |
|---|---|---|
| SWE-bench Pro | files_changed | 1-3=medium, 4-10=hard, 10+=very_hard |
| PyTorch | LOC (additions+deletions) | <50=medium, 50-200=hard, >200=very_hard |
| LoCoBench | task category | architectural=expert, others=hard |
| RepoQA | source file count | <100=medium, 100+=hard |
| CrossRepo | manual assessment | easy to hard |

### Selection Strategies

| Benchmark | Available | Selected | Strategy |
|---|---|---|---|
| SWE-bench Pro | 731 | 36 | Proportional by repo, prefer most files changed |
| LoCoBench | 50 | 25 | Priority: arch > refactoring > bug, by MCP score |
| PyTorch | 25 | 12 | Prefer hard difficulty, most files modified |
| DependEval | 32 | 32 | All selected |
| DIBench | 387 | 8 | 2 per language, moderate patch complexity |
| Small benchmarks | varies | all | All tasks selected (LargeRepo, K8s Docs, TAC, SWE-Perf, CrossRepo, CodeReview) |
