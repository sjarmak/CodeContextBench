"""Load and apply task selection metadata from selected_benchmark_tasks.json.

Provides utilities to:
1. Load the canonical task selection file
2. Build a lookup index by task_id
3. Enrich TaskMetrics with selection metadata (SDLC phase, MCP score, etc.)
4. Filter discovered runs to only canonical selected tasks

Stdlib only — no external dependencies. Python 3.10+.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from .models import TaskMetrics, RunMetrics


def load_selected_tasks(path: str | Path) -> dict:
    """Load selected_benchmark_tasks.json and return the full document.

    Args:
        path: Path to selected_benchmark_tasks.json.

    Returns:
        The parsed JSON document with metadata, methodology, statistics, tasks.

    Raises:
        FileNotFoundError: If the file doesn't exist.
        json.JSONDecodeError: If the file isn't valid JSON.
    """
    return json.loads(Path(path).read_text())


def build_task_index(selection: dict) -> dict[str, dict]:
    """Build a task_id → task metadata lookup from the selection document.

    Args:
        selection: The parsed selected_benchmark_tasks.json document.

    Returns:
        Dict mapping task_id to its full metadata dict.
    """
    return {t["task_id"]: t for t in selection.get("tasks", [])}


def enrich_task_metrics(
    tm: TaskMetrics,
    task_index: dict[str, dict],
) -> None:
    """Enrich a TaskMetrics with selection metadata if the task is in the index.

    Mutates tm in place, setting sdlc_phase, language, category, difficulty,
    mcp_benefit_score, mcp_benefit_breakdown, and repo from the selection data.

    Args:
        tm: The TaskMetrics to enrich.
        task_index: The task_id → metadata lookup from build_task_index().
    """
    meta = task_index.get(tm.task_id)
    if meta is None:
        return
    tm.sdlc_phase = meta.get("sdlc_phase")
    tm.language = meta.get("language")
    tm.category = meta.get("category")
    tm.difficulty = meta.get("difficulty")
    tm.mcp_benefit_score = meta.get("mcp_benefit_score")
    tm.mcp_benefit_breakdown = meta.get("mcp_breakdown")
    tm.repo = meta.get("repo")


def enrich_runs(
    runs: list[RunMetrics],
    task_index: dict[str, dict],
) -> None:
    """Enrich all TaskMetrics within a list of RunMetrics.

    Args:
        runs: List of RunMetrics to enrich.
        task_index: The task_id → metadata lookup from build_task_index().
    """
    for run in runs:
        for tm in run.tasks:
            enrich_task_metrics(tm, task_index)


def filter_runs_to_selected(
    runs: list[RunMetrics],
    task_index: dict[str, dict],
) -> list[RunMetrics]:
    """Filter runs to only include tasks present in the canonical selection.

    Returns new RunMetrics objects with only matching tasks. Runs that have
    no matching tasks are omitted entirely.

    Args:
        runs: List of RunMetrics to filter.
        task_index: The task_id → metadata lookup from build_task_index().

    Returns:
        Filtered list of RunMetrics.
    """
    filtered: list[RunMetrics] = []
    for run in runs:
        matching = [t for t in run.tasks if t.task_id in task_index]
        if not matching:
            continue
        filtered_run = RunMetrics(
            run_id=run.run_id,
            benchmark=run.benchmark,
            config_name=run.config_name,
            model=run.model,
            timestamp=run.timestamp,
            task_count=len(matching),
            tasks=matching,
            harness_config=run.harness_config,
        )
        filtered.append(filtered_run)
    return filtered


def get_benchmark_name_mapping() -> dict[str, str]:
    """Return mapping from discovery benchmark names to selection benchmark names.

    The discovery module infers short benchmark names (e.g. 'locobench',
    'swebenchpro', 'bigcode') while selected_benchmark_tasks.json uses the
    full benchmark directory names. This mapping bridges the two.
    """
    return {
        "locobench": "ccb_locobench",
        "swebenchpro": "ccb_swebenchpro",
        "bigcode": "ccb_largerepo",
        "k8s_docs": "ccb_k8sdocs",
        "ccb_pytorch": "ccb_pytorch",
        "ccb_tac": "ccb_tac",
        "ccb_sweperf": "ccb_sweperf",
    }


def normalize_benchmark_name(discovery_name: str) -> str:
    """Convert a discovery benchmark name to the canonical selection name."""
    mapping = get_benchmark_name_mapping()
    return mapping.get(discovery_name, discovery_name)
