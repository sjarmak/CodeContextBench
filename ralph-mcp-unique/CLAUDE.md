# Ralph Agent Instructions — MCP-Unique Benchmark Extension

You are an autonomous coding agent working on extending CodeContextBench with MCP-unique org-scale context retrieval tasks.

## Your Task

1. Read the PRD at `ralph-mcp-unique/prd.json` (relative to project root)
2. Read the progress log at `ralph-mcp-unique/progress.txt` (check Codebase Patterns section first)
3. Pick the **highest priority** user story where `passes: false`
4. Implement that single user story
5. Run quality checks (e.g., typecheck, lint, test - use whatever your project requires)
6. Update CLAUDE.md files if you discover reusable patterns
7. If checks pass, commit ALL changes to `main` with message: `feat: [Story ID] - [Story Title]`
8. Update the PRD to set `passes: true` for the completed story
9. Append your progress to `ralph-mcp-unique/progress.txt`

## Key Architecture Context

This extension adds an "MCP-unique / org-scale context retrieval" layer to CodeContextBench:

- **Use Case Registry** (`configs/use_case_registry.json`): 100 GTM use cases with metadata
- **Repo-Set Fixtures** (`fixtures/repo_sets/*.json`): define which repos are local vs MCP-only
- **Task Generator** (`scripts/generate_mcp_unique_tasks.py`): creates tasks from registry + fixtures
- **Oracle Checks** (`scripts/ccb_metrics/oracle_checks.py`): deterministic eval library
- **Retrieval Metrics** (`scripts/ccb_metrics/retrieval.py`): MCP context retrieval KPIs
- **Validity Gate** (`scripts/validate_mcp_task_instance.py`): SWE-Factory fail2pass pattern

### Design Principles
- **Exit-code-first** (SWE-Factory): every eval.sh returns exit 0/1, no custom log parsers
- **PRD-centered** (PRDBench): each task has explicit criteria JSON used by grader
- **Deterministic by default**: rubric-judge behind opt-in flag only
- **Polyrepo fixtures**: baseline has limited local access; MCP has full Sourcegraph access

### Existing Infrastructure to Reuse
- task.toml format: `benchmarks/ccb_*/task_name/task.toml`
- Dockerfile patterns: baseline + Dockerfile.sg_only (see `scripts/generate_sgonly_dockerfiles.py`)
- LLM judge pipeline: `scripts/run_judge.py` + `scripts/ccb_metrics/judge/`
- Harbor runner: `configs/_common.sh`, `configs/run_selected_tasks.sh`
- Selection registry: `configs/selected_benchmark_tasks.json`

## Progress Report Format

APPEND to ralph-mcp-unique/progress.txt (never replace, always append):
```
## [Date/Time] - [Story ID]
- What was implemented
- Files changed
- **Learnings for future iterations:**
  - Patterns discovered
  - Gotchas encountered
  - Useful context
---
```

## Quality Requirements

- ALL commits must pass quality checks (typecheck, lint, test)
- All Python files: `python3 -m py_compile <file>`
- All bash scripts: `bash -n <file>`
- All JSON files: `python3 -c "import json; json.load(open('<file>'))"`
- All JSON schemas: validate against themselves
- Do NOT commit broken code
- Follow existing CCB patterns (task.toml format, Dockerfile conventions, Harbor compatibility)

## Important Constraints

- **Harbor compatibility**: All tasks must produce result.json with standard reward format
- **Verifier path**: tests/ uploaded to `/tests/` in container, use `/tests/eval.sh` not `/workspace/tests/eval.sh`
- **sg_only mode**: Use `/tmp/.sg_only_mode` marker, see existing Dockerfile.sg_only patterns
- **Build context**: Dockerfile build context is `environment/` dir, not task root
- **No external deps**: oracle_checks.py must be stdlib-only Python (json, re, pathlib, sys)
- **Real SG repos**: All repos in fixtures must be actually indexed in Sourcegraph

## Stop Condition

After completing a user story, check if ALL stories have `passes: true`.

If ALL stories are complete and passing, reply with:
<promise>COMPLETE</promise>

If there are still stories with `passes: false`, end your response normally.

## Git Policy

- **All work happens on `main`** — do NOT create feature branches
- Never run `git checkout -b` or `git switch -c` — commit directly to `main`
- This avoids cross-session branch confusion when multiple agents work on the repo

## Important

- Work on ONE story per iteration
- Commit frequently
- Keep CI green
- Read the Codebase Patterns section in ralph-mcp-unique/progress.txt before starting
