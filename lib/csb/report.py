"""csb report — display benchmark results with CSB Score prominently.

Reads a submission JSON and renders a formatted summary in text, JSON, or HTML.
"""

from __future__ import annotations

import html as html_mod
import json
import sys
import webbrowser
from collections import defaultdict
from pathlib import Path
from typing import Any


def load_submission(results_path: str | Path) -> dict[str, Any]:
    """Load and return a submission JSON file."""
    path = Path(results_path)
    if not path.exists():
        raise FileNotFoundError(f"Results file not found: {path}")
    with open(path) as f:
        return json.load(f)


def display_report(
    results_path: str | Path,
    fmt: str = "text",
    open_browser: bool = False,
) -> int:
    """Display a benchmark results report.

    Parameters
    ----------
    results_path:
        Path to the submission JSON file.
    fmt:
        Output format — "text", "json", or "html".
    open_browser:
        If True and fmt is "html", open the report in a browser.

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

    return _render_text(submission)


def _render_text(submission: dict[str, Any]) -> int:
    """Render a text report to stdout."""
    csb_score = submission.get("csb_score", 0.0)
    suite = submission.get("suite", "unknown")
    agent_info = submission.get("agent_info", {})
    agent_name = agent_info.get("name", "unknown")
    metadata = submission.get("metadata", {})
    results = submission.get("results", [])

    # CSB Score prominently at top
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

    # Per-work-type breakdown
    by_work_type: dict[str, list[float]] = defaultdict(list)
    # We don't have work_type in submission results directly,
    # so group by task name prefix or show flat list
    for r in results:
        # Attempt to detect work_type from result or use "all"
        wt = r.get("work_type", "all")
        by_work_type[wt].append(r.get("reward", 0.0))

    if len(by_work_type) > 1 or "all" not in by_work_type:
        print("  Per-work-type breakdown:")
        print(f"  {'Work Type':<20} {'Pass Rate':>10} {'Tasks':>6}")
        print(f"  {'-'*20} {'-'*10} {'-'*6}")
        for wt in sorted(by_work_type):
            rewards = by_work_type[wt]
            passed = sum(1 for r in rewards if r >= 1.0)
            rate = passed / len(rewards) * 100 if rewards else 0.0
            print(f"  {wt:<20} {rate:>9.1f}% {len(rewards):>6}")
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
