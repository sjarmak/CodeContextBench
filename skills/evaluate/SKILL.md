---
name: evaluate
description: Extract metrics, score traces, and evaluate benchmark task results.
---

# Skill: Evaluate Results

## Scope

Use this skill when the user asks to:
- Extract and compute task metrics from completed runs
- Score traces and verify dual verification
- Re-extract metrics after trace updates
- Compare verifier outputs and validate scoring
- Generate evaluation reports

## Canonical Commands

```bash
# Extract task metrics from a run
python3 scripts/evaluation/extract_task_metrics.py --run-dir runs/staging/run_dir

# Score all traces in a run
python3 scripts/evaluation/trace_quality_pipeline.py --run-dir runs/staging/run_dir

# Reextract metrics for specific suite
python3 scripts/evaluation/reextract_all_metrics.py --filter csb_sdlc_debug

# Compute retrieval metrics (IR tasks)
python3 scripts/evaluation/compute_retrieval_metrics.py --run-dir runs/staging/run_dir

# Dual verification check
python3 scripts/evaluation/cross_validate_oracles.py --run-dir runs/staging/run_dir
```

## Metrics Pipeline

1. **Trace extraction** → parse trajectory.json for tool calls, outputs, reasoning
2. **Oracle verification** → compare against ground truth (local + Sourcegraph)
3. **Dual scoring** → compute reward for baseline and MCP configs
4. **Aggregation** → roll up to suite and model level
5. **Quality gates** → flag inconsistencies and outliers

## Verification Modes

- **Local verification** — on-disk oracle checks
- **Sourcegraph (SG) verification** — MCP-based symbol resolution
- **Dual** — both pass (canonical tasks)

## Related Skills

- `/run` — launch runs to generate traces
- `/report` — compile evaluation reports
- `/audit` — validate trace quality and consistency
