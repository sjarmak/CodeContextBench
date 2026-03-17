# Handoff: Run 39 Missing CodeScaleBench-Org Baselines

## Goal
Run baseline-local-artifact evaluation for 39 Org tasks that currently only have MCP results. This brings total paired coverage from 212 to 251 (100%).

## Current Status
- 81 Org tasks across 11 csb_org_* suites
- 42 already have paired results (baseline + MCP) in runs/official/
- **39 need baseline runs** (listed below)
- A sub-selection file is ready: `configs/mcp_baseline_rerun.json`

## Task List (39 tasks across 11 suites)

| Suite | Count | Task IDs |
|-------|-------|----------|
| csb_org_compliance | 5 | CCX-compliance-052, 053, 057-ds, 115, 118 |
| csb_org_crossorg | 1 | CCX-crossorg-062 |
| csb_org_crossrepo | 1 | CCX-dep-trace-106 |
| csb_org_crossrepo_tracing | 4 | CCX-config-trace-003, CCX-dep-trace-002, 102, 116 |
| csb_org_domain | 6 | CCX-domain-071, 072, 073, 074, 101, 112 |
| csb_org_incident | 6 | CCX-incident-032, 033, 034, 037, 108, 110 |
| csb_org_migration | 5 | CCX-migration-022, 026, 107, 114, 117 |
| csb_org_onboarding | 3 | CCX-onboard-043, 103, 109 |
| csb_org_org | 3 | CCX-agentic-081, 082, 083 |
| csb_org_platform | 2 | CCX-platform-104, 119 |
| csb_org_security | 3 | CCX-vuln-remed-013, 105, 111 |

## Config Details
- **Config**: `baseline-local-artifact` (auto-detected by runner for Org artifact-only tasks)
- **Model**: `anthropic/claude-haiku-4-5-20251001` (default)
- **Dockerfile**: Each task has `environment/Dockerfile.artifact_only` (full local code, agent produces answer.json)
- **Category**: staging (promotes to official after validation)
- **Selection file**: `configs/mcp_baseline_rerun.json` (pre-built, 39 tasks)

## Execution Steps

### 1. Pre-flight checks
```bash
python3 scripts/infra/check_infra.py
python3 scripts/authoring/validate_tasks_preflight.py --selection-file configs/mcp_baseline_rerun.json
```

### 2. Dry run (verify task detection)
```bash
./configs/harnesses/run_selected_tasks.sh \
  --selection-file configs/mcp_baseline_rerun.json \
  --baseline-only \
  --parallel 12 \
  --dry-run
```

You should see:
- 39 tasks detected
- Auto-detection message: "Auto-detected Org tasks (artifact-only) → using artifact configs (mcp-remote-artifact)"
- Config: `baseline-local-artifact`
- `--baseline-only` means only baselines run (no MCP)

### 3. Launch baselines
```bash
./configs/harnesses/run_selected_tasks.sh \
  --selection-file configs/mcp_baseline_rerun.json \
  --baseline-only \
  --parallel 12
```

Interactive confirmation will appear — approve it. Runs land in `runs/staging/`.

Estimated time: ~1-2 hours at 12 parallel slots (3 accounts x 4 sessions, 39 tasks, ~5 min each with artifact mode).

### 4. Monitor progress
```bash
# Quick status
ls runs/staging/*/baseline-local-artifact/ | wc -l

# Or use /watch-benchmarks skill for detailed status
```

### 5. Post-run: validate and promote
```bash
# Check results
python3 -c "
import json, glob
results = glob.glob('runs/staging/*/baseline-local-artifact/*/result.json')
print(f'Results: {len(results)}/39')
rewards = []
for r in results:
    data = json.load(open(r))
    reward = data.get('reward', data.get('score', -1))
    rewards.append(reward)
    if reward == 0:
        task = r.split('/')[-2]
        print(f'  ZERO: {task}')
print(f'Mean reward: {sum(rewards)/len(rewards):.3f}')
"

# Promote to official
python3 scripts/promote_run.py --execute <staging_run_name>

# Regenerate MANIFEST
python3 scripts/generate_manifest.py
```

### 6. Verify full coverage
```bash
python3 -c "
import json
m = json.load(open('runs/official/MANIFEST.json'))
mcp_suites = {k.split('/')[0] for k in m['runs'] if 'csb_org_' in k}
for suite in sorted(mcp_suites):
    bl_key = f'{suite}/baseline-local-artifact'
    mcp_key = f'{suite}/mcp-remote-artifact'
    bl_n = len(m['runs'].get(bl_key, {}).get('tasks', {}))
    mcp_n = len(m['runs'].get(mcp_key, {}).get('tasks', {}))
    print(f'{suite}: baseline={bl_n}, mcp={mcp_n}, paired={min(bl_n, mcp_n)}')
"
```

Target: all 81 Org tasks fully paired.

## Open Risks / Unknowns
- Some artifact-mode tasks produce complex answer.json that oracle_checks.py evaluates — check for 0-score tasks
- 5 mirrors are still pending creation (jdk, chromium, aosp, libreoffice, arangodb) but these only affect MCP runs, not baselines
- If any tasks fail to build, check Dockerfile.artifact_only exists and has correct base image

## Key Files
- `configs/mcp_baseline_rerun.json` — sub-selection file (39 tasks)
- `configs/harnesses/run_selected_tasks.sh` — unified runner
- `configs/_common.sh` — shared infra (token refresh, account rotation, `baseline_config_for()`)
- `agents/claude_baseline_agent.py` — agent code (V5 preamble)
- `scripts/promote_run.py` — staging → official promotion
- `scripts/generate_manifest.py` — MANIFEST regeneration
