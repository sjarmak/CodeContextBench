# DependEval Benchmark Failure Diagnosis

**Date**: 2026-02-06
**Run Analyzed**: `runs/official/archive/dependeval_opus_20260203_160607/baseline/`
**Tasks**: 9 (3 DR, 3 ME, 3 RC) across Java, JavaScript, Python
**Result**: All 9 tasks scored 0.0

## Executive Summary

All 9 archived DependEval tasks scored 0.0 on the Feb 3 baseline run. Three independent failure modes were identified:

| Failure Mode | Tasks Affected | Root Cause |
|---|---|---|
| Wrong task formulation | DR (3 tasks) | Instruction asks for package/module names; ground truth contains Android import packages at wrong granularity; eval uses exact-match (all-or-nothing) |
| Wrong ground truth data | ME (3 tasks) | Ground truth contains file dependency pairs (Task 2 DR data), NOT modified code (Task 1 ME data) |
| Docker build failure | ME (3 tasks) | Missing `code_content.txt` in environment/ dir; Dockerfile COPY fails |
| Low agent effort | RC (3 tasks) | Agent produced minimal output (7-31 tokens); graph similarity scored 0.0 |

Note: ME tasks had **two** failures stacked — even if Docker had succeeded, the ground truth mismatch would have prevented correct scoring.

## Per-Task-Type Root Cause Analysis

### (a) Dependency Recognition (DR) — 3 tasks, all 0.0

**What happened**: The agent ran and produced submissions, but scored 0.0 on all three.

**Root cause: Task formulation mismatch with DependEval Task 2**

The archived DR instruction says:
> "Your task is to identify all dependencies in the given code. Analyze the codebase and determine which external libraries, modules, or packages are being used."

But DependEval Task 2 (DR) is about **file dependency ordering** — determining the correct order to process files based on their import/call relationships. The ground truth for Task 2 is an ordered list of file paths, not package names.

However, the archived implementation created a **hybrid**: the instruction asks for package names, but the ground truth contains package-level imports (e.g., `["android.accounts", "android.content", "android.os", "android.text", "android.util"]`). This is neither the original DependEval Task 2 format (file ordering) nor a standard dependency extraction task.

**Evidence**:
- DR Java agent submitted `["android"]` (parent package)
- Ground truth expected `["android.accounts", "android.content", "android.os", "android.text", "android.util"]` (specific import packages)
- Eval uses exact set match: `pred_set == gt_set` → 1.0 or 0.0, no partial credit
- Agent output tokens: only 4 per task (minimal reasoning)

**Eval script behavior**: `eval_dr.py` line 48: `if pred_set == gt_set: return 1.0` / `return 0.0`

### (b) Multi-file Editing (ME) — 3 tasks, all 0.0 (never ran)

**What happened**: All three ME tasks failed at Docker environment setup. The agent never executed.

**Root cause 1: Missing `code_content.txt` file**

The ME task environment directories contain only a Dockerfile — no `code_content.txt`:
```
ME_java/multifile_editing-java-unknown/environment/
└── Dockerfile          # 408 bytes, minimal
```

DR and RC tasks include `code_content.txt` in their environment dirs, but ME tasks do not. Harbor's Docker build fails with:
```
RuntimeError: Docker compose command failed for environment multifile_editing-java-unknown
Error: failed to calculate checksum of ref: "/code_content.txt": not found
```

**Root cause 2: Ground truth loaded from wrong DependEval task**

Even if Docker had succeeded, scoring would have been incorrect. The ME ground truth files contain **file dependency pairs** (DependEval Task 2 DR format), NOT modified code (DependEval Task 1 ME format):

```json
// ME Java ground_truth.json - WRONG FORMAT
"[['Android-DraggableGridViewPager/.../TestActivity.java'], ['Android-DraggableGridViewPager/.../DraggableGridViewPager.java', ...]]"

// ME Python ground_truth.json - WRONG FORMAT
"[['SRCNN-pytorch/utils.py', 'SRCNN-pytorch/train.py'], ['SRCNN-pytorch/models.py', 'SRCNN-pytorch/train.py'], ...]"
```

DependEval Task 1 (ME) ground truth should be a `modified_complete_code` dict keyed by `#file N`:
```json
{"#file 1": "...modified source code...", "#file 2": "...modified source code..."}
```

The ME eval script (`eval_me.py`) expects a dict of `{filename: code_content}` and computes string similarity via `difflib.SequenceMatcher`. With the wrong ground truth format (a stringified list instead of a code dict), it would fall through to the generic JSON-to-string comparison and produce near-0.0 scores.

**ME instruction clarity**: The instruction asks the agent to modify code but provides no feature description or change specification (the "Problem Statement" section is empty). The `feature_description` and `detailed_feature_description` fields from DependEval Task 1 were never extracted into the instruction.

### (c) Repository Construction (RC) — 3 tasks, all 0.0

**What happened**: The agent ran and produced submissions, but scored 0.0 on all three.

**Root cause: Extremely low agent effort + strict evaluation**

Agent output statistics:
- RC Java: 7 output tokens
- RC JavaScript: 14 output tokens
- RC Python: 31 output tokens

The RC eval uses weighted graph F1: `0.15 * node_F1 + 0.85 * edge_F1`. With 85% weight on edges, even partially correct node identification with wrong edges scores near 0.0.

The RC tasks themselves appear correctly formulated — instruction matches DependEval Task 2 format, ground truth is a proper call-chain dict, and eval_rc.py implements NetworkX graph comparison. The primary issue is that the agent did not invest sufficient effort.

## Agent Output Analysis

| Task | Output Tokens | Duration | Verdict |
|---|---|---|---|
| DR Java | 4 | 23s | Barely tried |
| DR JavaScript | 4 | ~20s | Barely tried |
| DR Python | 4 | ~20s | Barely tried |
| ME Java | 0 (never ran) | <1s | Docker failure |
| ME JavaScript | 0 (never ran) | <1s | Docker failure |
| ME Python | 0 (never ran) | <1s | Docker failure |
| RC Java | 7 | ~25s | Minimal effort |
| RC JavaScript | 14 | ~25s | Minimal effort |
| RC Python | 31 | ~30s | Low effort |

All DR/RC tasks used only 2-5 tool calls before submitting answers with minimal reasoning.

## Summary of Issues

### Critical (blocks benchmark validity)

1. **DR eval mismatch**: Our tasks ask for dependency names but the eval uses binary exact-match with specific import package lists. The formulation is a hybrid that doesn't match DependEval's actual Task 2 (file ordering).

2. **ME ground truth format**: Ground truth files contain file dependency pairs (Task 2 data) instead of `modified_complete_code` dicts (Task 1 data). This makes ME evaluation fundamentally broken.

3. **ME Docker failure**: Missing `code_content.txt` in ME environment dirs prevents Docker build. Agent never runs.

4. **ME instruction incomplete**: The "Problem Statement" and feature description sections are empty — the agent has no specification for what code changes to make.

### High (degrades results)

5. **Agent low effort**: DR and RC tasks saw 4-31 output tokens with 2-5 tool calls. The tasks may need better prompting or the code content may need to be presented differently.

6. **No partial credit for DR**: Exact-match scoring (1.0 or 0.0) is extremely harsh. The original DependEval uses precision/recall for dependency edges, not binary package-name matching.

## Recommendations for Revival

1. **Redefine DR tasks** as file dependency ordering (matching DependEval Task 2): agent determines correct build/import order of source files.

2. **Fix ME ground truth** by extracting `modified_complete_code` from DependEval Task 1 data, keyed by file paths.

3. **Include code_content.txt** for all task types or restructure Dockerfiles to not require it.

4. **Populate ME instruction** with feature description from DependEval's `feature_description` / `detailed_feature_description` fields.

5. **Drop RC tasks** — RC requires building call-chain graphs from code, which is Task 3 in DependEval. This is an advanced task with complex evaluation. Focus on DR (file ordering) and ME (code editing) which are more practical and better-understood.

6. **Use partial-credit scoring** for DR (element-wise position match) instead of binary exact-match.

## Files Examined

### Archive Structure
- `archive/ccb_dependeval/{DR,ME,RC}_{java,javascript,python}/` — 9 task directories
- Each contains: `instruction.md`, `task.toml`, `tests/{test.sh, ground_truth.json, eval_scripts/}`

### Eval Scripts
- `eval_dr.py`: Binary exact-match on dependency sets
- `eval_me.py`: `difflib.SequenceMatcher` string similarity per file
- `eval_rc.py`: NetworkX graph F1 (0.15 node + 0.85 edge)

### Run Results
- `runs/official/archive/dependeval_opus_20260203_160607/baseline/` — 9 batch dirs
- All produced `reward: 0.0`
- ME tasks: `exception_info.exception_type: RuntimeError` (Docker build failure)
- DR/RC tasks: Agent ran but produced wrong/minimal output

### Reference
- `archive/ccb_dependeval/README.md` — Benchmark overview documenting all three task types
- DependEval source: https://github.com/ink7-sudo/DependEval
