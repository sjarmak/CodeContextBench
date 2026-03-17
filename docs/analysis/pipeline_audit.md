# CodeScaleBench Pipeline Audit Report

**Date:** 2026-03-17
**Scope:** Complete analysis of all major pipelines and workflows in CodeScaleBench repository
**Goal:** Identify overlaps, dead code, redundant paths, and improvement opportunities

---

## Executive Summary

The CodeScaleBench codebase implements 7 major pipelines with significant **code duplication and architectural fragmentation**:

1. **Trace Quality Pipeline** (2074 lines) - Well-structured but **underutilized** (results never integrated)
2. **Evaluation Pipeline** - **Scattered across 10+ scripts** (no unified scoring API)
3. **Coverage Auditing** - **Fragmented into 5 redundant scripts** (no single source of truth)
4. **Run Promotion Workflow** - Core but **order-dependent, no rollback mechanism**
5. **Task Mining/Scaffolding** - **Linear, well-defined but with duplicate validation**
6. **Report Generation** - **Multiple scripts producing overlapping output** with different APIs
7. **Repo Health** - Clean and integrated, **good model for consolidation**

### Critical Issues

- **8+ files redefine DIR_PREFIX_TO_SUITE mapping** independently (risk: inconsistency)
- **Ground truth loading implemented 3 different ways** (maintenance burden)
- **Task directory iteration reimplemented in 10+ files** (inconsistent filtering)
- **File comparison metrics (F1, recall) calculated 4 different ways** (source of truth unclear)
- **No unified result.json parser** (each script parses independently)

### Key Recommendations

1. **Extract suite mapping to configs/suite_mapping.json** (single source of truth)
2. **Create RunScanner abstraction** for consistent run discovery and filtering
3. **Consolidate metrics extraction** into unified TaskMetricsExtractor
4. **Integrate trace quality pipeline** results into MANIFEST.json and audit reports
5. **Make run promotion atomic** with transaction-like semantics
6. **Create unified Task/Result model** with schema versioning

---

## 1. TRACE QUALITY PIPELINE

### Overview

**Location:** `scripts/evaluation/trace_quality_pipeline.py` (2074 lines)
**Purpose:** Three-stage classification and quality analysis of all task traces in runs/official/ and runs/staging/

### Architecture

**Three-Stage Processing:**

1. **Validity Classification** (Infrastructure failures)
   - Detects: Task hangs, incomplete submissions, Docker failures, missing outputs
   - Gate: valid/invalid binary classification
   - Used by: promote_run.py (prevents promotion of invalid runs)

2. **Setup Quality Analysis** (Environment correctness)
   - Preamble validation (V5_PREAMBLE_MARKER checks)
   - MCP configuration verification
   - SG mirror path validation
   - Detects misconfigured preambles that would cause agent failures

3. **Quality Metrics Analysis** (Task output quality)
   - Symbol hallucination detection (code references non-existent symbols)
   - File comparison metrics extraction (F1 score, recall from test-stdout.txt)
   - Retrieval quality metrics (search effectiveness)
   - Verifier false negative detection

### Key Functions

```python
classify_validity()
  └─ Detects: task_dir doesn't exist, incomplete submission, Docker failure, etc.
  └─ Returns: valid/invalid + reason code

check_setup_quality()
  └─ Validates: Preamble markers, MCP config, SG mirror paths
  └─ Returns: Quality score + issue list

analyze_quality()
  └─ Extracts: Symbol hallucinations, F1 scores, recall metrics, search counts
  └─ Returns: Per-task quality scorecard
```

### Inputs & Outputs

**Inputs:**
- Run directories (runs/official/, runs/staging/)
- Benchmark suite definitions (benchmarks/csb_*/)
- Ground truth files (oracle_answer.json, ground_truth.json)
- Task manifests and task.toml files

**Outputs:**
- Per-trial validity classification (JSON, markdown)
- Per-task quality metrics (JSON)
- Aggregated statistics by suite

### Modularity Assessment

**Strengths:**
- Three-stage design is conceptually clean
- Well-separated validation vs. quality analysis
- Handles diverse failure modes (infrastructure, setup, output quality)

**Weaknesses:**
- **Monolithic implementation** - 2074 lines in single file
- **Tight coupling to run directory structure** - hardcoded assumptions about paths
- **Ground truth loading duplicates** logic in 2+ other scripts
- **Symbol hallucination detection not integrated** with promoted_verifier.py

### Dead Code & Unused Paths

| Code | Status | Issue |
|------|--------|-------|
| `_count_search_calls()` | Extracted but unused | Metrics never aggregated into main report |
| `_extract_symbols_from_code()` | Implemented | Symbol extraction exists but comparison incomplete |
| `_load_manifest_files()` | Implemented | Manifest loading present but never validated against actual |
| Preamble marker variants | Partially supported | Multiple candidates checked, only V5_PREAMBLE_MARKER used |

### Overlaps with Other Pipelines

| Component | Also in | Conflict |
|-----------|---------|----------|
| Symbol hallucination detection | promoted_verifier.py | Two independent implementations |
| F1 score extraction | oracle_checks.py | Different parsing approaches |
| Ground truth loading | ir_analysis.py, extract_task_metrics.py | 3 separate implementations |
| Error classification | status_fingerprints.py | Duplicated categorization logic |

### Utilization Status

**Critical Finding:** Results from trace_quality_pipeline.py are **effectively unused**:
- Generates detailed quality reports
- Never integrated into MANIFEST.json
- Never included in audit_official_scores.py output
- Never referenced in promotion workflow
- **Recommendation:** Integrate quality scores into task_metrics.json

---

## 2. EVALUATION PIPELINE

### Overview

**Scope:** Scoring, metrics extraction, and verification of benchmark task results

**Key Scripts:**
- `extract_task_metrics.py` - Per-task metrics extraction
- `reextract_all_metrics.py` - Batch re-extraction
- `promoted_verifier.py` - Suite-aware composite verifier
- `oracle_checks.py` (in csb_metrics/) - Core verification logic
- `abc_score_task.py` - ABC-task scoring
- `ir_analysis.py` - Information retrieval analysis
- `compute_retrieval_metrics.py` - IR metric computation
- `oracle_retrieval_analysis.py` - File vs. symbol breakdown
- `retrieval_impact_analysis.py` - MCP value attribution

### Three-Layer Architecture

#### Layer 1: Metrics Extraction

**Script:** `extract_task_metrics.py`

**Process:**
1. Read result.json from Harbor task output
2. Extract via csb_metrics/ extractors:
   - Token counts (input/output/cache)
   - MCP tool usage patterns
   - Search strategy classification
   - Code change metrics (files, lines, symbols)
   - Error fingerprints
3. Compute cost from token counts (2025 Anthropic pricing)
4. Enrich with ground truth and task contract data
5. Write task_metrics.json per task

**Inputs:**
- Task result.json
- Trajectory or transcript files
- Verifier test output
- Selected tasks config

**Outputs:**
- task_metrics.json per task directory

**Status:** Core functionality, no overlaps with other metric extraction

#### Layer 2: Scoring & Verification

**Primary Script:** `promoted_verifier.py`

**Architecture:**
```
answer.json
    ↓
oracle_checks.py (core logic)
    ↓
Check Results:
  - file_set_match (F1 score)
  - symbol_resolution (symbols present)
  - dependency_chain (code dependencies)
  - keyword_presence (semantic markers)
  - provenance (code attribution)
    ↓
Apply Suite Weights (from configs/eval_matrix.json)
    ↓
Composite Score (0.0 - 1.0)
```

**Suite-Specific Weights:**

| Suite | File_Set | Symbol | Dependency | Keyword | Provenance |
|-------|----------|--------|------------|---------|------------|
| csb_understand | 35% | 20% | 25% | 20% | — |
| csb_debug | 50% | 20% | — | 30% | — |
| csb_security | 40% | 20% | — | 30% | 10% |
| csb_refactor | 40% | 25% | 10% | 25% | — |
| (8 more suites) | varies | varies | varies | varies | varies |

**Scoring Results:**
- Per-check scores in verification.json
- Composite score in result.json
- Detailed check results in trajectory JSON

#### Layer 3: IR (Information Retrieval) Analysis

**Primary Script:** `ir_analysis.py`

**Metrics Computed:**
- Precision/Recall@K (K = 1, 5, 10, 20)
- Mean Reciprocal Rank (MRR)
- Normalized Discounted Cumulative Gain (nDCG)
- Mean Average Precision (MAP)
- Time-to-context metrics
- Cost-before-first-relevant

**Related Scripts:**
- `compute_retrieval_metrics.py` - Metric calculation
- `oracle_retrieval_analysis.py` - File vs. symbol breakdown
- `retrieval_impact_analysis.py` - MCP value attribution
- `normalize_retrieval_events.py` - Event normalization

### Critical Overlaps & Issues

#### 1. Ground Truth Loading (Triple Implementation)

| Script | Method | Status |
|--------|--------|--------|
| trace_quality_pipeline.py | Local function _load_ground_truth() | Standalone |
| ir_analysis.py | Import from csb_metrics.ground_truth | Cached |
| extract_task_metrics.py | Import from csb_metrics | Direct |

**Issue:** Three different code paths for same operation. Maintenance burden when GT schema changes.

#### 2. Retrieval Event Parsing (Duplicate Logic)

| Script | Parses | Method |
|--------|--------|--------|
| ir_analysis.py | Trajectory JSON | Custom event iterator |
| oracle_retrieval_analysis.py | Trajectory JSON | Alternative event parser |
| retrieval_impact_analysis.py | Trajectory JSON | Third implementation |

**Issue:** No unified retrieval event model. Inconsistent filtering and aggregation.

#### 3. File Comparison Metrics (Four Implementations)

| Component | Implementation | Status |
|-----------|----------------|--------|
| F1 score extraction | trace_quality_pipeline.py (_parse_verifier_debug) | Debug text parsing |
| F1 score calculation | oracle_checks.py (file_set_match) | Source of truth |
| F1 score comparison | ir_analysis.py | Different aggregation |
| F1 score reporting | compare_configs.py | Per-task divergence |

**Issue:** Four independent code paths for same metric. No agreement on calculation method.

#### 4. Error Fingerprinting (Partially Unified)

**Unified:** status_fingerprints.py provides fingerprint_error()
**Duplicates:** Multiple audit scripts reimplement categorization
**Inconsistency:** Different error categories in different scripts

### Evaluation Pipeline DAG

```
Harbor Result
    ↓
extract_task_metrics.py
    ├─ task_metrics.json (tokens, cost, MCP usage)
    ↓
promoted_verifier.py (parallel)
    ├─ oracle_checks.py
    ├─ abc_score_task.py (for ABC tasks)
    ├─ verification.json
    ↓
ir_analysis.py (parallel)
    ├─ normalize_retrieval_events.py
    ├─ oracle_retrieval_analysis.py
    ├─ retrieval_metrics.json (precision, recall, MRR, nDCG)
    ↓
[OUTPUTS]
├─ task_metrics.json
├─ verification.json
├─ retrieval_metrics.json
└─ Integrated: audit_official_scores.py combines all
```

### Opportunities for Improvement

1. **Create TaskMetrics dataclass** (single schema, versioned)
   ```python
   @dataclass
   class TaskMetrics:
       schema_version: str = "1.2.3"
       tokens: TokenCounts
       cost: float
       verification: VerificationResults
       ir_metrics: IRMetrics
       quality_scores: TraceQualityScores  # from trace_quality_pipeline
   ```

2. **Unified retrieval event model**
   ```python
   class RetrievalEvent:
       query: str
       results: List[RetrievalResult]
       precision_at_k: Dict[int, float]
       relevant_count: int
   ```

3. **Extract file comparison logic** to csb_metrics/file_comparison.py
   - Single F1/recall calculation method
   - Used by: oracle_checks, trace_quality, ir_analysis

---

## 3. COVERAGE AUDITING PIPELINE

### Overview

**Problem:** Multiple scripts audit different aspects of coverage with no unified view

**Scripts:**
1. `audit_gt_coverage.py` - Ground truth file coverage (GT status by suite)
2. `analyze_run_coverage.py` - Task completion vs. curated set (125-task list)
3. `audit_official_scores.py` - Official run score legitimacy
4. `build_canonical_manifest.py` - Task manifest generation
5. `build_repo_manifests.py` - Per-benchmark repo metadata

### Script-by-Script Breakdown

#### 1. audit_gt_coverage.py (Ground Truth Coverage)

**Inputs:** benchmarks/csb_*/ directory structure
**Outputs:** Per-suite GT status report

**Functionality:**
- Scans all benchmarks for ground_truth.json files
- Classifies GT status:
  - valid: proper GT exists
  - invalid-schema: malformed
  - empty: zero-length or null
  - missing: task has no GT
- Counts manual vs. curator-generated GT
- Reports coverage percentages

**Example Output:**
```json
{
  "csb_understand": {
    "total_tasks": 50,
    "with_gt": 48,
    "missing_gt": 2,
    "valid_gt": 48,
    "coverage_pct": 96.0
  }
}
```

#### 2. analyze_run_coverage.py (Run Completion Coverage)

**Inputs:**
- selected_benchmark_tasks.json (125-task curated list)
- runs/official/ directory

**Outputs:** Coverage report (curated tasks vs. completed)

**Functionality:**
- Simple set comparison: selected_tasks vs. actual completed
- Reports gaps by benchmark and config
- No score validation; purely presence-based

**Example Output:**
```
Missing from official runs:
  csb_understand:
    - task_001 (baseline)
    - task_002 (MCP)
  csb_debug:
    - task_050 (baseline)
```

#### 3. audit_official_scores.py (Score Legitimacy)

**Inputs:**
- runs/official/MANIFEST.json
- Per-task task_metrics.json
- Benchmark suite definitions

**Outputs:** Comprehensive audit report (JSON + human summary)

**Audit Checks:**
- Infrastructure health (timeouts, OOM, errors)
- Score range validation (0.0 - 1.0)
- Config fairness comparison (baseline vs. MCP)
- Verifier consistency (no contradictory results)
- Task contract compliance

**Example Issues Detected:**
```
Issues Found:
  - Task X: score=0.8 but error_count=5 (contradiction)
  - Task Y: MCP=0.9, baseline=0.1 (suspicious divergence)
  - Task Z: verifier returned invalid score=-0.1
```

#### 4. build_canonical_manifest.py (Task Manifest)

**Inputs:** benchmarks/ directory structure
**Outputs:** benchmarks/CANONICAL.json

**Functionality:**
- Scans benchmarks/csb/*/ directories
- **Filters for canonical tasks only** (those with dual_score_lib.sh)
- Extracts metadata from task.toml
- Builds registry of 275 canonical dual-verified tasks

**Output Structure:**
```json
{
  "version": "1.0",
  "description": "Canonical benchmark tasks with dual verification",
  "categories": {
    "base": [
      {
        "id": "ccx-config-trace-010",
        "path": "benchmarks/csb/crossrepo/ccx-config-trace-010",
        "task": { "language": "go", "difficulty": "hard", ... }
      }
    ]
  },
  "statistics": {
    "total_tasks": 275,
    "by_language": { "go": 120, "python": 155 },
    "by_difficulty": { "hard": 180, "medium": 95 }
  }
}
```

#### 5. build_repo_manifests.py (Repository Metadata)

**Inputs:** GitHub API, local benchmarks/
**Outputs:** Per-task repo_manifest.json files

**Functionality:**
- Extracts repo ownership/licensing/status
- Builds registry of all benchmarks
- Links to task manifests
- Used by: trace_quality_pipeline (symbol hallucination detection)

### Redundancy Matrix

| Dimension | audit_gt_coverage | audit_official_scores | analyze_run_coverage | build_canonical | build_repo |
|-----------|-------------------|----------------------|----------------------|-----------------|-----------|
| **GT Status** | ✓ PRIMARY | uses | ✗ | ✗ | ✗ |
| **Task Existence** | uses | uses | ✓ PRIMARY | ✓ PRIMARY | ✓ uses |
| **Coverage Reporting** | ✓ GT-only | ✓ comprehensive | ✓ run-only | ✗ | ✗ |
| **Repo Metadata** | ✗ | ✗ | ✗ | ✗ | ✓ PRIMARY |
| **Score Validation** | ✗ | ✓ PRIMARY | ✗ | ✗ | ✗ |

### Critical Issues

#### Issue 1: No Single Coverage Source of Truth

**Current State:**
- GT coverage from audit_gt_coverage.py
- Run coverage from analyze_run_coverage.py
- Score legitimacy from audit_official_scores.py
- No unified "coverage and quality report"

**Result:** User must run 3 scripts to understand full coverage picture

#### Issue 2: Suite Mapping Inconsistencies

Both audit_official_scores.py and analyze_run_coverage.py infer suite names from directory prefixes:
- audit_official_scores.py uses DIR_PREFIX_TO_SUITE (from aggregate_status.py)
- analyze_run_coverage.py reimplements filtering

**Risk:** If suite structure changes, scripts may diverge

#### Issue 3: Task Completeness Determination

No clear rule for "task is complete":
- audit_official_scores.py checks for result.json + valid score
- analyze_run_coverage.py checks for directory presence
- build_canonical_manifest.py filters by dual_score_lib.sh

**Issue:** Different definitions lead to different coverage numbers

### Recommendations

1. **Create unified CoverageAudit class**
   ```python
   class CoverageAudit:
       def audit_gt_coverage(self) → GTCoverageReport
       def audit_run_coverage(self) → RunCoverageReport
       def audit_score_quality(self) → ScoreQualityReport
       def generate_combined_report(self) → UnifiedCoverageReport
   ```

2. **Define "complete task" rule** (single definition)
   - result.json exists ✓
   - score exists and 0.0 ≤ score ≤ 1.0 ✓
   - no infrastructure errors ✓

3. **Extract suite mapping** (see §7: Repo Health for full details)

---

## 4. RUN PROMOTION WORKFLOW

### Overview

**Purpose:** Move validated runs from staging → official → archive
**Key Concept:** Staging runs are in-progress; official runs are published

### Promotion Pipeline

```
runs/staging/run_name
    ↓ [Consolidation]
    ├─ consolidate_staging.py
    │  ├─ Archive errored task dirs → archive/errored/
    │  ├─ Merge targeted rerun fragments
    │  ├─ Classify satellite runs
    │  └─ Skip if active tasks exist
    ↓
    ├─ [Validation]
    │  ├─ validate_task_run.py per task
    │  ├─ Check result.json structure
    │  ├─ Verify reward scores exist
    │  └─ Classify errors (timeout, OOM, etc.)
    ↓
    ├─ [Manifest Generation]
    │  └─ generate_manifest.py
    │     ├─ Scan all official tasks
    │     ├─ Group by suite/config
    │     ├─ Deduplicate (latest-by-timestamp wins)
    │     └─ Write runs/official/MANIFEST.json
    ↓
    ├─ [Metrics Extraction]
    │  └─ extract_task_metrics.py
    │     ├─ Token counts
    │     ├─ MCP usage patterns
    │     ├─ Cost computation
    │     └─ Write task_metrics.json
    ↓
    ├─ [Results Export]
    │  └─ export_official_results.py
    │     ├─ Generate per-suite summaries
    │     └─ Export to docs/official_results/
    ↓
    ├─ [Promotion (promote_run.py)]
    │  ├─ Validate gates: no hanging tasks, all scored
    │  ├─ Optional: --force bypass
    │  └─ Move to runs/official/run_name
    ↓
runs/official/run_name (published)
```

### Key Scripts

#### 1. promote_run.py (Main Orchestrator)

**Inputs:** runs/staging/run_name
**Outputs:** runs/official/run_name

**Workflow:**
1. Iterates all task directories in staging run
2. Calls validate_task_run.py per task
3. Checks gates:
   - No hanging tasks (task still running)
   - All results have reward scores
   - Error fingerprints classified
4. Generates MANIFEST.json (calls generate_manifest.py)
5. Extracts metrics (calls extract_task_metrics.py)
6. Moves validated run to runs/official/

**Force Promotion:** --force flag bypasses validation gates

**Issue:** Multiple sub-scripts called independently (not atomic)

#### 2. consolidate_staging.py (Pre-promotion Consolidation)

**Inputs:** runs/staging/ directory
**Outputs:** Consolidated staging directory

**Operations:**
1. **Archive errored tasks**
   - Move failed task dirs → archive/errored/
   - Keep in parent run dir structure

2. **Merge targeted reruns**
   - Identify: rerun fragments (subset of parent run)
   - Move tasks into parent run directory
   - Rename with time-range suffix

3. **Classify satellite runs**
   - Duplicate full runs (identical task sets) kept separate
   - Split-config runs (baseline + SG_full) merged into one

4. **Consistency check**
   - Skip any run with active/hanging tasks
   - Prevent promotion of incomplete work

**Example:**
```
Before:
  runs/staging/run_baseline_20260310/
  runs/staging/run_baseline_rerun_20260311/  (rerun, subset)
  runs/staging/run_baseline_20260310_errors/

After consolidation:
  runs/staging/run_baseline_20260310/
    ├─ task_1/
    ├─ task_2/
    └─ [merged] task_3/  (from rerun_20260311)
  runs/staging/archive/errored/
    └─ [moved] task_from_errors/
```

#### 3. generate_manifest.py (Canonical Manifest)

**Inputs:** runs/official/ (or raw_runs_dir)
**Outputs:** runs/official/MANIFEST.json

**Functionality:**
- Scans all task directories in runs/official/
- Groups by (suite, task_name, config)
- Deduplicates: **latest-by-timestamp wins**
  - If task_X run twice: keeps result with latest modification time
  - Allows overwriting with rerun results
- Suite inference: uses DIR_PREFIX_TO_SUITE mapping
- Output: Master manifest with all official tasks

**Manifest Schema:**
```json
{
  "version": "1.0",
  "generated_at": "2026-03-17T...",
  "runs": [
    {
      "run_id": "claude_haiku_20260310",
      "tasks": [
        {
          "suite": "csb_understand",
          "task_name": "task_001",
          "config": "baseline",
          "score": 0.85,
          "cost": 0.024
        }
      ]
    }
  ]
}
```

#### 4. promote_agent_oracles.py (Oracle Validation)

**Purpose:** Validate agent-curated oracle answers
**Inputs:** Answer.json from task result
**Outputs:** Validation report

**Checks:**
- answer_extraction format correctness
- Ground truth consistency
- Score plausibility

#### 5. promote_blocked.py (Unblock)

**Purpose:** Remove temporary block markers
**Functionality:** Validates unblock prerequisites before allowing promotion

### Archive Workflow

#### 6. archive_run.py (Old Run Archival)

**Purpose:** Archive runs older than N days
**Inputs:** runs/official/
**Outputs:** runs/official/archive/

**Operations:**
- Move runs older than threshold (e.g., 90 days)
- Optionally compress large files
- Track age, size, result count

#### 7. archive_non_manifest_runs.py (Cleanup)

**Purpose:** Archive orphaned runs
**Inputs:** runs/official/ + MANIFEST.json
**Outputs:** Runs not in manifest → archive/

**Use case:** Cleanup after MANIFEST.json deduplication

### Critical Issues

#### Issue 1: Non-Atomic Promotion

**Current:** promote_run.py calls sub-scripts sequentially:
1. validate_task_run.py (per task)
2. generate_manifest.py
3. extract_task_metrics.py
4. export_official_results.py
5. move_to_official()

**Problem:** If step 4 fails, partial results are written but run isn't moved

**Risk:** Inconsistent state if external process dies mid-promotion

#### Issue 2: Suite Mapping Fragmentation

Suite inference in generate_manifest.py:
```python
DIR_PREFIX_TO_SUITE = {
    'csb_understand': 'understand',
    'csb_debug': 'debug',
    # ... (manual mapping)
}
```

**Issue:** Defined in multiple files (generate_manifest, aggregate_status, promote_run, etc.)

#### Issue 3: No Rollback Mechanism

**Current:** Once moved to runs/official/, no automatic rollback
**Issue:** Can't easily undo bad promotion
**Workaround:** Manual move back to staging (risky, error-prone)

#### Issue 4: Order Dependency

1. consolidate_staging.py must run first (merges reruns)
2. promote_run.py must run on consolidated run
3. generate_manifest.py must scan all promoted runs

**Issue:** If run out of order, inconsistencies possible

### Recommendations

1. **Make promotion atomic**
   ```python
   def promote_run_atomic(staging_run, force=False):
       with transaction():
           validate_all_tasks()
           generate_manifest()
           extract_metrics()
           move_to_official()
       # Rollback on any failure
   ```

2. **Add version control to promoted runs**
   - Mark run as "provisional" until all post-promotion checks complete
   - Only then mark as "official"

3. **Extract suite mapping** (see §7 for consolidation plan)

---

## 5. TASK MINING & SCAFFOLDING PIPELINE

### Overview

**Purpose:** Pipeline from task discovery (GitHub issues) → task creation → validation → selection

### Pipeline Stages

```
Stage 1: Task Discovery & Candidate Mining
    ↓ [mine_bug_tasks.py]
    └─ GitHub Issues → Task Candidates (JSON)

Stage 2: Task Selection
    ↓ [select_benchmark_tasks.py]
    └─ Candidates → selected_benchmark_tasks.json (125 tasks)

Stage 3: Task Scaffolding (Parallel, task-type specific)
    ├─ [scaffold_swebench_pro_tasks.py] → SWE-Bench style tasks
    ├─ [scaffold_feature_tasks.py] → Feature-oriented tasks
    ├─ [scaffold_refactor_tasks.py] → Refactoring tasks
    ├─ [scaffold_scaling_gap_sdlc_tasks.py] → SDLC phase tasks
    └─ [scaffold_contextbench_tasks.py] → ContextBench tasks

Stage 4: Pre-Run Validation
    ↓ [validate_tasks_preflight.py]
    └─ Task dirs → validation report (exit 0/1)

Stage 5: Execution (Harbor)
    ↓ [harbor run]
    └─ Tasks executed

Stage 6: Post-Run Validation
    ↓ [validate_task_run.py]
    └─ Result validation

Stage 7: Promotion
    ↓ [promote_run.py]
    └─ Validated tasks → runs/official/
```

### Stage-by-Stage Detail

#### Stage 1: Task Discovery - mine_bug_tasks.py

**Purpose:** GitHub Issue candidate mining
**Language:** Pure Python (stdlib only)

**Inputs:**
- GitHub repo URL
- Issue label filter (e.g., 'bug')
- File count range (min, max)

**Outputs:** JSON file with candidates
```json
[
  {
    "issue_id": 12345,
    "title": "Bug: fix memory leak in parser",
    "pr_files": 8,
    "pr_lines": +234/-56,
    "difficulty_estimate": "medium"
  }
]
```

**Limitations:**
- GitHub API rate limits (60 req/hour unauthenticated, 5000 with auth)
- No authentication configured (hardcoded)
- File count heuristic is weak (doesn't account for file size)

**Recommendation:** Parameterize GitHub token, add file size heuristic

#### Stage 2: Task Selection - select_benchmark_tasks.py

**Purpose:** Curate balanced task selection

**Algorithm:**
1. Load all candidate pools (from mine_*.py scripts)
2. Apply selection criteria:
   - Coverage (how many suites represented)
   - Difficulty balance (even distribution of hard/medium/easy)
   - Suite targets (e.g., 15 csb_understand, 20 csb_debug, etc.)
3. Optimize for variance (avoid clustering)
4. Output: selected_benchmark_tasks.json (125 tasks)

**Output File:**
```json
{
  "total_selected": 125,
  "by_suite": {
    "csb_understand": 15,
    "csb_debug": 20,
    ...
  },
  "tasks": [
    {
      "id": "task_001",
      "suite": "csb_understand",
      "difficulty": "hard",
      "source": "github_issue_12345"
    }
  ]
}
```

**Critical:** This 125-task set is referenced by multiple scripts:
- analyze_run_coverage.py (coverage auditing)
- run_selected_tasks.sh (launch config)

#### Stage 3: Task Scaffolding

**Parallel implementations for different task types:**

##### 3a. scaffold_swebench_pro_tasks.py

**Type:** SWE-Bench style (fix-a-bug)

**Creates:**
- task.toml (language, difficulty, time_limit_sec)
- instruction.md (problem description)
- instruction_mcp.md (MCP retrieval hints)
- environment/Dockerfile (from SWEAP base image)
- tests/test.sh (regression test)
- tests/config.json (task contract)

**V5 Preamble:** Injected into Dockerfile/instruction.md

**Recent Update:** Mar 17 01:40 (latest in Phase 2 reorganization)

##### 3b. scaffold_feature_tasks.py

**Type:** Feature-oriented (add new functionality)

**Differs from swebench_pro:**
- Emphasizes requirements vs. bugfix regression
- Different preamble emphasis (feature vs. fix validation)

##### 3c. scaffold_refactor_tasks.py

**Type:** Code refactoring

**Specialization:**
- Refactoring-specific oracle checks
- Code structure metrics

##### 3d. scaffold_scaling_gap_sdlc_tasks.py

**Type:** SDLC phase tasks (understand/design/debug/fix/test/refactor)

**Generative:** Creates task variants for each SDLC phase

##### 3e. scaffold_contextbench_tasks.py

**Type:** ContextBench (lightweight, context-only)

#### Stage 4: Pre-Run Validation - validate_tasks_preflight.py

**Purpose:** Static validation before Harbor execution

**Checks:**
- task.toml valid TOML format
- Required fields present (name, language, difficulty, time_limit_sec)
- instruction.md length (≥200 chars, ≤5000)
- instruction.md no template placeholders
- tests/test.sh executable
- tests/test.sh has proper structure

**Full Check Mode:** --all flag enables:
- Dockerfile build test (optional, slow)
- Runtime smoke tests (runs container, executes test.sh)

**Recent Update:** Mar 17 01:40

#### Stage 6: Post-Run Validation - validate_task_run.py

**Purpose:** Verify results after Harbor execution

**Checks:**
- result.json exists
- result.json valid JSON
- Verifier output structure correct
- Reward score present and 0.0 ≤ score ≤ 1.0
- Trajectory.json (if expected) exists
- Error classification consistent

**Recent Update:** Mar 17 01:40

### Pipeline Flow Issues

#### Issue 1: Dual Validation Stages

- **validate_tasks_preflight.py** (pre-run): checks task definition
- **validate_task_run.py** (post-run): checks execution result

**Overlap:** Both check result.json structure (redundant)
**Opportunity:** Consolidate into single TaskValidator class

#### Issue 2: Linear Pipeline with No Branching

**Current:**
- Tasks created sequentially by suite type
- No parallelization of scaffolding
- Scaffolding → validation → run is linear

**Opportunity:**
- Parallelize scaffolding scripts (they're independent)
- Pre-create all task dirs, then run all validations in parallel

#### Issue 3: No Task Versioning

**Current:** Task overwritten if scaffolded again with same ID
**Issue:** No way to track task edits, revert changes, or run A/B tests
**Opportunity:** Version task definitions (task.toml v1, v2, etc.)

### Recommendations

1. **Consolidate validation** into TaskValidator class
   ```python
   class TaskValidator:
       def validate_definition(self, task_dir) → ValidationResult
       def validate_execution(self, task_dir, result_json) → ValidationResult
   ```

2. **Parallelize scaffolding**
   ```python
   def scaffold_all_tasks(tasks, parallel=8):
       with ThreadPoolExecutor(max_workers=parallel) as executor:
           for task in tasks:
               executor.submit(scaffold_task_type(task))
   ```

3. **Add task version control**
   - Store task definitions in Git subdir
   - Track scaffolding changes
   - Enable rollback to previous versions

---

## 6. REPORT GENERATION PIPELINE

### Overview

**Purpose:** Multiple analysis reports from completed runs
**Problem:** No unified API; each script implements own logic

### Scripts & Responsibilities

| Script | Focus | Inputs | Output Format | Status |
|--------|-------|--------|----------------|--------|
| cost_report.py | Token/cost analysis | Task result.json | JSON, table | Active |
| ir_analysis.py | Retrieval quality | Trajectory JSON, GT | JSON report | Active |
| compare_configs.py | Baseline vs. MCP | MANIFEST.json | JSON, table | Active |
| oracle_ir_analysis.py | File vs. symbol retrieval | Trajectory JSON | Markdown, JSON | Active |
| retrieval_impact_analysis.py | MCP value attribution | Retrieval events, scores | JSON | Active |
| export_official_results.py | Public export | Runs/official/ | HTML, CSV | Active |
| aggregate_status.py | Status aggregation | Task result.json | JSON, table, watch | Core |
| audit_official_scores.py | Score audit | MANIFEST.json, metrics | JSON, markdown | Active |
| browse_results.py | Interactive browser | Runs/official/ | TUI | Rarely used |

### Architecture Problems

#### Problem 1: Inconsistent Input Loading

| Script | Loads from | Method | Schema Version |
|--------|-----------|--------|-----------------|
| cost_report.py | result.json | Direct read | Implicit |
| ir_analysis.py | Trajectory JSON | csb_metrics import | csb_metrics v1 |
| oracle_ir_analysis.py | Trajectory JSON | Custom parser | Ad-hoc |
| compare_configs.py | MANIFEST.json | Direct JSON | v1.0 |

**Issue:** No schema versioning; if formats change, multiple scripts break

#### Problem 2: Overlapping Analysis

| Analysis | cost_report | ir_analysis | compare_configs | aggregate_status |
|----------|-------------|-------------|-----------------|------------------|
| **Token costs** | ✓ primary | computes but doesn't report | ✗ | ✗ |
| **Retrieval metrics** | ✗ | ✓ primary | ✗ | ✗ |
| **Config comparison** | ✗ | ✗ | ✓ primary | filters only |
| **Status summary** | ✗ | ✗ | ✗ | ✓ primary |

**Issue:** Each script independently loads and analyzes all runs

#### Problem 3: Output Format Inconsistency

```python
# cost_report.py: JSON arrays
costs = [{"task": "t1", "cost": 0.024}]

# ir_analysis.py: Markdown + JSON
"## IR Metrics\nPrecision@10: 0.75\n..."

# aggregate_status.py: Structured JSON or table
{
  "csb_understand": {
    "passed": 12,
    "failed": 3,
    "error_rate": 0.2
  }
}
```

**Issue:** No standard report schema; hard to aggregate

#### Problem 4: Result.json Parsing Multiplied

All of these parse result.json independently:
- cost_report.py
- ir_analysis.py
- oracle_ir_analysis.py
- retrieval_impact_analysis.py
- extract_task_metrics.py
- audit_official_scores.py
- aggregate_status.py

**Opportunity:** Unified result.json parser in csb_metrics/

### Pipeline Examples

#### Cost Report Example

**Input:** runs/staging/run_001/*/result.json
**Output:**
```json
{
  "by_config": {
    "baseline": {
      "avg_cost": 0.038,
      "total_cost": 4.75,
      "tokens": {
        "input": 45000,
        "output": 2500,
        "cache": 12000
      }
    }
  }
}
```

#### IR Analysis Example

**Input:** runs/official/run_001/*/trajectory.json + GT
**Output:**
```json
{
  "csb_understand": {
    "precision_at_10": 0.82,
    "recall_at_10": 0.76,
    "mrr": 0.85,
    "ndcg": 0.80
  }
}
```

#### Compare Configs Example

**Input:** MANIFEST.json (multiple configs)
**Output:**
```json
{
  "divergent_tasks": [
    {
      "task_id": "task_001",
      "baseline_score": 0.75,
      "mcp_score": 0.92,
      "improvement": +0.17
    }
  ]
}
```

### Recommendations

1. **Create unified RunReport dataclass**
   ```python
   @dataclass
   class RunReport:
       run_id: str
       cost_metrics: CostMetrics
       ir_metrics: IRMetrics
       score_distribution: ScoreDistribution
       config_comparison: ConfigComparison
   ```

2. **Implement unified result.json parser**
   ```python
   class ResultParser:
       def parse(self, result_json: dict) → ParsedResult
       # Single source of truth for parsing logic
   ```

3. **Create report registry**
   ```python
   REPORT_GENERATORS = {
       "cost": CostReportGenerator,
       "ir": IRReportGenerator,
       "config_compare": ConfigCompareReportGenerator,
   }
   ```

4. **Standardize output schema**
   - All reports output compatible JSON format
   - Schema versioning (report_schema: "1.0")
   - Allows automated aggregation

---

## 7. REPO HEALTH & MAINTENANCE PIPELINE

### Overview

**Purpose:** Keep repository in healthy, consistent state

**Status:** ✓ Well-integrated, good model for consolidation

### Scripts & Relationships

```
repo_health.py (Pre-commit/push gate)
    ├─ docs_consistency_check.py (required check)
    ├─ selection_file validation (required check)
    ├─ launch_policy check (required check)
    └─ validate_tasks_preflight.py --all (optional, unless full health)

refresh_agent_navigation.py (Manual regeneration)
    ├─ sync_agent_guides.py
    ├─ generate_script_registry.py
    ├─ generate_script_index.py
    └─ generate_start_here_by_task.py
```

### Stage-by-Stage Detail

#### Stage 1: repo_health.py (Pre-commit Gate)

**Purpose:** Automatic quality gate before commit/push

**Inputs:** Current working directory
**Outputs:** Exit code 0 (pass) or 1 (fail) + detailed error list

**Required Checks:**
1. **docs_consistency_check.py**
   - Validates AGENTS.md == CLAUDE.md (root and per-directory)
   - Checks file references exist
   - Validates script registry (scripts/registry.json)
   - Size budgets: root 8-12KB, local 6KB soft
   - Detects script index vs. registry drift

2. **selection_file validation**
   - Check configs/selected_benchmark_tasks.json exists
   - Validate JSON structure
   - Verify required fields

3. **launch_policy check**
   - Verify configs/*.sh source _common.sh (if using helpers)
   - Detect raw harbor run without gating
   - Enforce confirmation pattern

**Optional Check (Full Health):**
4. **validate_tasks_preflight.py --all**
   - Full task preflight validation
   - Can be slow (Dockerfile builds)
   - Only on explicit --no-quick request

**Configuration:** configs/repo_health.json
```json
{
  "checks": {
    "docs_consistency": {
      "script": "scripts/maintenance/docs_consistency_check.py",
      "required": true
    },
    "task_preflight_static": {
      "script": "scripts/authoring/validate_tasks_preflight.py",
      "args": ["--all"],
      "required": true
    }
  },
  "quick_checks": ["docs_consistency", "selection_file", "launch_policy"]
}
```

#### Stage 2: docs_consistency_check.py (Detailed Validator)

**Purpose:** Comprehensive documentation and configuration validation

**Checks Performed:**

1. **Guide Sync Check**
   - Compare root AGENTS.md vs. CLAUDE.md (should be identical)
   - Check per-directory guides (scripts/AGENTS.md, configs/AGENTS.md, etc.)
   - Verify LOCAL_SOURCES mapping in sync_agent_guides.py

2. **File Reference Check**
   - Scan AGENTS.md and CLAUDE.md for doc references
   - Verify referenced files exist (docs/ops/SCRIPT_INDEX.md, etc.)
   - Check script references in local guides

3. **Script Registry Validation**
   - Load scripts/registry.json
   - Verify schema (required fields: name, path, category, status)
   - Check all registered scripts exist

4. **Script Index Validation**
   - Regenerate docs/ops/SCRIPT_INDEX.md
   - Compare to current (detect stale index)
   - Report differences

5. **Size Budget Checks**
   - Root guides: 8-12KB (soft budget)
   - Local guides: 6KB soft (agents may exceed)
   - Warn if approaching limits

**Output:**
```
Docs consistency: FAILED
  - doc_missing: README.md
  - missing_ref: AGENTS.md:docs/ops/SCRIPT_INDEX.md
  - size_over_budget: scripts/CLAUDE.md (14KB > 12KB limit)
```

#### Stage 3: sync_agent_guides.py (Guide Regeneration)

**Purpose:** Regenerate AGENTS.md/CLAUDE.md from canonical sources

**Input Configuration:**
```python
ROOT_SOURCE = "docs/ops/ROOT_AGENT_GUIDE.md"
LOCAL_SOURCES = {
    "scripts": "docs/ops/local_guides/scripts.md",
    "configs": "docs/ops/local_guides/configs.md",
    "docs": "docs/ops/local_guides/docs.md",
}
```

**Output:**
- ./AGENTS.md (from ROOT_SOURCE)
- ./CLAUDE.md (identical to AGENTS.md)
- ./scripts/AGENTS.md (from LOCAL_SOURCES["scripts"])
- ./scripts/CLAUDE.md (identical)
- ./configs/AGENTS.md (from LOCAL_SOURCES["configs"])
- ./configs/CLAUDE.md (identical)
- ./docs/AGENTS.md (from LOCAL_SOURCES["docs"])
- ./docs/CLAUDE.md (identical)

**Key Insight:** AGENTS.md and CLAUDE.md are identical; both generated from same source.

#### Stage 4: refresh_agent_navigation.py (Full Refresh)

**Purpose:** Orchestrate all guide regeneration and validation

**Workflow:**
1. sync_agent_guides.py (regenerate guides)
2. generate_script_registry.py (scan scripts/ → scripts/registry.json)
3. generate_script_index.py (scripts/registry.json → docs/ops/SCRIPT_INDEX.md)
4. generate_start_here_by_task.py (docs/ops/task_routes.json → docs/START_HERE_BY_TASK.md)

**Used in:** Pre-commit hook, after major script reorganization

### Architecture Strengths

✓ **Clean separation:**
- repo_health.py is the gate (exit code only)
- docs_consistency_check.py does detailed validation
- sync_agent_guides.py owns guide regeneration

✓ **Single source of truth:**
- AGENTS.md/CLAUDE.md generated from docs/ops/
- Direct edits cause docs_consistency_check to fail
- Prevents drift

✓ **Local guides separated:**
- Each directory (scripts/, configs/, docs/) can have local override
- Central registry in docs/ops/local_guides/
- Prevents accidental conflicts

### Remaining Issues

#### Issue 1: Partial Duplication

**docs_consistency_check.py reimplements some logic from:**
- sync_agent_guides.py (guide comparison)
- generate_script_index.py (index validation)

**Could be eliminated:** Have docs_consistency_check call these functions directly instead of reimplementing

#### Issue 2: Configuration vs. Code Mapping

**LOCAL_SOURCES defined in two places:**
- docs/ops/local_guides/ (filesystem structure)
- sync_agent_guides.py (hardcoded mapping)

**If new local guide added:**
1. Create docs/ops/local_guides/new_dir.md
2. Update sync_agent_guides.py LOCAL_SOURCES
3. Run refresh_agent_navigation.py

**Better:** Discover LOCAL_SOURCES from docs/ops/local_guides/ directory

### Recommendations

1. **Reduce duplication in docs_consistency_check.py**
   - Call sync_agent_guides.generate() instead of reimplementing
   - Call generate_script_index.generate() instead of reimplementing

2. **Auto-discover local sources**
   ```python
   LOCAL_SOURCES = {
       d.name: d / f"{d.name}.md"
       for d in Path("docs/ops/local_guides").iterdir()
       if d.is_dir()
   }
   ```

3. **Consolidate registry generation**
   - scripts/registry.json should be auto-generated from directory scan
   - No manual editing of registry (source of truth is filesystem)

---

## 8. CRITICAL DUPLICATIONS (Cross-Cutting)

### Duplication 1: DIR_PREFIX_TO_SUITE Mapping

**Defined in 8+ files independently:**

| File | Variable | Status |
|------|----------|--------|
| aggregate_status.py | DIR_PREFIX_TO_SUITE | Master definition |
| generate_manifest.py | DIR_PREFIX_TO_SUITE | Copy |
| promote_run.py | (implicit) | Uses local filtering |
| trace_quality_pipeline.py | SUITE_PREFIXES | Similar |
| ir_analysis.py | SUITE_MAPPING | Similar |
| audit_traces.py | SUITE_MAPPING | Similar |
| reextract_all_metrics.py | (inline) | Inline copy |
| compare_configs.py | (inline) | Inline copy |

**Risk:** If suite structure changes (new suite added), must update 8+ files

**Solution:** Extract to `configs/suite_mapping.json`
```json
{
  "csb_understand": "csb/understand",
  "csb_debug": "csb/debug",
  "csb_security": "csb/security",
  ...
}
```

### Duplication 2: Ground Truth Loading

**Implemented three different ways:**

| Script | Method | Performance |
|--------|--------|-------------|
| trace_quality_pipeline.py | Local _load_ground_truth() | Loads from disk per call |
| ir_analysis.py | csb_metrics.ground_truth import | Cached in module |
| extract_task_metrics.py | csb_metrics import | Cached |

**Solution:** Unified cached loader in csb_metrics/
```python
class GroundTruthRegistry:
    @classmethod
    @cache
    def load(cls) → Dict[str, GroundTruth]:
        # Loads all GT files once, cache persists
```

### Duplication 3: Task Directory Iteration

**Reimplemented in 10+ scripts:**

```python
# aggregate_status.py (canonical)
def _iter_task_dirs(runs_root):
    for run_dir in sorted(runs_root.iterdir()):
        if not run_dir.is_dir():
            continue
        for task_dir in sorted(run_dir.iterdir()):
            if task_dir.is_dir():
                yield task_dir

# Similar logic in: reextract_all_metrics, ir_analysis, archive_run,
#                   consolidate_staging, promote_run, extract_task_metrics,
#                   etc. (8 more implementations)
```

**Solution:** Shared utility in config_utils.py
```python
class RunIterator:
    def iter_tasks(self, runs_dir, suite_filter=None,
                   config_filter=None, exclude_patterns=None):
        # Handles: discovery, filtering, deduplication
```

### Duplication 4: Error Fingerprinting

**Partially unified** (good!) but with inconsistencies:

| Fingerprint | status_fingerprints.py | Other scripts | Category |
|-------------|----------------------|--------------|----------|
| timeout | ✓ | uses | Reliable |
| OOM | ✓ | uses | Reliable |
| Docker error | ✓ | audit_* reimplements | Inconsistent |
| Auth failure | ✓ | audit_* reimplements | Inconsistent |
| Execution failure | ✓ | trace_quality reimplements | Inconsistent |

**Issue:** status_fingerprints.fingerprint_error() should be universally used

**Solution:** Audit scripts should import and use fingerprint_error() directly

### Duplication 5: Result.json Parsing

**Implemented separately in 7+ scripts:**

Each script contains logic like:
```python
result = json.load(open(task_dir / "result.json"))
score = result.get("score", 0.0)
error = result.get("error")
trajectory = result.get("trajectory")
```

**Solution:** Unified parser in csb_metrics/
```python
class ResultParser:
    @staticmethod
    def parse(path: Path) → ParsedResult:
        # Returns typed result with validation
```

### Duplication 6: File Comparison Metrics

**F1 score calculated 4 different ways:**

| Script | Method | Calculation |
|--------|--------|-------------|
| trace_quality_pipeline.py | _parse_verifier_debug() | Parse text DEBUG line |
| oracle_checks.py | file_set_match() | Set comparison (source of truth) |
| ir_analysis.py | extract from verification.json | Use oracle result |
| compare_configs.py | aggregate per-task | Use ir_analysis result |

**Inconsistency:** Four different "sources of truth"

**Solution:** Single F1 calculation in csb_metrics/file_comparison.py
```python
def compute_f1_score(expected_files: Set[str],
                     actual_files: Set[str]) → float:
    tp = len(expected_files & actual_files)
    precision = tp / len(actual_files) if actual_files else 0.0
    recall = tp / len(expected_files) if expected_files else 0.0
    return 2 * (precision * recall) / (precision + recall + 1e-8)
```

---

## 9. DEAD CODE & UNUSED FEATURES

### Trace Quality Pipeline Dead Code

| Code | Status | Issue |
|------|--------|-------|
| `_count_search_calls()` | Extracted | Metrics computed but never aggregated |
| `_extract_symbols_from_code()` | Implemented | Symbol extraction exists, comparison incomplete |
| `_load_manifest_files()` | Implemented | Manifest loading present, no validation |
| Preamble variant checks | Partial | Multiple candidates checked, V5 only used |

### Evaluation Pipeline Dead Code

| Code | Status | Issue |
|------|--------|-------|
| `abc_score_task.py` | Active but minimal | Only used for ABC tasks, no integration |
| Multiple F1 implementations | Duplicate | 4 ways to calculate same metric |
| `abc_criteria.py` | Specialized | Only applies to ABC-type tasks |

### Coverage Audit Overlaps

| Script | Overlaps With | Issue |
|--------|---------------|-------|
| audit_gt_coverage.py | audit_official_scores.py | Both filter by GT status |
| analyze_run_coverage.py | build_canonical_manifest.py | Both discover tasks |
| audit_official_scores.py | orbit_traces.py | Both validate scores |

### Report Generation Dead Code

| Script | Status | Issue |
|--------|--------|-------|
| browse_results.py | TUI interactive | Rarely used (requires terminal) |
| export_conversation_blog_assets.py | Specific use | Only for blog posts, dead code otherwise |
| extract_v2_report_data.py | Legacy | V2 format obsolete |

### Repo Health Dead Code

None identified. Pipeline is clean.

---

## 10. IMPROVEMENT RECOMMENDATIONS SUMMARY

### Priority 1: Critical (Fixes inconsistencies)

1. **Extract DIR_PREFIX_TO_SUITE to configs/suite_mapping.json**
   - **Impact:** Eliminates 8 files maintaining duplicate mapping
   - **Effort:** 1 hour
   - **Gain:** Single source of truth for suite discovery

2. **Create unified ResultParser in csb_metrics/**
   - **Impact:** Eliminates 7+ independent parsing implementations
   - **Effort:** 2 hours (validate against existing uses)
   - **Gain:** Type safety, schema versioning

3. **Consolidate ground truth loading**
   - **Impact:** Replaces 3 implementations with 1 cached loader
   - **Effort:** 1 hour
   - **Gain:** Performance (caching), single source of truth

### Priority 2: Important (Improves maintainability)

4. **Create RunScanner abstraction**
   - **Impact:** Eliminates 10+ reimplementations of task iteration
   - **Effort:** 2-3 hours
   - **Gain:** Consistent filtering, easier to add new iteration patterns

5. **Integrate trace quality pipeline results**
   - **Impact:** Unused 2074-line module becomes useful
   - **Effort:** 3-4 hours
   - **Gain:** Quality metrics available to audit reports

6. **Make run promotion atomic**
   - **Impact:** Prevents partial promotion failures
   - **Effort:** 2-3 hours
   - **Gain:** No more inconsistent states, automatic rollback

### Priority 3: Nice-to-have (Design improvements)

7. **Unify report generation API**
   - **Impact:** Different report formats → standard schema
   - **Effort:** 4-5 hours
   - **Gain:** Easy aggregation of multiple reports

8. **Create shared error fingerprinting**
   - **Impact:** Consistent error categorization across scripts
   - **Effort:** 1-2 hours
   - **Gain:** Unified error metrics and reporting

9. **Extract suite mapping discovery**
   - **Impact:** Auto-detect local guides from filesystem
   - **Effort:** 1 hour
   - **Gain:** No manual updates when adding new local guides

---

## 11. ARCHITECTURAL RECOMMENDATIONS

### Proposed Architecture: Unified Pipeline

```
Raw Inputs (GitHub API, Harbor output, disk)
    ↓
Abstraction Layer (unified parsers, loaders)
├─ ResultParser (result.json → ParsedResult)
├─ RunIterator (consistent task discovery)
├─ GroundTruthRegistry (cached GT loading)
├─ SuiteMapping (suite discovery)
└─ ErrorFingerprinter (consistent categorization)
    ↓
Pipeline Engines (use abstractions)
├─ EvaluationEngine
│  ├─ extract_metrics()
│  ├─ score_tasks()
│  └─ compute_ir_metrics()
├─ PromotionEngine
│  ├─ validate_run()
│  ├─ generate_manifest()
│  └─ export_results()
├─ CoverageAudit
│  ├─ audit_gt_coverage()
│  ├─ audit_run_coverage()
│  └─ audit_score_quality()
└─ ReportGenerator (unified output)
    ↓
Outputs (JSON, markdown, HTML)
└─ Consumers (dashboards, exports, audits)
```

### Key Principles

1. **Single source of truth** for each concept
   - Suite mapping: configs/suite_mapping.json
   - Ground truth: GroundTruthRegistry (cached)
   - Result parsing: ResultParser class
   - Error categories: status_fingerprints.py

2. **Abstraction layer** before pipelines
   - Unified iterators, parsers, loaders
   - Insulate pipelines from format changes

3. **Schema versioning** throughout
   - result.json schema version
   - task_metrics.json schema version
   - report schema version (for aggregation)

4. **Atomic operations** at boundaries
   - Run promotion: all-or-nothing
   - Manifest generation: consistent snapshot

---

## 12. CONCLUSION

### Current State Assessment

| Aspect | Rating | Status |
|--------|--------|--------|
| **Code duplication** | 🔴 Poor | 8+ duplicate implementations |
| **Architectural coherence** | 🟡 Fair | Pipelines work but fragmented |
| **Documentation** | 🟢 Good | Most pipelines documented |
| **Error handling** | 🟡 Fair | Partial fingerprinting coverage |
| **Schema versioning** | 🔴 Poor | No version tracking |
| **Testability** | 🔴 Poor | Tightly coupled implementations |

### Key Findings

1. **Critical duplications** block adoption of new suites (8+ files must be updated)
2. **Trace quality pipeline** (2074 lines) produces unused output
3. **Coverage auditing** fragmented (5 scripts, no single source of truth)
4. **No schema versioning** (format changes break multiple scripts)
5. **Run promotion** non-atomic (risk of partial state)

### Recommended Action Plan

**Phase 1 (1-2 weeks):** Extract common abstractions
- ✓ DIR_PREFIX_TO_SUITE → configs/suite_mapping.json
- ✓ ResultParser unified class
- ✓ GroundTruthRegistry cached loader
- ✓ RunScanner iterator abstraction

**Phase 2 (2-3 weeks):** Consolidate pipelines
- ✓ Integrate trace quality results
- ✓ Make run promotion atomic
- ✓ Unify coverage auditing
- ✓ Standardize report output

**Phase 3 (1 week):** Clean up and document
- ✓ Remove dead code
- ✓ Add schema versioning
- ✓ Document all pipelines
- ✓ Add integration tests

### Estimated ROI

- **Implementation:** 3-4 weeks of engineering
- **Benefit:** 50%+ reduction in duplication, easier suite/schema changes
- **Risk reduction:** Atomic operations prevent partial state failures

---

**Report Generated:** 2026-03-17
**Audit Conducted By:** Explore Agent + CodeScaleBench Refinery
**Next Steps:** Mayor review → Phase 2 consolidation prioritization
