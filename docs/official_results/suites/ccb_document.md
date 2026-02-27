# ccb_document

## Run/Config Summary

| Run | Config | Valid Tasks | Mean Reward | Pass Rate |
|---|---|---:|---:|---:|
| [ccb_document_haiku_20260224_174311](../runs/ccb_document_haiku_20260224_174311.md) | `baseline-local-direct` | 5 | 0.658 | 1.000 |
| [ccb_document_haiku_20260224_174311](../runs/ccb_document_haiku_20260224_174311.md) | `mcp-remote-direct` | 5 | 0.720 | 1.000 |
| [document_haiku_20260223_164240](../runs/document_haiku_20260223_164240.md) | `baseline-local-direct` | 14 | 0.904 | 1.000 |
| [document_haiku_20260223_164240](../runs/document_haiku_20260223_164240.md) | `mcp-remote-direct` | 20 | 0.822 | 1.000 |
| [document_haiku_20260226_013910](../runs/document_haiku_20260226_013910.md) | `baseline-local-direct` | 1 | 1.000 | 1.000 |

## Tasks

| Task | Benchmark | Config | Status | Reward | Runs | MCP Ratio |
|---|---|---|---|---:|---:|---:|
| [cilium-api-doc-gen-001](../tasks/document_haiku_20260223_164240--baseline-local-direct--cilium-api-doc-gen-001.md) | [source](../../benchmarks/ccb_document/cilium-api-doc-gen-001) | `baseline-local-direct` | `passed` | 0.960 | 2 | 0.000 |
| [sgonly_cilium-api-doc-gen-001](../tasks/document_haiku_20260223_164240--mcp-remote-direct--sgonly_cilium-api-doc-gen-001.md) | [source](../../benchmarks/ccb_document/cilium-api-doc-gen-001) | `mcp-remote-direct` | `passed` | 0.980 | 2 | 0.929 |
| [docgen-changelog-001](../tasks/document_haiku_20260223_164240--baseline-local-direct--docgen-changelog-001.md) | [source](../../benchmarks/ccb_document/docgen-changelog-001) | `baseline-local-direct` | `passed` | 1.000 | 2 | 0.000 |
| [sgonly_docgen-changelog-001](../tasks/document_haiku_20260223_164240--mcp-remote-direct--sgonly_docgen-changelog-001.md) | [source](../../benchmarks/ccb_document/docgen-changelog-001) | `mcp-remote-direct` | `passed` | 1.000 | 2 | 0.921 |
| [docgen-changelog-002](../tasks/document_haiku_20260223_164240--baseline-local-direct--docgen-changelog-002.md) | [source](../../benchmarks/ccb_document/docgen-changelog-002) | `baseline-local-direct` | `passed` | 0.700 | 2 | 0.000 |
| [sgonly_docgen-changelog-002](../tasks/document_haiku_20260223_164240--mcp-remote-direct--sgonly_docgen-changelog-002.md) | [source](../../benchmarks/ccb_document/docgen-changelog-002) | `mcp-remote-direct` | `passed` | 1.000 | 2 | 0.909 |
| [docgen-inline-001](../tasks/document_haiku_20260226_013910--baseline-local-direct--docgen-inline-001.md) | [source](../../benchmarks/ccb_document/docgen-inline-001) | `baseline-local-direct` | `passed` | 1.000 | 2 | 0.000 |
| [sgonly_docgen-inline-001](../tasks/document_haiku_20260223_164240--mcp-remote-direct--sgonly_docgen-inline-001.md) | [source](../../benchmarks/ccb_document/docgen-inline-001) | `mcp-remote-direct` | `passed` | 1.000 | 2 | 0.357 |
| [docgen-inline-002](../tasks/document_haiku_20260223_164240--baseline-local-direct--docgen-inline-002.md) | [source](../../benchmarks/ccb_document/docgen-inline-002) | `baseline-local-direct` | `passed` | 1.000 | 2 | 0.000 |
| [sgonly_docgen-inline-002](../tasks/document_haiku_20260223_164240--mcp-remote-direct--sgonly_docgen-inline-002.md) | [source](../../benchmarks/ccb_document/docgen-inline-002) | `mcp-remote-direct` | `passed` | 1.000 | 2 | 0.206 |
| [docgen-onboard-001](../tasks/document_haiku_20260223_164240--baseline-local-direct--docgen-onboard-001.md) | [source](../../benchmarks/ccb_document/docgen-onboard-001) | `baseline-local-direct` | `passed` | 1.000 | 2 | 0.000 |
| [sgonly_docgen-onboard-001](../tasks/document_haiku_20260223_164240--mcp-remote-direct--sgonly_docgen-onboard-001.md) | [source](../../benchmarks/ccb_document/docgen-onboard-001) | `mcp-remote-direct` | `passed` | 1.000 | 2 | 0.950 |
| [docgen-runbook-001](../tasks/document_haiku_20260223_164240--baseline-local-direct--docgen-runbook-001.md) | [source](../../benchmarks/ccb_document/docgen-runbook-001) | `baseline-local-direct` | `passed` | 1.000 | 2 | 0.000 |
| [sgonly_docgen-runbook-001](../tasks/document_haiku_20260223_164240--mcp-remote-direct--sgonly_docgen-runbook-001.md) | [source](../../benchmarks/ccb_document/docgen-runbook-001) | `mcp-remote-direct` | `passed` | 1.000 | 2 | 0.773 |
| [docgen-runbook-002](../tasks/document_haiku_20260223_164240--baseline-local-direct--docgen-runbook-002.md) | [source](../../benchmarks/ccb_document/docgen-runbook-002) | `baseline-local-direct` | `passed` | 1.000 | 2 | 0.000 |
| [sgonly_docgen-runbook-002](../tasks/document_haiku_20260223_164240--mcp-remote-direct--sgonly_docgen-runbook-002.md) | [source](../../benchmarks/ccb_document/docgen-runbook-002) | `mcp-remote-direct` | `passed` | 1.000 | 2 | 0.857 |
| [envoy-arch-doc-gen-001](../tasks/document_haiku_20260223_164240--baseline-local-direct--envoy-arch-doc-gen-001.md) | [source](../../benchmarks/ccb_document/envoy-arch-doc-gen-001) | `baseline-local-direct` | `passed` | 1.000 | 2 | 0.000 |
| [sgonly_envoy-arch-doc-gen-001](../tasks/document_haiku_20260223_164240--mcp-remote-direct--sgonly_envoy-arch-doc-gen-001.md) | [source](../../benchmarks/ccb_document/envoy-arch-doc-gen-001) | `mcp-remote-direct` | `passed` | 1.000 | 2 | 0.833 |
| [envoy-migration-doc-gen-001](../tasks/document_haiku_20260223_164240--baseline-local-direct--envoy-migration-doc-gen-001.md) | [source](../../benchmarks/ccb_document/envoy-migration-doc-gen-001) | `baseline-local-direct` | `passed` | 0.650 | 2 | 0.000 |
| [sgonly_envoy-migration-doc-gen-001](../tasks/document_haiku_20260223_164240--mcp-remote-direct--sgonly_envoy-migration-doc-gen-001.md) | [source](../../benchmarks/ccb_document/envoy-migration-doc-gen-001) | `mcp-remote-direct` | `passed` | 0.790 | 2 | 0.826 |
| [istio-arch-doc-gen-001](../tasks/document_haiku_20260223_164240--baseline-local-direct--istio-arch-doc-gen-001.md) | [source](../../benchmarks/ccb_document/istio-arch-doc-gen-001) | `baseline-local-direct` | `passed` | 1.000 | 2 | 0.000 |
| [sgonly_istio-arch-doc-gen-001](../tasks/document_haiku_20260223_164240--mcp-remote-direct--sgonly_istio-arch-doc-gen-001.md) | [source](../../benchmarks/ccb_document/istio-arch-doc-gen-001) | `mcp-remote-direct` | `passed` | 1.000 | 2 | 0.962 |
| [k8s-apiserver-doc-gen-001](../tasks/ccb_document_haiku_20260224_174311--baseline-local-direct--k8s-apiserver-doc-gen-001.md) | [source](../../benchmarks/ccb_document/k8s-apiserver-doc-gen-001) | `baseline-local-direct` | `passed` | 0.470 | 2 | 0.000 |
| [mcp_k8s-apiserver-doc-gen-001_e9qHQA](../tasks/ccb_document_haiku_20260224_174311--mcp-remote-direct--mcp_k8s-apiserver-doc-gen-001_e9qHQA.md) | [source](../../benchmarks/ccb_document/k8s-apiserver-doc-gen-001) | `mcp-remote-direct` | `passed` | 0.650 | 2 | 0.875 |
| [sgonly_k8s-apiserver-doc-gen-001](../tasks/document_haiku_20260223_164240--mcp-remote-direct--sgonly_k8s-apiserver-doc-gen-001.md) | [source](../../benchmarks/ccb_document/k8s-apiserver-doc-gen-001) | `mcp-remote-direct` | `passed` | 0.520 | 2 | 0.974 |
| [k8s-applyconfig-doc-gen-001](../tasks/ccb_document_haiku_20260224_174311--baseline-local-direct--k8s-applyconfig-doc-gen-001.md) | [source](../../benchmarks/ccb_document/k8s-applyconfig-doc-gen-001) | `baseline-local-direct` | `passed` | 1.000 | 2 | 0.000 |
| [mcp_k8s-applyconfig-doc-gen-001_JHZsM3](../tasks/ccb_document_haiku_20260224_174311--mcp-remote-direct--mcp_k8s-applyconfig-doc-gen-001_JHZsM3.md) | [source](../../benchmarks/ccb_document/k8s-applyconfig-doc-gen-001) | `mcp-remote-direct` | `passed` | 1.000 | 2 | 0.958 |
| [sgonly_k8s-applyconfig-doc-gen-001](../tasks/document_haiku_20260223_164240--mcp-remote-direct--sgonly_k8s-applyconfig-doc-gen-001.md) | [source](../../benchmarks/ccb_document/k8s-applyconfig-doc-gen-001) | `mcp-remote-direct` | `passed` | 0.650 | 2 | 0.955 |
| [k8s-clientgo-doc-gen-001](../tasks/ccb_document_haiku_20260224_174311--baseline-local-direct--k8s-clientgo-doc-gen-001.md) | [source](../../benchmarks/ccb_document/k8s-clientgo-doc-gen-001) | `baseline-local-direct` | `passed` | 0.650 | 2 | 0.000 |
| [mcp_k8s-clientgo-doc-gen-001_uV7Ssw](../tasks/ccb_document_haiku_20260224_174311--mcp-remote-direct--mcp_k8s-clientgo-doc-gen-001_uV7Ssw.md) | [source](../../benchmarks/ccb_document/k8s-clientgo-doc-gen-001) | `mcp-remote-direct` | `passed` | 0.650 | 2 | 0.868 |
| [sgonly_k8s-clientgo-doc-gen-001](../tasks/document_haiku_20260223_164240--mcp-remote-direct--sgonly_k8s-clientgo-doc-gen-001.md) | [source](../../benchmarks/ccb_document/k8s-clientgo-doc-gen-001) | `mcp-remote-direct` | `passed` | 0.650 | 2 | 0.872 |
| [k8s-fairqueuing-doc-gen-001](../tasks/ccb_document_haiku_20260224_174311--baseline-local-direct--k8s-fairqueuing-doc-gen-001.md) | [source](../../benchmarks/ccb_document/k8s-fairqueuing-doc-gen-001) | `baseline-local-direct` | `passed` | 0.550 | 2 | 0.000 |
| [mcp_k8s-fairqueuing-doc-gen-001_eRPJdR](../tasks/ccb_document_haiku_20260224_174311--mcp-remote-direct--mcp_k8s-fairqueuing-doc-gen-001_eRPJdR.md) | [source](../../benchmarks/ccb_document/k8s-fairqueuing-doc-gen-001) | `mcp-remote-direct` | `passed` | 0.650 | 2 | 0.957 |
| [sgonly_k8s-fairqueuing-doc-gen-001](../tasks/document_haiku_20260223_164240--mcp-remote-direct--sgonly_k8s-fairqueuing-doc-gen-001.md) | [source](../../benchmarks/ccb_document/k8s-fairqueuing-doc-gen-001) | `mcp-remote-direct` | `passed` | 0.020 | 2 | 0.944 |
| [k8s-kubelet-cm-doc-gen-001](../tasks/ccb_document_haiku_20260224_174311--baseline-local-direct--k8s-kubelet-cm-doc-gen-001.md) | [source](../../benchmarks/ccb_document/k8s-kubelet-cm-doc-gen-001) | `baseline-local-direct` | `passed` | 0.620 | 2 | 0.000 |
| [mcp_k8s-kubelet-cm-doc-gen-001_mVr2Xz](../tasks/ccb_document_haiku_20260224_174311--mcp-remote-direct--mcp_k8s-kubelet-cm-doc-gen-001_mVr2Xz.md) | [source](../../benchmarks/ccb_document/k8s-kubelet-cm-doc-gen-001) | `mcp-remote-direct` | `passed` | 0.650 | 2 | 0.968 |
| [sgonly_k8s-kubelet-cm-doc-gen-001](../tasks/document_haiku_20260223_164240--mcp-remote-direct--sgonly_k8s-kubelet-cm-doc-gen-001.md) | [source](../../benchmarks/ccb_document/k8s-kubelet-cm-doc-gen-001) | `mcp-remote-direct` | `passed` | 0.300 | 2 | 0.828 |
| [kafka-api-doc-gen-001](../tasks/document_haiku_20260223_164240--baseline-local-direct--kafka-api-doc-gen-001.md) | [source](../../benchmarks/ccb_document/kafka-api-doc-gen-001) | `baseline-local-direct` | `passed` | 0.940 | 2 | 0.000 |
| [sgonly_kafka-api-doc-gen-001](../tasks/document_haiku_20260223_164240--mcp-remote-direct--sgonly_kafka-api-doc-gen-001.md) | [source](../../benchmarks/ccb_document/kafka-api-doc-gen-001) | `mcp-remote-direct` | `passed` | 0.940 | 2 | 0.794 |
| [terraform-arch-doc-gen-001](../tasks/document_haiku_20260223_164240--baseline-local-direct--terraform-arch-doc-gen-001.md) | [source](../../benchmarks/ccb_document/terraform-arch-doc-gen-001) | `baseline-local-direct` | `passed` | 0.420 | 2 | 0.000 |
| [sgonly_terraform-arch-doc-gen-001](../tasks/document_haiku_20260223_164240--mcp-remote-direct--sgonly_terraform-arch-doc-gen-001.md) | [source](../../benchmarks/ccb_document/terraform-arch-doc-gen-001) | `mcp-remote-direct` | `passed` | 0.590 | 2 | 0.962 |
| [terraform-migration-doc-gen-001](../tasks/document_haiku_20260223_164240--baseline-local-direct--terraform-migration-doc-gen-001.md) | [source](../../benchmarks/ccb_document/terraform-migration-doc-gen-001) | `baseline-local-direct` | `passed` | 1.000 | 2 | 0.000 |
| [sgonly_terraform-migration-doc-gen-001](../tasks/document_haiku_20260223_164240--mcp-remote-direct--sgonly_terraform-migration-doc-gen-001.md) | [source](../../benchmarks/ccb_document/terraform-migration-doc-gen-001) | `mcp-remote-direct` | `passed` | 1.000 | 2 | 0.933 |
| [vscode-api-doc-gen-001](../tasks/document_haiku_20260223_164240--baseline-local-direct--vscode-api-doc-gen-001.md) | [source](../../benchmarks/ccb_document/vscode-api-doc-gen-001) | `baseline-local-direct` | `passed` | 0.980 | 2 | 0.000 |
| [sgonly_vscode-api-doc-gen-001](../tasks/document_haiku_20260223_164240--mcp-remote-direct--sgonly_vscode-api-doc-gen-001.md) | [source](../../benchmarks/ccb_document/vscode-api-doc-gen-001) | `mcp-remote-direct` | `passed` | 1.000 | 2 | 0.952 |

## Multi-Run Variance

Tasks with multiple valid runs (11 task/config pairs).

| Task | Benchmark | Config | Runs | Mean | Std | Individual Rewards |
|---|---|---|---:|---:|---:|---|
| docgen-inline-001 | [source](../../benchmarks/ccb_document/docgen-inline-001) | `baseline-local-direct` | 2 | 1.000 | 0.000 | 1.000, 1.000 |
| k8s-apiserver-doc-gen-001 | [source](../../benchmarks/ccb_document/k8s-apiserver-doc-gen-001) | `baseline-local-direct` | 2 | 0.560 | 0.127 | 0.650, 0.470 |
| k8s-apiserver-doc-gen-001 | [source](../../benchmarks/ccb_document/k8s-apiserver-doc-gen-001) | `mcp-remote-direct` | 2 | 0.585 | 0.092 | 0.520, 0.650 |
| k8s-applyconfig-doc-gen-001 | [source](../../benchmarks/ccb_document/k8s-applyconfig-doc-gen-001) | `baseline-local-direct` | 2 | 0.950 | 0.071 | 0.900, 1.000 |
| k8s-applyconfig-doc-gen-001 | [source](../../benchmarks/ccb_document/k8s-applyconfig-doc-gen-001) | `mcp-remote-direct` | 2 | 0.825 | 0.247 | 0.650, 1.000 |
| k8s-clientgo-doc-gen-001 | [source](../../benchmarks/ccb_document/k8s-clientgo-doc-gen-001) | `baseline-local-direct` | 2 | 0.825 | 0.247 | 1.000, 0.650 |
| k8s-clientgo-doc-gen-001 | [source](../../benchmarks/ccb_document/k8s-clientgo-doc-gen-001) | `mcp-remote-direct` | 2 | 0.650 | 0.000 | 0.650, 0.650 |
| k8s-fairqueuing-doc-gen-001 | [source](../../benchmarks/ccb_document/k8s-fairqueuing-doc-gen-001) | `baseline-local-direct` | 2 | 0.395 | 0.219 | 0.240, 0.550 |
| k8s-fairqueuing-doc-gen-001 | [source](../../benchmarks/ccb_document/k8s-fairqueuing-doc-gen-001) | `mcp-remote-direct` | 2 | 0.335 | 0.446 | 0.020, 0.650 |
| k8s-kubelet-cm-doc-gen-001 | [source](../../benchmarks/ccb_document/k8s-kubelet-cm-doc-gen-001) | `baseline-local-direct` | 2 | 0.675 | 0.078 | 0.730, 0.620 |
| k8s-kubelet-cm-doc-gen-001 | [source](../../benchmarks/ccb_document/k8s-kubelet-cm-doc-gen-001) | `mcp-remote-direct` | 2 | 0.475 | 0.247 | 0.300, 0.650 |
