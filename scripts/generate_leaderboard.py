#!/usr/bin/env python3
"""
Generate leaderboard views from MANIFEST.json.

Reads runs/official/MANIFEST.json and produces:
  - leaderboard.json: machine-readable per-benchmark and aggregate rankings
  - LEADERBOARD_RESULTS.md: human-readable ranking tables

Scoring rules (see docs/LEADERBOARD.md):
  - Per-benchmark: mean_reward across all tasks
  - Aggregate: unweighted mean of per-benchmark mean_rewards over qualifying benchmarks
  - Errored tasks count as reward=0.0
  - Must run ALL tasks in a benchmark to qualify for that benchmark's leaderboard
  - Tie-breaking: benchmarks_completed > pass_rate > median_reward > token_efficiency
"""

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = PROJECT_ROOT / "runs" / "official" / "MANIFEST.json"
SELECTED_TASKS_PATH = PROJECT_ROOT / "configs" / "selected_benchmark_tasks.json"

# Required task counts per benchmark (from selected_benchmark_tasks.json)
# Loaded dynamically in main(), but fallback defaults here for reference
DEFAULT_BENCHMARK_TASK_COUNTS = {
    "ccb_swebenchpro": 36,
    "ccb_dependeval": 32,
    "ccb_locobench": 25,
    "ccb_pytorch": 12,
    "ccb_repoqa": 10,
    "ccb_dibench": 8,
    "ccb_tac": 8,
    "ccb_k8sdocs": 5,
    "ccb_crossrepo": 5,
    "ccb_linuxflbench": 5,
    "ccb_largerepo": 4,
    "ccb_codereview": 3,
    "ccb_sweperf": 3,
}

TOTAL_BENCHMARKS = 13


def load_benchmark_task_counts() -> dict[str, int]:
    """Load required task counts per benchmark from selected_benchmark_tasks.json."""
    if not SELECTED_TASKS_PATH.exists():
        print(f"Warning: {SELECTED_TASKS_PATH} not found, using defaults", file=sys.stderr)
        return dict(DEFAULT_BENCHMARK_TASK_COUNTS)

    data = json.loads(SELECTED_TASKS_PATH.read_text())
    tasks = data.get("tasks", [])
    counts: dict[str, int] = defaultdict(int)
    for task in tasks:
        benchmark = task.get("benchmark", "")
        if benchmark:
            counts[benchmark] += 1
    return dict(counts) if counts else dict(DEFAULT_BENCHMARK_TASK_COUNTS)


def compute_pass_rate(tasks: dict) -> float:
    """Fraction of tasks with reward > 0.0."""
    if not tasks:
        return 0.0
    passed = sum(1 for t in tasks.values() if t.get("reward", 0.0) > 0.0)
    return round(passed / len(tasks), 4)


def compute_median_reward(tasks: dict) -> float:
    """Median of per-task rewards."""
    rewards = sorted(t.get("reward", 0.0) for t in tasks.values())
    n = len(rewards)
    if n == 0:
        return 0.0
    if n % 2 == 1:
        return rewards[n // 2]
    return (rewards[n // 2 - 1] + rewards[n // 2]) / 2.0


def generate_leaderboard(manifest: dict, benchmark_task_counts: dict) -> dict:
    """Generate leaderboard data from MANIFEST.

    Returns dict with 'per_benchmark' and 'aggregate' arrays.
    """
    runs = manifest.get("runs", {})

    # Group by (agent_model, config) -> {benchmark: run_data}
    # Each MANIFEST key is "suite/config"
    agent_benchmarks: dict[tuple[str, str], dict[str, dict]] = defaultdict(dict)

    for manifest_key, run_data in runs.items():
        parts = manifest_key.split("/")
        if len(parts) != 2:
            continue
        benchmark, config = parts
        model = run_data.get("model", "unknown")
        agent_benchmarks[(model, config)][benchmark] = run_data

    # Build per-benchmark leaderboard
    per_benchmark = []
    for (agent, config), benchmarks in sorted(agent_benchmarks.items()):
        short_agent = agent.rsplit("/", 1)[-1] if "/" in agent else agent
        submission_name = f"{short_agent} ({config})"

        for benchmark, run_data in sorted(benchmarks.items()):
            required = benchmark_task_counts.get(benchmark)
            actual = run_data.get("task_count", 0)
            is_complete = required is not None and actual >= required

            # Judge score: use run-level mean if present, else compute from tasks
            mean_judge = run_data.get("mean_judge_score")
            judge_count = run_data.get("judge_count", 0)
            if mean_judge is None:
                # Compute from per-task judge_score fields
                task_judges = [
                    t.get("judge_score") for t in run_data.get("tasks", {}).values()
                    if t.get("judge_score") is not None
                ]
                if task_judges:
                    mean_judge = round(sum(task_judges) / len(task_judges), 4)
                    judge_count = len(task_judges)

            entry = {
                "benchmark": benchmark,
                "submission": submission_name,
                "agent": agent,
                "config": config,
                "mean_reward": run_data.get("mean_reward", 0.0),
                "mean_judge_score": mean_judge,
                "judge_count": judge_count,
                "pass_rate": compute_pass_rate(run_data.get("tasks", {})),
                "task_count": actual,
                "required_tasks": required or actual,
                "is_complete": is_complete,
            }
            per_benchmark.append(entry)

    # Build aggregate leaderboard
    aggregate = []
    for (agent, config), benchmarks in sorted(agent_benchmarks.items()):
        complete_benchmarks = []
        for benchmark, run_data in benchmarks.items():
            required = benchmark_task_counts.get(benchmark)
            actual = run_data.get("task_count", 0)
            if required is not None and actual >= required:
                complete_benchmarks.append(benchmark)

        benchmarks_completed = len(complete_benchmarks)
        total_tasks = sum(r.get("task_count", 0) for r in benchmarks.values())

        # Aggregate score: mean of per-benchmark mean_rewards for COMPLETE benchmarks
        if complete_benchmarks:
            benchmark_means = [
                benchmarks[b].get("mean_reward", 0.0) for b in complete_benchmarks
            ]
            agg_score = round(sum(benchmark_means) / len(benchmark_means), 4)
        else:
            agg_score = 0.0

        # Total pass rate across all tasks
        all_tasks = {}
        for run_data in benchmarks.values():
            all_tasks.update(run_data.get("tasks", {}))
        total_pass_rate = compute_pass_rate(all_tasks)
        median_reward = compute_median_reward(all_tasks)

        # Display name: short agent name + config
        short_agent = agent.rsplit("/", 1)[-1] if "/" in agent else agent
        submission_name = f"{short_agent} ({config})"

        # Aggregate judge score: mean of per-benchmark mean_judge_scores where available
        benchmark_judge_scores = []
        for b in complete_benchmarks:
            rd = benchmarks[b]
            mj = rd.get("mean_judge_score")
            if mj is None:
                # Compute from per-task judge_score fields
                tj = [
                    t.get("judge_score") for t in rd.get("tasks", {}).values()
                    if t.get("judge_score") is not None
                ]
                if tj:
                    mj = sum(tj) / len(tj)
            if mj is not None:
                benchmark_judge_scores.append(mj)
        agg_judge = round(sum(benchmark_judge_scores) / len(benchmark_judge_scores), 4) if benchmark_judge_scores else None

        entry = {
            "submission": submission_name,
            "agent": agent,
            "config": config,
            "ccb_aggregate_score": agg_score,
            "ccb_aggregate_judge_score": agg_judge,
            "benchmarks_completed": benchmarks_completed,
            "total_benchmarks": TOTAL_BENCHMARKS,
            "total_tasks": total_tasks,
            "all_benchmarks_complete": benchmarks_completed == TOTAL_BENCHMARKS,
            "pass_rate": total_pass_rate,
            "median_reward": round(median_reward, 4),
        }
        aggregate.append(entry)

    # Sort per-benchmark: by benchmark, then mean_reward desc, then tie-breakers
    per_benchmark.sort(
        key=lambda e: (e["benchmark"], -e["mean_reward"], -e["pass_rate"]),
    )

    # Sort aggregate: by ccb_aggregate_score desc, then benchmarks_completed, then tie-breakers
    aggregate.sort(
        key=lambda e: (
            -e["ccb_aggregate_score"],
            -e["benchmarks_completed"],
            -e["pass_rate"],
            -e["median_reward"],
        ),
    )

    return {
        "generated": datetime.now(timezone.utc).isoformat(),
        "manifest_source": str(MANIFEST_PATH),
        "per_benchmark": per_benchmark,
        "aggregate": aggregate,
    }


def generate_markdown(leaderboard: dict, benchmark_task_counts: dict) -> str:
    """Generate LEADERBOARD_RESULTS.md content."""
    lines = [
        "# CodeContextBench Leaderboard Results",
        "",
        f"*Generated: {leaderboard['generated']}*",
        "",
    ]

    # Aggregate ranking
    lines.append("## Aggregate Ranking")
    lines.append("")
    agg = leaderboard["aggregate"]

    if agg:
        lines.append("| Rank | Submission | CCB Aggregate | Judge Score | Benchmarks | Tasks | Pass Rate |")
        lines.append("|------|-----------|--------------|-------------|------------|-------|-----------|")
        for i, entry in enumerate(agg, 1):
            judge_str = f"{entry['ccb_aggregate_judge_score']:.3f}" if entry.get('ccb_aggregate_judge_score') is not None else "---"
            lines.append(
                f"| {i} | {entry['submission']} | "
                f"{entry['ccb_aggregate_score']:.3f} | "
                f"{judge_str} | "
                f"{entry['benchmarks_completed']}/{entry['total_benchmarks']} | "
                f"{entry['total_tasks']} | {entry['pass_rate']:.3f} |"
            )
        lines.append("")
        lines.append("*Aggregate score is the mean of per-benchmark mean rewards over qualifying (complete) benchmarks.*")
        lines.append("")
    else:
        lines.append("*No submissions found.*")
        lines.append("")

    # Per-benchmark rankings
    lines.append("## Per-Benchmark Rankings")
    lines.append("")

    # Group by benchmark
    by_benchmark: dict[str, list] = defaultdict(list)
    for entry in leaderboard["per_benchmark"]:
        by_benchmark[entry["benchmark"]].append(entry)

    for benchmark in sorted(by_benchmark.keys()):
        entries = by_benchmark[benchmark]
        required = benchmark_task_counts.get(benchmark, "?")
        lines.append(f"### {benchmark} ({required} tasks)")
        lines.append("")
        lines.append("| Rank | Submission | Verifier Score | Judge Score | Pass Rate | Tasks | Complete |")
        lines.append("|------|-----------|----------------|-------------|-----------|-------|----------|")

        # Separate complete and incomplete
        complete_entries = [e for e in entries if e["is_complete"]]
        incomplete_entries = [e for e in entries if not e["is_complete"]]

        rank = 1
        for entry in complete_entries:
            judge_str = f"{entry['mean_judge_score']:.3f}" if entry.get('mean_judge_score') is not None else "---"
            lines.append(
                f"| {rank} | {entry['submission']} | "
                f"{entry['mean_reward']:.3f} | {judge_str} | {entry['pass_rate']:.3f} | "
                f"{entry['task_count']}/{entry['required_tasks']} | Yes |"
            )
            rank += 1
        for entry in incomplete_entries:
            judge_str = f"{entry['mean_judge_score']:.3f}" if entry.get('mean_judge_score') is not None else "---"
            lines.append(
                f"| - | {entry['submission']} | "
                f"{entry['mean_reward']:.3f} | {judge_str} | {entry['pass_rate']:.3f} | "
                f"{entry['task_count']}/{entry['required_tasks']} | No |"
            )
        lines.append("")

    # Footer
    lines.append("---")
    lines.append("")
    lines.append("*Scoring rules: see [docs/LEADERBOARD.md](docs/LEADERBOARD.md)*")
    lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Generate leaderboard from MANIFEST.json",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=MANIFEST_PATH,
        help=f"Path to MANIFEST.json (default: {MANIFEST_PATH})",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=PROJECT_ROOT / "leaderboard.json",
        help="Output path for leaderboard JSON",
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=PROJECT_ROOT / "LEADERBOARD_RESULTS.md",
        help="Output path for leaderboard Markdown",
    )
    args = parser.parse_args()

    if not args.manifest.exists():
        print(f"ERROR: MANIFEST not found: {args.manifest}", file=sys.stderr)
        sys.exit(1)

    manifest = json.loads(args.manifest.read_text())
    benchmark_task_counts = load_benchmark_task_counts()

    leaderboard = generate_leaderboard(manifest, benchmark_task_counts)

    # Write JSON
    with open(args.output_json, "w") as f:
        json.dump(leaderboard, f, indent=2)
    print(f"Wrote {args.output_json}")

    # Write Markdown
    md = generate_markdown(leaderboard, benchmark_task_counts)
    args.output_md.write_text(md)
    print(f"Wrote {args.output_md}")

    # Summary
    print(f"\nSubmissions: {len(leaderboard['aggregate'])}")
    print(f"Per-benchmark entries: {len(leaderboard['per_benchmark'])}")
    for entry in leaderboard["aggregate"]:
        print(f"  {entry['submission']}: {entry['ccb_aggregate_score']:.3f} ({entry['benchmarks_completed']}/{entry['total_benchmarks']} benchmarks)")


if __name__ == "__main__":
    main()
