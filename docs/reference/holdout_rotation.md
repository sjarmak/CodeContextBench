# Holdout Partition Rotation

## Purpose

The holdout partition system assigns each benchmark task to one of two groups:

- **public** (~60%): Tasks whose IDs, prompts, and ground truth may appear in
  published results, leaderboards, and technical reports. These enable
  reproducibility and external validation.
- **held-out** (~40%): Tasks whose IDs are never published. Scores on these
  tasks are reported only in aggregate. This prevents model providers from
  overfitting to known tasks (contamination).

## Rationale

Benchmark contamination occurs when model training data includes benchmark
questions or answers. A two-tier partition mitigates this:

1. **Public tasks** let the community reproduce and audit results.
2. **Held-out tasks** provide an uncontaminated signal. If a model scores
   significantly higher on public tasks than held-out tasks, that gap is
   evidence of contamination.

The 60/40 split balances reproducibility (enough public tasks for meaningful
comparison) against contamination resistance (enough held-out tasks for
statistical power).

## Stratification

The partition is stratified by SDLC work type to ensure every category has at
least 3 public tasks. This guarantees that per-category public results are
always reportable. The 9 SDLC work types are:

- sdlc_fix, sdlc_feature, sdlc_debug, sdlc_test, sdlc_refactor
- sdlc_design, sdlc_document, sdlc_understand, sdlc_secure

## Generation

The partition map is generated deterministically from a seed:

```bash
python3 scripts/maintenance/generate_partition.py --seed 42 --public-ratio 0.6
```

The output is written to `configs/partition_map.json`.

## Rotation Cadence

The held-out set should be rotated periodically to limit the value of any
leaked task IDs and to refresh the contamination signal.

| Event                                   | Action                                                                                                                            |
| --------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| **Scheduled rotation (every 6 months)** | Re-run `generate_partition.py` with a new seed. Record the old seed and rotation date in the commit message.                      |
| **Suspected contamination**             | Rotate immediately. Bump the seed, regenerate, and note the reason.                                                               |
| **Task addition or removal**            | Re-run with the same seed to incorporate new tasks. Existing assignments are not guaranteed to be stable across task-set changes. |

### Rotation Procedure

1. Choose a new seed (e.g., increment by 1, or use the current Unix timestamp).
2. Run the generator:
   ```bash
   python3 scripts/maintenance/generate_partition.py --seed <NEW_SEED>
   ```
3. Verify the output:
   - All 9 SDLC work types have >= 3 public tasks.
   - Public ratio is within 55-65%.
4. Commit the updated `configs/partition_map.json` with a message like:
   ```
   chore: rotate holdout partition (seed N -> M)
   ```
5. Update any published leaderboards to reflect the new partition epoch.

## File Locations

| File                                        | Purpose                                        |
| ------------------------------------------- | ---------------------------------------------- |
| `lib/csb/partition.py`                      | Core library: generate, load, query partitions |
| `configs/partition_map.json`                | Current partition assignments                  |
| `scripts/maintenance/generate_partition.py` | CLI to regenerate the partition map            |
| `docs/reference/holdout_rotation.md`        | This document                                  |

## Seed History

| Date       | Seed | Reason            |
| ---------- | ---- | ----------------- |
| 2026-04-03 | 42   | Initial partition |
