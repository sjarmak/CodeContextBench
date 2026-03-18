#!/usr/bin/env python3
"""Coverage gap CLI: find unrun tasks for any harness/config combination.

Reads selected_benchmark_tasks.json (canonical task list) and MANIFEST.json
(run history) to compute which tasks still need to be run.

Usage examples:
    # Show gaps for openhands baseline config (JSON output)
    python3 scripts/evaluation/coverage_gaps.py --harness openhands --config baseline

    # Show gaps for claude-code mcp-remote-direct (table output)
    python3 scripts/evaluation/coverage_gaps.py --config mcp-remote-direct --output table

    # Show all configs for openhands
    python3 scripts/evaluation/coverage_gaps.py --harness openhands --output table

    # Generate a subset JSON for re-running
    python3 scripts/evaluation/coverage_gaps.py --harness openhands --config baseline \\
        --generate-subset configs/harnesses/oh_gap_baseline_new.json

    # Use custom file paths
    python3 scripts/evaluation/coverage_gaps.py \\
        --selected-tasks configs/selected_benchmark_tasks.json \\
        --manifest runs/official/MANIFEST.json \\
        --harness openhands --config baseline
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# Default file locations
DEFAULT_SELECTED_TASKS = REPO_ROOT / "configs" / "selected_benchmark_tasks.json"
DEFAULT_MANIFEST = REPO_ROOT / "runs" / "official" / "MANIFEST.json"

# Prefixes that indicate a suite key (claude-code harness) vs a named harness key
SUITE_PREFIXES = ("csb_", "ccb_")


def is_suite_key(first_segment: str) -> bool:
    """Return True if this key segment is a benchmark suite (claude-code harness)."""
    return any(first_segment.startswith(p) for p in SUITE_PREFIXES)


def load_selected_tasks(path: Path) -> list[dict]:
    """Load and return the list of selected benchmark tasks."""
    data = json.loads(path.read_text())
    tasks = data.get("tasks", [])
    if not tasks:
        # Some subset files store tasks at the top level as a list
        if isinstance(data, list):
            tasks = data
    return tasks


def load_run_history(manifest_path: Path) -> dict[str, dict]:
    """Load the run_history dict from MANIFEST.json.

    Returns: {"{suite_or_harness}/{config}": {task_id: {...}, ...}}
    """
    data = json.loads(manifest_path.read_text())
    return data.get("run_history", {})


def get_harness_configs(run_history: dict, harness: str) -> list[str]:
    """Return all config names available for the given harness."""
    configs = set()
    for key in run_history:
        parts = key.split("/", 1)
        if len(parts) != 2:
            continue
        first, config = parts
        if harness == "claude-code":
            if is_suite_key(first):
                configs.add(config)
        else:
            if first == harness:
                configs.add(config)
    return sorted(configs)


def get_completed_tasks(
    run_history: dict,
    harness: str,
    config: str,
) -> set[str]:
    """Return set of task_ids that have at least one run recorded."""
    completed: set[str] = set()
    for key, task_data in run_history.items():
        parts = key.split("/", 1)
        if len(parts) != 2:
            continue
        first, key_config = parts
        if key_config != config:
            continue
        if harness == "claude-code":
            if not is_suite_key(first):
                continue
        else:
            if first != harness:
                continue
        for task_id, info in task_data.items():
            if info.get("n_runs", 0) > 0:
                completed.add(task_id)
    return completed


def compute_gap(
    selected_tasks: list[dict],
    completed: set[str],
) -> tuple[list[dict], dict[str, int]]:
    """Compute gap tasks and per-benchmark gap counts.

    Returns:
        gap_tasks: list of task dicts that haven't been run
        benchmark_counts: {benchmark_name: gap_count}
    """
    gap_tasks = []
    benchmark_counts: dict[str, int] = defaultdict(int)

    for task in selected_tasks:
        task_id = task.get("task_id", "")
        if task_id not in completed:
            gap_tasks.append(task)
            benchmark = task.get("benchmark", task.get("suite", "unknown"))
            benchmark_counts[benchmark] += 1

    return gap_tasks, dict(benchmark_counts)


def format_table(
    harness: str,
    config: str,
    total: int,
    completed_count: int,
    gap_tasks: list[dict],
    benchmark_counts: dict[str, int],
) -> str:
    """Format gap results as a human-readable table."""
    lines = []
    lines.append(f"Coverage Gap: {harness}/{config}")
    lines.append("=" * 60)
    lines.append(f"  Total selected tasks : {total}")
    lines.append(f"  Completed tasks      : {completed_count}")
    lines.append(f"  Gap (unrun) tasks    : {len(gap_tasks)}")
    lines.append(f"  Coverage             : {completed_count / total * 100:.1f}%" if total else "  Coverage: N/A")
    lines.append("")

    if benchmark_counts:
        lines.append("Gap by benchmark:")
        for bm, count in sorted(benchmark_counts.items()):
            lines.append(f"  {bm:<45} {count:>4} tasks")
        lines.append("")

    if gap_tasks:
        lines.append(f"Gap task IDs ({len(gap_tasks)} total):")
        for t in sorted(gap_tasks, key=lambda x: (x.get("benchmark", ""), x.get("task_id", ""))):
            lines.append(f"  {t.get('task_id', '?')}")

    return "\n".join(lines)


def format_multi_config_table(
    harness: str,
    results: list[dict],
    total: int,
) -> str:
    """Format gap results for multiple configs as a table."""
    lines = []
    lines.append(f"Coverage Gaps: {harness} (all configs)")
    lines.append("=" * 70)
    lines.append(f"{'Config':<35} {'Completed':>9} {'Gap':>6} {'Coverage':>10}")
    lines.append("-" * 70)
    for r in results:
        cov = f"{r['completed_count'] / total * 100:.1f}%" if total else "N/A"
        lines.append(
            f"{r['config']:<35} {r['completed_count']:>9} {r['gap_count']:>6} {cov:>10}"
        )
    lines.append("-" * 70)
    lines.append(f"{'Total selected tasks':<35} {total:>9}")
    return "\n".join(lines)


def write_subset(
    gap_tasks: list[dict],
    harness: str,
    config: str,
    output_path: Path,
) -> None:
    """Write gap tasks as a subset JSON file."""
    subset = {
        "description": f"{harness} gap fill: {config} missing tasks",
        "generated": date.today().isoformat(),
        "harness": harness,
        "config": config,
        "gap_count": len(gap_tasks),
        "tasks": sorted(gap_tasks, key=lambda x: (x.get("benchmark", ""), x.get("task_id", ""))),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(subset, indent=2))
    print(f"Wrote {len(gap_tasks)} gap tasks to {output_path}", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compute coverage gaps for a harness/config combination.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--harness", "-H",
        default="claude-code",
        help="Harness name: openhands, claude-code, cursor, etc. (default: claude-code)",
    )
    parser.add_argument(
        "--config", "-c",
        default=None,
        help=(
            "Config filter: baseline, baseline-local-direct, mcp-remote-direct, etc. "
            "If omitted, shows summary for all configs."
        ),
    )
    parser.add_argument(
        "--output", "-o",
        choices=["json", "table"],
        default="json",
        help="Output format (default: json)",
    )
    parser.add_argument(
        "--generate-subset",
        metavar="PATH",
        default=None,
        help=(
            "Write gap tasks as a subset JSON file to PATH. "
            "Requires --config to be specified."
        ),
    )
    parser.add_argument(
        "--selected-tasks",
        default=str(DEFAULT_SELECTED_TASKS),
        help=f"Path to selected_benchmark_tasks.json (default: {DEFAULT_SELECTED_TASKS})",
    )
    parser.add_argument(
        "--manifest",
        default=str(DEFAULT_MANIFEST),
        help=f"Path to MANIFEST.json (default: {DEFAULT_MANIFEST})",
    )
    parser.add_argument(
        "--list-harnesses",
        action="store_true",
        help="List all harnesses available in the manifest and exit.",
    )
    parser.add_argument(
        "--list-configs",
        action="store_true",
        help="List all configs available for the specified harness and exit.",
    )

    args = parser.parse_args()

    # Load data
    selected_tasks_path = Path(args.selected_tasks)
    manifest_path = Path(args.manifest)

    if not selected_tasks_path.exists():
        print(f"ERROR: selected tasks file not found: {selected_tasks_path}", file=sys.stderr)
        sys.exit(1)
    if not manifest_path.exists():
        print(f"ERROR: manifest not found: {manifest_path}", file=sys.stderr)
        sys.exit(1)

    selected_tasks = load_selected_tasks(selected_tasks_path)
    run_history = load_run_history(manifest_path)

    # --list-harnesses
    if args.list_harnesses:
        harnesses: set[str] = set()
        for key in run_history:
            parts = key.split("/", 1)
            if parts:
                first = parts[0]
                if is_suite_key(first):
                    harnesses.add("claude-code")
                else:
                    harnesses.add(first)
        for h in sorted(harnesses):
            print(h)
        return

    # --list-configs
    if args.list_configs:
        configs = get_harness_configs(run_history, args.harness)
        for c in configs:
            print(c)
        return

    total = len(selected_tasks)
    task_by_id = {t["task_id"]: t for t in selected_tasks}

    if args.config is None:
        # Show summary for all configs
        configs = get_harness_configs(run_history, args.harness)
        if not configs:
            print(
                f"ERROR: no data found for harness '{args.harness}'. "
                f"Use --list-harnesses to see available harnesses.",
                file=sys.stderr,
            )
            sys.exit(1)

        results = []
        for config in configs:
            completed = get_completed_tasks(run_history, args.harness, config)
            gap_tasks, benchmark_counts = compute_gap(selected_tasks, completed)
            results.append({
                "harness": args.harness,
                "config": config,
                "total_tasks": total,
                "completed_count": len(completed & set(task_by_id.keys())),
                "gap_count": len(gap_tasks),
                "coverage_pct": round(len(completed & set(task_by_id.keys())) / total * 100, 1) if total else 0.0,
                "gap_by_benchmark": benchmark_counts,
            })

        if args.output == "json":
            print(json.dumps({"harness": args.harness, "total_tasks": total, "configs": results}, indent=2))
        else:
            print(format_multi_config_table(args.harness, results, total))
        return

    # Single config mode
    config = args.config
    completed = get_completed_tasks(run_history, args.harness, config)
    gap_tasks, benchmark_counts = compute_gap(selected_tasks, completed)

    # completed_count: intersection with selected tasks (not ALL runs, just selected ones)
    selected_ids = set(task_by_id.keys())
    completed_count = len(completed & selected_ids)

    result = {
        "harness": args.harness,
        "config": config,
        "total_tasks": total,
        "completed_count": completed_count,
        "gap_count": len(gap_tasks),
        "coverage_pct": round(completed_count / total * 100, 1) if total else 0.0,
        "gap_by_benchmark": benchmark_counts,
        "gap_tasks": [t["task_id"] for t in sorted(gap_tasks, key=lambda x: (x.get("benchmark", ""), x.get("task_id", "")))],
    }

    if args.output == "json":
        print(json.dumps(result, indent=2))
    else:
        print(format_table(args.harness, config, total, completed_count, gap_tasks, benchmark_counts))

    if args.generate_subset:
        if not gap_tasks:
            print("No gap tasks — subset file not written.", file=sys.stderr)
        else:
            write_subset(gap_tasks, args.harness, config, Path(args.generate_subset))


if __name__ == "__main__":
    main()
