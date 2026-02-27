#!/usr/bin/env python3
"""Compute bootstrap confidence intervals for all white paper results.

Reads MANIFEST.json, pairs baseline/MCP tasks, computes 10K-resample
bootstrap CIs on paired deltas. Outputs formatted tables for the white paper.

Usage:
    python3 scripts/compute_bootstrap_cis.py
    python3 scripts/compute_bootstrap_cis.py --n-bootstrap 10000
"""

import json
import random
import sys
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = PROJECT_ROOT / "runs" / "official" / "MANIFEST.json"

# SDLC suites (170 tasks across 8 suites)
SDLC_SUITES = [
    "ccb_build", "ccb_debug", "ccb_design", "ccb_document",
    "ccb_fix", "ccb_secure", "ccb_test", "ccb_understand",
]

# MCP-unique suites (81 tasks across 11 suites)
MCP_UNIQUE_SUITES = [
    "ccb_mcp_compliance", "ccb_mcp_crossorg", "ccb_mcp_crossrepo",
    "ccb_mcp_crossrepo_tracing", "ccb_mcp_domain", "ccb_mcp_incident",
    "ccb_mcp_migration", "ccb_mcp_onboarding", "ccb_mcp_org",
    "ccb_mcp_platform", "ccb_mcp_security",
]

# Baseline config names (both legacy and new)
BASELINE_CONFIGS = {"baseline", "baseline-local-direct", "baseline-local-artifact"}
# MCP config names (both legacy and new)
MCP_CONFIGS = {"mcp", "mcp-remote-direct", "mcp-remote-artifact"}


def bootstrap_ci(values: list[float], n_bootstrap: int = 10000, ci: float = 0.95):
    """Percentile bootstrap CI for the mean. Seed=42 for reproducibility."""
    if not values:
        return (0.0, 0.0, 0.0)
    mean_val = sum(values) / len(values)
    if len(values) == 1:
        return (mean_val, mean_val, mean_val)

    rng = random.Random(42)
    resamples = []
    for _ in range(n_bootstrap):
        sample = rng.choices(values, k=len(values))
        resamples.append(sum(sample) / len(sample))
    resamples.sort()

    alpha = 1 - ci
    lo_idx = int(alpha / 2 * n_bootstrap)
    hi_idx = int((1 - alpha / 2) * n_bootstrap) - 1
    return (mean_val, resamples[lo_idx], resamples[hi_idx])


def collect_tasks_for_suite(manifest: dict, suite: str) -> tuple[dict, dict]:
    """Collect all baseline and MCP task rewards for a suite.

    Returns (baseline_tasks, mcp_tasks) where each is {task_name: reward}.
    Merges across old/new config names and direct/artifact modes.
    """
    baseline_tasks = {}
    mcp_tasks = {}

    for run_key, run_data in manifest["runs"].items():
        parts = run_key.split("/")
        if len(parts) != 2:
            continue
        run_suite, config = parts
        if run_suite != suite:
            continue

        tasks = run_data.get("tasks", {})
        for task_name, task_info in tasks.items():
            reward = task_info.get("reward", 0.0)
            # Skip errored tasks
            if task_info.get("status") == "errored":
                continue

            if config in BASELINE_CONFIGS:
                # Keep latest (in case of overlap between legacy and new names)
                if task_name not in baseline_tasks:
                    baseline_tasks[task_name] = reward
            elif config in MCP_CONFIGS:
                if task_name not in mcp_tasks:
                    mcp_tasks[task_name] = reward

    return baseline_tasks, mcp_tasks


def compute_paired_delta_ci(
    baseline_tasks: dict, mcp_tasks: dict, n_bootstrap: int = 10000
) -> dict:
    """Compute bootstrap CI on paired deltas."""
    # Find paired tasks
    paired_names = sorted(set(baseline_tasks.keys()) & set(mcp_tasks.keys()))
    if not paired_names:
        return {"n": 0, "baseline_mean": 0, "mcp_mean": 0, "delta": 0,
                "ci_lower": 0, "ci_upper": 0}

    bl_rewards = [baseline_tasks[t] for t in paired_names]
    mcp_rewards = [mcp_tasks[t] for t in paired_names]
    deltas = [mcp_rewards[i] - bl_rewards[i] for i in range(len(paired_names))]

    bl_mean = sum(bl_rewards) / len(bl_rewards)
    mcp_mean = sum(mcp_rewards) / len(mcp_rewards)
    delta_mean, ci_lo, ci_hi = bootstrap_ci(deltas, n_bootstrap=n_bootstrap)

    # Count MCP wins
    mcp_wins = sum(1 for d in deltas if d > 0)

    return {
        "n": len(paired_names),
        "baseline_mean": round(bl_mean, 3),
        "mcp_mean": round(mcp_mean, 3),
        "delta": round(delta_mean, 3),
        "ci_lower": round(ci_lo, 3),
        "ci_upper": round(ci_hi, 3),
        "mcp_wins": mcp_wins,
        "paired_tasks": paired_names,
    }


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-bootstrap", type=int, default=10000,
                        help="Number of bootstrap resamples (default: 10000)")
    parser.add_argument("--json", action="store_true",
                        help="Output raw JSON instead of formatted tables")
    args = parser.parse_args()

    manifest = json.loads(MANIFEST_PATH.read_text())
    n_boot = args.n_bootstrap

    # ---- Per-suite results ----
    all_results = {}
    sdlc_bl = []
    sdlc_mcp = []
    mcp_unique_bl = []
    mcp_unique_mcp = []

    for suite in SDLC_SUITES + MCP_UNIQUE_SUITES:
        bl, mcp = collect_tasks_for_suite(manifest, suite)
        result = compute_paired_delta_ci(bl, mcp, n_bootstrap=n_boot)
        all_results[suite] = result

        # Accumulate for aggregate
        paired = sorted(set(bl.keys()) & set(mcp.keys()))
        if suite in SDLC_SUITES:
            sdlc_bl.extend(bl[t] for t in paired)
            sdlc_mcp.extend(mcp[t] for t in paired)
        else:
            mcp_unique_bl.extend(bl[t] for t in paired)
            mcp_unique_mcp.extend(mcp[t] for t in paired)

    # ---- Aggregate CIs ----
    overall_bl = sdlc_bl + mcp_unique_bl
    overall_mcp = sdlc_mcp + mcp_unique_mcp
    overall_deltas = [overall_mcp[i] - overall_bl[i] for i in range(len(overall_bl))]
    sdlc_deltas = [sdlc_mcp[i] - sdlc_bl[i] for i in range(len(sdlc_bl))]
    mcp_unique_deltas = [mcp_unique_mcp[i] - mcp_unique_bl[i] for i in range(len(mcp_unique_bl))]

    overall_mean, overall_lo, overall_hi = bootstrap_ci(overall_deltas, n_bootstrap=n_boot)
    sdlc_mean, sdlc_lo, sdlc_hi = bootstrap_ci(sdlc_deltas, n_bootstrap=n_boot)
    mcp_u_mean, mcp_u_lo, mcp_u_hi = bootstrap_ci(mcp_unique_deltas, n_bootstrap=n_boot)

    if args.json:
        output = {
            "n_bootstrap": n_boot,
            "overall": {
                "n": len(overall_deltas),
                "baseline_mean": round(sum(overall_bl) / len(overall_bl), 3),
                "mcp_mean": round(sum(overall_mcp) / len(overall_mcp), 3),
                "delta": round(overall_mean, 3),
                "ci_lower": round(overall_lo, 3),
                "ci_upper": round(overall_hi, 3),
            },
            "sdlc_total": {
                "n": len(sdlc_deltas),
                "baseline_mean": round(sum(sdlc_bl) / len(sdlc_bl), 3),
                "mcp_mean": round(sum(sdlc_mcp) / len(sdlc_mcp), 3),
                "delta": round(sdlc_mean, 3),
                "ci_lower": round(sdlc_lo, 3),
                "ci_upper": round(sdlc_hi, 3),
            },
            "mcp_unique_total": {
                "n": len(mcp_unique_deltas),
                "baseline_mean": round(sum(mcp_unique_bl) / len(mcp_unique_bl), 3),
                "mcp_mean": round(sum(mcp_unique_mcp) / len(mcp_unique_mcp), 3),
                "delta": round(mcp_u_mean, 3),
                "ci_lower": round(mcp_u_lo, 3),
                "ci_upper": round(mcp_u_hi, 3),
            },
            "per_suite": all_results,
        }
        # Remove paired_tasks from JSON output for brevity
        for r in output["per_suite"].values():
            r.pop("paired_tasks", None)
        json.dump(output, sys.stdout, indent=2)
        print()
        return

    # ---- Formatted output ----
    print(f"Bootstrap CIs ({n_boot:,} resamples, seed=42, percentile method)")
    print("=" * 80)

    print(f"\n{'AGGREGATE':^80}")
    print("-" * 80)
    print(f"{'Slice':<25} {'n':>4} {'BL Mean':>8} {'MCP Mean':>9} {'Delta':>7} {'95% CI':>20}")
    print("-" * 80)

    def _ci_str(lo, hi):
        return f"[{lo:+.3f}, {hi:+.3f}]"

    def _excludes_zero(lo, hi):
        return lo > 0 or hi < 0

    overall_bl_mean = sum(overall_bl) / len(overall_bl)
    overall_mcp_mean = sum(overall_mcp) / len(overall_mcp)
    sdlc_bl_mean = sum(sdlc_bl) / len(sdlc_bl) if sdlc_bl else 0
    sdlc_mcp_mean = sum(sdlc_mcp) / len(sdlc_mcp) if sdlc_mcp else 0
    mcp_u_bl_mean = sum(mcp_unique_bl) / len(mcp_unique_bl) if mcp_unique_bl else 0
    mcp_u_mcp_mean = sum(mcp_unique_mcp) / len(mcp_unique_mcp) if mcp_unique_mcp else 0

    print(f"{'Overall':<25} {len(overall_deltas):>4} {overall_bl_mean:>8.3f} {overall_mcp_mean:>9.3f} {overall_mean:>+7.3f} {_ci_str(overall_lo, overall_hi):>20} {'*' if _excludes_zero(overall_lo, overall_hi) else ''}")
    print(f"{'SDLC total':<25} {len(sdlc_deltas):>4} {sdlc_bl_mean:>8.3f} {sdlc_mcp_mean:>9.3f} {sdlc_mean:>+7.3f} {_ci_str(sdlc_lo, sdlc_hi):>20} {'*' if _excludes_zero(sdlc_lo, sdlc_hi) else ''}")
    print(f"{'MCP-unique total':<25} {len(mcp_unique_deltas):>4} {mcp_u_bl_mean:>8.3f} {mcp_u_mcp_mean:>9.3f} {mcp_u_mean:>+7.3f} {_ci_str(mcp_u_lo, mcp_u_hi):>20} {'*' if _excludes_zero(mcp_u_lo, mcp_u_hi) else ''}")

    # Per-suite SDLC
    print(f"\n{'SDLC SUITES':^80}")
    print("-" * 80)
    print(f"{'Suite':<25} {'n':>4} {'BL Mean':>8} {'MCP Mean':>9} {'Delta':>7} {'95% CI':>20}")
    print("-" * 80)
    for suite in SDLC_SUITES:
        r = all_results[suite]
        short = suite.replace("ccb_", "")
        sig = "*" if _excludes_zero(r["ci_lower"], r["ci_upper"]) and r["n"] > 1 else ""
        ci = _ci_str(r["ci_lower"], r["ci_upper"]) if r["n"] > 1 else "—"
        print(f"{short:<25} {r['n']:>4} {r['baseline_mean']:>8.3f} {r['mcp_mean']:>9.3f} {r['delta']:>+7.3f} {ci:>20} {sig}")

    # Per-suite MCP-unique
    print(f"\n{'MCP-UNIQUE SUITES':^80}")
    print("-" * 80)
    print(f"{'Suite':<25} {'n':>4} {'BL Mean':>8} {'MCP Mean':>9} {'Delta':>7} {'95% CI':>20}")
    print("-" * 80)
    for suite in MCP_UNIQUE_SUITES:
        r = all_results[suite]
        short = suite.replace("ccb_mcp_", "")
        sig = "*" if _excludes_zero(r["ci_lower"], r["ci_upper"]) and r["n"] > 1 else ""
        ci = _ci_str(r["ci_lower"], r["ci_upper"]) if r["n"] > 1 else "—"
        print(f"{short:<25} {r['n']:>4} {r['baseline_mean']:>8.3f} {r['mcp_mean']:>9.3f} {r['delta']:>+7.3f} {ci:>20} {sig}")

    print()
    print("* = 95% CI excludes zero")
    print()

    # Summary for white paper copy
    print("=" * 80)
    print("WHITE PAPER COPY (markdown tables)")
    print("=" * 80)

    print(f"\nOverall: delta **{overall_mean:+.3f}** (95% CI: [{overall_lo:+.3f}, {overall_hi:+.3f}])")
    print(f"SDLC: delta **{sdlc_mean:+.3f}** (95% CI: [{sdlc_lo:+.3f}, {sdlc_hi:+.3f}])")
    print(f"MCP-unique: delta **{mcp_u_mean:+.3f}** (95% CI: [{mcp_u_lo:+.3f}, {mcp_u_hi:+.3f}])")


if __name__ == "__main__":
    main()
