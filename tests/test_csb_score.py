"""Tests for lib.csb.scoring — CSB Score computation."""

from __future__ import annotations

import pytest

from lib.csb.scoring import (
    DEFAULT_PASS_THRESHOLD,
    SCORE_FORMULA_DOC,
    compute_csb_score,
)

# ---------------------------------------------------------------------------
# Empty input
# ---------------------------------------------------------------------------


class TestEmptyInput:
    def test_empty_list_raises(self) -> None:
        with pytest.raises(ValueError, match="empty"):
            compute_csb_score([])


# ---------------------------------------------------------------------------
# Single work type
# ---------------------------------------------------------------------------


class TestSingleType:
    def test_all_pass_single_type(self) -> None:
        results = [
            {"work_type": "fix", "reward": 1.0},
            {"work_type": "fix", "reward": 1.0},
        ]
        assert compute_csb_score(results) == 100.0

    def test_all_fail_single_type(self) -> None:
        results = [
            {"work_type": "fix", "reward": 0.0},
            {"work_type": "fix", "reward": 0.5},
        ]
        assert compute_csb_score(results) == 0.0

    def test_half_pass_single_type(self) -> None:
        results = [
            {"work_type": "fix", "reward": 1.0},
            {"work_type": "fix", "reward": 0.0},
        ]
        assert compute_csb_score(results) == 50.0


# ---------------------------------------------------------------------------
# Multiple work types (equal weighting)
# ---------------------------------------------------------------------------


class TestMultipleTypes:
    def test_two_types_equal_weight(self) -> None:
        """fix: 1/2 pass = 50%, test: 1/1 pass = 100% → avg = 75.0"""
        results = [
            {"work_type": "fix", "reward": 1.0},
            {"work_type": "fix", "reward": 0.0},
            {"work_type": "test", "reward": 1.0},
        ]
        score = compute_csb_score(results)
        assert score == pytest.approx(75.0)

    def test_three_types(self) -> None:
        """fix: 0/1=0%, feature: 1/1=100%, test: 1/2=50% → avg ≈ 50.0"""
        results = [
            {"work_type": "fix", "reward": 0.0},
            {"work_type": "feature", "reward": 1.0},
            {"work_type": "test", "reward": 1.0},
            {"work_type": "test", "reward": 0.0},
        ]
        score = compute_csb_score(results)
        assert score == pytest.approx(50.0)

    def test_equal_weight_not_sample_weight(self) -> None:
        """100 fix tasks (all fail) + 1 test task (pass).

        Sample-weighted would give ~1%, but equal-weighted gives 50%.
        """
        results = [{"work_type": "fix", "reward": 0.0} for _ in range(100)]
        results.append({"work_type": "test", "reward": 1.0})
        score = compute_csb_score(results)
        assert score == pytest.approx(50.0)


# ---------------------------------------------------------------------------
# Edge cases: all pass / all fail across types
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_all_pass_all_types(self) -> None:
        results = [
            {"work_type": "fix", "reward": 1.0},
            {"work_type": "feature", "reward": 2.0},
            {"work_type": "test", "reward": 1.0},
        ]
        assert compute_csb_score(results) == 100.0

    def test_all_fail_all_types(self) -> None:
        results = [
            {"work_type": "fix", "reward": 0.0},
            {"work_type": "feature", "reward": 0.5},
            {"work_type": "test", "reward": 0.0},
        ]
        assert compute_csb_score(results) == 0.0

    def test_reward_above_threshold_still_passes(self) -> None:
        """reward > 1.0 should still count as pass."""
        results = [{"work_type": "fix", "reward": 5.0}]
        assert compute_csb_score(results) == 100.0

    def test_custom_threshold(self) -> None:
        results = [
            {"work_type": "fix", "reward": 0.5},
            {"work_type": "fix", "reward": 0.3},
        ]
        # With default threshold (1.0), both fail → 0.0
        assert compute_csb_score(results) == 0.0
        # With threshold 0.5, first passes → 50.0
        assert compute_csb_score(results, pass_threshold=0.5) == 50.0

    def test_single_result(self) -> None:
        assert compute_csb_score([{"work_type": "fix", "reward": 1.0}]) == 100.0
        assert compute_csb_score([{"work_type": "fix", "reward": 0.0}]) == 0.0


# ---------------------------------------------------------------------------
# Constants and documentation
# ---------------------------------------------------------------------------


class TestConstants:
    def test_default_threshold(self) -> None:
        assert DEFAULT_PASS_THRESHOLD == 1.0

    def test_formula_doc_exists(self) -> None:
        assert isinstance(SCORE_FORMULA_DOC, str)
        assert len(SCORE_FORMULA_DOC) > 50
        assert (
            "equal-weighted" in SCORE_FORMULA_DOC.lower()
            or "equal" in SCORE_FORMULA_DOC.lower()
        )
