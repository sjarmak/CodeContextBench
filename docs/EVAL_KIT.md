# CSB Eval Kit

Standalone Docker image for running CodeScaleBench (CSB-Quick) benchmarks against
any agent command. No Daytona, Harbor, or Sourcegraph configuration required.

## Prerequisites

- Docker 20.10+ (or Docker Desktop)
- An agent command that accepts a task prompt on stdin or via CLI argument

## Quickstart

Three commands to your first result:

```bash
# 1. Build the eval kit image
docker build -f Dockerfile.eval -t csb-eval .

# 2. Run against your agent
docker run --rm -v ./csb-results:/app/results \
  csb-eval --suite quick --agent-command 'your-agent --stdin'

# 3. View results
cat csb-results/submission.json
```

## Using Docker Compose

For convenience, a Compose file is provided:

```bash
AGENT_COMMAND='your-agent --stdin' docker compose -f docker-compose.eval.yml up
```

Results are written to `./csb-results/` on the host.

## Configuration Options

### Suite Selection

| Flag            | Description                             |
| --------------- | --------------------------------------- |
| `--suite quick` | CSB-Quick task set (default, ~20 tasks) |
| `--suite full`  | Full benchmark suite                    |

### Agent Command

The `--agent-command` flag specifies the command invoked per task. The eval runner
passes task context as a JSON file path argument. Your agent command should:

1. Accept a file path argument pointing to the task JSON
2. Write its output to the location specified in the task JSON
3. Exit with code 0 on success

### Environment Variables

| Variable         | Description                            | Default     |
| ---------------- | -------------------------------------- | ----------- |
| `AGENT_COMMAND`  | Agent command (used by docker-compose) | none        |
| `CSB_OUTPUT_DIR` | Directory for results output           | `./results` |

### Volume Mounts

Mount a host directory to `/app/results` to persist output:

```bash
docker run --rm -v /path/to/output:/app/results csb-eval --suite quick --agent-command '...'
```

## What Is Included

The eval kit image contains:

- `csb` CLI entrypoint
- `lib/csb/` -- core evaluation library (runner, scoring, reporting, partitioning)
- `scripts/evaluation/` -- evaluation and verification scripts
- `configs/csb_quick.json` -- CSB-Quick task manifest
- `schemas/` -- JSON schemas for validation
- `observatory/` -- taxonomy YAML, annotation schema, and exemplars

## What Is NOT Included

The image intentionally excludes:

- Task environment Dockerfiles (`benchmarks/*/environment/`)
- Git history (`.git/`)
- Run data (`runs/`, `data/`)
- Secrets (`.env*`)
- Harness configurations (`configs/harnesses/`)
- Base images (`base_images/`)

## Troubleshooting

### "No such file: configs/csb_quick.json"

The manifest was not copied into the image. Rebuild with:

```bash
docker build --no-cache -f Dockerfile.eval -t csb-eval .
```

### Agent command not found

Ensure your agent binary is either:

- Installed inside the container (extend the Dockerfile), or
- Accessible via a mounted volume and referenced by absolute path

### Permission denied on results directory

The container runs as root by default. Ensure the host results directory is
writable, or run with `--user $(id -u):$(id -g)`.

### Container exits immediately

Check that your `--agent-command` is valid. Run with `--help` to verify the
image works:

```bash
docker run --rm csb-eval --help
```

### JSON validation errors

The eval kit uses `jsonschema` for validating task manifests and submissions.
If you see schema validation errors, check that your agent output matches the
expected format in `schemas/submission.schema.json`.
