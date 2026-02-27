#!/usr/bin/env python3
"""Rescore task difficulty in selected_benchmark_tasks.json using a v2 formula.

The v2 model is intentionally constrained to 3 dimensions:
1) codebase size
2) codebase complexity
3) ground-truth knowledge depth
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path


WEIGHTS = {
    "size": 0.40,
    "complexity": 0.35,
    "ground_truth_depth": 0.25,
}

HARD_THRESHOLD = 0.62
EXPERT_THRESHOLD = 0.86

COMPLEXITY_BY_CATEGORY = {
    "dependency_chain_analysis": 0.95,
    "cross_repo_symbol_resolution": 0.92,
    "cross_file_refactoring": 0.85,
    "cross_file_reasoning": 0.84,
    "cross_service_debug": 0.88,
    "deep_causal_chain": 0.90,
    "fault_localization": 0.92,
    "bug_investigation": 0.82,
    "architectural_understanding": 0.86,
    "architecture_qa": 0.80,
    "impact_analysis": 0.78,
    "feature_implementation": 0.76,
    "interface_implementation": 0.74,
    "code_review": 0.68,
    "code-review": 0.68,
    "documentation_generation": 0.58,
    "api_reference": 0.56,
}

GROUND_TRUTH_BY_REWARD_TYPE = {
    "binary": 0.35,
    "test_ratio": 0.45,
    "semantic_similarity": 0.55,
    "f1": 0.58,
    "diff_similarity": 0.68,
    "score": 0.68,
    "continuous": 0.72,
    "checklist": 0.78,
    "partial_credit": 0.80,
    "ir_checklist": 0.86,
    "find_and_prove": 0.90,
}


def _clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(errors="replace")


def _extract_reward_type(task_toml_text: str) -> str | None:
    m = re.search(r'^\s*reward_type\s*=\s*"([^"]+)"\s*$', task_toml_text, flags=re.M)
    return m.group(1).strip().lower() if m else None


def _json_component_count(path: Path) -> int:
    if not path.exists():
        return 0
    try:
        data = json.loads(path.read_text())
    except Exception:
        return 0

    def leaf_count(x: object) -> int:
        if isinstance(x, dict):
            return sum(leaf_count(v) for v in x.values()) if x else 1
        if isinstance(x, list):
            return sum(leaf_count(v) for v in x) if x else 1
        return 1

    return leaf_count(data)


def _ground_truth_bonus(component_count: int, has_criteria: bool, has_oracle: bool) -> float:
    if component_count <= 3:
        comp = 0.02
    elif component_count <= 10:
        comp = 0.05
    elif component_count <= 25:
        comp = 0.09
    else:
        comp = 0.12
    return comp + (0.07 if has_criteria else 0.0) + (0.05 if has_oracle else 0.0)


def _context_norm(context_length: int | float | None) -> float:
    if not context_length:
        return 0.60
    c = float(context_length)
    if c <= 50_000:
        return 0.25
    if c <= 150_000:
        return 0.45
    if c <= 400_000:
        return 0.65
    if c <= 1_000_000:
        return 0.85
    return 1.0


def _files_norm(files_count: int | float | None) -> float:
    if not files_count:
        return 0.55
    f = float(files_count)
    if f <= 5:
        return 0.25
    if f <= 15:
        return 0.45
    if f <= 40:
        return 0.65
    if f <= 100:
        return 0.85
    return 1.0


def _size_score(task: dict) -> float:
    context_score = _context_norm(task.get("context_length"))
    files_score = _files_norm(task.get("files_count"))
    return _clamp(0.70 * context_score + 0.30 * files_score)


def _complexity_from_category(category: str | None) -> float:
    if not category:
        return 0.70
    cat = str(category).strip()
    if cat in COMPLEXITY_BY_CATEGORY:
        return COMPLEXITY_BY_CATEGORY[cat]
    lower = cat.lower()
    if "cross" in lower or "dependency" in lower:
        return 0.82
    if "debug" in lower or "fault" in lower:
        return 0.86
    if "architecture" in lower:
        return 0.83
    if "doc" in lower:
        return 0.58
    if "test" in lower:
        return 0.62
    return 0.70


def _complexity_score(task: dict) -> float:
    breakdown = task.get("mcp_breakdown") or {}
    if isinstance(breakdown, dict) and breakdown:
        cfd = float(breakdown.get("cross_file_deps", 0.70))
        sem = float(breakdown.get("semantic_search_potential", 0.70))
        catw = float(breakdown.get("task_category_weight", _complexity_from_category(task.get("category"))))
        return _clamp(0.50 * cfd + 0.30 * sem + 0.20 * catw)
    return _clamp(_complexity_from_category(task.get("category")))


def _ground_truth_depth_score(task: dict, repo_root: Path) -> float:
    task_dir = task.get("task_dir")
    if not task_dir:
        return 0.60
    abs_task = repo_root / "benchmarks" / str(task_dir)
    task_toml = _read_text(abs_task / "task.toml")
    reward_type = _extract_reward_type(task_toml)
    base = GROUND_TRUTH_BY_REWARD_TYPE.get(reward_type or "", 0.60)

    gt_components = _json_component_count(abs_task / "tests" / "ground_truth.json")
    has_criteria = (abs_task / "tests" / "criteria.json").exists()
    has_oracle = (abs_task / "oracle_answer.json").exists()
    bonus = _ground_truth_bonus(gt_components, has_criteria, has_oracle)
    return _clamp(base + bonus)


def _score(task: dict, repo_root: Path) -> tuple[float, dict[str, float]]:
    size = _size_score(task)
    complexity = _complexity_score(task)
    gt_depth = _ground_truth_depth_score(task, repo_root)
    score = (
        WEIGHTS["size"] * size
        + WEIGHTS["complexity"] * complexity
        + WEIGHTS["ground_truth_depth"] * gt_depth
    )
    score = _clamp(score)
    return score, {
        "size": round(size, 4),
        "complexity": round(complexity, 4),
        "ground_truth_depth": round(gt_depth, 4),
        "score": round(score, 4),
    }


def _label(task: dict, score: float) -> str:
    task_id = str(task.get("task_id", "")).lower()
    benchmark = str(task.get("benchmark", "")).lower()
    if benchmark == "ccb_debug" and task_id.startswith("linux-"):
        return "expert"
    if score >= EXPERT_THRESHOLD:
        return "expert"
    if score >= HARD_THRESHOLD:
        return "hard"
    return "medium"


def _update_metadata(payload: dict) -> None:
    md = payload.setdefault("metadata", {})
    md["last_updated"] = str(date.today())
    meth = payload.setdefault("methodology", {})
    meth["difficulty_formula"] = {
        "version": "2.0",
        "labels": ["medium", "hard", "expert"],
        "dimensions": ["codebase_size", "codebase_complexity", "ground_truth_knowledge_depth"],
        "weights": WEIGHTS,
        "thresholds": {"expert": EXPERT_THRESHOLD, "hard": HARD_THRESHOLD},
        "rule_override": "ccb_debug linux-* tasks are expert",
        "description": (
            "Difficulty is computed from size proxies (context/files), complexity proxies "
            "(cross-file + semantic + category), and ground-truth knowledge depth "
            "(reward_type + GT artifact richness)."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Rescore task difficulties with a deterministic v2 formula.")
    parser.add_argument(
        "--selection",
        default="configs/selected_benchmark_tasks.json",
        help="Path to selected_benchmark_tasks.json",
    )
    parser.add_argument("--write", action="store_true", help="Write changes back to disk")
    parser.add_argument(
        "--emit-breakdown",
        action="store_true",
        help="Write per-task v2 breakdown under task['difficulty_v2_breakdown']",
    )
    args = parser.parse_args()

    path = Path(args.selection)
    repo_root = path.resolve().parent.parent
    data = json.loads(path.read_text())
    tasks = data.get("tasks", [])

    before = Counter(str(t.get("difficulty", "unknown")) for t in tasks)
    changed = 0
    for t in tasks:
        new_score, breakdown = _score(t, repo_root)
        new_label = _label(t, new_score)
        old_label = str(t.get("difficulty", "unknown"))
        if old_label != new_label:
            changed += 1
        t["difficulty"] = new_label
        if args.emit_breakdown:
            t["difficulty_v2_breakdown"] = breakdown

    after = Counter(str(t.get("difficulty", "unknown")) for t in tasks)
    _update_metadata(data)

    print("Difficulty rescoring summary")
    print(f"- tasks: {len(tasks)}")
    print(f"- changed: {changed}")
    print(f"- before: {dict(before)}")
    print(f"- after: {dict(after)}")
    print(f"- write: {args.write}")

    if args.write:
        path.write_text(json.dumps(data, indent=2) + "\n")
        print(f"- wrote: {path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
