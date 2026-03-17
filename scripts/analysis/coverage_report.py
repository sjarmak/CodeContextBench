#!/usr/bin/env python3
"""Coverage analysis tool - answers "what is our coverage for X model/agent?"

Scans both runs/official/ and runs/staging/ to report coverage by suite,
distinguishing official vs staging and showing validation status for staging runs.

Usage:
    python3 scripts/analysis/coverage_report.py                          # All suites
    python3 scripts/analysis/coverage_report.py --model sonnet           # Filter by model
    python3 scripts/analysis/coverage_report.py --agent openhands        # Filter by agent
    python3 scripts/analysis/coverage_report.py --model sonnet --agent cc  # Both filters
"""

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "maintenance"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "evaluation"))

from config_utils import detect_suite, discover_configs
from official_runs import raw_runs_dir

# ANSI colors
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"

RUNS_OFFICIAL = raw_runs_dir(PROJECT_ROOT / "runs" / "official")
RUNS_STAGING = PROJECT_ROOT / "runs" / "staging"
BENCHMARKS_ROOT = PROJECT_ROOT / "benchmarks"


def extract_model_from_run_name(run_name: str) -> Optional[str]:
    """Extract model name from run directory name.

    Examples:
        csb_sdlc_design_sonnet_20260316_170420 -> sonnet
        openhands_sonnet46_20260316_170312 -> sonnet46
    """
    # Look for model patterns (sonnet, sonnet46, opus, haiku, etc.)
    for pattern in ["sonnet46", "sonnet", "opus", "haiku", "claude", "gpt"]:
        if pattern in run_name.lower():
            # Extract the actual token
            match = re.search(
                r"(sonnet\d*|opus|haiku|claude[^_]*|gpt[^_]*)",
                run_name.lower()
            )
            if match:
                return match.group(1)
    return None


def extract_agent_from_run_name(run_name: str) -> Optional[str]:
    """Extract agent/tool name from run directory name.

    Examples:
        openhands_sonnet46_20260316_170312 -> openhands
        cc_sonnet_20260316 -> cc
    """
    parts = run_name.split("_")
    # First part is often the agent/tool name
    if parts and parts[0] not in ["csb", "ccb"]:
        return parts[0]
    return None


def scan_canonical_tasks() -> dict[str, list[str]]:
    """Scan benchmarks/csb_*/ to find all canonical task directories.

    Returns:
        Dict mapping suite -> list of task names
    """
    canonical = defaultdict(list)

    if not BENCHMARKS_ROOT.exists():
        return canonical

    # Each benchmark directory is a suite
    for suite_dir in sorted(BENCHMARKS_ROOT.glob("csb_*")):
        if not suite_dir.is_dir():
            continue

        suite_name = suite_dir.name

        # Each task is a directory in the suite
        for task_dir in sorted(suite_dir.iterdir()):
            if task_dir.is_dir() and (task_dir / "task.toml").exists():
                canonical[suite_name].append(task_dir.name)

    return canonical


def scan_official_runs() -> dict[str, dict[str, set[str]]]:
    """Scan runs/official/ for completed tasks.

    Returns:
        Dict mapping suite -> config -> set of task names
    """
    coverage = defaultdict(lambda: defaultdict(set))

    if not RUNS_OFFICIAL.exists():
        return coverage

    # Scan official runs
    try:
        for run_dir in sorted(RUNS_OFFICIAL.iterdir()):
            if not run_dir.is_dir():
                continue

            suite = detect_suite(run_dir.name)
            if not suite:
                continue

            # Scan configs in this run
            for config in discover_configs(run_dir):
                config_path = run_dir / config

                # Find all result.json files
                for result_file in config_path.rglob("result.json"):
                    task_dir = result_file.parent
                    if "__" in task_dir.name:
                        task_name = task_dir.name.rsplit("__", 1)[0]
                        coverage[suite][config].add(task_name)
    except Exception:
        pass  # Gracefully handle missing or malformed runs

    return coverage


def scan_staging_runs(
    model_filter: Optional[str] = None,
    agent_filter: Optional[str] = None,
) -> dict[str, dict[str, dict[str, dict]]]:
    """Scan runs/staging/ for runs and their validation status.

    Staging structure: run_dir/config/timestamp/task_dir/result.json

    Returns:
        Dict mapping suite -> config -> task_name -> {status, run_name}
    """
    coverage = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))

    if not RUNS_STAGING.exists():
        return coverage

    for run_dir in sorted(RUNS_STAGING.iterdir()):
        if not run_dir.is_dir():
            continue

        run_name = run_dir.name

        # Apply model/agent filters
        if model_filter:
            model = extract_model_from_run_name(run_name)
            if not model or model_filter.lower() not in model.lower():
                continue

        if agent_filter:
            agent = extract_agent_from_run_name(run_name)
            if not agent or agent_filter.lower() not in agent.lower():
                continue

        suite = detect_suite(run_name)
        if not suite:
            continue

        # Staging structure: run_dir/config/timestamp/task_dir/result.json
        for config_path in run_dir.iterdir():
            if not config_path.is_dir():
                continue

            config_name = config_path.name

            # Iterate through timestamp directories
            for timestamp_path in config_path.iterdir():
                if not timestamp_path.is_dir():
                    continue

                # Iterate through task directories or result.json
                for task_or_result in timestamp_path.iterdir():
                    result_file = None
                    task_name = None

                    if task_or_result.is_file() and task_or_result.name == "result.json":
                        # result.json directly in timestamp dir
                        result_file = task_or_result
                        # Extract task name from result.json
                        try:
                            data = json.loads(result_file.read_text())
                            task_name = data.get("task_name", "")
                            if not task_name:
                                # Try to get from task_id
                                task_id = data.get("task_id", {})
                                if isinstance(task_id, dict):
                                    task_name = task_id.get("name", "")
                        except (json.JSONDecodeError, OSError):
                            pass

                    elif task_or_result.is_dir() and "__" in task_or_result.name:
                        # task_dir/result.json structure
                        task_name = task_or_result.name.rsplit("__", 1)[0]
                        result_file = task_or_result / "result.json"
                        if not result_file.exists():
                            result_file = None

                    if result_file and result_file.exists() and task_name:
                        # Check validation status
                        validation_status = "unlabeled"  # default

                        try:
                            data = json.loads(result_file.read_text())
                            status = data.get("status", "")
                            if status in ("passed", "failed"):
                                validation_status = "valid"
                            elif status == "errored":
                                validation_status = "invalid"
                        except (json.JSONDecodeError, OSError):
                            pass

                        coverage[suite][config_name][task_name] = {
                            "run_name": run_name,
                            "status": validation_status,
                        }

    return coverage


def format_coverage_summary(
    canonical: dict[str, list[str]],
    official: dict[str, dict[str, set[str]]],
    staging: dict[str, dict[str, dict[str, dict]]],
) -> str:
    """Format coverage report."""
    lines = []

    lines.append(f"\n{BOLD}Coverage Report{RESET}\n")
    lines.append(f"{'=' * 80}\n")

    total_canonical = sum(len(tasks) for tasks in canonical.values())
    total_official = sum(
        len(tasks) for config_tasks in official.values() for tasks in config_tasks.values()
    )
    total_staging = sum(
        len(tasks) for config_tasks in staging.values() for tasks in config_tasks.values()
    )

    lines.append(f"Canonical tasks (benchmarks/csb_*/):  {total_canonical}\n")
    lines.append(f"Official runs coverage:              {total_official} tasks\n")
    lines.append(f"Staging runs coverage:               {total_staging} tasks\n")
    lines.append(f"{'=' * 80}\n\n")

    # Report by suite
    all_suites = set(canonical.keys()) | set(official.keys()) | set(staging.keys())

    for suite in sorted(all_suites):
        canonical_tasks = set(canonical.get(suite, []))
        official_tasks = set()
        staging_tasks = set()
        staging_valid = 0
        staging_invalid = 0
        staging_unlabeled = 0

        # Aggregate official coverage
        for config_tasks in official.get(suite, {}).values():
            official_tasks.update(config_tasks)

        # Aggregate staging coverage and validation status
        for config_tasks in staging.get(suite, {}).values():
            for task_name, task_info in config_tasks.items():
                staging_tasks.add(task_name)
                if task_info["status"] == "valid":
                    staging_valid += 1
                elif task_info["status"] == "invalid":
                    staging_invalid += 1
                else:
                    staging_unlabeled += 1

        # Calculate coverage
        official_coverage = len(official_tasks & canonical_tasks) if canonical_tasks else 0
        official_pct = (official_coverage / len(canonical_tasks) * 100) if canonical_tasks else 0.0

        staging_coverage = len(staging_tasks & canonical_tasks) if canonical_tasks else 0
        staging_pct = (staging_coverage / len(canonical_tasks) * 100) if canonical_tasks else 0.0

        # Format suite header
        canonical_count = len(canonical_tasks)
        lines.append(f"{BOLD}{suite}{RESET}\n")
        lines.append(f"  Canonical tasks:       {canonical_count}\n")
        lines.append(
            f"  Official coverage:     {GREEN}{official_coverage}/{canonical_count} ({official_pct:.1f}%){RESET}\n"
        )

        if staging_tasks:
            status_str = (
                f"{staging_valid} valid"
                + (f", {staging_invalid} invalid" if staging_invalid > 0 else "")
                + (f", {staging_unlabeled} unlabeled" if staging_unlabeled > 0 else "")
            )
            lines.append(
                f"  Staging coverage:      {staging_coverage}/{canonical_count} ({staging_pct:.1f}%) [{status_str}]\n"
            )

        # Show gaps
        gaps = canonical_tasks - official_tasks - staging_tasks
        if gaps:
            lines.append(f"  {RED}Missing:{RESET} {len(gaps)} tasks\n")
            if len(gaps) <= 5:
                for task in sorted(gaps):
                    lines.append(f"    - {task}\n")
            else:
                for task in sorted(list(gaps)[:5]):
                    lines.append(f"    - {task}\n")
                lines.append(f"    ... and {len(gaps) - 5} more\n")

        lines.append("\n")

    return "".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Coverage analysis tool - reports test coverage by suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                              Show overall coverage
  %(prog)s --model sonnet               Filter to model
  %(prog)s --agent openhands            Filter to agent
  %(prog)s --model sonnet --agent cc    Filter to both
        """,
    )
    parser.add_argument("--model", type=str, default=None, help="Filter runs by model name")
    parser.add_argument("--agent", type=str, default=None, help="Filter runs by agent name")
    parser.add_argument("--json", action="store_true", help="Output as JSON instead of table")

    args = parser.parse_args()

    # Scan all sources
    canonical = scan_canonical_tasks()
    official = scan_official_runs()
    staging = scan_staging_runs(model_filter=args.model, agent_filter=args.agent)

    if args.json:
        # Output as JSON
        data = {
            "canonical": {suite: sorted(tasks) for suite, tasks in canonical.items()},
            "official": {
                suite: {
                    config: sorted(tasks)
                    for config, tasks in config_map.items()
                }
                for suite, config_map in official.items()
            },
            "staging": {
                suite: {
                    config: {
                        task: task_info
                        for task, task_info in task_map.items()
                    }
                    for config, task_map in config_map.items()
                }
                for suite, config_map in staging.items()
            },
        }
        print(json.dumps(data, indent=2))
    else:
        # Output as formatted report
        print(format_coverage_summary(canonical, official, staging))


if __name__ == "__main__":
    main()
