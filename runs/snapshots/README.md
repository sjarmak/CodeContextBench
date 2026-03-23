# Results Snapshots

Frozen, auditable benchmark results. Each snapshot is tied to a specific
benchmark suite version, model, and configuration(s).

## Snapshots

| Snapshot | Tasks | Model | Description |
|----------|------:|-------|-------------|
| `csb-v1-mixed371--haiku45--030326` | 371 | Haiku 4.5 | Initial report: baseline vs Sourcegraph MCP |
| `csb-v1-mixed371--sonnet46--expanded` | 464 | Sonnet 4.6 | Sonnet expansion |
| `csb-v1-mixed371--haiku45--mcp-comparison` | 747 | Haiku 4.5 | 3-way MCP: Augment + GitHub + Sourcegraph |
| `csb-v1-mixed371--opus46--mcp-comparison` | 23 | Opus 4.6 | Opus MCP comparison on complex codebases |

## Structure

Each snapshot contains:

```
{snapshot_id}/
  SNAPSHOT.json          # Manifest: suite, model, configs, aggregate scores
  browse.html            # Interactive results browser (open in browser)
  summary/
    rewards.json         # Per-task reward scores by config
    aggregate.json       # Mean scores, costs, timing
    timing.json          # Per-task wall clock, agent time, setup time
    costs.json           # Per-task cost and token breakdowns
  traces/                # Symlinks to source run directories (internal)
    {config}/{task_id}/
  export/                # Sanitized copies for public publishing
    traces/{config}/{task_id}/
      result.json        # Trial metadata
      task_metrics.json  # Reward, timing, cost, tokens
      verifier/reward.txt
      agent/instruction.txt
```

## Browsing

Open `browse.html` in any web browser for an interactive, sortable, filterable
view of all task results with baseline vs MCP comparison.

## Trajectories

Full agent trajectories (tool calls, LLM responses, per-step timing) are
available as compressed archives in the GitHub Release for each snapshot.

## Creating Snapshots

```bash
python3 scripts/publishing/create_snapshot.py \
  --suite benchmarks/suites/csb-v2-dual264.json \
  --model haiku45 --tag 040101 \
  --scan-dirs runs/staging runs/official/_raw
```

## Verifying & Exporting

```bash
python3 scripts/publishing/verify_snapshot.py --all
python3 scripts/publishing/export_snapshot.py runs/snapshots/{snapshot_id}
```
