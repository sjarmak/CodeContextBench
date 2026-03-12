# ccb_investigation

## Run/Config Summary

| Run | Config | Valid Tasks | Mean Reward | Pass Rate |
|---|---|---:|---:|---:|
| [investigation_haiku_20260207_150959](../runs/investigation_haiku_20260207_150959.md) | `baseline` | 1 | 1.000 | 1.000 |
| [investigation_haiku_20260207_150959](../runs/investigation_haiku_20260207_150959.md) | `sourcegraph_base` | 1 | 0.900 | 1.000 |
| [investigation_haiku_20260207_150959](../runs/investigation_haiku_20260207_150959.md) | `sourcegraph_full` | 1 | 1.000 | 1.000 |
| [investigation_haiku_20260207_151000](../runs/investigation_haiku_20260207_151000.md) | `baseline` | 1 | 1.000 | 1.000 |
| [investigation_haiku_20260207_151000](../runs/investigation_haiku_20260207_151000.md) | `sourcegraph_base` | 1 | 0.700 | 1.000 |
| [investigation_haiku_20260207_151000](../runs/investigation_haiku_20260207_151000.md) | `sourcegraph_full` | 1 | 0.700 | 1.000 |
| [investigation_haiku_20260207_151001](../runs/investigation_haiku_20260207_151001.md) | `baseline` | 1 | 0.880 | 1.000 |
| [investigation_haiku_20260207_151001](../runs/investigation_haiku_20260207_151001.md) | `sourcegraph_base` | 1 | 0.380 | 1.000 |
| [investigation_haiku_20260207_151001](../runs/investigation_haiku_20260207_151001.md) | `sourcegraph_full` | 1 | 0.840 | 1.000 |
| [investigation_haiku_20260207_151002](../runs/investigation_haiku_20260207_151002.md) | `baseline` | 1 | 1.000 | 1.000 |
| [investigation_haiku_20260207_151002](../runs/investigation_haiku_20260207_151002.md) | `sourcegraph_base` | 1 | 1.000 | 1.000 |
| [investigation_haiku_20260207_151002](../runs/investigation_haiku_20260207_151002.md) | `sourcegraph_full` | 1 | 1.000 | 1.000 |

## Tasks

| Task | Benchmark | Config | Status | Reward | Passed | Scorer Family | Output Contract | Runs | MCP Ratio |
|---|---|---|---|---:|---|---|---|---:|---:|
| [inv-debug-001](../tasks/investigation_haiku_20260207_151001--baseline--inv-debug-001--87a4241422.html) | — | `baseline` | `passed` | 0.880 | `True` | `-` | `-` | 2 | 0.000 |
| [inv-debug-001](../tasks/investigation_haiku_20260207_151001--sourcegraph_base--inv-debug-001--0c1a99696c.html) | — | `sourcegraph_base` | `passed` | 0.380 | `True` | `-` | `-` | 2 | 0.515 |
| [inv-debug-001](../tasks/investigation_haiku_20260207_151001--sourcegraph_full--inv-debug-001--34d07a14eb.html) | — | `sourcegraph_full` | `passed` | 0.840 | `True` | `-` | `-` | 2 | 0.944 |
| [inv-impact-001](../tasks/investigation_haiku_20260207_150959--baseline--inv-impact-001--9de33b2e99.html) | — | `baseline` | `passed` | 1.000 | `True` | `-` | `-` | 2 | 0.000 |
| [inv-impact-001](../tasks/investigation_haiku_20260207_150959--sourcegraph_base--inv-impact-001--1a0c9ca14b.html) | — | `sourcegraph_base` | `passed` | 0.900 | `True` | `-` | `-` | 2 | 0.970 |
| [inv-impact-001](../tasks/investigation_haiku_20260207_150959--sourcegraph_full--inv-impact-001--033354eab6.html) | — | `sourcegraph_full` | `passed` | 1.000 | `True` | `-` | `-` | 2 | 0.960 |
| [inv-migration-001](../tasks/investigation_haiku_20260207_151002--baseline--inv-migration-001--af5cebf446.html) | — | `baseline` | `passed` | 1.000 | `True` | `-` | `-` | 2 | 0.000 |
| [inv-migration-001](../tasks/investigation_haiku_20260207_151002--sourcegraph_base--inv-migration-001--78fc704fbf.html) | — | `sourcegraph_base` | `passed` | 1.000 | `True` | `-` | `-` | 2 | 0.889 |
| [inv-migration-001](../tasks/investigation_haiku_20260207_151002--sourcegraph_full--inv-migration-001--47ca1b599c.html) | — | `sourcegraph_full` | `passed` | 1.000 | `True` | `-` | `-` | 2 | 0.969 |
| [inv-regression-001](../tasks/investigation_haiku_20260207_151000--baseline--inv-regression-001--d711cac1b3.html) | — | `baseline` | `passed` | 1.000 | `True` | `-` | `-` | 2 | 0.000 |
| [inv-regression-001](../tasks/investigation_haiku_20260207_151000--sourcegraph_base--inv-regression-001--bbbbf6747a.html) | — | `sourcegraph_base` | `passed` | 0.700 | `True` | `-` | `-` | 2 | 0.810 |
| [inv-regression-001](../tasks/investigation_haiku_20260207_151000--sourcegraph_full--inv-regression-001--54d9d490fa.html) | — | `sourcegraph_full` | `passed` | 0.700 | `True` | `-` | `-` | 2 | 0.808 |

## Multi-Run Variance

Tasks with multiple valid runs (12 task/config pairs).

| Task | Benchmark | Config | Runs | Mean | Std | Individual Rewards |
|---|---|---|---:|---:|---:|---|
| inv-debug-001 | — | `baseline` | 2 | 0.910 | 0.042 | 0.940, 0.880 |
| inv-debug-001 | — | `sourcegraph_base` | 2 | 0.660 | 0.396 | 0.940, 0.380 |
| inv-debug-001 | — | `sourcegraph_full` | 2 | 0.890 | 0.071 | 0.940, 0.840 |
| inv-impact-001 | — | `baseline` | 2 | 0.960 | 0.057 | 0.920, 1.000 |
| inv-impact-001 | — | `sourcegraph_base` | 2 | 0.950 | 0.071 | 1.000, 0.900 |
| inv-impact-001 | — | `sourcegraph_full` | 2 | 0.960 | 0.057 | 0.920, 1.000 |
| inv-migration-001 | — | `baseline` | 2 | 1.000 | 0.000 | 1.000, 1.000 |
| inv-migration-001 | — | `sourcegraph_base` | 2 | 1.000 | 0.000 | 1.000, 1.000 |
| inv-migration-001 | — | `sourcegraph_full` | 2 | 1.000 | 0.000 | 1.000, 1.000 |
| inv-regression-001 | — | `baseline` | 2 | 0.950 | 0.071 | 0.900, 1.000 |
| inv-regression-001 | — | `sourcegraph_base` | 2 | 0.800 | 0.141 | 0.900, 0.700 |
| inv-regression-001 | — | `sourcegraph_full` | 2 | 0.800 | 0.141 | 0.900, 0.700 |
