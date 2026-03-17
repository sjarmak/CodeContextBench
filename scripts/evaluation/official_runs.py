#!/usr/bin/env python3
"""Shared helpers for official run curation and integrity checks."""

from __future__ import annotations

import json
from pathlib import Path

SKIP_PATTERNS = [
    "__broken_verifier",
    "validation_test",
    "archive",
    "__archived",
    # Legacy pre-fix MCP experiment runs that had misconfigured environments
    # (e.g., missing repo mounts). These should never be promoted into
    # runs/analysis or official results bundles.
    "__old_pre_fix_ccb_mcp_",
]
DEFAULT_PREFIX_MAP_PATH = Path("configs/run_dir_prefix_map.json")
TRIAGE_FILENAME = "triage.json"
TRIAGE_DECISIONS = {"include", "exclude", "pending"}
RAW_DIRNAME = "_raw"


def should_skip(dirname: str) -> bool:
    return any(pat in dirname for pat in SKIP_PATTERNS)


def load_prefix_map(project_root: Path) -> dict[str, str]:
    path = project_root / DEFAULT_PREFIX_MAP_PATH
    if not path.is_file():
        raise FileNotFoundError(f"Prefix map not found: {path}")
    data = json.loads(path.read_text())
    if not isinstance(data, dict):
        raise ValueError(f"Prefix map must be a JSON object: {path}")
    return {str(k): str(v) for k, v in data.items()}


def detect_suite(run_dir_name: str, prefix_map: dict[str, str]) -> str | None:
    for prefix, suite in prefix_map.items():
        if run_dir_name.startswith(prefix):
            return suite
    return None


def raw_runs_dir(runs_dir: Path) -> Path:
    """Return the directory that contains raw official run dirs.

    Compatibility behavior:
    - New layout: runs/official/_raw (preferred)
    - Legacy layout: runs/official
    """
    if runs_dir.name == RAW_DIRNAME and runs_dir.is_dir():
        return runs_dir
    candidate = runs_dir / RAW_DIRNAME
    if candidate.is_dir():
        return candidate
    return runs_dir


def top_level_run_dirs(runs_dir: Path) -> list[Path]:
    raw_dir = raw_runs_dir(runs_dir)
    if not raw_dir.is_dir():
        return []
    return sorted(
        [
            p
            for p in raw_dir.iterdir()
            if p.is_dir() and not should_skip(p.name)
        ],
        key=lambda p: p.name,
    )


def load_manifest(path: Path) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"MANIFEST not found: {path}")
    return json.loads(path.read_text())


def tracked_run_dirs_from_manifest(manifest: dict) -> set[str]:
    tracked: set[str] = set()
    run_history = manifest.get("run_history", {})
    if not isinstance(run_history, dict):
        return tracked
    for _key, tasks in run_history.items():
        if not isinstance(tasks, dict):
            continue
        for _task_name, stats in tasks.items():
            runs = stats.get("runs", []) if isinstance(stats, dict) else []
            if not isinstance(runs, list):
                continue
            for run in runs:
                if not isinstance(run, dict):
                    continue
                run_dir = run.get("run_dir")
                if isinstance(run_dir, str) and run_dir:
                    tracked.add(run_dir)
    return tracked


def read_triage(run_dir: Path) -> tuple[dict | None, str | None]:
    triage_path = run_dir / TRIAGE_FILENAME
    if not triage_path.is_file():
        return None, "missing"
    try:
        triage = json.loads(triage_path.read_text())
    except json.JSONDecodeError:
        return None, "invalid_json"
    if not isinstance(triage, dict):
        return None, "invalid_type"
    decision = triage.get("decision")
    if decision not in TRIAGE_DECISIONS:
        return triage, "invalid_decision"
    for field in ("reason_code", "reviewed_at", "reviewer"):
        if not triage.get(field):
            return triage, f"missing_{field}"
    return triage, None
