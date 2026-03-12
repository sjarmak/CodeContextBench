# ccb_linuxflbench

## Run/Config Summary

| Run | Config | Valid Tasks | Mean Reward | Pass Rate |
|---|---|---:|---:|---:|
| [linuxflbench_opus_20260206_164001__doubled_prefix](../runs/linuxflbench_opus_20260206_164001__doubled_prefix.md) | `sourcegraph_base` | 5 | 0.740 | 1.000 |
| [linuxflbench_opus_20260206_180131__doubled_prefix_ds_compromised](../runs/linuxflbench_opus_20260206_180131__doubled_prefix_ds_compromised.md) | `sourcegraph_full` | 5 | 0.860 | 1.000 |

## Tasks

| Task | Benchmark | Config | Status | Reward | Passed | Scorer Family | Output Contract | Runs | MCP Ratio |
|---|---|---|---|---:|---|---|---|---:|---:|
| [lfl-acpi-207835](../tasks/linuxflbench_opus_20260206_164001__doubled_prefix--sourcegraph_base--lfl-acpi-207835--1b931cee38.html) | — | `sourcegraph_base` | `passed` | 1.000 | `True` | `-` | `-` | 1 | 0.308 |
| [lfl-acpi-207835](../tasks/linuxflbench_opus_20260206_180131__doubled_prefix_ds_compromised--sourcegraph_full--lfl-acpi-207835--9cc23b43cb.html) | — | `sourcegraph_full` | `passed` | 1.000 | `True` | `-` | `-` | 3 | 0.647 |
| [lfl-nfs-117651](../tasks/linuxflbench_opus_20260206_164001__doubled_prefix--sourcegraph_base--lfl-nfs-117651--7da2a73fec.html) | — | `sourcegraph_base` | `passed` | 0.300 | `True` | `-` | `-` | 1 | 0.055 |
| [lfl-nfs-117651](../tasks/linuxflbench_opus_20260206_180131__doubled_prefix_ds_compromised--sourcegraph_full--lfl-nfs-117651--dd70e6a809.html) | — | `sourcegraph_full` | `passed` | 0.300 | `True` | `-` | `-` | 1 | 0.305 |
| [lfl-sata-203475](../tasks/linuxflbench_opus_20260206_164001__doubled_prefix--sourcegraph_base--lfl-sata-203475--a68b0b9795.html) | — | `sourcegraph_base` | `passed` | 1.000 | `True` | `-` | `-` | 1 | 0.375 |
| [lfl-sata-203475](../tasks/linuxflbench_opus_20260206_180131__doubled_prefix_ds_compromised--sourcegraph_full--lfl-sata-203475--80a90dae7d.html) | — | `sourcegraph_full` | `passed` | 1.000 | `True` | `-` | `-` | 1 | 0.520 |
| [lfl-sound-53441](../tasks/linuxflbench_opus_20260206_164001__doubled_prefix--sourcegraph_base--lfl-sound-53441--b8d7dfba19.html) | — | `sourcegraph_base` | `passed` | 0.700 | `True` | `-` | `-` | 1 | 0.055 |
| [lfl-sound-53441](../tasks/linuxflbench_opus_20260206_180131__doubled_prefix_ds_compromised--sourcegraph_full--lfl-sound-53441--8d68bfb997.html) | — | `sourcegraph_full` | `passed` | 1.000 | `True` | `-` | `-` | 1 | 0.143 |
| [lfl-wifi-206661](../tasks/linuxflbench_opus_20260206_164001__doubled_prefix--sourcegraph_base--lfl-wifi-206661--263dc192fe.html) | — | `sourcegraph_base` | `passed` | 0.700 | `True` | `-` | `-` | 1 | 0.350 |
| [lfl-wifi-206661](../tasks/linuxflbench_opus_20260206_180131__doubled_prefix_ds_compromised--sourcegraph_full--lfl-wifi-206661--0989a34031.html) | — | `sourcegraph_full` | `passed` | 1.000 | `True` | `-` | `-` | 2 | 0.423 |

## Multi-Run Variance

Tasks with multiple valid runs (2 task/config pairs).

| Task | Benchmark | Config | Runs | Mean | Std | Individual Rewards |
|---|---|---|---:|---:|---:|---|
| lfl-acpi-207835 | — | `sourcegraph_full` | 3 | 1.000 | 0.000 | 1.000, 1.000, 1.000 |
| lfl-wifi-206661 | — | `sourcegraph_full` | 2 | 1.000 | 0.000 | 1.000, 1.000 |
