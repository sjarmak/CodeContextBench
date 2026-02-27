# ccb_build

## Run/Config Summary

| Run | Config | Valid Tasks | Mean Reward | Pass Rate |
|---|---|---:|---:|---:|
| [ccb_build_haiku_022326](../runs/ccb_build_haiku_022326.md) | `baseline-local-direct` | 19 | 0.511 | 0.789 |
| [ccb_build_haiku_022326](../runs/ccb_build_haiku_022326.md) | `mcp-remote-direct` | 25 | 0.372 | 0.640 |
| [ccb_build_haiku_20260226_015500_backfill](../runs/ccb_build_haiku_20260226_015500_backfill.md) | `baseline-local-direct` | 1 | 0.820 | 1.000 |

## Tasks

| Task | Benchmark | Config | Status | Reward | Runs | MCP Ratio |
|---|---|---|---|---:|---:|---:|
| [bustub-hyperloglog-impl-001](../tasks/ccb_build_haiku_022326--baseline--bustub-hyperloglog-impl-001.md) | [source](../../benchmarks/ccb_build/bustub-hyperloglog-impl-001) | `baseline-local-direct` | `passed` | 0.167 | 2 | 0.000 |
| [sgonly_bustub-hyperloglog-impl-001](../tasks/ccb_build_haiku_022326--mcp--sgonly_bustub-hyperloglog-impl-001.md) | [source](../../benchmarks/ccb_build/bustub-hyperloglog-impl-001) | `mcp-remote-direct` | `failed` | 0.000 | 2 | 0.100 |
| [sgonly_camel-fix-protocol-feat-001](../tasks/ccb_build_haiku_022326--mcp--sgonly_camel-fix-protocol-feat-001.md) | [source](../../benchmarks/ccb_build/camel-fix-protocol-feat-001) | `mcp-remote-direct` | `passed` | 0.130 | 2 | 0.500 |
| [cgen-deps-install-001](../tasks/ccb_build_haiku_022326--baseline--cgen-deps-install-001.md) | [source](../../benchmarks/ccb_build/cgen-deps-install-001) | `baseline-local-direct` | `failed` | 0.000 | 2 | 0.000 |
| [sgonly_cgen-deps-install-001](../tasks/ccb_build_haiku_022326--mcp--sgonly_cgen-deps-install-001.md) | [source](../../benchmarks/ccb_build/cgen-deps-install-001) | `mcp-remote-direct` | `failed` | 0.000 | 2 | 0.929 |
| [codecoverage-deps-install-001](../tasks/ccb_build_haiku_022326--baseline--codecoverage-deps-install-001.md) | [source](../../benchmarks/ccb_build/codecoverage-deps-install-001) | `baseline-local-direct` | `failed` | 0.000 | 2 | 0.000 |
| [sgonly_codecoverage-deps-install-001](../tasks/ccb_build_haiku_022326--mcp--sgonly_codecoverage-deps-install-001.md) | [source](../../benchmarks/ccb_build/codecoverage-deps-install-001) | `mcp-remote-direct` | `failed` | 0.000 | 2 | 0.654 |
| [dotenv-expand-deps-install-001](../tasks/ccb_build_haiku_022326--baseline--dotenv-expand-deps-install-001.md) | [source](../../benchmarks/ccb_build/dotenv-expand-deps-install-001) | `baseline-local-direct` | `passed` | 1.000 | 2 | 0.000 |
| [sgonly_dotenv-expand-deps-install-001](../tasks/ccb_build_haiku_022326--mcp--sgonly_dotenv-expand-deps-install-001.md) | [source](../../benchmarks/ccb_build/dotenv-expand-deps-install-001) | `mcp-remote-direct` | `failed` | 0.000 | 2 | 0.692 |
| [dotnetkoans-deps-install-001](../tasks/ccb_build_haiku_022326--baseline--dotnetkoans-deps-install-001.md) | [source](../../benchmarks/ccb_build/dotnetkoans-deps-install-001) | `baseline-local-direct` | `failed` | 0.000 | 2 | 0.000 |
| [sgonly_dotnetkoans-deps-install-001](../tasks/ccb_build_haiku_022326--mcp--sgonly_dotnetkoans-deps-install-001.md) | [source](../../benchmarks/ccb_build/dotnetkoans-deps-install-001) | `mcp-remote-direct` | `failed` | 0.000 | 2 | 0.632 |
| [envoy-grpc-server-impl-001](../tasks/ccb_build_haiku_022326--baseline--envoy-grpc-server-impl-001.md) | [source](../../benchmarks/ccb_build/envoy-grpc-server-impl-001) | `baseline-local-direct` | `passed` | 0.400 | 2 | 0.000 |
| [sgonly_envoy-grpc-server-impl-001](../tasks/ccb_build_haiku_022326--mcp--sgonly_envoy-grpc-server-impl-001.md) | [source](../../benchmarks/ccb_build/envoy-grpc-server-impl-001) | `mcp-remote-direct` | `passed` | 0.440 | 2 | 0.938 |
| [eslint-markdown-deps-install-001](../tasks/ccb_build_haiku_022326--baseline--eslint-markdown-deps-install-001.md) | [source](../../benchmarks/ccb_build/eslint-markdown-deps-install-001) | `baseline-local-direct` | `passed` | 1.000 | 2 | 0.000 |
| [sgonly_eslint-markdown-deps-install-001](../tasks/ccb_build_haiku_022326--mcp--sgonly_eslint-markdown-deps-install-001.md) | [source](../../benchmarks/ccb_build/eslint-markdown-deps-install-001) | `mcp-remote-direct` | `failed` | 0.000 | 2 | 0.711 |
| [sgonly_flink-pricing-window-feat-001](../tasks/ccb_build_haiku_022326--mcp--sgonly_flink-pricing-window-feat-001.md) | [source](../../benchmarks/ccb_build/flink-pricing-window-feat-001) | `mcp-remote-direct` | `passed` | 0.510 | 2 | 0.565 |
| [flipt-dep-refactor-001](../tasks/ccb_build_haiku_022326--baseline--flipt-dep-refactor-001.md) | [source](../../benchmarks/ccb_build/flipt-dep-refactor-001) | `baseline-local-direct` | `passed` | 0.700 | 2 | 0.000 |
| [sgonly_flipt-dep-refactor-001](../tasks/ccb_build_haiku_022326--mcp--sgonly_flipt-dep-refactor-001.md) | [source](../../benchmarks/ccb_build/flipt-dep-refactor-001) | `mcp-remote-direct` | `passed` | 0.030 | 2 | 0.418 |
| [flipt-flagexists-refactor-001](../tasks/ccb_build_haiku_022326--baseline--flipt-flagexists-refactor-001.md) | [source](../../benchmarks/ccb_build/flipt-flagexists-refactor-001) | `baseline-local-direct` | `passed` | 0.450 | 2 | 0.000 |
| [sgonly_flipt-flagexists-refactor-001](../tasks/ccb_build_haiku_022326--mcp--sgonly_flipt-flagexists-refactor-001.md) | [source](../../benchmarks/ccb_build/flipt-flagexists-refactor-001) | `mcp-remote-direct` | `passed` | 0.750 | 2 | 0.352 |
| [iamactionhunter-deps-install-001](../tasks/ccb_build_haiku_022326--baseline--iamactionhunter-deps-install-001.md) | [source](../../benchmarks/ccb_build/iamactionhunter-deps-install-001) | `baseline-local-direct` | `passed` | 1.000 | 2 | 0.000 |
| [sgonly_iamactionhunter-deps-install-001](../tasks/ccb_build_haiku_022326--mcp--sgonly_iamactionhunter-deps-install-001.md) | [source](../../benchmarks/ccb_build/iamactionhunter-deps-install-001) | `mcp-remote-direct` | `passed` | 1.000 | 2 | 0.390 |
| [sgonly_k8s-noschedule-taint-feat-001](../tasks/ccb_build_haiku_022326--mcp--sgonly_k8s-noschedule-taint-feat-001.md) | [source](../../benchmarks/ccb_build/k8s-noschedule-taint-feat-001) | `mcp-remote-direct` | `passed` | 0.500 | 2 | 0.279 |
| [k8s-runtime-object-impl-001](../tasks/ccb_build_haiku_022326--baseline--k8s-runtime-object-impl-001.md) | [source](../../benchmarks/ccb_build/k8s-runtime-object-impl-001) | `baseline-local-direct` | `passed` | 0.110 | 2 | 0.000 |
| [sgonly_k8s-runtime-object-impl-001](../tasks/ccb_build_haiku_022326--mcp--sgonly_k8s-runtime-object-impl-001.md) | [source](../../benchmarks/ccb_build/k8s-runtime-object-impl-001) | `mcp-remote-direct` | `passed` | 0.120 | 2 | 0.831 |
| [sgonly_k8s-score-normalizer-refac-001](../tasks/ccb_build_haiku_022326--mcp--sgonly_k8s-score-normalizer-refac-001.md) | [source](../../benchmarks/ccb_build/k8s-score-normalizer-refac-001) | `mcp-remote-direct` | `passed` | 0.780 | 2 | 0.385 |
| [kafka-batch-accumulator-refac-001](../tasks/ccb_build_haiku_022326--baseline--kafka-batch-accumulator-refac-001.md) | [source](../../benchmarks/ccb_build/kafka-batch-accumulator-refac-001) | `baseline-local-direct` | `passed` | 0.320 | 2 | 0.000 |
| [sgonly_kafka-batch-accumulator-refac-001](../tasks/ccb_build_haiku_022326--mcp--sgonly_kafka-batch-accumulator-refac-001.md) | [source](../../benchmarks/ccb_build/kafka-batch-accumulator-refac-001) | `mcp-remote-direct` | `passed` | 0.680 | 2 | 0.333 |
| [pcap-parser-deps-install-001](../tasks/ccb_build_haiku_022326--baseline--pcap-parser-deps-install-001.md) | [source](../../benchmarks/ccb_build/pcap-parser-deps-install-001) | `baseline-local-direct` | `passed` | 1.000 | 2 | 0.000 |
| [sgonly_pcap-parser-deps-install-001](../tasks/ccb_build_haiku_022326--mcp--sgonly_pcap-parser-deps-install-001.md) | [source](../../benchmarks/ccb_build/pcap-parser-deps-install-001) | `mcp-remote-direct` | `failed` | 0.000 | 2 | 0.360 |
| [python-http-class-naming-refac-001](../tasks/ccb_build_haiku_022326--baseline--python-http-class-naming-refac-001.md) | [source](../../benchmarks/ccb_build/python-http-class-naming-refac-001) | `baseline-local-direct` | `passed` | 0.840 | 2 | 0.000 |
| [sgonly_python-http-class-naming-refac-001](../tasks/ccb_build_haiku_022326--mcp--sgonly_python-http-class-naming-refac-001.md) | [source](../../benchmarks/ccb_build/python-http-class-naming-refac-001) | `mcp-remote-direct` | `passed` | 0.880 | 2 | 0.293 |
| [rust-subtype-relation-refac-001](../tasks/ccb_build_haiku_20260226_015500_backfill--baseline-local-direct--rust-subtype-relation-refac-001.md) | [source](../../benchmarks/ccb_build/rust-subtype-relation-refac-001) | `baseline-local-direct` | `passed` | 0.820 | 2 | 0.000 |
| [sgonly_rust-subtype-relation-refac-001](../tasks/ccb_build_haiku_022326--mcp--sgonly_rust-subtype-relation-refac-001.md) | [source](../../benchmarks/ccb_build/rust-subtype-relation-refac-001) | `mcp-remote-direct` | `passed` | 0.710 | 2 | 0.464 |
| [sgonly_servo-scrollend-event-feat-001](../tasks/ccb_build_haiku_022326--mcp--sgonly_servo-scrollend-event-feat-001.md) | [source](../../benchmarks/ccb_build/servo-scrollend-event-feat-001) | `mcp-remote-direct` | `failed` | 0.000 | 2 | 0.544 |
| [similar-asserts-deps-install-001](../tasks/ccb_build_haiku_022326--baseline--similar-asserts-deps-install-001.md) | [source](../../benchmarks/ccb_build/similar-asserts-deps-install-001) | `baseline-local-direct` | `passed` | 1.000 | 2 | 0.000 |
| [sgonly_similar-asserts-deps-install-001](../tasks/ccb_build_haiku_022326--mcp--sgonly_similar-asserts-deps-install-001.md) | [source](../../benchmarks/ccb_build/similar-asserts-deps-install-001) | `mcp-remote-direct` | `passed` | 1.000 | 2 | 0.500 |
| [strata-cds-tranche-feat-001](../tasks/ccb_build_haiku_022326--baseline--strata-cds-tranche-feat-001.md) | [source](../../benchmarks/ccb_build/strata-cds-tranche-feat-001) | `baseline-local-direct` | `passed` | 0.410 | 2 | 0.000 |
| [sgonly_strata-cds-tranche-feat-001](../tasks/ccb_build_haiku_022326--mcp--sgonly_strata-cds-tranche-feat-001.md) | [source](../../benchmarks/ccb_build/strata-cds-tranche-feat-001) | `mcp-remote-direct` | `passed` | 0.280 | 2 | 0.567 |
| [strata-fx-european-refac-001](../tasks/ccb_build_haiku_022326--baseline--strata-fx-european-refac-001.md) | [source](../../benchmarks/ccb_build/strata-fx-european-refac-001) | `baseline-local-direct` | `passed` | 0.320 | 2 | 0.000 |
| [sgonly_strata-fx-european-refac-001](../tasks/ccb_build_haiku_022326--mcp--sgonly_strata-fx-european-refac-001.md) | [source](../../benchmarks/ccb_build/strata-fx-european-refac-001) | `mcp-remote-direct` | `passed` | 0.800 | 2 | 0.312 |
| [tensorrt-mxfp4-quant-feat-001](../tasks/ccb_build_haiku_022326--baseline--tensorrt-mxfp4-quant-feat-001.md) | [source](../../benchmarks/ccb_build/tensorrt-mxfp4-quant-feat-001) | `baseline-local-direct` | `passed` | 1.000 | 2 | 0.000 |
| [sgonly_tensorrt-mxfp4-quant-feat-001](../tasks/ccb_build_haiku_022326--mcp--sgonly_tensorrt-mxfp4-quant-feat-001.md) | [source](../../benchmarks/ccb_build/tensorrt-mxfp4-quant-feat-001) | `mcp-remote-direct` | `passed` | 0.700 | 2 | 0.537 |
| [vscode-stale-diagnostics-feat-001](../tasks/ccb_build_haiku_022326--baseline--vscode-stale-diagnostics-feat-001.md) | [source](../../benchmarks/ccb_build/vscode-stale-diagnostics-feat-001) | `baseline-local-direct` | `failed` | 0.000 | 2 | 0.000 |
| [sgonly_vscode-stale-diagnostics-feat-001](../tasks/ccb_build_haiku_022326--mcp--sgonly_vscode-stale-diagnostics-feat-001.md) | [source](../../benchmarks/ccb_build/vscode-stale-diagnostics-feat-001) | `mcp-remote-direct` | `failed` | 0.000 | 2 | 0.625 |

## Multi-Run Variance

Tasks with multiple valid runs (1 task/config pairs).

| Task | Benchmark | Config | Runs | Mean | Std | Individual Rewards |
|---|---|---|---:|---:|---:|---|
| rust-subtype-relation-refac-001 | [source](../../benchmarks/ccb_build/rust-subtype-relation-refac-001) | `baseline-local-direct` | 2 | 0.820 | 0.000 | 0.820, 0.820 |
