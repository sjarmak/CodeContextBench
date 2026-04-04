"""Tests for report summary/detailed view modes.

Covers:
- _aggregate_by_dimension grouping logic
- _aggregate_by_leaf_category grouping logic
- display_report with view_mode="summary" text output
- display_report with view_mode="detailed" text output
- --summary and --detailed CLI flags are mutually exclusive
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from lib.csb.report import (
    _aggregate_by_dimension,
    _aggregate_by_leaf_category,
    _load_category_to_dimension_map,
    display_report,
    load_submission,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def sample_results() -> list[dict]:
    """Results with failure_categories for aggregation tests."""
    return [
        {
            "task_name": "task_1",
            "reward": 0.0,
            "failure_categories": [
                {"category": "retrieval_failure"},
                {"category": "query_churn"},
            ],
        },
        {
            "task_name": "task_2",
            "reward": 0.5,
            "failure_categories": [
                {"category": "retrieval_failure"},
            ],
        },
        {
            "task_name": "task_3",
            "reward": 1.0,
            "failure_categories": [],
        },
        {
            "task_name": "task_4",
            "reward": 0.0,
            "failure_categories": [
                {"category": "execution_error"},
            ],
        },
    ]


@pytest.fixture()
def cat_to_dim() -> dict[str, str]:
    return {
        "retrieval_failure": "Retrieval",
        "query_churn": "Retrieval",
        "execution_error": "Execution",
    }


@pytest.fixture()
def submission_file(tmp_path: Path) -> Path:
    submission = {
        "csb_score": 42.5,
        "suite": "quick",
        "agent_info": {"name": "test-agent"},
        "metadata": {"timestamp": "2026-04-03T12:00:00Z"},
        "results": [
            {
                "task_name": "task_1",
                "reward": 0.0,
                "work_type": "fix",
                "failure_categories": [
                    {"category": "retrieval_failure"},
                ],
            },
            {
                "task_name": "task_2",
                "reward": 1.0,
                "work_type": "extend",
                "failure_categories": [],
            },
        ],
    }
    path = tmp_path / "results.json"
    path.write_text(json.dumps(submission))
    return path


# ---------------------------------------------------------------------------
# _aggregate_by_dimension
# ---------------------------------------------------------------------------


class TestAggregateByDimension:
    def test_groups_by_dimension(self, sample_results, cat_to_dim) -> None:
        result = _aggregate_by_dimension(sample_results, cat_to_dim)
        assert "Retrieval" in result
        assert "Execution" in result

    def test_task_count(self, sample_results, cat_to_dim) -> None:
        result = _aggregate_by_dimension(sample_results, cat_to_dim)
        # task_1 and task_2 have retrieval categories
        assert result["Retrieval"]["task_count"] == 2
        # task_4 has execution
        assert result["Execution"]["task_count"] == 1

    def test_annotation_count(self, sample_results, cat_to_dim) -> None:
        result = _aggregate_by_dimension(sample_results, cat_to_dim)
        # retrieval_failure x2 + query_churn x1 = 3 annotations under Retrieval
        assert result["Retrieval"]["annotation_count"] == 3

    def test_unknown_dimension(self) -> None:
        results = [
            {
                "task_name": "t",
                "reward": 0.0,
                "failure_categories": [{"category": "unknown_cat"}],
            }
        ]
        result = _aggregate_by_dimension(results, {})
        assert "Unknown" in result

    def test_empty_results(self, cat_to_dim) -> None:
        result = _aggregate_by_dimension([], cat_to_dim)
        assert result == {}


# ---------------------------------------------------------------------------
# _aggregate_by_leaf_category
# ---------------------------------------------------------------------------


class TestAggregateByLeafCategory:
    def test_groups_by_category(self, sample_results, cat_to_dim) -> None:
        result = _aggregate_by_leaf_category(sample_results, cat_to_dim)
        assert "retrieval_failure" in result
        assert "query_churn" in result
        assert "execution_error" in result

    def test_dimension_parent(self, sample_results, cat_to_dim) -> None:
        result = _aggregate_by_leaf_category(sample_results, cat_to_dim)
        assert result["retrieval_failure"]["dimension"] == "Retrieval"
        assert result["execution_error"]["dimension"] == "Execution"

    def test_count(self, sample_results, cat_to_dim) -> None:
        result = _aggregate_by_leaf_category(sample_results, cat_to_dim)
        assert result["retrieval_failure"]["count"] == 2
        assert result["query_churn"]["count"] == 1

    def test_tasks_list(self, sample_results, cat_to_dim) -> None:
        result = _aggregate_by_leaf_category(sample_results, cat_to_dim)
        task_names = [t[0] for t in result["retrieval_failure"]["tasks"]]
        assert "task_1" in task_names
        assert "task_2" in task_names

    def test_empty_results(self, cat_to_dim) -> None:
        result = _aggregate_by_leaf_category([], cat_to_dim)
        assert result == {}


# ---------------------------------------------------------------------------
# display_report with view modes
# ---------------------------------------------------------------------------


class TestDisplayReportViewModes:
    def test_default_mode(self, submission_file: Path, capsys) -> None:
        result = display_report(str(submission_file), fmt="text")
        assert result == 0
        captured = capsys.readouterr()
        assert "42.5" in captured.out

    def test_summary_mode(self, submission_file: Path, capsys) -> None:
        result = display_report(str(submission_file), fmt="text", view_mode="summary")
        assert result == 0

    def test_detailed_mode(self, submission_file: Path, capsys) -> None:
        result = display_report(str(submission_file), fmt="text", view_mode="detailed")
        assert result == 0

    def test_json_format_ignores_view_mode(self, submission_file: Path, capsys) -> None:
        result = display_report(str(submission_file), fmt="json", view_mode="summary")
        assert result == 0
        captured = capsys.readouterr()
        parsed = json.loads(captured.out)
        assert parsed["csb_score"] == 42.5

    def test_missing_file_returns_1(self, tmp_path: Path) -> None:
        result = display_report(str(tmp_path / "nope.json"))
        assert result == 1


# ---------------------------------------------------------------------------
# CLI mutual exclusivity
# ---------------------------------------------------------------------------


class TestReportCLIFlags:
    def test_summary_flag_parsed(self) -> None:
        from lib.csb.cli import main

        with patch("lib.csb.report.display_report", return_value=0) as mock:
            main(["report", "results.json", "--summary"])
            _, kwargs = mock.call_args
            assert kwargs["view_mode"] == "summary"

    def test_detailed_flag_parsed(self) -> None:
        from lib.csb.cli import main

        with patch("lib.csb.report.display_report", return_value=0) as mock:
            main(["report", "results.json", "--detailed"])
            _, kwargs = mock.call_args
            assert kwargs["view_mode"] == "detailed"

    def test_both_flags_error(self) -> None:
        from lib.csb.cli import main

        with pytest.raises(SystemExit) as exc_info:
            main(["report", "results.json", "--summary", "--detailed"])
        assert exc_info.value.code != 0

    def test_no_flags_default(self) -> None:
        from lib.csb.cli import main

        with patch("lib.csb.report.display_report", return_value=0) as mock:
            main(["report", "results.json"])
            _, kwargs = mock.call_args
            assert kwargs["view_mode"] is None
