"""CSB Gap Scanner — implements PIPELINE_SPEC §6.

Scans CSB_RUNS_DIR and compares against a task selection JSON to produce a
gap report: the set of (task_id, config) pairs that are not yet scored.

A result counts as "complete" only when:

    task_dir/verifier/validation_result.json  exists  AND  status == "scored"

The scanner handles all three result directory layouts documented in
docs/reference/RESULT_DIRECTORY_SPEC.md.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator


# ---------------------------------------------------------------------------
# Constants — config name canonicalization
# ---------------------------------------------------------------------------

# All config directory names that map to the "baseline" family
_BL_NAMES: frozenset[str] = frozenset(
    {"baseline", "baseline-local-direct", "baseline-local-artifact"}
)
# All config directory names that map to the "mcp" family
_MCP_NAMES: frozenset[str] = frozenset(
    {"mcp", "mcp-remote-direct", "mcp-remote-artifact"}
)

_KNOWN_CONFIGS: frozenset[str] = _BL_NAMES | _MCP_NAMES


def canonical_config(name: str) -> str | None:
    """Return the canonical config name or None if unknown."""
    if name in _BL_NAMES:
        return "baseline-local-direct"
    if name in _MCP_NAMES:
        return "mcp-remote-direct"
    return None


# ---------------------------------------------------------------------------
# Completion check  (PIPELINE_SPEC §6.2)
# ---------------------------------------------------------------------------

def is_complete(task_dir: Path) -> bool:
    """Return True iff validation_result.json exists and has status=scored."""
    vr = task_dir / "verifier" / "validation_result.json"
    if not vr.exists():
        return False
    try:
        data = json.loads(vr.read_text())
        return data.get("status") == "scored"
    except (json.JSONDecodeError, OSError):
        return False


def completion_status(task_dir: Path) -> str:
    """Return the status string from validation_result.json, or 'missing'."""
    vr = task_dir / "verifier" / "validation_result.json"
    if not vr.exists():
        return "missing"
    try:
        data = json.loads(vr.read_text())
        return data.get("status", "missing")
    except (json.JSONDecodeError, OSError):
        return "missing"


# ---------------------------------------------------------------------------
# Layout detection helpers
# ---------------------------------------------------------------------------

def _iter_config_task_dirs(runs_dir: Path) -> Iterator[tuple[str, str, Path]]:
    """Walk CSB_RUNS_DIR and yield (config_name, task_id, task_dir) tuples.

    Handles three result directory layouts (RESULT_DIRECTORY_SPEC.md):

    Layout 1 — old promoted (4-level):
        <runs_dir>/<category>/<run_id>/<config>/<batch_ts>/<task_id__hash>/

    Layout 2 — Harbor nested (standard):
        <runs_dir>/<category>/<agent>_<model>_<ts>/<config>/<batch_ts>/<task_id__hash>/

    Layout 3 — flat (for backwards compat):
        <runs_dir>/<config>/<task_id__hash>/
    """
    if not runs_dir.is_dir():
        return

    for child in runs_dir.iterdir():
        if not child.is_dir():
            continue
        name = child.name

        # Is this a config-level directory at the top level? (Layout 3)
        canon = canonical_config(name)
        if canon:
            yield from _scan_config_dir(canon, child)
            continue

        # Skip hidden / archive directories
        if name.startswith(".") or name == "archive":
            continue

        # Assume it's a category or run-level directory; descend
        for run_dir in child.iterdir():
            if not run_dir.is_dir():
                continue
            run_name = run_dir.name
            if run_name.startswith(".") or run_name == "archive":
                continue

            # Check if run_dir itself has config sub-dirs
            has_config_child = any(
                canonical_config(d.name) for d in run_dir.iterdir() if d.is_dir()
            )
            if has_config_child:
                for config_dir in run_dir.iterdir():
                    if not config_dir.is_dir():
                        continue
                    cname = canonical_config(config_dir.name)
                    if cname:
                        yield from _scan_config_dir(cname, config_dir)
            else:
                # Might itself be a config dir (shallow layout)
                cname = canonical_config(run_name)
                if cname:
                    yield from _scan_config_dir(cname, run_dir)


def _scan_config_dir(config: str, config_dir: Path) -> Iterator[tuple[str, str, Path]]:
    """Yield (config, task_id, task_dir) for every task dir under config_dir."""
    for entry in config_dir.iterdir():
        if not entry.is_dir():
            continue
        entry_name = entry.name
        if entry_name.startswith("."):
            continue

        # Does this directory itself contain verifier/?  → it's a task dir.
        if (entry / "verifier").is_dir() or (entry / "result.json").is_file():
            task_id = _extract_task_id(entry_name)
            yield config, task_id, entry
        else:
            # It's a batch_ts dir — descend one more level
            for task_dir in entry.iterdir():
                if not task_dir.is_dir():
                    continue
                task_id = _extract_task_id(task_dir.name)
                yield config, task_id, task_dir


def _extract_task_id(dir_name: str) -> str:
    """Strip the trailing __<hash> suffix from a task directory name."""
    if "__" in dir_name:
        # task_id__AbCdEfG → task_id
        return dir_name.rsplit("__", 1)[0]
    return dir_name


# ---------------------------------------------------------------------------
# Scored-task inventory
# ---------------------------------------------------------------------------

def build_scored_inventory(runs_dir: Path) -> dict[str, dict[str, str]]:
    """Return {task_id: {config: status}} for all task dirs found under runs_dir."""
    inventory: dict[str, dict[str, str]] = {}
    for config, task_id, task_dir in _iter_config_task_dirs(runs_dir):
        status = completion_status(task_dir)
        existing = inventory.setdefault(task_id, {})
        # If there are multiple trial dirs for the same task+config, prefer "scored"
        prev = existing.get(config, "missing")
        if prev != "scored":
            existing[config] = status
    return inventory


# ---------------------------------------------------------------------------
# Gap report
# ---------------------------------------------------------------------------

def compute_gap_report(
    runs_dir: Path,
    selection_file: Path,
    configs: list[str] | None = None,
) -> dict:
    """Compute the gap report for a given selection file and runs directory.

    Args:
        runs_dir: Absolute path to CSB_RUNS_DIR.
        selection_file: Path to selected_benchmark_tasks.json.
        configs: Config names to check. Defaults to both canonical configs.

    Returns:
        Gap report dict matching PIPELINE_SPEC §3 schema.
    """
    if configs is None:
        configs = ["baseline-local-direct", "mcp-remote-direct"]

    # Load selected tasks
    with open(selection_file) as f:
        sel_data = json.load(f)
    tasks = [t for t in sel_data.get("tasks", []) if not t.get("excluded")]

    # Build scored inventory
    inventory = build_scored_inventory(runs_dir)

    gaps = []
    scored_count = 0
    total_expected = len(tasks) * len(configs)

    for task in tasks:
        task_id = task["task_id"]
        benchmark = task.get("benchmark", "unknown")
        task_inv = inventory.get(task_id, {})

        for config in configs:
            status = task_inv.get(config, "missing")
            if status == "scored":
                scored_count += 1
            else:
                reason = status if status != "missing" else "missing"
                gaps.append(
                    {
                        "task_id": task_id,
                        "config": config,
                        "benchmark": benchmark,
                        "reason": reason,
                    }
                )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "csb_runs_dir": str(runs_dir),
        "selection_file": str(selection_file),
        "configs_checked": configs,
        "gaps": gaps,
        "summary": {
            "total_expected": total_expected,
            "scored": scored_count,
            "gap_count": len(gaps),
        },
    }


def compute_coverage_report(
    runs_dir: Path,
    selection_file: Path,
    configs: list[str] | None = None,
) -> dict:
    """Compute per-config coverage summary (PIPELINE_SPEC §5).

    Args:
        runs_dir: Absolute path to CSB_RUNS_DIR.
        selection_file: Path to selected_benchmark_tasks.json.
        configs: Config names to check.

    Returns:
        Coverage report dict with per-config breakdowns.
    """
    if configs is None:
        configs = ["baseline-local-direct", "mcp-remote-direct"]

    with open(selection_file) as f:
        sel_data = json.load(f)
    tasks = [t for t in sel_data.get("tasks", []) if not t.get("excluded")]
    task_ids = [t["task_id"] for t in tasks]

    inventory = build_scored_inventory(runs_dir)

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "csb_runs_dir": str(runs_dir),
        "selection_file": str(selection_file),
        "total_tasks": len(task_ids),
        "configs": {},
    }

    for config in configs:
        counts: dict[str, int] = {
            "scored": 0,
            "invalid_output": 0,
            "verifier_error": 0,
            "quarantined": 0,
            "missing": 0,
        }
        for task_id in task_ids:
            status = inventory.get(task_id, {}).get(config, "missing")
            key = status if status in counts else "missing"
            counts[key] += 1

        total = len(task_ids)
        scored = counts["scored"]
        coverage_pct = round(100.0 * scored / total, 1) if total else 0.0

        report["configs"][config] = {
            "total_tasks": total,
            "scored": scored,
            "invalid_output": counts["invalid_output"],
            "verifier_error": counts["verifier_error"],
            "quarantined": counts["quarantined"],
            "missing": counts["missing"],
            "coverage_pct": coverage_pct,
        }

    return report
