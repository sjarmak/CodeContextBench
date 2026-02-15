# Preamble V3 Testing Plan — 2026-02-14

## Status: Ready to Test ✅

All components prepared for iterative preamble validation testing.

---

## What Changed

### 1. Improved Preamble (V3) ✅

**Location**: `~/evals/custom_agents/agents/claudecode/agents/claude_baseline_agent.py`
**Commit**: 7079b89

**Key Improvements:**
- ✅ Categorized tools as "Synchronous" vs "Asynchronous"
- ✅ Added "When to Use Each Tool" section with clear decision criteria
- ✅ Added "Deepsearch Polling Guide" with retry strategy
- ✅ Balanced approach: start with sync tools, use deepsearch when stuck

**Deepsearch Guidance:**
```
When to use deepsearch:
- Understanding complex cross-file workflows
- Broad architectural questions
- When synchronous searches return confusing results
- Learning unfamiliar codebase patterns

When to use synchronous tools:
- Finding specific symbols, functions, classes
- Jumping to definitions or finding references
- Targeted file lookups
- Quick existence checks

Polling strategy:
- Wait 60-90s before deepsearch_read
- Retry 2-3 times with 30s delays
- Fall back to synchronous after 3-4 failed attempts (~3 min)
```

### 2. Representative Task Selection ✅

**Three-tier iterative testing approach:**

#### Tier 1: Single Task (Start Here)
**Task**: `pkg-doc-001` (K8s Docs)
- **Difficulty**: Medium
- **MCP Score**: 0.515
- **Why**: K8s Docs showed best MCP efficiency (-43% task time), documentation tasks naturally use both deepsearch (understanding) and synchronous tools (finding symbols)

**Config**: `configs/preamble_test_single.json`

#### Tier 2: 5-Task Expansion (If Tier 1 validates)
1. `pkg-doc-001` (K8s Docs) - medium, 0.515 MCP
2. `cross_file_reasoning_01` (CrossRepo) - hard, 0.92 MCP
3. `c_api_graphql_expert_079_...` (LoCoBench) - expert, 0.94 MCP
4. `instance_nodebb__nodebb-...` (SWE-bench Pro) - hard, 0.76 MCP
5. `sgt-002` (PyTorch) - medium, 0.57 MCP

**Coverage**: Diverse benchmarks, mix of difficulties, good MCP score range

**Config**: `configs/preamble_test_5tasks.json`

#### Tier 3: Full 14-Task Set (If Tier 2 validates)
One task per benchmark (all 14 benchmarks including investigation)

**Config**: `configs/preamble_test_tasks.json`

---

## How to Run Tests

### Single Task Test (Start Here)

```bash
# Run both baseline + sourcegraph_full
./configs/preamble_test_single_task.sh

# Or run just one config
./configs/preamble_test_single_task.sh --baseline-only
./configs/preamble_test_single_task.sh --full-only
```

**Output**: `runs/official/preamble_test_v3_single_TIMESTAMP/`

### What to Check After Run

1. **Tool Usage Patterns**:
   ```bash
   # Check trajectory for MCP tool calls
   cat runs/official/preamble_test_v3_single_*/sourcegraph_full/*/agent/trajectory.json | \
     grep -o '"name": "mcp__[^"]*"' | sort | uniq -c
   ```

2. **Deepsearch Success Rate**:
   - Count `deepsearch` calls
   - Count `deepsearch_read` calls
   - Check if reads returned actual results vs "still processing"
   - Verify retry attempts if polling failed

3. **Task Completion**:
   - Did task pass? (`result.json` → `verifier_result.rewards.reward`)
   - Task time vs baseline
   - Token usage

4. **Agent Behavior**:
   - Did agent use deepsearch for understanding?
   - Did agent use synchronous tools for targeted lookups?
   - Did agent follow the retry strategy if deepsearch polling failed?

---

## Validation Criteria

### For Tier 1 (Single Task)

**Must Pass:**
- ✅ Task completes successfully (no errors)
- ✅ Deepsearch polling succeeds OR agent correctly falls back to synchronous tools
- ✅ Agent uses both deepsearch and synchronous tools appropriately

**Good Signs:**
- Deepsearch used for understanding package structure
- Synchronous tools used for finding specific functions to document
- No tool usage errors or retries

**Red Flags:**
- Agent spams deepsearch without waiting for results
- Agent gives up immediately if deepsearch fails
- Agent never uses deepsearch even when appropriate
- Task fails due to MCP tool errors

### For Tier 2 (5 Tasks)

Same criteria as Tier 1, plus:
- Consistent tool usage patterns across tasks
- Deepsearch success rate >60% (or graceful fallback)
- No regression in task success vs baseline

### For Tier 3 (14 Tasks)

Full validation before migrating all 72 remaining Opus 4.6 tasks.

---

## Next Steps After Validation

### If Tier 1 Validates ✅
1. Expand to Tier 2 (5 tasks)
2. Analyze tool usage patterns across diverse benchmarks
3. Refine guidance if needed

### If Tier 2 Validates ✅
1. Expand to Tier 3 (14 tasks, full benchmark coverage)
2. Ensure preamble works consistently across all benchmark types

### If Tier 3 Validates ✅
1. **Full Opus 4.6 Migration** with final preamble:
   - 72 missing tasks (11 suite/config combos)
   - Priority: PyTorch, RepoQA, SWE-Perf, LargeRepo, others
2. **Re-run inconsistent Opus 4.6 tasks**:
   - Feb 7-11 runs used old preamble (V1)
   - Feb 12 runs used intermediate preamble (V2)
   - Re-run for consistency with final V3

### If Issues Found 🔴
1. Analyze failure patterns
2. Refine preamble guidance
3. Re-test at current tier before expanding

---

## Files Created

1. **Agent Changes**:
   - `~/evals/custom_agents/agents/claudecode/agents/claude_baseline_agent.py`
   - Commit: 7079b89

2. **Test Configs**:
   - `configs/preamble_test_single.json` (1 task)
   - `configs/preamble_test_5tasks.json` (5 tasks)
   - `configs/preamble_test_tasks.json` (14 tasks)

3. **Test Scripts**:
   - `configs/preamble_test_single_task.sh` (run single task test)

4. **Documentation**:
   - `docs/OPUS46_PREAMBLE_AUDIT_2026-02-14.md` (full audit)
   - `docs/PREAMBLE_V3_TEST_PLAN.md` (this file)

---

## Comparison: Preamble Versions

| Version | When | Characteristics | Status |
|---------|------|-----------------|--------|
| V1 | Pre-Feb 12 | 330 lines, mandatory workflow, min 3 searches | Used by Feb 7-11 Opus 4.6 runs |
| V2 | Feb 12 | 15 lines, concise, NO deepsearch guidance | Used by Feb 12 Opus 4.6 runs |
| V3 | Feb 14 | Balanced, clear deepsearch guidance, retry strategy | **Ready to test** ✅ |

---

## Ready to Launch

**Command to start Tier 1 test:**

```bash
cd ~/CodeContextBench
./configs/preamble_test_single_task.sh
```

**Expected runtime**: ~10-20 minutes (2 runs: baseline + sourcegraph_full)

**After completion**, review tool usage and decide whether to expand to Tier 2.
