#!/usr/bin/env python3
"""Analyze which MCP tool sequences correlate with higher reward scores.

Scans MCP trial directories in runs/official/_raw/, extracts tool call
sequences from trajectory.json, classifies each trial by dominant search
strategy, and correlates with reward scores from result.json.

Output: results/analysis/search_strategy_correlation.json
"""

import json
import os
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "runs" / "official" / "_raw"
OUT_FILE = ROOT / "results" / "analysis" / "search_strategy_correlation.json"

# MCP tool categories
KEYWORD_TOOLS = {"mcp__sourcegraph__sg_keyword_search", "mcp__sg_keyword_search"}
SEMANTIC_TOOLS = {"mcp__sourcegraph__sg_nls_search", "mcp__sg_nls_search"}
DEFINITION_TOOLS = {
    "mcp__sourcegraph__sg_read_file",
    "mcp__sg_read_file",
    "mcp__sourcegraph__sg_list_files",
    "mcp__sg_list_files",
    "mcp__sourcegraph__sg_go_to_definition",
    "mcp__sg_go_to_definition",
    "mcp__sourcegraph__sg_find_references",
    "mcp__sg_find_references",
    "mcp__sourcegraph__sg_grep",
    "mcp__sg_grep",
}
DIFF_TOOLS = {
    "mcp__sourcegraph__sg_diff_search",
    "mcp__sg_diff_search",
    "mcp__sourcegraph__sg_commit_search",
    "mcp__sg_commit_search",
    "mcp__sourcegraph__sg_compare_revisions",
    "mcp__sg_compare_revisions",
}
ALL_MCP_TOOLS = KEYWORD_TOOLS | SEMANTIC_TOOLS | DEFINITION_TOOLS | DIFF_TOOLS | {
    "mcp__sourcegraph__sg_list_repos",
    "mcp__sg_list_repos",
}

# Suite extraction from run directory name
SUITE_PREFIXES = [
    "csb_org_crossrepo_tracing",
    "csb_org_crossrepo",
    "csb_org_crossorg",
    "csb_org_compliance",
    "csb_org_domain",
    "csb_org_incident",
    "csb_org_onboarding",
    "csb_org_org",
    "csb_org_platform",
    "csb_org_security",
    "csb_sdlc_build",
    "csb_sdlc_debug",
    "csb_sdlc_document",
    "csb_sdlc_feature",
    "csb_sdlc_fix",
    "csb_sdlc_refactor",
    "csb_sdlc_secure",
    "csb_sdlc_test",
    "csb_sdlc_understand",
]

# Legacy prefixes
LEGACY_PREFIXES = {
    "understand": "csb_sdlc_understand",
    "secure": "csb_sdlc_secure",
    "test": "csb_sdlc_test",
    "linuxflbench": "csb_sdlc_debug",
    "bigcode": "csb_sdlc_feature",
    "openhands": "other",
}


def extract_suite(run_dir_name: str) -> str:
    """Extract suite name from the run directory name."""
    lower = run_dir_name.lower()
    for prefix in SUITE_PREFIXES:
        if prefix in lower:
            return prefix
    for legacy, mapped in LEGACY_PREFIXES.items():
        if lower.startswith(legacy):
            return mapped
    # Try old ccb_ prefix
    for prefix in SUITE_PREFIXES:
        ccb_variant = prefix.replace("csb_", "ccb_")
        if ccb_variant in lower:
            return prefix
    return "other"


def find_mcp_trial_dirs() -> list[tuple[Path, str]]:
    """Find all MCP trial directories (trajectory.json + result.json pairs).

    Returns list of (trial_dir, suite) tuples.
    """
    trials = []

    if not RAW_DIR.exists():
        print(f"ERROR: {RAW_DIR} does not exist", file=sys.stderr)
        return trials

    for run_dir in RAW_DIR.iterdir():
        if not run_dir.is_dir():
            continue
        run_name = run_dir.name
        suite = extract_suite(run_name)

        # Find MCP config dirs
        for config_dir in run_dir.iterdir():
            if not config_dir.is_dir():
                continue
            config_name = config_dir.name.lower()
            if "mcp" not in config_name and "sourcegraph" not in config_name and "sg" not in config_name:
                continue
            if config_name == "retrieval_events":
                continue

            # Traverse timestamp dirs -> trial dirs
            for ts_dir in config_dir.iterdir():
                if not ts_dir.is_dir():
                    continue
                for trial_dir in ts_dir.iterdir():
                    if not trial_dir.is_dir():
                        continue
                    traj = trial_dir / "agent" / "trajectory.json"
                    result = trial_dir / "result.json"
                    if traj.exists() and result.exists():
                        trials.append((trial_dir, suite))

    return trials


def extract_mcp_tools(trajectory_path: Path) -> list[str]:
    """Extract ordered list of MCP tool calls from trajectory."""
    try:
        with open(trajectory_path) as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return []

    tools = []
    for step in data.get("steps", []):
        for tc in step.get("tool_calls", []):
            fn = tc.get("function_name", "")
            if fn.startswith("mcp__"):
                tools.append(fn)
    return tools


def classify_strategy(mcp_tools: list[str]) -> str:
    """Classify the dominant search strategy from an ordered tool list."""
    if not mcp_tools:
        return "no_mcp_tools"

    counts = Counter()
    for tool in mcp_tools:
        if tool in KEYWORD_TOOLS:
            counts["keyword"] += 1
        elif tool in SEMANTIC_TOOLS:
            counts["semantic"] += 1
        elif tool in DEFINITION_TOOLS:
            counts["definition"] += 1
        elif tool in DIFF_TOOLS:
            counts["diff"] += 1

    search_counts = {k: v for k, v in counts.items() if k in ("keyword", "semantic", "diff")}

    if not search_counts:
        return "definition_only"

    total_search = sum(search_counts.values())
    dominant = max(search_counts, key=search_counts.get)
    dominant_frac = search_counts[dominant] / total_search

    if dominant_frac >= 0.6:
        return dominant
    return "mixed"


def get_reward(result_path: Path) -> float | None:
    """Extract reward score from result.json."""
    try:
        with open(result_path) as f:
            data = json.load(f)
        vr = data.get("verifier_result")
        if not isinstance(vr, dict):
            return None
        rewards = vr.get("rewards")
        if not isinstance(rewards, dict):
            return None
        reward = rewards.get("reward")
        if reward is not None:
            return float(reward)
    except (json.JSONDecodeError, OSError, TypeError, ValueError):
        pass
    return None


def tool_sequence_key(mcp_tools: list[str], max_len: int = 8) -> str:
    """Create a compact key for the first N MCP tool calls."""
    short_names = []
    for t in mcp_tools[:max_len]:
        name = t.replace("mcp__sourcegraph__sg_", "").replace("mcp__sg_", "")
        short_names.append(name)
    return " -> ".join(short_names) if short_names else "(empty)"


def main():
    print("Finding MCP trial directories...")
    all_trials = find_mcp_trial_dirs()
    print(f"Found {len(all_trials)} MCP trials with trajectory + result pairs")

    # Sample 200 if more available
    max_sample = 200
    if len(all_trials) > max_sample:
        random.seed(42)
        sampled = random.sample(all_trials, max_sample)
    else:
        sampled = all_trials

    print(f"Sampling {len(sampled)} trials for analysis...")

    # Process trials
    results = []
    for trial_dir, suite in sampled:
        traj_path = trial_dir / "agent" / "trajectory.json"
        result_path = trial_dir / "result.json"

        mcp_tools = extract_mcp_tools(traj_path)
        reward = get_reward(result_path)

        if reward is None:
            continue

        strategy = classify_strategy(mcp_tools)
        seq_key = tool_sequence_key(mcp_tools)

        tool_counts = Counter()
        for t in mcp_tools:
            short = t.replace("mcp__sourcegraph__sg_", "").replace("mcp__sg_", "")
            tool_counts[short] += 1

        results.append({
            "trial_dir": str(trial_dir.relative_to(ROOT)),
            "suite": suite,
            "strategy": strategy,
            "reward": reward,
            "n_mcp_calls": len(mcp_tools),
            "tool_counts": dict(tool_counts),
            "sequence_key": seq_key,
        })

    print(f"Processed {len(results)} trials with valid rewards")

    # === Aggregate by strategy (overall) ===
    strategy_stats = defaultdict(lambda: {"rewards": [], "count": 0})
    for r in results:
        s = strategy_stats[r["strategy"]]
        s["rewards"].append(r["reward"])
        s["count"] += 1

    overall_by_strategy = {}
    for strat, info in sorted(strategy_stats.items()):
        rewards = info["rewards"]
        overall_by_strategy[strat] = {
            "count": info["count"],
            "mean_reward": round(sum(rewards) / len(rewards), 4) if rewards else 0,
            "median_reward": round(sorted(rewards)[len(rewards) // 2], 4) if rewards else 0,
            "min_reward": round(min(rewards), 4) if rewards else 0,
            "max_reward": round(max(rewards), 4) if rewards else 0,
        }

    # === Aggregate by strategy + suite ===
    suite_strategy_stats = defaultdict(lambda: defaultdict(lambda: {"rewards": [], "count": 0}))
    for r in results:
        s = suite_strategy_stats[r["suite"]][r["strategy"]]
        s["rewards"].append(r["reward"])
        s["count"] += 1

    per_suite = {}
    for suite in sorted(suite_strategy_stats):
        per_suite[suite] = {}
        for strat, info in sorted(suite_strategy_stats[suite].items()):
            rewards = info["rewards"]
            per_suite[suite][strat] = {
                "count": info["count"],
                "mean_reward": round(sum(rewards) / len(rewards), 4) if rewards else 0,
            }

    # === Top 10 tool sequences by mean reward (min 2 occurrences) ===
    seq_stats = defaultdict(lambda: {"rewards": [], "count": 0, "strategies": []})
    for r in results:
        s = seq_stats[r["sequence_key"]]
        s["rewards"].append(r["reward"])
        s["count"] += 1
        s["strategies"].append(r["strategy"])

    # Filter to sequences with >= 2 occurrences, then sort by mean reward
    seq_ranked = []
    for seq_key, info in seq_stats.items():
        if info["count"] >= 2:
            mean_r = sum(info["rewards"]) / len(info["rewards"])
            seq_ranked.append({
                "sequence": seq_key,
                "count": info["count"],
                "mean_reward": round(mean_r, 4),
                "dominant_strategy": Counter(info["strategies"]).most_common(1)[0][0],
            })

    seq_ranked.sort(key=lambda x: x["mean_reward"], reverse=True)
    top_sequences = seq_ranked[:10]

    # === Tool-level correlation ===
    # For each MCP tool, compute mean reward of trials that used it
    tool_reward = defaultdict(list)
    for r in results:
        for tool in set(r["tool_counts"].keys()):
            tool_reward[tool].append(r["reward"])

    tool_correlations = {}
    for tool in sorted(tool_reward):
        rewards = tool_reward[tool]
        tool_correlations[tool] = {
            "n_trials_using": len(rewards),
            "mean_reward": round(sum(rewards) / len(rewards), 4),
        }

    # === Average MCP calls per strategy ===
    calls_by_strategy = defaultdict(list)
    for r in results:
        calls_by_strategy[r["strategy"]].append(r["n_mcp_calls"])

    avg_calls = {}
    for strat in sorted(calls_by_strategy):
        calls = calls_by_strategy[strat]
        avg_calls[strat] = round(sum(calls) / len(calls), 1)

    # === Build report ===
    report = {
        "metadata": {
            "total_mcp_trials_found": len(all_trials),
            "sampled": len(sampled),
            "valid_scored": len(results),
            "sample_seed": 42,
        },
        "overall_by_strategy": overall_by_strategy,
        "avg_mcp_calls_by_strategy": avg_calls,
        "tool_level_correlations": tool_correlations,
        "per_suite_breakdown": per_suite,
        "top_10_sequences_by_mean_reward": top_sequences,
    }

    # Write output
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_FILE, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\nReport written to {OUT_FILE}")

    # Print summary
    print("\n=== Overall Strategy Comparison ===")
    for strat, info in sorted(overall_by_strategy.items(), key=lambda x: x[1]["mean_reward"], reverse=True):
        print(f"  {strat:20s}  n={info['count']:3d}  mean={info['mean_reward']:.4f}  "
              f"median={info['median_reward']:.4f}  range=[{info['min_reward']:.2f}, {info['max_reward']:.2f}]")

    print("\n=== Average MCP Calls by Strategy ===")
    for strat, avg in sorted(avg_calls.items(), key=lambda x: x[1], reverse=True):
        print(f"  {strat:20s}  avg_calls={avg:.1f}")

    print("\n=== Tool-Level Correlations ===")
    for tool, info in sorted(tool_correlations.items(), key=lambda x: x[1]["mean_reward"], reverse=True):
        print(f"  {tool:25s}  n={info['n_trials_using']:3d}  mean_reward={info['mean_reward']:.4f}")

    print("\n=== Top 10 Sequences (min 2 occurrences) ===")
    for i, seq in enumerate(top_sequences, 1):
        print(f"  {i:2d}. [{seq['dominant_strategy']}] n={seq['count']} mean={seq['mean_reward']:.4f}")
        print(f"      {seq['sequence']}")


if __name__ == "__main__":
    main()
