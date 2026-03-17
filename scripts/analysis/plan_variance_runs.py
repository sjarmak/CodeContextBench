#!/usr/bin/env python3
"""Analyze run coverage gaps and generate targeted selection files for variance runs.

Reads MANIFEST.json run_history and selected_benchmark_tasks.json to identify
tasks below the target run count (default: 3) for each config, then generates
selection files and run commands for each needed wave.

Usage:
    python3 scripts/plan_variance_runs.py [--target N] [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = PROJECT_ROOT / "runs" / "official" / "MANIFEST.json"
SELECTION_PATH = PROJECT_ROOT / "configs" / "selected_benchmark_tasks.json"

SDLC_SUITES = {
    "csb_sdlc_feature", "csb_sdlc_refactor", "csb_sdlc_debug", "csb_sdlc_design", "csb_sdlc_document",
    "csb_sdlc_fix", "csb_sdlc_secure", "csb_sdlc_test", "csb_sdlc_understand",
    # Legacy names for backward compatibility
    "ccb_feature", "ccb_refactor", "ccb_debug", "ccb_design", "ccb_document",
    "ccb_fix", "ccb_secure", "ccb_test", "ccb_understand",
}

# Old config names map to new canonical names
BL_CONFIGS = {"baseline", "baseline-local-direct"}
MCP_CONFIGS = {"mcp", "mcp-remote-direct"}
BL_ARTIFACT_CONFIGS = {"baseline-local-artifact"}
MCP_ARTIFACT_CONFIGS = {"mcp-remote-artifact"}


def load_run_counts(manifest: dict) -> dict[tuple[str, str], dict[str, int]]:
    """Return {(suite, task_name_lower): {"bl": N, "mcp": N}} from run_history.

    Merges old and new config names. For artifact-mode tasks, merges
    artifact configs into the bl/mcp counts.
    """
    rh = manifest.get("run_history", {})
    counts: dict[tuple[str, str], dict[str, int]] = defaultdict(lambda: {"bl": 0, "mcp": 0})

    for key, tasks_data in rh.items():
        parts = key.split("/")
        if len(parts) != 2:
            continue
        suite, config = parts

        is_bl = config in BL_CONFIGS or config in BL_ARTIFACT_CONFIGS
        is_mcp = config in MCP_CONFIGS or config in MCP_ARTIFACT_CONFIGS

        if not is_bl and not is_mcp:
            continue

        for task_name, info in tasks_data.items():
            n = info.get("n_runs", 0)
            key_tuple = (suite, task_name.lower())
            if is_bl:
                counts[key_tuple]["bl"] += n
            else:
                counts[key_tuple]["mcp"] += n

    return dict(counts)


def load_selected_tasks(path: Path) -> list[dict]:
    """Load selected_benchmark_tasks.json and normalize."""
    data = json.loads(path.read_text())
    return data.get("tasks", [])


def analyze_gaps(
    selected_tasks: list[dict],
    run_counts: dict[tuple[str, str], dict[str, int]],
    target: int,
) -> list[dict]:
    """For each selected task, compute the deficit for bl and mcp configs."""
    gaps = []
    for task in selected_tasks:
        suite = task.get("benchmark") or task.get("mcp_suite", "")
        task_id = task.get("task_id", "")
        task_dir = task.get("task_dir", "")
        if not suite or not task_id:
            continue

        key = (suite, task_id.lower())
        current = run_counts.get(key, {"bl": 0, "mcp": 0})

        bl_deficit = max(0, target - current["bl"])
        mcp_deficit = max(0, target - current["mcp"])

        if bl_deficit > 0 or mcp_deficit > 0:
            gaps.append({
                "suite": suite,
                "task_id": task_id,
                "task_dir": task_dir,
                "is_sdlc": suite in SDLC_SUITES,
                "is_mcp_unique": "mcp_suite" in task and "benchmark" not in task,
                "bl_current": current["bl"],
                "mcp_current": current["mcp"],
                "bl_deficit": bl_deficit,
                "mcp_deficit": mcp_deficit,
                # Preserve original task entry for selection file generation
                "_orig": task,
            })

    return gaps


def generate_wave_selection(
    gaps: list[dict],
    wave: int,
    mode: str,  # "both", "baseline-only", "full-only"
) -> list[dict]:
    """Generate a selection file task list for a specific wave and mode.

    wave=1 means "tasks needing at least 1 more run" (i.e., deficit >= 1).
    mode filters which tasks to include based on their config deficit.
    """
    tasks = []
    for g in gaps:
        include = False
        if mode == "both":
            include = g["bl_deficit"] >= wave and g["mcp_deficit"] >= wave
        elif mode == "baseline-only":
            include = g["bl_deficit"] >= wave and g["mcp_deficit"] < wave
        elif mode == "full-only":
            include = g["mcp_deficit"] >= wave and g["bl_deficit"] < wave

        if include:
            tasks.append(g["_orig"])
    return tasks


def write_selection_file(tasks: list[dict], path: Path) -> None:
    """Write a selection file in the standard format."""
    data = {"tasks": tasks}
    path.write_text(json.dumps(data, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description="Plan variance rerun batches")
    parser.add_argument("--target", type=int, default=3, help="Target runs per config (default: 3)")
    parser.add_argument("--dry-run", action="store_true", help="Print plan without writing files")
    args = parser.parse_args()

    target = args.target

    if not MANIFEST_PATH.exists():
        print(f"ERROR: MANIFEST not found at {MANIFEST_PATH}", file=sys.stderr)
        sys.exit(1)

    manifest = json.loads(MANIFEST_PATH.read_text())
    run_counts = load_run_counts(manifest)
    selected_tasks = load_selected_tasks(SELECTION_PATH)

    print(f"Target: {target} runs per config")
    print(f"Selected tasks: {len(selected_tasks)}")
    print()

    gaps = analyze_gaps(selected_tasks, run_counts, target)

    if not gaps:
        print("All tasks already at target. Nothing to do.")
        return

    # Summarize
    sdlc_gaps = [g for g in gaps if g["is_sdlc"]]
    mcp_gaps = [g for g in gaps if not g["is_sdlc"]]

    print(f"Tasks below target: {len(gaps)} ({len(sdlc_gaps)} SDLC, {len(mcp_gaps)} MCP-unique)")
    print()

    # Distribution of deficits
    bl_deficit_dist = defaultdict(int)
    mcp_deficit_dist = defaultdict(int)
    for g in gaps:
        bl_deficit_dist[g["bl_deficit"]] += 1
        mcp_deficit_dist[g["mcp_deficit"]] += 1

    print("Baseline deficit distribution:")
    for d in sorted(bl_deficit_dist):
        print(f"  need {d} more: {bl_deficit_dist[d]} tasks")
    print("MCP deficit distribution:")
    for d in sorted(mcp_deficit_dist):
        print(f"  need {d} more: {mcp_deficit_dist[d]} tasks")
    print()

    # Per-suite summary
    suite_summary = defaultdict(lambda: {"bl_runs": 0, "mcp_runs": 0, "count": 0})
    for g in gaps:
        s = suite_summary[g["suite"]]
        s["count"] += 1
        s["bl_runs"] += g["bl_deficit"]
        s["mcp_runs"] += g["mcp_deficit"]

    print(f"{'Suite':<30} {'Tasks':>5} {'BL runs':>8} {'MCP runs':>9} {'Total':>6}")
    print("-" * 60)
    total_bl = total_mcp = total_tasks = 0
    for suite in sorted(suite_summary):
        s = suite_summary[suite]
        total = s["bl_runs"] + s["mcp_runs"]
        print(f"{suite:<30} {s['count']:>5} {s['bl_runs']:>8} {s['mcp_runs']:>9} {total:>6}")
        total_bl += s["bl_runs"]
        total_mcp += s["mcp_runs"]
        total_tasks += s["count"]
    print("-" * 60)
    print(f"{'TOTAL':<30} {total_tasks:>5} {total_bl:>8} {total_mcp:>9} {total_bl + total_mcp:>6}")
    print()

    # Generate wave plan
    # Strategy: run up to `target` waves. Each wave adds 1 run.
    # Within each wave, split into: both configs, baseline-only, mcp-only
    waves = []
    for wave_num in range(1, target + 1):
        both_tasks = generate_wave_selection(gaps, wave_num, "both")
        bl_only_tasks = generate_wave_selection(gaps, wave_num, "baseline-only")
        mcp_only_tasks = generate_wave_selection(gaps, wave_num, "full-only")

        if not both_tasks and not bl_only_tasks and not mcp_only_tasks:
            break

        waves.append({
            "wave": wave_num,
            "both": both_tasks,
            "baseline_only": bl_only_tasks,
            "mcp_only": mcp_only_tasks,
        })

    print(f"=== RUN PLAN ({len(waves)} waves) ===")
    print()

    output_dir = PROJECT_ROOT / "configs" / "variance_reruns"
    if not args.dry_run:
        output_dir.mkdir(exist_ok=True)

    all_commands = []

    for w in waves:
        wave_num = w["wave"]
        print(f"--- Wave {wave_num} ---")

        for mode, key, flag in [
            ("both configs", "both", ""),
            ("baseline-only", "baseline_only", "--baseline-only"),
            ("mcp-only", "mcp_only", "--full-only"),
        ]:
            tasks = w[key]
            if not tasks:
                continue

            # Count runs this wave adds
            agent_runs = len(tasks) * (2 if key == "both" else 1)
            filename = f"wave{wave_num}_{key}.json"
            filepath = output_dir / filename

            print(f"  {mode}: {len(tasks)} tasks ({agent_runs} agent runs)")
            print(f"    File: configs/variance_reruns/{filename}")

            if not args.dry_run:
                write_selection_file(tasks, filepath)

            cmd = (
                f"./configs/harnesses/run_selected_tasks.sh "
                f"--selection-file configs/variance_reruns/{filename} "
                f"--category staging"
            )
            if flag:
                cmd += f" {flag}"

            print(f"    Run:  {cmd}")
            all_commands.append(cmd)

        print()

    # Print sequential execution plan
    print("=== EXECUTION PLAN (copy-paste) ===")
    print()
    for i, cmd in enumerate(all_commands, 1):
        print(f"# Step {i}")
        print(cmd)
        print()

    if args.dry_run:
        print("[DRY RUN] No files written. Remove --dry-run to generate selection files.")
    else:
        print(f"Selection files written to: {output_dir}/")
        print(f"Total files: {sum(1 for w in waves for k in ['both','baseline_only','mcp_only'] if w[k])}")


if __name__ == "__main__":
    main()
