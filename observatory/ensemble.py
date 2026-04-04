"""Two-tier ensemble annotator: classifier for high-data categories,
heuristic fallback for structural categories, LLM for the rest.

Tier 1 (classifier): Categories with sufficient training data and F1 >= 0.7
    on the blended training set. Fast, runs on full corpus.

Tier 2 (heuristic): Structural categories that are deterministic
    (exception_crash, rate_limited_run, near_miss, minimal_progress,
    edit_verify_loop_failure). These have simple, reliable signal rules.

Tier 3 (LLM): Categories that require trajectory reading and can't be
    learned from signal features alone (decomposition_failure,
    insufficient_provenance, success_via_decomposition, etc.).
    Only run on a sample — too expensive for full corpus.

Usage::

    python -m observatory ensemble \\
        --signals observatory/annotations/heuristic/signals.json \\
        --model observatory/model.json \\
        --output observatory/annotations/ensemble/full.json \\
        --classifier-threshold 0.5 \\
        --classifier-min-f1 0.7
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from observatory.annotator import annotate_trial as heuristic_annotate
from observatory.classifier import load_model, predict_trial, signals_to_features


# Categories where heuristic rules are deterministic and reliable.
# These don't need the classifier — the rule IS the ground truth.
HEURISTIC_ONLY = {
    "exception_crash",
    "rate_limited_run",
    "near_miss",
    "minimal_progress",
    "edit_verify_loop_failure",
}


def ensemble_annotate(
    signals: dict,
    model: dict,
    corpus_stats: dict | None = None,
    classifier_threshold: float = 0.5,
    classifier_min_f1: float = 0.7,
) -> list[dict]:
    """Annotate a single trial using the two-tier ensemble.

    Returns a list of {name, confidence, evidence, source} dicts.
    """
    results: dict[str, dict] = {}

    # Tier 1: Heuristic for structural/deterministic categories
    heur_cats = heuristic_annotate(signals, corpus_stats)
    for c in heur_cats:
        if c["name"] in HEURISTIC_ONLY:
            results[c["name"]] = {
                "name": c["name"],
                "confidence": c["confidence"],
                "evidence": c["evidence"],
                "source": "heuristic",
            }

    # Tier 2: Classifier for categories with sufficient training data
    # Only use classifier predictions where training F1 was above threshold
    clf_cats = predict_trial(signals, model, threshold=classifier_threshold)
    for c in clf_cats:
        cat_name = c["name"]
        if cat_name in HEURISTIC_ONLY:
            continue  # Heuristic already handled these
        clf_meta = model["classifiers"].get(cat_name, {})
        eval_f1 = clf_meta.get("eval_f1", clf_meta.get("train_accuracy", 0))
        if eval_f1 >= classifier_min_f1 and cat_name not in results:
            results[cat_name] = {
                "name": cat_name,
                "confidence": c["confidence"],
                "evidence": c["evidence"] + f" [eval_f1={eval_f1:.2f}]",
                "source": "classifier",
            }

    # Tier 3: LLM would go here for remaining categories, but only on
    # sampled trials. Not called in batch mode — caller handles this.

    return list(results.values())


def ensemble_all(
    signals_list: list[dict],
    model: dict,
    classifier_threshold: float = 0.5,
    classifier_min_f1: float = 0.7,
) -> dict:
    """Run ensemble annotation on the full corpus."""
    from observatory.annotator import compute_corpus_stats
    from observatory.taxonomy import load_taxonomy

    taxonomy = load_taxonomy()
    now = datetime.now(timezone.utc).isoformat()

    # Compute corpus stats for heuristic rules that need them
    corpus_stats = compute_corpus_stats(signals_list)

    annotations = []
    tier_counts: dict[str, int] = {"heuristic": 0, "classifier": 0}
    for sig in signals_list:
        cats = ensemble_annotate(
            sig, model, corpus_stats,
            classifier_threshold=classifier_threshold,
            classifier_min_f1=classifier_min_f1,
        )
        if not cats:
            continue

        reward = sig.get("reward")
        # Strip internal 'source' key before output (not in annotation schema)
        clean_cats = [
            {k: v for k, v in c.items() if k != "source"}
            for c in cats
        ]
        annotations.append({
            "task_id": sig.get("task_id") or "unknown",
            "trial_path": sig.get("trial_path") or "",
            "config_name": sig.get("config_name"),
            "benchmark": sig.get("benchmark"),
            "model": sig.get("model"),
            "reward": float(reward) if reward is not None else 0.0,
            "passed": bool(sig.get("passed")),
            "categories": clean_cats,
            "annotated_at": now,
        })
        # Track tier counts from unstripped cats
        for c in cats:
            source = c.get("source", "unknown")
            tier_counts[source] = tier_counts.get(source, 0) + 1

    return {
        "schema_version": "observatory-annotation-v1",
        "taxonomy_version": str(taxonomy["version"]),
        "generated_at": now,
        "annotator": {
            "type": "ensemble",
            "identity": (
                f"heuristic({len(HEURISTIC_ONLY)} structural, "
                f"{tier_counts.get('heuristic', 0)} assignments) + "
                f"classifier({len(model['classifiers'])} trained, "
                f"{tier_counts.get('classifier', 0)} assignments, "
                f"threshold={classifier_threshold}, min_f1={classifier_min_f1})"
            ),
        },
        "annotations": annotations,
    }
