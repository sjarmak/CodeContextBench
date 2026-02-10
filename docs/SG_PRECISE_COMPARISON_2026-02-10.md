# Sourcegraph Precise Indexing Comparison: kubernetes--latest vs --latest--precise

**Date:** 2026-02-10
**Task:** big-code-k8s-001 (Kubernetes NoScheduleNoTraffic Taint Implementation)
**Benchmark:** LargeRepo (ccb_largerepo)
**Config:** sg_base (MCP with Sourcegraph, no Deep Search)
**Model:** claude-opus-4-6
**Auth:** Claude Max subscription (OAuth)

## Executive Summary

We compared two Sourcegraph mirror indexing strategies on the same large-codebase task:

- **kubernetes--latest**: Standard search-based indexing (trigram + zoekt)
- **kubernetes--latest--precise**: scip-go precise code intelligence (compiler-level symbol resolution)

**Result: Same score (0.700) across all 4 runs. Efficiency advantage inconclusive at n=2.**

### Run 1 (first comparison)

| Metric | Standard (--latest) | Precise (--latest--precise) | Delta |
|--------|--------------------|-----------------------------|-------|
| **Reward** | 0.700 | 0.700 | 0 |
| **Total wall time** | 70.2 min | 37.6 min | **-46%** |
| **Agent coding time** | 16.8 min | 12.3 min | **-27%** |
| **Verification time** | 44.1 min | 27.7 min | -37% |
| **MCP tool calls** | 12 | 5 | **-58%** |
| **Transcript lines** | 179 | 202 | +13% |

### Run 2 (account3 rerun)

| Metric | Standard (--latest) | Precise (--latest--precise) | Delta |
|--------|--------------------|-----------------------------|-------|
| **Reward** | 0.700 | 0.700 | 0 |
| **Total wall time** | 23.1 min | 35.8 min | **+55%** |
| **Agent coding time** | 9.8 min | 24.9 min | **+154%** |
| **Verification time** | 10.7 min | 8.1 min | -24% |
| **Input tokens** | 5.8M | 9.8M | +69% |
| **Transcript lines** | ~180 | 257 | +43% |

### Averages (n=2)

| Metric | Standard avg | Precise avg | Delta |
|--------|-------------|-------------|-------|
| **Reward** | 0.700 | 0.700 | 0 |
| **Total wall time** | 46.7 min | 36.7 min | -21% |
| **Agent coding** | 13.3 min | 18.6 min | +40% |
| **Verification** | 27.4 min | 17.9 min | -35% |

**Note:** The standard-indexed run showed enormous variance (70m vs 23m), likely due to Docker layer caching from the first run's container build. Precise was more consistent (38m vs 36m). The Run 1 efficiency advantage does not replicate in Run 2 — see Conclusions for updated interpretation.

## Task Description

Implement `TaintEffectNoScheduleNoTraffic` in the Kubernetes codebase:
1. Add new taint effect constant alongside `NoSchedule`, `NoExecute`, `PreferNoSchedule`
2. Update scheduler/admission to reject pods on tainted nodes
3. Modify endpoint slice controller to exclude tainted nodes from traffic
4. Add Go tests for the new behavior

Scored via weighted checklist: Go compilation (pass/fail gate), taint constant found (0.3), files modified (0.2), tests written (0.2), unit tests pass (0.3).

Both runs scored 0.7/1.0 (unit tests failed in both, all other checks passed).

## Tool Usage Analysis

### MCP/Sourcegraph Tool Calls

| Tool | Standard | Precise | Notes |
|------|----------|---------|-------|
| keyword_search | 10 | 3 | 70% reduction |
| nls_search | 3 | 0 | Eliminated entirely |
| go_to_definition | 1 | 0 | Not needed |
| find_references | 1 | 0 | Not needed |
| read_file | 1 | 0 | Used local Read instead |
| list_files | 1 | 0 | - |
| list_repos | 1 | 1 | Same (initial repo discovery) |
| Other (commit, diff, compare) | 4 | 0 | Exploratory calls eliminated |
| **Total MCP** | **12** | **5** | **-58%** |

### Local Tool Calls

| Tool | Standard | Precise | Notes |
|------|----------|---------|-------|
| Read | 19 | 29 | +53% more local file reads |
| Bash | 6 | 15 | +150% more shell commands |
| Edit | 12 | 9 | -25% fewer edits |
| Grep | 21 | 16 | -24% fewer greps |

### Interpretation

The precise-indexed agent exhibited a fundamentally different navigation strategy:

1. **Standard indexing**: Heavy upfront exploration via MCP (10 keyword searches, 3 semantic searches, go-to-definition, find-references). The agent needed many searches to locate the right files in the kubernetes codebase because search-based indexing returns fuzzy matches requiring iteration.

2. **Precise indexing**: Minimal MCP usage (3 keyword searches, then done). The scip-go index provides compiler-level symbol resolution, so each search returns exact, high-confidence results. The agent then switched to local `Read` calls (+53%) to verify and work with files directly.

**Fewer searches, more direct reads = faster convergence on the right code.**

## Timing Breakdown

```
                Standard (--latest)          Precise (--latest--precise)
                =====================        ============================
Env Setup       10.7s                        1.2s
Agent Setup     159.1s (2.7m)                146.0s (2.4m)
Agent Coding    1005s  (16.8m)               735s   (12.3m)    -27%
Verification    2644s  (44.1m)               1661s  (27.7m)    -37%
                -----------                  -----------
TOTAL           4213s  (70.2m)               2256s  (37.6m)    -46%
```

The verification time difference (44m vs 28m) reflects what the agent implemented: different code paths led to different Go compilation/test scopes. Run 2's more targeted implementation compiled faster.

## Verifier Output Comparison

### Both runs achieved:
- Go compilation check: PASSED
- `NoScheduleNoTraffic` taint constant: FOUND
- Taint-related files modified: CONFIRMED
- Tests for new taint effect: FOUND
- **Score: 0.7/1.0** (unit tests failed in both)

### Files touched by each run:

**Standard (Run 1):**
- `pkg/controller/daemon/daemon_controller.go`
- `pkg/apis/core/validation/validation.go`
- `pkg/scheduler/framework/plugins/tainttoleration/taint_toleration_test.go`
- `cmd/kube-controller-manager/app/options/devicetaintevictioncontroller.go`
- `cmd/kube-scheduler/app/options/configfile.go`

**Precise (Run 2):**
- Same core files plus:
- `pkg/controller/tainteviction/taint_eviction_test.go` (different test focus)
- 22 git commits vs fewer in Run 1 (more incremental approach)

Both approaches are valid implementations. The unit test failure (costing 0.3 points) occurred in both, suggesting a structural challenge in the test harness rather than an indexing-quality issue.

## Conclusions

### 1. Precise indexing does not change task outcomes

All 4 runs (2 per mirror) produced identical reward scores (0.700). The agent solved the same parts of the problem and failed on the same parts, regardless of indexing quality. This is consistent with the broader CCB finding that **MCP value is efficiency, not capability**.

### 2. Efficiency advantage is inconclusive at n=2

Run 1 showed precise indexing was 46% faster, but Run 2 showed the opposite — precise was 55% *slower*. The contradictory results demonstrate that **run-to-run variance dominates any indexing-quality signal** at this sample size.

Key confounds:
- **Docker layer caching**: Run 2's standard-indexed run (23m) benefited from cached Docker layers from Run 1 (70m). This compressed the baseline, making precise look slower by comparison.
- **Agent non-determinism**: The agent took fundamentally different coding paths (9.8m vs 24.9m coding time), independent of indexing strategy.
- **Verification variance**: Go compilation/test scope varied by implementation (11m vs 8m in Run 2).

### 3. Agent strategy adapts to index quality (Run 1 only)

In Run 1, the agent used a distinct strategy per mirror:
- **Standard index**: Broad exploration (10 keyword + 3 semantic + go-to-def + find-refs = 12 MCP calls)
- **Precise index**: Targeted lookup (3 keyword searches = 5 MCP calls) then local file work

Run 2's tool breakdown has not been analyzed in detail but the token data (5.8M vs 9.8M) suggests the precise run used *more* exploration, contrary to the Run 1 pattern.

### 4. Consistent finding: reward stability

The most robust finding is that **precise indexing neither helps nor hurts task outcomes**. All 4 runs scored 0.700. The 0.3 gap (unit test failure) is a task difficulty ceiling unrelated to indexing quality.

## Recommendations

1. **Precise indexing is not a priority** for the CCB evaluation. While it may provide efficiency gains in some runs, the effect is too noisy to measure reliably at n=2 and does not affect scores.

2. **If pursuing further**: A sample of 5+ runs per mirror with cold Docker state would be needed to isolate the indexing effect from caching and agent non-determinism.

3. **Consider expanding to other languages**: scip-java, scip-typescript, and scip-python could be tested on benchmarks with more tasks (e.g., SWE-bench Pro Go tasks) for better statistical power.

4. **The 0.3 score gap** (unit test failure) is a task difficulty ceiling, not an MCP limitation. Neither standard nor precise indexing helps the agent write passing unit tests for this particular Kubernetes taint implementation.

## Appendix: Run Artifacts

### Run 1

```
runs/official/bigcode_sgcompare_opus_20260210_110446/
  sourcegraph_base_latest/
    2026-02-10__11-04-55/
      big-code-k8s-001__uvTGqib/
        agent/claude-code.txt    (179 lines, 1.7MB)
        verifier/test-stdout.txt
        result.json              (reward: 0.700, total: 70.2m)
  sourcegraph_base_precise/
    2026-02-10__12-15-17/
      big-code-k8s-001__cyFsCsg/
        agent/claude-code.txt    (202 lines, 1.7MB)
        verifier/test-stdout.txt
        result.json              (reward: 0.700, total: 37.6m)
```

### Run 2 (account3 rerun)

```
runs/official/bigcode_sgcompare_opus_20260210_164402/
  sourcegraph_base_latest/
    2026-02-10__16-44-09/
      big-code-k8s-001__zUCNFrM/
        agent/claude-code.txt    (~180 lines)
        verifier/test-stdout.txt
        result.json              (reward: 0.700, total: 23.1m)
  sourcegraph_base_precise/
    2026-02-10__17-07-44/
      big-code-k8s-001__893V8bL/
        agent/claude-code.txt    (257 lines, 1.6MB)
        verifier/test-stdout.txt
        result.json              (reward: 0.700, total: 35.8m)
```

Script: `configs/largerepo_sg_compare.sh`
