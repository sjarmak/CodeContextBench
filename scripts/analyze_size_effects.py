#!/usr/bin/env python3
"""Analyze codebase size effects on agent performance.

Runs:
1. OLS regression: reward ~ log(LOC) + language + task_type + config
2. Confound severity: variance inflation factors (VIF-like diagnostics)
3. Neyman allocation: optimal task counts per size stratum
4. Power analysis: minimum n per stratum to detect target effect sizes
5. Minimum balanced subset: smallest set for confident size claims
"""

import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

PROJ_ROOT = Path(__file__).resolve().parent.parent


def load_data():
    """Load official results with cloc-updated LOC."""
    with open(PROJ_ROOT / "docs/official_results/data/official_results.json") as f:
        data = json.load(f)

    records = []
    for t in data["all_tasks"]:
        reward = t.get("reward")
        loc = t.get("repo_approx_loc")
        if reward is None or not loc or loc <= 0:
            continue

        bp = t.get("benchmark_path", "")
        suite = bp.split("/")[1] if "/" in bp else "unknown"
        task_type = "SDLC" if "sdlc" in suite else "Org"

        # Normalize language
        lang = (t.get("repo_primary_language") or "unknown").lower()
        # Bucket rare languages
        if lang in ("c", "c_cpp_headers"):
            lang = "c_cpp"
        elif lang in ("cpp",):
            lang = "c_cpp"
        elif lang in ("csharp",):
            lang = "csharp"
        elif lang in ("javascript", "json"):
            lang = "javascript"
        elif lang not in ("go", "java", "python", "rust", "typescript"):
            lang = "other"

        config = t.get("config", "unknown")
        is_mcp = 1 if "mcp" in config else 0

        # Extract task identity from benchmark_path
        task_id = bp.split("/")[-1] if "/" in bp else bp
        repo = t.get("repo") or ""

        records.append({
            "reward": reward,
            "log_loc": math.log10(loc),
            "loc": loc,
            "lang": lang,
            "task_type": task_type,
            "is_mcp": is_mcp,
            "config": config,
            "suite": suite,
            "task_id": task_id,
            "repo": repo,
        })

    return records


def size_bin(loc):
    if loc < 500_000:
        return "<500K"
    if loc < 2_000_000:
        return "500K-2M"
    if loc < 5_000_000:
        return "2M-5M"
    if loc < 10_000_000:
        return "5M-10M"
    return "10M+"


SIZE_BIN_ORDER = ["<500K", "500K-2M", "2M-5M", "5M-10M", "10M+"]


def ols_regression(records):
    """Manual OLS with dummy encoding (no sklearn/statsmodels dependency)."""
    # Design matrix: intercept, log_loc, is_mcp, language dummies, task_type dummy
    langs = sorted(set(r["lang"] for r in records))
    ref_lang = "go"  # reference category (most common)
    lang_dummies = [l for l in langs if l != ref_lang]

    n = len(records)
    p = 1 + 1 + 1 + len(lang_dummies) + 1  # intercept + log_loc + is_mcp + lang dummies + task_type
    feature_names = ["intercept", "log(LOC)", "is_mcp"] + [f"lang_{l}" for l in lang_dummies] + ["is_org"]

    X = np.zeros((n, p))
    y = np.array([r["reward"] for r in records])

    for i, r in enumerate(records):
        X[i, 0] = 1.0  # intercept
        X[i, 1] = r["log_loc"]
        X[i, 2] = r["is_mcp"]
        for j, l in enumerate(lang_dummies):
            X[i, 3 + j] = 1.0 if r["lang"] == l else 0.0
        X[i, -1] = 1.0 if r["task_type"] == "Org" else 0.0

    # OLS: beta = (X'X)^-1 X'y
    XtX = X.T @ X
    try:
        XtX_inv = np.linalg.inv(XtX)
    except np.linalg.LinAlgError:
        print("ERROR: Singular matrix, cannot compute OLS")
        return None

    beta = XtX_inv @ (X.T @ y)
    y_hat = X @ beta
    residuals = y - y_hat
    sse = residuals @ residuals
    sst = np.sum((y - np.mean(y)) ** 2)
    r_squared = 1 - sse / sst
    adj_r_squared = 1 - (1 - r_squared) * (n - 1) / (n - p)

    # Standard errors
    mse = sse / (n - p)
    se = np.sqrt(np.diag(XtX_inv) * mse)
    t_stats = beta / se

    # Partial R² for each feature (type III SS)
    partial_r2 = {}
    for j in range(1, p):  # skip intercept
        # Drop column j, refit
        X_reduced = np.delete(X, j, axis=1)
        try:
            beta_r = np.linalg.inv(X_reduced.T @ X_reduced) @ (X_reduced.T @ y)
            sse_r = np.sum((y - X_reduced @ beta_r) ** 2)
            partial_r2[feature_names[j]] = (sse_r - sse) / sse_r
        except np.linalg.LinAlgError:
            partial_r2[feature_names[j]] = float("nan")

    return {
        "beta": beta,
        "se": se,
        "t_stats": t_stats,
        "feature_names": feature_names,
        "r_squared": r_squared,
        "adj_r_squared": adj_r_squared,
        "n": n,
        "p": p,
        "partial_r2": partial_r2,
        "mse": mse,
    }


def confound_analysis(records):
    """Check how much size overlaps with language and task type."""
    print("\n" + "=" * 80)
    print("2. CONFOUND SEVERITY")
    print("=" * 80)

    # Cramér's V between size_bin and language
    size_bins = [size_bin(r["loc"]) for r in records]
    langs = [r["lang"] for r in records]
    task_types = [r["task_type"] for r in records]

    def cramers_v(cat1, cat2):
        ct = defaultdict(lambda: defaultdict(int))
        for a, b in zip(cat1, cat2):
            ct[a][b] += 1
        n = len(cat1)
        r = len(set(cat1))
        c = len(set(cat2))
        row_totals = {a: sum(ct[a].values()) for a in ct}
        col_totals = defaultdict(int)
        for a in ct:
            for b in ct[a]:
                col_totals[b] += ct[a][b]
        chi2 = 0
        for a in ct:
            for b in ct[a]:
                expected = row_totals[a] * col_totals[b] / n
                if expected > 0:
                    chi2 += (ct[a][b] - expected) ** 2 / expected
        return math.sqrt(chi2 / (n * (min(r, c) - 1))) if min(r, c) > 1 else 0

    v_size_lang = cramers_v(size_bins, langs)
    v_size_type = cramers_v(size_bins, task_types)
    v_lang_type = cramers_v(langs, task_types)

    print(f"\nCramér's V (association strength, 0=none, 1=perfect):")
    print(f"  size_bin × language:  {v_size_lang:.3f}  {'STRONG' if v_size_lang > 0.3 else 'moderate' if v_size_lang > 0.15 else 'weak'}")
    print(f"  size_bin × task_type: {v_size_type:.3f}  {'STRONG' if v_size_type > 0.3 else 'moderate' if v_size_type > 0.15 else 'weak'}")
    print(f"  language × task_type: {v_lang_type:.3f}  {'STRONG' if v_lang_type > 0.3 else 'moderate' if v_lang_type > 0.15 else 'weak'}")

    # Correlation between log_loc and is_mcp (should be ~0 by design)
    log_locs = np.array([r["log_loc"] for r in records])
    mcps = np.array([r["is_mcp"] for r in records])
    corr_loc_mcp = np.corrcoef(log_locs, mcps)[0, 1]
    print(f"\n  Pearson r(log_LOC, is_mcp): {corr_loc_mcp:.4f}  (should be ~0 by paired design)")

    return v_size_lang, v_size_type


def neyman_allocation(records):
    """Optimal task allocation across size strata (Neyman allocation)."""
    print("\n" + "=" * 80)
    print("3. NEYMAN ALLOCATION")
    print("=" * 80)

    # Group by size bin, compute within-stratum variance
    strata = defaultdict(list)
    for r in records:
        b = size_bin(r["loc"])
        strata[b].append(r["reward"])

    print(f"\n{'Stratum':>12s}  {'n':>5s}  {'mean':>6s}  {'std':>6s}  {'N*σ':>8s}  {'Neyman%':>8s}  {'Current%':>9s}  {'Gap':>6s}")
    print("-" * 80)

    total_n = sum(len(v) for v in strata.values())
    Ns_sigma = {}
    for b in SIZE_BIN_ORDER:
        vals = strata.get(b, [])
        n = len(vals)
        mu = np.mean(vals) if vals else 0
        sigma = np.std(vals, ddof=1) if len(vals) > 1 else 0
        Ns_sigma[b] = n * sigma  # N_h * sigma_h
        # Note: using current n as population proxy

    total_Ns = sum(Ns_sigma.values())

    for b in SIZE_BIN_ORDER:
        vals = strata.get(b, [])
        n = len(vals)
        mu = np.mean(vals) if vals else 0
        sigma = np.std(vals, ddof=1) if len(vals) > 1 else 0
        neyman_pct = Ns_sigma[b] / total_Ns * 100 if total_Ns > 0 else 0
        current_pct = n / total_n * 100
        gap = neyman_pct - current_pct
        print(f"{b:>12s}  {n:>5d}  {mu:>6.3f}  {sigma:>6.3f}  {Ns_sigma[b]:>8.1f}  {neyman_pct:>7.1f}%  {current_pct:>8.1f}%  {gap:>+5.1f}%")

    print(f"\nInterpretation: Positive gap = stratum is UNDERsampled (high variance, need more).")
    print(f"                Negative gap = stratum is OVERsampled (can reduce without losing power).")


def power_analysis(records):
    """Minimum n per stratum to detect size effect δ with 80% power."""
    print("\n" + "=" * 80)
    print("4. POWER ANALYSIS")
    print("=" * 80)

    strata = defaultdict(list)
    for r in records:
        b = size_bin(r["loc"])
        strata[b].append(r["reward"])

    # We want to detect a difference δ between adjacent strata
    # Two-sample t-test: n = 2 * (z_α + z_β)² * σ² / δ²
    # α=0.05, β=0.20 (80% power): z_α=1.96, z_β=0.84 → (z_α+z_β)²=7.84
    z_factor = 7.84  # (1.96 + 0.84)^2

    # Pooled variance across all strata
    all_rewards = [r["reward"] for r in records]
    pooled_sigma = np.std(all_rewards, ddof=1)

    print(f"\nPooled σ across all tasks: {pooled_sigma:.4f}")
    print(f"\nMinimum n PER STRATUM for two-sample comparison (α=0.05, power=0.80):")
    print(f"{'Target δ':>12s}  {'n/stratum':>10s}  {'Total (5 strata)':>16s}  {'×2 configs':>12s}")
    print("-" * 60)

    for delta in [0.02, 0.03, 0.05, 0.08, 0.10, 0.15]:
        n_per = math.ceil(2 * z_factor * pooled_sigma ** 2 / delta ** 2)
        total = n_per * 5
        total_x2 = total * 2  # baseline + MCP
        feasible = "✓" if n_per <= 80 else "stretch" if n_per <= 150 else "✗"
        print(f"{delta:>12.2f}  {n_per:>10d}  {total:>16d}  {total_x2:>12d}  {feasible}")

    # Per-stratum analysis
    print(f"\nPer-stratum variance and current vs required n (for δ=0.05):")
    print(f"{'Stratum':>12s}  {'σ':>6s}  {'Current n':>10s}  {'Need (δ=.05)':>13s}  {'Need (δ=.08)':>13s}  {'Status':>10s}")
    print("-" * 75)
    for b in SIZE_BIN_ORDER:
        vals = strata.get(b, [])
        sigma = np.std(vals, ddof=1) if len(vals) > 1 else pooled_sigma
        n_05 = math.ceil(2 * z_factor * sigma ** 2 / 0.05 ** 2)
        n_08 = math.ceil(2 * z_factor * sigma ** 2 / 0.08 ** 2)
        status = "OK" if len(vals) >= n_05 else "MARGINAL" if len(vals) >= n_08 else "UNDER"
        print(f"{b:>12s}  {sigma:>6.3f}  {len(vals):>10d}  {n_05:>13d}  {n_08:>13d}  {status:>10s}")


def repo_clustering_effect(records):
    """Estimate design effect from repo-level clustering."""
    print("\n" + "=" * 80)
    print("5. REPO CLUSTERING (DESIGN EFFECT)")
    print("=" * 80)

    # Tasks from the same repo are not independent — they share codebase characteristics
    # ICC (intraclass correlation) measures how much variance is between-repo vs within-repo
    repo_groups = defaultdict(list)
    for r in records:
        repo_groups[r["repo"] or r["task_id"]].append(r["reward"])

    # One-way ANOVA decomposition
    grand_mean = np.mean([r["reward"] for r in records])
    ss_between = 0
    ss_within = 0
    n_total = 0
    k = 0  # number of groups with >1 obs

    for repo, rewards in repo_groups.items():
        n_j = len(rewards)
        if n_j == 0:
            continue
        n_total += n_j
        group_mean = np.mean(rewards)
        ss_between += n_j * (group_mean - grand_mean) ** 2
        ss_within += sum((r - group_mean) ** 2 for r in rewards)
        if n_j > 1:
            k += 1

    n_groups = len(repo_groups)
    ms_between = ss_between / (n_groups - 1) if n_groups > 1 else 0
    ms_within = ss_within / (n_total - n_groups) if n_total > n_groups else 1

    # Average group size
    avg_n = n_total / n_groups if n_groups > 0 else 1

    # ICC = (MS_between - MS_within) / (MS_between + (avg_n - 1) * MS_within)
    icc = (ms_between - ms_within) / (ms_between + (avg_n - 1) * ms_within) if ms_between + (avg_n - 1) * ms_within > 0 else 0
    icc = max(0, icc)  # truncate negative ICC

    # Design effect = 1 + (avg_cluster_size - 1) * ICC
    deff = 1 + (avg_n - 1) * icc

    # Effective sample size
    n_eff = n_total / deff

    print(f"\n  Unique repos (clusters): {n_groups}")
    print(f"  Avg tasks per repo:      {avg_n:.1f}")
    print(f"  ICC (intraclass corr):   {icc:.3f}")
    print(f"  Design effect (DEFF):    {deff:.2f}")
    print(f"  Nominal n:               {n_total}")
    print(f"  Effective n:             {n_eff:.0f} ({n_eff/n_total*100:.0f}% of nominal)")
    print(f"\n  → Each task is worth ~{1/deff:.2f} independent observations.")
    print(f"  → Power calculations should use n_effective, not nominal n.")

    return icc, deff


def minimum_balanced_set(records, icc, deff):
    """Design the minimum task set for confident size claims."""
    print("\n" + "=" * 80)
    print("6. MINIMUM BALANCED SET")
    print("=" * 80)

    strata = defaultdict(list)
    repo_per_stratum = defaultdict(set)
    for r in records:
        b = size_bin(r["loc"])
        strata[b].append(r)
        repo_per_stratum[b].add(r["repo"] or r["task_id"])

    pooled_sigma = np.std([r["reward"] for r in records], ddof=1)

    # For each target delta, compute minimum n accounting for clustering
    print(f"\nMinimum EFFECTIVE n per stratum (adj for DEFF={deff:.2f}):")
    print(f"{'Target δ':>12s}  {'Eff n/str':>10s}  {'Nominal n/str':>14s}  {'Total tasks':>12s}  {'Unique repos/str':>16s}")
    print("-" * 75)

    for delta in [0.05, 0.08, 0.10]:
        z_factor = 7.84
        n_eff = math.ceil(2 * z_factor * pooled_sigma ** 2 / delta ** 2)
        n_nominal = math.ceil(n_eff * deff)
        # Need enough unique repos to avoid single-repo dominance (>=5)
        min_repos = max(5, math.ceil(n_nominal / 4))  # no repo > 25%
        total = n_nominal * 5 * 2  # 5 strata × 2 configs
        print(f"{delta:>12.2f}  {n_eff:>10d}  {n_nominal:>14d}  {total:>12d}  {min_repos:>16d}")

    # Current feasibility check
    print(f"\nCurrent data vs δ=0.08 requirement:")
    z_factor = 7.84
    target_delta = 0.08

    print(f"{'Stratum':>12s}  {'Have':>5s}  {'Repos':>6s}  {'Need(nom)':>10s}  {'Need(repos)':>12s}  {'Status':>10s}")
    print("-" * 65)

    all_ok = True
    for b in SIZE_BIN_ORDER:
        vals = strata.get(b, [])
        n_have = len(vals)
        n_repos = len(repo_per_stratum.get(b, set()))
        sigma_b = np.std([r["reward"] for r in vals], ddof=1) if len(vals) > 1 else pooled_sigma
        n_eff_need = math.ceil(2 * z_factor * sigma_b ** 2 / target_delta ** 2)
        n_nom_need = math.ceil(n_eff_need * deff)
        min_repos = max(5, math.ceil(n_nom_need / 4))
        ok_n = n_have >= n_nom_need
        ok_r = n_repos >= min_repos
        status = "OK" if ok_n and ok_r else "NEED MORE" if not ok_n else "NEED REPOS"
        if not (ok_n and ok_r):
            all_ok = False
        print(f"{b:>12s}  {n_have:>5d}  {n_repos:>6d}  {n_nom_need:>10d}  {min_repos:>12d}  {status:>10s}")

    if all_ok:
        print(f"\n✓ Current data is SUFFICIENT for δ=0.08 across all strata.")
    else:
        print(f"\n✗ Some strata need more data for δ=0.08.")

    # Suggest minimum trimmed set
    print(f"\n--- Suggested minimum balanced set (δ=0.08, 80% power) ---")
    target_per_stratum = {}
    for b in SIZE_BIN_ORDER:
        vals = strata.get(b, [])
        sigma_b = np.std([r["reward"] for r in vals], ddof=1) if len(vals) > 1 else pooled_sigma
        n_eff_need = math.ceil(2 * z_factor * sigma_b ** 2 / target_delta ** 2)
        n_nom_need = math.ceil(n_eff_need * deff)
        target_per_stratum[b] = max(n_nom_need, 20)  # floor of 20 per stratum

    total_min = sum(target_per_stratum.values())
    print(f"{'Stratum':>12s}  {'Tasks needed':>12s}  {'Currently have':>14s}  {'Can trim':>9s}")
    print("-" * 55)
    total_trim = 0
    for b in SIZE_BIN_ORDER:
        need = target_per_stratum[b]
        have = len(strata.get(b, []))
        trim = max(0, have - need)
        total_trim += trim
        print(f"{b:>12s}  {need:>12d}  {have:>14d}  {trim:>9d}")
    print(f"{'TOTAL':>12s}  {total_min:>12d}  {len(records):>14d}  {total_trim:>9d}")


def main():
    records = load_data()
    print(f"Loaded {len(records)} scored task evaluations")
    print(f"Unique tasks: {len(set(r['task_id'] for r in records))}")
    print(f"Unique repos: {len(set(r['repo'] for r in records))}")

    # 1. OLS Regression
    print("\n" + "=" * 80)
    print("1. OLS REGRESSION: reward ~ log(LOC) + is_mcp + language + task_type")
    print("=" * 80)

    result = ols_regression(records)
    if result:
        print(f"\nn={result['n']}, p={result['p']}")
        print(f"R² = {result['r_squared']:.4f}, Adj R² = {result['adj_r_squared']:.4f}")
        print(f"\n{'Feature':>20s}  {'Coeff':>8s}  {'SE':>8s}  {'t-stat':>8s}  {'|t|>1.96':>9s}  {'Partial R²':>10s}")
        print("-" * 75)
        for i, name in enumerate(result["feature_names"]):
            sig = "***" if abs(result["t_stats"][i]) > 2.58 else "**" if abs(result["t_stats"][i]) > 1.96 else ""
            pr2 = result["partial_r2"].get(name, float("nan"))
            pr2_str = f"{pr2:.4f}" if not math.isnan(pr2) else "   -"
            print(f"{name:>20s}  {result['beta'][i]:>+8.4f}  {result['se'][i]:>8.4f}  {result['t_stats'][i]:>+8.3f}  {sig:>9s}  {pr2_str:>10s}")

        print(f"\nKey finding: log(LOC) coefficient = {result['beta'][1]:+.4f}")
        print(f"  → A 10× increase in LOC is associated with a {result['beta'][1]:+.4f} change in reward")
        print(f"  → Statistical significance: {'YES' if abs(result['t_stats'][1]) > 1.96 else 'NO'} (t={result['t_stats'][1]:+.3f})")
        print(f"  → Partial R² = {result['partial_r2'].get('log(LOC)', 0):.4f} (variance uniquely explained by size)")

    # 2. Confound severity
    v_size_lang, v_size_type = confound_analysis(records)

    # 3. Neyman allocation
    neyman_allocation(records)

    # 4. Power analysis
    power_analysis(records)

    # 5. Repo clustering
    icc, deff = repo_clustering_effect(records)

    # 6. Minimum balanced set
    minimum_balanced_set(records, icc, deff)

    # 7. Summary recommendations
    print("\n" + "=" * 80)
    print("7. RECOMMENDATIONS")
    print("=" * 80)
    print(f"""
Key findings:
  - Size-language confound (Cramér's V={v_size_lang:.3f}): {'problematic' if v_size_lang > 0.3 else 'moderate' if v_size_lang > 0.15 else 'manageable'}
  - Size-tasktype confound (V={v_size_type:.3f}): {'problematic' if v_size_type > 0.3 else 'moderate' if v_size_type > 0.15 else 'manageable'}
  - Repo clustering (ICC={icc:.3f}, DEFF={deff:.2f}): effective n is {1/deff*100:.0f}% of nominal
  - log(LOC) partial R²: {result['partial_r2'].get('log(LOC)', 0):.4f}

Design implications:
  1. If partial R² for log(LOC) is very small (<0.01), codebase size has minimal
     independent effect after controlling for language and task type. The benchmark
     can make claims about "performance on large codebases" but not "size causes
     performance changes."

  2. To strengthen causal claims, prioritize:
     a) Adding Go/Python tasks in 10M+ repos (currently C/C++ dominated)
     b) Adding SDLC tasks in 10M+ repos (currently 91% Org)
     c) Increasing repo diversity in the 2M-5M bin (currently 36% kubernetes)

  3. The repo clustering effect means adding more tasks from the SAME repo has
     diminishing returns. Prefer adding tasks from NEW repos.
""")


if __name__ == "__main__":
    main()
