# ccb_mcp_incident

## Run/Config Summary

| Run | Config | Valid Tasks | Mean Reward | Pass Rate |
|---|---|---:|---:|---:|
| [ccb_mcp_incident_haiku_022126](../runs/ccb_mcp_incident_haiku_022126.md) | `baseline` | 1 | 0.500 | 1.000 |
| [ccb_mcp_incident_haiku_022126](../runs/ccb_mcp_incident_haiku_022126.md) | `mcp` | 1 | 1.000 | 1.000 |
| [ccb_mcp_incident_haiku_20260224_181919](../runs/ccb_mcp_incident_haiku_20260224_181919.md) | `mcp-remote-artifact` | 3 | 0.782 | 1.000 |
| [ccb_mcp_incident_haiku_20260225_011700](../runs/ccb_mcp_incident_haiku_20260225_011700.md) | `baseline-local-artifact` | 3 | 0.167 | 0.333 |
| [ccb_mcp_incident_haiku_20260226_035617](../runs/ccb_mcp_incident_haiku_20260226_035617.md) | `mcp-remote-direct` | 6 | 0.753 | 1.000 |
| [ccb_mcp_incident_haiku_20260226_035622_variance](../runs/ccb_mcp_incident_haiku_20260226_035622_variance.md) | `mcp-remote-direct` | 6 | 0.632 | 1.000 |
| [ccb_mcp_incident_haiku_20260226_035628_variance](../runs/ccb_mcp_incident_haiku_20260226_035628_variance.md) | `mcp-remote-direct` | 6 | 0.661 | 1.000 |
| [ccb_mcp_incident_haiku_20260226_035633_variance](../runs/ccb_mcp_incident_haiku_20260226_035633_variance.md) | `mcp-remote-direct` | 6 | 0.669 | 1.000 |
| [ccb_mcp_incident_haiku_20260226_205845](../runs/ccb_mcp_incident_haiku_20260226_205845.md) | `baseline-local-direct` | 6 | 0.722 | 1.000 |
| [ccb_mcp_incident_haiku_20260226_224414](../runs/ccb_mcp_incident_haiku_20260226_224414.md) | `baseline-local-direct` | 1 | 0.667 | 1.000 |
| [ccb_mcp_incident_haiku_20260226_224414](../runs/ccb_mcp_incident_haiku_20260226_224414.md) | `mcp-remote-direct` | 1 | 0.800 | 1.000 |

## Tasks

| Task | Benchmark | Config | Status | Reward | Runs | MCP Ratio |
|---|---|---|---|---:|---:|---:|
| [ccx-incident-031](../tasks/ccb_mcp_incident_haiku_022126--baseline--ccx-incident-031.md) | [source](../../benchmarks/ccb_mcp_incident/ccx-incident-031) | `baseline` | `passed` | 0.500 | 1 | 0.000 |
| [ccx-incident-031](../tasks/ccb_mcp_incident_haiku_022126--mcp--ccx-incident-031.md) | [source](../../benchmarks/ccb_mcp_incident/ccx-incident-031) | `mcp` | `passed` | 1.000 | 1 | 0.833 |
| [ccx-incident-032](../tasks/ccb_mcp_incident_haiku_20260226_205845--baseline-local-direct--ccx-incident-032.md) | [source](../../benchmarks/ccb_mcp_incident/ccx-incident-032) | `baseline-local-direct` | `passed` | 0.469 | 1 | 0.000 |
| [mcp_CCX-incident-032_3kc8CS](../tasks/ccb_mcp_incident_haiku_20260226_035617--mcp-remote-direct--mcp_CCX-incident-032_3kc8CS.md) | [source](../../benchmarks/ccb_mcp_incident/ccx-incident-032) | `mcp-remote-direct` | `passed` | 0.494 | 4 | 0.933 |
| [mcp_CCX-incident-032_3wlI0S](../tasks/ccb_mcp_incident_haiku_20260226_035633_variance--mcp-remote-direct--mcp_CCX-incident-032_3wlI0S.md) | [source](../../benchmarks/ccb_mcp_incident/ccx-incident-032) | `mcp-remote-direct` | `passed` | 0.361 | 4 | 0.938 |
| [mcp_CCX-incident-032_UtUNt4](../tasks/ccb_mcp_incident_haiku_20260226_035622_variance--mcp-remote-direct--mcp_CCX-incident-032_UtUNt4.md) | [source](../../benchmarks/ccb_mcp_incident/ccx-incident-032) | `mcp-remote-direct` | `passed` | 0.411 | 4 | 0.938 |
| [mcp_CCX-incident-032_zv1cD1](../tasks/ccb_mcp_incident_haiku_20260226_035628_variance--mcp-remote-direct--mcp_CCX-incident-032_zv1cD1.md) | [source](../../benchmarks/ccb_mcp_incident/ccx-incident-032) | `mcp-remote-direct` | `passed` | 0.415 | 4 | 0.941 |
| [ccx-incident-033](../tasks/ccb_mcp_incident_haiku_20260226_205845--baseline-local-direct--ccx-incident-033.md) | [source](../../benchmarks/ccb_mcp_incident/ccx-incident-033) | `baseline-local-direct` | `passed` | 0.359 | 1 | 0.000 |
| [mcp_CCX-incident-033_L9vdYC](../tasks/ccb_mcp_incident_haiku_20260226_035617--mcp-remote-direct--mcp_CCX-incident-033_L9vdYC.md) | [source](../../benchmarks/ccb_mcp_incident/ccx-incident-033) | `mcp-remote-direct` | `passed` | 0.321 | 4 | 0.938 |
| [mcp_CCX-incident-033_O4gECf](../tasks/ccb_mcp_incident_haiku_20260226_035633_variance--mcp-remote-direct--mcp_CCX-incident-033_O4gECf.md) | [source](../../benchmarks/ccb_mcp_incident/ccx-incident-033) | `mcp-remote-direct` | `passed` | 0.305 | 4 | 0.923 |
| [mcp_CCX-incident-033_5HJK5V](../tasks/ccb_mcp_incident_haiku_20260226_035622_variance--mcp-remote-direct--mcp_CCX-incident-033_5HJK5V.md) | [source](../../benchmarks/ccb_mcp_incident/ccx-incident-033) | `mcp-remote-direct` | `passed` | 0.359 | 4 | 0.875 |
| [mcp_CCX-incident-033_MF5qfV](../tasks/ccb_mcp_incident_haiku_20260226_035628_variance--mcp-remote-direct--mcp_CCX-incident-033_MF5qfV.md) | [source](../../benchmarks/ccb_mcp_incident/ccx-incident-033) | `mcp-remote-direct` | `passed` | 0.274 | 4 | 0.833 |
| [ccx-incident-034](../tasks/ccb_mcp_incident_haiku_20260226_205845--baseline-local-direct--ccx-incident-034.md) | [source](../../benchmarks/ccb_mcp_incident/ccx-incident-034) | `baseline-local-direct` | `passed` | 1.000 | 1 | 0.000 |
| [mcp_ccx-incident-034_89DyXl](../tasks/ccb_mcp_incident_haiku_20260226_035617--mcp-remote-direct--mcp_ccx-incident-034_89DyXl.md) | [source](../../benchmarks/ccb_mcp_incident/ccx-incident-034) | `mcp-remote-direct` | `passed` | 1.000 | 4 | 0.867 |
| [mcp_ccx-incident-034_mfigsf](../tasks/ccb_mcp_incident_haiku_20260226_035633_variance--mcp-remote-direct--mcp_ccx-incident-034_mfigsf.md) | [source](../../benchmarks/ccb_mcp_incident/ccx-incident-034) | `mcp-remote-direct` | `passed` | 1.000 | 4 | 0.923 |
| [mcp_ccx-incident-034_z8JpXN](../tasks/ccb_mcp_incident_haiku_20260226_035622_variance--mcp-remote-direct--mcp_ccx-incident-034_z8JpXN.md) | [source](../../benchmarks/ccb_mcp_incident/ccx-incident-034) | `mcp-remote-direct` | `passed` | 1.000 | 4 | 0.941 |
| [mcp_ccx-incident-034_mAJmrM](../tasks/ccb_mcp_incident_haiku_20260226_035628_variance--mcp-remote-direct--mcp_ccx-incident-034_mAJmrM.md) | [source](../../benchmarks/ccb_mcp_incident/ccx-incident-034) | `mcp-remote-direct` | `passed` | 1.000 | 4 | 0.875 |
| [ccx-incident-037](../tasks/ccb_mcp_incident_haiku_20260226_205845--baseline-local-direct--ccx-incident-037.md) | [source](../../benchmarks/ccb_mcp_incident/ccx-incident-037) | `baseline-local-direct` | `passed` | 0.857 | 1 | 0.000 |
| [mcp_ccx-incident-037_JmTj6j](../tasks/ccb_mcp_incident_haiku_20260226_035617--mcp-remote-direct--mcp_ccx-incident-037_JmTj6j.md) | [source](../../benchmarks/ccb_mcp_incident/ccx-incident-037) | `mcp-remote-direct` | `passed` | 0.933 | 4 | 0.857 |
| [mcp_ccx-incident-037_E9Irt3](../tasks/ccb_mcp_incident_haiku_20260226_035633_variance--mcp-remote-direct--mcp_ccx-incident-037_E9Irt3.md) | [source](../../benchmarks/ccb_mcp_incident/ccx-incident-037) | `mcp-remote-direct` | `passed` | 0.609 | 4 | 0.867 |
| [mcp_ccx-incident-037_4C20SX](../tasks/ccb_mcp_incident_haiku_20260226_035622_variance--mcp-remote-direct--mcp_ccx-incident-037_4C20SX.md) | [source](../../benchmarks/ccb_mcp_incident/ccx-incident-037) | `mcp-remote-direct` | `passed` | 0.733 | 4 | 0.923 |
| [mcp_ccx-incident-037_2kxTW3](../tasks/ccb_mcp_incident_haiku_20260226_035628_variance--mcp-remote-direct--mcp_ccx-incident-037_2kxTW3.md) | [source](../../benchmarks/ccb_mcp_incident/ccx-incident-037) | `mcp-remote-direct` | `passed` | 0.500 | 4 | 0.917 |
| [ccx-incident-108](../tasks/ccb_mcp_incident_haiku_20260226_205845--baseline-local-direct--ccx-incident-108.md) | [source](../../benchmarks/ccb_mcp_incident/ccx-incident-108) | `baseline-local-direct` | `passed` | 0.700 | 1 | 0.000 |
| [mcp_CCX-incident-108_vvAydm](../tasks/ccb_mcp_incident_haiku_20260226_035617--mcp-remote-direct--mcp_CCX-incident-108_vvAydm.md) | [source](../../benchmarks/ccb_mcp_incident/ccx-incident-108) | `mcp-remote-direct` | `passed` | 0.849 | 4 | 0.941 |
| [mcp_CCX-incident-108_Zcemvf](../tasks/ccb_mcp_incident_haiku_20260226_035633_variance--mcp-remote-direct--mcp_CCX-incident-108_Zcemvf.md) | [source](../../benchmarks/ccb_mcp_incident/ccx-incident-108) | `mcp-remote-direct` | `passed` | 0.815 | 4 | 0.952 |
| [mcp_CCX-incident-108_e9YZkb](../tasks/ccb_mcp_incident_haiku_20260226_035622_variance--mcp-remote-direct--mcp_CCX-incident-108_e9YZkb.md) | [source](../../benchmarks/ccb_mcp_incident/ccx-incident-108) | `mcp-remote-direct` | `passed` | 0.367 | 4 | 0.953 |
| [mcp_CCX-incident-108_J2t0WK](../tasks/ccb_mcp_incident_haiku_20260226_035628_variance--mcp-remote-direct--mcp_CCX-incident-108_J2t0WK.md) | [source](../../benchmarks/ccb_mcp_incident/ccx-incident-108) | `mcp-remote-direct` | `passed` | 0.833 | 4 | 0.975 |
| [ccx-incident-110](../tasks/ccb_mcp_incident_haiku_20260226_205845--baseline-local-direct--ccx-incident-110.md) | [source](../../benchmarks/ccb_mcp_incident/ccx-incident-110) | `baseline-local-direct` | `passed` | 0.944 | 1 | 0.000 |
| [mcp_CCX-incident-110_XxCjSw](../tasks/ccb_mcp_incident_haiku_20260226_035617--mcp-remote-direct--mcp_CCX-incident-110_XxCjSw.md) | [source](../../benchmarks/ccb_mcp_incident/ccx-incident-110) | `mcp-remote-direct` | `passed` | 0.923 | 4 | 0.889 |
| [mcp_CCX-incident-110_J8YtzN](../tasks/ccb_mcp_incident_haiku_20260226_035633_variance--mcp-remote-direct--mcp_CCX-incident-110_J8YtzN.md) | [source](../../benchmarks/ccb_mcp_incident/ccx-incident-110) | `mcp-remote-direct` | `passed` | 0.923 | 4 | 0.923 |
| [mcp_CCX-incident-110_A90zfo](../tasks/ccb_mcp_incident_haiku_20260226_035622_variance--mcp-remote-direct--mcp_CCX-incident-110_A90zfo.md) | [source](../../benchmarks/ccb_mcp_incident/ccx-incident-110) | `mcp-remote-direct` | `passed` | 0.923 | 4 | 0.900 |
| [mcp_CCX-incident-110_wEEezQ](../tasks/ccb_mcp_incident_haiku_20260226_035628_variance--mcp-remote-direct--mcp_CCX-incident-110_wEEezQ.md) | [source](../../benchmarks/ccb_mcp_incident/ccx-incident-110) | `mcp-remote-direct` | `passed` | 0.944 | 4 | 0.778 |
| [ccx-incident-113](../tasks/ccb_mcp_incident_haiku_20260226_224414--baseline-local-direct--ccx-incident-113.md) | [source](../../benchmarks/ccb_mcp_incident/ccx-incident-113) | `baseline-local-direct` | `passed` | 0.667 | 1 | 0.000 |
| [mcp_CCX-incident-113_Vo60b8](../tasks/ccb_mcp_incident_haiku_20260226_224414--mcp-remote-direct--mcp_CCX-incident-113_Vo60b8.md) | [source](../../benchmarks/ccb_mcp_incident/ccx-incident-113) | `mcp-remote-direct` | `passed` | 0.800 | 1 | 0.957 |
| [bl_CCX-incident-125_iYg2nb](../tasks/ccb_mcp_incident_haiku_20260225_011700--baseline-local-artifact--bl_CCX-incident-125_iYg2nb.md) | [source](../../benchmarks/ccb_mcp_incident/ccx-incident-125) | `baseline-local-artifact` | `passed` | 0.500 | 1 | 0.000 |
| [mcp_CCX-incident-125_zCy5RE](../tasks/ccb_mcp_incident_haiku_20260224_181919--mcp-remote-artifact--mcp_CCX-incident-125_zCy5RE.md) | [source](../../benchmarks/ccb_mcp_incident/ccx-incident-125) | `mcp-remote-artifact` | `passed` | 0.833 | 1 | 0.958 |
| [bl_CCX-incident-131_WtmsEJ](../tasks/ccb_mcp_incident_haiku_20260225_011700--baseline-local-artifact--bl_CCX-incident-131_WtmsEJ.md) | [source](../../benchmarks/ccb_mcp_incident/ccx-incident-131) | `baseline-local-artifact` | `failed` | 0.000 | 1 | 0.000 |
| [mcp_CCX-incident-131_DCrTsH](../tasks/ccb_mcp_incident_haiku_20260224_181919--mcp-remote-artifact--mcp_CCX-incident-131_DCrTsH.md) | [source](../../benchmarks/ccb_mcp_incident/ccx-incident-131) | `mcp-remote-artifact` | `passed` | 0.803 | 1 | 0.964 |
| [bl_CCX-incident-139_wQTNwM](../tasks/ccb_mcp_incident_haiku_20260225_011700--baseline-local-artifact--bl_CCX-incident-139_wQTNwM.md) | [source](../../benchmarks/ccb_mcp_incident/ccx-incident-139) | `baseline-local-artifact` | `failed` | 0.000 | 1 | 0.000 |
| [mcp_CCX-incident-139_bYo7Mz](../tasks/ccb_mcp_incident_haiku_20260224_181919--mcp-remote-artifact--mcp_CCX-incident-139_bYo7Mz.md) | [source](../../benchmarks/ccb_mcp_incident/ccx-incident-139) | `mcp-remote-artifact` | `passed` | 0.711 | 1 | 0.947 |

## Multi-Run Variance

Tasks with multiple valid runs (6 task/config pairs).

| Task | Benchmark | Config | Runs | Mean | Std | Individual Rewards |
|---|---|---|---:|---:|---:|---|
| CCX-incident-032 | [source](../../benchmarks/ccb_mcp_incident/ccx-incident-032) | `mcp-remote-direct` | 4 | 0.420 | 0.055 | 0.494, 0.361, 0.411, 0.415 |
| CCX-incident-033 | [source](../../benchmarks/ccb_mcp_incident/ccx-incident-033) | `mcp-remote-direct` | 4 | 0.315 | 0.035 | 0.321, 0.305, 0.274, 0.359 |
| CCX-incident-034 | [source](../../benchmarks/ccb_mcp_incident/ccx-incident-034) | `mcp-remote-direct` | 4 | 1.000 | 0.000 | 1.000, 1.000, 1.000, 1.000 |
| CCX-incident-037 | [source](../../benchmarks/ccb_mcp_incident/ccx-incident-037) | `mcp-remote-direct` | 4 | 0.694 | 0.186 | 0.933, 0.609, 0.500, 0.733 |
| CCX-incident-108 | [source](../../benchmarks/ccb_mcp_incident/ccx-incident-108) | `mcp-remote-direct` | 4 | 0.716 | 0.233 | 0.849, 0.815, 0.833, 0.367 |
| CCX-incident-110 | [source](../../benchmarks/ccb_mcp_incident/ccx-incident-110) | `mcp-remote-direct` | 4 | 0.928 | 0.011 | 0.923, 0.923, 0.944, 0.923 |
