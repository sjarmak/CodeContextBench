# PRD: Benchmark & Results Organization

**Status:** Draft
**Author:** stephanie_jarmak + claude
**Date:** 2026-03-23

## Problem

The benchmarks/ and runs/ directories have grown organically. There is no clear way to:
1. Identify which tasks constitute the current canonical benchmark suite
2. Distinguish the initial 370-task analysis set from the current 263 dual-verifier set
3. Find validated tasks by verifier type (artifact, direct, dual)
4. Link a snapshot of results to the benchmark suite that produced them
5. Browse traces for auditability in a way that's tied to a specific frozen analysis

This matters because we are preparing public results and need:
- Auditable, browsable traces linked to specific benchmark versions
- Clear separation between initial reported results and expanded results
- A versioning scheme that supports multiple frozen analysis snapshots

## Goals

### G1: Benchmark Suite Versioning
Reorganize benchmarks/ so that any consumer (human, script, CI) can unambiguously answer:
- "What are the canonical tasks right now?" (the 263 dual-verifier set)
- "What were the tasks in the initial technical report?" (the 370-task SDLC+org set)
- "What validated tasks exist, organized by verifier capability?"

### G2: Results Snapshot System
Create a snapshot mechanism for runs/ so that:
- Each frozen analysis has a unique, stable identifier
- Results are linked to the benchmark suite version that produced them
- Traces are browsable and auditable per snapshot
- New results (e.g., sonnet runs, MCP comparisons) can be added as expansion sets without breaking the initial snapshot

### G3: Trace Browsability
Ensure every snapshot has a self-contained way to explore traces:
- Per-task trace viewer (trajectory, tool calls, reward)
- Linked to the benchmark suite definition
- Sufficient metadata to understand config, model, MCP type
- Publishable to the public branch

### G4: Metadata Integrity
Every snapshot must include enough metadata to reconstruct:
- Which tasks were in the suite
- Which configs were run (baseline, mcp-remote-direct, augment-local-direct, etc.)
- Model used
- Reward scores, timing, cost, IR metrics
- Config fingerprint for reproducibility

## Non-Goals
- Changing the task definition format (task.toml stays as-is)
- Migrating historical runs that predate the analysis/ structure
- Building a web service — static HTML + JSON is sufficient
- Changing the harness or Harbor integration

## Terminology

| Term | Definition |
|------|-----------|
| **Benchmark suite** | A named, versioned set of task IDs with metadata about verifier type |
| **Snapshot** | A frozen set of results tied to a benchmark suite, with a unique ID |
| **Canonical suite** | The currently active benchmark suite (e.g., `csb-v2-dual263`) |
| **Trace** | The full audit trail for one task run: trajectory.json, tool calls, reward, timing |
| **Expansion set** | Results beyond the initial snapshot, run against the same or overlapping tasks |

## Design

### 1. Benchmark Directory Structure

```
benchmarks/
  suites/                          # Suite definitions (the source of truth)
    csb-v1-mixed370.json           # Initial 370-task suite (SDLC + org, mixed verifiers)
    csb-v2-dual263.json            # Current 263 dual-verifier canonical suite
    csb-v2-full-validated.json     # All validated tasks, superset

  tasks/                           # All task definitions (flat or by original suite)
    csb_sdlc_debug/
      linux-acpi-backlight-fault-001/
      ...
    csb_sdlc_fix/
      django-modelchoice-fk-fix-001/
      ...
    csb_org_migration/
      ccx-migration-026/
      ...
    ...

  indexes/                         # Derived indexes (generated, not hand-edited)
    by-verifier-type/
      dual.json                    # Task IDs that support both direct + artifact verification
      direct-only.json             # Tasks with direct verification only
      artifact-only.json           # Tasks with artifact verification only
    by-language.json
    by-difficulty.json
    by-repo.json
```

**Suite definition schema** (`csb-v1-mixed370.json`):
```json
{
  "suite_id": "csb-v1-mixed370",
  "version": "1.0",
  "created": "2026-03-26",
  "description": "Initial 370-task benchmark suite used for first technical report",
  "task_count": 370,
  "verifier_breakdown": {
    "direct": 180,
    "artifact": 120,
    "dual": 70
  },
  "tasks": [
    {
      "task_id": "django-modelchoice-fk-fix-001",
      "suite": "csb_sdlc_fix",
      "verifier_modes": ["direct", "artifact"],
      "language": "python",
      "difficulty": "hard"
    }
  ],
  "frozen": true,
  "technical_report": "docs/technical_reports/initial_report.md"
}
```

### 2. Results Snapshot Structure

```
runs/
  snapshots/
    csb-v1-mixed370--haiku45--030326/       # Snapshot ID = suite--model--date
      SNAPSHOT.json                          # Snapshot manifest
      traces/                                # Browsable per-task traces
        baseline-local-direct/
          django-modelchoice-fk-fix-001/
            trajectory.json
            task_metrics.json
            reward.txt
            instruction.txt
          ...
        mcp-remote-direct/
          django-modelchoice-fk-fix-001/
            trajectory.json
            task_metrics.json
            reward.txt
            instruction.txt
          ...
      summary/
        rewards.json                         # All task rewards by config
        timing.json                          # Wall clock, agent time, setup time
        costs.json                           # Per-task cost breakdown
        ir_metrics.json                      # Precision, recall, F1 per task
        aggregate.json                       # Mean scores, totals
      browse.html                            # Self-contained trace viewer

    csb-v1-mixed370--sonnet46--expanded/     # Expansion: sonnet runs on same suite
      SNAPSHOT.json
      traces/
      summary/
      browse.html

    csb-v2-dual263--haiku45--040101/         # Future: canonical suite results
      ...
```

**Snapshot manifest schema** (`SNAPSHOT.json`):
```json
{
  "snapshot_id": "csb-v1-mixed370--haiku45--030326",
  "suite_id": "csb-v1-mixed370",
  "suite_version": "1.0",
  "model": "claude-haiku-4-5-20251001",
  "configs": ["baseline-local-direct", "mcp-remote-direct"],
  "created": "2026-03-26",
  "frozen": true,
  "description": "Initial technical report results — haiku 4.5 baseline vs Sourcegraph MCP",
  "task_count": 370,
  "tasks_completed": 358,
  "tasks_errored": 12,
  "aggregate": {
    "baseline-local-direct": {"mean_reward": 0.52, "total_cost": 45.20, "total_agent_minutes": 180.5},
    "mcp-remote-direct": {"mean_reward": 0.58, "total_cost": 52.10, "total_agent_minutes": 120.3}
  },
  "source_runs": [
    "runs/staging/csb_sdlc_debug_haiku_20260301_...",
    "runs/staging/csb_org_migration_haiku_20260301_..."
  ],
  "config_fingerprint": "f52a5fd2bf40",
  "parent_snapshot": null,
  "expansion_of": null
}
```

### 3. Snapshot ID Scheme

Format: `{suite_id}--{model_short}--{date_or_hash}`

Examples:
- `csb-v1-mixed370--haiku45--030326` — initial report, frozen March 26
- `csb-v1-mixed370--sonnet46--expanded` — sonnet expansion on same suite
- `csb-v1-mixed370--opus46--mcp-comparison` — MCP comparison (augment/github/sg)
- `csb-v2-dual263--haiku45--040101` — future canonical suite

The `--expanded` or `--mcp-comparison` suffix distinguishes non-date-frozen snapshots.

### 4. Trace Browser

Each snapshot gets a `browse.html` that:
- Lists all tasks with reward, timing, cost columns
- Sortable/filterable by config, suite, reward, language
- Click-to-expand shows trajectory (tool calls, MCP calls, timing)
- Shows diff between configs (baseline vs MCP reward delta)
- Self-contained (inline CSS/JS, JSON data embedded or co-located)
- Works when published to the `public` branch

### 5. Export & Sanitization Pipeline

Before publishing a snapshot to the public branch:

```
scripts/publishing/export_snapshot.py --snapshot csb-v1-mixed370--haiku45--030326
```

This script:
1. Resolves all symlinks to verify trace integrity
2. Copies traces to `docs/official_results/{snapshot_id}/`
3. Sanitizes: strips absolute paths, account names, OAuth tokens from transcripts
4. Runs secret detection (same patterns as pre-commit hook)
5. Generates `browse.html` with embedded data
6. Validates: every task in suite JSON has a corresponding trace

### 6. Migration Plan

**Phase 1: Create suite definitions** (no file moves)
- Generate `benchmarks/suites/csb-v1-mixed370.json` from existing runs/analysis data
- Generate `benchmarks/suites/csb-v2-dual263.json` from current selected_benchmark_tasks.json
- Generate `benchmarks/suites/csb-v2-full-validated.json` — all tasks with valid results
- Generate verifier-type indexes under `benchmarks/indexes/`

**Phase 2: Create first snapshot**
- Package runs/analysis/ haiku baseline+MCP results into `runs/snapshots/csb-v1-mixed370--haiku45--030326/`
- Symlink traces from source runs
- Generate summary JSONs (rewards, timing, costs, IR metrics)
- Generate browse.html
- Run `verify_snapshot.py` to confirm all 370 tasks have traces

**Phase 3: Create expansion snapshots**
- Package sonnet runs as `csb-v1-mixed370--sonnet46--expanded`
- Package opus MCP comparison as `csb-v1-mixed370--opus46--mcp-comparison`
- Set `expansion_of` in SNAPSHOT.json to link to parent

**Phase 4: Reorganize benchmarks/**
- Move task definitions from `benchmarks/csb_sdlc_*` and `benchmarks/csb_org_*` into `benchmarks/tasks/`
- Remove duplicate `benchmarks/csb/` directory
- Delete `configs/selected_benchmark_tasks.json` (replaced by suite JSON)
- Update all path references in harness scripts, agent code, evaluation scripts

**Phase 5: Update harness integration**
- `run_selected_tasks.sh` reads suite JSON via `--suite-file benchmarks/suites/csb-v2-dual263.json`
- Post-run hook auto-creates snapshot stub with symlinks
- `export_snapshot.py` for public branch publishing
- `verify_snapshot.py` added to `repo_health.py` checks

## Decisions

1. **Symlinks for snapshots.** Traces are large; symlinks avoid duplication while keeping
   the snapshot directory navigable. If a source run is moved or deleted, the symlink
   breaks visibly (preferred over silent staleness). A `verify_snapshot.py` script will
   check for broken links before publishing.

2. **Keep suite subdirectories.** Tasks remain in `benchmarks/tasks/csb_sdlc_fix/task-name/`
   etc. Suite membership is defined in the suite JSON, but the directory grouping matches
   the category design and is familiar to all tooling.

3. **Tasks in multiple suites:** A task like `django-modelchoice-fk-fix-001` lives in one
   place under `benchmarks/tasks/csb_sdlc_fix/`. Both `csb-v1-mixed370.json` and
   `csb-v2-dual263.json` reference it by task_id + suite path. No duplication.

4. **Public branch: export with sanitization.** A `scripts/publishing/export_snapshot.py`
   script copies a snapshot to `docs/official_results/`, sanitizes absolute paths, strips
   credentials/account names from transcripts, and validates no secrets are present.
   This is safer than pushing snapshots directly to `upstream`.

5. **No backward compatibility.** `configs/selected_benchmark_tasks.json` will be replaced
   by the suite JSON system. All harness scripts will be updated to read suite definitions
   directly. The old file will be deleted (not deprecated).

## Open Questions

1. **Duplicate tasks in `benchmarks/csb/` vs `benchmarks/csb_sdlc_*/csb_org_*`:** Several
   tasks exist in both the legacy `csb/` flat structure and the suite-organized directories.
   During Phase 4, we need to deduplicate — keep the suite-organized copy, remove `csb/`.

## Success Criteria

- [ ] Any user can answer "what's in the canonical benchmark?" by reading one JSON file
- [ ] The initial 370-task results are frozen with a stable identifier and browsable traces
- [ ] Expanded results (sonnet, opus, MCP comparisons) are linked but distinct from the initial report
- [ ] `python3 scripts/maintenance/repo_health.py` passes after migration
- [ ] Harness scripts work with new layout without manual path edits
- [ ] browse.html works when pushed to the public branch
- [ ] Traces are auditable: for any reported number, you can trace back to the raw trajectory
