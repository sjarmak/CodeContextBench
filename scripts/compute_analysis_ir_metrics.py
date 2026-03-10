#!/usr/bin/env python3
"""Compute IR metrics for all tasks in runs/analysis/ using current ground truth.

Walks the analysis directory structure:
  runs/analysis/{csb_sdlc|csb_org}/{suite}/{baseline|mcp}/{task}/{task}_{N}/

For each trial, normalizes retrieval events from trajectory.json and computes
file-level IR metrics against the current (promoted) ground truth.

Usage:
    python3 scripts/compute_analysis_ir_metrics.py
    python3 scripts/compute_analysis_ir_metrics.py --output results/ir/analysis_ir_metrics.json
    python3 scripts/compute_analysis_ir_metrics.py --dry-run
"""

import argparse
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ANALYSIS_ROOT = ROOT / "runs" / "analysis"
BENCHMARKS = ROOT / "benchmarks"
SCRIPTS = ROOT / "scripts"

sys.path.insert(0, str(SCRIPTS))

from csb_metrics.ground_truth import build_ground_truth_registry
from normalize_retrieval_events import (
    normalize_task,
)
from retrieval_eval_pipeline import compute_file_level_metrics


def _load_selected_tasks():
    """Load the canonical task list."""
    tasks_file = ROOT / "configs" / "selected_benchmark_tasks.json"
    if not tasks_file.exists():
        return {}
    data = json.loads(tasks_file.read_text())
    raw = data.get("tasks", [])
    if isinstance(raw, list):
        return {t["task_id"].lower(): t for t in raw}
    return {k.lower(): v for k, v in raw.items()}


def _infer_benchmark(suite_name: str) -> str:
    """Infer benchmark name from suite directory name."""
    return suite_name


def walk_analysis_tasks():
    """Walk runs/analysis/ and yield task info dicts compatible with normalize_task()."""
    tasks = []

    for subset_dir in sorted(ANALYSIS_ROOT.iterdir()):
        if not subset_dir.is_dir():
            continue
        # csb_sdlc or csb_org
        subset = subset_dir.name

        for suite_dir in sorted(subset_dir.iterdir()):
            if not suite_dir.is_dir():
                continue
            suite = suite_dir.name

            for config_dir in sorted(suite_dir.iterdir()):
                if not config_dir.is_dir():
                    continue
                config_name = config_dir.name
                if config_name not in ("baseline", "mcp"):
                    continue

                for task_group in sorted(config_dir.iterdir()):
                    if not task_group.is_dir():
                        continue
                    task_name = task_group.name

                    for trial_dir in sorted(task_group.iterdir()):
                        if not trial_dir.is_dir():
                            continue

                        result_file = trial_dir / "result.json"
                        if not result_file.is_file():
                            continue

                        try:
                            rdata = json.loads(result_file.read_text())
                        except (json.JSONDecodeError, OSError):
                            rdata = {}

                        tasks.append({
                            "task_name": task_name,
                            "config_name": config_name,
                            "task_dir": trial_dir,
                            "batch_timestamp": "",
                            "result_data": rdata,
                            "run_id": f"analysis_{suite}",
                            "benchmark": suite,
                            "suite": suite,
                            "subset": subset,
                            "trial": trial_dir.name,
                        })

    return tasks


def main():
    parser = argparse.ArgumentParser(description="Compute IR metrics from runs/analysis/")
    parser.add_argument("--output", type=str, default="", help="Output JSON path")
    parser.add_argument("--dry-run", action="store_true", help="Just count tasks")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    # Load ground truth registry
    print("Loading ground truth registry...", file=sys.stderr)
    selected = _load_selected_tasks()
    gt_registry_raw = build_ground_truth_registry(BENCHMARKS, list(selected.values()))
    # Build case-insensitive lookup (analysis dirs use lowercase, GT keys use mixed case)
    gt_registry = {}
    for k, v in gt_registry_raw.items():
        gt_registry[k] = v
        gt_registry[k.lower()] = v
    print(f"  GT registry: {len(gt_registry_raw)} tasks ({len(gt_registry)} with lowercase aliases)", file=sys.stderr)

    # Walk analysis tasks
    print("Walking runs/analysis/...", file=sys.stderr)
    all_tasks = walk_analysis_tasks()
    print(f"  Found {len(all_tasks)} trial runs", file=sys.stderr)

    if args.dry_run:
        by_config = defaultdict(int)
        by_suite = defaultdict(int)
        unique_tasks = set()
        for t in all_tasks:
            by_config[t["config_name"]] += 1
            by_suite[t["suite"]] += 1
            unique_tasks.add(t["task_name"])
        print(f"\nUnique tasks: {len(unique_tasks)}")
        print(f"By config: {dict(by_config)}")
        print(f"By suite:")
        for s, n in sorted(by_suite.items()):
            print(f"  {s}: {n}")
        return 0

    # Process each trial
    print("Normalizing and computing metrics...", file=sys.stderr)
    task_metrics = []  # list of per-trial metric dicts
    skipped_no_gt = 0
    skipped_no_events = 0
    processed = 0

    for i, info in enumerate(all_tasks):
        if args.verbose and i % 100 == 0:
            print(f"  [{i}/{len(all_tasks)}]...", file=sys.stderr)

        # Normalize retrieval events
        doc = normalize_task(info, gt_registry)

        # Compute file-level metrics
        metrics = compute_file_level_metrics(doc)

        if not metrics.get("computable", False):
            reason = metrics.get("reason", "")
            if "no_ground_truth" in reason:
                skipped_no_gt += 1
            else:
                skipped_no_events += 1
            continue

        # Flatten nested precision/recall/f1/ndcg dicts into precision@K keys
        for metric_name in ["precision", "recall", "f1", "ndcg"]:
            nested = metrics.pop(metric_name, {})
            if isinstance(nested, dict):
                for k, v in nested.items():
                    metrics[f"{metric_name}@{k}"] = v

        metrics["task_name"] = info["task_name"]
        metrics["config"] = info["config_name"]
        metrics["suite"] = info["suite"]
        metrics["subset"] = info["subset"]
        metrics["trial"] = info["trial"]
        task_metrics.append(metrics)
        processed += 1

    print(f"  Processed: {processed}, no GT: {skipped_no_gt}, no events: {skipped_no_events}",
          file=sys.stderr)

    if not task_metrics:
        print("No computable metrics.", file=sys.stderr)
        return 1

    # Aggregate: average per task (across trials), then across tasks
    def aggregate(metrics_list, label=""):
        """Aggregate a list of per-trial metrics."""
        # Group by task
        by_task = defaultdict(list)
        for m in metrics_list:
            by_task[m["task_name"]].append(m)

        # Average each metric per task
        task_avgs = []
        for task_name, trials in by_task.items():
            avg = {"task_name": task_name, "n_trials": len(trials)}
            for key in ["file_recall", "mrr", "map_score", "context_efficiency"]:
                vals = [t[key] for t in trials if key in t]
                avg[key] = round(statistics.mean(vals), 4) if vals else None
            for k in [1, 3, 5, 10]:
                for metric in ["precision", "recall", "f1", "ndcg"]:
                    key = f"{metric}@{k}"
                    vals = [t[key] for t in trials if key in t]
                    avg[key] = round(statistics.mean(vals), 4) if vals else None
            avg["n_ground_truth"] = trials[0].get("n_ground_truth", 0)
            task_avgs.append(avg)

        # Overall means
        result = {"label": label, "n_tasks": len(task_avgs), "n_trials": len(metrics_list)}
        for key in ["file_recall", "mrr", "map_score", "context_efficiency"]:
            vals = [t[key] for t in task_avgs if t.get(key) is not None]
            result[key] = round(statistics.mean(vals), 4) if vals else None
            result[f"{key}_median"] = round(statistics.median(vals), 4) if vals else None
        for k in [1, 3, 5, 10]:
            for metric in ["precision", "recall", "f1", "ndcg"]:
                key = f"{metric}@{k}"
                vals = [t[key] for t in task_avgs if t.get(key) is not None]
                result[key] = round(statistics.mean(vals), 4) if vals else None

        return result, task_avgs

    # Split by config
    bl_metrics = [m for m in task_metrics if m["config"] == "baseline"]
    mcp_metrics = [m for m in task_metrics if m["config"] == "mcp"]

    overall_agg, overall_tasks = aggregate(task_metrics, "overall")
    bl_agg, bl_tasks = aggregate(bl_metrics, "baseline")
    mcp_agg, mcp_tasks = aggregate(mcp_metrics, "mcp")

    # By suite
    suites = sorted(set(m["suite"] for m in task_metrics))
    suite_aggs = {}
    for suite in suites:
        suite_bl = [m for m in task_metrics if m["suite"] == suite and m["config"] == "baseline"]
        suite_mcp = [m for m in task_metrics if m["suite"] == suite and m["config"] == "mcp"]
        bl_a, _ = aggregate(suite_bl, f"{suite}_baseline")
        mcp_a, _ = aggregate(suite_mcp, f"{suite}_mcp")
        suite_aggs[suite] = {"baseline": bl_a, "mcp": mcp_a}

    # Print summary
    print(f"\n{'=' * 70}")
    print("IR Metrics from runs/analysis/ (Current Ground Truth)")
    print(f"{'=' * 70}")

    for label, agg in [("OVERALL", overall_agg), ("BASELINE", bl_agg), ("MCP", mcp_agg)]:
        print(f"\n--- {label} ({agg['n_tasks']} tasks, {agg['n_trials']} trials) ---")
        print(f"  file_recall:        {agg.get('file_recall', 'N/A')}")
        print(f"  MRR:                {agg.get('mrr', 'N/A')}")
        print(f"  MAP:                {agg.get('map_score', 'N/A')}")
        print(f"  context_efficiency: {agg.get('context_efficiency', 'N/A')}")
        print(f"  P@1: {agg.get('precision@1', 'N/A')}  R@1: {agg.get('recall@1', 'N/A')}  F1@1: {agg.get('f1@1', 'N/A')}")
        print(f"  P@5: {agg.get('precision@5', 'N/A')}  R@5: {agg.get('recall@5', 'N/A')}  F1@5: {agg.get('f1@5', 'N/A')}")

    if bl_agg["n_tasks"] > 0 and mcp_agg["n_tasks"] > 0:
        print(f"\n--- MCP vs BASELINE DELTA ---")
        for key in ["file_recall", "mrr", "map_score", "context_efficiency"]:
            bl_v = bl_agg.get(key)
            mcp_v = mcp_agg.get(key)
            if bl_v is not None and mcp_v is not None:
                print(f"  {key:22s}: BL={bl_v:.4f}  MCP={mcp_v:.4f}  delta={mcp_v - bl_v:+.4f}")

    print(f"\n--- BY SUITE ---")
    for suite in suites:
        bl_a = suite_aggs[suite]["baseline"]
        mcp_a = suite_aggs[suite]["mcp"]
        bl_r = bl_a.get("file_recall", 0) or 0
        mcp_r = mcp_a.get("file_recall", 0) or 0
        delta = mcp_r - bl_r
        print(f"  {suite:35s}  BL_R={bl_r:.3f} ({bl_a['n_tasks']:3d}t)  "
              f"MCP_R={mcp_r:.3f} ({mcp_a['n_tasks']:3d}t)  delta={delta:+.3f}")

    print(f"{'=' * 70}")

    # Write report
    report = {
        "overall": overall_agg,
        "baseline": bl_agg,
        "mcp": mcp_agg,
        "by_suite": suite_aggs,
        "per_task": {
            "baseline": bl_tasks,
            "mcp": mcp_tasks,
        },
        "meta": {
            "total_trials": len(all_tasks),
            "computable_trials": processed,
            "skipped_no_gt": skipped_no_gt,
            "skipped_no_events": skipped_no_events,
        },
    }

    out_path = Path(args.output) if args.output else ROOT / "results" / "ir" / "analysis_ir_metrics.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2) + "\n")
    print(f"\nReport: {out_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
