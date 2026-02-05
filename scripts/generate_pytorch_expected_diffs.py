#!/usr/bin/env python3
"""Generate expected.diff files for PyTorch benchmark tasks.

Reads each task's task.toml for pre_fix_rev and ground_truth_rev,
downloads the diff from GitHub, and writes to tests/expected.diff.

Usage:
    python3 scripts/generate_pytorch_expected_diffs.py
    python3 scripts/generate_pytorch_expected_diffs.py --task sgt-002
    python3 scripts/generate_pytorch_expected_diffs.py --dry-run
"""
import argparse
import os
import sys
import urllib.request
import urllib.error

# Tasks that use the diff-based verifier (sgt-001 excluded: has custom verifier)
DIFF_TASKS = [
    "sgt-002", "sgt-003", "sgt-005", "sgt-007", "sgt-009",
    "sgt-010", "sgt-014", "sgt-016", "sgt-017", "sgt-021", "sgt-024",
]

BENCHMARKS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                              "benchmarks", "ccb_pytorch")
GITHUB_COMMIT_URL = "https://github.com/pytorch/pytorch/commit/{commit}.diff"


def parse_task_toml(task_dir: str) -> dict:
    """Parse task.toml to extract pre_fix_rev and ground_truth_rev.

    Simple parser — no toml library dependency.
    """
    toml_path = os.path.join(task_dir, "task.toml")
    if not os.path.isfile(toml_path):
        return {}

    result = {}
    with open(toml_path) as f:
        for line in f:
            line = line.strip()
            if line.startswith("pre_fix_rev"):
                result["pre_fix_rev"] = line.split("=", 1)[1].strip().strip('"')
            elif line.startswith("ground_truth_rev"):
                result["ground_truth_rev"] = line.split("=", 1)[1].strip().strip('"')
    return result


def download_diff(commit: str) -> str:
    """Download unified diff for a single commit from GitHub."""
    url = GITHUB_COMMIT_URL.format(commit=commit)
    print(f"  Downloading: {url}")
    req = urllib.request.Request(url)
    req.add_header("Accept", "text/plain")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        print(f"  ERROR: HTTP {e.code} for {url}", file=sys.stderr)
        return ""
    except Exception as e:
        print(f"  ERROR: {e}", file=sys.stderr)
        return ""


def count_diff_files(diff_text: str) -> int:
    """Count the number of files in a unified diff."""
    return sum(1 for line in diff_text.splitlines() if line.startswith("+++ b/"))


def main():
    parser = argparse.ArgumentParser(description="Generate expected.diff files for PyTorch tasks")
    parser.add_argument("--task", help="Process only this task ID (e.g. sgt-002)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without writing files")
    args = parser.parse_args()

    tasks = [args.task] if args.task else DIFF_TASKS
    success = 0
    failed = 0

    for task_id in tasks:
        if task_id not in DIFF_TASKS:
            print(f"WARNING: {task_id} not in DIFF_TASKS list, skipping")
            continue

        task_dir = os.path.join(BENCHMARKS_DIR, task_id)
        if not os.path.isdir(task_dir):
            print(f"ERROR: Task directory not found: {task_dir}")
            failed += 1
            continue

        config = parse_task_toml(task_dir)
        pre_fix = config.get("pre_fix_rev")
        ground_truth = config.get("ground_truth_rev")

        if not pre_fix or not ground_truth:
            print(f"ERROR: Missing commit hashes in {task_id}/task.toml")
            failed += 1
            continue

        print(f"\n{task_id}: ground_truth={ground_truth[:12]}")

        if args.dry_run:
            print(f"  Would download diff and write to {task_id}/tests/expected.diff")
            success += 1
            continue

        diff_text = download_diff(ground_truth)
        if not diff_text.strip():
            print(f"  ERROR: Empty diff for {task_id}")
            failed += 1
            continue

        file_count = count_diff_files(diff_text)
        print(f"  Files in diff: {file_count}")
        print(f"  Diff size: {len(diff_text)} bytes")

        output_dir = os.path.join(task_dir, "tests")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "expected.diff")
        with open(output_path, "w") as f:
            f.write(diff_text)
        print(f"  Written: {output_path}")
        success += 1

    print(f"\n{'DRY RUN ' if args.dry_run else ''}Summary: {success} succeeded, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
