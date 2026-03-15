#!/usr/bin/env python3
"""Analyze whether higher-token sessions produce better reward scores.

Scans runs/official/_raw/ for trial-level result.json files, extracts
token counts and reward scores, computes correlations, quintile analysis,
and token efficiency comparisons between baseline and MCP configs.

Output: results/analysis/token_cost_quality.json
"""

import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy import stats

RAW_DIR = Path(__file__).resolve().parents[2] / "runs" / "official" / "_raw"
OUT_FILE = Path(__file__).resolve().parents[2] / "results" / "analysis" / "token_cost_quality.json"

# Config classification: map directory names to baseline vs mcp
BASELINE_KEYWORDS = {"baseline", "baseline-local-direct", "baseline-local-artifact"}
MCP_KEYWORDS = {"mcp", "mcp-remote-direct", "mcp-remote-artifact", "sourcegraph", "sourcegraph_full", "sourcegraph_base"}

# Suite extraction from run directory name
SUITE_PATTERN = re.compile(
    r"(csb_(?:sdlc|org)_[a-z_]+|ccb_(?:sdlc|org)_[a-z_]+|"
    r"ccb_(?:mcp_)?(?:build|debug|document|feature|fix|refactor|secure|test|understand|"
    r"compliance|crossorg|crossrepo|crossrepo_tracing|dep_trace|domain|incident|"
    r"onboarding|org|platform|security|vuln_remed))"
)


def classify_config(path_parts: list[str]) -> str | None:
    """Determine if trial is baseline or mcp from directory path components."""
    for part in path_parts:
        low = part.lower()
        if any(kw == low for kw in BASELINE_KEYWORDS):
            return "baseline"
        if any(kw == low for kw in MCP_KEYWORDS):
            return "mcp"
        # Daytona flat dirs: check for mcp_ or baseline_ prefix in trial dir
        if "mcp-remote" in low or "mcp_" in low:
            return "mcp"
        if "baseline-local" in low or low.startswith("bl_"):
            return "baseline"
        if "sgonly_" in low or "sourcegraph" in low:
            return "mcp"
    return None


def extract_suite(run_dir_name: str) -> str:
    """Extract suite name from the top-level run directory name."""
    m = SUITE_PATTERN.search(run_dir_name)
    if m:
        suite = m.group(1)
        # Normalize ccb_ -> csb_ prefixes
        suite = re.sub(r"^ccb_mcp_", "csb_org_", suite)
        suite = re.sub(r"^ccb_(build|debug|document|feature|fix|refactor|secure|test|understand)",
                       r"csb_sdlc_\1", suite)
        suite = re.sub(r"^ccb_(sdlc|org)_", r"csb_\1_", suite)
        return suite

    # Fallback: try to get work type from dir name
    for wt in ["build", "debug", "document", "feature", "fix", "refactor",
                "secure", "test", "understand", "compliance", "crossorg",
                "crossrepo_tracing", "crossrepo", "dep_trace", "domain",
                "incident", "onboarding", "org", "platform", "security",
                "vuln_remed"]:
        if wt in run_dir_name.lower():
            if any(x in run_dir_name.lower() for x in ["org", "ccx", "compliance", "crossorg",
                                                         "crossrepo", "dep_trace", "domain",
                                                         "incident", "onboarding", "platform",
                                                         "security", "vuln_remed"]):
                return f"csb_org_{wt}"
            return f"csb_sdlc_{wt}"
    return "unknown"


def collect_trials() -> list[dict]:
    """Walk _raw/ and collect trial data from result.json files."""
    trials = []
    seen = set()

    for root, dirs, files in os.walk(RAW_DIR):
        # Skip dirs that cause permission issues or are irrelevant
        basename = os.path.basename(root)
        if basename in ("agent", "sessions", "projects"):
            dirs.clear()
            continue
        # Skip explicit error/archive dirs at top level only
        if basename in ("__errored_tasks", "_archived_errors", "_errored"):
            dirs.clear()
            continue

        if "result.json" not in files:
            continue

        result_path = os.path.join(root, "result.json")
        try:
            with open(result_path) as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue

        # Must be a trial-level result (has agent_result with tokens)
        ar = data.get("agent_result")
        if not ar or not isinstance(ar, dict):
            continue

        n_input = ar.get("n_input_tokens")
        n_output = ar.get("n_output_tokens")
        if n_input is None or n_output is None:
            continue

        vr = data.get("verifier_result")
        if not vr or not isinstance(vr, dict):
            continue
        rewards = vr.get("rewards")
        if not rewards or not isinstance(rewards, dict):
            continue
        reward = rewards.get("reward")
        if reward is None:
            continue

        total_tokens = (n_input or 0) + (n_output or 0)
        if total_tokens == 0:
            continue

        # Extract path components relative to _raw/
        rel = os.path.relpath(root, RAW_DIR)
        parts = rel.split(os.sep)

        # Run dir is the first component
        run_dir = parts[0] if parts else ""

        config_type = classify_config(parts)
        if config_type is None:
            # Try from task_name prefix
            task_name = data.get("task_name", "")
            if task_name.startswith("mcp_") or task_name.startswith("sgonly_"):
                config_type = "mcp"
            elif task_name.startswith("bl_"):
                config_type = "baseline"
            else:
                config_type = "unknown"

        suite = extract_suite(run_dir)

        # Deduplicate by trial id
        trial_id = data.get("id", result_path)
        if trial_id in seen:
            continue
        seen.add(trial_id)

        trials.append({
            "path": result_path,
            "n_input_tokens": n_input,
            "n_output_tokens": n_output,
            "n_cache_tokens": ar.get("n_cache_tokens", 0) or 0,
            "total_tokens": total_tokens,
            "reward": float(reward),
            "config": config_type,
            "suite": suite,
            "cost_usd": ar.get("cost_usd"),
            "run_dir": run_dir,
        })

    return trials


def compute_correlations(tokens: np.ndarray, rewards: np.ndarray) -> dict:
    """Compute Pearson and Spearman correlations with p-values."""
    if len(tokens) < 3:
        return {"pearson_r": None, "pearson_p": None,
                "spearman_rho": None, "spearman_p": None, "n": len(tokens)}

    pr, pp = stats.pearsonr(tokens, rewards)
    sr, sp = stats.spearmanr(tokens, rewards)
    return {
        "pearson_r": round(float(pr), 4),
        "pearson_p": float(f"{pp:.2e}"),
        "spearman_rho": round(float(sr), 4),
        "spearman_p": float(f"{sp:.2e}"),
        "n": int(len(tokens)),
    }


def quintile_analysis(tokens: np.ndarray, rewards: np.ndarray,
                      configs: np.ndarray | None = None) -> list[dict]:
    """Bin by token count quintiles, compute mean reward per bin."""
    if len(tokens) == 0:
        return []

    quintile_edges = np.percentile(tokens, [0, 20, 40, 60, 80, 100])
    bins = []

    for i in range(5):
        lo, hi = quintile_edges[i], quintile_edges[i + 1]
        if i == 4:
            mask = (tokens >= lo) & (tokens <= hi)
        else:
            mask = (tokens >= lo) & (tokens < hi)

        if mask.sum() == 0:
            continue

        bin_rewards = rewards[mask]
        bin_tokens = tokens[mask]

        entry = {
            "quintile": i + 1,
            "token_range": [int(lo), int(hi)],
            "n": int(mask.sum()),
            "mean_reward": round(float(bin_rewards.mean()), 4),
            "std_reward": round(float(bin_rewards.std()), 4),
            "median_reward": round(float(np.median(bin_rewards)), 4),
            "mean_tokens": int(bin_tokens.mean()),
        }

        # Per-config breakdown if provided
        if configs is not None:
            for cfg in ["baseline", "mcp"]:
                cfg_mask = mask & (configs == cfg)
                if cfg_mask.sum() > 0:
                    entry[f"mean_reward_{cfg}"] = round(float(rewards[cfg_mask].mean()), 4)
                    entry[f"n_{cfg}"] = int(cfg_mask.sum())

        bins.append(entry)

    return bins


def token_efficiency(trials: list[dict]) -> dict:
    """Compare reward per 1K tokens between baseline and MCP."""
    result = {}
    for cfg in ["baseline", "mcp"]:
        subset = [t for t in trials if t["config"] == cfg]
        if not subset:
            continue
        rewards = np.array([t["reward"] for t in subset])
        tokens = np.array([t["total_tokens"] for t in subset])

        # Reward per 1K tokens
        efficiency = rewards / (tokens / 1000.0)

        result[cfg] = {
            "n": len(subset),
            "mean_reward": round(float(rewards.mean()), 4),
            "mean_total_tokens": int(tokens.mean()),
            "median_total_tokens": int(np.median(tokens)),
            "mean_reward_per_1k_tokens": round(float(efficiency.mean()), 6),
            "median_reward_per_1k_tokens": round(float(np.median(efficiency)), 6),
            "mean_input_tokens": int(np.mean([t["n_input_tokens"] for t in subset])),
            "mean_output_tokens": int(np.mean([t["n_output_tokens"] for t in subset])),
        }

    if "baseline" in result and "mcp" in result:
        bl_eff = result["baseline"]["mean_reward_per_1k_tokens"]
        mcp_eff = result["mcp"]["mean_reward_per_1k_tokens"]
        result["efficiency_ratio_mcp_over_bl"] = round(mcp_eff / bl_eff, 4) if bl_eff > 0 else None
        result["delta_mean_reward"] = round(
            result["mcp"]["mean_reward"] - result["baseline"]["mean_reward"], 4
        )

    return result


def suite_breakdown(trials: list[dict]) -> dict:
    """Per-suite correlation and efficiency."""
    by_suite = defaultdict(list)
    for t in trials:
        by_suite[t["suite"]].append(t)

    breakdown = {}
    for suite, subset in sorted(by_suite.items()):
        if len(subset) < 5:
            continue
        tokens = np.array([t["total_tokens"] for t in subset])
        rewards = np.array([t["reward"] for t in subset])
        corr = compute_correlations(tokens, rewards)
        eff = token_efficiency(subset)
        breakdown[suite] = {
            "n": len(subset),
            "correlation": corr,
            "efficiency": eff,
        }

    return breakdown


def scatter_summary(tokens: np.ndarray, rewards: np.ndarray, n_bins: int = 20) -> list[dict]:
    """Create binned scatter data summary."""
    if len(tokens) == 0:
        return []

    # Log-spaced bins for better distribution
    log_tokens = np.log10(tokens + 1)
    bin_edges = np.linspace(log_tokens.min(), log_tokens.max(), n_bins + 1)
    bins = []

    for i in range(n_bins):
        lo, hi = bin_edges[i], bin_edges[i + 1]
        if i == n_bins - 1:
            mask = (log_tokens >= lo) & (log_tokens <= hi)
        else:
            mask = (log_tokens >= lo) & (log_tokens < hi)

        if mask.sum() == 0:
            continue

        bin_rewards = rewards[mask]
        bin_tokens = tokens[mask]

        bins.append({
            "token_bin_center": int(10 ** ((lo + hi) / 2)),
            "token_range": [int(10 ** lo), int(10 ** hi)],
            "n": int(mask.sum()),
            "mean_reward": round(float(bin_rewards.mean()), 4),
            "std_reward": round(float(bin_rewards.std()), 4),
            "mean_tokens": int(bin_tokens.mean()),
        })

    return bins


def main():
    print("Collecting trials from", RAW_DIR)
    trials = collect_trials()
    print(f"Found {len(trials)} valid trials with token data and reward scores")

    if not trials:
        print("ERROR: No valid trials found")
        sys.exit(1)

    # Filter out unknown configs for config-specific analysis
    known_config_trials = [t for t in trials if t["config"] in ("baseline", "mcp")]
    print(f"  baseline: {sum(1 for t in trials if t['config'] == 'baseline')}")
    print(f"  mcp: {sum(1 for t in trials if t['config'] == 'mcp')}")
    print(f"  unknown config: {sum(1 for t in trials if t['config'] == 'unknown')}")

    tokens_all = np.array([t["total_tokens"] for t in trials])
    rewards_all = np.array([t["reward"] for t in trials])
    configs_all = np.array([t["config"] for t in trials])

    # 1. Overall correlations
    overall_corr = compute_correlations(tokens_all, rewards_all)
    print(f"\nOverall correlation (n={overall_corr['n']}):")
    print(f"  Pearson r={overall_corr['pearson_r']}, p={overall_corr['pearson_p']}")
    print(f"  Spearman rho={overall_corr['spearman_rho']}, p={overall_corr['spearman_p']}")

    # Per-config correlations
    config_corr = {}
    for cfg in ["baseline", "mcp"]:
        subset = [t for t in trials if t["config"] == cfg]
        if len(subset) >= 3:
            t_arr = np.array([t["total_tokens"] for t in subset])
            r_arr = np.array([t["reward"] for t in subset])
            config_corr[cfg] = compute_correlations(t_arr, r_arr)

    # 2. Quintile analysis
    quintiles_overall = quintile_analysis(tokens_all, rewards_all, configs_all)
    print("\nQuintile analysis:")
    for q in quintiles_overall:
        print(f"  Q{q['quintile']}: tokens {q['token_range']}, "
              f"mean_reward={q['mean_reward']:.4f}, n={q['n']}")

    # Per-config quintiles
    quintiles_by_config = {}
    for cfg in ["baseline", "mcp"]:
        subset = [t for t in trials if t["config"] == cfg]
        if len(subset) >= 10:
            t_arr = np.array([t["total_tokens"] for t in subset])
            r_arr = np.array([t["reward"] for t in subset])
            quintiles_by_config[cfg] = quintile_analysis(t_arr, r_arr)

    # 3. Token efficiency comparison
    efficiency = token_efficiency(trials)
    print("\nToken efficiency:")
    for cfg in ["baseline", "mcp"]:
        if cfg in efficiency:
            e = efficiency[cfg]
            print(f"  {cfg}: mean_reward={e['mean_reward']:.4f}, "
                  f"mean_tokens={e['mean_total_tokens']}, "
                  f"reward/1K_tokens={e['mean_reward_per_1k_tokens']:.6f}")

    # 4. Suite breakdown
    suite_data = suite_breakdown(trials)

    # 5. Scatter summary
    scatter = scatter_summary(tokens_all, rewards_all)

    # 6. Diminishing returns: check if marginal reward gain decreases
    diminishing_returns = {}
    if len(quintiles_overall) >= 3:
        rewards_by_q = [q["mean_reward"] for q in quintiles_overall]
        marginal_gains = [rewards_by_q[i] - rewards_by_q[i - 1]
                          for i in range(1, len(rewards_by_q))]
        diminishing_returns = {
            "quintile_mean_rewards": rewards_by_q,
            "marginal_gains_q_to_q": [round(g, 4) for g in marginal_gains],
            "shows_diminishing_returns": (
                len(marginal_gains) >= 3 and
                marginal_gains[-1] < marginal_gains[0]
            ),
            "interpretation": (
                "Diminishing returns detected: later quintiles show smaller "
                "marginal gains than earlier ones"
                if (len(marginal_gains) >= 3 and marginal_gains[-1] < marginal_gains[0])
                else "No clear diminishing returns pattern"
            ),
        }

    # Assemble report
    report = {
        "metadata": {
            "total_trials": len(trials),
            "trials_with_known_config": len(known_config_trials),
            "baseline_trials": sum(1 for t in trials if t["config"] == "baseline"),
            "mcp_trials": sum(1 for t in trials if t["config"] == "mcp"),
            "unknown_config_trials": sum(1 for t in trials if t["config"] == "unknown"),
            "unique_suites": len(set(t["suite"] for t in trials)),
            "token_stats": {
                "min": int(tokens_all.min()),
                "max": int(tokens_all.max()),
                "mean": int(tokens_all.mean()),
                "median": int(np.median(tokens_all)),
                "std": int(tokens_all.std()),
            },
            "reward_stats": {
                "min": round(float(rewards_all.min()), 4),
                "max": round(float(rewards_all.max()), 4),
                "mean": round(float(rewards_all.mean()), 4),
                "median": round(float(np.median(rewards_all)), 4),
            },
        },
        "overall_correlation": overall_corr,
        "per_config_correlation": config_corr,
        "quintile_analysis": {
            "overall": quintiles_overall,
            "by_config": quintiles_by_config,
        },
        "diminishing_returns": diminishing_returns,
        "token_efficiency_comparison": efficiency,
        "suite_breakdown": suite_data,
        "scatter_data_summary": scatter,
    }

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_FILE, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\nReport written to {OUT_FILE}")
    return report


if __name__ == "__main__":
    main()
