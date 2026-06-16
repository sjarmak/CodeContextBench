# MCP-lift study explorer

Static, self-contained results explorer for the three-arm MCP-lift study
(9 discovery-heavy CodeScaleBench org tasks, n=3 per cell):

- **Arm A** Sonnet 4.6 + Sourcegraph MCP (no local source)
- **Arm B** Fable 5, baseline local checkout (no MCP)
- **Arm C** Sonnet 4.6, baseline local checkout (no MCP)

## Pages

- `index.html` / `comparison.html` — summary with the standings, the tooling-vs-model
  decomposition, and the per-task chart.
- `compare.html` — 3-way matrix; one row per task, click through to the side-by-side.
- `compare__<task>.html` — Sonnet | Sonnet+MCP | Fable in three columns, each with
  the instruction, full conversation, and every tool call.
- `*.html` (long filenames) — the representative full-trace page per arm per task.

Open `index.html` locally, or serve the folder (e.g. GitHub Pages) for the hosted
version linked from the blog post.

## Regenerate

```
python3 scripts/analysis/browse_3way.py runs/mcp_lift_study \
  --export explorer \
  --brand-page <path to comparison.html>
```

The exporter sanitizes local paths and secrets and refuses to write any page that
fails the leak guard. Representative trial = median reward of each arm's valid
trials (quarantined / instant-death trials excluded).
