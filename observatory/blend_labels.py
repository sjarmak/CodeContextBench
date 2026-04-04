"""Blend LLM and heuristic annotations into a unified training set.

Strategy:
- For categories where heuristic-vs-LLM agreement is high (F1 >= threshold),
  use heuristic labels at corpus scale as training data.
- For categories where only the LLM is reliable, use the LLM labels.
- For each trial, merge category sets from both sources based on trust level.

This produces a larger effective training set than LLM-only labeling,
at zero additional cost.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def blend(
    heuristic_file: str | Path,
    llm_file: str | Path,
    calibration_file: str | Path | None = None,
    heuristic_trust_threshold: float = 0.7,
    max_heuristic_samples: int = 2000,
) -> dict:
    """Produce a blended annotation set for classifier training.

    Parameters
    ----------
    heuristic_file : path
        Full heuristic annotations (corpus-scale).
    llm_file : path
        LLM annotations (small, high-quality sample).
    calibration_file : path, optional
        Calibration JSON from ``calibrate.compare_annotations()``.
        If provided, uses per-category F1 to decide trust. If absent,
        trusts all heuristic categories at or above threshold.
    heuristic_trust_threshold : float
        Minimum calibration F1 to trust a heuristic category.
    max_heuristic_samples : int
        Cap heuristic-only samples to avoid swamping LLM labels.

    Returns
    -------
    dict
        Annotation document in Observatory schema format.
    """
    with open(heuristic_file) as f:
        heur_data = json.load(f)
    with open(llm_file) as f:
        llm_data = json.load(f)

    heur_anns = heur_data.get("annotations", [])
    llm_anns = llm_data.get("annotations", [])

    # Determine which heuristic categories to trust
    trusted_heuristic_cats: set[str] = set()
    if calibration_file:
        with open(calibration_file) as f:
            cal = json.load(f)
        for cat, metrics in cal.get("categories", {}).items():
            if metrics.get("f1", 0) >= heuristic_trust_threshold:
                trusted_heuristic_cats.add(cat)
    else:
        # Without calibration, trust high-confidence structural categories
        trusted_heuristic_cats = {
            "rate_limited_run", "exception_crash", "near_miss",
            "over_exploration", "edit_verify_loop_failure",
        }

    # Index LLM annotations by trial_path
    llm_by_path: dict[str, dict] = {}
    for ann in llm_anns:
        p = ann.get("trial_path", "")
        if p:
            llm_by_path[p] = ann

    # Index heuristic annotations by trial_path
    heur_by_path: dict[str, dict] = {}
    for ann in heur_anns:
        p = ann.get("trial_path", "")
        if p:
            heur_by_path[p] = ann

    all_paths = set(llm_by_path.keys()) | set(heur_by_path.keys())
    blended: list[dict] = []
    heuristic_only_count = 0

    for path in sorted(all_paths):
        llm_ann = llm_by_path.get(path)
        heur_ann = heur_by_path.get(path)

        # Start from whichever annotation exists
        if llm_ann:
            # LLM labels are ground truth — use all its categories
            cats_by_name: dict[str, dict] = {}
            for c in llm_ann.get("categories", []):
                cats_by_name[c["name"]] = {
                    "name": c["name"],
                    "confidence": c.get("confidence", 0.8),
                    "evidence": c.get("evidence", "LLM annotation"),
                    "source": "llm",
                }

            # Supplement with trusted heuristic categories not in LLM set
            if heur_ann:
                for c in heur_ann.get("categories", []):
                    if c["name"] in trusted_heuristic_cats and c["name"] not in cats_by_name:
                        cats_by_name[c["name"]] = {
                            "name": c["name"],
                            "confidence": c.get("confidence", 0.6),
                            "evidence": c.get("evidence", "heuristic (trusted)"),
                            "source": "heuristic_trusted",
                        }

            base = llm_ann
        elif heur_ann and heuristic_only_count < max_heuristic_samples:
            # Heuristic-only trial: only include trusted categories
            cats_by_name = {}
            for c in heur_ann.get("categories", []):
                if c["name"] in trusted_heuristic_cats:
                    cats_by_name[c["name"]] = {
                        "name": c["name"],
                        "confidence": c.get("confidence", 0.6),
                        "evidence": c.get("evidence", "heuristic (trusted)"),
                        "source": "heuristic_trusted",
                    }
            if not cats_by_name:
                continue  # No trusted categories for this trial
            base = heur_ann
            heuristic_only_count += 1
        else:
            continue

        blended.append({
            "task_id": base.get("task_id", "unknown"),
            "trial_path": path,
            "config_name": base.get("config_name"),
            "benchmark": base.get("benchmark"),
            "model": base.get("model"),
            "reward": base.get("reward", 0.0),
            "passed": base.get("passed", False),
            "categories": list(cats_by_name.values()),
            "annotated_at": base.get("annotated_at"),
        })

    now = datetime.now(timezone.utc).isoformat()
    return {
        "schema_version": "observatory-annotation-v1",
        "taxonomy_version": "1.0",
        "generated_at": now,
        "annotator": {
            "type": "blended",
            "identity": (
                f"llm({len(llm_anns)} trials) + "
                f"heuristic({heuristic_only_count} trusted trials, "
                f"categories: {sorted(trusted_heuristic_cats)})"
            ),
        },
        "blend_metadata": {
            "llm_trials": len(llm_anns),
            "heuristic_only_trials": heuristic_only_count,
            "total_blended": len(blended),
            "trusted_heuristic_categories": sorted(trusted_heuristic_cats),
            "trust_threshold": heuristic_trust_threshold,
        },
        "annotations": blended,
    }
