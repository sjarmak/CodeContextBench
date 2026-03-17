#!/usr/bin/env python3
"""Canary empty-submission test: verify all verifiers reject empty/no-op solutions.

Builds each task's Docker image (or reuses cached), runs test.sh with zero agent
changes, and asserts reward.txt == 0.0. Tasks that score >0 on an empty submission
have a false-positive verifier bug.

This is a pre-deployment quality gate per arXiv 2507.02825 Outcome Validity
criterion O.c (empty/no-op solution must get reward=0).

Usage:
  python3 scripts/canary_empty_submission.py --dry-run          # List tasks to test
  python3 scripts/canary_empty_submission.py --execute           # Run all canary tests
  python3 scripts/canary_empty_submission.py --execute --suite csb/feature  # One suite
  python3 scripts/canary_empty_submission.py --execute --task benchmarks/csb/feature/cilium-policy-audit-logger-feat-001
"""

import argparse
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BENCHMARKS_DIR = PROJECT_ROOT / "benchmarks" / "csb"

# Task dirs that are known to legitimately pass on empty submission
# (e.g., analysis tasks that score on text quality, not code changes)
ALLOWLIST = set()


def discover_tasks(suite: str = None, task_path: str = None) -> list[Path]:
    """Find task directories to test."""
    if task_path:
        p = Path(task_path)
        if not p.is_absolute():
            p = PROJECT_ROOT / p
        return [p] if p.is_dir() else []

    if suite:
        suite_dir = BENCHMARKS_DIR / suite.replace("csb/", "")
        if not suite_dir.is_dir():
            suite_dir = PROJECT_ROOT / "benchmarks" / suite
        if not suite_dir.is_dir():
            print(f"Suite directory not found: {suite_dir}", file=sys.stderr)
            return []
        return sorted(
            d for d in suite_dir.iterdir()
            if d.is_dir() and not d.name.startswith((".", "_"))
            and (d / "tests" / "test.sh").is_file()
        )

    # All tasks
    tasks = []
    for suite_dir in sorted(BENCHMARKS_DIR.iterdir()):
        if not suite_dir.is_dir() or suite_dir.name.startswith((".", "_")):
            continue
        for task_dir in sorted(suite_dir.iterdir()):
            if (task_dir.is_dir()
                and not task_dir.name.startswith((".", "_"))
                and (task_dir / "tests" / "test.sh").is_file()):
                tasks.append(task_dir)
    return tasks


def has_dockerfile(task_dir: Path) -> bool:
    """Check if task has a buildable Dockerfile."""
    return (task_dir / "environment" / "Dockerfile").is_file() or (task_dir / "Dockerfile").is_file()


def build_image(task_dir: Path, tag: str) -> tuple[bool, str]:
    """Build Docker image for a task. Returns (success, error_message)."""
    dockerfile = task_dir / "environment" / "Dockerfile"
    if not dockerfile.is_file():
        dockerfile = task_dir / "Dockerfile"
    if not dockerfile.is_file():
        return False, "No Dockerfile found"

    context = dockerfile.parent
    cmd = [
        "docker", "build",
        "-t", tag,
        "-f", str(dockerfile),
        str(context),
    ]

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=300
        )
        if result.returncode != 0:
            return False, f"Build failed: {result.stderr[-200:]}"
        return True, ""
    except subprocess.TimeoutExpired:
        return False, "Build timed out (300s)"
    except Exception as e:
        return False, str(e)


def run_canary(task_dir: Path, tag: str) -> dict:
    """Run test.sh in Docker with zero agent changes. Returns result dict."""
    result = {
        "task": task_dir.name,
        "suite": task_dir.parent.name,
        "status": "unknown",
        "reward": None,
        "duration_s": 0,
        "error": None,
    }

    start = time.time()

    # Run the container: mount tests, create log dirs, run test.sh
    cmd = [
        "docker", "run", "--rm",
        "--name", f"canary-{task_dir.name[:40]}",
        "-e", "TASK_REPO_ROOT=/workspace",
        "-e", "TASK_OUTPUT=/workspace/answer.json",
        tag,
        "bash", "-c",
        "mkdir -p /logs/verifier /logs/agent/sessions && "
        "bash /tests/test.sh 2>&1; "
        "cat /logs/verifier/reward.txt 2>/dev/null || echo 'NO_REWARD_FILE'"
    ]

    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=120
        )
        result["duration_s"] = round(time.time() - start, 1)

        output = proc.stdout.strip()
        lines = output.split("\n")

        # Last line should be the reward value
        reward_line = lines[-1].strip() if lines else ""

        if reward_line == "NO_REWARD_FILE":
            result["status"] = "no_reward_file"
            result["error"] = "test.sh did not write reward.txt"
        else:
            try:
                reward = float(reward_line)
                result["reward"] = reward
                if reward <= 0.001:
                    result["status"] = "pass"  # Empty submission correctly rejected
                else:
                    result["status"] = "FAIL"  # False positive!
                    result["error"] = f"Empty submission scored {reward}"
            except ValueError:
                result["status"] = "parse_error"
                result["error"] = f"Could not parse reward: {reward_line[:50]}"

    except subprocess.TimeoutExpired:
        result["duration_s"] = round(time.time() - start, 1)
        result["status"] = "timeout"
        result["error"] = "Container timed out (120s)"
        # Kill the container
        subprocess.run(
            ["docker", "rm", "-f", f"canary-{task_dir.name[:40]}"],
            capture_output=True, timeout=10
        )
    except Exception as e:
        result["duration_s"] = round(time.time() - start, 1)
        result["status"] = "error"
        result["error"] = str(e)

    return result


def cleanup_image(tag: str):
    """Remove a Docker image."""
    subprocess.run(["docker", "rmi", "-f", tag], capture_output=True, timeout=30)


def main():
    parser = argparse.ArgumentParser(
        description="Canary test: verify verifiers reject empty submissions"
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true", help="List tasks without running")
    mode.add_argument("--execute", action="store_true", help="Run canary tests")

    parser.add_argument("--suite", help="Only test tasks in this suite (e.g., csb/feature)")
    parser.add_argument("--task", help="Test a single task directory")
    parser.add_argument("--keep-images", action="store_true", help="Don't remove Docker images after testing")
    parser.add_argument("--output", help="Write JSON results to file")
    args = parser.parse_args()

    tasks = discover_tasks(suite=args.suite, task_path=args.task)

    if not tasks:
        print("No tasks found.", file=sys.stderr)
        sys.exit(1)

    # Filter to tasks with Dockerfiles
    buildable = [t for t in tasks if has_dockerfile(t)]
    no_dockerfile = [t for t in tasks if not has_dockerfile(t)]

    if args.dry_run:
        print(f"Canary empty-submission test (DRY RUN)\n")
        print(f"  Buildable tasks: {len(buildable)}")
        print(f"  No Dockerfile:   {len(no_dockerfile)}")
        print(f"  Allowlisted:     {len([t for t in buildable if t.name in ALLOWLIST])}")
        print()
        for t in buildable:
            tag = "canary" if t.name not in ALLOWLIST else "skip"
            print(f"  [{tag}] {t.relative_to(PROJECT_ROOT)}")
        return

    # Execute canary tests
    results = []
    pass_count = 0
    fail_count = 0
    skip_count = 0
    error_count = 0

    print(f"Running canary tests on {len(buildable)} tasks...\n")

    for i, task_dir in enumerate(buildable):
        task_name = task_dir.name
        if task_name in ALLOWLIST:
            skip_count += 1
            continue

        tag = f"canary-{task_name[:50]}:latest"
        print(f"  [{i+1}/{len(buildable)}] {task_name}...", end=" ", flush=True)

        # Build
        ok, err = build_image(task_dir, tag)
        if not ok:
            r = {"task": task_name, "suite": task_dir.parent.name,
                 "status": "build_failed", "reward": None, "error": err}
            results.append(r)
            error_count += 1
            print(f"BUILD FAILED: {err[:60]}")
            continue

        # Run canary
        r = run_canary(task_dir, tag)
        results.append(r)

        if r["status"] == "pass":
            pass_count += 1
            print(f"PASS ({r['duration_s']}s)")
        elif r["status"] == "FAIL":
            fail_count += 1
            print(f"FAIL: {r['error']}")
        else:
            error_count += 1
            print(f"{r['status']}: {r.get('error', '')[:60]}")

        # Cleanup
        if not args.keep_images:
            cleanup_image(tag)

    # Summary
    print(f"\n{'='*60}")
    print(f"Canary Empty-Submission Results")
    print(f"{'='*60}")
    print(f"  Total:     {len(results)}")
    print(f"  Pass:      {pass_count} (empty submission correctly rejected)")
    print(f"  FAIL:      {fail_count} (FALSE POSITIVE — verifier bug)")
    print(f"  Errors:    {error_count} (build/timeout/parse)")
    print(f"  Skipped:   {skip_count} (allowlisted)")

    if fail_count > 0:
        print(f"\n  FALSE POSITIVES (score >0 on empty submission):")
        for r in results:
            if r["status"] == "FAIL":
                print(f"    {r['task']}: reward={r['reward']}")

    # Write results
    if args.output:
        Path(args.output).write_text(json.dumps(results, indent=2) + "\n")
        print(f"\nResults written to {args.output}")

    sys.exit(1 if fail_count > 0 else 0)


if __name__ == "__main__":
    main()
