Full post-run pipeline: triage → quarantine → promote → organize. Run this after a benchmark batch completes.

## Pipeline Steps

### 1. Triage
Classify every task in the completed run:
```bash
cd ~/CodeScaleBench
PYTHONPATH=scripts/maintenance:scripts/evaluation:scripts/running:scripts:$PYTHONPATH \
python3 scripts/evaluation/triage_run.py runs/staging/<run_name>
```
Parse the JSON output. Categories:
- **pass**: Task succeeded — promote
- **D (agent_quality)**: Agent ran correctly but scored 0 — promote (valid signal)
- **A (infra)**: Sandbox/Docker/timeout failure — quarantine, do NOT promote
- **B (setup)**: Environment misconfiguration — investigate: if stale paths, fix result.json; if real, quarantine
- **C (verifier)**: Verifier script failure — quarantine, do NOT promote; investigate verifier fix

### 2. Quarantine A/C trials
**BEFORE promoting**, move infra and verifier failures out:
- For each A/C trial, check if the same task has a valid pass/D trial in another run
- If yes: quarantine the bad trial (the valid one will be promoted)
- If no valid trial exists: flag the task for rerun or verifier fix
- Move bad trial dirs to `runs/official/_quarantine/{reason}/`

### 3. Consolidate (if fragmented runs exist)
```bash
python3 scripts/evaluation/consolidate_staging.py --dry-run
python3 scripts/evaluation/consolidate_staging.py --execute
```
If the script fails, manually clean empty trial dirs and remove empty runs.

### 4. Promote to official
Move run directories from `runs/staging/` to `runs/official/_raw/`:
```bash
# Option A: atomic promotion (may be slow on large dirs)
python3 scripts/running/promote_atomic.py <run_name>

# Option B: manual move + manifest regen (faster)
mv runs/staging/<run_name> runs/official/_raw/<run_name>
PYTHONPATH=scripts/maintenance:scripts/evaluation:scripts/running:scripts:$PYTHONPATH \
python3 scripts/maintenance/generate_manifest.py
```

### 5. Organize views
```bash
PYTHONPATH=scripts/maintenance:scripts/evaluation:scripts/running:scripts:$PYTHONPATH \
python3 scripts/analysis/organize_official_by_model.py \
  --official-dir runs/official --execute
```
Creates symlink views under csb_sdlc/{model}/ and csb_org/{model}/.

### 6. Update dashboard
```bash
python3 scripts/analysis/dashboard.py --generate-only
```

## Arguments

$ARGUMENTS — required: staging run name(s) to process

## Steps

1. Validate the run directory exists and is complete (no running harbor processes)
2. Run triage on each staging run and summarize categories
3. **Quarantine A and C trials** — move to `_quarantine/` BEFORE promotion
   - For each A/C task, check if a valid pass/D trial exists in another run
   - Report any tasks with NO valid trial (need rerun or verifier fix)
4. Fix B tasks if they're stale-path artifacts (update result.json paths)
5. Promote: move staging runs to `official/_raw/`
6. Regenerate MANIFEST: `python3 scripts/maintenance/generate_manifest.py`
7. Organize views: `python3 scripts/analysis/organize_official_by_model.py --official-dir runs/official --execute`
8. Regenerate dashboard: `python3 scripts/analysis/dashboard.py --generate-only`

## Post-Pipeline Cleanup & Readiness

After the promote/organize steps, always perform these checks and include the results in your summary:

### 9. Clean stale Daytona sandboxes
```bash
python3 scripts/infra/daytona_cost_guard.py teardown-candidates --yes
```
Report how many sandboxes were cleaned.

### 10. Remove empty staging directories
Delete any staging run directories with 0 trial results (leftover skeletons from interrupted runs).

### 11. Investigate Cat C (verifier) failures
For each Cat C task quarantined:
- Read the exception.txt and verifier output
- Identify root cause (missing libs, syntax error, undefined variables, etc.)
- **Fix the verifier script** before marking the task for rerun
- Report what was found and fixed

### 12. Check for recurring infra issues
Review Cat A failures for patterns:
- Sandbox name collisions → already fixed? (8-char suffix in daytona.py)
- Disk limit exceeded → check task.toml storage_mb
- Token expiry mid-run → check if token-aware picker was active
- Rate limiting → check capacity before rerun
Report any unfixed issues that would cause reruns to fail again.

### 13. Coverage matrix
Show the current dual-verifier coverage matrix (merging old `baseline`/`mcp` config names with `baseline-local-direct`/`mcp-remote-direct`).

### 14. Capacity check
```bash
python3 scripts/infra/fetch_usage.py
python3 scripts/infra/capacity.py
```
Report available slots and any rate-limited accounts.

### 15. Summary with next actions
Provide a consolidated summary:
- What was promoted, quarantined, cleaned
- Verifier fixes applied (if any)
- Tasks needing reruns (with reason and whether the root cause is fixed)
- Current coverage gaps by model/agent/config
- Available capacity for next launch
- Recommended next actions (which gaps to prioritize, any blockers)
