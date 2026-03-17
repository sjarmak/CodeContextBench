---
name: run
description: Launch and manage CodeScaleBench benchmark runs with paired-run guardrails, quick reruns, and execution orchestration.
---

# Skill: Run Benchmarks

## Scope

Use this skill when the user asks to:
- Run benchmark suites, rerun failures, or launch gap-fill batches
- Manage multi-account parallel execution
- Execute paired baseline+MCP runs with curation guardrails
- Perform quick reruns of specific tasks or suites

## Approval Gate (Required Before Running)

Before executing any benchmark run, confirm with the user:

1. **Model** — which model? (e.g., `anthropic/claude-haiku-4-5-20251001` for test runs)
2. **Suite / selection file** — which benchmark suite or `--selection-file`?
3. **Config** — paired (default), `--baseline-only`, or `--full-only`? Which `--full-config`?
4. **Parallel slots** — how many? (default: auto-detect; use 8+ for multi-account)
5. **Category** — `staging` (default) or `official`?

**Do NOT launch a run until the user has confirmed these five parameters.**

## Canonical Commands

- Per-suite default: `./configs/harnesses/<suite>_2config.sh`
- Unified selected-task runner: `./configs/harnesses/run_selected_tasks.sh`
- Config registry: `configs/eval_matrix.json`
- Quick rerun: use `--rerun` flag on base command

## Run Policy (Mandatory)

- Default execution is **paired by task**: `baseline` + `sourcegraph_full`
- Single-lane runs are **gap-fill only**:
  - `--baseline-only` requires valid existing `sourcegraph_full` counterpart runs
  - `--full-only` requires valid existing `baseline` counterpart runs
- Emergency bypass only: `ALLOW_UNPAIRED_SINGLE_CONFIG=true`
- Account readiness: Always run `python3 scripts/infra/account_health.py status` before launching

## Standard Launch Patterns

```bash
# Paired per-suite run
./configs/harnesses/pytorch_2config.sh --parallel 4

# Paired selected-task run
./configs/harnesses/run_selected_tasks.sh --benchmark csb_sdlc_pytorch

# Gap-fill baseline only (guarded)
./configs/harnesses/run_selected_tasks.sh --benchmark csb_sdlc_pytorch --baseline-only

# Quick rerun of failed tasks
./configs/harnesses/run_selected_tasks.sh --benchmark csb_sdlc_pytorch --rerun failed
```

## Infrastructure

- **Default environment**: Daytona (see `docs/DAYTONA.md`)
- **Parallelism**: Auto-detected from account count and rate limits; override with `--parallel N`
- **Orchestration**: `scripts/running/control_plane.py` manages multi-account scheduling
- **Monitoring**: `scripts/running/monitor_and_queue.sh` watches active runs

## Related Skills

- `/status` — monitor active runs, check completion
- `/audit` — post-run validation and integrity checks
- `/evaluate` — extract and score results
