# PRD: Enterprise Engineering Outcomes Evaluation System

## Introduction

Transform CodeContextBench from a research-oriented agent performance benchmark into an enterprise-grade evaluation system that demonstrates operational, economic, and governance impact of context infrastructure for real software organizations.

The benchmark currently measures agent task success across configurations (baseline vs. SG_full). The enterprise evolution adds three new evaluation layers — workflow impact, business outcomes, and governance compliance — that translate raw task results into metrics meaningful to platform engineering leaders, VP Engineering / CTO stakeholders, and enterprise procurement/security teams.

**Target market**: Early majority enterprises in regulated industries (fintech, healthcare tech, defense contractors, insurance, enterprise SaaS) with large legacy codebases, strict data boundaries, and an AI mandate. These organizations cannot rely on public LLM context and need governance, developer efficiency, and risk reduction evidence before adopting AI context infrastructure.

**Design constraint**: All new work layers on top of the existing scientific backbone (reproducibility, deterministic runs, task harness, QA layers). Nothing is removed.

## Goals

- Derive workflow impact metrics (engineering time saved, navigation reduction, onboarding speed) from existing trace data
- Build economic benchmarking (ROI, cost-per-success, productivity-per-dollar) from existing cost instrumentation
- Create governance simulation benchmark tasks that evaluate permission enforcement, cross-boundary leakage, and audit trail correctness
- Add reliability-at-scale analysis (variance distributions, confidence intervals, failure clustering) from multi-run data
- Implement failure-mode analysis engine that classifies why agents fail and what context was missing
- Produce structured JSON reports consumed by the CodeContextBench Dashboard for technical, workflow, executive, and failure analysis views
- Simplify configurations to 2-config (baseline + SG_full), dropping SG_base
- Add enterprise-realistic task categories (multi-team boundaries, stale docs, legacy dependencies, partial context)

## User Stories

### Phase 1: Configuration Simplification

#### US-001: Consolidate to 2-config evaluation
**Description:** As a benchmark operator, I want to run only baseline and SG_full configurations so that results are cleaner and run costs are halved.

**Acceptance Criteria:**
- [ ] All `*_3config.sh` scripts renamed/refactored to `*_2config.sh` with only baseline and sourcegraph_full
- [ ] `_common.sh` CONFIGS array defaults to `("baseline" "sourcegraph_full")`
- [ ] `compare_configs.py` handles 2-config comparison without breaking
- [ ] `generate_manifest.py` continues to process existing SG_base historical data but new runs only produce 2 configs
- [ ] `aggregate_status.py` gap analysis updated for 2-config expectations
- [ ] All scripts pass `bash -n` syntax check

---

### Phase 2: Workflow Metrics Layer (Derived from Existing Data)

#### US-002: Define workflow taxonomy and time model
**Description:** As a product marketer, I want engineering workflows categorized and mapped to time estimates so that task results translate to "hours saved."

**Acceptance Criteria:**
- [ ] Create `scripts/workflow_taxonomy.py` defining workflow categories:
  - `code_comprehension` — understanding unfamiliar code
  - `cross_repo_navigation` — locating code across repositories
  - `dependency_analysis` — tracing dependency chains
  - `bug_localization` — finding root cause
  - `feature_implementation` — producing a PR
  - `onboarding` — understanding a new service/repo
- [ ] Each category maps existing benchmark suites: e.g., LoCoBench→comprehension, CrossRepo→navigation, DIBench→dependency, SWE-Pro→implementation
- [ ] Each category includes calibrated time multipliers (tokens-to-minutes, tool-calls-to-minutes) based on published developer productivity research
- [ ] Time model documented in `docs/WORKFLOW_METRICS.md` with methodology and citations
- [ ] Taxonomy importable by other scripts as a Python module

#### US-003: Build workflow metrics extraction engine
**Description:** As an analyst, I want to extract workflow-level metrics from existing trace data so that I can compute time savings per workflow category.

**Acceptance Criteria:**
- [ ] Create `scripts/workflow_metrics.py` that:
  - Reads traces from `runs/official/` (reusing `aggregate_status.py` scan logic)
  - For each task, computes: agent_task_time, tool_call_count, file_reads, file_edits, search_queries, MCP_calls, context_switches (from trajectory.json)
  - Maps each task to workflow category via taxonomy
  - Computes per-workflow delta: `baseline_time - sg_full_time` = time saved
  - Estimates engineer-equivalent time using taxonomy multipliers
- [ ] Outputs `workflow_metrics.json` with per-task and per-category aggregates
- [ ] JSON schema matches dashboard's `enterprise_metrics_schema.json` structure
- [ ] Supports `--suite` and `--config` filters
- [ ] Handles missing trace data gracefully (skip task, log warning)

#### US-004: Compute navigation overhead reduction
**Description:** As a dev productivity leader, I want to see how much navigation overhead MCP reduces so that I can justify the infrastructure investment.

**Acceptance Criteria:**
- [ ] `workflow_metrics.py` computes navigation metrics per task:
  - `file_access_count` — total files read by agent
  - `search_query_count` — grep/glob/MCP search calls
  - `context_switch_count` — transitions between distinct files
  - `navigation_ratio` — search+read calls / total tool calls
- [ ] Computes delta between baseline and SG_full for each metric
- [ ] Aggregates by workflow category and benchmark suite
- [ ] Outputs `navigation_metrics` section in `workflow_metrics.json`

---

### Phase 3: Economic Benchmarking

#### US-005: Extend cost instrumentation with ROI metrics
**Description:** As a VP Engineering, I want cost-per-successful-outcome and productivity-per-dollar metrics so that I can build a business case for context infrastructure.

**Acceptance Criteria:**
- [ ] Create `scripts/economic_analysis.py` that:
  - Reads cost data from `task_metrics.json` / `result.json` (reusing `cost_report.py` extraction)
  - Computes per-task: `cost_per_success` = cost / reward (only for passing tasks)
  - Computes per-config: `avg_cost_per_success`, `total_cost`, `pass_rate`
  - Computes `marginal_cost_of_context` = SG_full_cost - baseline_cost per task
  - Computes `productivity_per_dollar` = tasks_passed / total_cost
  - Computes `token_efficiency` = tokens_used / reward (lower is better for passing tasks)
- [ ] Outputs `economic_metrics.json` with per-task and aggregate sections
- [ ] JSON includes `roi_summary` block: cost delta, pass rate delta, implied engineering hours saved per dollar
- [ ] Supports `--suite` filter

#### US-006: Build comparative cost model
**Description:** As a procurement analyst, I want to compare context infrastructure costs against baseline workflows so that I can evaluate total cost of ownership.

**Acceptance Criteria:**
- [ ] `economic_analysis.py` includes `--compare` mode that:
  - Computes per-task cost delta (SG_full vs baseline)
  - Categorizes tasks: "MCP cost-effective" (lower cost + same/better outcome), "MCP premium" (higher cost + better outcome), "MCP waste" (higher cost + same/worse outcome)
  - Computes break-even analysis: how many engineer-hours must be saved per dollar of MCP cost for positive ROI
- [ ] Outputs `cost_comparison` section in `economic_metrics.json`
- [ ] Handles tasks present in only one config (marks as "no comparison available")

---

### Phase 4: Governance Simulation

#### US-007: Design governance task format
**Description:** As a security architect, I want benchmark tasks that simulate enterprise permission boundaries so that I can evaluate whether AI context infrastructure respects data access controls.

**Acceptance Criteria:**
- [ ] Create `docs/GOVERNANCE_BENCHMARK.md` documenting:
  - Task design: how permission boundaries are simulated (file withholding, mock ACLs in CLAUDE.md, restricted directories)
  - 5 governance scenarios: (1) repo-scoped access, (2) sensitive file exclusion, (3) cross-team boundary enforcement, (4) audit trail generation, (5) degraded-context correctness
  - Evaluation criteria: leakage detection, boundary compliance, graceful degradation
  - Integration with existing Harbor task harness
- [ ] Design reviewed and approved before implementation (this US is design-only)

#### US-008: Scaffold governance benchmark suite
**Description:** As a benchmark developer, I want a `ccb_governance` benchmark suite with 6-8 tasks so that governance compliance can be empirically measured.

**Acceptance Criteria:**
- [ ] Create `benchmarks/ccb_governance/` directory with 6-8 task subdirectories
- [ ] Each task has: `task.toml`, `instruction.md`, `environment/Dockerfile`, `tests/test.sh`
- [ ] Tasks cover governance scenarios from US-007:
  - 2 tasks: repo-scoped access (agent must NOT use files from restricted repos)
  - 2 tasks: sensitive file exclusion (agent must complete task without accessing .env, credentials, etc.)
  - 1 task: cross-team boundary (agent must modify only owned files, not upstream team's code)
  - 1 task: audit trail (agent must log all file accesses, verifier checks completeness)
  - 1-2 tasks: degraded context (some files deliberately missing, agent must still produce correct output)
- [ ] All tasks buildable with `docker build` and passable by a competent agent
- [ ] Tasks registered in `selected_benchmark_tasks.json` with governance metadata
- [ ] Verifiers check for policy violations (not just task correctness)

#### US-009: Implement governance evaluator
**Description:** As a compliance officer, I want automated evaluation of governance compliance so that audit reports can be generated from benchmark runs.

**Acceptance Criteria:**
- [ ] Create `scripts/governance_evaluator.py` that:
  - For each governance task, reads trajectory.json to extract all file accesses
  - Compares accessed files against task's permitted file list (from task.toml metadata)
  - Detects boundary violations: unauthorized file reads, cross-repo leakage, sensitive file access
  - Scores: `compliance_rate` = tasks_without_violations / total_governance_tasks
  - Generates per-task violation report with specific file paths and tool calls
- [ ] Outputs `governance_report.json` with per-task and aggregate compliance metrics
- [ ] Supports both baseline and SG_full analysis (governance applies to both)
- [ ] Machine-readable violation records suitable for audit trail

---

### Phase 5: Reliability Analysis

#### US-010: Build variance analysis pipeline
**Description:** As an enterprise buyer, I want to see performance variance and reliability confidence intervals so that I can assess predictability, not just peak performance.

**Acceptance Criteria:**
- [ ] Create `scripts/reliability_analysis.py` that:
  - Groups tasks by (suite, config) and computes: mean reward, std dev, min, max, median
  - Computes 95% confidence intervals for pass rate per suite/config using bootstrap (1000 samples)
  - Computes cross-suite consistency: Gini coefficient of per-suite pass rates
  - Identifies "unreliable" tasks: tasks with different outcomes across re-runs (if multi-run data exists)
- [ ] Outputs `reliability_metrics.json` with:
  - Per-suite: mean, std, CI_lower, CI_upper, n_tasks
  - Per-config: aggregate reliability score (mean - 2*std as floor)
  - Cross-suite consistency index
- [ ] Handles single-run data gracefully (reports point estimates, notes insufficient data for CI)

#### US-011: Add failure clustering analysis
**Description:** As a product strategist, I want to know if failures cluster by domain, language, or complexity so that I can communicate strengths and limitations honestly.

**Acceptance Criteria:**
- [ ] `reliability_analysis.py` includes failure clustering:
  - Groups failed tasks by: language, difficulty, benchmark suite, SDLC phase, MCP benefit score quartile
  - Computes failure rate per group
  - Identifies statistically over-represented failure groups (chi-squared or Fisher exact test)
  - Reports "failure clusters": groups with failure rate >2x overall average
- [ ] Outputs `failure_clusters` section in `reliability_metrics.json`
- [ ] Includes human-readable descriptions: "Hard Python tasks fail 3x more often than average"

---

### Phase 6: Failure-Mode Analysis Engine

#### US-012: Build failure taxonomy
**Description:** As a product manager, I want every failed task classified by failure mode so that I can distinguish infrastructure failures from genuine agent limitations.

**Acceptance Criteria:**
- [ ] Create `scripts/failure_analysis.py` that extends `status_fingerprints.py` with higher-level failure taxonomy:
  - `context_insufficient` — agent couldn't find needed code/docs
  - `context_misused` — agent found relevant code but misinterpreted it
  - `implementation_error` — agent understood context but wrote wrong code
  - `verification_mismatch` — agent's solution is plausible but doesn't match verifier expectations
  - `infrastructure_failure` — Docker, auth, timeout, MCP connection errors
  - `scope_exceeded` — task requires changes beyond what agent attempted
- [ ] Classification uses: error fingerprints (existing), trajectory analysis (tool calls before failure), and result.json exception info
- [ ] Each failed task gets a `failure_mode` label and `failure_detail` explanation

#### US-013: Implement context attribution analysis
**Description:** As a solutions engineer, I want to know for each failure whether centralized context would have / did change the outcome so that I can build case studies.

**Acceptance Criteria:**
- [ ] `failure_analysis.py` includes context attribution for each failed task:
  - For baseline failures: checks if same task passed in SG_full → `context_resolved`
  - For SG_full failures: analyzes if MCP tools were used, what was searched, what was found → `context_attempted_insufficient` or `context_not_attempted`
  - For both-fail tasks: compares trajectories to identify if SG_full got further → `context_partial_help`
- [ ] Each task gets a `context_impact` classification: `resolved`, `partial_help`, `no_impact`, `made_worse`
- [ ] Outputs `failure_analysis.json` with per-task records and aggregate counts per failure mode

#### US-014: Generate structured failure reports
**Description:** As a marketing lead, I want machine-readable and human-readable failure analysis reports so that I can extract proof points for enterprise conversations.

**Acceptance Criteria:**
- [ ] `failure_analysis.py --report` generates:
  - `failure_analysis.json` — full machine-readable records
  - `failure_analysis.md` — human-readable report with:
    - Executive summary (failure rate by config, top failure modes)
    - Context impact summary (how many failures resolved by context infrastructure)
    - Per-suite breakdown with specific examples
    - "Case studies" section: 3-5 most illustrative context-resolved failures with before/after narratives
- [ ] JSON schema documented and compatible with dashboard ingestion
- [ ] Report includes `residual_limitations` section: failures that persist even with full context

---

### Phase 7: Enterprise Report Generation

#### US-015: Define report JSON schemas
**Description:** As a dashboard developer, I want well-defined JSON schemas for all enterprise metrics so that the dashboard can reliably consume new data.

**Acceptance Criteria:**
- [ ] Create `schemas/` directory with JSON Schema (Draft 7) files:
  - `workflow_metrics_schema.json`
  - `economic_metrics_schema.json`
  - `governance_report_schema.json`
  - `reliability_metrics_schema.json`
  - `failure_analysis_schema.json`
  - `enterprise_report_schema.json` (top-level envelope)
- [ ] Each schema includes required fields, types, descriptions, and examples
- [ ] Schemas validated against sample outputs from US-003, US-005, US-009, US-010, US-013
- [ ] Schemas compatible with existing dashboard `enterprise_metrics_schema.json`

#### US-016: Build enterprise report generator
**Description:** As a benchmark operator, I want a single command that produces all enterprise reports so that report generation is reproducible and automated.

**Acceptance Criteria:**
- [ ] Create `scripts/generate_enterprise_report.py` that orchestrates:
  - Calls workflow_metrics, economic_analysis, governance_evaluator, reliability_analysis, failure_analysis
  - Aggregates all outputs into `enterprise_report.json` (top-level envelope)
  - Generates `ENTERPRISE_REPORT.md` with four sections:
    1. **Technical Report**: retrieval accuracy, task success rates, performance metrics (from existing generate_eval_report.py)
    2. **Workflow Report**: time saved per category, navigation reduction, onboarding improvement
    3. **Executive Report**: productivity impact, economic efficiency, governance readiness, reliability score
    4. **Failure Analysis Dossier**: recurring breakdowns, context-driven resolutions, residual limitations
- [ ] Each section independently renderable (can extract just executive report)
- [ ] `--output-dir` flag to control output location (default: `reports/`)
- [ ] Validates output against schemas from US-015
- [ ] Exit code 0 only if all sections generated successfully

#### US-017: Add executive summary generator
**Description:** As a CTO reading the report, I want a 1-page executive summary with key numbers so that I can quickly assess whether context infrastructure is worth investing in.

**Acceptance Criteria:**
- [ ] `generate_enterprise_report.py` produces `executive_summary.json` and `EXECUTIVE_SUMMARY.md` containing:
  - **Headline metric**: "Context infrastructure improves agent reliability by X% across Y enterprise-scale tasks"
  - **Time savings**: "Estimated Z hours/week saved per 10 engineers in code navigation and comprehension"
  - **Economic efficiency**: "Cost per successful task reduced by $X.XX (Y% improvement)"
  - **Governance**: "N/M governance tasks passed compliance checks — AI deployable under enterprise data boundaries"
  - **Reliability**: "95% confidence interval: [X%, Y%] task success rate across Z domains"
  - **Key risk**: Top residual limitation in 1 sentence
- [ ] All numbers computed from actual benchmark data (no hardcoded values)
- [ ] Summary fits on 1 printed page (under 500 words)

---

### Phase 8: Enterprise Task Expansion

#### US-018: Design enterprise-realistic task templates
**Description:** As a benchmark designer, I want task templates that model real organizational complexity so that results are credible to enterprise architects.

**Acceptance Criteria:**
- [ ] Create `docs/ENTERPRISE_TASK_DESIGN.md` documenting:
  - Task complexity dimensions: multi-team ownership, conflicting docs, stale artifacts, partial context, legacy deps, polyglot services
  - Template for each dimension with example task structure
  - How to simulate ambiguity, knowledge fragmentation, and institutional memory loss in task design
  - Integration with existing Harbor task format
- [ ] Design reviewed and approved before task creation

#### US-019: Add multi-team ownership boundary tasks
**Description:** As a benchmark suite, I want tasks where the agent must navigate multi-team ownership boundaries and conflicting documentation so that we measure real enterprise navigation complexity.

**Acceptance Criteria:**
- [ ] Create `benchmarks/ccb_enterprise/` directory as a new benchmark suite
- [ ] Add 3 synthetic tasks with realistic multi-team and conflicting-docs scenarios:
  - Multi-team ownership with different coding styles across teams
  - Stale documentation that contradicts actual code patterns
  - Shared library contribution process with contribution guide requirements
- [ ] Each task has: task.toml, instruction.md, environment/Dockerfile, tests/test.sh
- [ ] Tasks buildable and verifiable with existing Harbor infrastructure
- [ ] Tasks registered in `selected_benchmark_tasks.json` with `benchmark='ccb_enterprise'`

**Automated via:** `ralph-ent-governance` Ralph instance (US-019, priority 5)

#### US-020: Add legacy system dependency tasks
**Description:** As a benchmark suite, I want tasks involving legacy system dependencies and polyglot service ecosystems so that we measure agent effectiveness in realistic enterprise codebases.

**Acceptance Criteria:**
- [ ] Add 2-3 synthetic tasks to `benchmarks/ccb_enterprise/`:
  - Legacy module with deprecated APIs, no type hints, minimal comments — agent must maintain backward compatibility
  - Polyglot ecosystem (Python + Node.js) with shared JSON schema — agent must propagate changes across language boundaries
- [ ] Tasks buildable and verifiable with existing Harbor infrastructure
- [ ] All `ccb_enterprise` tasks registered in `selected_benchmark_tasks.json`

**Automated via:** `ralph-ent-governance` Ralph instance (US-020, priority 6)

---

### Phase 9: SWE-bench Pro Variance Trials

#### US-021: Run variance trials for statistical power
**Description:** As a researcher, I want multiple independent runs of the same tasks so that I can compute meaningful confidence intervals and variance statistics.

**Acceptance Criteria:**
- [ ] Create `configs/variance_trials.sh` that runs baseline + SG_full on a representative subset (10-15 tasks across 3+ suites) for 3 independent trials each
- [ ] Trials use different random seeds / fresh Docker containers (no cache carryover)
- [ ] Results stored in separate batch directories with trial identifier
- [ ] `reliability_analysis.py` can ingest multi-trial data and compute per-task variance
- [ ] Total cost estimate documented before execution

---

## Functional Requirements

- FR-1: All new scripts must be runnable independently (`python3 scripts/<script>.py`) and as part of the orchestrated report pipeline
- FR-2: All JSON outputs must validate against their JSON Schema definitions
- FR-3: All scripts must support `--suite` and `--config` filters for targeted analysis
- FR-4: All scripts must handle missing/partial data gracefully (log warnings, skip tasks, never crash)
- FR-5: The enterprise report generator must be idempotent — running it twice produces identical output given identical inputs
- FR-6: New governance tasks must follow existing Harbor task format (task.toml, instruction.md, environment/Dockerfile, tests/test.sh)
- FR-7: Economic metrics must use the corrected cost extraction (from claude-code.txt JSONL, not cumulative n_input_tokens) per the existing reextract_all_metrics.py approach
- FR-8: Workflow time estimates must cite methodology and be clearly labeled as modeled/estimated (not measured)
- FR-9: All reports must distinguish between "measured" metrics (actual benchmark data) and "projected" metrics (modeled estimates)
- FR-10: Configuration simplification must preserve backward compatibility with historical SG_base data in MANIFEST
- FR-11: Dashboard integration must use new dedicated JSON schemas (not extending existing `enterprise_metrics_schema.json`)
- FR-12: Governance evaluator must produce audit-trail-quality records (timestamp, tool call, file accessed, policy evaluation result)

## Non-Goals (Out of Scope)

- **Real RBAC/SCIM integration**: v1 uses synthetic permission simulation only. Real IAM integration is a stretch goal.
- **Live dashboard UI development**: Dashboard changes are a separate project (CodeContextBench_Dashboard repo). This PRD covers JSON/markdown output generation only.
- **Copilot/Cursor agent drivers**: v1 does not add new agent configurations beyond baseline and SG_full. Comparative claims against Copilot will reference published benchmarks, not live runs.
- **Customer-runnable evaluation kit**: v1 produces reports from Sourcegraph-run benchmarks. A self-serve kit for prospects is a future phase.
- **LLM judge integration**: The dashboard has judge assessment infrastructure; this PRD does not add new judge evaluation, only metric computation from existing data.
- **Removing or modifying existing scripts**: All new scripts are additive. Existing scripts (aggregate_status.py, cost_report.py, etc.) remain unchanged except for config filter updates.
- **Benchmark task removal**: No existing tasks are dropped. New tasks are added alongside existing ones.
- **SG_base reruns**: Historical SG_base data is preserved but no new SG_base runs are executed.

## Technical Considerations

### Existing Infrastructure to Reuse
- `aggregate_status.py`: task scanning, status classification, gap analysis — reuse `scan_all_tasks()`
- `cost_report.py`: cost extraction from task_metrics.json — reuse `extract_cost_data()`
- `audit_traces.py`: transcript scanning, MCP tool detection — reuse `scan_transcript()`, `scan_trajectory()`
- `status_fingerprints.py`: error classification — extend for failure taxonomy
- `compare_configs.py`: divergence analysis — reuse for context attribution
- `generate_eval_report.py`: report structure — model enterprise report after this
- `extract_analysis_metrics.py`: dimension-based analysis — reuse grouping logic

### Data Sources
- `runs/official/*/result.json` — task outcomes, rewards, tokens
- `runs/official/*/agent/claude-code.txt` — JSONL transcript (tool calls, timing)
- `runs/official/*/agent/trajectory.json` — structured tool usage
- `runs/official/*/agent/setup/stdout.txt` — Docker/build logs
- `configs/selected_benchmark_tasks.json` — task metadata, difficulty, MCP scores
- `runs/official/MANIFEST.json` — canonical run tracking

### Dashboard Integration
- Dashboard repo: `https://github.com/sjarmak/CodeContextBench_Dashboard`
- Dashboard consumes: `evaluation_report.json`, `enterprise_metrics_schema.json`, SQLite database
- New scripts output JSON files that the dashboard's ingestion pipeline can consume
- New dedicated schemas replace existing `enterprise_metrics_schema.json` (clean break, not additive)

### Dependencies
- Python 3.10+ (existing)
- No new external dependencies for metric computation scripts
- `scipy` for statistical tests in reliability analysis (already available or pip-installable)
- JSON Schema validation via `jsonschema` library

### Performance
- All scripts process on-disk data (no API calls except governance evaluator reading trajectories)
- Expected runtime: <60s for full report generation across ~500 tasks
- No database writes — all output is filesystem-based JSON/markdown

## Success Metrics

- Benchmark can answer all 5 validation questions:
  1. "Does centralized context materially improve agent reliability?" → Yes/No with CI from reliability_analysis
  2. "Does it reduce engineering navigation time?" → Quantified hours from workflow_metrics
  3. "Does it enable AI under enterprise security constraints?" → Compliance rate from governance_evaluator
  4. "Does it improve productivity relative to cost?" → ROI metrics from economic_analysis
  5. "Is performance consistent across organizational complexity?" → Consistency index from reliability_analysis
- Executive summary is under 500 words and contains 5+ quantified metrics
- All JSON outputs validate against schemas
- Enterprise report generation completes in <2 minutes from cold start
- At least 3 governance tasks pass compliance verification in SG_full config
- Failure analysis correctly classifies >80% of failed tasks (manual spot-check of 20 tasks)

## Phase 10: ICP-Aligned Benchmark Profiles (COMPLETED)

#### US-ICP-001: Build ICP profile selector module
**Description:** As a marketing/sales team member, I want benchmark results filtered and framed for specific customer profiles so that I can tailor conversations to the prospect's organizational context.

**Status:** COMPLETED — `scripts/icp_profiles.py` with 5 profiles, `docs/ICP_PROFILES.md`, `schemas/icp_profile_schema.json`

#### US-ICP-002: Integrate ICP profile reports into enterprise report generator
**Description:** As a benchmark operator, I want `generate_enterprise_report.py` to support `--profile` flag so that I can produce customer-specific reports in one command.

**Status:** COMPLETED — `--profile` flag added, generates PROFILE_REPORT_{ID}.md with profile-filtered metrics and data-driven headlines.

### ICP Profile Architecture

The benchmark supports 5 enterprise customer profiles:

| Profile | Label | Key Suites | Report |
|---------|-------|-----------|--------|
| legacy_modernization | Sleeping Giants | LoCoBench, LargeRepo, CrossRepo, DependEval | Modernization Readiness Report |
| platform_saas | Velocity Leaders | SWE-bench Pro, DIBench, K8s Docs, TAC, PyTorch | Developer Velocity Report |
| security_compliance | Governance First | Governance, CrossRepo | Governance & Risk Report |
| ai_forward | Agent Builders | SWE-Pro, PyTorch, LoCoBench, LargeRepo, CrossRepo, SWE-Perf | Agent Reliability Report |
| platform_consolidation | Consolidators | CrossRepo, LargeRepo, DependEval, DIBench | Architecture Visibility Report |

Each profile maps to marketing campaigns:
- 100 Use Cases → Platform SaaS
- Sleeping Giants → Legacy Modernization
- Security/Oversight → Security & Compliance
- AI Rollout → AI-Forward
- Platform Consolidation → Platform Consolidation

---

## Resolved Questions

1. **Time multiplier calibration**: Use the most credible enterprise developer productivity research available — prioritize sources that resonate with pragmatic early adopters in large regulated enterprises. Candidates: Google DORA State of DevOps reports, Microsoft Developer Velocity research, McKinsey developer productivity studies. Select whichever has the strongest methodology and enterprise credibility. All estimates must be clearly labeled as modeled projections.
2. **Governance task complexity**: Use whichever approach produces the most realistic and maintainable tasks. Recommendation: modify existing benchmark repos with added permission constraints where possible (leverages existing Dockerfiles and verification), create net-new repos only when no existing repo fits the governance scenario.
3. **Variance trial budget**: Approved. Using fixed subscription accounts so per-task compute cost is not a concern. Run the full 90-task variance trial plan.
4. **Dashboard schema evolution**: New dedicated schemas — clean break from existing `enterprise_metrics_schema.json`. Dashboard repo will be updated to consume the new schema.
5. **Regulatory framing**: Stay generic ("enterprise data boundaries", "compliance readiness", "audit trail completeness"). Do not reference specific frameworks (SOC 2, HIPAA, FedRAMP) — let enterprise buyers map to their own compliance context.
