# CodeContextBench Benchmarks

This directory contains all benchmark task definitions for evaluating coding agents with and without Sourcegraph MCP. The canonical task selection is defined in [`selected_benchmark_tasks.json`](../selected_benchmark_tasks.json) (102 tasks across 8 benchmarks).

See [`docs/TASK_SELECTION.md`](../docs/TASK_SELECTION.md) for the selection methodology.

---

## Active Benchmarks

### 1. [swebench_pro/](swebench_pro/) - Multi-Language Bug Fixing
**Task Count**: 731 available, 36 selected
**Languages**: Go, TypeScript, Python
**SDLC Phase**: Implementation (bug fix)
**Focus**: Long-horizon software engineering on production codebases
**Repositories**: flipt-io/flipt, tutao/tutanota, internetarchive/openlibrary, ansible/ansible, and more
**Task Format**: Harbor (via adapter, pre-generated)

---

### 2. [locobench_agent/](locobench_agent/) - Long-Context Agent Tasks
**Task Count**: 50 available, 25 selected
**Languages**: Rust, C#, C, C++, Python, Java, JavaScript, TypeScript, Go
**SDLC Phases**: Architecture & Design, Implementation (refactoring), Implementation (bug fix)
**Focus**: Architectural understanding, cross-file refactoring, bug investigation on synthetic codebases
**Task Format**: Harbor (via adapter, pre-generated)

---

### 3. [github_mined/](github_mined/) - Real PyTorch Pull Requests
**Task Count**: 25 available, 12 selected
**Languages**: C++ (PyTorch)
**SDLC Phase**: Implementation (bug fix)
**Focus**: Multi-file code changes on real production codebase
**Repository**: PyTorch (pytorch/pytorch)
**Task Format**: Harbor (task.toml, instruction.md, tests/)

---

### 4. [big_code_mcp/](big_code_mcp/) - Large Codebase Navigation
**Task Count**: 4 (all selected)
**Languages**: Go, Rust, C++, TypeScript
**SDLC Phase**: Implementation (feature)
**Focus**: Feature implementation in very large codebases
**Repositories**: Kubernetes, Servo, TensorRT-LLM, VS Code
**Task Format**: Harbor (task.toml, instruction.md, tests/)

---

### 5. [kubernetes_docs/](kubernetes_docs/) - Documentation Generation
**Task Count**: 5 (all selected)
**Languages**: Go
**SDLC Phase**: Documentation
**Focus**: Reconstruct doc.go/README content for stripped Kubernetes packages
**Repositories**: kubernetes/kubernetes, kubernetes/enhancements
**Task Format**: Harbor (task.toml, instruction.md, tests/)

---

### 6. [tac_mcp_value/](tac_mcp_value/) - TheAgentCompany Tasks
**Task Count**: 8 (all selected)
**Languages**: C++, Python
**SDLC Phases**: Requirements & Discovery, Implementation (feature), Testing & QA, Maintenance
**Focus**: Diverse SDE tasks (codebase search, implementation, unit testing, troubleshooting)
**Task Format**: Harbor (task.toml, instruction.md, tests/)

---

### 7. [dependeval_benchmark/](dependeval_benchmark/) - Multi-File & Cross-Repo Tasks
**Task Count**: 9 (all selected)
**Languages**: Python, Java, JavaScript
**SDLC Phases**: Implementation (refactoring), Maintenance
**Types**: Dependency Recognition (DR), Repository Construction (RC), Multi-file Editing (ME)
**Task Format**: Harbor (task.toml, instruction.md, tests/)

---

### 8. [sweperf/](sweperf/) - Performance Testing
**Task Count**: 3 (all selected)
**Languages**: Python
**SDLC Phase**: Testing & QA
**Focus**: Performance-oriented software engineering tasks
**Task Format**: Harbor (task.toml, instruction.md, tests/)

---

## Benchmark Summary

| Benchmark | Available | Selected | Languages | SDLC Phase |
|-----------|-----------|----------|-----------|------------|
| swebench_pro | 731 | 36 | Go, TypeScript, Python | Bug fixing |
| locobench_agent | 50 | 25 | 9 languages | Architecture, Refactoring |
| github_mined | 25 | 12 | C++ | Bug fixing |
| big_code_mcp | 4 | 4 | Go, Rust, C++, TypeScript | Feature implementation |
| kubernetes_docs | 5 | 5 | Go | Documentation |
| tac_mcp_value | 8 | 8 | C++, Python | Mixed (4 phases) |
| dependeval_benchmark | 9 | 9 | Python, Java, JavaScript | Refactoring, Maintenance |
| sweperf | 3 | 3 | Python | Testing & QA |
| **Total** | **835** | **102** | | |

---

## Running Benchmarks

### 3-Config Comparison (Recommended)

Each benchmark has a shell runner in [`configs/`](../configs/) that executes selected tasks across the 3-config matrix (Baseline, MCP-NoDeepSearch, MCP-Full):

```bash
# Run all selected tasks for a benchmark
bash configs/locobench_3config.sh
bash configs/swebenchpro_3config.sh
bash configs/bigcode_3config.sh
bash configs/k8s_docs_3config.sh

# Run all benchmarks from the unified runner
bash configs/run_selected_tasks.sh

# Run only baseline config
bash configs/locobench_3config.sh --baseline-only
```

### Single Task Run

```bash
harbor run --path benchmarks/big_code_mcp/big-code-vsc-001 \
  --agent-import-path agents.claude_baseline_agent:BaselineClaudeCodeAgent \
  --model anthropic/claude-haiku-4-5-20251001 \
  -n 1
```

See [`docs/CONFIGS.md`](../docs/CONFIGS.md) for the full tool-by-tool breakdown of each config.

---

## Archived Benchmarks

Unused or superseded benchmarks have been moved to [`_archived/`](../_archived/):
- `benchmarks_10figure/` - Enterprise codebase challenges (requires external corpus)
- `benchmarks_dibench/` - Dependency inference (adapter-based, variable task count)
- `benchmarks_repoqa/` - Tool-sensitive code understanding (adapter-based, variable task count)
- `benchmarks_no_external_repos/` - Hello world, PRD bench, DevAI bench prototypes

---

## Results & Analysis

After running benchmarks, generate evaluation reports:

```bash
python3 scripts/generate_eval_report.py \
  --runs-dir /path/to/runs/official/ \
  --output-dir ./eval_reports/
```

See the root [README.md](../README.md) for the full metrics extraction pipeline.
