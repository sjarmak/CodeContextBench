#!/usr/bin/env python3
"""Per-task variance gap analysis for SDLC suites.

Scans MANIFEST.json + staging runs to find which individual SDLC tasks already
have 3+ valid paired runs (baseline + MCP), which have partial coverage, and
which have zero. Outputs targeted rerun configs containing ONLY the tasks that
need more passes.

Usage:
    python3 scripts/variance_gap_analysis.py
    python3 scripts/variance_gap_analysis.py --target 3 --output-configs
    python3 scripts/variance_gap_analysis.py --json
"""

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = PROJECT_ROOT / "runs" / "official" / "MANIFEST.json"
STAGING_DIR = PROJECT_ROOT / "runs" / "staging"
SELECTION_FILE = PROJECT_ROOT / "configs" / "selected_benchmark_tasks.json"

SDLC_SUITES = [
    "csb_sdlc_feature", "csb_sdlc_refactor", "csb_sdlc_debug", "csb_sdlc_design", "csb_sdlc_document",
    "csb_sdlc_fix", "csb_sdlc_secure", "csb_sdlc_test", "csb_sdlc_understand",
]

BL_CONFIGS = {"baseline", "baseline-local-direct", "baseline-local-artifact"}
MCP_CONFIGS = {"mcp", "mcp-remote-direct", "mcp-remote-artifact"}


def normalize_task_name(name: str) -> str:
    """Strip prefixes and Harbor random suffix from task names."""
    for pfx in ("sgonly_", "mcp_", "bl_"):
        if name.startswith(pfx):
            name = name[len(pfx):]
    name = re.sub(r"_[a-z0-9]{4,8}$", "", name)
    return name


def load_active_sdlc_tasks() -> dict:
    """Load active SDLC task_ids from selection file. Returns {task_id: benchmark}."""
    sel = json.loads(SELECTION_FILE.read_text())
    active = {}
    for t in sel["tasks"]:
        bm = t.get("benchmark", "")
        if bm in SDLC_SUITES:
            active[t["task_id"]] = bm
    return active


def collect_manifest_runs(active_tasks: dict) -> tuple:
    """Collect per-task run data from MANIFEST.json.

    Returns (task_bl_runs, task_mcp_runs) where each is {task_id: [reward, ...]}.
    """
    manifest = json.loads(MANIFEST_PATH.read_text())
    rh = manifest.get("run_history", {})

    task_bl = defaultdict(list)
    task_mcp = defaultdict(list)

    for run_key, tasks in rh.items():
        parts = run_key.split("/")
        if len(parts) != 2:
            continue
        suite, config = parts

        if config in BL_CONFIGS:
            config_type = "baseline"
        elif config in MCP_CONFIGS:
            config_type = "mcp"
        else:
            continue

        for task_name, task_info in tasks.items():
            tn = normalize_task_name(task_name)
            if tn not in active_tasks:
                continue

            runs = task_info.get("runs", [])
            valid = [r["reward"] for r in runs
                     if r.get("reward") is not None and r.get("status") != "errored"]

            if config_type == "baseline":
                task_bl[tn].extend(valid)
            else:
                task_mcp[tn].extend(valid)

    return task_bl, task_mcp


def scan_staging_runs(active_tasks: dict) -> tuple:
    """Scan runs/staging/ for additional task-level results not yet in MANIFEST.

    Returns (task_bl_runs, task_mcp_runs) same shape as collect_manifest_runs.
    """
    task_bl = defaultdict(list)
    task_mcp = defaultdict(list)

    if not STAGING_DIR.is_dir():
        return task_bl, task_mcp

    sdlc_set = set(SDLC_SUITES)
    for batch_dir in sorted(STAGING_DIR.iterdir()):
        if not batch_dir.is_dir():
            continue
        m = re.match(r"((?:csb_|ccb_)\w+?)_(?:haiku|sonnet|opus)_\d{8}_\d{6}", batch_dir.name)
        if not m:
            continue
        suite = m.group(1)
        if suite not in sdlc_set:
            continue

        for config_dir in batch_dir.iterdir():
            if not config_dir.is_dir():
                continue
            cname = config_dir.name
            if cname in BL_CONFIGS or cname.startswith("baseline"):
                ct = "baseline"
            elif cname in MCP_CONFIGS or cname.startswith("mcp"):
                ct = "mcp"
            else:
                continue

            for rj in config_dir.rglob("result.json"):
                try:
                    rdata = json.loads(rj.read_text())
                except Exception:
                    continue
                if "stats" in rdata:
                    continue  # batch-level

                task_name = rdata.get("task_name", "")
                if not task_name:
                    continue

                tn = normalize_task_name(task_name)
                if tn not in active_tasks:
                    continue

                vr = rdata.get("verifier_result") or {}
                rewards = vr.get("rewards") or {}
                reward = rewards.get("reward")
                if reward is not None:
                    if ct == "baseline":
                        task_bl[tn].append(reward)
                    else:
                        task_mcp[tn].append(reward)

    return task_bl, task_mcp


def merge_runs(*pairs) -> tuple:
    """Merge multiple (bl_dict, mcp_dict) pairs, deduplicating by value."""
    merged_bl = defaultdict(list)
    merged_mcp = defaultdict(list)
    for bl, mcp in pairs:
        for k, v in bl.items():
            merged_bl[k].extend(v)
        for k, v in mcp.items():
            merged_mcp[k].extend(v)
    return merged_bl, merged_mcp


def build_gap_analysis(active_tasks: dict, task_bl: dict, task_mcp: dict,
                       target: int = 3) -> dict:
    """Build per-task gap analysis.

    Returns dict with 'full' and 'gap' lists per suite, plus summary stats.
    """
    gap_tasks = defaultdict(list)
    full_tasks = defaultdict(list)
    suite_counts = defaultdict(int)

    for tid in sorted(active_tasks.keys()):
        bm = active_tasks[tid]
        suite_counts[bm] += 1
        bl = len(task_bl.get(tid, []))
        mc = len(task_mcp.get(tid, []))
        paired = min(bl, mc)
        entry = {
            "task_id": tid,
            "benchmark": bm,
            "bl_runs": bl,
            "mcp_runs": mc,
            "paired": paired,
            "need": max(0, target - paired),
            "bl_rewards": task_bl.get(tid, []),
            "mcp_rewards": task_mcp.get(tid, []),
        }

        if paired >= target:
            full_tasks[bm].append(entry)
        else:
            gap_tasks[bm].append(entry)

    return {
        "active_tasks": len(active_tasks),
        "suite_counts": dict(suite_counts),
        "target": target,
        "full_tasks": dict(full_tasks),
        "gap_tasks": dict(gap_tasks),
    }


def print_report(analysis: dict):
    """Print formatted gap analysis report."""
    target = analysis["target"]
    gap = analysis["gap_tasks"]
    full = analysis["full_tasks"]
    suite_counts = analysis["suite_counts"]

    print(f"Per-Task Variance Gap Analysis")
    print(f"  Active SDLC tasks: {analysis['active_tasks']}")
    print(f"  Target: {target} paired passes (baseline + MCP) per task")
    print(f"=" * 80)

    # Summary table
    header = f"  {'Suite':<20} {'Total':>5} {'>=3 pair':>8} {'<3 pair':>8} {'Zero':>5}"
    print(header)
    print("  " + "-" * 50)

    total_full = total_gap = total_zero = 0
    for s in sorted(SDLC_SUITES):
        n_full = len(full.get(s, []))
        gap_list = gap.get(s, [])
        n_gap = len(gap_list)
        n_zero = sum(1 for t in gap_list if t["paired"] == 0)
        total = suite_counts.get(s, 0)
        total_full += n_full
        total_gap += n_gap
        total_zero += n_zero
        print(f"  {s:<20} {total:>5} {n_full:>8} {n_gap:>8} {n_zero:>5}")

    print("  " + "-" * 50)
    print(f"  {'TOTAL':<20} {analysis['active_tasks']:>5} {total_full:>8} {total_gap:>8} {total_zero:>5}")

    # Detailed gap list
    print(f"\n{'=' * 80}")
    print(f"TASKS NEEDING MORE RUNS (< {target} paired passes)")
    print(f"{'=' * 80}")

    total_reruns_needed = 0
    for s in sorted(SDLC_SUITES):
        tasks = gap.get(s, [])
        if not tasks:
            continue
        print(f"\n--- {s} ({len(tasks)} tasks) ---")
        for t in sorted(tasks, key=lambda x: x["paired"]):
            need = t["need"]
            total_reruns_needed += need
            bl_str = ",".join(f"{r:.2f}" for r in t["bl_rewards"]) or "-"
            mcp_str = ",".join(f"{r:.2f}" for r in t["mcp_rewards"]) or "-"
            print(f"  {t['task_id']:<55} "
                  f"BL={t['bl_runs']} MCP={t['mcp_runs']} "
                  f"paired={t['paired']} need={need}")
            if t["bl_rewards"] or t["mcp_rewards"]:
                print(f"    BL rewards: [{bl_str}]  MCP rewards: [{mcp_str}]")

    # Summary stats
    gap_count = sum(len(v) for v in gap.values())
    print(f"\n{'=' * 80}")
    print(f"SUMMARY")
    print(f"  Tasks with full coverage:    {total_full}")
    print(f"  Tasks needing more runs:     {gap_count}")
    print(f"  Total additional paired runs needed: {total_reruns_needed}")
    print(f"  (That's {total_reruns_needed * 2} individual harbor runs = "
          f"{total_reruns_needed} baseline + {total_reruns_needed} MCP)")

    # Per-suite rerun costs
    print(f"\n  Per-suite rerun breakdown:")
    for s in sorted(SDLC_SUITES):
        tasks = gap.get(s, [])
        if not tasks:
            print(f"    {s:<20} DONE (all {len(full.get(s, []))} tasks at {target}+ pairs)")
            continue
        needs = sum(t["need"] for t in tasks)
        print(f"    {s:<20} {len(tasks)} tasks, {needs} additional pairs needed")


def generate_rerun_configs(analysis: dict, output_dir: Path):
    """Generate targeted rerun config JSON files per suite."""
    gap = analysis["gap_tasks"]
    target = analysis["target"]
    sel = json.loads(SELECTION_FILE.read_text())

    # Build task lookup from selection file
    task_lookup = {}
    for t in sel["tasks"]:
        task_lookup[t["task_id"]] = t

    for suite in sorted(SDLC_SUITES):
        tasks = gap.get(suite, [])
        if not tasks:
            continue

        # Max concurrency needed = max(need) across tasks
        max_need = max(t["need"] for t in tasks)

        config = {
            "metadata": {
                "title": f"Variance rerun: {suite} gap tasks ({len(tasks)} tasks, target {target} pairs)",
                "description": f"Targeted rerun for {suite} tasks with < {target} paired passes. "
                               f"Generated by variance_gap_analysis.py.",
                "generated_date": "2026-03-01",
                "total_tasks": len(tasks),
                "max_concurrency_needed": max_need,
                "note": f"Run with --concurrency {max_need} to fill all gaps in one batch. "
                        f"Or run with --concurrency 1 multiple times.",
            },
            "methodology": {
                "sdlc_suites": [suite],
            },
            "statistics": {
                "total_tasks": len(tasks),
                "per_suite": {suite: len(tasks)},
            },
            "tasks": [],
        }

        for t in sorted(tasks, key=lambda x: x["task_id"]):
            # Get full task metadata from selection file
            full_task = task_lookup.get(t["task_id"], {})
            task_entry = {
                "task_id": t["task_id"],
                "benchmark": suite,
                "task_dir": full_task.get("task_dir", f"{suite}/{t['task_id']}"),
                "language": full_task.get("language", "unknown"),
                "difficulty": full_task.get("difficulty", "unknown"),
                "current_bl_runs": t["bl_runs"],
                "current_mcp_runs": t["mcp_runs"],
                "current_paired": t["paired"],
                "runs_needed": t["need"],
            }
            # Copy optional fields
            for field in ("sdlc_phase", "category", "repo", "mcp_benefit_score"):
                if field in full_task:
                    task_entry[field] = full_task[field]
            config["tasks"].append(task_entry)

        out_path = output_dir / f"variance_gap_{suite}.json"
        out_path.write_text(json.dumps(config, indent=2) + "\n")
        print(f"  Written: {out_path.relative_to(PROJECT_ROOT)} ({len(tasks)} tasks)")

    # Also generate a combined "all gaps" config
    all_gap_tasks = []
    for suite in sorted(SDLC_SUITES):
        tasks = gap.get(suite, [])
        for t in tasks:
            full_task = task_lookup.get(t["task_id"], {})
            task_entry = {
                "task_id": t["task_id"],
                "benchmark": suite,
                "task_dir": full_task.get("task_dir", f"{suite}/{t['task_id']}"),
                "language": full_task.get("language", "unknown"),
                "difficulty": full_task.get("difficulty", "unknown"),
                "current_bl_runs": t["bl_runs"],
                "current_mcp_runs": t["mcp_runs"],
                "current_paired": t["paired"],
                "runs_needed": t["need"],
            }
            for field in ("sdlc_phase", "category", "repo", "mcp_benefit_score"):
                if field in full_task:
                    task_entry[field] = full_task[field]
            all_gap_tasks.append(task_entry)

    if all_gap_tasks:
        combined = {
            "metadata": {
                "title": f"Variance rerun: ALL SDLC gap tasks ({len(all_gap_tasks)} tasks)",
                "description": f"Combined rerun config for all SDLC tasks with < {target} paired passes.",
                "generated_date": "2026-03-01",
                "total_tasks": len(all_gap_tasks),
            },
            "methodology": {
                "sdlc_suites": sorted(set(t["benchmark"] for t in all_gap_tasks)),
            },
            "statistics": {
                "total_tasks": len(all_gap_tasks),
                "per_suite": defaultdict(int),
            },
            "tasks": all_gap_tasks,
        }
        for t in all_gap_tasks:
            combined["statistics"]["per_suite"][t["benchmark"]] += 1
        combined["statistics"]["per_suite"] = dict(combined["statistics"]["per_suite"])

        out_path = output_dir / "variance_gap_all_sdlc.json"
        out_path.write_text(json.dumps(combined, indent=2) + "\n")
        print(f"  Written: {out_path.relative_to(PROJECT_ROOT)} ({len(all_gap_tasks)} tasks)")


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--target", type=int, default=3,
                        help="Target number of paired passes per task (default: 3)")
    parser.add_argument("--include-staging", action="store_true",
                        help="Also scan runs/staging/ for additional results")
    parser.add_argument("--output-configs", action="store_true",
                        help="Generate per-suite rerun config JSON files in configs/variance_reruns/")
    parser.add_argument("--json", action="store_true",
                        help="Output analysis as JSON")
    args = parser.parse_args()

    active_tasks = load_active_sdlc_tasks()
    manifest_bl, manifest_mcp = collect_manifest_runs(active_tasks)

    if args.include_staging:
        staging_bl, staging_mcp = scan_staging_runs(active_tasks)
        task_bl, task_mcp = merge_runs(
            (manifest_bl, manifest_mcp),
            (staging_bl, staging_mcp),
        )
        print(f"(Including staging results)")
    else:
        task_bl, task_mcp = manifest_bl, manifest_mcp

    analysis = build_gap_analysis(active_tasks, task_bl, task_mcp, target=args.target)

    if args.json:
        # Strip reward lists for cleaner output
        output = {k: v for k, v in analysis.items()}
        for category in ("full_tasks", "gap_tasks"):
            cleaned = {}
            for suite, tasks in output[category].items():
                cleaned[suite] = [{k: v for k, v in t.items()
                                   if k not in ("bl_rewards", "mcp_rewards")}
                                  for t in tasks]
            output[category] = cleaned
        json.dump(output, sys.stdout, indent=2)
        print()
    else:
        print_report(analysis)

    if args.output_configs:
        config_dir = PROJECT_ROOT / "configs" / "variance_reruns"
        config_dir.mkdir(exist_ok=True)
        print(f"\nGenerating rerun configs in {config_dir.relative_to(PROJECT_ROOT)}/")
        generate_rerun_configs(analysis, config_dir)


if __name__ == "__main__":
    main()
