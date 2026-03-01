# Investigation Report: Stale Envoy Route Configuration After DestinationRule Update

## Summary

When multiple DestinationRules target the same host, Istio merges them into a single consolidated configuration. However, only the metadata (Name/Namespace) of one DR survives this merge. When a proxy's SidecarScope registers config dependencies for the merged DR, it only registers the surviving DR's metadata, causing updates to the "absorbed" DRs to be silently skipped by xDS push filtering. The proxy continues serving stale configuration even though the DestinationRule has been updated in the Kubernetes API server.

## Root Cause

The root cause spans three interconnected systems:

### 1. **DestinationRule Merging Loses Identity** (`pilot/pkg/model/destination_rule.go:38-109`)

The `mergeDestinationRule()` function combines multiple DRs for the same host into a single merged entry:

- **Line 41-42**: When a second DR for the same hostname exists, the code enters the merge path
- **Line 65-66**: A deep copy of the existing DR is made: `copied := mdr.DeepCopy()` followed by `p.destRules[resolvedHost][i] = &copied`
- **Lines 69-87**: Subsets from the new DR are appended to the merged rule
- **Lines 91-93**: Traffic policy is merged (only if the existing rule doesn't have one)

**The critical issue**: The metadata of the second DR (Name/Namespace from `destRuleConfig`) is **never persisted**. Only the first DR's `config.Config` object (with its original Name/Namespace) remains in `p.destRules[resolvedHost][i]`.

When two DRs are present for the same host:
- `reviews-traffic-policy` (v1, defining `TrafficPolicy`)
- `reviews-subsets` (v2, defining `Subsets`)

After merging, only `reviews-traffic-policy`'s metadata remains in the `consolidatedDestRules.destRules` map. The second DR's metadata is lost.

### 2. **Dependency Tracking Only Registers Surviving Metadata** (`pilot/pkg/model/sidecar.go:219-227, 410-415`)

When a SidecarScope is created, it populates config dependencies:

**In `DefaultSidecarScopeForNamespace()` (lines 219-227)**:
```go
for _, drList := range out.destinationRules {
    for _, dr := range drList {
        out.AddConfigDependencies(ConfigKey{
            Kind:      gvk.DestinationRule,
            Name:      dr.Name,              // Only ONE DR's metadata
            Namespace: dr.Namespace,
        })
    }
}
```

**In `ConvertToSidecarScope()` (lines 410-415)**:
```go
for _, dr := range drList {
    out.AddConfigDependencies(ConfigKey{
        Kind:      gvk.DestinationRule,
        Name:      dr.Name,                 // Only ONE DR's metadata
        Namespace: dr.Namespace,
    })
}
```

Since `drList` is populated from `ps.destinationRule(configNamespace, s)`, which queries the merged `destinationRuleIndex`, it only contains ONE `config.Config` object with only ONE set of metadata. The second DR's ConfigKey is never registered.

**Result**: `configDependencies` contains only `{reviews-traffic-policy, default}` but NOT `{reviews-subsets, default}`.

### 3. **xDS Push Filtering Skips Unregistered DRs** (`pilot/pkg/xds/proxy_dependencies.go:32-74`)

When a DestinationRule is updated, the control plane creates a `PushRequest` with the updated DR's ConfigKey. The xDS discovery server uses `ConfigAffectsProxy()` to filter which proxies need an update:

**Line 52-54 (`ConfigAffectsProxy`)**:
```go
if affected && checkProxyDependencies(proxy, config) {
    return true
}
```

**Lines 60-74 (`checkProxyDependencies`)**:
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
    }
    return false
}
```

**Dependency Check (`sidecar.go:521-540`)**:
```go
func (sc *SidecarScope) DependsOnConfig(config ConfigKey) bool {
    if sc == nil {
        return true
    }

    // Check if this kind is cluster-scoped
    if _, f := clusterScopedConfigTypes[config.Kind]; f {
        return config.Namespace == sc.RootNamespace || config.Namespace == sc.Namespace
    }

    // Check if this kind is known
    if _, f := sidecarScopeKnownConfigTypes[config.Kind]; !f {
        return true
    }

    _, exists := sc.configDependencies[config.HashCode()]  // Line 538
    return exists
}
```

When `reviews-subsets` is updated:
- A `PushRequest` with `ConfigKey{Kind: DestinationRule, Name: "reviews-subsets", Namespace: "default"}` is created
- For each proxy, `DependsOnConfig()` is called with this key
- Line 538 checks if this key's hashcode exists in `configDependencies`
- Since only `reviews-traffic-policy`'s metadata was registered, this check fails
- **`DependsOnConfig()` returns `false`**
- `ConfigAffectsProxy()` returns `false`
- The xDS push to this proxy is **skipped** (ads.go:688)

## Evidence

### Code References

1. **DestinationRule Merging Loss of Metadata**
   - File: `pilot/pkg/model/destination_rule.go`
   - Lines: 38-109, specifically lines 65-66 and 102
   - The second DR's metadata is lost when merging into an existing entry

2. **consolidatedDestRules Structure**
   - File: `pilot/pkg/model/push_context.go`
   - Lines: 251-256
   - Structure stores only `destRules map[host.Name][]*config.Config`, losing track of contributing DRs

3. **SidecarScope Dependency Registration**
   - File: `pilot/pkg/model/sidecar.go`
   - Lines: 219-227 (`DefaultSidecarScopeForNamespace`)
   - Lines: 410-415 (`ConvertToSidecarScope`)
   - Only registers metadata for DRs visible in the merged `destinationRules` map

4. **xDS Push Filtering**
   - File: `pilot/pkg/xds/proxy_dependencies.go`
   - Lines: 32-74 (`ConfigAffectsProxy`, `checkProxyDependencies`)
   - File: `pilot/pkg/xds/ads.go`
   - Line: 688 - `if !s.ProxyNeedsPush(con.proxy, pushRequest)` skips the push

5. **DependsOnConfig Check**
   - File: `pilot/pkg/model/sidecar.go`
   - Lines: 521-540
   - Line 538 performs the hashcode lookup that fails for the absorbed DR

## Affected Components

1. **`pilot/pkg/model/destination_rule.go`**
   - `mergeDestinationRule()` function
   - Merges multiple DRs but loses identity of absorbed ones

2. **`pilot/pkg/model/push_context.go`**
   - `consolidatedDestRules` struct (lines 251-256)
   - `destinationRuleIndex` struct (lines 111-119)
   - `SetDestinationRules()` function (lines 1672-1744)
   - `destinationRule()` function (lines 989-1066)
   - Stores merged DRs without tracking all contributing DRs

3. **`pilot/pkg/model/sidecar.go`**
   - `DefaultSidecarScopeForNamespace()` (lines 173-251)
   - `ConvertToSidecarScope()` (lines 254-431)
   - `DependsOnConfig()` (lines 521-540)
   - `AddConfigDependencies()` (lines 542-555)
   - Registers only visible DRs without accounting for absorbed ones

4. **`pilot/pkg/xds/proxy_dependencies.go`**
   - `ConfigAffectsProxy()` (lines 32-58)
   - `checkProxyDependencies()` (lines 60-74)
   - `DefaultProxyNeedsPush()` (lines 77-95)
   - Filters pushes based on incomplete dependency information

5. **`pilot/pkg/xds/ads.go`**
   - Line 688-690: Push skip decision
   - Uses `ProxyNeedsPush()` which internally calls `ConfigAffectsProxy()`

## Causal Chain

1. **Symptom**: Operator updates `reviews-subsets` DestinationRule → Envoy continues serving stale config → `/debug/config_dump` on sidecar shows old configuration

2. **Trigger**: Update event occurs for `reviews-subsets` DR → control plane creates PushRequest with `ConfigKey{Kind: DestinationRule, Name: "reviews-subsets", Namespace: "default"}`

3. **First Hop - Merge Already Happened**: During initial mesh configuration load, both `reviews-traffic-policy` and `reviews-subsets` DRs were processed by `SetDestinationRules()` (push_context.go:1672)
   - Both target the same host: `reviews.default.svc.cluster.local`
   - `mergeDestinationRule()` (destination_rule.go:38) merged them into one entry
   - Only `reviews-traffic-policy`'s metadata survived in `consolidatedDestRules.destRules[hostname]`

4. **Second Hop - Dependency Registration**: When the SidecarScope was created, `AddConfigDependencies()` was called for the merged DR list
   - `DefaultSidecarScopeForNamespace()` or `ConvertToSidecarScope()` iterated over `destinationRules` map
   - Since merging produced only one `config.Config` object (the surviving one), only `reviews-traffic-policy`'s ConfigKey was registered
   - `reviews-subsets`'s ConfigKey was never added to `configDependencies`

5. **Third Hop - Push Filter Check**: When the update event arrives for `reviews-subsets`, `ConfigAffectsProxy()` is called
   - (proxy_dependencies.go:52): `checkProxyDependencies(proxy, {reviews-subsets, default})`
   - (sidecar.go:538): `sc.DependsOnConfig()` checks if `{reviews-subsets, default}.HashCode()` exists in `configDependencies`
   - The check fails because only `{reviews-traffic-policy, default}` was registered

6. **Root Cause - Metadata Loss During Merge**: The fundamental issue is that `mergeDestinationRule()` (destination_rule.go:38-109) combines multiple DRs into a single `config.Config` object
   - Line 66: `p.destRules[resolvedHost][i] = &copied` - only one DR's metadata persists
   - The second DR's Name/Namespace are discarded
   - `consolidatedDestRules.destRules` loses track of which DRs contributed to the merge

7. **Final Result**: xDS push is skipped (ads.go:688) → proxy never receives update → Envoy continues using stale cluster and route configuration

## Recommendation

### Root Cause Fix Strategy

The fix must restore the identity of all contributing DRs so that dependency tracking can account for them:

**Option 1: Track All Contributing DRs (Recommended)**
- Modify `consolidatedDestRules` struct to maintain a list of all contributing DR ConfigKeys for each merged entry
- Example: add field `contributingConfigs []model.ConfigKey` to track all DRs that were merged
- Update `mergeDestinationRule()` to populate this list
- Modify `AddConfigDependencies()` in SidecarScope to register all contributing DRs, not just the merged result
- This preserves the merged behavior while ensuring complete dependency tracking

**Option 2: Track Merged DR Configuration Separately**
- Maintain a separate index mapping from "merged DR" ConfigKey to "contributing DRs" ConfigKeys
- Intercept config change events to check both direct and contributing DR dependencies
- Less elegant but avoids modifying the merging logic

**Option 3: Disable Merging for Dependency Tracking**
- Keep the merged configuration for xDS generation (current behavior)
- But separately track each contributing DR's metadata for dependency purposes
- Update `SetDestinationRules()` to maintain a parallel map of all contributing DRs

### Diagnostic Steps

To confirm this issue in a live cluster:

1. **Check merged vs. original DRs**:
   ```bash
   kubectl get destinationrules -A -o yaml | grep -A5 "^metadata:" | grep "name:"
   # Should show two separate DRs
   ```

2. **Inspect Pilot's internal state** (requires custom debug endpoint or logs):
   ```
   curl http://istiod:15014/debug/config_dump | grep "reviews" | jq '.destinationRuleIndex'
   # Should show only one merged entry instead of two
   ```

3. **Check SidecarScope dependencies** (requires code instrumentation):
   - Log the `configDependencies` map when SidecarScope is created
   - Verify that only one DR's ConfigKey is registered

4. **Monitor push events**:
   - Enable debug logging: `kubectl set env deploy/istiod -n istio-system PILOT_DEBUG_ADDR=:15014`
   - Filter for "ConfigAffectsProxy" debug logs when updating a DR
   - Should show false for the absorbed DR

5. **Verify the fix**:
   - After fix, both contributing DRs' ConfigKeys should appear in `configDependencies`
   - Updates to either DR should trigger a push
   - Proxy should receive updated config immediately

