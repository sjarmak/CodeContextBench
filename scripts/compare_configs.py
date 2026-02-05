#!/usr/bin/env python3
"""Compare benchmark results across agent configurations.

Shows where configs diverge, highlighting tasks where MCP helps or hurts.

Usage:
    # JSON output
    python3 scripts/compare_configs.py --format json

    # Table output
    python3 scripts/compare_configs.py --format table

    # Filter to one suite
    python3 scripts/compare_configs.py --suite ccb_pytorch --format table

    # Show only divergent tasks (some pass, some fail)
    python3 scripts/compare_configs.py --divergent-only --format table
"""

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from aggregate_status import (
    RUNS_DIR, SKIP_PATTERNS, DIR_PREFIX_TO_SUITE, CONFIGS,
    should_skip, detect_suite, _iter_task_dirs, classify_task,
)


def gather_comparison(
    suite_filter: str | None = None,
    timeout_hours: float = 4.0,
) -> dict:
    """Scan all tasks and group results by (suite, task_name) across configs.

    Returns structured comparison data.
    """
    # task_key = (suite, task_name) -> {config: record}
    task_matrix: dict[tuple[str, str], dict[str, dict]] = defaultdict(dict)

    if not RUNS_DIR.exists():
        return _build_comparison({}, suite_filter)

    for run_dir in sorted(RUNS_DIR.iterdir()):
        if not run_dir.is_dir() or should_skip(run_dir.name):
            continue

        suite = detect_suite(run_dir.name)
        if suite is None:
            continue
        if suite_filter and suite != suite_filter:
            continue

        for config in CONFIGS:
            config_path = run_dir / config
            if not config_path.is_dir():
                continue

            for task_dir in _iter_task_dirs(config_path):
                record = classify_task(task_dir, timeout_hours)
                record["suite"] = suite
                record["config"] = config
                key = (suite, record["task_name"])
                # Latest run dir wins (sorted order)
                task_matrix[key][config] = record

    return _build_comparison(task_matrix, suite_filter)


def _status_symbol(status: str) -> str:
    return {
        "completed_pass": "PASS",
        "completed_fail": "FAIL",
        "errored": "ERR",
        "timeout": "TOUT",
        "running": "RUN",
    }.get(status, status)


def _build_comparison(task_matrix, suite_filter) -> dict:
    """Build the comparison output structure."""
    tasks = []
    suite_stats = defaultdict(lambda: {c: {"pass": 0, "fail": 0, "error": 0, "total": 0} for c in CONFIGS})

    for (suite, task_name), configs in sorted(task_matrix.items()):
        row = {
            "suite": suite,
            "task_name": task_name,
            "configs": {},
            "divergent": False,
            "all_pass": True,
            "all_fail": True,
            "baseline_only_fail": False,
            "mcp_only_fail": False,
        }

        statuses = set()
        for config in CONFIGS:
            rec = configs.get(config)
            if rec is None:
                row["configs"][config] = {"status": "missing", "reward": None}
                continue

            status = rec["status"]
            reward = rec.get("reward")
            row["configs"][config] = {
                "status": status,
                "reward": reward,
                "wall_clock_seconds": rec.get("wall_clock_seconds"),
                "error_fingerprint": rec.get("error_fingerprint"),
            }

            is_pass = status == "completed_pass"
            statuses.add("pass" if is_pass else "nonpass")

            if is_pass:
                row["all_fail"] = False
                suite_stats[suite][config]["pass"] += 1
            else:
                row["all_pass"] = False
                if status == "errored":
                    suite_stats[suite][config]["error"] += 1
                else:
                    suite_stats[suite][config]["fail"] += 1
            suite_stats[suite][config]["total"] += 1

        # Determine divergence patterns
        if "pass" in statuses and "nonpass" in statuses:
            row["divergent"] = True

            # Check if baseline is the only one failing
            bl = row["configs"].get("baseline", {})
            sg_base = row["configs"].get("sourcegraph_base", {})
            sg_full = row["configs"].get("sourcegraph_full", {})

            bl_pass = bl.get("status") == "completed_pass"
            sgb_pass = sg_base.get("status") == "completed_pass"
            sgf_pass = sg_full.get("status") == "completed_pass"

            if not bl_pass and (sgb_pass or sgf_pass):
                row["baseline_only_fail"] = True
            if bl_pass and (not sgb_pass or not sgf_pass):
                row["mcp_only_fail"] = True

        tasks.append(row)

    # Compute overall stats per config
    config_totals = {}
    for config in CONFIGS:
        p = sum(s[config]["pass"] for s in suite_stats.values())
        t = sum(s[config]["total"] for s in suite_stats.values())
        config_totals[config] = {
            "pass": p,
            "total": t,
            "pass_rate": round(p / t, 4) if t > 0 else 0.0,
        }

    divergent_tasks = [t for t in tasks if t["divergent"]]
    baseline_only_fails = [t for t in tasks if t["baseline_only_fail"]]
    mcp_only_fails = [t for t in tasks if t["mcp_only_fail"]]

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "config_totals": config_totals,
        "suite_stats": {k: dict(v) for k, v in sorted(suite_stats.items())},
        "summary": {
            "total_tasks": len(tasks),
            "divergent_tasks": len(divergent_tasks),
            "all_pass": sum(1 for t in tasks if t["all_pass"]),
            "all_fail": sum(1 for t in tasks if t["all_fail"]),
            "baseline_only_fail": len(baseline_only_fails),
            "mcp_only_fail": len(mcp_only_fails),
        },
        "tasks": tasks,
    }


def format_comparison_table(data: dict) -> str:
    """Format comparison as ASCII table."""
    lines = []
    lines.append(f"Config Comparison Report  (generated: {data['generated_at']})")
    lines.append("")

    # Config totals
    lines.append("OVERALL:")
    for config in CONFIGS:
        ct = data["config_totals"].get(config, {})
        p = ct.get("pass", 0)
        t = ct.get("total", 0)
        rate = ct.get("pass_rate", 0)
        short = config.replace("sourcegraph_", "SG_")
        lines.append(f"  {short:18s}  {p:>3d}/{t:<3d}  ({rate:.0%})")
    lines.append("")

    # Summary
    s = data["summary"]
    lines.append(f"DIVERGENCE ANALYSIS ({s['total_tasks']} unique tasks):")
    lines.append(f"  All pass:           {s['all_pass']:>4d}")
    lines.append(f"  All fail:           {s['all_fail']:>4d}")
    lines.append(f"  Divergent:          {s['divergent_tasks']:>4d}")
    lines.append(f"  Baseline only fail: {s['baseline_only_fail']:>4d}  (MCP tools help)")
    lines.append(f"  MCP only fail:      {s['mcp_only_fail']:>4d}  (MCP tools hurt)")
    lines.append("")

    # Per-suite breakdown
    suite_stats = data.get("suite_stats", {})
    if suite_stats:
        header = f"{'Suite':25s}"
        for cfg in CONFIGS:
            short = cfg.replace("sourcegraph_", "SG_")
            header += f" | {short:>12s}"
        lines.append(header)
        lines.append("-" * len(header))

        for suite, cfgs in sorted(suite_stats.items()):
            row = f"{suite:25s}"
            for cfg in CONFIGS:
                s = cfgs.get(cfg, {})
                p = s.get("pass", 0)
                t = s.get("total", 0)
                row += f" | {p:>4d}/{t:<4d}   "
            lines.append(row)
        lines.append("")

    # Divergent tasks detail
    divergent = [t for t in data["tasks"] if t["divergent"]]
    if divergent:
        lines.append(f"DIVERGENT TASKS ({len(divergent)}):")
        header = f"  {'Suite':20s}  {'Task':30s}"
        for cfg in CONFIGS:
            short = cfg.replace("sourcegraph_", "SG_")
            header += f"  {short:>10s}"
        header += "  Signal"
        lines.append(header)
        lines.append("  " + "-" * (len(header) - 2))

        for t in divergent:
            row = f"  {t['suite']:20s}  {t['task_name']:30s}"
            for cfg in CONFIGS:
                c = t["configs"].get(cfg, {})
                sym = _status_symbol(c.get("status", "missing"))
                row += f"  {sym:>10s}"
            signal = ""
            if t["baseline_only_fail"]:
                signal = "MCP helps"
            elif t["mcp_only_fail"]:
                signal = "MCP hurts"
            row += f"  {signal}"
            lines.append(row)
        lines.append("")

    # All-fail tasks (potential adapter bugs)
    all_fail = [t for t in data["tasks"] if t["all_fail"]]
    if all_fail:
        lines.append(f"ALL-FAIL TASKS ({len(all_fail)}) — likely task/adapter issues:")
        for t in all_fail:
            configs_str = "  ".join(
                f"{cfg.replace('sourcegraph_', 'SG_')}={_status_symbol(t['configs'].get(cfg, {}).get('status', 'missing'))}"
                for cfg in CONFIGS
            )
            lines.append(f"  {t['suite']:20s}  {t['task_name']:30s}  {configs_str}")

    return "\n".join(lines)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Compare benchmark results across agent configurations."
    )
    parser.add_argument(
        "--format", choices=["json", "table"], default="json",
        help="Output format (default: json)",
    )
    parser.add_argument(
        "--suite", default=None,
        help="Filter to one benchmark suite",
    )
    parser.add_argument(
        "--divergent-only", action="store_true",
        help="Only show tasks where configs diverge",
    )
    parser.add_argument(
        "--timeout-hours", type=float, default=4.0,
        help="Hours before marking as timeout (default: 4)",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    data = gather_comparison(
        suite_filter=args.suite,
        timeout_hours=args.timeout_hours,
    )

    if args.divergent_only:
        data["tasks"] = [t for t in data["tasks"] if t["divergent"]]

    if args.format == "table":
        print(format_comparison_table(data))
    else:
        print(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()
