---
name: status
description: Monitor active runs, check task completion status, and watch benchmark execution progress.
---

# Skill: Status & Monitoring

## Scope

Use this skill when the user asks to:
- Check the status of active or completed runs
- Monitor benchmark execution progress in real-time
- List task completion rates by suite and configuration
- Watch for failures or bottlenecks during runs
- Analyze run fingerprints and anomalies

## Canonical Commands

```bash
# Overall staging status
python3 scripts/analysis/aggregate_status.py --staging

# Watch active runs (refresh every 10s)
python3 scripts/analysis/aggregate_status.py --watch

# Status by suite
python3 scripts/analysis/aggregate_status.py --staging --suite csb_sdlc_debug

# Status fingerprints (failure patterns)
python3 scripts/analysis/status_fingerprints.py runs/staging/run_dir/result.json
```

## Key Metrics

- **Completion rate** — tasks passed / total tasks
- **Model success rate** — tasks where agent succeeded
- **Verification success** — tasks that passed post-run validation
- **Timeouts & OOM** — infrastructure failure rates
- **Anomalies** — tasks with unexpected patterns (fingerprint match)

## Monitoring Patterns

- **Real-time watch**: `--watch` mode updates every 10 seconds
- **Batch status**: Full scan across runs/staging with counts by suite
- **Fingerprint triage**: Use `status_fingerprints` to bucket failures (timeout, OOM, auth, etc.)

## Related Skills

- `/run` — launch and manage runs
- `/audit` — deeper validation and health checks
- `/triage` — investigate specific task failures
