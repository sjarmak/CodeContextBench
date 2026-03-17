# CodeScaleBench Agent Router

This file is the root entrypoint for AI agents working in this repository.
Keep it small. Use it to route to the right workflow and local guide, not as the
full operations manual.

## Non-Negotiables
- All work happens on `main` by default. If you use feature branches, keep them small, short-lived, and easy to fast-forward back into `main`.
- Every `harbor run` must be gated by interactive confirmation.
- Before commit/push, run `python3 scripts/maintenance/repo_health.py` (or `--quick` for docs/config-only changes).
- **Never push `main` to `upstream`** (public). See "Git Remotes and Branching".
- Prefer a **remote execution environment** (e.g., Daytona) for large benchmark runs; use local Docker only when a task’s image or registry is incompatible with your cloud environment. See `docs/DAYTONA.md`.
- Set **parallelism based on your own account and model limits**. Avoid exceeding documented concurrency or rate caps for your environment or provider.
- Before launching any benchmark batch, check account readiness with `python3 scripts/infra/check_infra.py` or `python3 scripts/infra/account_health.py status`. Do not assume OAuth accounts are usable just because credentials exist.

## Git Remotes and Branching
- `origin` = sjarmak/CodeScaleBench (private), `upstream` = sourcegraph/CodeScaleBench (public).
- `git push` goes to `origin`. **NEVER push `main` to `upstream`** — it has sensitive content.
- Public releases: `git checkout public && git merge main && git push upstream public && git checkout main`
- `public` branch `.gitignore` strips dev noise; only `docs/technical_reports/` and `runs/analysis/` survive.

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

## Compaction / Handoff Checkpoints
- Compact after exploration, before multi-file edits.
- Compact after launching a benchmark batch.
- Compact after completing a triage batch or report generation pass.
- When handing work to a new session, use the generic `/handoff` skill to generate an inline copy/paste handoff prompt.
- Do not create a markdown handoff file unless the user explicitly asks for one.
- Use `docs/ops/HANDOFF_TEMPLATE.md` as a checklist for what the handoff should include.

## Landing the Plane (Session Completion)
- Track remaining follow-up in issues or beads.
- Run `python3 scripts/maintenance/repo_health.py` (or `--quick` for docs/config-only changes).
- Update issue/task status.
- `git pull --rebase && git push && git status` — pushes to `origin` (private). Do NOT push to `upstream` unless doing a public release.
- Clean up and hand off using `/handoff` plus `docs/ops/HANDOFF_TEMPLATE.md`.
- Work is not complete until push succeeds.

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
- After removing directories from the repo, also clean references from `scripts/maintenance/sync_agent_guides.py` (`LOCAL_SOURCES`) and `scripts/maintenance/docs_consistency_check.py` (`LOCAL_AGENT_TARGET_DIRS`).

### Daytona / Harbor
- Daytona builds images from Dockerfiles at sandbox creation time (`Image.from_dockerfile()`). Dockerfile fixes pushed to `main` take effect on the next run -- **no manual image rebuild needed**. Exception: pre-built GHCR base images must be rebuilt separately.
- Harbor+Daytona (`harbor run --environment-type daytona`) is the recommended production approach. The standalone `scripts/running/daytona_runner.py` is for quick validation only.
- Use `BASELINE_MCP_TYPE` env var to control MCP configuration: `none`, `sourcegraph`, `deepsearch`.
- Daytona SDK (`daytona_sdk`) over CLI for sandbox interaction -- the CLI is interactive-only for SSH.
- GHCR packages default to **private** for personal accounts and visibility cannot be changed via API. Use the GitHub web UI or push to an org.

### Docker / Build
- `uv tool install` segfaults on ARM64/QEMU emulation. Use `pip install` instead, or switch to Daytona (native x86_64).
- Build-push-clean pattern when building Docker images with limited disk (~45GB): build one image, push, then clean locally before the next.
- Colons in agent names (e.g., `module:ClassName`) break Docker volume mounts. Sanitize paths: replace `:` with `__`.

### MCP Configuration (inside sandboxes)
- `.mcp.json` must be placed at `$CLAUDE_CONFIG_DIR` (typically `/logs/agent/sessions/`), not `/app/` or `/root/`.
- Claude Code requires the `--mcp-config` CLI flag to load MCP config -- it does not auto-detect.
- Inject MCP usage instructions into the task prompt. Agents won't use MCP tools just because they're available.
- Set `NODE_TLS_REJECT_UNAUTHORIZED=0` for Node.js SSL in Docker containers (curl working does not mean Node.js fetch will work).
- Sourcegraph MCP uses **stdio transport** (`npx @sourcegraph/cody --stdio`), NOT HTTP. HTTP 405 = correct endpoint, wrong protocol.
- Sourcegraph skills show empty in headless mode. Embed skill prompt content in CLAUDE.md directly.
- Sourcegraph env vars: `SOURCEGRAPH_URL` and `SOURCEGRAPH_ACCESS_TOKEN` (NOT `_ENDPOINT` or `_TOKEN`).

### Harbor Result Format
- Timing fields (`started_at`, `finished_at`) live at the **top level** of `result.json`, not nested under `timing`.
- `trajectory.json` is generated by Harbor's `_convert_events_to_trajectory()` post-processing, NOT by Claude Code CLI directly.
- SWE-bench `test.sh` redirects stdout to a temp file -- Harbor never sees the parser's `START_TEST_OUTPUT`/`END_TEST_OUTPUT` markers via its normal capture.
- Token usage data lives in `trajectory.json`; plain transcript parsers do not see it.
- Harbor task contract requires writing `/logs/verifier/reward.txt`.

### Validation / Scoring
- `validators.py` is duplicated across `ccb_build` tasks. Changes must be applied to **all copies** (verify with `sha256sum`).
- Install scripts that print "INSTALL_SUCCESS" regardless of actual outcome are common. Always verify the binary exists and is executable.
- Agent completing in **<2 seconds** = agent never installed/ran (smoke test heuristic).
- Trial directory names are truncated with hash suffixes (e.g., `c_api_graphql_expert_079_archite__pm9xcPn`). The real task name lives in `config.json` at `task.path`.
- LoCoBench task IDs contain multi-word fields (e.g., `game_engine`, `cross_file_refactoring`). Use the 3-digit task number as a positional anchor for parsing instead of rigid regexes that assume single-word fields.
- **no_changes_guard**: Python sets `reward = 0.0` but bash `echo "$score"` uses the original variable. Write `reward.txt` inside the Python block, not after it.
- Wrap all test runners with `timeout 600`. Add `--forceExit` to Jest. Indefinite hangs (>2h) observed without timeout.
- Jest + TypeScript needs 4-6GB RAM. Set `memory_mb = 8192` in `task.toml` for front-end test suites (default 2GB causes OOM).
- **CSB dual-score**: agents produce file edits + `answer.json`; scored independently. Fallback: `promoted_verifier.py` → `oracle_checks.py` → heuristic.
- Rate-limited results (score=0, duration <30s): quarantine with `scripts/maintenance/quarantine_invalid_tasks.py --execute`.

### Git / Auth
- **Dual-remote**: `origin` = private, `upstream` = public. Only push `public` branch to `upstream`. See "Git Remotes and Branching".
- `gh auth refresh` without `-s <scope>` is a no-op. Use `gh auth refresh -h github.com -s write:packages`.
- Env vars must be **exported** for Harbor subprocesses. Use `set -a` before sourcing `.env.local`.
- GitHub push protection blocks API keys. Squash with `git reset --soft origin/main`.
- Shallow clones (`--depth 1`) fail on push. Always use full clones.
- Large repo push failures (HTTP 500): push in 100-commit increments.

### Python / Subprocess
- `dict.get(key, default)` does NOT protect against `None` values. Use `data.get("key") or default_value`.
- `with open(log) as f: subprocess.Popen(stdout=f)` closes the handle. Use `open()` without context manager for long-running subprocesses.
- macOS Bash 3.2 lacks `declare -A`.

### LLM Judge
- Always include "Respond with valid JSON only (escape all quotes and special characters)" in judge prompts. Unescaped quotes in LLM-generated JSON break parsing.
- Judge should use task-type-aware evaluation: different rubrics for code implementation, architectural understanding, and bug fix tasks.
- Tool categorization order matters: check MCP prefix (`mcp__`) before substring checks (e.g., `deep_search`) to avoid miscategorization of `mcp__deep_search`.

### OpenHands
- `sandbox_plugins` is a list (not property). Strip ALL plugins (`= []`) -- `agent_skills` indexes `/workspace` at startup (120s timeout on large repos). TOML config has no effect in v1.4.0.
- `shlex.quote()` breaks on shell metacharacters (0% execution). Base64-encode instructions on host, decode inside container.
- Background daemons outlive the main process and hang Daytona poll. Wrap with `pkill` cleanup; guard with `shutil.which('pkill')` (missing on minimal images).
- Alpine lacks `apt-get` (OH installer requirement). Use `bookworm` variants.
- OH MCP client has ~30s timeout. Block `deepsearch`/`deepsearch_read` in auth proxy; redirect to `keyword_search`/`nls_search`.
- `chown -R /workspace` blocks port binding >120s on large repos. Edit installed `runtime_init.py` source -- monkey-patches don't propagate to action_execution_server subprocess.
- Set `PYTHONSAFEPATH=1` to prevent repo-local packages from shadowing installed deps.

### Pre-commit / Pytest / Ralph
- Secret-detection hooks false-positive on code that _detects_ secrets. Use `--no-verify` when flagged code is detection logic.
- Classes named `TestPlan`/`TestCase`/`TestResult` get auto-collected by pytest. Rename to `EvaluationPlan` etc.
- Ralph sessions write learnings to `progress.txt` on feature branches, not main. Compound back after merge.

## Maintenance
- Root and local `AGENTS.md` / `CLAUDE.md` files are generated from sources in `docs/ops/`.
- `docs/START_HERE_BY_TASK.md` is generated from `docs/ops/task_routes.json`.
- Regenerate after edits (single command):
```bash
python3 scripts/maintenance/refresh_agent_navigation.py
```
