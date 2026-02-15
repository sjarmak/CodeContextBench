"""Ground truth file extraction for CodeContextBench tasks.

Extracts the set of files that need modification for each task, using
benchmark-specific strategies. Results cached in configs/ground_truth_files.json.

Ported from IR-SDLC-Factory/app/ir_sdlc/ground_truth_extraction.py, adapted
for CCB's benchmark-specific task formats. Uses simple file-level paths
(list[str]) instead of the CodeLocation/GroundTruth hierarchy.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class TaskGroundTruth:
    """Ground truth files for a single benchmark task."""

    task_id: str
    benchmark: str
    files: list[str]        # repo-relative paths needing modification
    source: str             # "patch" | "diff" | "ground_truth_dir" | "test_script" | "instruction"
    confidence: str         # "high" | "medium" | "low"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "TaskGroundTruth":
        return cls(**d)


# ---------------------------------------------------------------------------
# Per-benchmark extraction strategies
# ---------------------------------------------------------------------------

_DIFF_HEADER_RE = re.compile(r"^(?:diff --git a/.+ b/|[\+]{3} b/)(.+)$", re.MULTILINE)
_DIFF_MINUS_RE = re.compile(r"^--- a/(.+)$", re.MULTILINE)


def _files_from_patch(text: str) -> list[str]:
    """Extract file paths from unified diff / git-format patch text."""
    files: list[str] = []
    seen: set[str] = set()
    for m in _DIFF_HEADER_RE.finditer(text):
        path = m.group(1).strip()
        if path and path not in seen:
            seen.add(path)
            files.append(path)
    # Fallback: --- a/path lines
    for m in _DIFF_MINUS_RE.finditer(text):
        path = m.group(1).strip()
        if path and path not in seen and path != "/dev/null":
            seen.add(path)
            files.append(path)
    return files


def _gt_swebenchpro(task_dir: Path) -> Optional[TaskGroundTruth]:
    """Parse solve.sh gold patch for SWE-bench Pro tasks."""
    for rel in ("solution/solve.sh", "environment/solve.sh"):
        solve = task_dir / rel
        if solve.is_file():
            text = solve.read_text(errors="replace")
            files = _files_from_patch(text)
            if files:
                return TaskGroundTruth(
                    task_id=task_dir.name,
                    benchmark="ccb_swebenchpro",
                    files=files,
                    source="patch",
                    confidence="high",
                )
    return None


def _gt_pytorch(task_dir: Path) -> Optional[TaskGroundTruth]:
    """Parse expected.diff or instruction.md diff blocks for PyTorch tasks."""
    # Try explicit diff file first
    for name in ("tests/expected.diff", "tests/expected.patch"):
        diff_file = task_dir / name
        if diff_file.is_file():
            files = _files_from_patch(diff_file.read_text(errors="replace"))
            if files:
                return TaskGroundTruth(
                    task_id=task_dir.name,
                    benchmark="ccb_pytorch",
                    files=files,
                    source="diff",
                    confidence="high",
                )

    # Fallback: parse diff blocks in instruction.md
    instruction = task_dir / "instruction.md"
    if instruction.is_file():
        text = instruction.read_text(errors="replace")
        files = _files_from_patch(text)
        if files:
            return TaskGroundTruth(
                task_id=task_dir.name,
                benchmark="ccb_pytorch",
                files=files,
                source="diff",
                confidence="high",
            )
    return None


def _gt_k8s_docs(task_dir: Path) -> Optional[TaskGroundTruth]:
    """Read ground_truth/ directory listing for K8s Docs tasks."""
    gt_dir = task_dir / "ground_truth"
    if gt_dir.is_dir():
        files = [
            f.name for f in sorted(gt_dir.iterdir())
            if f.is_file() and not f.name.startswith(".")
        ]
        if files:
            return TaskGroundTruth(
                task_id=task_dir.name,
                benchmark="ccb_k8sdocs",
                files=files,
                source="ground_truth_dir",
                confidence="high",
            )
    return None


# File-path regex: matches paths like src/foo/bar.py, lib/utils.ts, etc.
_FILE_PATH_RE = re.compile(
    r"(?:^|[\s`\"'])("
    r"(?:src|lib|pkg|app|cmd|internal|test|tests|scripts|config|docs|benchmarks)"
    r"/[a-zA-Z0-9_/.-]+\.[a-zA-Z]{1,10}"
    r")(?:[\s`\"':]|$)",
    re.MULTILINE,
)

# Broader pattern: any path with / and extension
_GENERIC_PATH_RE = re.compile(
    r"(?:^|[\s`\"'])([a-zA-Z0-9_][a-zA-Z0-9_/.-]+/[a-zA-Z0-9_.-]+\.[a-zA-Z]{1,10})(?:[\s`\"':#,]|$)",
    re.MULTILINE,
)


def _gt_from_test_script(task_dir: Path) -> Optional[TaskGroundTruth]:
    """Parse tests/test.sh for file path references."""
    test_sh = task_dir / "tests" / "test.sh"
    if not test_sh.is_file():
        return None

    text = test_sh.read_text(errors="replace")
    paths: list[str] = []
    seen: set[str] = set()

    for regex in (_FILE_PATH_RE, _GENERIC_PATH_RE):
        for m in regex.finditer(text):
            path = m.group(1).strip().strip("'\"`)(`")
            # Filter out common false positives
            if (
                path not in seen
                and not path.startswith("http")
                and not path.startswith("/usr/")
                and not path.startswith("/bin/")
                and not path.startswith("/tmp/")
                and "node_modules" not in path
                and ".lock" not in path
            ):
                seen.add(path)
                paths.append(path)

    if paths:
        return TaskGroundTruth(
            task_id=task_dir.name,
            benchmark="",  # filled by caller
            files=paths,
            source="test_script",
            confidence="medium",
        )
    return None


def _gt_from_instruction(task_dir: Path) -> Optional[TaskGroundTruth]:
    """Regex-extract file paths from instruction.md."""
    instruction = task_dir / "instruction.md"
    if not instruction.is_file():
        return None

    text = instruction.read_text(errors="replace")
    paths: list[str] = []
    seen: set[str] = set()

    for regex in (_FILE_PATH_RE, _GENERIC_PATH_RE):
        for m in regex.finditer(text):
            path = m.group(1).strip().strip("'\"`)(`")
            if (
                path not in seen
                and not path.startswith("http")
                and not path.startswith("/usr/")
                and not path.startswith("/bin/")
                and not path.startswith("/tmp/")
                and "node_modules" not in path
                and ".lock" not in path
            ):
                seen.add(path)
                paths.append(path)

    if paths:
        return TaskGroundTruth(
            task_id=task_dir.name,
            benchmark="",  # filled by caller
            files=paths,
            source="instruction",
            confidence="low",
        )
    return None


# ---------------------------------------------------------------------------
# Strategy dispatch
# ---------------------------------------------------------------------------

_BENCHMARK_STRATEGIES = {
    "ccb_swebenchpro": _gt_swebenchpro,
    "ccb_pytorch": _gt_pytorch,
    "ccb_k8sdocs": _gt_k8s_docs,
}


def extract_ground_truth(
    task_id: str,
    benchmark: str,
    task_dir: Path,
) -> Optional[TaskGroundTruth]:
    """Extract ground truth files for a single task.

    Tries benchmark-specific strategy first, then falls back to
    test_script → instruction parsing.
    """
    if not task_dir.is_dir():
        return None

    # Benchmark-specific strategy
    strategy = _BENCHMARK_STRATEGIES.get(benchmark)
    if strategy:
        gt = strategy(task_dir)
        if gt:
            gt.task_id = task_id
            gt.benchmark = benchmark
            return gt

    # Fallback chain
    for fallback in (_gt_from_test_script, _gt_from_instruction):
        gt = fallback(task_dir)
        if gt:
            gt.task_id = task_id
            gt.benchmark = benchmark
            return gt

    return None


# ---------------------------------------------------------------------------
# Registry builder
# ---------------------------------------------------------------------------

def build_ground_truth_registry(
    benchmarks_dir: Path,
    selected_tasks: list[dict],
) -> dict[str, TaskGroundTruth]:
    """Build ground truth for all selected tasks.

    Args:
        benchmarks_dir: Path to benchmarks/ directory.
        selected_tasks: List of task dicts from selected_benchmark_tasks.json,
            each with at least 'task_id' and 'benchmark' keys.

    Returns:
        Dict mapping task_id → TaskGroundTruth.
    """
    registry: dict[str, TaskGroundTruth] = {}

    for task_meta in selected_tasks:
        task_id = task_meta.get("task_id", "")
        benchmark = task_meta.get("benchmark", "")
        if not task_id or not benchmark:
            continue

        # Resolve task directory
        task_dir = _resolve_task_dir(benchmarks_dir, benchmark, task_id)
        if task_dir is None:
            continue

        gt = extract_ground_truth(task_id, benchmark, task_dir)
        if gt:
            registry[task_id] = gt

    return registry


def _resolve_task_dir(
    benchmarks_dir: Path,
    benchmark: str,
    task_id: str,
) -> Optional[Path]:
    """Find the on-disk task directory for a given task.

    Handles varying layouts:
      - benchmarks/<benchmark>/<task_id>/       (standard)
      - benchmarks/<benchmark>/tasks/<prefix>/  (swebenchpro)
    """
    # Standard layout
    direct = benchmarks_dir / benchmark / task_id
    if direct.is_dir():
        return direct

    # SWE-bench Pro: tasks/<instance_*>/
    tasks_subdir = benchmarks_dir / benchmark / "tasks"
    if tasks_subdir.is_dir():
        # task_id may be a prefix of the directory name
        for d in tasks_subdir.iterdir():
            if d.is_dir() and (d.name == task_id or d.name.startswith(task_id)):
                return d

    return None


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

def save_registry(
    registry: dict[str, TaskGroundTruth],
    path: Path,
) -> None:
    """Write registry to JSON."""
    data = {tid: gt.to_dict() for tid, gt in registry.items()}
    path.write_text(json.dumps(data, indent=2) + "\n")


def load_registry(path: Path) -> dict[str, TaskGroundTruth]:
    """Load registry from JSON."""
    if not path.is_file():
        return {}
    raw = json.loads(path.read_text())
    return {tid: TaskGroundTruth.from_dict(d) for tid, d in raw.items()}
