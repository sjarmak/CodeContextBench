#!/usr/bin/env python3
"""Generate verifier-quality labels for all tasks using ABC audit output.

Reads the ABC audit JSON and the verifier quality scheme, then assigns each
task a classification: core_ready, conditional, or extension_only.

Output: configs/verifier_quality_labels.json
"""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCHEME_FILE = ROOT / "configs" / "verifier_quality_scheme.json"
OUTPUT_FILE = ROOT / "configs" / "verifier_quality_labels.json"
TASKS_FILE = ROOT / "configs" / "selected_benchmark_tasks.json"


def run_abc_audit() -> dict:
    result = subprocess.run(
        [sys.executable, "scripts/abc_audit.py", "--all", "--format", "json"],
        capture_output=True, text=True, cwd=ROOT,
    )
    if result.returncode != 0:
        print(f"ABC audit failed: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    return json.loads(result.stdout)


def classify_tasks(audit_data: dict) -> dict:
    """Classify each task based on suite-level and task-level audit signals."""
    tasks_data = json.loads(TASKS_FILE.read_text())["tasks"]
    task_to_suite = {t["task_id"].lower(): t["benchmark"] for t in tasks_data}
    all_task_ids = [t["task_id"] for t in tasks_data]

    # Build suite-level signal maps
    suite_signals = {}
    for report in audit_data["reports"]:
        suite = report["target"]
        signals = {}
        for r in report["results"]:
            if r["status"] in ("FAIL", "WARN"):
                signals[r["criterion_id"]] = {
                    "status": r["status"],
                    "details": r.get("details", {}),
                }
        suite_signals[suite] = signals

    # Extract per-task issues from O.e and T.9/T.10 details
    task_issues = {}  # task_id -> set of issue types
    for report in audit_data["reports"]:
        suite = report["target"]
        for r in report["results"]:
            details = r.get("details", {})
            issues = details.get("issues", [])
            for issue_str in issues:
                # Format: "task-id: description"
                if ": " in issue_str:
                    tid, desc = issue_str.split(": ", 1)
                    tid_lower = tid.strip().lower()
                    if tid_lower not in task_issues:
                        task_issues[tid_lower] = set()
                    if r["criterion_id"] == "T.10":
                        task_issues[tid_lower].add("fixed_tmp_paths")
                    elif r["criterion_id"] == "T.9":
                        if "existence" in desc.lower():
                            task_issues[tid_lower].add("existence_only")
                    elif r["criterion_id"] == "O.e":
                        if "only 1 assertion" in desc.lower():
                            task_issues[tid_lower].add("weak_assertion")

    # Also track suite-level R.4 missing oracle tasks
    for report in audit_data["reports"]:
        for r in report["results"]:
            if r["criterion_id"] == "R.4" and r["status"] == "WARN":
                missing = r.get("details", {}).get("missing", [])
                for tid in missing:
                    tid_lower = tid.strip().lower()
                    if tid_lower not in task_issues:
                        task_issues[tid_lower] = set()
                    task_issues[tid_lower].add("missing_oracle")

    # Classify each task
    labels = {}
    for task_id in all_task_ids:
        tid_lower = task_id.lower()
        issues = task_issues.get(tid_lower, set())

        if "fixed_tmp_paths" in issues:
            label = "extension_only"
            reason = "T.10: fixed /tmp paths in verifier"
        elif "existence_only" in issues and "weak_assertion" in issues:
            label = "extension_only"
            reason = "T.9+O.e: existence-only check with single assertion"
        elif "existence_only" in issues:
            label = "conditional"
            reason = "T.9: existence-only verifier check"
        elif "weak_assertion" in issues and "missing_oracle" in issues:
            label = "conditional"
            reason = "O.e+R.4: single assertion and missing oracle"
        elif "weak_assertion" in issues:
            label = "conditional"
            reason = "O.e: single assertion pattern"
        elif "missing_oracle" in issues:
            label = "conditional"
            reason = "R.4: missing oracle reference"
        else:
            label = "core_ready"
            reason = "No verifier quality issues detected"

        labels[task_id] = {
            "label": label,
            "reason": reason,
            "issues": sorted(issues) if issues else [],
        }

    return labels


def main():
    print("Running ABC audit...")
    audit_data = run_abc_audit()

    print("Classifying tasks...")
    labels = classify_tasks(audit_data)

    # Summary
    from collections import Counter
    dist = Counter(v["label"] for v in labels.values())
    print(f"Results: {dict(dist)}")

    output = {
        "schema_version": "1.0",
        "generated_by": "scripts/generate_verifier_labels.py",
        "total_tasks": len(labels),
        "summary": dict(dist),
        "labels": labels,
    }

    OUTPUT_FILE.write_text(json.dumps(output, indent=2) + "\n")
    print(f"Written to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
