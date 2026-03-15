# CodeScaleBench Conversation Database

Primary DB path:
- `data/conversations/codescalebench_conversations.db`

Builder script:
- `python3 scripts/build_conversation_db.py --project-root /home/stephanie_jarmak/CodeScaleBench --full-rebuild`

What is included:
- Claude local transcripts from `~/.claude/projects/*`
- Cursor agent transcripts from `~/.cursor/projects/*/agent-transcripts/*.jsonl`
- Codex sessions from `~/.codex/sessions/**/*.jsonl`
- Gemini chats from `~/.gemini/tmp/**/chats/session-*.json`
- Copilot session-state metadata from `~/.copilot/session-state/*`
- Curated historical DB from `~/codescalebench-conversation-db/codescalebench_conversations.sqlite`
- Transcript-memory DB from `~/.claude/tom/transcript-memory.db`

Schema (core):
- `sessions(session_id, agent, source_path, project_key, started_at, last_at, msg_count, user_msgs, assistant_msgs, tool_calls, error_count, title, ingested_at)`
- `messages(id, session_id, agent, ts, role, msg_type, text, ingested_at)`
- `messages_fts` (FTS5 index over `messages.text`)
- `ingest_runs` (run metadata)

Use this DB for build-story metrics, figures, and narrative extraction across agents.

## Blog Asset Extraction

Generate reproducible technical blog assets from the unified DB:

```bash
python3 scripts/export_conversation_blog_assets.py \
  --db-path data/conversations/codescalebench_conversations.db \
  --output-root data/conversations/blog_assets \
  --quote-count 80
```

Output layout:
- `data/conversations/blog_assets/sql/figure_queries.sql` (canonical SQL pulls)
- `data/conversations/blog_assets/csv/*.csv` (figure datasets)
- `data/conversations/blog_assets/figures/*.png` (optional plots; generated when matplotlib is available)
- `data/conversations/blog_assets/tables/*.md` (milestones/tool/error/process/data-quality tables)
- `data/conversations/blog_assets/quotes/*` (candidate + selected redacted quote snippets with attribution metadata)
- `data/conversations/blog_assets/provenance/*` (ingest run snapshot + export manifest)
