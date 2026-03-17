# Scripts Directory Guide

Use this file when working in `scripts/`.

## What Lives Here
- Operational entrypoints for benchmark runs, validation, analysis, reporting, and maintenance.
- Helper shell wrappers and verifier helper libraries.
- Historical one-off scripts kept for auditability.

## Navigation Rules
- Start with `docs/ops/SCRIPT_INDEX.md` to identify the right script.
- Prefer maintained scripts over `one_off` scripts unless a historical incident requires them.
- Check `scripts/registry.json` for category and status metadata before broad searching.

## Common Entry Points
- `scripts/maintenance/repo_health.py` - pre-commit/push health gate
- `scripts/infra/check_infra.py` - infra readiness
- `scripts/infra/account_health.py` - account readiness, recent rate-limit observations, active assignment tracking
- `scripts/authoring/validate_tasks_preflight.py` - task preflight validation
- `scripts/analysis/aggregate_status.py` - run status scan
- `scripts/authoring/validate_task_run.py` - post-run validation
- `scripts/running/daytona_runner.py` - standalone Daytona runner (task listing, dry runs, quick validation)
- `scripts/infra/build_daytona_registry.py` - regenerate Daytona task registry

## Editing Rules
- Preserve backward compatibility for high-use scripts unless the change is intentional.
- If you add/rename a script, regenerate the script registry/index.
- Label one-off scripts with prefixes like `rerun_`, `backfill_`, `fix_`, or `repair_`.
