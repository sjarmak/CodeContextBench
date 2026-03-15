# CodeScaleBench Agent Router

This file is the root entrypoint for AI agents working in this repository.
Keep it small. Use it to route to the right workflow and local guide, not as the
full operations manual.

## Non-Negotiables
- All work happens on `main` by default. If you use feature branches, keep them small, short-lived, and easy to fast-forward back into `main`.
- Every `harbor run` must be gated by interactive confirmation.
- Before commit/push, run `python3 scripts/repo_health.py` (or `--quick` for docs/config-only changes).
- Prefer a **remote execution environment** (e.g., Daytona) for large benchmark runs; use local Docker only when a task’s image or registry is incompatible with your cloud environment. See `docs/DAYTONA.md`.
- Set **parallelism based on your own account and model limits**. Avoid exceeding documented concurrency or rate caps for your environment or provider.
- Before launching any benchmark batch, check account readiness with `python3 scripts/check_infra.py` or `python3 scripts/account_health.py status`. Do not assume OAuth accounts are usable just because credentials exist.

## Beads Prerequisite and Usage
- Keep the Beads CLI (`bd`, alias `beads`) up to date before running agent workflows that rely on task graphs.
- Install or update with the official installer:
```bash
curl -fsSL https://raw.githubusercontent.com/steveyegge/beads/main/scripts/install.sh | bash
```
- Verify install/version with `bd --version` (or `beads --version`).
- Do not use `bd edit`; use non-interactive `bd create/update/close --json` or stdin-based `--description=-`.
- Typical flow: `bd ready --json`, `bd create ... --json`, `bd update <id> --claim`, `bd close <id> --reason "Done"`.

## Minimal Loading Policy
- Default load order: this file + one relevant skill + one relevant doc.
- Do not open broad catalogs (`docs/TASK_CATALOG.md`, large script lists, full reports) unless required.
- Prefer directory-local `AGENTS.md` / `CLAUDE.md` when working under `scripts/`, `configs/`, `tasks/`, or `docs/`.

## Fast Routing By Intent
- Launch or rerun benchmarks: `docs/DAYTONA.md` (Daytona, preferred) or `docs/START_HERE_BY_TASK.md`
- Monitor / status: `docs/START_HERE_BY_TASK.md` -> "Monitor Active Runs"
- Triage failures: `docs/START_HERE_BY_TASK.md` -> "Triage Failed Tasks"
- Compare configs / MCP impact / IR: `docs/START_HERE_BY_TASK.md` -> "Analyze Results"
- Repo policy / health gate: `docs/REPO_HEALTH.md`, `docs/ops/WORKFLOWS.md`
- Script discovery: `docs/ops/SCRIPT_INDEX.md`

## Local Guides
- `scripts/AGENTS.md` - script categories, safe usage, one-off handling
- `configs/AGENTS.md` - run launcher wrappers and confirmation gate policy
- `docs/AGENTS.md` - documentation IA and canonical vs archive guidance

## Compaction / Handoff
- Compact after exploration, after launching a batch, and after triage/report passes.
- Use `/handoff` skill for session handoffs (inline prompt, not a markdown file unless asked).
- Use `docs/ops/HANDOFF_TEMPLATE.md` as checklist.

## Landing the Plane
- Run `python3 scripts/repo_health.py` (or `--quick` for docs/config-only).
- `git pull --rebase && git push && git status` -- work is not done until push succeeds.
- Track follow-ups in issues or beads. Update status.

## Canonical Maps
- `docs/START_HERE_BY_TASK.md` - task-based read order
- `docs/ops/WORKFLOWS.md` - operational workflow summaries
- `docs/ops/TROUBLESHOOTING.md` - escalation and common failure routing
- `docs/ops/SCRIPT_INDEX.md` - generated script registry index
- `docs/reference/README.md` - stable specs and reference docs
- `docs/explanations/README.md` - rationale and context docs

## Common Gotchas (from session history)

### Documentation Generation
- **NEVER edit root `CLAUDE.md` or `AGENTS.md` directly.** Edit canonical sources under `docs/ops/` and regenerate. Direct edits cause `agent_guides_drift` failures in `repo_health.py`.
- After removing directories from the repo, also clean references from `scripts/sync_agent_guides.py` (`LOCAL_SOURCES`) and `scripts/docs_consistency_check.py` (`LOCAL_AGENT_TARGET_DIRS`).

### Daytona / Harbor
- Daytona builds from Dockerfiles at sandbox creation. Fixes on `main` take effect next run (pre-built GHCR images need separate rebuild).
- Harbor+Daytona (`harbor run --environment-type daytona`) is recommended. `scripts/daytona_runner.py` is for quick validation only.
- `BASELINE_MCP_TYPE` env var: `none`, `sourcegraph`, `deepsearch`.
- Use Daytona SDK (`daytona_sdk`) over CLI (CLI is interactive-only for SSH).
- GHCR packages default **private** for personal accounts; visibility change requires GitHub web UI.
- Snapshot names are **positional**: `daytona snapshot create ccb-name`, NOT `--name`.
- CLI/API version mismatch causes "Forbidden" errors. Keep CLI version in sync.
- Registry types enum: `internal`, `organization`, `transient`, `backup`. Use `organization` for GHCR/Docker Hub.

### Docker / Build
- `uv tool install` segfaults on ARM64/QEMU. Use `pip install` or Daytona (native x86_64).
- Build-push-clean pattern for limited disk (~45GB): build, push, clean before next image.
- Colons in agent names break Docker volume mounts. Replace `:` with `__`.
- Add `|| git init` fallback to `git clone` in Dockerfiles. Add `chown claude:claude /logs` + `adduser claude` for OH compat.
- `jefzda/` → `ghcr.io/sg-evals/` migration incomplete: 33 Dockerfiles in `csb/debug/` and `csb/fix/`.

### MCP Configuration (inside sandboxes)
- `.mcp.json` at `$CLAUDE_CONFIG_DIR` (typically `/logs/agent/sessions/`), not `/app/` or `/root/`. Claude Code needs `--mcp-config` flag.
- `NODE_TLS_REJECT_UNAUTHORIZED=0` for Node.js SSL in containers.
- Sourcegraph: **stdio** (`npx @sourcegraph/cody --stdio`), NOT HTTP. Skills empty in headless -- embed in CLAUDE.md.
- Sourcegraph env vars: `SOURCEGRAPH_URL` and `SOURCEGRAPH_ACCESS_TOKEN` (NOT `_ENDPOINT` or `_TOKEN`).

### Harbor Result Format
- Timing fields (`started_at`, `finished_at`) at **top level** of `result.json`, not nested under `timing`.
- `trajectory.json` generated by Harbor's `_convert_events_to_trajectory()`, not by Claude Code CLI.
- SWE-bench `test.sh` redirects stdout to temp file; Harbor never sees `START_TEST_OUTPUT`/`END_TEST_OUTPUT` markers.
- Token usage in `trajectory.json`; transcript parsers don't see it. Contract: write `/logs/verifier/reward.txt`.

### Security / Credentials
- **Never pass credentials via Docker `-e` flags** (leak into trajectory HTML). Use file-based injection: `/logs/agent/.credentials.json` with `chmod 600`.
- `sanitize_secrets.py` IS integrated into `export_official_results.py` (line 32), but allowlist bypass (`_FAKE_INDICATORS` substring matching too broad) undermines it. Use exact-match `FAKE_KEY_ALLOWLIST`.

### Harness-Agnostic Verifiers
- **no_changes_guard** must use `git diff origin/main HEAD` (not `git diff HEAD`) for auto-committing agents (e.g., OpenHands).
- Verifier fallbacks: `${TASK_WORKDIR:-/workspace}` for workdir, `${TASK_REPO_ROOT:-${VERIFY_REPO:-/workspace}}` for repo root.
- Set `GOWORK=off` in test.sh when sg_only verifier restores full repo (go.work may need newer Go).
- **122 active tasks** (259 total with backups) hardcode `ANSWER_PATH="/workspace/answer.json"` without fallbacks. Also check `ANSWER_JSON` variable in `answer_json_verifier_lib.sh`. All use same template pattern; bulk fix feasible. Zero scores on non-Harbor harnesses.

### Scripts / Code Quality
- **abc_audit.py duplicate functions**: `check_oa_equivalent_solutions`, `check_ob_negated_solutions`, `check_og_determinism`, `check_t10_shared_state` each defined twice. Python uses last definition silently.
- **ir_metrics.py `tt_all_r` bug**: Line 749 set comparison may report time-to-first-relevant instead of time-to-all-relevant.
- **`--skip-completed` defect** in `run_selected_tasks.sh`: requires both `result.json` AND `task_metrics.json`. Fix: check only `result.json`.
- **Task registry metadata header stale**: claims 436 tasks, actual 274. `sync_task_metadata.py --fix` doesn't update header block.
- **`verification_modes` + `use_case_category` missing from all 274 tasks**: Breaks auto-detection (always defaults to artifact-only) and `--use-case-category` filter (silently filters everything).

### Validation / Scoring
- `validators.py` duplicated across `ccb_build` tasks. Changes must hit **all copies** (`sha256sum`).
- Agent completing in **<2s** = never installed/ran. Real name in `config.json` at `task.path`.
- **no_changes_guard**: write `reward.txt` inside Python block, not in bash after it.
- `timeout 600` on all test runners. `--forceExit` for Jest. Jest+TS needs `memory_mb = 8192`.
- **CSB dual-score**: file edits + `answer.json` scored independently. Fallback: `promoted_verifier.py` -> `oracle_checks.py` -> heuristic.
- Rate-limited results (score=0, <30s): `scripts/quarantine_invalid_tasks.py --execute`.
- Bare `$VAR` in `instruction.md` gets expanded. Use `<placeholder>` syntax.
- Pass rate logic duplicated in `generate_eval_report.py` and `csb_metrics/models.py`. Sync both on changes.
- `cost_report.py`: `defaultdict(int)` + `.get("baseline", 1)` returns `0` when key exists. Use `or 1`.
- **TARGET_SUITE misalignment**: 55 stale suite names, 220 missing. `SUITE_WEIGHTS` falls back to equal-weight.
- **dual_score_lib.sh**: `scorer_artifact` always `"auto"` (`.setdefault()` overwrite). Audit trail broken.
- **Falsy value bugs**: `max_score=0` treated as false; `None` MCP metrics misclassified. Use `is None` / `== 0`.
- **promote_run.py**: Crashes on non-dict env config. Validate types before `.get()`.

### Git / Auth
- `gh auth refresh -h github.com -s write:packages` (explicit scope needed).
- Env vars must be **exported** for Harbor subprocesses (`set -a` before sourcing `.env.local`).
- GitHub push protection blocks synthetic keys. Squash with `git reset --soft origin/main`.
- Shallow clones fail on push. Some repos use `master`; detect with `git symbolic-ref refs/remotes/origin/HEAD`.
- **gitignore negation**: `!child/` doesn't work when parent dir is ignored. Use `git add -f`.

### Python / Subprocess
- `dict.get(key, default)` does NOT protect against `None` values. Use `data.get("key") or default_value`.
- `with open(log) as f: subprocess.Popen(stdout=f)` closes the handle. Use `open()` without context manager for long-running subprocesses.
- `json.load(open(path))` leaks file descriptors. Use `with open(path) as f: json.load(f)`. Affects 12 scripts.
- macOS Bash 3.2 lacks `declare -A`. Use pipe-delimited strings with `IFS='|' read -r`.

### LLM Judge
- Always include "Respond with valid JSON only" in judge prompts. Unescaped quotes break parsing.
- Judge should use task-type-aware evaluation: different rubrics per task type.
- Tool categorization: check MCP prefix (`mcp__`) before substring checks to avoid miscategorization.

### OpenHands
- Strip ALL `sandbox_plugins` (`= []`). Base64-encode instructions (not `shlex.quote()`). Alpine lacks `apt-get` -- use `bookworm`.
- OH MCP client ~30s timeout. Block `deepsearch`/`deepsearch_read` in auth proxy; redirect to `keyword_search`/`nls_search`.
- `chown -R /workspace` blocks >120s on large repos. Edit installed `runtime_init.py`. Set `PYTHONSAFEPATH=1`.

### CI / Workflows
- `docs-consistency.yml` is redundant -- subsumed by `repo_health.yml`. Doubles CI minutes.
- Export HTML silently truncates at 1200 rows (`filtered.slice(0, 1200)` in `export_official_results.py`).

### Pre-commit / Pytest / Ralph
- Secret-detection hooks false-positive on code that _detects_ secrets. Use `--no-verify` when flagged code is detection logic.
- Classes named `TestPlan`/`TestCase`/`TestResult` get auto-collected by pytest. Rename to `EvaluationPlan` etc.
- Ralph sessions write learnings to `progress.txt` on feature branches, not main. Compound back after merge.
- **Ralph `prd.json` is single-active**: Overwriting loses tracking state. Archive old `prd.json` before replacement.

## Maintenance
- Root and local `AGENTS.md` / `CLAUDE.md` files are generated from sources in `docs/ops/`.
- `docs/START_HERE_BY_TASK.md` is generated from `docs/ops/task_routes.json`.
- Regenerate after edits (single command):
```bash
python3 scripts/refresh_agent_navigation.py
```
