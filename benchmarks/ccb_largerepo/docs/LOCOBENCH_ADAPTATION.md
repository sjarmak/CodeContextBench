# LoCoBench Adaptation for Large-Repository Tasks

## Overview

The `ccb_largerepo` benchmark adapts design principles from **LoCoBench** (arXiv:2509.09614) — a benchmark for evaluating long-context code understanding — to real-world, production-scale repositories. Where LoCoBench uses synthetic code generation to create controlled test environments at 5.8K–700K+ token contexts, our adaptation operates on unmodified open-source repositories ranging from 350K to 30M+ lines of code.

This document explains what was adopted, what was adapted, and what was excluded.

## Design Principles Adopted

### 1. Task Categories

LoCoBench organizes tasks into categories that test distinct software engineering competencies. We adopted five of its eight categories:

| LoCoBench Category | Our Category | Rationale |
|---|---|---|
| `architectural_understanding` | `architectural_understanding` | Core strength — traces system-level design across modules |
| `cross_file_refactoring` | `cross_file_refactoring` | Tests multi-file reasoning and dependency awareness |
| `bug_investigation` | `bug_investigation` | Exercises call-chain tracing from symptom to root cause |
| `security_analysis` | `security_analysis` | Tests data-flow tracing across trust boundaries |
| `feature_implementation` | `feature_implementation` | Retained from original ccb_largerepo (predates LoCoBench integration) |

### 2. SE Metrics Framework (LCBS Dimensions)

LoCoBench defines four evaluation dimensions. We map each to our implementation:

| LCBS Dimension | Our Implementation | How It's Measured |
|---|---|---|
| **Software Engineering (SE)** | ACS, DTA, CFRD rubrics | LLM-as-judge scores on 1–5 scale via `judge_context.py` |
| **Functional Correctness (FC)** | Compilation + test verifiers | `test.sh` checks compilation (`go build`, `mvn`, `make`) + keyword detection |
| **Code Quality (CQ)** | Static analysis (future) | Planned but not yet implemented; LoCoBench uses linting metrics |
| **Long-Context Understanding (LCU)** | IR metrics (precision/recall/F1) | `verifier_lib.sh` computes against `ground_truth.json` |

The three SE sub-dimensions in our judge context:

- **ACS (Architectural Coherence Score)**: Does the agent understand the system's modular boundaries and component relationships?
- **DTA (Dependency Traversal Accuracy)**: Can the agent follow dependency chains across files and modules?
- **CFRD (Cross-File Reasoning Depth)**: Does the agent synthesize information from multiple files to reach a conclusion?

### 3. Structured Output Format

LoCoBench requires agents to produce structured output (identified files, dependency chains). We adopt this via `solution.md` parsing in `verifier_lib.sh`, which extracts:

- `## Files Examined` section for IR metrics computation
- `## Dependency Chain` section for dependency traversal accuracy

## Design Principles Adapted

### 1. Codebase Scale (5.8K tokens → 1M+ LOC)

LoCoBench generates synthetic codebases at controlled sizes (5.8K to 700K+ tokens). Our adaptation uses real repositories:

| Aspect | LoCoBench Original | Our Adaptation |
|---|---|---|
| Codebase size | 5.8K–700K+ tokens | 350K–30M lines of code |
| Code origin | Synthetically generated | Real open-source repositories |
| Pinning | Generated at test time | Git tags/commits pinned in `sg_indexing_list.json` |
| Language count | 13 | 7 (Go, Java, Python, C, C++, Rust, TypeScript) |

This shift from synthetic to real code means:

- **Richer context**: Real codebases have documentation, build configs, tests, and historical conventions that synthetic code lacks.
- **Noisier signal**: Real code has dead code, deprecated APIs, and inconsistent patterns that add realistic difficulty.
- **Higher stakes**: Tasks require understanding actual architectural decisions, not synthetic patterns.

### 2. Verifier Approach (Keyword Overlap → IR Metrics)

LoCoBench uses keyword overlap and exact-match scoring for its `verify.py` scripts. Our adaptation uses a composite scoring formula with information retrieval metrics:

```
score = 0.4 * task_quality + 0.3 * file_recall + 0.2 * file_precision + 0.1 * dep_accuracy
```

Where:
- **task_quality**: Binary compilation check + keyword detection (similar to LoCoBench FC)
- **file_recall**: Fraction of ground-truth files the agent identified
- **file_precision**: Fraction of agent-identified files that are in ground truth
- **dep_accuracy**: Order-aware matching of dependency chain traversal

This is more nuanced than LoCoBench's boolean pass/fail because partial credit matters when ground truth has 10–25 files.

### 3. Ground Truth Sourcing (Synthetic → Research-Derived)

LoCoBench generates ground truth programmatically (it knows the answer because it generated the code). We derive ground truth through:

- **Sourcegraph code search** for architectural and security tasks (keyword_search, find_references, list_files)
- **GitHub PR/issue analysis** for bug investigation tasks (real closed bugs with merged fixes)
- **Manual validation** for cross-repo dependency chains

All LLM-generated ground truth carries `confidence: "medium"` and a methodology note requiring manual validation.

### 4. Repository Diversity (Single-Project → Multi-Project)

LoCoBench generates one codebase per task. Our adaptation spans 15+ repositories across two tiers:

- **Tier A (Systems Infrastructure)**: Kubernetes, Django, PostgreSQL, Linux, Rust compiler
- **Tier B (Capital Markets)**: Apache Camel, Flink, Kafka, QuantLib, Strata, Hazelcast, Legend Engine

This tests whether agents generalize across architectural styles (microservices vs monolith), language ecosystems, and domain conventions.

## Design Principles Excluded

### 1. Synthetic Code Generation

LoCoBench's core innovation is generating controlled codebases where the ground truth is known by construction. We excluded this because:

- Our research question is about MCP tool value on **real** codebases, not synthetic ones.
- Synthetic code cannot reproduce the messy reality of 25-year-old C codebases (PostgreSQL, QuantLib) or build-system complexity (Bazel for K8s, Maven multi-module for Strata).
- The agent must handle real git history, real CI configs, and real test suites.

### 2. Context Window Stress Testing

LoCoBench systematically varies context length (5.8K to 700K+ tokens) to find where models degrade. We excluded this because:

- All our repositories already exceed typical context windows (the smallest, QuantLib, is 437K LOC).
- The MCP tools are specifically designed to avoid loading the full context — the interesting question is whether they can find the right subset.

### 3. Three Excluded Categories

We excluded three LoCoBench categories:

| Excluded Category | Reason |
|---|---|
| `code_comprehension` | Overlaps with `architectural_understanding` at production scale; the distinction (reading vs understanding) is less meaningful in million-LOC repos |
| `integration_testing` | Requires running the project's test suite inside Docker, which is infeasible for most of our repos (K8s tests take hours, PostgreSQL requires `initdb`) |
| `multi_session` | Our benchmark framework (Harbor) runs single-session trials; multi-session evaluation would require framework changes |

## Comparison Table

| Dimension | LoCoBench (Original) | ccb_largerepo (Our Adaptation) |
|---|---|---|
| **Codebase origin** | Synthetically generated | Real open-source repositories |
| **Codebase size** | 5.8K–700K+ tokens | 350K–30M LOC |
| **Task count** | 50 per category | 30+ total across 5 categories |
| **Task categories** | 8 | 5 (excluded 3) |
| **Languages** | 13 | 7 |
| **Evaluation** | Keyword overlap + linting | IR metrics + compilation + LLM-as-judge |
| **Ground truth** | Generated (high confidence) | Research-derived (medium confidence) |
| **Verifier** | `verify.py` (exact match) | `verifier_lib.sh` (composite IR score) |
| **Agent output** | Code changes | `solution.md` structured analysis |
| **MCP integration** | Not applicable | Core research variable (baseline vs SG_full) |
| **Reproducibility** | Deterministic (generated code) | Pinned commits (real code, fixed state) |

## References

- Liang, T., et al. (2025). "LoCoBench: A Comprehensive Benchmark for Long Context Code Understanding." *arXiv:2509.09614*.
- CodeContextBench project: `benchmarks/ccb_largerepo/` for task definitions, `scripts/ccb_metrics/judge_context.py` for SE dimension rubrics.
