# ccb_mcp_crossorg

## Run/Config Summary

| Run | Config | Valid Tasks | Mean Reward | Pass Rate |
|---|---|---:|---:|---:|
| [ccb_mcp_crossorg_haiku_022126](../runs/ccb_mcp_crossorg_haiku_022126.md) | `baseline` | 2 | 0.750 | 1.000 |
| [ccb_mcp_crossorg_haiku_022126](../runs/ccb_mcp_crossorg_haiku_022126.md) | `mcp` | 2 | 1.000 | 1.000 |
| [ccb_mcp_crossorg_haiku_20260224_181919](../runs/ccb_mcp_crossorg_haiku_20260224_181919.md) | `mcp-remote-artifact` | 2 | 0.171 | 0.500 |
| [ccb_mcp_crossorg_haiku_20260225_011700](../runs/ccb_mcp_crossorg_haiku_20260225_011700.md) | `baseline-local-artifact` | 2 | 0.062 | 0.500 |
| [ccb_mcp_crossorg_haiku_20260226_035617](../runs/ccb_mcp_crossorg_haiku_20260226_035617.md) | `mcp-remote-direct` | 1 | 0.800 | 1.000 |
| [ccb_mcp_crossorg_haiku_20260226_035622_variance](../runs/ccb_mcp_crossorg_haiku_20260226_035622_variance.md) | `mcp-remote-direct` | 1 | 0.680 | 1.000 |
| [ccb_mcp_crossorg_haiku_20260226_035628_variance](../runs/ccb_mcp_crossorg_haiku_20260226_035628_variance.md) | `mcp-remote-direct` | 1 | 0.680 | 1.000 |
| [ccb_mcp_crossorg_haiku_20260226_035633_variance](../runs/ccb_mcp_crossorg_haiku_20260226_035633_variance.md) | `mcp-remote-direct` | 1 | 0.711 | 1.000 |
| [ccb_mcp_crossorg_haiku_20260226_205845](../runs/ccb_mcp_crossorg_haiku_20260226_205845.md) | `baseline-local-direct` | 1 | 0.658 | 1.000 |

## Tasks

| Task | Benchmark | Config | Status | Reward | Runs | MCP Ratio |
|---|---|---|---|---:|---:|---:|
| [ccx-crossorg-061](../tasks/ccb_mcp_crossorg_haiku_022126--baseline--ccx-crossorg-061.md) | [source](../../benchmarks/ccb_mcp_crossorg/ccx-crossorg-061) | `baseline` | `passed` | 0.500 | 1 | 0.000 |
| [ccx-crossorg-061](../tasks/ccb_mcp_crossorg_haiku_022126--mcp--ccx-crossorg-061.md) | [source](../../benchmarks/ccb_mcp_crossorg/ccx-crossorg-061) | `mcp` | `passed` | 1.000 | 1 | 0.889 |
| [ccx-crossorg-062](../tasks/ccb_mcp_crossorg_haiku_20260226_205845--baseline-local-direct--ccx-crossorg-062.md) | [source](../../benchmarks/ccb_mcp_crossorg/ccx-crossorg-062) | `baseline-local-direct` | `passed` | 0.658 | 1 | 0.000 |
| [mcp_CCX-crossorg-062_7tCLGe](../tasks/ccb_mcp_crossorg_haiku_20260226_035628_variance--mcp-remote-direct--mcp_CCX-crossorg-062_7tCLGe.md) | [source](../../benchmarks/ccb_mcp_crossorg/ccx-crossorg-062) | `mcp-remote-direct` | `passed` | 0.680 | 4 | 0.986 |
| [mcp_CCX-crossorg-062_CJrdeX](../tasks/ccb_mcp_crossorg_haiku_20260226_035622_variance--mcp-remote-direct--mcp_CCX-crossorg-062_CJrdeX.md) | [source](../../benchmarks/ccb_mcp_crossorg/ccx-crossorg-062) | `mcp-remote-direct` | `passed` | 0.680 | 4 | 0.854 |
| [mcp_CCX-crossorg-062_Dp7ADh](../tasks/ccb_mcp_crossorg_haiku_20260226_035633_variance--mcp-remote-direct--mcp_CCX-crossorg-062_Dp7ADh.md) | [source](../../benchmarks/ccb_mcp_crossorg/ccx-crossorg-062) | `mcp-remote-direct` | `passed` | 0.711 | 4 | 0.929 |
| [mcp_CCX-crossorg-062_XLX9KX](../tasks/ccb_mcp_crossorg_haiku_20260226_035617--mcp-remote-direct--mcp_CCX-crossorg-062_XLX9KX.md) | [source](../../benchmarks/ccb_mcp_crossorg/ccx-crossorg-062) | `mcp-remote-direct` | `passed` | 0.800 | 4 | 0.987 |
| [ccx-crossorg-066](../tasks/ccb_mcp_crossorg_haiku_022126--baseline--ccx-crossorg-066.md) | [source](../../benchmarks/ccb_mcp_crossorg/ccx-crossorg-066) | `baseline` | `passed` | 1.000 | 1 | 0.000 |
| [ccx-crossorg-066](../tasks/ccb_mcp_crossorg_haiku_022126--mcp--ccx-crossorg-066.md) | [source](../../benchmarks/ccb_mcp_crossorg/ccx-crossorg-066) | `mcp` | `passed` | 1.000 | 1 | 0.857 |
| [bl_CCX-crossorg-121_PDC0i6](../tasks/ccb_mcp_crossorg_haiku_20260225_011700--baseline-local-artifact--bl_CCX-crossorg-121_PDC0i6.md) | [source](../../benchmarks/ccb_mcp_crossorg/ccx-crossorg-121) | `baseline-local-artifact` | `failed` | 0.000 | 1 | 0.000 |
| [mcp_CCX-crossorg-121_ZILlm2](../tasks/ccb_mcp_crossorg_haiku_20260224_181919--mcp-remote-artifact--mcp_CCX-crossorg-121_ZILlm2.md) | [source](../../benchmarks/ccb_mcp_crossorg/ccx-crossorg-121) | `mcp-remote-artifact` | `passed` | 0.343 | 1 | 0.944 |
| [bl_CCX-crossorg-132_5p0UW6](../tasks/ccb_mcp_crossorg_haiku_20260225_011700--baseline-local-artifact--bl_CCX-crossorg-132_5p0UW6.md) | [source](../../benchmarks/ccb_mcp_crossorg/ccx-crossorg-132) | `baseline-local-artifact` | `passed` | 0.125 | 1 | 0.000 |
| [mcp_CCX-crossorg-132_22a84e](../tasks/ccb_mcp_crossorg_haiku_20260224_181919--mcp-remote-artifact--mcp_CCX-crossorg-132_22a84e.md) | [source](../../benchmarks/ccb_mcp_crossorg/ccx-crossorg-132) | `mcp-remote-artifact` | `failed` | 0.000 | 1 | 0.971 |

## Multi-Run Variance

Tasks with multiple valid runs (1 task/config pairs).

| Task | Benchmark | Config | Runs | Mean | Std | Individual Rewards |
|---|---|---|---:|---:|---:|---|
| CCX-crossorg-062 | [source](../../benchmarks/ccb_mcp_crossorg/ccx-crossorg-062) | `mcp-remote-direct` | 4 | 0.718 | 0.057 | 0.800, 0.680, 0.680, 0.711 |
