# ccb_pytorch

## Run/Config Summary

| Run | Config | Valid Tasks | Mean Reward | Pass Rate |
|---|---|---:|---:|---:|
| [pytorch_gapfill_opus_20260205_040301](../runs/pytorch_gapfill_opus_20260205_040301.md) | `baseline` | 1 | 1.000 | 1.000 |
| [pytorch_gapfill_opus_20260205_040301](../runs/pytorch_gapfill_opus_20260205_040301.md) | `sourcegraph_full` | 2 | 1.000 | 1.000 |
| [pytorch_opus_20260203_160607](../runs/pytorch_opus_20260203_160607.md) | `baseline` | 4 | 1.000 | 1.000 |
| [pytorch_opus_20260203_160607](../runs/pytorch_opus_20260203_160607.md) | `sourcegraph_full` | 1 | 1.000 | 1.000 |
| [pytorch_opus_20260204_133210](../runs/pytorch_opus_20260204_133210.md) | `baseline` | 4 | 1.000 | 1.000 |
| [pytorch_opus_20260204_133210](../runs/pytorch_opus_20260204_133210.md) | `sourcegraph_full` | 2 | 1.000 | 1.000 |
| [pytorch_opus_20260205_192410](../runs/pytorch_opus_20260205_192410.md) | `baseline` | 1 | 0.000 | 0.000 |
| [pytorch_opus_20260205_204033](../runs/pytorch_opus_20260205_204033.md) | `baseline` | 4 | 0.000 | 0.000 |
| [pytorch_opus_20260205_204033](../runs/pytorch_opus_20260205_204033.md) | `sourcegraph_base` | 12 | 0.080 | 0.083 |
| [pytorch_opus_20260205_204033](../runs/pytorch_opus_20260205_204033.md) | `sourcegraph_full` | 8 | 0.120 | 0.125 |

## Tasks

| Task | Benchmark | Config | Status | Reward | Passed | Scorer Family | Output Contract | Runs | MCP Ratio |
|---|---|---|---|---:|---|---|---|---:|---:|
| [sgt-001](../tasks/pytorch_opus_20260205_192410--baseline--sgt-001--fee1c05dce.html) | — | `baseline` | `failed` | 0.000 | `False` | `-` | `-` | 1 | 0.000 |
| [sgt-001](../tasks/pytorch_opus_20260205_204033--sourcegraph_base--sgt-001--61210442d5.html) | — | `sourcegraph_base` | `failed` | 0.000 | `False` | `-` | `-` | 2 | 0.057 |
| [sgt-001](../tasks/pytorch_opus_20260205_204033--sourcegraph_full--sgt-001--437a901e5f.html) | — | `sourcegraph_full` | `failed` | 0.000 | `False` | `-` | `-` | 1 | 0.119 |
| [sgt-002](../tasks/pytorch_opus_20260203_160607--baseline--sgt-002--9e38c7b796.html) | — | `baseline` | `passed` | 1.000 | `True` | `-` | `-` | 1 | 0.000 |
| [sgt-002](../tasks/pytorch_opus_20260205_204033--sourcegraph_base--sgt-002--4cd88c0387.html) | — | `sourcegraph_base` | `passed` | 0.956 | `True` | `-` | `-` | 2 | 0.104 |
| [sgt-002](../tasks/pytorch_opus_20260205_204033--sourcegraph_full--sgt-002--a6267d61f3.html) | — | `sourcegraph_full` | `passed` | 0.960 | `True` | `-` | `-` | 1 | 0.183 |
| [sgt-003](../tasks/pytorch_opus_20260203_160607--baseline--sgt-003--5e8ec338ed.html) | — | `baseline` | `passed` | 1.000 | `True` | `-` | `-` | 1 | 0.000 |
| [sgt-003](../tasks/pytorch_opus_20260205_204033--sourcegraph_base--sgt-003--5d352f4e40.html) | — | `sourcegraph_base` | `failed` | 0.000 | `False` | `-` | `-` | 1 | 0.312 |
| [sgt-003](../tasks/pytorch_opus_20260205_204033--sourcegraph_full--sgt-003--8714caea71.html) | — | `sourcegraph_full` | `failed` | 0.000 | `False` | `-` | `-` | 1 | 0.183 |
| [sgt-005](../tasks/pytorch_opus_20260204_133210--baseline--sgt-005--08ebab02f2.html) | — | `baseline` | `passed` | 1.000 | `True` | `-` | `-` | 1 | 0.000 |
| [sgt-005](../tasks/pytorch_opus_20260205_204033--sourcegraph_base--sgt-005--d8d2cae643.html) | — | `sourcegraph_base` | `failed` | 0.000 | `False` | `-` | `-` | 2 | 0.200 |
| [sgt-005](../tasks/pytorch_opus_20260205_204033--sourcegraph_full--sgt-005--90b45181e0.html) | — | `sourcegraph_full` | `failed` | 0.000 | `False` | `-` | `-` | 2 | 0.171 |
| [sgt-007](../tasks/pytorch_gapfill_opus_20260205_040301--baseline--sgt-007--6bcd8ef599.html) | — | `baseline` | `passed` | 1.000 | `True` | `-` | `-` | 1 | 0.000 |
| [sgt-007](../tasks/pytorch_opus_20260205_204033--sourcegraph_base--sgt-007--9ac8d58ac2.html) | — | `sourcegraph_base` | `failed` | 0.000 | `False` | `-` | `-` | 2 | 0.222 |
| [sgt-007](../tasks/pytorch_opus_20260205_204033--sourcegraph_full--sgt-007--7328147729.html) | — | `sourcegraph_full` | `failed` | 0.000 | `False` | `-` | `-` | 2 | 0.348 |
| [sgt-008](../tasks/pytorch_opus_20260204_133210--baseline--sgt-008--ecd34aca50.html) | — | `baseline` | `passed` | 1.000 | `True` | `-` | `-` | 1 | 0.000 |
| [sgt-008](../tasks/pytorch_opus_20260204_133210--sourcegraph_full--sgt-008--6107c2c2a6.html) | — | `sourcegraph_full` | `passed` | 1.000 | `True` | `-` | `-` | 1 | 0.125 |
| [sgt-009](../tasks/pytorch_opus_20260204_133210--baseline--sgt-009--85ca8e56f0.html) | — | `baseline` | `passed` | 1.000 | `True` | `-` | `-` | 1 | 0.000 |
| [sgt-009](../tasks/pytorch_opus_20260205_204033--sourcegraph_base--sgt-009--923d143c57.html) | — | `sourcegraph_base` | `failed` | 0.000 | `False` | `-` | `-` | 2 | 0.080 |
| [sgt-009](../tasks/pytorch_opus_20260205_204033--sourcegraph_full--sgt-009--22f26b2a86.html) | — | `sourcegraph_full` | `failed` | 0.000 | `False` | `-` | `-` | 2 | 0.170 |
| [sgt-010](../tasks/pytorch_opus_20260204_133210--baseline--sgt-010--a6dc324695.html) | — | `baseline` | `passed` | 1.000 | `True` | `-` | `-` | 1 | 0.000 |
| [sgt-010](../tasks/pytorch_opus_20260205_204033--sourcegraph_base--sgt-010--e15c06c864.html) | — | `sourcegraph_base` | `failed` | 0.000 | `False` | `-` | `-` | 2 | 0.107 |
| [sgt-010](../tasks/pytorch_opus_20260205_204033--sourcegraph_full--sgt-010--89c65a2fa2.html) | — | `sourcegraph_full` | `failed` | 0.000 | `False` | `-` | `-` | 2 | 0.222 |
| [sgt-012](../tasks/pytorch_opus_20260203_160607--baseline--sgt-012--6b0fdf0254.html) | — | `baseline` | `passed` | 1.000 | `True` | `-` | `-` | 1 | 0.000 |
| [sgt-012](../tasks/pytorch_opus_20260203_160607--sourcegraph_full--sgt-012--04bbbab120.html) | — | `sourcegraph_full` | `passed` | 1.000 | `True` | `-` | `-` | 1 | 0.125 |
| [sgt-014](../tasks/pytorch_opus_20260203_160607--baseline--sgt-014--582285925f.html) | — | `baseline` | `passed` | 1.000 | `True` | `-` | `-` | 1 | 0.000 |
| [sgt-014](../tasks/pytorch_opus_20260205_204033--sourcegraph_base--sgt-014--3f3065f42e.html) | — | `sourcegraph_base` | `failed` | 0.000 | `False` | `-` | `-` | 1 | 0.123 |
| [sgt-014](../tasks/pytorch_opus_20260205_204033--sourcegraph_full--sgt-014--ad888edce8.html) | — | `sourcegraph_full` | `failed` | 0.000 | `False` | `-` | `-` | 1 | 0.127 |
| [sgt-016](../tasks/pytorch_opus_20260205_204033--baseline--sgt-016--57e7132dd2.html) | — | `baseline` | `failed` | 0.000 | `False` | `-` | `-` | 2 | 0.000 |
| [sgt-016](../tasks/pytorch_opus_20260205_204033--sourcegraph_base--sgt-016--624d198134.html) | — | `sourcegraph_base` | `failed` | 0.000 | `False` | `-` | `-` | 2 | 0.305 |
| [sgt-016](../tasks/pytorch_opus_20260204_133210--sourcegraph_full--sgt-016--4873c0aedf.html) | — | `sourcegraph_full` | `passed` | 1.000 | `True` | `-` | `-` | 1 | 0.271 |
| [sgt-017](../tasks/pytorch_opus_20260205_204033--baseline--sgt-017--20a8b40919.html) | — | `baseline` | `failed` | 0.000 | `False` | `-` | `-` | 2 | 0.000 |
| [sgt-017](../tasks/pytorch_opus_20260205_204033--sourcegraph_base--sgt-017--b6072d74f7.html) | — | `sourcegraph_base` | `failed` | 0.000 | `False` | `-` | `-` | 2 | 0.276 |
| [sgt-017](../tasks/pytorch_gapfill_opus_20260205_040301--sourcegraph_full--sgt-017--dd833ee351.html) | — | `sourcegraph_full` | `passed` | 1.000 | `True` | `-` | `-` | 1 | 0.220 |
| [sgt-021](../tasks/pytorch_opus_20260205_204033--baseline--sgt-021--6b5d721eda.html) | — | `baseline` | `failed` | 0.000 | `False` | `-` | `-` | 1 | 0.000 |
| [sgt-021](../tasks/pytorch_opus_20260205_204033--sourcegraph_base--sgt-021--36ab4f338f.html) | — | `sourcegraph_base` | `failed` | 0.000 | `False` | `-` | `-` | 1 | 0.146 |
| [sgt-024](../tasks/pytorch_opus_20260205_204033--baseline--sgt-024--5fa51851b1.html) | — | `baseline` | `failed` | 0.000 | `False` | `-` | `-` | 2 | 0.000 |
| [sgt-024](../tasks/pytorch_opus_20260205_204033--sourcegraph_base--sgt-024--409ae1b160.html) | — | `sourcegraph_base` | `failed` | 0.000 | `False` | `-` | `-` | 2 | 0.476 |
| [sgt-024](../tasks/pytorch_gapfill_opus_20260205_040301--sourcegraph_full--sgt-024--5b670ef812.html) | — | `sourcegraph_full` | `passed` | 1.000 | `True` | `-` | `-` | 1 | 0.190 |

## Multi-Run Variance

Tasks with multiple valid runs (15 task/config pairs).

| Task | Benchmark | Config | Runs | Mean | Std | Individual Rewards |
|---|---|---|---:|---:|---:|---|
| sgt-001 | — | `sourcegraph_base` | 2 | 0.000 | 0.000 | 0.000, 0.000 |
| sgt-002 | — | `sourcegraph_base` | 2 | 0.978 | 0.031 | 1.000, 0.956 |
| sgt-005 | — | `sourcegraph_base` | 2 | 0.500 | 0.707 | 1.000, 0.000 |
| sgt-007 | — | `sourcegraph_base` | 2 | 0.500 | 0.707 | 1.000, 0.000 |
| sgt-007 | — | `sourcegraph_full` | 2 | 0.500 | 0.707 | 1.000, 0.000 |
| sgt-009 | — | `sourcegraph_base` | 2 | 0.500 | 0.707 | 1.000, 0.000 |
| sgt-009 | — | `sourcegraph_full` | 2 | 0.500 | 0.707 | 1.000, 0.000 |
| sgt-010 | — | `sourcegraph_base` | 2 | 0.500 | 0.707 | 1.000, 0.000 |
| sgt-010 | — | `sourcegraph_full` | 2 | 0.500 | 0.707 | 1.000, 0.000 |
| sgt-016 | — | `baseline` | 2 | 0.500 | 0.707 | 1.000, 0.000 |
| sgt-016 | — | `sourcegraph_base` | 2 | 0.500 | 0.707 | 1.000, 0.000 |
| sgt-017 | — | `baseline` | 2 | 0.500 | 0.707 | 1.000, 0.000 |
| sgt-017 | — | `sourcegraph_base` | 2 | 0.500 | 0.707 | 1.000, 0.000 |
| sgt-024 | — | `baseline` | 2 | 0.500 | 0.707 | 1.000, 0.000 |
| sgt-024 | — | `sourcegraph_base` | 2 | 0.500 | 0.707 | 1.000, 0.000 |
