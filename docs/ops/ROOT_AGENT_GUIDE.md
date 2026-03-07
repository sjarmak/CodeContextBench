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

## Beads Prerequisite
- Keep the Beads CLI (`bd`, alias `beads`) up to date before running agent workflows that rely on task graphs.
- Install or update with the official installer:
```bash
curl -fsSL https://raw.githubusercontent.com/steveyegge/beads/main/scripts/install.sh | bash
```
- Verify install/version with `bd --version` (or `beads --version`).

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
- Use `docs/ops/HANDOFF_TEMPLATE.md` when handing work to a new session.

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
- Daytona builds images from Dockerfiles at sandbox creation time (`Image.from_dockerfile()`). Dockerfile fixes pushed to `main` take effect on the next run -- **no manual image rebuild needed**. Exception: pre-built GHCR base images must be rebuilt separately.
- Harbor+Daytona (`harbor run --environment-type daytona`) is the recommended production approach. The standalone `scripts/daytona_runner.py` is for quick validation only.
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

### Harbor Result Format
- Timing fields (`started_at`, `finished_at`) live at the **top level** of `result.json`, not nested under `timing`.
- `trajectory.json` is generated by Harbor's `_convert_events_to_trajectory()` post-processing, NOT by Claude Code CLI directly.
- SWE-bench `test.sh` redirects stdout to a temp file -- Harbor never sees the parser's `START_TEST_OUTPUT`/`END_TEST_OUTPUT` markers via its normal capture.

### Validation / Scoring
- `validators.py` is duplicated across `ccb_build` tasks. Changes must be applied to **all copies** (verify with `sha256sum`).
- Install scripts that print "INSTALL_SUCCESS" regardless of actual outcome are common. Always verify the binary exists and is executable.
- Agent completing in **<2 seconds** = agent never installed/ran (smoke test heuristic).

### Git / Auth
- `gh auth refresh` without `-s <scope>` is a no-op for adding scopes. Must use `gh auth refresh -h github.com -s write:packages` explicitly.
- Environment variables must be **explicitly exported** for Harbor subprocesses. Use `set -a` before sourcing `.env.local`.
- GitHub push protection blocks synthetic/fake API keys in test data. Use `git reset --soft origin/main` to squash intermediate commits that contained fake credentials.

## Maintenance
- Root and local `AGENTS.md` / `CLAUDE.md` files are generated from sources in `docs/ops/`.
- `docs/START_HERE_BY_TASK.md` is generated from `docs/ops/task_routes.json`.
- Regenerate after edits (single command):
```bash
python3 scripts/refresh_agent_navigation.py
```
