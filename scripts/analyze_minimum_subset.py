#!/usr/bin/env python3
"""Design the minimum balanced benchmark subset for confident claims.

Analyzes the factor space and computes power requirements for:
  1. Config effect (baseline vs MCP)
  2. Task category (comprehension, implementation, quality)
  3. Codebase complexity (size × structural complexity)
  4. Cross-suite comparisons
  5. Factor interactions (does MCP help more on larger/harder codebases?)

Uses repo-level clustering adjustment (DEFF) throughout.
"""

import json
import math
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

PROJ_ROOT = Path(__file__).resolve().parent.parent

# ── Taxonomy: map suites to task macro-categories ──
# Comprehension: understanding, reading, navigating code
# Implementation: writing, editing, creating code
# Quality: testing, debugging, security, compliance
SUITE_TO_CATEGORY = {
    # SDLC suites
    "csb_sdlc_understand": "comprehension",
    "csb_sdlc_design": "comprehension",
    "csb_sdlc_document": "comprehension",
    "csb_sdlc_feature": "implementation",
    "csb_sdlc_refactor": "implementation",
    "csb_sdlc_fix": "implementation",
    "csb_sdlc_debug": "quality",
    "csb_sdlc_test": "quality",
    "csb_sdlc_secure": "quality",
    # Org suites
    "csb_org_onboarding": "comprehension",
    "csb_org_domain": "comprehension",
    "csb_org_org": "comprehension",
    "csb_org_crossrepo": "comprehension",
    "csb_org_crossrepo_tracing": "comprehension",
    "csb_org_crossorg": "comprehension",
    "csb_org_incident": "quality",
    "csb_org_security": "quality",
    "csb_org_compliance": "quality",
    "csb_org_migration": "implementation",
    "csb_org_platform": "implementation",
}

# ── Codebase complexity bins (LOC × structural complexity) ──
def loc_tier(loc):
    if loc < 500_000: return "small"
    if loc < 5_000_000: return "medium"
    return "large"

def complexity_tier(complexity):
    if complexity is None: return "unknown"
    if complexity < 0.5: return "low"
    if complexity < 0.75: return "medium"
    return "high"


def load_data():
    """Load official results merged with selected tasks metadata."""
    with open(PROJ_ROOT / "docs/official_results/data/official_results.json") as f:
        official = json.load(f)

    records = []
    for t in official["all_tasks"]:
        reward = t.get("reward")
        loc = t.get("repo_approx_loc", 0)
        if reward is None or not loc or loc <= 0:
            continue

        bp = t.get("benchmark_path", "")
        suite = bp.split("/")[1] if "/" in bp else "unknown"
        task_id = bp.split("/")[-1] if "/" in bp else bp
        config = t.get("config", "unknown")
        is_mcp = 1 if "mcp" in config else 0

        # Language normalization
        lang = (t.get("repo_primary_language") or "unknown").lower()
        if lang in ("c", "cpp", "c_cpp_headers"): lang = "c_cpp"
        elif lang in ("javascript", "json"): lang = "javascript"
        elif lang not in ("go", "java", "python", "rust", "typescript", "csharp"):
            lang = "other"

        task_type = "SDLC" if "sdlc" in suite else "Org"
        category = SUITE_TO_CATEGORY.get(suite, "unknown")
        lt = loc_tier(loc)
        rc = t.get("repo_complexity")
        ct = complexity_tier(rc)

        records.append({
            "reward": reward,
            "loc": loc,
            "log_loc": math.log10(loc),
            "lang": lang,
            "task_type": task_type,
            "category": category,
            "suite": suite,
            "task_id": task_id,
            "is_mcp": is_mcp,
            "config": config,
            "loc_tier": lt,
            "complexity_tier": ct,
            "repo_complexity": rc,
            "repo": t.get("repo") or task_id,
        })

    return records


def compute_icc_deff(records, group_key="task_id"):
    """Compute ICC and design effect for a grouping variable."""
    groups = defaultdict(list)
    for r in records:
        groups[r[group_key]].append(r["reward"])

    grand_mean = np.mean([r["reward"] for r in records])
    ss_between = ss_within = 0
    n_total = 0

    for gid, rewards in groups.items():
        n_j = len(rewards)
        if n_j == 0: continue
        n_total += n_j
        gm = np.mean(rewards)
        ss_between += n_j * (gm - grand_mean) ** 2
        ss_within += sum((r - gm) ** 2 for r in rewards)

    n_groups = len(groups)
    if n_groups <= 1 or n_total <= n_groups:
        return 0, 1.0

    ms_b = ss_between / (n_groups - 1)
    ms_w = ss_within / (n_total - n_groups)
    avg_n = n_total / n_groups

    denom = ms_b + (avg_n - 1) * ms_w
    icc = max(0, (ms_b - ms_w) / denom) if denom > 0 else 0
    deff = 1 + (avg_n - 1) * icc
    return icc, deff


def power_n(sigma, delta, alpha=0.05, power=0.80):
    """Two-sample t-test: n per group for given sigma, delta."""
    # z_alpha/2 + z_beta
    z_a = 1.96 if alpha == 0.05 else 2.58
    z_b = 0.84 if power == 0.80 else 1.28
    z_factor = (z_a + z_b) ** 2
    return math.ceil(2 * z_factor * sigma ** 2 / delta ** 2)


def section(title):
    print(f"\n{'=' * 90}")
    print(title)
    print("=" * 90)


def analyze_factors(records, deff):
    """Analyze each factor's effect size, variance, and power requirements."""
    section("FACTOR ANALYSIS: Effect sizes and power requirements")

    factors = {
        "config": {"key": "is_mcp", "levels": {0: "baseline", 1: "MCP"},
                    "claim": "MCP improves agent performance"},
        "task_type": {"key": "task_type", "levels": {"SDLC": "SDLC", "Org": "Org"},
                      "claim": "SDLC vs Org tasks differ in difficulty"},
        "category": {"key": "category",
                      "levels": {"comprehension": "comprehension", "implementation": "implementation", "quality": "quality"},
                      "claim": "Task category affects performance"},
        "loc_tier": {"key": "loc_tier",
                     "levels": {"small": "<500K", "medium": "500K-5M", "large": "5M+"},
                     "claim": "Codebase size affects performance"},
        "complexity": {"key": "complexity_tier",
                       "levels": {"low": "low", "medium": "medium", "high": "high"},
                       "claim": "Repo structural complexity affects performance"},
    }

    results = {}

    for fname, finfo in factors.items():
        key = finfo["key"]
        levels = finfo["levels"]

        # Group by level
        level_data = defaultdict(list)
        level_tasks = defaultdict(set)
        for r in records:
            val = r[key]
            if val in levels:
                level_data[levels[val]].append(r["reward"])
                level_tasks[levels[val]].add(r["task_id"])

        if len(level_data) < 2:
            continue

        print(f"\n--- {fname.upper()}: {finfo['claim']} ---")
        print(f"{'Level':>20s}  {'n_evals':>8s}  {'n_tasks':>8s}  {'mean':>7s}  {'std':>7s}")
        print("-" * 60)

        level_stats = {}
        for lname in levels.values():
            vals = level_data.get(lname, [])
            n_tasks = len(level_tasks.get(lname, set()))
            mu = np.mean(vals) if vals else 0
            sigma = np.std(vals, ddof=1) if len(vals) > 1 else 0
            level_stats[lname] = {"n": len(vals), "n_tasks": n_tasks, "mean": mu, "std": sigma}
            print(f"{lname:>20s}  {len(vals):>8d}  {n_tasks:>8d}  {mu:>7.3f}  {sigma:>7.3f}")

        # Pairwise effect sizes (Cohen's d)
        level_names = list(level_stats.keys())
        print(f"\n  Pairwise comparisons:")
        print(f"  {'Pair':>35s}  {'δ':>7s}  {'Cohen d':>8s}  {'n_eff/grp (80% pwr)':>20s}  {'n_nom/grp':>10s}")

        max_delta = 0
        for i in range(len(level_names)):
            for j in range(i + 1, len(level_names)):
                a, b = level_names[i], level_names[j]
                sa, sb = level_stats[a], level_stats[b]
                delta = abs(sa["mean"] - sb["mean"])
                pooled_s = math.sqrt((sa["std"]**2 + sb["std"]**2) / 2) if sa["std"] > 0 and sb["std"] > 0 else 0.01
                cohens_d = delta / pooled_s if pooled_s > 0 else 0
                n_eff = power_n(pooled_s, max(delta, 0.01))
                n_nom = math.ceil(n_eff * deff)
                max_delta = max(max_delta, delta)
                print(f"  {a+' vs '+b:>35s}  {delta:>7.3f}  {cohens_d:>8.3f}  {n_eff:>20d}  {n_nom:>10d}")

        results[fname] = {"stats": level_stats, "max_delta": max_delta}

    return results


def interaction_analysis(records, deff):
    """Check if MCP effect varies by category and size."""
    section("INTERACTION ANALYSIS: Does MCP benefit vary by factor?")

    for factor_name, factor_key in [("category", "category"), ("loc_tier", "loc_tier"), ("complexity", "complexity_tier")]:
        print(f"\n--- MCP effect × {factor_name} ---")
        print(f"{'Level':>20s}  {'BL_mean':>8s}  {'MCP_mean':>9s}  {'Δ(MCP-BL)':>10s}  {'n_BL':>6s}  {'n_MCP':>6s}")
        print("-" * 70)

        levels = sorted(set(r[factor_key] for r in records if r[factor_key] not in ("unknown",)))
        for level in levels:
            bl = [r["reward"] for r in records if r[factor_key] == level and r["is_mcp"] == 0]
            mcp = [r["reward"] for r in records if r[factor_key] == level and r["is_mcp"] == 1]
            if not bl or not mcp:
                continue
            bl_mean = np.mean(bl)
            mcp_mean = np.mean(mcp)
            delta = mcp_mean - bl_mean
            print(f"{level:>20s}  {bl_mean:>8.3f}  {mcp_mean:>9.3f}  {delta:>+10.3f}  {len(bl):>6d}  {len(mcp):>6d}")


def cross_tab_coverage(records):
    """Show coverage of the factor cross-product."""
    section("CROSS-TABULATION: Factor coverage matrix")

    # category × loc_tier × config
    cells = defaultdict(lambda: {"n_evals": 0, "n_tasks": set(), "n_repos": set()})
    for r in records:
        cat = r["category"]
        lt = r["loc_tier"]
        if cat == "unknown": continue
        key = (cat, lt)
        cells[key]["n_evals"] += 1
        cells[key]["n_tasks"].add(r["task_id"])
        cells[key]["n_repos"].add(r["repo"])

    categories = ["comprehension", "implementation", "quality"]
    tiers = ["small", "medium", "large"]

    print(f"\n{'':>20s}", end="")
    for lt in tiers:
        print(f"  {'─── ' + lt + ' ───':>20s}", end="")
    print()

    print(f"{'Category':>20s}", end="")
    for lt in tiers:
        print(f"  {'tasks/repos/evals':>20s}", end="")
    print()
    print("-" * 80)

    sparse_cells = []
    for cat in categories:
        print(f"{cat:>20s}", end="")
        for lt in tiers:
            c = cells[(cat, lt)]
            nt = len(c["n_tasks"])
            nr = len(c["n_repos"])
            ne = c["n_evals"]
            print(f"  {f'{nt}t/{nr}r/{ne}e':>20s}", end="")
            if nt < 10:
                sparse_cells.append((cat, lt, nt))
        print()

    if sparse_cells:
        print(f"\n⚠  Sparse cells (< 10 tasks):")
        for cat, lt, nt in sparse_cells:
            print(f"  {cat} × {lt}: {nt} tasks")


def minimum_subset_design(records, factor_results, deff):
    """Compute minimum subset for each claim at various power levels."""
    section("MINIMUM BALANCED SUBSET DESIGN")

    icc, _ = compute_icc_deff(records)
    pooled_sigma = np.std([r["reward"] for r in records], ddof=1)

    print(f"\nGlobal parameters:")
    print(f"  Pooled σ:      {pooled_sigma:.4f}")
    print(f"  DEFF:          {deff:.2f}")
    print(f"  ICC:           {icc:.3f}")

    # Define the claims we want to power
    claims = [
        {
            "name": "MCP vs Baseline",
            "observed_delta": abs(factor_results["config"]["max_delta"]),
            "target_deltas": [0.02, 0.03, 0.05],
            "factor": "config",
            "n_levels": 2,
            "note": "Paired design (same task, both configs) reduces variance",
        },
        {
            "name": "SDLC vs Org",
            "observed_delta": abs(factor_results["task_type"]["max_delta"]),
            "target_deltas": [0.05, 0.10, 0.15],
            "factor": "task_type",
            "n_levels": 2,
        },
        {
            "name": "Category (comp/impl/qual)",
            "observed_delta": abs(factor_results["category"]["max_delta"]),
            "target_deltas": [0.03, 0.05, 0.08],
            "factor": "category",
            "n_levels": 3,
        },
        {
            "name": "Codebase size tier",
            "observed_delta": abs(factor_results["loc_tier"]["max_delta"]),
            "target_deltas": [0.03, 0.05, 0.08],
            "factor": "loc_tier",
            "n_levels": 3,
        },
        {
            "name": "Complexity tier",
            "observed_delta": abs(factor_results.get("complexity", {}).get("max_delta", 0.05)),
            "target_deltas": [0.03, 0.05, 0.08],
            "factor": "complexity",
            "n_levels": 3,
        },
    ]

    print(f"\n{'Claim':>30s}  {'Obs Δ':>6s}  {'Tgt Δ':>6s}  {'n_eff/lvl':>10s}  {'n_nom/lvl':>10s}  {'n_total':>8s}  {'Have':>6s}  {'Feasible':>9s}")
    print("-" * 105)

    recommended_n = {}

    for claim in claims:
        obs_d = claim["observed_delta"]
        for td in claim["target_deltas"]:
            n_eff = power_n(pooled_sigma, td)
            # For paired MCP design, variance is reduced
            if claim["factor"] == "config":
                # Paired t-test: use within-task SD of (MCP - BL) difference
                diffs = []
                task_config = defaultdict(dict)
                for r in records:
                    task_config[r["task_id"]][r["is_mcp"]] = task_config[r["task_id"]].get(r["is_mcp"], [])
                    task_config[r["task_id"]][r["is_mcp"]].append(r["reward"])
                for tid, configs in task_config.items():
                    if 0 in configs and 1 in configs:
                        diffs.append(np.mean(configs[1]) - np.mean(configs[0]))
                if diffs:
                    paired_sigma = np.std(diffs, ddof=1)
                    n_eff = power_n(paired_sigma, td)
                    # For paired, DEFF is different (task-level, not repo-level)
                    n_nom = n_eff  # already at task level
                else:
                    n_nom = math.ceil(n_eff * deff)
            else:
                n_nom = math.ceil(n_eff * deff)

            n_total = n_nom * claim["n_levels"] * 2  # × 2 configs
            # How many we currently have per level
            have_per_level = min(
                len([r for r in records if r.get(claim["factor"].replace("complexity", "complexity_tier").replace("loc_tier", "loc_tier"), r.get(claim["factor"])) == lv])
                for lv in (factor_results.get(claim["factor"], {}).get("stats", {}).keys() or ["?"])
            ) if factor_results.get(claim["factor"], {}).get("stats") else 0

            feasible = "YES" if n_nom <= have_per_level else "STRETCH" if n_nom <= have_per_level * 2 else "NO"

            print(f"{claim['name']:>30s}  {obs_d:>6.3f}  {td:>6.3f}  {n_eff:>10d}  {n_nom:>10d}  {n_total:>8d}  {have_per_level:>6d}  {feasible:>9s}")

        recommended_n[claim["name"]] = n_nom  # last (largest delta = smallest n)

    # ── Now compute the actual minimum set ──
    section("RECOMMENDED MINIMUM TASK SET")

    # Task-level aggregation
    task_data = defaultdict(lambda: {"rewards": [], "loc": 0, "category": "", "loc_tier": "",
                                      "complexity_tier": "", "suite": "", "lang": "", "repo": "",
                                      "task_type": ""})
    for r in records:
        td = task_data[r["task_id"]]
        td["rewards"].append(r["reward"])
        td["loc"] = r["loc"]
        td["category"] = r["category"]
        td["loc_tier"] = r["loc_tier"]
        td["complexity_tier"] = r["complexity_tier"]
        td["suite"] = r["suite"]
        td["lang"] = r["lang"]
        td["repo"] = r["repo"]
        td["task_type"] = r["task_type"]

    n_unique_tasks = len(task_data)

    # Define the target: cover all cells of category × loc_tier with minimum repos
    categories = ["comprehension", "implementation", "quality"]
    loc_tiers = ["small", "medium", "large"]

    print(f"\nTarget: 3 categories × 3 size tiers = 9 cells")
    print(f"Constraint: ≥ 5 unique repos per cell, paired (BL+MCP) runs")
    print(f"\nWith paired design (MCP effect tested within-task),")
    print(f"the MCP claim doesn't need extra tasks — just 2 runs per task.")
    print(f"\nFor between-cell comparisons (category, size):")

    # Paired MCP sigma (already computed above)
    task_config = defaultdict(dict)
    for r in records:
        task_config[r["task_id"]][r["is_mcp"]] = task_config[r["task_id"]].get(r["is_mcp"], [])
        task_config[r["task_id"]][r["is_mcp"]].append(r["reward"])
    diffs = []
    for tid, configs in task_config.items():
        if 0 in configs and 1 in configs:
            diffs.append(np.mean(configs[1]) - np.mean(configs[0]))
    paired_sigma = np.std(diffs, ddof=1) if diffs else pooled_sigma

    print(f"  Paired σ (MCP-BL differences): {paired_sigma:.4f}")
    print(f"  Between-task σ: {pooled_sigma:.4f}")

    # Minimum per cell for δ=0.05 between categories/sizes
    n_per_cell_05 = power_n(pooled_sigma, 0.05)
    n_per_cell_08 = power_n(pooled_sigma, 0.08)
    n_per_cell_10 = power_n(pooled_sigma, 0.10)

    # For paired MCP test within each cell
    n_mcp_paired_02 = power_n(paired_sigma, 0.02)
    n_mcp_paired_03 = power_n(paired_sigma, 0.03)
    n_mcp_paired_05 = power_n(paired_sigma, 0.05)

    print(f"\n  Between-cell (category/size) comparisons:")
    print(f"    δ=0.05: {n_per_cell_05} tasks/cell → {n_per_cell_05 * 9} total unique tasks")
    print(f"    δ=0.08: {n_per_cell_08} tasks/cell → {n_per_cell_08 * 9} total unique tasks")
    print(f"    δ=0.10: {n_per_cell_10} tasks/cell → {n_per_cell_10 * 9} total unique tasks")

    print(f"\n  MCP effect (paired within-task):")
    print(f"    δ=0.02: {n_mcp_paired_02} tasks total (any cell)")
    print(f"    δ=0.03: {n_mcp_paired_03} tasks total")
    print(f"    δ=0.05: {n_mcp_paired_05} tasks total")

    # Current coverage
    print(f"\n  Current coverage per cell:")
    print(f"  {'':>20s}", end="")
    for lt in loc_tiers:
        print(f"  {lt:>12s}", end="")
    print(f"  {'row total':>10s}")
    print("  " + "-" * 70)

    total_tasks = 0
    cell_counts = {}
    for cat in categories:
        print(f"  {cat:>20s}", end="")
        row_total = 0
        for lt in loc_tiers:
            n = sum(1 for tid, td in task_data.items() if td["category"] == cat and td["loc_tier"] == lt)
            cell_counts[(cat, lt)] = n
            row_total += n
            print(f"  {n:>12d}", end="")
        print(f"  {row_total:>10d}")
        total_tasks += row_total

    print(f"  {'col total':>20s}", end="")
    for lt in loc_tiers:
        col = sum(cell_counts.get((c, lt), 0) for c in categories)
        print(f"  {col:>12d}", end="")
    print(f"  {total_tasks:>10d}")

    # Identify binding constraint
    min_cell = min(cell_counts.values())
    min_cell_name = [k for k, v in cell_counts.items() if v == min_cell][0]

    print(f"\n  Smallest cell: {min_cell_name[0]} × {min_cell_name[1]} = {min_cell} tasks")
    print(f"  This is the BINDING CONSTRAINT for balanced factorial design.")

    # Recommendation tiers
    print(f"\n{'─' * 90}")
    print(f"RECOMMENDATION TIERS")
    print(f"{'─' * 90}")

    tiers_config = [
        ("Conservative (δ=0.05)", 0.05, n_per_cell_05),
        ("Moderate (δ=0.08)", 0.08, n_per_cell_08),
        ("Pragmatic (δ=0.10)", 0.10, n_per_cell_10),
    ]

    for tier_name, delta, n_cell in tiers_config:
        n_min_tasks = n_cell * 9  # 9 cells
        n_runs = n_min_tasks * 2  # BL + MCP
        n_repos_per_cell = max(5, n_cell // 3)  # no repo > 33% of cell

        can_do = all(cell_counts.get((c, l), 0) >= n_cell for c in categories for l in loc_tiers)
        shortfalls = [(c, l, n_cell - cell_counts.get((c, l), 0))
                      for c in categories for l in loc_tiers
                      if cell_counts.get((c, l), 0) < n_cell]

        print(f"\n  {tier_name}:")
        print(f"    Tasks per cell:     {n_cell}")
        print(f"    Min repos per cell: {n_repos_per_cell}")
        print(f"    Total unique tasks: {n_min_tasks}")
        print(f"    Total runs (×2):    {n_runs}")
        print(f"    Detectable MCP Δ:   {delta:.2f} (within each cell)")
        print(f"    Currently feasible: {'YES' if can_do else 'NO'}")
        if shortfalls:
            print(f"    Shortfalls:")
            for c, l, gap in shortfalls:
                print(f"      {c:>20s} × {l:<8s}: need {gap} more tasks")

    # What claims can we ALREADY make?
    section("CLAIMS SUPPORTED BY CURRENT DATA")

    # For each comparison, check if current n is sufficient
    comparisons = [
        ("MCP vs Baseline (overall)", len(diffs), paired_sigma, "paired"),
        ("SDLC vs Org", min(len([r for r in records if r["task_type"] == "SDLC"]),
                           len([r for r in records if r["task_type"] == "Org"])), pooled_sigma, "independent"),
    ]

    for cat_pair in [("comprehension", "implementation"), ("comprehension", "quality"), ("implementation", "quality")]:
        n_a = len([tid for tid, td in task_data.items() if td["category"] == cat_pair[0]])
        n_b = len([tid for tid, td in task_data.items() if td["category"] == cat_pair[1]])
        comparisons.append((f"{cat_pair[0]} vs {cat_pair[1]}", min(n_a, n_b), pooled_sigma, "independent"))

    for lt_pair in [("small", "medium"), ("small", "large"), ("medium", "large")]:
        n_a = len([tid for tid, td in task_data.items() if td["loc_tier"] == lt_pair[0]])
        n_b = len([tid for tid, td in task_data.items() if td["loc_tier"] == lt_pair[1]])
        comparisons.append((f"size:{lt_pair[0]} vs {lt_pair[1]}", min(n_a, n_b), pooled_sigma, "independent"))

    print(f"\n{'Comparison':>40s}  {'n_min':>6s}  {'MDE (80% pwr)':>14s}  {'Sufficient for':>15s}")
    print("-" * 85)

    for name, n_min, sigma, design in comparisons:
        if design == "paired":
            # MDE = sigma * (z_a + z_b) / sqrt(n)
            if n_min > 0:
                mde = sigma * (1.96 + 0.84) / math.sqrt(n_min)
            else:
                mde = float("inf")
        else:
            if n_min > 0:
                mde = sigma * (1.96 + 0.84) * math.sqrt(2 / n_min)
            else:
                mde = float("inf")

        quality = "δ≤0.03" if mde <= 0.03 else "δ≤0.05" if mde <= 0.05 else "δ≤0.08" if mde <= 0.08 else "δ≤0.10" if mde <= 0.10 else "δ≤0.15" if mde <= 0.15 else "underpowered"
        print(f"{name:>40s}  {n_min:>6d}  {mde:>14.4f}  {quality:>15s}")


def main():
    records = load_data()
    print(f"Loaded {len(records)} evaluations, {len(set(r['task_id'] for r in records))} tasks")

    icc, deff = compute_icc_deff(records)
    print(f"ICC={icc:.3f}, DEFF={deff:.2f} (effective n = {len(records)/deff:.0f})")

    factor_results = analyze_factors(records, deff)
    interaction_analysis(records, deff)
    cross_tab_coverage(records)
    minimum_subset_design(records, factor_results, deff)


if __name__ == "__main__":
    main()
