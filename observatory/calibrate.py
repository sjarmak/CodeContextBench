"""Agreement and calibration analysis for the Agent Reliability Observatory.

Supports two comparison modes:

1. **Heuristic-vs-LLM** (original): Aligns annotations from two sources
   (typically heuristic and LLM) by trial_path and computes per-category
   agreement metrics: true positives, false positives, false negatives,
   precision, recall, and F1.

2. **Cross-model** (new): Compares annotations from two different model
   families using Cohen's kappa for inter-rater reliability measurement.
   Identifies categories where annotators disagree beyond chance.

Used to identify categories where annotators are unreliable and to
calibrate confidence thresholds.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _load_annotations(path: str | Path) -> dict[str, set[str]]:
    """Load an annotation file and return {trial_path: set of category names}.

    Handles both annotation document format (with top-level 'annotations' key)
    and raw list format.
    """
    with open(path) as f:
        data = json.load(f)

    annotations = data.get("annotations", data) if isinstance(data, dict) else data
    if not isinstance(annotations, list):
        raise ValueError(f"Expected annotations list, got {type(annotations).__name__}")

    result: dict[str, set[str]] = {}
    for ann in annotations:
        trial = ann.get("trial_path", "")
        if not trial:
            continue
        cats = {c["name"] for c in ann.get("categories", []) if "name" in c}
        result[trial] = cats
    return result


def compare_annotations(
    heuristic_file: str | Path,
    llm_file: str | Path,
) -> dict[str, Any]:
    """Compare heuristic and LLM annotations and compute agreement metrics.

    Aligns annotations by ``trial_path``. For each shared trial, compares
    the set of category names from each source:

    - **TP**: both sources assign the category
    - **FP**: heuristic assigns it, LLM does not
    - **FN**: LLM assigns it, heuristic does not

    Parameters
    ----------
    heuristic_file : str or Path
        Path to the heuristic annotation JSON file.
    llm_file : str or Path
        Path to the LLM annotation JSON file.

    Returns
    -------
    dict
        Summary with keys:

        - ``shared_trials``: number of trials present in both files
        - ``categories``: dict mapping category name to metrics dict
          (``true_positive``, ``false_positive``, ``false_negative``,
          ``precision``, ``recall``, ``f1``)
        - ``macro_avg``: macro-averaged precision, recall, f1 across
          categories with at least one TP+FP+FN
    """
    heuristic = _load_annotations(heuristic_file)
    llm = _load_annotations(llm_file)

    shared = set(heuristic.keys()) & set(llm.keys())

    # Collect all category names seen in shared trials
    all_cats: set[str] = set()
    for trial in shared:
        all_cats |= heuristic[trial]
        all_cats |= llm[trial]

    # Compute per-category TP / FP / FN
    category_metrics: dict[str, dict[str, Any]] = {}
    for cat in sorted(all_cats):
        tp = fp = fn = 0
        for trial in shared:
            in_h = cat in heuristic[trial]
            in_l = cat in llm[trial]
            if in_h and in_l:
                tp += 1
            elif in_h and not in_l:
                fp += 1
            elif not in_h and in_l:
                fn += 1

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (
            2 * precision * recall / (precision + recall)
            if (precision + recall) > 0
            else 0.0
        )

        category_metrics[cat] = {
            "true_positive": tp,
            "false_positive": fp,
            "false_negative": fn,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
        }

    # Macro average over categories that had any signal
    active = [
        m
        for m in category_metrics.values()
        if m["true_positive"] + m["false_positive"] + m["false_negative"] > 0
    ]
    if active:
        macro_p = sum(m["precision"] for m in active) / len(active)
        macro_r = sum(m["recall"] for m in active) / len(active)
        macro_f1 = sum(m["f1"] for m in active) / len(active)
    else:
        macro_p = macro_r = macro_f1 = 0.0

    return {
        "shared_trials": len(shared),
        "categories": category_metrics,
        "macro_avg": {
            "precision": round(macro_p, 4),
            "recall": round(macro_r, 4),
            "f1": round(macro_f1, 4),
        },
    }


def format_markdown(summary: dict[str, Any]) -> str:
    """Render the agreement summary as a Markdown table.

    Parameters
    ----------
    summary : dict
        Output of ``compare_annotations()``.

    Returns
    -------
    str
        Markdown string with a metrics table and macro averages.
    """
    lines: list[str] = []
    lines.append("## Heuristic vs LLM Agreement\n")
    lines.append(f"Shared trials: {summary['shared_trials']}\n")

    lines.append("| Category | TP | FP | FN | Precision | Recall | F1 |")
    lines.append("|----------|---:|---:|---:|----------:|-------:|---:|")

    cats = summary["categories"]
    # Sort by F1 descending, then name ascending
    for name in sorted(cats, key=lambda n: (-cats[n]["f1"], n)):
        m = cats[name]
        lines.append(
            f"| {name} | {m['true_positive']} | {m['false_positive']} "
            f"| {m['false_negative']} | {m['precision']:.2f} "
            f"| {m['recall']:.2f} | {m['f1']:.2f} |"
        )

    macro = summary["macro_avg"]
    lines.append(
        f"| **Macro avg** | | | | **{macro['precision']:.2f}** "
        f"| **{macro['recall']:.2f}** | **{macro['f1']:.2f}** |"
    )

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Cross-model calibration (Cohen's kappa)
# ---------------------------------------------------------------------------

UNCALIBRATED_THRESHOLD = 0.4
"""Categories with kappa below this value are flagged as 'uncalibrated'."""


def cohen_kappa(a_labels: list[int], b_labels: list[int]) -> float:
    """Compute Cohen's kappa for two binary label vectors.

    Parameters
    ----------
    a_labels : list of int
        Binary labels (0 or 1) from rater A, one per item.
    b_labels : list of int
        Binary labels (0 or 1) from rater B, same length as *a_labels*.

    Returns
    -------
    float
        Cohen's kappa coefficient. Returns 0.0 when both raters assign the
        same label to every item (perfect agreement by chance, undefined kappa).

    Raises
    ------
    ValueError
        If the input vectors differ in length or are empty.
    """
    if len(a_labels) != len(b_labels):
        raise ValueError(
            f"Label vectors must be the same length "
            f"(got {len(a_labels)} and {len(b_labels)})"
        )
    if not a_labels:
        raise ValueError("Label vectors must not be empty")

    n = len(a_labels)

    # Confusion matrix cells
    both_pos = sum(1 for a, b in zip(a_labels, b_labels) if a == 1 and b == 1)
    both_neg = sum(1 for a, b in zip(a_labels, b_labels) if a == 0 and b == 0)
    a_pos_b_neg = sum(1 for a, b in zip(a_labels, b_labels) if a == 1 and b == 0)
    a_neg_b_pos = sum(1 for a, b in zip(a_labels, b_labels) if a == 0 and b == 1)

    observed_agreement = (both_pos + both_neg) / n

    # Marginal probabilities
    a_pos_rate = (both_pos + a_pos_b_neg) / n
    b_pos_rate = (both_pos + a_neg_b_pos) / n

    expected_agreement = (a_pos_rate * b_pos_rate) + (
        (1 - a_pos_rate) * (1 - b_pos_rate)
    )

    if expected_agreement >= 1.0:
        return 0.0

    return (observed_agreement - expected_agreement) / (1.0 - expected_agreement)


def compare_cross_model(
    model_a_file: str | Path,
    model_b_file: str | Path,
    *,
    uncalibrated_threshold: float = UNCALIBRATED_THRESHOLD,
) -> dict[str, Any]:
    """Compare annotations from two model families using Cohen's kappa.

    For each category observed in the shared trials, builds a binary vector
    (1 = category present, 0 = absent) per model and computes Cohen's kappa.

    Parameters
    ----------
    model_a_file : str or Path
        Path to annotation JSON from model A.
    model_b_file : str or Path
        Path to annotation JSON from model B.
    uncalibrated_threshold : float
        Kappa threshold below which a category is flagged as 'uncalibrated'.

    Returns
    -------
    dict
        Summary with keys:

        - ``shared_trials``: count of trials present in both files
        - ``categories``: dict mapping category name to
          ``kappa``, ``agreement``, ``a_count``, ``b_count``, ``calibrated``
        - ``uncalibrated_categories``: list of category names with kappa
          below the threshold
        - ``macro_kappa``: average kappa across all categories with signal
    """
    model_a = _load_annotations(model_a_file)
    model_b = _load_annotations(model_b_file)

    shared_trials = sorted(set(model_a.keys()) & set(model_b.keys()))

    if not shared_trials:
        return {
            "shared_trials": 0,
            "categories": {},
            "uncalibrated_categories": [],
            "macro_kappa": 0.0,
        }

    # Collect all category names from shared trials
    all_cats: set[str] = set()
    for trial in shared_trials:
        all_cats |= model_a[trial]
        all_cats |= model_b[trial]

    category_results: dict[str, dict[str, Any]] = {}
    uncalibrated: list[str] = []

    for cat in sorted(all_cats):
        a_vec = [1 if cat in model_a[t] else 0 for t in shared_trials]
        b_vec = [1 if cat in model_b[t] else 0 for t in shared_trials]

        kappa_val = cohen_kappa(a_vec, b_vec)
        agreement = sum(1 for a, b in zip(a_vec, b_vec) if a == b) / len(shared_trials)
        is_calibrated = kappa_val >= uncalibrated_threshold

        if not is_calibrated:
            uncalibrated.append(cat)

        category_results[cat] = {
            "kappa": round(kappa_val, 4),
            "agreement": round(agreement, 4),
            "a_count": sum(a_vec),
            "b_count": sum(b_vec),
            "calibrated": is_calibrated,
        }

    # Macro-average kappa across categories with any positive label
    active_kappas = [
        m["kappa"] for m in category_results.values() if m["a_count"] + m["b_count"] > 0
    ]
    macro_kappa = sum(active_kappas) / len(active_kappas) if active_kappas else 0.0

    return {
        "shared_trials": len(shared_trials),
        "categories": category_results,
        "uncalibrated_categories": uncalibrated,
        "macro_kappa": round(macro_kappa, 4),
    }


def format_cross_model_markdown(
    summary: dict[str, Any],
    model_a_name: str = "Model A",
    model_b_name: str = "Model B",
) -> str:
    """Render cross-model calibration summary as Markdown.

    Parameters
    ----------
    summary : dict
        Output of ``compare_cross_model()``.
    model_a_name : str
        Display name for model A.
    model_b_name : str
        Display name for model B.

    Returns
    -------
    str
        Markdown report string.
    """
    lines: list[str] = []
    lines.append(f"## Cross-Model Calibration: {model_a_name} vs {model_b_name}\n")
    lines.append(f"Shared trials: {summary['shared_trials']}\n")
    lines.append(f"Macro kappa: **{summary['macro_kappa']:.4f}**\n")

    lines.append(
        f"| Category | Kappa | Agreement | {model_a_name} Count "
        f"| {model_b_name} Count | Calibrated |"
    )
    lines.append(
        "|----------|------:|----------:|-----------:|-----------:|:----------:|"
    )

    cats = summary["categories"]
    for name in sorted(cats, key=lambda n: (-cats[n]["kappa"], n)):
        m = cats[name]
        cal_icon = "Yes" if m["calibrated"] else "**No**"
        lines.append(
            f"| {name} | {m['kappa']:.4f} | {m['agreement']:.2f} "
            f"| {m['a_count']} | {m['b_count']} | {cal_icon} |"
        )

    if summary["uncalibrated_categories"]:
        lines.append("")
        lines.append(
            f"**Uncalibrated categories** (kappa < {UNCALIBRATED_THRESHOLD}): "
            + ", ".join(sorted(summary["uncalibrated_categories"]))
        )

    return "\n".join(lines) + "\n"
