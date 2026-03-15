# Conversation Blog Assets

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
