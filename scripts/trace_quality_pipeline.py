#!/usr/bin/env python3
"""Trace classification and quality analysis pipeline for CodeScaleBench.

Classifies every trial directory in runs/official/ (and optionally runs/staging/)
into valid/invalid, checks setup quality, and performs quality analysis.

Three stages:
  1. Valid/Invalid classification (infrastructure failure detection)
  2. Setup quality (preamble, MCP config correctness)
  3. Quality analysis (hallucination, retrieval quality, verifier false negatives)

Usage:
    python3 scripts/trace_quality_pipeline.py
    python3 scripts/trace_quality_pipeline.py --include-staging
    python3 scripts/trace_quality_pipeline.py --stage 1 --verbose
    python3 scripts/trace_quality_pipeline.py --output /tmp/report.json
"""

import argparse
import json
import re
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

# ---------------------------------------------------------------------------
# Import existing modules (with fallbacks)
# ---------------------------------------------------------------------------

try:
    from aggregate_status import (
        _iter_task_dirs, detect_suite, should_skip, DIR_PREFIX_TO_SUITE,
        _extract_task_name, _extract_reward,
    )
except ImportError:
    # Inline fallbacks
    SKIP_PATTERNS = ["__broken_verifier", "validation_test", "archive", "__v1_hinted", "__aborted"]

    def should_skip(dirname: str) -> bool:
        return any(pat in dirname for pat in SKIP_PATTERNS)

    DIR_PREFIX_TO_SUITE = {}  # will be populated if needed

    def detect_suite(dirname: str) -> Optional[str]:
        return None

    def _extract_task_name(dirname: str) -> str:
        parts = dirname.rsplit("__", 1)
        return parts[0] if len(parts) == 2 else dirname

    def _extract_reward(data: dict) -> Optional[float]:
        verifier = data.get("verifier_result") or {}
        rewards = verifier.get("rewards") or {}
        reward = rewards.get("reward")
        if reward is None:
            reward = rewards.get("score")
        if reward is not None:
            return float(reward)
        return None

    def _iter_task_dirs(config_path: Path):
        if not config_path.is_dir():
            return
        for entry in sorted(config_path.iterdir()):
            if not entry.is_dir() or should_skip(entry.name):
                continue
            if entry.name.startswith("20"):
                for trial_dir in sorted(entry.iterdir()):
                    if trial_dir.is_dir() and not trial_dir.name.startswith("20") and not should_skip(trial_dir.name):
                        yield trial_dir
            elif "__" in entry.name:
                yield entry
            elif entry.name.startswith(("ccb_", "csb_")):
                for trial_dir in sorted(entry.iterdir()):
                    if trial_dir.is_dir() and not should_skip(trial_dir.name):
                        yield trial_dir

try:
    from status_fingerprints import fingerprint_error
except ImportError:
    def fingerprint_error(exception_info):
        return {"fingerprint_id": "unknown", "label": "Unknown", "severity": "unknown"}

# NOTE: We intentionally do NOT import scan_transcript from audit_traces.py.
# It reads entire transcript files line-by-line which is too slow for 5000+ trials.
# We use a lightweight MCP detection approach instead.

try:
    from config_utils import is_mcp_config, discover_configs, is_config_dir
except ImportError:
    def is_mcp_config(config_name: str) -> bool:
        return config_name.startswith("mcp-") or config_name in {
            "sourcegraph_full", "sourcegraph_base", "sourcegraph_isolated",
            "sourcegraph", "artifact_full", "deepsearch",
        }

    def discover_configs(run_dir: Path) -> list[str]:
        if not run_dir.is_dir():
            return []
        configs = []
        for child in run_dir.iterdir():
            if child.is_dir() and not child.name.startswith(("archive", "20", ".")):
                configs.append(child.name)
        return sorted(configs)

    def is_config_dir(name: str) -> bool:
        return True

# MCP tool detection regex (from audit_traces.py)
MCP_TOOL_USE_RE = re.compile(r'"name"\s*:\s*"mcp__sourcegraph__(?:sg_)?(\w+)"')

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

RUNS_DIR_OFFICIAL = PROJECT_ROOT / "runs" / "official"
RUNS_DIR_STAGING = PROJECT_ROOT / "runs" / "staging"
BENCHMARKS_DIRS = [
    PROJECT_ROOT / "benchmarks",
    PROJECT_ROOT / "sourcegraph_benchmarks",
]

V5_PREAMBLE_MARKER = "IMPORTANT: Source Code Access"
SG_MIRROR_MARKER = "sg-evals/"


# ---------------------------------------------------------------------------
# Ground truth loading
# ---------------------------------------------------------------------------

_GT_CACHE: dict[str, list[str]] = {}


def _normalize_task_name(raw_name: str) -> str:
    """Strip config prefixes and Harbor random suffixes from trial names.

    Examples:
        sgonly_CCX-crossorg-280__abc123  -> CCX-crossorg-280
        bl_CCX-compliance-124_QApFIR     -> CCX-compliance-124
        mcp_k8s-noschedule-taint-feature-001__xyz  -> k8s-noschedule-taint-feature-001
    """
    name = raw_name
    # Strip config prefixes
    for prefix in ("sgonly_", "bl_", "mcp_", "baseline_"):
        if name.startswith(prefix):
            name = name[len(prefix):]
            break
    # Strip Harbor random suffix (__XXXXXXX)
    parts = name.rsplit("__", 1)
    if len(parts) == 2 and len(parts[1]) <= 8 and parts[1].isalnum():
        name = parts[0]
    # Strip Harbor hash-like suffixes from task names (_XXXXXXX at end)
    parts = name.rsplit("_", 1)
    if len(parts) == 2 and 4 <= len(parts[1]) <= 8 and parts[1].isalnum() and not parts[1].isdigit():
        # Only strip if it looks like a random suffix (mixed case, not a pure number like -001)
        name = parts[0]
    return name


def _load_ground_truth(task_name: str) -> Optional[list[str]]:
    """Load oracle ground truth files for a task. Returns list of file paths or None."""
    clean_name = _normalize_task_name(task_name)
    if clean_name in _GT_CACHE:
        return _GT_CACHE[clean_name]

    # Try exact name first, then normalized name
    candidates = [clean_name]
    if clean_name != task_name:
        candidates.append(task_name)

    for bench_root in BENCHMARKS_DIRS:
        if not bench_root.is_dir():
            continue
        for suite_dir in bench_root.iterdir():
            if not suite_dir.is_dir():
                continue
            for name in candidates:
                # Try exact match first, then case-insensitive
                task_dir = suite_dir / name
                if not task_dir.is_dir():
                    # Case-insensitive fallback
                    lower_name = name.lower()
                    for entry in suite_dir.iterdir():
                        if entry.is_dir() and entry.name.lower() == lower_name:
                            task_dir = entry
                            break
                    else:
                        continue
                if not task_dir.is_dir():
                    continue
                # Try oracle_answer.json first, then ground_truth.json
                for gt_name in ("oracle_answer.json", "ground_truth.json"):
                    gt_path = task_dir / "tests" / gt_name
                    if gt_path.is_file():
                        try:
                            data = json.loads(gt_path.read_text())
                            raw_files = data.get("files", [])
                            if isinstance(raw_files, list) and raw_files:
                                files = []
                                for f in raw_files:
                                    if isinstance(f, str):
                                        files.append(f)
                                    elif isinstance(f, dict):
                                        fp = f.get("file", f.get("path", ""))
                                        if fp:
                                            files.append(fp)
                                if files:
                                    _GT_CACHE[clean_name] = files
                                    return files
                        except (json.JSONDecodeError, OSError):
                            pass
    _GT_CACHE[clean_name] = None
    return None


def _parse_verifier_debug(task_dir: Path) -> Optional[dict]:
    """Parse file comparison data from test-stdout.txt.

    Supports two formats:
    1. Text DEBUG line: DEBUG: agent_files=31, oracle_files=21, overlap=17, F1=0.6538, sym_score=0.8333
    2. JSON checks format: {"checks": {"file_set_match": {"recall": 0.5, "precision": 0.29, "f1": 0.36, ...}}}

    Returns dict with parsed values or None.
    """
    stdout_path = task_dir / "verifier" / "test-stdout.txt"
    if not stdout_path.is_file():
        return None
    try:
        text = stdout_path.read_text(errors="replace")

        # Format 1: Text DEBUG line (sourcegraph_benchmarks evaluators)
        m = re.search(
            r"DEBUG:\s*agent_files=(\d+),\s*oracle_files=(\d+),\s*overlap=(\d+),\s*F1=([\d.]+),\s*sym_score=([\d.]+)",
            text,
        )
        if m:
            return {
                "agent_files": int(m.group(1)),
                "oracle_files": int(m.group(2)),
                "overlap": int(m.group(3)),
                "f1": float(m.group(4)),
                "sym_score": float(m.group(5)),
                "source": "debug_line",
            }

        # Format 2: JSON checks (oracle_checks.py / promoted verifier)
        # The test-stdout.txt may start with or contain a JSON block.
        # Try parsing the whole text as JSON first, then extract the checks block.
        if '"checks"' in text and '"file_set_match"' in text:
            # Try parsing the entire output as JSON
            parsed = None
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError:
                # Try parsing just the part before "Composite score:" (common suffix)
                for sep in ("Composite score:", "\nComposite", "\nScore:"):
                    idx = text.find(sep)
                    if idx > 0:
                        try:
                            parsed = json.loads(text[:idx].rstrip().rstrip(","))
                            break
                        except json.JSONDecodeError:
                            continue
                # Last resort: find balanced braces from the start
                if parsed is None and text.lstrip().startswith("{"):
                    depth = 0
                    end = 0
                    for i, c in enumerate(text):
                        if c == "{":
                            depth += 1
                        elif c == "}":
                            depth -= 1
                            if depth == 0:
                                end = i + 1
                                break
                    if end > 0:
                        try:
                            parsed = json.loads(text[:end])
                        except json.JSONDecodeError:
                            pass

            if parsed and isinstance(parsed, dict):
                fsm = parsed.get("checks", {}).get("file_set_match", {})
                if fsm:
                    recall = fsm.get("recall", 0)
                    precision = fsm.get("precision", 0)
                    f1 = fsm.get("f1", 0)
                    matched = len(fsm.get("matched", []))
                    missing = len(fsm.get("missing", []))
                    extra = len(fsm.get("extra", []))
                    oracle_n = matched + missing
                    agent_n = matched + extra
                    sym = parsed.get("checks", {}).get("symbol_resolution", {})
                    return {
                        "agent_files": agent_n,
                        "oracle_files": oracle_n,
                        "overlap": matched,
                        "f1": float(f1),
                        "precision": float(precision),
                        "recall": float(recall),
                        "sym_score": float(sym.get("recall", 0)) if sym else 0.0,
                        "source": "json_checks",
                    }

        # Format 3: RepoQA verifier (Correct Function / Correct Path)
        m_path = re.search(r"Correct Path:\s*([\d.]+)", text)
        m_func = re.search(r"Correct Function:\s*([\d.]+)", text)
        if m_path and m_func:
            return {
                "agent_files": 1,
                "oracle_files": 1,
                "overlap": 1 if float(m_path.group(1)) > 0.5 else 0,
                "f1": float(m_func.group(1)),
                "sym_score": float(m_func.group(1)),
                "source": "repoqa",
            }

    except OSError:
        pass
    return None


# ---------------------------------------------------------------------------
# Stage 1: Valid/Invalid Classification
# ---------------------------------------------------------------------------

def classify_validity(task_dir: Path) -> dict:
    """Classify a trial as valid or invalid based on infrastructure failures.

    Returns dict with:
        stage1_class: "valid" | "invalid"
        stage1_reason: null | reason string
        reward: float | None
        wall_clock_seconds: float | None
        agent_result_present: bool
        exception_info: dict | None
    """
    result_path = task_dir / "result.json"
    if not result_path.is_file():
        return {
            "stage1_class": "invalid",
            "stage1_reason": "no_result_json",
            "reward": None,
            "wall_clock_seconds": None,
            "agent_result_present": False,
            "exception_info": None,
        }

    try:
        data = json.loads(result_path.read_text())
    except (json.JSONDecodeError, OSError):
        return {
            "stage1_class": "invalid",
            "stage1_reason": "corrupt_result_json",
            "reward": None,
            "wall_clock_seconds": None,
            "agent_result_present": False,
            "exception_info": None,
        }

    # Skip batch-level result.json (no task_name)
    if "task_name" not in data and "trial_name" not in data:
        return {
            "stage1_class": "invalid",
            "stage1_reason": "batch_level_result",
            "reward": None,
            "wall_clock_seconds": None,
            "agent_result_present": False,
            "exception_info": None,
        }

    reward = _extract_reward(data)
    agent_result = data.get("agent_result")
    exception_info = data.get("exception_info")

    # Compute wall clock
    wc = data.get("wall_clock_seconds")
    if wc is None:
        started = data.get("started_at", "")
        finished = data.get("finished_at", "")
        if started and finished:
            try:
                s = datetime.fromisoformat(started.replace("Z", "+00:00"))
                f = datetime.fromisoformat(finished.replace("Z", "+00:00"))
                wc = (f - s).total_seconds()
            except (ValueError, TypeError):
                pass

    result = {
        "reward": reward,
        "wall_clock_seconds": round(wc, 1) if wc is not None else None,
        "agent_result_present": agent_result is not None,
        "exception_info": exception_info,
    }

    # Check: agent_never_ran
    if agent_result is None and exception_info is not None:
        result["stage1_class"] = "invalid"
        result["stage1_reason"] = "agent_never_ran"
        return result

    # Check: rate_limited (reward=0, short duration, few tokens)
    if reward is not None and reward == 0.0 and wc is not None and wc < 30:
        n_output = 0
        if isinstance(agent_result, dict):
            n_output = agent_result.get("n_output_tokens") or 0
        if n_output < 500:
            result["stage1_class"] = "invalid"
            result["stage1_reason"] = "rate_limited"
            return result

    # Check exception info for specific failure types
    if exception_info is not None:
        exc_text = ""
        if isinstance(exception_info, dict):
            exc_text = " ".join([
                str(exception_info.get("exception_type", exception_info.get("type", ""))),
                str(exception_info.get("exception_message", exception_info.get("message", ""))),
                str(exception_info.get("exception_traceback", exception_info.get("traceback", ""))),
            ])
        elif isinstance(exception_info, str):
            exc_text = exception_info

        exc_lower = exc_text.lower()

        # auth_error
        if any(p in exc_lower for p in ["authentication failed", "403", "forbidden",
                                         "token refresh", "credentials expired"]):
            result["stage1_class"] = "invalid"
            result["stage1_reason"] = "auth_error"
            return result

        # docker_build_failure
        if any(p in exc_lower for p in ["failed to solve", "exit code: 128",
                                         "docker build", "image pull"]):
            result["stage1_class"] = "invalid"
            result["stage1_reason"] = "docker_build_failure"
            return result

        # environment_error
        if any(p in exc_lower for p in ["module_not_found", "command not found",
                                         "modulenotfounderror", "no such file"]):
            result["stage1_class"] = "invalid"
            result["stage1_reason"] = "environment_error"
            return result

        # Use fingerprint for remaining
        fp = fingerprint_error(exception_info)
        if fp:
            sev = fp.get("severity", "")
            if sev in ("infra", "api", "setup"):
                result["stage1_class"] = "invalid"
                result["stage1_reason"] = f"infra_other:{fp['fingerprint_id']}"
                return result
            # task-level errors (timeout with reward) are valid
            if sev == "task" and reward is not None:
                result["stage1_class"] = "valid"
                result["stage1_reason"] = None
                return result

        # Exception present but no reward = invalid
        if reward is None:
            result["stage1_class"] = "invalid"
            result["stage1_reason"] = f"infra_other:exception_no_reward"
            return result

    # Check: verifier_crash (no reward at all, no exception)
    if reward is None and exception_info is None:
        reward_txt = task_dir / "verifier" / "reward.txt"
        if not reward_txt.is_file():
            result["stage1_class"] = "invalid"
            result["stage1_reason"] = "verifier_crash"
            return result

    # Valid
    result["stage1_class"] = "valid"
    result["stage1_reason"] = None
    return result


# ---------------------------------------------------------------------------
# Stage 2: Setup Quality
# ---------------------------------------------------------------------------

def check_setup_quality(task_dir: Path, config_name: str) -> dict:
    """Check experimental setup correctness for a valid trial.

    Returns dict with:
        stage2_class: "valid_goodsetup" | "valid_badsetup"
        stage2_reasons: list[str]
    """
    reasons = []
    is_mcp = is_mcp_config(config_name)

    instruction_path = task_dir / "agent" / "instruction.txt"
    instruction_text = ""
    if instruction_path.is_file():
        try:
            instruction_text = instruction_path.read_text(errors="replace")
        except OSError:
            pass

    # Check for MCP tool calls in transcript (lightweight: read up to 2MB)
    transcript_path = task_dir / "agent" / "claude-code.txt"
    mcp_calls = 0
    has_mcp_tools_available = False

    if transcript_path.is_file():
        try:
            # Read up to 2MB — enough to detect MCP calls without parsing the full file
            with open(transcript_path, "r", errors="replace") as f:
                chunk = f.read(2 * 1024 * 1024)
            # Check init line (first line)
            first_nl = chunk.find("\n")
            if first_nl > 0:
                first_line = chunk[:first_nl]
                if "mcp__sourcegraph" in first_line and '"init"' in first_line:
                    has_mcp_tools_available = True
            # Count MCP tool_use calls in the chunk
            mcp_calls = len(MCP_TOOL_USE_RE.findall(chunk))
        except OSError:
            pass

    if is_mcp:
        # MCP run checks
        has_preamble = V5_PREAMBLE_MARKER in instruction_text
        has_mirror_ref = SG_MIRROR_MARKER in instruction_text

        if not has_preamble:
            reasons.append("missing_v5_preamble")
        if not has_mirror_ref:
            reasons.append("no_sg_mirror_reference")
        if mcp_calls == 0:
            reasons.append("zero_mcp_tool_calls")
    else:
        # Baseline run checks
        if mcp_calls > 0:
            reasons.append("baseline_has_mcp_calls")
        if V5_PREAMBLE_MARKER in instruction_text:
            reasons.append("baseline_has_sg_preamble")

    if reasons:
        return {"stage2_class": "valid_badsetup", "stage2_reasons": reasons}
    return {"stage2_class": "valid_goodsetup", "stage2_reasons": []}


# ---------------------------------------------------------------------------
# Stage 3: Quality Analysis
# ---------------------------------------------------------------------------

def _compute_recall_at_k(ordered_accesses: list[tuple[int, str]],
                         gt_norm: set[str],
                         checkpoints: tuple[int, ...] = (5, 10, 20)) -> dict:
    """Compute recall at k tool calls from an ordered access list.

    Args:
        ordered_accesses: list of (tool_call_index, normalized_path) in call order
        gt_norm: set of normalized ground truth file paths
        checkpoints: k values to compute recall at

    Returns:
        dict with recall_at_5, recall_at_10, recall_at_20, convergence_score
    """
    if not gt_norm or not ordered_accesses:
        return {}

    found_at: dict[int, set[str]] = {}  # cumulative oracle files found by tool call N
    cumulative: set[str] = set()
    result = {}

    for call_idx, norm_path in ordered_accesses:
        if norm_path in gt_norm:
            cumulative.add(norm_path)
        found_at[call_idx] = set(cumulative)

    total_recall = len(cumulative) / len(gt_norm) if gt_norm else 0.0

    # Compute recall at each checkpoint (by ordered position, not call_idx)
    for k in checkpoints:
        # Take the first k unique file accesses
        seen_at_k: set[str] = set()
        for i, (_, norm_path) in enumerate(ordered_accesses):
            if i >= k:
                break
            if norm_path in gt_norm:
                seen_at_k.add(norm_path)
        recall_k = len(seen_at_k) / len(gt_norm) if gt_norm else 0.0
        result[f"recall_at_{k}"] = round(recall_k, 4)

    # Convergence score: recall@10 / recall@total (how fast the agent converges)
    recall_at_10 = result.get("recall_at_10", 0.0)
    if total_recall > 0:
        result["convergence_score"] = round(recall_at_10 / total_recall, 4)
    else:
        result["convergence_score"] = 0.0

    return result


def analyze_quality(task_dir: Path, task_name: str, config_name: str, reward: Optional[float]) -> dict:
    """Perform quality analysis on a valid_goodsetup trial.

    Returns dict with hallucination, retrieval, and verifier analysis.
    """
    analysis = {}

    # Load ground truth
    gt_files = _load_ground_truth(task_name)

    # --- Hallucination / file coverage detection ---
    # Source 1: Parse verifier DEBUG output (most reliable — evaluator already compared)
    verifier_debug = _parse_verifier_debug(task_dir)
    if verifier_debug:
        agent_n = verifier_debug["agent_files"]
        oracle_n = verifier_debug["oracle_files"]
        overlap = verifier_debug["overlap"]
        precision = overlap / agent_n if agent_n else 0.0
        recall = overlap / oracle_n if oracle_n else 1.0
        analysis["hallucination"] = {
            "source": "verifier_debug",
            "agent_file_count": agent_n,
            "oracle_file_count": oracle_n,
            "true_positives": overlap,
            "false_positives": agent_n - overlap,
            "false_negatives": oracle_n - overlap,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": verifier_debug["f1"],
            "sym_score": verifier_debug["sym_score"],
        }

    # Source 2: Parse answer.json if no verifier debug (SDLC tasks with answer artifact)
    if "hallucination" not in analysis:
        # Try multiple answer.json locations
        answer_paths = [
            task_dir / "artifacts" / "answer.json",
            task_dir / "verifier" / "answer.json",
            task_dir / "agent" / "answer.json",
        ]
        for answer_path in answer_paths:
            if not answer_path.is_file():
                continue
            try:
                answer_data = json.loads(answer_path.read_text())
                # answer.json uses analysis.files_examined[].path format
                agent_files = []
                analysis_section = answer_data.get("analysis", {})
                if isinstance(analysis_section, dict):
                    for fe in analysis_section.get("files_examined", []):
                        if isinstance(fe, dict):
                            p = fe.get("path", fe.get("file", ""))
                            if p:
                                agent_files.append(p)
                        elif isinstance(fe, str):
                            agent_files.append(fe)
                # Also check top-level "files" key
                if not agent_files:
                    raw = answer_data.get("files", [])
                    if isinstance(raw, list):
                        for f in raw:
                            if isinstance(f, str):
                                agent_files.append(f)
                            elif isinstance(f, dict):
                                p = f.get("file", f.get("path", ""))
                                if p:
                                    agent_files.append(p)

                if agent_files and gt_files is not None:
                    gt_normalized = {_normalize_path(f) for f in gt_files}
                    agent_normalized = {_normalize_path(f) for f in agent_files}
                    true_pos = agent_normalized & gt_normalized
                    precision = len(true_pos) / len(agent_normalized) if agent_normalized else 0.0
                    recall = len(true_pos) / len(gt_normalized) if gt_normalized else 1.0
                    analysis["hallucination"] = {
                        "source": "answer_json",
                        "answer_path": str(answer_path.relative_to(task_dir)),
                        "agent_file_count": len(agent_normalized),
                        "oracle_file_count": len(gt_normalized),
                        "true_positives": len(true_pos),
                        "false_positives": len(agent_normalized) - len(true_pos),
                        "false_negatives": len(gt_normalized) - len(true_pos),
                        "precision": round(precision, 4),
                        "recall": round(recall, 4),
                    }
                    break
            except (json.JSONDecodeError, OSError):
                continue

    # --- Retrieval quality ---
    # Try trajectory.json first (structured, complete, no 4MB cap issue),
    # fall back to raw transcript parsing if unavailable.
    search_stats = _parse_trajectory(task_dir)
    if search_stats is None:
        transcript_path = task_dir / "agent" / "claude-code.txt"
        search_stats = _count_search_calls(transcript_path)

    if search_stats:
        analysis["retrieval"] = search_stats
        accessed_files = search_stats.get("files_accessed", [])

        # Add file recall if we have ground truth
        if gt_files is not None and accessed_files:
            gt_norm = {_normalize_path(f) for f in gt_files}
            accessed_norm = {_normalize_path(f) for f in accessed_files}
            overlap = gt_norm & accessed_norm
            analysis["retrieval"]["file_recall"] = round(
                len(overlap) / len(gt_norm) if gt_norm else 1.0, 4
            )
            analysis["retrieval"]["oracle_files_found"] = len(overlap)
            analysis["retrieval"]["oracle_files_total"] = len(gt_norm)

            # Compute recall@k if we have ordered access data (from trajectory)
            ordered_accesses = search_stats.get("ordered_file_accesses", [])
            if ordered_accesses:
                recall_at_k = _compute_recall_at_k(ordered_accesses, gt_norm)
                analysis["retrieval"].update(recall_at_k)

        # --- Claimed files precision (from answer.json or trajectory) ---
        claimed_files = search_stats.get("claimed_files", [])
        # Also try loading from on-disk answer.json if trajectory didn't capture it
        if not claimed_files:
            for ap in [task_dir / "artifacts" / "answer.json",
                       task_dir / "verifier" / "answer.json",
                       task_dir / "agent" / "answer.json"]:
                if not ap.is_file():
                    continue
                try:
                    ad = json.loads(ap.read_text())
                    asec = ad.get("analysis", {})
                    if isinstance(asec, dict):
                        for fe in asec.get("files_examined", []):
                            if isinstance(fe, dict):
                                p = fe.get("path", fe.get("file", ""))
                                if p:
                                    claimed_files.append(_normalize_path(p))
                            elif isinstance(fe, str):
                                claimed_files.append(_normalize_path(fe))
                    if not claimed_files:
                        raw = ad.get("files", [])
                        if isinstance(raw, list):
                            for f in raw:
                                if isinstance(f, str):
                                    claimed_files.append(_normalize_path(f))
                                elif isinstance(f, dict):
                                    p = f.get("file", f.get("path", ""))
                                    if p:
                                        claimed_files.append(_normalize_path(p))
                    if claimed_files:
                        break
                except (json.JSONDecodeError, OSError):
                    continue

        if claimed_files and gt_files is not None:
            gt_norm = {_normalize_path(f) for f in gt_files}
            claimed_norm = {f for f in claimed_files if f}
            if claimed_norm:
                claimed_tp = claimed_norm & gt_norm
                analysis["retrieval"]["claimed_precision"] = round(
                    len(claimed_tp) / len(claimed_norm) if claimed_norm else 0.0, 4
                )
                analysis["retrieval"]["claimed_file_count"] = len(claimed_norm)
        # Rename the existing precision metric for clarity when claimed is present
        if "claimed_precision" in analysis.get("retrieval", {}):
            analysis["retrieval"]["exploration_precision"] = round(
                len({_normalize_path(f) for f in accessed_files} & {_normalize_path(f) for f in gt_files})
                / len({_normalize_path(f) for f in accessed_files})
                if accessed_files and gt_files else 0.0,
                4
            )

        # Source 3: Transcript-based hallucination (when verifier debug and answer.json unavailable)
        if "hallucination" not in analysis and gt_files is not None and accessed_files:
            gt_norm = {_normalize_path(f) for f in gt_files}
            accessed_norm = {_normalize_path(f) for f in accessed_files}
            # Filter out non-source files (answer.json, test files, config)
            accessed_source = {f for f in accessed_norm
                               if f and not f.endswith(('.json', '.txt', '.log', '.md'))
                               and '/tests/' not in f and 'answer' not in f
                               and not f.startswith(('logs/', '/logs', '/tmp', '/tests'))}
            if accessed_source:
                true_pos = accessed_source & gt_norm
                precision = len(true_pos) / len(accessed_source) if accessed_source else 0.0
                recall = len(true_pos) / len(gt_norm) if gt_norm else 1.0
                analysis["hallucination"] = {
                    "source": "transcript",
                    "agent_file_count": len(accessed_source),
                    "oracle_file_count": len(gt_norm),
                    "true_positives": len(true_pos),
                    "false_positives": len(accessed_source) - len(true_pos),
                    "false_negatives": len(gt_norm) - len(true_pos),
                    "precision": round(precision, 4),
                    "recall": round(recall, 4),
                }

        # Remove internal data from output (too large / internal)
        for key in ("files_accessed", "ordered_file_accesses", "claimed_files"):
            if key in analysis.get("retrieval", {}):
                del analysis["retrieval"][key]

    # --- Verifier false negatives ---
    if reward is not None and reward == 0.0:
        halluc = analysis.get("hallucination", {})
        recall = halluc.get("recall", 0)
        if recall > 0.5:
            analysis["verifier_flag"] = {
                "flag": "potential_false_negative",
                "reason": f"reward=0 but agent file recall={recall:.2f} (>0.5), agent found {halluc.get('true_positives',0)}/{halluc.get('oracle_file_count',0)} oracle files",
                "agent_recall": recall,
            }
        # Also flag via verifier debug F1
        if verifier_debug and verifier_debug["f1"] > 0.5:
            analysis["verifier_flag"] = {
                "flag": "potential_false_negative",
                "reason": f"reward=0 but verifier-computed F1={verifier_debug['f1']:.4f} (>0.5)",
                "f1": verifier_debug["f1"],
            }

    return analysis


def _normalize_path(path) -> str:
    """Normalize file path for comparison.

    Handles:
    - /workspace/file.py → file.py
    - /workspace/envoy--v1.31.2/source/tls/... → source/tls/...
    - repo_slug::path/to/file → path/to/file
    - a/file.py, b/file.py (diff prefixes) → file.py
    """
    if isinstance(path, dict):
        path = path.get("file", path.get("path", ""))
    if not isinstance(path, str):
        return ""
    p = path.strip()
    for prefix in ("/workspace/", "workspace/"):
        if p.startswith(prefix):
            p = p[len(prefix):]
    if p.startswith(("a/", "b/")):
        p = p[2:]
    # Strip repo:: prefix (multi-repo ground truth)
    if "::" in p:
        p = p.split("::", 1)[1]
    # Strip version-pinned repo directory prefixes (e.g., envoy--v1.31.2/)
    # These appear in multi-repo tasks where workspace has repo-slug dirs.
    if "--" in p.split("/", 1)[0]:
        parts = p.split("/", 1)
        if len(parts) == 2:
            p = parts[1]
    # Strip sg-evals mirror prefix (e.g., sg-evals/envoy/)
    if p.startswith("sg-evals/"):
        p = p[len("sg-evals/"):]
        # May still have repo name prefix
        parts = p.split("/", 1)
        if len(parts) == 2:
            p = parts[1]
    p = p.strip("/")
    return p.lower()


SEARCH_TOOLS = {"Grep", "Glob", "keyword_search", "nls_search",
                "find_references", "go_to_definition", "list_files",
                "diff_search", "commit_search"}

# Tools whose arguments contain a file path (used for ordered access tracking)
_FILE_ARG_TOOLS = {"Read", "Edit", "Write"}

# Regex for extracting /workspace/ paths from Bash commands
_WORKSPACE_PATH_RE = re.compile(r'/workspace/([\w./+-]+\.[\w]+)')


def _parse_trajectory(task_dir: Path) -> Optional[dict]:
    """Parse trajectory.json for tool call stats, file access, and ordered access list.

    Returns the same format as _count_search_calls, plus:
        ordered_file_accesses: list of (tool_call_index, normalized_path) in call order
        claimed_files: list of file paths from the agent's final answer.json write
    Or None if trajectory.json is missing/unreadable.
    """
    trajectory_path = task_dir / "agent" / "trajectory.json"
    if not trajectory_path.is_file():
        return None

    # Size guard: skip files > 10MB
    try:
        if trajectory_path.stat().st_size > 10 * 1024 * 1024:
            return None
    except OSError:
        return None

    try:
        data = json.loads(trajectory_path.read_text(errors="replace"))
    except (json.JSONDecodeError, OSError):
        return None

    steps = data.get("steps", [])
    if not isinstance(steps, list):
        return None

    total_tool_calls = 0
    search_calls = 0
    mcp_calls = 0
    seen_files: set[str] = set()
    ordered_accesses: list[tuple[int, str]] = []  # (tool_call_index, norm_path)
    claimed_files: list[str] = []
    last_answer_json_content: Optional[str] = None

    for step in steps:
        extra = step.get("extra") or {}
        tool_name = extra.get("tool_use_name", "")
        if not tool_name:
            continue

        total_tool_calls += 1
        raw_args = extra.get("raw_arguments") or {}
        if not isinstance(raw_args, dict):
            raw_args = {}

        call_idx = total_tool_calls  # 1-based index

        # Count search calls
        if tool_name in SEARCH_TOOLS:
            search_calls += 1

        # Count MCP calls
        if tool_name.startswith("mcp__sourcegraph__"):
            mcp_calls += 1
            # Also count as search if it's a search-type MCP tool
            short_name = tool_name.replace("mcp__sourcegraph__", "").replace("sg_", "")
            if short_name in SEARCH_TOOLS:
                search_calls += 1

        # Extract file paths from tool arguments
        if tool_name in _FILE_ARG_TOOLS:
            fp = raw_args.get("file_path") or raw_args.get("file") or raw_args.get("path", "")
            if fp:
                norm = _normalize_path(fp)
                if norm and "." in norm.rsplit("/", 1)[-1]:
                    if norm not in seen_files:
                        ordered_accesses.append((call_idx, norm))
                    seen_files.add(norm)
                # Track writes to answer.json for claimed_files extraction
                if tool_name == "Write" and "answer.json" in fp:
                    content = raw_args.get("content", "")
                    if content:
                        last_answer_json_content = content

        elif tool_name == "Bash":
            cmd = raw_args.get("command", "")
            if isinstance(cmd, str):
                for pm in _WORKSPACE_PATH_RE.finditer(cmd):
                    norm = pm.group(1).lower().strip("/")
                    if norm and not norm.startswith(("node_modules/", ".git/", "logs/", "tmp/")):
                        if norm not in seen_files:
                            ordered_accesses.append((call_idx, norm))
                        seen_files.add(norm)
                # Also check for writes to answer.json via cat/echo heredoc
                if "answer.json" in cmd:
                    # Try to extract JSON content from heredoc or echo
                    json_start = cmd.find("{")
                    json_end = cmd.rfind("}")
                    if json_start >= 0 and json_end > json_start:
                        last_answer_json_content = cmd[json_start:json_end + 1]

        elif tool_name == "Grep":
            # Grep path argument
            gpath = raw_args.get("path", "")
            if gpath:
                norm = _normalize_path(gpath)
                if norm and "." in norm.rsplit("/", 1)[-1]:
                    if norm not in seen_files:
                        ordered_accesses.append((call_idx, norm))
                    seen_files.add(norm)

        elif tool_name.startswith("mcp__sourcegraph__"):
            # Extract paths from MCP tool arguments
            for key in ("path", "file", "filePath", "fileName"):
                val = raw_args.get(key, "")
                if val:
                    norm = _normalize_path(val)
                    if norm and "." in norm.rsplit("/", 1)[-1]:
                        if norm not in seen_files:
                            ordered_accesses.append((call_idx, norm))
                        seen_files.add(norm)

    # Parse claimed files from the last answer.json write
    if last_answer_json_content:
        try:
            answer_data = json.loads(last_answer_json_content)
            analysis_section = answer_data.get("analysis", {})
            if isinstance(analysis_section, dict):
                for fe in analysis_section.get("files_examined", []):
                    if isinstance(fe, dict):
                        p = fe.get("path", fe.get("file", ""))
                        if p:
                            claimed_files.append(_normalize_path(p))
                    elif isinstance(fe, str):
                        claimed_files.append(_normalize_path(fe))
            if not claimed_files:
                raw = answer_data.get("files", [])
                if isinstance(raw, list):
                    for f in raw:
                        if isinstance(f, str):
                            claimed_files.append(_normalize_path(f))
                        elif isinstance(f, dict):
                            p = f.get("file", f.get("path", ""))
                            if p:
                                claimed_files.append(_normalize_path(p))
        except (json.JSONDecodeError, AttributeError):
            pass

    files_accessed = sorted(seen_files)

    return {
        "total_tool_calls": total_tool_calls,
        "search_calls": search_calls,
        "mcp_calls": mcp_calls,
        "unique_files_read": len(files_accessed),
        "files_accessed": files_accessed,
        "ordered_file_accesses": ordered_accesses,
        "claimed_files": claimed_files,
        "source": "trajectory",
    }


def _count_search_calls(transcript_path: Path) -> Optional[dict]:
    """Count search tool calls in a transcript. Returns stats dict or None.

    Reads up to 4MB of the transcript to keep performance bounded.
    This is the fallback when trajectory.json is unavailable.
    """
    if not transcript_path.is_file():
        return None

    try:
        with open(transcript_path, "r", errors="replace") as f:
            chunk = f.read(4 * 1024 * 1024)
    except OSError:
        return None

    total_tool_calls = chunk.count('"type":"tool_use"') + chunk.count('"type": "tool_use"')

    search_calls = 0
    for pattern in ['"Grep"', '"Glob"', '"keyword_search"', '"nls_search"',
                    '"find_references"', '"go_to_definition"', '"list_files"',
                    '"diff_search"', '"commit_search"']:
        search_calls += chunk.count(pattern)

    mcp_calls = len(MCP_TOOL_USE_RE.findall(chunk))

    # Extract file paths from transcript using multiple strategies.
    seen_files = set()

    # Strategy 1: Structured tool arguments (Read/Edit/Write file_path)
    for pm in re.finditer(r'"(?:file_path|path)"\s*:\s*"([^"]+)"', chunk):
        fp = pm.group(1)
        norm = _normalize_path(fp)
        if norm and "." in norm.rsplit("/", 1)[-1]:
            seen_files.add(norm)

    # Strategy 2: All /workspace/ paths in the transcript (catches Bash args,
    # tool results, find/grep output, MCP read_file responses).
    # Match paths with file extensions to exclude directories.
    for pm in re.finditer(r'/workspace/([\w./+-]+\.[\w]+)', chunk):
        norm = pm.group(1).lower().strip("/")
        # Filter out common noise
        if norm and not norm.startswith(("node_modules/", ".git/", "logs/", "tmp/")):
            seen_files.add(norm)

    # Strategy 3: MCP sg_read_file / sg_keyword_search file references.
    # These appear as "path": "dir/file.ext" in MCP tool results.
    for pm in re.finditer(r'"(?:file|filePath|fileName)"\s*:\s*"([^"]+)"', chunk):
        fp = pm.group(1)
        norm = _normalize_path(fp)
        if norm and "." in norm.rsplit("/", 1)[-1]:
            seen_files.add(norm)

    files_accessed = sorted(seen_files)

    return {
        "total_tool_calls": total_tool_calls,
        "search_calls": search_calls,
        "mcp_calls": mcp_calls,
        "unique_files_read": len(files_accessed),
        "files_accessed": files_accessed,
        "source": "transcript",
    }


# ---------------------------------------------------------------------------
# Directory walking
# ---------------------------------------------------------------------------

def iter_all_trials(runs_dirs: list[Path], verbose: bool = False):
    """Walk run directories and yield (task_dir, run_name, config_name, suite) tuples."""
    count = 0
    for runs_dir in runs_dirs:
        if not runs_dir.is_dir():
            continue

        for run_dir in sorted(runs_dir.iterdir()):
            if not run_dir.is_dir():
                continue
            if should_skip(run_dir.name):
                continue
            # Skip special directories
            if run_dir.name in ("_meta", "_quarantine", "_views_legacy",
                                "archive", "MANIFEST.json", "flag_reclassification_review.json"):
                continue

            # The directory structure can be:
            # 1) runs/official/_raw/{batch}/config/timestamp/trial/
            # 2) runs/official/csb_sdlc/{model}/{suite}/config/timestamp/trial/
            # 3) runs/official/{suite_run}/config/timestamp/trial/ (old format)
            # We need to walk all of these generically.

            # Detect if this is a suite-prefixed run dir
            suite = detect_suite(run_dir.name)

            if suite is not None:
                # Old-style: run_dir is named after the suite+batch
                for config_name in discover_configs(run_dir):
                    config_path = run_dir / config_name
                    for trial_dir in _iter_task_dirs(config_path):
                        count += 1
                        yield trial_dir, run_dir.name, config_name, suite
            else:
                # Could be _raw, csb_sdlc, csb_org, openhands etc.
                # Walk recursively looking for result.json
                _walk_nested(run_dir, run_dir.name, count, verbose,
                             results := [])
                for item in results:
                    yield item
                count += len(results)

    if verbose:
        print(f"  [walk] Found {count} trial directories", file=sys.stderr)


def _walk_nested(parent: Path, top_name: str, count: int, verbose: bool,
                 results: list):
    """Walk nested directory structures looking for config/trial patterns."""
    if not parent.is_dir():
        return

    for child in sorted(parent.iterdir()):
        if not child.is_dir() or should_skip(child.name):
            continue

        # Check if child is a config directory
        configs = discover_configs(child)
        if configs:
            suite = detect_suite(child.name)
            for config_name in configs:
                config_path = child / config_name
                for trial_dir in _iter_task_dirs(config_path):
                    results.append((trial_dir, top_name, config_name, suite))
            continue

        # Check if this directory itself has config-like children
        has_config_children = False
        for grandchild in child.iterdir():
            if grandchild.is_dir():
                gc_configs = discover_configs(grandchild)
                if gc_configs:
                    has_config_children = True
                    break

        if has_config_children:
            _walk_nested(child, top_name, count, verbose, results)
            continue

        # Check if this is already a config dir with trial dirs inside
        # (e.g., _raw/batch/config/timestamp/trial)
        for trial_dir in _iter_task_dirs(child):
            result_file = trial_dir / "result.json"
            if result_file.is_file():
                # Try to detect config from parent chain
                config_name = _infer_config(trial_dir)
                suite = _infer_suite(trial_dir)
                results.append((trial_dir, top_name, config_name, suite))


def _infer_config(trial_dir: Path) -> str:
    """Try to infer config name from directory ancestry."""
    for parent in trial_dir.parents:
        name = parent.name
        if name in ("baseline", "baseline-local-direct", "baseline-local-artifact",
                     "mcp-remote-direct", "mcp-remote-artifact",
                     "sourcegraph_full", "sourcegraph_isolated", "mcp_unknown",
                     "mcp", "sourcegraph"):
            return name
    return "unknown"


def _infer_suite(trial_dir: Path) -> Optional[str]:
    """Try to infer suite from directory ancestry or trial name."""
    for parent in trial_dir.parents:
        suite = detect_suite(parent.name)
        if suite:
            return suite
    # Try from trial dir name
    return detect_suite(trial_dir.name)


# ---------------------------------------------------------------------------
# Pipeline orchestration
# ---------------------------------------------------------------------------

def run_pipeline(
    runs_dirs: list[Path],
    stages: str = "all",
    verbose: bool = False,
) -> dict:
    """Run the classification pipeline on all trial directories.

    Args:
        runs_dirs: List of run directories to scan.
        stages: "1", "2", "3", or "all".
        verbose: Print progress to stderr.

    Returns:
        Report dict with summary and per-trial records.
    """
    run_stage1 = stages in ("1", "all")
    run_stage2 = stages in ("2", "all")
    run_stage3 = stages in ("3", "all")

    trials = []
    counters = Counter()
    invalid_reasons = Counter()
    badsetup_reasons = Counter()

    t0 = time.time()
    n_processed = 0

    for trial_dir, run_name, config_name, suite in iter_all_trials(runs_dirs, verbose):
        n_processed += 1
        if verbose and n_processed % 500 == 0:
            print(f"  [pipeline] Processed {n_processed} trials...", file=sys.stderr)

        task_name = _extract_task_name(trial_dir.name)

        # Try to get a better task name from result.json (cached via stage1)
        result_path = trial_dir / "result.json"
        result_task_name = None
        if result_path.is_file():
            try:
                data = json.loads(result_path.read_text())
                result_task_name = data.get("task_name", "")
            except (json.JSONDecodeError, OSError):
                pass

        if result_task_name:
            task_name = result_task_name

        record = {
            "task_dir": str(trial_dir),
            "task_name": task_name,
            "config": config_name,
            "suite": suite,
            "run_name": run_name,
        }

        # Stage 1
        if run_stage1:
            s1 = classify_validity(trial_dir)
            record["stage1_class"] = s1["stage1_class"]
            record["stage1_reason"] = s1["stage1_reason"]
            record["reward"] = s1["reward"]
            record["wall_clock_seconds"] = s1.get("wall_clock_seconds")

            counters[s1["stage1_class"]] += 1
            if s1["stage1_reason"]:
                invalid_reasons[s1["stage1_reason"]] += 1
        else:
            record["stage1_class"] = "valid"
            record["stage1_reason"] = None
            record["reward"] = None

        # Stage 2 (only for valid trials)
        if run_stage2 and record["stage1_class"] == "valid":
            s2 = check_setup_quality(trial_dir, config_name)
            record["stage2_class"] = s2["stage2_class"]
            record["stage2_reasons"] = s2["stage2_reasons"]
            counters[s2["stage2_class"]] += 1
            for r in s2["stage2_reasons"]:
                badsetup_reasons[r] += 1
        else:
            record["stage2_class"] = None
            record["stage2_reasons"] = []

        # Stage 3 (only for valid_goodsetup)
        if run_stage3 and record.get("stage2_class") == "valid_goodsetup":
            s3 = analyze_quality(trial_dir, task_name, config_name, record.get("reward"))
            record["stage3"] = s3 if s3 else None
        else:
            record["stage3"] = None

        trials.append(record)

    elapsed = time.time() - t0

    # Build summary
    total = len(trials)
    n_invalid = counters.get("invalid", 0)
    n_goodsetup = counters.get("valid_goodsetup", 0)
    n_badsetup = counters.get("valid_badsetup", 0)
    n_valid_no_s2 = counters.get("valid", 0)  # valid but stage2 not run

    # Stage 3 aggregates
    s3_trials = [t for t in trials if t.get("stage3")]
    halluc_trials = [t for t in s3_trials if t["stage3"].get("hallucination")]
    verifier_flags = [t for t in s3_trials if t["stage3"].get("verifier_flag")]

    avg_precision = 0.0
    avg_recall = 0.0
    if halluc_trials:
        avg_precision = sum(t["stage3"]["hallucination"]["precision"] for t in halluc_trials) / len(halluc_trials)
        avg_recall = sum(t["stage3"]["hallucination"]["recall"] for t in halluc_trials) / len(halluc_trials)

    # Retrieval stats
    retrieval_trials = [t for t in s3_trials if t["stage3"].get("retrieval")]
    avg_file_recall = 0.0
    if retrieval_trials:
        recalls = [t["stage3"]["retrieval"].get("file_recall", 0) for t in retrieval_trials
                   if t["stage3"]["retrieval"].get("file_recall") is not None]
        if recalls:
            avg_file_recall = sum(recalls) / len(recalls)

    # recall@k and convergence aggregates (overall and per-config)
    def _avg_metric(trials_list, metric_key):
        vals = [t["stage3"]["retrieval"].get(metric_key) for t in trials_list
                if t["stage3"].get("retrieval") and t["stage3"]["retrieval"].get(metric_key) is not None]
        return round(sum(vals) / len(vals), 4) if vals else None

    recall_at_k_overall = {}
    for k in ("recall_at_5", "recall_at_10", "recall_at_20", "convergence_score",
              "claimed_precision", "exploration_precision"):
        val = _avg_metric(retrieval_trials, k)
        if val is not None:
            recall_at_k_overall[k] = val

    # Per-config breakdown (BL vs MCP)
    recall_at_k_by_config = {}
    for t in retrieval_trials:
        cfg = t.get("config", "unknown")
        # Normalize to BL vs MCP
        config_group = "MCP" if is_mcp_config(cfg) else "BL"
        if config_group not in recall_at_k_by_config:
            recall_at_k_by_config[config_group] = []
        recall_at_k_by_config[config_group].append(t)

    per_config_metrics = {}
    for config_group, group_trials in recall_at_k_by_config.items():
        metrics = {}
        for k in ("recall_at_5", "recall_at_10", "recall_at_20", "convergence_score",
                  "claimed_precision", "exploration_precision", "file_recall"):
            val = _avg_metric(group_trials, k)
            if val is not None:
                metrics[k] = val
        metrics["count"] = len(group_trials)
        per_config_metrics[config_group] = metrics

    # Count trajectory vs transcript source usage
    traj_source_counts = Counter()
    for t in retrieval_trials:
        src = t["stage3"]["retrieval"].get("source", "unknown")
        traj_source_counts[src] += 1

    summary = {
        "total": total,
        "invalid": n_invalid,
        "valid_badsetup": n_badsetup,
        "valid_goodsetup": n_goodsetup,
        "valid_no_stage2": n_valid_no_s2,
        "by_invalid_reason": dict(invalid_reasons.most_common()),
        "by_badsetup_reason": dict(badsetup_reasons.most_common()),
        "stage3": {
            "trials_analyzed": len(s3_trials),
            "with_hallucination_data": len(halluc_trials),
            "avg_precision": round(avg_precision, 4),
            "avg_recall": round(avg_recall, 4),
            "with_retrieval_data": len(retrieval_trials),
            "avg_file_recall": round(avg_file_recall, 4),
            "verifier_false_negative_flags": len(verifier_flags),
            "retrieval_source_counts": dict(traj_source_counts),
            "recall_at_k": recall_at_k_overall,
            "recall_at_k_by_config": per_config_metrics,
        },
        "elapsed_seconds": round(elapsed, 1),
    }

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": summary,
        "trials": trials,
    }


# ---------------------------------------------------------------------------
# Markdown summary output
# ---------------------------------------------------------------------------

def print_markdown_summary(report: dict):
    """Print a concise markdown summary to stdout."""
    s = report["summary"]
    total = s["total"]

    print("# Trace Quality Pipeline Report")
    print(f"\nGenerated: {report['generated_at']}")
    print(f"Elapsed: {s['elapsed_seconds']:.1f}s")
    print()

    print("## Stage 1: Validity Classification")
    print(f"| Category | Count | % |")
    print(f"|----------|------:|--:|")
    print(f"| **Total trials** | {total} | 100% |")
    n_valid = total - s["invalid"]
    print(f"| Valid | {n_valid} | {n_valid/total*100:.1f}% |" if total else "| Valid | 0 | 0% |")
    print(f"| Invalid | {s['invalid']} | {s['invalid']/total*100:.1f}% |" if total else "| Invalid | 0 | 0% |")
    print()

    if s["by_invalid_reason"]:
        print("### Invalid Reasons")
        print("| Reason | Count |")
        print("|--------|------:|")
        for reason, count in sorted(s["by_invalid_reason"].items(), key=lambda x: -x[1]):
            print(f"| {reason} | {count} |")
        print()

    if s.get("valid_goodsetup", 0) or s.get("valid_badsetup", 0):
        print("## Stage 2: Setup Quality")
        print(f"| Category | Count |")
        print(f"|----------|------:|")
        print(f"| Good setup | {s['valid_goodsetup']} |")
        print(f"| Bad setup | {s['valid_badsetup']} |")
        print()

        if s["by_badsetup_reason"]:
            print("### Bad Setup Reasons")
            print("| Reason | Count |")
            print("|--------|------:|")
            for reason, count in sorted(s["by_badsetup_reason"].items(), key=lambda x: -x[1]):
                print(f"| {reason} | {count} |")
            print()

    s3 = s.get("stage3", {})
    if s3.get("trials_analyzed", 0) > 0:
        print("## Stage 3: Quality Analysis")
        print(f"| Metric | Value |")
        print(f"|--------|------:|")
        print(f"| Trials analyzed | {s3['trials_analyzed']} |")
        print(f"| With hallucination data | {s3['with_hallucination_data']} |")
        print(f"| Avg answer precision | {s3['avg_precision']:.4f} |")
        print(f"| Avg answer recall | {s3['avg_recall']:.4f} |")
        print(f"| With retrieval data | {s3['with_retrieval_data']} |")
        print(f"| Avg file recall | {s3['avg_file_recall']:.4f} |")
        print(f"| Verifier false-negative flags | {s3['verifier_false_negative_flags']} |")

        # Retrieval source counts
        src_counts = s3.get("retrieval_source_counts", {})
        if src_counts:
            src_str = ", ".join(f"{k}={v}" for k, v in sorted(src_counts.items()))
            print(f"| Retrieval data source | {src_str} |")

        # recall@k overall
        rak = s3.get("recall_at_k", {})
        if rak:
            for key in ("recall_at_5", "recall_at_10", "recall_at_20",
                        "convergence_score", "claimed_precision", "exploration_precision"):
                if key in rak:
                    label = key.replace("_", " ").title()
                    print(f"| {label} | {rak[key]:.4f} |")
        print()

        # Per-config recall@k breakdown
        per_cfg = s3.get("recall_at_k_by_config", {})
        if per_cfg:
            print("### Retrieval Metrics by Config (BL vs MCP)")
            cols = ["file_recall", "recall_at_5", "recall_at_10", "recall_at_20",
                    "convergence_score", "claimed_precision", "exploration_precision"]
            # Build header
            present_cols = [c for c in cols if any(c in m for m in per_cfg.values())]
            if present_cols:
                header = "| Config | N |" + "|".join(f" {c} " for c in present_cols) + "|"
                sep = "|--------|--:|" + "|".join("------:" for _ in present_cols) + "|"
                print(header)
                print(sep)
                for cfg_name in sorted(per_cfg.keys()):
                    m = per_cfg[cfg_name]
                    vals = "|".join(f" {m.get(c, '-'):.4f} " if isinstance(m.get(c), (int, float)) else " - "
                                    for c in present_cols)
                    print(f"| {cfg_name} | {m.get('count', 0)} |{vals}|")
                print()

    # Top-level config breakdown
    trials = report["trials"]
    config_counts = Counter()
    config_valid = Counter()
    for t in trials:
        cfg = t.get("config", "unknown")
        config_counts[cfg] += 1
        if t.get("stage1_class") == "valid":
            config_valid[cfg] += 1

    if config_counts:
        print("## By Config")
        print("| Config | Total | Valid | Valid% |")
        print("|--------|------:|------:|-------:|")
        for cfg, cnt in config_counts.most_common():
            v = config_valid[cfg]
            pct = v / cnt * 100 if cnt else 0
            print(f"| {cfg} | {cnt} | {v} | {pct:.1f}% |")
        print()

    # Suite breakdown
    suite_counts = Counter()
    suite_valid = Counter()
    for t in trials:
        su = t.get("suite") or "unknown"
        suite_counts[su] += 1
        if t.get("stage1_class") == "valid":
            suite_valid[su] += 1

    if suite_counts and len(suite_counts) > 1:
        print("## By Suite (top 15)")
        print("| Suite | Total | Valid | Valid% |")
        print("|-------|------:|------:|-------:|")
        for su, cnt in suite_counts.most_common(15):
            v = suite_valid[su]
            pct = v / cnt * 100 if cnt else 0
            print(f"| {su} | {cnt} | {v} | {pct:.1f}% |")
        print()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Trace classification and quality analysis pipeline."
    )
    parser.add_argument(
        "--runs-dir", type=str, default=str(RUNS_DIR_OFFICIAL),
        help=f"Primary runs directory (default: {RUNS_DIR_OFFICIAL})",
    )
    parser.add_argument(
        "--include-staging", action="store_true",
        help="Also scan runs/staging/",
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help="Write JSON report to this file",
    )
    parser.add_argument(
        "--stage", choices=["1", "2", "3", "all"], default="all",
        help="Run only a specific stage (default: all)",
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Print progress to stderr",
    )
    args = parser.parse_args()

    runs_dirs = [Path(args.runs_dir)]
    if args.include_staging:
        runs_dirs.append(RUNS_DIR_STAGING)

    if args.verbose:
        print(f"Scanning: {[str(d) for d in runs_dirs]}", file=sys.stderr)

    report = run_pipeline(runs_dirs, stages=args.stage, verbose=args.verbose)

    # Print markdown summary to stdout
    print_markdown_summary(report)

    # Write JSON report
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2, default=str) + "\n")
        print(f"\nJSON report written to: {args.output}")


if __name__ == "__main__":
    main()
