"""Trace quality analysis and reporting.

Integrates with trace_quality_pipeline.py to provide structured access
to trace quality metrics for integration into MANIFEST.json and audit outputs.
"""

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class TraceQualityMetrics:
    """Quality metrics for a single trial/task."""

    task_name: str
    config: str
    suite: str
    run_name: str

    # Stage 1: Validity classification
    stage1_class: Optional[str] = None  # "valid" or "invalid"
    stage1_reason: Optional[str] = None  # Reason for invalid (if applicable)
    reward: Optional[float] = None  # Extracted reward/score

    # Stage 2: Setup quality (only for valid trials)
    stage2_class: Optional[str] = None  # "valid_goodsetup" or "valid_badsetup"
    stage2_reasons: list[str] = field(default_factory=list)  # List of issues found

    # Stage 3: Quality analysis (only for valid_goodsetup)
    hallucination_detected: bool = False
    hallucination_precision: Optional[float] = None
    hallucination_recall: Optional[float] = None
    verifier_flag: bool = False
    retrieval_metrics: dict = field(default_factory=dict)  # file_recall, recall@k, etc.

    # Derived quality flags
    has_quality_issues: bool = False
    quality_flags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "task_name": self.task_name,
            "config": self.config,
            "suite": self.suite,
            "run_name": self.run_name,
            "validity": self.stage1_class,
            "validity_reason": self.stage1_reason,
            "reward": self.reward,
            "setup_quality": self.stage2_class,
            "setup_issues": self.stage2_reasons,
            "quality_analysis": {
                "hallucination_detected": self.hallucination_detected,
                "hallucination_precision": self.hallucination_precision,
                "hallucination_recall": self.hallucination_recall,
                "verifier_flag": self.verifier_flag,
                "retrieval_metrics": self.retrieval_metrics,
            },
            "quality_flags": self.quality_flags,
            "has_quality_issues": self.has_quality_issues,
        }

    def add_quality_flag(self, flag: str):
        """Add a quality flag (e.g., 'hallucination', 'setup_issue', 'low_precision')."""
        if flag not in self.quality_flags:
            self.quality_flags.append(flag)
        self.has_quality_issues = True

    def is_low_quality(self) -> bool:
        """Check if trial has quality issues that should be flagged."""
        return (
            self.stage1_class == "invalid"
            or self.stage2_class == "valid_badsetup"
            or self.hallucination_detected
            or self.verifier_flag
            or len(self.quality_flags) > 0
        )


class TraceQualityReporter:
    """Handles trace quality analysis and reporting.

    Integrates with trace_quality_pipeline.py to provide structured
    access to quality metrics across runs and configurations.
    """

    def __init__(self, pipeline_results: Optional[dict] = None):
        """Initialize with optional pipeline results.

        Args:
            pipeline_results: Dict from trace_quality_pipeline.run_pipeline()
        """
        self.pipeline_results = pipeline_results or {}
        self.metrics_by_task: dict[str, TraceQualityMetrics] = {}
        self._parse_pipeline_results()

    def _parse_pipeline_results(self):
        """Parse pipeline results and extract TraceQualityMetrics."""
        trials = self.pipeline_results.get("trials", [])

        for record in trials:
            task_name = record.get("task_name", "unknown")
            config = record.get("config", "unknown")
            suite = record.get("suite", "unknown")
            run_name = record.get("run_name", "unknown")

            metrics = TraceQualityMetrics(
                task_name=task_name,
                config=config,
                suite=suite,
                run_name=run_name,
            )

            # Parse stage 1
            metrics.stage1_class = record.get("stage1_class")
            metrics.stage1_reason = record.get("stage1_reason")
            metrics.reward = record.get("reward")

            # Parse stage 2
            metrics.stage2_class = record.get("stage2_class")
            metrics.stage2_reasons = record.get("stage2_reasons", [])

            if metrics.stage1_class == "invalid":
                metrics.add_quality_flag("invalid")

            if metrics.stage2_class == "valid_badsetup":
                metrics.add_quality_flag("bad_setup")

            # Parse stage 3
            stage3 = record.get("stage3")
            if stage3:
                halluc = stage3.get("hallucination")
                if halluc:
                    metrics.hallucination_detected = True
                    metrics.hallucination_precision = halluc.get("precision")
                    metrics.hallucination_recall = halluc.get("recall")
                    metrics.add_quality_flag("hallucination")

                metrics.verifier_flag = stage3.get("verifier_flag", False)
                if metrics.verifier_flag:
                    metrics.add_quality_flag("verifier_flag")

                retrieval = stage3.get("retrieval")
                if retrieval:
                    metrics.retrieval_metrics = retrieval
                    # Flag low retrieval performance
                    file_recall = retrieval.get("file_recall")
                    if file_recall is not None and file_recall < 0.5:
                        metrics.add_quality_flag("low_retrieval_recall")

            key = f"{run_name}/{config}/{task_name}"
            self.metrics_by_task[key] = metrics

    def get_metrics(self, run_name: str, config: str, task_name: str) -> Optional[TraceQualityMetrics]:
        """Get metrics for a specific task."""
        key = f"{run_name}/{config}/{task_name}"
        return self.metrics_by_task.get(key)

    def get_quality_flags(self, run_name: str, config: str, task_name: str) -> list[str]:
        """Get quality flags for a specific task."""
        metrics = self.get_metrics(run_name, config, task_name)
        return metrics.quality_flags if metrics else []

    def has_quality_issues(self, run_name: str, config: str, task_name: str) -> bool:
        """Check if a task has any quality issues."""
        metrics = self.get_metrics(run_name, config, task_name)
        return metrics.is_low_quality() if metrics else False

    def get_summary(self) -> dict:
        """Get summary statistics from pipeline results."""
        if not self.pipeline_results:
            return {}

        return {
            "total_trials": self.pipeline_results.get("total_trials", 0),
            "invalid_count": self.pipeline_results.get("n_invalid", 0),
            "valid_goodsetup_count": self.pipeline_results.get("n_goodsetup", 0),
            "valid_badsetup_count": self.pipeline_results.get("n_badsetup", 0),
            "hallucination_trials": self.pipeline_results.get("n_halluc_trials", 0),
            "verifier_flags": self.pipeline_results.get("n_verifier_flags", 0),
            "average_hallucination_precision": self.pipeline_results.get("avg_hallucination_precision"),
            "average_hallucination_recall": self.pipeline_results.get("avg_hallucination_recall"),
            "average_file_recall": self.pipeline_results.get("avg_file_recall"),
        }

    def export_to_json(self, output_path: Path) -> None:
        """Export metrics to JSON file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "summary": self.get_summary(),
            "metrics": {
                key: metrics.to_dict() for key, metrics in self.metrics_by_task.items()
            },
        }

        output_path.write_text(json.dumps(data, indent=2, default=str) + "\n")

    def iter_low_quality_tasks(self) -> list[tuple[str, TraceQualityMetrics]]:
        """Iterate over tasks with quality issues."""
        return [
            (key, metrics)
            for key, metrics in self.metrics_by_task.items()
            if metrics.is_low_quality()
        ]

    def get_metrics_for_run(self, run_name: str) -> list[TraceQualityMetrics]:
        """Get all metrics for a specific run."""
        return [
            metrics
            for metrics in self.metrics_by_task.values()
            if metrics.run_name == run_name
        ]
