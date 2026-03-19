"""Harness-enforced validation_result.json writer.

Every task execution MUST produce a validation_result.json even on failure
(PIPELINE_SPEC §1.3, Invariant I-2).  This module provides helpers for
harnesses and post-processors to write compliant records.

Usage — write a synthetic failure record (e.g. on crash or timeout)::

    from lib.csb.validation_writer import write_failure_result
    write_failure_result(
        task_dir=Path("/runs/staging/.../my-task__AbC"),
        status="verifier_error",
        reason="timeout",
        message="Task exceeded 3600s timeout",
    )

Usage — write a scored result::

    from lib.csb.validation_writer import write_scored_result
    write_scored_result(
        task_dir=Path("/runs/staging/.../my-task__AbC"),
        reward=0.75,
        passed=True,
        scorer_family="oracle_checks",
    )
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "validation_result.v1alpha1"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _atomic_write(path: Path, data: dict) -> None:
    """Write JSON to path atomically (write to tmp, then rename)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(".json.tmp")
    try:
        tmp_path.write_text(json.dumps(data, indent=2))
        tmp_path.rename(path)
    except Exception:
        tmp_path.unlink(missing_ok=True)
        raise


def _verifier_dir(task_dir: Path) -> Path:
    return task_dir / "verifier"


def validation_result_path(task_dir: Path) -> Path:
    """Return the canonical path for validation_result.json inside a task dir."""
    return _verifier_dir(task_dir) / "validation_result.json"


def already_scored(task_dir: Path) -> bool:
    """Return True iff the task already has a scored validation result."""
    vr = validation_result_path(task_dir)
    if not vr.exists():
        return False
    try:
        data = json.loads(vr.read_text())
        return data.get("status") == "scored"
    except (json.JSONDecodeError, OSError):
        return False


def write_scored_result(
    task_dir: Path,
    reward: float,
    passed: bool,
    scorer_family: str = "oracle_checks",
    pass_threshold: float = 0.0,
    output_mode: str = "repo_state",
    primary_path: str | None = None,
    required_artifact: bool = False,
    sub_scores: dict[str, Any] | None = None,
) -> Path:
    """Write a scored validation result for a task.

    Returns the path to the written file.
    """
    record = {
        "schema_version": SCHEMA_VERSION,
        "status": "scored",
        "scorable": True,
        "scorer_family": scorer_family,
        "reward": float(reward),
        "pass_threshold": float(pass_threshold),
        "passed": bool(passed),
        "output_contract": {
            "mode": output_mode,
            "primary_path": primary_path,
            "required_artifact": required_artifact,
        },
        "sub_scores": sub_scores or {},
        "failure": None,
        "written_at": _now_iso(),
    }
    path = validation_result_path(task_dir)
    _atomic_write(path, record)
    return path


def write_failure_result(
    task_dir: Path,
    status: str,
    reason: str,
    message: str,
    output_mode: str = "repo_state",
    primary_path: str | None = None,
    required_artifact: bool = False,
) -> Path:
    """Write a non-scored validation result for a task.

    Args:
        task_dir: Task result directory.
        status: One of "invalid_output" | "verifier_error".
        reason: Short reason code (e.g. "timeout", "quarantined", "crash").
        message: Human-readable error message.

    Returns:
        Path to the written file.
    """
    if status not in ("invalid_output", "verifier_error"):
        raise ValueError(f"status must be 'invalid_output' or 'verifier_error', got: {status!r}")

    record = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "scorable": False,
        "scorer_family": "none",
        "reward": 0.0,
        "pass_threshold": 0.0,
        "passed": False,
        "output_contract": {
            "mode": output_mode,
            "primary_path": primary_path,
            "required_artifact": required_artifact,
        },
        "sub_scores": {},
        "failure": {
            "reason": reason,
            "message": message,
        },
        "written_at": _now_iso(),
    }
    path = validation_result_path(task_dir)
    _atomic_write(path, record)
    return path


def write_quarantine_result(task_dir: Path, attempts: int, last_error: str) -> Path:
    """Write a quarantine record (circuit breaker fired at MAX_ATTEMPTS).

    This fulfils PIPELINE_SPEC §2.4 and Invariant I-7.
    """
    return write_failure_result(
        task_dir=task_dir,
        status="verifier_error",
        reason="quarantined",
        message=(
            f"Circuit breaker fired after {attempts} attempt(s). "
            f"Last error: {last_error}"
        ),
    )
