# Script Index

Generated from `scripts/registry.json` by `scripts/maintenance/generate_script_index.py`.

## When To Read This
- You need to find the right script without opening many files.
- You need to identify maintained vs one-off scripts.

## Do Not Read First If
- You already know the workflow: use `docs/START_HERE_BY_TASK.md` first.
- You are working in a single script and only need that file.

## Usage
- Filter by category first, then open the specific script.
- Treat `one_off` scripts as historical unless explicitly needed.

## Core Operations

- `scripts/analysis/aggregate_status.py` - Scans run directories, classifies task status, and supports watch mode for active runs.
- `scripts/infra/check_infra.py` - Pre-run infrastructure readiness checker (tokens, Docker, disk, Harbor CLI).
- `scripts/maintenance/docs_consistency_check.py` - Validates documentation references, agent-guide sync/size budgets, and generated navigation artifacts.
- `scripts/maintenance/generate_eval_report.py` - Builds the deterministic aggregate evaluation report for completed runs.
- `scripts/maintenance/generate_manifest.py` - Rebuilds `MANIFEST.json` from on-disk run results.
- `scripts/maintenance/generate_script_index.py` - Generates `docs/ops/SCRIPT_INDEX.md` from `scripts/registry.json`.
- `scripts/maintenance/generate_script_registry.py` - Generates `scripts/registry.json`, the machine-readable script inventory used for agent navigation.
- `scripts/maintenance/refresh_agent_navigation.py` - One-command refresh/check for generated agent-navigation artifacts (guides + script registry/index).
- `scripts/maintenance/repo_health.py` - Repo health gate that runs required pre-commit/push checks (docs drift, selection file, task preflight).
- `scripts/analysis/status_fingerprints.py` - Known failure regex fingerprints used by status/triage tooling.
- `scripts/maintenance/sync_agent_guides.py` - Syncs generated root/local `AGENTS.md` and `CLAUDE.md` files from canonical sources in `docs/ops/`.
- `scripts/authoring/validate_task_run.py` - Post-run validation for a run/task output directory (`result.json`, scoring, anomalies).
- `scripts/authoring/validate_tasks_preflight.py` - Pre-flight task validator (static checks plus optional no-agent runtime smoke).

## Analysis & Comparison

- `scripts/analysis/analyze_harness_design.py` - Analysis/comparison script for analyze harness design.
- `scripts/analysis/analyze_mcp_unique_haiku.py` - Analysis/comparison script for analyze mcp unique haiku.
- `scripts/analysis/analyze_minimum_subset.py` - Analysis/comparison script for analyze minimum subset.
- `scripts/analysis/analyze_paired_cost_official_raw.py` - Analysis/comparison script for analyze paired cost official raw.
- `scripts/analysis/analyze_rq_power.py` - Analysis/comparison script for analyze rq power.
- `scripts/analysis/analyze_run_coverage.py` - Analysis/comparison script for analyze run coverage.
- `scripts/analysis/analyze_size_effects.py` - Analysis/comparison script for analyze size effects.
- `scripts/evaluation/audit_traces.py` - Analysis/comparison script for audit traces.
- `scripts/evaluation/compare_configs.py` - Compares benchmark outcomes across configs on matched task sets.
- `scripts/analysis/comprehensive_analysis.py` - Analysis/comparison script for comprehensive analysis.
- `scripts/evaluation/compute_retrieval_metrics.py` - Analysis/comparison script for compute retrieval metrics.
- `scripts/evaluation/cost_breakdown_analysis.py` - Analysis/comparison script for cost breakdown analysis.
- `scripts/evaluation/cost_report.py` - Aggregates token and cost metrics per run, suite, and config.
- `scripts/analysis/doe_variance_analysis.py` - Analysis/comparison script for doe variance analysis.
- `scripts/evaluation/ds_audit.py` - Analysis/comparison script for ds audit.
- `scripts/evaluation/economic_analysis.py` - Analysis/comparison script for economic analysis.
- `scripts/evaluation/failure_analysis.py` - Analysis/comparison script for failure analysis.
- `scripts/analysis/ir_analysis.py` - Runs retrieval/IR analysis over normalized events and evaluation outputs.
- `scripts/evaluation/mcp_audit.py` - Audits MCP tool usage patterns and reward/time deltas across runs.
- `scripts/infra/mcp_cost_analysis.py` - Analysis/comparison script for mcp cost analysis.
- `scripts/evaluation/normalize_retrieval_events.py` - Analysis/comparison script for normalize retrieval events.
- `scripts/evaluation/oracle_ir_analysis.py` - Analysis/comparison script for oracle ir analysis.
- `scripts/evaluation/oracle_retrieval_analysis.py` - Analysis/comparison script for oracle retrieval analysis.
- `scripts/evaluation/reliability_analysis.py` - Analysis/comparison script for reliability analysis.
- `scripts/evaluation/retrieval_eval_pipeline.py` - Analysis/comparison script for retrieval eval pipeline.
- `scripts/evaluation/retrieval_impact_analysis.py` - Analysis/comparison script for retrieval impact analysis.
- `scripts/analysis/suite_power_analysis.py` - Analysis/comparison script for suite power analysis.
- `scripts/analysis/variance_gap_analysis.py` - Analysis/comparison script for variance gap analysis.

## QA & Quality

- `scripts/evaluation/abc_audit.py` - QA/validation script for abc audit.
- `scripts/evaluation/abc_criteria.py` - QA/validation script for abc criteria.
- `scripts/evaluation/abc_score_task.py` - QA/validation script for abc score task.
- `scripts/evaluation/governance_evaluator.py` - QA/validation script for governance evaluator.
- `scripts/evaluation/official_integrity.py` - QA/validation script for official integrity.
- `scripts/evaluation/official_runs.py` - QA/validation script for official runs.
- `scripts/maintenance/quarantine_invalid_tasks.py` - QA/validation script for quarantine invalid tasks.
- `scripts/authoring/validate_artifact_golden.py` - QA/validation script for validate artifact golden.
- `scripts/authoring/validate_official_integrity.py` - QA/validation script for validate official integrity.
- `scripts/authoring/validate_org_task_instance.py` - QA/validation script for validate org task instance.

## Data Management

- `scripts/maintenance/archive_non_manifest_runs.py` - Data/run management script for archive non manifest runs.
- `scripts/maintenance/archive_run.py` - Data/run management script for archive run.
- `scripts/evaluation/consolidate_staging.py` - Data/run management script for consolidate staging.
- `scripts/evaluation/extract_task_metrics.py` - Data/run management script for extract task metrics.
- `scripts/infra/migrate_results.py` - Data/run management script for migrate results.
- `scripts/analysis/organize_staging_to_official.py` - Data/run management script for organize staging to official.
- `scripts/running/promote_run.py` - Promotes a staged run into the official results flow with integrity checks.
- `scripts/evaluation/reextract_all_metrics.py` - Data/run management script for reextract all metrics.
- `scripts/running/rerun_failed.py` - Generates targeted rerun commands for failed tasks (despite `rerun_` prefix, this is part of normal ops).
- `scripts/maintenance/sync_task_metadata.py` - Reconciles `task.toml` metadata with the canonical task selection registry (`--fix` to apply changes).

## Submission & Reporting

- `scripts/maintenance/generate_comprehensive_report.py` - Submission/reporting script for generate comprehensive report.
- `scripts/maintenance/generate_enterprise_report.py` - Submission/reporting script for generate enterprise report.
- `scripts/maintenance/generate_leaderboard.py` - Submission/reporting script for generate leaderboard.
- `scripts/maintenance/generate_retrieval_report.py` - Submission/reporting script for generate retrieval report.
- `scripts/evaluation/ingest_judge_results.py` - Submission/reporting script for ingest judge results.
- `scripts/evaluation/package_submission.py` - Submission/reporting script for package submission.
- `scripts/authoring/validate_submission.py` - Submission/reporting script for validate submission.

## Task Creation & Selection

- `scripts/running/curate_oracle.py` - Task creation/selection script for curate oracle.
- `scripts/evaluation/customize_mcp_skeletons.py` - Task creation/selection script for customize mcp skeletons.
- `scripts/maintenance/generate_csb_org_tasks.py` - Task creation/selection script for generate csb org tasks.
- `scripts/maintenance/generate_dependeval_tasks.py` - Task creation/selection script for generate dependeval tasks.
- `scripts/maintenance/generate_pytorch_expected_diffs.py` - Task creation/selection script for generate pytorch expected diffs.
- `scripts/infra/materialize_dependeval_repos.py` - Task creation/selection script for materialize dependeval repos.
- `scripts/infra/materialize_sdlc_suites.py` - Task creation/selection script for materialize sdlc suites.
- `scripts/authoring/mine_bug_tasks.py` - Task creation/selection script for mine bug tasks.
- `scripts/infra/register_new_org_tasks.py` - Task creation/selection script for register new org tasks.
- `scripts/infra/rename_tasks.py` - Task creation/selection script for rename tasks.
- `scripts/authoring/select_benchmark_tasks.py` - Task creation/selection script for select benchmark tasks.
- `scripts/authoring/select_dependeval_tasks.py` - Task creation/selection script for select dependeval tasks.
- `scripts/authoring/select_subset.py` - Selects a representative task subset stratified by suite effect-size bucket, language, difficulty, and codebase size. Outputs JSON selection file and plain-text task list.

## Infra & Mirrors

- `scripts/infra/build_canonical_manifest.py` - Infrastructure or mirror management script for build canonical manifest.
- `scripts/infra/build_conversation_db.py` - Infrastructure or mirror management script for build conversation db.
- `scripts/infra/build_core_manifest.py` - Infrastructure or mirror management script for build core manifest.
- `scripts/infra/build_daytona_registry.py` - Infrastructure or mirror management script for build daytona registry.
- `scripts/infra/build_linux_base_images.sh` - Infrastructure or mirror management script for build linux base images.
- `scripts/infra/build_repo_manifests.py` - Infrastructure or mirror management script for build repo manifests.
- `scripts/infra/build_unified_manifest.py` - Infrastructure or mirror management script for build unified manifest.
- `scripts/infra/create_mcp_expansion_mirrors.sh` - Infrastructure or mirror management script for create mcp expansion mirrors.
- `scripts/infra/create_missing_mcp_mirrors.sh` - Infrastructure or mirror management script for create missing mcp mirrors.
- `scripts/infra/create_scip_branches.sh` - Infrastructure or mirror management script for create scip branches.
- `scripts/infra/create_sg_benchmark_repos.sh` - Infrastructure or mirror management script for create sg benchmark repos.
- `scripts/infra/create_sg_mirrors.py` - Infrastructure or mirror management script for create sg mirrors.
- `scripts/infra/create_sg_tac_repos.sh` - Infrastructure or mirror management script for create sg tac repos.
- `scripts/infra/headless_login.py` - Infrastructure or mirror management script for headless login.
- `scripts/infra/inject_sg_repo_env.py` - Infrastructure or mirror management script for inject sg repo env.
- `scripts/running/monitor_and_queue.sh` - Infrastructure or mirror management script for monitor and queue.
- `scripts/infra/prebuild_images.sh` - Infrastructure or mirror management script for prebuild images.
- `scripts/infra/prebuild_with_credentials.sh` - Infrastructure or mirror management script for prebuild with credentials.
- `scripts/running/stop_task.sh` - Infrastructure or mirror management script for stop task.
- `scripts/infra/swap_default_branch.sh` - Infrastructure or mirror management script for swap default branch.
- `scripts/maintenance/sync_oracle_files.py` - Infrastructure or mirror management script for sync oracle files.
- `scripts/maintenance/sync_pytorch_verifiers.sh` - Infrastructure or mirror management script for sync pytorch verifiers.
- `scripts/maintenance/update_gt_registry.py` - Infrastructure or mirror management script for update gt registry.
- `scripts/maintenance/update_loc_from_cloc.py` - Infrastructure or mirror management script for update loc from cloc.
- `scripts/infra/update_sg_only_mirrors.py` - Infrastructure or mirror management script for update sg only mirrors.

## Library / Helpers

- `scripts/evaluation/answer_json_verifier_lib.sh` - Helper library/wrapper used by other scripts (answer json verifier lib).
- `scripts/evaluation/artifact_verifier_lib.sh` - Helper library/wrapper used by other scripts (artifact verifier lib).
- `scripts/maintenance/config_utils.py` - Helper library/wrapper used by other scripts (config utils).
- `scripts/evaluation/eval_matrix.py` - Helper library/wrapper used by other scripts (eval matrix).
- `scripts/evaluation/sgonly_verifier_wrapper.sh` - Helper library/wrapper used by other scripts (sgonly verifier wrapper).
- `scripts/evaluation/workflow_metrics.py` - Helper library/wrapper used by other scripts (workflow metrics).
- `scripts/analysis/workflow_taxonomy.py` - Helper library/wrapper used by other scripts (workflow taxonomy).

## Validation

- `scripts/authoring/validate_core_manifest.py` - Validation script for validate core manifest.
- `scripts/authoring/validate_enterprise_readiness.py` - Validation script for validate enterprise readiness.
- `scripts/authoring/validate_on_contextbench.py` - Validation script for validate on contextbench.

## Generation

- `scripts/maintenance/generate_artifact_dockerfiles.py` - Generation script for generate artifact dockerfiles.
- `scripts/maintenance/generate_artifact_only_dockerfiles.py` - Generation script for generate artifact only dockerfiles.
- `scripts/maintenance/generate_coverage_gap_configs.py` - Generation script for generate coverage gap configs.
- `scripts/maintenance/generate_csb_selection.py` - Generation script for generate csb selection.
- `scripts/maintenance/generate_instruction_mcp.py` - Generation script for generate instruction mcp.
- `scripts/evaluation/generate_promoted_verifiers.py` - Generation script for generate promoted verifiers.
- `scripts/maintenance/generate_repoqa_largerepo_tasks.py` - Generation script for generate repoqa largerepo tasks.
- `scripts/maintenance/generate_sgonly_dockerfiles.py` - Generation script for generate sgonly dockerfiles.
- `scripts/maintenance/generate_start_here_by_task.py` - Generation script for generate start here by task.
- `scripts/maintenance/generate_task_specs_from_gt.py` - Generation script for generate task specs from gt.
- `scripts/evaluation/generate_verifier_labels.py` - Generation script for generate verifier labels.

## Migration

- `scripts/infra/migrate_dockerfiles_clone_as_claude.py` - Migration script for migrate dockerfiles clone as claude.
- `scripts/infra/migrate_dockerfiles_to_mirrors.py` - Migration script for migrate dockerfiles to mirrors.
- `scripts/infra/migrate_sweap_to_ghcr.py` - Migration script for migrate sweap to ghcr.
- `scripts/infra/migrate_to_sg_evals.sh` - Migration script for migrate to sg evals.
- `scripts/infra/migrate_to_sg_evals_batch2.sh` - Migration script for migrate to sg evals batch2.
- `scripts/evaluation/migrate_to_verifier_lib.py` - Migration script for migrate to verifier lib.
- `scripts/infra/migrate_validation_result_sidecar.py` - Migration script for migrate validation result sidecar.

## Misc

- `scripts/csb_metrics/__init__.py` - Utility script for   init  .
- `scripts/csb_metrics/judge/__init__.py` - Utility script for   init  .
- `scripts/infra/account_health.py` - Utility script for account health.
- `scripts/evaluation/add_compile_gates.py` - Utility script for add compile gates.
- `scripts/evaluation/add_verification_metadata.py` - Utility script for add verification metadata.
- `scripts/csb_metrics/judge/agreement.py` - Utility script for agreement.
- `scripts/evaluation/apply_verifier_fixes.py` - Utility script for apply verifier fixes.
- `scripts/evaluation/assign_oracle_confidence.py` - Utility script for assign oracle confidence.
- `scripts/evaluation/audit_canonical_evaluation_contract.py` - Utility script for audit canonical evaluation contract.
- `scripts/evaluation/audit_gt_coverage.py` - Utility script for audit gt coverage.
- `scripts/evaluation/audit_official_scores.py` - Utility script for audit official scores.
- `scripts/evaluation/audit_unpinned_repos.py` - Utility script for audit unpinned repos.
- `scripts/evaluation/audit_v2_report_data.py` - Utility script for audit v2 report data.
- `scripts/csb_metrics/judge/backends.py` - Utility script for backends.
- `scripts/evaluation/backfill_instruction_artifacts.py` [one_off] - Historical one-off script: backfill instruction artifacts.
- `scripts/evaluation/backfill_reviewers.py` [one_off] - Historical one-off script: backfill reviewers.
- `scripts/evaluation/backfill_size_metadata.py` [one_off] - Historical one-off script: backfill size metadata.
- `scripts/evaluation/backfill_triage_from_manifest.py` [one_off] - Historical one-off script: backfill triage from manifest.
- `scripts/analysis/browse_results.py` - Utility script for browse results.
- `scripts/evaluation/canary_empty_submission.py` - Utility script for canary empty submission.
- `scripts/maintenance/check_harness_readiness.py` - Utility script for check harness readiness.
- `scripts/maintenance/collect_repo_cloc.py` - Utility script for collect repo cloc.
- `scripts/evaluation/compare_contextbench_results.py` - Utility script for compare contextbench results.
- `scripts/evaluation/compare_old_new_ground_truth.py` - Utility script for compare old new ground truth.
- `scripts/evaluation/compute_analysis_ir_metrics.py` - Utility script for compute analysis ir metrics.
- `scripts/analysis/compute_bootstrap_cis.py` - Utility script for compute bootstrap cis.
- `scripts/running/context_retrieval_agent.py` - Utility script for context retrieval agent.
- `scripts/running/control_plane.py` - Utility script for control plane.
- `scripts/running/convert_harbor_to_contextbench.py` - Utility script for convert harbor to contextbench.
- `scripts/csb_metrics/coverage_audit.py` - Utility script for coverage audit.
- `scripts/evaluation/coverage_gaps.py` - Utility script for coverage gaps.
- `scripts/analysis/coverage_report.py` - Utility script for coverage report.
- `scripts/evaluation/cross_validate_gt.py` - Utility script for cross validate gt.
- `scripts/evaluation/cross_validate_oracles.py` - Utility script for cross validate oracles.
- `scripts/infra/daytona_cost_guard.py` - Utility script for daytona cost guard.
- `scripts/running/daytona_curator_runner.py` - Utility script for daytona curator runner.
- `scripts/running/daytona_poc_runner.py` - Utility script for daytona poc runner.
- `scripts/running/daytona_runner.py` - Utility script for daytona runner.
- `scripts/analysis/dependeval_eval_dr.py` - Utility script for dependeval eval dr.
- `scripts/analysis/dependeval_eval_me.py` - Utility script for dependeval eval me.
- `scripts/analysis/derive_n_repos.py` - Utility script for derive n repos.
- `scripts/csb_metrics/discovery.py` - Utility script for discovery.
- `scripts/infra/distribute_shared_libs.py` - Utility script for distribute shared libs.
- `scripts/analysis/docgen_quality_sweep.py` - Utility script for docgen quality sweep.
- `scripts/analysis/doe_power_curves.py` - Utility script for doe power curves.
- `scripts/analysis/doe_select_tasks.py` - Utility script for doe select tasks.
- `scripts/evaluation/ds_hybrid_retrieval.py` - Utility script for ds hybrid retrieval.
- `scripts/evaluation/ds_wrapper.sh` - Utility script for ds wrapper.
- `scripts/evaluation/dual_score_lib.sh` - Utility script for dual score lib.
- `scripts/csb_metrics/judge/engine.py` - Utility script for engine.
- `scripts/analysis/export_conversation_blog_assets.py` - Utility script for export conversation blog assets.
- `scripts/analysis/export_engineering_diary_assets.py` - Utility script for export engineering diary assets.
- `scripts/analysis/export_official_results.py` - Utility script for export official results.
- `scripts/evaluation/extract_analysis_metrics.py` - Utility script for extract analysis metrics.
- `scripts/analysis/extract_build_diary.py` - Utility script for extract build diary.
- `scripts/analysis/extract_build_narrative.py` - Utility script for extract build narrative.
- `scripts/analysis/extract_v2_report_data.py` - Utility script for extract v2 report data.
- `scripts/csb_metrics/extractors.py` - Utility script for extractors.
- `scripts/analysis/find_mcp_distracted.py` - Utility script for find mcp distracted.
- `scripts/infra/fix_h3_tokens.py` [one_off] - Historical one-off script: fix h3 tokens.
- `scripts/infra/fix_memory_mb.py` [one_off] - Historical one-off script: fix memory mb.
- `scripts/infra/fix_workspace_perms.py` [one_off] - Historical one-off script: fix workspace perms.
- `scripts/csb_metrics/ground_truth.py` - Utility script for ground truth.
- `scripts/csb_metrics/ground_truth_registry.py` - Utility script for ground truth registry.
- `scripts/evaluation/handoff_monitor_scrollend.sh` - Utility script for handoff monitor scrollend.
- `scripts/evaluation/hybrid_retrieval_pipeline.py` - Utility script for hybrid retrieval pipeline.
- `scripts/infra/hydrate_task_specs.py` - Utility script for hydrate task specs.
- `scripts/evaluation/icp_profiles.py` - Utility script for icp profiles.
- `scripts/evaluation/integrate_answer_json_wave1.py` - Utility script for integrate answer json wave1.
- `scripts/evaluation/integrate_answer_json_wave2.py` - Utility script for integrate answer json wave2.
- `scripts/evaluation/integrate_answer_json_wave3.py` - Utility script for integrate answer json wave3.
- `scripts/evaluation/integrate_dual_score.py` - Utility script for integrate dual score.
- `scripts/csb_metrics/ir_metrics.py` - Utility script for ir metrics.
- `scripts/csb_metrics/judge_context.py` - Utility script for judge context.
- `scripts/evaluation/judge_demo.py` - Utility script for judge demo.
- `scripts/running/launch_sonnet46_benchmark.sh` - Utility script for launch sonnet46 benchmark.
- `scripts/analysis/list_gemini_models.py` - Utility script for list gemini models.
- `scripts/infra/mirror_largerepo_expansion.sh` - Utility script for mirror largerepo expansion.
- `scripts/csb_metrics/judge/models.py` - Utility script for models.
- `scripts/csb_metrics/models.py` - Utility script for models.
- `scripts/csb_metrics/judge/oracle.py` - Utility script for oracle.
- `scripts/csb_metrics/oracle_checks.py` - Utility script for oracle checks.
- `scripts/evaluation/oracle_drift_check.py` - Utility script for oracle drift check.
- `scripts/analysis/organize_official_by_model.py` - Utility script for organize official by model.
- `scripts/analysis/plan_variance_runs.py` - Utility script for plan variance runs.
- `scripts/analysis/plot_build_diary.py` - Utility script for plot build diary.
- `scripts/analysis/plot_build_diary_supplementary.py` - Utility script for plot build diary supplementary.
- `scripts/analysis/plot_build_narrative.py` - Utility script for plot build narrative.
- `scripts/analysis/plot_conversation_blog_svgs.py` - Utility script for plot conversation blog svgs.
- `scripts/running/prepare_analysis_runs.py` - Utility script for prepare analysis runs.
- `scripts/running/promote_agent_oracles.py` - Utility script for promote agent oracles.
- `scripts/running/promote_atomic.py` - Utility script for promote atomic.
- `scripts/running/promote_blocked.py` - Utility script for promote blocked.
- `scripts/evaluation/promoted_verifier.py` - Utility script for promoted verifier.
- `scripts/evaluation/prompt_hygiene.py` - Utility script for prompt hygiene.
- `scripts/csb_metrics/judge/prompts.py` - Utility script for prompts.
- `scripts/infra/push_base_images_ghcr.sh` - Utility script for push base images ghcr.
- `scripts/infra/regenerate_artifact_dockerfiles.py` - Utility script for regenerate artifact dockerfiles.
- `scripts/infra/rehost_sweap_images.py` - Utility script for rehost sweap images.
- `scripts/infra/remirror_org_repos.sh` - Utility script for remirror org repos.
- `scripts/infra/rename_project.py` - Utility script for rename project.
- `scripts/maintenance/repair_h3_trajectories.py` [one_off] - Historical one-off script: repair h3 trajectories.
- `scripts/csb_metrics/report_formatter.py` - Utility script for report formatter.
- `scripts/running/rerun_crossrepo_2tasks.sh` [one_off] - Historical one-off script: rerun crossrepo 2tasks.
- `scripts/running/rerun_crossrepo_all4.sh` [one_off] - Historical one-off script: rerun crossrepo all4.
- `scripts/running/rerun_crossrepo_fixed.sh` [one_off] - Historical one-off script: rerun crossrepo fixed.
- `scripts/running/rerun_errored_tasks.sh` [one_off] - Historical one-off script: rerun errored tasks.
- `scripts/running/rerun_fixed_tasks.sh` [one_off] - Historical one-off script: rerun fixed tasks.
- `scripts/running/rerun_zero_mcp_tasks.sh` [one_off] - Historical one-off script: rerun zero mcp tasks.
- `scripts/evaluation/rescore_difficulty.py` - Utility script for rescore difficulty.
- `scripts/csb_metrics/result_parser.py` - Utility script for result parser.
- `scripts/csb_metrics/retrieval.py` - Utility script for retrieval.
- `scripts/evaluation/run_judge.py` - Utility script for run judge.
- `scripts/running/run_missing_oracles.sh` - Utility script for run missing oracles.
- `scripts/csb_metrics/run_promotion.py` - Utility script for run promotion.
- `scripts/running/run_scaling_gap_oracles.sh` - Utility script for run scaling gap oracles.
- `scripts/csb_metrics/run_scanner.py` - Utility script for run scanner.
- `scripts/running/run_sg_local.sh` - Utility script for run sg local.
- `scripts/evaluation/run_sg_validation.py` - Utility script for run sg validation.
- `scripts/maintenance/sanitize_secrets.py` - Utility script for sanitize secrets.
- `scripts/authoring/scaffold_contextbench_tasks.py` - Utility script for scaffold contextbench tasks.
- `scripts/authoring/scaffold_csb_unified.py` - Utility script for scaffold csb unified.
- `scripts/authoring/scaffold_feature_tasks.py` - Utility script for scaffold feature tasks.
- `scripts/authoring/scaffold_refactor_tasks.py` - Utility script for scaffold refactor tasks.
- `scripts/authoring/scaffold_scaling_gap_sdlc_tasks.py` - Utility script for scaffold scaling gap sdlc tasks.
- `scripts/authoring/scaffold_swebench_pro_tasks.py` - Utility script for scaffold swebench pro tasks.
- `scripts/authoring/scaffold_task_expansion_wave1.py` - Utility script for scaffold task expansion wave1.
- `scripts/analysis/scan_swebench_errors.py` - Utility script for scan swebench errors.
- `scripts/analysis/sdlc_anomaly_scan.py` - Utility script for sdlc anomaly scan.
- `scripts/analysis/search_strategy_correlation.py` - Utility script for search strategy correlation.
- `scripts/authoring/select_contextbench_pilot.py` - Utility script for select contextbench pilot.
- `scripts/evaluation/smoke_artifact_verifier.py` - Utility script for smoke artifact verifier.
- `scripts/evaluation/smoke_test_tasks.py` - Utility script for smoke test tasks.
- `scripts/authoring/split_edit_reference_files.py` - Utility script for split edit reference files.
- `scripts/csb_metrics/statistics.py` - Utility script for statistics.
- `scripts/csb_metrics/task_selection.py` - Utility script for task selection.
- `scripts/analysis/token_cost_quality.py` - Utility script for token cost quality.
- `scripts/csb_metrics/trace_quality.py` - Utility script for trace quality.
- `scripts/evaluation/trace_quality_pipeline.py` - Utility script for trace quality pipeline.
- `scripts/csb_metrics/transcript_paths.py` - Utility script for transcript paths.
- `scripts/evaluation/triage_run.py` - Utility script for triage run.
- `scripts/evaluation/verify_oracle_fail2pass.py` - Utility script for verify oracle fail2pass.
- `scripts/evaluation/verify_retrieval_eval_smoke.py` - Utility script for verify retrieval eval smoke.

## Regeneration
```bash
python3 scripts/maintenance/generate_script_registry.py
python3 scripts/maintenance/generate_script_index.py
```
