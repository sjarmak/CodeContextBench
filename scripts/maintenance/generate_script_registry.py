#!/usr/bin/env python3
"""Generate a machine-readable registry for scripts/ to aid agent navigation."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS_DIR = ROOT / "scripts"
REGISTRY_PATH = SCRIPTS_DIR / "registry.json"
OVERRIDES_PATH = SCRIPTS_DIR / "registry_overrides.json"

ONE_OFF_PREFIXES = ("rerun_", "backfill_", "fix_", "repair_")

CATEGORY_HINTS = {
    "core_operations": {
        "check_infra.py",
        "validate_tasks_preflight.py",
        "aggregate_status.py",
        "validate_task_run.py",
        "status_fingerprints.py",
        "generate_eval_report.py",
        "generate_manifest.py",
        "repo_health.py",
        "docs_consistency_check.py",
    },
    "analysis_comparison": {
        "compare_configs.py",
        "mcp_audit.py",
        "ir_analysis.py",
        "cost_report.py",
        "cost_breakdown_analysis.py",
        "failure_analysis.py",
        "reliability_analysis.py",
        "audit_traces.py",
        "ds_audit.py",
        "retrieval_eval_pipeline.py",
        "compute_retrieval_metrics.py",
        "normalize_retrieval_events.py",
    },
    "qa_quality": {
        "abc_audit.py",
        "abc_score_task.py",
        "abc_criteria.py",
        "validate_official_integrity.py",
        "quarantine_invalid_tasks.py",
        "validate_org_task_instance.py",
        "validate_artifact_golden.py",
    },
    "data_management": {
        "sync_task_metadata.py",
        "archive_run.py",
        "archive_non_manifest_runs.py",
        "promote_run.py",
        "extract_task_metrics.py",
        "reextract_all_metrics.py",
        "rerun_failed.py",
        "migrate_results.py",
        "consolidate_staging.py",
        "organize_staging_to_official.py",
    },
    "submission_reporting": {
        "validate_submission.py",
        "package_submission.py",
        "generate_leaderboard.py",
        "generate_comprehensive_report.py",
        "ingest_judge_results.py",
        "generate_enterprise_report.py",
        "generate_retrieval_report.py",
    },
    "task_creation_selection": {
        "select_benchmark_tasks.py",
        "mine_bug_tasks.py",
        "generate_pytorch_expected_diffs.py",
        "select_dependeval_tasks.py",
        "generate_dependeval_tasks.py",
        "generate_csb_org_tasks.py",
        "register_new_org_tasks.py",
        "materialize_dependeval_repos.py",
        "materialize_sdlc_suites.py",
        "curate_oracle.py",
        "customize_mcp_skeletons.py",
        "rename_tasks.py",
        "select_subset.py",
    },
}


def detect_status(name: str) -> str:
    if name.startswith(ONE_OFF_PREFIXES):
        return "one_off"
    return "maintained"


def detect_category(name: str) -> str:
    for category, exacts in CATEGORY_HINTS.items():
        if name in exacts:
            return category

    if name.endswith("_verifier_lib.sh") or name in {
        "answer_json_verifier_lib.sh",
        "artifact_verifier_lib.sh",
        "sgonly_verifier_wrapper.sh",
        "config_utils.py",
        "eval_matrix.py",
        "workflow_metrics.py",
        "workflow_taxonomy.py",
    }:
        return "library_helpers"

    if name.startswith(("create_", "update_", "inject_", "prebuild_", "build_", "swap_", "sync_")):
        return "infra_mirrors"
    if name in {"headless_login.py", "monitor_and_queue.sh", "stop_task.sh"}:
        return "infra_mirrors"

    if name.startswith("generate_"):
        return "generation"
    if name.startswith("validate_"):
        return "validation"
    if name.startswith("analyze_") or name.endswith("_analysis.py"):
        return "analysis_comparison"
    if name.startswith("migrate_"):
        return "migration"
    if name.startswith("official_") or name.startswith("governance_"):
        return "qa_quality"

    return "misc"


def summarize(name: str, category: str, status: str) -> str:
    stem = name.rsplit(".", 1)[0]
    human = stem.replace("_", " ")
    if status == "one_off":
        return f"Historical one-off script: {human}."
    if category == "core_operations":
        return f"Core operations script for {human}."
    if category == "analysis_comparison":
        return f"Analysis/comparison script for {human}."
    if category == "qa_quality":
        return f"QA/validation script for {human}."
    if category == "data_management":
        return f"Data/run management script for {human}."
    if category == "submission_reporting":
        return f"Submission/reporting script for {human}."
    if category == "task_creation_selection":
        return f"Task creation/selection script for {human}."
    if category == "infra_mirrors":
        return f"Infrastructure or mirror management script for {human}."
    if category == "library_helpers":
        return f"Helper library/wrapper used by other scripts ({human})."
    if category == "validation":
        return f"Validation script for {human}."
    if category == "generation":
        return f"Generation script for {human}."
    if category == "migration":
        return f"Migration script for {human}."
    return f"Utility script for {human}."


def load_overrides() -> dict[str, dict]:
    if not OVERRIDES_PATH.is_file():
        return {}
    payload = json.loads(OVERRIDES_PATH.read_text())
    entries = payload.get("overrides")
    if not isinstance(entries, list):
        raise SystemExit("scripts/registry_overrides.json must contain an 'overrides' list")
    overrides: dict[str, dict] = {}
    for item in entries:
        if not isinstance(item, dict) or not isinstance(item.get("name"), str):
            raise SystemExit("Invalid registry override entry (expected object with string 'name')")
        overrides[item["name"]] = item
    return overrides


def script_entries() -> list[dict]:
    overrides = load_overrides()
    entries: list[dict] = []
    # Scan root level and all subdirectories for scripts
    for path in sorted(SCRIPTS_DIR.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix not in {".py", ".sh"}:
            continue
        if path.name == "registry.json":
            continue
        if path.name.endswith(".pyc"):
            continue
        category = detect_category(path.name)
        status = detect_status(path.name)
        rel_path = path.relative_to(SCRIPTS_DIR)
        entry = {
            "name": path.name,
            "path": f"scripts/{rel_path}",
            "category": category,
            "status": status,
            "language": "python" if path.suffix == ".py" else "shell" if path.suffix == ".sh" else "other",
            "summary": summarize(path.name, category, status),
        }
        override = overrides.get(path.name)
        if override:
            for key in ("category", "status", "summary"):
                if key in override and isinstance(override[key], str):
                    entry[key] = override[key]
        entries.append(entry)
    return entries


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail if scripts/registry.json is stale")
    args = parser.parse_args()

    entries = script_entries()
    counts = Counter(entry["category"] for entry in entries)
    payload = {
        "version": 1,
        "schema_note": "Auto-generated script registry for agent navigation. Curate summaries/categories over time if needed.",
        "scripts": entries,
        "category_counts": dict(sorted(counts.items())),
    }
    rendered = json.dumps(payload, indent=2) + "\n"
    if args.check:
        if not REGISTRY_PATH.is_file() or REGISTRY_PATH.read_text() != rendered:
            print("Script registry: STALE")
            print("  - run: python3 scripts/generate_script_registry.py")
            return 1
        print(f"Script registry: OK ({len(entries)} scripts)")
        return 0

    REGISTRY_PATH.write_text(rendered)
    print(f"Wrote {REGISTRY_PATH.relative_to(ROOT)} ({len(entries)} scripts)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
