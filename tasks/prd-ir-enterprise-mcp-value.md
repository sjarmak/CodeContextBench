# PRD: Compelling IR Analysis for Enterprise MCP Value

## Introduction

The current IR analysis (`scripts/ir_analysis.py`) demonstrates that MCP significantly improves retrieval ranking (MRR +0.169, p=0.008) and time-to-first-relevant file (2.7x faster). However, the analysis falls short of a compelling enterprise story due to: insufficient enterprise task sample size (15 tasks), over-hinted instructions that bypass MCP discovery (9/20 tasks give exact file paths), missing retrieval-to-outcome correlation, no cost-efficiency metrics, and TTFR/TTAR coverage gaps from missing trajectory.json files.

This PRD covers three workstreams: (1) analysis pipeline improvements to produce stakeholder-ready output, (2) task redesign to force genuine MCP discovery, and (3) infrastructure fixes to ensure trajectory data is always captured.

## Goals

- Produce a stakeholder-ready IR analysis report demonstrating MCP value in enterprise codebases
- Reach 30+ enterprise/governance tasks with LOW/MEDIUM hint levels to achieve statistical power
- Connect retrieval quality to task outcomes with a composite "MCP value score"
- Add cost-efficiency metrics (tokens per relevant file, dollar ROI)
- Eliminate TTFR/TTAR data gaps by synthesizing trajectory from claude-code.txt and fixing run scripts
- Achieve statistical significance on TTFR/TTAR comparisons (currently p=0.26 / p=0.37)

## User Stories

### US-001: Synthesize trajectory.json from claude-code.txt

**Description:** As an analyst, I want trajectory.json to be generated from claude-code.txt when Harbor fails to produce it, so that TTFR/TTAR metrics have complete coverage.

**Acceptance Criteria:**
- [ ] New function `synthesize_trajectory(transcript_path: Path) -> dict` in `scripts/ccb_metrics/ir_metrics.py`
- [ ] Parses claude-code.txt JSONL: extracts tool_use/tool_result blocks with tool_use_ids
- [ ] Generates synthetic timestamps from message ordering (uses relative step indices when no real timestamps available)
- [ ] Falls back to real trajectory.json when it exists; only synthesizes when missing
- [ ] Integration in `ir_analysis.py`: auto-synthesizes for runs missing trajectory.json
- [ ] Test: run IR analysis and confirm "Skipped (no transcript)" drops to 0

### US-002: Fix run setup scripts to always produce trajectory.json

**Description:** As a benchmark operator, I want trajectory.json to always be generated during runs, so that post-run analysis never has coverage gaps.

**Acceptance Criteria:**
- [ ] Verify the H3 subagent fix in `claude_baseline_agent.py` `_get_session_dir()` is active (filters subagent dirs)
- [ ] Add a post-run validation step in `_common.sh` that warns if trajectory.json is missing after a task completes
- [ ] Document in AGENTS.md: trajectory.json generation requirements and troubleshooting
- [ ] Test: run a single task with `--path` mode and verify trajectory.json exists in output

### US-003: Retrieval-to-outcome correlation analysis

**Description:** As a stakeholder, I want to see that better retrieval quality leads to better task outcomes, not just better search metrics in isolation.

**Acceptance Criteria:**
- [ ] New function `compute_retrieval_outcome_correlation()` in `ir_analysis.py`
- [ ] Loads MANIFEST.json rewards alongside IR scores, joins by (task_id, config)
- [ ] Computes per-task: MRR delta (SG_full - baseline) vs reward delta
- [ ] Computes Spearman rank correlation between MRR and reward across tasks
- [ ] Outputs scatter data (task_id, mrr_bl, mrr_sg, reward_bl, reward_sg, mrr_delta, reward_delta)
- [ ] Adds correlation section to table output: r, p-value, interpretation
- [ ] Test: run `python3 scripts/ir_analysis.py` and see RETRIEVAL-OUTCOME CORRELATION section

### US-004: Composite MCP value score

**Description:** As a stakeholder, I want a single composite score per task that combines retrieval quality, task outcome, and efficiency into one "MCP value" number.

**Acceptance Criteria:**
- [ ] New dataclass `MCPValueScore` in `scripts/ccb_metrics/ir_metrics.py` with components:
  - `retrieval_lift`: normalized MRR delta (SG_full - baseline) / max possible delta
  - `outcome_lift`: reward delta (SG_full - baseline)
  - `efficiency_lift`: normalized TTFR reduction (baseline - SG_full) / baseline
  - `cost_ratio`: (SG_full tokens for retrieval) / (baseline tokens for retrieval)
  - `composite`: weighted combination of above (weights configurable)
- [ ] New function `compute_mcp_value_scores()` that joins IR scores, MANIFEST rewards, and token data
- [ ] Aggregation by suite in table output: mean composite score per benchmark
- [ ] Tasks ranked by composite score in output (top 10 MCP-helped, top 10 MCP-hurt)
- [ ] Test: run analysis and see MCP VALUE SCORE section with per-suite and per-task rankings

### US-005: Cost-efficiency metrics

**Description:** As a stakeholder, I want to understand the ROI of MCP: how many tokens/dollars does it cost per relevant file found.

**Acceptance Criteria:**
- [ ] New metrics in IR analysis: `tokens_per_relevant_file`, `tokens_before_first_relevant`
- [ ] Reads task_metrics.json for token counts alongside IR scores
- [ ] Computes: total input tokens / n_overlap (tokens per relevant file found)
- [ ] Computes: cumulative tokens up to TTFR step (tokens spent before first relevant file)
- [ ] Aggregates by config and suite in table output
- [ ] Adds delta and percentage change columns (baseline vs SG_full)
- [ ] Test: run analysis and see COST EFFICIENCY section

### US-006: Redesign 9 over-hinted enterprise tasks

**Description:** As a benchmark designer, I want to remove exact file paths, line numbers, and implementation roadmaps from over-hinted tasks so that MCP discovery is genuinely exercised.

**Acceptance Criteria:**
- [ ] Redesign instructions for these 9 HIGH_HINT tasks:
  - `dep-discovery-001`: Remove "approximately 9 packages" and starting file hint
  - `dep-impact-001`: Remove `options.py` path, `admin_changelist/` path, "approximately 5 files"
  - `dep-refactor-001`: Remove `resource.go` path, "approximately 10 call sites across 8 files"
  - `dep-refactor-002`: Remove all 3 implementation file paths (`fs/store.go`, `fs/snapshot.go`, `sql/common/flag.go`)
  - `polyglot-ecosystem-001`: Remove line numbers (25-92), field number (10), `GetSegmentKeys` pattern hint
  - `multi-team-ownership-002`: Remove `duration.go` filename, `DurationTracker` struct name
  - `degraded-context-001`: Remove `errors.go` filename, struct field names, phase-specific wrapping targets
  - `repo-scoped-access-002`: Remove `metrics.go` filename, `EvaluationMetrics` struct name
  - `policy-enforcement-001`: Remove `SoftDeleteManager` class name, method signatures, field names
- [ ] Each redesigned instruction preserves the problem statement and expected behavior
- [ ] Each redesigned instruction does NOT name specific files, line numbers, or struct/class names
- [ ] Verifiers (test.sh) remain unchanged — they test the same behavior
- [ ] Ground truth files updated if instruction changes affect expected file access patterns

### US-007: Add 15 new enterprise tasks with LOW hint levels

**Description:** As a benchmark designer, I want 15+ new enterprise tasks that describe problems without revealing file locations, forcing the agent to use MCP for discovery.

**Acceptance Criteria:**
- [ ] 15 new tasks across enterprise and governance suites
- [ ] Each task has: task.toml, instruction.md, Dockerfile, tests/test.sh
- [ ] All instructions are LOW_HINT: describe the bug/feature/change by behavior only, no file paths
- [ ] Task types cover enterprise scenarios: cross-repo dependency, multi-team ownership, large codebase navigation, API contract changes, security boundary enforcement
- [ ] At least 5 tasks use multi-file ground truth (3+ files to find)
- [ ] At least 3 tasks require cross-package or cross-module discovery
- [ ] Ground truth files documented for each new task
- [ ] All tasks pass preflight validation (`/validate-tasks`)
- [ ] Tasks registered in `selected_benchmark_tasks.json`

### US-008: Stakeholder-ready report output

**Description:** As a stakeholder, I want the IR analysis to produce a clean, formatted report suitable for sharing in enterprise contexts.

**Acceptance Criteria:**
- [ ] New `--report` flag on `ir_analysis.py` that generates a structured markdown report
- [ ] Report sections: Executive Summary, Retrieval Quality, Time-to-Context, Cost Efficiency, MCP Value Rankings, Statistical Methodology
- [ ] Executive Summary: 3-4 bullet points with key findings and statistical significance
- [ ] Each section includes: metric table, interpretation paragraph, per-suite breakdown
- [ ] Enterprise-friendly labels (baseline = "IDE-native", SG_full = "Context infrastructure")
- [ ] Report saved to `docs/ir_analysis_report.md`
- [ ] Test: run `python3 scripts/ir_analysis.py --report` and verify output is clean markdown

### US-009: Rerun redesigned tasks and validate

**Description:** As a benchmark operator, I want to rerun all redesigned enterprise tasks (baseline + SG_full) to get clean paired data with the new instructions.

**Acceptance Criteria:**
- [ ] All 9 redesigned tasks rerun with both baseline and SG_full configs
- [ ] All 15 new tasks run with both baseline and SG_full configs
- [ ] All runs produce trajectory.json (verified post-run)
- [ ] MANIFEST regenerated with new results
- [ ] IR analysis rerun shows 30+ enterprise/governance tasks with TTFR/TTAR data
- [ ] Statistical tests on TTFR and TTAR reach p < 0.05 (or results documented if not)

## Functional Requirements

- FR-1: `synthesize_trajectory()` must parse claude-code.txt JSONL and produce a dict compatible with `extract_time_to_context()` input format
- FR-2: Synthetic trajectory must use monotonic step indices as timestamps when real timestamps unavailable
- FR-3: The `_common.sh` post-run check must log a WARNING (not error) when trajectory.json is missing, to avoid blocking the run pipeline
- FR-4: Retrieval-outcome correlation must use Spearman rank correlation (not Pearson) since rewards are ordinal (0/1 or 0-1 continuous)
- FR-5: Composite MCP value score weights must be configurable via CLI args with sensible defaults
- FR-6: Cost-efficiency metrics must use agent task time tokens (from task_metrics.json), not raw wall-clock token counts
- FR-7: Redesigned task instructions must be reviewed to ensure verifiers still pass — the expected behavior must not change
- FR-8: The `--report` flag must work with all existing filters (`--suite`, `--json`, etc.)
- FR-9: New enterprise tasks must use existing Dockerfiles/environments (Django, Flipt) to avoid new infrastructure
- FR-10: Ground truth for new tasks must be added to `ground_truth.py` using the manual extraction pattern (like K8s Docs, TAC, LargeRepo)

## Non-Goals

- No changes to the MCP preamble or agent behavior — this is analysis and task design only
- No new benchmark suites — tasks go into existing `ccb_enterprise` and `ccb_governance`
- No real-time dashboard — output is static markdown/JSON reports
- No changes to Harbor internals — trajectory synthesis works around gaps, not fixes Harbor
- No LoCoBench reinclusion — it remains dropped from IR analysis
- No SG_base analysis — only baseline vs SG_full (SG_base was dropped project-wide)

## Technical Considerations

- `trajectory.json` is generated by Harbor's `ClaudeCode._convert_events_to_trajectory()` from session JSONL files, not from claude-code.txt directly. The synthesis function works from claude-code.txt (which is always present) as a fallback.
- The H3 bug (subagent dirs confusing `_get_session_dir()`) is already fixed in `claude_baseline_agent.py` lines 160-201. US-002 verifies this fix is active and adds runtime warnings.
- MANIFEST.json lives inside symlinked `runs/official/` — retrieval-outcome join must resolve through the symlink.
- Token data comes from `task_metrics.json` (extracted by `reextract_all_metrics.py`), not from trajectory.json or MANIFEST.
- Enterprise tasks use two codebases: Django (Python) and Flipt (Go). New tasks should reuse these to avoid Dockerfile proliferation.

## Success Metrics

- 30+ enterprise/governance tasks with paired baseline + SG_full data
- TTFR statistical significance: p < 0.05 on paired enterprise tasks
- Retrieval-outcome Spearman correlation: r > 0.3 with p < 0.05
- Zero "Skipped (no transcript)" in IR analysis output
- Stakeholder report clearly demonstrates: MCP finds relevant files faster, in better order, and this translates to better task outcomes

## Open Questions

- Should the composite MCP value score normalize across benchmarks (z-score) or use raw deltas? Z-scoring prevents large-reward benchmarks from dominating.
- For synthetic trajectory timestamps: should we use step count (1, 2, 3...) or estimate real seconds from token counts? Step count is simpler but less comparable to real TTFR.
- How many of the 15 new tasks should be Flipt (Go) vs Django (Python)? Current split is 7 Flipt / 13 Django.
- Should redesigned tasks be versioned (dep-impact-001-v2) or replace in-place? In-place is cleaner but loses history.
