# ccb_understand

## Run/Config Summary

| Run | Config | Valid Tasks | Mean Reward | Pass Rate |
|---|---|---:|---:|---:|
| [understand_haiku_20260224_001815](../runs/understand_haiku_20260224_001815.md) | `baseline-local-direct` | 13 | 0.592 | 0.692 |
| [understand_haiku_20260224_001815](../runs/understand_haiku_20260224_001815.md) | `mcp-remote-direct` | 13 | 0.841 | 1.000 |
| [understand_haiku_20260225_211346](../runs/understand_haiku_20260225_211346.md) | `baseline-local-direct` | 7 | 0.789 | 1.000 |
| [understand_haiku_20260225_211346](../runs/understand_haiku_20260225_211346.md) | `mcp-remote-direct` | 7 | 0.870 | 1.000 |

## Tasks

| Task | Benchmark | Config | Status | Reward | Runs | MCP Ratio |
|---|---|---|---|---:|---:|---:|
| [argocd-arch-orient-001](../tasks/understand_haiku_20260224_001815--baseline-local-direct--argocd-arch-orient-001.md) | [source](../../benchmarks/ccb_understand/argocd-arch-orient-001) | `baseline-local-direct` | `failed` | 0.000 | 2 | 0.000 |
| [sgonly_argocd-arch-orient-001](../tasks/understand_haiku_20260224_001815--mcp-remote-direct--sgonly_argocd-arch-orient-001.md) | [source](../../benchmarks/ccb_understand/argocd-arch-orient-001) | `mcp-remote-direct` | `passed` | 0.810 | 2 | 0.977 |
| [argocd-sync-reconcile-qa-001](../tasks/understand_haiku_20260224_001815--baseline-local-direct--argocd-sync-reconcile-qa-001.md) | [source](../../benchmarks/ccb_understand/argocd-sync-reconcile-qa-001) | `baseline-local-direct` | `passed` | 0.920 | 2 | 0.000 |
| [sgonly_argocd-sync-reconcile-qa-001](../tasks/understand_haiku_20260224_001815--mcp-remote-direct--sgonly_argocd-sync-reconcile-qa-001.md) | [source](../../benchmarks/ccb_understand/argocd-sync-reconcile-qa-001) | `mcp-remote-direct` | `passed` | 0.830 | 2 | 0.970 |
| [cilium-ebpf-datapath-handoff-001](../tasks/understand_haiku_20260224_001815--baseline-local-direct--cilium-ebpf-datapath-handoff-001.md) | [source](../../benchmarks/ccb_understand/cilium-ebpf-datapath-handoff-001) | `baseline-local-direct` | `passed` | 1.000 | 2 | 0.000 |
| [sgonly_cilium-ebpf-datapath-handoff-001](../tasks/understand_haiku_20260224_001815--mcp-remote-direct--sgonly_cilium-ebpf-datapath-handoff-001.md) | [source](../../benchmarks/ccb_understand/cilium-ebpf-datapath-handoff-001) | `mcp-remote-direct` | `passed` | 0.830 | 2 | 0.968 |
| [cilium-ebpf-fault-qa-001](../tasks/understand_haiku_20260224_001815--baseline-local-direct--cilium-ebpf-fault-qa-001.md) | [source](../../benchmarks/ccb_understand/cilium-ebpf-fault-qa-001) | `baseline-local-direct` | `passed` | 0.770 | 2 | 0.000 |
| [sgonly_cilium-ebpf-fault-qa-001](../tasks/understand_haiku_20260224_001815--mcp-remote-direct--sgonly_cilium-ebpf-fault-qa-001.md) | [source](../../benchmarks/ccb_understand/cilium-ebpf-fault-qa-001) | `mcp-remote-direct` | `passed` | 0.820 | 2 | 0.973 |
| [cilium-project-orient-001](../tasks/understand_haiku_20260224_001815--baseline-local-direct--cilium-project-orient-001.md) | [source](../../benchmarks/ccb_understand/cilium-project-orient-001) | `baseline-local-direct` | `failed` | 0.000 | 2 | 0.000 |
| [sgonly_cilium-project-orient-001](../tasks/understand_haiku_20260224_001815--mcp-remote-direct--sgonly_cilium-project-orient-001.md) | [source](../../benchmarks/ccb_understand/cilium-project-orient-001) | `mcp-remote-direct` | `passed` | 0.960 | 2 | 0.974 |
| [django-composite-field-recover-001](../tasks/understand_haiku_20260225_211346--baseline-local-direct--django-composite-field-recover-001.md) | [source](../../benchmarks/ccb_understand/django-composite-field-recover-001) | `baseline-local-direct` | `passed` | 0.400 | 2 | 0.000 |
| [sgonly_django-composite-field-recover-001](../tasks/understand_haiku_20260225_211346--mcp-remote-direct--sgonly_django-composite-field-recover-001.md) | [source](../../benchmarks/ccb_understand/django-composite-field-recover-001) | `mcp-remote-direct` | `passed` | 0.750 | 2 | 0.290 |
| [django-template-inherit-recall-001](../tasks/understand_haiku_20260224_001815--baseline-local-direct--django-template-inherit-recall-001.md) | [source](../../benchmarks/ccb_understand/django-template-inherit-recall-001) | `baseline-local-direct` | `passed` | 0.250 | 2 | 0.000 |
| [sgonly_django-template-inherit-recall-001](../tasks/understand_haiku_20260224_001815--mcp-remote-direct--sgonly_django-template-inherit-recall-001.md) | [source](../../benchmarks/ccb_understand/django-template-inherit-recall-001) | `mcp-remote-direct` | `passed` | 0.250 | 2 | 0.143 |
| [envoy-contributor-workflow-001](../tasks/understand_haiku_20260224_001815--baseline-local-direct--envoy-contributor-workflow-001.md) | [source](../../benchmarks/ccb_understand/envoy-contributor-workflow-001) | `baseline-local-direct` | `passed` | 0.970 | 2 | 0.000 |
| [sgonly_envoy-contributor-workflow-001](../tasks/understand_haiku_20260224_001815--mcp-remote-direct--sgonly_envoy-contributor-workflow-001.md) | [source](../../benchmarks/ccb_understand/envoy-contributor-workflow-001) | `mcp-remote-direct` | `passed` | 0.910 | 2 | 0.955 |
| [envoy-ext-authz-handoff-001](../tasks/understand_haiku_20260225_211346--baseline-local-direct--envoy-ext-authz-handoff-001.md) | [source](../../benchmarks/ccb_understand/envoy-ext-authz-handoff-001) | `baseline-local-direct` | `passed` | 0.770 | 2 | 0.000 |
| [sgonly_envoy-ext-authz-handoff-001](../tasks/understand_haiku_20260225_211346--mcp-remote-direct--sgonly_envoy-ext-authz-handoff-001.md) | [source](../../benchmarks/ccb_understand/envoy-ext-authz-handoff-001) | `mcp-remote-direct` | `passed` | 0.830 | 2 | 0.960 |
| [envoy-filter-chain-qa-001](../tasks/understand_haiku_20260224_001815--baseline-local-direct--envoy-filter-chain-qa-001.md) | [source](../../benchmarks/ccb_understand/envoy-filter-chain-qa-001) | `baseline-local-direct` | `passed` | 0.970 | 2 | 0.000 |
| [sgonly_envoy-filter-chain-qa-001](../tasks/understand_haiku_20260224_001815--mcp-remote-direct--sgonly_envoy-filter-chain-qa-001.md) | [source](../../benchmarks/ccb_understand/envoy-filter-chain-qa-001) | `mcp-remote-direct` | `passed` | 0.880 | 2 | 0.967 |
| [envoy-request-routing-qa-001](../tasks/understand_haiku_20260224_001815--baseline-local-direct--envoy-request-routing-qa-001.md) | [source](../../benchmarks/ccb_understand/envoy-request-routing-qa-001) | `baseline-local-direct` | `failed` | 0.000 | 2 | 0.000 |
| [sgonly_envoy-request-routing-qa-001](../tasks/understand_haiku_20260224_001815--mcp-remote-direct--sgonly_envoy-request-routing-qa-001.md) | [source](../../benchmarks/ccb_understand/envoy-request-routing-qa-001) | `mcp-remote-direct` | `passed` | 0.870 | 2 | 0.971 |
| [istio-xds-serving-qa-001](../tasks/understand_haiku_20260224_001815--baseline-local-direct--istio-xds-serving-qa-001.md) | [source](../../benchmarks/ccb_understand/istio-xds-serving-qa-001) | `baseline-local-direct` | `passed` | 1.000 | 2 | 0.000 |
| [sgonly_istio-xds-serving-qa-001](../tasks/understand_haiku_20260224_001815--mcp-remote-direct--sgonly_istio-xds-serving-qa-001.md) | [source](../../benchmarks/ccb_understand/istio-xds-serving-qa-001) | `mcp-remote-direct` | `passed` | 1.000 | 2 | 0.971 |
| [k8s-cri-containerd-reason-001](../tasks/understand_haiku_20260225_211346--baseline-local-direct--k8s-cri-containerd-reason-001.md) | [source](../../benchmarks/ccb_understand/k8s-cri-containerd-reason-001) | `baseline-local-direct` | `passed` | 0.850 | 2 | 0.000 |
| [sgonly_k8s-cri-containerd-reason-001](../tasks/understand_haiku_20260225_211346--mcp-remote-direct--sgonly_k8s-cri-containerd-reason-001.md) | [source](../../benchmarks/ccb_understand/k8s-cri-containerd-reason-001) | `mcp-remote-direct` | `passed` | 0.850 | 2 | 0.857 |
| [kafka-build-orient-001](../tasks/understand_haiku_20260225_211346--baseline-local-direct--kafka-build-orient-001.md) | [source](../../benchmarks/ccb_understand/kafka-build-orient-001) | `baseline-local-direct` | `passed` | 0.840 | 2 | 0.000 |
| [sgonly_kafka-build-orient-001](../tasks/understand_haiku_20260225_211346--mcp-remote-direct--sgonly_kafka-build-orient-001.md) | [source](../../benchmarks/ccb_understand/kafka-build-orient-001) | `mcp-remote-direct` | `passed` | 0.870 | 2 | 0.955 |
| [kafka-contributor-workflow-001](../tasks/understand_haiku_20260224_001815--baseline-local-direct--kafka-contributor-workflow-001.md) | [source](../../benchmarks/ccb_understand/kafka-contributor-workflow-001) | `baseline-local-direct` | `passed` | 0.950 | 2 | 0.000 |
| [sgonly_kafka-contributor-workflow-001](../tasks/understand_haiku_20260224_001815--mcp-remote-direct--sgonly_kafka-contributor-workflow-001.md) | [source](../../benchmarks/ccb_understand/kafka-contributor-workflow-001) | `mcp-remote-direct` | `passed` | 0.820 | 2 | 0.955 |
| [kafka-message-lifecycle-qa-001](../tasks/understand_haiku_20260224_001815--baseline-local-direct--kafka-message-lifecycle-qa-001.md) | [source](../../benchmarks/ccb_understand/kafka-message-lifecycle-qa-001) | `baseline-local-direct` | `passed` | 0.860 | 2 | 0.000 |
| [sgonly_kafka-message-lifecycle-qa-001](../tasks/understand_haiku_20260224_001815--mcp-remote-direct--sgonly_kafka-message-lifecycle-qa-001.md) | [source](../../benchmarks/ccb_understand/kafka-message-lifecycle-qa-001) | `mcp-remote-direct` | `passed` | 1.000 | 2 | 0.972 |
| [numpy-dtype-localize-001](../tasks/understand_haiku_20260225_211346--baseline-local-direct--numpy-dtype-localize-001.md) | [source](../../benchmarks/ccb_understand/numpy-dtype-localize-001) | `baseline-local-direct` | `passed` | 1.000 | 2 | 0.000 |
| [sgonly_numpy-dtype-localize-001](../tasks/understand_haiku_20260225_211346--mcp-remote-direct--sgonly_numpy-dtype-localize-001.md) | [source](../../benchmarks/ccb_understand/numpy-dtype-localize-001) | `mcp-remote-direct` | `passed` | 1.000 | 2 | 0.957 |
| [terraform-plan-pipeline-qa-001](../tasks/understand_haiku_20260224_001815--baseline-local-direct--terraform-plan-pipeline-qa-001.md) | [source](../../benchmarks/ccb_understand/terraform-plan-pipeline-qa-001) | `baseline-local-direct` | `failed` | 0.000 | 2 | 0.000 |
| [sgonly_terraform-plan-pipeline-qa-001](../tasks/understand_haiku_20260224_001815--mcp-remote-direct--sgonly_terraform-plan-pipeline-qa-001.md) | [source](../../benchmarks/ccb_understand/terraform-plan-pipeline-qa-001) | `mcp-remote-direct` | `passed` | 0.950 | 2 | 0.971 |
| [terraform-state-backend-handoff-001](../tasks/understand_haiku_20260225_211346--baseline-local-direct--terraform-state-backend-handoff-001.md) | [source](../../benchmarks/ccb_understand/terraform-state-backend-handoff-001) | `baseline-local-direct` | `passed` | 0.710 | 2 | 0.000 |
| [sgonly_terraform-state-backend-handoff-001](../tasks/understand_haiku_20260225_211346--mcp-remote-direct--sgonly_terraform-state-backend-handoff-001.md) | [source](../../benchmarks/ccb_understand/terraform-state-backend-handoff-001) | `mcp-remote-direct` | `passed` | 0.830 | 2 | 0.969 |
| [vscode-ext-host-qa-001](../tasks/understand_haiku_20260225_211346--baseline-local-direct--vscode-ext-host-qa-001.md) | [source](../../benchmarks/ccb_understand/vscode-ext-host-qa-001) | `baseline-local-direct` | `passed` | 0.950 | 2 | 0.000 |
| [sgonly_vscode-ext-host-qa-001](../tasks/understand_haiku_20260225_211346--mcp-remote-direct--sgonly_vscode-ext-host-qa-001.md) | [source](../../benchmarks/ccb_understand/vscode-ext-host-qa-001) | `mcp-remote-direct` | `passed` | 0.960 | 2 | 0.963 |

## Multi-Run Variance

Tasks with multiple valid runs (7 task/config pairs).

| Task | Benchmark | Config | Runs | Mean | Std | Individual Rewards |
|---|---|---|---:|---:|---:|---|
| django-composite-field-recover-001 | [source](../../benchmarks/ccb_understand/django-composite-field-recover-001) | `baseline-local-direct` | 2 | 0.400 | 0.000 | 0.400, 0.400 |
| envoy-ext-authz-handoff-001 | [source](../../benchmarks/ccb_understand/envoy-ext-authz-handoff-001) | `mcp-remote-direct` | 2 | 0.830 | 0.000 | 0.830, 0.830 |
| k8s-cri-containerd-reason-001 | [source](../../benchmarks/ccb_understand/k8s-cri-containerd-reason-001) | `baseline-local-direct` | 2 | 0.850 | 0.000 | 0.850, 0.850 |
| kafka-build-orient-001 | [source](../../benchmarks/ccb_understand/kafka-build-orient-001) | `baseline-local-direct` | 2 | 0.780 | 0.085 | 0.720, 0.840 |
| numpy-dtype-localize-001 | [source](../../benchmarks/ccb_understand/numpy-dtype-localize-001) | `mcp-remote-direct` | 2 | 0.967 | 0.047 | 0.933, 1.000 |
| terraform-state-backend-handoff-001 | [source](../../benchmarks/ccb_understand/terraform-state-backend-handoff-001) | `mcp-remote-direct` | 2 | 0.730 | 0.141 | 0.630, 0.830 |
| vscode-ext-host-qa-001 | [source](../../benchmarks/ccb_understand/vscode-ext-host-qa-001) | `baseline-local-direct` | 2 | 0.975 | 0.035 | 1.000, 0.950 |
