---
name: scaffold
description: Create, mine, and validate new benchmark tasks and task suites.
---

# Skill: Task Scaffolding & Authoring

## Scope

Use this skill when the user asks to:
- Create new benchmark tasks or suites
- Mine tasks from source repositories
- Scaffold task definitions with metadata and structure
- Validate task authoring and compliance
- Update task metadata and verifiers

## Canonical Commands

```bash
# Scaffold new task from template
python3 scripts/authoring/scaffold_task.py --suite csb_sdlc_debug --task-name my-task-001

# Mine tasks from repo
python3 scripts/authoring/mine_bug_tasks.py --source-repo https://github.com/org/repo

# Validate task structure
python3 scripts/authoring/validate_tasks_preflight.py --task benchmarks/csb/debug/my-task-001

# Create task specifications from ground truth
python3 scripts/infra/build_daytona_registry.py --task benchmarks/csb/debug/my-task-001

# Backfill task metadata
python3 scripts/evaluation/backfill_instruction_artifacts.py --task-id my-task-001
```

## Task Definition Structure

```
benchmarks/csb/CATEGORY/TASK_ID/
├── task.toml                 # Metadata: language, difficulty, time_limit_sec
├── instruction.md            # Task description and requirements
├── instruction_mcp.md        # MCP-specific retrieval hints
├── environment/
│   ├── Dockerfile
│   └── Dockerfile.sg_only    # Sourcegraph-only variant
├── tests/
│   ├── test.sh               # Main verifier
│   ├── oracle_checks.py      # Ground truth validation
│   ├── task_spec.json        # Task contract
│   └── ground_truth.json     # Reference solution
└── reviewers.json            # Metadata: author, reviewer
```

## Task Authoring Steps

1. **Create** — scaffold template with metadata
2. **Write** — instruction.md, environment/Dockerfile
3. **Implement** — test.sh and oracle_checks.py
4. **Validate** — `validate_tasks_preflight.py`
5. **Review** — ensure compliance before inclusion

## Related Skills

- `/audit` — validate task definitions
- `/run` — execute new tasks
- `/evaluate` — score task results
