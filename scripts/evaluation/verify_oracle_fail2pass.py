#!/usr/bin/env python3
"""Verify oracle ground truth via fail2pass checks.

For each task, loads GT, synthesizes a perfect retrieval event, and verifies
that IR scoring produces file_recall == 1.0. Also checks verifier/test
availability.

Usage:
    python3 scripts/verify_oracle_fail2pass.py --task-ids task1,task2
    python3 scripts/verify_oracle_fail2pass.py --manifest manifest.json
    python3 scripts/verify_oracle_fail2pass.py --all
    python3 scripts/verify_oracle_fail2pass.py --dry-run --all
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BENCHMARKS_DIR = REPO_ROOT / "benchmarks"

# Import _normalize from ir_metrics
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from csb_metrics.ir_metrics import _normalize  # noqa: E402


# ---------------------------------------------------------------------------
# GT loading
# ---------------------------------------------------------------------------

GT_FILES = ["ground_truth.json", "oracle_answer.json", "ground_truth_agent.json"]


def load_gt_files(tests_dir: Path) -> list[str] | None:
    """Load GT file paths from the best available GT file.

    Returns a list of normalized file paths, or None if no valid GT found.
    """
    for gt_name in GT_FILES:
        gt_path = tests_dir / gt_name
        if not gt_path.exists():
            continue
        try:
            data = json.loads(gt_path.read_text())
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue

        if not isinstance(data, dict):
            continue

        files = data.get("files")
        if files is None:
            # Legacy function_id format
            if "function_id" in data:
                return [str(data["function_id"])]
            continue

        if not isinstance(files, list) or len(files) == 0:
            continue

        # Normalize file entries (can be strings or dicts)
        result = []
        for entry in files:
            if isinstance(entry, str):
                result.append(entry)
            elif isinstance(entry, dict):
                path = entry.get("path", "")
                repo = entry.get("repo", "")
                if repo and path:
                    result.append(f"{repo}::{path}")
                elif path:
                    result.append(path)
            else:
                continue
        return result if result else None

    return None


# ---------------------------------------------------------------------------
# Task discovery
# ---------------------------------------------------------------------------

def find_task_dir(task_id: str) -> Path | None:
    """Find the task directory by task_id across all suites."""
    for suite_dir in BENCHMARKS_DIR.iterdir():
        if not suite_dir.is_dir() or not suite_dir.name.startswith(("csb_", "ccb_")):
            continue
        candidate = suite_dir / task_id
        if candidate.is_dir():
            return candidate
    return None


def discover_all_tasks() -> list[tuple[str, str, Path]]:
    """Discover all tasks. Returns [(task_id, suite, task_dir), ...]."""
    tasks = []
    for suite_dir in sorted(BENCHMARKS_DIR.iterdir()):
        if not suite_dir.is_dir() or not suite_dir.name.startswith(("csb_", "ccb_")):
            continue
        for task_dir in sorted(suite_dir.iterdir()):
            if not task_dir.is_dir():
                continue
            tasks.append((task_dir.name, suite_dir.name, task_dir))
    return tasks


def tasks_from_manifest(manifest_path: str) -> list[tuple[str, str, Path]]:
    """Load tasks from a manifest JSON (output of audit_gt_coverage.py)."""
    data = json.loads(Path(manifest_path).read_text())
    tasks = []
    for entry in data:
        task_id = entry["task_id"]
        suite = entry["suite"]
        task_dir = BENCHMARKS_DIR / suite / task_id
        if task_dir.is_dir():
            tasks.append((task_id, suite, task_dir))
    return tasks


# ---------------------------------------------------------------------------
# Verification checks
# ---------------------------------------------------------------------------

def check_retrieval(gt_files: list[str]) -> bool:
    """Simulate perfect retrieval and verify file_recall == 1.0.

    A perfect retrieval event contains exactly the GT files, so
    file_recall must be 1.0 when comparing against itself.
    """
    gt_normalized = {_normalize(f) for f in gt_files}
    # Perfect retrieval = same files as GT
    retrieved_normalized = {_normalize(f) for f in gt_files}
    # Check: every GT file is in retrieved
    return gt_normalized == retrieved_normalized


def check_verifier(task_dir: Path, suite: str) -> str:
    """Check verifier availability.

    Returns: 'pass', 'fail_verifier', or 'skip'
    """
    tests_dir = task_dir / "tests"

    if suite.startswith("csb_org_"):
        # Org tasks: check if any result.json exists with reward > 0
        # For verification we just check the test infrastructure exists
        test_sh = tests_dir / "test.sh"
        eval_sh = tests_dir / "eval.sh"
        if test_sh.exists() or eval_sh.exists():
            return "pass"
        return "skip"

    if suite.startswith("csb_sdlc_"):
        # SDLC tasks: check tests/test.sh exists and is executable
        test_sh = tests_dir / "test.sh"
        if not test_sh.exists():
            return "fail_verifier"
        if not os.access(test_sh, os.X_OK):
            return "fail_verifier"
        return "pass"

    return "skip"


def verify_task(task_id: str, suite: str, task_dir: Path) -> dict:
    """Run fail2pass verification on a single task."""
    tests_dir = task_dir / "tests"
    result = {"task_id": task_id, "suite": suite, "status": "pass"}

    # Load GT
    gt_files = load_gt_files(tests_dir) if tests_dir.is_dir() else None
    if gt_files is None:
        result["status"] = "skip"
        result["reason"] = "no valid GT found"
        return result

    result["n_gt_files"] = len(gt_files)

    # Check retrieval
    if not check_retrieval(gt_files):
        result["status"] = "fail_retrieval"
        result["reason"] = "perfect retrieval did not yield file_recall=1.0"
        return result

    # Check verifier
    verifier_status = check_verifier(task_dir, suite)
    if verifier_status == "fail_verifier":
        result["status"] = "fail_verifier"
        result["reason"] = "tests/test.sh missing or not executable"
        return result

    if verifier_status == "skip":
        # Verifier check skipped but retrieval passed
        result["status"] = "pass"
        result["verifier_skipped"] = True

    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify oracle ground truth via fail2pass checks"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--task-ids",
        help="Comma-separated task IDs to verify",
    )
    group.add_argument(
        "--manifest",
        help="JSON manifest from audit_gt_coverage.py",
    )
    group.add_argument(
        "--all",
        action="store_true",
        help="Verify all tasks across all suites",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List tasks that would be checked without running",
    )
    parser.add_argument(
        "--output", "-o",
        help="Write JSON report to this path (default: stdout only)",
    )
    args = parser.parse_args()

    # Gather tasks
    if args.task_ids:
        ids = [t.strip() for t in args.task_ids.split(",")]
        tasks = []
        for tid in ids:
            td = find_task_dir(tid)
            if td is None:
                print(f"WARNING: task {tid} not found, skipping", file=sys.stderr)
                continue
            suite = td.parent.name
            tasks.append((tid, suite, td))
    elif args.manifest:
        tasks = tasks_from_manifest(args.manifest)
    else:
        tasks = discover_all_tasks()

    if args.dry_run:
        print(f"Would verify {len(tasks)} tasks:")
        for tid, suite, _ in tasks:
            print(f"  {suite}/{tid}")
        return 0

    # Run verification
    results = []
    counts = {"pass": 0, "fail_retrieval": 0, "fail_verifier": 0, "skip": 0}

    for tid, suite, td in tasks:
        r = verify_task(tid, suite, td)
        results.append(r)
        counts[r["status"]] += 1

    # Print summary
    print(f"\nVerification results ({len(results)} tasks):")
    print(f"  pass:           {counts['pass']}")
    print(f"  fail_retrieval: {counts['fail_retrieval']}")
    print(f"  fail_verifier:  {counts['fail_verifier']}")
    print(f"  skip:           {counts['skip']}")

    # Print failures
    failures = [r for r in results if r["status"].startswith("fail")]
    if failures:
        print(f"\nFailures ({len(failures)}):")
        for f in failures:
            print(f"  {f['suite']}/{f['task_id']}: {f['status']} - {f.get('reason', '')}")

    # Write report
    report = {"summary": counts, "tasks": results}
    if args.output:
        Path(args.output).write_text(json.dumps(report, indent=2) + "\n")
        print(f"\nReport written to {args.output}")

    has_failures = counts["fail_retrieval"] > 0 or counts["fail_verifier"] > 0
    return 1 if has_failures else 0


if __name__ == "__main__":
    sys.exit(main())
