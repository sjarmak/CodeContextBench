"""Unified report formatter for standardized output across all report scripts.

Provides consistent structure and multiple output formats for benchmark analysis reports.
"""

import csv
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


@dataclass
class ReportMetadata:
    """Standard metadata for all reports."""

    title: str
    description: str
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    version: str = "1.0"
    author: str = "CodeScaleBench Pipeline"

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ReportSummary:
    """Standard summary statistics for reports."""

    total_items: int = 0
    totals: dict[str, Any] = field(default_factory=dict)  # Suite/config specific totals
    overall_metrics: dict[str, Any] = field(default_factory=dict)  # Key metrics

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ReportFinding:
    """A single finding in a report."""

    category: str  # e.g., "gap", "anomaly", "insight"
    severity: str  # "info" | "warning" | "critical"
    title: str
    description: str
    details: Optional[dict] = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Report:
    """Standard report structure."""

    metadata: ReportMetadata
    summary: ReportSummary
    findings: list[ReportFinding] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)  # Script-specific details

    def add_finding(
        self,
        category: str,
        severity: str,
        title: str,
        description: str,
        details: Optional[dict] = None,
    ):
        """Add a finding to the report."""
        self.findings.append(
            ReportFinding(
                category=category,
                severity=severity,
                title=title,
                description=description,
                details=details,
            )
        )

    def to_dict(self) -> dict:
        """Convert report to dictionary."""
        return {
            "metadata": self.metadata.to_dict(),
            "summary": self.summary.to_dict(),
            "findings": [f.to_dict() for f in self.findings],
            "details": self.details,
        }


class ReportFormatter:
    """Formats reports in various output styles."""

    def __init__(self, report: Report):
        """Initialize formatter with a report."""
        self.report = report

    def to_json(self, indent: int = 2) -> str:
        """Format report as JSON."""
        return json.dumps(self.report.to_dict(), indent=indent, default=str)

    def to_markdown(self) -> str:
        """Format report as markdown."""
        lines = []

        # Title and metadata
        lines.append(f"# {self.report.metadata.title}\n")
        lines.append(f"**Description:** {self.report.metadata.description}\n")
        lines.append(
            f"**Generated:** {self.report.metadata.generated_at} | "
            f"**Version:** {self.report.metadata.version}\n"
        )

        # Summary section
        lines.append("\n## Summary\n")
        summary = self.report.summary
        lines.append(f"- **Total Items:** {summary.total_items}\n")

        if summary.overall_metrics:
            lines.append("### Overall Metrics\n")
            for key, value in summary.overall_metrics.items():
                if isinstance(value, float):
                    lines.append(f"- **{key}:** {value:.2f}\n")
                else:
                    lines.append(f"- **{key}:** {value}\n")

        # Findings section
        if self.report.findings:
            lines.append("\n## Findings\n")

            # Group by severity
            by_severity = {}
            for finding in self.report.findings:
                if finding.severity not in by_severity:
                    by_severity[finding.severity] = []
                by_severity[finding.severity].append(finding)

            severity_order = ["critical", "warning", "info"]
            for severity in severity_order:
                if severity in by_severity:
                    lines.append(f"\n### {severity.upper()}\n")
                    for finding in by_severity[severity]:
                        lines.append(f"**{finding.title}** ({finding.category})\n")
                        lines.append(f"> {finding.description}\n")
                        if finding.details:
                            lines.append("```json\n")
                            lines.append(json.dumps(finding.details, indent=2))
                            lines.append("\n```\n")

        return "".join(lines)

    def to_csv(
        self,
        row_name: str = "name",
        columns: Optional[list[str]] = None,
    ) -> str:
        """Format report as CSV.

        Args:
            row_name: Column name for row identifiers
            columns: List of column names to include (defaults to all in details)

        Returns:
            CSV string
        """
        if not self.report.details:
            return ""

        # Determine columns
        if columns is None:
            if isinstance(self.report.details, dict):
                # Get all keys from first-level values
                all_keys = set()
                for v in self.report.details.values():
                    if isinstance(v, dict):
                        all_keys.update(v.keys())
                columns = sorted(all_keys)
            else:
                return ""

        # Build CSV
        lines = []
        header = [row_name] + columns
        lines.append(",".join(header))

        for name, row_data in self.report.details.items():
            if not isinstance(row_data, dict):
                continue

            row = [name]
            for col in columns:
                value = row_data.get(col, "")
                # Escape CSV values
                if isinstance(value, str):
                    escaped = value.replace('"', '""')
                    value = f'"{escaped}"'
                else:
                    value = str(value)
                row.append(value)

            lines.append(",".join(row))

        return "\n".join(lines)

    def to_table(
        self,
        row_name: str = "name",
        columns: Optional[list[str]] = None,
    ) -> str:
        """Format report as ASCII table.

        Args:
            row_name: Column name for row identifiers
            columns: List of column names to include (defaults to all in details)

        Returns:
            Formatted table string
        """
        if not self.report.details:
            return ""

        # Determine columns
        if columns is None:
            if isinstance(self.report.details, dict):
                all_keys = set()
                for v in self.report.details.values():
                    if isinstance(v, dict):
                        all_keys.update(v.keys())
                columns = sorted(all_keys)
            else:
                return ""

        # Calculate column widths
        col_widths = {row_name: len(row_name)}
        for col in columns:
            col_widths[col] = len(str(col))

        for row_data in self.report.details.values():
            if isinstance(row_data, dict):
                for col in columns:
                    value = str(row_data.get(col, ""))
                    col_widths[col] = max(col_widths[col], len(value))

        # Build table
        lines = []

        # Header
        header_parts = [row_name.ljust(col_widths[row_name])]
        for col in columns:
            header_parts.append(str(col).ljust(col_widths[col]))
        header = "  ".join(header_parts)
        lines.append(header)

        # Separator
        separator_parts = ["-" * col_widths[row_name]]
        for col in columns:
            separator_parts.append("-" * col_widths[col])
        lines.append("  ".join(separator_parts))

        # Rows
        for name, row_data in self.report.details.items():
            if not isinstance(row_data, dict):
                continue

            row_parts = [str(name).ljust(col_widths[row_name])]
            for col in columns:
                value = str(row_data.get(col, ""))
                row_parts.append(value.ljust(col_widths[col]))

            lines.append("  ".join(row_parts))

        return "\n".join(lines)

    def save(
        self,
        output_path: Path,
        format: str = "json",
        **format_kwargs,
    ) -> None:
        """Save report to file.

        Args:
            output_path: Path to save report
            format: Output format ('json', 'markdown', 'csv', 'table')
            **format_kwargs: Additional arguments for format-specific methods
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if format == "json":
            content = self.to_json()
        elif format == "markdown":
            content = self.to_markdown()
        elif format == "csv":
            content = self.to_csv(**format_kwargs)
        elif format == "table":
            content = self.to_table(**format_kwargs)
        else:
            raise ValueError(f"Unsupported format: {format}")

        output_path.write_text(content)

    def print(self, format: str = "markdown") -> None:
        """Print report to stdout.

        Args:
            format: Output format ('json', 'markdown', 'csv', 'table')
        """
        if format == "json":
            print(self.to_json())
        elif format == "markdown":
            print(self.to_markdown())
        elif format == "csv":
            print(self.to_csv())
        elif format == "table":
            print(self.to_table())
        else:
            raise ValueError(f"Unsupported format: {format}")
