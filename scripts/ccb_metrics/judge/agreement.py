"""Inter-judge agreement metrics for the CCB LLM Judge.

Implements Cohen's kappa (2 raters) and Fleiss' kappa (3+ raters)
with Landis-Koch interpretation. Stdlib only.

>>> cohens_kappa([1.0, 0.5, 0.0], [1.0, 0.5, 0.0])
1.0
>>> cohens_kappa([], [])
0.0
>>> fleiss_kappa([])
0.0
>>> fleiss_kappa([[3, 0], [0, 3]])
1.0
"""

from __future__ import annotations


def cohens_kappa(ratings_a: list[float], ratings_b: list[float]) -> float:
    """Compute Cohen's kappa for two raters.

    Args:
        ratings_a: Scores from rater A (one per item).
        ratings_b: Scores from rater B (one per item).

    Returns:
        Cohen's kappa coefficient.  1.0 = perfect agreement,
        0.0 = chance agreement, negative = worse than chance.

    >>> cohens_kappa([1.0, 0.5, 0.0], [1.0, 0.5, 0.0])
    1.0
    >>> cohens_kappa([1.0, 1.0, 1.0], [1.0, 1.0, 1.0])
    1.0
    >>> cohens_kappa([1.0, 0.0], [0.0, 1.0])
    -1.0
    >>> cohens_kappa([], [])
    0.0
    """
    if not ratings_a or not ratings_b:
        return 0.0
    n = len(ratings_a)
    if n != len(ratings_b):
        raise ValueError("Rating lists must have equal length")

    # Unique categories from both raters
    categories = sorted(set(ratings_a) | set(ratings_b))
    cat_idx = {c: i for i, c in enumerate(categories)}
    k = len(categories)

    # Confusion matrix
    matrix = [[0] * k for _ in range(k)]
    for a, b in zip(ratings_a, ratings_b):
        matrix[cat_idx[a]][cat_idx[b]] += 1

    # Observed agreement
    po = sum(matrix[i][i] for i in range(k)) / n

    # Expected agreement by chance
    pe = sum(
        sum(matrix[i][j] for j in range(k)) * sum(matrix[j][i] for j in range(k))
        for i in range(k)
    ) / (n * n)

    # All-same ratings: pe=1.0, denominator=0
    if pe >= 1.0:
        return 1.0

    return (po - pe) / (1.0 - pe)


def fleiss_kappa(ratings_matrix: list[list[int]]) -> float:
    """Compute Fleiss' kappa for 3+ raters.

    Args:
        ratings_matrix: N subjects x k categories, where entry [i][j] is
            the number of raters who assigned category j to subject i.

    Returns:
        Fleiss' kappa coefficient.

    >>> fleiss_kappa([[3, 0], [0, 3]])
    1.0
    >>> fleiss_kappa([[2, 0], [0, 2]])
    1.0
    >>> fleiss_kappa([])
    0.0
    """
    if not ratings_matrix:
        return 0.0

    N = len(ratings_matrix)
    k = len(ratings_matrix[0])
    n = sum(ratings_matrix[0])  # raters per subject

    if n <= 1:
        return 0.0

    # Per-subject agreement P_i
    p_bar_sum = 0.0
    for row in ratings_matrix:
        p_i = (sum(x * x for x in row) - n) / (n * (n - 1))
        p_bar_sum += p_i
    p_bar = p_bar_sum / N

    # Category proportions -> expected chance agreement
    total = N * n
    p_e = 0.0
    for j in range(k):
        col_sum = sum(ratings_matrix[i][j] for i in range(N))
        p_j = col_sum / total
        p_e += p_j * p_j

    # All-same ratings: p_e=1.0, denominator=0
    if p_e >= 1.0:
        return 1.0

    return (p_bar - p_e) / (1.0 - p_e)


def _interpret_kappa(kappa: float) -> str:
    """Interpret kappa using Landis-Koch scale.

    >>> _interpret_kappa(0.85)
    'almost_perfect'
    >>> _interpret_kappa(0.5)
    'moderate'
    >>> _interpret_kappa(-0.1)
    'poor'
    """
    if kappa < 0.0:
        return "poor"
    if kappa <= 0.20:
        return "slight"
    if kappa <= 0.40:
        return "fair"
    if kappa <= 0.60:
        return "moderate"
    if kappa <= 0.80:
        return "substantial"
    return "almost_perfect"


def agreement_report(round_scores: list[list[float]]) -> dict:
    """Compute agreement statistics across multiple judge rounds.

    Args:
        round_scores: R rounds x T tasks. round_scores[r][t] is the
            score for task t in round r.

    Returns:
        Dict with kappa, interpretation (Landis-Koch), n_rounds, n_tasks.
        Uses Cohen's kappa for 2 rounds, Fleiss' kappa for 3+.

    >>> agreement_report([[1.0, 0.0], [1.0, 0.0]])
    {'kappa': 1.0, 'interpretation': 'almost_perfect', 'n_rounds': 2, 'n_tasks': 2}
    >>> agreement_report([])
    {'kappa': 0.0, 'interpretation': 'poor', 'n_rounds': 0, 'n_tasks': 0}
    """
    if not round_scores or not round_scores[0]:
        return {"kappa": 0.0, "interpretation": "poor", "n_rounds": 0, "n_tasks": 0}

    n_rounds = len(round_scores)
    n_tasks = len(round_scores[0])

    if n_rounds < 2:
        return {
            "kappa": 1.0,
            "interpretation": "almost_perfect",
            "n_rounds": 1,
            "n_tasks": n_tasks,
        }

    if n_rounds == 2:
        kappa = cohens_kappa(round_scores[0], round_scores[1])
    else:
        # Convert round_scores to Fleiss' ratings matrix
        all_scores: set[float] = set()
        for round_s in round_scores:
            all_scores.update(round_s)
        categories = sorted(all_scores)
        cat_idx = {c: i for i, c in enumerate(categories)}
        k = len(categories)

        # Build ratings matrix: n_tasks x k categories
        matrix = [[0] * k for _ in range(n_tasks)]
        for round_s in round_scores:
            for t, score in enumerate(round_s):
                matrix[t][cat_idx[score]] += 1

        kappa = fleiss_kappa(matrix)

    return {
        "kappa": kappa,
        "interpretation": _interpret_kappa(kappa),
        "n_rounds": n_rounds,
        "n_tasks": n_tasks,
    }
