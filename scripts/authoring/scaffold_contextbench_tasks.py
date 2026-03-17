#!/usr/bin/env python3
"""Scaffold ContextBench tasks into Harbor-compatible benchmark directories.

Reads the pilot selection file produced by select_contextbench_pilot.py and
creates a benchmarks/ccb_contextbench/{task_id}/ directory for each task with:
  - task.toml
  - instruction.md
  - environment/Dockerfile (baseline: full source from mirror)
  - environment/Dockerfile.sg_only (MCP: empty workspace + Sourcegraph)
  - tests/test.sh, verify_diff.py, expected.patch, gold_context.json,
    sgonly_verifier_wrapper.sh

Usage:
    python3 scripts/scaffold_contextbench_tasks.py
    python3 scripts/scaffold_contextbench_tasks.py --selection configs/contextbench_pilot_50.json
    python3 scripts/scaffold_contextbench_tasks.py --dry-run
"""

from __future__ import annotations

import argparse
import json
import logging
import shutil
import sys
from pathlib import Path

from prompt_hygiene import sanitize_instruction_text

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
BENCHMARKS_DIR = REPO_ROOT / "calibration" / "curator_calibration"
SELECTION_DEFAULT = REPO_ROOT / "configs" / "contextbench_pilot_50.json"

# Reference task for copying verifier infrastructure
REFERENCE_TASK = REPO_ROOT / "benchmarks" / "csb_sdlc_fix" / "envoy-dfp-host-leak-fix-001"

log = logging.getLogger(__name__)

# Language -> base Docker image
LANG_IMAGES = {
    "python": "python:3.11-slim",
    "javascript": "node:20-slim",
    "typescript": "node:20-slim",
    "java": "eclipse-temurin:17-jdk",
    "go": "golang:1.23-bookworm",
    "rust": "rust:1.77-slim",
    "ruby": "ruby:3.3-slim",
    "c": "ubuntu:22.04",
    "c++": "ubuntu:22.04",
    "cpp": "ubuntu:22.04",
}


def _base_image(language: str) -> str:
    return LANG_IMAGES.get(language.lower(), "ubuntu:22.04")


def _task_toml(task: dict) -> str:
    """Generate task.toml content."""
    task_id = task["task_id"]
    instance_id = task["instance_id"]
    repo = task["repo"]
    language = task["language"]
    commit = task["base_commit"]

    return f'''version = "1.0"
[metadata]
name = "{task_id}"
description = "ContextBench cross-validation: {instance_id}"
license = "Apache-2.0"

[task]
id = "{task_id}"
repo = "{repo}"
category = "contextbench_cross_validation"
language = "{language}"
pre_fix_rev = "{commit}"
difficulty = "medium"
time_limit_sec = 1800

[verification]
type = "test"
command = "bash /tests/test.sh"
reward_type = "diff_similarity"
description = "Similarity between agent diff and expected ground-truth patch"

[environment]
build_timeout_sec = 1800.0
'''


def _instruction_md(task: dict) -> str:
    """Generate instruction.md wrapping ContextBench's problem_statement."""
    instance_id = task["instance_id"]
    repo = task["repo"]
    language = task["language"]
    problem_statement = task.get("_problem_statement", "")

    return f"""# Fix: {instance_id}

**Repository:** {repo}
**Language:** {language}
**Category:** contextbench_cross_validation

## Description

{problem_statement}

## Task

Diagnose and fix the issue described above. The repository has been cloned at the relevant commit. Make the necessary code changes to resolve the bug.

## Success Criteria

Your code changes should resolve the described issue. The implementation will be verified against the expected patch using diff similarity scoring.

**Time Limit:** 30 minutes
"""


def _dockerfile_baseline(task: dict) -> str:
    """Generate baseline Dockerfile (full source from mirror)."""
    language = task["language"]
    mirror = task["mirror_name"]
    base = _base_image(language)

    return f"""# {task["task_id"]} — baseline (full local source)
FROM {base}

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \\
    git ca-certificates python3 curl \\
    && rm -rf /var/lib/apt/lists/*

RUN if ! command -v node > /dev/null 2>&1; then \\
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \\
    apt-get install -y --no-install-recommends nodejs; \\
    fi

RUN (adduser --disabled-password --gecos '' claude 2>/dev/null || true) && \\
    mkdir -p /workspace && chown claude:claude /workspace

USER claude
RUN git clone --depth 1 https://github.com/sg-evals/{mirror}.git /workspace
USER root

RUN mkdir -p /logs/agent /logs/verifier
RUN chown -R claude:claude /workspace /logs

WORKDIR /workspace
ENTRYPOINT []
"""


def _dockerfile_sg_only(task: dict) -> str:
    """Generate Dockerfile.sg_only (empty workspace + Sourcegraph MCP)."""
    mirror = task["mirror_name"]

    return f"""# {task["task_id"]} — sg_only_env variant (v2: clone-at-verify)
# Empty workspace — agent uses Sourcegraph MCP for code access.
# Verifier clones mirror(s) at verification time via clone manifest.

FROM ubuntu:22.04

ENV SOURCEGRAPH_REPO_NAME=sg-evals/{mirror}

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \\
    git \\
    ca-certificates \\
    python3 \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Install Node.js (needed by verifier)
RUN if ! command -v node > /dev/null 2>&1; then \\
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \\
    apt-get install -y --no-install-recommends nodejs; \\
    fi

WORKDIR /workspace

# Empty git repo so agent can commit work
RUN git init && \\
    git config user.email "agent@example.com" && \\
    git config user.name "Agent"

RUN mkdir -p /logs/agent /logs/verifier

# Clone manifest for verifier (clone-at-verify strategy)
RUN echo '{{"workdir":"/workspace","repos":[{{"mirror":"sg-evals/{mirror}","target_dir":"."}}]}}' > /tmp/.sg_only_clone_manifest.json

# Mark sg_only mode
RUN touch /tmp/.sg_only_mode

# Pre-create claude user and set ownership at build time.
RUN (adduser --disabled-password --gecos '' claude 2>/dev/null || true) && \\
    for d in /workspace /app /testbed /logs; do [ -d "$d" ] && chown -R claude:claude "$d"; done || true

ENTRYPOINT []
"""


def _test_sh() -> str:
    """Generate test.sh using the diff_similarity verifier pattern."""
    return """#!/bin/bash
# Reward: diff_similarity (0.0-1.0) — diff match to expected patch

# sg_only_env: restore full repo before verification (no-op for regular runs)
[ -f /tmp/.sg_only_mode ] && [ -f /tests/sgonly_verifier_wrapper.sh ] && source /tests/sgonly_verifier_wrapper.sh

set -eo pipefail
mkdir -p /logs/verifier
cd "${VERIFY_REPO:-/workspace}"
git config --global --add safe.directory /workspace 2>/dev/null || true
# Resolve initial commit — mirrors use orphan commits with different SHAs than upstream
PRE_FIX_REV=$(git rev-parse HEAD 2>/dev/null || echo "HEAD")
python3 /tests/verify_diff.py \\
    --expected /tests/expected.patch \\
    --pre-fix-rev "$PRE_FIX_REV" \\
    --output /logs/verifier/reward.json \\
    2>&1 | tee /logs/verifier/verifier.log
REWARD=$(python3 -c "import json; print(json.load(open('/logs/verifier/reward.json')).get('reward', 0.0))" 2>/dev/null || echo "0.0")
echo "$REWARD" > /logs/verifier/reward.txt
echo "Final reward: $REWARD"
git diff "$PRE_FIX_REV" > /logs/verifier/agent.diff 2>/dev/null || true
git diff "$PRE_FIX_REV" --stat > /logs/verifier/diff.stat 2>/dev/null || true
exit 0
"""


def scaffold_task(task: dict, dry_run: bool = False) -> bool:
    """Scaffold a single ContextBench task into Harbor format."""
    task_id = task["task_id"]
    task_dir = BENCHMARKS_DIR / task_id

    if task_dir.exists():
        log.info("Already exists: %s", task_dir)
        return True

    if dry_run:
        log.info("Would create: %s", task_dir)
        return True

    # Create directory structure
    env_dir = task_dir / "environment"
    tests_dir = task_dir / "tests"
    env_dir.mkdir(parents=True, exist_ok=True)
    tests_dir.mkdir(parents=True, exist_ok=True)

    # Write generated files
    (task_dir / "task.toml").write_text(_task_toml(task))
    (task_dir / "instruction.md").write_text(sanitize_instruction_text(_instruction_md(task)))
    (env_dir / "Dockerfile").write_text(_dockerfile_baseline(task))
    (env_dir / "Dockerfile.sg_only").write_text(_dockerfile_sg_only(task))
    (tests_dir / "test.sh").write_text(_test_sh())

    # Write patch as expected.patch
    patch = task.get("_patch", "")
    (tests_dir / "expected.patch").write_text(patch)

    # Write gold_context for retrieval evaluation
    gold_context = task.get("_gold_context", "[]")
    (tests_dir / "gold_context.json").write_text(gold_context if isinstance(gold_context, str) else json.dumps(gold_context))

    # Copy verify_diff.py from reference task
    ref_verify = REFERENCE_TASK / "tests" / "verify_diff.py"
    if ref_verify.exists():
        shutil.copy2(ref_verify, tests_dir / "verify_diff.py")
    else:
        log.warning("Reference verify_diff.py not found: %s", ref_verify)

    # Copy sgonly_verifier_wrapper.sh from reference task
    ref_wrapper = REFERENCE_TASK / "tests" / "sgonly_verifier_wrapper.sh"
    if ref_wrapper.exists():
        shutil.copy2(ref_wrapper, tests_dir / "sgonly_verifier_wrapper.sh")
    else:
        log.warning("Reference sgonly_verifier_wrapper.sh not found: %s", ref_wrapper)

    log.info("Created: %s (%s, %s)", task_id, task["language"], task["repo"])
    return True


def scaffold_all(selection_file: Path, dry_run: bool = False) -> int:
    """Scaffold all tasks from the selection file."""
    if not selection_file.exists():
        log.error("Selection file not found: %s", selection_file)
        sys.exit(1)

    selection = json.loads(selection_file.read_text())
    tasks = selection.get("tasks", [])

    if not tasks:
        log.error("No tasks in selection file")
        sys.exit(1)

    log.info("Scaffolding %d tasks%s", len(tasks), " (dry run)" if dry_run else "")

    created = 0
    failed = 0
    for task in tasks:
        try:
            if scaffold_task(task, dry_run):
                created += 1
            else:
                failed += 1
        except Exception as e:
            log.error("Failed to scaffold %s: %s", task.get("task_id", "?"), e)
            failed += 1

    print(f"\n=== Scaffolding Complete ===")
    print(f"Created: {created}")
    print(f"Failed:  {failed}")
    print(f"Output:  {BENCHMARKS_DIR}")

    # Also generate a run_selected_tasks.sh-compatible selection entry list
    run_selection = []
    for task in tasks:
        run_selection.append({
            "benchmark": "curator_calibration",
            "task_dir": f"curator_calibration/{task['task_id']}",
            "task_id": task["task_id"],
            "suite": "curator_calibration",
        })

    run_sel_path = REPO_ROOT / "configs" / "contextbench_run_selection.json"
    run_sel_path.write_text(json.dumps({"tasks": run_selection}, indent=2) + "\n")
    log.info("Wrote run selection: %s", run_sel_path)

    return created


def main():
    parser = argparse.ArgumentParser(
        description="Scaffold ContextBench tasks into Harbor format"
    )
    parser.add_argument(
        "--selection",
        type=Path,
        default=SELECTION_DEFAULT,
        help="Path to pilot selection JSON",
    )
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    scaffold_all(args.selection, args.dry_run)


if __name__ == "__main__":
    main()
