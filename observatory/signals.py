"""Signal extraction from trial directories.

Reads result.json, task_metrics.json, and trajectory.json from a trial
directory and produces a flat signal dict suitable for heuristic annotation.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict | None:
    """Load a JSON file, returning None if missing or malformed."""
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None


def _extract_reward(data: dict) -> float | None:
    """Extract reward from result.json (mirrors aggregate_status.py)."""
    verifier = data.get("verifier_result") or {}
    rewards = verifier.get("rewards") or {}
    reward = rewards.get("reward")
    if reward is None:
        reward = rewards.get("score")
    if reward is not None:
        return float(reward)
    return None


# --- Tool name sets for trajectory pattern detection ---

_SEARCH_TOOLS = frozenset({
    "Grep", "Glob", "grep", "rg",
    "sg_keyword_search", "sg_nls_search", "keyword_search",
    "nls_search", "deepsearch", "deepsearch_read", "deep_search",
    "mcp__sg_keyword_search", "mcp__sg_nls_search",
    "mcp__keyword_search", "mcp__nls_search",
    "mcp__deepsearch", "mcp__deepsearch_read", "mcp__deep_search",
    "mcp__sourcegraph__sg_keyword_search", "mcp__sourcegraph__sg_nls_search",
    "mcp__sourcegraph__sg_diff_search", "mcp__sourcegraph__sg_commit_search",
    "WebSearch",
})

_EDIT_TOOLS = frozenset({
    "Edit", "Write", "file_write", "NotebookEdit",
})

_TEST_COMMAND_PATTERNS = (
    "pytest", "python -m pytest", "npm test", "npm run test",
    "yarn test", "cargo test", "go test", "make test",
    "jest", "mocha", "ruby -e", "rspec", "test.sh", "./test",
    "bash test", "sh test",
)

_CODE_NAV_TOOLS = frozenset({
    "go_to_definition", "find_references", "sg_get_symbol",
    "mcp__go_to_definition", "mcp__find_references", "mcp__sg_get_symbol",
    "mcp__sourcegraph__sg_go_to_definition", "mcp__sourcegraph__sg_find_references",
    "ToolSearch",
})

_SEMANTIC_SEARCH_TOOLS = frozenset({
    "sg_nls_search", "nls_search", "deepsearch", "deepsearch_read",
    "deep_search",
    "mcp__sg_nls_search", "mcp__nls_search",
    "mcp__deepsearch", "mcp__deepsearch_read", "mcp__deep_search",
    "mcp__sourcegraph__sg_nls_search",
})


def _extract_search_query(tc: dict) -> str | None:
    """Extract the query/pattern string from a search tool call."""
    args = tc.get("arguments") or {}
    if isinstance(args, str):
        return args
    for key in ("pattern", "query", "search_query", "q"):
        if key in args:
            return str(args[key])
    return None


def _is_test_bash(tc: dict) -> bool:
    """Check if a Bash tool call is running tests."""
    if tc.get("function_name") != "Bash":
        return False
    args = tc.get("arguments") or {}
    cmd = args.get("command", "") if isinstance(args, dict) else str(args)
    cmd_lower = cmd.lower()
    return any(p in cmd_lower for p in _TEST_COMMAND_PATTERNS)


def _observation_indicates_failure(step: dict) -> bool:
    """Heuristic: check if a step's observation suggests test failure."""
    obs = step.get("observation") or {}
    results = obs.get("results") or []
    for r in results:
        content = str(r.get("content", ""))
        lower = content.lower()
        if any(kw in lower for kw in (
            "fail", "error", "assert", "exception",
            "exit code 1", "exit code 2", "non-zero",
            "failed", "failures", "errors",
        )):
            return True
    return False


def _detect_trajectory_patterns(traj: dict | None) -> dict:
    """Detect behavioral patterns in trajectory data.

    Returns a dict with pattern signals:
      - query_churn_count: number of distinct search queries
      - edit_verify_cycles: count of edit->test->fail patterns
      - repeated_tool_failures: count of consecutive same-tool errors
      - has_code_nav_tools: whether go-to-def/find-references were used
      - has_semantic_search: whether NLS/deepsearch was used
    """
    defaults = {
        "query_churn_count": None,
        "edit_verify_cycles": None,
        "repeated_tool_failures": None,
        "has_code_nav_tools": None,
        "has_semantic_search": None,
        "has_git_tools": None,
    }
    if traj is None:
        return defaults

    steps = traj.get("steps") or []
    if not steps:
        return {
            "query_churn_count": 0,
            "edit_verify_cycles": 0,
            "repeated_tool_failures": 0,
            "has_code_nav_tools": False,
            "has_semantic_search": False,
            "has_git_tools": False,
        }

    # Flatten all tool calls with their step context into a sequence
    flat_calls: list[tuple[dict, dict]] = []  # (tool_call, parent_step)
    seen_queries: set[str] = set()
    has_code_nav = False
    has_semantic = False
    has_git = False

    _GIT_HISTORY_COMMANDS = ("git log", "git blame", "git diff", "git show")

    for step in steps:
        for tc in step.get("tool_calls") or []:
            fn = tc.get("function_name", "")
            flat_calls.append((tc, step))

            # Code nav detection
            if fn in _CODE_NAV_TOOLS:
                has_code_nav = True

            # Semantic search detection
            if fn in _SEMANTIC_SEARCH_TOOLS:
                has_semantic = True

            # Git history tool detection (Bash calls with git log/blame/diff/show)
            if not has_git and fn == "Bash":
                args = tc.get("arguments") or {}
                cmd = args.get("command", "") if isinstance(args, dict) else str(args)
                if any(gc in cmd for gc in _GIT_HISTORY_COMMANDS):
                    has_git = True

            # Collect distinct search queries
            if fn in _SEARCH_TOOLS:
                q = _extract_search_query(tc)
                if q:
                    seen_queries.add(q)

    query_churn_count = len(seen_queries)

    # --- Edit-verify cycle detection ---
    # Walk flat_calls looking for: edit tool -> test bash -> observation failure
    edit_verify_cycles = 0
    i = 0
    while i < len(flat_calls) - 1:
        tc, _step = flat_calls[i]
        fn = tc.get("function_name", "")
        if fn in _EDIT_TOOLS:
            # Look ahead for a test command
            j = i + 1
            while j < len(flat_calls):
                next_tc, next_step = flat_calls[j]
                next_fn = next_tc.get("function_name", "")
                if _is_test_bash(next_tc):
                    if _observation_indicates_failure(next_step):
                        edit_verify_cycles += 1
                    break
                elif next_fn in _EDIT_TOOLS:
                    # Another edit before any test — stop lookahead
                    break
                j += 1
        i += 1

    # --- Repeated tool failures ---
    # Count runs of consecutive same-tool calls where observation indicates failure
    repeated_tool_failures = 0
    prev_fn: str | None = None
    consecutive_fails = 0
    for tc, step in flat_calls:
        fn = tc.get("function_name", "")
        if fn == prev_fn and _observation_indicates_failure(step):
            consecutive_fails += 1
            if consecutive_fails >= 2:
                repeated_tool_failures += 1
        else:
            consecutive_fails = 1 if _observation_indicates_failure(step) else 0
            prev_fn = fn

    return {
        "query_churn_count": query_churn_count,
        "edit_verify_cycles": edit_verify_cycles,
        "repeated_tool_failures": repeated_tool_failures,
        "has_code_nav_tools": has_code_nav,
        "has_semantic_search": has_semantic,
        "has_git_tools": has_git,
    }


def _get(d: dict | None, *keys: str, default: Any = None) -> Any:
    """Safely traverse nested dicts. Returns *default* on any miss or None."""
    val = d
    for k in keys:
        if not isinstance(val, dict):
            return default
        val = val.get(k)
    return val if val is not None else default


def _load_suite_mapping() -> dict[str, str]:
    """Load the canonical suite prefix mapping from configs/suite_mapping.json.

    Returns a dict of prefix -> suite_name, sorted longest-prefix-first
    so that e.g. 'crossrepo_tracing_' matches before 'crossrepo_'.
    """
    mapping_path = Path(__file__).resolve().parent.parent / "configs" / "suite_mapping.json"
    try:
        with open(mapping_path) as f:
            data = json.load(f)
        raw = data.get("mapping", {})
        # Sort by descending prefix length for correct longest-match
        return dict(sorted(raw.items(), key=lambda x: -len(x[0])))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


_suite_mapping: dict[str, str] | None = None


def _benchmark_from_path(trial_dir: Path) -> str | None:
    """Detect benchmark suite from the run directory name in the trial path.

    Uses the canonical suite_mapping.json prefix table (longest-prefix-first).
    Path pattern: .../_raw/{run_name}/{config}/...
    """
    global _suite_mapping
    if _suite_mapping is None:
        _suite_mapping = _load_suite_mapping()

    parts = trial_dir.resolve().parts
    try:
        idx = parts.index("_raw")
    except ValueError:
        return None
    if idx + 1 >= len(parts):
        return None

    run_name = parts[idx + 1]
    for prefix, suite in _suite_mapping.items():
        if run_name.startswith(prefix):
            return suite
    return None


_MODEL_KEYWORDS = {
    "opus": "anthropic/claude-opus-4-5-20251101",
    "sonnet": "anthropic/claude-sonnet-4-6",
    "sonnet46": "anthropic/claude-sonnet-4-6",
    "haiku": "anthropic/claude-haiku-4-5-20251001",
    "haiku45": "anthropic/claude-haiku-4-5-20251001",
}


def _model_from_path(trial_dir: Path) -> str | None:
    """Extract model name from the run directory name.

    Run names typically contain a model keyword: e.g.,
    ``csb_org_migration_haiku_20260302_175827``.
    """
    parts = trial_dir.resolve().parts
    try:
        idx = parts.index("_raw")
    except ValueError:
        return None
    if idx + 1 >= len(parts):
        return None
    run_name = parts[idx + 1]
    # Split on _ and check each segment against known model keywords
    for segment in run_name.split("_"):
        if segment in _MODEL_KEYWORDS:
            return _MODEL_KEYWORDS[segment]
    return None


def _config_from_path(trial_dir: Path) -> str | None:
    """Extract config name from the trial directory path.

    Expected layout: .../_raw/{run_name}/{config}/{timestamp}/{task}__{hash}/
    The config is the second component after ``_raw``.

    Special cases:
    - ``_errored`` directories: return ``"_errored"`` — these are quarantined
      trials that failed before config assignment.
    - Flat layouts where the second component is a timestamp: return the run
      name itself as the config (e.g., ``feature_haiku_vscode_rerun_*``).
    """
    parts = trial_dir.resolve().parts
    try:
        idx = parts.index("_raw")
    except ValueError:
        return None
    # _raw / run_name / config
    if idx + 2 < len(parts):
        candidate = parts[idx + 2]
        # _errored is a meaningful label for quarantined trials
        if candidate == "_errored":
            return "_errored"
        # Other _ prefixed dirs: skip
        if candidate.startswith("_"):
            return None
        # Timestamps (YYYY-MM-DD__HH-MM-SS) mean flat layout — use run name
        if len(candidate) >= 4 and candidate[:4].isdigit() and "-" in candidate[:5]:
            return parts[idx + 1]
        return candidate
    return None


def extract_signals(trial_dir: Path) -> dict:
    """Extract quantitative reliability signals from a single trial directory.

    Reads whichever of result.json, task_metrics.json, and
    agent/trajectory.json are present.  Missing files or fields are
    represented as ``None`` — the function never crashes on absent data.

    Parameters
    ----------
    trial_dir : Path
        Path to a trial directory (contains result.json at minimum).

    Returns
    -------
    dict
        Flat signal dictionary with the keys documented in US-005.
    """
    result = _load_json(trial_dir / "result.json")
    metrics = _load_json(trial_dir / "task_metrics.json")
    traj = _load_json(trial_dir / "agent" / "trajectory.json")

    # --- reward / passed ---
    reward = None
    if metrics:
        reward = metrics.get("reward")
    if reward is None and result:
        reward = _extract_reward(result)

    passed = None
    if metrics and "status" in metrics:
        passed = metrics["status"] == "passed"
    elif reward is not None:
        passed = reward > 0

    # --- tool counts (prefer task_metrics.json, fall back to trajectory) ---
    tool_calls_total = _get(metrics, "tool_calls_total")
    tool_calls_by_name: dict | None = _get(metrics, "tool_calls_by_name")
    search_calls_keyword = _get(metrics, "search_calls_keyword")
    search_calls_nls = _get(metrics, "search_calls_nls")
    search_calls_deepsearch = _get(metrics, "search_calls_deepsearch")
    mcp_ratio = _get(metrics, "mcp_ratio")

    # If task_metrics is missing, derive tool counts from trajectory
    if tool_calls_total is None and traj:
        by_name: dict[str, int] = {}
        for step in traj.get("steps") or []:
            for tc in step.get("tool_calls") or []:
                fn = tc.get("function_name", "unknown")
                by_name[fn] = by_name.get(fn, 0) + 1
        tool_calls_by_name = by_name
        tool_calls_total = sum(by_name.values())

    # --- exception ---
    has_exception = None
    if result:
        exc = result.get("exception_info")
        has_exception = exc is not None and exc != {}

    # --- timing ---
    wall_clock_seconds = _get(metrics, "wall_clock_seconds")
    ttfr = _get(metrics, "ttfr")

    # Fall back to result.json timestamps
    if wall_clock_seconds is None and result:
        started = result.get("started_at")
        finished = result.get("finished_at")
        if started and finished:
            from datetime import datetime, timezone

            try:
                t0 = datetime.fromisoformat(started.replace("Z", "+00:00"))
                t1 = datetime.fromisoformat(finished.replace("Z", "+00:00"))
                wall_clock_seconds = (t1 - t0).total_seconds()
            except (ValueError, TypeError):
                pass

    # --- tokens / cost ---
    input_tokens = _get(metrics, "input_tokens")
    output_tokens = _get(metrics, "output_tokens")
    cost_usd = _get(metrics, "cost_usd")

    if input_tokens is None and result:
        agent_res = result.get("agent_result") or {}
        input_tokens = agent_res.get("n_input_tokens")
        output_tokens = agent_res.get("n_output_tokens")
        cost_usd = agent_res.get("cost_usd")

    # --- trajectory presence ---
    has_trajectory = traj is not None
    trajectory_steps = len(traj.get("steps") or []) if traj else None

    # --- trajectory pattern detection (US-006) ---
    patterns = _detect_trajectory_patterns(traj)

    # --- metadata for downstream grouping ---
    task_id = _get(metrics, "task_id") or _get(result, "task_name")
    config_name = _get(metrics, "config_name")
    benchmark = _get(metrics, "benchmark")
    model = _get(metrics, "model") or _get(result, "agent_info", "model_info", "name")

    # --- metadata fallback chain ---
    # Load config.json once for multiple fallbacks.
    config_json = None
    if not config_name or not benchmark or not model:
        config_json = _load_json(trial_dir / "config.json")

    if not config_name:
        config_name = _config_from_path(trial_dir)

    if not benchmark:
        benchmark = _get(config_json, "environment", "kwargs", "label_benchmark")
    if not benchmark:
        benchmark = _benchmark_from_path(trial_dir)

    # Model fallback: config.json agents[0].model_name, then run dir name parsing
    if not model and config_json:
        agents = config_json.get("agents") or []
        if agents and isinstance(agents[0], dict):
            model = agents[0].get("model_name")
    if not model:
        model = _model_from_path(trial_dir)

    return {
        "trial_path": str(trial_dir),
        "task_id": task_id,
        "config_name": config_name,
        "benchmark": benchmark,
        "model": model,
        "reward": reward,
        "passed": passed,
        "tool_calls_total": tool_calls_total,
        "tool_calls_by_name": tool_calls_by_name,
        "search_calls_keyword": search_calls_keyword,
        "search_calls_nls": search_calls_nls,
        "search_calls_deepsearch": search_calls_deepsearch,
        "mcp_ratio": mcp_ratio,
        "has_exception": has_exception,
        "wall_clock_seconds": wall_clock_seconds,
        "ttfr": ttfr,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost_usd": cost_usd,
        "has_trajectory": has_trajectory,
        "trajectory_steps": trajectory_steps,
        "query_churn_count": patterns["query_churn_count"],
        "edit_verify_cycles": patterns["edit_verify_cycles"],
        "repeated_tool_failures": patterns["repeated_tool_failures"],
        "has_code_nav_tools": patterns["has_code_nav_tools"],
        "has_semantic_search": patterns["has_semantic_search"],
        "has_git_tools": patterns["has_git_tools"],
    }


def _iter_trial_dirs(runs_dir: Path):
    """Yield trial directory paths under a runs/_raw/ tree.

    Handles multiple nesting layouts:
      - runs_dir/{run}/{config}/{timestamp}/{task}__{hash}/
      - runs_dir/{run}/{config}/{task}__{hash}/
      - runs_dir/{config}/{task}__{hash}/

    A directory is considered a trial if it contains ``result.json``.
    """
    for result_file in sorted(runs_dir.rglob("result.json")):
        trial_dir = result_file.parent
        # Skip nested dirs that also contain result.json higher up
        # (e.g., config-level result.json aggregates). A trial dir should
        # also have an agent/ subfolder or at minimum not be a config dir.
        if (trial_dir / "agent").is_dir() or (trial_dir / "task_metrics.json").exists():
            yield trial_dir


def extract_all(runs_dir: Path) -> list[dict]:
    """Walk a runs directory and extract signals from every trial.

    Parameters
    ----------
    runs_dir : Path
        Root of the raw run data (e.g. ``runs/official/_raw``).

    Returns
    -------
    list[dict]
        One signal dict per trial.
    """
    signals: list[dict] = []
    for trial_dir in _iter_trial_dirs(runs_dir):
        signals.append(extract_signals(trial_dir))
    return signals
