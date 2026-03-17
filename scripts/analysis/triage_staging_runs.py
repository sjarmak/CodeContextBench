#!/usr/bin/env python3
"""Triage untriaged staging runs using trace quality pipeline.

Identifies staging runs that haven't been classified as valid/invalid
and runs the trace quality classification pipeline on them.
"""

import json
import subprocess
import sys
from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

RUNS_STAGING = PROJECT_ROOT / "runs" / "staging"
TRACE_QUALITY_PIPELINE = PROJECT_ROOT / "scripts" / "evaluation" / "trace_quality_pipeline.py"

# ANSI colors
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"


def find_untriaged_runs() -> list[str]:
    """Find all untriaged staging runs."""
    untriaged = []

    if not RUNS_STAGING.exists():
        return untriaged

    for run_dir in sorted(RUNS_STAGING.iterdir()):
        if not run_dir.is_dir():
            continue

        # Check if this run has any result.json files with status
        result_files = list(run_dir.rglob("result.json"))
        if not result_files:
            untriaged.append(run_dir.name)
            continue

        # Check if any results have valid status (passed/failed/errored)
        has_status = False
        for result_file in result_files:
            try:
                data = json.loads(result_file.read_text())
                status = data.get("status", "")
                if status in ("passed", "failed", "errored"):
                    has_status = True
                    break
            except (json.JSONDecodeError, OSError):
                pass

        if not has_status:
            untriaged.append(run_dir.name)

    return untriaged


def run_trace_quality_on_staging():
    """Run trace quality pipeline on staging directory."""
    print(f"\n{BOLD}Running Trace Quality Pipeline on Staging Runs{RESET}\n")
    print(f"{'=' * 80}\n")

    # Create output directory for trace quality results
    output_dir = PROJECT_ROOT / "runs" / "staging" / "_trace_quality_reports"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Run trace quality pipeline with staging directory
    output_file = output_dir / "trace_quality_report.json"
    metrics_file = output_dir / "trace_quality_metrics.json"

    cmd = [
        sys.executable,
        str(TRACE_QUALITY_PIPELINE),
        "--runs-dir",
        str(RUNS_STAGING),
        "--output",
        str(output_file),
        "--stage",
        "all",
        "--verbose",
    ]

    print(f"Running: {' '.join(cmd)}\n")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=3600,  # 1 hour timeout
        )

        print(result.stdout)
        if result.stderr:
            print(f"Warnings/Info:\n{result.stderr}\n")

        if result.returncode != 0:
            print(f"{RED}Pipeline returned exit code {result.returncode}{RESET}")
            return False

        # Check if output files were created
        if output_file.exists():
            print(f"\n{GREEN}✓ Trace quality report written to:{RESET}")
            print(f"  {output_file}")

            # Parse the report to show summary
            try:
                data = json.loads(output_file.read_text())
                summary = data.get("summary", {})
                total = summary.get("total_trials", 0)
                invalid = summary.get("n_invalid", 0)
                goodsetup = summary.get("n_goodsetup", 0)
                badsetup = summary.get("n_badsetup", 0)

                print(f"\n{BOLD}Classification Summary:{RESET}")
                print(f"  Total trials processed: {total}")
                print(f"  Valid (good setup):     {GREEN}{goodsetup}{RESET}")
                print(f"  Valid (bad setup):      {YELLOW}{badsetup}{RESET}")
                print(f"  Invalid:                {RED}{invalid}{RESET}")

                # Show top issues
                trials = data.get("trials", [])
                invalid_trials = [
                    t
                    for t in trials
                    if t.get("stage1_class") == "invalid"
                ]
                if invalid_trials:
                    print(f"\n{RED}Top Invalid Runs:{RESET}")
                    reasons = defaultdict(int)
                    for trial in invalid_trials:
                        reason = trial.get("stage1_reason", "unknown")
                        reasons[reason] += 1

                    for reason, count in sorted(
                        reasons.items(), key=lambda x: -x[1]
                    )[:5]:
                        print(f"  - {reason}: {count} trials")
            except (json.JSONDecodeError, OSError):
                pass

        if metrics_file.exists():
            print(f"  {metrics_file}")

        return True

    except subprocess.TimeoutExpired:
        print(f"{RED}Pipeline timed out after 1 hour{RESET}")
        return False
    except Exception as e:
        print(f"{RED}Error running pipeline: {e}{RESET}")
        return False


def report_triage_status():
    """Report the triage status of staging runs."""
    print(f"\n{BOLD}Staging Run Triage Status{RESET}\n")
    print(f"{'=' * 80}\n")

    untriaged = find_untriaged_runs()

    if not untriaged:
        print(f"{GREEN}✓ All staging runs have been triaged!{RESET}\n")
        return

    print(f"{YELLOW}Found {len(untriaged)} untriaged runs:{RESET}\n")

    # Group by model
    by_model = defaultdict(list)
    for run_name in untriaged:
        # Extract model from run name
        parts = run_name.split("_")
        model = None
        for part in parts:
            if any(m in part.lower() for m in ["sonnet", "opus", "haiku", "claude"]):
                model = part
                break
        if not model:
            model = "unknown"

        by_model[model].append(run_name)

    for model in sorted(by_model.keys()):
        runs = by_model[model]
        print(f"  {model}: {len(runs)} runs")
        for run in sorted(runs):
            print(f"    - {run}")

    print()


def main():
    # Report current status
    report_triage_status()

    # Run trace quality pipeline on staging
    untriaged = find_untriaged_runs()
    if not untriaged:
        print(f"{GREEN}No untriaged runs to process.{RESET}")
        return

    success = run_trace_quality_on_staging()

    if success:
        print(f"\n{GREEN}{'=' * 80}{RESET}")
        print(f"{GREEN}Triage complete! Check runs/staging/_trace_quality_reports/{RESET}")
        print(f"{GREEN}for detailed trace quality analysis.{RESET}")
    else:
        print(f"\n{RED}Triage failed. Check error messages above.{RESET}")
        sys.exit(1)


if __name__ == "__main__":
    main()
