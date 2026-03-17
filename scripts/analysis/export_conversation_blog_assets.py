#!/usr/bin/env python3
"""Export reproducible blog assets from unified conversation DB.

Outputs under data/conversations/blog_assets:
- csv/: figure/query datasets
- figures/: PNG charts (if matplotlib available)
- tables/: markdown summary tables
- quotes/: candidate + selected + redacted snippet files
- provenance/: latest ingest run metadata + export manifest

Designed for SQLite compatibility and deterministic extraction.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import sqlite3
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_csv(path: Path, columns: list[str], rows: Iterable[tuple | list]) -> int:
    ensure_dir(path.parent)
    count = 0
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(columns)
        for r in rows:
            w.writerow(r)
            count += 1
    return count


def run_query(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> tuple[list[str], list[tuple]]:
    cur = conn.execute(sql, params)
    cols = [c[0] for c in cur.description]
    rows = cur.fetchall()
    return cols, rows


def safe_slug(s: str) -> str:
    return re.sub(r"[^a-z0-9_]+", "_", s.lower()).strip("_")


def build_figure_queries() -> dict[str, str]:
    return {
        "fig01_activity_timeline": """
WITH msg_daily AS (
  SELECT substr(ts,1,10) AS day, agent, COUNT(*) AS messages
  FROM messages
  WHERE ts IS NOT NULL
  GROUP BY 1,2
),
sess_daily AS (
  SELECT substr(COALESCE(last_at, started_at),1,10) AS day, agent, COUNT(*) AS sessions
  FROM sessions
  WHERE COALESCE(last_at, started_at) IS NOT NULL
  GROUP BY 1,2
),
combined AS (
  SELECT day, agent, messages, 0 AS sessions FROM msg_daily
  UNION ALL
  SELECT day, agent, 0 AS messages, sessions FROM sess_daily
)
SELECT day, agent, SUM(messages) AS messages, SUM(sessions) AS sessions
FROM combined
GROUP BY day, agent
ORDER BY day, agent;
""",
        "fig02_agent_mix": """
SELECT substr(ts,1,7) AS ym, agent, COUNT(*) AS messages
FROM messages
WHERE ts IS NOT NULL
GROUP BY 1,2
ORDER BY 1,2;
""",
        "fig03_tool_intensity": """
SELECT agent, session_id, msg_count, tool_calls, error_count,
       ROUND(CAST(tool_calls AS REAL)/NULLIF(msg_count,0),4) AS tools_per_msg,
       started_at, last_at
FROM sessions
ORDER BY tool_calls DESC;
""",
        "fig04_error_retry_pressure": """
WITH retry_hits AS (
  SELECT m.session_id, m.agent, COUNT(*) AS retry_mentions
  FROM messages m
  WHERE m.text IS NOT NULL
    AND (
      LOWER(m.text) LIKE '%retry%'
      OR LOWER(m.text) LIKE '%retried%'
      OR LOWER(m.text) LIKE '%backoff%'
      OR LOWER(m.text) LIKE '%timeout%'
      OR m.text LIKE '%429%'
    )
  GROUP BY 1,2
)
SELECT s.agent, s.session_id, s.error_count, s.tool_calls, s.msg_count,
       COALESCE(r.retry_mentions,0) AS retry_mentions, s.started_at, s.last_at
FROM sessions s
LEFT JOIN retry_hits r ON r.session_id=s.session_id AND r.agent=s.agent
ORDER BY s.error_count DESC, retry_mentions DESC;
""",
        "fig05_incident_heatmap": """
WITH tagged AS (
  SELECT substr(m.ts,1,10) AS day, m.agent, 'infra' AS theme
  FROM messages m
  WHERE m.ts IS NOT NULL
    AND m.text IS NOT NULL
    AND (
      LOWER(m.text) LIKE '%daytona%'
      OR LOWER(m.text) LIKE '%docker%'
      OR LOWER(m.text) LIKE '%registry%'
      OR LOWER(m.text) LIKE '%network%'
      OR LOWER(m.text) LIKE '%ssh%'
    )
  UNION ALL
  SELECT substr(m.ts,1,10) AS day, m.agent, 'benchmark_ops' AS theme
  FROM messages m
  WHERE m.ts IS NOT NULL
    AND m.text IS NOT NULL
    AND (
      LOWER(m.text) LIKE '%oracle%'
      OR LOWER(m.text) LIKE '%verifier%'
      OR LOWER(m.text) LIKE '%artifact%'
      OR LOWER(m.text) LIKE '%harbor%'
    )
  UNION ALL
  SELECT substr(m.ts,1,10) AS day, m.agent, 'agent_design' AS theme
  FROM messages m
  WHERE m.ts IS NOT NULL
    AND m.text IS NOT NULL
    AND (
      LOWER(m.text) LIKE '%mcp%'
      OR LOWER(m.text) LIKE '%retrieval%'
      OR LOWER(m.text) LIKE '%context%'
    )
)
SELECT day, agent, theme, COUNT(*) AS hits
FROM tagged
GROUP BY 1,2,3
ORDER BY 1,2,3;
""",
        "fig06_dedupe_impact": """
SELECT id, started_at, completed_at,
       session_count, message_count,
       json_extract(notes,'$.dedupe.input_rows')   AS dedupe_input_rows,
       json_extract(notes,'$.dedupe.kept_rows')    AS dedupe_kept_rows,
       json_extract(notes,'$.dedupe.dropped_rows') AS dedupe_dropped_rows
FROM ingest_runs
ORDER BY id;
""",
        "fig07_cost_throughput_proxy": """
WITH msg AS (
  SELECT substr(ts,1,10) AS day, COUNT(*) AS messages
  FROM messages WHERE ts IS NOT NULL GROUP BY 1
),
tools AS (
  SELECT substr(COALESCE(last_at, started_at),1,10) AS day, SUM(tool_calls) AS tool_calls
  FROM sessions WHERE COALESCE(last_at, started_at) IS NOT NULL GROUP BY 1
),
combined AS (
  SELECT day, messages, 0 AS tool_calls FROM msg
  UNION ALL
  SELECT day, 0 AS messages, tool_calls FROM tools
)
SELECT day, SUM(messages) AS messages, SUM(tool_calls) AS tool_calls
FROM combined
GROUP BY day
ORDER BY day;
""",
    }


def maybe_plot(csv_dir: Path, fig_dir: Path) -> list[str]:
    outputs: list[str] = []
    try:
        import matplotlib.pyplot as plt  # type: ignore
    except Exception:
        return outputs

    ensure_dir(fig_dir)

    def read_csv(path: Path) -> list[dict[str, str]]:
        with path.open("r", encoding="utf-8") as f:
            return list(csv.DictReader(f))

    # fig01
    p = csv_dir / "fig01_activity_timeline.csv"
    if p.exists():
        rows = read_csv(p)
        by_day: dict[str, int] = defaultdict(int)
        for r in rows:
            by_day[r["day"]] += int(r["messages"])
        days = sorted(by_day)
        vals = [by_day[d] for d in days]
        plt.figure(figsize=(11, 4))
        plt.plot(days, vals, linewidth=1.5)
        plt.xticks(rotation=45, ha="right")
        plt.title("Daily Messages Across Agents")
        plt.tight_layout()
        out = fig_dir / "fig01_activity_timeline.png"
        plt.savefig(out, dpi=160)
        plt.close()
        outputs.append(str(out))

    # fig03
    p = csv_dir / "fig03_tool_intensity.csv"
    if p.exists():
        rows = read_csv(p)
        by_agent: dict[str, list[float]] = defaultdict(list)
        for r in rows:
            try:
                by_agent[r["agent"]].append(float(r["tools_per_msg"] or 0.0))
            except ValueError:
                pass
        labels = sorted(by_agent)
        vals = [by_agent[k] for k in labels]
        if labels:
            plt.figure(figsize=(11, 4))
            plt.violinplot(vals, showmeans=True, showmedians=True)
            plt.xticks(range(1, len(labels) + 1), labels, rotation=35, ha="right")
            plt.title("Tools per Message Distribution by Agent")
            plt.tight_layout()
            out = fig_dir / "fig03_tool_intensity_violin.png"
            plt.savefig(out, dpi=160)
            plt.close()
            outputs.append(str(out))

    # fig06
    p = csv_dir / "fig06_dedupe_impact.csv"
    if p.exists():
        rows = read_csv(p)
        xs = [str(r["id"]) for r in rows]
        kept = [int(float(r["dedupe_kept_rows"] or 0)) for r in rows]
        dropped = [int(float(r["dedupe_dropped_rows"] or 0)) for r in rows]
        if xs:
            plt.figure(figsize=(8, 4))
            plt.bar(xs, kept, label="kept")
            plt.bar(xs, dropped, bottom=kept, label="dropped")
            plt.title("Dedupe Impact by Ingest Run")
            plt.xlabel("ingest run id")
            plt.ylabel("sessions")
            plt.legend()
            plt.tight_layout()
            out = fig_dir / "fig06_dedupe_impact.png"
            plt.savefig(out, dpi=160)
            plt.close()
            outputs.append(str(out))

    return outputs


def p95(values: list[float]) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    idx = max(0, math.ceil(0.95 * len(s)) - 1)
    return s[idx]


def write_tables(conn: sqlite3.Connection, out_dir: Path) -> list[Path]:
    ensure_dir(out_dir)
    written: list[Path] = []

    # table01 milestones
    _, day_rows = run_query(
        conn,
        """
SELECT substr(ts,1,10) AS day, COUNT(*) AS messages
FROM messages
WHERE ts IS NOT NULL
GROUP BY 1
ORDER BY messages DESC
LIMIT 15;
""",
    )
    _, sess_rows = run_query(
        conn,
        """
SELECT agent, session_id, msg_count, tool_calls, error_count, started_at, last_at
FROM sessions
ORDER BY (msg_count + tool_calls * 3 + error_count * 10) DESC
LIMIT 15;
""",
    )
    p = out_dir / "table01_milestones.md"
    with p.open("w", encoding="utf-8") as f:
        f.write("# Milestones\n\n")
        f.write("## Highest-Volume Days\n\n")
        f.write("| Day | Messages |\n|---|---:|\n")
        for r in day_rows:
            f.write(f"| {r[0]} | {r[1]} |\n")
        f.write("\n## Highest-Intensity Sessions\n\n")
        f.write("| Agent | Session | Msgs | Tool Calls | Errors | Started | Last |\n|---|---|---:|---:|---:|---|---|\n")
        for r in sess_rows:
            f.write(f"| {r[0]} | `{r[1]}` | {r[2]} | {r[3]} | {r[4]} | {r[5] or ''} | {r[6] or ''} |\n")
    written.append(p)

    # table02 tool use patterns
    _, rows = run_query(
        conn,
        """
SELECT agent, msg_count, tool_calls
FROM sessions;
""",
    )
    by_agent: dict[str, dict[str, object]] = {}
    for agent, msg_count, tool_calls in rows:
        d = by_agent.setdefault(agent, {"sessions": 0, "tools": [], "ratio": []})
        d["sessions"] = int(d["sessions"]) + 1
        d["tools"].append(float(tool_calls))  # type: ignore[index]
        ratio = float(tool_calls) / float(msg_count) if msg_count else 0.0
        d["ratio"].append(ratio)  # type: ignore[index]

    p = out_dir / "table02_tool_use_patterns.md"
    with p.open("w", encoding="utf-8") as f:
        f.write("# Tool Use Patterns\n\n")
        f.write("| Agent | Sessions | Avg Tool Calls | P95 Tool Calls | Avg Tools/Msg |\n")
        f.write("|---|---:|---:|---:|---:|\n")
        for agent in sorted(by_agent):
            d = by_agent[agent]
            tools: list[float] = d["tools"]  # type: ignore[assignment]
            ratio: list[float] = d["ratio"]  # type: ignore[assignment]
            avg_tools = sum(tools) / len(tools)
            avg_ratio = sum(ratio) / len(ratio)
            f.write(
                f"| {agent} | {d['sessions']} | {avg_tools:.2f} | {p95(tools):.2f} | {avg_ratio:.4f} |\n"
            )
    written.append(p)

    # table03 error/retry
    _, rows = run_query(
        conn,
        """
WITH retry_hits AS (
  SELECT m.session_id, m.agent, COUNT(*) AS retry_mentions
  FROM messages m
  WHERE m.text IS NOT NULL
    AND (
      LOWER(m.text) LIKE '%retry%'
      OR LOWER(m.text) LIKE '%retried%'
      OR LOWER(m.text) LIKE '%backoff%'
      OR LOWER(m.text) LIKE '%timeout%'
      OR m.text LIKE '%429%'
    )
  GROUP BY 1,2
)
SELECT s.agent, s.session_id, s.error_count, s.tool_calls, s.msg_count,
       COALESCE(r.retry_mentions,0) AS retry_mentions, s.started_at, s.last_at
FROM sessions s
LEFT JOIN retry_hits r ON r.session_id=s.session_id AND r.agent=s.agent
WHERE s.error_count > 0 OR COALESCE(r.retry_mentions,0) > 0
ORDER BY s.error_count DESC, retry_mentions DESC
LIMIT 25;
""",
    )
    p = out_dir / "table03_error_retry_patterns.md"
    with p.open("w", encoding="utf-8") as f:
        f.write("# Error and Retry Patterns\n\n")
        f.write("| Agent | Session | Errors | Retry Mentions | Tool Calls | Msgs | Started | Last |\n")
        f.write("|---|---|---:|---:|---:|---:|---|---|\n")
        for r in rows:
            f.write(
                f"| {r[0]} | `{r[1]}` | {r[2]} | {r[5]} | {r[3]} | {r[4]} | {r[6] or ''} | {r[7] or ''} |\n"
            )
    written.append(p)

    # table04 cost/throughput/process evolution proxy
    _, rows = run_query(
        conn,
        """
WITH msg AS (
  SELECT substr(ts,1,10) AS day, COUNT(*) AS messages
  FROM messages WHERE ts IS NOT NULL GROUP BY 1
),
tools AS (
  SELECT substr(COALESCE(last_at, started_at),1,10) AS day, SUM(tool_calls) AS tool_calls, COUNT(*) AS sessions
  FROM sessions WHERE COALESCE(last_at, started_at) IS NOT NULL GROUP BY 1
),
combined AS (
  SELECT day, messages, 0 AS tool_calls, 0 AS sessions FROM msg
  UNION ALL
  SELECT day, 0 AS messages, tool_calls, sessions FROM tools
)
SELECT day, SUM(messages) AS messages, SUM(tool_calls) AS tool_calls, SUM(sessions) AS sessions
FROM combined
GROUP BY day
ORDER BY day;
""",
    )
    p = out_dir / "table04_cost_throughput_process.md"
    with p.open("w", encoding="utf-8") as f:
        f.write("# Cost/Throughput/Process Evolution (Proxy)\n\n")
        f.write("| Day | Phase | Messages | Tool Calls | Sessions |\n|---|---|---:|---:|---:|\n")
        days = [r[0] for r in rows]
        n = len(days)
        for i, r in enumerate(rows):
            if n == 0:
                phase = "n/a"
            elif i < n / 3:
                phase = "early"
            elif i < (2 * n) / 3:
                phase = "mid"
            else:
                phase = "late"
            f.write(f"| {r[0]} | {phase} | {r[1]} | {r[2]} | {r[3]} |\n")
    written.append(p)

    # table05 data quality limits
    _, sess = run_query(
        conn,
        """
SELECT agent,
       COUNT(*) AS sessions,
       SUM(CASE WHEN started_at IS NOT NULL THEN 1 ELSE 0 END) AS started_present,
       SUM(CASE WHEN last_at IS NOT NULL THEN 1 ELSE 0 END) AS last_present
FROM sessions
GROUP BY agent
ORDER BY sessions DESC;
""",
    )
    _, msgs = run_query(
        conn,
        """
SELECT agent, COUNT(*) AS messages,
       SUM(CASE WHEN ts IS NOT NULL THEN 1 ELSE 0 END) AS ts_present
FROM messages
GROUP BY agent
ORDER BY messages DESC;
""",
    )
    p = out_dir / "table05_data_quality_limits.md"
    with p.open("w", encoding="utf-8") as f:
        f.write("# Data Quality and Limits\n\n")
        f.write("## Session Timestamp Coverage\n\n")
        f.write("| Agent | Sessions | Started Present | Last Present |\n|---|---:|---:|---:|\n")
        for r in sess:
            f.write(f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} |\n")
        f.write("\n## Message Timestamp Coverage\n\n")
        f.write("| Agent | Messages | ts Present |\n|---|---:|---:|\n")
        for r in msgs:
            f.write(f"| {r[0]} | {r[1]} | {r[2]} |\n")
        f.write(
            "\n## Known Caveats\n\n"
            "- Cursor transcripts in this DB currently have null message timestamps.\n"
            "- Copilot rows are session-state metadata pseudo-messages, not full transcripts.\n"
            "- External sources may include mirrored historical material despite dedupe safeguards.\n"
            "- Alias history (CodeContextBench/CodeScaleBench + dashboard siblings) is intentionally included.\n"
        )
    written.append(p)

    return written


SENSITIVE_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("email", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}")),
    ("home_path", re.compile(r"/home/[A-Za-z0-9_.-]+")),
    ("api_key", re.compile(r"\\b(sk-[A-Za-z0-9]{16,}|ghp_[A-Za-z0-9]{20,}|AIza[0-9A-Za-z-_]{20,})\\b")),
    ("jwt", re.compile(r"\\beyJ[A-Za-z0-9_-]{10,}\\.[A-Za-z0-9._-]{10,}\\.[A-Za-z0-9._-]{10,}\\b")),
]


def normalize_text_for_dedupe(text: str) -> str:
    text = text.lower()
    text = re.sub(r"\\s+", " ", text)
    text = re.sub(r"[^a-z0-9 ]+", "", text)
    return text.strip()


def redact_text(text: str) -> tuple[str, list[str]]:
    red = text
    flags: list[str] = []
    for name, pat in SENSITIVE_PATTERNS:
        if pat.search(red):
            red = pat.sub(f"[{name.upper()}_REDACTED]", red)
            flags.append(name)
    return red, sorted(set(flags))


@dataclass
class QuoteRec:
    message_id: int
    session_id: str
    agent: str
    ts: str | None
    role: str
    source_path: str
    project_key: str
    quote: str
    score: int


def score_quote(text: str) -> int:
    t = text.lower()
    score = 0
    keywords = {
        "incident": ["error", "failed", "timeout", "429", "retry", "panic", "oom"],
        "infra": ["daytona", "docker", "network", "registry", "ssh"],
        "benchmark": ["harbor", "oracle", "verifier", "artifact", "benchmark"],
        "design": ["tradeoff", "dedupe", "alias", "reproducibility", "mcp", "context"],
    }
    for words in keywords.values():
        if any(w in t for w in words):
            score += 2
    if 120 <= len(text) <= 500:
        score += 2
    if any(c.isdigit() for c in text):
        score += 1
    return score


def build_quotes(conn: sqlite3.Connection, out_dir: Path, select_n: int = 80) -> list[Path]:
    ensure_dir(out_dir)
    written: list[Path] = []

    sql = """
SELECT m.id, m.session_id, m.agent, m.ts, m.role, s.source_path, s.project_key,
       substr(m.text,1,600) AS quote
FROM messages m
JOIN sessions s ON s.session_id=m.session_id AND s.agent=m.agent
WHERE m.role IN ('user','assistant')
  AND m.text IS NOT NULL
  AND length(trim(m.text)) BETWEEN 80 AND 600
  AND m.agent NOT LIKE 'external_%'
ORDER BY m.ts DESC;
"""
    cur = conn.execute(sql)
    candidates: list[QuoteRec] = []
    for row in cur.fetchall():
        q = row[7] or ""
        sc = score_quote(q)
        if sc < 3:
            continue
        candidates.append(
            QuoteRec(
                message_id=int(row[0]),
                session_id=row[1],
                agent=row[2],
                ts=row[3],
                role=row[4],
                source_path=row[5],
                project_key=row[6],
                quote=q,
                score=sc,
            )
        )

    cand_csv = out_dir / "quotes_candidates.csv"
    write_csv(
        cand_csv,
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
            (
                q.message_id,
                q.session_id,
                q.agent,
                q.ts,
                q.role,
                q.source_path,
                q.project_key,
                q.score,
                q.quote,
            )
            for q in candidates
        ],
    )
    written.append(cand_csv)

    candidates.sort(key=lambda q: (q.score, q.ts or "", q.message_id), reverse=True)

    selected: list[dict[str, object]] = []
    seen_hash: set[str] = set()
    seen_norm: set[str] = set()
    per_session: Counter[str] = Counter()
    per_agent: Counter[str] = Counter()

    for q in candidates:
        if len(selected) >= select_n:
            break
        if per_session[q.session_id] >= 2:
            continue
        if per_agent[q.agent] >= max(10, select_n // 2):
            continue

        exact_h = hashlib.sha256(q.quote.encode("utf-8")).hexdigest()
        norm = normalize_text_for_dedupe(q.quote)
        norm_h = hashlib.sha256(norm.encode("utf-8")).hexdigest()
        if exact_h in seen_hash or norm_h in seen_norm:
            continue

        redacted, flags = redact_text(q.quote)
        selected.append(
            {
                "quote_id": f"q{len(selected)+1:03d}",
                "message_id": q.message_id,
                "session_id": q.session_id,
                "agent": q.agent,
                "ts": q.ts,
                "role": q.role,
                "source_path": q.source_path,
                "project_key": q.project_key,
                "score": q.score,
                "text_original_hash": exact_h,
                "text_redacted_hash": hashlib.sha256(redacted.encode("utf-8")).hexdigest(),
                "redaction_flags": ",".join(flags),
                "theme_tags": infer_tags(q.quote),
                "quote_redacted": redacted,
            }
        )

        seen_hash.add(exact_h)
        seen_norm.add(norm_h)
        per_session[q.session_id] += 1
        per_agent[q.agent] += 1

    sel_csv = out_dir / "quotes_selected.csv"
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
        "theme_tags",
        "quote_redacted",
    ]
    write_csv(sel_csv, cols, [[r[c] for c in cols] for r in selected])
    written.append(sel_csv)

    md = out_dir / "quotes_selected_redacted.md"
    with md.open("w", encoding="utf-8") as f:
        f.write("# Selected Redacted Quotes\n\n")
        for r in selected:
            f.write(f"## {r['quote_id']}\n")
            f.write(
                f"- agent: `{r['agent']}`\n"
                f"- ts: `{r['ts']}`\n"
                f"- session_id: `{r['session_id']}`\n"
                f"- role: `{r['role']}`\n"
                f"- tags: `{r['theme_tags']}`\n"
                f"- redaction_flags: `{r['redaction_flags'] or 'none'}`\n\n"
            )
            f.write(f"> {r['quote_redacted']}\n\n")
    written.append(md)

    return written


def infer_tags(text: str) -> str:
    t = text.lower()
    tags: list[str] = []
    if any(w in t for w in ["daytona", "docker", "network", "registry", "ssh"]):
        tags.append("infra")
    if any(w in t for w in ["oracle", "verifier", "artifact", "harbor", "benchmark"]):
        tags.append("benchmark_ops")
    if any(w in t for w in ["mcp", "context", "retrieval", "dedupe", "alias", "tradeoff"]):
        tags.append("agent_design")
    if any(w in t for w in ["retry", "timeout", "failed", "error", "429"]):
        tags.append("error_retry")
    return ",".join(tags) or "general"


def write_query_file(path: Path, queries: dict[str, str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as f:
        f.write("-- Blog asset extraction queries for unified conversation DB\n")
        f.write(f"-- Generated: {now_iso()}\n\n")
        for name, sql in queries.items():
            f.write(f"-- {name}\n{sql.strip()}\n\n")


def write_provenance(conn: sqlite3.Connection, out_dir: Path) -> tuple[Path, Path]:
    ensure_dir(out_dir)
    row = conn.execute(
        """
SELECT id, started_at, completed_at, project_key, project_root, agents, session_count, message_count, notes
FROM ingest_runs
ORDER BY id DESC
LIMIT 1;
"""
    ).fetchone()
    latest = {
        "id": row[0] if row else None,
        "started_at": row[1] if row else None,
        "completed_at": row[2] if row else None,
        "project_key": row[3] if row else None,
        "project_root": row[4] if row else None,
        "agents": row[5] if row else None,
        "session_count": row[6] if row else None,
        "message_count": row[7] if row else None,
        "notes": json.loads(row[8]) if row and row[8] else None,
    }
    latest_path = out_dir / "latest_ingest_run.json"
    latest_path.write_text(json.dumps(latest, indent=2), encoding="utf-8")

    manifest = {
        "generated_at": now_iso(),
        "db_path": "data/conversations/codescalebench_conversations.db",
        "latest_ingest_run_id": latest.get("id"),
    }
    manifest_path = out_dir / "export_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return latest_path, manifest_path


def write_readme(path: Path) -> None:
    path.write_text(
        """# Conversation Blog Assets

This directory contains reproducible extraction outputs from:
- `data/conversations/codescalebench_conversations.db`

Layout:
- `sql/figure_queries.sql`: canonical SQL for figure datasets
- `csv/*.csv`: query outputs used for charts and tables
- `figures/*.png`: optional generated charts (if matplotlib installed)
- `tables/*.md`: milestone/tool/error/process/data-quality tables
- `quotes/*`: candidate and selected redacted snippets with attribution metadata
- `provenance/*`: ingest run snapshot and export manifest

Regenerate:
- `python3 scripts/export_conversation_blog_assets.py`

Notes:
- Exports pin to the latest ingest run metadata at generation time.
- Quote outputs are redacted and deduplicated; do a final human editorial review before publication.
""",
        encoding="utf-8",
    )


def run(args: argparse.Namespace) -> int:
    db_path = Path(args.db_path).resolve()
    out_root = Path(args.output_root).resolve()

    if not db_path.exists():
        raise SystemExit(f"DB not found: {db_path}")

    ensure_dir(out_root)
    csv_dir = out_root / "csv"
    fig_dir = out_root / "figures"
    table_dir = out_root / "tables"
    quote_dir = out_root / "quotes"
    sql_dir = out_root / "sql"
    prov_dir = out_root / "provenance"

    conn = sqlite3.connect(str(db_path))
    try:
        queries = build_figure_queries()
        write_query_file(sql_dir / "figure_queries.sql", queries)

        csv_counts: dict[str, int] = {}
        for name, sql in queries.items():
            cols, rows = run_query(conn, sql)
            n = write_csv(csv_dir / f"{safe_slug(name)}.csv", cols, rows)
            csv_counts[name] = n

        tables = write_tables(conn, table_dir)
        quotes = build_quotes(conn, quote_dir, select_n=args.quote_count)
        plot_outputs = maybe_plot(csv_dir, fig_dir)
        latest_path, manifest_path = write_provenance(conn, prov_dir)
        write_readme(out_root / "README.md")

        summary = {
            "generated_at": now_iso(),
            "db_path": str(db_path),
            "output_root": str(out_root),
            "csv": csv_counts,
            "tables": [str(p) for p in tables],
            "quotes": [str(p) for p in quotes],
            "figures": plot_outputs,
            "provenance": [str(latest_path), str(manifest_path)],
        }
        (out_root / "export_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

        print(f"DB: {db_path}")
        print(f"Output: {out_root}")
        print(f"CSV datasets: {len(csv_counts)}")
        print(f"Tables: {len(tables)}")
        print(f"Quote files: {len(quotes)}")
        print(f"Figures: {len(plot_outputs)}")
        return 0
    finally:
        conn.close()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--db-path",
        default="data/conversations/codescalebench_conversations.db",
        help="Input unified conversation SQLite DB",
    )
    p.add_argument(
        "--output-root",
        default="data/conversations/blog_assets",
        help="Output root directory",
    )
    p.add_argument(
        "--quote-count",
        type=int,
        default=80,
        help="Maximum selected quotes",
    )
    return p


def main() -> int:
    return run(build_parser().parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
