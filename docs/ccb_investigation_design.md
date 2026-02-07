# ccb_investigation Benchmark Suite — Design Document

## 1. Purpose & Motivation

The `ccb_investigation` benchmark suite tests an agent's ability to **find, trace, and explain** code-level phenomena in large codebases — without writing any code. These tasks model the detective work that senior engineers do daily: regression hunting, impact analysis, cross-service debugging, and migration auditing.

**Why this suite matters for MCP value demonstration:**
- Investigation tasks are the hardest to solve without code search tools
- Local `grep`/`find` fail at scale (100K+ LOC) and across repos
- Sourcegraph's `find_references`, `go_to_definition`, `commit_search`, `diff_search`, and Deep Search provide massive advantage
- The output is a structured report (not code), so verification uses checklist scoring against ground-truth findings

**Key differentiator from existing benchmarks:**
- Unlike LoCoBench bug_investigation (synthetic repos), these use **real open-source repos with real regressions**
- Unlike CrossRepo (code changes), these produce **analysis reports** — no `patch.diff`
- Unlike LargeRepo (feature implementation), the agent must **discover and explain**, not build

## 2. Suite Architecture

### Output Format

Every task requires the agent to produce `/logs/agent/investigation.md` containing:

```markdown
# Investigation Report

## Summary
<1-2 sentence finding>

## Root Cause
<Specific file, function, and mechanism>

## Evidence
<Code references with file paths and line numbers>

## Affected Components
<List of packages/modules impacted>

## Recommendation
<Fix strategy or migration path>
```

### Verification Approach: Weighted Checklist

Verification uses **deterministic pattern matching** against a `ground_truth.json` that specifies:
1. **Required findings** (weighted 0.40) — specific strings/patterns that must appear in the report
2. **File references** (weighted 0.30) — specific file paths the agent must identify
3. **Causal chain** (weighted 0.20) — ordered sequence of components in the explanation
4. **Negative checks** (weighted 0.10) — patterns that should NOT appear (wrong conclusions)

This avoids the embedding-model dependency of LoCoBench's `semantic_similarity` and gives deterministic, reproducible scores.

### Reward Type

`checklist` — consistent with K8s Docs and LargeRepo tasks.

## 3. Repo Selection

All repos are **public GitHub repos already indexed in Sourcegraph**. No sg-benchmarks mirrors needed (repos are large enough that HEAD approximates the target commit for investigation purposes, and we pin specific commits in the Dockerfile).

| Repo | SG Name | Language | Size | Why |
|------|---------|----------|------|-----|
| grafana/grafana | `github.com/grafana/grafana` | Go + TS | 2M+ LOC | Full-stack, plugin architecture, rich regression history |
| kubernetes/kubernetes | `github.com/kubernetes/kubernetes` | Go | 3M+ LOC | Multi-component, API versioning, scheduler/controller interactions |
| django/django | `github.com/django/django` | Python | 300K+ LOC | Framework with migration system, middleware chain, ORM layers |
| prometheus/prometheus | `github.com/prometheus/prometheus` | Go | 500K+ LOC | Metrics pipeline, TSDB, query engine, multi-component |

## 4. Task Specifications

### Task 1: `inv-regression-001` — Regression Hunt (Grafana)

**Title:** Dashboard Migration v38 Table Panel Regression

**Repo:** `grafana/grafana` at commit `26d36ec` (parent commit = the broken state)

**Scenario:** After upgrading Grafana from v10.3 to v10.4, some dashboards with table panels fail to render. The table panel's field override configuration is silently dropped during import. Users see tables with missing column formatting. The error only occurs on dashboards that were saved without explicit `fieldConfig.defaults.custom` objects — dashboards with explicit custom config work fine.

**Agent prompt (instruction.md):**
> You are investigating a regression in Grafana's dashboard migration system. After upgrading to a recent version, some dashboards with table panels have lost their field override configuration (column widths, text alignment, cell display modes). The bug only affects dashboards where `fieldConfig.defaults.custom` was not explicitly set.
>
> **Investigate and produce a report at `/logs/agent/investigation.md` with:**
> 1. Which migration function is responsible
> 2. The exact conditional logic that fails
> 3. Why dashboards with explicit `defaults.custom` are unaffected
> 4. Which dashboard schema version triggers the issue
> 5. The files and functions involved in the migration chain
>
> Do NOT write any code fixes. Your job is to produce a thorough investigation report.

**Ground truth findings (verified from commit `26d36ec` diff):**
- File: `apps/dashboard/pkg/migration/schemaversion/v38.go`
- Function: `processPanelsV38()`
- Root cause: The old code extracted `defaults` then `custom` with early `continue` — if `defaults["custom"]` was nil/missing, the entire panel was skipped, including the `migrateOverrides(fieldConfig)` call at the bottom
- The fix nests the defaults.custom processing inside an `if` block but calls `migrateOverrides(fieldConfig)` unconditionally outside it
- Specific broken pattern: `custom, ok := defaults["custom"].(map[string]interface{}); if !ok { continue }` — the `continue` skipped override migration
- Test file: `apps/dashboard/pkg/migration/schemaversion/v38_test.go` (added comprehensive test for missing defaults.custom edge case)

**Verification checklist:**
- Finding: mentions "v38" or "schema version 38" or "schemaVersion.*38" (0.10)
- Finding: mentions "fieldConfig.defaults.custom" or "defaults.custom" (0.10)
- Finding: mentions "continue" or early return skipping overrides (0.10)
- Finding: mentions "migrateOverrides" being skipped/bypassed (0.10)
- File ref: identifies `v38.go` or `apps/dashboard/pkg/migration/schemaversion/` (0.10)
- File ref: identifies `processPanelsV38` function (0.10)
- File ref: identifies `migrateOverrides` function (0.10)
- Causal chain: nil check on defaults.custom → continue → migrateOverrides skipped → overrides lost (0.10)
- Causal chain: explains why explicit defaults.custom works (type assertion succeeds, no continue) (0.10)
- Negative: does NOT blame rendering, frontend, or dashboard save logic (0.10)

**MCP advantage:** The migration pipeline spans multiple files across `pkg/services/` and `public/app/`. Finding which schema version handler is responsible requires searching for "v38" or "schemaVersion" across the migration chain — trivial with `keyword_search`, very slow with local grep in a 2M LOC codebase.

**Difficulty:** hard
**Time limit:** 1200 sec (20 min)
**MCP benefit score:** 0.88

---

### Task 2: `inv-impact-001` — Impact Analysis (Kubernetes)

**Title:** DRA AllocationMode API Change Impact

**Repo:** `kubernetes/kubernetes` at commit `2e534d6` (the change) + its parent

**Scenario:** The Dynamic Resource Allocation (DRA) feature is introducing a change to allow `AllocationMode: All` from multi-node resource pools. Before this change ships, the team needs an impact analysis: which components are affected, what test coverage exists, and what performance implications should be expected.

**Agent prompt (instruction.md):**
> You are performing an impact analysis for a proposed Kubernetes change. The DRA (Dynamic Resource Allocation) scheduler plugin is being modified to allow `AllocationMode: All` from multi-node resource pools (previously restricted to single-node pools only).
>
> **Produce an impact analysis report at `/logs/agent/investigation.md` covering:**
> 1. All source files that reference `AllocationMode` or the DRA allocation logic
> 2. Which controllers and schedulers are affected
> 3. What test files cover the current allocation behavior
> 4. What performance implications exist (scheduler hot paths affected)
> 5. Which downstream consumers (kubelet, device plugins) would see changed behavior
> 6. Risk assessment: what could break if this change has bugs
>
> Do NOT write any code. Produce a comprehensive impact analysis report.

**Ground truth findings (verified from commit `2e534d6` diff):**
- Primary files: `staging/src/k8s.io/dynamic-resource-allocation/structured/internal/*/pools_*.go` (3 copies: stable, incubating, experimental)
- Function: `GatherPools()` — modified to pre-collect all slices by pool across ALL nodes before filtering to target node
- New struct: `poolIdentifier{driver, pool string}` for cross-node pool grouping
- Completeness check changed: old code compared `len(pool.Slices)` vs `Slices[0].Spec.Pool.ResourceSliceCount` (only node-local slices); new code compares across all nodes
- Test file: `staging/src/k8s.io/dynamic-resource-allocation/structured/internal/allocatortesting/allocator_testing.go` (added `allocation-mode-all-with-multi-host-resource-pool` test case)
- Performance risk: `slicesByPool` map iterates ALL slices twice (grouping + completeness check) before node filtering
- The revert (`a0e500a`) says: "It caused a performance regression, a different fix is needed"

**Verification checklist:**
- Finding: identifies `dynamicresources` plugin/package (0.08)
- Finding: mentions `AllocationMode` enum/constant (0.08)
- Finding: mentions scheduler `Filter` or `Score` functions (0.08)
- Finding: mentions kubelet device manager or resource claim (0.08)
- Finding: mentions performance/latency concern (0.08)
- File ref: identifies file in `pkg/scheduler/framework/plugins/dynamicresources/` (0.10)
- File ref: identifies DRA API types in `staging/` or `api/resource/` (0.10)
- File ref: identifies at least one test file (0.08)
- File ref: identifies kubelet-side code (0.08)
- Causal chain: allocation mode change → pool scope expansion → more candidates → scheduler load (0.08)
- Causal chain: mentions risk of double allocation or race condition (0.08)
- Negative: does NOT confuse DRA with CSI storage (0.08)

**MCP advantage:** `find_references` on `AllocationMode` instantly reveals all 15+ files that reference it. Without MCP, the agent would need to grep across 3M+ LOC, wade through staging/ symlinks, and manually trace the scheduler→kubelet path. `go_to_definition` is critical for understanding the type hierarchy.

**Difficulty:** hard
**Time limit:** 1200 sec (20 min)
**MCP benefit score:** 0.92

---

### Task 3: `inv-debug-001` — Cross-Service Debug (Prometheus)

**Title:** Remote-Write Queue Resharding Failure

**Repo:** `prometheus/prometheus` at commit `ba14bc4` (the broken change, before revert `6806b68`)

**Scenario:** After a Prometheus upgrade, remote-write destinations intermittently stop receiving samples. The issue correlates with target count changes (scaling up/down scraped targets). Prometheus logs show "resharding" messages but some queues appear to stall after resharding completes.

**Agent prompt (instruction.md):**
> You are debugging a production issue with Prometheus remote-write. After upgrading Prometheus, remote-write to external TSDB backends (Cortex/Thanos) intermittently stops delivering samples. The issue correlates with target discovery changes — when targets are added or removed, some remote-write shards stall.
>
> Prometheus logs show:
> ```
> level=info msg="Resharding queues" from=4 to=6
> level=info msg="Resharding done" numShards=6
> ```
> But after resharding, metrics show some shards have `prometheus_remote_storage_samples_pending` stuck at >0 with no progress.
>
> **Investigate and produce a report at `/logs/agent/investigation.md` covering:**
> 1. How remote-write queue resharding works (which files/functions)
> 2. What changed in the resharding logic recently
> 3. The specific mechanism causing shards to stall
> 4. Why the issue is intermittent (timing/race condition)
> 5. Which metrics or logs would confirm the root cause
>
> Do NOT write any code fixes. Produce a thorough debugging report.

**Ground truth findings (verified from revert commit `6806b68` diff):**
- Primary file: `storage/remote/queue_manager.go`
- Secondary file: `storage/remote/write.go`
- Function: `calculateDesiredShards()` in queue_manager.go
- Broken commits: `ba14bc4` (deprecated per-QM counters) and `184c7eb` (moved dataIn/highestTimestamp computation)
- Root cause: `dataIn` rate tracking was removed from per-QueueManager and moved to shared WriteStorage level. The `calculateDesiredShards()` function lost its call to `t.dataIn.tick()`. Without this, the EWMA rate decays to 0, causing the shard calculation formula `timePerSample * (dataInRate + backlogCatchup)` to produce 0 desired shards
- Additionally: dropped samples (series not found after relabeling) were counted as incoming but never outgoing, inflating `dataPendingRate = dataInRate - dataOutRate` and causing over-scaling
- The fix (revert) restores: `samplesIn *ewmaRate` parameter to `NewQueueManager()`, `dataDropped *ewmaRate` field, `highestRecvTimestamp *maxTimestamp`, and a dedicated `run()` goroutine in WriteStorage that ticks `samplesIn` every `shardUpdateDuration`
- Intermittent because: only manifests when target count changes trigger resharding, and timing of dropped samples vs outgoing batches determines whether the formula diverges
- Test file: `storage/remote/queue_manager_test.go` (TestCalculateDesiredShardsDetail updated with `dataDropped` field)

**Verification checklist:**
- Finding: identifies `queue_manager.go` (0.10)
- Finding: mentions `calculateDesiredShards` function (0.10)
- Finding: mentions `dataIn` or `samplesIn` rate tracking (0.10)
- Finding: mentions EWMA rate or `ewmaRate` (0.05)
- Finding: mentions dropped samples not being accounted for (0.10)
- File ref: `storage/remote/queue_manager.go` (0.10)
- File ref: `storage/remote/write.go` (0.10)
- File ref: identifies test file `queue_manager_test.go` (0.05)
- Causal chain: dataIn tracking moved/broken → calculateDesiredShards gets wrong rate → shard count diverges → queue stalls (0.10)
- Causal chain: dropped samples inflate dataPendingRate → over-scaling (0.10)
- Negative: does NOT blame network connectivity, Cortex/Thanos receiver, or scrape config (0.10)

**MCP advantage:** `commit_search` and `diff_search` can find recent changes to `queue_manager.go` and identify the metric-related commits. `find_references` on the resharding function reveals the full call chain. Deep Search can answer "how does remote-write resharding work in Prometheus?" directly. Without MCP, the agent must manually read through the 500K LOC codebase to understand the remote-write pipeline.

**Difficulty:** hard
**Time limit:** 1200 sec (20 min)
**MCP benefit score:** 0.90

---

### Task 4: `inv-migration-001` — Migration Audit (Django)

**Title:** ADMINS/MANAGERS Settings Format Migration Audit

**Repo:** `django/django` at commit just before `e295033` (the migration hasn't happened yet)

**Scenario:** Django is migrating the `ADMINS` and `MANAGERS` settings from tuples of `(name, email)` to plain email strings. Before executing this migration, the team needs a comprehensive audit of all code that reads, validates, or processes these settings to ensure nothing breaks.

**Agent prompt (instruction.md):**
> Django is changing the `ADMINS` and `MANAGERS` settings from their current format of `[(name, email), ...]` tuples to simple `[email, ...]` string lists. This is tracked in ticket #36138.
>
> **Produce a migration audit report at `/logs/agent/investigation.md` covering:**
> 1. Every file that reads `settings.ADMINS` or `settings.MANAGERS`
> 2. Every file that validates or type-checks the settings format
> 3. Every file that unpacks the tuple format (e.g., `for name, email in settings.ADMINS`)
> 4. All documentation references that show the old tuple format
> 5. Test files that use the old format in fixtures or assertions
> 6. Third-party compatibility concerns (what breaks for users with old-format settings)
> 7. A migration checklist: each file that needs changes, what change is needed
>
> Do NOT write any code. Produce a comprehensive migration audit.

**Ground truth findings (verified from commit `e295033` diff — 10 files changed):**
- Primary file: `django/core/mail/__init__.py` — function `_send_server_message()` is the core consumer
- Old pattern: `for name, email in recipients` tuple unpacking → `to=[a[1] for a in recipients]`
- New pattern: `to=recipients` (direct string list) with deprecation warning for old tuple format
- Validation change: `ValueError` → `ImproperlyConfigured` exception type
- New validation: `isinstance(address, (str, Promise))` check for each item
- Deprecation: `RemovedInDjango70Warning` issued when old tuple format detected, with auto-extraction `recipients = [a[1] for a in recipients]`
- Documentation files changed: `docs/ref/settings.txt`, `docs/releases/6.0.txt`, `docs/internals/deprecation.txt`, `docs/internals/contributing/writing-documentation.txt`
- Test files changed: `tests/mail/tests.py` (main mail tests), `tests/logging_tests/tests.py` (AdminEmailHandler), `tests/mail/test_sendtestemail.py`, `tests/middleware/tests.py` (BrokenLinkEmailsMiddleware), `tests/view_tests/tests/test_debug.py` (error reporting)
- Follow-up commit: `90fc762` — cleaned up duplicate code in mail_admins()/mail_managers()
- Another follow-up: `a8536e3` — corrected ADMINS format in `django/conf/global_settings.py` comment

**Verification checklist:**
- Finding: identifies `_send_server_message` function (0.10)
- Finding: identifies `mail_admins` or `mail_managers` function (0.10)
- Finding: mentions tuple unpacking `(name, email)` or `a[1]` as the pattern to change (0.10)
- Finding: mentions `ImproperlyConfigured` or error type change (0.05)
- File ref: `django/core/mail/__init__.py` (0.10)
- File ref: `docs/ref/settings.txt` (0.05)
- File ref: identifies `tests/mail/tests.py` (0.10)
- File ref: identifies `tests/logging_tests/tests.py` (0.05)
- File ref: identifies at least one more test file (middleware or view_tests) (0.05)
- Causal chain: settings format change → tuple unpacking in `_send_server_message` breaks → `to=` argument fails → error notifications lost (0.10)
- Checklist: provides at least 4 specific files with specific needed changes (0.10)
- Negative: does NOT only mention settings.py (must find framework-internal consumers) (0.10)

**MCP advantage:** `keyword_search` for `settings.ADMINS` instantly finds all 8-12 references across the Django codebase. `find_references` traces from the settings constant to every consumer. Deep Search can explain "how does Django's admin email notification system work?" Without MCP, finding all tuple-unpacking sites across Django's modular structure requires careful manual search through `utils/`, `core/mail/`, `core/checks/`, and test directories.

**Difficulty:** medium
**Time limit:** 900 sec (15 min)
**MCP benefit score:** 0.85

## 5. File Structure

```
benchmarks/ccb_investigation/
├── CLAUDE.md                          # Suite-level MCP instructions
├── inv-regression-001/
│   ├── task.toml
│   ├── instruction.md
│   ├── environment/
│   │   └── Dockerfile
│   └── tests/
│       ├── test.sh
│       └── ground_truth.json
├── inv-impact-001/
│   ├── task.toml
│   ├── instruction.md
│   ├── environment/
│   │   └── Dockerfile
│   └── tests/
│       ├── test.sh
│       └── ground_truth.json
├── inv-debug-001/
│   ├── task.toml
│   ├── instruction.md
│   ├── environment/
│   │   └── Dockerfile
│   └── tests/
│       ├── test.sh
│       └── ground_truth.json
└── inv-migration-001/
    ├── task.toml
    ├── instruction.md
    ├── environment/
    │   └── Dockerfile
    └── tests/
        ├── test.sh
        └── ground_truth.json
```

## 6. Shared Verifier (test.sh)

All tasks use the same verification pattern. The `test.sh`:

1. Checks for `/logs/agent/investigation.md`
2. Loads `/tests/ground_truth.json` with expected findings
3. Scores using weighted checklist:
   - Required findings (grep patterns in report) — 0.40
   - File references (file paths mentioned) — 0.30
   - Causal chain (ordered pattern sequence) — 0.20
   - Negative checks (wrong conclusions absent) — 0.10
4. Writes score to `/logs/verifier/reward.txt`

## 7. Docker Environment

Each task Dockerfile:
1. Clones the repo at the specific commit (`git clone --depth 1 --branch <tag>` or `git clone` + `git checkout <commit>`)
2. Sets up workspace at `/workspace`
3. Installs minimal dependencies (Go toolchain for Go repos, Python for Django)
4. Does NOT install Sourcegraph — MCP is configured via `task.toml` setup_scripts

Container resources: 2 CPUs, 8GB RAM, 20GB storage (consistent with LargeRepo tasks).

## 8. CLAUDE.md (Suite-Level)

```markdown
# Investigation Benchmark Suite

This suite tests your ability to investigate code-level phenomena in large codebases.

## Search Strategy

**This repository is large.** You MUST use Sourcegraph MCP tools for investigation:

- Use `keyword_search` to find all references to specific symbols, configs, or patterns
- Use `find_references` to trace symbol usage across the codebase
- Use `go_to_definition` to understand type hierarchies and function contracts
- Use `commit_search` to find recent changes that may have caused regressions
- Use `diff_search` to find what code was added/removed in recent changes
- Use `deepsearch` for high-level "how does X work?" questions

## Output Requirements

Write your investigation report to `/logs/agent/investigation.md`.

Your report MUST include:
1. **Summary** — 1-2 sentence finding
2. **Root Cause** — Specific file, function, and mechanism
3. **Evidence** — Code references with file paths and line numbers
4. **Affected Components** — List of packages/modules impacted
5. **Recommendation** — Fix strategy or migration path

Do NOT write code fixes. Your job is investigation and analysis only.
```

## 9. Registration

Add to `configs/selected_benchmark_tasks.json`:

```json
{
  "task_id": "inv-regression-001",
  "benchmark": "ccb_investigation",
  "sdlc_phase": "Debugging (regression hunt)",
  "language": "go",
  "difficulty": "hard",
  "category": "regression_hunt",
  "repo": "grafana/grafana",
  "mcp_benefit_score": 0.88,
  "mcp_breakdown": {
    "context_complexity": 0.90,
    "cross_file_deps": 0.85,
    "semantic_search_potential": 0.90,
    "task_category_weight": 0.85
  },
  "task_dir": "ccb_investigation/inv-regression-001"
},
{
  "task_id": "inv-impact-001",
  "benchmark": "ccb_investigation",
  "sdlc_phase": "Planning (impact analysis)",
  "language": "go",
  "difficulty": "hard",
  "category": "impact_analysis",
  "repo": "kubernetes/kubernetes",
  "mcp_benefit_score": 0.92,
  "mcp_breakdown": {
    "context_complexity": 0.95,
    "cross_file_deps": 0.90,
    "semantic_search_potential": 0.90,
    "task_category_weight": 0.90
  },
  "task_dir": "ccb_investigation/inv-impact-001"
},
{
  "task_id": "inv-debug-001",
  "benchmark": "ccb_investigation",
  "sdlc_phase": "Debugging (cross-service)",
  "language": "go",
  "difficulty": "hard",
  "category": "cross_service_debug",
  "repo": "prometheus/prometheus",
  "mcp_benefit_score": 0.90,
  "mcp_breakdown": {
    "context_complexity": 0.90,
    "cross_file_deps": 0.90,
    "semantic_search_potential": 0.90,
    "task_category_weight": 0.88
  },
  "task_dir": "ccb_investigation/inv-debug-001"
},
{
  "task_id": "inv-migration-001",
  "benchmark": "ccb_investigation",
  "sdlc_phase": "Maintenance (migration audit)",
  "language": "python",
  "difficulty": "medium",
  "category": "migration_audit",
  "repo": "django/django",
  "mcp_benefit_score": 0.85,
  "mcp_breakdown": {
    "context_complexity": 0.80,
    "cross_file_deps": 0.85,
    "semantic_search_potential": 0.90,
    "task_category_weight": 0.82
  },
  "task_dir": "ccb_investigation/inv-migration-001"
}
```

## 10. Config Script

Create `configs/investigation_3config.sh` following the pattern of `pytorch_3config.sh`:
- TASKS_DIR pointing to `benchmarks/ccb_investigation`
- 3 configs: baseline, sourcegraph_base, sourcegraph_full
- Uses `--path` mode (local task dirs, not harbor registry)
- Parallel execution support

## 11. instance_to_mirror.json Entry

```json
"investigation": {
  "_note": "Investigation tasks use public GitHub repos directly (already indexed in SG). No sg-benchmarks mirrors needed.",
  "tasks": {
    "inv-regression-001": {
      "repo": "grafana/grafana",
      "mirror_name": null,
      "note": "Public GitHub repo, indexed at HEAD. Task pins specific commit in Dockerfile."
    },
    "inv-impact-001": {
      "repo": "kubernetes/kubernetes",
      "mirror_name": null,
      "note": "Public GitHub repo, indexed at HEAD."
    },
    "inv-debug-001": {
      "repo": "prometheus/prometheus",
      "mirror_name": null,
      "note": "Public GitHub repo, indexed at HEAD."
    },
    "inv-migration-001": {
      "repo": "django/django",
      "mirror_name": null,
      "note": "Public GitHub repo, indexed at HEAD."
    }
  }
}
```

**Important SG indexing note:** Public GitHub repos are indexed at HEAD, not at the specific commit the agent works with. For investigation tasks this is acceptable because:
1. The codebase structure and file organization rarely changes dramatically
2. The agent needs to find patterns and trace call chains, not match exact line numbers
3. If precise commit indexing is needed, we can create sg-benchmarks mirrors later

## 12. Expected Results & MCP Value Hypothesis

| Task | Baseline (no MCP) | SG_base | SG_full |
|------|-------------------|---------|---------|
| inv-regression-001 | 0.2-0.4 | 0.5-0.7 | 0.7-0.9 |
| inv-impact-001 | 0.1-0.3 | 0.4-0.6 | 0.6-0.8 |
| inv-debug-001 | 0.2-0.4 | 0.5-0.7 | 0.7-0.9 |
| inv-migration-001 | 0.3-0.5 | 0.6-0.8 | 0.7-0.9 |

**Rationale:**
- Baseline agents can read local files but struggle to efficiently search 300K-3M LOC codebases
- SG_base (keyword search) dramatically improves finding specific references
- SG_full (+ Deep Search) helps understand architectural context and recent changes
- Investigation tasks should show the **largest MCP delta** of any benchmark because the entire task IS search

## 13. Risk Factors

1. **Repo size vs. container disk:** Grafana and Kubernetes are multi-GB. Shallow clones (`--depth 1`) needed.
2. **SG HEAD vs. task commit:** Public repos index HEAD, but agent works at a historical commit. File paths/names may differ. Mitigation: pick commits <6 months old.
3. **Deterministic verification:** Checklist patterns must be specific enough to avoid false positives but flexible enough to accept valid alternative phrasings. Test with 2-3 manual runs.
4. **Time limits:** Investigation requires reading + reasoning, not just coding. 20 minutes may be tight for the K8s impact analysis. Monitor and adjust.

## 14. Implementation Order

1. **Validate repo commits** — Confirm each target commit exists and the scenario is reproducible
2. **Write ground_truth.json** — Define exact checklist patterns for each task
3. **Write shared test.sh** — Implement the checklist verifier
4. **Write Dockerfiles** — Clone repos at correct commits
5. **Write instruction.md** — Agent prompts with scenario context
6. **Write task.toml** — Harbor configuration
7. **Write CLAUDE.md** — Suite-level and per-task MCP instructions
8. **Write investigation_3config.sh** — Run configuration
9. **Register in selected_benchmark_tasks.json and instance_to_mirror.json**
10. **Dry run** — Test one task manually with `harbor run --path`
