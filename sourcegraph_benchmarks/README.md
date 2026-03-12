# MCP-Eval-Tasks

Benchmark tasks automatically mined from [sourcegraph/sourcegraph](https://github.com/sourcegraph/sourcegraph) for evaluating AI coding agents with MCP tools (Sourcegraph code search, Deep Search) against their own codebases.

## How These Tasks Were Created

Tasks are generated using the **`/mine-tasks`** skill from [CodeScaleBench](https://github.com/sourcegraph/CodeScaleBench), an open benchmark for measuring how well AI coding agents leverage code intelligence tools at scale.

### Mining Process

1. **SDLC Task Mining** — Scans merged PRs/MRs (or `git log` when no host API is available). Scores candidates on patch size, test coverage, issue quality, and code complexity. Extracts the pre-fix commit, generates ground truth from the patch, and produces reproducible task environments.

2. **Org-Scale Task Mining** — Analyzes codebase structure for cross-package dependency chains, configuration propagation patterns, API surfaces, security-sensitive code paths, and other patterns that require deep codebase understanding to trace.

3. **Reviewer Discovery** — Identifies MR/PR authors, reviewers, and top contributors per code area using `git log` frequency analysis plus host-specific reviewer APIs when available. Results are stored in `reviewers.json` per task.

4. **Quality Validation** — Each task is scored against the ABC framework (instruction clarity, verifier quality, reproducibility). All tasks in this repo score >= 0.7.

### Oracle Verification

Ground truth (oracle) data is verified using the **Curator Agent** (`scripts/context_retrieval_agent.py` in CodeScaleBench):

- Uses Claude to independently discover the relevant files and symbols for each task
- Runs against Sourcegraph's indexed codebase via MCP tools
- Compares curator output against hand-crafted oracle for F1 scoring
- SDLC tasks achieved **F1 = 1.00** (exact match) on curator validation

## Task Types

### SDLC Tasks (3 tasks)

Agent must reproduce a real code change from a merged PR, starting from the pre-fix commit.

| Task | Suite | Language | Source PR |
|------|-------|----------|-----------|
| sg-gitlab-ratelimit-fix-001 | fix | Go | [#10567](https://github.com/sourcegraph/sourcegraph/pull/10567) |
| sg-deepsearch-imgbomb-fix-001 | secure | Go | [#10512](https://github.com/sourcegraph/sourcegraph/pull/10512) |
| sg-deepsearch-anchor-fix-001 | fix | TypeScript | [#10611](https://github.com/sourcegraph/sourcegraph/pull/10611) |

### Org-Scale Tasks (3 tasks)

Agent must discover and map code patterns across the monorepo, producing a structured `answer.json`.

| Task | Suite | Difficulty | Pattern |
|------|-------|------------|---------|
| ccx-sgauth-301 | compliance | hard | Auth middleware chain + authz providers |
| ccx-sgcompletion-302 | cross-service trace | very_hard | LLM completions request lifecycle |
| ccx-sgencrypt-305 | compliance | medium | Encryption key management audit |

## Task Structure

Each task directory contains:

```
task-name/
  task.toml              # Metadata, verification config, resource limits
  instruction.md         # Task prompt (tool-neutral, no difficulty hint)
  instruction_mcp.md     # Same prompt with MCP tools note
  reviewers.json         # Suggested reviewers from code ownership analysis
  environment/
    Dockerfile           # Reproducible build environment (pinned commits)
  tests/
    test.sh              # Verifier with partial credit scoring
    ground_truth.json    # Expected files (SDLC tasks)
    oracle_answer.json   # Expected files + symbols (org-scale tasks)
    expected/            # Ground truth marker directory
```

## Running Tasks

These tasks are designed to run in the [CodeScaleBench](https://github.com/sourcegraph/CodeScaleBench) harness (Harbor), but the baseline task images are plain Docker environments and should remain runnable outside Harbor as long as the harness respects the task contract.

Each task now publishes a minimal contract through environment variables:

- `TASK_WORKDIR` — canonical workspace directory
- `TASK_REPO_ROOT` — verifier repo root
- `TASK_OUTPUT` — required primary output artifact when the task expects one

To evaluate an agent:

1. Clone this repo into your CodeScaleBench `benchmarks/` directory (or a custom task directory)
2. Build the Docker environment: `docker build -t task-name environment/`
3. Run the agent inside the container with the instruction prompt
4. Execute `tests/test.sh` to compute the reward score (0.0 - 1.0)

## Mining Your Own Tasks

Point `/mine-tasks` at any repo and get a baseline-vs-MCP comparison for your AI coding agents.

### Quick Eval (recommended for first run)

```bash
# Install CodeScaleBench
git clone https://github.com/sourcegraph/CodeScaleBench.git
cd CodeScaleBench

# Run the mine-tasks skill
claude /mine-tasks
# Select the mining mode, provide your repo URL or local path, and review the proposed tasks.
```

The current mining workflow supports:
- quick eval generation for baseline vs MCP comparisons
- full benchmark mining for org-scale tasks, reviewer extraction, and CodeScaleBench task scaffolding
- GitHub, GitLab, Bitbucket, Azure DevOps, Forgejo/Gitea, local repos, and generic `git log` fallback

For contributing tasks back to CodeScaleBench, use full benchmark mining so the generated tasks, reviewers, and metadata are registry-ready from the start.

## License

Task definitions and verification scripts are provided under the same license as the source repository (Apache-2.0 for sourcegraph/sourcegraph).
