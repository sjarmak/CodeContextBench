# Design: Blind-Bug Instruction Variants

**Beads Issue**: CodeContextBench-fph
**Status**: Design
**Author**: Claude Code
**Date**: 2026-02-12

## Problem

Many SWE-bench Pro instructions reveal the exact location of the bug (class names, method names, module paths). An agent reading "Fix `CertificateErrorWrapper` constructor" can immediately `grep CertificateErrorWrapper` and find the target file. This bypasses the discovery phase where Sourcegraph's search capabilities would shine.

In real-world bug fixing, developers often start with a vague symptom report ("SSL errors display wrong") and must discover WHERE the bug lives before fixing it. MCP code search tools are most valuable in this discovery phase.

## Goal

Create `instruction_blind.md` variants for selected SWE-bench Pro tasks that describe **symptoms only**, forcing the agent to discover bug locations through code search. Same verifier, same Dockerfile, different instruction. Measure whether MCP improves discovery success.

## Approach

### Location-Revealing Analysis

Analyzed all 36 selected SWE-bench Pro tasks. Rated each instruction's location-revealing level:

| Level | Count | Description | Example |
|-------|-------|-------------|---------|
| **HIGH** | ~8 | Names exact class/method/type | "Fix `WorkSearchScheme.process_user_query`" |
| **MEDIUM-HIGH** | ~6 | Names module + external lib | "tctl top, Auth Server, golang-lru" |
| **MEDIUM** | ~10 | Names functional area | "plugin activation operations" |
| **LOW** | ~12 | Pure symptoms | "logs look broken on Windows" |

### Best Candidates for Blind Variants

Only HIGH-rated tasks benefit from blind variants (the delta between original and blind is largest):

| # | Task | Repo | Disclosed Element | Blind Version |
|---|------|------|-------------------|---------------|
| 1 | qutebrowser-e5340c44 | qutebrowser | `CertificateErrorWrapper` class | "SSL certificate error pages display incorrectly; constructor fails in tests" |
| 2 | element-web-cf3c899d | element-hq | `VoiceBroadcastLiveness` type | "Voice broadcast icon doesn't update when playback state changes" |
| 3 | openlibrary-7f6b7722 | internetarchive | `WorkSearchScheme.process_user_query` method | "Work search returns errors for queries with trailing dashes or quoted phrases" |
| 4 | teleport-3587cca7 | gravitational | `tctl top`, Auth Server, `golang-lru` | "Metrics dashboard shows nothing unless debug mode is enabled; needs memory-safe always-on metrics" |
| 5 | vuls-d18e7a75 | future-architect | `models.ScanResult`, `trivy-to-vuls` CLI | "Add integration to consume Trivy vulnerability scanner JSON output" |

**Phase 1 MVP**: Tasks 1-3 (highest delta, clearest blind rewrites).
**Phase 2**: Tasks 4-5 + scan remaining 36 tasks for additional HIGH candidates.

## Implementation

### 1. Create instruction_blind.md Files

Place alongside existing `instruction.md` in each task directory:

```
benchmarks/ccb_swebenchpro/tasks/instance_qutebrowser__qutebrowser-e5340c44.../
├── instruction.md          ← Original (mentions CertificateErrorWrapper)
├── instruction_blind.md    ← NEW (symptoms only)
├── task.toml
├── tests/test.sh           ← Unchanged (independent of instruction)
└── environment/Dockerfile  ← Unchanged
```

### 2. Agent Config: Environment Variable Override

Add ~5 lines to `claude_baseline_agent.py` around line 786 where instruction is loaded:

```python
# After instruction = task.paths.task_dir / "instruction.md" is read
instruction_variant = os.environ.get("INSTRUCTION_VARIANT", "default")
if instruction_variant == "blind":
    blind_path = Path(task_dir) / "instruction_blind.md"
    if blind_path.exists():
        instruction = blind_path.read_text()
    else:
        logger.warning(f"No instruction_blind.md found for {task_name}, using default")
```

### 3. Config Script: `configs/blind_variant_3config.sh`

Runs 4 configs per task:
1. **baseline** (original instruction, no MCP) — existing data, no rerun needed
2. **baseline_blind** (blind instruction, no MCP) — NEW
3. **SG_full** (original instruction, full MCP) — existing data, no rerun needed
4. **SG_full_blind** (blind instruction, full MCP) — NEW

Only configs 2 and 4 are new runs:

```bash
# Blind baseline: no MCP, vague instructions
INSTRUCTION_VARIANT=blind \
BASELINE_MCP_TYPE=none \
harbor run --path "${TASK_DIR}" --jobs-dir "${JOBS_BASE}/baseline_blind" ...

# Blind + MCP: vague instructions, full Sourcegraph
INSTRUCTION_VARIANT=blind \
BASELINE_MCP_TYPE=sourcegraph_full \
SOURCEGRAPH_REPO_NAME="${TASK_SG_REPO}" \
harbor run --path "${TASK_DIR}" --jobs-dir "${JOBS_BASE}/sourcegraph_full_blind" ...
```

### 4. Blind Instruction Writing Guidelines

Each `instruction_blind.md` must:

1. **Remove all identifiers**: No class names, method names, type names, file paths
2. **Keep the symptom**: What the user observes (error messages, incorrect behavior)
3. **Keep the expected behavior**: What should happen instead
4. **Keep the repo context**: Repository name and base commit (needed for Harbor)
5. **Remove "Key Files to Examine"** sections entirely
6. **Remove technical implementation hints**: Don't say "use LRU cache" — say "cap memory usage"

### Example: Qutebrowser Blind Variant

**Original** (HIGH location-revealing):
> The WebKit CertificateErrorWrapper class has an inconsistent constructor signature that doesn't accept named reply arguments... Additionally, the HTML rendering for SSL certificate errors lacks clear specification for single vs. multiple error scenarios and proper HTML escaping...

**Blind** (symptoms only):
> ## SSL Certificate Error Display Issues
>
> Users report two problems with how the browser handles SSL certificate errors:
>
> 1. **Test failures**: Code that creates certificate error objects with named parameters fails. The constructor doesn't accept the expected arguments.
>
> 2. **Display formatting**: When certificate errors are shown to users, the HTML rendering has issues — special characters aren't properly escaped, and the display doesn't distinguish between single vs. multiple errors clearly.
>
> Investigate the browser's certificate error handling code and fix both the constructor interface and the HTML rendering.

**Delta**: Original tells you to search `CertificateErrorWrapper` (1 grep, done). Blind requires searching for certificate error handling patterns, SSL error display code, constructor definitions — multiple searches needed.

## What This Measures

### Primary Metric: Discovery Success Rate

```
                    Original Instruction    Blind Instruction    Delta
Baseline (no MCP)   X% pass                 Y% pass             Y-X (expected negative)
SG_full (with MCP)  A% pass                 B% pass             B-A (expected less negative)
```

**MCP value for discovery** = `(B-A) - (Y-X)`

If MCP helps with discovery, the pass rate drop from original→blind should be smaller with MCP than without.

### Secondary Metrics

- **Time to first edit**: How long before the agent starts modifying code (discovery phase duration)
- **MCP tool calls before first edit**: More calls = more discovery needed
- **Search query quality**: What terms does the agent use when given only symptoms?
- **False starts**: Does the agent edit wrong files before finding the real target?

## Verification

Tests are **completely independent** of instruction content:
- test.sh files embed expected behavior as hardcoded git patches
- Reward is computed from test output (pass/fail), not instruction adherence
- Verified by reading Harbor's task loading code: instruction is a one-time input to the agent, tests never reference it

This means blind variants will use **identical verifiers** — no test changes needed.

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Blind instructions too vague → agent gives up | Include enough symptom detail for a skilled developer to find the bug. Test with 1 task first. |
| Agent ignores symptoms, searches randomly | Acceptable — measures real discovery ability. Random search is what we're testing. |
| Blind instructions accidentally leak location | Peer review each variant. Checklist: no class/method/file names, no module paths, no "look at X" hints. |
| Small sample size (3-5 tasks) limits statistical power | Phase 1 is proof-of-concept. If signal is clear, expand to all HIGH tasks. |
| Tests depend on instruction content | Verified they don't — tests check code correctness only. |

## Files to Create/Modify

| File | Action | Lines |
|------|--------|-------|
| `benchmarks/ccb_swebenchpro/tasks/*/instruction_blind.md` | Create (3-5 files) | ~50 each |
| `agents/claude_baseline_agent.py` | Add INSTRUCTION_VARIANT env var handling | ~5 |
| `configs/blind_variant_3config.sh` | Create config script | ~120 |
| `configs/selected_benchmark_tasks.json` | No change needed |  |

**Total estimated effort**: ~400 lines across 6-8 files.

## Open Questions

1. **Should we also create MEDIUM-HIGH blind variants?** Tasks like Teleport/Vuls give hints but not exact locations. Removing hints might not change behavior much.
2. **How many trials per task?** Standard is 1, but variance might be high with blind instructions. Consider 2-3 trials for statistical confidence.
3. **Should blind variants get longer time limits?** Discovery takes time. Current tasks have 15-30 min limits. May need +50% for blind variants.
