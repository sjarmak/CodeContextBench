#!/usr/bin/env python3
"""Analyze what CodeScaleBench can currently claim about harness differences.

Focus:
  - reward outcomes
  - time and token efficiency
  - TTFR and cost summaries where available
  - whether regrouping suites improves inferential power
  - minimal task or repo additions needed for stronger claims
"""

from __future__ import annotations

import json
import math
import re
from collections import defaultdict
from functools import lru_cache
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parent.parent
OFFICIAL_RESULTS = ROOT / "docs" / "official_results" / "data" / "official_results.json"
SELECTED_TASKS = ROOT / "configs" / "selected_benchmark_tasks.json"
IR_RESULTS = ROOT / "results" / "ir" / "retrieval_metrics_promoted.json"
COST_ANALYSIS_DIR = ROOT / "docs" / "analysis"

CURRENT_3_CATEGORY = {
    "csb_sdlc_understand": "comprehension",
    "csb_sdlc_design": "comprehension",
    "csb_sdlc_document": "comprehension",
    "csb_sdlc_feature": "implementation",
    "csb_sdlc_refactor": "implementation",
    "csb_sdlc_fix": "implementation",
    "csb_sdlc_debug": "quality",
    "csb_sdlc_test": "quality",
    "csb_sdlc_secure": "quality",
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

DISCOVERY_VS_EXECUTION = {
    "csb_sdlc_understand": "discovery",
    "csb_sdlc_design": "discovery",
    "csb_sdlc_document": "discovery",
    "csb_org_onboarding": "discovery",
    "csb_org_domain": "discovery",
    "csb_org_org": "discovery",
    "csb_org_crossrepo": "discovery",
    "csb_org_crossrepo_tracing": "discovery",
    "csb_org_crossorg": "discovery",
    "csb_sdlc_feature": "execution",
    "csb_sdlc_refactor": "execution",
    "csb_sdlc_fix": "execution",
    "csb_sdlc_debug": "execution",
    "csb_sdlc_test": "execution",
    "csb_sdlc_secure": "execution",
    "csb_org_incident": "execution",
    "csb_org_security": "execution",
    "csb_org_compliance": "execution",
    "csb_org_migration": "execution",
    "csb_org_platform": "execution",
}

FOUR_WAY = {
    "csb_sdlc_understand": "discovery",
    "csb_sdlc_design": "discovery",
    "csb_sdlc_document": "discovery",
    "csb_org_onboarding": "discovery",
    "csb_org_domain": "discovery",
    "csb_org_org": "discovery",
    "csb_org_crossrepo": "discovery",
    "csb_org_crossrepo_tracing": "discovery",
    "csb_org_crossorg": "discovery",
    "csb_sdlc_feature": "change",
    "csb_sdlc_refactor": "change",
    "csb_sdlc_fix": "change",
    "csb_org_migration": "change",
    "csb_org_platform": "change",
    "csb_sdlc_debug": "assurance",
    "csb_sdlc_test": "assurance",
    "csb_sdlc_secure": "assurance",
    "csb_org_security": "assurance",
    "csb_org_compliance": "assurance",
    "csb_org_incident": "incident",
}


def section(title: str) -> None:
    print(f"\n{'=' * 96}")
    print(title)
    print("=" * 96)


def normalize_task_id(raw: str) -> str:
    task_id = (raw or "").split("/")[-1].strip().lower()
    task_id = re.sub(r"^(mcp_|bl_|sgonly_)", "", task_id)
    task_id = re.sub(r"_[a-z0-9]{4,8}$", "", task_id)
    return task_id


def side_from_config(config: str) -> str:
    return "mcp" if "mcp" in (config or "") else "bl"


def family_from_config(config: str) -> str:
    name = (config or "").lower()
    if "artifact" in name:
        return "artifact"
    if "direct" in name:
        return "direct"
    return "other"


def mde(sd: float, n: int, alpha: float = 0.05, power: float = 0.80) -> float:
    if n <= 0:
        return float("inf")
    z_alpha = 1.96 if alpha == 0.05 else 2.58
    z_beta = 0.84 if power == 0.80 else 1.28
    return (z_alpha + z_beta) * sd / math.sqrt(n)


def n_for_delta(sd: float, delta: float, alpha: float = 0.05, power: float = 0.80) -> int:
    if delta <= 0:
        return 999999
    z_alpha = 1.96 if alpha == 0.05 else 2.58
    z_beta = 0.84 if power == 0.80 else 1.28
    return math.ceil(((z_alpha + z_beta) * sd / delta) ** 2)


def mean_sd(values: list[float]) -> tuple[float, float]:
    arr = np.asarray(values, dtype=float)
    if arr.size == 0:
        return float("nan"), float("nan")
    if arr.size == 1:
        return float(arr[0]), 0.0
    return float(arr.mean()), float(arr.std(ddof=1))


def load_selected_repo_map() -> dict[tuple[str, str], str]:
    doc = json.loads(SELECTED_TASKS.read_text())
    return {
        (task["benchmark"], str(task["task_id"]).lower()): str(task.get("repo") or "")
        for task in doc["tasks"]
    }


def latest_analysis_file(pattern: str) -> Path:
    matches = sorted(COST_ANALYSIS_DIR.glob(pattern))
    if not matches:
        raise FileNotFoundError(f"No analysis files match {pattern!r} in {COST_ANALYSIS_DIR}")
    return matches[-1]


def build_task_pairs(repo_map: dict[tuple[str, str], str]) -> list[dict]:
    doc = json.loads(OFFICIAL_RESULTS.read_text())
    grouped = defaultdict(lambda: {"bl": [], "mcp": [], "suite": None, "task_id": None, "family": None})

    for task in doc["all_tasks"]:
        reward = task.get("reward")
        if reward is None:
            continue
        family = family_from_config(task.get("config", ""))
        if family not in {"artifact", "direct"}:
            continue

        suite = task.get("suite") or "unknown"
        task_id = normalize_task_id(task.get("benchmark_path", ""))
        key = (suite, task_id, family)
        grouped[key]["suite"] = suite
        grouped[key]["task_id"] = task_id
        grouped[key]["family"] = family
        grouped[key][side_from_config(task.get("config", ""))].append(task)

    pairs = []
    for (suite, task_id, _family), sides in grouped.items():
        if not sides["bl"] or not sides["mcp"]:
            continue

        row = {
            "suite": suite,
            "task_id": task_id,
            "family": sides["family"],
            "repo": repo_map.get((suite, task_id), ""),
            "category3": CURRENT_3_CATEGORY.get(suite, "unknown"),
            "category2": DISCOVERY_VS_EXECUTION.get(suite, "unknown"),
            "category4": FOUR_WAY.get(suite, "unknown"),
        }

        for metric in ("reward", "agent_execution_seconds", "wall_clock_seconds", "input_tokens"):
            bl_mean = float(np.mean([entry.get(metric) or 0 for entry in sides["bl"]]))
            mcp_mean = float(np.mean([entry.get(metric) or 0 for entry in sides["mcp"]]))
            row[f"bl_{metric}"] = bl_mean
            row[f"mcp_{metric}"] = mcp_mean
            row[f"d_{metric}"] = mcp_mean - bl_mean

        pairs.append(row)

    return pairs


def load_cost_summary() -> dict[str, dict]:
    doc = json.loads(latest_analysis_file("ir_and_cost_by_suite_*.json").read_text())
    return doc["cost_by_suite"]


def load_ttfr_summary() -> tuple[dict, dict]:
    doc = json.loads(IR_RESULTS.read_text())
    return doc.get("overall", {}), doc.get("by_config", {})


def print_effect_table(rows: list[dict], label: str, metric: str, unit: str = "") -> None:
    values = [row[f"d_{metric}"] for row in rows]
    bl_vals = [row[f"bl_{metric}"] for row in rows]
    mcp_vals = [row[f"mcp_{metric}"] for row in rows]
    mean_delta, sd_delta = mean_sd(values)
    suffix = unit or ""
    if metric == "reward":
        print(
            f"{label:>18s}  n={len(values):>3d}  "
            f"BL={np.mean(bl_vals):>10.4f}{suffix}  MCP={np.mean(mcp_vals):>10.4f}{suffix}  "
            f"Δ={mean_delta:+10.4f}{suffix}  sd={sd_delta:>10.4f}{suffix}  MDE={mde(sd_delta, len(values)):>10.4f}{suffix}"
        )
    elif "tokens" in metric:
        print(
            f"{label:>18s}  n={len(values):>3d}  "
            f"BL={np.mean(bl_vals):>10.0f}{suffix}  MCP={np.mean(mcp_vals):>10.0f}{suffix}  "
            f"Δ={mean_delta:>+10.0f}{suffix}  sd={sd_delta:>10.0f}{suffix}  MDE={mde(sd_delta, len(values)):>10.0f}{suffix}"
        )
    else:
        print(
            f"{label:>18s}  n={len(values):>3d}  "
            f"BL={np.mean(bl_vals):>10.1f}{suffix}  MCP={np.mean(mcp_vals):>10.1f}{suffix}  "
            f"Δ={mean_delta:+10.1f}{suffix}  sd={sd_delta:>10.1f}{suffix}  MDE={mde(sd_delta, len(values)):>10.1f}{suffix}"
        )


def print_repo_effect_table(rows: list[dict], label: str, metric: str, unit: str = "") -> None:
    by_repo = defaultdict(list)
    for row in rows:
        repo = row["repo"]
        if repo:
            by_repo[repo].append(row[f"d_{metric}"])

    repo_means = [float(np.mean(vals)) for vals in by_repo.values()]
    mean_delta, sd_delta = mean_sd(repo_means)
    suffix = unit or ""
    if metric == "reward":
        print(
            f"{label:>18s}  repos={len(repo_means):>3d}  "
            f"Δ={mean_delta:+10.4f}{suffix}  sd={sd_delta:>10.4f}{suffix}  "
            f"MDE={mde(sd_delta, len(repo_means)):>10.4f}{suffix}  n@obs={n_for_delta(sd_delta, abs(mean_delta)):>4d}"
        )
    elif "tokens" in metric:
        print(
            f"{label:>18s}  repos={len(repo_means):>3d}  "
            f"Δ={mean_delta:>+10.0f}{suffix}  sd={sd_delta:>10.0f}{suffix}  "
            f"MDE={mde(sd_delta, len(repo_means)):>10.0f}{suffix}  n@obs={n_for_delta(sd_delta, abs(mean_delta)):>4d}"
        )
    else:
        print(
            f"{label:>18s}  repos={len(repo_means):>3d}  "
            f"Δ={mean_delta:>+10.1f}{suffix}  sd={sd_delta:>10.1f}{suffix}  "
            f"MDE={mde(sd_delta, len(repo_means)):>10.1f}{suffix}  n@obs={n_for_delta(sd_delta, abs(mean_delta)):>4d}"
        )


def summarize_grouping(rows: list[dict], group_field: str, name: str) -> None:
    section(f"Grouping: {name}")
    grouped = defaultdict(list)
    for row in rows:
        grouped[row[group_field]].append(row["d_reward"])

    print(f"{'Group':>18s}  {'n':>4s}  {'Δ reward':>10s}  {'sd':>9s}  {'MDE':>9s}  {'n@obs':>6s}")
    print("-" * 72)
    for group_name in sorted(grouped):
        delta, sd = mean_sd(grouped[group_name])
        n = len(grouped[group_name])
        need = n_for_delta(sd, abs(delta))
        print(f"{group_name:>18s}  {n:>4d}  {delta:>+10.4f}  {sd:>9.4f}  {mde(sd, n):>9.4f}  {need:>6d}")


def best_contiguous_partitions(rows: list[dict], k: int) -> list[dict]:
    suite_values = defaultdict(list)
    for row in rows:
        suite_values[row["suite"]].append(row["d_reward"])

    ordered_suites = sorted(suite_values, key=lambda suite: np.mean(suite_values[suite]))
    interval = {}
    arrays = [np.asarray(suite_values[suite], dtype=float) for suite in ordered_suites]

    for start in range(len(ordered_suites)):
        merged = []
        for end in range(start, len(ordered_suites)):
            merged.extend(arrays[end])
            arr = np.asarray(merged, dtype=float)
            interval[(start, end)] = {
                "suites": ordered_suites[start:end + 1],
                "n": int(arr.size),
                "mean": float(arr.mean()),
                "sd": float(arr.std(ddof=1)) if arr.size > 1 else 0.0,
                "sse": float(np.sum((arr - arr.mean()) ** 2)),
            }

    @lru_cache(maxsize=None)
    def solve(start: int, groups_left: int) -> tuple[float, tuple[tuple[int, int], ...]]:
        if groups_left == 1:
            return interval[(start, len(ordered_suites) - 1)]["sse"], ((start, len(ordered_suites) - 1),)

        best_score = float("inf")
        best_split: tuple[tuple[int, int], ...] | None = None
        max_end = len(ordered_suites) - groups_left
        for end in range(start, max_end + 1):
            score_rest, split_rest = solve(end + 1, groups_left - 1)
            score = interval[(start, end)]["sse"] + score_rest
            if score < best_score:
                best_score = score
                best_split = ((start, end),) + split_rest

        assert best_split is not None
        return best_score, best_split

    _, split = solve(0, k)
    return [interval[idx] for idx in split]


def print_data_driven_groupings(rows: list[dict]) -> None:
    section("Data-Driven Upper Bound (Post Hoc Only)")
    for k in (2, 3, 4):
        print(f"\n{k} contiguous groups after sorting suites by observed reward delta:")
        parts = best_contiguous_partitions(rows, k)
        for part in parts:
            print(
                f"  n={part['n']:>3d}  Δ={part['mean']:+.4f}  sd={part['sd']:.4f}  "
                f"MDE={mde(part['sd'], part['n']):.4f}  suites={', '.join(part['suites'])}"
            )


def weighted_category_costs(cost_by_suite: dict[str, dict], mapping: dict[str, str]) -> dict[str, dict]:
    grouped = defaultdict(lambda: {"n": 0, "pair_cost_sum": 0.0})
    for suite, stats in cost_by_suite.items():
        category = mapping[suite]
        n = int(stats["n"])
        pair_cost = float(stats["baseline_cost_mean_usd"]) + float(stats["mcp_cost_mean_usd"])
        grouped[category]["n"] += n
        grouped[category]["pair_cost_sum"] += n * pair_cost

    out = {}
    for category, stats in grouped.items():
        out[category] = {
            "n": stats["n"],
            "mean_pair_cost_usd": stats["pair_cost_sum"] / stats["n"] if stats["n"] else float("nan"),
        }
    return out


def weighted_category_pair_time(rows: list[dict], group_field: str) -> dict[str, float]:
    grouped = defaultdict(list)
    for row in rows:
        grouped[row[group_field]].append(row["bl_agent_execution_seconds"] + row["mcp_agent_execution_seconds"])
    return {group: float(np.mean(vals)) for group, vals in grouped.items()}


def print_expansion_plan(rows: list[dict], group_field: str, mapping_name: str, cost_by_suite: dict[str, dict]) -> None:
    section(f"Expansion Plan: {mapping_name}")
    grouped = defaultdict(list)
    for row in rows:
        grouped[row[group_field]].append(row["d_reward"])

    category_costs = weighted_category_costs(cost_by_suite, CURRENT_3_CATEGORY)
    pair_times = weighted_category_pair_time(rows, "category3")

    print(
        f"{'Group':>18s}  {'Current':>7s}  {'Need@obs':>8s}  {'Add@obs':>7s}  "
        f"{'Need@0.05':>9s}  {'Add@0.05':>8s}  {'Pair$':>7s}  {'Add$@obs':>10s}  {'AddHours@obs':>12s}"
    )
    print("-" * 112)
    for group_name in sorted(grouped):
        delta, sd = mean_sd(grouped[group_name])
        current_n = len(grouped[group_name])
        need_obs = n_for_delta(sd, abs(delta))
        need_005 = n_for_delta(sd, 0.05)
        add_obs = max(0, need_obs - current_n)
        add_005 = max(0, need_005 - current_n)

        # Cost/time are only canonical for the current 3-category mapping.
        pair_cost = category_costs.get(group_name, {}).get("mean_pair_cost_usd")
        pair_hours = pair_times.get(group_name, float("nan")) / 3600.0
        add_cost = add_obs * pair_cost if pair_cost == pair_cost else float("nan")
        add_hours = add_obs * pair_hours if pair_hours == pair_hours else float("nan")

        print(
            f"{group_name:>18s}  {current_n:>7d}  {need_obs:>8d}  {add_obs:>7d}  "
            f"{need_005:>9d}  {add_005:>8d}  {pair_cost:>7.3f}  {add_cost:>10.1f}  {add_hours:>12.1f}"
        )


def print_repo_expansion(rows: list[dict], group_field: str, mapping_name: str, cost_by_suite: dict[str, dict]) -> None:
    section(f"Repo-Level Expansion: {mapping_name}")
    category_costs = weighted_category_costs(cost_by_suite, CURRENT_3_CATEGORY)
    pair_times = weighted_category_pair_time(rows, "category3")

    print(
        f"{'Group':>18s}  {'Repos':>6s}  {'Need@obs':>8s}  {'AddRepos':>8s}  "
        f"{'Need@0.05':>9s}  {'Add@0.05':>8s}  {'Pair$':>7s}  {'Add$@obs':>10s}"
    )
    print("-" * 104)

    grouped = defaultdict(lambda: defaultdict(list))
    for row in rows:
        repo = row["repo"]
        if repo:
            grouped[row[group_field]][repo].append(row["d_reward"])

    for group_name in sorted(grouped):
        repo_means = [float(np.mean(vals)) for vals in grouped[group_name].values()]
        delta, sd = mean_sd(repo_means)
        current_n = len(repo_means)
        need_obs = n_for_delta(sd, abs(delta))
        need_005 = n_for_delta(sd, 0.05)
        add_obs = max(0, need_obs - current_n)
        add_005 = max(0, need_005 - current_n)
        pair_cost = category_costs.get(group_name, {}).get("mean_pair_cost_usd")
        add_cost = add_obs * pair_cost if pair_cost == pair_cost else float("nan")

        print(
            f"{group_name:>18s}  {current_n:>6d}  {need_obs:>8d}  {add_obs:>8d}  "
            f"{need_005:>9d}  {add_005:>8d}  {pair_cost:>7.3f}  {add_cost:>10.1f}"
        )

    overall_pair_cost = sum(v["mean_pair_cost_usd"] * v["n"] for v in category_costs.values()) / sum(v["n"] for v in category_costs.values())
    overall_pair_hours = sum(pair_times[g] * len([row for row in rows if row["category3"] == g]) for g in pair_times) / (3600.0 * len(rows))
    overall_grouped = defaultdict(list)
    for row in rows:
        if row["repo"]:
            overall_grouped[row["repo"]].append(row["d_reward"])
    overall_means = [float(np.mean(vals)) for vals in overall_grouped.values()]
    overall_delta, overall_sd = mean_sd(overall_means)
    need_obs = n_for_delta(overall_sd, abs(overall_delta))
    need_005 = n_for_delta(overall_sd, 0.05)
    add_obs = max(0, need_obs - len(overall_means))
    add_005 = max(0, need_005 - len(overall_means))
    print(
        f"\n{'overall':>18s}  {len(overall_means):>6d}  {need_obs:>8d}  {add_obs:>8d}  "
        f"{need_005:>9d}  {add_005:>8d}  {overall_pair_cost:>7.3f}  {add_obs * overall_pair_cost:>10.1f}"
    )
    print(f"{'':>18s}  {'':>6s}  {'':>8s}  {'':>8s}  {'':>9s}  {'':>8s}  {'':>7s}  {'pair-hours@overall='}{overall_pair_hours:.2f}")


def main() -> None:
    repo_map = load_selected_repo_map()
    rows = build_task_pairs(repo_map)
    cost_by_suite = load_cost_summary()
    ttfr_overall, ttfr_by_config = load_ttfr_summary()

    section("Dataset")
    unique_repos = len({row["repo"] for row in rows if row["repo"]})
    print(f"Paired tasks: {len(rows)}")
    print(f"Unique repos in paired task set: {unique_repos}")
    print(f"Suites: {len({row['suite'] for row in rows})}")

    section("Task-Unit Claims")
    print_effect_table(rows, "reward", "reward")
    print_effect_table(rows, "agent_seconds", "agent_execution_seconds", "s")
    print_effect_table(rows, "wall_seconds", "wall_clock_seconds", "s")
    print_effect_table(rows, "input_tokens", "input_tokens")

    section("Repo-Unit Claims")
    print_repo_effect_table(rows, "reward", "reward")
    print_repo_effect_table(rows, "agent_seconds", "agent_execution_seconds", "s")
    print_repo_effect_table(rows, "input_tokens", "input_tokens")

    section("Current Semantic Grouping")
    summarize_grouping(rows, "category3", "Current 3-category mapping")

    section("Alternative Semantic Groupings")
    summarize_grouping(rows, "category2", "Discovery vs Execution")
    summarize_grouping(rows, "category4", "Discovery / Change / Assurance / Incident")

    print_data_driven_groupings(rows)

    section("TTFR Summary")
    ttfr = ttfr_overall.get("ttfr_seconds", {})
    if ttfr:
        print(f"Overall TTFR mean={ttfr.get('mean', float('nan')):.1f}s median={ttfr.get('median', float('nan')):.1f}s n={ttfr.get('n', '?')}")
    for config_name in ("baseline-local-direct", "mcp-remote-direct", "baseline-local-artifact", "mcp-remote-artifact"):
        config_stats = ttfr_by_config.get(config_name, {})
        config_ttfr = config_stats.get("ttfr_seconds")
        if config_ttfr:
            print(f"{config_name:>24s}: mean={config_ttfr.get('mean', float('nan')):.1f}s n={config_ttfr.get('n', '?')}")

    section("Cost Summary")
    weighted = weighted_category_costs(cost_by_suite, CURRENT_3_CATEGORY)
    total_n = sum(stats["n"] for stats in weighted.values())
    overall_pair_cost = sum(stats["mean_pair_cost_usd"] * stats["n"] for stats in weighted.values()) / total_n
    print(f"Weighted mean paired cost (baseline + MCP): ${overall_pair_cost:.3f}")
    for category_name in sorted(weighted):
        print(
            f"{category_name:>18s}: n={weighted[category_name]['n']:>3d}  "
            f"mean pair cost=${weighted[category_name]['mean_pair_cost_usd']:.3f}"
        )

    print_expansion_plan(rows, "category3", "Current 3-category mapping", cost_by_suite)
    print_repo_expansion(rows, "category3", "Current 3-category mapping", cost_by_suite)


if __name__ == "__main__":
    main()
