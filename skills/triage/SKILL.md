---
name: triage
description: Investigate and triage failed benchmark tasks, analyze root causes, and plan reruns.
---

# Skill: Triage Failures

## Scope

Use this skill when the user asks to:
- Investigate why specific tasks failed
- Categorize failures by type (timeout, OOM, infra, logic)
- Recommend fixes or reruns
- Analyze failure patterns across suites
- Prepare rerun configurations for failed tasks

## Canonical Commands

```bash
# Triage a specific task result
python3 scripts/analysis/status_fingerprints.py runs/staging/run_dir/task_id/result.json

# List all failures in a run with categorization
python3 scripts/analysis/aggregate_status.py --staging --suite csb_sdlc_debug --failures-only

# Deep analysis of error patterns
grep -r "error\|fail\|timeout" runs/staging/run_dir/*/trajectory.json

# Check task logs and stdout
cat runs/staging/run_dir/task_id/agent/solution.md
```

## Failure Categories

- **Timeout** — task exceeded time limit (check time_limit_sec in task.toml)
- **OOM** — out of memory (memory_mb insufficient in task.toml)
- **Infrastructure** — Docker, network, permissions, image pull failures
- **Auth** — OAuth token expired or insufficient scopes
- **Logic** — agent produced wrong output or reference fix incorrect
- **Verification** — test script broken or changed contract

## Rerun Strategy

1. Identify root cause using fingerprints and logs
2. If infrastructure issue: increase timeout or memory, switch environment (Daytona → local)
3. If auth: refresh credentials before rerun
4. If task contract broken: update test.sh or oracle_checks.py
5. Use `/run` skill with `--rerun` flag or custom selection file

## Related Skills

- `/run` — execute reruns after diagnosis
- `/status` — see current failure overview
- `/evaluate` — deep analysis of task outputs
