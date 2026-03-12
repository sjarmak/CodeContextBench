# Cilium Codebase Orientation

## 1. Main Entry Point

**Binary entry point:** `daemon/main.go`

```go
func main() {
    agentHive := hive.New(cmd.Agent)
    cmd.Execute(cmd.NewAgentCmd(agentHive))
}
```

**CLI initialization:** `daemon/cmd/root.go` — `NewAgentCmd(h *hive.Hive) *cobra.Command`
- Uses the `github.com/spf13/cobra` library to create the root `cilium-agent` command.
- Registers all flags via `InitGlobalFlags()` and binds them to viper via `option.BindEnv()`.
- Uses `cobra.OnInitialize()` to wire `option.InitConfig()`, `initDaemonConfig()`, and `initLogging()` before command execution.
- When the command runs, it calls `initEnv()`, validates config, then `h.Run()` to start the hive.

**Dependency injection framework:** `github.com/cilium/hive` (vendored at `vendor/github.com/cilium/hive/`)
- Cilium wraps it in `pkg/hive/hive.go` as `hive.New(cells ...cell.Cell)`.
- The entire agent is organized as a tree of `cell.Module` / `cell.Provide` / `cell.Invoke` cells.
- Top-level decomposition is in `daemon/cmd/cells.go`:
  - `Agent` = `Infrastructure` + `ControlPlane` + `datapath.Cell`
  - `Infrastructure` — API server, K8s client, metrics, CNI.
  - `ControlPlane` — policy, endpoints, services, IPAM, BGP, Envoy, etc.

---

## 2. Core Packages

### `pkg/policy`
The heart of Cilium's policy engine. Contains:
- `repository.go` — `Repository` struct: the in-memory store of all policy `api.Rules`. Exposes `PolicyAdd`, `PolicyDelete`, `ReplaceByResourceLocked`. Acts as the single source of truth for policy.
- `l4.go` — `L4Filter`, `L7ParserType` (HTTP, Kafka, DNS, TLS, CRD), and `L4Policy` which maps port/protocol to filters.
- `rule.go` / `rules.go` — Translates `api.Rule` into internal representation and resolves selectors.
- `distillery.go` — `PolicyCache` that caches per-identity `SelectorPolicy` and produces `EndpointPolicy` consumed by endpoints.
- `mapstate.go` — `MapState`, the datapath-level view of policy as a set of `(identity, port, proto, direction)` → allow/deny entries.

### `pkg/datapath`
Abstraction layer over the Linux/eBPF datapath. Contains:
- `pkg/datapath/types/` — Go interfaces (`Datapath`, `Loader`, `NodeHandler`, etc.) that decouple the control plane from the actual datapath implementation.
- `pkg/datapath/linux/` — Linux-specific implementation: routing, IPsec, sysctl, neighbor discovery, BIG TCP.
- `pkg/datapath/loader/` — Compiles and loads BPF programs into the kernel via `clang` and the `cilium/ebpf` library. Responsible for calling `WriteEndpointConfig()` to produce per-endpoint header files.
- `pkg/datapath/maps/` — Lifecycle management (open, create, migrate, delete) for BPF maps at agent startup/teardown.

### `pkg/k8s`
All Kubernetes integration logic:
- `pkg/k8s/client/` — `Clientset` interface and real/fake implementations, provided as a hive cell.
- `pkg/k8s/watchers/` — Core K8s object watchers: pods, endpoints, CiliumNodes, services. Drives the K8s event processing loop.
- `pkg/k8s/apis/cilium.io/v2/` — CRD Go types: `CiliumNetworkPolicy`, `CiliumClusterwideNetworkPolicy`, `CiliumNode`, etc.
- `pkg/k8s/resource/` — Generic typed K8s resource stream abstraction used by newer watchers.
- `pkg/k8s/synced/` — Tracks which CRDs have been synced with the API server, providing wait primitives for dependent components.

### `pkg/endpoint`
Represents a locally running workload (pod). Each `Endpoint` object:
- Holds the per-endpoint policy (`desiredPolicy`, `realizedPolicy` of type `EndpointPolicy`).
- Owns the per-endpoint BPF policy map (path: `bpffs/<id>/policy_map`).
- `bpf.go` — `regenerateBPF()`: the core regeneration pipeline that compiles BPF programs, writes endpoint config headers, and calls `syncPolicyMap()` to reconcile the BPF policy map.
- `regenerator.go` / `regeneration/` — Batches and serializes endpoint regeneration requests.

### `pkg/maps/policymap`
Wraps the per-endpoint BPF hash map (`cilium_policy_<id>`) used by datapath programs to make per-packet allow/deny decisions:
- `PolicyMap` struct with `AllowKey()`, `DenyKey()`, `DeleteKey()`, `OpenOrCreate()`.
- `PolicyKey` encodes (identity, destination port, protocol, traffic direction).
- `PolicyEntry` encodes the verdict plus proxy port and auth type.

### `pkg/bpf`
Low-level eBPF helpers:
- `map.go` / `map_linux.go` — Generic `Map` struct wrapping the `cilium/ebpf` library with Cilium-specific semantics (pinning under `/sys/fs/bpf/`, event buffers, migration support).
- `bpffs_linux.go` — BPF filesystem (bpffs) mounting.
- `endpoint.go` — Helpers to build per-endpoint map paths.

---

## 3. Configuration Loading

**Library:** `github.com/spf13/viper` is used throughout for config binding.

**Pipeline:**

1. **CLI flags** are registered in `daemon/cmd/daemon_main.go:InitGlobalFlags()` using `cobra` flag definitions (`flags.String`, `flags.Bool`, etc.).
   Each flag is immediately bound to a viper key and a `CILIUM_<FLAG_NAME>` environment variable via `option.BindEnv(vp, optionName)` (`pkg/option/config.go:1361`).

2. **cobra.OnInitialize** triggers `option.InitConfig()` (`pkg/option/config.go:4215`) before the command runs:
   - Sets the env prefix `"cilium"` on viper (`vp.SetEnvPrefix("cilium")`).
   - If `--config-dir` is set, reads every file in the directory as a `key=value` flat text config via `ReadDirConfig()` and merges it into viper with `MergeConfig()`. This is how Kubernetes ConfigMaps are consumed.
   - If `--config-file` is set, passes it directly to `vp.SetConfigFile()`.
   - Otherwise, looks for `$HOME/cilium.yaml` (no extension needed — viper supports YAML, TOML, JSON, etc.).
   - Calls `vp.ReadInConfig()` to load the file.

3. **Formats supported:** YAML (default), TOML, JSON, HCL, and any format viper supports. The config directory (`--config-dir`) uses plain single-value files (one option per file, matching Kubernetes ConfigMap format).

4. **Config struct:** `option.DaemonConfig` (`pkg/option/config.go:1401`) — a large flat struct holding every agent option.
   - Singleton: `option.Config` (package-level `*DaemonConfig`).
   - Populated from viper in `DaemonConfig.Populate(vp *viper.Viper)` (`pkg/option/config.go:2975`).
   - Validated in `DaemonConfig.Validate(vp *viper.Viper)` (`pkg/option/config.go:2790`).
   - Exposed to hive cells via `cell.Provide(func() *option.DaemonConfig { return option.Config })` in `daemon/cmd/cells.go:101`.

---

## 4. Test Structure

Cilium uses several testing approaches:

### 1. Standard Go Unit Tests
The vast majority of tests are plain `go test` files (`*_test.go`) co-located with the source code under `pkg/`. They use `github.com/stretchr/testify/assert` and `require`. Examples:
- `pkg/policy/repository_test.go`, `pkg/option/config_test.go`, `pkg/k8s/watchers/watcher_test.go`.

### 2. Privileged Tests (require root + network namespaces)
Tests that need real kernel/network resources are gated by `testutils.PrivilegedTest(t)` (`pkg/testutils/privileged.go:17`):
```go
func PrivilegedTest(tb testing.TB) {
    if os.Getenv("PRIVILEGED_TESTS") == "" {
        tb.Skipf("Set %s to run this test", privilegedEnv)
    }
}
```
Examples: `daemon/cmd/daemon_privileged_test.go` (tests `removeOldRouterState` in real network namespaces), `pkg/datapath/linux/` tests. Run with `PRIVILEGED_TESTS=1 go test ./...`.

Similarly, integration tests are gated by `testutils.IntegrationTest(t)` and `INTEGRATION_TESTS=1`.

### 3. Control Plane Integration Tests
Live under `test/controlplane/`. `test/controlplane/controlplane_test.go` wires together a real (but in-process, non-privileged) control-plane hive against a fake K8s API server, then replays fixture YAML resources. Tests cover services, node ports, dual-stack, graceful termination, and CiliumNode handling. Run with `go test ./test/controlplane/...`.

### 4. BPF Verifier Tests
`test/verifier/verifier_test.go` — loads compiled BPF ELF objects into the kernel verifier (read-only). Checks that all BPF programs pass the in-kernel verifier across different kernel versions. Parameterized by `--ci-kernel-version`. Requires a real Linux kernel but not full Cilium agent.

### 5. End-to-End Tests (Ginkgo + real clusters)
Located under `test/k8s/` and `test/runtime/`. Use the Ginkgo BDD framework (`github.com/onsi/ginkgo`) with Gomega matchers. These spin up real Kubernetes or standalone clusters (via Vagrant or cloud providers) and exercise the full Cilium stack. `test/k8s/net_policies.go` is an example covering full `CiliumNetworkPolicy` enforcement. Run via `make test` or the CI pipelines.

---

## 5. Network Policy Pipeline

Tracing a `CiliumNetworkPolicy` from CRD creation to eBPF enforcement:

### Stage 1: CRD Type Definition
**File:** `pkg/k8s/apis/cilium.io/v2/cnp_types.go`
**Type:** `CiliumNetworkPolicy` (implements `runtime.Object`)
The `Spec` field is `*api.Rule` (from `pkg/policy/api/`). The `api.Rule` tree defines `EndpointSelector`, `Ingress`/`Egress` rules, `ToPorts` with optional `L7Rules` (HTTP, Kafka, DNS, or generic `L7Proto`).

### Stage 2: Kubernetes Watcher
**Package:** `pkg/policy/k8s/`
**Files:** `watcher.go`, `cilium_network_policy.go`, `cell.go`
`policyWatcher.watchResources()` subscribes to `resource.Resource[*cilium_v2.CiliumNetworkPolicy]` events. On `Upsert` events, `onUpsert()` is called, which:
- Skips no-op updates (same generation).
- Resolves any `CiliumCIDRGroup` references to concrete CIDR sets.
- Resolves any `ToServices` references to endpoint IPs.
- Calls `policyManager.PolicyAdd(rules, opts)` with the translated `api.Rules`.

Kubernetes `NetworkPolicy` objects go through `pkg/k8s/network_policy.go:ParseNetworkPolicy()` first to convert them to `api.Rules`.

### Stage 3: Policy Repository
**File:** `daemon/cmd/policy.go`
**Function:** `Daemon.PolicyAdd()` → `Daemon.policyAdd()`
The daemon enqueues a `PolicyAddEvent` into the event queue. `policyAdd()`:
- Acquires `d.policy.Mutex`.
- Calls `d.policy.ReplaceByResourceLocked()` or `AddListLocked()` to upsert rules into the `Repository` (`pkg/policy/repository.go`).
- Determines which endpoints are selected by the new/changed rules using `FindSelectedEndpoints()`.
- Enqueues a `PolicyReactionEvent`.

### Stage 4: Endpoint Regeneration
**File:** `daemon/cmd/policy.go:reactToRuleUpdates()` → `pkg/endpoint/bpf.go`
`PolicyReactionEvent.Handle()` calls `reactToRuleUpdates()`, which:
- For endpoints selected by the new rule: calls `ep.RegenerateIfAlive(regenMetadata)`.
- For others: bumps the policy revision counter via `PolicyRevisionBumpEvent`.

`Endpoint.regenerateBPF()` (`pkg/endpoint/bpf.go`) re-resolves the endpoint's policy by calling `distillery.Consume()` on the `PolicyCache`, producing a new `EndpointPolicy` with an updated `MapState`. It then compiles/loads updated BPF programs via `datapath.Loader().WriteEndpointConfig()` and calls `syncPolicyMap()`.

### Stage 5: BPF Policy Map Synchronization
**Files:** `pkg/endpoint/bpf.go`, `pkg/maps/policymap/policymap.go`
`Endpoint.syncPolicyMap()` diffs the `desiredPolicy.MapState` against `realizedPolicy.MapState` and:
- Calls `policymap.AllowKey(PolicyKey, authType, proxyPort)` for new allow entries.
- Calls `policymap.DenyKey(PolicyKey)` for new deny entries.
- Calls `policymap.DeleteKey(PolicyKey)` for stale entries.

The `PolicyMap` is a BPF hash map pinned at `/sys/fs/bpf/tc/globals/cilium_policy_<id>`. The datapath BPF programs do an O(1) map lookup on each packet to enforce policy.

---

## 6. Adding a New Network Policy Type

Example: adding a new L7 filter for an imaginary `gRPC` protocol.

### Step 1: Define the L7 rule type
**File:** `pkg/policy/api/grpc.go` (new file)
Define `PortRuleGRPC` struct with kubebuilder annotations, similar to `pkg/policy/api/http.go`.

### Step 2: Add the field to `L7Rules`
**File:** `pkg/policy/api/l4.go`
Add a `GRPC []PortRuleGRPC` field to the `L7Rules` struct (lines ~249–278).
Update `L7Rules.Len()` to include `len(rules.GRPC)`.

### Step 3: Add validation
**File:** `pkg/policy/api/rule_validation.go`
In `validateL7Rules()`, add a case for the new `GRPC` field, check that it is not mixed with other L7 types (the `L7Rules` struct is a union — only one field may be set).

### Step 4: Register the L7 parser type
**File:** `pkg/policy/l4.go`
Add a `ParserTypeGRPC L7ParserType = "grpc"` constant (around line 379).
In the rule-merging logic (around line 880), add a case for the `GRPC` field to set `l4.L7Parser = ParserTypeGRPC`.

### Step 5: Handle the new rule in policy resolution
**File:** `pkg/policy/rule.go`
In `createL4Filter()` (or the equivalent rule resolution logic), add handling for `rules.GRPC` similar to how `rules.HTTP` and `rules.Kafka` are handled, merging rules into `PerEpData.L7Rules`.

### Step 6: Implement the proxy redirect / Envoy integration
**File:** `pkg/proxy/` and/or `pkg/envoy/`
- If the protocol can be handled by Envoy, register the parser in `pkg/policy/repository.go:GetEnvoyHTTPRules()` or provide an Envoy network filter config.
- If it requires a standalone proxy, implement a new listener in `pkg/proxy/`.

### Step 7: Update deepcopy/deepequal generated code
Run `make generate` to regenerate `pkg/policy/api/zz_generated.deepcopy.go` and `zz_generated.deepequal.go` (these are generated by controller-gen / custom generators).

### Step 8: Update CRD schema
**File:** `pkg/k8s/apis/cilium.io/v2/cnp_types.go` (indirectly, through `api.Rule`)
Re-run `make generate-k8s-api` to regenerate CRD YAML manifests under `install/kubernetes/`.

### Step 9: Write tests
- Unit tests in `pkg/policy/api/` for rule validation.
- Unit tests in `pkg/policy/` for rule resolution and `L4Filter` generation.
- Integration/E2E tests in `test/k8s/` using a real cluster.
