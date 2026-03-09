# Configs Directory Guide

Use this file when working in `configs/` launchers and run orchestration wrappers.

## Non-Negotiables
- Every `harbor run` invocation must be interactively confirmed.
- Do not reintroduce `--yes` for `configs/run_selected_tasks.sh`.
- Validate config naming and paired-run semantics via shared helpers in `configs/_common.sh`.
- Before launching, rely on the shared account-readiness gate in `configs/_common.sh`. It reads `scripts/account_health.py` state, drops unsafe accounts, and may cap parallelism to safe slots.

## Parallelism Policy
- **Daytona (default)**: 62 task pairs (124 concurrent sandboxes, 1 headroom). `run_selected_tasks.sh` auto-detects `HARBOR_ENV=daytona` and sets 124 parallel slots. Daytona's Tier 3 limit is 125 concurrent sandboxes (250 vCPU / 2 per sandbox). Each task pair = 2 sandboxes (baseline + MCP). The job pool queue (`_wait_for_slot`) ensures we never exceed 124 in-flight processes.
- **Local Docker**: Auto-detected as `number_of_accounts x 6` concurrent slots (currently 30 with 5 accounts). Only for sweap-images tasks (9 csb_sdlc_debug + 9 csb_sdlc_fix) that cannot run on Daytona.
- **Do NOT hardcode `--parallel`** unless you have a specific reason. Let `run_selected_tasks.sh` auto-detect from the environment.

## Navigation Rules
- Start with `configs/_common.sh` for shared run policy and confirmation behavior.
- Use `configs/run_selected_tasks.sh` for selected-task execution flows.
- Use `configs/*_2config.sh` wrappers for paired baseline/MCP runs.
- **Daytona is the default execution environment** — all production and variance runs use `HARBOR_ENV=daytona`. Local Docker is only for the 18 sweap-images tasks that are Daytona-incompatible. See `docs/DAYTONA.md` for prerequisites and capacity planning.
- For launch readiness, check `python3 scripts/check_infra.py` or `python3 scripts/account_health.py status` before touching wrapper defaults or manually setting `--parallel`.

## When Editing
- Preserve `confirm_launch()` gating behavior.
- Preserve `account_readiness_preflight()` and runtime account-state updates in `_common.sh`; new launchers should not bypass them.
- Keep config name semantics aligned with `docs/CONFIGS.md`.
- Run at least `python3 scripts/docs_consistency_check.py` after changing command references.
