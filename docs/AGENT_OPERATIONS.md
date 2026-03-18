# Agent Operations Guide: CodeScaleBench

> **Purpose**: Single authoritative reference for agents working in this repo.
> Covers the full lifecycle: what coverage means, how to launch runs, how to
> classify failures, when to promote, and what qualifies as quality output.

---

## 1. Coverage Contract

### What "full coverage" means

A **complete evaluation** requires results for every task in the canonical task
selection file, across every config in the evaluation matrix.

| Component | Source of truth | Location |
|-----------|----------------|----------|
| Task universe | `configs/harnesses/selected_benchmark_tasks.json` | `.tasks[]` (exclude `.excluded=true`) |
| Config matrix | Per-harness `*_2config.sh` scripts | Varies by harness |
| Completed results | `runs/official/MANIFEST.json` | `.runs[run_id].tasks` + `.run_history[run_id]` |

### Config matrices by harness

| Harness | Configs | Script |
|---------|---------|--------|
| Claude Code | `baseline-local-direct`, `mcp-remote-direct` | `run_selected_tasks.sh` |
| OpenHands | `baseline-local-direct`, `mcp-remote-direct` | `openhands_2config.sh` |
| Cursor | `baseline-local-direct`, `mcp-remote-direct` | `cursor_2config.sh` |
| Codex | `baseline-local-direct`, `mcp-remote-direct` | `codex_2config.sh` |
| Gemini | `baseline-local-direct`, `mcp-remote-direct` | `gemini_2config.sh` |

Each config pair has semantic meaning:
- **baseline-local-direct**: Agent has full local repo source. No MCP tools. Uses `Dockerfile`.
- **mcp-remote-direct**: Source deleted from container. Agent gets Sourcegraph MCP tools. Uses `Dockerfile.sg_only`.

### How to compute coverage gaps

```bash
python3 -c "
import json

manifest = json.load(open('runs/official/MANIFEST.json'))
selection = json.load(open('configs/harnesses/selected_benchmark_tasks.json'))
active_tasks = [t['task_id'] for t in selection['tasks'] if not t.get('excluded')]

# Change these for your harness
run_ids = {
    'baseline-local-direct': 'openhands/baseline-local-direct',
    'mcp-remote-direct': 'openhands/mcp-remote-direct',
}

run_history = manifest.get('run_history', {})
for config, run_id in run_ids.items():
    completed = set(run_history.get(run_id, {}).keys())
    gaps = [t for t in active_tasks if t not in completed]
    print(f'{config}: {len(active_tasks)-len(gaps)}/{len(active_tasks)} ({len(gaps)} gaps)')
    if gaps:
        print(f'  Missing: {gaps[:10]}...' if len(gaps)>10 else f'  Missing: {gaps}')
"
```

### Creating a gap-fill subset

When gaps are identified, create a subset JSON for targeted reruns:

```bash
python3 -c "
import json

manifest = json.load(open('runs/official/MANIFEST.json'))
selection = json.load(open('configs/harnesses/selected_benchmark_tasks.json'))
run_history = manifest.get('run_history', {})

# Identify missing tasks for a specific config
config_run_id = 'openhands/mcp-remote-direct'  # adjust per harness
completed = set(run_history.get(config_run_id, {}).keys())
gap_tasks = [t for t in selection['tasks']
             if not t.get('excluded') and t['task_id'] not in completed]

subset = {'metadata': {'description': f'Gap fill for {config_run_id}', 'task_count': len(gap_tasks)},
          'tasks': gap_tasks}
outfile = 'configs/harnesses/gap_fill_subset.json'
json.dump(subset, open(outfile, 'w'), indent=2)
print(f'Wrote {len(gap_tasks)} tasks to {outfile}')
"
```

Then launch:
```bash
CSB_SKIP_CONFIRM=1 bash configs/harnesses/openhands_2config.sh \
    --full-only --subset gap_fill_subset.json
```

---

## 2. Run Lifecycle

```
Launch (harness script)
  ↓
Results land in: runs/staging/<run_dir>/<config>/<timestamp>/<task_hash>/
  ↓
Validate (scripts/running/promote_run.py --dry-run)
  ↓
Promote (scripts/running/promote_run.py <run_dir>)
  ↓
Regenerate MANIFEST (scripts/maintenance/generate_manifest.py)
  ↓
Archive old runs (scripts/maintenance/archive_run.py)
```

### Key rules

- **Never edit `runs/official/` directly** — use promote_run.py
- **MANIFEST.json is regenerated, not hand-edited** — run generate_manifest.py
- **staging/ is ephemeral** — runs may land directly in official/_raw/ for some harnesses
- **Promotion is atomic** — all-or-nothing via RunPromotionOrchestrator

---

## 3. Failure Classification & Triage Decision Tree

When a task fails (reward=0 or missing result.json), classify it using this tree.
**Each category has a different resolution path.**

### Category A: Infrastructure Failures (rerun without changes)

These are NOT agent quality issues. The task never got a fair run.

| Symptom | Fingerprint | Action |
|---------|-------------|--------|
| No result.json, process killed | VM spindown, OOM kill | Clean up, rerun |
| No result.json, logs show `429` or `rate_limit` | API rate limiting | Wait, rerun with different account rotation |
| No result.json, Docker build log shows build failure | Docker build error (OOM, network, apt) | Fix Dockerfile or increase resources in task.toml, rerun |
| No result.json, `connection refused` or timeout in logs | Transient network error | Rerun |
| result.json exists but `"status": "error"` | Harbor/harness crash | Check harness logs, likely rerun |

**Detection**: `scripts/analysis/status_fingerprints.py` has 12 regex patterns.
Run `python3 scripts/analysis/aggregate_status.py runs/staging/<dir>` to classify.

### Category B: Setup/Configuration Errors (fix config, then rerun)

The agent ran but the environment was misconfigured.

| Symptom | Fingerprint | Action |
|---------|-------------|--------|
| MCP run but agent never uses MCP tools | Missing preamble or tools not injected | Check `instruction_mcp.md` exists, verify `BASELINE_MCP_TYPE=sourcegraph_full` |
| MCP run, tools available, but agent ignores them | Preamble present but doesn't instruct usage | Strengthen MCP usage instruction in agent prompt |
| Agent has MCP tools but SG mirror not set up | `sg-evals/` repo missing for this task | Run `scripts/infra/create_sg_*_repos.sh` |
| instruction.md leaks file paths or solution hints | Contaminated instruction | Fix instruction.md, remove leaked paths, rerun |
| Dockerfile.sg_only still contains full source | sg_only variant not generated | Run `scripts/maintenance/generate_sgonly_dockerfiles.py` |

**Detection**: `scripts/evaluation/trace_quality_pipeline.py` Stage 2 (Setup Quality)
checks for V5 preamble markers, SG mirror markers, and MCP tool presence.

### Category C: Verifier/Oracle Issues (fix verifier, re-score)

The agent produced valid output but the verifier scored incorrectly.

| Symptom | Fingerprint | Action |
|---------|-------------|--------|
| reward=0 but agent trace shows correct solution | Verifier false negative | Run with `DEBUG_MODE=true`, check `/logs/verifier/debug/`, fix eval.sh |
| reward=1.0 but solution is clearly wrong | Verifier false positive | Fix oracle_answer.json or oracle_checks.py, re-score |
| eval.sh exits with parse error | Verifier bug | Fix eval.sh script, re-run verifier only |
| validation_result.json has `"status": "verifier_error"` | Verifier crash | Check stderr in verifier logs |
| Oracle doesn't match expected format | oracle_answer.json schema mismatch | Validate against schemas/judge_result.schema.json |
| Dual verification <80% for oracle promotion | Weak oracle | Curate oracle: `scripts/running/curate_oracle.py` |

**Detection**: Check `validation_result.json` for `"status"` field. Values:
- `"scored"` — verifier ran successfully
- `"invalid_output"` — agent produced unparseable output
- `"verifier_error"` — verifier itself crashed

**Re-scoring without re-running the agent**:
```bash
# Re-run only the verifier on existing agent output
docker exec <container> bash /tests/eval.sh  # or test.sh
```

### Category D: Agent Quality Issues (genuine failures — analyze, don't rerun)

The agent had a fair environment and produced a suboptimal solution.

| Symptom | Fingerprint | Action |
|---------|-------------|--------|
| Agent searched <5 files, never found relevant code | Insufficient context retrieval | Analyze IR metrics, consider prompt improvement |
| Agent searched >10 files, found relevant code, but edit was wrong | Implementation error | Genuine agent limitation — record as failed |
| Agent exceeded context window or timeout | Scope exceeded (>100 tool calls) | Task may be too hard, or agent strategy inefficient |
| Agent searched correct files but missed key context | Context misused | Analyze retrieval precision, check if MCP would help |

**Detection**: `scripts/evaluation/failure_analysis.py` classifies using the
6-category taxonomy. Feed it result.json + trajectory.

**Key principle**: Category D failures are **valid data points**. Do NOT rerun
them hoping for a different result — they represent the agent's actual capability
on that task. Only rerun if you suspect A/B/C contamination.

---

## 4. Quality Criteria for Valid Agent Output

A run result is **valid and usable** when ALL of these hold:

### Minimum validity (for inclusion in MANIFEST)
- [ ] `result.json` exists and is valid JSON
- [ ] `reward.txt` exists with a float in [0.0, 1.0]
- [ ] Agent completed (not killed/crashed)
- [ ] Docker build succeeded
- [ ] No Category A or B issues detected

### Full quality (for statistical analysis)
- [ ] `trajectory.json` exists and is parseable (enables TTFR/TTAR metrics)
- [ ] `task_metrics.json` exists (or can be generated via extract_task_metrics.py)
- [ ] For MCP configs: agent actually invoked MCP tools (≥1 tool call)
- [ ] For MCP configs: Dockerfile.sg_only was used (source deleted)
- [ ] `validation_result.json` has `"status": "scored"` (not verifier_error)
- [ ] No instruction contamination detected (no leaked file paths)

### Parseable trace requirements
A trace is **fully parseable** when:
- `trajectory.json` contains structured tool call records
- Each tool call has: tool name, input, output, timestamp
- TTFR (Time to First Retrieval) and TTAR (Time to All Retrieval) can be computed
- Token counts are extractable (input_tokens, output_tokens, cache_read)
- Cost can be computed from token counts

---

## 5. Config Versioning

Each unique evaluation configuration should be identifiable by:

| Dimension | Example | Where tracked |
|-----------|---------|---------------|
| Harness | openhands, claude-code, cursor | Run ID prefix |
| Model | anthropic/claude-sonnet-4-6 | MANIFEST `.runs[].model` |
| Config variant | baseline-local-direct | MANIFEST run_id suffix |
| Agent code version | git SHA of agents/ | **NOT currently tracked** |
| Preamble version | Hash of instruction + system prompt | **NOT currently tracked** |
| Dockerfile variant | SHA of Dockerfile.sg_only | **NOT currently tracked** |

**Gap**: When agent code or prompts change, old runs become stale but there's
no automated way to detect this. A config fingerprint system is needed.

### Workaround until fingerprinting exists

When making changes to agent code, prompts, or Dockerfiles:
1. Note the git SHA before and after
2. Add a comment to MANIFEST or run metadata indicating the change
3. Consider whether old runs need to be re-run or just flagged as stale

---

## 6. Key Scripts Quick Reference

| Task | Script | Example |
|------|--------|---------|
| Launch OH 2-config run | `configs/harnesses/openhands_2config.sh` | `CSB_SKIP_CONFIRM=1 bash openhands_2config.sh --subset gap.json` |
| Launch CC 2-config run | `configs/harnesses/run_selected_tasks.sh` | `CSB_SKIP_CONFIRM=1 bash run_selected_tasks.sh --benchmark csb_sdlc_fix` |
| Check coverage gaps | See Section 1 snippet | — |
| Classify run failures | `scripts/analysis/aggregate_status.py` | `python3 aggregate_status.py runs/staging/<dir>` |
| Deep failure analysis | `scripts/evaluation/failure_analysis.py` | — |
| Trace quality audit | `scripts/evaluation/trace_quality_pipeline.py` | — |
| Promote staging → official | `scripts/running/promote_run.py` | `python3 promote_run.py <staging_dir>` |
| Regenerate MANIFEST | `scripts/maintenance/generate_manifest.py` | `python3 generate_manifest.py --output runs/official/MANIFEST.json` |
| Validate task pre-run | `scripts/authoring/validate_tasks_preflight.py` | — |
| Validate task post-run | `scripts/authoring/validate_task_run.py` | — |
| Check infra health | `scripts/infra/check_infra.py` | — |
| Account health | `scripts/infra/account_health.py` | — |
| Archive old runs | `scripts/maintenance/archive_run.py` | — |
| Extract task metrics | `scripts/evaluation/extract_task_metrics.py` | — |
| ABC quality audit | `scripts/evaluation/abc_audit.py` | — |
| MCP utilization audit | `scripts/evaluation/mcp_audit.py` | — |

---

## 7. Dual Verification System

### How it works

Each task has two independent verification layers:

1. **Deterministic verifier** (`tests/eval.sh` / `tests/test.sh`):
   - Runs inside the Docker container post-agent
   - Emits `reward.txt` (0.0-1.0) and `validation_result.json`
   - Types: test_ratio, git_diff, answer_json, custom shell

2. **Oracle ground truth** (`tests/oracle_answer.json` or `tests/ground_truth.json`):
   - Static expected output for comparison
   - 6-source priority chain for discovery (see `csb_metrics/ground_truth.py`)
   - Has `_metadata.dual_verification` tracking verification completeness

### Promotion gates

Oracle answers can only be promoted to canonical when:
- Dual verification ≥80% (`n_dual_verified / n_total >= 0.80`)
- Cross-validation F1 ≥0.6

### When to suspect verifier issues

- reward=0 but agent trace shows plausible solution → **false negative**
- reward=1.0 across all configs (too good to be true) → **possible false positive**
- `validation_result.json` missing or has `verifier_error` status → **verifier crash**
- Score distributions are bimodal (0.0 and 1.0 only) → **may need continuous scoring**

---

## 8. Long-Running Harness Execution

Benchmark runs are **long-running processes** (hours, not minutes). They should
NOT be run inside polecat sessions which have context limits.

### Correct approach for launching runs

```bash
# From the rig directory (mayor/rig/ or crew member's clone)
cd /path/to/codescalebench/rig

# Launch as background process with nohup
CSB_SKIP_CONFIRM=1 nohup bash configs/harnesses/openhands_2config.sh \
    --subset oh_gap_mcp.json \
    --full-only \
    > /tmp/oh_gap_mcp_$(date +%Y%m%d_%H%M%S).log 2>&1 &

echo "PID: $!"
# Monitor: tail -f /tmp/oh_gap_mcp_*.log
```

### Monitoring active runs

```bash
# Check if processes are still running
ps aux | grep harnesses | grep -v grep

# Tail the log
tail -f /tmp/oh_gap_*.log

# Check run status
python3 scripts/analysis/aggregate_status.py runs/staging/<latest_dir> --watch
```

### What to do when a run is interrupted (VM spindown, crash)

1. **Don't panic** — results already written to disk are safe
2. **Check what completed**: Look in `runs/staging/<dir>/<config>/` for task dirs with `result.json`
3. **Compute remaining gaps**: Use the coverage gap script (Section 1)
4. **Generate new subset**: Only include tasks that didn't complete
5. **Relaunch**: Use `--subset` with the gap file
6. **Do NOT rerun already-completed tasks** — the `--skip-completed` flag or subset approach avoids this

---

## 9. Error Catalog (Quick Reference)

From `docs/ERROR_CATALOG.md` and `status_fingerprints.py`:

| Code | Pattern | Severity | Category |
|------|---------|----------|----------|
| E001 | Docker build OOM | infra | A |
| E002 | Docker build network timeout | infra | A |
| E003 | API rate limit (429) | infra | A |
| E004 | OAuth token expired | infra | A |
| E005 | Agent timeout (wall clock) | scope | D |
| E006 | Agent context window exceeded | scope | D |
| E007 | Verifier parse error | verifier | C |
| E008 | Missing Dockerfile.sg_only | setup | B |
| E009 | MCP tools not injected | setup | B |
| E010 | Instruction contamination | setup | B |
| E011 | VM killed / process signal | infra | A |
| E012 | Disk space exhausted | infra | A |
