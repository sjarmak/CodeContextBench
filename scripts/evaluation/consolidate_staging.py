#!/usr/bin/env python3
"""Consolidate staging runs: archive errored tasks, merge targeted reruns.

Operations:
1. Within each completed run dir, move errored task dirs to archive/errored/
2. Merge targeted rerun fragments into their parent run dir (time-range rename).
3. Keep duplicate full runs (identical task sets) separate for variance analysis.
4. Merge split-config runs (one has baseline, other has SG_full) into one dir.
5. Skip any run dir that still has running tasks.

Usage:
    python3 scripts/consolidate_staging.py --dry-run   # preview
    python3 scripts/consolidate_staging.py --execute    # do it
"""

import argparse
import json
import os
import re
import shutil
import subprocess
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
STAGING = REPO_ROOT / "runs" / "staging"


def get_aggregate_data():
    result = subprocess.run(
        ["python3", "scripts/analysis/aggregate_status.py", "--staging"],
        capture_output=True, text=True,
        cwd=str(REPO_ROOT),
    )
    return json.loads(result.stdout)


def parse_timestamp(run_dir_name: str) -> str:
    """Extract YYYYMMDD_HHMMSS from run dir name."""
    m = re.search(r"(\d{8}_\d{6})", run_dir_name)
    return m.group(1) if m else ""


def suite_key(run_dir_name: str) -> str:
    """Extract suite prefix (e.g. 'build', 'debug') from run dir name."""
    m = re.match(r"^(\w+?)_sonnet_", run_dir_name)
    return m.group(1) if m else run_dir_name


def get_task_set(run_dir: str) -> set:
    """Get normalized task names from a run dir (across both configs)."""
    tasks = set()
    for config in ["baseline", "sourcegraph_full"]:
        config_path = STAGING / run_dir / config
        if not config_path.exists():
            continue
        for d in os.listdir(config_path):
            if d.startswith(("ccb_", "csb_")):
                # Normalize: strip config suffix
                norm = re.sub(r"_(baseline|sourcegraph_full)$", "", d)
                tasks.add(norm)
    return tasks


def get_configs_present(run_dir: str) -> set:
    """Which config dirs exist in a run dir."""
    configs = set()
    for config in ["baseline", "sourcegraph_full"]:
        if (STAGING / run_dir / config).exists():
            configs.add(config)
    return configs


def classify_satellite(primary: str, satellite: str) -> str:
    """Classify a satellite run relative to primary.

    Returns:
        'rerun'     - targeted rerun (small fragment, merge into primary)
        'duplicate' - identical task set (keep separate for variance)
        'split'     - complementary configs (merge into one dir)
    """
    p_tasks = get_task_set(primary)
    s_tasks = get_task_set(satellite)
    p_configs = get_configs_present(primary)
    s_configs = get_configs_present(satellite)

    # Explicit rerun in name
    if "rerun" in satellite:
        return "rerun"

    # Complementary configs (one has baseline, other has SG_full)
    if not p_configs & s_configs and p_configs | s_configs == {"baseline", "sourcegraph_full"}:
        return "split"

    # Same task set = duplicate for variance
    if p_tasks == s_tasks:
        return "duplicate"

    # Small fragment targeting specific tasks = rerun
    if len(s_tasks) < len(p_tasks) * 0.5:
        return "rerun"

    # Default: treat as duplicate (safe — keeps data)
    return "duplicate"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--execute", action="store_true")
    args = parser.parse_args()

    data = get_aggregate_data()

    # Build per-task status map
    task_map = {}
    run_has_running = defaultdict(bool)

    for t in data.get("tasks", []):
        td = t.get("task_dir", "")
        rel = td.replace(str(STAGING) + "/", "")
        parts = rel.split("/")
        if len(parts) < 3:
            continue
        run_dir = parts[0]
        config = parts[1]
        ccb_dir = parts[2]
        status = t.get("status", "?")
        task_map[(run_dir, config, ccb_dir)] = status
        if status == "running":
            run_has_running[run_dir] = True

    # ── Step 1: Archive errored tasks ──
    archive_ops = []
    for (run_dir, config, ccb_dir), status in task_map.items():
        if status != "errored":
            continue
        if run_has_running[run_dir]:
            continue

        src = STAGING / run_dir / config / ccb_dir
        dst = STAGING / run_dir / config / "archive" / "errored" / ccb_dir

        if src.exists():
            archive_ops.append(("task_dir", src, dst))
            # Grab matching .log file
            task_short = ccb_dir.replace(f"_{config}", "").replace(
                "ccb_" + suite_key(run_dir) + "_", ""
            )
            log_file = STAGING / run_dir / config / f"{task_short}.log"
            if log_file.exists():
                log_dst = STAGING / run_dir / config / "archive" / "errored" / log_file.name
                archive_ops.append(("log", log_file, log_dst))

    dir_count = len([o for o in archive_ops if o[0] == "task_dir"])
    print(f"=== Step 1: Archive {dir_count} errored task dirs ===")
    for op_type, src, dst in archive_ops:
        label = "DIR " if op_type == "task_dir" else "LOG "
        print(f"  {label} {src.relative_to(STAGING)}")
        print(f"    -> {dst.relative_to(STAGING)}")

    if args.execute:
        for _, src, dst in archive_ops:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
        print(f"  [DONE] Archived {len(archive_ops)} items")

    # ── Step 2: Classify and merge/keep runs per suite ──
    suite_runs = defaultdict(list)
    for run_dir in sorted(os.listdir(STAGING)):
        if run_dir == "archive" or not (STAGING / run_dir).is_dir():
            continue
        suite_runs[suite_key(run_dir)].append(run_dir)

    print(f"\n=== Step 2: Merge targeted reruns & splits (keep duplicates) ===")
    merge_ops = []

    for suite, runs in sorted(suite_runs.items()):
        completed = [r for r in runs if not run_has_running[r]]
        active = [r for r in runs if run_has_running[r]]

        if len(completed) <= 1:
            if active:
                print(f"\n  {suite}: {len(completed)} completed, {len(active)} active — nothing to merge yet")
            continue

        # Sort by timestamp; primary = earliest full run
        by_ts = sorted(completed, key=parse_timestamp)
        primary = by_ts[0]
        satellites = by_ts[1:]

        # Classify each satellite
        to_merge = []  # (run_dir, classification)
        to_keep = []
        for sat in satellites:
            cls = classify_satellite(primary, sat)
            if cls in ("rerun", "split"):
                to_merge.append((sat, cls))
            else:
                to_keep.append((sat, cls))

        if not to_merge:
            print(f"\n  {suite}: {len(to_keep)} duplicate runs kept for variance, nothing to merge")
            continue

        # Compute time range for rename
        merge_timestamps = [parse_timestamp(primary)] + [parse_timestamp(s) for s, _ in to_merge]
        earliest = min(merge_timestamps)
        latest = max(merge_timestamps)
        new_name = f"{suite}_sonnet_{earliest}_to_{latest}" if earliest != latest else None

        print(f"\n  {suite}:")
        print(f"    Primary: {primary}")
        for sat, cls in to_merge:
            print(f"    Merge ({cls}): {sat}")
        for sat, cls in to_keep:
            print(f"    Keep ({cls}): {sat}")
        if active:
            print(f"    Skip (active): {', '.join(active)}")
        if new_name:
            print(f"    Rename primary to: {new_name}")

        # Build merge ops
        for sat, cls in to_merge:
            sat_path = STAGING / sat
            for config in ["baseline", "sourcegraph_full"]:
                config_path = sat_path / config
                if not config_path.exists():
                    continue
                # Ensure target config dir exists in primary
                primary_config = STAGING / primary / config

                for item in sorted(os.listdir(config_path)):
                    if item == "archive":
                        continue
                    src = config_path / item
                    dst = primary_config / item
                    if dst.exists():
                        # For reruns: newer replaces older (the rerun is the fix)
                        merge_ops.append(("replace", src, dst, sat))
                    else:
                        merge_ops.append(("move", src, dst, sat))

            merge_ops.append(("rmdir", sat_path, None, sat))

        if new_name:
            merge_ops.append(("rename", STAGING / primary, STAGING / new_name, primary))

        # Print details
        for op, src, dst, sat in merge_ops:
            if op in ("move", "replace") and sat in [s for s, _ in to_merge]:
                print(f"    {op}: {src.name}")

    print(f"\n  Total merge operations: {len(merge_ops)}")

    if args.execute:
        for op, src, dst, info in merge_ops:
            if op in ("move", "replace"):
                if dst.exists() and op == "replace":
                    archive_dst = dst.parent / "archive" / "superseded" / dst.name
                    archive_dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(dst), str(archive_dst))
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(src), str(dst))
            elif op == "rmdir":
                try:
                    shutil.rmtree(str(src))
                except Exception as e:
                    print(f"  [WARN] Could not remove {src}: {e}")
            elif op == "rename":
                if src.exists() and not dst.exists():
                    shutil.move(str(src), str(dst))
        print("  [DONE] Merge complete")

    # ── Summary ──
    print(f"\n=== Summary ===")
    print(f"  Errored tasks archived: {dir_count}")
    print(f"  Fragment runs merged: {len([o for o in merge_ops if o[0] == 'rmdir'])}")
    print(f"  Duplicate runs kept for variance: {sum(1 for s, runs in suite_runs.items() for _ in runs) - dir_count}")
    print(f"  Active runs untouched: {sum(1 for v in run_has_running.values() if v)}")


if __name__ == "__main__":
    main()
