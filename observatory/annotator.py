"""Heuristic annotator for the Agent Reliability Observatory.

Applies rule-based heuristics to extracted signal vectors and produces
candidate taxonomy annotations.  Each rule maps signal conditions to a
category with a numeric confidence level (0-1) and an evidence string.

Rules are drawn from docs/prd/OBSERVATORY_PRD.md section 8.
"""

from __future__ import annotations

import statistics
from datetime import datetime, timezone
from typing import Any

from observatory.taxonomy import load_taxonomy

# Confidence levels mapped to numeric values (schema uses 0-1).
_HIGH = 0.9
_MEDIUM = 0.6
_LOW = 0.3


def _safe_get(signals: dict, key: str, default: Any = None) -> Any:
    """Get a signal value, treating None as *default*."""
    val = signals.get(key)
    return val if val is not None else default


def annotate_trial(
    signals: dict,
    corpus_stats: dict | None = None,
) -> list[dict]:
    """Apply heuristic rules to a signal vector and return category assignments.

    Parameters
    ----------
    signals : dict
        Signal vector produced by ``extract_signals()``.
    corpus_stats : dict, optional
        Corpus-level statistics for threshold-based rules.  Expected keys:
        ``tool_calls_mean``, ``tool_calls_std``.

    Returns
    -------
    list[dict]
        Category assignments, each with keys *name*, *confidence*, *evidence*.
    """
    categories: list[dict] = []

    reward = signals.get("reward")
    has_exception = signals.get("has_exception")
    tool_calls_total = signals.get("tool_calls_total")
    search_keyword = _safe_get(signals, "search_calls_keyword", 0)
    search_nls = _safe_get(signals, "search_calls_nls", 0)
    search_deep = _safe_get(signals, "search_calls_deepsearch", 0)
    total_search = search_keyword + search_nls + search_deep
    mcp_ratio = signals.get("mcp_ratio")
    wall_clock = signals.get("wall_clock_seconds")
    ttfr = signals.get("ttfr")
    query_churn = signals.get("query_churn_count")
    edit_cycles = signals.get("edit_verify_cycles")
    has_code_nav = signals.get("has_code_nav_tools")
    has_semantic = signals.get("has_semantic_search")
    config_name = signals.get("config_name") or ""

    # ── Failure modes ────────────────────────────────────────────

    # exception_crash: exception_info non-null (high)
    if has_exception is True:
        categories.append({
            "name": "exception_crash",
            "confidence": _HIGH,
            "evidence": "exception_info non-null in result.json",
        })

    # rate_limited_run: wall_clock < 30s AND reward = 0 (high)
    if (reward is not None and reward == 0
            and wall_clock is not None and wall_clock < 30):
        categories.append({
            "name": "rate_limited_run",
            "confidence": _HIGH,
            "evidence": f"wall_clock={wall_clock:.1f}s (<30s) with reward=0",
        })

    # Partial reward: near_miss (>= 0.5) vs minimal_progress (< 0.5)
    if reward is not None and 0 < reward < 1.0:
        if reward >= 0.5:
            categories.append({
                "name": "near_miss",
                "confidence": _HIGH,
                "evidence": f"reward={reward:.2f} (close to full solution, >= 0.5)",
            })
        else:
            categories.append({
                "name": "minimal_progress",
                "confidence": _HIGH,
                "evidence": f"reward={reward:.2f} (partial progress, < 0.5)",
            })

    # edit_verify_loop_failure: >=3 edit-verify-fail cycles (high)
    if edit_cycles is not None and edit_cycles >= 3:
        categories.append({
            "name": "edit_verify_loop_failure",
            "confidence": _HIGH,
            "evidence": (
                f"edit_verify_cycles={edit_cycles} "
                "(>=3 edit->test->fail cycles)"
            ),
        })

    # retrieval_failure: reward < 0.5, search_calls > 3, ttfr missing (medium)
    if (reward is not None and reward < 0.5
            and total_search > 3
            and ttfr is None):
        categories.append({
            "name": "retrieval_failure",
            "confidence": _MEDIUM,
            "evidence": (
                f"reward={reward}, total_search_calls={total_search} (>3), "
                "ttfr=None (never found relevant file)"
            ),
        })

    # query_churn: >=4 distinct search queries (medium)
    if query_churn is not None and query_churn >= 4:
        categories.append({
            "name": "query_churn",
            "confidence": _MEDIUM,
            "evidence": f"query_churn_count={query_churn} (>=4 distinct queries)",
        })

    # over_exploration: tool_calls > mean+2σ AND reward=0 (medium)
    if (corpus_stats is not None
            and tool_calls_total is not None
            and reward is not None and reward == 0):
        mean = corpus_stats.get("tool_calls_mean", 0)
        std = corpus_stats.get("tool_calls_std", 0)
        threshold = mean + 2 * std
        if threshold > 0 and tool_calls_total > threshold:
            categories.append({
                "name": "over_exploration",
                "confidence": _MEDIUM,
                "evidence": (
                    f"tool_calls_total={tool_calls_total} > "
                    f"{threshold:.0f} (mean+2\u03c3) with reward=0"
                ),
            })

    # over_exploration (repeated failures): repeated_tool_failures >= 5 AND reward < 0.5
    repeated_failures = _safe_get(signals, "repeated_tool_failures", 0)
    if repeated_failures >= 5 and reward is not None and reward < 0.5:
        categories.append({
            "name": "over_exploration",
            "confidence": _MEDIUM,
            "evidence": (
                f"repeated_tool_failures={repeated_failures} (>=5) "
                f"with reward={reward}"
            ),
        })

    # missing_code_navigation: no code-nav tools on crossrepo/tracing/dep/migration tasks (medium)
    benchmark = _safe_get(signals, "benchmark", "")
    if (reward is not None and reward < 0.5
            and has_code_nav is False
            and any(kw in benchmark for kw in ("crossrepo", "tracing", "dep", "migration"))):
        categories.append({
            "name": "missing_code_navigation",
            "confidence": _MEDIUM,
            "evidence": (
                f"reward={reward}, has_code_nav_tools=False, "
                f"benchmark='{benchmark}' matches crossrepo/tracing/dep/migration pattern"
            ),
        })

    # wrong_tool_choice: MCP available, mcp_ratio=0, reward=0 (low)
    if (reward is not None and reward == 0
            and mcp_ratio is not None and mcp_ratio == 0
            and any(k in config_name for k in ("sourcegraph", "mcp"))):
        categories.append({
            "name": "wrong_tool_choice",
            "confidence": _LOW,
            "evidence": (
                f"config={config_name} has MCP tools but "
                "mcp_ratio=0, reward=0"
            ),
        })

    # ── Success modes ────────────────────────────────────────────

    # success_via_code_nav: reward >= 0.5 AND code-nav tools used (medium)
    if (reward is not None and reward >= 0.5
            and has_code_nav is True):
        categories.append({
            "name": "success_via_code_nav",
            "confidence": _MEDIUM,
            "evidence": "reward>=0.5 with go-to-def/find-references tool usage",
        })

    # success_via_semantic_search: reward >= 0.5 AND NLS/deepsearch (medium)
    if (reward is not None and reward >= 0.5
            and (search_nls > 0 or search_deep > 0)):
        categories.append({
            "name": "success_via_semantic_search",
            "confidence": _MEDIUM,
            "evidence": (
                f"reward={reward:.2f} with "
                f"nls={search_nls}, deepsearch={search_deep}"
            ),
        })

    # success_via_commit_context: reward >= 0.5 AND git history tools used (medium)
    has_git_tools = signals.get("has_git_tools")
    if (reward is not None and reward >= 0.5
            and has_git_tools is True):
        categories.append({
            "name": "success_via_commit_context",
            "confidence": _MEDIUM,
            "evidence": "reward>=0.5 with git log/blame/diff/show usage in trajectory",
        })

    # success_via_local_exec: reward >= 0.5 AND edit-verify present (medium)
    if (reward is not None and reward >= 0.5
            and edit_cycles is not None and edit_cycles >= 1):
        categories.append({
            "name": "success_via_local_exec",
            "confidence": _MEDIUM,
            "evidence": (
                f"reward={reward:.2f} with {edit_cycles} "
                "edit-verify cycle(s) showing test-driven iteration"
            ),
        })

    return categories


def compute_corpus_stats(signals_list: list[dict]) -> dict[str, float]:
    """Compute corpus-level statistics needed by threshold-based rules."""
    tool_counts = [
        s["tool_calls_total"]
        for s in signals_list
        if s.get("tool_calls_total") is not None
    ]
    stats: dict[str, float] = {}
    if len(tool_counts) >= 2:
        stats["tool_calls_mean"] = statistics.mean(tool_counts)
        stats["tool_calls_std"] = statistics.stdev(tool_counts)
    elif len(tool_counts) == 1:
        stats["tool_calls_mean"] = tool_counts[0]
        stats["tool_calls_std"] = 0.0
    return stats


def annotate_all(signals_list: list[dict]) -> dict:
    """Annotate all trials and return a full annotation document.

    Computes corpus-level statistics needed by threshold-based rules
    (e.g. over_exploration), then applies heuristic rules to each trial.
    Only trials with at least one matching rule are included.

    Parameters
    ----------
    signals_list : list[dict]
        List of signal dicts from ``extract_all()``.

    Returns
    -------
    dict
        Annotation document matching ``observatory/annotation_schema.json``.
    """
    corpus_stats = compute_corpus_stats(signals_list)

    taxonomy = load_taxonomy()
    now = datetime.now(timezone.utc).isoformat()

    annotations: list[dict] = []
    for sig in signals_list:
        cats = annotate_trial(sig, corpus_stats=corpus_stats)
        if not cats:
            continue

        reward_val = sig.get("reward")
        annotation: dict[str, Any] = {
            "task_id": sig.get("task_id") or "unknown",
            "trial_path": sig.get("trial_path") or "",
            "reward": float(reward_val) if reward_val is not None else 0.0,
            "passed": bool(sig.get("passed")) if sig.get("passed") is not None else False,
            "categories": cats,
            "annotated_at": now,
        }
        # Optional metadata (only include if present)
        for key in ("config_name", "benchmark", "model"):
            if sig.get(key):
                annotation[key] = sig[key]

        annotations.append(annotation)

    return {
        "schema_version": "observatory-annotation-v1",
        "taxonomy_version": str(taxonomy["version"]),
        "generated_at": now,
        "annotator": {
            "type": "heuristic",
            "identity": "observatory.annotator v0.1",
        },
        "annotations": annotations,
    }
