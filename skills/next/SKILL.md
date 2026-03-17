---
name: next
description: Plan upcoming work, analyze coverage gaps, and recommend next steps for benchmarking.
---

# Skill: What's Next / Planning

## Scope

Use this skill when the user asks to:
- Identify what benchmarking work should happen next
- Analyze coverage gaps and incomplete suites
- Plan variance runs and gap-fill campaigns
- Recommend task categories to focus on
- Generate next-step recommendations based on current state

## Canonical Commands

```bash
# Overall readiness assessment
python3 scripts/infra/check_infra.py

# Current run status and coverage
python3 scripts/analysis/aggregate_status.py --staging

# Gap analysis (missing suites/configs)
grep -r "missing\|incomplete" runs/staging/*/result.json | head -20

# Plan variance runs
python3 scripts/analysis/plan_variance_runs.py --target 50 --dry-run

# Coverage gap analysis
python3 scripts/analysis/analyze_run_coverage.py --runs-dir runs/staging
```

## Planning Workflow

1. **Assess current state** — status, completion rates, failures
2. **Identify gaps** — missing suites, configurations, models
3. **Categorize work** — high-priority, medium, low-priority next steps
4. **Estimate effort** — time, resources, dependencies
5. **Recommend** — specific run commands and configurations

## Gap Analysis Dimensions

- **Suite coverage** — which suites are incomplete?
- **Configuration** — missing baseline, MCP, or paired runs?
- **Model coverage** — which models need testing?
- **Environment** — Daytona vs local Docker?
- **Rerun strategy** — which failures should be retried?

## Variance Planning

- **Power analysis** — how many runs for statistical significance?
- **Rebalancing** — equalize difficulty across runs
- **DOE (Design of Experiments)** — optimize run selection
- **Gap-fill** — targeted runs to complete coverage

## Related Skills

- `/status` — check current completion state
- `/run` — execute next steps
- `/audit` — validate readiness for next phase
