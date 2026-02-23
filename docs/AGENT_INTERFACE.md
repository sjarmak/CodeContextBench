# Agent Interface Specification

This document describes what an agent receives and must produce when running a CodeContextBench task.

## Input

### Workspace

The agent's working directory is one of:

| Path | Used by |
|------|---------|
| `/workspace/` | Most benchmarks (DocGen, LargeRepo, TAC, CodeReview, LinuxFLBench, Enterprise, etc.) |
| `/app/` | SWE-bench Pro |
| `/testbed/` | Some SWE-bench variants |

The workspace contains the repository code at a specific commit (the `pre_fix_rev` from `task.toml`). The agent has full read/write access.

### Instruction

The task instruction is delivered as the agent's prompt text. It is read from `instruction.md` in the task directory and includes:

- Problem description (bug report, feature request, or documentation task)
- Repository and difficulty metadata
- Specific files or areas to modify
- Constraints (e.g., "do not modify tests")

### Time Limit

Each task has a `time_limit_sec` field in `task.toml` (typically 300-1800 seconds). The agent process is killed if it exceeds this limit.

### Environment Variables

| Variable | Description |
|----------|-------------|
| `TASK_NAME` | Task identifier (e.g., `sgt-001`, `applyconfig-doc-001`) |
| `TIME_LIMIT_SEC` | Maximum execution time in seconds |

## Output

The agent modifies files in the workspace to solve the task. After the agent finishes (or times out), the verifier runs `tests/test.sh` to evaluate the result.

### Verification

The test script (`tests/test.sh`) is uploaded by Harbor to `/tests/` in the container at runtime. It is **not** present in the workspace directory. The script:

1. Runs inside the container after the agent completes
2. Writes a reward to `/logs/verifier/reward.txt` as a plain decimal float (0.0-1.0)
3. Always exits 0 (Harbor reads the reward value, not the exit code)

### Result Format

Harbor produces a `result.json` for each task containing:

```json
{
  "task_name": "sgt-001",
  "verifier_result": {
    "rewards": {
      "reward": 0.85
    }
  },
  "exception_info": null,
  "started_at": "2026-02-01T12:00:00Z",
  "finished_at": "2026-02-01T12:15:00Z",
  "agent_info": {
    "name": "claude-code",
    "model_info": {
      "name": "anthropic/claude-opus-4-6"
    }
  },
  "agent_result": {
    "n_input_tokens": 150000,
    "n_output_tokens": 25000
  }
}
```

See `schemas/result.schema.json` for the formal schema.

### Trace and transcript locations

Harbor writes each task trial under a **task trial directory**. The pipeline expects the agent trace and transcript in that directory’s `agent/` subdir.

**Directory layout (per run):**

```
<jobs_dir>/<config>/<timestamp>/<task_id>__<trial_id>/
├── result.json          # Harbor result (reward, exception, tokens)
├── config.json
├── exception.txt        # If the run raised
├── trial.log
└── agent/
    ├── trajectory.json       # Primary trace (ATIF v1.2 tool/conversation steps)
    ├── instruction.txt      # Instruction actually sent to the agent
    ├── openhands-code.txt   # OpenHands harness transcript (fallback)
    ├── claude-code.txt      # Claude harness transcript (fallback)
    ├── gemini-code.txt      # Gemini harness transcript (fallback)
    └── setup/               # Setup phase logs
```

**Where the trace is expected:**

| Artifact | Path | Used by |
|----------|------|--------|
| **Trajectory** | `<task_trial_dir>/agent/trajectory.json` | Metrics (tool counts, TTFR/TTAR), audits, failure analysis |
| **Transcript** | `<task_trial_dir>/agent/<harness>-code.txt` or `agent/transcript.jsonl` | Fallback when `trajectory.json` is missing; see `scripts/ccb_metrics/transcript_paths.py` |

Example for one OpenHands trial:

```
runs/staging/openhands_gpt53codex_<timestamp>/baseline/<run_timestamp>/openhands-search-file-test-001__<trial_id>/agent/
```

If the run raises before or during the agent loop (e.g. setup or agent init), Harbor may not write `trajectory.json` or the transcript; validation will report “trajectory.json missing” and metrics will use transcript fallback when available.

## Agent Configurations

CodeContextBench evaluates agents under two MCP (Model Context Protocol) configurations:

### Baseline (`baseline-local-direct`)

The agent uses only its built-in tools:

- **Bash** - Run commands (tests, builds, shell operations)
- **Read** - Read files
- **Edit** - Edit files
- **Grep** - Content search (ripgrep)
- **Glob** - File pattern matching
- **Task** - Launch sub-agents

No external code search tools are available. The agent has full local source code and relies on local tools for code discovery.

### MCP-Full (`mcp-remote-direct`)

The agent receives all 13 Sourcegraph MCP tools for code discovery. Local source code is truncated/empty (via `Dockerfile.sg_only`), forcing reliance on MCP tools:

- `mcp__sourcegraph__keyword_search` - Exact string/regex search across indexed repos
- `mcp__sourcegraph__nls_search` - Natural language semantic search
- `mcp__sourcegraph__deepsearch` - Deep semantic code analysis
- `mcp__sourcegraph__deepsearch_read` - Read Deep Search results
- `mcp__sourcegraph__read_file` - Read files from the Sourcegraph index
- `mcp__sourcegraph__list_files` - Browse directory structure
- `mcp__sourcegraph__list_repos` - Discover available repositories
- `mcp__sourcegraph__go_to_definition` - Jump to symbol definitions
- `mcp__sourcegraph__find_references` - Find all callers/references
- `mcp__sourcegraph__commit_search` - Search commit history
- `mcp__sourcegraph__diff_search` - Search code diffs
- `mcp__sourcegraph__compare_revisions` - Compare revisions
- `mcp__sourcegraph__get_contributor_repos` - Find contributor repositories

All local tools (Grep, Glob, Bash) remain available but return empty/useless results for source files since the workspace is truncated. Deep Search is asynchronous: it returns a polling link, and the agent must call `deepsearch_read` to retrieve results.

See [CONFIGS.md](CONFIGS.md) for the full configuration matrix including artifact evaluation variants.

## Constraints

### Network Access

Varies by task. Most tasks run in Docker containers with full network access for package installation during environment setup. Some tasks (e.g., TAC benchmarks) require network access to external services (RocketChat).

### Resource Limits

Defined in `task.toml` under the `[environment]` section:

```toml
[environment]
build_timeout_sec = 1200.0
```

### Container Environment

Tasks run in Docker containers built from `environment/Dockerfile` in each task directory. The container includes all dependencies needed to build and test the project.

## Minimal Agent Example

A minimal agent that reads the instruction and creates a placeholder file:

```bash
#!/bin/bash
# Read the instruction
cat /workspace/instruction.md

# Make a change (real agents would analyze and implement)
echo "// TODO: implement fix" > /workspace/fix.txt

# Run tests to check
bash /tests/test.sh 2>&1 || true
```

Real agents should:
1. Read and understand the instruction
2. Explore the codebase to locate relevant code
3. Implement the required changes
4. Run the test suite to verify correctness
