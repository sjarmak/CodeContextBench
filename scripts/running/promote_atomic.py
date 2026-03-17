#!/usr/bin/env python3
"""Atomic run promotion using RunPromotionOrchestrator.

This is the recommended way to promote runs. It ensures all-or-nothing semantics:
- All steps (move, manifest regen, metrics, results export) succeed together
- Or everything rolls back and the run stays in staging
"""

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from csb_metrics.run_promotion import RunPromotionOrchestrator, validate_promotion_feasibility

STAGING_DIR = PROJECT_ROOT / "runs" / "staging"
OFFICIAL_DIR = PROJECT_ROOT / "runs" / "official"
MANIFEST_SCRIPT = PROJECT_ROOT / "scripts" / "maintenance" / "generate_manifest.py"
EXTRACT_METRICS_SCRIPT = PROJECT_ROOT / "scripts" / "evaluation" / "extract_task_metrics.py"
EXPORT_RESULTS_SCRIPT = PROJECT_ROOT / "scripts" / "analysis" / "export_official_results.py"


def promote_runs_atomically(
    run_names: list[str],
    dry_run: bool = True,
    output_log: Path | None = None,
):
    """Promote multiple runs using atomic orchestrator.

    Args:
        run_names: List of run names to promote
        dry_run: If True, validate but don't commit changes
        output_log: Optional path to write JSON log of results
    """
    orchestrator = RunPromotionOrchestrator(
        staging_dir=STAGING_DIR,
        official_dir=OFFICIAL_DIR,
        manifest_script=MANIFEST_SCRIPT,
        extract_metrics_script=EXTRACT_METRICS_SCRIPT,
        export_results_script=EXPORT_RESULTS_SCRIPT,
    )

    # Pre-flight validation
    print(f"{'=' * 60}")
    print("PRE-FLIGHT VALIDATION")
    print(f"{'=' * 60}\n")

    validation_passed = True
    for run_name in run_names:
        staging_run = STAGING_DIR / run_name
        feasible, errors = validate_promotion_feasibility(staging_run, OFFICIAL_DIR)

        if feasible:
            print(f"✓ {run_name}: Ready for promotion")
        else:
            print(f"✗ {run_name}: Validation failed:")
            for error in errors:
                print(f"  - {error}")
            validation_passed = False

    if not validation_passed:
        print(f"\n{len(run_names)} run(s) failed validation. Aborting.")
        return

    # Atomic promotion
    print(f"\n{'=' * 60}")
    if dry_run:
        print("DRY RUN MODE - No changes will be made")
    else:
        print("EXECUTING ATOMIC PROMOTION")
    print(f"{'=' * 60}\n")

    results = orchestrator.promote_runs(run_names, dry_run=dry_run, continue_on_error=True)

    # Report results
    print(f"\n{'=' * 60}")
    print("PROMOTION RESULTS")
    print(f"{'=' * 60}\n")

    successful = []
    failed = []

    for result in results:
        status_icon = "✓" if result.success else "✗"
        print(f"{status_icon} {result.run_name}")
        print(f"  Duration: {result.duration_seconds:.1f}s")
        print(f"  Completed: {', '.join(result.steps_completed)}")

        if result.steps_failed:
            print(f"  Failed: {', '.join(result.steps_failed)}")
        if result.error_message:
            print(f"  Error: {result.error_message}")

        if result.success:
            successful.append(result)
        else:
            failed.append(result)

        print()

    print(f"Summary: {len(successful)} successful, {len(failed)} failed\n")

    # Write log if requested
    if output_log:
        log_data = {
            "timestamp": results[0].timestamp if results else "",
            "mode": "dry-run" if dry_run else "execute",
            "results": [r.to_dict() for r in results],
            "summary": {
                "total": len(results),
                "successful": len(successful),
                "failed": len(failed),
            },
        }
        output_log.write_text(json.dumps(log_data, indent=2))
        print(f"Log written to: {output_log}")


def main():
    parser = argparse.ArgumentParser(
        description="Atomically promote runs from staging to official using transactions.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run: validate without making changes
  %(prog)s navprove_opus_20260217_120000

  # Execute: atomically promote runs (all-or-nothing)
  %(prog)s --execute navprove_opus_* experiment_20260317_*

  # Execute and write log
  %(prog)s --execute --log /tmp/promotion.json navprove_opus_20260217_120000
        """,
    )
    parser.add_argument("runs", nargs="+", help="Staging run name(s) to promote")
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute promotion (default is dry-run validation)",
    )
    parser.add_argument(
        "--log",
        type=Path,
        help="Write JSON log of promotion results",
    )

    args = parser.parse_args()

    try:
        promote_runs_atomically(
            run_names=args.runs,
            dry_run=not args.execute,
            output_log=args.log,
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
