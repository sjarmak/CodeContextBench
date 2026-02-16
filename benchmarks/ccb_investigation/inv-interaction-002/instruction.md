# Investigation: Intermittent Policy Drops in Large Cilium Clusters

**Repository:** cilium/cilium
**Task Type:** Multi-Component Interaction (investigation only — no code fixes)

## Scenario

A Cilium operator running a large Kubernetes cluster (500+ nodes, 10,000+ endpoints) reports intermittent network policy enforcement failures. Specific symptoms:

1. Newly created pods occasionally have **incomplete network policies** — traffic that should be allowed by CiliumNetworkPolicy is being dropped
2. The issue is **non-deterministic** and only reproduces under load (many pods being created simultaneously)
3. Affected pods eventually self-heal after a subsequent endpoint regeneration, but there is a window (seconds to minutes) where policy is incorrect
4. The issue is more likely to occur in clusters with many unique security identities and complex label selectors
5. Restarting the Cilium agent on the affected node does NOT immediately fix the issue — it may take several policy regeneration cycles

The operator's Cilium agent logs on the affected node show:

```
level=debug msg="Processing identity update" identity=12345 labels="k8s:app=backend,k8s:io.cilium.k8s.namespace.labels.team=platform"
level=debug msg="Initial list of identities received"
level=debug msg="Endpoint regeneration" endpoint-id=456 reason="policy change"
level=warning msg="Endpoint policy calculation may be incomplete" endpoint-id=456 identity=12345
```

Notice that the "Initial list of identities received" message appears BETWEEN the identity update and the endpoint regeneration — suggesting a timing-dependent issue with how identity information propagates through the system.

## Your Task

Investigate the root cause of the incomplete policy calculation. Your investigation must cover:

1. **Identify ALL interacting components** — at least 3 distinct Cilium subsystems are involved in this race condition. Determine what each one does and how they interact
2. **The event flow** — trace how a new identity is allocated, propagated to the policy computation engine, and consumed by endpoint regeneration
3. **The race condition** — identify the specific ordering of operations that leads to incomplete policy. What happens when step X occurs before step Y has completed?
4. **The synchronization gap** — what signal or synchronization primitive is missing that would prevent this race?
5. **The impact** — how does the incomplete policy manifest in the eBPF datapath (which traffic is incorrectly allowed or denied)?
6. **The full interaction chain** — which files and functions form the complete path from identity allocation to policy enforcement

## Output Requirements

Write your investigation report to `/logs/agent/investigation.md` with these sections:

```
# Investigation Report

## Summary
<1-2 sentence finding>

## Root Cause
<Specific file, function, and mechanism>

## Evidence
<Code references with file paths and line numbers>

## Affected Components
<List of packages/modules impacted — must identify all interacting components>

## Causal Chain
<Ordered list showing the race condition: what happens when operations occur in the wrong order>

## Recommendation
<Fix strategy: what synchronization is needed and where>
```

## Constraints

- Do NOT write any code fixes
- Do NOT modify any source files
- Your job is investigation and analysis only
- The bug involves interaction between multiple Cilium subsystems — no single component is at fault in isolation
- The issue only manifests under specific timing conditions in large clusters
- Start from the symptom (incomplete endpoint policy) and trace backward through the code to find the race
