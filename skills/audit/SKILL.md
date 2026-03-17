---
name: audit
description: Run repo health checks, validate benchmark tasks, and audit run integrity.
---

# Skill: Audit & Validation

## Scope

Use this skill when the user asks to:
- Run pre-commit/push repo health gates
- Validate task definitions and structure
- Audit benchmark run integrity and completeness
- Check documentation consistency
- Verify contract compliance (task.toml, tests, oracles)

## Canonical Commands

```bash
# Full repo health gate
python3 scripts/maintenance/repo_health.py

# Quick health (docs + selection file only)
python3 scripts/maintenance/repo_health.py --quick

# Validate all tasks
python3 scripts/authoring/validate_tasks_preflight.py --all

# Validate specific task
python3 scripts/authoring/validate_tasks_preflight.py --task benchmarks/csb/debug/task-name

# Post-run task validation
python3 scripts/authoring/validate_task_run.py runs/staging/run_dir/task_id

# Audit canonical evaluation contract
python3 scripts/evaluation/audit_canonical_evaluation_contract.py
```

## Health Gate Checks

- **Docs consistency** — CLAUDE.md, AGENTS.md, script index drift
- **Task preflight** — instruction length, test.sh present, no placeholders
- **Selection file** — configs/selected_benchmark_tasks.json valid JSON
- **Launch policy** — configs/*.sh use _common.sh, no raw harbor run

## Task Validation

- Task metadata in task.toml (language, difficulty, time_limit_sec)
- test.sh and oracle_checks.py present and executable
- Instruction.md length and format compliance
- Verifier contract (test, artifact, verification modes)

## Related Skills

- `/run` — execute benchmarks that will be audited
- `/report` — compile audit findings into reports
