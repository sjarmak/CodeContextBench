# ccb_design

## Run/Config Summary

| Run | Config | Valid Tasks | Mean Reward | Pass Rate |
|---|---|---:|---:|---:|
| [ccb_design_haiku_20260226_015500_backfill](../runs/ccb_design_haiku_20260226_015500_backfill.md) | `baseline-local-direct` | 7 | 0.723 | 0.857 |
| [design_haiku_20260223_124652](../runs/design_haiku_20260223_124652.md) | `baseline-local-direct` | 13 | 0.770 | 1.000 |
| [design_haiku_20260223_124652](../runs/design_haiku_20260223_124652.md) | `mcp-remote-direct` | 20 | 0.718 | 1.000 |

## Tasks

| Task | Benchmark | Config | Status | Reward | Runs | MCP Ratio |
|---|---|---|---|---:|---:|---:|
| [camel-routing-arch-001](../tasks/ccb_design_haiku_20260226_015500_backfill--baseline-local-direct--camel-routing-arch-001.md) | [source](../../benchmarks/ccb_design/camel-routing-arch-001) | `baseline-local-direct` | `passed` | 0.870 | 2 | 0.000 |
| [sgonly_camel-routing-arch-001](../tasks/design_haiku_20260223_124652--mcp-remote-direct--sgonly_camel-routing-arch-001.md) | [source](../../benchmarks/ccb_design/camel-routing-arch-001) | `mcp-remote-direct` | `passed` | 0.730 | 2 | 0.966 |
| [django-modeladmin-impact-001](../tasks/design_haiku_20260223_124652--baseline-local-direct--django-modeladmin-impact-001.md) | [source](../../benchmarks/ccb_design/django-modeladmin-impact-001) | `baseline-local-direct` | `passed` | 1.000 | 2 | 0.000 |
| [sgonly_django-modeladmin-impact-001](../tasks/design_haiku_20260223_124652--mcp-remote-direct--sgonly_django-modeladmin-impact-001.md) | [source](../../benchmarks/ccb_design/django-modeladmin-impact-001) | `mcp-remote-direct` | `passed` | 1.000 | 2 | 0.939 |
| [django-orm-query-arch-001](../tasks/design_haiku_20260223_124652--baseline-local-direct--django-orm-query-arch-001.md) | [source](../../benchmarks/ccb_design/django-orm-query-arch-001) | `baseline-local-direct` | `passed` | 0.910 | 2 | 0.000 |
| [sgonly_django-orm-query-arch-001](../tasks/design_haiku_20260223_124652--mcp-remote-direct--sgonly_django-orm-query-arch-001.md) | [source](../../benchmarks/ccb_design/django-orm-query-arch-001) | `mcp-remote-direct` | `passed` | 0.990 | 2 | 0.969 |
| [django-pre-validate-signal-design-001](../tasks/design_haiku_20260223_124652--baseline-local-direct--django-pre-validate-signal-design-001.md) | [source](../../benchmarks/ccb_design/django-pre-validate-signal-design-001) | `baseline-local-direct` | `passed` | 1.000 | 2 | 0.000 |
| [sgonly_django-pre-validate-signal-design-001](../tasks/design_haiku_20260223_124652--mcp-remote-direct--sgonly_django-pre-validate-signal-design-001.md) | [source](../../benchmarks/ccb_design/django-pre-validate-signal-design-001) | `mcp-remote-direct` | `passed` | 1.000 | 2 | 0.157 |
| [django-rate-limit-design-001](../tasks/design_haiku_20260223_124652--baseline-local-direct--django-rate-limit-design-001.md) | [source](../../benchmarks/ccb_design/django-rate-limit-design-001) | `baseline-local-direct` | `passed` | 0.900 | 2 | 0.000 |
| [sgonly_django-rate-limit-design-001](../tasks/design_haiku_20260223_124652--mcp-remote-direct--sgonly_django-rate-limit-design-001.md) | [source](../../benchmarks/ccb_design/django-rate-limit-design-001) | `mcp-remote-direct` | `passed` | 1.000 | 2 | 0.333 |
| [envoy-routeconfig-dep-chain-001](../tasks/design_haiku_20260223_124652--baseline-local-direct--envoy-routeconfig-dep-chain-001.md) | [source](../../benchmarks/ccb_design/envoy-routeconfig-dep-chain-001) | `baseline-local-direct` | `passed` | 1.000 | 2 | 0.000 |
| [sgonly_envoy-routeconfig-dep-chain-001](../tasks/design_haiku_20260223_124652--mcp-remote-direct--sgonly_envoy-routeconfig-dep-chain-001.md) | [source](../../benchmarks/ccb_design/envoy-routeconfig-dep-chain-001) | `mcp-remote-direct` | `passed` | 1.000 | 2 | 0.857 |
| [envoy-stream-aggregated-sym-001](../tasks/design_haiku_20260223_124652--baseline-local-direct--envoy-stream-aggregated-sym-001.md) | [source](../../benchmarks/ccb_design/envoy-stream-aggregated-sym-001) | `baseline-local-direct` | `passed` | 0.570 | 2 | 0.000 |
| [sgonly_envoy-stream-aggregated-sym-001](../tasks/design_haiku_20260223_124652--mcp-remote-direct--sgonly_envoy-stream-aggregated-sym-001.md) | [source](../../benchmarks/ccb_design/envoy-stream-aggregated-sym-001) | `mcp-remote-direct` | `passed` | 0.320 | 2 | 0.971 |
| [etcd-grpc-api-upgrade-001](../tasks/ccb_design_haiku_20260226_015500_backfill--baseline-local-direct--etcd-grpc-api-upgrade-001.md) | [source](../../benchmarks/ccb_design/etcd-grpc-api-upgrade-001) | `baseline-local-direct` | `failed` | 0.000 | 2 | 0.000 |
| [sgonly_etcd-grpc-api-upgrade-001](../tasks/design_haiku_20260223_124652--mcp-remote-direct--sgonly_etcd-grpc-api-upgrade-001.md) | [source](../../benchmarks/ccb_design/etcd-grpc-api-upgrade-001) | `mcp-remote-direct` | `passed` | 0.714 | 2 | 0.108 |
| [flink-checkpoint-arch-001](../tasks/ccb_design_haiku_20260226_015500_backfill--baseline-local-direct--flink-checkpoint-arch-001.md) | [source](../../benchmarks/ccb_design/flink-checkpoint-arch-001) | `baseline-local-direct` | `passed` | 0.800 | 2 | 0.000 |
| [sgonly_flink-checkpoint-arch-001](../tasks/design_haiku_20260223_124652--mcp-remote-direct--sgonly_flink-checkpoint-arch-001.md) | [source](../../benchmarks/ccb_design/flink-checkpoint-arch-001) | `mcp-remote-direct` | `passed` | 0.730 | 2 | 0.958 |
| [flipt-protobuf-metadata-design-001](../tasks/design_haiku_20260223_124652--baseline-local-direct--flipt-protobuf-metadata-design-001.md) | [source](../../benchmarks/ccb_design/flipt-protobuf-metadata-design-001) | `baseline-local-direct` | `passed` | 1.000 | 2 | 0.000 |
| [sgonly_flipt-protobuf-metadata-design-001](../tasks/design_haiku_20260223_124652--mcp-remote-direct--sgonly_flipt-protobuf-metadata-design-001.md) | [source](../../benchmarks/ccb_design/flipt-protobuf-metadata-design-001) | `mcp-remote-direct` | `passed` | 0.330 | 2 | 0.345 |
| [flipt-transitive-deps-001](../tasks/design_haiku_20260223_124652--baseline-local-direct--flipt-transitive-deps-001.md) | [source](../../benchmarks/ccb_design/flipt-transitive-deps-001) | `baseline-local-direct` | `passed` | 0.856 | 2 | 0.000 |
| [sgonly_flipt-transitive-deps-001](../tasks/design_haiku_20260223_124652--mcp-remote-direct--sgonly_flipt-transitive-deps-001.md) | [source](../../benchmarks/ccb_design/flipt-transitive-deps-001) | `mcp-remote-direct` | `passed` | 0.711 | 2 | 0.949 |
| [k8s-crd-lifecycle-arch-001](../tasks/ccb_design_haiku_20260226_015500_backfill--baseline-local-direct--k8s-crd-lifecycle-arch-001.md) | [source](../../benchmarks/ccb_design/k8s-crd-lifecycle-arch-001) | `baseline-local-direct` | `passed` | 0.690 | 2 | 0.000 |
| [sgonly_k8s-crd-lifecycle-arch-001](../tasks/design_haiku_20260223_124652--mcp-remote-direct--sgonly_k8s-crd-lifecycle-arch-001.md) | [source](../../benchmarks/ccb_design/k8s-crd-lifecycle-arch-001) | `mcp-remote-direct` | `passed` | 0.770 | 2 | 0.829 |
| [k8s-dra-allocation-impact-001](../tasks/ccb_design_haiku_20260226_015500_backfill--baseline-local-direct--k8s-dra-allocation-impact-001.md) | [source](../../benchmarks/ccb_design/k8s-dra-allocation-impact-001) | `baseline-local-direct` | `passed` | 1.000 | 2 | 0.000 |
| [sgonly_k8s-dra-allocation-impact-001](../tasks/design_haiku_20260223_124652--mcp-remote-direct--sgonly_k8s-dra-allocation-impact-001.md) | [source](../../benchmarks/ccb_design/k8s-dra-allocation-impact-001) | `mcp-remote-direct` | `passed` | 0.900 | 2 | 0.913 |
| [k8s-scheduler-arch-001](../tasks/ccb_design_haiku_20260226_015500_backfill--baseline-local-direct--k8s-scheduler-arch-001.md) | [source](../../benchmarks/ccb_design/k8s-scheduler-arch-001) | `baseline-local-direct` | `passed` | 0.730 | 2 | 0.000 |
| [sgonly_k8s-scheduler-arch-001](../tasks/design_haiku_20260223_124652--mcp-remote-direct--sgonly_k8s-scheduler-arch-001.md) | [source](../../benchmarks/ccb_design/k8s-scheduler-arch-001) | `mcp-remote-direct` | `passed` | 0.720 | 2 | 0.773 |
| [k8s-sharedinformer-sym-001](../tasks/design_haiku_20260223_124652--baseline-local-direct--k8s-sharedinformer-sym-001.md) | [source](../../benchmarks/ccb_design/k8s-sharedinformer-sym-001) | `baseline-local-direct` | `passed` | 0.630 | 2 | 0.000 |
| [sgonly_k8s-sharedinformer-sym-001](../tasks/design_haiku_20260223_124652--mcp-remote-direct--sgonly_k8s-sharedinformer-sym-001.md) | [source](../../benchmarks/ccb_design/k8s-sharedinformer-sym-001) | `mcp-remote-direct` | `passed` | 0.620 | 2 | 0.967 |
| [k8s-typemeta-dep-chain-001](../tasks/design_haiku_20260223_124652--baseline-local-direct--k8s-typemeta-dep-chain-001.md) | [source](../../benchmarks/ccb_design/k8s-typemeta-dep-chain-001) | `baseline-local-direct` | `passed` | 0.330 | 2 | 0.000 |
| [sgonly_k8s-typemeta-dep-chain-001](../tasks/design_haiku_20260223_124652--mcp-remote-direct--sgonly_k8s-typemeta-dep-chain-001.md) | [source](../../benchmarks/ccb_design/k8s-typemeta-dep-chain-001) | `mcp-remote-direct` | `passed` | 0.670 | 2 | 0.833 |
| [kafka-flink-streaming-arch-001](../tasks/ccb_design_haiku_20260226_015500_backfill--baseline-local-direct--kafka-flink-streaming-arch-001.md) | [source](../../benchmarks/ccb_design/kafka-flink-streaming-arch-001) | `baseline-local-direct` | `passed` | 0.970 | 2 | 0.000 |
| [sgonly_kafka-flink-streaming-arch-001](../tasks/design_haiku_20260223_124652--mcp-remote-direct--sgonly_kafka-flink-streaming-arch-001.md) | [source](../../benchmarks/ccb_design/kafka-flink-streaming-arch-001) | `mcp-remote-direct` | `passed` | 0.400 | 2 | 0.896 |
| [postgres-query-exec-arch-001](../tasks/design_haiku_20260223_124652--baseline-local-direct--postgres-query-exec-arch-001.md) | [source](../../benchmarks/ccb_design/postgres-query-exec-arch-001) | `baseline-local-direct` | `passed` | 0.840 | 2 | 0.000 |
| [sgonly_postgres-query-exec-arch-001](../tasks/design_haiku_20260223_124652--mcp-remote-direct--sgonly_postgres-query-exec-arch-001.md) | [source](../../benchmarks/ccb_design/postgres-query-exec-arch-001) | `mcp-remote-direct` | `passed` | 0.830 | 2 | 0.976 |
| [quantlib-barrier-pricing-arch-001](../tasks/design_haiku_20260223_124652--baseline-local-direct--quantlib-barrier-pricing-arch-001.md) | [source](../../benchmarks/ccb_design/quantlib-barrier-pricing-arch-001) | `baseline-local-direct` | `passed` | 0.850 | 2 | 0.000 |
| [sgonly_quantlib-barrier-pricing-arch-001](../tasks/design_haiku_20260223_124652--mcp-remote-direct--sgonly_quantlib-barrier-pricing-arch-001.md) | [source](../../benchmarks/ccb_design/quantlib-barrier-pricing-arch-001) | `mcp-remote-direct` | `passed` | 0.830 | 2 | 0.968 |
| [terraform-provider-iface-sym-001](../tasks/design_haiku_20260223_124652--baseline-local-direct--terraform-provider-iface-sym-001.md) | [source](../../benchmarks/ccb_design/terraform-provider-iface-sym-001) | `baseline-local-direct` | `passed` | 0.120 | 2 | 0.000 |
| [sgonly_terraform-provider-iface-sym-001](../tasks/design_haiku_20260223_124652--mcp-remote-direct--sgonly_terraform-provider-iface-sym-001.md) | [source](../../benchmarks/ccb_design/terraform-provider-iface-sym-001) | `mcp-remote-direct` | `passed` | 0.090 | 2 | 0.929 |

## Multi-Run Variance

Tasks with multiple valid runs (7 task/config pairs).

| Task | Benchmark | Config | Runs | Mean | Std | Individual Rewards |
|---|---|---|---:|---:|---:|---|
| camel-routing-arch-001 | [source](../../benchmarks/ccb_design/camel-routing-arch-001) | `baseline-local-direct` | 2 | 0.870 | 0.000 | 0.870, 0.870 |
| etcd-grpc-api-upgrade-001 | [source](../../benchmarks/ccb_design/etcd-grpc-api-upgrade-001) | `baseline-local-direct` | 2 | 0.000 | 0.000 | 0.000, 0.000 |
| flink-checkpoint-arch-001 | [source](../../benchmarks/ccb_design/flink-checkpoint-arch-001) | `baseline-local-direct` | 2 | 0.800 | 0.000 | 0.800, 0.800 |
| k8s-crd-lifecycle-arch-001 | [source](../../benchmarks/ccb_design/k8s-crd-lifecycle-arch-001) | `baseline-local-direct` | 2 | 0.690 | 0.000 | 0.690, 0.690 |
| k8s-dra-allocation-impact-001 | [source](../../benchmarks/ccb_design/k8s-dra-allocation-impact-001) | `baseline-local-direct` | 2 | 1.000 | 0.000 | 1.000, 1.000 |
| k8s-scheduler-arch-001 | [source](../../benchmarks/ccb_design/k8s-scheduler-arch-001) | `baseline-local-direct` | 2 | 0.730 | 0.000 | 0.730, 0.730 |
| kafka-flink-streaming-arch-001 | [source](../../benchmarks/ccb_design/kafka-flink-streaming-arch-001) | `baseline-local-direct` | 2 | 0.970 | 0.000 | 0.970, 0.970 |
