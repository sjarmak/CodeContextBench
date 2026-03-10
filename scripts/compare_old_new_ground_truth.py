#!/usr/bin/env python3
"""Compare old (.bak) vs new (promoted) ground truth across all tasks.

Produces per-task and aggregate statistics on:
  - File count changes (old vs new)
  - File overlap (Jaccard, precision, recall treating old as "gold")
  - Files added by curator, files removed by curator
  - Schema differences

Usage:
    python3 scripts/compare_old_new_ground_truth.py
    python3 scripts/compare_old_new_ground_truth.py --output results/gt_comparison.json
    python3 scripts/compare_old_new_ground_truth.py --suite csb_sdlc_fix
"""

import argparse
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BENCHMARKS = ROOT / "benchmarks"


def normalize_file_path(p):
    """Normalize file paths for comparison (strip leading ./ and whitespace)."""
    if isinstance(p, dict):
        # Some old formats use {"repo": ..., "path": ...}
        return p.get("path", "").strip().lstrip("./")
    return str(p).strip().lstrip("./")


def extract_files(data):
    """Extract normalized file list from ground truth data."""
    if isinstance(data, list):
        # Some old GT files are plain lists of file paths/strings
        files = data
    else:
        files = data.get("files", [])
    return sorted(set(normalize_file_path(f) for f in files if f))


def compare_task(old_path, new_path, task_key):
    """Compare old and new ground truth for a single task."""
    try:
        old_data = json.loads(old_path.read_text())
        new_data = json.loads(new_path.read_text())
    except (json.JSONDecodeError, OSError) as e:
        return {"task": task_key, "error": str(e)}

    old_files = extract_files(old_data)
    new_files = extract_files(new_data)

    old_set = set(old_files)
    new_set = set(new_files)

    intersection = old_set & new_set
    added = new_set - old_set  # curator found, old didn't have
    removed = old_set - new_set  # old had, curator didn't include

    n_old = len(old_set)
    n_new = len(new_set)
    n_overlap = len(intersection)

    # Treat old as "reference" to compute precision/recall of new relative to old
    precision_vs_old = n_overlap / n_new if n_new > 0 else 0
    recall_vs_old = n_overlap / n_old if n_old > 0 else 0
    f1_vs_old = (2 * precision_vs_old * recall_vs_old / (precision_vs_old + recall_vs_old)
                 if (precision_vs_old + recall_vs_old) > 0 else 0)

    jaccard = n_overlap / len(old_set | new_set) if (old_set | new_set) else 1.0

    return {
        "task": task_key,
        "old_count": n_old,
        "new_count": n_new,
        "overlap": n_overlap,
        "added": len(added),
        "removed": len(removed),
        "jaccard": round(jaccard, 4),
        "precision_vs_old": round(precision_vs_old, 4),
        "recall_vs_old": round(recall_vs_old, 4),
        "f1_vs_old": round(f1_vs_old, 4),
        "added_files": sorted(added),
        "removed_files": sorted(removed),
        "old_keys": sorted(old_data.keys()) if isinstance(old_data, dict) else ["_list"],
        "new_keys": sorted(new_data.keys()) if isinstance(new_data, dict) else ["_list"],
        "delta_count": n_new - n_old,
    }


def main():
    parser = argparse.ArgumentParser(description="Compare old vs new ground truth")
    parser.add_argument("--suite", type=str, default="", help="Filter to specific suite")
    parser.add_argument("--output", type=str, default="", help="Write JSON report to file")
    parser.add_argument("--verbose", action="store_true", help="Show per-task details")
    args = parser.parse_args()

    results = []
    sdlc_results = []
    org_results = []

    for suite_dir in sorted(BENCHMARKS.iterdir()):
        if not suite_dir.is_dir():
            continue
        if not suite_dir.name.startswith(("csb_", "ccb_")):
            continue
        if args.suite and suite_dir.name != args.suite:
            continue

        is_org = suite_dir.name.startswith(("csb_org_", "ccb_mcp_"))

        for task_dir in sorted(suite_dir.iterdir()):
            if not task_dir.is_dir():
                continue
            tests = task_dir / "tests"
            if not tests.is_dir():
                continue

            if is_org:
                old_path = tests / "oracle_answer.json.bak"
                new_path = tests / "oracle_answer.json"
            else:
                old_path = tests / "ground_truth.json.bak"
                new_path = tests / "ground_truth.json"

            if not old_path.exists() or not new_path.exists():
                continue

            task_key = f"{suite_dir.name}/{task_dir.name}"
            result = compare_task(old_path, new_path, task_key)
            results.append(result)
            if is_org:
                org_results.append(result)
            else:
                sdlc_results.append(result)

    if not results:
        print("No .bak files found for comparison.")
        return 1

    # Filter out errors
    valid = [r for r in results if "error" not in r]
    valid_sdlc = [r for r in sdlc_results if "error" not in r]
    valid_org = [r for r in org_results if "error" not in r]

    def compute_aggregate(tasks, label):
        if not tasks:
            return {"label": label, "n": 0}
        old_counts = [t["old_count"] for t in tasks]
        new_counts = [t["new_count"] for t in tasks]
        jaccards = [t["jaccard"] for t in tasks]
        f1s = [t["f1_vs_old"] for t in tasks]
        deltas = [t["delta_count"] for t in tasks]
        added = [t["added"] for t in tasks]
        removed = [t["removed"] for t in tasks]

        # Categorize changes
        identical = sum(1 for t in tasks if t["jaccard"] == 1.0)
        high_overlap = sum(1 for t in tasks if 0.5 <= t["jaccard"] < 1.0)
        low_overlap = sum(1 for t in tasks if 0.0 < t["jaccard"] < 0.5)
        no_overlap = sum(1 for t in tasks if t["jaccard"] == 0.0)
        grew = sum(1 for t in tasks if t["delta_count"] > 0)
        shrank = sum(1 for t in tasks if t["delta_count"] < 0)
        same_size = sum(1 for t in tasks if t["delta_count"] == 0)

        return {
            "label": label,
            "n": len(tasks),
            "old_files_mean": round(statistics.mean(old_counts), 2),
            "new_files_mean": round(statistics.mean(new_counts), 2),
            "old_files_median": statistics.median(old_counts),
            "new_files_median": statistics.median(new_counts),
            "old_files_total": sum(old_counts),
            "new_files_total": sum(new_counts),
            "jaccard_mean": round(statistics.mean(jaccards), 4),
            "jaccard_median": round(statistics.median(jaccards), 4),
            "f1_vs_old_mean": round(statistics.mean(f1s), 4),
            "f1_vs_old_median": round(statistics.median(f1s), 4),
            "delta_mean": round(statistics.mean(deltas), 2),
            "total_added": sum(added),
            "total_removed": sum(removed),
            "identical": identical,
            "high_overlap": high_overlap,
            "low_overlap": low_overlap,
            "no_overlap": no_overlap,
            "grew": grew,
            "shrank": shrank,
            "same_size": same_size,
        }

    agg_all = compute_aggregate(valid, "all")
    agg_sdlc = compute_aggregate(valid_sdlc, "sdlc")
    agg_org = compute_aggregate(valid_org, "org")

    # Print summary
    print(f"{'=' * 70}")
    print("Ground Truth Re-Curation Comparison: Old (.bak) vs New (Promoted)")
    print(f"{'=' * 70}")

    for agg in [agg_all, agg_sdlc, agg_org]:
        if agg["n"] == 0:
            continue
        print(f"\n--- {agg['label'].upper()} ({agg['n']} tasks) ---")
        print(f"  File counts:  old mean={agg['old_files_mean']}, new mean={agg['new_files_mean']}")
        print(f"                old total={agg['old_files_total']}, new total={agg['new_files_total']}")
        print(f"  Jaccard:      mean={agg['jaccard_mean']}, median={agg['jaccard_median']}")
        print(f"  F1 vs old:    mean={agg['f1_vs_old_mean']}, median={agg['f1_vs_old_median']}")
        print(f"  Delta:        mean={agg['delta_mean']:+.2f} files/task")
        print(f"  Total added:  {agg['total_added']} files | Total removed: {agg['total_removed']} files")
        print(f"  Identical:    {agg['identical']} | High overlap: {agg['high_overlap']} | Low: {agg['low_overlap']} | None: {agg['no_overlap']}")
        print(f"  Grew: {agg['grew']} | Shrank: {agg['shrank']} | Same size: {agg['same_size']}")

    # Biggest changes
    if valid:
        print(f"\n--- MOST CHANGED (lowest Jaccard) ---")
        by_jaccard = sorted(valid, key=lambda t: t["jaccard"])
        for t in by_jaccard[:15]:
            print(f"  J={t['jaccard']:.3f}  {t['task']}  old={t['old_count']} new={t['new_count']} +{t['added']}/-{t['removed']}")

        print(f"\n--- MOST STABLE (highest Jaccard, not identical) ---")
        stable = [t for t in valid if t["jaccard"] < 1.0]
        by_jaccard_desc = sorted(stable, key=lambda t: -t["jaccard"])
        for t in by_jaccard_desc[:10]:
            print(f"  J={t['jaccard']:.3f}  {t['task']}  old={t['old_count']} new={t['new_count']} +{t['added']}/-{t['removed']}")

        print(f"\n--- IDENTICAL (Jaccard=1.0) ---")
        identical_tasks = [t for t in valid if t["jaccard"] == 1.0]
        print(f"  {len(identical_tasks)} tasks with identical file lists")
        for t in identical_tasks[:10]:
            print(f"    {t['task']} ({t['old_count']} files)")

        # Size change distribution
        print(f"\n--- SIZE CHANGE DISTRIBUTION ---")
        delta_buckets = defaultdict(int)
        for t in valid:
            d = t["delta_count"]
            if d < -5:
                delta_buckets["shrank >5"] += 1
            elif d < 0:
                delta_buckets["shrank 1-5"] += 1
            elif d == 0:
                delta_buckets["same"] += 1
            elif d <= 5:
                delta_buckets["grew 1-5"] += 1
            else:
                delta_buckets["grew >5"] += 1
        for bucket in ["shrank >5", "shrank 1-5", "same", "grew 1-5", "grew >5"]:
            print(f"  {bucket:15s}: {delta_buckets[bucket]}")

    if args.verbose:
        print(f"\n--- ALL TASKS ---")
        for t in sorted(valid, key=lambda x: x["task"]):
            print(f"  {t['task']:60s}  old={t['old_count']:3d}  new={t['new_count']:3d}  "
                  f"J={t['jaccard']:.3f}  +{t['added']}/-{t['removed']}")

    # Write JSON report
    report = {
        "summary": {
            "all": agg_all,
            "sdlc": agg_sdlc,
            "org": agg_org,
        },
        "per_task": valid,
    }

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, indent=2) + "\n")
        print(f"\nReport written to {out_path}")
    else:
        # Default output location
        out_path = ROOT / "results" / "gt_comparison_old_vs_new.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, indent=2) + "\n")
        print(f"\nReport written to {out_path}")

    print(f"{'=' * 70}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
