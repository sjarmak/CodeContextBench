---
name: report
description: Generate evaluation reports, analyze run costs, and compare configurations.
---

# Skill: Reports & Analysis

## Scope

Use this skill when the user asks to:
- Generate comprehensive evaluation reports
- Analyze run costs and spending
- Compare configurations and model performance
- Perform impact analysis (IR, MCP effects)
- Export and visualize results

## Canonical Commands

```bash
# Generate full evaluation report
python3 scripts/maintenance/generate_eval_report.py

# Cost breakdown analysis
python3 scripts/evaluation/cost_report.py --run-dir runs/staging/run_dir

# Cost analysis by model/suite
python3 scripts/evaluation/cost_breakdown_analysis.py --staging

# Compare configurations
python3 scripts/evaluation/compare_configs.py --config1 baseline --config2 sourcegraph_full

# IR analysis (information retrieval)
python3 scripts/evaluation/ir_analysis.py --run-dir runs/staging/run_dir

# Oracle impact analysis
python3 scripts/evaluation/oracle_ir_analysis.py --runs-dir runs/staging
```

## Report Types

- **Evaluation Report** — task-level metrics, pass rates by suite/model
- **Cost Report** — token usage, API calls, infrastructure costs
- **Config Comparison** — baseline vs MCP performance delta
- **Impact Analysis** — retrieval quality and verifier contribution
- **Trend Analysis** — performance over time across runs

## Key Metrics

- **Pass rate** — % tasks passed verification
- **Model success** — % tasks where agent succeeded
- **Cost per task** — average tokens/$ spent
- **Improvement (MCP)** — gain from Sourcegraph integration
- **Verification cost** — dual verification overhead

## Related Skills

- `/evaluate` — extract and score individual task results
- `/run` — generate results to analyze
- `/status` — check run status before generating reports
