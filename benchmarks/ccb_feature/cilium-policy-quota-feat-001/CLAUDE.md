# cilium-policy-quota-feat-001: Policy Quota Controller

## Task Type: Feature Implementation (Controller)

Implement per-namespace policy quota enforcement in Cilium.

## Key Reference Files
- `pkg/policy/k8s/watcher.go` — policy watcher pattern
- `pkg/k8s/apis/cilium.io/v2/types_cnp.go` — CRD types
- `operator/pkg/ciliumenvoyconfig/` — hive controller pattern
- `pkg/k8s/resource/resource.go` — resource framework

## Search Strategy
- Search for `CiliumNetworkPolicy` to find policy types and watchers
- Search for `hive.Cell` for dependency injection patterns
- Search for `resource.Resource` for K8s resource watching
- Search for `DeepCopyObject` for CRD type patterns
