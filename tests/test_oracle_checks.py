#!/usr/bin/env python3
"""Comprehensive unit tests for oracle_checks.py matching logic.

Tests cover: _normalize_repo, _coerce_file_entry, _match_items,
check_file_set_match, check_symbol_resolution, check_keyword_presence,
and check_dependency_chain.
"""

import sys
from pathlib import Path

import pytest

# Import from a representative copy (all copies are identical).
sys.path.insert(
    0,
    str(
        Path(__file__).resolve().parent.parent
        / "benchmarks"
        / "csb"
        / "crossrepo"
        / "ccx-config-trace-010"
        / "tests"
    ),
)
import oracle_checks


# =========================================================================
# 1. _normalize_repo
# =========================================================================
class TestNormalizeRepo:
    """Tests for _normalize_repo — reduces repo identifiers to base names."""

    def test_sg_evals_prefix_stripping(self):
        assert oracle_checks._normalize_repo("sg-evals/kubernetes-client-go") == "kubernetes-client-go"

    def test_version_suffix_removal(self):
        assert oracle_checks._normalize_repo("client-go--v0.32.0") == "client-go"

    def test_combined_prefix_and_suffix(self):
        assert oracle_checks._normalize_repo("sg-evals/kubernetes--v1.32.0") == "kubernetes"

    def test_github_com_prefix(self):
        # _normalize_repo only strips org/ prefix (last segment), so
        # "github.com/sg-evals/foo" splits on "/" and takes "foo"
        assert oracle_checks._normalize_repo("github.com/sg-evals/foo") == "foo"

    def test_git_suffix_not_stripped(self):
        # _normalize_repo does not strip .git — it only strips --hash/--version
        # Document actual behavior: .git is kept
        result = oracle_checks._normalize_repo("repo.git")
        assert result == "repo.git"

    def test_noop_on_clean_name(self):
        assert oracle_checks._normalize_repo("kubernetes") == "kubernetes"

    def test_noop_on_simple_org_repo(self):
        assert oracle_checks._normalize_repo("openjdk/jdk") == "jdk"

    def test_hash_suffix_removal(self):
        assert oracle_checks._normalize_repo("sg-evals/firefox--871325b8") == "firefox"

    def test_lowercased(self):
        assert oracle_checks._normalize_repo("Chromium/Chromium") == "chromium"

    def test_empty_string(self):
        assert oracle_checks._normalize_repo("") == ""

    def test_multiple_slashes(self):
        # "a/b/c" -> rsplit("/",1) -> ["a/b", "c"] -> "c"
        assert oracle_checks._normalize_repo("a/b/c") == "c"

    def test_double_dash_short_hex_not_stripped(self):
        # Short hex (<6 chars) should NOT be stripped
        assert oracle_checks._normalize_repo("repo--abc") == "repo--abc"

    def test_double_dash_six_char_hex_stripped(self):
        assert oracle_checks._normalize_repo("repo--abcdef") == "repo"


# =========================================================================
# 2. _coerce_file_entry
# =========================================================================
class TestCoerceFileEntry:
    """Tests for _coerce_file_entry — normalizes diverse input formats."""

    def test_string_with_org_and_repo_and_path(self):
        result = oracle_checks._coerce_file_entry("sg-evals/kubernetes--v1.32.0/pkg/api/types.go")
        assert result == {"repo": "sg-evals/kubernetes--v1.32.0", "path": "pkg/api/types.go"}

    def test_string_simple_path(self):
        # "path/to/file.go" splits as ["path", "to", "file.go"] -> repo="path/to", path="file.go"
        result = oracle_checks._coerce_file_entry("path/to/file.go")
        assert result == {"repo": "path/to", "path": "file.go"}

    def test_string_bare_filename(self):
        result = oracle_checks._coerce_file_entry("file.go")
        assert result == {"repo": "", "path": "file.go"}

    def test_string_github_com_prefix(self):
        result = oracle_checks._coerce_file_entry("github.com/sg-evals/repo--hash/src/main.go")
        assert result == {"repo": "sg-evals/repo--hash", "path": "src/main.go"}

    def test_dict_with_path_key_passthrough(self):
        entry = {"repo": "a/b", "path": "x.go"}
        result = oracle_checks._coerce_file_entry(entry)
        assert result is entry  # same object returned

    def test_dict_with_extra_keys_passthrough(self):
        entry = {"repo": "a/b", "path": "x.go", "tier": "required"}
        result = oracle_checks._coerce_file_entry(entry)
        assert result is entry

    def test_dict_without_path_key_passthrough(self):
        # Dict input is returned as-is regardless of keys
        entry = {"file": "x.go"}
        result = oracle_checks._coerce_file_entry(entry)
        assert result is entry

    def test_non_string_non_dict(self):
        result = oracle_checks._coerce_file_entry(42)
        assert result == {"repo": "", "path": "42"}

    def test_string_two_components(self):
        result = oracle_checks._coerce_file_entry("org/file.go")
        assert result == {"repo": "org", "path": "file.go"}


# =========================================================================
# 3. _match_items
# =========================================================================
class TestMatchItems:
    """Tests for _match_items — two-pass matching with normalization."""

    def test_exact_match(self):
        oracle = [{"repo": "a/b", "path": "x.go"}]
        answer = [{"repo": "a/b", "path": "x.go"}]
        matched, missing, extra = oracle_checks._match_items(answer, oracle, ["repo", "path"])
        assert len(matched) == 1
        assert len(missing) == 0
        assert len(extra) == 0

    def test_normalized_match_repo_prefix(self):
        """sg-evals/jdk--742e735d should match openjdk/jdk via normalization."""
        oracle = [{"repo": "sg-evals/jdk--742e735d", "path": "src/Foo.java"}]
        answer = [{"repo": "openjdk/jdk", "path": "src/Foo.java"}]
        matched, missing, extra = oracle_checks._match_items(answer, oracle, ["repo", "path"])
        assert len(matched) == 1
        assert len(missing) == 0
        assert len(extra) == 0

    def test_path_only_fallback(self):
        """Different repos, same path — should match via path-only fallback."""
        oracle = [{"repo": "upstream/thing", "path": "src/main.go"}]
        answer = [{"repo": "totally-different/name", "path": "src/main.go"}]
        matched, missing, extra = oracle_checks._match_items(answer, oracle, ["repo", "path"])
        assert len(matched) == 1

    def test_no_match(self):
        oracle = [{"repo": "a/b", "path": "x.go"}]
        answer = [{"repo": "c/d", "path": "y.go"}]
        matched, missing, extra = oracle_checks._match_items(answer, oracle, ["repo", "path"])
        assert len(matched) == 0
        assert len(missing) == 1
        assert len(extra) == 1

    def test_partial_match(self):
        oracle = [
            {"repo": "a/b", "path": "x.go"},
            {"repo": "a/b", "path": "y.go"},
            {"repo": "a/b", "path": "z.go"},
        ]
        answer = [
            {"repo": "a/b", "path": "x.go"},
            {"repo": "a/b", "path": "z.go"},
            {"repo": "a/b", "path": "w.go"},  # extra
        ]
        matched, missing, extra = oracle_checks._match_items(answer, oracle, ["repo", "path"])
        assert len(matched) == 2
        assert len(missing) == 1  # y.go
        assert len(extra) == 1  # w.go

    def test_empty_oracle(self):
        matched, missing, extra = oracle_checks._match_items(
            [{"repo": "a", "path": "x"}], [], ["repo", "path"]
        )
        assert len(matched) == 0
        assert len(missing) == 0
        assert len(extra) == 1

    def test_empty_answer(self):
        matched, missing, extra = oracle_checks._match_items(
            [], [{"repo": "a", "path": "x"}], ["repo", "path"]
        )
        assert len(matched) == 0
        assert len(missing) == 1
        assert len(extra) == 0

    def test_three_field_exact(self):
        """Symbol-level matching with repo+path+symbol."""
        oracle = [{"repo": "a/b", "path": "x.go", "symbol": "Foo"}]
        answer = [{"repo": "a/b", "path": "x.go", "symbol": "Foo"}]
        matched, missing, extra = oracle_checks._match_items(
            answer, oracle, ["repo", "path", "symbol"]
        )
        assert len(matched) == 1

    def test_three_field_normalized(self):
        oracle = [{"repo": "sg-evals/jdk--abcdef", "path": "x.java", "symbol": "Bar"}]
        answer = [{"repo": "openjdk/jdk", "path": "x.java", "symbol": "Bar"}]
        matched, missing, extra = oracle_checks._match_items(
            answer, oracle, ["repo", "path", "symbol"]
        )
        assert len(matched) == 1

    def test_duplicate_oracle_entries(self):
        """Duplicate oracle entries should be deduplicated by key."""
        oracle = [
            {"repo": "a/b", "path": "x.go"},
            {"repo": "a/b", "path": "x.go"},
        ]
        answer = [{"repo": "a/b", "path": "x.go"}]
        matched, missing, extra = oracle_checks._match_items(answer, oracle, ["repo", "path"])
        assert len(matched) == 1
        assert len(missing) == 0


# =========================================================================
# 4. check_file_set_match
# =========================================================================
class TestCheckFileSetMatch:
    """Tests for check_file_set_match — file overlap scoring."""

    def test_perfect_match(self):
        oracle = [{"repo": "a/b", "path": "x.go"}, {"repo": "a/b", "path": "y.go"}]
        answer = [{"repo": "a/b", "path": "x.go"}, {"repo": "a/b", "path": "y.go"}]
        result = oracle_checks.check_file_set_match(answer, oracle)
        assert result["recall"] == 1.0
        assert result["precision"] == 1.0
        assert result["f1"] == 1.0

    def test_subset_found(self):
        oracle = [{"repo": "a/b", "path": "x.go"}, {"repo": "a/b", "path": "y.go"}]
        answer = [{"repo": "a/b", "path": "x.go"}]
        result = oracle_checks.check_file_set_match(answer, oracle)
        assert result["recall"] == 0.5
        assert result["precision"] == 1.0

    def test_extra_files(self):
        oracle = [{"repo": "a/b", "path": "x.go"}]
        answer = [{"repo": "a/b", "path": "x.go"}, {"repo": "a/b", "path": "z.go"}]
        result = oracle_checks.check_file_set_match(answer, oracle)
        assert result["recall"] == 1.0
        assert result["precision"] == 0.5

    def test_empty_agent_answer(self):
        oracle = [{"repo": "a/b", "path": "x.go"}, {"repo": "a/b", "path": "y.go"}]
        result = oracle_checks.check_file_set_match([], oracle)
        assert result["recall"] == 0.0
        assert result["precision"] == 0.0
        assert result["f1"] == 0.0

    def test_empty_oracle(self):
        result = oracle_checks.check_file_set_match(
            [{"repo": "a/b", "path": "x.go"}], []
        )
        # No oracle files: recall=1.0 (vacuously), precision=0.0
        assert result["recall"] == 1.0
        assert result["precision"] == 0.0

    def test_cross_repo_notation(self):
        """Files with :: notation should match via coercion + normalization."""
        # String format "client-go::rest/config.go" coerced to {"repo":"client-go", "path":"rest/config.go"}
        oracle = [{"repo": "sg-evals/client-go--v0.32.0", "path": "rest/config.go"}]
        answer = [{"repo": "client-go", "path": "rest/config.go"}]
        result = oracle_checks.check_file_set_match(answer, oracle)
        assert result["f1"] == 1.0

    def test_string_entries_coerced(self):
        """String file entries should be coerced to dicts."""
        oracle = ["sg-evals/kubernetes--v1.32.0/pkg/api/types.go"]
        answer = [{"repo": "kubernetes/kubernetes", "path": "pkg/api/types.go"}]
        result = oracle_checks.check_file_set_match(answer, oracle)
        # Both normalize to "kubernetes" repo, same path
        assert result["f1"] == 1.0

    def test_mirror_vs_upstream(self):
        """sg-evals mirror name should match upstream org/repo."""
        oracle = [{"repo": "sg-evals/jdk--742e735d", "path": "src/Foo.java"}]
        answer = [{"repo": "openjdk/jdk", "path": "src/Foo.java"}]
        result = oracle_checks.check_file_set_match(answer, oracle)
        assert result["f1"] == 1.0

    def test_tiered_scoring(self):
        """Weighted recall/F1 when oracle has tier annotations."""
        oracle = [
            {"repo": "a/b", "path": "x.go", "tier": "required"},
            {"repo": "a/b", "path": "y.go", "tier": "sufficient"},
        ]
        # Agent finds only the required file
        answer = [{"repo": "a/b", "path": "x.go"}]
        result = oracle_checks.check_file_set_match(answer, oracle)
        assert result["required_recall"] == 1.0
        # weighted_recall: matched required(2) / total(2+1=3) = 0.6667
        assert result["weighted_recall"] == pytest.approx(0.6667, abs=0.001)
        assert "weighted_f1" in result

    def test_tiered_all_matched(self):
        oracle = [
            {"repo": "a/b", "path": "x.go", "tier": "required"},
            {"repo": "a/b", "path": "y.go", "tier": "sufficient"},
        ]
        answer = [
            {"repo": "a/b", "path": "x.go"},
            {"repo": "a/b", "path": "y.go"},
        ]
        result = oracle_checks.check_file_set_match(answer, oracle)
        assert result["weighted_recall"] == 1.0
        assert result["required_recall"] == 1.0

    def test_no_tier_no_weighted_keys(self):
        oracle = [{"repo": "a/b", "path": "x.go"}]
        answer = [{"repo": "a/b", "path": "x.go"}]
        result = oracle_checks.check_file_set_match(answer, oracle)
        assert "weighted_recall" not in result
        assert "required_recall" not in result


# =========================================================================
# 5. check_symbol_resolution
# =========================================================================
class TestCheckSymbolResolution:
    """Tests for check_symbol_resolution — symbol overlap scoring."""

    def test_exact_match(self):
        oracle = [{"repo": "a/b", "path": "x.go", "symbol": "Foo"}]
        answer = [{"repo": "a/b", "path": "x.go", "symbol": "Foo"}]
        result = oracle_checks.check_symbol_resolution(answer, oracle)
        assert result["recall"] == 1.0
        assert result["precision"] == 1.0

    def test_sg_evals_prefix_match(self):
        oracle = [{"repo": "sg-evals/jdk--742e735d", "path": "src/Foo.java", "symbol": "doStuff"}]
        answer = [{"repo": "openjdk/jdk", "path": "src/Foo.java", "symbol": "doStuff"}]
        result = oracle_checks.check_symbol_resolution(answer, oracle)
        assert result["recall"] == 1.0

    def test_version_suffix_match(self):
        oracle = [{"repo": "sg-evals/client-go--v0.32.0", "path": "rest/config.go", "symbol": "NewConfig"}]
        answer = [{"repo": "client-go", "path": "rest/config.go", "symbol": "NewConfig"}]
        result = oracle_checks.check_symbol_resolution(answer, oracle)
        assert result["recall"] == 1.0

    def test_no_match_different_symbol(self):
        oracle = [{"repo": "a/b", "path": "x.go", "symbol": "Foo"}]
        answer = [{"repo": "a/b", "path": "x.go", "symbol": "Bar"}]
        result = oracle_checks.check_symbol_resolution(answer, oracle)
        assert result["recall"] == 0.0

    def test_partial_match(self):
        oracle = [
            {"repo": "a/b", "path": "x.go", "symbol": "Foo"},
            {"repo": "a/b", "path": "y.go", "symbol": "Bar"},
        ]
        answer = [{"repo": "a/b", "path": "x.go", "symbol": "Foo"}]
        result = oracle_checks.check_symbol_resolution(answer, oracle)
        assert result["recall"] == 0.5
        assert result["precision"] == 1.0

    def test_empty_answer(self):
        oracle = [{"repo": "a/b", "path": "x.go", "symbol": "Foo"}]
        result = oracle_checks.check_symbol_resolution([], oracle)
        assert result["recall"] == 0.0
        assert result["precision"] == 0.0

    def test_empty_oracle(self):
        answer = [{"repo": "a/b", "path": "x.go", "symbol": "Foo"}]
        result = oracle_checks.check_symbol_resolution(answer, [])
        assert result["recall"] == 1.0  # vacuous
        assert result["precision"] == 0.0

    # --- Accept-any-of group tests ---

    def test_group_match_first_alternative(self):
        """Matching the first alternative in a group gives full recall."""
        oracle = [
            {"repo": "a/b", "path": "x.go", "symbol": "Foo", "group": "g1"},
            {"repo": "c/d", "path": "y.go", "symbol": "Foo", "group": "g1"},
        ]
        answer = [{"repo": "a/b", "path": "x.go", "symbol": "Foo"}]
        result = oracle_checks.check_symbol_resolution(answer, oracle)
        assert result["recall"] == 1.0
        assert result["group_aware"] is True
        assert result["groups_satisfied"] == 1

    def test_group_match_second_alternative(self):
        """Matching the second alternative in a group gives full recall."""
        oracle = [
            {"repo": "a/b", "path": "x.go", "symbol": "Foo", "group": "g1"},
            {"repo": "c/d", "path": "y.go", "symbol": "Foo", "group": "g1"},
        ]
        answer = [{"repo": "c/d", "path": "y.go", "symbol": "Foo"}]
        result = oracle_checks.check_symbol_resolution(answer, oracle)
        assert result["recall"] == 1.0
        assert result["groups_satisfied"] == 1

    def test_group_no_match(self):
        """No match in a group gives zero recall."""
        oracle = [
            {"repo": "a/b", "path": "x.go", "symbol": "Foo", "group": "g1"},
            {"repo": "c/d", "path": "y.go", "symbol": "Foo", "group": "g1"},
        ]
        answer = [{"repo": "e/f", "path": "z.go", "symbol": "Bar"}]
        result = oracle_checks.check_symbol_resolution(answer, oracle)
        assert result["recall"] == 0.0
        assert result["groups_satisfied"] == 0

    def test_group_with_ungrouped(self):
        """Mixed grouped and ungrouped symbols: recall = satisfied / total."""
        oracle = [
            {"repo": "a/b", "path": "x.go", "symbol": "Foo", "group": "g1"},
            {"repo": "c/d", "path": "y.go", "symbol": "Foo", "group": "g1"},
            {"repo": "e/f", "path": "z.go", "symbol": "Bar"},  # ungrouped
        ]
        # Match one alternative from the group + the ungrouped symbol
        answer = [
            {"repo": "c/d", "path": "y.go", "symbol": "Foo"},
            {"repo": "e/f", "path": "z.go", "symbol": "Bar"},
        ]
        result = oracle_checks.check_symbol_resolution(answer, oracle)
        assert result["recall"] == 1.0  # 1 group + 1 ungrouped = 2/2
        assert result["groups_satisfied"] == 1

    def test_group_partial_with_ungrouped(self):
        """One group matched, one ungrouped missed."""
        oracle = [
            {"repo": "a/b", "path": "x.go", "symbol": "Foo", "group": "g1"},
            {"repo": "c/d", "path": "y.go", "symbol": "Foo", "group": "g1"},
            {"repo": "e/f", "path": "z.go", "symbol": "Bar"},
        ]
        answer = [{"repo": "a/b", "path": "x.go", "symbol": "Foo"}]
        result = oracle_checks.check_symbol_resolution(answer, oracle)
        assert result["recall"] == 0.5  # 1 group satisfied / 2 total

    def test_multiple_groups(self):
        """Two separate groups, each with alternatives."""
        oracle = [
            {"repo": "a/b", "path": "x.go", "symbol": "Foo", "group": "g1"},
            {"repo": "c/d", "path": "y.go", "symbol": "Foo", "group": "g1"},
            {"repo": "e/f", "path": "w.go", "symbol": "Bar", "group": "g2"},
            {"repo": "g/h", "path": "v.go", "symbol": "Bar", "group": "g2"},
        ]
        # Match one from each group
        answer = [
            {"repo": "c/d", "path": "y.go", "symbol": "Foo"},
            {"repo": "e/f", "path": "w.go", "symbol": "Bar"},
        ]
        result = oracle_checks.check_symbol_resolution(answer, oracle)
        assert result["recall"] == 1.0
        assert result["groups_total"] == 2
        assert result["groups_satisfied"] == 2

    def test_no_group_field_backward_compat(self):
        """Without group fields, behaves identically to original logic."""
        oracle = [
            {"repo": "a/b", "path": "x.go", "symbol": "Foo"},
            {"repo": "c/d", "path": "y.go", "symbol": "Bar"},
        ]
        answer = [{"repo": "a/b", "path": "x.go", "symbol": "Foo"}]
        result = oracle_checks.check_symbol_resolution(answer, oracle)
        assert result["recall"] == 0.5
        assert "group_aware" not in result

    def test_group_missing_shows_unsatisfied_only(self):
        """Missing list only contains symbols from unsatisfied groups."""
        oracle = [
            {"repo": "a/b", "path": "x.go", "symbol": "Foo", "group": "g1"},
            {"repo": "c/d", "path": "y.go", "symbol": "Foo", "group": "g1"},
            {"repo": "e/f", "path": "z.go", "symbol": "Bar"},
        ]
        # Match the group but miss the ungrouped
        answer = [{"repo": "a/b", "path": "x.go", "symbol": "Foo"}]
        result = oracle_checks.check_symbol_resolution(answer, oracle)
        # Missing should only contain the ungrouped Bar, not the alternative y.go:Foo
        missing_symbols = [m["symbol"] for m in result["missing"]]
        assert "Bar" in missing_symbols
        assert "Foo" not in missing_symbols


# =========================================================================
# 6. check_keyword_presence
# =========================================================================
class TestCheckKeywordPresence:
    """Tests for check_keyword_presence — keyword recall scoring."""

    def test_all_keywords_found(self):
        result = oracle_checks.check_keyword_presence(
            "The Foo function calls Bar and Baz",
            ["foo", "bar", "baz"],
        )
        assert result["keyword_recall"] == 1.0
        assert len(result["found"]) == 3
        assert len(result["missing"]) == 0

    def test_some_keywords_found(self):
        result = oracle_checks.check_keyword_presence(
            "The Foo function calls Bar",
            ["foo", "bar", "baz"],
        )
        assert result["keyword_recall"] == pytest.approx(0.6667, abs=0.001)
        assert len(result["found"]) == 2
        assert result["missing"] == ["baz"]

    def test_case_insensitive(self):
        result = oracle_checks.check_keyword_presence(
            "KUBERNETES uses ETCD for storage",
            ["kubernetes", "etcd"],
        )
        assert result["keyword_recall"] == 1.0

    def test_no_keywords_found(self):
        result = oracle_checks.check_keyword_presence(
            "Nothing relevant here",
            ["foo", "bar"],
        )
        assert result["keyword_recall"] == 0.0
        assert len(result["missing"]) == 2

    def test_empty_keywords_list(self):
        result = oracle_checks.check_keyword_presence("some text", [])
        assert result["keyword_recall"] == 1.0  # vacuous

    def test_empty_answer_text(self):
        result = oracle_checks.check_keyword_presence("", ["foo"])
        assert result["keyword_recall"] == 0.0

    def test_substring_match(self):
        """Keywords should match as substrings, not whole words."""
        result = oracle_checks.check_keyword_presence(
            "The foobar function",
            ["foo"],
        )
        assert result["keyword_recall"] == 1.0

    def test_total_field(self):
        result = oracle_checks.check_keyword_presence("foo bar", ["foo", "bar", "baz"])
        assert result["total"] == 3


# =========================================================================
# 7. check_dependency_chain
# =========================================================================
class TestCheckDependencyChain:
    """Tests for check_dependency_chain — ordered dependency tracing."""

    def test_correct_order(self):
        chain = [
            {"repo": "a", "path": "x.go", "symbol": "f1"},
            {"repo": "b", "path": "y.go", "symbol": "f2"},
            {"repo": "c", "path": "z.go", "symbol": "f3"},
        ]
        result = oracle_checks.check_dependency_chain(chain, chain)
        assert result["order_correct"] is True
        assert result["chain_recall"] == 1.0
        assert result["matched_steps"] == 3
        assert result["missing_steps"] == []

    def test_reversed_order(self):
        oracle = [
            {"repo": "a", "path": "x.go", "symbol": "f1"},
            {"repo": "b", "path": "y.go", "symbol": "f2"},
        ]
        answer = [
            {"repo": "b", "path": "y.go", "symbol": "f2"},
            {"repo": "a", "path": "x.go", "symbol": "f1"},
        ]
        result = oracle_checks.check_dependency_chain(answer, oracle)
        # All steps found, but order is wrong
        assert result["chain_recall"] == 1.0
        assert result["order_correct"] is False

    def test_missing_entries(self):
        oracle = [
            {"repo": "a", "path": "x.go", "symbol": "f1"},
            {"repo": "b", "path": "y.go", "symbol": "f2"},
            {"repo": "c", "path": "z.go", "symbol": "f3"},
        ]
        answer = [
            {"repo": "a", "path": "x.go", "symbol": "f1"},
        ]
        result = oracle_checks.check_dependency_chain(answer, oracle)
        assert result["chain_recall"] == pytest.approx(0.3333, abs=0.001)
        assert result["order_correct"] is False
        assert result["matched_steps"] == 1
        assert len(result["missing_steps"]) == 2

    def test_empty_answer(self):
        oracle = [{"repo": "a", "path": "x.go", "symbol": "f1"}]
        result = oracle_checks.check_dependency_chain([], oracle)
        assert result["chain_recall"] == 0.0
        assert result["matched_steps"] == 0

    def test_empty_oracle(self):
        answer = [{"repo": "a", "path": "x.go", "symbol": "f1"}]
        result = oracle_checks.check_dependency_chain(answer, [])
        assert result["chain_recall"] == 1.0  # vacuous
        assert result["order_correct"] is True

    def test_normalized_repo_matching(self):
        """Mirror repo names should match upstream names."""
        oracle = [
            {"repo": "sg-evals/jdk--742e735d", "path": "src/Foo.java", "symbol": "init"},
            {"repo": "sg-evals/client-go--v0.32.0", "path": "rest/config.go", "symbol": "NewConfig"},
        ]
        answer = [
            {"repo": "openjdk/jdk", "path": "src/Foo.java", "symbol": "init"},
            {"repo": "client-go", "path": "rest/config.go", "symbol": "NewConfig"},
        ]
        result = oracle_checks.check_dependency_chain(answer, oracle)
        assert result["chain_recall"] == 1.0
        assert result["order_correct"] is True

    def test_path_only_fallback(self):
        """Different repo names but same path+symbol should still match."""
        oracle = [{"repo": "upstream/thing", "path": "main.go", "symbol": "Run"}]
        answer = [{"repo": "fork/other", "path": "main.go", "symbol": "Run"}]
        result = oracle_checks.check_dependency_chain(answer, oracle)
        assert result["chain_recall"] == 1.0

    def test_partial_order(self):
        """Subset in correct relative order — recall partial, order False (missing steps)."""
        oracle = [
            {"repo": "a", "path": "x.go", "symbol": "f1"},
            {"repo": "b", "path": "y.go", "symbol": "f2"},
            {"repo": "c", "path": "z.go", "symbol": "f3"},
        ]
        answer = [
            {"repo": "a", "path": "x.go", "symbol": "f1"},
            {"repo": "c", "path": "z.go", "symbol": "f3"},
        ]
        result = oracle_checks.check_dependency_chain(answer, oracle)
        assert result["chain_recall"] == pytest.approx(0.6667, abs=0.001)
        # order_correct requires ALL steps matched
        assert result["order_correct"] is False


# =========================================================================
# 8. _get_primary_score
# =========================================================================
class TestGetPrimaryScore:
    """Tests for _get_primary_score — score extraction helper."""

    def test_file_set_match_prefers_weighted_f1(self):
        result = {"f1": 0.5, "weighted_f1": 0.8}
        assert oracle_checks._get_primary_score(result, "file_set_match") == 0.8

    def test_file_set_match_falls_back_to_f1(self):
        result = {"f1": 0.5}
        assert oracle_checks._get_primary_score(result, "file_set_match") == 0.5

    def test_symbol_resolution_uses_recall(self):
        result = {"recall": 0.75}
        assert oracle_checks._get_primary_score(result, "symbol_resolution") == 0.75

    def test_dependency_chain_uses_chain_recall(self):
        result = {"chain_recall": 0.6}
        assert oracle_checks._get_primary_score(result, "dependency_chain") == 0.6

    def test_keyword_presence_uses_keyword_recall(self):
        result = {"keyword_recall": 0.333}
        assert oracle_checks._get_primary_score(result, "keyword_presence") == 0.333

    def test_json_schema_match_bool_true(self):
        result = {"valid": True}
        assert oracle_checks._get_primary_score(result, "json_schema_match") == 1.0

    def test_json_schema_match_bool_false(self):
        result = {"valid": False}
        assert oracle_checks._get_primary_score(result, "json_schema_match") == 0.0

    def test_unknown_check_type(self):
        result = {"something": 42}
        assert oracle_checks._get_primary_score(result, "nonexistent") == 0


# =========================================================================
# 9. check_provenance
# =========================================================================
class TestCheckProvenance:
    """Tests for check_provenance — citation checking."""

    def test_all_cited(self):
        result = oracle_checks.check_provenance(
            "Found in kubernetes/kubernetes at pkg/api/types.go",
            must_cite_paths=["pkg/api/types.go"],
            must_cite_repos=["kubernetes/kubernetes"],
        )
        assert result["provenance_score"] == 1.0

    def test_partial_citations(self):
        result = oracle_checks.check_provenance(
            "Found in kubernetes/kubernetes at pkg/api/types.go",
            must_cite_paths=["pkg/api/types.go", "cmd/main.go"],
            must_cite_repos=["kubernetes/kubernetes"],
        )
        assert result["provenance_score"] == pytest.approx(0.6667, abs=0.001)

    def test_no_citations(self):
        result = oracle_checks.check_provenance(
            "Nothing relevant",
            must_cite_paths=["a.go"],
            must_cite_repos=["k8s"],
        )
        assert result["provenance_score"] == 0.0

    def test_empty_requirements(self):
        result = oracle_checks.check_provenance("anything")
        assert result["provenance_score"] == 1.0  # vacuous
