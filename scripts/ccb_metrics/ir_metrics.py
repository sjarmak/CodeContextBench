"""Information retrieval metrics for CodeContextBench.

Provides standard IR metrics (precision, recall, MRR, nDCG, MAP, F1) plus
file-level recall and context efficiency. Operates on simple file-path lists
rather than the full CodeLocation/GroundTruth hierarchy used by IR-SDLC-Factory.

Also provides transcript parsing to extract the ordered list of files
retrieved by an agent during a task run.
"""

from __future__ import annotations

import json
import math
import re
import statistics
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Core IR metric functions (pure math, stdlib only)
# ---------------------------------------------------------------------------

def precision_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    """Precision@K = |relevant ∩ retrieved[:k]| / k."""
    if k <= 0:
        return 0.0
    top_k = retrieved[:k]
    if not top_k:
        return 0.0
    hits = sum(1 for f in top_k if _normalize(f) in relevant)
    return hits / k


def recall_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    """Recall@K = |relevant ∩ retrieved[:k]| / |relevant|."""
    if not relevant:
        return 1.0
    top_k = retrieved[:k]
    if not top_k:
        return 0.0
    norm_top = {_normalize(f) for f in top_k}
    found = sum(1 for r in relevant if r in norm_top)
    return found / len(relevant)


def f1_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    """F1@K = harmonic mean of precision@K and recall@K."""
    p = precision_at_k(retrieved, relevant, k)
    r = recall_at_k(retrieved, relevant, k)
    if p + r == 0:
        return 0.0
    return 2 * p * r / (p + r)


def mrr(retrieved: list[str], relevant: set[str]) -> float:
    """Mean Reciprocal Rank = 1 / rank_of_first_relevant."""
    for i, f in enumerate(retrieved):
        if _normalize(f) in relevant:
            return 1.0 / (i + 1)
    return 0.0


def ndcg_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    """Normalized Discounted Cumulative Gain @ K (binary relevance)."""
    if k <= 0 or not relevant:
        return 0.0

    top_k = retrieved[:k]

    # DCG
    dcg = 0.0
    for i, f in enumerate(top_k):
        if _normalize(f) in relevant:
            dcg += 1.0 / math.log2(i + 2)  # i+2 because log2(1)=0

    # Ideal DCG: all relevant items first
    ideal_k = min(k, len(relevant))
    idcg = sum(1.0 / math.log2(i + 2) for i in range(ideal_k))

    if idcg == 0:
        return 0.0
    return dcg / idcg


def mean_average_precision(retrieved: list[str], relevant: set[str]) -> float:
    """Average Precision (MAP for a single query)."""
    if not relevant:
        return 1.0

    n_relevant = len(relevant)
    sum_prec = 0.0
    hits = 0

    for i, f in enumerate(retrieved):
        if _normalize(f) in relevant:
            hits += 1
            sum_prec += hits / (i + 1)

    if hits == 0:
        return 0.0
    return sum_prec / n_relevant


def file_level_recall(retrieved: list[str], relevant: set[str]) -> float:
    """Fraction of ground-truth files found anywhere in retrieved list."""
    if not relevant:
        return 1.0
    norm_retrieved = {_normalize(f) for f in retrieved}
    found = sum(1 for r in relevant if r in norm_retrieved)
    return found / len(relevant)


def context_efficiency(retrieved: list[str], relevant: set[str]) -> float:
    """Fraction of retrieved files that are relevant (= precision over all)."""
    if not retrieved:
        return 0.0
    norm_relevant = relevant  # already normalized by caller
    hits = sum(1 for f in retrieved if _normalize(f) in norm_relevant)
    return hits / len(retrieved)


def _normalize(path: str) -> str:
    """Normalize a file path for comparison.

    Strips /workspace/ prefix, a/ b/ diff prefixes, leading/trailing slashes,
    and lowercases the result.
    """
    p = path.strip()
    # Strip /workspace/ prefix (Harbor container paths)
    for prefix in ("/workspace/", "workspace/"):
        if p.startswith(prefix):
            p = p[len(prefix):]
    # Strip diff a/ b/ prefixes
    if p.startswith(("a/", "b/")):
        p = p[2:]
    p = p.strip("/")
    return p.lower()


# ---------------------------------------------------------------------------
# Result container
# ---------------------------------------------------------------------------

@dataclass
class IRScores:
    """IR evaluation scores for a single (task, config) pair."""

    task_id: str
    config_name: str

    precision: dict[int, float] = field(default_factory=dict)   # {1: .., 3: .., 5: .., 10: ..}
    recall: dict[int, float] = field(default_factory=dict)
    f1: dict[int, float] = field(default_factory=dict)
    mrr: float = 0.0
    ndcg: dict[int, float] = field(default_factory=dict)
    map_score: float = 0.0
    file_recall: float = 0.0
    context_efficiency: float = 0.0
    n_retrieved: int = 0
    n_ground_truth: int = 0
    n_overlap: int = 0

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "config_name": self.config_name,
            "precision": self.precision,
            "recall": self.recall,
            "f1": self.f1,
            "mrr": self.mrr,
            "ndcg": self.ndcg,
            "map_score": self.map_score,
            "file_recall": self.file_recall,
            "context_efficiency": self.context_efficiency,
            "n_retrieved": self.n_retrieved,
            "n_ground_truth": self.n_ground_truth,
            "n_overlap": self.n_overlap,
        }


def compute_ir_scores(
    retrieved: list[str],
    ground_truth_files: list[str],
    task_id: str,
    config_name: str,
    k_values: list[int] | None = None,
) -> IRScores:
    """Compute all IR metrics for a (task, config) pair.

    Args:
        retrieved: Ordered list of file paths the agent accessed.
        ground_truth_files: Files that needed modification (from TaskGroundTruth).
        task_id: Task identifier.
        config_name: Config label (e.g. "baseline", "sourcegraph_full").
        k_values: K values for @K metrics (default [1, 3, 5, 10]).

    Returns:
        IRScores dataclass.
    """
    if k_values is None:
        k_values = [1, 3, 5, 10]

    relevant = {_normalize(f) for f in ground_truth_files}
    norm_retrieved = {_normalize(f) for f in retrieved}
    overlap = relevant & norm_retrieved

    scores = IRScores(
        task_id=task_id,
        config_name=config_name,
        mrr=mrr(retrieved, relevant),
        map_score=mean_average_precision(retrieved, relevant),
        file_recall=file_level_recall(retrieved, relevant),
        context_efficiency=context_efficiency(retrieved, relevant),
        n_retrieved=len(retrieved),
        n_ground_truth=len(relevant),
        n_overlap=len(overlap),
    )

    for k in k_values:
        scores.precision[k] = round(precision_at_k(retrieved, relevant, k), 4)
        scores.recall[k] = round(recall_at_k(retrieved, relevant, k), 4)
        scores.f1[k] = round(f1_at_k(retrieved, relevant, k), 4)
        scores.ndcg[k] = round(ndcg_at_k(retrieved, relevant, k), 4)

    scores.mrr = round(scores.mrr, 4)
    scores.map_score = round(scores.map_score, 4)
    scores.file_recall = round(scores.file_recall, 4)
    scores.context_efficiency = round(scores.context_efficiency, 4)

    return scores


def aggregate_ir_scores(scores: list[IRScores]) -> dict:
    """Aggregate IR scores across tasks: mean/std/median per metric."""
    if not scores:
        return {}

    # Collect scalar metrics
    scalars = {
        "mrr": [s.mrr for s in scores],
        "map_score": [s.map_score for s in scores],
        "file_recall": [s.file_recall for s in scores],
        "context_efficiency": [s.context_efficiency for s in scores],
    }

    # Collect @k metrics
    k_values = set()
    for s in scores:
        k_values.update(s.precision.keys())
    k_values = sorted(k_values)

    for k in k_values:
        scalars[f"precision@{k}"] = [s.precision.get(k, 0.0) for s in scores]
        scalars[f"recall@{k}"] = [s.recall.get(k, 0.0) for s in scores]
        scalars[f"f1@{k}"] = [s.f1.get(k, 0.0) for s in scores]
        scalars[f"ndcg@{k}"] = [s.ndcg.get(k, 0.0) for s in scores]

    result = {}
    for name, values in scalars.items():
        result[name] = {
            "mean": round(statistics.mean(values), 4),
            "std": round(statistics.stdev(values), 4) if len(values) > 1 else 0.0,
            "median": round(statistics.median(values), 4),
            "n": len(values),
        }

    result["_totals"] = {
        "n_tasks": len(scores),
        "mean_retrieved": round(statistics.mean([s.n_retrieved for s in scores]), 1),
        "mean_ground_truth": round(statistics.mean([s.n_ground_truth for s in scores]), 1),
        "mean_overlap": round(statistics.mean([s.n_overlap for s in scores]), 1),
    }

    return result


# ---------------------------------------------------------------------------
# Transcript parsing — extract retrieved files
# ---------------------------------------------------------------------------

# MCP tool names that read/search remote files
_MCP_READ_TOOLS = {
    "mcp__sourcegraph__sg_read_file", "mcp__sourcegraph__read_file",
}
_MCP_SEARCH_TOOLS = {
    "mcp__sourcegraph__sg_keyword_search", "mcp__sourcegraph__keyword_search",
    "mcp__sourcegraph__sg_nls_search", "mcp__sourcegraph__nls_search",
    "mcp__sourcegraph__sg_find_references", "mcp__sourcegraph__find_references",
    "mcp__sourcegraph__sg_go_to_definition", "mcp__sourcegraph__go_to_definition",
    "mcp__sourcegraph__sg_list_files", "mcp__sourcegraph__list_files",
    "mcp__sourcegraph__sg_diff_search", "mcp__sourcegraph__diff_search",
    "mcp__sourcegraph__sg_commit_search", "mcp__sourcegraph__commit_search",
    "mcp__sourcegraph__sg_compare_revisions", "mcp__sourcegraph__compare_revisions",
}
_LOCAL_FILE_TOOLS = {"Read", "Grep", "Glob"}

# Regex for "path": "some/file.ext" in JSON-like text
_PATH_JSON_RE = re.compile(r'"path"\s*:\s*"([^"]+)"')


def extract_retrieved_files(transcript_path: Path) -> list[str]:
    """Parse a claude-code.txt JSONL transcript and extract accessed files.

    Returns ordered list of unique file paths (first-seen order).
    For MCP tools: extracts paths from tool_result content.
    For local tools (Read/Grep/Glob): extracts paths from tool input params.
    """
    if not transcript_path.is_file():
        return []

    files: list[str] = []
    seen: set[str] = set()

    def _add(path: str) -> None:
        norm = _normalize(path)
        if norm and norm not in seen and _looks_like_file(norm):
            seen.add(norm)
            files.append(path.strip())

    def _process_tool_use(tool_name: str, tool_input: dict) -> None:
        """Process a tool_use block and extract file paths."""
        if isinstance(tool_input, str):
            try:
                tool_input = json.loads(tool_input)
            except json.JSONDecodeError:
                tool_input = {}
        if not isinstance(tool_input, dict):
            return

        if tool_name in _LOCAL_FILE_TOOLS:
            fp = tool_input.get("file_path") or tool_input.get("path") or ""
            if fp:
                _add(fp)
        elif tool_name in _MCP_READ_TOOLS:
            fp = tool_input.get("path", "")
            if fp:
                _add(fp)

    def _process_tool_result(tool_name: str, content: str) -> None:
        """Process a tool_result and extract file paths from output."""
        if tool_name in _MCP_SEARCH_TOOLS or tool_name in _MCP_READ_TOOLS:
            for m in _PATH_JSON_RE.finditer(content):
                _add(m.group(1))
        elif tool_name == "Glob":
            for fline in content.splitlines():
                fline = fline.strip()
                if fline and "/" in fline and "." in fline:
                    _add(fline)
        elif tool_name == "Grep":
            for fline in content.splitlines():
                fline = fline.strip()
                if fline and "/" in fline and "." in fline and not fline.startswith("#"):
                    _add(fline)

    # Map tool_use_id → tool_name for matching results to their calls
    tool_id_to_name: dict[str, str] = {}

    for line in transcript_path.read_text(errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue

        msg_type = entry.get("type", "")

        # Harbor claude-code.txt: tool calls and results are nested inside
        # "assistant" and "user" messages within message.content arrays.
        if msg_type == "assistant":
            message = entry.get("message", entry)
            content_blocks = message.get("content", [])
            if isinstance(content_blocks, list):
                for block in content_blocks:
                    if isinstance(block, dict) and block.get("type") == "tool_use":
                        name = block.get("name", "")
                        tid = block.get("id", "")
                        inp = block.get("input", {})
                        if tid and name:
                            tool_id_to_name[tid] = name
                        _process_tool_use(name, inp)

        elif msg_type == "user":
            message = entry.get("message", entry)
            content_blocks = message.get("content", [])
            if isinstance(content_blocks, list):
                for block in content_blocks:
                    if isinstance(block, dict) and block.get("type") == "tool_result":
                        tid = block.get("tool_use_id", "")
                        name = tool_id_to_name.get(tid, "")
                        raw = block.get("content", "")
                        if isinstance(raw, list):
                            raw = " ".join(
                                item.get("text", "") if isinstance(item, dict) else str(item)
                                for item in raw
                            )
                        if not isinstance(raw, str):
                            raw = str(raw)
                        if name:
                            _process_tool_result(name, raw)

            # Also check top-level tool_use_result (Harbor shortcut)
            tur = entry.get("tool_use_result", {})
            if isinstance(tur, dict):
                stdout = tur.get("stdout", "")
                if stdout and isinstance(stdout, str):
                    # Associate with last tool call via parent_tool_use_id
                    ptid = entry.get("parent_tool_use_id") or ""
                    if not ptid:
                        # Try matching the tool_use_id in content blocks
                        if isinstance(content_blocks, list):
                            for block in content_blocks:
                                if isinstance(block, dict) and block.get("type") == "tool_result":
                                    ptid = block.get("tool_use_id", "")
                    name = tool_id_to_name.get(ptid, "")
                    if name:
                        _process_tool_result(name, stdout)

        # Top-level tool_use / tool_result entries (non-Harbor format)
        elif msg_type == "tool_use":
            name = entry.get("tool_name", "") or entry.get("name", "")
            tid = entry.get("id", "")
            inp = entry.get("input", {}) or entry.get("tool_input", {})
            if tid and name:
                tool_id_to_name[tid] = name
            _process_tool_use(name, inp)

        elif msg_type == "tool_result":
            tid = entry.get("tool_use_id", "")
            name = entry.get("tool_name", "") or entry.get("name", "") or tool_id_to_name.get(tid, "")
            raw = entry.get("content", "") or entry.get("result", "")
            if isinstance(raw, list):
                raw = " ".join(
                    item.get("text", "") if isinstance(item, dict) else str(item)
                    for item in raw
                )
            if not isinstance(raw, str):
                raw = str(raw)
            if name:
                _process_tool_result(name, raw)

    return files


def _looks_like_file(path: str) -> bool:
    """Heuristic: does the normalized path look like a real file?"""
    if not path or len(path) < 2:
        return False
    # Must have an extension
    basename = path.rsplit("/", 1)[-1] if "/" in path else path
    if "." not in basename:
        return False
    # Skip obvious non-files
    if path.startswith(("http:", "https:", "ftp:")):
        return False
    # Skip grep-like output lines (contain line numbers after filename)
    if re.search(r"-\d+-", path) or re.search(r":\d+:", path):
        return False
    # Skip lines that look like code snippets
    if any(c in path for c in ("(", ")", "{", "}", "=", ";", "#", "\\", "  ")):
        return False
    # Path should be reasonably short
    if len(path) > 200:
        return False
    return True
