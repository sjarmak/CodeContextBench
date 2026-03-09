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

## Compaction / Handoff Checkpoints
- Compact after exploration, before multi-file edits.
- Compact after launching a benchmark batch.
- Compact after completing a triage batch or report generation pass.
- When handing work to a new session, use the generic `/handoff` skill to generate an inline copy/paste handoff prompt.
- Do not create a markdown handoff file unless the user explicitly asks for one.
- Use `docs/ops/HANDOFF_TEMPLATE.md` as a checklist for what the handoff should include.

## Landing the Plane (Session Completion)
- Track remaining follow-up in issues or beads.
- Run `python3 scripts/repo_health.py` (or `--quick` for docs/config-only changes).
- Update issue/task status.
- `git pull --rebase && git push && git status` and confirm `main` is up to date with `origin/main`.
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
- Sourcegraph MCP uses **stdio transport** (`npx @sourcegraph/cody --stdio`), NOT HTTP endpoints. HTTP 405 from the endpoint means it exists but requires stdio.
- Sourcegraph skills installed via `npx -y skills add` show empty `"skills": []` in headless/containerized mode. Embed skill prompt content directly in the task's CLAUDE.md instead.
- Sourcegraph MCP env vars are `SOURCEGRAPH_URL` and `SOURCEGRAPH_ACCESS_TOKEN`. Do NOT use `SOURCEGRAPH_ENDPOINT` or `SOURCEGRAPH_TOKEN` -- those are wrong variable names.

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

### Git / Auth
- `gh auth refresh` without `-s <scope>` is a no-op for adding scopes. Must use `gh auth refresh -h github.com -s write:packages` explicitly.
- Environment variables must be **explicitly exported** for Harbor subprocesses. Use `set -a` before sourcing `.env.local`.
- Account readiness is tracked in `runs/state/account_health.json`. Launchers source `configs/_common.sh`, filter out unsafe accounts before launch, and record recent runtime rate-limit observations there for operator context.
- GitHub push protection blocks synthetic/fake API keys in test data. Use `git reset --soft origin/main` to squash intermediate commits that contained fake credentials.
- Shallow clones (`--depth 1`) fail on push to GitHub with `remote: fatal: did not receive expected object`. Always use full clones for repos that will be pushed.
- Some repos use `master` as default branch. Detect with `git symbolic-ref refs/remotes/origin/HEAD` and remap to `main` if needed.
- GitHub secret scanning blocks pushes containing embedded secrets (Slack webhooks, API keys in source). Users must manually unblock via the provided `/security/secret-scanning/unblock-secret/` URL.

### Python / Subprocess
- `dict.get(key, default)` does **NOT** protect against `None` values. If key exists with value `None`, the default is not used. Use `data.get("key") or default_value` for Harbor result fields that may be `null`.
- `with open(log) as f: subprocess.Popen(stdout=f)` closes the file handle immediately after `Popen()` returns. Use `open()` without context manager for long-running subprocesses.
- macOS ships Bash 3.2 which lacks associative arrays (`declare -A`). Use pipe-delimited string arrays with `IFS='|' read -r` for compatibility.

### LLM Judge
- Always include "Respond with valid JSON only (escape all quotes and special characters)" in judge prompts. Unescaped quotes in LLM-generated JSON break parsing.
- Judge should use task-type-aware evaluation: different rubrics for code implementation, architectural understanding, and bug fix tasks.
- Tool categorization order matters: check MCP prefix (`mcp__`) before substring checks (e.g., `deep_search`) to avoid miscategorization of `mcp__deep_search`.

## Maintenance
- Root and local `AGENTS.md` / `CLAUDE.md` files are generated from sources in `docs/ops/`.
- `docs/START_HERE_BY_TASK.md` is generated from `docs/ops/task_routes.json`.
- Regenerate after edits (single command):
```bash
python3 scripts/refresh_agent_navigation.py
```
