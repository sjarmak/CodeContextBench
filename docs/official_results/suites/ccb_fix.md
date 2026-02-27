# ccb_fix

## Run/Config Summary

| Run | Config | Valid Tasks | Mean Reward | Pass Rate |
|---|---|---:|---:|---:|
| [ccb_fix_haiku_20260224_203138](../runs/ccb_fix_haiku_20260224_203138.md) | `baseline-local-direct` | 1 | 0.710 | 1.000 |
| [ccb_fix_haiku_20260224_203138](../runs/ccb_fix_haiku_20260224_203138.md) | `mcp-remote-direct` | 1 | 0.740 | 1.000 |
| [fix_haiku_20260223_171232](../runs/fix_haiku_20260223_171232.md) | `baseline-local-direct` | 19 | 0.479 | 0.632 |
| [fix_haiku_20260223_171232](../runs/fix_haiku_20260223_171232.md) | `mcp-remote-direct` | 18 | 0.508 | 0.611 |
| [fix_haiku_20260224_011821](../runs/fix_haiku_20260224_011821.md) | `baseline-local-direct` | 2 | 0.000 | 0.000 |
| [fix_haiku_20260224_011821](../runs/fix_haiku_20260224_011821.md) | `mcp-remote-direct` | 3 | 0.260 | 0.333 |
| [fix_haiku_20260226_024454](../runs/fix_haiku_20260226_024454.md) | `baseline-local-direct` | 3 | 0.000 | 0.000 |
| [fix_haiku_20260226_024454](../runs/fix_haiku_20260226_024454.md) | `mcp-remote-direct` | 3 | 0.000 | 0.000 |
| [fix_haiku_20260226_new3tasks](../runs/fix_haiku_20260226_new3tasks.md) | `baseline-local-direct` | 3 | 0.727 | 1.000 |
| [fix_haiku_20260226_new3tasks](../runs/fix_haiku_20260226_new3tasks.md) | `mcp-remote-direct` | 3 | 0.801 | 1.000 |

## Tasks

| Task | Benchmark | Config | Status | Reward | Runs | MCP Ratio |
|---|---|---|---|---:|---:|---:|
| [ansible-abc-imports-fix-001](../tasks/fix_haiku_20260223_171232--baseline-local-direct--ansible-abc-imports-fix-001.md) | [source](../../benchmarks/ccb_fix/ansible-abc-imports-fix-001) | `baseline-local-direct` | `passed` | 0.943 | 2 | 0.000 |
| [sgonly_ansible-abc-imports-fix-001](../tasks/fix_haiku_20260223_171232--mcp-remote-direct--sgonly_ansible-abc-imports-fix-001.md) | [source](../../benchmarks/ccb_fix/ansible-abc-imports-fix-001) | `mcp-remote-direct` | `passed` | 1.000 | 2 | 0.299 |
| [ansible-module-respawn-fix-001](../tasks/fix_haiku_20260223_171232--baseline-local-direct--ansible-module-respawn-fix-001.md) | [source](../../benchmarks/ccb_fix/ansible-module-respawn-fix-001) | `baseline-local-direct` | `passed` | 0.471 | 3 | 0.000 |
| [sgonly_ansible-module-respawn-fix-001](../tasks/fix_haiku_20260223_171232--mcp-remote-direct--sgonly_ansible-module-respawn-fix-001.md) | [source](../../benchmarks/ccb_fix/ansible-module-respawn-fix-001) | `mcp-remote-direct` | `failed` | 0.000 | 1 | 0.291 |
| [django-modelchoice-fk-fix-001](../tasks/fix_haiku_20260223_171232--baseline-local-direct--django-modelchoice-fk-fix-001.md) | [source](../../benchmarks/ccb_fix/django-modelchoice-fk-fix-001) | `baseline-local-direct` | `passed` | 0.450 | 2 | 0.000 |
| [sgonly_django-modelchoice-fk-fix-001](../tasks/fix_haiku_20260223_171232--mcp-remote-direct--sgonly_django-modelchoice-fk-fix-001.md) | [source](../../benchmarks/ccb_fix/django-modelchoice-fk-fix-001) | `mcp-remote-direct` | `passed` | 0.450 | 2 | 0.655 |
| [django-select-for-update-fix-001](../tasks/fix_haiku_20260223_171232--baseline-local-direct--django-select-for-update-fix-001.md) | [source](../../benchmarks/ccb_fix/django-select-for-update-fix-001) | `baseline-local-direct` | `passed` | 0.670 | 2 | 0.000 |
| [sgonly_django-select-for-update-fix-001](../tasks/fix_haiku_20260223_171232--mcp-remote-direct--sgonly_django-select-for-update-fix-001.md) | [source](../../benchmarks/ccb_fix/django-select-for-update-fix-001) | `mcp-remote-direct` | `passed` | 0.780 | 2 | 0.711 |
| [envoy-dfp-host-leak-fix-001](../tasks/fix_haiku_20260226_new3tasks--baseline-local-direct--envoy-dfp-host-leak-fix-001.md) | [source](../../benchmarks/ccb_fix/envoy-dfp-host-leak-fix-001) | `baseline-local-direct` | `passed` | 0.727 | 1 | 0.000 |
| [sgonly_envoy-dfp-host-leak-fix-001](../tasks/fix_haiku_20260226_new3tasks--mcp-remote-direct--sgonly_envoy-dfp-host-leak-fix-001.md) | [source](../../benchmarks/ccb_fix/envoy-dfp-host-leak-fix-001) | `mcp-remote-direct` | `passed` | 0.665 | 1 | 0.345 |
| [envoy-udp-proxy-cds-fix-001](../tasks/fix_haiku_20260226_new3tasks--baseline-local-direct--envoy-udp-proxy-cds-fix-001.md) | [source](../../benchmarks/ccb_fix/envoy-udp-proxy-cds-fix-001) | `baseline-local-direct` | `passed` | 0.755 | 1 | 0.000 |
| [sgonly_envoy-udp-proxy-cds-fix-001](../tasks/fix_haiku_20260226_new3tasks--mcp-remote-direct--sgonly_envoy-udp-proxy-cds-fix-001.md) | [source](../../benchmarks/ccb_fix/envoy-udp-proxy-cds-fix-001) | `mcp-remote-direct` | `passed` | 0.784 | 1 | 0.485 |
| [flipt-cockroachdb-backend-fix-001](../tasks/fix_haiku_20260223_171232--baseline-local-direct--flipt-cockroachdb-backend-fix-001.md) | [source](../../benchmarks/ccb_fix/flipt-cockroachdb-backend-fix-001) | `baseline-local-direct` | `passed` | 0.973 | 2 | 0.000 |
| [sgonly_flipt-cockroachdb-backend-fix-001](../tasks/fix_haiku_20260223_171232--mcp-remote-direct--sgonly_flipt-cockroachdb-backend-fix-001.md) | [source](../../benchmarks/ccb_fix/flipt-cockroachdb-backend-fix-001) | `mcp-remote-direct` | `passed` | 0.973 | 2 | 0.508 |
| [flipt-ecr-auth-oci-fix-001](../tasks/fix_haiku_20260223_171232--baseline-local-direct--flipt-ecr-auth-oci-fix-001.md) | [source](../../benchmarks/ccb_fix/flipt-ecr-auth-oci-fix-001) | `baseline-local-direct` | `passed` | 0.987 | 2 | 0.000 |
| [sgonly_flipt-ecr-auth-oci-fix-001](../tasks/fix_haiku_20260223_171232--mcp-remote-direct--sgonly_flipt-ecr-auth-oci-fix-001.md) | [source](../../benchmarks/ccb_fix/flipt-ecr-auth-oci-fix-001) | `mcp-remote-direct` | `passed` | 0.995 | 2 | 0.139 |
| [flipt-eval-latency-fix-001](../tasks/fix_haiku_20260223_171232--baseline-local-direct--flipt-eval-latency-fix-001.md) | [source](../../benchmarks/ccb_fix/flipt-eval-latency-fix-001) | `baseline-local-direct` | `passed` | 0.550 | 2 | 0.000 |
| [sgonly_flipt-eval-latency-fix-001](../tasks/fix_haiku_20260223_171232--mcp-remote-direct--sgonly_flipt-eval-latency-fix-001.md) | [source](../../benchmarks/ccb_fix/flipt-eval-latency-fix-001) | `mcp-remote-direct` | `failed` | 0.000 | 2 | 0.200 |
| [flipt-otlp-exporter-fix-001](../tasks/fix_haiku_20260223_171232--baseline-local-direct--flipt-otlp-exporter-fix-001.md) | [source](../../benchmarks/ccb_fix/flipt-otlp-exporter-fix-001) | `baseline-local-direct` | `passed` | 0.978 | 2 | 0.000 |
| [sgonly_flipt-otlp-exporter-fix-001](../tasks/fix_haiku_20260223_171232--mcp-remote-direct--sgonly_flipt-otlp-exporter-fix-001.md) | [source](../../benchmarks/ccb_fix/flipt-otlp-exporter-fix-001) | `mcp-remote-direct` | `passed` | 0.979 | 2 | 0.221 |
| [flipt-trace-sampling-fix-001](../tasks/fix_haiku_20260223_171232--baseline-local-direct--flipt-trace-sampling-fix-001.md) | [source](../../benchmarks/ccb_fix/flipt-trace-sampling-fix-001) | `baseline-local-direct` | `passed` | 0.987 | 2 | 0.000 |
| [sgonly_flipt-trace-sampling-fix-001](../tasks/fix_haiku_20260223_171232--mcp-remote-direct--sgonly_flipt-trace-sampling-fix-001.md) | [source](../../benchmarks/ccb_fix/flipt-trace-sampling-fix-001) | `mcp-remote-direct` | `passed` | 0.985 | 2 | 0.119 |
| [k8s-dra-scheduler-event-fix-001](../tasks/fix_haiku_20260223_171232--baseline-local-direct--k8s-dra-scheduler-event-fix-001.md) | [source](../../benchmarks/ccb_fix/k8s-dra-scheduler-event-fix-001) | `baseline-local-direct` | `passed` | 0.680 | 2 | 0.000 |
| [sgonly_k8s-dra-scheduler-event-fix-001](../tasks/fix_haiku_20260223_171232--mcp-remote-direct--sgonly_k8s-dra-scheduler-event-fix-001.md) | [source](../../benchmarks/ccb_fix/k8s-dra-scheduler-event-fix-001) | `mcp-remote-direct` | `passed` | 0.750 | 2 | 0.810 |
| [kafka-producer-bufpool-fix-001](../tasks/ccb_fix_haiku_20260224_203138--baseline-local-direct--kafka-producer-bufpool-fix-001.md) | [source](../../benchmarks/ccb_fix/kafka-producer-bufpool-fix-001) | `baseline-local-direct` | `passed` | 0.710 | 2 | 0.000 |
| [mcp_kafka-producer-bufpool-fix-001_2pvDVv](../tasks/ccb_fix_haiku_20260224_203138--mcp-remote-direct--mcp_kafka-producer-bufpool-fix-001_2pvDVv.md) | [source](../../benchmarks/ccb_fix/kafka-producer-bufpool-fix-001) | `mcp-remote-direct` | `passed` | 0.740 | 3 | 0.955 |
| [sgonly_kafka-producer-bufpool-fix-001](../tasks/fix_haiku_20260224_011821--mcp-remote-direct--sgonly_kafka-producer-bufpool-fix-001.md) | [source](../../benchmarks/ccb_fix/kafka-producer-bufpool-fix-001) | `mcp-remote-direct` | `passed` | 0.780 | 3 | 0.900 |
| [navidrome-windows-log-fix-001](../tasks/fix_haiku_20260226_024454--baseline-local-direct--navidrome-windows-log-fix-001.md) | [source](../../benchmarks/ccb_fix/navidrome-windows-log-fix-001) | `baseline-local-direct` | `failed` | 0.000 | 2 | 0.000 |
| [sgonly_navidrome-windows-log-fix-001](../tasks/fix_haiku_20260226_024454--mcp-remote-direct--sgonly_navidrome-windows-log-fix-001.md) | [source](../../benchmarks/ccb_fix/navidrome-windows-log-fix-001) | `mcp-remote-direct` | `failed` | 0.000 | 2 | 0.286 |
| [nodebb-notif-dropdown-fix-001](../tasks/fix_haiku_20260223_171232--baseline-local-direct--nodebb-notif-dropdown-fix-001.md) | [source](../../benchmarks/ccb_fix/nodebb-notif-dropdown-fix-001) | `baseline-local-direct` | `failed` | 0.000 | 2 | 0.000 |
| [sgonly_nodebb-notif-dropdown-fix-001](../tasks/fix_haiku_20260223_171232--mcp-remote-direct--sgonly_nodebb-notif-dropdown-fix-001.md) | [source](../../benchmarks/ccb_fix/nodebb-notif-dropdown-fix-001) | `mcp-remote-direct` | `failed` | 0.000 | 2 | 0.446 |
| [nodebb-plugin-validate-fix-001](../tasks/fix_haiku_20260226_024454--baseline-local-direct--nodebb-plugin-validate-fix-001.md) | [source](../../benchmarks/ccb_fix/nodebb-plugin-validate-fix-001) | `baseline-local-direct` | `failed` | 0.000 | 2 | 0.000 |
| [sgonly_nodebb-plugin-validate-fix-001](../tasks/fix_haiku_20260226_024454--mcp-remote-direct--sgonly_nodebb-plugin-validate-fix-001.md) | [source](../../benchmarks/ccb_fix/nodebb-plugin-validate-fix-001) | `mcp-remote-direct` | `failed` | 0.000 | 2 | 0.125 |
| [openlibrary-fntocli-adapter-fix-001](../tasks/fix_haiku_20260223_171232--baseline-local-direct--openlibrary-fntocli-adapter-fix-001.md) | [source](../../benchmarks/ccb_fix/openlibrary-fntocli-adapter-fix-001) | `baseline-local-direct` | `passed` | 0.667 | 2 | 0.000 |
| [sgonly_openlibrary-fntocli-adapter-fix-001](../tasks/fix_haiku_20260223_171232--mcp-remote-direct--sgonly_openlibrary-fntocli-adapter-fix-001.md) | [source](../../benchmarks/ccb_fix/openlibrary-fntocli-adapter-fix-001) | `mcp-remote-direct` | `passed` | 1.000 | 2 | 0.108 |
| [openlibrary-search-query-fix-001](../tasks/fix_haiku_20260226_024454--baseline-local-direct--openlibrary-search-query-fix-001.md) | [source](../../benchmarks/ccb_fix/openlibrary-search-query-fix-001) | `baseline-local-direct` | `failed` | 0.000 | 2 | 0.000 |
| [sgonly_openlibrary-search-query-fix-001](../tasks/fix_haiku_20260226_024454--mcp-remote-direct--sgonly_openlibrary-search-query-fix-001.md) | [source](../../benchmarks/ccb_fix/openlibrary-search-query-fix-001) | `mcp-remote-direct` | `failed` | 0.000 | 2 | 0.175 |
| [openlibrary-solr-boolean-fix-001](../tasks/fix_haiku_20260223_171232--baseline-local-direct--openlibrary-solr-boolean-fix-001.md) | [source](../../benchmarks/ccb_fix/openlibrary-solr-boolean-fix-001) | `baseline-local-direct` | `failed` | 0.000 | 2 | - |
| [sgonly_openlibrary-solr-boolean-fix-001](../tasks/fix_haiku_20260223_171232--mcp-remote-direct--sgonly_openlibrary-solr-boolean-fix-001.md) | [source](../../benchmarks/ccb_fix/openlibrary-solr-boolean-fix-001) | `mcp-remote-direct` | `passed` | 0.667 | 3 | - |
| [protonmail-conv-testhooks-fix-001](../tasks/fix_haiku_20260223_171232--baseline-local-direct--protonmail-conv-testhooks-fix-001.md) | — | `baseline-local-direct` | `failed` | 0.000 | 1 | - |
| [protonmail-dropdown-sizing-fix-001](../tasks/fix_haiku_20260224_011821--baseline-local-direct--protonmail-dropdown-sizing-fix-001.md) | — | `baseline-local-direct` | `failed` | 0.000 | 2 | - |
| [sgonly_protonmail-dropdown-sizing-fix-001](../tasks/fix_haiku_20260224_011821--mcp-remote-direct--sgonly_protonmail-dropdown-sizing-fix-001.md) | — | `mcp-remote-direct` | `failed` | 0.000 | 1 | - |
| [protonmail-holiday-calendar-fix-001](../tasks/fix_haiku_20260224_011821--baseline-local-direct--protonmail-holiday-calendar-fix-001.md) | — | `baseline-local-direct` | `failed` | 0.000 | 2 | - |
| [sgonly_protonmail-holiday-calendar-fix-001](../tasks/fix_haiku_20260224_011821--mcp-remote-direct--sgonly_protonmail-holiday-calendar-fix-001.md) | — | `mcp-remote-direct` | `failed` | 0.000 | 1 | - |
| [pytorch-cudnn-version-fix-001](../tasks/fix_haiku_20260223_171232--baseline-local-direct--pytorch-cudnn-version-fix-001.md) | [source](../../benchmarks/ccb_fix/pytorch-cudnn-version-fix-001) | `baseline-local-direct` | `failed` | 0.000 | 2 | 0.000 |
| [sgonly_pytorch-cudnn-version-fix-001](../tasks/fix_haiku_20260223_171232--mcp-remote-direct--sgonly_pytorch-cudnn-version-fix-001.md) | [source](../../benchmarks/ccb_fix/pytorch-cudnn-version-fix-001) | `mcp-remote-direct` | `failed` | 0.000 | 2 | 0.586 |
| [pytorch-dynamo-keyerror-fix-001](../tasks/fix_haiku_20260223_171232--baseline-local-direct--pytorch-dynamo-keyerror-fix-001.md) | [source](../../benchmarks/ccb_fix/pytorch-dynamo-keyerror-fix-001) | `baseline-local-direct` | `failed` | 0.000 | 2 | 0.000 |
| [sgonly_pytorch-dynamo-keyerror-fix-001](../tasks/fix_haiku_20260223_171232--mcp-remote-direct--sgonly_pytorch-dynamo-keyerror-fix-001.md) | [source](../../benchmarks/ccb_fix/pytorch-dynamo-keyerror-fix-001) | `mcp-remote-direct` | `failed` | 0.000 | 2 | 0.625 |
| [pytorch-release-210-fix-001](../tasks/fix_haiku_20260223_171232--baseline-local-direct--pytorch-release-210-fix-001.md) | [source](../../benchmarks/ccb_fix/pytorch-release-210-fix-001) | `baseline-local-direct` | `failed` | 0.000 | 2 | 0.000 |
| [sgonly_pytorch-release-210-fix-001](../tasks/fix_haiku_20260223_171232--mcp-remote-direct--sgonly_pytorch-release-210-fix-001.md) | [source](../../benchmarks/ccb_fix/pytorch-release-210-fix-001) | `mcp-remote-direct` | `failed` | 0.000 | 2 | 0.241 |
| [pytorch-relu-gelu-fusion-fix-001](../tasks/fix_haiku_20260223_171232--baseline-local-direct--pytorch-relu-gelu-fusion-fix-001.md) | [source](../../benchmarks/ccb_fix/pytorch-relu-gelu-fusion-fix-001) | `baseline-local-direct` | `passed` | 0.739 | 2 | 0.000 |
| [sgonly_pytorch-relu-gelu-fusion-fix-001](../tasks/fix_haiku_20260223_171232--mcp-remote-direct--sgonly_pytorch-relu-gelu-fusion-fix-001.md) | [source](../../benchmarks/ccb_fix/pytorch-relu-gelu-fusion-fix-001) | `mcp-remote-direct` | `passed` | 0.561 | 2 | 0.370 |
| [pytorch-tracer-graph-cleanup-fix-001](../tasks/fix_haiku_20260223_171232--baseline-local-direct--pytorch-tracer-graph-cleanup-fix-001.md) | [source](../../benchmarks/ccb_fix/pytorch-tracer-graph-cleanup-fix-001) | `baseline-local-direct` | `failed` | 0.000 | 2 | 0.000 |
| [sgonly_pytorch-tracer-graph-cleanup-fix-001](../tasks/fix_haiku_20260223_171232--mcp-remote-direct--sgonly_pytorch-tracer-graph-cleanup-fix-001.md) | [source](../../benchmarks/ccb_fix/pytorch-tracer-graph-cleanup-fix-001) | `mcp-remote-direct` | `failed` | 0.000 | 2 | 0.217 |
| [terraform-plan-null-unknown-fix-001](../tasks/fix_haiku_20260226_new3tasks--baseline-local-direct--terraform-plan-null-unknown-fix-001.md) | [source](../../benchmarks/ccb_fix/terraform-plan-null-unknown-fix-001) | `baseline-local-direct` | `passed` | 0.699 | 1 | 0.000 |
| [sgonly_terraform-plan-null-unknown-fix-001](../tasks/fix_haiku_20260226_new3tasks--mcp-remote-direct--sgonly_terraform-plan-null-unknown-fix-001.md) | [source](../../benchmarks/ccb_fix/terraform-plan-null-unknown-fix-001) | `mcp-remote-direct` | `passed` | 0.955 | 1 | 0.193 |

## Multi-Run Variance

Tasks with multiple valid runs (10 task/config pairs).

| Task | Benchmark | Config | Runs | Mean | Std | Individual Rewards |
|---|---|---|---:|---:|---:|---|
| ansible-module-respawn-fix-001 | [source](../../benchmarks/ccb_fix/ansible-module-respawn-fix-001) | `baseline-local-direct` | 2 | 0.471 | 0.000 | 0.471, 0.471 |
| kafka-producer-bufpool-fix-001 | [source](../../benchmarks/ccb_fix/kafka-producer-bufpool-fix-001) | `mcp-remote-direct` | 3 | 0.767 | 0.023 | 0.780, 0.780, 0.740 |
| navidrome-windows-log-fix-001 | [source](../../benchmarks/ccb_fix/navidrome-windows-log-fix-001) | `baseline-local-direct` | 2 | 0.000 | 0.000 | 0.000, 0.000 |
| navidrome-windows-log-fix-001 | [source](../../benchmarks/ccb_fix/navidrome-windows-log-fix-001) | `mcp-remote-direct` | 2 | 0.000 | 0.000 | 0.000, 0.000 |
| nodebb-plugin-validate-fix-001 | [source](../../benchmarks/ccb_fix/nodebb-plugin-validate-fix-001) | `baseline-local-direct` | 2 | 0.000 | 0.000 | 0.000, 0.000 |
| nodebb-plugin-validate-fix-001 | [source](../../benchmarks/ccb_fix/nodebb-plugin-validate-fix-001) | `mcp-remote-direct` | 2 | 0.000 | 0.000 | 0.000, 0.000 |
| openlibrary-search-query-fix-001 | [source](../../benchmarks/ccb_fix/openlibrary-search-query-fix-001) | `baseline-local-direct` | 2 | 0.000 | 0.000 | 0.000, 0.000 |
| openlibrary-search-query-fix-001 | [source](../../benchmarks/ccb_fix/openlibrary-search-query-fix-001) | `mcp-remote-direct` | 2 | 0.000 | 0.000 | 0.000, 0.000 |
| openlibrary-solr-boolean-fix-001 | [source](../../benchmarks/ccb_fix/openlibrary-solr-boolean-fix-001) | `baseline-local-direct` | 2 | 0.000 | 0.000 | 0.000, 0.000 |
| openlibrary-solr-boolean-fix-001 | [source](../../benchmarks/ccb_fix/openlibrary-solr-boolean-fix-001) | `mcp-remote-direct` | 2 | 0.667 | 0.000 | 0.667, 0.667 |
