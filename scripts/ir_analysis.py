#!/usr/bin/env python3
"""IR (Information Retrieval) analysis for CodeContextBench.

Computes IR quality metrics (precision, recall, MRR, nDCG, MAP) by comparing
the files each agent retrieved against ground-truth files that needed change.

Usage:
    # Build ground truth from benchmark task dirs
    python3 scripts/ir_analysis.py --build-ground-truth

    # Run IR analysis (builds ground truth if missing)
    python3 scripts/ir_analysis.py

    # JSON output
    python3 scripts/ir_analysis.py --json

    # Filter to one benchmark
    python3 scripts/ir_analysis.py --suite ccb_swebenchpro

    # Per-task scores
    python3 scripts/ir_analysis.py --per-task
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ccb_metrics.ground_truth import (
    build_ground_truth_registry,
    load_registry,
    save_registry,
    TaskGroundTruth,
)
from ccb_metrics.ir_metrics import (
    compute_ir_scores,
    aggregate_ir_scores,
    extract_retrieved_files,
    IRScores,
)

RUNS_DIR = Path("/home/stephanie_jarmak/evals/custom_agents/agents/claudecode/runs/official")
BENCHMARKS_DIR = Path(__file__).resolve().parent.parent / "benchmarks"
SELECTION_FILE = Path(__file__).resolve().parent.parent / "configs" / "selected_benchmark_tasks.json"
GT_CACHE = Path(__file__).resolve().parent.parent / "configs" / "ground_truth_files.json"

SKIP_PATTERNS = ["__broken_verifier", "validation_test", "archive", "__archived"]
CONFIGS = ["baseline", "sourcegraph_full"]
# Benchmarks dropped from evaluation — exclude from ground truth builds
DROPPED_BENCHMARKS = {"ccb_dependeval"}

DIR_PREFIX_TO_SUITE = {
    "bigcode_mcp_": "ccb_largerepo",
    "bigcode_sgcompare_": "ccb_largerepo",
    "codereview_": "ccb_codereview",
    "crossrepo_": "ccb_crossrepo",
    "dependeval_": "ccb_dependeval",
    "dibench_": "ccb_dibench",
    "enterprise_": "ccb_enterprise",
    "governance_": "ccb_governance",
    "investigation_": "ccb_investigation",
    "k8s_docs_": "ccb_k8sdocs",
    "linuxflbench_": "ccb_linuxflbench",
    "locobench_": "ccb_locobench",
    "pytorch_": "ccb_pytorch",
    "repoqa_": "ccb_repoqa",
    "swebenchpro_": "ccb_swebenchpro",
    "sweperf_": "ccb_sweperf",
    "tac_": "ccb_tac",
    "paired_rerun_dibench_": "ccb_dibench",
    "paired_rerun_crossrepo_": "ccb_crossrepo",
    "paired_rerun_pytorch_": "ccb_pytorch",
    "paired_rerun_": None,
}


def should_skip(dirname: str) -> bool:
    return any(pat in dirname for pat in SKIP_PATTERNS)


def _is_batch_timestamp(name: str) -> bool:
    return bool(re.match(r"\d{4}-\d{2}-\d{2}__\d{2}-\d{2}-\d{2}", name))


def _suite_from_run_dir(name: str) -> str | None:
    for prefix, suite in DIR_PREFIX_TO_SUITE.items():
        if name.startswith(prefix):
            return suite
    if name.startswith("swebenchpro_gapfill_"):
        return "ccb_swebenchpro"
    return None


def _load_selected_tasks() -> list[dict]:
    """Load selected tasks from config, excluding dropped benchmarks."""
    if not SELECTION_FILE.is_file():
        return []
    data = json.loads(SELECTION_FILE.read_text())
    tasks = data.get("tasks", [])
    return [t for t in tasks if t.get("benchmark", "") not in DROPPED_BENCHMARKS]


def _ensure_ground_truth() -> dict[str, TaskGroundTruth]:
    """Load or build ground truth registry."""
    if GT_CACHE.is_file():
        registry = load_registry(GT_CACHE)
        if registry:
            return registry

    selected = _load_selected_tasks()
    registry = build_ground_truth_registry(BENCHMARKS_DIR, selected)
    if registry:
        save_registry(registry, GT_CACHE)
    return registry


def _walk_task_dirs() -> list[dict]:
    """Walk run directories, collect task info with dedup by timestamp."""
    all_tasks: dict[tuple[str, str, str], dict] = {}  # (suite, config, task_id) -> info

    if not RUNS_DIR.exists():
        return []

    for run_dir in sorted(RUNS_DIR.iterdir()):
        if not run_dir.is_dir() or run_dir.name in ("archive", "MANIFEST.json"):
            continue
        if should_skip(run_dir.name):
            continue

        suite = _suite_from_run_dir(run_dir.name)

        for config_dir in sorted(run_dir.iterdir()):
            if not config_dir.is_dir():
                continue
            config_name = config_dir.name
            if config_name not in CONFIGS:
                continue

            for batch_dir in sorted(config_dir.iterdir()):
                if not batch_dir.is_dir() or not _is_batch_timestamp(batch_dir.name):
                    continue

                for task_dir in sorted(batch_dir.iterdir()):
                    if not task_dir.is_dir():
                        continue

                    # Extract task_id from dir name (strip hash suffix)
                    task_name = task_dir.name
                    # Task dirs: task_name__hash
                    if "__" in task_name:
                        parts = task_name.rsplit("__", 1)
                        if len(parts[1]) >= 6:  # hash-like suffix
                            task_name = parts[0]

                    # Find transcript (Harbor layout: agent/claude-code.txt)
                    transcript = task_dir / "agent" / "claude-code.txt"
                    if not transcript.is_file():
                        transcript = task_dir / "claude-code.txt"
                    if not transcript.is_file():
                        transcript = task_dir / "agent_output" / "claude-code.txt"

                    # Timestamp-based dedup
                    started_at = ""
                    result_file = task_dir / "result.json"
                    if result_file.is_file():
                        try:
                            rdata = json.loads(result_file.read_text())
                            started_at = rdata.get("started_at", "")
                            # Also try to get task_name from result
                            if "task_name" in rdata:
                                task_name = rdata["task_name"]
                        except Exception:
                            pass

                    task_suite = suite
                    if task_suite is None:
                        # Infer from task_name
                        task_suite = _infer_suite(task_name)

                    info = {
                        "task_id": task_name,
                        "suite": task_suite or "unknown",
                        "config": config_name,
                        "task_dir": str(task_dir),
                        "transcript": str(transcript) if transcript.is_file() else None,
                        "started_at": started_at,
                    }

                    key = (info["suite"], config_name, task_name)
                    if key in all_tasks:
                        if started_at > all_tasks[key].get("started_at", ""):
                            all_tasks[key] = info
                    else:
                        all_tasks[key] = info

    return list(all_tasks.values())


def _infer_suite(task_id: str) -> str | None:
    """Infer suite from task_id patterns."""
    if task_id.startswith("instance_"):
        return "ccb_swebenchpro"
    if task_id.startswith("sgt-"):
        return "ccb_pytorch"
    if task_id.endswith("-doc-001"):
        return "ccb_k8sdocs"
    return None


def run_ir_analysis(
    suite_filter: str | None = None,
    per_task: bool = False,
) -> dict:
    """Main analysis pipeline."""
    gt_registry = _ensure_ground_truth()
    if not gt_registry:
        return {"error": "No ground truth available. Run --build-ground-truth first."}

    tasks = _walk_task_dirs()
    if suite_filter:
        tasks = [t for t in tasks if t["suite"] == suite_filter]

    # Compute IR scores for tasks with ground truth
    all_scores: list[IRScores] = []
    by_suite_config: dict[tuple[str, str], list[IRScores]] = defaultdict(list)
    skipped_no_gt = 0
    skipped_no_transcript = 0

    for task_info in tasks:
        task_id = task_info["task_id"]
        config = task_info["config"]
        suite = task_info["suite"]

        gt = gt_registry.get(task_id)
        if not gt:
            skipped_no_gt += 1
            continue

        if not task_info.get("transcript"):
            skipped_no_transcript += 1
            continue

        retrieved = extract_retrieved_files(Path(task_info["transcript"]))
        scores = compute_ir_scores(
            retrieved=retrieved,
            ground_truth_files=gt.files,
            task_id=task_id,
            config_name=config,
        )
        all_scores.append(scores)
        by_suite_config[(suite, config)].append(scores)

    # Aggregate
    overall_by_config: dict[str, list[IRScores]] = defaultdict(list)
    for s in all_scores:
        overall_by_config[s.config_name].append(s)

    result: dict = {
        "summary": {
            "total_tasks_with_gt": len(gt_registry),
            "total_runs_analyzed": len(all_scores),
            "skipped_no_ground_truth": skipped_no_gt,
            "skipped_no_transcript": skipped_no_transcript,
        },
        "overall_by_config": {
            cfg: aggregate_ir_scores(scores)
            for cfg, scores in sorted(overall_by_config.items())
        },
        "by_suite_config": {
            f"{suite}__{cfg}": aggregate_ir_scores(scores)
            for (suite, cfg), scores in sorted(by_suite_config.items())
        },
    }

    # Statistical tests: compare baseline vs SG_full
    bl_scores = overall_by_config.get("baseline", [])
    sg_scores = overall_by_config.get("sourcegraph_full", [])
    if len(bl_scores) >= 5 and len(sg_scores) >= 5:
        try:
            from ccb_metrics.statistics import welchs_t_test, cohens_d, bootstrap_ci

            # Match by task_id for paired comparison
            bl_by_id = {s.task_id: s for s in bl_scores}
            sg_by_id = {s.task_id: s for s in sg_scores}
            common = set(bl_by_id) & set(sg_by_id)

            if len(common) >= 5:
                bl_recalls = [bl_by_id[tid].file_recall for tid in sorted(common)]
                sg_recalls = [sg_by_id[tid].file_recall for tid in sorted(common)]
                bl_mrrs = [bl_by_id[tid].mrr for tid in sorted(common)]
                sg_mrrs = [sg_by_id[tid].mrr for tid in sorted(common)]

                result["statistical_tests"] = {
                    "n_paired": len(common),
                    "file_recall": {
                        "welchs_t": welchs_t_test(bl_recalls, sg_recalls),
                        "cohens_d": cohens_d(bl_recalls, sg_recalls),
                        "bootstrap_ci_delta": bootstrap_ci(
                            [s - b for b, s in zip(bl_recalls, sg_recalls)]
                        ),
                    },
                    "mrr": {
                        "welchs_t": welchs_t_test(bl_mrrs, sg_mrrs),
                        "cohens_d": cohens_d(bl_mrrs, sg_mrrs),
                        "bootstrap_ci_delta": bootstrap_ci(
                            [s - b for b, s in zip(bl_mrrs, sg_mrrs)]
                        ),
                    },
                }
        except ImportError:
            pass

    if per_task:
        result["per_task"] = [s.to_dict() for s in all_scores]

    return result


def format_table(data: dict) -> str:
    """Format IR analysis results as ASCII table."""
    lines = []
    lines.append("IR Analysis Report")
    lines.append("=" * 70)
    lines.append("")

    s = data.get("summary", {})
    lines.append(f"Tasks with ground truth: {s.get('total_tasks_with_gt', 0)}")
    lines.append(f"Runs analyzed:           {s.get('total_runs_analyzed', 0)}")
    lines.append(f"Skipped (no GT):         {s.get('skipped_no_ground_truth', 0)}")
    lines.append(f"Skipped (no transcript): {s.get('skipped_no_transcript', 0)}")
    lines.append("")

    # Overall by config
    overall = data.get("overall_by_config", {})
    if overall:
        lines.append("OVERALL BY CONFIG:")
        header = f"  {'Config':20s} {'MRR':>8s} {'MAP':>8s} {'F.Recall':>8s} {'Ctx.Eff':>8s} {'P@5':>8s} {'R@5':>8s} {'n':>5s}"
        lines.append(header)
        lines.append("  " + "-" * (len(header) - 2))

        for cfg, agg in sorted(overall.items()):
            if not agg:
                continue
            row = f"  {cfg:20s}"
            for metric in ("mrr", "map_score", "file_recall", "context_efficiency", "precision@5", "recall@5"):
                val = agg.get(metric, {}).get("mean", 0.0)
                row += f" {val:>8.3f}"
            n = agg.get("_totals", {}).get("n_tasks", 0)
            row += f" {n:>5d}"
            lines.append(row)
        lines.append("")

    # By suite+config
    by_sc = data.get("by_suite_config", {})
    if by_sc:
        lines.append("BY SUITE x CONFIG:")
        header = f"  {'Suite__Config':35s} {'MRR':>7s} {'MAP':>7s} {'F.Rec':>7s} {'n':>4s}"
        lines.append(header)
        lines.append("  " + "-" * (len(header) - 2))

        for key, agg in sorted(by_sc.items()):
            if not agg:
                continue
            mrr_m = agg.get("mrr", {}).get("mean", 0.0)
            map_m = agg.get("map_score", {}).get("mean", 0.0)
            fr_m = agg.get("file_recall", {}).get("mean", 0.0)
            n = agg.get("_totals", {}).get("n_tasks", 0)
            lines.append(f"  {key:35s} {mrr_m:>7.3f} {map_m:>7.3f} {fr_m:>7.3f} {n:>4d}")
        lines.append("")

    # Statistical tests
    stats = data.get("statistical_tests", {})
    if stats:
        lines.append("STATISTICAL TESTS (baseline vs SG_full):")
        lines.append(f"  Paired tasks: {stats.get('n_paired', 0)}")
        for metric_name in ("file_recall", "mrr"):
            ms = stats.get(metric_name, {})
            if not ms:
                continue
            t = ms.get("welchs_t", {})
            d = ms.get("cohens_d", {})
            bci = ms.get("bootstrap_ci_delta", {})
            sig = "***" if t.get("is_significant") else "n.s."
            lines.append(
                f"  {metric_name}: t={t.get('t_stat', 'N/A')}, "
                f"p={t.get('p_value', 'N/A')}, d={d.get('d', 'N/A')} "
                f"({d.get('magnitude', '')}), "
                f"delta CI=[{bci.get('ci_lower', 'N/A')}, {bci.get('ci_upper', 'N/A')}] "
                f"{sig}"
            )
        lines.append("")

    return "\n".join(lines)


def parse_args():
    parser = argparse.ArgumentParser(
        description="IR quality analysis for CodeContextBench."
    )
    parser.add_argument(
        "--build-ground-truth", action="store_true",
        help="Extract ground truth for all selected tasks and write cache",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output JSON instead of table",
    )
    parser.add_argument(
        "--suite", default=None,
        help="Filter to one benchmark suite",
    )
    parser.add_argument(
        "--per-task", action="store_true",
        help="Include per-task IR scores in output",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    if args.build_ground_truth:
        selected = _load_selected_tasks()
        registry = build_ground_truth_registry(BENCHMARKS_DIR, selected)
        save_registry(registry, GT_CACHE)
        print(f"Ground truth extracted for {len(registry)} tasks → {GT_CACHE}")
        # Show breakdown
        by_bench = defaultdict(int)
        by_source = defaultdict(int)
        by_confidence = defaultdict(int)
        for gt in registry.values():
            by_bench[gt.benchmark] += 1
            by_source[gt.source] += 1
            by_confidence[gt.confidence] += 1
        print(f"  By benchmark: {dict(sorted(by_bench.items()))}")
        print(f"  By source:    {dict(sorted(by_source.items()))}")
        print(f"  By confidence:{dict(sorted(by_confidence.items()))}")
        return

    data = run_ir_analysis(
        suite_filter=args.suite,
        per_task=args.per_task,
    )

    if args.json:
        print(json.dumps(data, indent=2))
    else:
        print(format_table(data))


if __name__ == "__main__":
    main()
