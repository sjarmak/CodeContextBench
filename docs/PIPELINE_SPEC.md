# CSB Pipeline Specification

> **When To Read This**: Before implementing any harness, gap detection script, or result
> scanner. This doc is the acceptance criteria for all work under epic co-7dk. New code
> that handles runs, validation, or coverage MUST conform to these contracts.

---

## Overview

The CSB pipeline has five stages: **Selection → Gap Detection → Execution → Validation →
Coverage/Promotion**. Each stage has a defined input and output contract. A single
parameterized harness replaces the 27 duplicate `*_2config.sh` wrappers that previously
scattered this logic.

---

## 1. Result Contract

### 1.1 Canonical Result Location

All task results MUST be written to an **absolute path** derived from `CSB_RUNS_DIR`:

```
${CSB_RUNS_DIR}/${CATEGORY}/${AGENT}_${MODEL_SHORT}_${TIMESTAMP}/${CONFIG}/${BATCH_TS}/${TASK_ID}__${HASH}/
```

| Segment | Example | Notes |
|---------|---------|-------|
| `CSB_RUNS_DIR` | `/home/user/gt/runs` | Mandatory env var. Never relative. |
| `CATEGORY` | `staging`, `official` | Run category label. |
| `AGENT` | `openhands`, `claude` | Agent short name. |
| `MODEL_SHORT` | `sonnet46`, `haiku45` | Normalized model identifier. |
| `TIMESTAMP` | `20260319_140523` | Run start time, `%Y%m%d_%H%M%S`. |
| `CONFIG` | `baseline-local-direct`, `mcp-remote-direct` | Canonical config name. |
| `BATCH_TS` | `2026-03-19__14-05-23` | Harbor batch timestamp. |
| `TASK_ID__HASH` | `k8s-taint-feat-001__AbCdEfG` | Task dir from Harbor. |

**`CSB_RUNS_DIR` is mandatory.** Harnesses MUST fail at startup if it is unset or empty.
A relative fallback (e.g. `runs/`) is not permitted — it silently produces different paths
in worktrees and causes gap detection to miss results. See co-0it for the root incident.

### 1.2 Required Files Per Task

Every executed task directory MUST contain:

| File | Owner | Notes |
|------|-------|-------|
| `result.json` | Harbor | Task-level result. Must have `task_name` field. |
| `task_metrics.json` | Post-processing | Extracted by `scripts/evaluation/extract_task_metrics.py`. |
| `verifier/validation_result.json` | Verifier | Required even on failure. See §1.3. |

### 1.3 `validation_result.json` Schema

Path inside the task dir: `verifier/validation_result.json`
(Inside the container this maps to `/logs/verifier/validation_result.json`.)

Schema version: `validation_result.v1alpha1`

**Required fields** (all statuses):

```json
{
  "schema_version": "validation_result.v1alpha1",
  "status": "scored | invalid_output | verifier_error",
  "scorable": true,
  "scorer_family": "oracle_checks | test_ratio | ...",
  "reward": 0.75,
  "pass_threshold": 0.0,
  "passed": true,
  "output_contract": {
    "mode": "repo_state | answer_json_native | ...",
    "primary_path": "/workspace/answer.json",
    "required_artifact": false
  },
  "sub_scores": {},
  "failure": null
}
```

**Status values:**

| Value | Meaning |
|-------|---------|
| `scored` | Verifier ran and produced a reward. |
| `invalid_output` | Agent output was missing or malformed. |
| `verifier_error` | Verifier itself threw an exception. |

**No silent drops.** Every task execution — including crashes, timeouts, and missing
agent output — MUST produce a `validation_result.json` with an appropriate non-`scored`
status, `reward=0.0`, and a populated `failure` object.

See `docs/reference/VALIDATION_RESULT_SCHEMA.md` for the full field inventory.

---

## 2. Harness Interface

### 2.1 Canonical Config Names

| Config | `BASELINE_MCP_TYPE` | Dockerfile used |
|--------|---------------------|-----------------|
| `baseline-local-direct` | `none` | `environment/Dockerfile` |
| `mcp-remote-direct` | `sourcegraph_full` | `environment/Dockerfile.sg_only` |
| `baseline-local-artifact` | `none` | `environment/Dockerfile.artifact_baseline` |
| `mcp-remote-artifact` | `sourcegraph_full` | `environment/Dockerfile.artifact_only` |

Config names are stable identifiers. They appear in result directory paths and in
`validation_result.json`. Do not invent new names without updating `configs/_common.sh`
and `docs/reference/CONFIGS.md`.

### 2.2 Required CLI Flags

A compliant harness MUST accept these flags:

| Flag | Type | Meaning |
|------|------|---------|
| `--agent` | string | Agent identifier (e.g. `openhands`, `claude`). |
| `--config` | string | Config name(s) to run (see §2.1). Repeatable or comma-separated. |
| `--subset` | path | Selection JSON file (default: `configs/selected_benchmark_tasks.json`). |
| `--skip-completed` | bool | Skip tasks where `validation_result.json` has `status=scored`. |
| `--parallel` | int | Max concurrent task slots. Default: auto-detect from accounts. |
| `--accounts` | int/string | Override account count or list account home dirs. |
| `--dry-run` | bool | Print planned runs without executing. |
| `--category` | string | Run category label written into the result path (default: `staging`). |

### 2.3 Required Environment Variables

| Variable | Required | Default | Meaning |
|----------|----------|---------|---------|
| `CSB_RUNS_DIR` | **MANDATORY** | — | Absolute path for all results. Harness exits 1 if unset. |
| `CSB_SKIP_CONFIRM` | optional | `0` | Set to `1` to suppress the interactive launch gate. |

### 2.4 Required Runtime Behaviors

#### Skip-Completed

When `--skip-completed` is active, a task+config pair is considered complete if and
only if:

```
${CSB_RUNS_DIR}/.../baseline-local-direct/.../task-id__*/verifier/validation_result.json
```
exists and contains `"status": "scored"`. Existence of `result.json` alone is not
sufficient — the task may have run but failed validation.

#### Circuit Breaker

Each task has a **per-config attempt counter** persisted in the run state file (§2.5).
When a task's attempt count reaches `MAX_ATTEMPTS` (default: 3), the harness MUST:

1. Mark the task as `quarantined` in the run state file.
2. Write a synthetic `validation_result.json` with `status="verifier_error"`,
   `reward=0.0`, and a `failure` object explaining the quarantine reason.
3. Log the quarantine with task ID, config, attempt count, and last error.
4. Continue with remaining tasks — do not abort the run.

#### Per-Task Validation

`validation_result.json` MUST be written during task execution, not deferred to batch
end. If the harness crashes after task 50 of 100, tasks 1–50 must already have
their validation records. Batch-end-only validation (the current OH bug, co-zyy) is
non-compliant.

#### Persistent Run State File

The harness MUST write a JSON state file at:

```
${CSB_RUNS_DIR}/${CATEGORY}/${AGENT}_${MODEL_SHORT}_${TIMESTAMP}/run_state.json
```

Schema:

```json
{
  "schema_version": "run_state.v1",
  "run_id": "openhands_sonnet46_20260319_140523",
  "started_at": "2026-03-19T14:05:23Z",
  "tasks": {
    "k8s-taint-feat-001": {
      "baseline-local-direct": {
        "status": "scored | failed | quarantined | pending | running",
        "attempts": 1,
        "last_error": null,
        "result_dir": "/abs/path/to/task/dir"
      }
    }
  }
}
```

The state file is updated atomically (write to `.tmp` then rename) after each task
completes. It enables crash recovery without re-running already-scored tasks.

### 2.5 Single Parameterized Harness

The 27 `*_2config.sh` files (co-85k) MUST be replaced by a single harness that accepts
`--agent` and `--config` flags. The goal is:

```bash
# Instead of:
./configs/harnesses/openhands_2config.sh
./configs/harnesses/feature_2config.sh
./configs/harnesses/fix_2config.sh
# ...24 more

# One harness (to be created in co-85k, name TBD):
run_harness --agent openhands --config baseline-local-direct,mcp-remote-direct
run_harness --agent claude --config baseline-local-direct
```

Shared logic currently in `configs/_common.sh` (account rotation, token refresh,
cost guard, confirm gate, trajectory check) is preserved as library code.

---

## 3. Pipeline Stages

### Stage 1: Selection

**Input**: `configs/selected_benchmark_tasks.json` (canonical) or `--subset` override.

**Output**: Ordered list of `(task_id, task_dir, benchmark)` tuples.

**Contract**:
- Tasks with `"excluded": true` are filtered out.
- `task_dir` is relative to `benchmarks/`; harness prepends repo root to get absolute path.
- Supports both `benchmark` field (standard) and `mcp_suite` field (MCP-unique tasks).
- `--dry-run` output confirms the final task list before any execution.

### Stage 2: Gap Detection

**Input**: `selected_benchmark_tasks.json` + scan of `CSB_RUNS_DIR`.

**Output**: Gap report JSON identifying missing `(task_id, config)` pairs.

**Contract**:
- Scanner MUST use `CSB_RUNS_DIR` (absolute) as the scan root — never relative `runs/`.
- Scanner handles all three result directory layouts described in
  `docs/reference/RESULT_DIRECTORY_SPEC.md`.
- A result counts as "present" only when `validation_result.json` has `status=scored`.
  A `result.json` without `validation_result.json`, or with status `invalid_output` or
  `verifier_error`, does NOT close the gap.
- Gap report schema:

```json
{
  "generated_at": "2026-03-19T14:00:00Z",
  "csb_runs_dir": "/abs/path",
  "gaps": [
    {
      "task_id": "k8s-taint-feat-001",
      "config": "baseline-local-direct",
      "benchmark": "csb_sdlc_feature",
      "reason": "missing | invalid_output | verifier_error | quarantined"
    }
  ],
  "summary": {
    "total_expected": 370,
    "scored": 310,
    "gap_count": 60
  }
}
```

### Stage 3: Execution

**Input**: Gap report or full task list + harness flags.

**Output**: Task result directories under `CSB_RUNS_DIR` (§1.1).

**Contract**:
- Each task is launched as an independent Harbor run.
- Account assignment uses round-robin across `~/.claude-homes/account*/` directories.
- Paired mode (baseline + MCP simultaneously per task) is the default to equalize
  wall-clock timing.
- Daytona is the default execution environment (`HARBOR_ENV=daytona`). Local Docker
  only for tasks incompatible with Daytona (sweap-images tasks).
- `JOBS_BASE` uses absolute `CSB_RUNS_DIR` — never relative `runs/`.

### Stage 4: Validation

**Input**: Task result directory.

**Output**: `verifier/validation_result.json` written inside the task dir.

**Contract**:
- Written by the verifier DURING task execution (not deferred to batch end).
- ALWAYS written, even on agent crash, timeout, or missing output.
- Uses schema from §1.3.
- Validation is per-task, not per-batch. `validate_and_report()` may be called at
  batch end as a summary, but each task's `validation_result.json` is the source of
  truth — not the batch-level validation log.

### Stage 5: Coverage Report and Promotion

**Input**: Scan of `CSB_RUNS_DIR` for a specific run or category.

**Output**: Coverage summary + optional promotion to `runs/official/`.

**Coverage report schema** (per config):

```json
{
  "run_id": "openhands_sonnet46_20260319_140523",
  "config": "baseline-local-direct",
  "total_tasks": 185,
  "scored": 170,
  "invalid_output": 8,
  "verifier_error": 3,
  "quarantined": 4,
  "coverage_pct": 91.9
}
```

**Promotion quality gates** (configurable, defaults below):

| Gate | Default | Meaning |
|------|---------|---------|
| `min_coverage_pct` | 85% | Fraction of tasks with `status=scored`. |
| `max_error_rate_pct` | 5% | Fraction with `status=verifier_error` or `quarantined`. |

Promotion MUST fail explicitly (non-zero exit, logged reason) if gates are not met.
Silent promotion of incomplete runs is non-compliant.

---

## 4. Invariants

These are absolute constraints. No harness or tool may violate them.

| # | Invariant | Rationale |
|---|-----------|-----------|
| I-1 | Results ALWAYS at absolute `CSB_RUNS_DIR` path | Worktree compatibility; gap detection coverage |
| I-2 | `validation_result.json` ALWAYS written per task | No silent drops; crash recovery |
| I-3 | Failures ALWAYS logged with reason | Debugging; quarantine accounting |
| I-4 | Gap detection covers ALL result locations | No orphaned results; accurate coverage |
| I-5 | One canonical harness (no duplicates) | Single source of truth; no config drift |
| I-6 | `CSB_RUNS_DIR` unset → harness exits 1 | Prevent relative-path silently wrong runs |
| I-7 | Circuit breaker fires at `MAX_ATTEMPTS=3` | Prevent infinite retry on bad tasks |
| I-8 | Validation runs before batch end | Per-task accountability; crash safety |

---

## 5. Account / Parallelism Contract

### 5.1 Account Auto-Detection

The harness detects accounts by globbing `~/.claude-homes/account*/`:

```bash
CLAUDE_HOMES=( ~/.claude-homes/account*/ )
```

Each account directory must contain `.claude/.credentials.json` with a valid OAuth
token. Accounts with expired tokens (< `ACCOUNT_MIN_TOKEN_MINUTES=90` minutes remaining)
are excluded from the rotation pool at preflight time.

### 5.2 Default Session Slots

| Environment | Default Slots | Cap | Formula |
|-------------|---------------|-----|---------|
| Daytona | `min(account_count × 62, 124)` | 124 | Tier 3: 125 concurrent sandboxes, 1 headroom |
| Local Docker | `account_count × SESSIONS_PER_ACCOUNT` | — | Default `SESSIONS_PER_ACCOUNT=6` |
| OpenHands (Daytona) | `4 per account` | configurable | Controlled via `--parallel` or env var |

`--parallel` overrides auto-detection. Do NOT hardcode `--parallel` in wrapper scripts
unless forced by a specific capacity constraint.

### 5.3 Rate-Limit Retry

When a task fails with a rate-limit error:

1. Increment the task's attempt counter in run state.
2. Rotate to the next account in the round-robin pool.
3. Apply exponential backoff: `base=30s, multiplier=2, max=5m`.
4. Retry up to `MAX_ATTEMPTS=3`; then quarantine (§2.4).

### 5.4 Cost Guard Preflight

For Daytona runs, the cost guard (`scripts/infra/daytona_cost_guard.py`) MUST run before
any task is launched. It validates:

- Estimated sandbox-hours against `configs/daytona_cost_policy.json`.
- Parallelism does not exceed tier capacity.
- Selection file resolves to a non-empty task list.

The guard sets `DAYTONA_COST_GUARD_PREFLIGHT_DONE=1`. Harnesses MUST check this flag
(via `harbor_run_guarded`) before calling `harbor run --env daytona`.

---

## 6. Gap Detection Spec (Detail)

Gap detection is a first-class pipeline stage, not a post-hoc audit. It runs:
1. Before a batch (to compute which tasks need running).
2. After a batch (to verify coverage).
3. On demand (to identify remaining work across all categories).

### 6.1 Scan Root

```python
scan_root = Path(os.environ["CSB_RUNS_DIR"])
```

If `CSB_RUNS_DIR` is unset, the scanner exits with an error. It does not fall back to
`runs/`.

### 6.2 Completion Check

A `(task_id, config)` pair is **complete** when:

```python
def is_complete(task_dir: Path) -> bool:
    vr = task_dir / "verifier" / "validation_result.json"
    if not vr.exists():
        return False
    data = json.loads(vr.read_text())
    return data.get("status") == "scored"
```

### 6.3 Layout Handling

The scanner handles all three result directory layouts from
`docs/reference/RESULT_DIRECTORY_SPEC.md`:

- **Layout 1** (old promoted): 4-level depth, `baseline`/`mcp` config dirs.
- **Layout 2** (Harbor nested): `baseline-local-direct`/`mcp-remote-direct` config dirs.
- **Layout 3** (artifact): `baseline-local-artifact`/`mcp-remote-artifact` config dirs.

Config dir canonicalization:

```python
BL_NAMES = {"baseline", "baseline-local-direct", "baseline-local-artifact"}
MCP_NAMES = {"mcp", "mcp-remote-direct", "mcp-remote-artifact"}
```

---

## 7. Reference: Existing Code

| Concept | Current Location | Status |
|---------|-----------------|--------|
| Harness (OH) | `configs/harnesses/openhands_2config.sh` | Needs: skip-completed, per-task validation, circuit breaker, absolute CSB_RUNS_DIR (co-7xy, co-zyy, co-2i0) |
| Harness (Claude) | `configs/harnesses/run_selected_tasks.sh` | Has skip-completed; relative `runs/` path bug |
| Shared helpers | `configs/_common.sh` | `validate_and_report()`, `run_tasks_parallel()`, account rotation |
| 27 duplicates | `configs/harnesses/*_2config.sh` | Target for consolidation (co-85k) |
| Gap detection | `configs/harnesses/fill_openhands_gaps.sh` | OH-specific; extend to general gap scanner |
| Coverage analysis | `scripts/analysis/analyze_run_coverage.py` | Scans `runs/official/`; needs CSB_RUNS_DIR awareness |
| Promotion | `scripts/running/promote_run.py` | Silent drop bug (co-pfj) |
| Metrics extraction | `scripts/evaluation/extract_task_metrics.py` | Called after each run |
| Validation schema | `docs/reference/VALIDATION_RESULT_SCHEMA.md` | Canonical; this spec references it |
| Result dir layout | `docs/reference/RESULT_DIRECTORY_SPEC.md` | Canonical; gap detection must handle all 3 layouts |

---

## 8. Acceptance Criteria (co-7dk Subtasks)

| Bead | Acceptance Criteria |
|------|---------------------|
| co-zyy | `openhands_2config.sh:run_mode()` calls `validate_and_report()` per task, not just at batch end. |
| co-7xy | `openhands_2config.sh` supports `--skip-completed` using `validation_result.json status=scored`. |
| co-2i0 | Circuit breaker at `MAX_ATTEMPTS=3`; persistent `run_state.json` updated atomically. |
| co-85k | Single `run.sh` with `--agent` + `--config` flags replaces all 27 `*_2config.sh` files. |
| co-pfj | `promote_run.py` and `coverage_report.py` log all dropped results with task ID and reason. |
| co-0it | `CSB_RUNS_DIR` is absolute; harnesses exit 1 if unset. ✓ (landed) |
