# CodeScaleBench-Org Task Templates

Templates for generating Harbor-compatible Org benchmark task directories.
All templates use Python `string.Template` syntax: `$variable` or `${variable}`.
Literal `$` signs in bash code are escaped as `$$`.

## Template Files

| File | Purpose |
|------|---------|
| `task.toml.j2` | Harbor task metadata and verification config |
| `instruction.md.j2` | Agent instruction with customer-framed prompt |
| `eval.sh.j2` | Exit-code-first evaluator calling oracle_checks.py |
| `task_spec.json.j2` | Full TaskSpec (oracle + evaluation checks) |
| `Dockerfile.j2` | Baseline: clones local_checkout_repos |
| `Dockerfile.sg_only.j2` | MCP-Full: no clone, marks /tmp/.sg_only_mode |

## Template Variables

### task.toml.j2

| Variable | Type | Example | Description |
|----------|------|---------|-------------|
| `$task_id` | string | `CCX-dep-trace-001` | Task identifier (CCX-<family>-<NNN>) |
| `$task_description` | string | `Trace blast radius of client-go changes` | Short description |
| `$primary_repo` | string | `kubernetes/kubernetes` | Main local repo (org/name) |
| `$task_family` | string | `cross-repo-dep-trace` | Task family ID from registry |
| `$language` | string | `go` | Primary programming language |
| `$difficulty` | string | `medium` | Task difficulty: easy/medium/hard |
| `$time_limit_sec` | int | `900` | Agent time limit in seconds |
| `$mcp_suite` | string | `csb_org_crossrepo_tracing` | CSB MCP suite name |
| `$use_case_id` | int | `1` | Use case ID from registry (1-100) |
| `$repo_set_id` | string | `kubernetes-ecosystem` | Fixture ID |

### instruction.md.j2

| Variable | Type | Example | Description |
|----------|------|---------|-------------|
| `$task_title` | string | `Kubernetes Dependency Blast Radius` | Human-readable title |
| `$customer_prompt` | string | `Find all repos that import...` | Customer-framed task prompt |
| `$context_description` | string | `You are a platform engineer...` | Background/role context |
| `$local_repo_description` | string | `The local /workspace contains kubernetes/kubernetes` | What's available locally |
| `$mcp_repos_description` | string | `- sg-evals/kubernetes-client-go...` | MCP-only repos bullet list |
| `$evaluation_criteria` | string | `- Recall of affected repos...` | What scoring checks |

### eval.sh.j2

| Variable | Type | Example | Description |
|----------|------|---------|-------------|
| `$task_id` | string | `CCX-dep-trace-001` | Task ID for logging |

### task_spec.json.j2

| Variable | Type | Example | Description |
|----------|------|---------|-------------|
| `$task_id` | string | `CCX-dep-trace-001` | Task identifier |
| `$task_family` | string | `cross-repo-dep-trace` | Task family |
| `$use_case_id` | int | `1` | Use case ID |
| `$category` | string | `A` | Category A-J |
| `$mcp_suite` | string | `csb_org_crossrepo_tracing` | Suite name |
| `$user_story` | string | `As a platform engineer...` | PRD user story |
| `$constraints_json` | JSON array | `["Must cite file paths"]` | Constraint list as JSON string |
| `$success_definition` | string | `Agent identifies all affected repos` | Success criteria |
| `$seed_prompt` | string | `Find all repos importing...` | Curation seed prompt |
| `$repo_set_id` | string | `kubernetes-ecosystem` | Fixture ID |
| `$required_files_json` | JSON array | `[]` | Oracle file list (empty until curated) |
| `$required_symbols_json` | JSON array | `[]` | Oracle symbol list (empty until curated) |
| `$dependency_chains_json` | JSON array | `[]` | Oracle chains (empty until curated) |
| `$evaluation_modes_json` | JSON array | `["deterministic"]` | Evaluation modes |
| `$evaluation_checks_json` | JSON array | `[{"type":"file_set_match",...}]` | Check configurations |

### Dockerfile.j2

| Variable | Type | Example | Description |
|----------|------|---------|-------------|
| `$language_packages` | string | `golang-go` | apt packages for the language |
| `$clone_commands` | string | `RUN git clone...` | Shell commands to clone local repos |

### Dockerfile.sg_only.j2

| Variable | Type | Example | Description |
|----------|------|---------|-------------|
| `$task_id` | string | `CCX-dep-trace-001` | Task ID for Dockerfile comment |

## Generation

Templates are filled by `scripts/generate_mcp_unique_tasks.py`:

```bash
python3 scripts/generate_mcp_unique_tasks.py --use-case-ids 1 --out benchmarks/
python3 scripts/generate_mcp_unique_tasks.py --category A --dry-run
python3 scripts/generate_mcp_unique_tasks.py --all --curate-oracle
```

## Layout

Generated task directories follow:

```
benchmarks/<mcp_suite>/<task_slug>/
├── environment/
│   ├── Dockerfile        (baseline: clones local repos)
│   └── Dockerfile.sg_only
├── tests/
│   ├── eval.sh
│   ├── oracle_checks.py  (copied from scripts/csb_metrics/oracle_checks.py)
│   ├── task_spec.json
│   └── oracle_answer.json (populated by curate_oracle.py)
├── task.toml
└── instruction.md
```
