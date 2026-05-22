#!/usr/bin/env python3
"""Side-by-side baseline vs MCP retrieval-history browser.

Scans paired baseline/mcp trial directories (the layout produced by the
analysis runs at runs/analysis/<suite>/<model>/{baseline,mcp}/) and emits
HTML compare pages plus a JSON manifest of MCP wins.

Examples:

    # Scan all paired suites under runs/analysis/, render only MCP wins >= 0.20,
    # write to docs/analysis/compare/ and the gallery to docs/analysis/compare/gallery/.
    python3 scripts/analysis/browse_compare.py

    # Custom threshold and output dir
    python3 scripts/analysis/browse_compare.py --threshold 0.10 --out browse/compare

    # Limit gallery size (keeps top-N rendered HTML pages)
    python3 scripts/analysis/browse_compare.py --gallery-limit 30

    # Just one suite/model cell
    python3 scripts/analysis/browse_compare.py --suite csb_org_crossrepo_tracing --model cc_sonnet46
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))

# Reuse parsers / formatters from the single-run browser.
from browse_results import (  # noqa: E402
    EVENT_LIMIT,
    STYLE,
    esc,
    extract_task_data,
    fmt_float,
    fmt_int,
    fmt_json,
    fmt_sec,
    slugify_fragment,
    truncate_text,
)


# Trial dir names use several suffix conventions across suites:
#   `<task>__<8-char-id>`        e.g. camel-fix-protocol-feat-001__jF7dqK8
#   `mcp_<task>___<8-char-id>`   e.g. mcp_camel-fix-protocol-feat-001___bkrkgQE
#   `<task>_<6-char-id>`         e.g. ccx-compliance-051_ecrb0b
# We also lowercase because some MCP-side trials capitalize the prefix
# (CCX-compliance-052 vs ccx-compliance-052) for the same canonical task.
_SUFFIX_RE = re.compile(r"_{1,3}[A-Za-z0-9]{5,8}$")
_CONFIG_PREFIXES = ("mcp_", "bl_", "sgonly_", "baseline_")


def canonical_task_name(raw: str) -> str:
    name = raw
    for p in _CONFIG_PREFIXES:
        if name.startswith(p):
            name = name[len(p):]
    name = _SUFFIX_RE.sub("", name)
    return name.lower()

REPO_ROOT = THIS_DIR.parent.parent
DEFAULT_ANALYSIS_ROOT = REPO_ROOT / "runs" / "analysis"
DEFAULT_OUT = REPO_ROOT / "docs" / "analysis" / "compare"


@dataclass(frozen=True)
class Cell:
    suite: str
    model: str
    root: Path  # runs/analysis/<suite>/<model>


@dataclass(frozen=True)
class Pair:
    task: str
    cell: Cell
    baseline: dict
    mcp: dict

    @property
    def delta(self) -> float:
        return float(self.mcp.get("reward") or 0.0) - float(self.baseline.get("reward") or 0.0)

    @property
    def slug(self) -> str:
        return slugify_fragment(f"{self.cell.suite}__{self.cell.model}__{self.task}")


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------

def discover_cells(analysis_root: Path, suite: str | None, model: str | None) -> list[Cell]:
    cells: list[Cell] = []
    for suite_dir in sorted(analysis_root.iterdir()):
        if not suite_dir.is_dir() or suite_dir.name.startswith("_"):
            continue
        if suite and suite_dir.name != suite:
            continue
        for model_dir in sorted(suite_dir.iterdir()):
            if not model_dir.is_dir():
                continue
            if model and model_dir.name != model:
                continue
            if (model_dir / "baseline").is_dir() and (model_dir / "mcp").is_dir():
                cells.append(Cell(suite=suite_dir.name, model=model_dir.name, root=model_dir))
    return cells


def best_trial_by_task(side_dir: Path, config_name: str) -> dict[str, dict]:
    """Map normalized task_name -> highest-reward trial data dict for one side."""
    best: dict[str, dict] = {}
    for trial in sorted(side_dir.iterdir()):
        if not trial.is_dir():
            continue
        if not (trial / "result.json").is_file():
            continue
        try:
            rel = str(trial.relative_to(side_dir.parents[2]))
        except ValueError:
            rel = trial.name
        td = extract_task_data(trial, config_name, scope_name="", trial_relpath=rel)
        if td is None:
            continue
        # Override browse_results' too-strict normalize with the suite-aware one.
        name = canonical_task_name(td.get("raw_name") or trial.name)
        td["task_name"] = name
        prev = best.get(name)
        if prev is None or float(td.get("reward") or 0) > float(prev.get("reward") or 0):
            best[name] = td
    return best


def collect_pairs(cells: list[Cell]) -> list[Pair]:
    pairs: list[Pair] = []
    for cell in cells:
        bl = best_trial_by_task(cell.root / "baseline", "baseline")
        mc = best_trial_by_task(cell.root / "mcp", "mcp")
        for task, b in bl.items():
            m = mc.get(task)
            if m is None:
                continue
            pairs.append(Pair(task=task, cell=cell, baseline=b, mcp=m))
    return pairs


# Local-filesystem tool names across both agent harnesses (Claude Code + OpenHands).
_LOCAL_FILE_TOOLS = (
    "Read", "Glob", "Grep", "Edit", "Write", "Bash",
    "str_replace_editor", "execute_bash", "execute_ipython_cell",
)
_WEB_TOOLS = ("WebSearch", "WebFetch")


def has_broken_baseline_env(pair: Pair, web_min: int = 10, local_max: int = 5) -> bool:
    """True when the baseline trial appears to have had no local-file access and
    fell back to web search instead. Signal: many web tool calls (>= web_min) AND
    almost no local-file calls (<= local_max). This typically marks a broken
    Daytona/Docker sandbox where the workspace mount failed, so the win is
    an artifact of MCP merely having any access at all, not a fair comparison.
    """
    tools = (pair.baseline or {}).get("tool_calls_by_name") or {}
    web = sum(tools.get(k, 0) for k in _WEB_TOOLS)
    local = sum(tools.get(k, 0) for k in _LOCAL_FILE_TOOLS)
    return web >= web_min and local <= local_max


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

EXTRA_STYLE = """\
.cmp { display:grid; grid-template-columns:1fr 1fr; gap:14px; }
.col { background:var(--panel); border:1px solid var(--border); border-radius:12px; padding:14px; }
.col h2 { font-size:16px; margin:0 0 8px; }
.tag { display:inline-block; padding:2px 8px; border-radius:999px; font-size:11px; margin-left:6px; }
.tag.bl { background:rgba(88,166,255,0.18); color:#58a6ff; }
.tag.mcp { background:rgba(71,209,140,0.22); color:var(--accent); }
.delta-pos { color:var(--accent); font-weight:600; }
.delta-neg { color:#ffcc66; font-weight:600; }
.kpi { display:grid; grid-template-columns:repeat(4,1fr); gap:8px; margin:8px 0 12px; }
.kpi .metric .v { font-size:16px; }
@media (max-width: 1100px) { .cmp { grid-template-columns:1fr; } .kpi { grid-template-columns:repeat(2,1fr); } }
"""


def fmt_delta(d: float) -> str:
    sign = "+" if d >= 0 else ""
    cls = "delta-pos" if d > 0 else ("delta-neg" if d < 0 else "")
    return f"<span class='{cls}'>{sign}{d:.3f}</span>"


def _kpi(rows: list[tuple[str, str]]) -> str:
    return "".join(
        f"<div class='metric'><div class='k'>{esc(k)}</div><div class='v'>{esc(v)}</div></div>"
        for k, v in rows
    )


def _column_html(side: str, t: dict) -> str:
    tag_cls = "bl" if side == "baseline" else "mcp"
    tag_label = "Baseline" if side == "baseline" else "MCP"
    trace = t.get("trace") or {}
    tcalls = trace.get("tool_calls", [])
    events = trace.get("events", [])
    cchanges = trace.get("code_changes", [])
    bash = trace.get("bash_commands", [])

    cost = f"${t['cost_usd']:.2f}" if t.get("cost_usd") else "-"
    kpi = _kpi([
        ("Reward", fmt_float(t.get("reward"), 4)),
        ("Tool calls", str(t.get("tool_calls_total") or 0)),
        ("Time", fmt_sec(t.get("wall_clock_sec"))),
        ("Cost", cost),
        ("Input tok", fmt_int(t.get("input_tokens"))),
        ("Output tok", fmt_int(t.get("output_tokens"))),
        ("MCP ratio", fmt_float(t.get("mcp_ratio"), 2)),
        ("Files mod", str(t.get("files_modified") or 0)),
    ])

    tool_break = "".join(
        f"<tr><td><code>{esc(n)}</code></td><td class='num'>{int(c)}</td></tr>"
        for n, c in sorted((t.get("tool_calls_by_name") or {}).items(), key=lambda x: -x[1])
    ) or "<tr><td colspan='2'>-</td></tr>"

    # Compact tool-call list: numbered, tool name + key input field, output truncated.
    def _input_summary(tool: str, inp) -> str:
        if not isinstance(inp, dict):
            return ""
        for key in ("file_path", "path", "pattern", "query", "command", "url", "name"):
            v = inp.get(key)
            if v:
                return f"{key}={truncate_text(str(v), 160)}"
        return truncate_text(json.dumps(inp, ensure_ascii=False), 160)

    tc_html = "".join(
        f"<details><summary>#{i}. <code>{esc(c.get('tool') or '?')}</code> "
        f"<span class='meta mono'>{esc(_input_summary(c.get('tool') or '', c.get('input')))}</span></summary>"
        f"<h4>Input</h4><pre>{fmt_json(c.get('input'))}</pre>"
        + (
            f"<h4>Output</h4><pre>{esc(truncate_text(str(c.get('output_text') or ''), 4000))}</pre>"
            if c.get("output_text")
            else ""
        )
        + "</details>"
        for i, c in enumerate(tcalls[:EVENT_LIMIT], 1)
    ) or "<p class='meta'>No tool calls.</p>"

    cc_html = "".join(
        f"<details><summary>{i}. {esc(str(ch.get('type','')).upper())} "
        f"<code>{esc(ch.get('file_path',''))}</code></summary>"
        + (
            "<div class='split'>"
            f"<div><h4>Before</h4><pre>{esc(truncate_text(str(ch.get('old_string','')), 2000))}</pre></div>"
            f"<div><h4>After</h4><pre>{esc(truncate_text(str(ch.get('new_string','')), 2000))}</pre></div>"
            "</div>"
            if ch.get("type") == "edit"
            else f"<pre>{esc(truncate_text(str(ch.get('content','')), 2000))}</pre>"
        )
        + "</details>"
        for i, ch in enumerate(cchanges[:EVENT_LIMIT], 1)
    ) or "<p class='meta'>No code changes.</p>"

    bash_html = "".join(
        f"<pre>{i}. $ {esc(truncate_text(str(b.get('command','')), 800))}</pre>"
        for i, b in enumerate(bash[:EVENT_LIMIT], 1)
    ) or "<p class='meta'>No bash commands.</p>"

    return (
        f"<div class='col'>"
        f"<h2>{tag_label} <span class='tag {tag_cls}'>{esc(t.get('config') or side)}</span></h2>"
        f"<p class='meta mono'>{esc(t.get('trial_name') or '-')}</p>"
        f"<div class='kpi'>{kpi}</div>"
        f"<details><summary>Tool breakdown</summary>"
        f"<table><thead><tr><th>Tool</th><th class='num'>Calls</th></tr></thead><tbody>{tool_break}</tbody></table>"
        f"</details>"
        f"<details open><summary>Tool calls ({len(tcalls)})</summary>{tc_html}</details>"
        f"<details><summary>Code changes ({len(cchanges)})</summary>{cc_html}</details>"
        f"<details><summary>Bash commands ({len(bash)})</summary>{bash_html}</details>"
        f"<details><summary>Conversation events ({len(events)})</summary>"
        + "".join(
            f"<div class='meta mono'>#{i} {esc(e.get('type') or '-')}/"
            f"{esc(e.get('subtype') or '-')} "
            f"<code>{esc(e.get('tool') or '')}</code></div>"
            f"<pre>{esc(truncate_text(str(e.get('text') or ''), 1200))}</pre>"
            for i, e in enumerate(events[:EVENT_LIMIT], 1)
        )
        + "</details>"
        f"</div>"
    )


def render_pair_page(pair: Pair) -> str:
    bl, mc = pair.baseline, pair.mcp
    head = (
        f"<h1>{esc(pair.task)}</h1>"
        f"<p class='meta'>{esc(pair.cell.suite)} / {esc(pair.cell.model)} "
        f" | Baseline <strong>{fmt_float(bl.get('reward'), 4)}</strong>"
        f" vs MCP <strong>{fmt_float(mc.get('reward'), 4)}</strong>"
        f" | Delta {fmt_delta(pair.delta)}</p>"
    )
    instruction = bl.get("instruction_text") or mc.get("instruction_text") or ""
    instr_panel = (
        f"<div class='col'><h2>Task instruction</h2>"
        f"<pre>{esc(truncate_text(instruction, 4000))}</pre></div>"
        if instruction
        else ""
    )
    return (
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        f"<title>{esc(pair.task)} — baseline vs MCP</title>"
        f"<style>{STYLE}{EXTRA_STYLE}</style></head><body><div class='wrap'>"
        "<p><a href='index.html'>&larr; Back to MCP-win index</a></p>"
        f"{head}"
        f"<div class='cmp'>{instr_panel or ''}</div>"
        f"<div class='cmp'>{_column_html('baseline', bl)}{_column_html('mcp', mc)}</div>"
        "</div></body></html>"
    )


def render_index_page(out_dir: Path, rendered: list[Pair], all_wins: list[dict]) -> str:
    rendered_slugs = {p.slug for p in rendered}
    rows = []
    for w in all_wins:
        slug = w["slug"]
        link = f"<a href='{slug}.html'>open</a>" if slug in rendered_slugs else "<span class='meta'>regen</span>"
        rows.append(
            "<tr>"
            f"<td><code>{esc(w['suite'])}</code></td>"
            f"<td><code>{esc(w['model'])}</code></td>"
            f"<td>{esc(w['task'])}</td>"
            f"<td class='num'>{fmt_float(w['baseline_reward'], 3)}</td>"
            f"<td class='num'>{fmt_float(w['mcp_reward'], 3)}</td>"
            f"<td class='num delta-pos'>+{w['delta']:.3f}</td>"
            f"<td>{link}</td>"
            "</tr>"
        )
    return (
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        "<title>MCP wins — baseline vs MCP side-by-side</title>"
        f"<style>{STYLE}{EXTRA_STYLE}"
        "table { table-layout:auto; } td.num { text-align:right; font-variant-numeric:tabular-nums; }"
        "</style></head><body><div class='wrap'>"
        "<h1>MCP wins — baseline vs MCP side-by-side</h1>"
        f"<p class='meta'>{len(all_wins)} task pairs where MCP &ge; baseline by the chosen threshold; "
        f"{len(rendered)} pre-rendered. Full manifest: <a href='wins_manifest.json'>wins_manifest.json</a>. "
        "Regenerate any row locally via "
        "<code>python3 scripts/analysis/browse_compare.py --threshold 0.10 --out browse/compare</code>.</p>"
        "<table><thead><tr>"
        "<th>Suite</th><th>Model</th><th>Task</th>"
        "<th class='num'>Baseline</th><th class='num'>MCP</th><th class='num'>Delta</th><th></th>"
        "</tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table>"
        "</div></body></html>"
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--analysis-root",
        type=Path,
        default=DEFAULT_ANALYSIS_ROOT,
        help="Root holding <suite>/<model>/{baseline,mcp}/ trial dirs.",
    )
    ap.add_argument("--suite", default=None, help="Restrict to one suite dir name.")
    ap.add_argument("--model", default=None, help="Restrict to one model dir name (cc_sonnet46, cc_haiku45, oh_sonnet46).")
    ap.add_argument("--threshold", type=float, default=0.20,
                    help="Minimum MCP - baseline reward delta to count as a win (default 0.20).")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT,
                    help="Output directory (default docs/analysis/compare/).")
    ap.add_argument("--gallery-limit", type=int, default=20,
                    help="Render at most this many HTML pages, ranked by delta desc (default 20). "
                         "The full manifest still lists every win.")
    ap.add_argument("--render-all", action="store_true",
                    help="Render every win as HTML (ignores --gallery-limit). Big.")
    ap.add_argument("--include-broken-env-baselines", action="store_true",
                    help="Keep pairs where the baseline trial appears to have had no "
                         "local-file access and fell back to web search (>= 10 WebSearch/"
                         "WebFetch calls, <= 5 local-file calls). Excluded by default "
                         "because such 'wins' are artifacts of the sandbox failing, not "
                         "evidence that MCP retrieval beat a real local-file baseline.")
    args = ap.parse_args(argv)

    analysis_root: Path = args.analysis_root
    if not analysis_root.is_dir():
        print(f"ERROR: not a directory: {analysis_root}", file=sys.stderr)
        return 2

    cells = discover_cells(analysis_root, args.suite, args.model)
    if not cells:
        print("No paired baseline/mcp cells found.", file=sys.stderr)
        return 1
    print(f"Scanning {len(cells)} (suite, model) cells under {analysis_root}...")

    pairs = collect_pairs(cells)
    print(f"  Collected {len(pairs)} task pairs.")

    if not args.include_broken_env_baselines:
        excluded = [p for p in pairs if has_broken_baseline_env(p)]
        pairs = [p for p in pairs if not has_broken_baseline_env(p)]
        if excluded:
            print(f"  Excluded {len(excluded)} pair(s) with broken-env baseline "
                  "(heavy web-search use, no local-file access):")
            for p in excluded:
                print(f"    - {p.cell.suite}/{p.cell.model}/{p.task} "
                      f"(delta={p.delta:+.3f})")

    wins = [p for p in pairs if p.delta >= args.threshold]
    wins.sort(key=lambda p: p.delta, reverse=True)
    print(f"  {len(wins)} MCP wins with delta >= {args.threshold:.2f}.")

    out_dir: Path = args.out
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest = [
        {
            "suite": p.cell.suite,
            "model": p.cell.model,
            "task": p.task,
            "slug": p.slug,
            "baseline_reward": p.baseline.get("reward"),
            "mcp_reward": p.mcp.get("reward"),
            "delta": round(p.delta, 4),
            "baseline_trial_name": p.baseline.get("trial_name"),
            "mcp_trial_name": p.mcp.get("trial_name"),
        }
        for p in wins
    ]
    (out_dir / "wins_manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"  Wrote {out_dir / 'wins_manifest.json'}")

    rendered = wins if args.render_all else wins[: args.gallery_limit]
    for pair in rendered:
        (out_dir / f"{pair.slug}.html").write_text(render_pair_page(pair))
    print(f"  Rendered {len(rendered)} compare pages in {out_dir}/")

    (out_dir / "index.html").write_text(render_index_page(out_dir, rendered, manifest))
    print(f"  Wrote {out_dir / 'index.html'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
