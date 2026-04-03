#!/usr/bin/env python3
"""Tests for scripts/evaluation/verifier_audit.py — Verifier Audit Framework."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(
    0, str(Path(__file__).resolve().parent.parent / "scripts" / "evaluation")
)

from verifier_audit import (
    DEFAULT_PASS_THRESHOLD,
    FN_FLAG_THRESHOLD,
    audit_single_task,
    build_parser,
    discover_tasks,
    run_audit,
    wilson_score_interval,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def task_tree(tmp_path: Path) -> Path:
    """Create a minimal benchmark task tree with oracle_checks and task_spec."""
    suite_dir = tmp_path / "csb" / "feature"
    suite_dir.mkdir(parents=True)

    # Task with oracle
    t1 = suite_dir / "test-task-001"
    t1.mkdir()
    (t1 / "task.toml").write_text(
        '[metadata]\nname = "test-task-001"\n\n'
        "[task]\n"
        'id = "test-task-001"\n'
        'difficulty = "medium"\n\n'
        "[verification]\n"
        'type = "test"\n'
        'command = "bash /tests/test.sh"\n'
        'reward_type = "score"\n'
    )

    tests_dir = t1 / "tests"
    tests_dir.mkdir()

    # Write a simple oracle_checks.py that scores based on file overlap
    (tests_dir / "oracle_checks.py").write_text(
        "def run_all_checks(answer, spec):\n"
        '    expected = set(spec.get("expected_files", []))\n'
        '    actual = set(answer.get("files", []))\n'
        "    if not expected:\n"
        '        return {"composite_score": 0.0}\n'
        "    overlap = expected & actual\n"
        "    score = len(overlap) / len(expected)\n"
        '    return {"composite_score": score}\n'
    )

    (tests_dir / "task_spec.json").write_text(
        json.dumps(
            {
                "expected_files": ["src/main.py", "src/utils.py", "README.md"],
                "expected_symbols": ["main", "parse_args"],
                "expected_keywords": ["import", "def"],
            }
        )
    )

    # Task without oracle (should be skipped)
    t2 = suite_dir / "no-oracle-task"
    t2.mkdir()
    (t2 / "task.toml").write_text(
        '[metadata]\nname = "no-oracle-task"\n\n'
        "[task]\n"
        'id = "no-oracle-task"\n\n'
        "[verification]\n"
        'type = "test"\n'
        'reward_type = "binary"\n'
    )

    return tmp_path


@pytest.fixture
def high_fn_tree(tmp_path: Path) -> Path:
    """Create a task tree where the oracle always rejects (high FN rate)."""
    suite_dir = tmp_path / "csb" / "debug"
    suite_dir.mkdir(parents=True)

    t1 = suite_dir / "strict-verifier-001"
    t1.mkdir()
    (t1 / "task.toml").write_text(
        "[task]\n"
        'id = "strict-verifier-001"\n\n'
        "[verification]\n"
        'type = "test"\n'
        'reward_type = "score"\n'
    )

    tests_dir = t1 / "tests"
    tests_dir.mkdir()

    # Oracle that always returns 0 (rejects everything including gold)
    (tests_dir / "oracle_checks.py").write_text(
        "def run_all_checks(answer, spec):\n" '    return {"composite_score": 0.0}\n'
    )
    (tests_dir / "task_spec.json").write_text(json.dumps({"expected_files": ["a.py"]}))

    return tmp_path


# ---------------------------------------------------------------------------
# Wilson Score Interval Tests
# ---------------------------------------------------------------------------


class TestWilsonScoreInterval:
    """Tests for the Wilson score confidence interval computation."""

    def test_zero_total_returns_full_range(self) -> None:
        lower, upper = wilson_score_interval(0, 0)
        assert lower == 0.0
        assert upper == 1.0

    def test_all_successes(self) -> None:
        lower, upper = wilson_score_interval(10, 10)
        assert lower > 0.5
        assert upper <= 1.0

    def test_no_successes(self) -> None:
        lower, upper = wilson_score_interval(0, 10)
        assert lower >= 0.0
        assert upper < 0.5

    def test_half_successes(self) -> None:
        lower, upper = wilson_score_interval(50, 100)
        assert 0.35 < lower < 0.50
        assert 0.50 < upper < 0.65

    def test_bounds_are_ordered(self) -> None:
        for s in range(11):
            lower, upper = wilson_score_interval(s, 10)
            assert lower <= upper, f"Failed for {s}/10"

    def test_bounds_within_zero_one(self) -> None:
        for s in range(21):
            lower, upper = wilson_score_interval(s, 20)
            assert 0.0 <= lower <= 1.0
            assert 0.0 <= upper <= 1.0

    def test_single_observation_success(self) -> None:
        lower, upper = wilson_score_interval(1, 1)
        assert lower > 0.0
        assert upper == 1.0 or upper > 0.9

    def test_single_observation_failure(self) -> None:
        lower, upper = wilson_score_interval(0, 1)
        assert lower == 0.0 or lower < 0.1
        assert upper < 1.0


# ---------------------------------------------------------------------------
# Flag Threshold Tests
# ---------------------------------------------------------------------------


class TestFlagThreshold:
    """Tests for the >10% false negative flagging logic."""

    def test_flag_threshold_constant(self) -> None:
        assert FN_FLAG_THRESHOLD == 0.10

    def test_high_fn_rate_flagged(self, high_fn_tree: Path) -> None:
        result = run_audit(high_fn_tree, dry_run=False)
        assert len(result["flagged_verifiers"]) > 0
        assert "strict-verifier-001" in result["flagged_verifiers"]

    def test_good_verifier_not_flagged(self, task_tree: Path) -> None:
        result = run_audit(task_tree, dry_run=False)
        assert "test-task-001" not in result.get("flagged_verifiers", [])

    def test_exact_threshold_not_flagged(self) -> None:
        """A verifier at exactly 10% FN should NOT be flagged (> not >=)."""
        # Simulate: the threshold check is strictly greater than
        rate = 0.10
        assert not (rate > FN_FLAG_THRESHOLD)

    def test_above_threshold_flagged(self) -> None:
        rate = 0.11
        assert rate > FN_FLAG_THRESHOLD


# ---------------------------------------------------------------------------
# JSON Output Format Tests
# ---------------------------------------------------------------------------


class TestJsonOutputFormat:
    """Tests that the output matches the expected schema structure."""

    def test_output_has_required_top_level_fields(self, task_tree: Path) -> None:
        result = run_audit(task_tree, dry_run=False)
        assert "schema_version" in result
        assert "generated_at" in result
        assert "total_audited" in result
        assert "flagged_verifiers" in result
        assert "results" in result

    def test_schema_version_is_1_0(self, task_tree: Path) -> None:
        result = run_audit(task_tree, dry_run=False)
        assert result["schema_version"] == "1.0"

    def test_result_entry_has_required_fields(self, task_tree: Path) -> None:
        result = run_audit(task_tree, dry_run=False)
        assert result["total_audited"] >= 1

        entry = result["results"][0]
        required_fields = [
            "task_id",
            "false_positive_rate",
            "false_negative_rate",
            "confidence_interval_95",
            "n_good_tested",
            "n_bad_tested",
            "pass_threshold",
        ]
        for field in required_fields:
            assert field in entry, f"Missing field: {field}"

    def test_confidence_interval_structure(self, task_tree: Path) -> None:
        result = run_audit(task_tree, dry_run=False)
        entry = result["results"][0]
        ci = entry["confidence_interval_95"]
        assert "fp_lower" in ci
        assert "fp_upper" in ci
        assert "fn_lower" in ci
        assert "fn_upper" in ci

    def test_output_written_to_file(self, task_tree: Path, tmp_path: Path) -> None:
        output_path = tmp_path / "output" / "audit.json"
        run_audit(task_tree, output_path=output_path, dry_run=False)
        assert output_path.exists()
        data = json.loads(output_path.read_text())
        assert "results" in data

    def test_flagged_verifiers_is_list(self, task_tree: Path) -> None:
        result = run_audit(task_tree, dry_run=False)
        assert isinstance(result["flagged_verifiers"], list)

    def test_rates_are_bounded(self, task_tree: Path) -> None:
        result = run_audit(task_tree, dry_run=False)
        for entry in result["results"]:
            assert 0.0 <= entry["false_positive_rate"] <= 1.0
            assert 0.0 <= entry["false_negative_rate"] <= 1.0


# ---------------------------------------------------------------------------
# Task Discovery Tests
# ---------------------------------------------------------------------------


class TestTaskDiscovery:
    """Tests for task discovery logic."""

    def test_discovers_tasks(self, task_tree: Path) -> None:
        tasks = discover_tasks(task_tree)
        task_ids = [t["task_id"] for t in tasks]
        assert "test-task-001" in task_ids
        assert "no-oracle-task" in task_ids

    def test_skips_backups(self, tmp_path: Path) -> None:
        backup_dir = tmp_path / "backups" / "suite" / "task-old"
        backup_dir.mkdir(parents=True)
        (backup_dir / "task.toml").write_text('[task]\nid = "task-old"\n')
        tasks = discover_tasks(tmp_path)
        task_ids = [t["task_id"] for t in tasks]
        assert "task-old" not in task_ids


# ---------------------------------------------------------------------------
# Dry Run Tests
# ---------------------------------------------------------------------------


class TestDryRun:
    """Tests for --dry-run mode."""

    def test_dry_run_returns_counts(self, task_tree: Path) -> None:
        result = run_audit(task_tree, dry_run=True)
        assert result["dry_run"] is True
        assert "total_discovered" in result
        assert "auditable" in result
        assert "skipped" in result
        assert "auditable_tasks" in result
        assert "skipped_tasks" in result

    def test_dry_run_classifies_tasks(self, task_tree: Path) -> None:
        result = run_audit(task_tree, dry_run=True)
        assert "test-task-001" in result["auditable_tasks"]
        assert "no-oracle-task" in result["skipped_tasks"]


# ---------------------------------------------------------------------------
# CLI Tests
# ---------------------------------------------------------------------------


class TestCLI:
    """Tests for CLI argument parsing and --help."""

    def test_help_exits_zero(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(PROJECT_ROOT / "scripts" / "evaluation" / "verifier_audit.py"),
                "--help",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "Verifier Audit Framework" in result.stdout

    def test_parser_defaults(self) -> None:
        parser = build_parser()
        args = parser.parse_args([])
        assert args.tasks_dir == PROJECT_ROOT / "benchmarks"
        assert args.output == PROJECT_ROOT / "configs" / "verifier_audit_results.json"
        assert args.dry_run is False

    def test_parser_custom_args(self, tmp_path: Path) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "--tasks-dir",
                str(tmp_path),
                "--output",
                str(tmp_path / "out.json"),
                "--dry-run",
                "--pass-threshold",
                "0.5",
            ]
        )
        assert args.tasks_dir == tmp_path
        assert args.output == tmp_path / "out.json"
        assert args.dry_run is True
        assert args.pass_threshold == 0.5


# ---------------------------------------------------------------------------
# Audit Single Task Tests
# ---------------------------------------------------------------------------


class TestAuditSingleTask:
    """Tests for individual task auditing."""

    def test_returns_none_for_missing_oracle(self, task_tree: Path) -> None:
        tasks = discover_tasks(task_tree)
        no_oracle = next(t for t in tasks if t["task_id"] == "no-oracle-task")
        result = audit_single_task(no_oracle)
        assert result is None

    def test_returns_result_for_valid_task(self, task_tree: Path) -> None:
        tasks = discover_tasks(task_tree)
        valid = next(t for t in tasks if t["task_id"] == "test-task-001")
        result = audit_single_task(valid)
        assert result is not None
        assert result["task_id"] == "test-task-001"
        assert result["n_good_tested"] >= 1
        assert result["n_bad_tested"] >= 1
