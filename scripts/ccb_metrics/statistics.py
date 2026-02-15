"""Statistical analysis utilities for CodeContextBench A/B comparisons.

Provides hypothesis testing, effect size calculations, bootstrap confidence
intervals, and McNemar's test for paired pass/fail outcomes. Pure stdlib —
no external dependencies (math, statistics, random only).

Ported from IR-SDLC-Factory/app/ir_sdlc/comparative_analysis.py,
stripped of AgentRunner/ABComparator/ComparisonReport classes.
"""

from __future__ import annotations

import math
import random
import statistics
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _normal_cdf(x: float) -> float:
    """Approximate standard normal CDF via the error function."""
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def _chi2_cdf_df1(x: float) -> float:
    """Chi-squared CDF for df=1: P(X <= x) = 2*Phi(sqrt(x)) - 1."""
    if x <= 0:
        return 0.0
    return 2 * _normal_cdf(math.sqrt(x)) - 1


# ---------------------------------------------------------------------------
# Core statistical functions
# ---------------------------------------------------------------------------

def welchs_t_test(
    a: List[float],
    b: List[float],
    alpha: float = 0.05,
) -> dict:
    """Welch's t-test for independent samples (unequal variances).

    Args:
        a: Baseline group measurements.
        b: Treatment group measurements.
        alpha: Significance level.

    Returns:
        Dict with keys: t_stat, p_value, df, n_a, n_b, is_significant,
        interpretation.
    """
    n_a, n_b = len(a), len(b)
    if n_a < 2 or n_b < 2:
        return {
            "t_stat": 0.0,
            "p_value": 1.0,
            "df": 0.0,
            "n_a": n_a,
            "n_b": n_b,
            "is_significant": False,
            "interpretation": "Insufficient sample size (need >= 2 per group)",
        }

    mean_a, mean_b = statistics.mean(a), statistics.mean(b)
    var_a, var_b = statistics.variance(a), statistics.variance(b)

    se = math.sqrt(var_a / n_a + var_b / n_b)
    if se == 0:
        return {
            "t_stat": 0.0,
            "p_value": 1.0,
            "df": 0.0,
            "n_a": n_a,
            "n_b": n_b,
            "is_significant": False,
            "interpretation": "Zero variance in both groups",
        }

    t_stat = (mean_b - mean_a) / se

    # Welch-Satterthwaite degrees of freedom
    num = (var_a / n_a + var_b / n_b) ** 2
    denom = (var_a / n_a) ** 2 / (n_a - 1) + (var_b / n_b) ** 2 / (n_b - 1)
    df = num / denom if denom > 0 else 1.0

    # Two-tailed p-value (normal approximation, adequate for df > ~30)
    p_value = 2 * (1 - _normal_cdf(abs(t_stat)))

    is_sig = p_value < alpha
    direction = "higher" if t_stat > 0 else "lower"
    interpretation = (
        f"Treatment is {'significantly ' if is_sig else 'not significantly '}"
        f"{direction} than baseline "
        f"(t={t_stat:.3f}, p={p_value:.4f}, df={df:.1f})"
    )

    return {
        "t_stat": round(t_stat, 4),
        "p_value": round(p_value, 6),
        "df": round(df, 1),
        "n_a": n_a,
        "n_b": n_b,
        "is_significant": is_sig,
        "interpretation": interpretation,
    }


def cohens_d(
    a: List[float],
    b: List[float],
) -> dict:
    """Cohen's d effect size with 95 % confidence interval.

    Args:
        a: Baseline group.
        b: Treatment group.

    Returns:
        Dict with keys: d, magnitude, ci_lower, ci_upper.
    """
    n_a, n_b = len(a), len(b)
    if n_a < 1 or n_b < 1:
        return {"d": 0.0, "magnitude": "invalid", "ci_lower": 0.0, "ci_upper": 0.0}
    if n_a == 1 and n_b == 1:
        return {"d": 0.0, "magnitude": "insufficient_data", "ci_lower": 0.0, "ci_upper": 0.0}

    mean_a, mean_b = statistics.mean(a), statistics.mean(b)
    var_a = statistics.variance(a) if n_a > 1 else 0.0
    var_b = statistics.variance(b) if n_b > 1 else 0.0

    pooled_var = ((n_a - 1) * var_a + (n_b - 1) * var_b) / max(n_a + n_b - 2, 1)
    pooled_std = math.sqrt(pooled_var) if pooled_var > 0 else 1e-10

    d = (mean_b - mean_a) / pooled_std

    # Cohen's conventions
    abs_d = abs(d)
    if abs_d < 0.2:
        magnitude = "negligible"
    elif abs_d < 0.5:
        magnitude = "small"
    elif abs_d < 0.8:
        magnitude = "medium"
    else:
        magnitude = "large"

    # Hedges & Olkin (1985) approximate 95 % CI
    se = math.sqrt((n_a + n_b) / (n_a * n_b) + (d ** 2) / (2 * (n_a + n_b)))
    ci_lower = d - 1.96 * se
    ci_upper = d + 1.96 * se

    return {
        "d": round(d, 4),
        "magnitude": magnitude,
        "ci_lower": round(ci_lower, 4),
        "ci_upper": round(ci_upper, 4),
    }


def mcnemar_test(
    paired: List[Tuple[bool, bool]],
    alpha: float = 0.05,
) -> dict:
    """McNemar's test for paired nominal data (pass/fail per task).

    Args:
        paired: List of (baseline_passed, treatment_passed) tuples.
        alpha: Significance level.

    Returns:
        Dict with chi2, p_value, b, c, is_significant, interpretation.
    """
    if not paired:
        return {
            "chi2": 0.0,
            "p_value": 1.0,
            "b": 0,
            "c": 0,
            "n": 0,
            "is_significant": False,
            "interpretation": "Empty sample",
        }

    # b = baseline fail, treatment pass  (treatment improved)
    # c = baseline pass, treatment fail  (treatment regressed)
    b = sum(1 for bl, tr in paired if not bl and tr)
    c = sum(1 for bl, tr in paired if bl and not tr)
    n = len(paired)

    if b + c == 0:
        return {
            "chi2": 0.0,
            "p_value": 1.0,
            "b": b,
            "c": c,
            "n": n,
            "is_significant": False,
            "interpretation": "No discordant pairs — identical outcomes",
        }

    # Continuity-corrected McNemar chi-squared
    chi2 = (abs(b - c) - 1) ** 2 / (b + c)
    p_value = 1 - _chi2_cdf_df1(chi2)
    is_sig = p_value < alpha

    if b > c:
        direction = "treatment improved"
    elif c > b:
        direction = "baseline better"
    else:
        direction = "no clear direction"

    interpretation = (
        f"McNemar: {direction} "
        f"(b={b}, c={c}, chi2={chi2:.3f}, p={p_value:.4f})"
    )

    return {
        "chi2": round(chi2, 4),
        "p_value": round(p_value, 6),
        "b": b,
        "c": c,
        "n": n,
        "is_significant": is_sig,
        "interpretation": interpretation,
    }


def bootstrap_ci(
    data: List[float],
    stat_fn: Callable[[List[float]], float] = statistics.mean,
    n: int = 10_000,
    confidence: float = 0.95,
    seed: int = 42,
) -> dict:
    """Percentile bootstrap confidence interval.

    Args:
        data: Sample values.
        stat_fn: Statistic to bootstrap (default: mean).
        n: Number of bootstrap resamples.
        confidence: Confidence level.
        seed: RNG seed for reproducibility.

    Returns:
        Dict with estimate, ci_lower, ci_upper.
    """
    if not data:
        return {"estimate": 0.0, "ci_lower": 0.0, "ci_upper": 0.0}

    estimate = stat_fn(data)

    if len(data) == 1:
        return {"estimate": estimate, "ci_lower": estimate, "ci_upper": estimate}

    rng = random.Random(seed)
    resamples = []
    for _ in range(n):
        sample = rng.choices(data, k=len(data))
        resamples.append(stat_fn(sample))

    resamples.sort()
    alpha = 1 - confidence
    lo_idx = int(alpha / 2 * n)
    hi_idx = int((1 - alpha / 2) * n) - 1

    return {
        "estimate": round(estimate, 6),
        "ci_lower": round(resamples[lo_idx], 6),
        "ci_upper": round(resamples[hi_idx], 6),
    }


# ---------------------------------------------------------------------------
# Result containers
# ---------------------------------------------------------------------------

@dataclass
class MetricComparison:
    """Comparison of a single metric between baseline and treatment."""

    metric_name: str

    # Summary stats
    baseline_mean: float = 0.0
    baseline_std: float = 0.0
    baseline_n: int = 0
    treatment_mean: float = 0.0
    treatment_std: float = 0.0
    treatment_n: int = 0

    # Deltas
    absolute_diff: float = 0.0
    relative_diff_pct: float = 0.0

    # Statistical tests (populated by compute())
    t_test: Optional[dict] = None
    effect_size: Optional[dict] = None
    ci: Optional[dict] = None

    def compute(
        self,
        baseline_values: List[float],
        treatment_values: List[float],
    ) -> "MetricComparison":
        """Populate all fields from raw value lists. Returns self."""
        self.baseline_n = len(baseline_values)
        self.treatment_n = len(treatment_values)

        if baseline_values:
            self.baseline_mean = statistics.mean(baseline_values)
            self.baseline_std = (
                statistics.stdev(baseline_values) if len(baseline_values) > 1 else 0.0
            )
        if treatment_values:
            self.treatment_mean = statistics.mean(treatment_values)
            self.treatment_std = (
                statistics.stdev(treatment_values) if len(treatment_values) > 1 else 0.0
            )

        self.absolute_diff = self.treatment_mean - self.baseline_mean
        if self.baseline_mean != 0:
            self.relative_diff_pct = (self.absolute_diff / self.baseline_mean) * 100

        if self.baseline_n >= 2 and self.treatment_n >= 2:
            self.t_test = welchs_t_test(baseline_values, treatment_values)
            self.effect_size = cohens_d(baseline_values, treatment_values)

        # Bootstrap CI on the difference (when paired) or on treatment mean
        if baseline_values and treatment_values:
            min_len = min(len(baseline_values), len(treatment_values))
            diffs = [
                treatment_values[i] - baseline_values[i]
                for i in range(min_len)
            ]
            if diffs:
                self.ci = bootstrap_ci(diffs)

        return self

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "baseline": {
                "mean": round(self.baseline_mean, 4),
                "std": round(self.baseline_std, 4),
                "n": self.baseline_n,
            },
            "treatment": {
                "mean": round(self.treatment_mean, 4),
                "std": round(self.treatment_std, 4),
                "n": self.treatment_n,
            },
            "absolute_diff": round(self.absolute_diff, 4),
            "relative_diff_pct": round(self.relative_diff_pct, 2),
            "t_test": self.t_test,
            "effect_size": self.effect_size,
            "confidence_interval": self.ci,
        }


@dataclass
class PairedComparisonReport:
    """Aggregate comparison of baseline vs treatment across multiple metrics."""

    metrics: List[MetricComparison] = field(default_factory=list)
    mcnemar: Optional[dict] = None
    summary: str = ""

    def to_dict(self) -> dict:
        return {
            "metrics": [m.to_dict() for m in self.metrics],
            "mcnemar": self.mcnemar,
            "summary": self.summary,
        }
