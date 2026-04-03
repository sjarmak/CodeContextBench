"""csb eval runner — execute benchmark tasks against an external agent command.

Pipeline:
    1. Load suite manifest (e.g. configs/csb_quick.json)
    2. Iterate tasks, invoke agent-command as subprocess per task
    3. Collect per-task results
    4. Compute aggregate CSB Score
    5. Write submission JSON
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# Mapping from suite alias to manifest path (relative to repo root)
SUITE_MANIFESTS: dict[str, str] = {
    "quick": "configs/csb_quick.json",
    "full": "configs/selected_benchmark_tasks.json",
}

CSB_VERSION = "1.0.0"


def load_suite(suite: str) -> dict[str, Any]:
    """Load and return a suite manifest dict.

    Parameters
    ----------
    suite:
        Suite alias ("quick" or "full").

    Returns
    -------
    dict
        Parsed manifest with ``metadata`` and ``tasks`` keys.

    Raises
    ------
    ValueError
        If *suite* is not a recognised alias or manifest is missing.
    """
    rel_path = SUITE_MANIFESTS.get(suite)
    if rel_path is None:
        raise ValueError(
            f"Unknown suite {suite!r}. Choose from: {', '.join(sorted(SUITE_MANIFESTS))}"
        )
    manifest_path = _REPO_ROOT / rel_path
    if not manifest_path.exists():
        raise ValueError(f"Suite manifest not found: {manifest_path}")
    with open(manifest_path) as f:
        return json.load(f)


def _invoke_agent(
    agent_command: str,
    task: dict[str, Any],
    timeout: int,
) -> dict[str, Any]:
    """Invoke the agent command for a single task.

    The agent receives task information via environment variables:
        CSB_TASK_ID, CSB_SUITE, CSB_WORK_TYPE, CSB_DIFFICULTY, CSB_TASK_CONFIG

    The agent is expected to write a JSON object to stdout with at minimum:
        {"reward": <float 0.0-1.0>}

    Returns a result dict suitable for the submission ``results`` array.
    """
    task_config = json.dumps(task)
    env = {
        **os.environ,
        "CSB_TASK_ID": task.get("task_id", ""),
        "CSB_SUITE": task.get("suite", ""),
        "CSB_WORK_TYPE": task.get("work_type", ""),
        "CSB_DIFFICULTY": task.get("difficulty", ""),
        "CSB_TASK_CONFIG": task_config,
    }

    started_at = datetime.now(timezone.utc).isoformat()
    try:
        proc = subprocess.run(
            agent_command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )
        finished_at = datetime.now(timezone.utc).isoformat()

        if proc.returncode != 0:
            return {
                "task_name": task.get("task_id", "unknown"),
                "reward": 0.0,
                "started_at": started_at,
                "finished_at": finished_at,
                "error": f"Agent exited with code {proc.returncode}: {proc.stderr[:500]}",
            }

        # Parse agent stdout as JSON
        try:
            agent_output = json.loads(proc.stdout.strip())
        except (json.JSONDecodeError, ValueError):
            return {
                "task_name": task.get("task_id", "unknown"),
                "reward": 0.0,
                "started_at": started_at,
                "finished_at": finished_at,
                "error": f"Agent stdout is not valid JSON: {proc.stdout[:500]}",
            }

        reward = float(agent_output.get("reward", 0.0))
        reward = max(0.0, min(1.0, reward))

        result: dict[str, Any] = {
            "task_name": task.get("task_id", "unknown"),
            "reward": reward,
            "started_at": started_at,
            "finished_at": finished_at,
        }
        # Forward optional fields from agent output
        if "failure_categories" in agent_output:
            result["failure_categories"] = agent_output["failure_categories"]
        if "agent_result" in agent_output:
            result["agent_result"] = agent_output["agent_result"]

        return result

    except subprocess.TimeoutExpired:
        finished_at = datetime.now(timezone.utc).isoformat()
        return {
            "task_name": task.get("task_id", "unknown"),
            "reward": 0.0,
            "started_at": started_at,
            "finished_at": finished_at,
            "error": f"Agent timed out after {timeout}s",
        }


def run_eval(
    suite: str,
    agent_command: str,
    output_path: str | Path,
    timeout: int = 300,
) -> dict[str, Any]:
    """Run the full eval pipeline and write a submission JSON.

    Parameters
    ----------
    suite:
        Suite alias ("quick" or "full").
    agent_command:
        Shell command to invoke for each task.
    output_path:
        Path to write the submission JSON.
    timeout:
        Per-task timeout in seconds.

    Returns
    -------
    dict
        The submission dict that was written.
    """
    from lib.csb.scoring import compute_csb_score

    manifest = load_suite(suite)
    tasks = manifest.get("tasks", [])

    if not tasks:
        raise ValueError(f"Suite {suite!r} has no tasks.")

    print(f"[csb eval] Suite: {suite} ({len(tasks)} tasks)", file=sys.stderr)
    print(f"[csb eval] Agent command: {agent_command}", file=sys.stderr)
    print(f"[csb eval] Timeout per task: {timeout}s", file=sys.stderr)
    print(file=sys.stderr)

    results: list[dict[str, Any]] = []
    for i, task in enumerate(tasks, 1):
        task_id = task.get("task_id", "unknown")
        print(
            f"[csb eval] [{i}/{len(tasks)}] Running {task_id}...",
            file=sys.stderr,
            flush=True,
        )
        result = _invoke_agent(agent_command, task, timeout)
        results.append(result)

        if "error" in result:
            print(f"  -> ERROR: {result['error']}", file=sys.stderr)
        else:
            print(f"  -> reward={result['reward']:.2f}", file=sys.stderr)

    # Attach work_type to results for scoring
    task_work_types = {t["task_id"]: t.get("work_type", "unknown") for t in tasks}
    scoring_results = [
        {
            "work_type": task_work_types.get(r["task_name"], "unknown"),
            "reward": r["reward"],
        }
        for r in results
    ]
    csb_score = compute_csb_score(scoring_results)

    submission: dict[str, Any] = {
        "suite": manifest.get("metadata", {}).get("title", suite),
        "agent_info": {
            "name": agent_command.split()[0] if agent_command else "unknown",
        },
        "results": results,
        "csb_score": round(csb_score, 2),
        "metadata": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "csb_version": CSB_VERSION,
            "run_id": str(uuid.uuid4()),
            "notes": f"Eval run: suite={suite}, tasks={len(tasks)}",
        },
    }

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(submission, f, indent=2)

    print(file=sys.stderr)
    print(f"[csb eval] CSB Score: {csb_score:.1f} / 100", file=sys.stderr)
    print(f"[csb eval] Results written to: {output_path}", file=sys.stderr)

    return submission
