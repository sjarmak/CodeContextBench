#!/usr/bin/env python3
"""Export milestone-first engineering diary assets from unified conversation DB.

This script intentionally focuses on build decisions, architecture evolution,
and issue-resolution loops, not model metadata.

Outputs under docs/assets/blog/medium by default:
- csv/: figure datasets
- figures/: SVG charts (Sourcegraph-like styling)
- tables/: markdown tables for the post
- quotes/: redacted, attributed quote snippets
- sql/: extraction seed query + taxonomy definitions
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sqlite3
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from typing import Iterable

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


PALETTE = {
    "bg": "#020202",
    "text": "#ededed",
    "text_secondary": "#a9a9a9",
    "grid": "#343434",
    "pos": "#8552f2",
    "neg": "#ff7867",
    "base": "#6b7280",
    "accent": "#914bdc",
    "muted": "#4b5563",
    "success": "#6ee7b7",
    "warning": "#f59e0b",
}


WORKSTREAMS: list[tuple[str, list[str], str]] = [
    (
        "skills_qa_task_factory",
        [
            r"\bskills?\b",
            r"\bqa\b",
            r"task audit",
            r"abc audit",
            r"task creation",
            r"ir-sdlc-factory",
            r"\bsdlc\b",
            r"scaffold",
        ],
        "Skills, QA, Task Factory",
    ),
    (
        "dashboard_audit",
        [
            r"dashboard",
            r"runs explorer",
            r"visibility",
            r"monitor",
            r"manifest",
            r"promotion",
            r"archive",
            r"triage",
            r"audit",
        ],
        "Dashboard + Audit Ops",
    ),
    (
        "ir_eval_pipeline",
        [
            r"information retrieval",
            r"retrieval pipeline",
            r"ir analysis",
            r"normalize retrieval",
            r"ground truth",
            r"precision",
            r"recall",
            r"file recall",
        ],
        "IR Evaluation Pipeline",
    ),
    (
        "curator_contextbench",
        [
            r"curator",
            r"contextbench",
            r"human annotated",
            r"context retrieval agent",
            r"oracle hydration",
            r"curate oracle",
        ],
        "Curator + ContextBench",
    ),
    (
        "llm_judge_trace",
        [
            r"llm as a judge",
            r"judge pipeline",
            r"trace analysis",
            r"trajectory",
            r"verifier",
            r"oracle",
            r"scor",
        ],
        "LLM Judge + Trace Analysis",
    ),
    (
        "harness_infra",
        [
            r"harbor",
            r"docker",
            r"dockerfile",
            r"daytona",
            r"harness",
            r"sandbox",
            r"registry",
            r"oauth",
            r"token refresh",
        ],
        "Harness + Infra",
    ),
]


ISSUE_CLUSTERS: list[tuple[str, list[str], str]] = [
    (
        "daytona_bootstrap",
        [
            r"daytonaerror",
            r"daytona error",
            r"sandbox startup",
            r"allocation",
            r"token refresh",
            r"oauth",
            r"api key",
        ],
        "Daytona bootstrap/auth",
    ),
    (
        "docker_build",
        [
            r"docker",
            r"dockerfile",
            r"build fail",
            r"image names",
            r"overlay2",
            r"chown timeout",
            r"missing dockerfile",
        ],
        "Docker build/runtime",
    ),
    (
        "verifier_oracle",
        [
            r"verifier",
            r"oracle",
            r"ground truth",
            r"test\.sh",
            r"parse error",
            r"bad-oracle",
        ],
        "Verifier/oracle quality",
    ),
    (
        "retrieval_mcp",
        [
            r"mcp",
            r"deep search",
            r"context retrieval",
            r"cloudflare",
            r"waf",
            r"403",
            r"search quality",
        ],
        "MCP/retrieval path",
    ),
    (
        "run_orchestration",
        [
            r"staging",
            r"official",
            r"promotion",
            r"archive",
            r"rerun",
            r"coverage gap",
            r"queue",
            r"batch",
        ],
        "Run orchestration",
    ),
]


ISSUE_MARKERS = [
    r"\berror\b",
    r"\bfailed\b",
    r"\btimeout\b",
    r"\bexception\b",
    r"\bblocked\b",
    r"\bstall",
    r"\b429\b",
    r"\b500\b",
    r"\bforbidden\b",
]


RESOLUTION_MARKERS = [
    r"\bfix:",
    r"\bfixed\b",
    r"\bresolved\b",
    r"\bmitigat",
    r"\bworkaround\b",
    r"\bpatch",
    r"\bretry logic\b",
    r"\bbackoff\b",
    r"\badded\b",
    r"\bimplemented\b",
    r"\bremoved\b",
    r"\bpromote\b",
]


DECISION_MARKERS = [
    r"\bdecid",
    r"\bchose\b",
    r"\bswitch",
    r"\binstead of\b",
    r"\btrade-?off\b",
    r"\bstrategy\b",
    r"\bwe should\b",
    r"\blet's\b",
    r"\bplan\b",
    r"\bpromote\b",
    r"\barchive\b",
    r"\bdrop\b",
    r"\bkeep\b",
]


DECISION_THEMES: list[tuple[str, list[str], str]] = [
    (
        "quality_vs_speed",
        [r"qa", r"quality", r"variance", r"statistical", r"deadline", r"fast", r"slow"],
        "Quality vs Speed",
    ),
    (
        "local_vs_remote",
        [r"daytona", r"local docker", r"local", r"remote", r"cloud"],
        "Local vs Remote Execution",
    ),
    (
        "curation_depth",
        [r"curat", r"ground truth", r"oracle", r"coverage", r"mcp-unique", r"sdlc"],
        "Curation Depth",
    ),
    (
        "repro_vs_pragmatic",
        [r"reproduc", r"dedupe", r"alias", r"mirror", r"strict"],
        "Reproducibility Tradeoffs",
    ),
    (
        "infra_reliability",
        [r"retry", r"timeout", r"token", r"oauth", r"docker", r"harbor", r"daytona"],
        "Infra Reliability",
    ),
]


ARTIFACT_PATTERNS = {
    "scripts": re.compile(r"\bscripts/[A-Za-z0-9_./-]+"),
    "docs": re.compile(r"\bdocs/[A-Za-z0-9_./-]+"),
    "configs": re.compile(r"\bconfigs/[A-Za-z0-9_./-]+"),
    "benchmarks": re.compile(r"\bbenchmarks/[A-Za-z0-9_./-]+"),
    "tasks": re.compile(r"\btasks/[A-Za-z0-9_./-]+"),
}


COMMIT_LINE_RE = re.compile(
    r"(?m)^(?:[0-9a-f]{7,40}\s+)?(feat|fix|perf|docs|chore|refactor|test):\s+(.+)$",
    re.IGNORECASE,
)


SENSITIVE_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("email", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")),
    ("home_path", re.compile(r"/home/[A-Za-z0-9_.-]+")),
    ("api_key", re.compile(r"\b(sk-[A-Za-z0-9]{16,}|ghp_[A-Za-z0-9]{20,}|AIza[0-9A-Za-z-_]{20,})\b")),
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9._-]{10,}\.[A-Za-z0-9._-]{10,}\b")),
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def setup_style() -> None:
    plt.rcParams.update(
        {
            "figure.facecolor": PALETTE["bg"],
            "axes.facecolor": PALETTE["bg"],
            "axes.edgecolor": PALETTE["grid"],
            "axes.labelcolor": PALETTE["text"],
            "xtick.color": PALETTE["text"],
            "ytick.color": PALETTE["text"],
            "text.color": PALETTE["text"],
            "grid.color": PALETTE["grid"],
            "font.family": "sans-serif",
            "font.sans-serif": ["Poly Sans", "Arial", "DejaVu Sans", "sans-serif"],
            "font.size": 10,
            "axes.titlesize": 12,
            "axes.titleweight": "bold",
        }
    )


def write_csv(path: Path, columns: list[str], rows: Iterable[Iterable[object]]) -> int:
    ensure_dir(path.parent)
    n = 0
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(columns)
        for r in rows:
            w.writerow(list(r))
            n += 1
    return n


def normalize_text(text: str) -> str:
    t = text.lower()
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"[^a-z0-9 ]+", "", t)
    return t.strip()


def redact_text(text: str) -> tuple[str, list[str]]:
    red = text
    flags: list[str] = []
    for name, pat in SENSITIVE_PATTERNS:
        if pat.search(red):
            red = pat.sub(f"[{name.upper()}_REDACTED]", red)
            flags.append(name)
    return red, sorted(set(flags))


def theme_label(theme_key: str) -> str:
    for key, _, label in DECISION_THEMES:
        if key == theme_key:
            return label
    return "General"


def workstream_label(ws_key: str) -> str:
    for key, _, label in WORKSTREAMS:
        if key == ws_key:
            return label
    return ws_key


def cluster_label(cluster_key: str) -> str:
    for key, _, label in ISSUE_CLUSTERS:
        if key == cluster_key:
            return label
    return cluster_key


@dataclass
class MsgRec:
    msg_id: int
    ts: str
    day: str
    session_id: str
    agent: str
    role: str
    source_path: str
    project_key: str
    text: str


def compile_map(entries: list[tuple[str, list[str], str]]) -> dict[str, tuple[list[re.Pattern[str]], str]]:
    out: dict[str, tuple[list[re.Pattern[str]], str]] = {}
    for key, pats, label in entries:
        out[key] = ([re.compile(p, re.IGNORECASE) for p in pats], label)
    return out


def compile_list(patterns: list[str]) -> list[re.Pattern[str]]:
    return [re.compile(p, re.IGNORECASE) for p in patterns]


def any_match(text: str, pats: list[re.Pattern[str]]) -> bool:
    return any(p.search(text) for p in pats)


def classify_theme(text: str, theme_map: dict[str, tuple[list[re.Pattern[str]], str]]) -> tuple[str, str]:
    best = ("general", "General", 0)
    for key, (pats, label) in theme_map.items():
        hits = sum(1 for p in pats if p.search(text))
        if hits > best[2]:
            best = (key, label, hits)
    return best[0], best[1]


def fetch_messages(conn: sqlite3.Connection, start_date: str | None, end_date: str | None) -> list[MsgRec]:
    where = [
        "m.ts IS NOT NULL",
        "m.role IN ('user','assistant')",
        "m.text IS NOT NULL",
        "m.agent NOT LIKE 'external_%'",
        "(s.project_key LIKE '%CodeScaleBench%' OR s.project_key LIKE '%CodeContextBench%')",
    ]
    params: list[str] = []
    if start_date:
        where.append("m.ts >= ?")
        params.append(start_date)
    if end_date:
        where.append("m.ts < ?")
        params.append(end_date)

    sql = f"""
SELECT m.id, m.ts, substr(m.ts,1,10) AS day,
       m.session_id, m.agent, m.role, s.source_path, s.project_key, m.text
FROM messages m
JOIN sessions s ON s.session_id=m.session_id AND s.agent=m.agent
WHERE {' AND '.join(where)}
ORDER BY m.ts;
"""

    cur = conn.execute(sql, tuple(params))
    rows: list[MsgRec] = []
    for r in cur.fetchall():
        rows.append(
            MsgRec(
                msg_id=int(r[0]),
                ts=str(r[1]),
                day=str(r[2]),
                session_id=str(r[3]),
                agent=str(r[4]),
                role=str(r[5]),
                source_path=str(r[6] or ""),
                project_key=str(r[7] or ""),
                text=str(r[8] or ""),
            )
        )
    return rows


def export_diary_assets(messages: list[MsgRec], out_root: Path) -> dict[str, object]:
    csv_dir = out_root / "csv"
    fig_dir = out_root / "figures"
    table_dir = out_root / "tables"
    quote_dir = out_root / "quotes"
    sql_dir = out_root / "sql"

    ensure_dir(csv_dir)
    ensure_dir(fig_dir)
    ensure_dir(table_dir)
    ensure_dir(quote_dir)
    ensure_dir(sql_dir)

    ws_map = compile_map(WORKSTREAMS)
    cluster_map = compile_map(ISSUE_CLUSTERS)
    issue_markers = compile_list(ISSUE_MARKERS)
    resolution_markers = compile_list(RESOLUTION_MARKERS)
    decision_markers = compile_list(DECISION_MARKERS)
    theme_map = compile_map(DECISION_THEMES)
    workstream_patterns = [p for pats, _label in ws_map.values() for p in pats]

    days = sorted({m.day for m in messages})

    day_ws_sessions: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    day_cluster_issue: dict[str, Counter[str]] = defaultdict(Counter)
    day_cluster_resolution: dict[str, Counter[str]] = defaultdict(Counter)

    first_issue_ts: dict[tuple[str, str], datetime] = {}
    first_resolution_ts: dict[tuple[str, str], datetime] = {}

    artifact_mentions = Counter()
    artifact_paths: dict[str, set[str]] = defaultdict(set)

    decision_rows: list[dict[str, object]] = []
    quote_candidates: list[dict[str, object]] = []
    commit_counts: dict[str, Counter[str]] = defaultdict(Counter)

    for m in messages:
        t = m.text
        t_low = t.lower()

        # Workstream mentions counted as active sessions/day.
        for ws_key, (pats, _label) in ws_map.items():
            if any_match(t_low, pats):
                day_ws_sessions[m.day][ws_key].add(m.session_id)

        # Issue + resolution counts by cluster.
        is_issue = any_match(t_low, issue_markers)
        is_resolution = any_match(t_low, resolution_markers)
        for cluster_key, (pats, _label) in cluster_map.items():
            if any_match(t_low, pats):
                if is_issue:
                    day_cluster_issue[m.day][cluster_key] += 1
                    key = (m.session_id, cluster_key)
                    try:
                        ts = datetime.fromisoformat(m.ts.replace("Z", "+00:00"))
                    except ValueError:
                        ts = None
                    if ts is not None and key not in first_issue_ts:
                        first_issue_ts[key] = ts
                if is_resolution:
                    day_cluster_resolution[m.day][cluster_key] += 1
                    key = (m.session_id, cluster_key)
                    try:
                        ts = datetime.fromisoformat(m.ts.replace("Z", "+00:00"))
                    except ValueError:
                        ts = None
                    if ts is not None and key not in first_resolution_ts:
                        first_resolution_ts[key] = ts

        # Artifact mentions and unique paths.
        for art_type, pat in ARTIFACT_PATTERNS.items():
            found = pat.findall(t)
            if found:
                artifact_mentions[art_type] += len(found)
                artifact_paths[art_type].update(found)

        # Decision candidates.
        marker_hits = sum(1 for p in decision_markers if p.search(t_low))
        theme_key, theme_lbl = classify_theme(t_low, theme_map)
        theme_hits = 0 if theme_key == "general" else 1
        score = marker_hits + theme_hits
        if score >= 2 and 60 <= len(t.strip()) <= 520:
            snippet = " ".join(t.strip().split())
            decision_rows.append(
                {
                    "msg_id": m.msg_id,
                    "ts": m.ts,
                    "day": m.day,
                    "session_id": m.session_id,
                    "agent": m.agent,
                    "role": m.role,
                    "theme": theme_lbl,
                    "score": score,
                    "snippet": snippet,
                    "source_path": m.source_path,
                    "project_key": m.project_key,
                }
            )

        # Commit-like status lines embedded in conversations.
        for match in COMMIT_LINE_RE.finditer(t):
            kind = match.group(1).lower()
            commit_counts[m.day][kind] += 1

        # Quote candidates anchored on engineering signal.
        signal_hits = 0
        if any_match(t_low, issue_markers):
            signal_hits += 1
        if any_match(t_low, resolution_markers):
            signal_hits += 1
        if marker_hits > 0:
            signal_hits += 1
        if any_match(t_low, workstream_patterns):
            signal_hits += 1
        if signal_hits >= 2 and 80 <= len(t.strip()) <= 650:
            quote_candidates.append(
                {
                    "message_id": m.msg_id,
                    "session_id": m.session_id,
                    "agent": m.agent,
                    "ts": m.ts,
                    "role": m.role,
                    "source_path": m.source_path,
                    "project_key": m.project_key,
                    "score": signal_hits,
                    "text": t.strip(),
                }
            )

    # fig01: workstream timeline (session counts)
    fig01_rows = []
    for day in days:
        row = {"day": day}
        total = set()
        for ws_key, _pats, _label in WORKSTREAMS:
            sids = day_ws_sessions[day].get(ws_key, set())
            row[ws_key] = len(sids)
            total |= sids
        row["total_active_sessions"] = len(total)
        fig01_rows.append(row)

    write_csv(
        csv_dir / "fig01_workstream_timeline.csv",
        ["day"] + [k for k, _, _ in WORKSTREAMS] + ["total_active_sessions"],
        [
            [r["day"]]
            + [r[k] for k, _, _ in WORKSTREAMS]
            + [r["total_active_sessions"]]
            for r in fig01_rows
        ],
    )

    # fig02: architecture milestones from first+peak day per workstream
    fig02_rows = []
    for ws_key, _pats, label in WORKSTREAMS:
        active = [(d, len(day_ws_sessions[d].get(ws_key, set()))) for d in days]
        first_day = next((d for d, n in active if n > 0), "")
        peak_day, peak_sessions = ("", 0)
        if active:
            peak_day, peak_sessions = max(active, key=lambda x: x[1])
        total_sessions = len(set().union(*[day_ws_sessions[d].get(ws_key, set()) for d in days]))
        fig02_rows.append((ws_key, label, first_day, peak_day, peak_sessions, total_sessions))

    write_csv(
        csv_dir / "fig02_architecture_milestones.csv",
        ["workstream_key", "workstream", "first_day", "peak_day", "peak_sessions", "total_sessions"],
        fig02_rows,
    )

    # fig03: decision points
    decision_rows.sort(key=lambda r: (int(r["score"]), str(r["ts"])), reverse=True)
    seen_norm: set[str] = set()
    dedup_decisions: list[dict[str, object]] = []
    for r in decision_rows:
        norm = normalize_text(str(r["snippet"]))
        h = hashlib.sha256(norm.encode("utf-8")).hexdigest()
        if h in seen_norm:
            continue
        seen_norm.add(h)
        dedup_decisions.append(r)

    write_csv(
        csv_dir / "fig03_decision_points.csv",
        ["msg_id", "ts", "day", "session_id", "agent", "role", "theme", "score", "snippet"],
        [
            [
                r["msg_id"],
                r["ts"],
                r["day"],
                r["session_id"],
                r["agent"],
                r["role"],
                r["theme"],
                r["score"],
                r["snippet"],
            ]
            for r in dedup_decisions
        ],
    )

    # fig04: issue-resolution timeline (all clusters)
    fig04_rows = []
    for day in days:
        issue_count = sum(day_cluster_issue[day].values())
        res_count = sum(day_cluster_resolution[day].values())
        ratio = (res_count / issue_count) if issue_count else 0.0
        fig04_rows.append((day, issue_count, res_count, round(ratio, 4)))

    write_csv(
        csv_dir / "fig04_issue_resolution_timeline.csv",
        ["day", "issues", "resolutions", "resolution_ratio"],
        fig04_rows,
    )

    # fig05: issue cluster heatmap data
    fig05_rows = []
    for day in days:
        for c_key, _p, c_label in ISSUE_CLUSTERS:
            fig05_rows.append(
                (
                    day,
                    c_key,
                    c_label,
                    day_cluster_issue[day][c_key],
                    day_cluster_resolution[day][c_key],
                )
            )

    write_csv(
        csv_dir / "fig05_issue_cluster_heatmap.csv",
        ["day", "cluster_key", "cluster", "issue_hits", "resolution_hits"],
        fig05_rows,
    )

    # fig06: reusable components mapped to benchmark-builder stages
    build_stages = [
        "Task Design",
        "Quality Gates",
        "Execution Harness",
        "Evaluation Analysis",
        "Operations",
    ]
    stage_scores = {
        "skills_qa_task_factory": [1.0, 0.9, 0.4, 0.2, 0.3],
        "dashboard_audit": [0.2, 0.5, 0.6, 0.5, 1.0],
        "ir_eval_pipeline": [0.3, 0.7, 0.2, 1.0, 0.4],
        "curator_contextbench": [0.6, 0.7, 0.4, 0.8, 0.3],
        "llm_judge_trace": [0.2, 0.8, 0.2, 1.0, 0.5],
        "harness_infra": [0.1, 0.3, 1.0, 0.4, 0.9],
    }
    reuse_notes = {
        "skills_qa_task_factory": "Task templates, skill wrappers, task intake flow",
        "dashboard_audit": "Run state model (READY/BLOCKED/ERROR), promotion checks",
        "ir_eval_pipeline": "Retrieval normalization + metric extraction pipeline",
        "curator_contextbench": "Curator workflow with timeout/retry and coverage closure",
        "llm_judge_trace": "Judge+trace coupling for root-cause attribution",
        "harness_infra": "Harbor/Docker/Daytona routing with shared artifact contract",
    }
    fig06_rows = []
    for ws_key, _pats, ws_label in WORKSTREAMS:
        scores = stage_scores.get(ws_key, [0.0] * len(build_stages))
        for stage, score in zip(build_stages, scores):
            fig06_rows.append(
                (
                    ws_key,
                    ws_label,
                    stage,
                    round(float(score), 3),
                    reuse_notes.get(ws_key, ""),
                )
            )

    write_csv(
        csv_dir / "fig06_reusable_components.csv",
        ["component_key", "component", "build_stage", "reuse_score", "reuse_asset_hint"],
        fig06_rows,
    )

    # fig07: commit-signal lines from conversation logs
    commit_types = ["feat", "fix", "perf", "docs", "chore", "refactor", "test"]
    fig07_rows = []
    for day in days:
        row = [day] + [commit_counts[day][k] for k in commit_types]
        row.append(sum(commit_counts[day][k] for k in commit_types))
        fig07_rows.append(row)

    write_csv(
        csv_dir / "fig07_commit_signal.csv",
        ["day"] + commit_types + ["total"],
        fig07_rows,
    )

    # Write extraction specification SQL + taxonomies for transparency.
    query_text = """-- Engineering diary extraction seed query (message-level)
SELECT m.id, m.ts, m.session_id, m.agent, m.role, s.source_path, s.project_key, m.text
FROM messages m
JOIN sessions s ON s.session_id=m.session_id AND s.agent=m.agent
WHERE m.ts IS NOT NULL
  AND m.role IN ('user','assistant')
  AND m.text IS NOT NULL
  AND m.agent NOT LIKE 'external_%'
  AND (s.project_key LIKE '%CodeScaleBench%' OR s.project_key LIKE '%CodeContextBench%')
ORDER BY m.ts;
"""
    taxonomy = {
        "workstreams": {k: {"label": lbl, "patterns": pats} for k, pats, lbl in WORKSTREAMS},
        "issue_clusters": {k: {"label": lbl, "patterns": pats} for k, pats, lbl in ISSUE_CLUSTERS},
        "issue_markers": ISSUE_MARKERS,
        "resolution_markers": RESOLUTION_MARKERS,
        "decision_markers": DECISION_MARKERS,
        "decision_themes": {k: {"label": lbl, "patterns": pats} for k, pats, lbl in DECISION_THEMES},
    }
    (sql_dir / "engineering_diary_queries.sql").write_text(query_text, encoding="utf-8")
    (sql_dir / "engineering_diary_taxonomy.json").write_text(
        json.dumps(taxonomy, indent=2), encoding="utf-8"
    )

    # Tables.
    write_tables(
        table_dir=table_dir,
        fig01_rows=fig01_rows,
        fig02_rows=fig02_rows,
        fig06_rows=fig06_rows,
        decisions=dedup_decisions,
        days=days,
        cluster_issue=day_cluster_issue,
        cluster_resolution=day_cluster_resolution,
        first_issue_ts=first_issue_ts,
        first_resolution_ts=first_resolution_ts,
    )

    # Quote selection.
    write_quotes(quote_dir, quote_candidates)

    # Figures.
    render_figures(
        fig_dir=fig_dir,
        fig01_rows=fig01_rows,
        fig02_rows=fig02_rows,
        decisions=dedup_decisions,
        fig04_rows=fig04_rows,
        fig05_rows=fig05_rows,
        fig06_rows=fig06_rows,
        fig07_rows=fig07_rows,
    )

    return {
        "days": len(days),
        "messages": len(messages),
        "decisions": len(dedup_decisions),
        "quotes_candidates": len(quote_candidates),
    }


def write_tables(
    table_dir: Path,
    fig01_rows: list[dict[str, object]],
    fig02_rows: list[tuple],
    fig06_rows: list[tuple],
    decisions: list[dict[str, object]],
    days: list[str],
    cluster_issue: dict[str, Counter[str]],
    cluster_resolution: dict[str, Counter[str]],
    first_issue_ts: dict[tuple[str, str], datetime],
    first_resolution_ts: dict[tuple[str, str], datetime],
) -> None:
    ensure_dir(table_dir)

    # table01: milestone ledger from architecture milestones + peak activity
    p1 = table_dir / "table01_milestone_ledger.md"
    with p1.open("w", encoding="utf-8") as f:
        f.write("# Milestone Ledger\n\n")
        f.write("| Workstream | First Active Day | Peak Day | Peak Sessions | Total Sessions |\n")
        f.write("|---|---|---|---:|---:|\n")
        for ws_key, ws_label, first_day, peak_day, peak_sessions, total_sessions in fig02_rows:
            f.write(
                f"| {ws_label} | {first_day or 'n/a'} | {peak_day or 'n/a'} | {peak_sessions} | {total_sessions} |\n"
            )

        top_days = sorted(fig01_rows, key=lambda r: int(r["total_active_sessions"]), reverse=True)[:10]
        f.write("\n## Highest Engineering Activity Days\n\n")
        f.write("| Day | Active Sessions | Harness+Infra | Curator+ContextBench | Judge+Trace |\n")
        f.write("|---|---:|---:|---:|---:|\n")
        for r in top_days:
            f.write(
                f"| {r['day']} | {r['total_active_sessions']} | {r['harness_infra']} | {r['curator_contextbench']} | {r['llm_judge_trace']} |\n"
            )

    # table02: key decisions and tradeoffs
    p2 = table_dir / "table02_decisions_tradeoffs.md"
    with p2.open("w", encoding="utf-8") as f:
        f.write("# Decisions and Tradeoffs\n\n")
        f.write("| Day | Theme | Role | Decision Snippet |\n")
        f.write("|---|---|---|---|\n")
        for r in sorted(decisions, key=lambda d: (str(d["ts"]), int(d["score"])), reverse=True)[:30]:
            snippet = str(r["snippet"]).replace("|", " ")
            if len(snippet) > 180:
                snippet = snippet[:177] + "..."
            f.write(f"| {r['day']} | {r['theme']} | {r['role']} | {snippet} |\n")

    # table03: issue-resolution playbook
    # Build cluster-level lag statistics from first issue->resolution in session.
    lag_minutes: dict[str, list[float]] = defaultdict(list)
    sessions_with_both: Counter[str] = Counter()
    for (session_id, cluster_key), issue_ts in first_issue_ts.items():
        key = (session_id, cluster_key)
        if key in first_resolution_ts:
            delta = (first_resolution_ts[key] - issue_ts).total_seconds() / 60.0
            if delta >= 0:
                lag_minutes[cluster_key].append(delta)
                sessions_with_both[cluster_key] += 1

    p3 = table_dir / "table03_issue_resolution_playbook.md"
    with p3.open("w", encoding="utf-8") as f:
        f.write("# Issue-to-Resolution Playbook\n\n")
        f.write("| Issue Cluster | Issue Hits | Resolution Hits | Resolution Coverage | Median Session Lag (min) |\n")
        f.write("|---|---:|---:|---:|---:|\n")
        for c_key, _pats, c_label in ISSUE_CLUSTERS:
            issue_hits = sum(cluster_issue[d][c_key] for d in days)
            res_hits = sum(cluster_resolution[d][c_key] for d in days)
            coverage = (sessions_with_both[c_key] / max(1, len([1 for (sid, ck) in first_issue_ts if ck == c_key])))
            med = median(lag_minutes[c_key]) if lag_minutes[c_key] else 0.0
            f.write(
                f"| {c_label} | {issue_hits} | {res_hits} | {coverage:.2%} | {med:.1f} |\n"
            )

    # table04: architecture evolution by phase
    # Split timeline into thirds for a simple engineering diary arc.
    n = len(days)
    one = max(1, n // 3)
    phases = [
        ("Phase 1: Foundation", days[:one]),
        ("Phase 2: Scale-Up", days[one : 2 * one]),
        ("Phase 3: Stabilization", days[2 * one :]),
    ]
    p4 = table_dir / "table04_architecture_evolution.md"
    with p4.open("w", encoding="utf-8") as f:
        f.write("# Architecture Evolution\n\n")
        f.write("| Phase | Date Range | Dominant Workstreams | Build Focus |\n")
        f.write("|---|---|---|---|\n")
        for phase_name, phase_days in phases:
            if not phase_days:
                continue
            ws_totals = Counter()
            for d in phase_days:
                # approximate from fig01 rows
                row = next((r for r in fig01_rows if r["day"] == d), None)
                if row:
                    for ws_key, _p, _lbl in WORKSTREAMS:
                        ws_totals[workstream_label(ws_key)] += int(row[ws_key])
            top_ws = ", ".join([k for k, _v in ws_totals.most_common(3)])
            focus = {
                "Phase 1: Foundation": "Task scaffolding, QA checks, baseline harness setup",
                "Phase 2: Scale-Up": "Daytona/Harbor scaling, retrieval+curator integration, judge pipeline",
                "Phase 3: Stabilization": "Audit, rerun loops, promotion policy, variance closure",
            }.get(phase_name, "Execution and hardening")
            f.write(f"| {phase_name} | {phase_days[0]} to {phase_days[-1]} | {top_ws} | {focus} |\n")

    # table05: reusable components (builder-stage map).
    comp_stage: dict[str, list[tuple[str, float, str]]] = defaultdict(list)
    for _key, comp, stage, score, hint in fig06_rows:
        comp_stage[str(comp)].append((str(stage), float(score), str(hint)))

    p5 = table_dir / "table05_reusable_components.md"
    with p5.open("w", encoding="utf-8") as f:
        f.write("# Reusable Components for Other Teams\n\n")
        f.write("| Component | Best Use Stages | Reuse Score Profile | What To Reuse |\n")
        f.write("|---|---|---|---|\n")
        for _ws_key, ws_label, _fd, _pd, _pk, _tot in fig02_rows:
            stages = sorted(comp_stage.get(ws_label, []), key=lambda x: x[1], reverse=True)
            top = [s for s, score, _h in stages if score >= 0.7]
            if not top and stages:
                top = [stages[0][0]]
            profile = ", ".join([f"{s}:{score:.1f}" for s, score, _h in stages])
            hint = stages[0][2] if stages else "Reusable as a standalone subsystem."
            f.write(
                f"| {ws_label} | {', '.join(top)} | {profile} | {hint} |\n"
            )

    # table06: post placement guide
    p6 = table_dir / "table06_post_asset_placement.md"
    with p6.open("w", encoding="utf-8") as f:
        f.write("# Post Asset Placement Guide\n\n")
        f.write("| Post Section | Figure | Supporting Table | Why It Belongs Here |\n")
        f.write("|---|---|---|---|\n")
        f.write("| Opening: Why this benchmark existed | fig01_workstream_timeline.svg | table01_milestone_ledger.md | Shows scope and build intensity over time. |\n")
        f.write("| System design evolution | fig02_architecture_evolution.svg | table04_architecture_evolution.md | Makes architecture shifts visible by phase. |\n")
        f.write("| Decision process | fig03_decision_theme_mix.svg | table02_decisions_tradeoffs.md | Anchors narrative in concrete decision evidence. |\n")
        f.write("| Debugging and reliability | fig04_issue_resolution_timeline.svg | table03_issue_resolution_playbook.md | Quantifies issue pressure and closure behavior. |\n")
        f.write("| Incident taxonomy | fig05_issue_cluster_heatmap.svg | table03_issue_resolution_playbook.md | Shows where failures concentrated. |\n")
        f.write("| Reuse for other teams | fig06_reusable_components.svg | table05_reusable_components.md | Converts lessons into reusable implementation components. |\n")
        f.write("| Build cadence summary | fig07_commit_signal.svg | table05_reusable_components.md | Shows throughput of feature/fix iterations. |\n")


def write_quotes(quote_dir: Path, candidates: list[dict[str, object]], max_selected: int = 60) -> None:
    ensure_dir(quote_dir)

    cands = sorted(candidates, key=lambda r: (int(r["score"]), str(r["ts"])), reverse=True)
    write_csv(
        quote_dir / "quotes_engineering_candidates.csv",
        [
            "message_id",
            "session_id",
            "agent",
            "ts",
            "role",
            "source_path",
            "project_key",
            "score",
            "quote",
        ],
        [
            [
                r["message_id"],
                r["session_id"],
                r["agent"],
                r["ts"],
                r["role"],
                r["source_path"],
                r["project_key"],
                r["score"],
                r["text"],
            ]
            for r in cands
        ],
    )

    selected = []
    seen = set()
    per_session = Counter()
    for r in cands:
        if len(selected) >= max_selected:
            break
        norm = normalize_text(str(r["text"]))
        nh = hashlib.sha256(norm.encode("utf-8")).hexdigest()
        if nh in seen:
            continue
        if per_session[str(r["session_id"])] >= 2:
            continue
        red, flags = redact_text(str(r["text"]))
        selected.append(
            {
                "quote_id": f"qd{len(selected)+1:03d}",
                "message_id": r["message_id"],
                "session_id": r["session_id"],
                "agent": r["agent"],
                "ts": r["ts"],
                "role": r["role"],
                "source_path": r["source_path"],
                "project_key": r["project_key"],
                "score": r["score"],
                "text_original_hash": hashlib.sha256(str(r["text"]).encode("utf-8")).hexdigest(),
                "text_redacted_hash": hashlib.sha256(red.encode("utf-8")).hexdigest(),
                "redaction_flags": ",".join(flags),
                "quote_redacted": red,
            }
        )
        seen.add(nh)
        per_session[str(r["session_id"])] += 1

    cols = [
        "quote_id",
        "message_id",
        "session_id",
        "agent",
        "ts",
        "role",
        "source_path",
        "project_key",
        "score",
        "text_original_hash",
        "text_redacted_hash",
        "redaction_flags",
        "quote_redacted",
    ]
    write_csv(
        quote_dir / "quotes_engineering_selected.csv",
        cols,
        [[r[c] for c in cols] for r in selected],
    )

    md = quote_dir / "quotes_engineering_selected_redacted.md"
    with md.open("w", encoding="utf-8") as f:
        f.write("# Engineering Diary Quotes (Redacted)\n\n")
        for r in selected:
            f.write(f"## {r['quote_id']}\n")
            f.write(
                f"- ts: `{r['ts']}`\n"
                f"- session_id: `{r['session_id']}`\n"
                f"- role: `{r['role']}`\n"
                f"- score: `{r['score']}`\n"
                f"- redaction_flags: `{r['redaction_flags'] or 'none'}`\n\n"
            )
            f.write(f"> {r['quote_redacted']}\n\n")


def save_figure(fig: plt.Figure, path_svg: Path) -> None:
    ensure_dir(path_svg.parent)
    fig.tight_layout()
    fig.savefig(path_svg, format="svg", bbox_inches="tight")
    fig.savefig(path_svg.with_suffix(".png"), dpi=220, bbox_inches="tight")
    plt.close(fig)


def render_figures(
    fig_dir: Path,
    fig01_rows: list[dict[str, object]],
    fig02_rows: list[tuple],
    decisions: list[dict[str, object]],
    fig04_rows: list[tuple],
    fig05_rows: list[tuple],
    fig06_rows: list[tuple],
    fig07_rows: list[list[object]],
) -> None:
    setup_style()

    # fig01 workstream timeline
    days = [datetime.strptime(str(r["day"]), "%Y-%m-%d") for r in fig01_rows]
    ws_keys = [k for k, _p, _l in WORKSTREAMS]
    ws_labels = [l for _k, _p, l in WORKSTREAMS]
    data = np.array([[int(r[k]) for r in fig01_rows] for k in ws_keys], dtype=float)

    fig, ax = plt.subplots(figsize=(12, 5.2))
    colors = [
        PALETTE["pos"],
        PALETTE["accent"],
        "#7c7f86",
        "#9ca3af",
        "#cbd5e1",
        PALETTE["warning"],
    ]
    ax.stackplot(days, data, labels=ws_labels, colors=colors, alpha=0.86)
    ax.set_title("Engineering Diary: Workstream Intensity by Day")
    ax.set_ylabel("Active sessions/day")
    ax.grid(axis="y", alpha=0.35)
    ax.legend(loc="upper left", ncol=2, fontsize=8, frameon=False)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(days) // 10)))
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
    save_figure(fig, fig_dir / "fig01_workstream_timeline.svg")

    # fig02 architecture evolution (clean flowchart)
    ws_stats = {
        str(r[0]): {
            "label": str(r[1]),
            "first_day": str(r[2]),
            "peak_day": str(r[3]),
            "peak_sessions": int(r[4]),
            "total_sessions": int(r[5]),
        }
        for r in fig02_rows
    }
    total_issues = sum(int(r[1]) for r in fig04_rows)
    total_resolutions = sum(int(r[2]) for r in fig04_rows)
    resolution_ratio = (total_resolutions / total_issues) if total_issues else 0.0

    timeline_days = [datetime.strptime(str(r["day"]), "%Y-%m-%d") for r in fig01_rows]
    n_days = len(timeline_days)
    one = max(1, n_days // 3)
    phase_windows = [
        ("Foundation", timeline_days[:one]),
        ("Scale-Up", timeline_days[one : 2 * one]),
        ("Stabilization", timeline_days[2 * one :]),
    ]

    def phase_range(days_in_phase: list[datetime]) -> str:
        if not days_in_phase:
            return ""
        return f"{days_in_phase[0].strftime('%b %d')} - {days_in_phase[-1].strftime('%b %d')}"

    def ws_meta(ws_key: str) -> str:
        s = ws_stats[ws_key]
        peak_day = ""
        if s["peak_day"]:
            peak_day = datetime.strptime(s["peak_day"], "%Y-%m-%d").strftime("%b %d")
        return f"peak {s['peak_sessions']}/day ({peak_day})\n{s['total_sessions']} active sessions"

    fig, ax = plt.subplots(figsize=(12.2, 6.0))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    phase_x = [0.04, 0.365, 0.69]
    phase_w = 0.27
    phase_colors = [PALETTE["pos"], PALETTE["accent"], PALETTE["text_secondary"]]
    for i, (phase_name, phase_days) in enumerate(phase_windows):
        x = phase_x[i]
        band = FancyBboxPatch(
            (x, 0.90),
            phase_w,
            0.07,
            boxstyle="round,pad=0.004,rounding_size=0.01",
            linewidth=1.0,
            edgecolor=phase_colors[i],
            facecolor=PALETTE["bg"],
            alpha=0.95,
            transform=ax.transAxes,
        )
        ax.add_patch(band)
        ax.text(
            x + 0.015,
            0.955,
            phase_name,
            fontsize=10.5,
            fontweight="bold",
            color=phase_colors[i],
            transform=ax.transAxes,
            ha="left",
            va="top",
        )
        ax.text(
            x + 0.015,
            0.924,
            phase_range(phase_days),
            fontsize=7.8,
            color=PALETTE["text_secondary"],
            transform=ax.transAxes,
            ha="left",
            va="top",
        )

    nodes = {
        "skills": (0.06, 0.62, 0.22, 0.22),
        "harness": (0.06, 0.29, 0.22, 0.22),
        "ir": (0.39, 0.70, 0.22, 0.14),
        "curator": (0.39, 0.49, 0.22, 0.14),
        "judge": (0.39, 0.28, 0.22, 0.14),
        "dashboard": (0.72, 0.62, 0.22, 0.22),
        "ops_loop": (0.72, 0.29, 0.22, 0.22),
    }

    node_style = {
        "skills": ("Skills + QA + Task Factory", ws_meta("skills_qa_task_factory"), "#121224", PALETTE["pos"]),
        "harness": ("Harness + Infra", ws_meta("harness_infra"), "#121224", PALETTE["pos"]),
        "ir": ("IR Evaluation Pipeline", ws_meta("ir_eval_pipeline"), "#131529", PALETTE["accent"]),
        "curator": ("Curator + ContextBench", ws_meta("curator_contextbench"), "#131529", PALETTE["accent"]),
        "judge": ("LLM Judge + Trace Analysis", ws_meta("llm_judge_trace"), "#131529", PALETTE["accent"]),
        "dashboard": ("Dashboard + Task Audit", ws_meta("dashboard_audit"), "#111a20", PALETTE["text_secondary"]),
        "ops_loop": (
            "Promotion + Retry + Archive Loop",
            f"{total_resolutions:,}/{total_issues:,} issue closures\n{resolution_ratio:.1%} resolution throughput",
            "#111a20",
            PALETTE["text_secondary"],
        ),
    }

    def draw_node(node_key: str) -> None:
        x, y, w, h = nodes[node_key]
        title, meta, fill, edge = node_style[node_key]
        patch = FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0.01,rounding_size=0.015",
            linewidth=1.35,
            edgecolor=edge,
            facecolor=fill,
            alpha=0.98,
            transform=ax.transAxes,
        )
        ax.add_patch(patch)
        ax.text(
            x + 0.015,
            y + h - 0.03,
            title,
            fontsize=9.5,
            fontweight="bold",
            color=PALETTE["text"],
            transform=ax.transAxes,
            ha="left",
            va="top",
        )
        ax.text(
            x + 0.015,
            y + 0.03,
            meta,
            fontsize=8.1,
            color=PALETTE["text_secondary"],
            transform=ax.transAxes,
            ha="left",
            va="bottom",
            linespacing=1.2,
        )

    for node_key in nodes:
        draw_node(node_key)

    def edge(start: tuple[float, float], end: tuple[float, float], label: str = "", dashed: bool = False) -> None:
        arr = FancyArrowPatch(
            start,
            end,
            arrowstyle="-|>",
            mutation_scale=12,
            linewidth=1.35,
            color=PALETTE["text_secondary"],
            linestyle="--" if dashed else "-",
            transform=ax.transAxes,
        )
        ax.add_patch(arr)
        if label:
            mx = (start[0] + end[0]) / 2
            my = (start[1] + end[1]) / 2
            ax.text(
                mx,
                my + 0.018,
                label,
                fontsize=7.5,
                color=PALETTE["text_secondary"],
                transform=ax.transAxes,
                ha="center",
                va="center",
            )

    # Non-crossing left-to-right flow
    edge((0.28, 0.75), (0.39, 0.77), "task specs")
    edge((0.28, 0.73), (0.39, 0.56), "curation targets")
    edge((0.28, 0.40), (0.39, 0.56), "runtime constraints")
    edge((0.28, 0.38), (0.39, 0.35), "execution traces")
    edge((0.50, 0.70), (0.50, 0.63), "retrieval checks")
    edge((0.50, 0.49), (0.50, 0.42), "curated context")
    edge((0.61, 0.35), (0.72, 0.73), "scored outcomes")
    edge((0.61, 0.56), (0.72, 0.40), "run evidence")
    edge((0.83, 0.62), (0.83, 0.51), "triage decisions")
    edge((0.72, 0.31), (0.28, 0.63), "feedback to task/QA", dashed=True)

    ax.set_title("Architecture Evolution: Build System to Audit Loop")
    save_figure(fig, fig_dir / "fig02_architecture_evolution.svg")

    # fig03 decision focus by build phase (matrix, not snippet bars)
    day_keys = [str(r["day"]) for r in fig01_rows]
    n_days = len(day_keys)
    one = max(1, n_days // 3)
    phase_map: dict[str, str] = {}
    for i, d in enumerate(day_keys):
        if i < one:
            phase_map[d] = "Foundation"
        elif i < 2 * one:
            phase_map[d] = "Scale-Up"
        else:
            phase_map[d] = "Stabilization"
    phases = ["Foundation", "Scale-Up", "Stabilization"]

    theme_counts = Counter(str(r["theme"]) for r in decisions)
    top_themes = [t for t, _n in theme_counts.most_common(6) if t != "General"][:5]
    if "General" in theme_counts:
        top_themes.append("General")
    if not top_themes:
        top_themes = ["General"]

    raw = np.zeros((len(top_themes), len(phases)), dtype=float)
    t_ix = {t: i for i, t in enumerate(top_themes)}
    p_ix = {p: i for i, p in enumerate(phases)}
    for d in decisions:
        theme = str(d["theme"])
        phase = phase_map.get(str(d["day"]))
        if theme in t_ix and phase in p_ix:
            raw[t_ix[theme], p_ix[phase]] += 1

    col_sums = raw.sum(axis=0)
    matrix = np.divide(raw, np.where(col_sums == 0, 1.0, col_sums), where=np.ones_like(raw, dtype=bool))

    fig, ax = plt.subplots(figsize=(10.8, 5.0))
    sg_cmap = LinearSegmentedColormap.from_list(
        "sg_blurple",
        ["#0b0b12", "#1c1630", "#3b2478", "#8552f2", "#c7b6ff"],
    )
    vmax = max(0.01, float(np.max(matrix)))
    im = ax.imshow(matrix, aspect="auto", cmap=sg_cmap, vmin=0, vmax=vmax)
    ax.set_yticks(range(len(top_themes)))
    ax.set_yticklabels(top_themes)
    ax.set_xticks(range(len(phases)))
    ax.set_xticklabels(phases)
    ax.set_title("Decision Focus by Build Phase")
    ax.set_ylabel("Decision theme")
    ax.set_xlabel("Architecture phase")
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            ax.text(
                j,
                i,
                f"{matrix[i, j]*100:.0f}%",
                ha="center",
                va="center",
                fontsize=8,
                color="#111111" if (matrix[i, j] / vmax) > 0.72 else PALETTE["text"],
            )
    cb = fig.colorbar(im, ax=ax, pad=0.02)
    cb.set_label("Relative phase focus")
    cb.ax.tick_params(labelsize=8, colors=PALETTE["text"])
    cb.outline.set_edgecolor(PALETTE["grid"])
    save_figure(fig, fig_dir / "fig03_decision_theme_mix.svg")

    # fig04 issues vs resolutions timeline
    d4 = [datetime.strptime(r[0], "%Y-%m-%d") for r in fig04_rows]
    issues = [int(r[1]) for r in fig04_rows]
    resolutions = [int(r[2]) for r in fig04_rows]
    fig, ax = plt.subplots(figsize=(11.5, 4.8))
    ax.plot(d4, issues, color=PALETTE["neg"], linewidth=2.0, label="Issue mentions")
    ax.plot(d4, resolutions, color=PALETTE["success"], linewidth=2.0, label="Resolution mentions")
    ax.fill_between(d4, issues, resolutions, where=np.array(resolutions) >= np.array(issues),
                    color=PALETTE["success"], alpha=0.14)
    ax.fill_between(d4, issues, resolutions, where=np.array(issues) > np.array(resolutions),
                    color=PALETTE["neg"], alpha=0.12)
    ax.set_title("Issue Pressure vs Resolution Throughput")
    ax.set_ylabel("Mentions/day")
    ax.grid(axis="y", alpha=0.35)
    ax.legend(frameon=False)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(d4) // 10)))
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
    save_figure(fig, fig_dir / "fig04_issue_resolution_timeline.svg")

    # fig05 issue cluster heatmap (issues only)
    days_sorted = sorted({r[0] for r in fig05_rows})
    clusters = [lbl for _k, _p, lbl in ISSUE_CLUSTERS]
    d_ix = {d: i for i, d in enumerate(days_sorted)}
    c_ix = {lbl: i for i, lbl in enumerate(clusters)}
    matrix = np.zeros((len(clusters), len(days_sorted)), dtype=float)
    for day, _ck, clabel, issue_hits, _res_hits in fig05_rows:
        matrix[c_ix[clabel], d_ix[day]] = int(issue_hits)

    fig, ax = plt.subplots(figsize=(12.2, 4.8))
    im = ax.imshow(matrix, aspect="auto", cmap="magma", interpolation="nearest")
    ax.set_yticks(range(len(clusters)))
    ax.set_yticklabels(clusters)
    step = max(1, len(days_sorted) // 12)
    xt = list(range(0, len(days_sorted), step))
    ax.set_xticks(xt)
    ax.set_xticklabels([days_sorted[i] for i in xt], rotation=30, ha="right")
    ax.set_title("Issue Cluster Heatmap")
    cb = fig.colorbar(im, ax=ax, pad=0.02)
    cb.set_label("Issue mentions")
    cb.ax.tick_params(labelsize=8, colors=PALETTE["text"])
    cb.outline.set_edgecolor(PALETTE["grid"])
    save_figure(fig, fig_dir / "fig05_issue_cluster_heatmap.svg")

    # fig06 reusable components map for benchmark builders
    components = [label for _k, _p, label in WORKSTREAMS]
    stages = ["Task Design", "Quality Gates", "Execution Harness", "Evaluation Analysis", "Operations"]
    score_mat = np.zeros((len(components), len(stages)), dtype=float)
    c_ix = {c: i for i, c in enumerate(components)}
    s_ix = {s: i for i, s in enumerate(stages)}
    for _key, comp, stage, score, _hint in fig06_rows:
        score_mat[c_ix[str(comp)], s_ix[str(stage)]] = float(score)

    fig, ax = plt.subplots(figsize=(11.6, 5.3))
    sg_cmap = LinearSegmentedColormap.from_list(
        "sg_blurple",
        ["#0b0b12", "#1c1630", "#3b2478", "#8552f2", "#c7b6ff"],
    )
    im = ax.imshow(score_mat, aspect="auto", cmap=sg_cmap, vmin=0, vmax=1.0)
    ax.set_yticks(range(len(components)))
    ax.set_yticklabels(components)
    ax.set_xticks(range(len(stages)))
    ax.set_xticklabels(stages, rotation=20, ha="right")
    ax.set_title("Reusable Components Map for Benchmark Builders")
    ax.set_xlabel("Where to reuse it in your benchmark build")
    ax.set_ylabel("Component")
    for i in range(score_mat.shape[0]):
        for j in range(score_mat.shape[1]):
            v = score_mat[i, j]
            badge = "High" if v >= 0.75 else ("Med" if v >= 0.45 else "Low")
            ax.text(
                j,
                i,
                badge,
                ha="center",
                va="center",
                fontsize=7.8,
                color="#111111" if v > 0.72 else PALETTE["text"],
            )
    cb = fig.colorbar(im, ax=ax, pad=0.02)
    cb.set_label("Reuse suitability")
    cb.ax.tick_params(labelsize=8, colors=PALETTE["text"])
    cb.outline.set_edgecolor(PALETTE["grid"])
    save_figure(fig, fig_dir / "fig06_reusable_components.svg")

    # fig07 commit signal timeline
    cdays = [datetime.strptime(str(r[0]), "%Y-%m-%d") for r in fig07_rows]
    feat = [int(r[1]) for r in fig07_rows]
    fix = [int(r[2]) for r in fig07_rows]
    docs = [int(r[4]) for r in fig07_rows]
    fig, ax = plt.subplots(figsize=(11.4, 4.8))
    ax.plot(cdays, feat, color=PALETTE["pos"], linewidth=2.0, label="feat")
    ax.plot(cdays, fix, color=PALETTE["neg"], linewidth=2.0, label="fix")
    ax.plot(cdays, docs, color=PALETTE["text_secondary"], linewidth=1.6, label="docs")
    ax.set_title("Build Log Signal from Conversation Updates")
    ax.set_ylabel("Commit-style lines/day")
    ax.grid(axis="y", alpha=0.35)
    ax.legend(frameon=False)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(cdays) // 10)))
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
    save_figure(fig, fig_dir / "fig07_commit_signal.svg")


def write_readme(out_root: Path, summary: dict[str, object]) -> None:
    p = out_root / "README.md"
    p.write_text(
        f"""# Engineering Diary Assets (Conversation DB)

Generated: {now_iso()}

This bundle is focused on **build milestones, decisions, architecture evolution, and issue resolution** from conversation content.

## Inputs
- DB: `data/conversations/codescalebench_conversations.db`
- Filter: non-external sessions with project key matching CodeScaleBench/CodeContextBench

## Outputs
- `csv/fig01_workstream_timeline.csv`
- `csv/fig02_architecture_milestones.csv`
- `csv/fig03_decision_points.csv`
- `csv/fig04_issue_resolution_timeline.csv`
- `csv/fig05_issue_cluster_heatmap.csv`
- `csv/fig06_reusable_components.csv`
- `csv/fig07_commit_signal.csv`
- `figures/*.svg` and `figures/*.png`
- `tables/*.md`
- `quotes/quotes_engineering_selected_redacted.md`
- `sql/engineering_diary_queries.sql`
- `sql/engineering_diary_taxonomy.json`

## Summary
- Days covered: {summary.get('days')}
- Messages analyzed: {summary.get('messages')}
- Decision snippets: {summary.get('decisions')}
- Quote candidates: {summary.get('quotes_candidates')}
""",
        encoding="utf-8",
    )


def run(args: argparse.Namespace) -> int:
    db_path = Path(args.db_path).resolve()
    out_root = Path(args.out_root).resolve()
    ensure_dir(out_root)

    if not db_path.exists():
        raise SystemExit(f"DB not found: {db_path}")

    conn = sqlite3.connect(str(db_path))
    try:
        messages = fetch_messages(conn, args.start_date, args.end_date)
        if not messages:
            raise SystemExit("No messages matched extraction filters")

        summary = export_diary_assets(messages, out_root)
        write_readme(out_root, summary)

        manifest = {
            "generated_at": now_iso(),
            "db_path": str(db_path),
            "out_root": str(out_root),
            "filters": {
                "start_date": args.start_date,
                "end_date": args.end_date,
                "projects": ["*CodeScaleBench*", "*CodeContextBench*"],
                "exclude_agents": "external_%",
            },
            "summary": summary,
        }
        (out_root / "engineering_diary_manifest.json").write_text(
            json.dumps(manifest, indent=2), encoding="utf-8"
        )

        print(f"DB: {db_path}")
        print(f"Out: {out_root}")
        print(json.dumps(summary, indent=2))
        return 0
    finally:
        conn.close()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--db-path",
        default="data/conversations/codescalebench_conversations.db",
        help="Path to unified conversation SQLite DB",
    )
    p.add_argument(
        "--out-root",
        default="docs/assets/blog/medium",
        help="Output root for blog assets",
    )
    p.add_argument(
        "--start-date",
        default="2026-02-01",
        help="Inclusive lower timestamp bound (ISO prefix accepted)",
    )
    p.add_argument(
        "--end-date",
        default="2026-03-06",
        help="Exclusive upper timestamp bound (ISO prefix accepted)",
    )
    return p


def main() -> int:
    return run(build_parser().parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
