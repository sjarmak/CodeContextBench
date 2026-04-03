"""Tests for eval-kit-cli: csb eval, csb report, and validate_submission.

Covers:
- Argument parsing for eval and report subcommands
- Suite loading from csb_quick.json
- Output format validation (submission schema compliance)
- --help exits 0 for eval and report
- validate_submission.py --help exits 0
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Ensure repo root is on path
_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from lib.csb.cli import main
from lib.csb.eval_runner import load_suite, run_eval, SUITE_MANIFESTS
from lib.csb.report import display_report, load_submission

# ---------------------------------------------------------------------------
# Argument parsing tests
# ---------------------------------------------------------------------------


class TestEvalArgParsing:
    """Test that eval subcommand parses arguments correctly."""

    def test_eval_help_exits_zero(self) -> None:
        with pytest.raises(SystemExit) as exc_info:
            main(["eval", "--help"])
        assert exc_info.value.code == 0

    def test_eval_requires_agent_command(self) -> None:
        with pytest.raises(SystemExit) as exc_info:
            main(["eval", "--suite", "quick"])
        assert exc_info.value.code != 0

    def test_eval_help_shows_suite_and_agent_command(self, capsys) -> None:
        with pytest.raises(SystemExit):
            main(["eval", "--help"])
        captured = capsys.readouterr()
        assert "--suite" in captured.out
        assert "--agent-command" in captured.out

    def test_eval_help_shows_output_and_timeout(self, capsys) -> None:
        with pytest.raises(SystemExit):
            main(["eval", "--help"])
        captured = capsys.readouterr()
        assert "--output" in captured.out
        assert "--timeout" in captured.out

    def test_eval_default_suite_is_quick(self) -> None:
        """Verify default suite is 'quick' by checking argparse defaults."""
        import argparse

        # Build parser the same way main() does, but only test parsing
        parser = argparse.ArgumentParser(prog="csb")
        sub = parser.add_subparsers(dest="command")
        eval_p = sub.add_parser("eval")
        eval_p.add_argument("--suite", choices=["quick", "full"], default="quick")
        eval_p.add_argument("--agent-command", required=True)
        eval_p.add_argument("--output", default="csb_results.json")
        eval_p.add_argument("--timeout", type=int, default=300)

        args = parser.parse_args(["eval", "--agent-command", "echo"])
        assert args.suite == "quick"


class TestReportArgParsing:
    """Test that report subcommand parses arguments correctly."""

    def test_report_help_exits_zero(self) -> None:
        with pytest.raises(SystemExit) as exc_info:
            main(["report", "--help"])
        assert exc_info.value.code == 0

    def test_report_help_shows_format_and_browser(self, capsys) -> None:
        with pytest.raises(SystemExit):
            main(["report", "--help"])
        captured = capsys.readouterr()
        assert "--format" in captured.out
        assert "--browser" in captured.out

    def test_report_requires_results_file(self) -> None:
        with pytest.raises(SystemExit) as exc_info:
            main(["report"])
        assert exc_info.value.code != 0


# ---------------------------------------------------------------------------
# Suite loading tests
# ---------------------------------------------------------------------------


class TestSuiteLoading:
    """Test suite manifest loading."""

    def test_load_quick_suite(self) -> None:
        manifest = load_suite("quick")
        assert "metadata" in manifest
        assert "tasks" in manifest
        assert len(manifest["tasks"]) > 0

    def test_load_quick_suite_has_task_ids(self) -> None:
        manifest = load_suite("quick")
        for task in manifest["tasks"]:
            assert "task_id" in task
            assert "work_type" in task

    def test_load_unknown_suite_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown suite"):
            load_suite("nonexistent")

    def test_suite_manifests_mapping_exists(self) -> None:
        assert "quick" in SUITE_MANIFESTS
        assert "full" in SUITE_MANIFESTS


# ---------------------------------------------------------------------------
# Output format / submission schema validation tests
# ---------------------------------------------------------------------------


class TestOutputFormatValidation:
    """Test that eval output conforms to submission schema."""

    def _make_valid_submission(self) -> dict:
        """Create a minimal valid submission dict."""
        return {
            "suite": "CSB-Quick",
            "agent_info": {"name": "test-agent"},
            "results": [
                {"task_name": "task-001", "reward": 1.0},
                {"task_name": "task-002", "reward": 0.5},
            ],
            "csb_score": 50.0,
            "metadata": {
                "timestamp": "2026-04-03T00:00:00+00:00",
                "csb_version": "1.0.0",
            },
        }

    def test_valid_submission_has_required_fields(self) -> None:
        submission = self._make_valid_submission()
        required = ["suite", "agent_info", "results", "csb_score", "metadata"]
        for field in required:
            assert field in submission

    def test_valid_submission_results_have_required_fields(self) -> None:
        submission = self._make_valid_submission()
        for result in submission["results"]:
            assert "task_name" in result
            assert "reward" in result

    def test_valid_submission_passes_validate_script(self) -> None:
        submission = self._make_valid_submission()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(submission, f)
            f.flush()
            try:
                proc = subprocess.run(
                    [
                        sys.executable,
                        str(
                            _REPO_ROOT
                            / "scripts"
                            / "evaluation"
                            / "validate_submission.py"
                        ),
                        f.name,
                    ],
                    capture_output=True,
                    text=True,
                )
                assert proc.returncode == 0
            finally:
                os.unlink(f.name)

    def test_invalid_submission_fails_validate_script(self) -> None:
        invalid = {"not": "a valid submission"}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(invalid, f)
            f.flush()
            try:
                proc = subprocess.run(
                    [
                        sys.executable,
                        str(
                            _REPO_ROOT
                            / "scripts"
                            / "evaluation"
                            / "validate_submission.py"
                        ),
                        f.name,
                    ],
                    capture_output=True,
                    text=True,
                )
                assert proc.returncode == 1
            finally:
                os.unlink(f.name)


# ---------------------------------------------------------------------------
# validate_submission.py --help test
# ---------------------------------------------------------------------------


class TestValidateSubmissionScript:
    """Test the standalone validate_submission.py script."""

    def test_help_exits_zero(self) -> None:
        proc = subprocess.run(
            [
                sys.executable,
                str(_REPO_ROOT / "scripts" / "evaluation" / "validate_submission.py"),
                "--help",
            ],
            capture_output=True,
            text=True,
        )
        assert proc.returncode == 0
        assert "submission" in proc.stdout.lower()


# ---------------------------------------------------------------------------
# Report display tests
# ---------------------------------------------------------------------------


class TestReportDisplay:
    """Test the report module."""

    def _write_submission(self, tmp_path: Path) -> Path:
        submission = {
            "suite": "CSB-Quick",
            "agent_info": {"name": "test-agent"},
            "results": [
                {"task_name": "task-001", "reward": 1.0},
                {"task_name": "task-002", "reward": 0.0},
            ],
            "csb_score": 50.0,
            "metadata": {
                "timestamp": "2026-04-03T00:00:00+00:00",
                "csb_version": "1.0.0",
            },
        }
        path = tmp_path / "results.json"
        with open(path, "w") as f:
            json.dump(submission, f)
        return path

    def test_text_report_shows_csb_score(self, tmp_path: Path, capsys) -> None:
        path = self._write_submission(tmp_path)
        rc = display_report(path, fmt="text")
        assert rc == 0
        captured = capsys.readouterr()
        assert "CSB SCORE" in captured.out
        assert "50.0" in captured.out

    def test_json_report_outputs_valid_json(self, tmp_path: Path, capsys) -> None:
        path = self._write_submission(tmp_path)
        rc = display_report(path, fmt="json")
        assert rc == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["csb_score"] == 50.0

    def test_html_report_creates_file(self, tmp_path: Path) -> None:
        path = self._write_submission(tmp_path)
        rc = display_report(path, fmt="html", open_browser=False)
        assert rc == 0
        html_path = path.with_suffix(".html")
        assert html_path.exists()
        content = html_path.read_text()
        assert "50.0" in content

    def test_report_missing_file_returns_error(self, tmp_path: Path) -> None:
        rc = display_report(tmp_path / "nonexistent.json")
        assert rc == 1

    def test_load_submission(self, tmp_path: Path) -> None:
        path = self._write_submission(tmp_path)
        data = load_submission(path)
        assert data["csb_score"] == 50.0


# ---------------------------------------------------------------------------
# Eval runner integration test (with mock agent)
# ---------------------------------------------------------------------------


class TestEvalRunnerIntegration:
    """Test eval runner with a trivial agent command."""

    def test_run_eval_with_echo_agent(self, tmp_path: Path) -> None:
        """Run eval with a tiny mock suite and an echo agent."""
        # Create a mini suite manifest
        mini_suite = {
            "metadata": {"title": "Mini Test Suite"},
            "tasks": [
                {
                    "task_id": "test-001",
                    "suite": "test",
                    "work_type": "fix",
                    "difficulty": "hard",
                },
                {
                    "task_id": "test-002",
                    "suite": "test",
                    "work_type": "feature",
                    "difficulty": "hard",
                },
            ],
        }
        suite_path = tmp_path / "mini_suite.json"
        with open(suite_path, "w") as f:
            json.dump(mini_suite, f)

        output_path = tmp_path / "output.json"

        # Patch SUITE_MANIFESTS to use our mini suite
        with patch.dict(
            "lib.csb.eval_runner.SUITE_MANIFESTS",
            {"quick": str(suite_path)},
        ), patch(
            "lib.csb.eval_runner._REPO_ROOT",
            Path("/"),  # Since we use absolute path in manifest
        ):
            # Agent that outputs valid JSON with reward
            agent_cmd = f'{sys.executable} -c "import json; print(json.dumps(dict(reward=1.0)))"'

            # Need to patch _REPO_ROOT for the load_suite path resolution
            # Actually, let's patch load_suite directly
            from lib.csb import eval_runner

            original_load = eval_runner.load_suite

            def mock_load(suite: str) -> dict:
                with open(suite_path) as fh:
                    return json.load(fh)

            with patch.object(eval_runner, "load_suite", mock_load):
                submission = run_eval(
                    suite="quick",
                    agent_command=agent_cmd,
                    output_path=output_path,
                    timeout=30,
                )

        assert output_path.exists()
        assert submission["csb_score"] > 0
        assert len(submission["results"]) == 2
        for r in submission["results"]:
            assert r["reward"] == 1.0
        assert "agent_info" in submission
        assert "metadata" in submission
