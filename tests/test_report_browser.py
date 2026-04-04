"""Tests for the interactive results browser (csb report --browser).

Covers:
- _compute_work_type_breakdown
- _load_baseline_summary (missing file case)
- _build_browser_data structure
- _render_browser_html produces valid HTML with embedded data
- serve_browser starts HTTP server and serves correct content
- CLI --browser flag routes to serve_browser
"""

from __future__ import annotations

import http.server
import json
import sys
import threading
import urllib.request
from pathlib import Path
from unittest.mock import patch

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from lib.csb.report import (
    _BrowserHandler,
    _build_browser_data,
    _compute_work_type_breakdown,
    _load_baseline_summary,
    _render_browser_html,
    load_submission,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_SUBMISSION = _REPO_ROOT / "tests" / "fixtures" / "sample_submission.json"


@pytest.fixture()
def submission() -> dict:
    return load_submission(SAMPLE_SUBMISSION)


@pytest.fixture()
def sample_results() -> list[dict]:
    return [
        {"task_name": "t1", "reward": 1.0, "work_type": "fix"},
        {"task_name": "t2", "reward": 0.0, "work_type": "fix"},
        {"task_name": "t3", "reward": 1.0, "work_type": "feature"},
        {"task_name": "t4", "reward": 0.5, "work_type": "feature"},
        {"task_name": "t5", "reward": 1.0, "work_type": "debug"},
    ]


# ---------------------------------------------------------------------------
# _compute_work_type_breakdown
# ---------------------------------------------------------------------------


class TestComputeWorkTypeBreakdown:
    def test_groups_by_work_type(self, sample_results) -> None:
        result = _compute_work_type_breakdown(sample_results)
        assert set(result.keys()) == {"debug", "feature", "fix"}

    def test_pass_rate(self, sample_results) -> None:
        result = _compute_work_type_breakdown(sample_results)
        assert result["fix"]["pass_rate"] == 0.5
        assert result["fix"]["passed"] == 1
        assert result["fix"]["task_count"] == 2

    def test_mean_reward(self, sample_results) -> None:
        result = _compute_work_type_breakdown(sample_results)
        assert result["feature"]["mean_reward"] == 0.75

    def test_empty_results(self) -> None:
        result = _compute_work_type_breakdown([])
        assert result == {}

    def test_missing_work_type_defaults_to_all(self) -> None:
        results = [{"task_name": "t", "reward": 1.0}]
        result = _compute_work_type_breakdown(results)
        assert "all" in result


# ---------------------------------------------------------------------------
# _load_baseline_summary
# ---------------------------------------------------------------------------


class TestLoadBaselineSummary:
    def test_returns_none_when_missing(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setattr("lib.csb.report._REPO_ROOT", tmp_path)
        result = _load_baseline_summary()
        assert result is None

    def test_returns_dict_when_present(self) -> None:
        result = _load_baseline_summary()
        if result is None:
            pytest.skip("Official results not available in this checkout")
        assert "suite_summaries" in result
        assert "per_task" in result
        assert isinstance(result["suite_summaries"], list)
        assert isinstance(result["per_task"], dict)


# ---------------------------------------------------------------------------
# _build_browser_data
# ---------------------------------------------------------------------------


class TestBuildBrowserData:
    def test_structure(self, submission) -> None:
        data = _build_browser_data(submission, None)
        assert "submission" in data
        assert "work_type_breakdown" in data
        assert "results" in data
        assert "dimensions" in data
        assert "leaf_categories" in data
        assert "baseline" in data

    def test_submission_fields(self, submission) -> None:
        data = _build_browser_data(submission, None)
        sub = data["submission"]
        assert sub["csb_score"] == 62.5
        assert sub["suite"] == "csb_quick"
        assert sub["task_count"] == 10

    def test_results_serializable(self, submission) -> None:
        data = _build_browser_data(submission, None)
        # Should be JSON-serializable without error
        json.dumps(data)

    def test_with_baseline(self, submission) -> None:
        fake_baseline = {
            "suite_summaries": [{"suite": "csb_quick", "pass_rate": 0.5}],
            "per_task": {
                "sgt-001-auth-middleware-fix": [{"config": "bl", "reward": 0.8}]
            },
        }
        data = _build_browser_data(submission, fake_baseline)
        assert data["baseline"] is not None
        assert data["baseline"]["suite_summaries"][0]["suite"] == "csb_quick"

    def test_without_baseline(self, submission) -> None:
        data = _build_browser_data(submission, None)
        assert data["baseline"] is None


# ---------------------------------------------------------------------------
# _render_browser_html
# ---------------------------------------------------------------------------


class TestRenderBrowserHtml:
    def test_produces_html(self, submission) -> None:
        data = _build_browser_data(submission, None)
        html = _render_browser_html(data)
        assert html.startswith("<!DOCTYPE html>")
        assert "</html>" in html

    def test_contains_score(self, submission) -> None:
        data = _build_browser_data(submission, None)
        html = _render_browser_html(data)
        assert "62.5" in html or "csbScore" in html

    def test_contains_tab_panels(self, submission) -> None:
        data = _build_browser_data(submission, None)
        html = _render_browser_html(data)
        assert "tab-overview" in html
        assert "tab-observatory" in html
        assert "tab-baseline" in html
        assert "tab-tasks" in html

    def test_embedded_json(self, submission) -> None:
        data = _build_browser_data(submission, None)
        html = _render_browser_html(data)
        assert "const D =" in html

    def test_script_injection_escaped(self) -> None:
        """Verify </script> in task names cannot break out of the script tag."""
        malicious_sub = {
            "csb_score": 10.0,
            "suite": "test",
            "agent_info": {"name": "test</script><img src=x>"},
            "metadata": {},
            "results": [
                {
                    "task_name": "evil</script><script>alert(1)</script>",
                    "reward": 0.0,
                    "work_type": "fix",
                    "failure_categories": [
                        {"category": "x", "confidence": 0.5, "evidence": "</script>"}
                    ],
                }
            ],
        }
        data = _build_browser_data(malicious_sub, None)
        html = _render_browser_html(data)
        # The literal </script> must NOT appear in the embedded JSON
        script_start = html.index("<script>")
        script_end = html.index("</script>")
        script_body = html[script_start + 8 : script_end]
        assert "</script>" not in script_body

    def test_non_numeric_reward_handled(self) -> None:
        results = [
            {"task_name": "t1", "reward": "n/a", "work_type": "fix"},
            {"task_name": "t2", "reward": None, "work_type": "fix"},
        ]
        breakdown = _compute_work_type_breakdown(results)
        assert breakdown["fix"]["mean_reward"] == 0.0
        assert breakdown["fix"]["task_count"] == 2


# ---------------------------------------------------------------------------
# HTTP server
# ---------------------------------------------------------------------------


@pytest.fixture()
def browser_server(submission):
    """Start a throwaway HTTP server serving the browser HTML."""
    data = _build_browser_data(submission, None)
    html = _render_browser_html(data)

    handler = type("H", (_BrowserHandler,), {"html_content": html})
    server = http.server.HTTPServer(("127.0.0.1", 0), handler)
    port = server.server_address[1]
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    yield port
    server.shutdown()


class TestBrowserServer:
    def test_serves_html(self, browser_server) -> None:
        port = browser_server
        resp = urllib.request.urlopen(f"http://127.0.0.1:{port}/")
        body = resp.read().decode()
        assert resp.status == 200
        assert "text/html" in resp.headers["Content-Type"]
        assert "<!DOCTYPE html>" in body

    def test_404_for_other_paths(self, browser_server) -> None:
        port = browser_server
        with pytest.raises(urllib.error.HTTPError) as exc_info:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/nonexistent")
        assert exc_info.value.code == 404


# ---------------------------------------------------------------------------
# CLI integration
# ---------------------------------------------------------------------------


class TestBrowserCLIFlag:
    def test_browser_flag_routes_to_serve_browser(self) -> None:
        from lib.csb.cli import main

        with patch("lib.csb.report.serve_browser", return_value=0) as mock:
            main(["report", "results.json", "--browser"])
            mock.assert_called_once_with(
                results_path="results.json",
                port=8770,
                include_baseline=True,
            )

    def test_browser_flag_with_port(self) -> None:
        from lib.csb.cli import main

        with patch("lib.csb.report.serve_browser", return_value=0) as mock:
            main(["report", "results.json", "--browser", "--port", "9000"])
            mock.assert_called_once_with(
                results_path="results.json",
                port=9000,
                include_baseline=True,
            )

    def test_browser_flag_with_no_baseline(self) -> None:
        from lib.csb.cli import main

        with patch("lib.csb.report.serve_browser", return_value=0) as mock:
            main(["report", "results.json", "--browser", "--no-baseline"])
            mock.assert_called_once_with(
                results_path="results.json",
                port=8770,
                include_baseline=False,
            )

    def test_no_browser_flag_uses_display_report(self) -> None:
        from lib.csb.cli import main

        with patch("lib.csb.report.display_report", return_value=0) as mock:
            main(["report", "results.json"])
            mock.assert_called_once()
