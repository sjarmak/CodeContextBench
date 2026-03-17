#!/usr/bin/env python3
"""Integrate dual_score_lib.sh into all benchmarks/csb/ task verifiers.

For each task in benchmarks/csb/:
1. Copies dual_score_lib.sh to tests/
2. Appends source line to the END of test.sh (or eval.sh for Org tasks)
3. Ensures answer_json_verifier_lib.sh is present for tasks that need it

Three verifier patterns are handled:
  A) SDLC test.sh with answer_json_verifier_lib (123 tasks) — append dual_score source
  B) SDLC test.sh without answer_json_verifier_lib (8 tasks) — add both libs
  C) Org test.sh → eval.sh (81 tasks) — append to eval.sh
  D) Org promoted_verifier test.sh (55 tasks) — append to test.sh
  E) Org onboard-search test.sh (8 tasks) — append to test.sh
"""

import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSB_DIR = os.path.join(ROOT, "benchmarks", "csb")
DUAL_SCORE_LIB = os.path.join(ROOT, "scripts", "dual_score_lib.sh")
ANSWER_JSON_LIB = os.path.join(ROOT, "scripts", "answer_json_verifier_lib.sh")

DUAL_SCORE_SOURCE_LINE = '\n# Dual-score: independently score both direct edits and answer.json\n[ -f /tests/dual_score_lib.sh ] && source /tests/dual_score_lib.sh\n'

ANSWER_JSON_SOURCE_BLOCK = """
# Artifact mode: parse answer.json, extract analysis text, apply diffs
if [ -f /tests/answer_json_verifier_lib.sh ]; then
    source /tests/answer_json_verifier_lib.sh
fi
"""


def discover_tasks():
    """Find all task directories in benchmarks/csb/."""
    tasks = []
    for suite in sorted(os.listdir(CSB_DIR)):
        suite_path = os.path.join(CSB_DIR, suite)
        if not os.path.isdir(suite_path):
            continue
        for task_name in sorted(os.listdir(suite_path)):
            task_path = os.path.join(suite_path, task_name)
            if not os.path.isdir(task_path):
                continue
            tests_dir = os.path.join(task_path, "tests")
            if not os.path.isdir(tests_dir):
                continue
            tasks.append((suite, task_name, task_path))
    return tasks


def classify_task(task_path):
    """Classify task verifier pattern."""
    tests_dir = os.path.join(task_path, "tests")
    test_sh = os.path.join(tests_dir, "test.sh")
    eval_sh = os.path.join(tests_dir, "eval.sh")

    if not os.path.exists(test_sh):
        return "unknown", None

    with open(test_sh, "r") as f:
        test_content = f.read()

    # Pattern C: test.sh delegates to eval.sh
    if "exec bash" in test_content and "eval.sh" in test_content:
        if os.path.exists(eval_sh):
            return "eval_sh", eval_sh
        return "eval_sh_missing", test_sh

    # Pattern D: promoted_verifier
    if "promoted_verifier" in test_content:
        return "promoted_verifier", test_sh

    # Pattern E: onboard-search (solution.json)
    if "solution.json" in test_content and "RepoQA" in test_content:
        return "onboard_search", test_sh

    # Pattern A: has answer_json_verifier_lib
    if "answer_json_verifier_lib" in test_content:
        return "sdlc_with_answer_json", test_sh

    # Pattern B: SDLC without answer_json_verifier_lib
    return "sdlc_without_answer_json", test_sh


def has_dual_score(filepath):
    """Check if dual_score_lib.sh is already sourced."""
    with open(filepath, "r") as f:
        return "dual_score_lib.sh" in f.read()


def append_dual_score(filepath):
    """Append dual score source line to a shell script."""
    with open(filepath, "r") as f:
        content = f.read()

    # Don't add if already present
    if "dual_score_lib.sh" in content:
        return False

    # Remove trailing whitespace/newlines, then add our block
    content = content.rstrip() + "\n" + DUAL_SCORE_SOURCE_LINE

    with open(filepath, "w") as f:
        f.write(content)
    return True


def add_answer_json_lib(test_sh_path):
    """Add answer_json_verifier_lib source block to test.sh if missing."""
    with open(test_sh_path, "r") as f:
        content = f.read()

    if "answer_json_verifier_lib" in content:
        return False

    # Insert after the shebang and set -e lines
    lines = content.split("\n")
    insert_idx = 1  # After shebang
    for i, line in enumerate(lines):
        if line.startswith("set -") or line.startswith("[ -f /tmp/.sg_only_mode"):
            insert_idx = i + 1

    lines.insert(insert_idx, ANSWER_JSON_SOURCE_BLOCK)
    with open(test_sh_path, "w") as f:
        f.write("\n".join(lines))
    return True


def main():
    dry_run = "--dry-run" in sys.argv

    tasks = discover_tasks()
    print(f"Found {len(tasks)} tasks in benchmarks/csb/")

    # Classify
    by_type = {}
    for suite, task_name, task_path in tasks:
        task_type, target_file = classify_task(task_path)
        by_type.setdefault(task_type, []).append((suite, task_name, task_path, target_file))

    print("\nTask classification:")
    for task_type, items in sorted(by_type.items()):
        print(f"  {task_type:30s} {len(items):3d} tasks")

    if dry_run:
        print("\n[DRY RUN] Pass without --dry-run to execute.")
        return

    stats = {"copied_lib": 0, "added_dual_score": 0, "added_answer_json": 0, "skipped": 0}

    for suite, task_name, task_path, target_file in [
        item for items in by_type.values() for item in items
    ]:
        tests_dir = os.path.join(task_path, "tests")
        task_type, _ = classify_task(task_path)

        # Copy dual_score_lib.sh to tests/
        dst_dual = os.path.join(tests_dir, "dual_score_lib.sh")
        if not os.path.exists(dst_dual):
            shutil.copy2(DUAL_SCORE_LIB, dst_dual)
            stats["copied_lib"] += 1

        # Copy answer_json_verifier_lib.sh to tests/ if not present
        dst_answer = os.path.join(tests_dir, "answer_json_verifier_lib.sh")
        if not os.path.exists(dst_answer):
            shutil.copy2(ANSWER_JSON_LIB, dst_answer)

        if target_file is None:
            stats["skipped"] += 1
            continue

        # For eval.sh tasks, append to eval.sh (not test.sh which just delegates)
        if task_type == "eval_sh":
            if append_dual_score(target_file):
                stats["added_dual_score"] += 1
            else:
                stats["skipped"] += 1
            continue

        # For SDLC tasks without answer_json_lib, add it
        if task_type == "sdlc_without_answer_json":
            if add_answer_json_lib(target_file):
                stats["added_answer_json"] += 1

        # Append dual_score source to all other test.sh files
        if append_dual_score(target_file):
            stats["added_dual_score"] += 1
        else:
            stats["skipped"] += 1

    print(f"\nResults:")
    print(f"  Copied dual_score_lib.sh:       {stats['copied_lib']}")
    print(f"  Added dual_score source line:    {stats['added_dual_score']}")
    print(f"  Added answer_json_verifier_lib:  {stats['added_answer_json']}")
    print(f"  Skipped (already present):       {stats['skipped']}")


if __name__ == "__main__":
    main()
