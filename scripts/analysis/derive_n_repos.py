#!/usr/bin/env python3
"""Derive n_repos for all tasks from Dockerfile clone topology.

For tasks with a Dockerfile: count `git clone` commands (minimum 1).
For tasks without a Dockerfile: infer from instruction.md repo references,
falling back to 1 (single primary repo).

Writes n_repos back into configs/selected_benchmark_tasks.json.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TASKS_FILE = ROOT / "configs" / "selected_benchmark_tasks.json"


def count_clones_in_dockerfile(dockerfile: Path) -> int:
    text = dockerfile.read_text(errors="ignore")
    return max(1, len(re.findall(r"\bgit\s+clone\b", text)))


def infer_from_instruction(task_dir: Path) -> int | None:
    """Try to infer n_repos from instruction.md repo references."""
    inst = task_dir / "instruction.md"
    if not inst.exists():
        return None
    text = inst.read_text(errors="ignore")
    # Count distinct "# Repo:" or "## Repo:" lines
    repo_headers = re.findall(r"^#+\s*Repo\s*:", text, re.MULTILINE)
    if len(repo_headers) > 1:
        return len(repo_headers)
    # Count distinct github clone URLs
    urls = set(re.findall(r"github\.com/[\w.-]+/[\w.-]+", text))
    if len(urls) > 1:
        return len(urls)
    return None


def derive_n_repos(task: dict) -> int:
    task_dir_rel = task.get("task_dir", "")
    if not task_dir_rel:
        task_dir_rel = f"{task['benchmark']}/{task['task_id']}"

    task_dir = ROOT / "benchmarks" / task_dir_rel
    dockerfile = task_dir / "environment" / "Dockerfile"

    if dockerfile.exists():
        return count_clones_in_dockerfile(dockerfile)

    inferred = infer_from_instruction(task_dir)
    if inferred is not None:
        return inferred

    # Default: single repo
    return 1


def main():
    data = json.loads(TASKS_FILE.read_text())
    tasks = data["tasks"]

    changed = 0
    for t in tasks:
        n = derive_n_repos(t)
        if t.get("n_repos") != n:
            changed += 1
        t["n_repos"] = n

    TASKS_FILE.write_text(json.dumps(data, indent=2) + "\n")
    print(f"Updated {changed}/{len(tasks)} tasks with n_repos")

    # Summary
    from collections import Counter
    dist = Counter(t["n_repos"] for t in tasks)
    for k in sorted(dist):
        print(f"  n_repos={k}: {dist[k]} tasks")


if __name__ == "__main__":
    main()
