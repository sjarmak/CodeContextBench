#!/usr/bin/env python3
"""Build a unified conversation database for CodeScaleBench across agents.

Sources (best-effort):
- Claude Code JSONL: ~/.claude/projects/<project>/*.jsonl
- Cursor transcripts: ~/.cursor/projects/<project>/agent-transcripts/*.jsonl
- Codex sessions: ~/.codex/sessions/**/*.jsonl
- Gemini chats: ~/.gemini/tmp/**/chats/session-*.json
- Copilot session metadata: ~/.copilot/session-state/*
- Existing curated DB: ~/codescalebench-conversation-db/codescalebench_conversations.sqlite
- Transcript-memory DB: ~/.claude/tom/transcript-memory.db

Default output:
  data/conversations/codescalebench_conversations.db
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_project_key(path_str: str) -> str:
    p = path_str.replace("/", "-")
    if not p.startswith("-"):
        p = "-" + p
    return p.replace("_", "-")


def project_aliases(project_root: Path) -> set[str]:
    base = project_root.name
    aliases = {base}
    # Preserve historical rename context: CodeContextBench -> CodeScaleBench
    if base == "CodeScaleBench":
        aliases.add("CodeContextBench")
    if base == "CodeContextBench":
        aliases.add("CodeScaleBench")
    return aliases


@dataclass
class SessionRec:
    session_id: str
    agent: str
    source_path: str
    project_key: str
    started_at: str | None
    last_at: str | None
    msg_count: int
    user_msgs: int
    assistant_msgs: int
    tool_calls: int
    error_count: int
    title: str | None


@dataclass
class MessageRec:
    session_id: str
    agent: str
    ts: str | None
    role: str
    msg_type: str
    text: str | None


def likely_relevant_project(name: str | None, aliases: set[str]) -> bool:
    if not name:
        return False
    name_l = name.lower()
    alias_l = {a.lower() for a in aliases}
    if any(a in name_l for a in alias_l):
        return True
    # Include historical/dashboard sibling projects relevant to the build story.
    extras = ("dashboard", "sg-benchmark", "benchmark-forks", "forks-benchmark")
    return any(tag in name_l for tag in extras)


AGENT_PREFERENCE = {
    "claude": 100,
    "codex": 90,
    "cursor": 80,
    "gemini": 70,
    "copilot": 60,
    "external_claude_archive": 50,
    "external_codex": 40,
    "external_cursor": 30,
    "external_transcript_memory": 20,
}


def logical_session_id(agent: str, session_id: str) -> str:
    """Normalize source-specific IDs so duplicates can be collapsed safely."""
    if agent == "external_transcript_memory" and session_id.startswith("tm:"):
        return session_id[3:]
    if session_id.startswith("ext:"):
        parts = session_id.split(":", 2)
        if len(parts) == 3:
            return parts[2]
    return session_id


def row_signature(sess: SessionRec, msgs: list[MessageRec]) -> str:
    """Coarse content signature for duplicate collapse across mirrored sources."""
    first_text = ""
    last_text = ""
    if msgs:
        for m in msgs:
            if m.text:
                first_text = (m.text or "")[:140]
                break
        for m in reversed(msgs):
            if m.text:
                last_text = (m.text or "")[:140]
                break
    return "|".join(
        [
            logical_session_id(sess.agent, sess.session_id),
            sess.started_at or "",
            sess.last_at or "",
            str(sess.msg_count),
            str(sess.tool_calls),
            first_text,
            last_text,
        ]
    )


def dedupe_rows(rows: list[tuple[SessionRec, list[MessageRec]]]) -> tuple[list[tuple[SessionRec, list[MessageRec]]], dict[str, int]]:
    """Prefer primary local sources, drop mirrored duplicates."""
    deduped: list[tuple[SessionRec, list[MessageRec]]] = []
    dropped = 0
    # First pass: if a logical session appears in both primary and external sources,
    # keep the highest-preference source.
    by_logical: dict[str, tuple[SessionRec, list[MessageRec]]] = {}
    for sess, msgs in rows:
        lid = logical_session_id(sess.agent, sess.session_id)
        existing = by_logical.get(lid)
        if not existing:
            by_logical[lid] = (sess, msgs)
            continue

        prev_sess, prev_msgs = existing
        prev_pref = AGENT_PREFERENCE.get(prev_sess.agent, 0)
        curr_pref = AGENT_PREFERENCE.get(sess.agent, 0)
        if curr_pref > prev_pref:
            by_logical[lid] = (sess, msgs)
            dropped += 1
        elif curr_pref == prev_pref and len(msgs) > len(prev_msgs):
            by_logical[lid] = (sess, msgs)
            dropped += 1
        else:
            dropped += 1

    # Second pass: collapse any remaining coarse-signature duplicates.
    seen_sig: set[str] = set()
    for sess, msgs in by_logical.values():
        sig = row_signature(sess, msgs)
        if sig in seen_sig:
            dropped += 1
            continue
        seen_sig.add(sig)
        deduped.append((sess, msgs))

    stats = {"input_rows": len(rows), "kept_rows": len(deduped), "dropped_rows": dropped}
    return deduped, stats


def extract_text(value: object) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts: list[str] = []
        for item in value:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                txt = (
                    item.get("text")
                    or item.get("input_text")
                    or item.get("output_text")
                    or item.get("content")
                )
                if isinstance(txt, str):
                    parts.append(txt)
        return "\n".join(p for p in parts if p)
    if isinstance(value, dict):
        txt = value.get("text") or value.get("content")
        return txt if isinstance(txt, str) else ""
    return ""


def parse_claude_file(path: Path, project_key: str) -> tuple[SessionRec | None, list[MessageRec]]:
    messages: list[MessageRec] = []
    timestamps: list[str] = []
    sid: str | None = None
    tool_calls = 0
    error_count = 0
    user_msgs = 0
    assistant_msgs = 0
    first_user_text: str | None = None

    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            msg_type = obj.get("type")
            if msg_type not in {"user", "assistant", "progress"}:
                continue

            ts = obj.get("timestamp")
            if isinstance(ts, str) and ts:
                timestamps.append(ts)

            sid = sid or obj.get("sessionId") or path.stem
            msg = obj.get("message", {}) if isinstance(obj.get("message"), dict) else {}
            content = msg.get("content")
            text = extract_text(content)

            if msg_type == "user":
                user_msgs += 1
                if text and not first_user_text:
                    first_user_text = text[:240]
                if isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "tool_result":
                            if block.get("is_error"):
                                error_count += 1
            elif msg_type == "assistant":
                assistant_msgs += 1
                if isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "tool_use":
                            tool_calls += 1

            role = "assistant" if msg_type == "assistant" else "user"
            messages.append(
                MessageRec(
                    session_id=sid,
                    agent="claude",
                    ts=ts if isinstance(ts, str) else None,
                    role=role,
                    msg_type=msg_type,
                    text=text[:10000] if text else None,
                )
            )

    if not messages:
        return None, []

    sess = SessionRec(
        session_id=sid or path.stem,
        agent="claude",
        source_path=str(path),
        project_key=project_key,
        started_at=min(timestamps) if timestamps else None,
        last_at=max(timestamps) if timestamps else None,
        msg_count=len(messages),
        user_msgs=user_msgs,
        assistant_msgs=assistant_msgs,
        tool_calls=tool_calls,
        error_count=error_count,
        title=first_user_text,
    )
    return sess, messages


def parse_cursor_file(path: Path, project_key: str) -> tuple[SessionRec | None, list[MessageRec]]:
    messages: list[MessageRec] = []
    user_msgs = 0
    assistant_msgs = 0
    first_user_text: str | None = None
    sid = path.stem

    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            role = obj.get("role")
            msg = obj.get("message", {}) if isinstance(obj.get("message"), dict) else {}
            text = extract_text(msg.get("content"))
            if role == "user":
                user_msgs += 1
                if text and not first_user_text:
                    first_user_text = text[:240]
            elif role == "assistant":
                assistant_msgs += 1
            else:
                continue
            messages.append(
                MessageRec(
                    session_id=sid,
                    agent="cursor",
                    ts=None,
                    role=role,
                    msg_type=role,
                    text=text[:10000] if text else None,
                )
            )

    if not messages:
        return None, []

    sess = SessionRec(
        session_id=sid,
        agent="cursor",
        source_path=str(path),
        project_key=project_key,
        started_at=None,
        last_at=None,
        msg_count=len(messages),
        user_msgs=user_msgs,
        assistant_msgs=assistant_msgs,
        tool_calls=0,
        error_count=0,
        title=first_user_text,
    )
    return sess, messages


def parse_codex_file(path: Path, project_aliases_lower: set[str], project_key: str) -> tuple[SessionRec | None, list[MessageRec]]:
    messages: list[MessageRec] = []
    user_msgs = 0
    assistant_msgs = 0
    tool_calls = 0
    sid = path.stem
    first_user_text: str | None = None
    timestamps: list[str] = []
    relevant = False

    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            ts = obj.get("timestamp")
            if isinstance(ts, str) and ts:
                timestamps.append(ts)

            entry_type = obj.get("type")
            payload = obj.get("payload", {}) if isinstance(obj.get("payload"), dict) else {}

            if entry_type == "session_meta":
                sid = payload.get("id") or sid
                cwd = payload.get("cwd", "")
                if isinstance(cwd, str):
                    cwd_l = cwd.lower()
                    if any(alias in cwd_l for alias in project_aliases_lower):
                        relevant = True

            if entry_type == "response_item" and payload.get("type") == "message":
                role = payload.get("role")
                if role not in {"user", "assistant"}:
                    continue
                text = extract_text(payload.get("content"))
                if role == "user":
                    user_msgs += 1
                    if text and not first_user_text:
                        first_user_text = text[:240]
                else:
                    assistant_msgs += 1
                messages.append(
                    MessageRec(
                        session_id=sid,
                        agent="codex",
                        ts=ts if isinstance(ts, str) else None,
                        role=role,
                        msg_type="message",
                        text=text[:10000] if text else None,
                    )
                )

            if entry_type == "response_item" and payload.get("type") == "function_call":
                tool_calls += 1

    if not relevant and not any(alias in str(path).lower() for alias in project_aliases_lower):
        return None, []
    if not messages:
        return None, []

    sess = SessionRec(
        session_id=sid,
        agent="codex",
        source_path=str(path),
        project_key=project_key,
        started_at=min(timestamps) if timestamps else None,
        last_at=max(timestamps) if timestamps else None,
        msg_count=len(messages),
        user_msgs=user_msgs,
        assistant_msgs=assistant_msgs,
        tool_calls=tool_calls,
        error_count=0,
        title=first_user_text,
    )
    return sess, messages


def parse_gemini_file(path: Path, project_aliases_lower: set[str], project_key: str) -> tuple[SessionRec | None, list[MessageRec]]:
    try:
        obj = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except json.JSONDecodeError:
        return None, []

    sid = obj.get("sessionId") or path.stem
    messages: list[MessageRec] = []
    user_msgs = 0
    assistant_msgs = 0
    tool_calls = 0
    error_count = 0
    first_user_text: str | None = None

    source_l = str(path).lower()
    if not any(alias in source_l for alias in project_aliases_lower):
        proj_hash = str(obj.get("projectHash", "")).lower()
        if not any(alias in proj_hash for alias in project_aliases_lower):
            return None, []

    for m in obj.get("messages", []):
        if not isinstance(m, dict):
            continue
        mtype = m.get("type")
        ts = m.get("timestamp")
        if mtype == "user":
            role = "user"
            user_msgs += 1
        elif mtype == "gemini":
            role = "assistant"
            assistant_msgs += 1
            tcalls = m.get("toolCalls")
            if isinstance(tcalls, list):
                tool_calls += len(tcalls)
                for tc in tcalls:
                    if isinstance(tc, dict) and tc.get("status") == "error":
                        error_count += 1
        else:
            continue

        text = extract_text(m.get("content"))
        if role == "user" and text and not first_user_text:
            first_user_text = text[:240]

        messages.append(
            MessageRec(
                session_id=sid,
                agent="gemini",
                ts=ts if isinstance(ts, str) else None,
                role=role,
                msg_type=mtype,
                text=text[:10000] if text else None,
            )
        )

    if not messages:
        return None, []

    sess = SessionRec(
        session_id=sid,
        agent="gemini",
        source_path=str(path),
        project_key=project_key,
        started_at=obj.get("startTime"),
        last_at=obj.get("lastUpdated"),
        msg_count=len(messages),
        user_msgs=user_msgs,
        assistant_msgs=assistant_msgs,
        tool_calls=tool_calls,
        error_count=error_count,
        title=first_user_text,
    )
    return sess, messages


def parse_copilot_session(session_dir: Path, project_aliases_lower: set[str], project_key: str) -> tuple[SessionRec | None, list[MessageRec]]:
    workspace = session_dir / "workspace.yaml"
    checkpoints = session_dir / "checkpoints" / "index.md"
    if not workspace.exists() and not checkpoints.exists():
        return None, []

    workspace_text = workspace.read_text(encoding="utf-8", errors="replace") if workspace.exists() else ""
    if project_aliases_lower and not any(alias in workspace_text.lower() for alias in project_aliases_lower):
        return None, []

    sid = session_dir.name
    title = None
    if checkpoints.exists():
        for line in checkpoints.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and not line.startswith("|"):
                title = line[:240]
                break

    stat_src = workspace if workspace.exists() else checkpoints
    started = datetime.fromtimestamp(stat_src.stat().st_ctime, tz=timezone.utc).isoformat()
    updated = datetime.fromtimestamp(stat_src.stat().st_mtime, tz=timezone.utc).isoformat()

    # Copilot CLI session-state doesn't reliably persist full message transcripts here,
    # so we store metadata as a pseudo-message for discoverability.
    pseudo_text = workspace_text[:10000] if workspace_text else None
    msgs = [
        MessageRec(
            session_id=sid,
            agent="copilot",
            ts=updated,
            role="metadata",
            msg_type="session_state",
            text=pseudo_text,
        )
    ]

    sess = SessionRec(
        session_id=sid,
        agent="copilot",
        source_path=str(session_dir),
        project_key=project_key,
        started_at=started,
        last_at=updated,
        msg_count=1,
        user_msgs=0,
        assistant_msgs=0,
        tool_calls=0,
        error_count=0,
        title=title,
    )
    return sess, msgs


def create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        PRAGMA journal_mode=WAL;
        PRAGMA foreign_keys=ON;

        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT NOT NULL,
            agent TEXT NOT NULL,
            source_path TEXT NOT NULL,
            project_key TEXT NOT NULL,
            started_at TEXT,
            last_at TEXT,
            msg_count INTEGER NOT NULL,
            user_msgs INTEGER NOT NULL,
            assistant_msgs INTEGER NOT NULL,
            tool_calls INTEGER NOT NULL,
            error_count INTEGER NOT NULL,
            title TEXT,
            ingested_at TEXT NOT NULL,
            PRIMARY KEY (session_id, agent)
        );

        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            agent TEXT NOT NULL,
            ts TEXT,
            role TEXT NOT NULL,
            msg_type TEXT NOT NULL,
            text TEXT,
            ingested_at TEXT NOT NULL,
            FOREIGN KEY (session_id, agent) REFERENCES sessions(session_id, agent)
        );

        CREATE INDEX IF NOT EXISTS idx_messages_agent_ts ON messages(agent, ts);
        CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id, agent);

        CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(
            session_id, agent, role, text,
            content='messages', content_rowid='id'
        );

        CREATE TABLE IF NOT EXISTS ingest_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            started_at TEXT NOT NULL,
            completed_at TEXT,
            project_key TEXT NOT NULL,
            project_root TEXT NOT NULL,
            agents TEXT NOT NULL,
            session_count INTEGER NOT NULL DEFAULT 0,
            message_count INTEGER NOT NULL DEFAULT 0,
            notes TEXT
        );
        """
    )


def rebuild_fts(conn: sqlite3.Connection) -> None:
    conn.execute("INSERT INTO messages_fts(messages_fts) VALUES('rebuild')")


def gather_claude(project_root: Path, aliases: set[str]) -> Iterable[tuple[SessionRec, list[MessageRec]]]:
    base = Path.home() / ".claude" / "projects"
    if not base.exists():
        return []

    targets = set()
    for a in aliases:
        targets.add(normalize_project_key(str(project_root.parent / a)))

    out: list[tuple[SessionRec, list[MessageRec]]] = []
    seen_realpaths: set[str] = set()
    for d in base.iterdir():
        if not d.is_dir():
            continue
        name_l = d.name.lower()
        if d.name not in targets and not any(a.lower() in name_l for a in aliases):
            continue
        for f in sorted(d.glob("*.jsonl")):
            rp = str(f.resolve())
            if rp in seen_realpaths:
                continue
            seen_realpaths.add(rp)
            sess, msgs = parse_claude_file(f, d.name)
            if sess:
                out.append((sess, msgs))
    return out


def gather_cursor(project_root: Path, aliases: set[str]) -> Iterable[tuple[SessionRec, list[MessageRec]]]:
    base = Path.home() / ".cursor" / "projects"
    if not base.exists():
        return []

    out: list[tuple[SessionRec, list[MessageRec]]] = []
    seen_realpaths: set[str] = set()
    alias_l = {a.lower() for a in aliases}
    for d in base.iterdir():
        if not d.is_dir():
            continue
        if not any(a in d.name.lower() for a in alias_l):
            continue
        tdir = d / "agent-transcripts"
        if not tdir.exists():
            continue
        for f in sorted(tdir.glob("*.jsonl")):
            rp = str(f.resolve())
            if rp in seen_realpaths:
                continue
            seen_realpaths.add(rp)
            sess, msgs = parse_cursor_file(f, d.name)
            if sess:
                out.append((sess, msgs))
    return out


def gather_codex(project_root: Path, aliases: set[str]) -> Iterable[tuple[SessionRec, list[MessageRec]]]:
    base = Path.home() / ".codex" / "sessions"
    if not base.exists():
        return []

    key = normalize_project_key(str(project_root))
    alias_l = {a.lower() for a in aliases}
    out: list[tuple[SessionRec, list[MessageRec]]] = []
    for f in sorted(base.rglob("*.jsonl")):
        sess, msgs = parse_codex_file(f, alias_l, key)
        if sess:
            out.append((sess, msgs))
    return out


def gather_gemini(project_root: Path, aliases: set[str]) -> Iterable[tuple[SessionRec, list[MessageRec]]]:
    base = Path.home() / ".gemini" / "tmp"
    if not base.exists():
        return []

    key = normalize_project_key(str(project_root))
    alias_l = {a.lower() for a in aliases}
    out: list[tuple[SessionRec, list[MessageRec]]] = []
    for f in sorted(base.rglob("session-*.json")):
        sess, msgs = parse_gemini_file(f, alias_l, key)
        if sess:
            out.append((sess, msgs))
    return out


def gather_copilot(project_root: Path, aliases: set[str]) -> Iterable[tuple[SessionRec, list[MessageRec]]]:
    base = Path.home() / ".copilot" / "session-state"
    if not base.exists():
        return []

    key = normalize_project_key(str(project_root))
    alias_l = {a.lower() for a in aliases}
    out: list[tuple[SessionRec, list[MessageRec]]] = []
    for d in sorted(base.iterdir()):
        if not d.is_dir():
            continue
        sess, msgs = parse_copilot_session(d, alias_l, key)
        if sess:
            out.append((sess, msgs))
    return out


def gather_external_curated_db(seed_db_path: Path, project_root: Path, aliases: set[str]) -> Iterable[tuple[SessionRec, list[MessageRec]]]:
    if not seed_db_path.exists():
        return []

    project_key = normalize_project_key(str(project_root))
    out: list[tuple[SessionRec, list[MessageRec]]] = []
    src = sqlite3.connect(f"file:{seed_db_path}?mode=ro", uri=True)
    src.row_factory = sqlite3.Row
    try:
        rows = src.execute(
            """
            SELECT id, source, project, conversation_uid, title, started_at, ended_at,
                   path, message_count, tool_call_count
            FROM conversations
            """
        ).fetchall()
        for r in rows:
            if not likely_relevant_project(r["project"], aliases):
                continue

            conv_id = r["id"]
            ext_source = f"external_{r['source']}"
            sid = f"ext:{r['source']}:{r['conversation_uid'] or conv_id}"

            msg_rows = src.execute(
                """
                SELECT role, msg_type, timestamp, text
                FROM messages
                WHERE conversation_id = ?
                ORDER BY ordinal
                """,
                (conv_id,),
            ).fetchall()

            user_msgs = 0
            assistant_msgs = 0
            messages: list[MessageRec] = []
            for m in msg_rows:
                role = (m["role"] or "").lower()
                if role == "user":
                    user_msgs += 1
                elif role in {"assistant", "gemini", "copilot", "tool"}:
                    assistant_msgs += 1

                messages.append(
                    MessageRec(
                        session_id=sid,
                        agent=ext_source,
                        ts=m["timestamp"],
                        role=role or "unknown",
                        msg_type=m["msg_type"] or "message",
                        text=m["text"][:10000] if isinstance(m["text"], str) else None,
                    )
                )

            sess = SessionRec(
                session_id=sid,
                agent=ext_source,
                source_path=r["path"] or str(seed_db_path),
                project_key=project_key,
                started_at=r["started_at"],
                last_at=r["ended_at"],
                msg_count=int(r["message_count"] or len(messages)),
                user_msgs=user_msgs,
                assistant_msgs=assistant_msgs,
                tool_calls=int(r["tool_call_count"] or 0),
                error_count=0,
                title=r["title"],
            )
            out.append((sess, messages))
    finally:
        src.close()
    return out


def gather_transcript_memory_db(tm_db_path: Path, project_root: Path, aliases: set[str]) -> Iterable[tuple[SessionRec, list[MessageRec]]]:
    if not tm_db_path.exists():
        return []

    project_key = normalize_project_key(str(project_root))
    alias_l = {a.lower() for a in aliases}
    out: list[tuple[SessionRec, list[MessageRec]]] = []
    src = sqlite3.connect(f"file:{tm_db_path}?mode=ro", uri=True)
    src.row_factory = sqlite3.Row
    try:
        sess_rows = src.execute(
            """
            SELECT s.session_id, s.project_name, s.project_path, s.created_at, s.modified_at,
                   s.first_prompt
            FROM sessions s
            """
        ).fetchall()

        for s in sess_rows:
            proj = (s["project_name"] or "").lower()
            if not any(a in proj for a in alias_l) and "dashboard" not in proj:
                continue

            session_id = s["session_id"]
            sid = f"tm:{session_id}"
            msg_rows = src.execute(
                """
                SELECT timestamp, type, text_content
                FROM messages
                WHERE session_id = ?
                ORDER BY timestamp
                """,
                (session_id,),
            ).fetchall()

            tc_row = src.execute(
                "SELECT COUNT(*) AS c FROM tool_calls WHERE session_id = ?",
                (session_id,),
            ).fetchone()
            err_row = src.execute(
                "SELECT COUNT(*) AS c FROM tool_calls WHERE session_id = ? AND is_error = 1",
                (session_id,),
            ).fetchone()

            messages: list[MessageRec] = []
            user_msgs = 0
            assistant_msgs = 0
            for m in msg_rows:
                mtype = (m["type"] or "").lower()
                if mtype == "user":
                    user_msgs += 1
                    role = "user"
                elif mtype in {"assistant", "progress"}:
                    assistant_msgs += 1
                    role = "assistant"
                else:
                    role = "unknown"

                messages.append(
                    MessageRec(
                        session_id=sid,
                        agent="external_transcript_memory",
                        ts=m["timestamp"],
                        role=role,
                        msg_type=mtype or "message",
                        text=m["text_content"][:10000] if isinstance(m["text_content"], str) else None,
                    )
                )

            sess = SessionRec(
                session_id=sid,
                agent="external_transcript_memory",
                source_path=s["project_path"] or str(tm_db_path),
                project_key=project_key,
                started_at=s["created_at"],
                last_at=s["modified_at"],
                msg_count=len(messages),
                user_msgs=user_msgs,
                assistant_msgs=assistant_msgs,
                tool_calls=int(tc_row["c"] if tc_row else 0),
                error_count=int(err_row["c"] if err_row else 0),
                title=s["first_prompt"][:240] if isinstance(s["first_prompt"], str) else None,
            )
            out.append((sess, messages))
    finally:
        src.close()
    return out


def insert_all(conn: sqlite3.Connection, rows: list[tuple[SessionRec, list[MessageRec]]], ingested_at: str) -> tuple[int, int, Counter[str]]:
    sessions_n = 0
    messages_n = 0
    by_agent: Counter[str] = Counter()

    for sess, msgs in rows:
        conn.execute(
            """
            INSERT OR REPLACE INTO sessions (
                session_id, agent, source_path, project_key,
                started_at, last_at, msg_count, user_msgs, assistant_msgs,
                tool_calls, error_count, title, ingested_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                sess.session_id,
                sess.agent,
                sess.source_path,
                sess.project_key,
                sess.started_at,
                sess.last_at,
                sess.msg_count,
                sess.user_msgs,
                sess.assistant_msgs,
                sess.tool_calls,
                sess.error_count,
                sess.title,
                ingested_at,
            ),
        )
        sessions_n += 1
        by_agent[sess.agent] += 1

        conn.execute(
            "DELETE FROM messages WHERE session_id = ? AND agent = ?",
            (sess.session_id, sess.agent),
        )

        if msgs:
            conn.executemany(
                """
                INSERT INTO messages (
                    session_id, agent, ts, role, msg_type, text, ingested_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        m.session_id,
                        m.agent,
                        m.ts,
                        m.role,
                        m.msg_type,
                        m.text,
                        ingested_at,
                    )
                    for m in msgs
                ],
            )
            messages_n += len(msgs)

    return sessions_n, messages_n, by_agent


def run(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root).expanduser().resolve()
    db_path = Path(args.db_path).expanduser().resolve()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    aliases = project_aliases(project_root)
    selected = {a.strip().lower() for a in args.agents.split(",") if a.strip()}

    conn = sqlite3.connect(str(db_path))
    try:
        create_schema(conn)

        started = now_iso()
        run_id = conn.execute(
            "INSERT INTO ingest_runs (started_at, project_key, project_root, agents) VALUES (?, ?, ?, ?)",
            (started, normalize_project_key(str(project_root)), str(project_root), ",".join(sorted(selected))),
        ).lastrowid

        if args.full_rebuild:
            conn.execute("DELETE FROM messages")
            conn.execute("DELETE FROM sessions")

        all_rows: list[tuple[SessionRec, list[MessageRec]]] = []
        if "claude" in selected:
            all_rows.extend(gather_claude(project_root, aliases))
        if "cursor" in selected:
            all_rows.extend(gather_cursor(project_root, aliases))
        if "codex" in selected:
            all_rows.extend(gather_codex(project_root, aliases))
        if "gemini" in selected:
            all_rows.extend(gather_gemini(project_root, aliases))
        if "copilot" in selected:
            all_rows.extend(gather_copilot(project_root, aliases))
        ext_db = Path(args.external_db).expanduser()
        all_rows.extend(gather_external_curated_db(ext_db, project_root, aliases))
        tm_db = Path(args.transcript_memory_db).expanduser()
        all_rows.extend(gather_transcript_memory_db(tm_db, project_root, aliases))
        all_rows, dedupe_stats = dedupe_rows(all_rows)

        ingested_at = now_iso()
        sessions_n, messages_n, by_agent = insert_all(conn, all_rows, ingested_at)
        rebuild_fts(conn)

        completed = now_iso()
        conn.execute(
            "UPDATE ingest_runs SET completed_at = ?, session_count = ?, message_count = ?, notes = ? WHERE id = ?",
            (
                completed,
                sessions_n,
                messages_n,
                json.dumps({"by_agent": by_agent, "dedupe": dedupe_stats}),
                run_id,
            ),
        )
        conn.commit()

        print(f"DB: {db_path}")
        print(f"project_root: {project_root}")
        print(f"aliases: {', '.join(sorted(aliases))}")
        print(f"sessions: {sessions_n}")
        print(f"messages: {messages_n}")
        print(
            "dedupe: "
            f"input={dedupe_stats['input_rows']} "
            f"kept={dedupe_stats['kept_rows']} "
            f"dropped={dedupe_stats['dropped_rows']}"
        )
        for agent, n in sorted(by_agent.items()):
            print(f"  {agent}: {n} sessions")
        return 0
    finally:
        conn.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project-root",
        default=str(Path.cwd()),
        help="Project root used to scope relevant sessions (default: cwd)",
    )
    parser.add_argument(
        "--db-path",
        default="data/conversations/codescalebench_conversations.db",
        help="Output SQLite database path",
    )
    parser.add_argument(
        "--agents",
        default="claude,cursor,codex,gemini,copilot",
        help="Comma-separated agents to ingest",
    )
    parser.add_argument(
        "--full-rebuild",
        action="store_true",
        help="Delete existing session/message rows before ingest",
    )
    parser.add_argument(
        "--external-db",
        default=str(
            Path.home()
            / "codescalebench-conversation-db"
            / "codescalebench_conversations.sqlite"
        ),
        help="Optional path to a prebuilt curated conversation DB to merge in",
    )
    parser.add_argument(
        "--transcript-memory-db",
        default=str(Path.home() / ".claude" / "tom" / "transcript-memory.db"),
        help="Optional path to transcript-memory SQLite DB to merge in",
    )
    return parser


def main() -> int:
    return run(build_parser().parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
