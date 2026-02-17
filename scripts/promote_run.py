#!/usr/bin/env python3
"""Promote validated benchmark runs from staging to official.

Runs land in runs/staging/ by default. This script validates them
and moves them to runs/official/ if they pass quality gates.

Usage:
    # List staging runs and their validation status
    python3 scripts/promote_run.py --list

    # Dry-run: show what would happen (default)
    python3 scripts/promote_run.py navprove_opus_20260217_120000

    # Actually promote
    python3 scripts/promote_run.py --execute navprove_opus_20260217_120000

    # Promote all eligible runs
    python3 scripts/promote_run.py --execute --all

    # Force-promote despite validation failures
    python3 scripts/promote_run.py --execute --force navprove_opus_20260217_120000
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STAGING_DIR = PROJECT_ROOT / "runs" / "staging"
OFFICIAL_DIR = PROJECT_ROOT / "runs" / "official"
VALIDATE_SCRIPT = PROJECT_ROOT / "scripts" / "validate_task_run.py"
MANIFEST_SCRIPT = PROJECT_ROOT / "scripts" / "generate_manifest.py"

SKIP_PATTERNS = ["__broken_verifier", "validation_test", "archive", "__v1_hinted"]
CONFIGS = ["baseline", "sourcegraph_base", "sourcegraph_full", "sourcegraph_isolated", "sourcegraph_only"]

# ANSI colors
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"


@dataclass
class ValidationResult:
    run_name: str
    configs_found: list[str] = field(default_factory=list)
    total_tasks: int = 0
    tasks_with_results: int = 0
    critical_count: int = 0
    warning_count: int = 0
    info_count: int = 0
    flags: list[dict] = field(default_factory=list)
    error: str | None = None


def should_skip(name: str) -> bool:
    return any(pat in name for pat in SKIP_PATTERNS)


def find_task_dirs(config_path: Path) -> list[Path]:
    """Find task directories, handling both layouts.

    Layout v1: config/task_name__hash/result.json
    Layout v2: config/batch_timestamp/task_name__hash/result.json
    """
    task_dirs = []
    if not config_path.is_dir():
        return task_dirs

    batch_ts_re = re.compile(r"^\d{4}-\d{2}-\d{2}__\d{2}-\d{2}-\d{2}$")

    for entry in sorted(config_path.iterdir()):
        if not entry.is_dir() or should_skip(entry.name):
            continue

        if batch_ts_re.match(entry.name):
            # Layout v2: batch timestamp dir — look inside for task dirs
            for sub in sorted(entry.iterdir()):
                if sub.is_dir() and "__" in sub.name and not should_skip(sub.name):
                    task_dirs.append(sub)
        elif "__" in entry.name:
            # Layout v1: direct task dir
            task_dirs.append(entry)

    return task_dirs


def validate_run(run_dir: Path) -> ValidationResult:
    """Validate a staging run and return results."""
    result = ValidationResult(run_name=run_dir.name)

    if not run_dir.is_dir():
        result.error = f"Directory not found: {run_dir}"
        return result

    # Find config subdirectories
    for config_name in CONFIGS:
        config_path = run_dir / config_name
        if config_path.is_dir():
            result.configs_found.append(config_name)

    if not result.configs_found:
        result.error = "No config directories found (expected baseline/, sourcegraph_full/, etc.)"
        return result

    # Validate each config
    for config_name in result.configs_found:
        config_path = run_dir / config_name
        task_dirs = find_task_dirs(config_path)
        result.total_tasks += len(task_dirs)

        # Count tasks with result.json
        for td in task_dirs:
            if (td / "result.json").exists():
                result.tasks_with_results += 1

        # Check for existing flagged_tasks.json (written by validate_and_report during run)
        flagged_file = config_path / "flagged_tasks.json"
        if flagged_file.exists():
            try:
                data = json.loads(flagged_file.read_text())
                result.critical_count += data.get("critical_count", 0)
                result.warning_count += data.get("warning_count", 0)
                result.info_count += data.get("info_count", 0)
                result.flags.extend(data.get("flags", []))
            except (json.JSONDecodeError, OSError):
                pass
        else:
            # Run validation if flagged_tasks.json doesn't exist
            try:
                subprocess.run(
                    [
                        sys.executable,
                        str(VALIDATE_SCRIPT),
                        "--jobs-dir", str(config_path),
                        "--config", config_name,
                    ],
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
                # Re-read the generated file
                if flagged_file.exists():
                    data = json.loads(flagged_file.read_text())
                    result.critical_count += data.get("critical_count", 0)
                    result.warning_count += data.get("warning_count", 0)
                    result.info_count += data.get("info_count", 0)
                    result.flags.extend(data.get("flags", []))
            except (subprocess.TimeoutExpired, OSError) as e:
                result.error = f"Validation failed for {config_name}: {e}"

    return result


def check_gates(
    result: ValidationResult, max_warnings: int, force: bool
) -> tuple[bool, list[str]]:
    """Check promotion gates. Returns (passed, reasons)."""
    reasons = []
    passed = True

    if result.error:
        reasons.append(f"{RED}[FAIL]{RESET} Validation error: {result.error}")
        if not force:
            passed = False

    if result.critical_count > 0:
        reasons.append(
            f"{RED}[FAIL]{RESET} {result.critical_count} critical issue(s) found"
        )
        if not force:
            passed = False
    else:
        reasons.append(f"{GREEN}[PASS]{RESET} No critical issues")

    missing = result.total_tasks - result.tasks_with_results
    if missing > 0:
        reasons.append(
            f"{RED}[FAIL]{RESET} {missing} task(s) missing result.json ({result.tasks_with_results}/{result.total_tasks})"
        )
        if not force:
            passed = False
    else:
        reasons.append(
            f"{GREEN}[PASS]{RESET} All tasks completed ({result.tasks_with_results}/{result.total_tasks})"
        )

    if result.warning_count > max_warnings:
        reasons.append(
            f"{YELLOW}[WARN]{RESET} {result.warning_count} warnings (threshold: {max_warnings})"
        )
        if not force:
            passed = False
    else:
        reasons.append(
            f"{GREEN}[PASS]{RESET} Warnings within threshold ({result.warning_count} <= {max_warnings})"
        )

    return passed, reasons


def discover_staging_runs() -> list[Path]:
    """List all run directories in staging."""
    if not STAGING_DIR.is_dir():
        return []

    runs = []
    for entry in sorted(STAGING_DIR.iterdir()):
        if entry.is_dir() and not should_skip(entry.name) and entry.name != "archive":
            runs.append(entry)
    return runs


def get_run_age(run_dir: Path) -> str:
    """Get human-readable age of a run directory."""
    try:
        mtime = run_dir.stat().st_mtime
        age_seconds = (datetime.now().timestamp() - mtime)
        if age_seconds < 3600:
            return f"{int(age_seconds / 60)}m ago"
        elif age_seconds < 86400:
            return f"{int(age_seconds / 3600)}h ago"
        else:
            return f"{int(age_seconds / 86400)}d ago"
    except OSError:
        return "unknown"


def cmd_list():
    """List staging runs with validation status."""
    runs = discover_staging_runs()
    if not runs:
        print("No staging runs found.")
        return

    print(f"\n{BOLD}Staging Runs ({len(runs)} total):{RESET}\n")
    print(f"  {'RUN NAME':<55s} {'TASKS':>5s} {'DONE':>5s} {'CRIT':>5s} {'WARN':>5s} {'AGE':>8s} {'STATUS'}")
    print(f"  {'-' * 55} {'-' * 5} {'-' * 5} {'-' * 5} {'-' * 5} {'-' * 8} {'-' * 12}")

    for run_dir in runs:
        result = validate_run(run_dir)
        age = get_run_age(run_dir)

        if result.error:
            status = f"{RED}ERROR{RESET}"
        elif result.critical_count > 0:
            status = f"{RED}BLOCKED{RESET}"
        elif result.tasks_with_results < result.total_tasks:
            status = f"{YELLOW}RUNNING{RESET}"
        else:
            status = f"{GREEN}READY{RESET}"

        print(
            f"  {run_dir.name:<55s} {result.total_tasks:>5d} "
            f"{result.tasks_with_results:>5d} {result.critical_count:>5d} "
            f"{result.warning_count:>5d} {age:>8s} {status}"
        )

    print()


def cmd_promote(
    run_names: list[str],
    execute: bool,
    force: bool,
    max_warnings: int,
    promote_all: bool,
    regenerate: bool,
):
    """Validate and promote staging runs."""
    if promote_all:
        staging_runs = discover_staging_runs()
        if not staging_runs:
            print("No staging runs found.")
            return
        run_dirs = staging_runs
    else:
        run_dirs = []
        for name in run_names:
            run_dir = STAGING_DIR / name
            if not run_dir.is_dir():
                print(f"{RED}ERROR:{RESET} Staging run not found: {name}")
                print(f"  Expected: {run_dir}")
                sys.exit(1)
            run_dirs.append(run_dir)

    promoted = []
    skipped = []

    for run_dir in run_dirs:
        print(f"\n{BOLD}Validating:{RESET} {run_dir.name}")

        result = validate_run(run_dir)

        print(f"  Configs: {', '.join(result.configs_found) or 'none'}")
        print(f"  Tasks: {result.total_tasks} total, {result.tasks_with_results} with results")
        print(f"  Validation: {result.critical_count} critical, {result.warning_count} warnings, {result.info_count} info")

        if result.error:
            print(f"  {RED}Error:{RESET} {result.error}")

        passed, reasons = check_gates(result, max_warnings, force)

        print(f"\n  Promotion gates:")
        for r in reasons:
            print(f"    {r}")

        if force and not passed:
            print(f"\n  {YELLOW}--force: bypassing failed gates{RESET}")
            passed = True

        official_dest = OFFICIAL_DIR / run_dir.name
        if official_dest.exists():
            if force:
                suffix = datetime.now().strftime("__promoted_%Y%m%d_%H%M%S")
                official_dest = OFFICIAL_DIR / (run_dir.name + suffix)
                print(f"\n  {YELLOW}Conflict: appending suffix → {official_dest.name}{RESET}")
            else:
                print(f"\n  {RED}[FAIL]{RESET} Already exists in official: {official_dest.name}")
                skipped.append(run_dir.name)
                continue

        if not passed:
            print(f"\n  {RED}BLOCKED:{RESET} Run does not pass promotion gates.")
            if not force:
                print(f"  Use --force to bypass.")
            skipped.append(run_dir.name)
            continue

        if execute:
            print(f"\n  Promoting: {run_dir.name}")
            shutil.move(str(run_dir), str(official_dest))
            print(f"  {GREEN}Moved to:{RESET} {official_dest}")
            promoted.append(official_dest.name)
        else:
            print(f"\n  {BOLD}DRY RUN:{RESET} Would move:")
            print(f"    {run_dir} → {official_dest}")
            promoted.append(run_dir.name)

    # Summary
    print(f"\n{'=' * 60}")
    if execute:
        print(f"Promoted: {len(promoted)}, Skipped: {len(skipped)}")
    else:
        print(f"Would promote: {len(promoted)}, Would skip: {len(skipped)}")

    if not execute and promoted:
        print(f"\nUse --execute to perform the promotion.")

    # Regenerate MANIFEST after promotion
    if execute and promoted and regenerate:
        print(f"\nRegenerating MANIFEST.json...")
        try:
            proc = subprocess.run(
                [sys.executable, str(MANIFEST_SCRIPT)],
                capture_output=True,
                text=True,
                timeout=120,
            )
            if proc.returncode == 0:
                print(f"  {GREEN}MANIFEST regenerated.{RESET}")
                # Show summary from stdout
                for line in proc.stdout.strip().split("\n")[-3:]:
                    print(f"  {line}")
            else:
                print(f"  {YELLOW}MANIFEST generation returned code {proc.returncode}{RESET}")
                if proc.stderr:
                    print(f"  {proc.stderr[:200]}")
        except (subprocess.TimeoutExpired, OSError) as e:
            print(f"  {RED}MANIFEST generation failed: {e}{RESET}")


def main():
    parser = argparse.ArgumentParser(
        description="Promote validated benchmark runs from staging to official.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --list                         List staging runs
  %(prog)s navprove_opus_20260217_*       Dry-run validation
  %(prog)s --execute navprove_opus_*      Promote to official
  %(prog)s --execute --all                Promote all eligible
  %(prog)s --execute --force <name>       Bypass gates
        """,
    )
    parser.add_argument("runs", nargs="*", help="Staging run directory name(s)")
    parser.add_argument("--list", action="store_true", help="List staging runs with status")
    parser.add_argument("--execute", action="store_true", help="Actually move runs (default is dry-run)")
    parser.add_argument("--force", action="store_true", help="Bypass validation gates")
    parser.add_argument("--all", action="store_true", help="Promote all eligible staging runs")
    parser.add_argument("--max-warnings", type=int, default=10, help="Max allowed warnings (default: 10)")
    parser.add_argument("--no-regenerate", action="store_true", help="Skip MANIFEST regeneration")

    args = parser.parse_args()

    if args.list:
        cmd_list()
        return

    if not args.runs and not args.all:
        parser.print_help()
        sys.exit(1)

    cmd_promote(
        run_names=args.runs,
        execute=args.execute,
        force=args.force,
        max_warnings=args.max_warnings,
        promote_all=args.all,
        regenerate=not args.no_regenerate,
    )


if __name__ == "__main__":
    main()
