"""csb report — display benchmark results with CSB Score prominently.

Reads a submission JSON and renders a formatted summary in text, JSON, or HTML.

View modes:
  - (default): current flat per-task listing with per-work-type breakdown
  - --summary: scores and annotations grouped by taxonomy v2 dimensions
  - --detailed: per-leaf-category breakdown with tasks listed under each
  - --browser: interactive localhost dashboard with all views + baseline comparison
"""

from __future__ import annotations

import html as html_mod
import http.server
import json
import sys
import threading
import webbrowser
from collections import defaultdict
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def load_submission(results_path: str | Path) -> dict[str, Any]:
    """Load and return a submission JSON file."""
    path = Path(results_path)
    if not path.exists():
        raise FileNotFoundError(f"Results file not found: {path}")
    with open(path) as f:
        return json.load(f)


def _load_category_to_dimension_map() -> dict[str, str]:
    """Load taxonomy v2 and return a mapping of leaf category name -> dimension name.

    Returns an empty dict if taxonomy_v2.yaml is not found or cannot be parsed.
    """
    taxonomy_path = _REPO_ROOT / "observatory" / "taxonomy_v2.yaml"
    if not taxonomy_path.exists():
        return {}
    try:
        from observatory.taxonomy import load_taxonomy

        taxonomy = load_taxonomy(taxonomy_path)
        if "dimensions" not in taxonomy:
            return {}
        cat_to_dim: dict[str, str] = {}
        for dimension in taxonomy["dimensions"]:
            dim_name = dimension["name"]
            for cat in dimension.get("categories", []):
                cat_to_dim[cat["name"]] = dim_name
        return cat_to_dim
    except Exception:
        return {}


def _aggregate_by_dimension(
    results: list[dict[str, Any]],
    cat_to_dim: dict[str, str],
) -> dict[str, dict[str, Any]]:
    """Aggregate results by taxonomy v2 dimensions.

    Returns a dict keyed by dimension name, each containing:
      - tasks: number of tasks with annotations in that dimension
      - mean_reward: mean reward across those tasks
      - rewards: list of rewards
      - categories: dict of category_name -> count
      - task_names: list of task names
    """
    dim_data: dict[str, dict[str, Any]] = {}
    for r in results:
        for fc in r.get("failure_categories", []):
            cat_name = fc.get("category", "")
            dim_name = cat_to_dim.get(cat_name, "Unknown")
            if dim_name not in dim_data:
                dim_data[dim_name] = {
                    "tasks": set(),
                    "rewards": [],
                    "categories": defaultdict(int),
                    "task_names": [],
                }
            entry = dim_data[dim_name]
            task_name = r.get("task_name", "unknown")
            if task_name not in entry["tasks"]:
                entry["tasks"].add(task_name)
                entry["rewards"].append(r.get("reward", 0.0))
                entry["task_names"].append(task_name)
            entry["categories"][cat_name] += 1

    # Convert sets to counts
    result: dict[str, dict[str, Any]] = {}
    for dim_name in sorted(dim_data):
        entry = dim_data[dim_name]
        rewards = entry["rewards"]
        mean_r = sum(rewards) / len(rewards) if rewards else 0.0
        result[dim_name] = {
            "task_count": len(entry["tasks"]),
            "mean_reward": mean_r,
            "annotation_count": sum(entry["categories"].values()),
            "categories": dict(sorted(entry["categories"].items())),
        }
    return result


def _aggregate_by_leaf_category(
    results: list[dict[str, Any]],
    cat_to_dim: dict[str, str],
) -> dict[str, dict[str, Any]]:
    """Aggregate results by leaf category.

    Returns a dict keyed by category name, each containing:
      - dimension: parent dimension name
      - count: number of annotations
      - tasks: list of (task_name, reward) tuples
    """
    cat_data: dict[str, dict[str, Any]] = {}
    for r in results:
        for fc in r.get("failure_categories", []):
            cat_name = fc.get("category", "")
            if cat_name not in cat_data:
                cat_data[cat_name] = {
                    "dimension": cat_to_dim.get(cat_name, "Unknown"),
                    "count": 0,
                    "tasks": [],
                }
            cat_data[cat_name]["count"] += 1
            cat_data[cat_name]["tasks"].append(
                (r.get("task_name", "unknown"), r.get("reward", 0.0))
            )
    return dict(sorted(cat_data.items(), key=lambda kv: (kv[1]["dimension"], kv[0])))


def display_report(
    results_path: str | Path,
    fmt: str = "text",
    open_browser: bool = False,
    view_mode: str | None = None,
) -> int:
    """Display a benchmark results report.

    Parameters
    ----------
    results_path:
        Path to the submission JSON file.
    fmt:
        Output format — "text", "json", or "html".
    open_browser:
        If True and fmt is "html", open the static report in a browser.
        For the interactive localhost dashboard, use ``serve_browser()``.
    view_mode:
        None for default, "summary" for dimension-level rollup,
        "detailed" for per-leaf-category breakdown.

    Returns
    -------
    int
        Exit code (0 on success, 1 on error).
    """
    try:
        submission = load_submission(results_path)
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"[csb report] ERROR: {exc}", file=sys.stderr)
        return 1

    if fmt == "json":
        print(json.dumps(submission, indent=2))
        return 0

    if fmt == "html":
        return _render_html(submission, results_path, open_browser)

    if view_mode == "summary":
        return _render_text_summary(submission)

    if view_mode == "detailed":
        return _render_text_detailed(submission)

    return _render_text(submission)


def _render_text(submission: dict[str, Any]) -> int:
    """Render a text report to stdout."""
    _render_text_header(submission)
    results = submission.get("results", [])

    # Per-work-type breakdown
    breakdown = _compute_work_type_breakdown(results)
    if len(breakdown) > 1 or "all" not in breakdown:
        print("  Per-work-type breakdown:")
        print(f"  {'Work Type':<20} {'Pass Rate':>10} {'Tasks':>6}")
        print(f"  {'-'*20} {'-'*10} {'-'*6}")
        for wt, stats in breakdown.items():
            rate = stats["pass_rate"] * 100
            print(f"  {wt:<20} {rate:>9.1f}% {stats['task_count']:>6}")
        print()

    # Per-task results
    print(f"  {'Task':<45} {'Reward':>7}")
    print(f"  {'-'*45} {'-'*7}")
    for r in results:
        task_name = r.get("task_name", "unknown")
        reward = r.get("reward", 0.0)
        # Truncate long task names
        display_name = task_name[:44] if len(task_name) > 44 else task_name
        marker = " *" if "error" in r else ""
        print(f"  {display_name:<45} {reward:>6.2f}{marker}")

    errors = [r for r in results if "error" in r]
    if errors:
        print()
        print(f"  * {len(errors)} task(s) had errors.")

    print()
    return 0


def _render_text_header(submission: dict[str, Any]) -> None:
    """Print the common CSB score header block."""
    csb_score = submission.get("csb_score", 0.0)
    suite = submission.get("suite", "unknown")
    agent_info = submission.get("agent_info", {})
    agent_name = agent_info.get("name", "unknown")
    metadata = submission.get("metadata", {})
    results = submission.get("results", [])

    print()
    print("=" * 60)
    print(f"  CSB SCORE: {csb_score:.1f} / 100")
    print("=" * 60)
    print()
    print(f"  Suite:     {suite}")
    print(f"  Agent:     {agent_name}")
    print(f"  Tasks:     {len(results)}")
    print(f"  Timestamp: {metadata.get('timestamp', 'N/A')}")
    print(f"  Version:   {metadata.get('csb_version', 'N/A')}")
    if metadata.get("run_id"):
        print(f"  Run ID:    {metadata['run_id']}")
    print()


def _render_text_summary(submission: dict[str, Any]) -> int:
    """Render a dimension-level summary report to stdout."""
    _render_text_header(submission)
    results = submission.get("results", [])

    cat_to_dim = _load_category_to_dimension_map()
    if not cat_to_dim:
        print(
            "  [WARN] taxonomy_v2.yaml not found; " "falling back to default report.",
            file=sys.stderr,
        )
        return _render_text(submission)

    dim_agg = _aggregate_by_dimension(results, cat_to_dim)

    if not dim_agg:
        print("  No taxonomy annotations found in results.")
        print()
        return 0

    print("  Dimension-Level Summary")
    print(f"  {'Dimension':<20} {'Mean Reward':>12} {'Tasks':>6} {'Annotations':>12}")
    print(f"  {'-'*20} {'-'*12} {'-'*6} {'-'*12}")
    for dim_name, stats in dim_agg.items():
        print(
            f"  {dim_name:<20} {stats['mean_reward']:>11.2f} "
            f"{stats['task_count']:>6} {stats['annotation_count']:>12}"
        )
    print()

    # Per-dimension category breakdown
    for dim_name, stats in dim_agg.items():
        print(f"  {dim_name}:")
        for cat_name, count in stats["categories"].items():
            print(f"    {cat_name:<35} {count:>4} annotations")
        print()

    return 0


def _render_text_detailed(submission: dict[str, Any]) -> int:
    """Render a per-leaf-category detailed report to stdout."""
    _render_text_header(submission)
    results = submission.get("results", [])

    cat_to_dim = _load_category_to_dimension_map()
    if not cat_to_dim:
        print(
            "  [WARN] taxonomy_v2.yaml not found; " "falling back to default report.",
            file=sys.stderr,
        )
        return _render_text(submission)

    cat_agg = _aggregate_by_leaf_category(results, cat_to_dim)

    if not cat_agg:
        print("  No taxonomy annotations found in results.")
        print()
        return 0

    print("  Per-Category Detailed Breakdown")
    print()

    current_dim = None
    for cat_name, info in cat_agg.items():
        dim = info["dimension"]
        if dim != current_dim:
            current_dim = dim
            print(f"  [{dim}]")

        print(f"    {cat_name} ({info['count']} annotations)")
        for task_name, reward in info["tasks"]:
            display_name = task_name[:40] if len(task_name) > 40 else task_name
            print(f"      {display_name:<42} {reward:.2f}")
        print()

    return 0


def _render_html(
    submission: dict[str, Any],
    results_path: str | Path,
    open_browser: bool,
) -> int:
    """Render an HTML report and optionally open in browser."""
    csb_score = submission.get("csb_score", 0.0)
    suite = html_mod.escape(str(submission.get("suite", "unknown")))
    agent_name = html_mod.escape(
        str(submission.get("agent_info", {}).get("name", "unknown"))
    )
    results = submission.get("results", [])
    metadata = submission.get("metadata", {})

    rows = ""
    for r in results:
        task_name = html_mod.escape(str(r.get("task_name", "unknown")))
        reward = r.get("reward", 0.0)
        color = (
            "#2ecc71" if reward >= 1.0 else "#e74c3c" if reward == 0.0 else "#f39c12"
        )
        rows += (
            f"<tr><td>{task_name}</td>"
            f"<td style='color:{color};font-weight:bold'>{reward:.2f}</td></tr>\n"
        )

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>CSB Report — {suite}</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
         max-width: 900px; margin: 40px auto; padding: 0 20px; background: #fafafa; }}
  .score-box {{ background: #2c3e50; color: white; padding: 30px; border-radius: 12px;
                text-align: center; margin-bottom: 30px; }}
  .score-box h1 {{ font-size: 3em; margin: 0; }}
  .score-box p {{ margin: 5px 0; opacity: 0.8; }}
  .meta {{ background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px;
           border: 1px solid #e0e0e0; }}
  table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 8px;
           overflow: hidden; border: 1px solid #e0e0e0; }}
  th {{ background: #34495e; color: white; padding: 12px; text-align: left; }}
  td {{ padding: 10px 12px; border-bottom: 1px solid #eee; }}
  tr:hover {{ background: #f5f5f5; }}
</style>
</head>
<body>
<div class="score-box">
  <h1>{csb_score:.1f}</h1>
  <p>CSB Score (out of 100)</p>
</div>
<div class="meta">
  <strong>Suite:</strong> {suite} |
  <strong>Agent:</strong> {agent_name} |
  <strong>Tasks:</strong> {len(results)} |
  <strong>Timestamp:</strong> {html_mod.escape(str(metadata.get('timestamp', 'N/A')))}
</div>
<table>
<tr><th>Task</th><th>Reward</th></tr>
{rows}
</table>
</body>
</html>"""

    # Write HTML next to results file
    html_path = Path(results_path).with_suffix(".html")
    with open(html_path, "w") as f:
        f.write(html_content)
    print(f"[csb report] HTML report written to: {html_path}", file=sys.stderr)

    if open_browser:
        webbrowser.open(str(html_path.resolve()))

    return 0


# ---------------------------------------------------------------------------
# Interactive browser (csb report --browser)
# ---------------------------------------------------------------------------


def _compute_work_type_breakdown(
    results: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Compute per-work-type pass rates and task counts."""
    buckets: dict[str, list[float]] = defaultdict(list)
    for r in results:
        wt = r.get("work_type", "all")
        try:
            reward = float(r.get("reward") or 0.0)
        except (TypeError, ValueError):
            reward = 0.0
        buckets[wt].append(reward)

    breakdown: dict[str, dict[str, Any]] = {}
    for wt in sorted(buckets):
        rewards = buckets[wt]
        passed = sum(1 for rw in rewards if rw >= 1.0)
        breakdown[wt] = {
            "pass_rate": passed / len(rewards) if rewards else 0.0,
            "task_count": len(rewards),
            "passed": passed,
            "mean_reward": sum(rewards) / len(rewards) if rewards else 0.0,
        }
    return breakdown


def _load_baseline_summary() -> dict[str, Any] | None:
    """Load a compact baseline summary from official results.

    Returns None if the file is unavailable. Extracts only suite_summaries
    and a per-task reward lookup to keep the embedded payload small.
    """
    baseline_path = (
        _REPO_ROOT / "docs" / "official_results" / "data" / "official_results.json"
    )
    if not baseline_path.exists():
        return None
    try:
        with open(baseline_path, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return None

    suite_summaries = data.get("suite_summaries", [])

    # Build compact per-task lookup: {task_name: [{config, reward}]}
    per_task: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for t in data.get("tasks", data.get("all_tasks", [])):
        task_name = t.get("task_name", "")
        if not task_name:
            continue
        per_task[task_name].append(
            {
                "config": t.get("config", "unknown"),
                "reward": t.get("reward", 0.0),
            }
        )

    return {
        "suite_summaries": suite_summaries,
        "per_task": dict(per_task),
    }


def _build_browser_data(
    submission: dict[str, Any],
    baseline: dict[str, Any] | None,
) -> dict[str, Any]:
    """Assemble all computed data into a single JSON-serializable dict."""
    results = submission.get("results", [])
    cat_to_dim = _load_category_to_dimension_map()
    dim_agg = _aggregate_by_dimension(results, cat_to_dim) if cat_to_dim else {}
    cat_agg = _aggregate_by_leaf_category(results, cat_to_dim) if cat_to_dim else {}

    # Convert cat_agg tasks from tuples to lists for JSON serialization
    cat_agg_serializable: dict[str, Any] = {}
    for cat_name, info in cat_agg.items():
        cat_agg_serializable[cat_name] = {
            "dimension": info["dimension"],
            "count": info["count"],
            "tasks": [[tn, rw] for tn, rw in info["tasks"]],
        }

    return {
        "submission": {
            "csb_score": submission.get("csb_score", 0.0),
            "suite": submission.get("suite", "unknown"),
            "agent_info": submission.get("agent_info", {}),
            "metadata": submission.get("metadata", {}),
            "task_count": len(results),
        },
        "work_type_breakdown": _compute_work_type_breakdown(results),
        "results": [
            {
                "task_name": r.get("task_name", "unknown"),
                "reward": r.get("reward", 0.0),
                "work_type": r.get("work_type", "all"),
                "failure_categories": r.get("failure_categories", []),
                "error": r.get("error"),
            }
            for r in results
        ],
        "dimensions": dim_agg,
        "leaf_categories": cat_agg_serializable,
        "baseline": baseline,
    }


def _render_browser_html(data: dict[str, Any]) -> str:
    """Generate a self-contained HTML page with embedded JSON data."""
    sub = data["submission"]
    title = html_mod.escape(
        f"{sub['agent_info'].get('name', 'Agent')} — {sub['suite']}"
    )
    # Escape <, >, & to prevent </script> injection (standard XSS prevention)
    data_json = (
        json.dumps(data, separators=(",", ":"))
        .replace("&", r"\u0026")
        .replace("<", r"\u003c")
        .replace(">", r"\u003e")
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CSB Report — {title}</title>
<style>
:root {{
  --bg: #0f1419; --panel: #182028; --text: #eef3f8; --muted: #9bb0c3;
  --accent: #47d18c; --warn: #ffcc66; --fail: #f87171; --partial: #fbbf24;
  --border: #2e3d4a;
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ font-family: ui-sans-serif, system-ui, -apple-system, sans-serif;
       background: var(--bg); color: var(--text); }}
.wrap {{ max-width: 1100px; margin: 0 auto; padding: 24px; }}
.mono {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }}

/* Score header */
.score-header {{ display: flex; align-items: center; gap: 32px;
                 background: var(--panel); border-radius: 12px; padding: 28px 36px;
                 margin-bottom: 20px; border: 1px solid var(--border); }}
.score-num {{ font-size: 3.2em; font-weight: 700; color: var(--accent); line-height: 1; }}
.score-label {{ color: var(--muted); font-size: 0.85em; }}
.score-meta {{ display: flex; flex-wrap: wrap; gap: 8px 24px; color: var(--muted); font-size: 0.85em; }}
.score-meta b {{ color: var(--text); font-weight: 500; }}

/* Tabs */
.tabs {{ display: flex; gap: 0; margin-bottom: 20px; border-bottom: 1px solid var(--border); }}
.tabs button {{ background: none; border: none; color: var(--muted); padding: 10px 20px;
               font-size: 0.9em; cursor: pointer; border-bottom: 2px solid transparent;
               transition: color 0.15s, border-color 0.15s; }}
.tabs button:hover {{ color: var(--text); }}
.tabs button.active {{ color: var(--accent); border-bottom-color: var(--accent); }}
.tab-panel {{ display: none; }}
.tab-panel.active {{ display: block; }}

/* Panels */
.panel {{ background: var(--panel); border-radius: 10px; padding: 24px;
          margin-bottom: 16px; border: 1px solid var(--border); }}
.panel h2 {{ font-size: 1.1em; margin-bottom: 16px; font-weight: 600; }}
.panel h3 {{ font-size: 0.95em; margin: 16px 0 10px; color: var(--muted); font-weight: 500; }}

/* Bar chart */
.bar-row {{ display: flex; align-items: center; gap: 12px; margin-bottom: 10px; }}
.bar-label {{ width: 120px; font-size: 0.85em; color: var(--muted); text-align: right;
              flex-shrink: 0; }}
.bar-track {{ flex: 1; height: 24px; background: rgba(255,255,255,0.05); border-radius: 6px;
              overflow: hidden; position: relative; }}
.bar-fill {{ height: 100%; border-radius: 6px; transition: width 0.4s ease; }}
.bar-value {{ width: 70px; font-size: 0.85em; text-align: right; flex-shrink: 0; }}

/* Tables */
table {{ width: 100%; border-collapse: collapse; }}
th {{ color: var(--muted); font-weight: 500; font-size: 0.8em; text-transform: uppercase;
     letter-spacing: 0.04em; padding: 10px 12px; text-align: left;
     border-bottom: 1px solid var(--border); }}
td {{ padding: 9px 12px; border-bottom: 1px solid rgba(255,255,255,0.04); font-size: 0.88em; }}
tr:hover td {{ background: rgba(255,255,255,0.03); }}
.reward-pass {{ color: var(--accent); font-weight: 600; }}
.reward-fail {{ color: var(--fail); font-weight: 600; }}
.reward-partial {{ color: var(--partial); font-weight: 600; }}

/* Dimension cards */
.dim-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 14px; }}
.dim-card {{ background: rgba(255,255,255,0.03); border-radius: 8px; padding: 16px;
             border: 1px solid var(--border); }}
.dim-card h4 {{ font-size: 0.95em; margin-bottom: 8px; }}
.dim-stat {{ display: flex; justify-content: space-between; font-size: 0.82em;
             color: var(--muted); margin-bottom: 4px; }}
.dim-cats {{ margin-top: 10px; font-size: 0.8em; }}
.dim-cats span {{ display: inline-block; background: rgba(71,209,140,0.12); color: var(--accent);
                  padding: 2px 8px; border-radius: 999px; margin: 2px 4px 2px 0; }}

/* Category detail */
.cat-group {{ margin-bottom: 20px; }}
.cat-group h4 {{ font-size: 0.88em; color: var(--accent); margin-bottom: 6px; cursor: pointer; }}
.cat-tasks {{ padding-left: 16px; font-size: 0.82em; color: var(--muted); }}

/* Filters */
.filters {{ display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 14px; }}
.filters select, .filters input {{ background: var(--panel); color: var(--text);
  border: 1px solid var(--border); border-radius: 8px; padding: 7px 10px; font-size: 0.85em; }}
.filters input {{ min-width: 200px; }}

/* Baseline */
.delta-pos {{ color: var(--accent); }}
.delta-neg {{ color: var(--fail); }}
.delta-zero {{ color: var(--muted); }}

/* Expandable row */
.expand-row td {{ padding: 0; }}
.expand-content {{ padding: 12px 20px; background: rgba(255,255,255,0.02);
                   font-size: 0.82em; color: var(--muted); }}
.expand-content .fc-item {{ margin-bottom: 6px; }}
.fc-cat {{ color: var(--warn); font-weight: 500; }}
.fc-conf {{ display: inline-block; width: 40px; text-align: right; margin-left: 8px; }}
.fc-evidence {{ display: block; padding-left: 16px; margin-top: 2px; font-size: 0.92em;
                color: var(--muted); opacity: 0.8; }}

.empty-msg {{ color: var(--muted); font-size: 0.9em; padding: 24px; text-align: center; }}
</style>
</head>
<body>
<div class="wrap">
  <div class="score-header">
    <div>
      <div class="score-num" id="csbScore"></div>
      <div class="score-label">CSB Score (0-100)</div>
    </div>
    <div class="score-meta" id="scoreMeta"></div>
  </div>
  <div class="tabs" id="tabBar">
    <button data-tab="overview" class="active">Overview</button>
    <button data-tab="observatory">Observatory</button>
    <button data-tab="baseline">Baseline</button>
    <button data-tab="tasks">Tasks</button>
  </div>
  <div id="tab-overview" class="tab-panel active"></div>
  <div id="tab-observatory" class="tab-panel"></div>
  <div id="tab-baseline" class="tab-panel"></div>
  <div id="tab-tasks" class="tab-panel"></div>
</div>
<script>
const D = {data_json};

// --- Utilities ---
function esc(s) {{ return s == null ? '-' : String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }}
function fmtR(v) {{ return v == null ? '-' : Number(v).toFixed(2); }}
function fmtPct(v) {{ return (v * 100).toFixed(1) + '%'; }}
function rewardClass(r) {{ return r >= 1 ? 'reward-pass' : r === 0 ? 'reward-fail' : 'reward-partial'; }}
function deltaClass(d) {{ return d > 0.005 ? 'delta-pos' : d < -0.005 ? 'delta-neg' : 'delta-zero'; }}
function deltaStr(d) {{ return (d > 0 ? '+' : '') + fmtR(d); }}

// --- Tabs ---
document.getElementById('tabBar').addEventListener('click', e => {{
  const btn = e.target.closest('button[data-tab]');
  if (!btn) return;
  document.querySelectorAll('.tabs button').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
  btn.classList.add('active');
  document.getElementById('tab-' + btn.dataset.tab).classList.add('active');
}});

// --- Score Header ---
document.getElementById('csbScore').textContent = D.submission.csb_score.toFixed(1);
const meta = D.submission;
document.getElementById('scoreMeta').innerHTML =
  '<div><b>Suite:</b> ' + esc(meta.suite) + '</div>' +
  '<div><b>Agent:</b> ' + esc((meta.agent_info||{{}}).name) + '</div>' +
  '<div><b>Tasks:</b> ' + meta.task_count + '</div>' +
  '<div><b>Timestamp:</b> ' + esc((meta.metadata||{{}}).timestamp) + '</div>' +
  (meta.metadata && meta.metadata.csb_version ? '<div><b>Version:</b> ' + esc(meta.metadata.csb_version) + '</div>' : '');

// --- Overview Tab ---
(function() {{
  const el = document.getElementById('tab-overview');
  const wt = D.work_type_breakdown;
  const types = Object.keys(wt);
  if (types.length === 0 || (types.length === 1 && types[0] === 'all')) {{
    el.innerHTML = '<div class="panel"><h2>Results Summary</h2>' +
      '<p style="color:var(--muted)">Total tasks: ' + D.results.length +
      ' | Overall pass rate: ' + fmtPct(D.results.filter(r=>r.reward>=1).length / Math.max(D.results.length,1)) + '</p></div>';
    return;
  }}
  let bars = '';
  for (const t of types) {{
    const pr = wt[t].pass_rate;
    const color = pr >= 0.7 ? 'var(--accent)' : pr >= 0.4 ? 'var(--warn)' : 'var(--fail)';
    bars += '<div class="bar-row">' +
      '<div class="bar-label">' + esc(t) + '</div>' +
      '<div class="bar-track"><div class="bar-fill" style="width:' + (pr*100) + '%;background:' + color + '"></div></div>' +
      '<div class="bar-value">' + fmtPct(pr) + ' <span style="color:var(--muted);font-size:0.85em">(' + wt[t].passed + '/' + wt[t].task_count + ')</span></div></div>';
  }}
  // Summary stats
  const total = D.results.length;
  const passed = D.results.filter(r => r.reward >= 1).length;
  const meanR = total ? (D.results.reduce((s,r) => s + r.reward, 0) / total) : 0;
  const errors = D.results.filter(r => r.error).length;
  el.innerHTML = '<div class="panel"><h2>Per-Work-Type Pass Rates</h2>' + bars + '</div>' +
    '<div class="panel"><h2>Summary</h2>' +
    '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:12px;font-size:0.9em">' +
    '<div><div style="color:var(--muted);font-size:0.8em">Total Tasks</div><div style="font-size:1.5em;font-weight:600">' + total + '</div></div>' +
    '<div><div style="color:var(--muted);font-size:0.8em">Passed</div><div style="font-size:1.5em;font-weight:600;color:var(--accent)">' + passed + '</div></div>' +
    '<div><div style="color:var(--muted);font-size:0.8em">Mean Reward</div><div style="font-size:1.5em;font-weight:600">' + fmtR(meanR) + '</div></div>' +
    (errors ? '<div><div style="color:var(--muted);font-size:0.8em">Errors</div><div style="font-size:1.5em;font-weight:600;color:var(--fail)">' + errors + '</div></div>' : '') +
    '</div></div>';
}})();

// --- Observatory Tab ---
(function() {{
  const el = document.getElementById('tab-observatory');
  const dims = D.dimensions;
  const cats = D.leaf_categories;
  const dimNames = Object.keys(dims);
  if (dimNames.length === 0) {{
    el.innerHTML = '<div class="empty-msg">No Observatory annotations found in results.</div>';
    return;
  }}
  // Dimension cards
  let cards = '<div class="dim-grid">';
  for (const dn of dimNames) {{
    const d = dims[dn];
    let catPills = '';
    for (const [cn, cnt] of Object.entries(d.categories)) {{
      catPills += '<span>' + esc(cn) + ' (' + cnt + ')</span>';
    }}
    cards += '<div class="dim-card"><h4>' + esc(dn) + '</h4>' +
      '<div class="dim-stat"><span>Tasks</span><span>' + d.task_count + '</span></div>' +
      '<div class="dim-stat"><span>Mean Reward</span><span>' + fmtR(d.mean_reward) + '</span></div>' +
      '<div class="dim-stat"><span>Annotations</span><span>' + d.annotation_count + '</span></div>' +
      '<div class="dim-cats">' + catPills + '</div></div>';
  }}
  cards += '</div>';

  // Leaf category details
  let details = '';
  let curDim = '';
  for (const [cn, info] of Object.entries(cats)) {{
    if (info.dimension !== curDim) {{
      if (curDim) details += '</div>';
      curDim = info.dimension;
      details += '<h3>[' + esc(curDim) + ']</h3><div>';
    }}
    let taskRows = '';
    for (const [tn, rw] of info.tasks) {{
      taskRows += '<div style="display:flex;justify-content:space-between">' +
        '<span>' + esc(tn) + '</span><span class="' + rewardClass(rw) + '">' + fmtR(rw) + '</span></div>';
    }}
    details += '<div class="cat-group"><h4>' + esc(cn) + ' (' + info.count + ' annotations)</h4>' +
      '<div class="cat-tasks">' + taskRows + '</div></div>';
  }}
  if (curDim) details += '</div>';

  el.innerHTML = '<div class="panel"><h2>Dimension Summary</h2>' + cards + '</div>' +
    '<div class="panel"><h2>Category Details</h2>' + (details || '<div class="empty-msg">No category details available.</div>') + '</div>';
}})();

// --- Baseline Tab ---
(function() {{
  const el = document.getElementById('tab-baseline');
  const bl = D.baseline;
  if (!bl) {{
    el.innerHTML = '<div class="empty-msg">Baseline data not available. Run from the CodeScaleBench repo root to enable comparison.</div>';
    return;
  }}

  // Suite-level comparison
  let suiteHtml = '';
  const ss = bl.suite_summaries || [];
  if (ss.length > 0) {{
    let rows = '';
    for (const s of ss) {{
      rows += '<tr><td>' + esc(s.suite) + '</td><td>' + esc(s.config) + '</td>' +
        '<td>' + fmtPct(s.pass_rate || 0) + '</td><td>' + s.task_count + '</td></tr>';
    }}
    suiteHtml = '<div class="panel"><h2>Official Baseline Results</h2>' +
      '<table><tr><th>Suite</th><th>Config</th><th>Pass Rate</th><th>Tasks</th></tr>' + rows + '</table></div>';
  }}

  // Per-task comparison
  const pt = bl.per_task || {{}};
  let matched = 0, userBetter = 0, blBetter = 0, ties = 0;
  let taskRows = '';
  for (const r of D.results) {{
    const blEntries = pt[r.task_name];
    if (!blEntries || blEntries.length === 0) continue;
    // Use best baseline reward across configs
    const bestBl = Math.max(...blEntries.map(e => e.reward));
    const delta = r.reward - bestBl;
    matched++;
    if (delta > 0.005) userBetter++;
    else if (delta < -0.005) blBetter++;
    else ties++;
    taskRows += '<tr><td class="mono" style="font-size:0.82em">' + esc(r.task_name) + '</td>' +
      '<td class="' + rewardClass(r.reward) + '">' + fmtR(r.reward) + '</td>' +
      '<td class="' + rewardClass(bestBl) + '">' + fmtR(bestBl) + '</td>' +
      '<td class="' + deltaClass(delta) + '">' + deltaStr(delta) + '</td></tr>';
  }}

  let matchHtml = '';
  if (matched > 0) {{
    matchHtml = '<div class="panel"><h2>Per-Task Comparison (' + matched + ' matched)</h2>' +
      '<div style="display:flex;gap:24px;margin-bottom:14px;font-size:0.85em;color:var(--muted)">' +
      '<span>You better: <b class="delta-pos">' + userBetter + '</b></span>' +
      '<span>Baseline better: <b class="delta-neg">' + blBetter + '</b></span>' +
      '<span>Tied: <b>' + ties + '</b></span></div>' +
      '<table><tr><th>Task</th><th>Your Reward</th><th>Baseline</th><th>Delta</th></tr>' +
      taskRows + '</table></div>';
  }} else {{
    matchHtml = '<div class="panel"><div class="empty-msg">No overlapping tasks found between your results and baseline.</div></div>';
  }}

  el.innerHTML = suiteHtml + matchHtml;
}})();

// --- Tasks Tab ---
(function() {{
  const el = document.getElementById('tab-tasks');
  const results = D.results;
  const workTypes = [...new Set(results.map(r => r.work_type))].sort();

  let filterHtml = '<div class="filters">' +
    '<input id="taskSearch" placeholder="Search task name...">' +
    '<select id="wtFilter"><option value="">All work types</option>' +
    workTypes.map(w => '<option value="' + esc(w) + '">' + esc(w) + '</option>').join('') + '</select>' +
    '<select id="statusFilter"><option value="">All</option><option value="pass">Passed</option><option value="fail">Failed</option><option value="partial">Partial</option></select>' +
    '</div>';

  el.innerHTML = filterHtml + '<div class="panel" style="padding:0;overflow:auto"><table id="taskTable">' +
    '<thead><tr><th>Task</th><th>Work Type</th><th>Reward</th><th>Categories</th></tr></thead>' +
    '<tbody id="taskRows"></tbody></table></div>';

  const tbody = document.getElementById('taskRows');
  const searchEl = document.getElementById('taskSearch');
  const wtEl = document.getElementById('wtFilter');
  const stEl = document.getElementById('statusFilter');

  function renderTasks() {{
    const q = searchEl.value.toLowerCase();
    const wf = wtEl.value;
    const sf = stEl.value;
    let html = '';
    for (const r of results) {{
      if (q && !r.task_name.toLowerCase().includes(q)) continue;
      if (wf && r.work_type !== wf) continue;
      if (sf === 'pass' && r.reward < 1) continue;
      if (sf === 'fail' && r.reward !== 0) continue;
      if (sf === 'partial' && (r.reward <= 0 || r.reward >= 1)) continue;
      const fcs = r.failure_categories || [];
      const catStr = fcs.map(fc => fc.category || fc.name || '').filter(Boolean).join(', ') || '-';
      const rid = 'row-' + r.task_name.replace(/[^a-zA-Z0-9]/g, '_');
      html += '<tr class="task-row" data-id="' + rid + '" style="cursor:pointer">' +
        '<td class="mono" style="font-size:0.82em">' + esc(r.task_name) + '</td>' +
        '<td>' + esc(r.work_type) + '</td>' +
        '<td class="' + rewardClass(r.reward) + '">' + fmtR(r.reward) + '</td>' +
        '<td style="font-size:0.82em;color:var(--muted)">' + esc(catStr) + '</td></tr>';
      // Expandable detail row (hidden by default)
      if (fcs.length > 0) {{
        let fcHtml = '';
        for (const fc of fcs) {{
          fcHtml += '<div class="fc-item"><span class="fc-cat">' + esc(fc.category || fc.name || '') + '</span>' +
            '<span class="fc-conf">' + (fc.confidence != null ? fmtR(fc.confidence) : '-') + '</span>' +
            (fc.evidence ? '<span class="fc-evidence">' + esc(fc.evidence) + '</span>' : '') + '</div>';
        }}
        html += '<tr class="expand-row" data-parent="' + rid + '" style="display:none">' +
          '<td colspan="4"><div class="expand-content">' + fcHtml + '</div></td></tr>';
      }}
    }}
    tbody.innerHTML = html || '<tr><td colspan="4" class="empty-msg">No matching tasks.</td></tr>';
  }}

  // Expand/collapse on click
  tbody.addEventListener('click', e => {{
    const row = e.target.closest('tr.task-row');
    if (!row) return;
    const id = row.dataset.id;
    const detail = tbody.querySelector('tr.expand-row[data-parent="' + id + '"]');
    if (detail) {{
      detail.style.display = detail.style.display === 'none' ? '' : 'none';
    }}
  }});

  searchEl.addEventListener('input', renderTasks);
  wtEl.addEventListener('change', renderTasks);
  stEl.addEventListener('change', renderTasks);
  renderTasks();
}})();
</script>
</body>
</html>"""


class _BrowserHandler(http.server.BaseHTTPRequestHandler):
    """Serves a single HTML page for the results browser."""

    html_content: str = ""

    def do_GET(self) -> None:
        if self.path in ("/", "/index.html"):
            content = self.html_content.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        else:
            self.send_error(404)

    def log_message(self, format: str, *args: Any) -> None:
        pass  # Suppress request logging


def serve_browser(
    results_path: str | Path,
    port: int = 8770,
    include_baseline: bool = True,
) -> int:
    """Load results, build interactive browser, and serve on localhost."""
    try:
        submission = load_submission(results_path)
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"[csb report] ERROR: {exc}", file=sys.stderr)
        return 1

    print("[csb report] Loading data...", file=sys.stderr)

    baseline = _load_baseline_summary() if include_baseline else None
    data = _build_browser_data(submission, baseline)
    html_content = _render_browser_html(data)

    # Try binding to the requested port, retry up to +10
    handler = type("Handler", (_BrowserHandler,), {"html_content": html_content})
    server = None
    bound_port = port
    for offset in range(11):
        try:
            server = http.server.HTTPServer(("127.0.0.1", port + offset), handler)
            bound_port = port + offset
            break
        except OSError:
            continue

    if server is None:
        print(
            f"[csb report] ERROR: Could not bind to ports {port}-{port + 10}.",
            file=sys.stderr,
        )
        return 1

    url = f"http://127.0.0.1:{bound_port}/"
    print(f"[csb report] Serving at {url}", file=sys.stderr)
    print("[csb report] Press Ctrl+C to stop.", file=sys.stderr)

    # Open browser after a short delay so the server is ready
    threading.Timer(0.5, lambda: webbrowser.open(url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[csb report] Stopped.", file=sys.stderr)
    finally:
        server.server_close()

    return 0
