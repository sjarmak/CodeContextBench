# ccb_tac

## Run/Config Summary

| Run | Config | Valid Tasks | Mean Reward | Pass Rate |
|---|---|---:|---:|---:|
| [tac_opus_20260203_160607](../runs/tac_opus_20260203_160607.md) | `baseline` | 2 | 0.000 | 0.000 |
| [tac_opus_20260203_221123__python_default_bug](../runs/tac_opus_20260203_221123__python_default_bug.md) | `sourcegraph_base` | 6 | 0.000 | 0.000 |
| [tac_opus_20260204_190539](../runs/tac_opus_20260204_190539.md) | `sourcegraph_full` | 2 | 0.000 | 0.000 |
| [tac_opus_20260205_010555__python_default_bug](../runs/tac_opus_20260205_010555__python_default_bug.md) | `baseline` | 6 | 0.000 | 0.000 |

## Tasks

| Task | Benchmark | Config | Status | Reward | Passed | Scorer Family | Output Contract | Runs | MCP Ratio |
|---|---|---|---|---:|---|---|---|---:|---:|
| [tac-buffer-pool-manager](../tasks/tac_opus_20260205_010555__python_default_bug--baseline--tac-buffer-pool-manager--62bd306a63.html) | — | `baseline` | `failed` | 0.000 | `None` | `-` | `-` | 2 | 0.000 |
| [tac-buffer-pool-manager](../tasks/tac_opus_20260203_221123__python_default_bug--sourcegraph_base--tac-buffer-pool-manager--0eff3fe0e2.html) | — | `sourcegraph_base` | `failed` | 0.000 | `False` | `-` | `-` | 1 | 0.037 |
| [tac-copilot-arena-endpoint](../tasks/tac_opus_20260203_160607--baseline--tac-copilot-arena-endpoint--77e0bd10ad.html) | — | `baseline` | `failed` | 0.000 | `False` | `-` | `-` | 1 | 0.000 |
| [tac-copilot-arena-endpoint](../tasks/tac_opus_20260204_190539--sourcegraph_full--tac-copilot-arena-endpoint--33d44b95d7.html) | — | `sourcegraph_full` | `failed` | 0.000 | `False` | `-` | `-` | 1 | 0.051 |
| [tac-dependency-change](../tasks/tac_opus_20260205_010555__python_default_bug--baseline--tac-dependency-change--c19a7a2782.html) | — | `baseline` | `failed` | 0.000 | `None` | `-` | `-` | 2 | 0.000 |
| [tac-dependency-change](../tasks/tac_opus_20260203_221123__python_default_bug--sourcegraph_base--tac-dependency-change--8732cfa747.html) | — | `sourcegraph_base` | `failed` | 0.000 | `False` | `-` | `-` | 1 | 0.096 |
| [tac-find-in-codebase-1](../tasks/tac_opus_20260205_010555__python_default_bug--baseline--tac-find-in-codebase-1--bd63982778.html) | — | `baseline` | `failed` | 0.000 | `None` | `-` | `-` | 2 | 0.000 |
| [tac-find-in-codebase-1](../tasks/tac_opus_20260203_221123__python_default_bug--sourcegraph_base--tac-find-in-codebase-1--fb0e32ce2e.html) | — | `sourcegraph_base` | `failed` | 0.000 | `False` | `-` | `-` | 1 | 0.042 |
| [tac-find-in-codebase-2](../tasks/tac_opus_20260205_010555__python_default_bug--baseline--tac-find-in-codebase-2--51246daeb5.html) | — | `baseline` | `failed` | 0.000 | `None` | `-` | `-` | 2 | 0.000 |
| [tac-find-in-codebase-2](../tasks/tac_opus_20260203_221123__python_default_bug--sourcegraph_base--tac-find-in-codebase-2--ae7b6a8702.html) | — | `sourcegraph_base` | `failed` | 0.000 | `False` | `-` | `-` | 1 | 0.133 |
| [tac-implement-hyperloglog](../tasks/tac_opus_20260205_010555__python_default_bug--baseline--tac-implement-hyperloglog--73728f4d80.html) | — | `baseline` | `failed` | 0.000 | `None` | `-` | `-` | 2 | 0.000 |
| [tac-implement-hyperloglog](../tasks/tac_opus_20260203_221123__python_default_bug--sourcegraph_base--tac-implement-hyperloglog--2b8dad2111.html) | — | `sourcegraph_base` | `failed` | 0.000 | `False` | `-` | `-` | 1 | 0.131 |
| [tac-troubleshoot-dev-setup](../tasks/tac_opus_20260203_160607--baseline--tac-troubleshoot-dev-setup--3de82e5df8.html) | — | `baseline` | `failed` | 0.000 | `False` | `-` | `-` | 1 | 0.000 |
| [tac-troubleshoot-dev-setup](../tasks/tac_opus_20260204_190539--sourcegraph_full--tac-troubleshoot-dev-setup--fbd09a8ead.html) | — | `sourcegraph_full` | `failed` | 0.000 | `False` | `-` | `-` | 1 | 0.120 |
| [tac-write-unit-test](../tasks/tac_opus_20260205_010555__python_default_bug--baseline--tac-write-unit-test--626f455291.html) | — | `baseline` | `failed` | 0.000 | `None` | `-` | `-` | 2 | 0.000 |
| [tac-write-unit-test](../tasks/tac_opus_20260203_221123__python_default_bug--sourcegraph_base--tac-write-unit-test--305ec1b266.html) | — | `sourcegraph_base` | `failed` | 0.000 | `False` | `-` | `-` | 1 | 0.129 |

## Multi-Run Variance

Tasks with multiple valid runs (6 task/config pairs).

| Task | Benchmark | Config | Runs | Mean | Std | Individual Rewards |
|---|---|---|---:|---:|---:|---|
| tac-buffer-pool-manager | — | `baseline` | 2 | 0.000 | 0.000 | 0.000, 0.000 |
| tac-dependency-change | — | `baseline` | 2 | 0.000 | 0.000 | 0.000, 0.000 |
| tac-find-in-codebase-1 | — | `baseline` | 2 | 0.000 | 0.000 | 0.000, 0.000 |
| tac-find-in-codebase-2 | — | `baseline` | 2 | 0.000 | 0.000 | 0.000, 0.000 |
| tac-implement-hyperloglog | — | `baseline` | 2 | 0.000 | 0.000 | 0.000, 0.000 |
| tac-write-unit-test | — | `baseline` | 2 | 0.000 | 0.000 | 0.000, 0.000 |
