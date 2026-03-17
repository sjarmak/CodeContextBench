"""Unified run/task directory scanner with consistent filtering and iteration.

Provides a single abstraction for discovering and filtering task directories
across different benchmark suites and run layouts.
"""

from pathlib import Path
from typing import Callable, Optional

from csb_metrics.result_parser import ResultParser


class RunScanner:
    """Unified scanner for task directories in a run with consistent filtering.

    Handles:
    - Discovering task directories across different layouts
    - Filtering by suite, task name, or custom predicates
    - Accessing result.json for each task
    - Optional result validation
    """

    def __init__(self, run_dir: Path | str, validate_results: bool = False):
        """Initialize scanner for a run directory.

        Args:
            run_dir: Root directory of a benchmark run
            validate_results: If True, only yield tasks with valid result.json files
        """
        self.run_dir = Path(run_dir)
        self.validate_results = validate_results

        if not self.run_dir.is_dir():
            raise ValueError(f"Run directory not found: {self.run_dir}")

    def iter_task_dirs(
        self,
        suite_filter: Optional[str] = None,
        task_name_filter: Optional[Callable[[str], bool]] = None,
        config_filter: Optional[Callable[[str], bool]] = None,
    ) -> list[Path]:
        """Discover task directories matching optional filters.

        Args:
            suite_filter: If provided, only include tasks from this suite
            task_name_filter: Optional predicate for task names
            config_filter: Optional predicate for config names

        Returns:
            List of task directory paths matching filters
        """
        from maintenance.config_utils import detect_suite

        task_dirs = []

        # Find all result.json files in the run
        for result_file in sorted(self.run_dir.rglob("result.json")):
            task_dir = result_file.parent

            # Validate if requested
            if self.validate_results:
                try:
                    parser = ResultParser(result_file)
                    if not parser.is_valid_trial:
                        continue
                except (ValueError, FileNotFoundError):
                    continue

            # Apply suite filter
            if suite_filter:
                detected_suite = detect_suite(task_dir.name)
                if detected_suite != suite_filter:
                    continue

            # Apply config filter
            if config_filter:
                # Infer config name from path (config_name/.../ structure)
                rel_parts = task_dir.relative_to(self.run_dir).parts
                config_name = rel_parts[0] if rel_parts else ""
                if not config_filter(config_name):
                    continue

            # Apply task name filter
            if task_name_filter:
                task_name = task_dir.name
                if not task_name_filter(task_name):
                    continue

            task_dirs.append(task_dir)

        return task_dirs

    def iter_with_results(
        self,
        suite_filter: Optional[str] = None,
        task_name_filter: Optional[Callable[[str], bool]] = None,
        config_filter: Optional[Callable[[str], bool]] = None,
    ) -> list[tuple[Path, ResultParser]]:
        """Discover task directories and yield with parsed results.

        Args:
            suite_filter: If provided, only include tasks from this suite
            task_name_filter: Optional predicate for task names
            config_filter: Optional predicate for config names

        Returns:
            List of (task_dir, result_parser) tuples
        """
        task_dirs = self.iter_task_dirs(
            suite_filter=suite_filter,
            task_name_filter=task_name_filter,
            config_filter=config_filter,
        )

        results = []
        for task_dir in task_dirs:
            result_file = task_dir / "result.json"
            try:
                parser = ResultParser(result_file)
                if self.validate_results and not parser.is_valid_trial:
                    continue
                results.append((task_dir, parser))
            except (ValueError, FileNotFoundError):
                continue

        return results

    def count_tasks(
        self,
        suite_filter: Optional[str] = None,
        task_name_filter: Optional[Callable[[str], bool]] = None,
    ) -> int:
        """Count total tasks matching filters.

        Args:
            suite_filter: If provided, only count tasks from this suite
            task_name_filter: Optional predicate for task names

        Returns:
            Number of matching tasks
        """
        return len(
            self.iter_task_dirs(
                suite_filter=suite_filter, task_name_filter=task_name_filter
            )
        )

    def group_by_suite(self) -> dict[str, list[Path]]:
        """Group task directories by suite.

        Returns:
            Dict mapping suite names to lists of task directories
        """
        from maintenance.config_utils import detect_suite

        groups = {}
        for task_dir in self.iter_task_dirs():
            suite = detect_suite(task_dir.name) or "unknown"
            if suite not in groups:
                groups[suite] = []
            groups[suite].append(task_dir)

        return groups

    def group_by_config(self) -> dict[str, list[Path]]:
        """Group task directories by config.

        Returns:
            Dict mapping config names to lists of task directories
        """
        groups = {}
        for task_dir in self.iter_task_dirs():
            rel_parts = task_dir.relative_to(self.run_dir).parts
            config_name = rel_parts[0] if rel_parts else "unknown"
            if config_name not in groups:
                groups[config_name] = []
            groups[config_name].append(task_dir)

        return groups
