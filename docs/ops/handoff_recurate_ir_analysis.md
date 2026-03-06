# Re-Curation IR Analysis — COMPLETED 2026-03-06

> **Status**: All tasks complete. This doc is kept for historical reference.
> **Skill**: Use `/curate-ground-truth` for future curation runs.

## Final Results

- **381/381 tasks** re-curated and promoted to canonical (160 SDLC + 221 Org)
- **Commits**: `b08164eae` (160 SDLC + 207 Org promoted), `58df5ae4d` (14 onboard-search added)

### Coverage Breakdown

| Source | Count | Notes |
|--------|-------|-------|
| Daytona curator (Opus 4.6, phase1, hybrid) | 356 | Automated via `daytona_curator_runner.py` |
| Manual from canonical | 11 | 4 linux kernel (repo too large) + 7 large-repo timeouts |
| Schema conversion (function_id → files) | 14 | `ccx-onboard-search-*` semantic retrieval tasks |

### IR Metrics (Post-Promotion)

| Metric | Value |
|--------|-------|
| Computable tasks | 1,921 |
| File recall (mean) | 0.394 |
| MRR | 0.352 |
| MAP | 0.239 |
| mcp-remote-artifact recall | 0.596 |
| baseline-local-direct recall | 0.330 |

### V2 Report Summary

375 paired tasks: BL=0.459, MCP=0.480, delta=+0.021

## Key Architecture Notes

- `write_curator_outputs()` in `context_retrieval_agent.py` handles both SDLC and Org file writing
- When `overwrite=False` (default), writes `_agent` variants; when `overwrite=True`, writes canonical
- `ground_truth_meta.json` contains curator metadata: model, backend, prompt version, cost, timestamp
- The curator uses phase1 prompt (`PHASE1_CLI_PROMPTS` + `PHASE1_SUFFIX`) which is recall-focused (F1=0.749 on calibration set)
- Hybrid backend = local tools (Bash, Read, Glob, Grep) + Sourcegraph MCP (sg_keyword_search, sg_nls_search)
- `extract_v2_report_data.py` scans both `runs/official/` and `runs/official/_raw/` via `scan_roots` loop
- `ccx-onboard-search-*` tasks: `ground_truth.json` keeps `function_id` schema for verifier; `oracle_answer.json` uses standard `files` schema for IR
