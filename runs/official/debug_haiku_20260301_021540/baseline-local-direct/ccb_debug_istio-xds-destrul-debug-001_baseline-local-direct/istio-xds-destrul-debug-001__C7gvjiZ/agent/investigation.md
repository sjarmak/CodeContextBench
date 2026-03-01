# Investigation Report: Stale Envoy Route Configuration After DestinationRule Update in Istio

## Summary

When multiple DestinationRules for the same host are merged during PushContext initialization, only one DestinationRule's configuration metadata (Name/Namespace) survives in the consolidated list. The SidecarScope's dependency tracking then registers only this surviving DestinationRule's ConfigKey. When the other contributing DestinationRules are updated, the xDS push filtering incorrectly skips the push because `DependsOnConfig()` does not find their ConfigKeys in the registered dependencies, resulting in stale Envoy configuration on the sidecar.

## Root Cause

The root cause is a **metadata loss during DestinationRule merging** combined with **incomplete dependency registration** in SidecarScope:

1. **In `pilot/pkg/model/destination_rule.go:mergeDestinationRule()`** (lines 38-109): When two DestinationRules for the same host (e.g., "reviews-traffic-policy" and "reviews-subsets") are processed:
   - The function iterates through existing rules in `p.destRules[resolvedHost]`
   - If a compatible rule is found (same workload selector or both without selector), it deep copies the existing rule, merges the incoming rule's subsets and traffic policies into it, and stores the updated copy back in the list
   - If no compatible rule exists, the incoming rule is added as a new entry
   - **The result**: The merged list contains only the surviving rule's full `config.Config` object (including its original Name/Namespace metadata), while the other contributing rule's identity is completely lost

2. **In `pilot/pkg/model/sidecar.go:ConvertToSidecarScope()`** (lines 406-418): When building the SidecarScope, the code iterates over the returned merged destination rules:
   ```go
   for _, s := range out.services {
       ...
       if drList := ps.destinationRule(configNamespace, s); drList != nil {
           out.destinationRules[s.Hostname] = drList
           for _, dr := range drList {
               out.AddConfigDependencies(ConfigKey{
                   Kind:      gvk.DestinationRule,
                   Name:      dr.Name,
                   Namespace: dr.Namespace,
               })
           }
       }
   }
   ```
   - It calls `ps.destinationRule()` which returns the merged list (potentially with fewer entries than original DestinationRules)
   - For each DR in the merged list, it registers a ConfigKey using that DR's Name/Namespace
   - **The problem**: Only the surviving DR's ConfigKey is registered; the other DR's ConfigKey is never added to `configDependencies`

3. **In `pilot/pkg/xds/proxy_dependencies.go:checkProxyDependencies()`** (lines 60-74): When a DestinationRule is updated:
   ```go
   func checkProxyDependencies(proxy *model.Proxy, config model.ConfigKey) bool {
       switch proxy.Type {
       case model.SidecarProxy:
           if proxy.SidecarScope.DependsOnConfig(config) {
               return true
           } else if proxy.PrevSidecarScope != nil && proxy.PrevSidecarScope.DependsOnConfig(config) {
               return true
           }
       ...
       return false
   }
   ```
   - The function checks if the proxy's SidecarScope depends on the changed config
   - This delegates to `SidecarScope.DependsOnConfig()`

4. **In `pilot/pkg/model/sidecar.go:DependsOnConfig()`** (lines 523-540):
   ```go
   func (sc *SidecarScope) DependsOnConfig(config ConfigKey) bool {
       ...
       _, exists := sc.configDependencies[config.HashCode()]
       return exists
   }
   ```
   - Looks up the ConfigKey's hash in the `configDependencies` map
   - **Returns false if not found**, which means the push is skipped

## Evidence

### File: `pilot/pkg/model/destination_rule.go` (mergeDestinationRule function)
- **Lines 41-66**: The loop iterates through existing DRs; when a merge is triggered, the existing DR at index `i` is deep copied and updated in place
- **Line 100-103**: If no merge occurred (`addRuleToProcessedDestRules` still true), the new rule is appended; otherwise it's silently discarded (not added)
- **Evidence of metadata loss**: The merged rule retains only the first DR's `config.Config` metadata (Name: "reviews-traffic-policy", Namespace: "default"), while the second DR ("reviews-subsets") is completely absent from the final list

### File: `pilot/pkg/model/push_context.go` (SetDestinationRules and destinationRule functions)
- **Lines 1672-1743**: SetDestinationRules calls mergeDestinationRule for each config, building consolidatedDestRules structures
- **Lines 990-1066**: The destinationRule() function returns `[]*config.Config` from the consolidated index, where each entry is the merged result with only one config's metadata
- **Evidence**: The destRules map stores multiple DRs as a single merged list, obscuring the original contribution from multiple DRs

### File: `pilot/pkg/model/sidecar.go` (ConvertToSidecarScope function)
- **Lines 406-418**: Iterates over the merged destination rule list returned by `ps.destinationRule()`
- **Line 408**: `if drList := ps.destinationRule(configNamespace, s); drList != nil {`
- **Lines 411-415**: For each DR in drList, adds a ConfigKey to dependencies:
  ```go
  out.AddConfigDependencies(ConfigKey{
      Kind:      gvk.DestinationRule,
      Name:      dr.Name,          // This is the merged DR's Name, not all contributing DRs
      Namespace: dr.Namespace,      // This is the merged DR's Namespace
  })
  ```
- **Evidence of incomplete dependency registration**: Only DRs present in the merged list are registered; any DR whose identity was lost during merging is not tracked

### File: `pilot/pkg/xds/proxy_dependencies.go` (ConfigAffectsProxy and checkProxyDependencies)
- **Lines 32-58**: ConfigAffectsProxy loops through ConfigsUpdated; for each config, calls checkProxyDependencies
- **Lines 60-74**: checkProxyDependencies calls DependsOnConfig to determine if a proxy is affected
- **Line 64**: `if proxy.SidecarScope.DependsOnConfig(config) { return true }`
- **Evidence of push filtering logic**: If DependsOnConfig returns false, the loop continues and eventually returns false, meaning the proxy is not affected and the push is skipped

### File: `pilot/pkg/model/sidecar.go` (DependsOnConfig function)
- **Lines 523-540**: Returns the result of `_, exists := sc.configDependencies[config.HashCode()]`
- **Evidence of the filter**: If the updated DR's ConfigKey hash is not in configDependencies, the function returns false

### File: `pilot/pkg/model/config.go` (ConfigKey.HashCode)
- **Lines 54-74**: ConfigKey is constructed from Kind, Name, Namespace, and Group/Version
- **Line 60-73**: HashCode() hashes these fields
- **Evidence**: Each DestinationRule gets a unique ConfigKey based on its Name/Namespace; if one DR's metadata is lost, its ConfigKey cannot be found during the dependency check

### File: `pilot/pkg/bootstrap/server.go` (configHandler)
- **Lines 881-904**: When a config changes, a PushRequest is created with ConfigsUpdated containing the changed config's ConfigKey:
  ```go
  ConfigsUpdated: map[model.ConfigKey]struct{}{{
      Kind:      curr.GroupVersionKind,
      Name:      curr.Name,
      Namespace: curr.Namespace,
  }: {}},
  ```
- **Evidence**: The push request correctly identifies "reviews-subsets" as the changed config, but the proxy filtering logic doesn't recognize it as a dependency

## Affected Components

1. **`pilot/pkg/model/destination_rule.go`**: Merges multiple DestinationRules, losing metadata of non-surviving entries
2. **`pilot/pkg/model/push_context.go`**: Stores merged DestinationRules in `destinationRuleIndex`, obscuring the original contributing rules
3. **`pilot/pkg/model/sidecar.go`**:
   - Registers only surviving DRs' ConfigKeys in `configDependencies`
   - Filters push requests using `DependsOnConfig()` based on incomplete dependency map
4. **`pilot/pkg/xds/proxy_dependencies.go`**: Uses `DependsOnConfig()` to filter xDS pushes, which fails when a DR's ConfigKey is not registered
5. **`pilot/pkg/bootstrap/server.go`**: Creates push requests with the correct changed config, but the downstream filtering is incomplete

## Causal Chain

1. **Initial state**: Two DestinationRules exist for the same host in the same namespace:
   - "reviews-traffic-policy" (defines traffic policy)
   - "reviews-subsets" (defines subsets)

2. **PushContext initialization** → `SetDestinationRules()` is called with both DRs

3. **Merging phase** → `mergeDestinationRule()` processes both DRs:
   - First DR ("reviews-traffic-policy") is added to the list
   - Second DR ("reviews-subsets") is compatible and should be merged
   - The function merges subsets into the first DR and does NOT add the second DR
   - **Result**: Only one entry in `destRules[host]` with name "reviews-traffic-policy"

4. **Dependency registration** → `ConvertToSidecarScope()` iterates over services:
   - Calls `ps.destinationRule()` which returns the merged list
   - For each DR in the merged list, adds a ConfigKey to `configDependencies`
   - **Result**: Only ConfigKey for "reviews-traffic-policy" is registered

5. **Configuration change** → An operator updates "reviews-subsets":
   - Kubernetes API server updates the resource
   - configHandler in bootstrap/server.go detects the change
   - Creates PushRequest with ConfigKey{Name: "reviews-subsets", Namespace: "default", Kind: DestinationRule}

6. **Push filtering** → `ConfigAffectsProxy()` is called:
   - Iterates through ConfigsUpdated (contains "reviews-subsets")
   - Calls `checkProxyDependencies()` for this ConfigKey
   - Calls `proxy.SidecarScope.DependsOnConfig(ConfigKey{Name: "reviews-subsets", ...})`

7. **Dependency lookup failure** → `DependsOnConfig()` fails:
   - Looks up hash of "reviews-subsets" ConfigKey in `configDependencies` map
   - Hash not found (only "reviews-traffic-policy" is in the map)
   - **Returns false**

8. **Push skipped** → `ConfigAffectsProxy()` returns false
   - The proxy is not added to the list of affected proxies
   - No xDS push is sent to the sidecar
   - **Envoy continues with stale configuration**

9. **Workaround** → Restarting the pod triggers a full PushContext recompute and re-registration, briefly fixing the issue until another DR update

## Recommendation

**Root fix strategy**: Track all contributing DestinationRules in the dependency map, not just the surviving one.

### Diagnostic Steps
1. Add logging to `ConvertToSidecarScope()` to print all ConfigKeys being registered vs. all DRs in the merged list
2. Add logging to `mergeDestinationRule()` to track which DRs are being merged and which one "survives"
3. Verify that when querying `ps.destinationRule()`, the returned list has fewer entries than the original DestinationRules for the same host
4. Check the sidecar's `/debug` endpoint to confirm only one DR is listed in configDependencies

### Implementation approach (options):
1. **Modify mergeDestinationRule()** to track all contributing DRs and return this mapping, allowing SidecarScope to register all of them
2. **Store a list of original config names** in the merged config's metadata/annotations so dependency tracking can reference the originals
3. **Register multiple ConfigKeys** when merging: after merging, AddConfigDependencies should be called for each contributing DR, not just the surviving one
4. **Pre-merge filtering**: Ensure that all DRs for a given host are registered as dependencies before merging, so the merge operation doesn't hide any identities

### Verification
- Create test case with two DestinationRules for the same host in the same namespace
- Update one of them and verify xDS push is triggered
- Verify that both DRs are in the dependency map after SidecarScope initialization
- Confirm Envoy config is updated correctly after each DR update
