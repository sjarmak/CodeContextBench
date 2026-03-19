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

**Two concerns are kept strictly separate:**

| Concern | WHAT (Run Configuration) | HOW (Runtime Settings) |
|---------|--------------------------|------------------------|
| Defined by | Agent-authored YAML/JSON file | Harness auto-detection |
| Contains | Agent, model, augmentation configs, preamble, vars | Parallelism, account spread, capacity |
| Validated | At harness startup against schema | Computed from environment at launch time |
| Baked in? | Yes — stable, version-controlled | No — never hardcoded |

Agents invoke the pipeline via `csb run <config.yaml>`. They do not specify parallelism,
account counts, or scheduling — the harness computes those from available capacity.

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
| `CATEGORY` | `staging`, `official` | From run config `category` field. |
| `AGENT` | `openhands`, `claude` | Agent plugin short name. |
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

### 1.4 Result Deduplication Policy

When the same `(task_id, config)` pair appears in multiple result directories (e.g. a
partial run followed by a gap-fill run), the **latest scored result wins**:

```python
def resolve_result(candidates: list[Path]) -> Path:
    """Return the most recently scored result directory."""
    scored = [
        d for d in candidates
        if is_complete(d / "verifier" / "validation_result.json")
    ]
    if not scored:
        # Fall back to most recent non-scored dir for error inspection
        return max(candidates, key=lambda d: d.stat().st_mtime)
    return max(scored, key=lambda d: d.stat().st_mtime)
```

**Rules:**
- A `scored` result always beats a non-scored result regardless of timestamp.
- Among multiple `scored` results, the most recently written wins.
- Gap detection and coverage tools apply this policy when they encounter duplicates.
- Harnesses do NOT delete older result directories — they are kept for debugging.

---

## 2. Run Configuration Schema

Run configurations describe **what to run** (agent, model, augmentation configs, task
selection, preamble). They do NOT specify parallelism, account counts, or scheduling —
those are runtime concerns resolved at launch (§5).

### 2.1 Schema (`run_config.v1`)

```yaml
# run_config.v1 — version-controlled, agent-authored
schema_version: run_config.v1
agent: openhands              # Agent plugin name (resolves to plugin profile, §3)
model: claude-sonnet-4-6      # Model identifier passed to agent
configs:                      # One or more augmentation configs to run
  - baseline-local-direct
  - mcp-remote-direct
subset: configs/selected_benchmark_tasks.json  # Task selection file
category: staging             # Result path label (staging | official)
schedule: independent         # independent (default) | paired (see §4.3 Stage 3)
skip_completed: true          # Skip tasks with status=scored
preamble: null                # Optional: path to additional system prompt file
vars: {}                      # Agent-plugin-specific key/value overrides
```

**`configs` field** uses canonical config names:

| Config | `BASELINE_MCP_TYPE` | Dockerfile used |
|--------|---------------------|-----------------|
| `baseline-local-direct` | `none` | `environment/Dockerfile` |
| `mcp-remote-direct` | `sourcegraph_full` | `environment/Dockerfile.sg_only` |
| `baseline-local-artifact` | `none` | `environment/Dockerfile.artifact_baseline` |
| `mcp-remote-artifact` | `sourcegraph_full` | `environment/Dockerfile.artifact_only` |

Config names are stable identifiers used in result directory paths and
`validation_result.json`. Do not invent new names without updating `configs/_common.sh`
and `docs/reference/CONFIGS.md`.

### 2.2 Validation

The harness validates the run config at startup (before any task is launched):

1. `schema_version` is `run_config.v1`.
2. `agent` resolves to a known plugin (§3).
3. All entries in `configs` are known canonical names.
4. `subset` file exists and resolves to a non-empty task list.
5. `CSB_RUNS_DIR` env var is set and absolute (exit 1 if not).

Validation failure is fatal and reported with the specific field and reason.

### 2.3 Agent-Invocation Example

```bash
# Agents create a config file and invoke csb run — they do NOT specify parallelism
cat > /tmp/my_run.yaml <<'EOF'
schema_version: run_config.v1
agent: openhands
model: claude-sonnet-4-6
configs:
  - baseline-local-direct
  - mcp-remote-direct
category: staging
EOF

csb run /tmp/my_run.yaml          # harness validates, computes runtime, executes
csb run /tmp/my_run.yaml --dry-run  # print plan without executing
csb coverage --category staging   # gap report after run
```

---

## 3. Agent Plugin Interface

The `--agent` field in a run config resolves to an **agent plugin profile**. Plugins are
the only place where agent-specific configuration lives (Docker image, launcher command,
credential path, environment wiring). The harness core is agent-agnostic.

### 3.1 Plugin Contract

Each agent plugin MUST provide:

| Field | Type | Example | Meaning |
|-------|------|---------|---------|
| `name` | string | `openhands` | Short identifier used in run configs and result paths. |
| `launcher` | string | `harbor run --agent openhands` | Command the harness invokes per task. |
| `dockerfile_variant` | map | `{baseline: "Dockerfile", mcp: "Dockerfile.sg_only"}` | Which Dockerfile per config family. |
| `credential_path` | string | `~/.claude-homes/account{N}` | Account home dir pattern. |
| `default_timeout_s` | int | `600` | Per-task timeout passed to Harbor. |
| `default_sessions_per_account` | int | `4` | Default parallelism per account (runtime hint; §5.2). |
| `env_wiring` | map | `{OPENHANDS_MODEL: "{model}"}` | Env vars set from run config fields. |

The harness provides: result path construction, run state tracking, circuit breaker,
`CSB_RUNS_DIR` enforcement, skip-completed logic, account rotation, cost guard.

### 3.2 Built-In Plugins

| Plugin | Launcher | Notes |
|--------|----------|-------|
| `openhands` | `harbor run --agent openhands` | Docker-based; OH-specific env wiring. |
| `claude` | `harbor run --agent claude` | Claude Code CLI; MCP config via `.mcp.json`. |
| `copilot` | `harbor run --agent copilot` | GitHub Copilot CLI integration. |
| `cursor` | `harbor run --agent cursor` | Cursor IDE headless mode. |

Custom agents implement the plugin contract and register under `configs/agent_plugins/`.

### 3.3 Agent-Specific Config Stays in the Plugin

Examples of what lives in the plugin profile (NOT in harness core or run config):

- OpenHands: Docker sandbox params, `OPENHANDS_MODEL`, `sandbox_plugins=[]`
- Claude: `.mcp.json` placement, `SOURCEGRAPH_URL`, `NODE_TLS_REJECT_UNAUTHORIZED`
- Copilot/Cursor: CLI invocation flags, auth token paths

Run configs only specify `agent: <name>` — the harness resolves the rest.

---

## 4. Harness Interface

### 4.1 `csb` CLI

The agent-facing interface is the `csb` CLI tool (to be created in co-85k):

```
csb run <config.yaml> [--dry-run]      # Validate run config and execute
csb coverage [--category CATEGORY]    # Gap report (JSON to stdout)
csb status <run_id>                   # Run state JSON
csb promote <run_id>                  # Promote run to official (with quality gates)
```

Agents interact with the pipeline through this CLI, not by invoking harness scripts
directly. The CLI enforces all invariants (§6) as code-level guarantees.

### 4.2 Required Environment Variables

| Variable | Required | Default | Meaning |
|----------|----------|---------|---------|
| `CSB_RUNS_DIR` | **MANDATORY** | — | Absolute path for all results. `csb run` exits 1 if unset. |
| `CSB_SKIP_CONFIRM` | optional | `0` | Set to `1` to suppress the interactive launch gate. |

### 4.3 Required Runtime Behaviors

#### Skip-Completed

When `skip_completed: true` in the run config, a task+config pair is considered complete
if and only if:

```
${CSB_RUNS_DIR}/.../baseline-local-direct/.../task-id__*/verifier/validation_result.json
```
exists and contains `"status": "scored"`. Existence of `result.json` alone is not
sufficient — the task may have run but failed validation.

#### Circuit Breaker

Each task has a **per-config attempt counter** persisted in the run state file (§4.4).
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

### 4.4 Persistent Run State File

The harness MUST write a JSON state file at:

```
${CSB_RUNS_DIR}/${CATEGORY}/${AGENT}_${MODEL_SHORT}_${TIMESTAMP}/run_state.json
```

Schema:

```json
{
  "schema_version": "run_state.v1",
  "run_id": "openhands_sonnet46_20260319_140523",
  "run_config_path": "/abs/path/to/run_config.yaml",
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

### 4.5 Single Parameterized Harness

The 27 `*_2config.sh` files (co-85k) MUST be replaced by `csb run`. The goal is:

```bash
# Instead of:
./configs/harnesses/openhands_2config.sh
./configs/harnesses/feature_2config.sh
# ...25 more

# One invocation:
csb run configs/runs/openhands_staging.yaml
csb run configs/runs/claude_mcp_comparison.yaml
```

Shared logic currently in `configs/_common.sh` (account rotation, token refresh,
cost guard, confirm gate, trajectory check) is preserved as library code used by
the harness core.

---

## 5. Pipeline Stages

### Stage 1: Selection

**Input**: Run config `subset` field (default: `configs/selected_benchmark_tasks.json`).

**Output**: Ordered list of `(task_id, task_dir, benchmark)` tuples.

**Contract**:
- Tasks with `"excluded": true` are filtered out.
- `task_dir` is relative to `benchmarks/`; harness prepends repo root to get absolute path.
- Supports both `benchmark` field (standard) and `mcp_suite` field (MCP-unique tasks).
- `--dry-run` output confirms the final task list before any execution.

### Stage 2: Gap Detection

**Input**: Run config `subset` + scan of `CSB_RUNS_DIR`.

**Output**: Gap report JSON identifying missing `(task_id, config)` pairs.

**Contract**:
- Scanner MUST use `CSB_RUNS_DIR` (absolute) as the scan root — never relative `runs/`.
- Scanner handles all three result directory layouts described in
  `docs/reference/RESULT_DIRECTORY_SPEC.md`.
- A result counts as "present" only when `validation_result.json` has `status=scored`.
  A `result.json` without `validation_result.json`, or with status `invalid_output` or
  `verifier_error`, does NOT close the gap.
- Duplicate result dirs are resolved by the deduplication policy (§1.4).
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

**Input**: Gap report or full task list from run config.

**Output**: Task result directories under `CSB_RUNS_DIR` (§1.1).

**Contract**:
- Each task is launched as an independent Harbor run.
- Account assignment uses round-robin across `~/.claude-homes/account*/` directories.
- **Default schedule is `independent`** — tasks for each config are dispatched as
  capacity allows, without coupling baseline and MCP runs per task.
- **`paired` schedule** (opt-in via `schedule: paired` in run config) runs baseline
  and MCP for the same task simultaneously to equalize wall-clock timing. Use paired
  when timing comparisons across configs are the primary goal.

  > **Tradeoff**: Paired scheduling keeps timing comparable but wastes slots when
  > configs have unequal runtimes (e.g., baseline takes 10 min, MCP takes 2 min —
  > paired holds the MCP slot idle for 8 min). Independent scheduling maximizes
  > throughput; paired maximizes timing fairness. Default is `independent`.

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

## 6. Invariants

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
| I-9 | Run config (WHAT) never contains runtime settings | Reproducibility; config portability |
| I-10 | Duplicate results resolved by latest-scored policy | Gap fill runs don't produce ambiguous state |

---

## 7. Enforcement Mechanisms

Invariants are enforced by code, not agent compliance. This section maps each invariant
to the specific mechanism that enforces it.

| Invariant | Enforced By | Mechanism |
|-----------|-------------|-----------|
| I-1 (absolute path) | `csb run` startup | Validates `CSB_RUNS_DIR` is set and absolute; exits 1 if not. All path construction goes through a single helper that prefixes `CSB_RUNS_DIR`. |
| I-2 (validation_result always written) | Harbor verifier wrapper | Verifier entrypoint is wrapped; any exception or missing output triggers synthetic `validation_result.json` with `status=verifier_error`. |
| I-3 (failures logged) | `run_state.json` writer | Harness updates `run_state.json` atomically on every task completion, including failures. Quarantine writes both state and synthetic validation result. |
| I-4 (gap detection completeness) | `csb coverage` scanner | Scanner walks all three layout variants (§7.2) and applies deduplication policy (§1.4). Agents query `csb coverage --json`; they do not implement their own scanning. |
| I-5 (one harness) | `csb run` replaces all `*_2config.sh` | co-85k removes the duplicates. CI lint gate rejects new `*_2config.sh` files. |
| I-6 (`CSB_RUNS_DIR` unset → exit 1) | `csb run` startup validation (§2.2) | First check before any work begins. |
| I-7 (circuit breaker) | Harness task dispatcher | Reads `run_state.json` attempt counter before each dispatch; quarantines at `MAX_ATTEMPTS=3`. |
| I-8 (per-task validation) | Harbor task lifecycle hook | `validate_and_report()` is called in the task completion callback, not at batch end. |
| I-9 (run config ≠ runtime) | Run config schema validation | `run_config.v1` schema rejects unknown fields. Parallelism/account fields are not in the schema and will fail validation if present. |
| I-10 (deduplication) | `csb coverage` + `csb run --skip-completed` | Both tools call the same `resolve_result()` function (§1.4). No tool makes its own deduplication decision. |

---

## 8. Runtime Settings (HOW)

Runtime settings are **not part of run configs**. They are computed by the harness at
launch time from available capacity. Agents do not specify them.

### 8.1 Account Auto-Detection

The harness detects accounts by globbing `~/.claude-homes/account*/`:

```bash
CLAUDE_HOMES=( ~/.claude-homes/account*/ )
```

Each account directory must contain `.claude/.credentials.json` with a valid OAuth
token. Accounts with expired tokens (< `ACCOUNT_MIN_TOKEN_MINUTES=90` minutes remaining)
are excluded from the rotation pool at preflight time.

### 8.2 Default Parallelism

The harness auto-computes parallelism. Agents do not set `--parallel` unless overriding
for a specific capacity constraint.

| Environment | Default Formula | Notes |
|-------------|----------------|-------|
| Daytona | `min(account_count × 62, 124)` | Tier 3: 125 concurrent sandboxes, 1 headroom |
| Local Docker | `account_count × plugin.default_sessions_per_account` | Plugin default is 4 per account |

**Agent plugin default** (`default_sessions_per_account`) lives in the plugin profile
(§3.1), not in run configs or harness flags. The harness uses the plugin's default
unless the operator overrides via `CSB_SESSIONS_PER_ACCOUNT` env var.

The previous hardcoded per-agent values (6 for Claude, 4 for OH) are replaced by
plugin profile defaults. All existing plugins default to **4 per account** until
capacity testing justifies a higher value.

### 8.3 Rate-Limit Retry

When a task fails with a rate-limit error:

1. Increment the task's attempt counter in run state.
2. Rotate to the next account in the round-robin pool.
3. Apply exponential backoff: `base=30s, multiplier=2, max=5m`.
4. Retry up to `MAX_ATTEMPTS=3`; then quarantine (§4.3).

### 8.4 Cost Guard Preflight

For Daytona runs, the cost guard (`scripts/infra/daytona_cost_guard.py`) MUST run before
any task is launched. It validates:

- Estimated sandbox-hours against `configs/daytona_cost_policy.json`.
- Parallelism does not exceed tier capacity.
- Selection file resolves to a non-empty task list.

The guard sets `DAYTONA_COST_GUARD_PREFLIGHT_DONE=1`. Harnesses MUST check this flag
(via `harbor_run_guarded`) before calling `harbor run --env daytona`.

---

## 9. Gap Detection Spec (Detail)

Gap detection is a first-class pipeline stage, not a post-hoc audit. It runs:
1. Before a batch (to compute which tasks need running).
2. After a batch (to verify coverage).
3. On demand (to identify remaining work across all categories).

Agents query gap state via `csb coverage --json`. They do NOT implement their own
`CSB_RUNS_DIR` scanners — that logic lives in the `csb` tool.

### 9.1 Scan Root

```python
scan_root = Path(os.environ["CSB_RUNS_DIR"])
```

If `CSB_RUNS_DIR` is unset, the scanner exits with an error. It does not fall back to
`runs/`.

### 9.2 Completion Check

A `(task_id, config)` pair is **complete** when:

```python
def is_complete(task_dir: Path) -> bool:
    vr = task_dir / "verifier" / "validation_result.json"
    if not vr.exists():
        return False
    data = json.loads(vr.read_text())
    return data.get("status") == "scored"
```

When multiple result directories exist for the same pair, the deduplication policy
(§1.4) is applied first.

### 9.3 Layout Handling

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

## 10. Reference: Existing Code

| Concept | Current Location | Status |
|---------|-----------------|--------|
| Harness (OH) | `configs/harnesses/openhands_2config.sh` | Needs: skip-completed, per-task validation, circuit breaker, absolute CSB_RUNS_DIR (co-7xy, co-zyy, co-2i0) |
| Harness (Claude) | `configs/harnesses/run_selected_tasks.sh` | Has skip-completed; relative `runs/` path bug + needs full spec compliance (co-cgw) |
| Shared helpers | `configs/_common.sh` | `validate_and_report()`, `run_tasks_parallel()`, account rotation |
| 27 duplicates | `configs/harnesses/*_2config.sh` | Target for consolidation into `csb run` (co-85k) |
| Gap detection | `configs/harnesses/fill_openhands_gaps.sh` | OH-specific; superseded by `csb coverage` |
| Coverage analysis | `scripts/analysis/analyze_run_coverage.py` | Scans `runs/official/`; needs CSB_RUNS_DIR awareness |
| Promotion | `scripts/running/promote_run.py` | Silent drop bug (co-pfj) |
| Metrics extraction | `scripts/evaluation/extract_task_metrics.py` | Called after each run |
| Validation schema | `docs/reference/VALIDATION_RESULT_SCHEMA.md` | Canonical; this spec references it |
| Result dir layout | `docs/reference/RESULT_DIRECTORY_SPEC.md` | Canonical; gap detection must handle all 3 layouts |

---

## 11. Acceptance Criteria (co-7dk Subtasks)

| Bead | Acceptance Criteria |
|------|---------------------|
| co-zyy | `openhands_2config.sh:run_mode()` calls `validate_and_report()` per task, not just at batch end. |
| co-7xy | `openhands_2config.sh` supports `--skip-completed` using `validation_result.json status=scored`. |
| co-2i0 | Circuit breaker at `MAX_ATTEMPTS=3`; persistent `run_state.json` updated atomically. |
| co-85k | `csb run <config.yaml>` with run config schema validation replaces all 27 `*_2config.sh` files. |
| co-pfj | `promote_run.py` and `coverage_report.py` log all dropped results with task ID and reason. |
| co-0it | `CSB_RUNS_DIR` is absolute; harnesses exit 1 if unset. ✓ (landed) |
| co-cgw | `run_selected_tasks.sh` brought into full spec compliance: absolute `CSB_RUNS_DIR`, `--agent`/`--config` flags, `--skip-completed` via `validation_result.json status=scored`. |
