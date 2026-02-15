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


def _gt_crossrepo(task_dir: Path) -> Optional[TaskGroundTruth]:
    """Parse tests/expected_changes.json for CrossRepo tasks."""
    ec = task_dir / "tests" / "expected_changes.json"
    if not ec.is_file():
        return None
    try:
        data = json.loads(ec.read_text(errors="replace"))
    except (json.JSONDecodeError, OSError):
        return None
    files = data.get("expected_files", [])
    if files and isinstance(files, list):
        return TaskGroundTruth(
            task_id=task_dir.name,
            benchmark="ccb_crossrepo",
            files=[f for f in files if isinstance(f, str)],
            source="expected_changes_json",
            confidence="high",
        )
    return None


def _gt_repoqa(task_dir: Path) -> Optional[TaskGroundTruth]:
    """Parse tests/ground_truth.json for RepoQA tasks (single function target)."""
    gt = task_dir / "tests" / "ground_truth.json"
    if not gt.is_file():
        return None
    try:
        data = json.loads(gt.read_text(errors="replace"))
    except (json.JSONDecodeError, OSError):
        return None
    canonical_path = data.get("canonical_path", "")
    if canonical_path:
        return TaskGroundTruth(
            task_id=task_dir.name,
            benchmark="ccb_repoqa",
            files=[canonical_path],
            source="ground_truth_json",
            confidence="high",
        )
    return None


def _gt_sweperf(task_dir: Path) -> Optional[TaskGroundTruth]:
    """Parse tests/ground_truth.json for SWE-Perf tasks (target function file)."""
    gt = task_dir / "tests" / "ground_truth.json"
    if not gt.is_file():
        return None
    try:
        data = json.loads(gt.read_text(errors="replace"))
    except (json.JSONDecodeError, OSError):
        return None
    file_path = data.get("file_path", "")
    if file_path:
        return TaskGroundTruth(
            task_id=task_dir.name,
            benchmark="ccb_sweperf",
            files=[file_path],
            source="ground_truth_json",
            confidence="low",  # Agent may modify additional files beyond target
        )
    return None


def _gt_dibench(task_dir: Path) -> Optional[TaskGroundTruth]:
    """Parse tests/instance.json for DIBench tasks (build file to edit)."""
    instance = task_dir / "tests" / "instance.json"
    if not instance.is_file():
        return None
    try:
        data = json.loads(instance.read_text(errors="replace"))
    except (json.JSONDecodeError, OSError):
        return None
    build_files = data.get("build_files", [])
    if build_files and isinstance(build_files, list):
        files = [f for f in build_files if isinstance(f, str)]
        if files:
            return TaskGroundTruth(
                task_id=task_dir.name,
                benchmark="ccb_dibench",
                files=files,
                source="instance_json",
                confidence="high",
            )
    return None


def _gt_tac(task_dir: Path) -> Optional[TaskGroundTruth]:
    """Extract ground truth from TAC task instructions.

    TAC tasks have black-box evaluation inside Docker images, so we extract
    target files from instruction.md. Different task types have different
    approaches:
    - Implementation tasks: explicit file paths in instruction
    - Search tasks: no files to modify (returns None)
    - Dependency tasks: pyproject.toml / myenv.txt
    """
    instruction = task_dir / "instruction.md"
    if not instruction.is_file():
        return None

    text = instruction.read_text(errors="replace")
    task_name = task_dir.name

    # --- Hardcoded ground truth for known TAC tasks ---
    # These are extracted from instruction.md analysis. TAC evaluators are
    # encrypted inside Docker images so we can't auto-extract.
    _TAC_GROUND_TRUTH: dict[str, tuple[list[str], str]] = {
        # Implementation tasks: files explicitly listed in instruction
        "tac-implement-hyperloglog": (
            [
                "src/include/primer/hyperloglog.h",
                "src/include/primer/hyperloglog_presto.h",
                "src/primer/hyperloglog.cpp",
                "src/primer/hyperloglog_presto.cpp",
                "src/include/common/util/hash_util.h",
            ],
            "high",
        ),
        # Buffer pool manager: issue-based, files not explicitly listed
        "tac-buffer-pool-manager": (
            [
                "src/include/buffer/buffer_pool_manager.h",
                "src/buffer/buffer_pool_manager.cpp",
                "src/include/buffer/lru_k_replacer.h",
                "src/buffer/lru_k_replacer.cpp",
            ],
            "medium",  # Inferred from bustub project structure
        ),
        # Unit test writing: single explicit target file
        "tac-write-unit-test": (
            ["tests/unit/test_agent_skill.py"],
            "high",
        ),
        # Dependency change: explicit files
        "tac-dependency-change": (
            ["pyproject.toml", "poetry.lock"],
            "high",
        ),
        # API endpoint: inferred from task pattern
        "tac-copilot-arena-endpoint": (
            ["app.py"],
            "medium",
        ),
        # Troubleshooting: explicit file
        "tac-troubleshoot-dev-setup": (
            ["myenv.txt"],
            "high",
        ),
        # Search/navigation tasks: no files to modify
        # tac-find-in-codebase-1: RocketChat message only
        # tac-find-in-codebase-2: RocketChat message only
    }

    if task_name in _TAC_GROUND_TRUTH:
        files, confidence = _TAC_GROUND_TRUTH[task_name]
        return TaskGroundTruth(
            task_id=task_name,
            benchmark="ccb_tac",
            files=files,
            source="instruction_manual",
            confidence=confidence,
        )
    return None


def _gt_largerepo(task_dir: Path) -> Optional[TaskGroundTruth]:
    """Extract ground truth for LargeRepo tasks.

    Uses instruction.md analysis + trajectory mining from passing agent runs.
    LargeRepo tasks are open-ended feature implementations, so ground truth
    is approximate — based on what areas of code need modification.
    """
    task_name = task_dir.name

    # --- Ground truth mined from passing agent runs + instruction analysis ---
    # big-code-trt-001: 2 passing runs (reward=1.0), files from git diff
    # big-code-k8s-001: partial pass (reward=0.7), files from instruction + run
    # big-code-servo-001: no passing runs, files from instruction analysis
    # big-code-vsc-001: handled by fallback (test_script extraction)
    _LARGEREPO_GROUND_TRUTH: dict[str, tuple[list[str], str, str]] = {
        # TensorRT-LLM: mined from 2 passing runs (baseline + SG_full)
        "big-code-trt-001": (
            [
                "cpp/include/tensorrt_llm/common/quantization.h",
                "tensorrt_llm/quantization/mode.py",
                "tensorrt_llm/_torch/modules/fused_moe/fused_moe_trtllm_gen.py",
                "tensorrt_llm/_torch/modules/fused_moe/interface.py",
                "tensorrt_llm/_torch/modules/fused_moe/fused_moe_cutlass.py",
                "tensorrt_llm/quantization/utils/fp4_utils.py",
            ],
            "trajectory_mining",
            "high",  # Common files across 2 independent passing runs
        ),
        # Kubernetes: from instruction + partial-pass run analysis
        "big-code-k8s-001": (
            [
                "staging/src/k8s.io/api/core/v1/types.go",
                "pkg/apis/core/types.go",
                "pkg/scheduler/eventhandlers.go",
                "pkg/controller/tainteviction/taint_eviction.go",
                "staging/src/k8s.io/endpointslice/reconciler.go",
            ],
            "instruction_and_run",
            "medium",  # Partial pass only; may need more files
        ),
        # Servo: from instruction analysis only (no passing runs)
        "big-code-servo-001": (
            [
                "components/script/dom/document.rs",
                "components/script/dom/window.rs",
                "components/script/dom/element.rs",
                "components/script/dom/event.rs",
            ],
            "instruction",
            "low",  # No passing runs; inferred from scroll/DOM architecture
        ),
    }

    if task_name in _LARGEREPO_GROUND_TRUTH:
        files, source, confidence = _LARGEREPO_GROUND_TRUTH[task_name]
        return TaskGroundTruth(
            task_id=task_name,
            benchmark="ccb_largerepo",
            files=files,
            source=source,
            confidence=confidence,
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
    "ccb_crossrepo": _gt_crossrepo,
    "ccb_repoqa": _gt_repoqa,
    "ccb_sweperf": _gt_sweperf,
    "ccb_dibench": _gt_dibench,
    "ccb_tac": _gt_tac,
    "ccb_largerepo": _gt_largerepo,
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

    # Build list of candidate task_id variants to try
    candidates = [task_id]
    # __ → - normalization (swebenchpro task_ids use __ but dirs use -)
    norm = task_id.replace("__", "-")
    if norm != task_id:
        candidates.append(norm)
    # Strip ccb_ prefix (repoqa/sweperf/dibench task_ids have ccb_ but dirs don't)
    if task_id.startswith("ccb_"):
        candidates.append(task_id[4:])
    # Strip benchmark prefix from task_id (e.g. ccb_dibench-foo → dibench-foo)
    for prefix in ("ccb_dibench-", "ccb_tac-", "ccb_largerepo-"):
        if task_id.startswith(prefix):
            stripped = task_id[len("ccb_"):]  # e.g. dibench-foo
            if stripped not in candidates:
                candidates.append(stripped)

    # Try direct path with all candidates
    for cand in candidates[1:]:  # skip first (already tried above)
        direct_cand = benchmarks_dir / benchmark / cand
        if direct_cand.is_dir():
            return direct_cand

    # Benchmarks with tasks/ subdirectory (swebenchpro, repoqa, sweperf, etc.)
    tasks_subdir = benchmarks_dir / benchmark / "tasks"
    if tasks_subdir.is_dir():
        for cand in candidates:
            for d in tasks_subdir.iterdir():
                if d.is_dir() and (d.name == cand or d.name.startswith(cand)):
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
