"""Unit tests for tiered scoring in scripts/csb_metrics/oracle_checks.py.

Covers the two-tier weighted scoring added to check_file_set_match and the
_get_primary_score preference for weighted_f1 over plain f1.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.csb_metrics.oracle_checks import check_file_set_match, _get_primary_score


def _file(repo, path, tier=None):
    f = {"repo": repo, "path": path}
    if tier is not None:
        f["tier"] = tier
    return f


# ---------------------------------------------------------------------------
# check_file_set_match — backward-compatibility (no tiers)
# ---------------------------------------------------------------------------

class FileSetMatchUntiedTests(unittest.TestCase):

    def test_perfect_match(self):
        oracle = [_file("a/b", "x.go"), _file("a/b", "y.go")]
        answer = [_file("a/b", "x.go"), _file("a/b", "y.go")]
        r = check_file_set_match(answer, oracle)
        self.assertEqual(r["recall"], 1.0)
        self.assertEqual(r["precision"], 1.0)
        self.assertEqual(r["f1"], 1.0)
        self.assertNotIn("weighted_f1", r)

    def test_partial_recall(self):
        oracle = [_file("a/b", "x.go"), _file("a/b", "y.go")]
        answer = [_file("a/b", "x.go")]
        r = check_file_set_match(answer, oracle)
        self.assertEqual(r["recall"], 0.5)
        self.assertEqual(r["precision"], 1.0)
        self.assertAlmostEqual(r["f1"], 0.6667, places=3)

    def test_no_overlap(self):
        oracle = [_file("a/b", "x.go")]
        answer = [_file("a/b", "z.go")]
        r = check_file_set_match(answer, oracle)
        self.assertEqual(r["recall"], 0.0)
        self.assertEqual(r["f1"], 0.0)

    def test_empty_oracle_returns_full_recall(self):
        r = check_file_set_match([], [])
        self.assertEqual(r["recall"], 1.0)

    def test_mirror_repo_normalization(self):
        # Oracle uses sg-evals mirror name; answer uses upstream name
        oracle = [_file("sg-evals/jdk--742e735d", "src/Foo.java")]
        answer = [_file("openjdk/jdk", "src/Foo.java")]
        r = check_file_set_match(answer, oracle)
        self.assertEqual(r["f1"], 1.0)


# ---------------------------------------------------------------------------
# check_file_set_match — tiered oracle
# ---------------------------------------------------------------------------

class FileSetMatchTieredTests(unittest.TestCase):

    def test_tiered_result_has_extra_fields(self):
        oracle = [
            _file("a/b", "x.go", tier="required"),
            _file("a/b", "y.go", tier="sufficient"),
        ]
        answer = [_file("a/b", "x.go")]
        r = check_file_set_match(answer, oracle)
        for key in ("weighted_recall", "weighted_f1", "required_recall", "required_total", "required_matched"):
            self.assertIn(key, r, f"missing key: {key}")

    def test_weighted_recall_formula(self):
        # required=2, sufficient=1 → total_weight=3
        # answer matches required only → matched_weight=2 → weighted_recall=2/3
        oracle = [
            _file("a/b", "main.go", tier="required"),
            _file("a/b", "test.go", tier="sufficient"),
        ]
        answer = [_file("a/b", "main.go")]
        r = check_file_set_match(answer, oracle)
        self.assertAlmostEqual(r["weighted_recall"], 2 / 3, places=3)

    def test_weighted_recall_all_required_matched(self):
        oracle = [
            _file("a/b", "main.go", tier="required"),
            _file("a/b", "util.go", tier="required"),
        ]
        answer = [_file("a/b", "main.go"), _file("a/b", "util.go")]
        r = check_file_set_match(answer, oracle)
        self.assertEqual(r["weighted_recall"], 1.0)

    def test_weighted_recall_only_sufficient_matched(self):
        # required=2, sufficient=1 → total_weight=3; match only sufficient(1)
        oracle = [
            _file("a/b", "main.go", tier="required"),
            _file("a/b", "test.go", tier="sufficient"),
        ]
        answer = [_file("a/b", "test.go")]
        r = check_file_set_match(answer, oracle)
        self.assertAlmostEqual(r["weighted_recall"], 1 / 3, places=3)

    def test_required_recall_perfect_when_all_required_found(self):
        oracle = [
            _file("a/b", "main.go", tier="required"),
            _file("a/b", "test.go", tier="sufficient"),
        ]
        answer = [_file("a/b", "main.go")]
        r = check_file_set_match(answer, oracle)
        self.assertEqual(r["required_recall"], 1.0)
        self.assertEqual(r["required_total"], 1)
        self.assertEqual(r["required_matched"], 1)

    def test_required_recall_zero_when_no_required_found(self):
        oracle = [
            _file("a/b", "main.go", tier="required"),
            _file("a/b", "test.go", tier="sufficient"),
        ]
        answer = [_file("a/b", "test.go")]
        r = check_file_set_match(answer, oracle)
        self.assertEqual(r["required_recall"], 0.0)
        self.assertEqual(r["required_matched"], 0)

    def test_required_recall_none_when_no_required_in_oracle(self):
        oracle = [_file("a/b", "test.go", tier="sufficient")]
        answer = [_file("a/b", "test.go")]
        r = check_file_set_match(answer, oracle)
        self.assertIsNone(r["required_recall"])
        self.assertEqual(r["required_total"], 0)

    def test_weighted_f1_higher_than_plain_f1_when_required_matched(self):
        # When we match the required file (weight 2) but miss sufficient (weight 1),
        # weighted_recall (2/3) > plain recall (1/2), so weighted_f1 > f1
        oracle = [
            _file("a/b", "main.go", tier="required"),
            _file("a/b", "test.go", tier="sufficient"),
        ]
        answer = [_file("a/b", "main.go")]
        r = check_file_set_match(answer, oracle)
        self.assertGreater(r["weighted_f1"], r["f1"])

    def test_weighted_f1_lower_than_plain_f1_when_only_sufficient_matched(self):
        # When we match only sufficient (weight 1) and miss required (weight 2),
        # weighted_recall (1/3) < plain recall (1/2), so weighted_f1 < f1
        oracle = [
            _file("a/b", "main.go", tier="required"),
            _file("a/b", "test.go", tier="sufficient"),
        ]
        answer = [_file("a/b", "test.go")]
        r = check_file_set_match(answer, oracle)
        self.assertLess(r["weighted_f1"], r["f1"])

    def test_perfect_match_tiered_equals_one(self):
        oracle = [
            _file("a/b", "main.go", tier="required"),
            _file("a/b", "test.go", tier="sufficient"),
        ]
        answer = [_file("a/b", "main.go"), _file("a/b", "test.go")]
        r = check_file_set_match(answer, oracle)
        self.assertEqual(r["weighted_recall"], 1.0)
        self.assertEqual(r["weighted_f1"], 1.0)
        self.assertEqual(r["required_recall"], 1.0)

    def test_no_match_tiered_equals_zero(self):
        oracle = [
            _file("a/b", "main.go", tier="required"),
            _file("a/b", "test.go", tier="sufficient"),
        ]
        answer = [_file("a/b", "other.go")]
        r = check_file_set_match(answer, oracle)
        self.assertEqual(r["weighted_recall"], 0.0)
        self.assertEqual(r["weighted_f1"], 0.0)
        self.assertEqual(r["required_recall"], 0.0)

    def test_partial_tier_annotation_triggers_tiered_scoring(self):
        # Only one file has a tier — has_tiers should still be True
        oracle = [
            _file("a/b", "main.go", tier="required"),
            _file("a/b", "other.go"),  # no tier key
        ]
        answer = [_file("a/b", "main.go")]
        r = check_file_set_match(answer, oracle)
        self.assertIn("weighted_f1", r)

    def test_three_required_two_sufficient(self):
        # total_weight = 3*2 + 2*1 = 8; match all required → matched_weight=6
        oracle = [
            _file("a/b", f"r{i}.go", tier="required") for i in range(3)
        ] + [
            _file("a/b", f"s{i}.go", tier="sufficient") for i in range(2)
        ]
        answer = [_file("a/b", f"r{i}.go") for i in range(3)]
        r = check_file_set_match(answer, oracle)
        self.assertAlmostEqual(r["weighted_recall"], 6 / 8, places=3)
        self.assertEqual(r["required_recall"], 1.0)
        self.assertEqual(r["required_matched"], 3)


# ---------------------------------------------------------------------------
# _get_primary_score
# ---------------------------------------------------------------------------

class GetPrimaryScoreTests(unittest.TestCase):

    def test_prefers_weighted_f1_for_file_set_match(self):
        result = {"f1": 0.5, "weighted_f1": 0.7}
        score = _get_primary_score(result, "file_set_match")
        self.assertEqual(score, 0.7)

    def test_falls_back_to_f1_when_no_weighted_f1(self):
        result = {"f1": 0.5}
        score = _get_primary_score(result, "file_set_match")
        self.assertEqual(score, 0.5)

    def test_returns_zero_when_no_f1_at_all(self):
        result = {}
        score = _get_primary_score(result, "file_set_match")
        self.assertEqual(score, 0.0)

    def test_symbol_resolution_uses_recall(self):
        result = {"recall": 0.8, "weighted_f1": 0.9}
        score = _get_primary_score(result, "symbol_resolution")
        self.assertEqual(score, 0.8)

    def test_dependency_chain_uses_chain_recall(self):
        result = {"chain_recall": 0.6}
        score = _get_primary_score(result, "dependency_chain")
        self.assertEqual(score, 0.6)

    def test_keyword_presence_uses_keyword_recall(self):
        result = {"keyword_recall": 0.75}
        score = _get_primary_score(result, "keyword_presence")
        self.assertEqual(score, 0.75)

    def test_unknown_check_type_returns_zero(self):
        result = {"f1": 0.9}
        score = _get_primary_score(result, "nonexistent_type")
        self.assertEqual(score, 0.0)

    def test_weighted_f1_zero_still_preferred_over_nonzero_f1(self):
        # weighted_f1 present but zero — should return 0.0, not fall back to f1
        result = {"f1": 0.8, "weighted_f1": 0.0}
        score = _get_primary_score(result, "file_set_match")
        self.assertEqual(score, 0.0)


if __name__ == "__main__":
    unittest.main()
