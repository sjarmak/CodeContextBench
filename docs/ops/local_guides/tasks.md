# Tasks Directory Guide

Use this file when modifying benchmark task definitions or task metadata.

## What Lives Here
- Harbor task instances (`task.toml`, `instruction.md`, verifier/test files, Dockerfiles).
- Suite-specific task organization and metadata used by selection and validation scripts.

## Navigation Rules
- Start with `docs/TASK_CATALOG.md` for inventory context only if you need cross-suite coverage.
- For edits, open the specific task directory and `task.toml` first.
- Run preflight validation after task changes (`scripts/authoring/validate_tasks_preflight.py`).

## Guardrails
- Keep task metadata synchronized with `configs/selected_benchmark_tasks.json` when applicable.
- Keep tasks aligned with the stable contract in `docs/reference/TASK_CONTRACT.md`.
- Use runtime smoke validation for new/changed tasks before broader runs.
- Document verifier quirks in the relevant docs instead of expanding root agent guides.

## Migration Workflow
- Audit contract drift with `python3 scripts/authoring/validate_tasks_preflight.py --all --contract-only --summary-by-check`.
- Fix the highest-count checks first: path contract drift, variant workdir mismatches, then storage over-requests.
- Re-run `python3 scripts/authoring/validate_tasks_preflight.py --task <task_dir>` after each migrated task or generator.
