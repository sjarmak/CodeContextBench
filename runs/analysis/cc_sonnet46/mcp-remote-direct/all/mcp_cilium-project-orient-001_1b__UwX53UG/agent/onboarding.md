# Cilium Codebase Orientation

## 1. Main Entry Point

The `cilium-agent` binary starts in `daemon/main.go`:

```go
func main() {
    agentHive := hive.New(cmd.Agent)
    cmd.Execute(cmd.NewAgentCmd(agentHive))
}
```

**Binary entry point:** `daemon/main.go:11` — `func main()`

**CLI initialization** is handled in `daemon/cmd/root.go` via `NewAgentCmd()`. This function:
- Creates a `cobra.Command` named `"cilium-agent"`
- Registers all CLI flags via `h.RegisterFlags(rootCmd.Flags())` and `InitGlobalFlags()`
- Registers cobra init hooks: `option.InitConfig()`, `initDaemonConfig()`, `initLogging()`
- The command's `Run` function calls `initEnv()`, validates config, and then `h.Run()` to start the hive

**Dependency Injection Framework:** Cilium uses **Hive** (`github.com/cilium/hive`), a custom DI framework modeled after `uber-go/fx`-style cells. The `hive.New()` call in `daemon/main.go` takes a root `cell.Cell` — `cmd.Agent` — and wires all components together. Individual cells declare their dependencies by embedding `cell.In` in their parameter structs, and expose outputs via `cell.Provide`.

**Component composition** is defined in `daemon/cmd/cells.go`. The `Agent` cell is a `cell.Module` that contains:
- `Infrastructure` — external access (Kubernetes client, pprof, gops, metrics server, Cilium REST API socket)
- `ControlPlane` — per-node control logic (endpoint manager, node manager, policy watcher, IPAM, services, auth, BGP, etc.)
- `datapath.Cell` — privileged kernel-level operations (BPF maps, iptables, loader, ipcache sync)

---

## 2. Core Packages

### `pkg/policy` — Network Policy Engine
The central policy package. Key types:
- `Repository` (`pkg/policy/repository.go:110`) — stores all active policy rules indexed by `ruleKey` and `ResourceID`. Exposes two event queues: `RepositoryChangeQueue` and `RuleReactionQueue` to serialize policy updates and trigger endpoint regenerations.
- `SelectorCache` (`pkg/policy/selectorcache.go`) — caches label selectors to avoid repeated evaluation.
- `PolicyCache` / `SelectorPolicy` (`pkg/policy/distillery.go`) — caches per-identity resolved policies ready for datapath consumption via `Consume(owner PolicyOwner) *EndpointPolicy`.
- The `api` sub-package (`pkg/policy/api/`) defines the user-facing rule structures: `Rule`, `IngressRule`, `EgressRule`, `PortRule`, `L7Rules`, etc.

### `pkg/datapath` — Datapath Abstraction Layer
Abstracts all kernel-level operations. Key sub-packages:
- `pkg/datapath/types/` — interfaces (`Datapath`, `Loader`, `NodeHandler`, `ConfigWriter`, etc.) that decouple control-plane from kernel implementation.
- `pkg/datapath/linux/` — Linux-specific implementation (TC/XDP program attachment, routing, neighbor tables).
- `pkg/datapath/loader/` — compiles and loads BPF programs per endpoint using clang.
- `pkg/datapath/ipcache/` — synchronizes the userspace IPCache with the kernel BPF `ipcache` map.
- `pkg/datapath/cells.go` — the hive cell that wires all datapath sub-components together.

### `pkg/k8s` — Kubernetes Integration
Everything needed to interact with the Kubernetes API:
- `pkg/k8s/client/` — provides `Clientset` (typed K8s client), injected via hive.
- `pkg/k8s/apis/cilium.io/v2/` — CRD Go types: `CiliumNetworkPolicy` (`cnp_types.go`), `CiliumClusterwideNetworkPolicy` (`ccnp_types.go`), `CiliumEndpoint`, `CiliumNode`, etc.
- `pkg/k8s/watchers/` — core K8s watchers cell (pod, node, service, endpoint watchers).
- `pkg/k8s/resource/` — typed resource stores and event streams over K8s objects.
- `pkg/k8s/synced/` — coordination primitives to wait until specific CRDs/resources are synced.

### `pkg/endpoint` — Endpoint Management
Models a single local workload endpoint (pod/container):
- `Endpoint` struct (`pkg/endpoint/endpoint.go`) — tracks all state: identity, labels, computed policy, BPF maps, proxy config.
- `pkg/endpoint/policy.go` — `regeneratePolicy()` recomputes policy for an endpoint from the repository.
- `pkg/endpoint/bpf.go` — `regenerateBPF()` rewrites BPF headers and syncs BPF maps; `syncPolicyMap()` applies pending policy changes to the kernel per-endpoint `policymap`.
- `pkg/endpoint/regeneration/` — context types and triggers for endpoint regeneration.

### `pkg/maps` — eBPF Map Definitions
Defines all BPF map schemas and Go accessors:
- `pkg/maps/policymap/` — per-endpoint policy map (`PolicyMap`) used by BPF programs to make allow/deny decisions.
- `pkg/maps/ctmap/` — connection tracking maps.
- `pkg/maps/lxcmap/` — endpoint (LXC) map mapping endpoint IDs to their metadata.
- `pkg/maps/nat/` — NAT maps for SNAT/DNAT.
- `pkg/maps/ipcache/` — global ipcache BPF map mapping IPs to security identities.
- `pkg/maps/lbmap/` — load balancer maps for service VIP routing.

---

## 3. Configuration Loading

Configuration is loaded through a multi-stage pipeline using **Viper** (`github.com/spf13/viper`) as the config-binding library, with **Cobra** (`github.com/spf13/cobra`) for CLI flag parsing.

**Pipeline stages (in order):**

1. **Flag registration** — `InitGlobalFlags()` in `daemon/cmd/daemon_main.go` registers all CLI flags with Cobra and binds each to a Viper key via `option.BindEnv()` (`pkg/option/config.go:1361`). This also binds a `CILIUM_<FLAG>` environment variable for every flag automatically.

2. **cobra.OnInitialize hooks** (registered in `daemon/cmd/root.go:66`) run before command execution:
   - `option.InitConfig()` (`pkg/option/config.go:4215`) — reads config from the `--config-dir` directory (a directory of key=value files, compatible with Kubernetes ConfigMap volume mounts), then reads a YAML/TOML/JSON config file specified by `--config`. Uses `vp.ReadInConfig()`.
   - `initDaemonConfig()` — populates the global `option.Config` (`*option.DaemonConfig`) from the populated Viper instance.
   - `initLogging()` — configures log levels and output format.

3. **Config formats supported:** YAML, TOML, JSON (via Viper), plus directory-based key=value files.

4. **Main config struct:** `option.DaemonConfig` (`pkg/option/config.go:1401`) — a large struct with hundreds of fields covering all daemon options. The global singleton is `option.Config`. It is provided to hive cells via `cell.Provide(func() *option.DaemonConfig { return option.Config })` in `daemon/cmd/cells.go:101`.

5. **Per-cell config:** Individual cells also define their own smaller config structs using `cell.Config(MyConfig{})`, which the hive framework automatically populates from Viper using struct field name matching.

---

## 4. Test Structure

The project uses several distinct testing approaches:

### 1. Standard Go Unit Tests
Co-located with the package they test (e.g., `pkg/policy/repository_test.go`, `pkg/option/config_test.go`). Run with `go test ./pkg/...`. These use the standard `testing` package and `github.com/stretchr/testify`, and test pure logic with no kernel dependencies.

### 2. Privileged Tests
Tests that require root/kernel capabilities (loading BPF programs, creating network namespaces, etc.). They call `testutils.PrivilegedTest(t)` at the start, which skips the test unless running as root. Examples:
- `pkg/maps/policymap/policymap_privileged_test.go` — tests actual BPF map operations.
- `pkg/datapath/loader/tc_test.go` — tests TC program attachment.
- `pkg/datapath/linux/probes/probes_test.go` — tests kernel feature probes.
- `pkg/mountinfo/mountinfo_privileged_test.go` — tests filesystem mount detection.

### 3. BPF / Datapath C Tests
Located in `bpf/tests/`. Written in C and executed via a Go test harness (`bpf/tests/bpftest/bpf_test.go`). These compile and run eBPF programs in a controlled environment to test datapath logic in isolation (e.g., conntrack, NAT, policy drop, nodeport load balancing). Example files: `bpf/tests/tc_lxc_policy_drop.c`, `bpf/tests/bpf_ct_tests.c`, `bpf/tests/conntrack_test.c`.

### 4. End-to-End Tests
Located in `test/`. Ginkgo-based tests that run against real Kubernetes clusters or VMs via Vagrant:
- Entry point: `test/test_suite_test.go` — bootstraps the Ginkgo suite using `github.com/onsi/ginkgo`, imports `test/k8s` and `test/runtime`.
- `test/k8s/` — full K8s e2e tests: network policies (`net_policies.go`), services, FQDN, Hubble, BGP, bandwidth, chaos tests.
- `test/runtime/` — runtime tests against a single Cilium node.
- `test/controlplane/` — lighter-weight controlplane integration tests checking policy and endpoint reconciliation without a full cluster.

---

## 5. Network Policy Pipeline

A `CiliumNetworkPolicy` travels through the following stages from CRD definition to eBPF enforcement:

### Stage 1: CRD Type Definition
**Package:** `pkg/k8s/apis/cilium.io/v2/`
**Key file:** `cnp_types.go`

`CiliumNetworkPolicy` is a Kubernetes CRD with `Spec *api.Rule` and `Specs api.Rules`. The `api.Rule` struct (from `pkg/policy/api/rule.go`) contains `EndpointSelector`, `Ingress []IngressRule`, `Egress []EgressRule`, and optional `EnableDefaultDeny`. `IngressRule` and `EgressRule` compose `IngressCommonRule`/`EgressCommonRule` (endpoint/CIDR/entity selectors) with `ToPorts []PortRule` (L4/L7 rules).

### Stage 2: Kubernetes Watcher / Event Ingestion
**Package:** `pkg/policy/k8s/`
**Key files:** `watcher.go`, `cilium_network_policy.go`

The `policyWatcher` struct (registered via `policyK8s.Cell` in `daemon/cmd/cells.go`) watches typed K8s resource event streams for `CiliumNetworkPolicy`, `CiliumClusterwideNetworkPolicy`, `NetworkPolicy`, and `CiliumCIDRGroup` resources. On `Upsert` events, `onUpsert()` translates the K8s object to an internal `types.SlimCNP`, resolves any `CiliumCIDRGroup` references, and calls the `PolicyManager` interface to add rules to the repository.

### Stage 3: Policy Repository
**Package:** `pkg/policy/`
**Key file:** `repository.go`

The `Repository` struct holds all active rules in `map[ruleKey]*rule`. Updates are serialized through `RepositoryChangeQueue`. When rules change, the repository increments its `revision` atomic counter and queues endpoint regeneration events through `RuleReactionQueue`, which triggers all affected endpoints to recompute their policy.

### Stage 4: Endpoint Policy Computation
**Package:** `pkg/endpoint/`, `pkg/policy/`
**Key files:** `pkg/endpoint/policy.go`, `pkg/policy/distillery.go`

`regeneratePolicy()` (`pkg/endpoint/policy.go:200`) is called for each affected endpoint. It uses the `PolicyCache` (`pkg/policy/distillery.go`) to resolve the endpoint's identity against all repository rules via `SelectorPolicy.Consume()`, producing an `EndpointPolicy` — a distilled, identity-indexed set of allow/deny rules specific to this endpoint.

### Stage 5: BPF Regeneration and Policy Map Sync
**Package:** `pkg/endpoint/`, `pkg/maps/policymap/`
**Key files:** `pkg/endpoint/bpf.go`, `pkg/maps/policymap/policymap.go`

`regenerateBPF()` (`pkg/endpoint/bpf.go:520`) rewrites BPF C header files for the endpoint and instructs the datapath loader to recompile and reload the endpoint's BPF programs. Then `syncPolicyMap()` (`pkg/endpoint/bpf.go:1333`) reconciles the desired `EndpointPolicy` against the live kernel `PolicyMap` BPF map (one per endpoint, at path `bpf/LocalMapPath(policymap.MapName, endpointID)`). The BPF datapath uses this map at packet-processing time to allow or drop connections.

---

## 6. Adding a New Network Policy Type

To add a new L7 protocol filter (e.g., a "MyProtocol" L7 rule), the following sequence of changes is required:

### Step 1: Define the API type — `pkg/policy/api/`
- Create `pkg/policy/api/myprotocol.go` with a new struct `PortRuleMyProtocol` (following the pattern of the existing HTTP rule struct in the proxy's kafka package imported via `pkg/policy/api/l4.go`).
- Add a `MyProtocol *PortRuleMyProtocol` field to the `PortRule` struct in `pkg/policy/api/l4.go` (alongside existing `HTTP`, `DNS`, `Kafka` fields).
- Regenerate `zz_generated.deepcopy.go` and `zz_generated.deepequal.go` in that package.

### Step 2: Update CRD validation — `pkg/k8s/apis/cilium.io/v2/`
- Add kubebuilder validation annotations to `cnp_types.go` if the new field needs schema constraints.
- Regenerate the CRD YAML under `pkg/k8s/apis/cilium.io/client/` and the deepcopy files.

### Step 3: Add rule validation — `pkg/policy/api/rule_validation.go`
- Implement validation for `PortRuleMyProtocol` (port restrictions, field mutual exclusivity, etc.) in `rule_validation.go`.

### Step 4: Extend the internal policy model — `pkg/policy/`
- Update `pkg/policy/l4.go` to handle the new protocol type in `L4Filter` resolution — detect the new rule type and set the correct proxy redirect type.
- Update `pkg/policy/rule.go` to process the new `PortRuleMyProtocol` when resolving ingress/egress rules.

### Step 5: Implement proxy handling — `pkg/proxy/` and `pkg/envoy/`
- If routed through Envoy: add xDS filter configuration in `pkg/envoy/` and update the Envoy control plane to generate the appropriate listener/filter chain.
- If a standalone proxy: add a new proxy type in `pkg/proxy/`, register it, and implement the L7 parsing/enforcement logic.

### Step 6: Update endpoint BPF generation — `pkg/endpoint/`
- Ensure `regeneratePolicy()` in `pkg/endpoint/policy.go` correctly captures the new redirect type.
- Ensure `regenerateBPF()` in `pkg/endpoint/bpf.go` generates the correct BPF header flag to redirect matching traffic to the new proxy port.

### Step 7: Add tests
- Unit tests for `PortRuleMyProtocol` validation: `pkg/policy/api/rule_validation_test.go`.
- Policy resolution tests: `pkg/policy/l4_test.go`, `pkg/policy/rule_test.go`.
- Endpoint redirect tests: `pkg/endpoint/redirect_test.go` (see existing pattern).
- E2e tests in `test/k8s/` verifying the new rule type is enforced on a real cluster.
