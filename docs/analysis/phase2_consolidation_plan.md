# Phase 2: Pipeline Consolidation - Integration

**Previous work:** Phase 1 extracted common abstractions (DIR_PREFIX_TO_SUITE, ResultParser, GroundTruthRegistry, RunScanner)

**Phase 2 goals:** Integrate abstraction layers into major pipelines to eliminate redundant code and unify workflows.

## 2.1 Integrate Trace Quality Results (est. 4-6h)

**Current issue:** Trace Quality Pipeline (2074 lines) produces detailed validation reports but outputs are never integrated into MANIFEST.json or audit outputs.

**Approach:**
1. Create `TraceQualityReporter` abstraction that encapsulates trace quality analysis
2. Update `trace_quality_pipeline.py` to output structured JSON (not just logs)
3. Modify `generate_manifest.py` to load and merge trace quality metrics
4. Add quality flags to task metadata in MANIFEST.json

**Files to update:**
- scripts/evaluation/trace_quality_pipeline.py
- scripts/maintenance/generate_manifest.py
- scripts/csb_metrics/trace_quality.py (new - abstraction layer)

**Success criteria:** Quality validation results appear in official MANIFEST.json

## 2.2 Make Run Promotion Atomic (est. 3-4h)

**Current issue:** Non-atomic workflow can fail halfway:
- consolidate_staging.py → promote_run.py → generate_manifest.py → extract_metrics.py → export_results.py
- Partial state on failure = corrupted official runs

**Approach:**
1. Create `RunPromotionOrchestrator` that coordinates all steps atomically
2. Implement rollback on failure using transaction pattern
3. Write intermediate state to temporary directory, only commit on final success
4. Add `--validate-only` mode to each step for pre-flight checks

**Files to update:**
- scripts/running/promote_run.py (orchestrator entry point)
- scripts/evaluation/consolidate_staging.py (add transaction support)
- scripts/maintenance/generate_manifest.py (add transaction support)
- scripts/maintenance/generate_eval_report.py (add transaction support)
- scripts/analysis/export_official_results.py (add transaction support)
- scripts/evaluation/extract_task_metrics.py (add transaction support)

**Success criteria:** All-or-nothing promotion; partial failures don't corrupt official runs

## 2.3 Unify Coverage Auditing (est. 3-4h)

**Current issue:** 5 scripts define "complete" differently:
- audit_gt_coverage.py (ground truth coverage)
- analyze_run_coverage.py (run completion)
- audit_official_scores.py (score legitimacy)
- build_canonical_manifest.py (task registry)
- build_repo_manifests.py (repo metadata)

**Approach:**
1. Create `CoverageAudit` abstraction with unified definitions
2. Define coverage tiers: missing, partial, complete, verified
3. Single query interface: `coverage.get_tasks_by_status(suite, status)`
4. Update all 5 scripts to use unified interface

**Files to update:**
- scripts/csb_metrics/coverage_audit.py (new - unified abstraction)
- scripts/evaluation/audit_gt_coverage.py
- scripts/analysis/analyze_run_coverage.py
- scripts/evaluation/audit_official_scores.py
- scripts/infra/build_canonical_manifest.py
- scripts/infra/build_repo_manifests.py

**Success criteria:** Single query returns consistent coverage across all 5 scripts

## 2.4 Standardize Report Output (est. 2-3h)

**Current issue:** Multiple report scripts produce inconsistent output:
- cost_report.py → JSON arrays
- ir_analysis.py → markdown tables
- compare_configs.py → structured JSON
- aggregate_status.py → JSON with custom schema
- generate_eval_report.py → markdown with embedded JSON

**Approach:**
1. Create `ReportFormatter` abstraction with standard output schemas
2. Define common report structure: metadata, summary, findings, details
3. Support multiple output formats: JSON, markdown, CSV
4. Update all report scripts to use unified formatter

**Files to update:**
- scripts/csb_metrics/report_formatter.py (new - unified abstraction)
- scripts/evaluation/cost_report.py
- scripts/analysis/ir_analysis.py
- scripts/evaluation/compare_configs.py
- scripts/analysis/aggregate_status.py
- scripts/maintenance/generate_eval_report.py

**Success criteria:** All reports have consistent structure and can be post-processed uniformly

## Implementation Order

1. **2.1 Trace Quality** (4-6h) - Feeds into manifest generation
2. **2.2 Run Promotion** (3-4h) - Depends on manifest generation from 2.1
3. **2.3 Coverage Audit** (3-4h) - Independent, can run in parallel with 2.1-2.2
4. **2.4 Report Format** (2-3h) - Independent, can run in parallel with 2.1-2.3

**Total estimated effort:** 12-17 hours of work

## Rollback Strategy

If Phase 2 introduces regressions:
1. Each task outputs versioned abstractions (e.g., `trace_quality_v1`, `coverage_audit_v1`)
2. Can switch back to old implementations by importing old module versions
3. Gradual migration: old code runs in parallel during transition period

## Success Metrics

- [ ] Trace quality results integrated into MANIFEST.json
- [ ] Run promotion is atomic (all-or-nothing)
- [ ] Coverage audit returns consistent results across all 5 scripts
- [ ] All reports have unified structure
- [ ] No performance regression in major pipelines
- [ ] All existing tests pass
