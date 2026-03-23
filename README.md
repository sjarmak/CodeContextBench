# CodeScaleBench

Benchmark suite for evaluating how AI coding agents leverage external context retrieval tools on realistic developer tasks in large, enterprise-scale codebases.

This repository contains:
- **275 benchmark tasks** across 20 suites covering 9 developer work types
- **Versioned benchmark suites** with dual-verifier support (`benchmarks/suites/`)
- **Auditable results snapshots** with per-task traces, scores, timing, and cost (`runs/snapshots/`)
- **Metrics extraction and reporting pipelines** for score/cost/retrieval analysis
- **Task indexes** by complexity, language, repo size, and multi-repo scope (`benchmarks/indexes/`)

Tasks are executed via the [Harbor](https://github.com/laude-institute/harbor/tree/main) runner with the Claude Code agent harness.

---

## Results

Official results are available as frozen, auditable snapshots in [`runs/snapshots/`](runs/snapshots/).

| Snapshot | Tasks | Model | Configs | Mean Reward |
|----------|------:|-------|---------|:-----------:|
| `csb-v1-mixed371--haiku45--030326` | 371 | Haiku 4.5 | Baseline, Sourcegraph MCP | 0.536 / 0.565 |

Each snapshot includes:
- `browse.html` — Interactive results browser (open in any web browser)
- `SNAPSHOT.json` — Machine-readable manifest
- `export/traces/` — Per-task result metadata, reward scores, agent instructions
- `export/summary/` — Aggregate scores, timing, cost breakdowns

Full agent trajectories are available as compressed archives in the corresponding [GitHub Release](https://github.com/sourcegraph/CodeScaleBench/releases).

---

## Benchmark Suites

Suite definitions in [`benchmarks/suites/`](benchmarks/suites/) specify exactly which tasks are in each benchmark version:

| Suite | Tasks | Description |
|-------|------:|-------------|
| `csb-v1-mixed371` | 371 | Initial report: mixed verifiers, 151 SDLC + 220 org tasks |
| `csb-v2-dual264` | 264 | Canonical: all dual-verifier tasks |
| `csb-v2-full-validated` | 275 | Complete: all validated tasks including Daytona-excluded |

Task indexes in [`benchmarks/indexes/`](benchmarks/indexes/) provide views by:
- **Complexity** — scored by repo size, repo count, GT files, difficulty
- **Language** — 13 languages (Go, C++, Java, Python, Rust, C#, JS, TS, ...)
- **Repo size** — small (<100MB) through xlarge (>5GB)
- **Multi-repo** — 136 multi-repo tasks across 28 repo sets

---

## Task Taxonomy

All tasks represent realistic developer work in large, often multi-repo, enterprise codebases. Tasks are organized by **developer work type**.

| Work Type | Tasks | Description | Repo Scope |
|-----------|------:|-------------|------------|
| **crossrepo** | 47 | Cross-repo navigation, dependency tracing, org-wide discovery | 18 single, 9 dual, 20 multi |
| **understand** | 44 | Codebase comprehension, architecture, onboarding, domain knowledge | 36 single, 4 dual, 4 multi |
| **refactor** | 43 | Code transformation, migration, dependency updates | 26 single, 2 dual, 15 multi |
| **security** | 39 | Security review, vulnerability remediation, compliance audit | 26 single, 2 dual, 11 multi |
| **feature** | 34 | Feature implementation, org-wide feature work | 24 single, 2 dual, 8 multi |
| **debug** | 26 | Debugging, root cause analysis, incident triage | 15 single, 8 dual, 3 multi |
| **fix** | 19 | Bug repair from issue reports | 19 single |
| **test** | 12 | Test generation, code review, QA | 12 single |
| **document** | 11 | API docs, architecture docs, migration guides | 10 single, 1 dual |
| **Total** | **275** | | 186 single, 28 dual, 61 multi |

---

## Evaluation Configurations

Tasks are evaluated across multiple MCP configurations to measure the impact of external code retrieval tools:

| Config | Code Access | MCP Tools |
|--------|-------------|-----------|
| `baseline-local-direct` | Full local code | None (built-in tools only) |
| `mcp-remote-direct` | Remote only (Sourcegraph) | keyword_search, nls_search, read_file, find_references, go_to_definition, ... |
| `augment-local-direct` | Full local code | Augment Context Engine (`codebase-retrieval`) |
| `github-remote-direct` | Remote only (GitHub API) | search_code, get_file_contents, get_repository_tree, ... |

---

## Repository Structure

```
benchmarks/
  suites/                # Versioned benchmark suite definitions (JSON)
  indexes/               # Task indexes by complexity, language, repo size, multi-repo
  tasks/                 # 275 task definitions across 20 suite directories
    csb_sdlc_feature/    #   Feature implementation (23 tasks)
    csb_sdlc_fix/        #   Bug repair (19 tasks)
    csb_org_migration/   #   Framework migration (25 tasks)
    ...                  #   (20 suites total)
runs/
  snapshots/             # Frozen, auditable result snapshots
    {snapshot_id}/
      SNAPSHOT.json      #   Manifest: suite, model, configs, aggregates
      browse.html        #   Interactive results browser
      export/            #   Sanitized traces for public consumption
scripts/                 # Metrics extraction, evaluation, and operational tooling
  publishing/            #   Snapshot creation, verification, export
  evaluation/            #   IR metrics, retrieval analysis, judge pipelines
  csb_metrics/           #   Python package: models, extractors, discovery
docs/
  technical_reports/     # Published technical reports
  official_results/      # Pointer to runs/snapshots/
```

---

## Quickstart

```bash
git clone https://github.com/sourcegraph/CodeScaleBench.git
cd CodeScaleBench

# Browse benchmark suites
cat benchmarks/suites/csb-v2-dual264.json | python3 -m json.tool | head -20

# Explore task indexes
cat benchmarks/indexes/by-complexity.json | python3 -m json.tool | head -30

# Open results browser
open runs/snapshots/csb-v1-mixed371--haiku45--030326/browse.html
```

### Running benchmarks (requires Harbor)

```bash
# Pre-flight checks
python3 scripts/infra/check_infra.py

# Run canonical suite
./configs/harnesses/run_selected_tasks.sh \
  --suite-file benchmarks/suites/csb-v2-dual264.json
```

---

## Quality Assurance

CodeScaleBench includes a multi-stage QA pipeline:

| Phase | Script | Purpose |
|-------|--------|---------|
| **Pre-flight** | `scripts/authoring/validate_tasks_preflight.py` | Task integrity checks |
| **Infra check** | `scripts/infra/check_infra.py` | OAuth tokens, Docker, disk |
| **Post-run** | `scripts/authoring/validate_task_run.py` | Scoring anomalies, MCP usage |
| **Snapshot verify** | `scripts/publishing/verify_snapshot.py` | Symlink integrity, completeness |

---

## License

See [LICENSE](LICENSE).
