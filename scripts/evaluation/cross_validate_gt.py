#!/usr/bin/env python3
"""Cross-validate curator-generated GT against pre-existing manual GT.

Scans benchmarks/ for tasks with both ground_truth_agent.json AND
(ground_truth.json or oracle_answer.json), then computes file-level
precision, recall, F1 and flags disagreements.

Usage:
    python3 scripts/cross_validate_gt.py
    python3 scripts/cross_validate_gt.py --threshold 0.6
    python3 scripts/cross_validate_gt.py --output report.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BENCHMARKS_DIR = REPO_ROOT / "benchmarks"

# Reuse _normalize from ir_metrics for path normalization
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from csb_metrics.ir_metrics import _normalize  # noqa: E402


def extract_file_set(gt_path: Path) -> set[str]:
    """Extract normalized file paths from a GT file."""
    data = json.loads(gt_path.read_text())
    if not isinstance(data, dict):
        return set()

    raw_files = data.get("files", [])
    if not isinstance(raw_files, list):
        return set()

    result = set()
    for entry in raw_files:
        if isinstance(entry, str):
            result.add(_normalize(entry))
        elif isinstance(entry, dict):
            path = entry.get("path", "")
            repo = entry.get("repo", "")
            # For cross-validation, normalize to path-only (strip repo)
            if path:
                result.add(_normalize(path))
        # skip other types
    return result


def compute_f1(reference: set[str], candidate: set[str]) -> dict:
    """Compute precision, recall, F1 between reference and candidate file sets."""
    if not reference and not candidate:
        return {"precision": 1.0, "recall": 1.0, "f1": 1.0}
    if not candidate:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0}
    if not reference:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0}

    tp = len(reference & candidate)
    precision = tp / len(candidate) if candidate else 0.0
    recall = tp / len(reference) if reference else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    return {"precision": precision, "recall": recall, "f1": f1}


def find_cross_validation_pairs() -> list[dict]:
    """Find tasks with both curator-generated and manual GT files."""
    pairs = []

    for suite_dir in sorted(BENCHMARKS_DIR.iterdir()):
        if not suite_dir.is_dir() or not suite_dir.name.startswith(("csb_", "ccb_")):
            continue

        for task_dir in sorted(suite_dir.iterdir()):
            if not task_dir.is_dir():
                continue

            tests_dir = task_dir / "tests"
            if not tests_dir.is_dir():
                continue

            # Find curator-generated GT
            curator_path = tests_dir / "ground_truth_agent.json"
            if not curator_path.exists():
                continue

            # Find manual GT (ground_truth.json or oracle_answer.json)
            manual_path = None
            for name in ["ground_truth.json", "oracle_answer.json"]:
                candidate = tests_dir / name
                if candidate.exists():
                    manual_path = candidate
                    break

            if manual_path is None:
                continue

            pairs.append({
                "suite": suite_dir.name,
                "task_id": task_dir.name,
                "manual_path": str(manual_path.relative_to(REPO_ROOT)),
                "curator_path": str(curator_path.relative_to(REPO_ROOT)),
            })

    return pairs


def cross_validate(pairs: list[dict], threshold: float) -> dict:
    """Run cross-validation on all pairs."""
    results = []
    flagged = []

    for pair in pairs:
        manual_files = extract_file_set(REPO_ROOT / pair["manual_path"])
        curator_files = extract_file_set(REPO_ROOT / pair["curator_path"])

        metrics = compute_f1(reference=manual_files, candidate=curator_files)

        extra_files = sorted(curator_files - manual_files)
        missing_files = sorted(manual_files - curator_files)

        entry = {
            "suite": pair["suite"],
            "task_id": pair["task_id"],
            "precision": round(metrics["precision"], 4),
            "recall": round(metrics["recall"], 4),
            "f1": round(metrics["f1"], 4),
            "n_manual": len(manual_files),
            "n_curator": len(curator_files),
            "n_overlap": len(manual_files & curator_files),
            "extra_files": extra_files,
            "missing_files": missing_files,
        }
        results.append(entry)

        if metrics["f1"] < threshold:
            flagged.append(entry)

    f1_values = [r["f1"] for r in results]
    mean_f1 = sum(f1_values) / len(f1_values) if f1_values else 0.0

    return {
        "total_cross_validated": len(results),
        "above_threshold": len(results) - len(flagged),
        "below_threshold": len(flagged),
        "mean_f1": round(mean_f1, 4),
        "threshold": threshold,
        "tasks": results,
        "flagged_tasks": [f["task_id"] for f in flagged],
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Cross-validate curator GT against manual GT"
    )
    parser.add_argument(
        "--threshold", "-t",
        type=float, default=0.5,
        help="F1 threshold for flagging disagreements (default: 0.5)",
    )
    parser.add_argument(
        "--output", "-o",
        help="Write JSON report to this path",
    )
    args = parser.parse_args()

    pairs = find_cross_validation_pairs()
    if not pairs:
        print("No tasks found with both curator and manual GT files.")
        return 0

    report = cross_validate(pairs, args.threshold)

    # Print summary
    print(f"Cross-validated: {report['total_cross_validated']} tasks")
    print(f"Above threshold (F1 >= {args.threshold}): {report['above_threshold']}")
    print(f"Below threshold (F1 < {args.threshold}): {report['below_threshold']}")
    print(f"Mean F1: {report['mean_f1']:.4f}")

    if report["flagged_tasks"]:
        print(f"\nFlagged for review ({len(report['flagged_tasks'])}):")
        for tid in report["flagged_tasks"]:
            task = next(t for t in report["tasks"] if t["task_id"] == tid)
            print(f"  {task['suite']}/{tid}: F1={task['f1']:.3f} "
                  f"(P={task['precision']:.3f} R={task['recall']:.3f})")

    if args.output:
        Path(args.output).write_text(json.dumps(report, indent=2) + "\n")
        print(f"\nReport written to {args.output}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
