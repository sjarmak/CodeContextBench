# ccb_crossrepo

## Run/Config Summary

| Run | Config | Valid Tasks | Mean Reward | Pass Rate |
|---|---|---:|---:|---:|
| [crossrepo_opus_20260202_204733](../runs/crossrepo_opus_20260202_204733.md) | `sourcegraph_full` | 2 | 0.000 | 0.000 |
| [crossrepo_opus_20260203_160607](../runs/crossrepo_opus_20260203_160607.md) | `baseline` | 1 | 1.000 | 1.000 |
| [crossrepo_opus_20260204_133742__verifier_path_bug](../runs/crossrepo_opus_20260204_133742__verifier_path_bug.md) | `baseline` | 4 | 0.000 | 0.000 |
| [crossrepo_opus_20260204_133742__verifier_path_bug](../runs/crossrepo_opus_20260204_133742__verifier_path_bug.md) | `sourcegraph_base` | 4 | 0.000 | 0.000 |

## Tasks

| Task | Benchmark | Config | Status | Reward | Passed | Scorer Family | Output Contract | Runs | MCP Ratio |
|---|---|---|---|---:|---|---|---|---:|---:|
| [api_upgrade_01](../tasks/crossrepo_opus_20260204_133742__verifier_path_bug--baseline--api_upgrade_01--f49a44a8b3.html) | — | `baseline` | `failed` | 0.000 | `False` | `-` | `-` | 2 | 0.000 |
| [api_upgrade_01](../tasks/crossrepo_opus_20260204_133742__verifier_path_bug--sourcegraph_base--api_upgrade_01--040fe703ce.html) | — | `sourcegraph_base` | `failed` | 0.000 | `False` | `-` | `-` | 1 | 0.061 |
| [bug_localization_01](../tasks/crossrepo_opus_20260204_133742__verifier_path_bug--baseline--bug_localization_01--824c15a53c.html) | — | `baseline` | `failed` | 0.000 | `False` | `-` | `-` | 2 | 0.000 |
| [bug_localization_01](../tasks/crossrepo_opus_20260204_133742__verifier_path_bug--sourcegraph_base--bug_localization_01--91fe32eb4e.html) | — | `sourcegraph_base` | `failed` | 0.000 | `False` | `-` | `-` | 1 | 0.425 |
| [bug_localization_01](../tasks/crossrepo_opus_20260202_204733--sourcegraph_full--bug_localization_01--2003e945b9.html) | — | `sourcegraph_full` | `failed` | 0.000 | `None` | `-` | `-` | 1 | 0.388 |
| [cross_file_reasoning_01](../tasks/crossrepo_opus_20260204_133742__verifier_path_bug--baseline--cross_file_reasoning_01--9ac976e826.html) | — | `baseline` | `failed` | 0.000 | `False` | `-` | `-` | 2 | 0.000 |
| [cross_file_reasoning_01](../tasks/crossrepo_opus_20260204_133742__verifier_path_bug--sourcegraph_base--cross_file_reasoning_01--a2fd779457.html) | — | `sourcegraph_base` | `failed` | 0.000 | `False` | `-` | `-` | 1 | 0.667 |
| [cross_file_reasoning_01](../tasks/crossrepo_opus_20260202_204733--sourcegraph_full--cross_file_reasoning_01--f8f6ac4a40.html) | — | `sourcegraph_full` | `failed` | 0.000 | `None` | `-` | `-` | 1 | 0.793 |
| [refactor_rename_01](../tasks/crossrepo_opus_20260204_133742__verifier_path_bug--baseline--refactor_rename_01--59c563a0d7.html) | — | `baseline` | `failed` | 0.000 | `False` | `-` | `-` | 2 | 0.000 |
| [refactor_rename_01](../tasks/crossrepo_opus_20260204_133742__verifier_path_bug--sourcegraph_base--refactor_rename_01--09e157d09b.html) | — | `sourcegraph_base` | `failed` | 0.000 | `False` | `-` | `-` | 1 | 0.333 |
| [simple_test_01](../tasks/crossrepo_opus_20260203_160607--baseline--simple_test_01--a247e01964.html) | — | `baseline` | `passed` | 1.000 | `True` | `-` | `-` | 2 | 0.000 |

## Multi-Run Variance

Tasks with multiple valid runs (6 task/config pairs).

| Task | Benchmark | Config | Runs | Mean | Std | Individual Rewards |
|---|---|---|---:|---:|---:|---|
| api_upgrade_01 | — | `baseline` | 2 | 0.000 | 0.000 | 0.000, 0.000 |
| bug_localization_01 | — | `baseline` | 2 | 0.000 | 0.000 | 0.000, 0.000 |
| cross_file_reasoning_01 | — | `baseline` | 2 | 0.000 | 0.000 | 0.000, 0.000 |
| refactor_rename_01 | — | `baseline` | 2 | 0.000 | 0.000 | 0.000, 0.000 |
| simple_test_01 | — | `baseline` | 2 | 1.000 | 0.000 | 1.000, 1.000 |
| simple_test_01 | — | `sourcegraph_full` | 2 | 1.000 | 0.000 | 1.000, 1.000 |
