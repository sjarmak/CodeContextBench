"""Report generator for the Agent Reliability Observatory.

Aggregates annotations into a Markdown reliability report with a JSON
companion file containing machine-readable statistics.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _load_taxonomy_polarity() -> dict[str, str]:
    """Return a mapping of category name -> polarity from the taxonomy."""
    try:
        from observatory.taxonomy import load_taxonomy
        tax = load_taxonomy()
        return {c["name"]: c["polarity"] for c in tax["categories"]}
    except Exception:
        return {}


def _corpus_stats(annotations: list[dict]) -> dict[str, Any]:
    """Compute top-level corpus statistics."""
    total = len(annotations)
    passed = sum(1 for a in annotations if a.get("passed"))
    failed = total - passed
    rewards = [a["reward"] for a in annotations if a.get("reward") is not None]
    avg_reward = sum(rewards) / len(rewards) if rewards else 0.0

    configs = set()
    benchmarks = set()
    for a in annotations:
        if a.get("config_name"):
            configs.add(a["config_name"])
        if a.get("benchmark"):
            benchmarks.add(a["benchmark"])

    return {
        "total_trials": total,
        "passed": passed,
        "failed": failed,
        "pass_rate": round(passed / total, 4) if total else 0,
        "avg_reward": round(avg_reward, 4),
        "configs": sorted(configs),
        "benchmarks": sorted(benchmarks),
    }


def _category_counts(annotations: list[dict]) -> dict[str, int]:
    """Count how many trials are assigned each category."""
    counts: Counter = Counter()
    for a in annotations:
        for cat in a.get("categories", []):
            counts[cat["name"]] += 1
    return dict(counts.most_common())


def _category_by_config(annotations: list[dict]) -> dict[str, dict[str, int]]:
    """Nested dict: config_name -> category_name -> count."""
    result: dict[str, dict[str, int]] = defaultdict(lambda: Counter())
    for a in annotations:
        cfg = a.get("config_name") or "unknown"
        for cat in a.get("categories", []):
            result[cfg][cat["name"]] += 1
    # Convert counters to plain dicts, sorted
    return {k: dict(sorted(v.items(), key=lambda x: -x[1])) for k, v in sorted(result.items())}


def _category_by_suite(annotations: list[dict]) -> dict[str, dict[str, int]]:
    """Nested dict: benchmark_suite -> category_name -> count."""
    result: dict[str, dict[str, int]] = defaultdict(lambda: Counter())
    for a in annotations:
        suite = a.get("benchmark") or "unknown"
        for cat in a.get("categories", []):
            result[suite][cat["name"]] += 1
    # Convert counters to plain dicts, sorted by total count desc
    return {k: dict(sorted(v.items(), key=lambda x: -x[1]))
            for k, v in sorted(result.items(), key=lambda x: -sum(x[1].values()))}


def _core_task_name(trial_path: str) -> str:
    """Extract canonical task name from trial_path for cross-config pairing.

    Trial dirs follow the pattern ``{prefix}_{task}__{hash}`` or ``{task}__{hash}``.
    Strips config-specific prefixes (bl_, mcp_, sgonly_, baseline_) and the
    trailing ``__hash`` to produce a case-insensitive key.
    """
    trial_dir = trial_path.rstrip("/").rsplit("/", 1)[-1]
    # Strip __hash suffix
    if "__" in trial_dir:
        trial_dir = trial_dir.rsplit("__", 1)[0]
    # Strip known config-specific prefixes
    for prefix in ("baseline_", "bl_", "mcp_", "sgonly_"):
        if trial_dir.startswith(prefix):
            trial_dir = trial_dir[len(prefix):]
            break
    return trial_dir.lower()


def _paired_comparison(annotations: list[dict]) -> list[dict]:
    """Compare failure-mode deltas between config pairs on shared tasks.

    For each pair of configs that share >= 20 tasks, compute per-category
    delta = count_in_A - count_in_B.  Returns a list of pair dicts with
    the top 5 categories in each direction (fixed-by-B and introduced-by-B).
    """
    # Group annotations by (core_task, config) → set of category names
    task_config_cats: dict[tuple[str, str], set[str]] = defaultdict(set)
    for a in annotations:
        cfg = a.get("config_name")
        path = a.get("trial_path", "")
        if not cfg or not path:
            continue
        core = _core_task_name(path)
        for cat in a.get("categories", []):
            task_config_cats[(core, cfg)].add(cat["name"])

    # Build per-task -> configs that ran it
    task_configs: dict[str, set[str]] = defaultdict(set)
    for (core, cfg) in task_config_cats:
        task_configs[core].add(cfg)

    # Only consider tasks with 2+ configs
    multi_config_tasks = {t: cfgs for t, cfgs in task_configs.items() if len(cfgs) >= 2}

    # For each config pair, compute deltas
    all_configs = sorted({cfg for cfgs in multi_config_tasks.values() for cfg in cfgs})
    pair_results = []

    for i, cfg_a in enumerate(all_configs):
        for cfg_b in all_configs[i + 1:]:
            # Find shared tasks
            shared = [t for t in multi_config_tasks
                       if cfg_a in multi_config_tasks[t] and cfg_b in multi_config_tasks[t]]
            if len(shared) < 20:
                continue

            # Delta: positive = more in A, negative = more in B
            delta: Counter = Counter()
            for task in shared:
                cats_a = task_config_cats.get((task, cfg_a), set())
                cats_b = task_config_cats.get((task, cfg_b), set())
                for cat in cats_a - cats_b:
                    delta[cat] += 1
                for cat in cats_b - cats_a:
                    delta[cat] -= 1

            # Top 5 where A has more (introduced by A / fixed by B)
            introduced_by_a = sorted(
                [(cat, cnt) for cat, cnt in delta.items() if cnt > 0],
                key=lambda x: -x[1],
            )[:5]
            # Top 5 where B has more (introduced by B / fixed by A)
            introduced_by_b = sorted(
                [(cat, cnt) for cat, cnt in delta.items() if cnt < 0],
                key=lambda x: x[1],
            )[:5]

            pair_results.append({
                "config_a": cfg_a,
                "config_b": cfg_b,
                "shared_tasks": len(shared),
                "introduced_by_a": [{"category": c, "delta": d} for c, d in introduced_by_a],
                "introduced_by_b": [{"category": c, "delta": abs(d)} for c, d in introduced_by_b],
            })

    # Sort by number of shared tasks descending
    pair_results.sort(key=lambda x: -x["shared_tasks"])
    return pair_results


def _top_categories_with_examples(
    annotations: list[dict],
    polarity_map: dict[str, str],
    polarity: str,
    top_n: int = 3,
    examples_per: int = 2,
) -> list[dict]:
    """Get top N categories of given polarity with example trials."""
    # Count by polarity
    counts: Counter = Counter()
    cat_trials: dict[str, list[dict]] = defaultdict(list)

    for a in annotations:
        for cat in a.get("categories", []):
            name = cat["name"]
            if polarity_map.get(name) == polarity:
                counts[name] += 1
                cat_trials[name].append({
                    "task_id": a.get("task_id", "unknown"),
                    "config_name": a.get("config_name", "unknown"),
                    "reward": a.get("reward", 0),
                    "evidence": cat.get("evidence", ""),
                })

    results = []
    for name, count in counts.most_common(top_n):
        examples = cat_trials[name][:examples_per]
        results.append({"name": name, "count": count, "examples": examples})
    return results


def _render_markdown(
    stats: dict,
    cat_counts: dict[str, int],
    cat_by_config: dict[str, dict[str, int]],
    cat_by_suite: dict[str, dict[str, int]],
    top_failures: list[dict],
    top_successes: list[dict],
    polarity_map: dict[str, str],
    generated_at: str,
    paired_comparisons: list[dict] | None = None,
) -> str:
    """Render the Markdown reliability report."""
    lines: list[str] = []

    # Header
    lines.append("# Agent Reliability Observatory — Report")
    lines.append("")
    lines.append(f"Generated: {generated_at}")
    lines.append("")

    # Corpus Stats
    lines.append("## Corpus Statistics")
    lines.append("")
    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Total annotated trials | {stats['total_trials']:,} |")
    lines.append(f"| Passed | {stats['passed']:,} |")
    lines.append(f"| Failed | {stats['failed']:,} |")
    lines.append(f"| Pass rate | {stats['pass_rate']:.1%} |")
    lines.append(f"| Average reward | {stats['avg_reward']:.4f} |")
    lines.append(f"| Configs | {len(stats['configs'])} |")
    lines.append(f"| Benchmarks | {len(stats['benchmarks'])} |")
    lines.append("")

    # Category Frequency
    lines.append("## Category Frequency")
    lines.append("")
    lines.append("| # | Category | Polarity | Count |")
    lines.append("|---|----------|----------|-------|")
    for i, (name, count) in enumerate(cat_counts.items(), 1):
        pol = polarity_map.get(name, "unknown")
        lines.append(f"| {i} | {name} | {pol} | {count:,} |")
    lines.append("")

    # Config Breakdown
    lines.append("## Category Breakdown by Config")
    lines.append("")
    for cfg, cats in cat_by_config.items():
        lines.append(f"### {cfg}")
        lines.append("")
        lines.append("| Category | Count |")
        lines.append("|----------|-------|")
        for name, count in cats.items():
            lines.append(f"| {name} | {count:,} |")
        lines.append("")

    # Configuration Comparison (Paired)
    if paired_comparisons:
        lines.append("## Configuration Comparison (Paired)")
        lines.append("")
        lines.append("Compares failure-mode categories between config pairs on shared tasks.")
        lines.append("Deltas show how many more shared tasks had a category in one config vs the other.")
        lines.append("")
        for pair in paired_comparisons:
            lines.append(
                f"### {pair['config_a']} vs {pair['config_b']} "
                f"({pair['shared_tasks']} shared tasks)"
            )
            lines.append("")
            if pair["introduced_by_a"]:
                lines.append(f"**More frequent in {pair['config_a']}:**")
                lines.append("")
                lines.append("| Category | Delta |")
                lines.append("|----------|-------|")
                for item in pair["introduced_by_a"]:
                    lines.append(f"| {item['category']} | +{item['delta']} |")
                lines.append("")
            if pair["introduced_by_b"]:
                lines.append(f"**More frequent in {pair['config_b']}:**")
                lines.append("")
                lines.append("| Category | Delta |")
                lines.append("|----------|-------|")
                for item in pair["introduced_by_b"]:
                    lines.append(f"| {item['category']} | +{item['delta']} |")
                lines.append("")

    # Suite Breakdown (top 10 suites by annotation volume)
    lines.append("## Category Breakdown by Benchmark Suite (Top 10)")
    lines.append("")
    for i, (suite, cats) in enumerate(cat_by_suite.items()):
        if i >= 10:
            break
        total = sum(cats.values())
        lines.append(f"### {suite} ({total:,} annotations)")
        lines.append("")
        lines.append("| Category | Count |")
        lines.append("|----------|-------|")
        for name, count in list(cats.items())[:8]:  # Top 8 per suite
            lines.append(f"| {name} | {count:,} |")
        lines.append("")

    # Top Failure Categories
    lines.append("## Top Failure Categories")
    lines.append("")
    for entry in top_failures:
        lines.append(f"### {entry['name']} ({entry['count']:,} trials)")
        lines.append("")
        for ex in entry["examples"]:
            lines.append(
                f"- **{ex['task_id']}** (config: {ex['config_name']}, "
                f"reward: {ex['reward']:.2f}): {ex['evidence']}"
            )
        lines.append("")

    # Success Mode Summary
    lines.append("## Success Mode Summary")
    lines.append("")
    if top_successes:
        for entry in top_successes:
            lines.append(f"### {entry['name']} ({entry['count']:,} trials)")
            lines.append("")
            for ex in entry["examples"]:
                lines.append(
                    f"- **{ex['task_id']}** (config: {ex['config_name']}, "
                    f"reward: {ex['reward']:.2f}): {ex['evidence']}"
                )
            lines.append("")
    else:
        lines.append("No success-mode annotations found in this corpus.")
        lines.append("")

    return "\n".join(lines)


def generate_report(annotations: dict, output_dir: Path) -> tuple[Path, Path]:
    """Generate a Markdown reliability report and JSON companion.

    Parameters
    ----------
    annotations : dict
        Full annotation document matching annotation_schema.json.
    output_dir : Path
        Directory where reliability_report.md and .json will be written.

    Returns
    -------
    tuple[Path, Path]
        Paths to the generated .md and .json files.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    ann_list = annotations.get("annotations", [])
    polarity_map = _load_taxonomy_polarity()
    generated_at = datetime.now(timezone.utc).isoformat()

    stats = _corpus_stats(ann_list)
    cat_counts = _category_counts(ann_list)
    cat_by_config = _category_by_config(ann_list)
    cat_by_suite = _category_by_suite(ann_list)
    top_failures = _top_categories_with_examples(ann_list, polarity_map, "failure")
    top_successes = _top_categories_with_examples(ann_list, polarity_map, "success")
    paired_comparisons = _paired_comparison(ann_list)

    # Markdown report
    md_content = _render_markdown(
        stats, cat_counts, cat_by_config, cat_by_suite,
        top_failures, top_successes,
        polarity_map, generated_at,
        paired_comparisons=paired_comparisons,
    )
    md_path = output_dir / "reliability_report.md"
    md_path.write_text(md_content)

    # JSON companion
    json_data = {
        "generated_at": generated_at,
        "corpus_stats": stats,
        "category_counts": cat_counts,
        "category_by_config": cat_by_config,
        "category_by_suite": cat_by_suite,
        "paired_comparisons": paired_comparisons,
    }
    json_path = output_dir / "reliability_report.json"
    with open(json_path, "w") as f:
        json.dump(json_data, f, indent=2)

    return md_path, json_path
