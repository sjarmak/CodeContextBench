# Investigation: Consumer Group Rebalance Timeout with Cooperative Rebalancing

**Repository:** apache/kafka
**Task Type:** Multi-Component Interaction (investigation only — no code fixes)

## Scenario

A Kafka operator running a large-scale consumer application reports intermittent consumer group rebalance failures when using the CooperativeStickyAssignor. Specific symptoms:

1. **Consumer kicked out of group** — during rebalancing, consumers are removed from the consumer group after hitting the rebalance timeout, even though the consumer is still alive and calling poll()
2. The issue is **non-deterministic** and only reproduces under moderate network latency (50-200ms) between consumers and Kafka brokers
3. The problem started after upgrading from eager rebalancing (RangeAssignor) to cooperative rebalancing (CooperativeStickyAssignor)
4. Affected consumers show normal poll() behavior — poll(Duration.ofMillis(1000)) is being called regularly every ~500ms
5. **Auto-commit is enabled** (`enable.auto.commit=true`)
6. The issue is MORE likely to occur when:
   - The consumer has many partitions assigned (50+ partitions)
   - Offset commits take longer than usual (network latency, broker load)
   - Rebalances are triggered frequently (consumers joining/leaving)

The operator's consumer logs show:

```
[Consumer clientId=consumer-1, groupId=my-group] Revoking previously assigned partitions []
[Consumer clientId=consumer-1, groupId=my-group] (Re-)joining group
[Consumer clientId=consumer-1, groupId=my-group] Offset commit in progress for partitions [topic-0, topic-1, ...]
[Consumer clientId=consumer-1, groupId=my-group] poll(Duration) exceeded timeout: expected ~1000ms but took 8200ms
[Consumer clientId=consumer-1, groupId=my-group] Member consumer-1-abcd-1234 sending LeaveGroup request to coordinator
[Consumer clientId=consumer-1, groupId=my-group] Member was kicked out of group, resetting generation
```

Notice that poll() is taking MUCH longer than the requested duration, and offset commits appear to be happening repeatedly during rebalancing.

## Your Task

Investigate the root cause of the consumer rebalance timeout. Your investigation must cover:

1. **Identify ALL interacting components** — at least 3 distinct Kafka consumer subsystems are involved in this race condition. Determine what each one does and how they interact
2. **The rebalance flow** — trace what happens when a consumer needs to rebalance: what triggers it, what preparation steps occur, and where offset commits fit in
3. **The async vs sync gap** — the bug involves a change from synchronous to asynchronous behavior. Identify where this transition happens and what signal is missing
4. **The timing condition** — what specific sequence of poll() calls and offset commit operations leads to the timeout? Why does the consumer keep initiating new offset commits?
5. **The completion tracking** — what state is supposed to track whether the offset commit completed, and why isn't it being updated correctly in cooperative rebalancing?
6. **The full interaction chain** — which files and functions form the complete path from rebalance trigger → offset commit → rebalance completion

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
<Ordered list showing the race condition: what happens when operations occur in the wrong order or without proper synchronization>

## Recommendation
<Fix strategy: what synchronization is needed and where>
```

## Constraints

- Do NOT write any code fixes
- Do NOT modify any source files
- Your job is investigation and analysis only
- The bug involves interaction between multiple Kafka consumer subsystems — no single component is at fault in isolation
- The issue only manifests under specific timing conditions (network latency + cooperative rebalancing)
- Start from the symptom (consumer kicked out during rebalance) and trace backward through the code to find the race
