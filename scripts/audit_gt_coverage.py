#!/usr/bin/env python3
"""Audit ground truth coverage across all benchmark suites.

Scans benchmarks/csb_sdlc_*/ and benchmarks/csb_org_*/ for GT files,
categorizes each task, and reports coverage per suite.

Usage:
    python3 scripts/audit_gt_coverage.py
    python3 scripts/audit_gt_coverage.py --output manifest.json
    python3 scripts/audit_gt_coverage.py --threshold 0.90
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BENCHMARKS_DIR = REPO_ROOT / "benchmarks"

# GT file names in priority order (manual first, then curator-generated)
MANUAL_GT_FILES = ["ground_truth.json", "oracle_answer.json"]
CURATOR_GT_FILES = ["ground_truth_agent.json"]
ALL_GT_FILES = MANUAL_GT_FILES + CURATOR_GT_FILES


def classify_gt(tests_dir: Path) -> tuple[str, str, str | None]:
    """Classify a task's GT status and provenance.

    Returns (status, provenance, gt_file_path):
        status: 'valid' | 'invalid-schema' | 'empty' | 'missing'
        provenance: 'manual' | 'curator' | 'none'
        gt_file_path: relative path to the GT file used, or None
    """
    # Check manual files first (higher priority), then curator
    for gt_name in ALL_GT_FILES:
        gt_path = tests_dir / gt_name
        if not gt_path.exists():
            continue

        provenance = "manual" if gt_name in MANUAL_GT_FILES else "curator"
        rel_path = str(gt_path.relative_to(REPO_ROOT))

        try:
            data = json.loads(gt_path.read_text())
        except (json.JSONDecodeError, UnicodeDecodeError):
            return "invalid-schema", provenance, rel_path

        if not isinstance(data, dict):
            return "invalid-schema", provenance, rel_path

        # Check for 'files' key
        if "files" not in data:
            # Legacy onboard-search format uses 'function_id'
            if "function_id" in data:
                return "valid", provenance, rel_path
            return "invalid-schema", provenance, rel_path

        files = data["files"]
        if not isinstance(files, list) or len(files) == 0:
            return "empty", provenance, rel_path

        return "valid", provenance, rel_path

    return "missing", "none", None


def detect_dockerfile_type(task_dir: Path) -> str:
    """Detect which Dockerfile variants exist for a task."""
    env_dir = task_dir / "environment"
    if not env_dir.is_dir():
        return "none"

    types = []
    for name in sorted(env_dir.iterdir()):
        if name.name.startswith("Dockerfile"):
            suffix = name.name.replace("Dockerfile", "").lstrip(".")
            types.append(suffix if suffix else "default")
    return ",".join(types) if types else "none"


def scan_benchmarks() -> list[dict]:
    """Scan all benchmark suites and classify each task."""
    results = []

    for suite_dir in sorted(BENCHMARKS_DIR.iterdir()):
        if not suite_dir.is_dir():
            continue
        if not suite_dir.name.startswith(("csb_", "ccb_")):
            continue

        suite_name = suite_dir.name

        for task_dir in sorted(suite_dir.iterdir()):
            if not task_dir.is_dir():
                continue

            tests_dir = task_dir / "tests"
            if not tests_dir.is_dir():
                # Task without tests/ dir counts as missing
                status, provenance, gt_file = "missing", "none", None
            else:
                status, provenance, gt_file = classify_gt(tests_dir)

            results.append({
                "suite": suite_name,
                "task_id": task_dir.name,
                "status": status,
                "provenance": provenance,
                "gt_file": gt_file,
                "dockerfile_type": detect_dockerfile_type(task_dir),
            })

    return results


def print_summary_table(results: list[dict]) -> None:
    """Print per-suite summary table to stdout."""
    # Aggregate by suite
    suites: dict[str, dict] = {}
    for r in results:
        s = suites.setdefault(r["suite"], {
            "total": 0, "valid": 0, "invalid": 0, "empty": 0, "missing": 0
        })
        s["total"] += 1
        if r["status"] == "valid":
            s["valid"] += 1
        elif r["status"] == "invalid-schema":
            s["invalid"] += 1
        elif r["status"] == "empty":
            s["empty"] += 1
        elif r["status"] == "missing":
            s["missing"] += 1

    # Print table
    header = f"{'suite':<40} {'total':>5} {'valid':>5} {'invalid':>7} {'empty':>5} {'missing':>7} {'coverage%':>9}"
    print(header)
    print("-" * len(header))

    grand = {"total": 0, "valid": 0, "invalid": 0, "empty": 0, "missing": 0}
    for suite_name in sorted(suites):
        s = suites[suite_name]
        cov = (s["valid"] / s["total"] * 100) if s["total"] > 0 else 0
        print(f"{suite_name:<40} {s['total']:>5} {s['valid']:>5} {s['invalid']:>7} {s['empty']:>5} {s['missing']:>7} {cov:>8.1f}%")
        for k in grand:
            grand[k] += s[k]

    print("-" * len(header))
    cov = (grand["valid"] / grand["total"] * 100) if grand["total"] > 0 else 0
    print(f"{'TOTAL':<40} {grand['total']:>5} {grand['valid']:>5} {grand['invalid']:>7} {grand['empty']:>5} {grand['missing']:>7} {cov:>8.1f}%")


def build_manifest(results: list[dict]) -> list[dict]:
    """Build manifest of non-valid tasks."""
    return [
        {
            "suite": r["suite"],
            "task_id": r["task_id"],
            "status": r["status"],
            "dockerfile_type": r["dockerfile_type"],
        }
        for r in results
        if r["status"] != "valid"
    ]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit ground truth coverage across benchmark suites"
    )
    parser.add_argument(
        "--output", "-o",
        help="Write manifest JSON of non-valid tasks to this path",
    )
    parser.add_argument(
        "--threshold", "-t",
        type=float, default=0.75,
        help="Coverage threshold (0-1). Exit 1 if below (default: 0.75)",
    )
    args = parser.parse_args()

    results = scan_benchmarks()
    print_summary_table(results)

    total = len(results)
    valid = sum(1 for r in results if r["status"] == "valid")
    coverage = valid / total if total > 0 else 0

    print(f"\nOverall coverage: {valid}/{total} = {coverage:.1%}")
    print(f"Threshold: {args.threshold:.0%}")

    if args.output:
        manifest = build_manifest(results)
        Path(args.output).write_text(json.dumps(manifest, indent=2) + "\n")
        print(f"Manifest written to {args.output} ({len(manifest)} tasks)")

    if coverage < args.threshold:
        print("FAIL: Coverage below threshold")
        return 1

    print("PASS: Coverage meets threshold")
    return 0


if __name__ == "__main__":
    sys.exit(main())
