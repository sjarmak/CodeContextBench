"""CSB Score — single citable aggregate score for CodeScaleBench runs.

CSB Score = weighted average of per-work-type pass rates, scaled to 0–100.
Each work type is weighted equally so that breadth matters: an agent that
covers all work types scores higher than one that aces a single type.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Sequence

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_PASS_THRESHOLD: float = 1.0

SCORE_FORMULA_DOC: str = (
    "CSB Score (0-100) is the equal-weighted average of per-work-type pass rates. "
    "Steps: (1) Group results by work_type. "
    "(2) For each work_type compute pass_rate = count(reward >= threshold) / total. "
    "(3) CSB Score = mean(pass_rates) * 100. "
    "Equal weighting ensures breadth across work types matters as much as depth "
    "within any single type. A 'pass' is defined as reward >= 1.0 by default."
)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def compute_csb_score(
    results: Sequence[dict],
    *,
    pass_threshold: float = DEFAULT_PASS_THRESHOLD,
) -> float:
    """Compute the CSB aggregate score from a list of result dicts.

    Each result dict must contain at minimum:
        - ``work_type`` (str): the work-type label (e.g. "fix", "feature").
        - ``reward`` (float|int): the task reward value.

    Parameters
    ----------
    results:
        Sequence of result dictionaries.
    pass_threshold:
        Minimum reward value to count as a pass (default 1.0).

    Returns
    -------
    float
        CSB Score in the range [0.0, 100.0].

    Raises
    ------
    ValueError
        If *results* is empty (no data to aggregate).
    """
    if not results:
        raise ValueError("Cannot compute CSB Score from empty results.")

    # Group by work_type
    buckets: dict[str, list[float]] = defaultdict(list)
    for r in results:
        work_type = r["work_type"]
        reward = float(r["reward"])
        buckets[work_type].append(reward)

    # Per-type pass rates
    pass_rates: list[float] = []
    for rewards in buckets.values():
        passed = sum(1 for rw in rewards if rw >= pass_threshold)
        pass_rates.append(passed / len(rewards))

    # Equal-weighted average, scaled to 0-100
    score = (sum(pass_rates) / len(pass_rates)) * 100.0

    # Clamp to [0.0, 100.0] for safety (mathematically already bounded)
    return max(0.0, min(100.0, score))
