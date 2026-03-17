# Troubleshooting

## When To Read This
- You hit infra failures, verifier anomalies, missing outputs, or MCP regressions.

## Do Not Read First If
- You only need the standard run flow: use `docs/ops/WORKFLOWS.md`.

## Escalation Routing
- Repeated infra failures: stop reruns, fix root cause first (`scripts/infra/check_infra.py`).
- Suspected verifier bug: quarantine task, collect evidence, open follow-up.
- Missing trajectories: use transcript/JSONL fallback and document limitation.
- Widespread MCP regressions: run `scripts/evaluation/mcp_audit.py` before changing prompts/configs.

## Useful References
- `docs/ERROR_CATALOG.md`
- `docs/QA_PROCESS.md`
- `docs/REPO_HEALTH.md`
- `docs/ops/SCRIPT_INDEX.md`

## Minimal Triage Checklist
1. Confirm exact run/task path and error signature.
2. Validate task output files.
3. Check whether failure matches known fingerprint.
4. Classify as infra / verifier / task / agent behavior.
5. Choose isolated rerun or fix path.

## Daytona / OpenHands Notes

- Do not classify a trial as a Daytona image-build stall from `trial.log` alone. Some orphaned or crashed trials leave `trial.log` at `Building environment from ...` even after agent setup succeeded.
- Before calling it a remote build issue, check for:
  - `agent/setup/return-code.txt`
  - `agent/instruction.txt`
  - `agent/command-0/command.txt`
- If those files exist, the environment build already progressed past Docker build and the failure is later in launcher orchestration or agent startup handoff.
- For MCP harness triage, inspect `agent/instruction.txt` first and confirm it names the expected `github.com/sg-evals/...` mirror. A generic repo target such as `github.com/the codebase` indicates prompt wiring drift, not task difficulty.
- **OpenHands orphaned sandbox / hung harness**: OpenHands spawns persistent background daemons (tmux, jupyter kernel gateway, ipykernel, action execution server) that outlive the main process. These orphans prevent Daytona's session-command from reporting an exit code, causing Harbor's `_poll_response` loop to hang indefinitely. The `OpenHandsHarnessAgent` in `agents/harnesses/openhands/agent.py` includes a `_CLEANUP_SUFFIX` that kills these daemons after the main pipeline exits. If you see a sandbox stuck in `started` state with no harness process running, this is the likely cause. Claude Code runs are unaffected because they don't spawn persistent background services.

## Known Process-Failure Patterns

- `Sandbox with name ... already exists`: treat as stale Daytona state, not a task failure. This usually means a previous `BUILD_FAILED` or crashed run left a sandbox behind, or the run used pre-fix naming. Clean the old sandbox before rerunning.
- `Disk request ... exceeds maximum allowed per sandbox (10GB)`: this is a request-time rejection, not evidence the task actually used that much disk. Audit the task's `storage` setting first before routing it off Daytona.
- `CancelledError` traceback ending inside `harbor/environments/daytona.py` `_poll_response()` during `_run_verification()`: the agent may already have finished. Check for `trajectory.json`, transcript completion, and verifier artifacts before classifying it as a timeout. Harbor cleanup does not run until control returns to the trial `finally` block, so these can leave orphan sandboxes/processes behind.
- OpenHands setup failure referencing repo-local packages such as `/workspace/pandas/__init__.py` or `/app/pandas/__init__.py`: this is a harness startup isolation bug, not a benchmark failure. The common trigger is the OpenHands install smoke-test or runtime starting from the repo root, which lets task packages shadow installed dependencies.
