# Official Results Browser

Use this workflow to publish valid official scores with easy-to-view parsed traces.

## What It Exports

`python3 scripts/export_official_results.py` scans `runs/official/` and exports only valid scored tasks (status `passed`/`failed` with numeric reward) into a static bundle:

- `docs/official_results/README.md` - run/config score summary
- `docs/official_results/runs/*.md` - per-run task tables
- `docs/official_results/tasks/*.md` - per-task metrics and parsed trace/tool summaries
- `docs/official_results/data/official_results.json` - machine-readable data
- `docs/official_results/audits/*.json` - per-task audit payloads with trace parsing and SHA256 checksums
- `docs/official_results/traces/*/trajectory.json` - bundled raw trajectory traces
- `docs/official_results/index.html` - local interactive browser

Suite-level views and top-level summaries are deduplicated to one canonical row
per `suite + config + task_name` (latest by task `started_at`). Full historical
rows are preserved in `data/official_results.json` as `all_tasks`.

For SDLC suites (`ccb_feature`, `ccb_refactor`, `ccb_debug`, `ccb_design`, `ccb_document`,
`ccb_fix`, `ccb_secure`, `ccb_test`, `ccb_understand`), legacy config labels
are normalized during export:
- `baseline` -> `baseline-local-direct`
- `mcp` -> `mcp-remote-direct`

For MCP-unique suites (`ccb_mcp_*`), legacy config labels are normalized to
artifact-mode configs:
- `baseline` -> `baseline-local-artifact`
- `mcp` -> `mcp-remote-artifact`

## Usage

If you promote runs with:

```bash
python3 scripts/promote_run.py --execute <staging_run_name>
```

`docs/official_results` is refreshed automatically after successful promotion
and MANIFEST regeneration. Use `--no-export-official-results` to skip that
step when needed.

```bash
python3 scripts/export_official_results.py \
  --runs-dir ./runs/official/ \
  --output-dir ./docs/official_results/
```

Filter to specific run(s):

```bash
python3 scripts/export_official_results.py \
  --run ccb_mcp_compliance_haiku_20260226_205845 \
  --run ccb_mcp_domain_haiku_20260226_205845
```

Serve locally after export:

```bash
python3 scripts/export_official_results.py --serve
```

## Notes

- The exporter prefers `task_metrics.json` when present and falls back to transcript parsing for tool-call extraction.
- Task pages link to bundled `audits/*.json` so GitHub viewers can audit without local `runs/official/`.
- If `runs/official/MANIFEST.json` exists, export is automatically scoped to run directories tracked in the manifest.
