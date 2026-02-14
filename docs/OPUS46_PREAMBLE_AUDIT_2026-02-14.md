# Opus 4.6 & Preamble Consistency Audit — 2026-02-14

## Executive Summary

✅ **MANIFEST Fixed**: Now correctly extracts model from `config.json`
⚠️ **Incomplete Coverage**: 28/39 suite/config combos have Opus 4.6, 11 still on Opus 4.5
🚨 **Preamble Inconsistency**: Opus 4.6 runs used 2 different preambles (old vs new)

---

## 1. MANIFEST Generation Fix

### Problem
- `generate_manifest.py` hardcoded `model: "anthropic/claude-opus-4-5-20251101"`
- Opus 4.6 runs weren't being tracked in MANIFEST

### Solution Applied
- Added `_extract_model_from_config()` to read model from `config.json`
- Updated `scan_config_dir()` to extract and store model per task
- Updated manifest generation to use extracted model instead of hardcoded value

### Result
```
✅ Opus 4.6: 28 suite/config combos now visible in MANIFEST
⚠️ Opus 4.5: 11 suite/config combos (baseline + sourcegraph_base gaps)
```

---

## 2. Opus 4.6 Coverage Status

### Complete (All 3 Configs)
- ✅ **CrossRepo**: BL + SG_base + SG_full (Feb 7)
- ✅ **DependEval**: BL + SG_base + SG_full (Feb 8-9)
- ✅ **K8s Docs**: BL + SG_base + SG_full (Feb 10)
- ✅ **LoCoBench**: BL + SG_base + SG_full (Feb 7, 12)
- ✅ **SWE-bench Pro**: BL + SG_base + SG_full (Feb 8, 11-12)
- ✅ **TAC**: BL + SG_base + SG_full (Feb 7)

### Partial (Missing Baseline or SG_base)
- ⚠️ **CodeReview**: Missing BL (3 tasks)
- ⚠️ **DIBench**: Missing BL (8 tasks)
- ⚠️ **LargeRepo**: Missing BL + SG_base (4 tasks each = 8 total)
- ⚠️ **LinuxFLBench**: Missing BL (5 tasks)
- ⚠️ **PyTorch**: Missing BL + SG_base (11 tasks each = 22 total) — **IN PROGRESS**
- ⚠️ **RepoQA**: Missing BL + SG_base (10 tasks each = 20 total)
- ⚠️ **SWE-Perf**: Missing BL + SG_base (3 tasks each = 6 total)

### Migration Needed
**Total: 72 tasks across 11 suite/config combos** need Opus 4.6 runs

---

## 3. Preamble Consistency Audit

### Critical Finding: TWO Different Preambles Used

#### Preamble V1 (Pre-Feb 12): "Mandatory Search Workflow"
**Commit**: 775c3d8 (before Feb 12 13:33 UTC)
**Used by**: Feb 7-11 Opus 4.6 runs

**Characteristics**:
- 330-line preamble with mandatory two-phase workflow
- "You MUST use Sourcegraph MCP tools for ALL code navigation"
- Minimum 3 searches before opening files
- Extensive decision logic and workflow mandates
- Strong identity framing ("You are a codebase understanding agent")

**Affected Runs** (Opus 4.6):
- CrossRepo (Feb 7)
- TAC (Feb 7)
- LargeRepo SG_full (Feb 8)
- DependEval (Feb 8-9)
- DIBench SG_full (Feb 9)
- K8s Docs (Feb 10)
- LoCoBench SG_full (Feb 7)
- RepoQA SG_full (Feb 7)
- PyTorch SG_full (Feb 7)

#### Preamble V2 (Post-Feb 12): "Concise Tool Reference"
**Commit**: 30d772f (Feb 12 13:33 UTC)
**Used by**: Feb 12+ Opus 4.6 runs

**Characteristics**:
- 15-line concise tool reference
- No workflow mandates
- Lists tools with brief descriptions
- Note about remote vs local files
- Includes deepsearch but NO guidance on when to use it

**Affected Runs** (Opus 4.6):
- DIBench SG_base (Feb 12)
- LoCoBench BL + SG_base (Feb 12)
- SWE-bench Pro BL + SG_base (Feb 12)
- SWE-Perf SG_full (Feb 12)
- **PyTorch paired run (Feb 14, IN PROGRESS)** 🏃

### Preamble V2 Current State (Lines 255-277)

```markdown
## Sourcegraph MCP Tools

You have access to Sourcegraph code search tools (keyword_search, nls_search,
list_files, read_file, go_to_definition, find_references, deepsearch, deepsearch_read).

Sourcegraph repository: `github.com/{repo}` (use `repo:^github.com/{repo}$` filter)

Available tools:
- keyword_search — exact keyword/pattern search
- nls_search — semantic/fuzzy search
- read_file — read file contents
- list_files — list directory contents
- go_to_definition — jump to symbol definition
- find_references — find all usages
- commit_search — search commit history
- diff_search — search code changes
- compare_revisions — compare two branches/commits
- deepsearch — AI-powered deep analysis (async: returns polling link)
- deepsearch_read — read Deep Search results after 60+ seconds

Note: Sourcegraph indexes the remote repository. Local files may differ — trust local code.
```

**Missing**: Decision guidance on when to use deepsearch vs synchronous tools

---

## 4. Known Preamble Testing Plan

### From MCP_REPORT_TRIAGE_2026-02-07.md

**P1 Issue (Line 27-28)**:
> "Strengthen MCP preamble (6 runs had `no_context_usage`)"

**P2 Issue (Line 34)**:
> "Add preamble guidance for search strategies"

### Archived Test Runs (Line 8-9)
- `locobench_preamble_test_*` (v1, v2, v3) — single-task preamble iteration tests
- These were archived on Feb 7 as one-off experiments

### No Documented Plan Found
- No PRD user story for systematic preamble testing
- No design doc for "representative task set" testing
- User mentioned planning tests on representative tasks to verify tool usage

---

## 5. Recommended Next Steps

### Phase 1: Fix MANIFEST & Coverage Gaps ✅

1. ✅ **MANIFEST fixed** — model extraction working
2. ⚠️ **Complete Opus 4.6 migration**:
   - Run 72 missing tasks (11 suite/config combos)
   - Priority order:
     - PyTorch (current run will handle BL + SG_full when complete)
     - RepoQA BL + SG_base (10 each = 20 tasks)
     - SWE-Perf BL + SG_base (3 each = 6 tasks)
     - LargeRepo BL + SG_base (4 each = 8 tasks)
     - Others (CodeReview, DIBench, LinuxFLBench BL)

### Phase 2: Preamble Design & Testing

1. **Design improved preamble** with balanced deepsearch guidance:
   ```
   When to use deepsearch:
   - Understanding complex flows across multiple files
   - Broad conceptual questions ("How does authentication work?")
   - When synchronous searches return confusing/incomplete results

   When to use synchronous tools (keyword_search, nls_search, etc.):
   - Finding specific symbols, functions, or identifiers
   - Targeted file/definition lookups
   - Following references or jumping to definitions
   - Quick existence checks

   Retry strategy if deepsearch polling fails:
   - Wait 60-90 seconds minimum before calling deepsearch_read
   - If no results, retry deepsearch_read 2-3 times with 30s delays
   - Fallback to synchronous tools if polling continues to fail
   ```

2. **Select representative task set** for preamble A/B testing:
   - 5-8 tasks per benchmark (mix of easy/medium/hard)
   - Focus on benchmarks where MCP helps (K8s Docs, LoCoBench, CrossRepo)
   - Include 1-2 from benchmarks where MCP hurts (SWE-Perf, PyTorch)
   - Total: ~30-50 tasks for fast iteration

3. **Run preamble experiments**:
   - V2 Current (no guidance)
   - V3 With deepsearch guidance (proposed above)
   - Compare tool usage patterns, task success, and efficiency

### Phase 3: Full Opus 4.6 Re-run with Final Preamble

Once preamble is validated:
- Re-run ALL tasks with Opus 4.6 + final preamble
- This ensures:
  - Consistent model (Opus 4.6)
  - Consistent preamble (final version)
  - Clean slate for paper results

---

## 6. Current Active Work

🏃 **PyTorch paired run** (started Feb 14 12:43 UTC):
- 12 tasks (6 tasks × 2 configs: baseline + sourcegraph_full)
- Using Opus 4.6 ✅
- Using Preamble V2 (concise, no deepsearch guidance) ⚠️
- ETA: 2-3 hours to complete

---

## 7. Files Modified

1. `/home/stephanie_jarmak/CodeContextBench/scripts/generate_manifest.py`:
   - Added `_extract_model_from_config()` function
   - Updated `scan_config_dir()` to include model in task entries
   - Updated manifest generation to use extracted model

2. `/home/stephanie_jarmak/CodeContextBench/docs/OPUS46_PREAMBLE_AUDIT_2026-02-14.md`:
   - This document

---

## 8. Open Questions

1. **Preamble testing scope**: Run on representative subset or full suite?
2. **Deepsearch guidance specificity**: How prescriptive should the guidance be?
3. **Migration strategy**: Incremental (11 suite/config combos) or full sweep (all 39)?
4. **Timing**: Run preamble experiments first, or complete Opus 4.6 migration first?

---

## Appendix: Opus 4.6 Coverage Detail

| Suite | Baseline | SG_base | SG_full | Status |
|-------|----------|---------|---------|--------|
| CodeReview | ❌ 4.5 | ✅ 4.6 | ✅ 4.6 | Missing BL |
| CrossRepo | ✅ 4.6 | ✅ 4.6 | ✅ 4.6 | Complete |
| DependEval | ✅ 4.6 | ✅ 4.6 | ✅ 4.6 | Complete |
| DIBench | ❌ 4.5 | ✅ 4.6 | ✅ 4.6 | Missing BL |
| K8s Docs | ✅ 4.6 | ✅ 4.6 | ✅ 4.6 | Complete |
| LargeRepo | ❌ 4.5 | ❌ 4.5 | ✅ 4.6 | Missing BL+SG_base |
| LinuxFLBench | ❌ 4.5 | ✅ 4.6 | ✅ 4.6 | Missing BL |
| LoCoBench | ✅ 4.6 | ✅ 4.6 | ✅ 4.6 | Complete |
| PyTorch | ❌ 4.5 | ❌ 4.5 | ✅ 4.6 | Missing BL+SG_base (in progress) |
| RepoQA | ❌ 4.5 | ❌ 4.5 | ✅ 4.6 | Missing BL+SG_base |
| SWE-bench Pro | ✅ 4.6 | ✅ 4.6 | ✅ 4.6 | Complete |
| SWE-Perf | ❌ 4.5 | ❌ 4.5 | ✅ 4.6 | Missing BL+SG_base |
| TAC | ✅ 4.6 | ✅ 4.6 | ✅ 4.6 | Complete |
