#!/usr/bin/env python3
"""Power analysis for CodeScaleBench research questions.

RQ1: MCP vs baseline across SDLC phases (mean reward, pass rate)
RQ2: Per-suite MCP delta heterogeneity
RQ3: IR quality → task outcome correlation (Spearman r)
RQ4: Efficiency trade-offs (tokens, time, TTFR)
RQ5: Org-scale discovery feasibility (org task scores, cross-repo)
"""

import json
import math
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

PROJ_ROOT = Path(__file__).resolve().parent.parent

SUITE_TO_PHASE = {
    "csb_sdlc_understand": "Comprehension", "csb_sdlc_design": "Design",
    "csb_sdlc_document": "Documentation", "csb_sdlc_feature": "Implementation",
    "csb_sdlc_refactor": "Refactoring", "csb_sdlc_fix": "Bug Fix",
    "csb_sdlc_debug": "Debugging", "csb_sdlc_test": "Testing",
    "csb_sdlc_secure": "Security",
    "csb_org_onboarding": "Onboarding", "csb_org_domain": "Domain Knowledge",
    "csb_org_org": "Org Discovery", "csb_org_crossrepo": "Cross-Repo",
    "csb_org_crossrepo_tracing": "Dep Tracing", "csb_org_crossorg": "Cross-Org",
    "csb_org_incident": "Incident Response", "csb_org_security": "Vuln Remediation",
    "csb_org_compliance": "Compliance", "csb_org_migration": "Migration",
    "csb_org_platform": "Platform Knowledge",
}


def section(title):
    print(f"\n{'=' * 90}")
    print(f"  {title}")
    print("=" * 90)


def power_n_paired(sigma_d, delta, alpha=0.05, power=0.80):
    """n for paired t-test."""
    z_a = 1.96 if alpha == 0.05 else 2.58
    z_b = 0.84 if power == 0.80 else 1.28
    return math.ceil(((z_a + z_b) * sigma_d / delta) ** 2)


def power_n_twosample(sigma, delta, alpha=0.05, power=0.80):
    """n per group for independent two-sample t-test."""
    z_a = 1.96 if alpha == 0.05 else 2.58
    z_b = 0.84 if power == 0.80 else 1.28
    return math.ceil(2 * ((z_a + z_b) * sigma / delta) ** 2)


def power_n_correlation(r, alpha=0.05, power=0.80):
    """n for detecting Spearman/Pearson correlation r."""
    z_a = 1.96 if alpha == 0.05 else 2.58
    z_b = 0.84 if power == 0.80 else 1.28
    # Fisher z-transform: n = ((z_a + z_b) / arctanh(r))^2 + 3
    if abs(r) < 0.001:
        return 99999
    return math.ceil(((z_a + z_b) / math.atanh(min(abs(r), 0.99))) ** 2 + 3)


def mde_paired(sigma_d, n, alpha=0.05, power=0.80):
    """Minimum detectable effect for paired test."""
    z_a = 1.96 if alpha == 0.05 else 2.58
    z_b = 0.84 if power == 0.80 else 1.28
    return (z_a + z_b) * sigma_d / math.sqrt(n) if n > 0 else float("inf")


def mde_twosample(sigma, n_per_group, alpha=0.05, power=0.80):
    """MDE for two-sample test."""
    z_a = 1.96 if alpha == 0.05 else 2.58
    z_b = 0.84 if power == 0.80 else 1.28
    return (z_a + z_b) * sigma * math.sqrt(2 / n_per_group) if n_per_group > 0 else float("inf")


def load_all_data():
    """Load official results + IR metrics."""
    with open(PROJ_ROOT / "docs/official_results/data/official_results.json") as f:
        official = json.load(f)

    ir_data = []
    ir_path = PROJ_ROOT / "results/ir/retrieval_metrics_promoted.json"
    if ir_path.is_file():
        with open(ir_path) as f:
            ir_raw = json.load(f)
        pt = ir_raw.get("per_task", [])
        ir_data = pt if isinstance(pt, list) else []

    return official, ir_data


def analyze_rq1(official):
    """RQ1: MCP vs baseline across SDLC phases."""
    section("RQ1: MCP vs Baseline Across SDLC Phases")

    # Build paired task data per suite
    suite_pairs = defaultdict(lambda: defaultdict(lambda: {"bl": [], "mcp": []}))
    for t in official["all_tasks"]:
        reward = t.get("reward")
        if reward is None:
            continue
        bp = t.get("benchmark_path", "")
        suite = bp.split("/")[1] if "/" in bp else "?"
        tid = bp.split("/")[-1]
        config = t.get("config", "")
        key = "mcp" if "mcp" in config else "bl"
        suite_pairs[suite][tid][key].append(reward)

    # Overall paired analysis
    all_diffs = []
    for suite, tasks in suite_pairs.items():
        for tid, cfg in tasks.items():
            if cfg["bl"] and cfg["mcp"]:
                all_diffs.append(np.mean(cfg["mcp"]) - np.mean(cfg["bl"]))

    sigma_d = np.std(all_diffs, ddof=1)
    obs_delta = np.mean(all_diffs)
    n_paired = len(all_diffs)

    print(f"\n  OVERALL (paired within-task):")
    print(f"    Paired tasks: {n_paired}")
    print(f"    Observed Δ(MCP-BL): {obs_delta:+.4f}")
    print(f"    Paired σ_d: {sigma_d:.4f}")
    print(f"    MDE (current n): {mde_paired(sigma_d, n_paired):.4f}")
    print(f"    n needed for observed Δ: {power_n_paired(sigma_d, abs(obs_delta)) if abs(obs_delta) > 0.001 else '>10K'}")
    print(f"    Status: {'POWERED' if abs(obs_delta) > mde_paired(sigma_d, n_paired) else 'UNDERPOWERED'}")

    # Per-suite analysis
    print(f"\n  PER-SUITE BREAKDOWN:")
    print(f"  {'Suite':>35s}  {'Phase':>16s}  {'n':>4s}  {'Δ':>7s}  {'σ_d':>6s}  {'MDE':>7s}  {'Status':>10s}  {'Need':>5s}")
    print("  " + "-" * 100)

    suite_results = {}
    for suite in sorted(suite_pairs.keys()):
        tasks = suite_pairs[suite]
        diffs = []
        for tid, cfg in tasks.items():
            if cfg["bl"] and cfg["mcp"]:
                diffs.append(np.mean(cfg["mcp"]) - np.mean(cfg["bl"]))

        if len(diffs) < 2:
            continue

        n = len(diffs)
        delta = np.mean(diffs)
        sd = np.std(diffs, ddof=1)
        mde = mde_paired(sd, n)
        powered = abs(delta) > mde
        need = power_n_paired(sd, abs(delta)) if abs(delta) > 0.005 else 9999
        phase = SUITE_TO_PHASE.get(suite, "?")
        status = "OK" if powered else "UNDER"

        print(f"  {suite:>35s}  {phase:>16s}  {n:>4d}  {delta:>+7.3f}  {sd:>6.3f}  {mde:>7.3f}  {status:>10s}  {need:>5d}")
        suite_results[suite] = {"n": n, "delta": delta, "sd": sd, "mde": mde, "powered": powered, "need": need}

    # What n per suite do we need for RQ1?
    print(f"\n  MINIMUM n PER SUITE to detect various MCP deltas:")
    median_sd = np.median([sr["sd"] for sr in suite_results.values()])
    print(f"  (using median per-suite σ_d = {median_sd:.4f})")
    for delta in [0.03, 0.05, 0.08, 0.10, 0.15]:
        n_need = power_n_paired(median_sd, delta)
        total = n_need * len(suite_results)
        print(f"    Δ={delta:.2f}: {n_need:>4d} tasks/suite × {len(suite_results)} suites = {total} total")

    return suite_results, sigma_d, n_paired


def analyze_rq2(suite_results, all_sigma_d):
    """RQ2: Heterogeneity of MCP benefit across task types."""
    section("RQ2: MCP Benefit Heterogeneity Across Task Types")

    deltas = {s: r["delta"] for s, r in suite_results.items()}
    delta_vals = list(deltas.values())

    print(f"\n  MCP delta range: [{min(delta_vals):+.3f}, {max(delta_vals):+.3f}]")
    print(f"  MCP delta std across suites: {np.std(delta_vals, ddof=1):.4f}")
    print(f"  Mean MCP delta: {np.mean(delta_vals):+.4f}")

    # Sort by delta
    print(f"\n  Suites ranked by MCP benefit:")
    print(f"  {'Suite':>35s}  {'Phase':>16s}  {'Δ(MCP-BL)':>10s}  {'n':>4s}  {'Powered':>8s}")
    print("  " + "-" * 80)
    for suite, delta in sorted(deltas.items(), key=lambda x: -x[1]):
        r = suite_results[suite]
        phase = SUITE_TO_PHASE.get(suite, "?")
        status = "YES" if r["powered"] else "no"
        print(f"  {suite:>35s}  {phase:>16s}  {delta:>+10.3f}  {r['n']:>4d}  {status:>8s}")

    # For RQ2, we need to detect that the BEST suite differs from the WORST suite
    best = max(deltas.values())
    worst = min(deltas.values())
    spread = best - worst
    # This is a two-sample test on deltas: compare MCP effect in suite A vs suite B
    # But each suite's delta has its own SE
    n_best_suite = [r for s, r in suite_results.items() if deltas[s] == best][0]["n"]
    n_worst_suite = [r for s, r in suite_results.items() if deltas[s] == worst][0]["n"]
    sd_best = [r for s, r in suite_results.items() if deltas[s] == best][0]["sd"]
    sd_worst = [r for s, r in suite_results.items() if deltas[s] == worst][0]["sd"]

    # SE of delta difference
    se_diff = math.sqrt(sd_best ** 2 / n_best_suite + sd_worst ** 2 / n_worst_suite)
    z_stat = spread / se_diff if se_diff > 0 else 0

    print(f"\n  Best-vs-worst spread: {spread:.3f}")
    print(f"  SE of spread: {se_diff:.4f}")
    print(f"  z-statistic: {z_stat:.2f} ({'significant' if abs(z_stat) > 1.96 else 'NOT significant'})")

    # What n per suite would make this significant?
    pooled_sd = math.sqrt((sd_best ** 2 + sd_worst ** 2) / 2)
    n_need = power_n_twosample(pooled_sd, spread)
    print(f"  n per suite to detect this spread: {n_need}")


def analyze_rq3(official, ir_data):
    """RQ3: IR quality → task outcome correlation."""
    section("RQ3: IR Quality vs Task Outcomes (Correlation)")

    # Merge IR metrics with reward data
    # IR data is keyed by some task identifier
    reward_by_task = defaultdict(list)
    config_by_entry = {}
    for t in official["all_tasks"]:
        bp = t.get("benchmark_path", "")
        tid = bp.split("/")[-1]
        reward = t.get("reward")
        config = t.get("config", "")
        if reward is not None:
            reward_by_task[tid].append(reward)

    # Match IR entries to rewards
    # IR per_task keys might be run-level, not task-level
    ir_reward_pairs = {"file_recall": [], "mrr": [], "map_score": []}

    import re
    for entry in ir_data:
        if not isinstance(entry, dict):
            continue
        tid = entry.get("task_name", "")
        # Clean up task_id
        clean_tid = re.sub(r"^(bl_|mcp_|sgonly_)", "", tid)
        clean_tid = re.sub(r"_[a-z0-9]{4,8}$", "", clean_tid)

        rewards = reward_by_task.get(clean_tid, [])
        if not rewards:
            # Try lowercase
            for k in reward_by_task:
                if k.lower() == clean_tid.lower():
                    rewards = reward_by_task[k]
                    break
        if not rewards:
            continue

        mean_reward = np.mean(rewards)
        for metric_name in ir_reward_pairs:
            val = entry.get(metric_name)
            if val is not None and isinstance(val, (int, float)):
                ir_reward_pairs[metric_name].append((val, mean_reward))

    print(f"\n  Matched IR-reward pairs:")
    for metric, pairs in ir_reward_pairs.items():
        if len(pairs) < 5:
            print(f"    {metric}: {len(pairs)} pairs (insufficient)")
            continue

        x = np.array([p[0] for p in pairs])
        y = np.array([p[1] for p in pairs])

        # Spearman rank correlation
        from scipy.stats import spearmanr
        rho, p_val = spearmanr(x, y)

        # Power: what n do we need to detect this correlation?
        n_have = len(pairs)
        n_need = power_n_correlation(rho) if abs(rho) > 0.01 else 99999

        print(f"    {metric:>15s}: ρ={rho:+.4f}, p={p_val:.4f}, n={n_have}, need={n_need}, "
              f"{'POWERED' if n_have >= n_need else 'UNDER'}")

    # What correlations CAN we detect with current n?
    print(f"\n  Detectable correlations at current n:")
    for metric, pairs in ir_reward_pairs.items():
        n = len(pairs)
        if n < 5:
            continue
        # MDE for correlation: r = (z_a + z_b) / sqrt(n - 3)
        min_r = (1.96 + 0.84) / math.sqrt(n - 3) if n > 3 else 1.0
        print(f"    {metric:>15s} (n={n}): can detect |ρ| ≥ {min_r:.3f}")


def analyze_rq4(official):
    """RQ4: Efficiency trade-offs (tokens, time, TTFR)."""
    section("RQ4: Efficiency Trade-offs")

    # Pair BL vs MCP per task
    task_metrics = defaultdict(lambda: {"bl": [], "mcp": []})
    for t in official["all_tasks"]:
        bp = t.get("benchmark_path", "")
        tid = bp.split("/")[-1]
        config = t.get("config", "")
        key = "mcp" if "mcp" in config else "bl"

        task_metrics[tid][key].append({
            "input_tokens": t.get("input_tokens", 0),
            "output_tokens": t.get("output_tokens", 0),
            "cache_tokens": t.get("cache_tokens", 0),
            "time": t.get("agent_execution_seconds", 0),
            "reward": t.get("reward", 0),
        })

    # Compute paired differences for each efficiency metric
    metrics = ["input_tokens", "output_tokens", "time"]
    metric_labels = {"input_tokens": "Input Tokens", "output_tokens": "Output Tokens", "time": "Wall-Clock (s)"}

    print(f"\n  {'Metric':>20s}  {'BL mean':>12s}  {'MCP mean':>12s}  {'Δ':>12s}  {'σ_d':>10s}  {'MDE':>10s}  {'Status':>8s}")
    print("  " + "-" * 90)

    for m in metrics:
        diffs = []
        bl_vals = []
        mcp_vals = []
        for tid, cfg in task_metrics.items():
            if cfg["bl"] and cfg["mcp"]:
                bl_mean = np.mean([e[m] for e in cfg["bl"]])
                mcp_mean = np.mean([e[m] for e in cfg["mcp"]])
                diffs.append(mcp_mean - bl_mean)
                bl_vals.append(bl_mean)
                mcp_vals.append(mcp_mean)

        if len(diffs) < 2:
            continue

        delta = np.mean(diffs)
        sd = np.std(diffs, ddof=1)
        n = len(diffs)
        mde = mde_paired(sd, n)
        powered = abs(delta) > mde

        label = metric_labels.get(m, m)
        print(f"  {label:>20s}  {np.mean(bl_vals):>12.0f}  {np.mean(mcp_vals):>12.0f}  "
              f"{delta:>+12.0f}  {sd:>10.0f}  {mde:>10.0f}  {'OK' if powered else 'UNDER':>8s}")

    # TTFR from IR data
    ir_path = PROJ_ROOT / "results/ir/retrieval_metrics_promoted.json"
    if ir_path.is_file():
        with open(ir_path) as f:
            ir = json.load(f)
        overall_ttfr = ir.get("overall", {}).get("ttfr_seconds", {})
        if overall_ttfr:
            print(f"\n  TTFR (Time to First Relevant file):")
            print(f"    Mean: {overall_ttfr.get('mean', '?'):.1f}s, Median: {overall_ttfr.get('median', '?'):.1f}s")
            print(f"    σ: {overall_ttfr.get('std', '?'):.1f}s, n: {overall_ttfr.get('n', '?')}")

            by_config = ir.get("by_config", {})
            if by_config:
                print(f"\n    Per-config TTFR:")
                for cfg, metrics in sorted(by_config.items()):
                    ttfr = metrics.get("ttfr_seconds")
                    if ttfr and isinstance(ttfr, dict):
                        print(f"      {cfg:>30s}: mean={ttfr.get('mean', '?'):.1f}s, n={ttfr.get('n', '?')}")


def analyze_rq5(official):
    """RQ5: Org-scale discovery tasks."""
    section("RQ5: Org-Scale Discovery (MCP-Enabled Tasks)")

    org_suites = [s for s in SUITE_TO_PHASE if "org" in s]
    sdlc_suites = [s for s in SUITE_TO_PHASE if "sdlc" in s]

    # Pair by task
    org_pairs = defaultdict(lambda: {"bl": [], "mcp": []})
    sdlc_pairs = defaultdict(lambda: {"bl": [], "mcp": []})

    for t in official["all_tasks"]:
        bp = t.get("benchmark_path", "")
        suite = bp.split("/")[1] if "/" in bp else "?"
        tid = bp.split("/")[-1]
        config = t.get("config", "")
        reward = t.get("reward")
        mcp_ratio = t.get("mcp_ratio", 0) or 0
        tool_calls_mcp = t.get("tool_calls_mcp", 0) or 0

        if reward is None:
            continue

        key = "mcp" if "mcp" in config else "bl"
        entry = {"reward": reward, "mcp_ratio": mcp_ratio, "mcp_calls": tool_calls_mcp}

        if suite in org_suites:
            org_pairs[tid][key].append(entry)
        elif suite in sdlc_suites:
            sdlc_pairs[tid][key].append(entry)

    # Org task analysis
    org_diffs = []
    org_bl_scores = []
    org_mcp_scores = []
    org_mcp_usage = []
    for tid, cfg in org_pairs.items():
        if cfg["bl"] and cfg["mcp"]:
            bl_mean = np.mean([e["reward"] for e in cfg["bl"]])
            mcp_mean = np.mean([e["reward"] for e in cfg["mcp"]])
            org_diffs.append(mcp_mean - bl_mean)
            org_bl_scores.append(bl_mean)
            org_mcp_scores.append(mcp_mean)
            org_mcp_usage.append(np.mean([e["mcp_calls"] for e in cfg["mcp"]]))

    sdlc_diffs = []
    for tid, cfg in sdlc_pairs.items():
        if cfg["bl"] and cfg["mcp"]:
            sdlc_diffs.append(np.mean([e["reward"] for e in cfg["mcp"]]) - np.mean([e["reward"] for e in cfg["bl"]]))

    if org_diffs:
        org_delta = np.mean(org_diffs)
        org_sd = np.std(org_diffs, ddof=1)
        org_n = len(org_diffs)
        org_mde = mde_paired(org_sd, org_n)
        print(f"\n  Org tasks (n={org_n} paired):")
        print(f"    BL mean:  {np.mean(org_bl_scores):.3f}")
        print(f"    MCP mean: {np.mean(org_mcp_scores):.3f}")
        print(f"    Δ: {org_delta:+.4f}, σ_d: {org_sd:.4f}, MDE: {org_mde:.4f}")
        print(f"    Status: {'POWERED' if abs(org_delta) > org_mde else 'UNDERPOWERED'}")
        print(f"    Mean MCP tool calls (MCP config): {np.mean(org_mcp_usage):.1f}")

    if sdlc_diffs:
        sdlc_delta = np.mean(sdlc_diffs)
        sdlc_sd = np.std(sdlc_diffs, ddof=1)
        sdlc_n = len(sdlc_diffs)
        sdlc_mde = mde_paired(sdlc_sd, sdlc_n)
        print(f"\n  SDLC tasks (n={sdlc_n} paired):")
        print(f"    Δ: {sdlc_delta:+.4f}, σ_d: {sdlc_sd:.4f}, MDE: {sdlc_mde:.4f}")
        print(f"    Status: {'POWERED' if abs(sdlc_delta) > sdlc_mde else 'UNDERPOWERED'}")

    if org_diffs and sdlc_diffs:
        # Compare MCP benefit: Org vs SDLC
        org_mcp_benefit = np.mean(org_diffs)
        sdlc_mcp_benefit = np.mean(sdlc_diffs)
        diff_of_diffs = org_mcp_benefit - sdlc_mcp_benefit
        se_diff = math.sqrt(org_sd ** 2 / org_n + sdlc_sd ** 2 / sdlc_n)
        z = diff_of_diffs / se_diff if se_diff > 0 else 0

        print(f"\n  MCP benefit: Org vs SDLC:")
        print(f"    Org MCP Δ:  {org_mcp_benefit:+.4f}")
        print(f"    SDLC MCP Δ: {sdlc_mcp_benefit:+.4f}")
        print(f"    Difference: {diff_of_diffs:+.4f}, z={z:.2f} ({'significant' if abs(z) > 1.96 else 'NOT significant'})")

    # Cross-repo coverage: how many org suites specifically need MCP?
    print(f"\n  Org suite MCP adoption (MCP config runs):")
    suite_mcp_usage = defaultdict(list)
    for t in official["all_tasks"]:
        bp = t.get("benchmark_path", "")
        suite = bp.split("/")[1] if "/" in bp else "?"
        config = t.get("config", "")
        if suite in org_suites and "mcp" in config:
            suite_mcp_usage[suite].append(t.get("tool_calls_mcp", 0) or 0)

    print(f"  {'Suite':>35s}  {'Mean MCP calls':>15s}  {'% using MCP':>12s}  {'n':>4s}")
    print("  " + "-" * 75)
    for suite in sorted(suite_mcp_usage.keys()):
        calls = suite_mcp_usage[suite]
        mean_calls = np.mean(calls)
        pct_using = sum(1 for c in calls if c > 0) / len(calls) * 100
        print(f"  {suite:>35s}  {mean_calls:>15.1f}  {pct_using:>11.0f}%  {len(calls):>4d}")


def synthesis(suite_results):
    """Final synthesis: minimum task set per RQ."""
    section("SYNTHESIS: Minimum Task Set Per Research Question")

    median_sd = np.median([r["sd"] for r in suite_results.values()])
    n_suites = len(suite_results)

    print(f"""
  Current: 372 unique tasks, 20 suites, ~18.6 tasks/suite avg

  ┌─────────────────────────────────────────────────────────────────────────┐
  │ RQ   Claim                          Min Tasks  Current  Gap   Status   │
  ├─────────────────────────────────────────────────────────────────────────┤""")

    # RQ1: Overall MCP effect - paired, n=370
    n_rq1_overall = power_n_paired(0.2213, 0.035)
    print(f"  │ RQ1a Overall MCP Δ=0.035           {n_rq1_overall:>5d}      370     -   OK       │")

    # RQ1: Per-suite MCP - need ~n per suite to detect suite-level deltas
    # Most suites have Δ~0.02-0.08, σ_d~0.15-0.30
    n_rq1_suite = power_n_paired(median_sd, 0.05)
    total_rq1_suite = n_rq1_suite * n_suites
    have_min_suite = min(r["n"] for r in suite_results.values())
    gap_rq1 = max(0, n_rq1_suite - have_min_suite)
    status_rq1 = "OK" if gap_rq1 == 0 else f"+{gap_rq1}/suite"
    print(f"  │ RQ1b Per-suite MCP (Δ=0.05)        {n_rq1_suite:>5d}/s    {have_min_suite:>5d}/s  {gap_rq1:>4d}  {status_rq1:<8s} │")

    # RQ2: Heterogeneity - need enough per suite to compare best vs worst
    n_rq2 = power_n_paired(median_sd, 0.10)  # detect 10pp spread between suites
    print(f"  │ RQ2  Suite heterogeneity (Δ=0.10)   {n_rq2:>5d}/s    {have_min_suite:>5d}/s  {max(0, n_rq2-have_min_suite):>4d}  {'OK' if n_rq2 <= have_min_suite else f'+{n_rq2-have_min_suite}/s':<8s} │")

    # RQ3: Correlation - need ~85 pairs for r=0.3, ~783 for r=0.1
    n_rq3_r03 = power_n_correlation(0.3)
    n_rq3_r02 = power_n_correlation(0.2)
    print(f"  │ RQ3  IR↔reward corr (ρ=0.3)        {n_rq3_r03:>5d}     1921     -   OK       │")
    print(f"  │ RQ3  IR↔reward corr (ρ=0.2)        {n_rq3_r02:>5d}     1921     -   OK       │")

    # RQ4: Efficiency - paired, large effect expected
    # Tokens typically differ by thousands → powered with small n
    print(f"  │ RQ4  Token/time differences          ~50      370     -   OK       │")

    # RQ5: Org vs SDLC MCP benefit
    n_rq5 = power_n_paired(0.22, 0.03)  # detect 3pp MCP delta in org subset
    print(f"  │ RQ5  Org MCP effect (Δ=0.03)       {n_rq5:>5d}      220     -   {'OK' if n_rq5 <= 220 else 'UNDER':<8s} │")

    print(f"""  └─────────────────────────────────────────────────────────────────────────┘

  BINDING CONSTRAINT: RQ1b (per-suite MCP detection at Δ=0.05)
    Requires {n_rq1_suite} tasks per suite × {n_suites} suites = {total_rq1_suite} total
    Smallest suites: csb_sdlc_understand (10), csb_sdlc_secure (12), csb_sdlc_document (13)

  ACHIEVABLE TARGETS:
    • Δ=0.05/suite: {n_rq1_suite}/suite — need to grow smallest suites
    • Δ=0.08/suite: {power_n_paired(median_sd, 0.08)}/suite — closer to current
    • Δ=0.10/suite: {power_n_paired(median_sd, 0.10)}/suite — achievable for most suites
    • Δ=0.15/suite: {power_n_paired(median_sd, 0.15)}/suite — ALL suites already meet this

  RECOMMENDED MINIMUM (Δ=0.10/suite for RQ1b/RQ2):
    {power_n_paired(median_sd, 0.10)} tasks/suite × {n_suites} suites = {power_n_paired(median_sd, 0.10) * n_suites} unique tasks
    × 2 configs = {power_n_paired(median_sd, 0.10) * n_suites * 2} total runs
    × 3 replications = {power_n_paired(median_sd, 0.10) * n_suites * 2 * 3} evaluations

  EXPANSION PRIORITY (to reach Δ=0.10/suite):
    Suites below {power_n_paired(median_sd, 0.10)} tasks:""")

    target = power_n_paired(median_sd, 0.10)
    for suite in sorted(suite_results.keys(), key=lambda s: suite_results[s]["n"]):
        r = suite_results[suite]
        if r["n"] < target:
            phase = SUITE_TO_PHASE.get(suite, "?")
            gap = target - r["n"]
            print(f"      {suite:>35s} ({phase:>16s}): {r['n']:>3d} → need +{gap}")

    # Can we TRIM anywhere?
    over = [(s, r["n"] - target) for s, r in suite_results.items() if r["n"] > target]
    if over:
        trimmable = sum(excess for _, excess in over)
        print(f"\n  Trimmable (above target): {trimmable} tasks across {len(over)} suites")
        print(f"    BUT: more runs per task improves reliability, only trim if budget-constrained")


def main():
    official, ir_data = load_all_data()
    suite_results, sigma_d, n_paired = analyze_rq1(official)
    analyze_rq2(suite_results, sigma_d)

    try:
        analyze_rq3(official, ir_data)
    except ImportError:
        print("\n  (scipy not available — skipping Spearman correlation)")

    analyze_rq4(official)
    analyze_rq5(official)
    synthesis(suite_results)


if __name__ == "__main__":
    main()
