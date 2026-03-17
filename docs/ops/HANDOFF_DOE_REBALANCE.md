# Handoff: DOE-Driven SDLC Task Rebalance

## Goal

Rebalance the 9 SDLC benchmark suites from uniform 20 tasks/suite (180 total) to Neyman-optimal allocation at 150 tasks total, based on empirical variance decomposition from 175 paired pilot runs across 3-8 replicates per task. This maximizes statistical power for detecting the MCP treatment effect and its interaction with SDLC phase, codebase size, and task complexity — while reducing total task count by 17%.

## Context: Why This Matters

A Design of Experiments (DOE) variance decomposition showed that uniform n=20/suite is simultaneously over-sampling low-variance suites and under-sampling high-variance ones:

- **csb_sdlc_fix** (sigma2_task=0.1518, ICC=0.964): task heterogeneity dominates — the suite mixes trivially-solvable patches with multi-file fixes. Needs MORE tasks.
- **csb_sdlc_understand** (sigma2_task=0.0123, ICC=0.078): agent stochasticity dominates — same task gives different results each run. Needs more REPS, not tasks.

The Neyman-optimal allocation for a 150-task budget (proportional to within-suite SD) is:

| Suite       | Current n | Target n | Delta | Action                 |
|-------------|-----------|----------|-------|------------------------|
| fix         | 20        | 25       | +5    | Promote 5 from backups |
| test        | 18        | 23       | +5    | Create 5 new tasks     |
| feature     | 20        | 22       | +2    | Create 2 new tasks     |
| debug       | 20        | 18       | -2    | Move 2 to backups      |
| refactor    | 20        | 15       | -5    | Move 5 to backups      |
| design      | 20        | 14       | -6    | Move 6 to backups      |
| document    | 20        | 12       | -8    | Move 8 to backups      |
| secure      | 20        | 11       | -9    | Move 9 to backups      |
| understand  | 20        | 10       | -10   | Move 10 to backups     |
| **TOTAL**   | **180**   | **150**  | **-30** |                      |

## Current Status

- DOE analysis scripts written and validated:
  - `scripts/doe_variance_analysis.py` — variance decomposition, per-suite power, Neyman/minimax allocation
  - `scripts/doe_power_curves.py` — power curves for main effect, SDLC interaction, continuous moderators, 3-arm SCIP design
- Both scripts read from `runs/official/MANIFEST.json` (run_history section)
- Analysis outputs verified against 175 paired tasks, 3-8 reps each
- No task directories or selection files modified yet

## Files Changed (this session)

- `scripts/doe_variance_analysis.py` — NEW (variance decomposition + allocation)
- `scripts/doe_power_curves.py` — NEW (power curves for interaction effects)

## Key Findings / Decisions

1. **150 tasks is the practical sweet spot** — gives >87% power for SDLC×Config interaction at d=0.15, >95% for main effect at d=0.10, >83% for complexity interaction
2. **342 tasks would be needed for d=0.10 SDLC interaction** (38/suite) — not worth the cost unless that granularity is required
3. **Three-arm SCIP design is cheap to add** — SCIP vs fuzzy contrast only needs 16-64 tasks because both arms use same MCP tools (lower delta variance)
4. **Observed overall MCP delta is near zero (+0.001)** — the interesting signal is in the interaction (fix/understand benefit, debug/refactor hurt)
5. **High-variance suites to GROW**: fix (sigma2=0.154), test (0.127), feature (0.116)
6. **Low-variance suites to SHRINK**: understand (0.027), secure (0.031), document (0.038)

## Task Inventory for Rebalance

### Suites that GROW (need new/promoted tasks)

**csb_sdlc_fix (+5, target 25):**
- 5 backup tasks available in `benchmarks/backups/csb_sdlc_fix_extra/`:
  - Check quality before promoting — they were removed for "over-represented repo" reason
  - If repo diversity is a concern, create new tasks from under-represented repos instead

**csb_sdlc_test (+5, target 23):**
- 2 backup tasks in `benchmarks/backups/csb_sdlc_test_tac/` — but these need external RocketChat server (incompatible)
- Must scaffold 5 new tasks using `/scaffold-task` skill
- Prioritize high-variance task types (unit test generation, integration testing, code review)

**csb_sdlc_feature (+2, target 22):**
- No backup tasks available
- Scaffold 2 new tasks — prioritize languages/repos under-represented in current 20

### Suites that SHRINK (move to backups)

Selection criteria for which tasks to move OUT:
1. **Keep high-variance tasks** (sigma2_rep > suite median) — they contribute most information
2. **Keep tasks with extreme deltas** (|MCP - baseline| is large) — most informative for interaction estimation
3. **Remove low-information tasks** (consistent pass or consistent fail across both configs) — they add no signal
4. **Maintain language/repo diversity** in the remaining set

**csb_sdlc_debug (-2, target 18):** Move 2 lowest-information tasks
**csb_sdlc_refactor (-5, target 15):** Move 5 lowest-information tasks
**csb_sdlc_design (-6, target 14):** Move 6 lowest-information tasks
**csb_sdlc_document (-8, target 12):** Move 8 lowest-information tasks
**csb_sdlc_secure (-9, target 11):** Move 9 lowest-information tasks
**csb_sdlc_understand (-10, target 10):** Move 10 lowest-information tasks

## Implementation Plan

### Phase 1: Identify tasks to move (analysis only)

```bash
# Run the variance analysis to get per-task stats
python3 scripts/doe_variance_analysis.py --json > /tmp/doe_analysis.json

# The JSON output includes task_means and task_stds per suite per config
# Use these to rank tasks by information value
```

Write a selection script (e.g. `doe_select_tasks.py`) that:
1. Reads `MANIFEST.json` run_history for per-task reward vectors
2. For each suite, ranks tasks by "information value":
   - High value = large |delta| OR high replicate variance (the task discriminates between configs or shows agent sensitivity)
   - Low value = delta ≈ 0 AND low replicate variance (both configs solve it the same way every time)
3. Selects the top-N tasks to KEEP per suite (N = Neyman target)
4. Outputs the keep/move lists

### Phase 2: Move task directories

```bash
# For each suite that shrinks, move excess tasks to backups
# Example for csb_sdlc_understand (20 → 10):
mkdir -p benchmarks/backups/csb_sdlc_understand_doe_trim/
mv benchmarks/csb_sdlc_understand/<task_to_remove>/ benchmarks/backups/csb_sdlc_understand_doe_trim/

# For csb_sdlc_fix (20 → 25), promote from backups:
mv benchmarks/backups/csb_sdlc_fix_extra/<task>/ benchmarks/csb_sdlc_fix/
```

### Phase 3: Scaffold new tasks (for suites that grow beyond backup supply)

```bash
# csb_sdlc_test needs 5 new tasks, csb_sdlc_feature needs 2 new tasks
# Use /scaffold-task skill for each
```

### Phase 4: Regenerate selection file and manifest

```bash
python3 scripts/select_benchmark_tasks.py  # regenerate selection JSON
python3 scripts/generate_manifest.py        # update MANIFEST
python3 scripts/maintenance/repo_health.py              # health gate
```

### Phase 5: Validate and run pilot

```bash
# Validate all tasks still pass preflight
python3 scripts/authoring/validate_tasks_preflight.py

# Run one pass of all 150 tasks to confirm nothing broke
# (use existing variance run configs as template)
```

## Open Risks / Unknowns

1. **Backup task quality**: The 5 csb_sdlc_fix_extra tasks were removed for repo over-representation — need to check if promoting them creates unacceptable repo bias
2. **New task scaffolding**: 7 new tasks needed (5 csb_sdlc_test, 2 csb_sdlc_feature) — each requires instruction, verifier, Dockerfile, and oracle curation. Budget ~2-3 hours per task.
3. **Historical comparability**: Changing suite sizes means old runs (n=20) aren't directly comparable to new runs (variable n). Document this in the white paper methods section.
4. **Org suites unaddressed**: This rebalance only covers SDLC suites. The 11 Org suites (220 tasks) don't have enough variance run data yet for the same analysis. Run doe_variance_analysis.py with `--include-mcp-unique` after collecting Org variance data.
5. **csb_sdlc_test currently has 18 tasks** (not 20) — growing to 23 means adding 5, not 3

## Next Best Command

```bash
# Start by writing the information-value ranking script
# This is the prerequisite for deciding WHICH tasks to keep/move
python3 scripts/doe_variance_analysis.py --json 2>/dev/null | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(json.dumps(data, indent=2)[:2000])
"
```

## Reference: Key DOE Parameters

- **delta=0.15**: minimum detectable effect size (15 percentage points) for SDLC interaction
- **reps=3**: planned replicates per task per arm (minimum; 5 for understand/secure)
- **arms=3**: baseline + MCP/fuzzy + MCP/SCIP (three-arm design)
- **alpha=0.05**: significance level (two-sided)
- **Power target: 0.80** (80% probability of detecting a true effect)
- **Neyman allocation**: tasks ∝ within-suite SD (minimizes overall variance for fixed budget)
