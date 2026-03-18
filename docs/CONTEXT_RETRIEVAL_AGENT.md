# Context Retrieval Agent — Calibration & Oracle Generation

## Overview

The **context retrieval agent** is an LLM-powered tool that identifies files relevant to understanding and solving software engineering tasks. It is calibrated against human-annotated contexts from ContextBench and generates oracle ground truth files used in CodeScaleBench's IR (Information Retrieval) evaluation pipeline.

### Purpose

1. **Calibration**: Align agent behavior with human annotations of "relevant files" from ContextBench
2. **Oracle Generation**: Produce machine-generated ground truth (`*_agent.json` files) when human annotations are unavailable
3. **IR Evaluation**: Enable post-hoc retrieval metrics (precision, recall, F1) across SDLC benchmarks using curated oracle files

---

## The ContextBench Calibration Dataset

### What is ContextBench?

[ContextBench](https://github.com/EuniAI/ContextBench) is an external benchmark developed by Nanjing University and UCL consisting of:

- **1,136 issue-resolution tasks** from 66 repositories
- **8 programming languages** (Python, Java, JavaScript, TypeScript, Go, Rust, C, C++)
- **Human-annotated gold contexts** at multiple granularities:
  - File-level (which files are relevant)
  - Symbol-level (which functions/classes)
  - Span-level (which line ranges within files)
  - Edit-location (where changes occur)

### Gold Context Format

ContextBench's `gold_context` field is a JSON list of **span-level annotations**:

```json
[
  {
    "file": "path/to/source.py",
    "start_line": 344,
    "end_line": 396,
    "content": "..."
  },
  {
    "file": "path/to/test.py",
    "start_line": 100,
    "end_line": 120,
    "content": "..."
  }
]
```

**Key insight**: Gold context includes **both modification files AND understanding files**. For example:
- Test files that reveal the bug (read, typically not modified)
- Configuration files that define constraints (read for context)
- Dependencies showing the call chain (read to understand flow)
- Related implementations (read for patterns)

This is fundamentally different from patch-only extraction (which only captures modified files).

---

## Agent Behavior: "Relevant Files"

The agent is tasked with identifying **all files a developer would need to read or modify** to understand and solve the task.

### File Categories

| Category | Include When | Examples |
|----------|--------------|----------|
| **Source code** | Needs modification OR essential to understanding | Bug fix location, dependency implementation, utility functions |
| **Test files** | Reveals bug behavior OR needs updates | Test cases showing failure, assertions to update |
| **Documentation** | Helps understand the issue | API docs, design docs, CHANGELOG |
| **Configuration** | Affects task understanding | package.json (dependencies), CMakeLists.txt (build constraints) |
| **Type definitions** | Type understanding needed | .d.ts files, .h headers with type signatures |

### Size Calibration

Files per task follow a distribution:
- **Small contexts**: 1-3 files (narrow, focused issues)
- **Medium contexts**: 3-8 files (multi-component understanding)
- **Large contexts**: 8-15+ files (complex dependencies or broad issues)

This aligns with ContextBench's empirical distribution where the median task requires 3-5 files of understanding.

---

## System Prompt: Unified Curator

The agent uses a **single unified system prompt** (`CURATOR_SYSTEM_PROMPT`) for all backends and modes. The prompt is parameterized by `{tool_description}` which varies by backend (local/deepsearch/hybrid) and mode (SDK/CLI).

Key elements of the curator prompt:

1. **Role**: "benchmark curator agent for CodeScaleBench" — not solving the task, producing ground truth
2. **Calibration**: aligned with ContextBench human-annotated gold context (read + modify files)
3. **Inclusion rule**: "file if a developer MUST read it to correctly solve the task"
4. **Classification**: agent must label each file as "edit" (needs modification) or "context" (understanding only)
5. **Chunks**: agent must produce line ranges for every included file
6. **Size calibration**: 1-3 small, 3-8 medium, 8-15+ large (from ContextBench empirical distribution)

This replaces the previous 6 separate prompts (SDK x3 + CLI x3) that had contradictory guidance (SDK said "Be PRECISE/patch-only", CLI said "Be THOROUGH/inclusive").

---

## Validation & Calibration Workflow

### Script: `validate_on_contextbench.py`

This script calibrates the agent against ContextBench by:

1. **Loading tasks** from ContextBench parquet (`data/contextbench/verified.parquet`)
2. **Extracting ground truth** from `gold_context` field (unique file paths from spans)
3. **Running the agent** on each task via `context_retrieval_agent.py`
4. **Computing metrics**: file-level recall, precision, F1
5. **Reporting results** by language, complexity, and file category

### Extraction Logic

```python
# Extract unique files from ContextBench's human-annotated gold_context
gc_str = task.get("gold_context", "[]")
gold_files = set()
for item in json.loads(gc_str):
    if "file" in item:
        gold_files.add(item["file"])
```

This replaces the previous (broken) logic that looked for a `files` field that didn't exist.

### Running Calibration

**Three phases with increasing sample sizes:**

```bash
# Phase 0: Test (1 task) — verify setup
python3 scripts/authoring/validate_on_contextbench.py --limit 1 --verbose

# Phase 1: Pilot (10 tasks) — quick feedback
python3 scripts/authoring/validate_on_contextbench.py --limit 10

# Phase 2: Verify (50 tasks) — stable metrics
python3 scripts/authoring/validate_on_contextbench.py --limit 50

# Phase 3: Full (500 tasks) — comprehensive eval
python3 scripts/authoring/validate_on_contextbench.py --verified
```

Each phase:
- Stratifies by **language** and **complexity** (small/medium/large)
- Reports **file-level F1** and per-category metrics
- Saves results to `results/contextbench/phase{N}_calibration_report.json`

### Expected Metrics

From Phase 2 baseline (50 tasks, Opus 4.6, hybrid backend):
- **File F1**: ~0.70 (recall 0.79, precision 0.62)
- **Composite score**: 0.72 (multi-metric blend)
- **Cost**: ~$0.44/task
- **Coverage by language**: Python 0.749, C++ 0.693, TypeScript 0.634

---

## Agent Execution Modes

### 1. SDK Mode (Python Anthropic client)

Uses `run_agent()` — direct Python API calls:

```bash
python3 scripts/running/context_retrieval_agent.py \
    --task-dir benchmarks/csb_sdlc_fix/task-001 \
    --backend hybrid \
    --model claude-opus-4-6
```

**Backends**:
- `local` — grep, find, file reading only
- `deepsearch` — Sourcegraph Deep Search only
- `hybrid` — both (default)

**Output**:
- `*_agent.json` — agent-generated oracle
- `*_agent.metadata.json` — timing, tokens, cost

### 2. CLI Mode (Claude CLI subscription)

Uses `run_agent_cli()` — subprocess invocation of `claude` binary:

```bash
CLAUDE_CODE_OAUTH_TOKEN=... python3 scripts/running/context_retrieval_agent.py \
    --cli-mode \
    --model claude-opus-4-6
```

**Advantages**:
- ✅ Subscription billing (no per-token cost)
- ✅ Integrated tool loop (faster)
- ✅ Cache support (reduces tokens)

**Disadvantages**:
- ❌ Requires `claude` CLI binary
- ❌ OAuth token (subject to auth outages)
- ❌ Platform-dependent

### 3. Verification & Cross-Validation

After generation, verify agent oracles:

```bash
python3 scripts/evaluation/cross_validate_oracles.py \
    --oracle1 ground_truth.json \
    --oracle2 ground_truth_agent.json
```

Metrics:
- **Jaccard similarity** (file-level set overlap)
- **F1 agreement** (precision/recall between oracles)
- **High-divergence list** (tasks with F1 < 0.5)

---

## Integration with CodeScaleBench IR Pipeline

### How IR Evaluation Uses Oracle Files

CodeScaleBench runs a **post-hoc IR analysis** pipeline on SDLC task traces:

1. **Normalize retrieval events** from agent transcripts
2. **Extract retrieved files** (from read/search/grep tool calls)
3. **Compare against ground truth** from oracle files
4. **Compute metrics**:
   - **File-level recall**: Fraction of ground truth files found in trace
   - **File-level precision**: Fraction of retrieved files that are ground truth
   - **File F1**: Harmonic mean (primary metric)
   - **Coverage AUC**: How quickly agent finds relevant files

### Ground Truth Priority Chain

For each task, IR evaluation loads ground truth from (`scripts/csb_metrics/ground_truth.py`):

1. `tests/ground_truth.json` (highest confidence)
2. `tests/expected_defects.json`
3. `tests/expected_changes.json`
4. `tests/reference_fix.patch` / `tests/expected.diff`
5. `solution/solve.sh` gold patch
6. **`*_agent.json` ← agent-generated oracle** (medium confidence)
7. `instruction.md` / `tests/test.sh` regex extraction (lowest confidence)

**If no human-annotated ground truth exists, the IR pipeline uses agent-generated oracles.**

---

## Output Format

The curator agent produces up to **3 files per task**:

### 1. `ground_truth.json` (ALL tasks — IR pipeline format)

Matches `schemas/retrieval_events_schema.json` ground_truth block. Files as plain strings.

```json
{
  "files": [
    "django/forms/models.py",
    "tests/forms_tests/tests/test_model_forms.py",
    "django/forms/fields.py"
  ],
  "expected_edit_files": ["django/forms/models.py"],
  "expected_edit_files_source": "curator_agent_verifier_analysis",
  "expected_edit_files_confidence": "high",
  "symbols": [
    {"file": "django/forms/models.py", "symbol": "ModelChoiceField", "repo": null}
  ],
  "chunks": [
    {"file": "django/forms/models.py", "line_start": 1312, "line_end": 1340, "annotation": "prepare_value — bug site"},
    {"file": "tests/forms_tests/tests/test_model_forms.py", "line_start": 100, "line_end": 120, "annotation": "test revealing the bug"}
  ],
  "dependency_chain": ["django/forms/fields.py", "django/forms/models.py"]
}
```

**Fields**:
- `files` — required, repo-relative path strings (NOT `{repo, path}` dicts)
- `expected_edit_files` — subset of `files` that need modification (optional)
- `symbols` — key function/class definitions, format: `{file, symbol, repo}` (optional)
- `chunks` — line-range annotations per file, format: `{file, line_start, line_end, annotation}` (optional but recommended)
- `dependency_chain` — ordered file list tracing call/import chain (optional)

### 2. `oracle_answer.json` (Org tasks only — artifact verifier format)

Same format as before, consumed by `oracle_checks.py`:

```json
{
  "files": [{"repo": "sg-evals/django--abc123", "path": "django/forms/models.py"}],
  "symbols": [{"repo": "sg-evals/django--abc123", "path": "django/forms/models.py", "symbol": "ModelChoiceField"}],
  "chain": [{"repo": "sg-evals/django--abc123", "path": "django/forms/fields.py", "symbol": "Field.clean"}],
  "text": "The ModelChoiceField class...",
  "_metadata": {"generator": "context_retrieval_agent", "model": "claude-opus-4-6", "backend": "hybrid", ...}
}
```

### 3. `ground_truth_meta.json` (ALL tasks — sidecar)

```json
{
  "has_ground_truth": true,
  "has_chunk_ground_truth": true,
  "ground_truth_source": "curator_agent",
  "ground_truth_confidence": "high",
  "task_name": "django-modelchoice-fk-fix-001",
  "curator_agent_version": "2.0",
  "model": "claude-opus-4-6",
  "backend": "hybrid",
  "files_count": 3,
  "edit_files_count": 1,
  "chunks_count": 2,
  "symbols_count": 1,
  "cost_usd": 0.44,
  "elapsed_sec": 42.3
}
```

### Overwrite Safety

By default, existing `ground_truth.json` and `oracle_answer.json` are NOT overwritten. The agent writes to `_agent` variants (`ground_truth_agent.json`, `oracle_answer_agent.json`). Use `--overwrite-existing` to write directly to canonical filenames.

---

## Calibration & Maintenance

### When to Re-Calibrate

Run Phase 2 calibration (50 tasks) after:

1. **System prompt updates** — to validate behavioral changes
2. **Model upgrades** — Opus 4.5 → 4.6, etc.
3. **Backend changes** — new tools, search API updates
4. **Metric definitions** — if retrieval eval spec changes

### Current Baseline

**Phase 2 Results** (50 tasks, claude-opus-4-6, hybrid):

```
Composite score: 0.7182 (threshold: 0.65) ✅
File F1:        0.6956 (recall: 0.7915, precision: 0.6204)
Cost:           $21.80 total ($0.44/task)
Runtime:        50 tasks × 8 parallel workers

By language:
  Python (n=27):  F1 = 0.749
  C++ (n=3):      F1 = 0.693
  Rust (n=2):     F1 = 0.667
  Java (n=1):     F1 = 0.667
  JavaScript (n=5): F1 = 0.645
  TypeScript (n=5): F1 = 0.634
  C (n=3):        F1 = 0.551
  Go (n=4):       F1 = 0.546

By complexity:
  Small (1-3 files, n=35):   F1 = 0.727
  Medium (3-8 files, n=7):   F1 = 0.582
  Large (8+ files, n=8):     F1 = 0.523
```

**Status**: ✅ PASS (all composites > 0.50, composite mean > 0.65 threshold)

---

## References

### Documentation
- [ContextBench GitHub](https://github.com/EuniAI/ContextBench)
- [ContextBench Docs](https://euniai.github.io/ContextBench/)
- [CodeScaleBench Retrieval Eval Spec](./RETRIEVAL_EVAL_SPEC.md)

### Scripts
- `scripts/running/context_retrieval_agent.py` — agent implementation (run_agent, run_agent_cli)
- `scripts/authoring/validate_on_contextbench.py` — calibration harness
- `scripts/evaluation/cross_validate_oracles.py` — oracle agreement metrics
- `scripts/running/promote_agent_oracles.py` — promotion to canonical ground truth

### Progress Tracking
- `ralph-oracle/progress.txt` — implementation log (local, gitignored)
- `ralph-oracle/prd.json` — product requirements (calibration user stories)

---

## Troubleshooting

### No Ground Truth Found

**Error**: "Composite score unknown — has_ground_truth: false"

**Cause**: `gold_context` field empty or unparseable

**Fix**:
```python
# Debug: check task structure
gc = json.loads(task['gold_context'])
print(f"Files: {len(set(item['file'] for item in gc))}")
```

### Low Precision (many false positives)

**Likely cause**: Agent identifying too many context files

**Fix**:
1. Check `validate_on_contextbench.py` extracts correctly from `gold_context`
2. Review agent output for over-broad file selection
3. Consider adding negative examples to system prompt

### Low Recall (missing true files)

**Likely cause**: Agent not exploring broadly enough with Deep Search

**Fix**:
1. Verify Deep Search is being called (hybrid/deepsearch backends)
2. Check SG token is valid (`SOURCEGRAPH_ACCESS_TOKEN`)
3. Increase tool call budget if hitting `MAX_TOOL_CALLS`

### OAuth Failures

**Error**: "CLAUDE_CODE_OAUTH_TOKEN expired" or "auth service down"

**Mitigation**:
- Use API key mode: `ANTHROPIC_API_KEY=...` + SDK mode (not CLI)
- CLI mode requires OAuth subscription; wait for service recovery
- Phase 0 testing can proceed with SDK mode

---

## Glossary

| Term | Definition |
|------|-----------|
| **Oracle** | Ground truth file set (human-annotated or agent-generated) |
| **Gold context** | ContextBench's human-annotated relevant files (span-level) |
| **Calibration** | Tuning agent to match human annotation targets |
| **IR pipeline** | Post-hoc retrieval evaluation on task traces |
| **Retrieval event** | One tool call (read, grep, search) by agent |
| **Coverage** | File-level recall (fraction of gold files retrieved) |
| **Precision** | Fraction of retrieved files that are gold |
| **F1** | Harmonic mean of recall and precision |
