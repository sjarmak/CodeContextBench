# Official Results Browser

Use this workflow to browse scored task results with parsed traces and task metrics.

## What It Exports

`python3 scripts/export_official_results.py` scans `runs/analysis/` by default and exports only valid scored tasks (status `passed`/`failed` with numeric reward) into a static bundle:

- `docs/official_results/README.md` - run/config score summary
- `docs/official_results/runs/*.md` - per-run task tables
- `docs/official_results/tasks/*.html` - per-task metrics and parsed trace/tool summaries
- `docs/official_results/data/official_results.json` - machine-readable data
- `docs/official_results/audits/*.json` - per-task audit payloads with trace parsing and SHA256 checksums
- `docs/official_results/traces/*/trajectory.json` - bundled raw trajectory traces
- `docs/official_results/index.html` - local interactive browser

Suite-level views and top-level summaries are deduplicated to one canonical row
per `suite + config + task_name` (latest by task `started_at`). Full historical
rows are preserved in `data/official_results.json` as `all_tasks`.

For SDLC suites (`csb_sdlc_feature`, `csb_sdlc_refactor`, `csb_sdlc_debug`, `csb_sdlc_design`, `csb_sdlc_document`,
`csb_sdlc_fix`, `csb_sdlc_secure`, `csb_sdlc_test`, `csb_sdlc_understand`), legacy config labels
are normalized during export:
- `baseline` -> `baseline-local-direct`
- `mcp` -> `mcp-remote-direct`

For Org suites (`csb_org_*`), legacy config labels are normalized to
artifact-mode configs:
- `baseline` -> `baseline-local-artifact`
- `mcp` -> `mcp-remote-artifact`

## Usage

Default usage (pull from `runs/analysis/`):

```bash
python3 scripts/export_official_results.py \
  --output-dir ./docs/official_results/
```

To export curated official runs instead:

```bash
python3 scripts/export_official_results.py \
  --runs-dir ./runs/official/ \
  --output-dir ./docs/official_results/
```

If you promote runs with:

```bash
python3 scripts/promote_run.py --execute <staging_run_name>
```

`docs/official_results` is refreshed automatically after successful promotion
and MANIFEST regeneration. Use `--no-export-official-results` to skip that
step when needed.

Filter to specific run(s):

```bash
python3 scripts/export_official_results.py \
  --run csb_org_compliance_haiku_20260226_205845 \
  --run csb_org_domain_haiku_20260226_205845
```

Serve locally after export:

```bash
python3 scripts/export_official_results.py --serve
```

## Notes

- The exporter prefers `task_metrics.json` when present and falls back to transcript parsing for tool-call extraction.
- Task pages link to bundled `audits/*.json` so GitHub viewers can audit without local runs data.
- If `MANIFEST.json` exists under the selected `--runs-dir`, export is automatically scoped to run directories tracked in the manifest.
