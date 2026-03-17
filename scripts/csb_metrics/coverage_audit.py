"""Unified coverage auditing across ground truth, runs, and canonicality.

Provides a single interface to query coverage status across:
- Ground truth availability (valid/invalid/missing)
- Run completion status (passed/failed/errored)
- Canonical status (has dual verifiers)
- Coverage tiers (missing/partial/complete/verified)
"""

import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class CoverageStatus:
    """Coverage status for a single task."""

    task_id: str
    suite: str

    # Ground truth coverage
    gt_status: str  # 'valid' | 'invalid-schema' | 'empty' | 'missing'
    gt_provenance: Optional[str] = None  # 'manual' | 'curator' | 'none'
    gt_file: Optional[str] = None  # Path to GT file

    # Run coverage
    run_status: Optional[str] = None  # 'passed' | 'failed' | 'errored' | None
    run_completed: bool = False  # Has task_metrics.json

    # Canonical status
    has_dual_verifiers: bool = False

    # Derived tier
    tier: str = "missing"  # 'missing' | 'partial' | 'complete' | 'verified'

    def __post_init__(self):
        """Compute coverage tier based on component statuses."""
        self._compute_tier()

    def _compute_tier(self):
        """Compute overall coverage tier."""
        # missing: no ground truth and no run results
        if self.gt_status in ("missing", "invalid-schema", "empty"):
            if not self.run_completed:
                self.tier = "missing"
                return

        # partial: ground truth exists but no successful run, or run exists but no GT
        if self.gt_status == "valid" and not self.run_completed:
            self.tier = "partial"
            return

        if self.run_completed and self.gt_status != "valid":
            self.tier = "partial"
            return

        # complete: both GT and run exist with passing status
        if self.gt_status == "valid" and self.run_completed:
            if self.run_status == "passed":
                self.tier = "complete"
            else:
                self.tier = "partial"
            return

        # verified: complete + has dual verifiers
        if (
            self.tier == "complete"
            and self.has_dual_verifiers
            and self.run_status == "passed"
        ):
            self.tier = "verified"

    def is_low_coverage(self) -> bool:
        """Check if task has low coverage."""
        return self.tier in ("missing", "partial")

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "task_id": self.task_id,
            "suite": self.suite,
            "tier": self.tier,
            "gt_status": self.gt_status,
            "gt_provenance": self.gt_provenance,
            "gt_file": self.gt_file,
            "run_status": self.run_status,
            "run_completed": self.run_completed,
            "has_dual_verifiers": self.has_dual_verifiers,
        }


class CoverageAudit:
    """Unified coverage auditing across multiple sources."""

    def __init__(self):
        """Initialize the coverage audit."""
        self.coverage_by_task: dict[str, CoverageStatus] = {}
        self.coverage_by_suite: dict[str, list[CoverageStatus]] = defaultdict(list)
        self.tier_counts: dict[str, int] = defaultdict(int)

    def add_coverage(self, status: CoverageStatus):
        """Add a coverage status for a task."""
        self.coverage_by_task[status.task_id] = status
        self.coverage_by_suite[status.suite].append(status)
        self.tier_counts[status.tier] += 1

    def get_status(self, task_id: str) -> Optional[CoverageStatus]:
        """Get coverage status for a specific task."""
        return self.coverage_by_task.get(task_id)

    def get_tasks_by_tier(self, tier: str) -> list[CoverageStatus]:
        """Get all tasks at a specific coverage tier.

        Args:
            tier: 'missing' | 'partial' | 'complete' | 'verified'

        Returns:
            List of CoverageStatus objects matching the tier.
        """
        return [
            status
            for status in self.coverage_by_task.values()
            if status.tier == tier
        ]

    def get_tasks_by_suite(self, suite: str) -> list[CoverageStatus]:
        """Get all tasks in a specific suite."""
        return self.coverage_by_suite.get(suite, [])

    def get_low_coverage_tasks(self) -> list[CoverageStatus]:
        """Get all tasks with missing or partial coverage."""
        return [
            status
            for status in self.coverage_by_task.values()
            if status.is_low_coverage()
        ]

    def get_summary(self) -> dict:
        """Get summary statistics."""
        total = len(self.coverage_by_task)
        if total == 0:
            return {
                "total": 0,
                "missing": 0,
                "partial": 0,
                "complete": 0,
                "verified": 0,
                "coverage_percent": 0.0,
            }

        missing = self.tier_counts.get("missing", 0)
        partial = self.tier_counts.get("partial", 0)
        complete = self.tier_counts.get("complete", 0)
        verified = self.tier_counts.get("verified", 0)

        # Coverage: complete + verified tasks
        covered = complete + verified
        coverage_percent = (covered / total * 100) if total > 0 else 0.0

        return {
            "total": total,
            "missing": missing,
            "partial": partial,
            "complete": complete,
            "verified": verified,
            "coverage_percent": round(coverage_percent, 1),
        }

    def get_summary_by_suite(self) -> dict[str, dict]:
        """Get coverage summary by suite."""
        summaries = {}
        for suite, tasks in self.coverage_by_suite.items():
            total = len(tasks)
            if total == 0:
                continue

            tier_counts = defaultdict(int)
            for task in tasks:
                tier_counts[task.tier] += 1

            missing = tier_counts.get("missing", 0)
            partial = tier_counts.get("partial", 0)
            complete = tier_counts.get("complete", 0)
            verified = tier_counts.get("verified", 0)

            covered = complete + verified
            coverage_percent = (covered / total * 100) if total > 0 else 0.0

            summaries[suite] = {
                "total": total,
                "missing": missing,
                "partial": partial,
                "complete": complete,
                "verified": verified,
                "coverage_percent": round(coverage_percent, 1),
            }

        return summaries

    def export_to_json(self, output_path: Path) -> None:
        """Export coverage audit to JSON file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "summary": self.get_summary(),
            "by_suite": self.get_summary_by_suite(),
            "tasks": {
                task_id: status.to_dict()
                for task_id, status in self.coverage_by_task.items()
            },
        }

        output_path.write_text(json.dumps(data, indent=2) + "\n")

    def print_summary(self, verbose: bool = False):
        """Print a summary report."""
        summary = self.get_summary()
        print(f"\nCoverage Summary")
        print(f"{'=' * 60}")
        print(f"  Total tasks:        {summary['total']}")
        print(f"  Verified:           {summary['verified']}")
        print(f"  Complete:           {summary['complete']}")
        print(f"  Partial:            {summary['partial']}")
        print(f"  Missing:            {summary['missing']}")
        print(f"  Coverage:           {summary['coverage_percent']:.1f}%")
        print()

        if verbose:
            print(f"Coverage by Suite")
            print(f"{'Suite':<40} {'Total':>6} {'Verified':>8} {'Complete':>9} {'Partial':>8} {'Missing':>7} {'Coverage':>9}")
            print(f"{'-' * 40} {'-' * 6} {'-' * 8} {'-' * 9} {'-' * 8} {'-' * 7} {'-' * 9}")

            for suite, suite_summary in sorted(self.get_summary_by_suite().items()):
                print(
                    f"{suite:<40} {suite_summary['total']:>6} "
                    f"{suite_summary['verified']:>8} {suite_summary['complete']:>9} "
                    f"{suite_summary['partial']:>8} {suite_summary['missing']:>7} "
                    f"{suite_summary['coverage_percent']:>8.1f}%"
                )
            print()
