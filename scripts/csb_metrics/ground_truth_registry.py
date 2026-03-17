"""Cached loader for ground truth files across all tasks.

Provides centralized, cached access to oracle answer and ground truth files
to avoid redundant I/O across multiple scripts.
"""

import json
from pathlib import Path
from typing import Any, Optional


class GroundTruthRegistry:
    """Cached loader for ground truth files (oracle_answer.json, ground_truth.json, etc.).

    Maintains a per-instance cache to avoid redundant file reads across
    multiple lookups. Typically used as a singleton or per-run-scan instance.
    """

    def __init__(self, benchmarks_root: Path | str | None = None):
        """Initialize registry.

        Args:
            benchmarks_root: Root directory containing benchmark task directories.
                             If None, inferred as <repo_root>/benchmarks
        """
        if benchmarks_root is None:
            # Infer from script location
            benchmarks_root = Path(__file__).resolve().parent.parent.parent / "benchmarks"
        else:
            benchmarks_root = Path(benchmarks_root)

        self.benchmarks_root = benchmarks_root
        self._oracle_cache: dict[str, Optional[dict]] = {}
        self._ground_truth_cache: dict[str, Optional[dict]] = {}

    def get_oracle_answer(self, task_dir: Path | str) -> Optional[dict]:
        """Load oracle_answer.json for a task, with caching.

        Args:
            task_dir: Path to task directory

        Returns:
            Parsed oracle_answer.json, or None if not found
        """
        task_dir = Path(task_dir)
        cache_key = str(task_dir.absolute())

        if cache_key in self._oracle_cache:
            return self._oracle_cache[cache_key]

        oracle_file = task_dir / "tests" / "oracle_answer.json"
        result = None

        if oracle_file.is_file():
            try:
                result = json.loads(oracle_file.read_text())
            except (json.JSONDecodeError, OSError):
                pass

        self._oracle_cache[cache_key] = result
        return result

    def get_ground_truth(self, task_dir: Path | str) -> Optional[dict]:
        """Load ground_truth.json for a task, with caching.

        Args:
            task_dir: Path to task directory

        Returns:
            Parsed ground_truth.json, or None if not found
        """
        task_dir = Path(task_dir)
        cache_key = str(task_dir.absolute())

        if cache_key in self._ground_truth_cache:
            return self._ground_truth_cache[cache_key]

        ground_truth_file = task_dir / "tests" / "ground_truth.json"
        result = None

        if ground_truth_file.is_file():
            try:
                result = json.loads(ground_truth_file.read_text())
            except (json.JSONDecodeError, OSError):
                pass

        self._ground_truth_cache[cache_key] = result
        return result

    def get_expected_answer(self, task_dir: Path | str) -> Optional[Any]:
        """Get the expected answer from oracle_answer.json.

        Args:
            task_dir: Path to task directory

        Returns:
            The 'answer' field from oracle_answer.json, or None
        """
        oracle = self.get_oracle_answer(task_dir)
        if oracle:
            return oracle.get("answer")
        return None

    def get_ground_truth_files(self, task_dir: Path | str) -> list[str]:
        """Get list of ground truth files from ground_truth.json.

        Args:
            task_dir: Path to task directory

        Returns:
            List of file paths from ground_truth.json['files'], or empty list
        """
        ground_truth = self.get_ground_truth(task_dir)
        if ground_truth and isinstance(ground_truth, dict):
            files = ground_truth.get("files")
            if isinstance(files, list):
                return files
        return []

    def get_answer_type(self, task_dir: Path | str) -> Optional[str]:
        """Get answer type classification from oracle_answer.json.

        Args:
            task_dir: Path to task directory

        Returns:
            Value of 'type' field in oracle_answer.json, or None
        """
        oracle = self.get_oracle_answer(task_dir)
        if oracle:
            return oracle.get("type")
        return None

    def clear_cache(self) -> None:
        """Clear all cached entries."""
        self._oracle_cache.clear()
        self._ground_truth_cache.clear()


# Module-level singleton for convenience
_GLOBAL_REGISTRY: Optional[GroundTruthRegistry] = None


def get_global_registry(benchmarks_root: Path | str | None = None) -> GroundTruthRegistry:
    """Get or create the global GroundTruthRegistry instance.

    Args:
        benchmarks_root: Root directory for benchmarks (only used on first call)

    Returns:
        Cached global registry instance
    """
    global _GLOBAL_REGISTRY
    if _GLOBAL_REGISTRY is None:
        _GLOBAL_REGISTRY = GroundTruthRegistry(benchmarks_root)
    return _GLOBAL_REGISTRY
