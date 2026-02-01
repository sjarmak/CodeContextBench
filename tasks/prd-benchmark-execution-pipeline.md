# PRD: Benchmark Execution Pipeline for Paper Results

## Introduction

Get CodeContextBench benchmark runs producing valid, comparable results across 3 agent configurations so the paper's Results section (Section 4) can be populated with real data. The benchmarks repo (`sjarmak/CodeContextBench`) contains task definitions; the runner infrastructure lives at `~/evals/custom_agents/agents/claudecode/`. This PRD covers the work needed in **both** repos to go from current state (1 working benchmark, 2 broken) to all benchmarks producing results across a consistent 3-config matrix.

### Current State

| Benchmark | Tasks | Configs Run | Status |
|-----------|-------|-------------|--------|
| LoCoBench | 50 | baseline, deepsearch | Working. Mean reward ~0.50 for both. Needs re-run with final config names. |
| SWE-Bench Pro | 48 | baseline, deepsearch | Agent works (6-14M input tokens/task) but 0 tasks pass all required tests. Not an infra bug — genuine agent performance. 16/48 partial passes per mode. |
| BigCode MCP | 4 | baseline, sourcegraph_hybrid, deepsearch_hybrid | All batches show 0 completed task dirs. Tasks fail to produce results. Infra bug. |
| K8s Docs | 5 | baseline, sourcegraph | Individual jobs in `CodeContextBench/jobs/`. Not run through standard pipeline. No result.json. |

### Key Decisions Made

1. **3-config matrix** (not 5): Baseline, MCP-NoDeepSearch (`sourcegraph_no_deepsearch`), MCP-Full (`sourcegraph_hybrid`). SCIP not separately controllable.
2. **Fix SWE-Bench Pro first**: Largest dataset, most comparable to published benchmarks.
3. **Repos stay separate**: Benchmarks in `sjarmak/CodeContextBench`, runner at `~/evals/custom_agents/agents/claudecode/`.
4. **Re-run LoCoBench**: With final config names for consistency across benchmarks.

## Goals

- All 4 benchmarks (LoCoBench, SWE-Bench Pro, BigCode MCP, K8s Docs) produce valid results across 3 configs
- Consistent config naming: `baseline`, `sourcegraph_no_deepsearch`, `sourcegraph_hybrid`
- Results stored in `runs/official/` with standard directory structure
- Post-processing extracts metrics needed for paper tables (reward, tokens, tool usage, timing)
- Paper's Section 4 tables can be populated from the data

## User Stories

### US-001: Diagnose and Fix BigCode MCP Empty Results
**Description:** As a researcher, I want BigCode MCP runs to produce task result directories so I can collect benchmark data from large-codebase tasks.

**Acceptance Criteria:**
- [ ] Investigate why all BigCode batch directories have 0 task subdirectories despite logs existing (`big-code-k8s-001.log`, etc.)
- [ ] Read the BigCode comparison shell script (`configs/bigcode_mcp_comparison.sh`) and trace the Harbor invocation to identify the failure point
- [ ] Check Harbor logs for the BigCode runs in `runs/official/bigcode_mcp_opus_20260131_130446/baseline/` for error messages
- [ ] Identify root cause (likely: Docker image pull failure, resource limits, task path resolution, or Harbor config issue)
- [ ] Apply fix and verify by running 1 BigCode task (e.g., `big-code-k8s-001`) in baseline mode, confirming a task directory with `agent/`, `verifier/`, and `result.json` is produced
- [ ] Document the root cause and fix in a brief note for reproducibility

### US-002: Standardize Agent Configs to 3-Config Matrix
**Description:** As a researcher, I want exactly 3 named agent configurations that map to the paper's methodology so all benchmarks use identical config definitions.

**Acceptance Criteria:**
- [ ] Verify `BASELINE_MCP_TYPE=none` (Baseline) works correctly — no MCP tools available to agent
- [ ] Verify `BASELINE_MCP_TYPE=sourcegraph_no_deepsearch` (MCP-NoDeepSearch) works correctly — keyword search + NLS available, Deep Search NOT available
- [ ] Verify `BASELINE_MCP_TYPE=sourcegraph_hybrid` (MCP-Full) works correctly — all Sourcegraph tools including Deep Search available
- [ ] For each config, confirm the exact tool whitelist by checking what tools appear in the agent's `mcp_servers` init line in a trace
- [ ] Document the 3 configs with their tool lists in a `CONFIGS.md` file at `~/evals/custom_agents/agents/claudecode/docs/CONFIGS.md`
- [ ] Update paper Table 1 mapping: Baseline=`none`, MCP-Base=`sourcegraph_no_deepsearch`, MCP-Full=`sourcegraph_hybrid`

### US-003: Create Unified Comparison Configs for All Benchmarks
**Description:** As a researcher, I want YAML configs for each benchmark that run all 3 agent configurations so I can execute the full comparison matrix with a single command per benchmark.

**Acceptance Criteria:**
- [ ] Create `configs/locobench_3config.yaml` with `mcp_modes: [baseline, sourcegraph_no_deepsearch, sourcegraph_hybrid]` and all 50 LoCoBench task IDs
- [ ] Create `configs/swebenchpro_3config.yaml` with same 3 modes and all 50 SWE-Bench Pro task IDs (from existing `swebenchpro_50_tasks_comparison.yaml`)
- [ ] Create `configs/bigcode_3config.yaml` with same 3 modes and all 4 BigCode task IDs
- [ ] All configs use pinned model `anthropic/claude-opus-4-5-20251101`
- [ ] All configs set `run_category: official`
- [ ] Each config has a corresponding shell script runner (`.sh`) if the benchmark requires it (BigCode and LoCoBench use shell scripts)
- [ ] Dry-run (`./run-eval dry-run -c configs/<name>.yaml`) succeeds for each config, showing the expected 3 x N task matrix

### US-004: Integrate K8s Docs into Standard Runner Pipeline
**Description:** As a researcher, I want K8s Docs tasks to run through the same `run-eval` pipeline as other benchmarks so results are in consistent format.

**Acceptance Criteria:**
- [ ] Create `configs/k8s_docs_3config.yaml` (or `.sh`) that runs all 5 K8s Docs tasks through Harbor with the 3-config matrix
- [ ] Task paths point to `CodeContextBench/benchmarks/ccb_k8sdocs/` task directories
- [ ] Verify Harbor can execute K8s Docs tasks: agent gets instruction, produces output, verifier runs `test.sh` and generates `reward.txt`
- [ ] Results land in `runs/official/k8s_docs_<timestamp>/` with standard structure (`baseline/`, `sourcegraph_no_deepsearch/`, `sourcegraph_hybrid/` subdirectories)
- [ ] Each task directory contains `agent/claude-code.txt`, `verifier/reward.txt`, and `result.json`

### US-005: Execute LoCoBench 3-Config Official Run
**Description:** As a researcher, I want fresh LoCoBench results with the final 3-config naming so data is consistent with other benchmarks.

**Acceptance Criteria:**
- [ ] Run all 50 LoCoBench tasks under `baseline`, `sourcegraph_no_deepsearch`, and `sourcegraph_hybrid`
- [ ] Results stored in `runs/official/locobench_3config_<timestamp>/`
- [ ] All 150 task directories (50 x 3) contain `reward.txt` with valid scores
- [ ] Mean reward computed per config and documented
- [ ] Traces (`agent/claude-code.txt`) present for all runs

### US-006: Execute SWE-Bench Pro 3-Config Official Run
**Description:** As a researcher, I want SWE-Bench Pro results across all 3 configs to measure agent performance on real-world issue resolution.

**Acceptance Criteria:**
- [ ] Run all 48-50 SWE-Bench Pro tasks under `baseline`, `sourcegraph_no_deepsearch`, and `sourcegraph_hybrid`
- [ ] Results stored in `runs/official/swebenchpro_3config_<timestamp>/`
- [ ] All task directories contain `verifier/test-stdout.txt` with pass/fail counts
- [ ] Per-config metrics computed: full pass rate, partial pass rate (any tests passing), mean partial score
- [ ] Note: Expect low absolute pass rates (0% full pass in prior runs). The value is in comparing across configs.

### US-007: Execute BigCode MCP 3-Config Official Run
**Description:** As a researcher, I want BigCode MCP results to show MCP impact on large codebases.

**Acceptance Criteria:**
- [ ] Run all 4 BigCode tasks under all 3 configs (requires US-001 fix first)
- [ ] Results stored in `runs/official/bigcode_3config_<timestamp>/`
- [ ] All 12 task directories (4 x 3) contain verifier results
- [ ] Serial execution (concurrency=1) due to large repo sizes

### US-008: Execute K8s Docs 3-Config Official Run
**Description:** As a researcher, I want K8s Docs results through the standard pipeline for documentation generation analysis.

**Acceptance Criteria:**
- [ ] Run all 5 K8s Docs tasks under all 3 configs (requires US-004 integration first)
- [ ] Results stored in `runs/official/k8s_docs_3config_<timestamp>/`
- [ ] All 15 task directories (5 x 3) contain `verifier/reward.txt`
- [ ] Ground truth comparison via existing `evaluate_docs.py` LLM judge run on all outputs

### US-009: Build Post-Processing Script for Paper Tables
**Description:** As a researcher, I want a single script that reads all official runs and produces the data tables needed for paper Section 4.

**Acceptance Criteria:**
- [ ] Script takes run directories as input (or auto-discovers from `runs/official/`)
- [ ] Produces **Table: Aggregate Performance** — per-config success rate and mean reward across all benchmarks
- [ ] Produces **Table: Per-Benchmark Breakdown** — success rate and mean reward per benchmark per config
- [ ] Produces **Table: Efficiency Metrics** — mean input tokens, output tokens, cache tokens, wall-clock time per config
- [ ] Produces **Table: Tool Utilization** — MCP tool call count, local tool call count, MCP/total ratio per config (extracted from trajectory.json or claude-code.txt)
- [ ] Outputs both markdown (for quick review) and CSV (for analysis) formats
- [ ] Handles missing data gracefully (e.g., if a benchmark only has 2 of 3 configs complete)

### US-010: Push Benchmarks Repo to GitHub
**Description:** As a researcher, I want the CodeContextBench benchmarks repo pushed to GitHub so it serves as the reproducibility artifact referenced in the paper.

**Acceptance Criteria:**
- [ ] `benchmarks-only` branch content pushed to `main` on `sjarmak/CodeContextBench` (currently only initial commit is on remote)
- [ ] Verify all benchmark directories are present: `ccb_k8sdocs/`, `ccb_largerepo/`, `ccb_pytorch/`, `ccb_locobench/`, `ccb_swebenchpro/`, `ccb_dibench/`, `ccb_repoqa/`
- [ ] README.md updated with benchmark descriptions and task counts
- [ ] No credentials, API keys, or `.env` files included
- [ ] MANIFEST.json present for benchmarks that have them

## Functional Requirements

- FR-1: The `BASELINE_MCP_TYPE` environment variable must accept exactly these values: `none`, `sourcegraph_no_deepsearch`, `sourcegraph_hybrid`
- FR-2: The `sourcegraph_no_deepsearch` mode must configure the Sourcegraph MCP endpoint but exclude `sg_deepsearch` from the allowed tools list
- FR-3: All YAML configs for official runs must use pinned model `anthropic/claude-opus-4-5-20251101` (not the auto-resolving `claude-opus-4-5`)
- FR-4: Post-processing must extract tool usage from `trajectory.json` (ATIF v1.2 format) — specifically counting calls to `mcp__sourcegraph__*` tools vs local tools
- FR-5: All official runs must use `run_category: official` and store results under `runs/official/`
- FR-6: For SWE-Bench Pro, partial scores must be computed as (required tests passed / total required tests) since full pass rate is expected to be very low
- FR-7: K8s Docs evaluation must include both test.sh verification scores AND LLM judge scores (via `evaluate_docs.py`)

## Non-Goals

- **DI-Bench, RepoQA, Agent Company**: Deferred to future work. Not included in this execution round.
- **Paper writing**: This PRD produces data; prose for Sections 4-6 is authored separately.
- **Dashboard updates**: The Streamlit dashboard exists on the CodeContextBench `main` branch but updating it is not in scope.
- **Statistical significance testing**: Deferred to post-processing analysis after data collection.
- **Human evaluation sampling**: The 10% human eval described in the paper methodology is deferred.
- **LaTeX table formatting**: Markdown/CSV output is sufficient; LaTeX formatting is a separate step.

## Technical Considerations

### Runner Infrastructure Location
All runner changes happen in `~/evals/custom_agents/agents/claudecode/`:
- Agent code: `agents/claude_baseline_agent.py`
- Configs: `configs/`
- Runner lib: `lib/`
- Scripts: `scripts/`
- Results: `runs/official/`

### Benchmark Task Paths
Configs reference CodeContextBench benchmark dirs via absolute paths:
- LoCoBench: `/home/stephanie_jarmak/CodeContextBench/benchmarks/ccb_locobench/tasks`
- BigCode: `/home/stephanie_jarmak/CodeContextBench/benchmarks/ccb_largerepo`
- K8s Docs: `/home/stephanie_jarmak/CodeContextBench/benchmarks/ccb_k8sdocs`
- SWE-Bench Pro: Uses Harbor registry (`swebenchpro@1.0`), not local paths

### MCP Mode Implementation
The `sourcegraph_no_deepsearch` mode already has code paths in `claude_baseline_agent.py` (line ~250). It connects to the same Sourcegraph MCP endpoint but should exclude `sg_deepsearch` from the `--allowedTools` list. Verification needed that this filtering actually works (the tool might still appear in `mcp_servers` but be blocked by the allow list).

### SWE-Bench Pro Expectations
Prior runs show 0% full pass rate but ~33% partial pass rate (16/48 tasks with some tests passing). This is not an infrastructure bug — the agent does real work (6-14M tokens per task) but fails to resolve all required tests. The paper should frame this as partial resolution analysis rather than binary pass/fail.

### Cost Estimates
Based on existing runs (Opus 4.5, ~10M input tokens avg per SWE-Bench task):
- LoCoBench: 50 tasks x 3 configs = 150 runs
- SWE-Bench Pro: 48 tasks x 3 configs = 144 runs
- BigCode: 4 tasks x 3 configs = 12 runs
- K8s Docs: 5 tasks x 3 configs = 15 runs
- **Total: ~321 runs**

## Success Metrics

- All 4 benchmarks have at least 1 complete official run across all 3 configs
- Post-processing script produces comparison tables from the run data
- Clear signal visible in at least 1 benchmark showing config differentiation (MCP vs baseline)
- Data sufficient to write paper Section 4.1 (Aggregate Performance) and 4.2 (Per-Benchmark Breakdown)

## Open Questions

1. **SWE-Bench Pro scoring**: Should we use binary pass/fail (0% for all configs) or partial scores (tests_passed/tests_required)? Partial scores give more signal but deviate from standard SWE-Bench reporting.
2. **LoCoBench deepsearch vs sourcegraph_hybrid**: The existing run used `deepsearch` mode (deprecated). Will `sourcegraph_hybrid` produce meaningfully different results since it includes the same Deep Search plus additional tools?
3. **BigCode root cause**: The failure mode (0 task dirs despite logs) needs investigation before we can estimate if it's a quick fix or a deeper Harbor integration issue.
4. **K8s Docs verifier**: The existing `test.sh` scripts produce 0-10 point scores. Should these be normalized to 0.0-1.0 for consistency with other benchmarks?
