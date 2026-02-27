# ccb_mcp_security

## Run/Config Summary

| Run | Config | Valid Tasks | Mean Reward | Pass Rate |
|---|---|---:|---:|---:|
| [ccb_mcp_security_haiku_022126](../runs/ccb_mcp_security_haiku_022126.md) | `baseline` | 2 | 0.500 | 1.000 |
| [ccb_mcp_security_haiku_022126](../runs/ccb_mcp_security_haiku_022126.md) | `mcp` | 2 | 0.821 | 1.000 |
| [ccb_mcp_security_haiku_20260224_181919](../runs/ccb_mcp_security_haiku_20260224_181919.md) | `mcp-remote-artifact` | 4 | 0.777 | 1.000 |
| [ccb_mcp_security_haiku_20260225_011700](../runs/ccb_mcp_security_haiku_20260225_011700.md) | `baseline-local-artifact` | 4 | 0.000 | 0.000 |
| [ccb_mcp_security_haiku_20260226_035617](../runs/ccb_mcp_security_haiku_20260226_035617.md) | `mcp-remote-direct` | 4 | 0.744 | 1.000 |
| [ccb_mcp_security_haiku_20260226_035622_variance](../runs/ccb_mcp_security_haiku_20260226_035622_variance.md) | `mcp-remote-direct` | 4 | 0.578 | 1.000 |
| [ccb_mcp_security_haiku_20260226_035628_variance](../runs/ccb_mcp_security_haiku_20260226_035628_variance.md) | `baseline-local-direct` | 1 | 0.367 | 1.000 |
| [ccb_mcp_security_haiku_20260226_035628_variance](../runs/ccb_mcp_security_haiku_20260226_035628_variance.md) | `mcp-remote-direct` | 4 | 0.767 | 1.000 |
| [ccb_mcp_security_haiku_20260226_035633_variance](../runs/ccb_mcp_security_haiku_20260226_035633_variance.md) | `mcp-remote-direct` | 4 | 0.731 | 1.000 |
| [ccb_mcp_security_haiku_20260226_205845](../runs/ccb_mcp_security_haiku_20260226_205845.md) | `baseline-local-direct` | 3 | 0.682 | 1.000 |

## Tasks

| Task | Benchmark | Config | Status | Reward | Runs | MCP Ratio |
|---|---|---|---|---:|---:|---:|
| [ccx-vuln-remed-011](../tasks/ccb_mcp_security_haiku_022126--baseline--ccx-vuln-remed-011.md) | [source](../../benchmarks/ccb_mcp_security/ccx-vuln-remed-011) | `baseline` | `passed` | 0.750 | 1 | 0.000 |
| [ccx-vuln-remed-011](../tasks/ccb_mcp_security_haiku_022126--mcp--ccx-vuln-remed-011.md) | [source](../../benchmarks/ccb_mcp_security/ccx-vuln-remed-011) | `mcp` | `passed` | 1.000 | 1 | 0.971 |
| [ccx-vuln-remed-012](../tasks/ccb_mcp_security_haiku_20260226_035628_variance--baseline-local-direct--ccx-vuln-remed-012.md) | [source](../../benchmarks/ccb_mcp_security/ccx-vuln-remed-012) | `baseline-local-direct` | `passed` | 0.367 | 4 | 0.000 |
| [mcp_CCX-vuln-remed-012_6P8wqO](../tasks/ccb_mcp_security_haiku_20260226_035633_variance--mcp-remote-direct--mcp_CCX-vuln-remed-012_6P8wqO.md) | [source](../../benchmarks/ccb_mcp_security/ccx-vuln-remed-012) | `mcp-remote-direct` | `passed` | 0.563 | 4 | 0.973 |
| [mcp_CCX-vuln-remed-012_6fFmnM](../tasks/ccb_mcp_security_haiku_20260226_035628_variance--mcp-remote-direct--mcp_CCX-vuln-remed-012_6fFmnM.md) | [source](../../benchmarks/ccb_mcp_security/ccx-vuln-remed-012) | `mcp-remote-direct` | `passed` | 0.533 | 4 | 0.909 |
| [mcp_CCX-vuln-remed-012_9JwGrW](../tasks/ccb_mcp_security_haiku_20260226_035622_variance--mcp-remote-direct--mcp_CCX-vuln-remed-012_9JwGrW.md) | [source](../../benchmarks/ccb_mcp_security/ccx-vuln-remed-012) | `mcp-remote-direct` | `passed` | 0.397 | 4 | 0.889 |
| [mcp_CCX-vuln-remed-012_lrLTYc](../tasks/ccb_mcp_security_haiku_20260226_035617--mcp-remote-direct--mcp_CCX-vuln-remed-012_lrLTYc.md) | [source](../../benchmarks/ccb_mcp_security/ccx-vuln-remed-012) | `mcp-remote-direct` | `passed` | 0.463 | 4 | 0.923 |
| [ccx-vuln-remed-013](../tasks/ccb_mcp_security_haiku_20260226_205845--baseline-local-direct--ccx-vuln-remed-013.md) | [source](../../benchmarks/ccb_mcp_security/ccx-vuln-remed-013) | `baseline-local-direct` | `passed` | 0.336 | 1 | 0.000 |
| [mcp_CCX-vuln-remed-013_JtNIGY](../tasks/ccb_mcp_security_haiku_20260226_035633_variance--mcp-remote-direct--mcp_CCX-vuln-remed-013_JtNIGY.md) | [source](../../benchmarks/ccb_mcp_security/ccx-vuln-remed-013) | `mcp-remote-direct` | `passed` | 0.624 | 4 | 0.958 |
| [mcp_CCX-vuln-remed-013_LoBHLI](../tasks/ccb_mcp_security_haiku_20260226_035628_variance--mcp-remote-direct--mcp_CCX-vuln-remed-013_LoBHLI.md) | [source](../../benchmarks/ccb_mcp_security/ccx-vuln-remed-013) | `mcp-remote-direct` | `passed` | 0.749 | 4 | 0.963 |
| [mcp_CCX-vuln-remed-013_Kmqlzc](../tasks/ccb_mcp_security_haiku_20260226_035622_variance--mcp-remote-direct--mcp_CCX-vuln-remed-013_Kmqlzc.md) | [source](../../benchmarks/ccb_mcp_security/ccx-vuln-remed-013) | `mcp-remote-direct` | `passed` | 0.105 | 4 | 0.971 |
| [mcp_CCX-vuln-remed-013_WOkHxn](../tasks/ccb_mcp_security_haiku_20260226_035617--mcp-remote-direct--mcp_CCX-vuln-remed-013_WOkHxn.md) | [source](../../benchmarks/ccb_mcp_security/ccx-vuln-remed-013) | `mcp-remote-direct` | `passed` | 0.705 | 4 | 0.926 |
| [ccx-vuln-remed-014](../tasks/ccb_mcp_security_haiku_022126--baseline--ccx-vuln-remed-014.md) | [source](../../benchmarks/ccb_mcp_security/ccx-vuln-remed-014) | `baseline` | `passed` | 0.250 | 1 | 0.000 |
| [ccx-vuln-remed-014](../tasks/ccb_mcp_security_haiku_022126--mcp--ccx-vuln-remed-014.md) | [source](../../benchmarks/ccb_mcp_security/ccx-vuln-remed-014) | `mcp` | `passed` | 0.643 | 1 | 0.976 |
| [ccx-vuln-remed-105](../tasks/ccb_mcp_security_haiku_20260226_205845--baseline-local-direct--ccx-vuln-remed-105.md) | [source](../../benchmarks/ccb_mcp_security/ccx-vuln-remed-105) | `baseline-local-direct` | `passed` | 0.709 | 1 | 0.000 |
| [mcp_CCX-vuln-remed-105_JZsxbp](../tasks/ccb_mcp_security_haiku_20260226_035633_variance--mcp-remote-direct--mcp_CCX-vuln-remed-105_JZsxbp.md) | [source](../../benchmarks/ccb_mcp_security/ccx-vuln-remed-105) | `mcp-remote-direct` | `passed` | 0.737 | 4 | 0.909 |
| [mcp_CCX-vuln-remed-105_aQMP88](../tasks/ccb_mcp_security_haiku_20260226_035628_variance--mcp-remote-direct--mcp_CCX-vuln-remed-105_aQMP88.md) | [source](../../benchmarks/ccb_mcp_security/ccx-vuln-remed-105) | `mcp-remote-direct` | `passed` | 0.784 | 4 | 0.971 |
| [mcp_CCX-vuln-remed-105_79Rpkl](../tasks/ccb_mcp_security_haiku_20260226_035622_variance--mcp-remote-direct--mcp_CCX-vuln-remed-105_79Rpkl.md) | [source](../../benchmarks/ccb_mcp_security/ccx-vuln-remed-105) | `mcp-remote-direct` | `passed` | 0.809 | 4 | 0.952 |
| [mcp_CCX-vuln-remed-105_1RoC5v](../tasks/ccb_mcp_security_haiku_20260226_035617--mcp-remote-direct--mcp_CCX-vuln-remed-105_1RoC5v.md) | [source](../../benchmarks/ccb_mcp_security/ccx-vuln-remed-105) | `mcp-remote-direct` | `passed` | 0.809 | 4 | 0.958 |
| [ccx-vuln-remed-111](../tasks/ccb_mcp_security_haiku_20260226_205845--baseline-local-direct--ccx-vuln-remed-111.md) | [source](../../benchmarks/ccb_mcp_security/ccx-vuln-remed-111) | `baseline-local-direct` | `passed` | 1.000 | 1 | 0.000 |
| [mcp_CCX-vuln-remed-111_gpcSkd](../tasks/ccb_mcp_security_haiku_20260226_035633_variance--mcp-remote-direct--mcp_CCX-vuln-remed-111_gpcSkd.md) | [source](../../benchmarks/ccb_mcp_security/ccx-vuln-remed-111) | `mcp-remote-direct` | `passed` | 1.000 | 4 | 0.846 |
| [mcp_CCX-vuln-remed-111_AFyYzp](../tasks/ccb_mcp_security_haiku_20260226_035628_variance--mcp-remote-direct--mcp_CCX-vuln-remed-111_AFyYzp.md) | [source](../../benchmarks/ccb_mcp_security/ccx-vuln-remed-111) | `mcp-remote-direct` | `passed` | 1.000 | 4 | 0.909 |
| [mcp_CCX-vuln-remed-111_u7rGCx](../tasks/ccb_mcp_security_haiku_20260226_035622_variance--mcp-remote-direct--mcp_CCX-vuln-remed-111_u7rGCx.md) | [source](../../benchmarks/ccb_mcp_security/ccx-vuln-remed-111) | `mcp-remote-direct` | `passed` | 1.000 | 4 | 0.846 |
| [mcp_CCX-vuln-remed-111_7hdRBX](../tasks/ccb_mcp_security_haiku_20260226_035617--mcp-remote-direct--mcp_CCX-vuln-remed-111_7hdRBX.md) | [source](../../benchmarks/ccb_mcp_security/ccx-vuln-remed-111) | `mcp-remote-direct` | `passed` | 1.000 | 4 | 0.966 |
| [bl_CCX-vuln-remed-126_5Us92F](../tasks/ccb_mcp_security_haiku_20260225_011700--baseline-local-artifact--bl_CCX-vuln-remed-126_5Us92F.md) | [source](../../benchmarks/ccb_mcp_security/ccx-vuln-remed-126) | `baseline-local-artifact` | `failed` | 0.000 | 1 | 0.000 |
| [mcp_CCX-vuln-remed-126_HYpbDr](../tasks/ccb_mcp_security_haiku_20260224_181919--mcp-remote-artifact--mcp_CCX-vuln-remed-126_HYpbDr.md) | [source](../../benchmarks/ccb_mcp_security/ccx-vuln-remed-126) | `mcp-remote-artifact` | `passed` | 0.745 | 1 | 0.978 |
| [bl_CCX-vuln-remed-130_Zk4x7i](../tasks/ccb_mcp_security_haiku_20260225_011700--baseline-local-artifact--bl_CCX-vuln-remed-130_Zk4x7i.md) | [source](../../benchmarks/ccb_mcp_security/ccx-vuln-remed-130) | `baseline-local-artifact` | `failed` | 0.000 | 1 | 0.000 |
| [mcp_CCX-vuln-remed-130_0JULg6](../tasks/ccb_mcp_security_haiku_20260224_181919--mcp-remote-artifact--mcp_CCX-vuln-remed-130_0JULg6.md) | [source](../../benchmarks/ccb_mcp_security/ccx-vuln-remed-130) | `mcp-remote-artifact` | `passed` | 1.000 | 1 | 0.955 |
| [bl_CCX-vuln-remed-135_UVjwY5](../tasks/ccb_mcp_security_haiku_20260225_011700--baseline-local-artifact--bl_CCX-vuln-remed-135_UVjwY5.md) | [source](../../benchmarks/ccb_mcp_security/ccx-vuln-remed-135) | `baseline-local-artifact` | `failed` | 0.000 | 1 | 0.000 |
| [mcp_CCX-vuln-remed-135_Uueqpt](../tasks/ccb_mcp_security_haiku_20260224_181919--mcp-remote-artifact--mcp_CCX-vuln-remed-135_Uueqpt.md) | [source](../../benchmarks/ccb_mcp_security/ccx-vuln-remed-135) | `mcp-remote-artifact` | `passed` | 0.611 | 1 | 0.929 |
| [bl_CCX-vuln-remed-141_Hv3FTI](../tasks/ccb_mcp_security_haiku_20260225_011700--baseline-local-artifact--bl_CCX-vuln-remed-141_Hv3FTI.md) | [source](../../benchmarks/ccb_mcp_security/ccx-vuln-remed-141) | `baseline-local-artifact` | `failed` | 0.000 | 1 | 0.000 |
| [mcp_CCX-vuln-remed-141_y0cxyE](../tasks/ccb_mcp_security_haiku_20260224_181919--mcp-remote-artifact--mcp_CCX-vuln-remed-141_y0cxyE.md) | [source](../../benchmarks/ccb_mcp_security/ccx-vuln-remed-141) | `mcp-remote-artifact` | `passed` | 0.750 | 1 | 0.958 |

## Multi-Run Variance

Tasks with multiple valid runs (5 task/config pairs).

| Task | Benchmark | Config | Runs | Mean | Std | Individual Rewards |
|---|---|---|---:|---:|---:|---|
| CCX-vuln-remed-012 | [source](../../benchmarks/ccb_mcp_security/ccx-vuln-remed-012) | `baseline-local-direct` | 4 | 0.475 | 0.095 | 0.433, 0.586, 0.514, 0.367 |
| CCX-vuln-remed-012 | [source](../../benchmarks/ccb_mcp_security/ccx-vuln-remed-012) | `mcp-remote-direct` | 4 | 0.489 | 0.074 | 0.463, 0.563, 0.397, 0.533 |
| CCX-vuln-remed-013 | [source](../../benchmarks/ccb_mcp_security/ccx-vuln-remed-013) | `mcp-remote-direct` | 4 | 0.545 | 0.298 | 0.705, 0.624, 0.105, 0.749 |
| CCX-vuln-remed-105 | [source](../../benchmarks/ccb_mcp_security/ccx-vuln-remed-105) | `mcp-remote-direct` | 4 | 0.785 | 0.034 | 0.809, 0.737, 0.809, 0.784 |
| CCX-vuln-remed-111 | [source](../../benchmarks/ccb_mcp_security/ccx-vuln-remed-111) | `mcp-remote-direct` | 4 | 1.000 | 0.000 | 1.000, 1.000, 1.000, 1.000 |
