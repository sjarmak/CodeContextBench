# Task Selection Methodology

## Overview

Selected **93 tasks** from 826 available across 7 benchmarks, stratified by SDLC phase with MCP benefit scoring.

## SDLC Phase Coverage

| SDLC Phase | Tasks | Benchmarks |
|------------|-------|------------|
| Requirements & Discovery | 2 | ccb_tac |
| Architecture & Design | 9 | ccb_locobench |
| Implementation (feature) | 9 | ccb_largerepo, ccb_pytorch, ccb_tac |
| Implementation (bug fix) | 49 | ccb_locobench, ccb_pytorch, ccb_swebenchpro |
| Implementation (refactoring) | 13 | ccb_locobench |
| Testing & QA | 4 | ccb_sweperf, ccb_tac |
| Documentation | 5 | ccb_k8sdocs |
| Maintenance | 2 | ccb_tac |

## Benchmark Coverage

| Benchmark | Available | Selected | Strategy |
|-----------|-----------|----------|----------|
| ccb_k8sdocs | 5 | 5 | All selected (small benchmark) |
| ccb_largerepo | 4 | 4 | All selected (small benchmark) |
| ccb_locobench | 50 | 25 | Priority: arch > refactoring > bug, by MCP score |
| ccb_pytorch | 25 | 12 | Prefer hard difficulty, then most files modified |
| ccb_swebenchpro | 731 | 36 | Proportional by repo, prefer most files changed |
| ccb_sweperf | 3 | 3 | All selected (small benchmark) |
| ccb_tac | 8 | 8 | All selected (small benchmark) |

## Language Distribution

| Language | Tasks |
|----------|-------|
| python | 26 |
| go | 19 |
| cpp | 17 |
| typescript | 9 |
| rust | 8 |
| c | 7 |
| csharp | 3 |
| javascript | 3 |
| python,cpp | 1 |

## MCP Benefit Scoring

Each task receives an MCP benefit score in [0.0, 1.0] computed as:

```
score = 0.25 * context_complexity
      + 0.30 * cross_file_deps
      + 0.20 * semantic_search_potential
      + 0.25 * task_category_weight
```

**Average MCP benefit score:** 0.7015

### Component Definitions

- **context_complexity**: Per-task where possible. LoCoBench uses `context_length` (1M+ tokens = 1.0). SWE-bench Pro uses `solution_loc_changed` (500+ LOC = 1.0). PyTorch blends base codebase size (0.6) with patch LOC (range 0.6–1.0). K8s Docs uses package source file count (450+ files = 1.0).
- **cross_file_deps**: Per-task from `files_count`, `solution_files_changed`, or parsed metadata. SWE-bench Pro/PyTorch normalize at 20+ files. K8s Docs normalizes at 450 files (package scope). LoCoBench uses task metadata.
- **semantic_search_potential**: Per-task where possible. SWE-bench Pro scales by `solution_files_changed` (30+ files = 1.0). PyTorch blends base (0.5) with files touched. K8s Docs scales by package file count. Large repos fixed at 0.9.
- **task_category_weight**: Per-category MCP affinity (architectural_understanding=1.0, cross_file_refactoring=0.9, etc.)

## Per-Benchmark Selection Strategies

### SWE-Bench Pro (~35 tasks)
Proportional allocation by repository, ensuring at least 1 task per repo. Within each repo, tasks with the most files changed in their solution patch are preferred. Language corrections applied (e.g., NodeBB -> javascript, navidrome -> go). Diversity check ensures >=3 tasks each for Go, TypeScript, and JavaScript language families.

### LoCoBench Agent (~25 tasks)
All bug_investigation tasks (3) selected first, then all cross_file_refactoring (13), then top architectural_understanding tasks by MCP score to fill remaining budget. All tasks have >700K token context and 70+ files.

### GitHub Mined (~12 tasks)
All PyTorch cross-module tasks. Selection prioritizes hard difficulty, then tasks with the most files modified in the ground truth PR.

### Small Benchmarks (all selected)
ccb_largerepo (4), ccb_k8sdocs (5), ccb_tac (8), ccb_sweperf (3) — all tasks selected due to small size.

