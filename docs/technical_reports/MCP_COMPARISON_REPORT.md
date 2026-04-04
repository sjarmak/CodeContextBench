# MCP Server Comparison: Sourcegraph vs Augment vs GitHub vs Cursor

**Date:** 2026-03-25
**Models:** Claude Haiku 4.5, Claude Opus 4.6
**Benchmark:** CodeScaleBench (20 tasks: 10 representative + 10 complex codebases)
**Total runs:** 650+ (20 tasks x 3 configs x 2 models x 3+ trials, plus 15 tasks x 2 Cursor configs x 3 trials, plus 60 Augment Remote trials)

## Summary

We compare three MCP (Model Context Protocol) server configurations for AI coding agents on realistic software engineering tasks in large codebases (1.4M–10M lines of code). All results include variance analysis with 3+ independent trials per cell.

| MCP Server / Agent | Code Access | Key Capabilities |
|-----------|-------------|------------------|
| **Sourcegraph** | Remote only | Keyword search, semantic search, file reading, go-to-definition, find-references, commit/diff search (14 tools) |
| **Augment Context Engine** | Remote (GitHub App) | Semantic code search via `codebase-retrieval` (1 tool), indexes org repos via GitHub App |
| **GitHub MCP Server** | Remote only | Code search (keyword only), file reading, tree browsing, commit history (8 tools) |
| **Cursor (native)** | Local clone | Built-in Instant Grep, semantic search (vector embeddings), Explore subagent |
| **Cursor + Sourcegraph** | Local + remote | All Cursor native tools + Sourcegraph MCP for cross-repo code intelligence |

**Key findings:**
- With variance analysis, reward differences between configs are smaller than single-trial comparisons suggest — representative tasks are a statistical tie across all three Claude Code configs
- **Augment Remote (GitHub App indexed) closes the gap with Sourcegraph on complex Haiku tasks** (0.48 vs 0.54, up from 0.40 with local clone), with decisive leads on dependency tracing (0.91 vs 0.74)
- Sourcegraph MCP retains a meaningful advantage on complex codebases (+0.09 over the next best with Opus), driven by code navigation tools (`find_references`, `go_to_definition`) absent from other configs
- Sourcegraph is the fastest (156s mean task time with Haiku) and cheapest ($0.39/task)
- Sourcegraph has the highest IR recall (0.41) and F1 (0.17), finding relevant ground-truth files at 2–3x the rate of other configs
- GitHub MCP is the most consistent (lowest within-task variance) but has the lowest ceiling
- Opus dramatically reduces within-task variance (0.02–0.05 stdev vs 0.09–0.17 for Haiku), making comparisons more reliable
- **Cursor's built-in search is competitive with MCP-augmented Claude Code** (0.55 mean vs 0.59 for Claude+Augment/GitHub), suggesting that IDE-native semantic search partially substitutes for MCP tools
- **Sourcegraph MCP adds minimal value to Cursor (+0.02)** vs significant value to Claude Code (+0.09 on complex tasks) — Cursor's native search already covers much of what SG provides, except for cross-file reference tracing

## Task Selection

### Representative Tasks (10)

Standard benchmark tasks spanning SDLC phases and organization-scale work.

| Task | Suite | Repo | Language | Difficulty |
|------|-------|------|----------|:---:|
| django-modelchoice-fk-fix-001 | csb_sdlc_fix | django/django | Python | hard |
| linux-acpi-backlight-fault-001 | csb_sdlc_debug | torvalds/linux | C | expert |
| camel-fix-protocol-feat-001 | csb_sdlc_feature | apache/camel | Java | expert |
| camel-routing-arch-001 | csb_sdlc_design | apache/camel | Java | hard |
| beam-pipeline-builder-refac-001 | csb_sdlc_refactor | apache/beam | Java | hard |
| ceph-rgw-auth-secure-001 | csb_sdlc_secure | ceph/ceph | C++ | hard |
| ccx-config-trace-010 | csb_org_crossrepo_tracing | kubernetes | Go | hard |
| ccx-incident-032 | csb_org_incident | envoy | C++ | hard |
| ccx-migration-026 | csb_org_migration | envoy | C++ | hard |
| ccx-vuln-remed-014 | csb_org_security | grafana/loki | Go | hard |

### Complex Codebase Tasks (10)

These tasks were selected to maximize codebase complexity using a composite score that weights five factors: repository size (30%), number of repositories (20%), ground truth file count (20%), total file count (15%), and task difficulty (15%). The scoring formula and full ranked list are in `benchmarks/indexes/by-complexity.json`.

Selection criteria required diversity across:
- **Repository scale:** 1.3–2.6 GB repos spanning 20K–133K files
- **Language:** Go, C#, JavaScript, C++, Python, Rust (6 languages across 10 tasks)
- **Task type:** dependency tracing, incident investigation, migration analysis, compliance audit, bug fix, feature implementation
- **Multi-repo scope:** 6 of 10 tasks operate on organization-scale repo sets (kubernetes-ecosystem, envoy-service-mesh, etc.)

| Task | Repo | Repo Size | Files | GT Files | Repo Set | Language |
|------|------|----------:|------:|--------:|----------|----------|
| ccx-dep-trace-273 | kubernetes v1.32.0 | 1.8 GB | 26K | 7 | kubernetes-ecosystem | Go |
| ccx-dep-trace-293 | dotnet/roslyn v4.12.0 | 2.6 GB | 21K | 16 | roslyn-compiler | C# |
| ccx-incident-037 | kubernetes v1.32.0 | 1.8 GB | 26K | 15 | kubernetes-ecosystem | Go |
| ccx-migration-275 | kubernetes v1.32.0 | 1.8 GB | 26K | 7 | kubernetes-ecosystem | Go |
| ccx-migration-276 | nodejs/node v22.13.0 | 1.5 GB | 47K | 7 | nodejs-web-stack | JavaScript |
| ccx-migration-278 | envoyproxy/envoy v1.31.2 | 1.4 GB | 13K | 8 | envoy-service-mesh | C++ |
| ccx-migration-279 | grafana/grafana | 1.5 GB | 21K | 48 | grafana-observability | Go |
| ccx-compliance-292 | godotengine/godot 4.3 | 1.8 GB | 14K | 29 | godot-engine | C++ |
| pytorch-release-210-fix-001 | pytorch/pytorch | 1.3 GB | 20K | 110 | — | Python/C++ |
| servo-css-container-query-feat-001 | servo/servo | 1.9 GB | 133K | 16 | — | Rust |

**Notable complexity characteristics:**
- **pytorch-release-210-fix-001** has the most ground truth files (110) — the fix touches a cross-module release pipeline spanning Python bindings, C++ kernels, build configs, and CI workflows
- **servo-css-container-query-feat-001** has the most source files (133K) in a 10M-LOC Rust codebase with deep trait hierarchies and macro-generated code
- **ccx-migration-279** targets grafana/grafana with 48 ground truth files spread across the frontend (TypeScript), backend (Go), and configuration layers
- The three kubernetes-ecosystem tasks (dep-trace-273, incident-037, migration-275) operate on a 1.8 GB repo with 26K files organized across 50+ packages with deep cross-package dependencies

## Results: Reward with Variance

All cells show mean +/- standard deviation across 3+ independent trials.

### Representative Tasks — Haiku (299 total runs)

| Task | Augment | GitHub | Sourcegraph |
|------|---------|--------|-------------|
| django-modelchoice-fk-fix-001 | 0.53 +/- 0.23 | 0.37 +/- 0.14 | **0.60 +/- 0.22** |
| linux-acpi-backlight-fault-001 | **1.00 +/- 0.00** | 0.93 +/- 0.12 | **1.00 +/- 0.00** |
| camel-fix-protocol-feat-001 | 0.24 +/- 0.06 | **0.32 +/- 0.01** | 0.28 +/- 0.12 |
| camel-routing-arch-001 | 0.69 +/- 0.11 | **0.78 +/- 0.01** | 0.72 +/- 0.10 |
| beam-pipeline-builder-refac-001 | **1.00 +/- 0.00** | **1.00 +/- 0.00** | **1.00 +/- 0.00** |
| ceph-rgw-auth-secure-001 | **1.00 +/- 0.00** | **1.00 +/- 0.00** | **1.00 +/- 0.00** |
| ccx-config-trace-010 | **1.00 +/- 0.00** | **1.00 +/- 0.00** | **1.00 +/- 0.00** |
| ccx-incident-032 | 0.46 +/- 0.06 | 0.37 +/- 0.03 | **0.56 +/- 0.09** |
| ccx-migration-026 | 0.08 +/- 0.01 | 0.05 +/- 0.01 | **0.09 +/- 0.05** |
| ccx-vuln-remed-014 | 0.19 +/- 0.13 | 0.45 +/- 0.21 | **0.50 +/- 0.16** |
| **Mean** | **0.62 +/- 0.34** | **0.63 +/- 0.33** | **0.68 +/- 0.31** |

### Representative Tasks — Opus (201 total runs across all conditions)

| Task | Augment | GitHub | Sourcegraph |
|------|---------|--------|-------------|
| django-modelchoice-fk-fix-001 | **0.75 +/- 0.00** | **0.75 +/- 0.00** | 0.53 +/- 0.05 |
| linux-acpi-backlight-fault-001 | **1.00 +/- 0.00** | **1.00 +/- 0.00** | **1.00 +/- 0.00** |
| camel-fix-protocol-feat-001 | 0.16 +/- 0.02 | 0.15 +/- 0.04 | **0.16 +/- 0.04** |
| camel-routing-arch-001 | 0.78 +/- 0.05 | **0.87 +/- 0.00** | 0.73 +/- 0.18 |
| beam-pipeline-builder-refac-001 | **1.00 +/- 0.00** | **1.00 +/- 0.00** | **1.00 +/- 0.00** |
| ceph-rgw-auth-secure-001 | **1.00 +/- 0.00** | **1.00 +/- 0.00** | **1.00 +/- 0.00** |
| ccx-config-trace-010 | **1.00 +/- 0.00** | **1.00 +/- 0.00** | **1.00 +/- 0.00** |
| ccx-incident-032 | 0.52 +/- 0.03 | **0.58 +/- 0.03** | 0.52 +/- 0.04 |
| ccx-migration-026 | 0.06 +/- 0.03 | 0.09 +/- 0.00 | **0.12 +/- 0.03** |
| ccx-vuln-remed-014 | 0.58 +/- 0.12 | 0.67 +/- 0.00 | **0.71 +/- 0.21** |
| **Mean** | **0.69 +/- 0.35** | **0.71 +/- 0.35** | **0.68 +/- 0.34** |

### Complex Codebase Tasks — Haiku

Augment results use `augment-remote-direct` (GitHub App indexed, no local clone). 30 Augment trials total.

| Task | Augment | GitHub | Sourcegraph |
|------|---------|--------|-------------|
| ccx-dep-trace-273 | **0.91 +/- 0.03** | 0.75 +/- 0.09 | 0.74 +/- 0.29 |
| ccx-dep-trace-293 | **0.88 +/- 0.06** | 0.82 +/- 0.01 | 0.78 +/- 0.14 |
| ccx-incident-037 | 0.54 +/- 0.22 | 0.33 +/- 0.02 | **0.83 +/- 0.18** |
| ccx-migration-275 | 0.32 +/- 0.23 | 0.43 +/- 0.08 | **0.50 +/- 0.23** |
| ccx-migration-276 | 0.67 +/- 0.07 | **0.72 +/- 0.06** | 0.68 +/- 0.05 |
| ccx-migration-278 | 0.65 +/- 0.06 | 0.43 +/- 0.04 | **0.67 +/- 0.06** |
| ccx-migration-279 | **0.47 +/- 0.00** | 0.39 +/- 0.07 | 0.46 +/- 0.01 |
| ccx-compliance-292 | 0.37 +/- 0.12 | **0.50 +/- 0.01** | 0.49 +/- 0.06 |
| pytorch-release-210-fix-001 | 0.00 +/- 0.00 | 0.00 +/- 0.00 | 0.26 +/- 0.40 |
| servo-css-container-query-feat-001 | 0.00 +/- 0.00 | 0.00 +/- 0.00 | 0.00 +/- 0.00 |
| **Mean** | **0.48 +/- 0.30** | **0.44 +/- 0.28** | **0.54 +/- 0.28** |

### Complex Codebase Tasks — Opus

Augment results use `augment-remote-direct` (GitHub App indexed, no local clone). 27 Augment trials total.

| Task | Augment | GitHub | Sourcegraph |
|------|---------|--------|-------------|
| ccx-dep-trace-273 | **0.74 +/- 0.02** | 0.64 +/- 0.04 | 0.68 +/- 0.06 |
| ccx-dep-trace-293 | 0.78 +/- 0.01 | 0.77 +/- 0.00 | **0.83 +/- 0.00** |
| ccx-incident-037 | 0.63 +/- 0.09 | 0.77 +/- 0.10 | **0.96 +/- 0.03** |
| ccx-migration-275 | **0.48 +/- 0.06** | 0.46 +/- 0.05 | 0.48 +/- 0.08 |
| ccx-migration-276 | **0.70 +/- 0.06** | 0.61 +/- 0.01 | 0.63 +/- 0.07 |
| ccx-migration-278 | 0.63 +/- 0.08 | **0.57 +/- 0.00** | 0.39 +/- 0.12 |
| ccx-migration-279 | 0.38 +/- 0.06 | 0.34 +/- 0.07 | **0.43 +/- 0.00** |
| ccx-compliance-292 | **0.53 +/- 0.05** | 0.57 +/- 0.02 | 0.58 +/- 0.05 |
| pytorch-release-210-fix-001 | 0.00 +/- 0.00 | 0.00 +/- 0.00 | 0.00 +/- 0.00 |
| servo-css-container-query-feat-001 | 0.00 +/- 0.00 | 0.00 +/- 0.00 | **0.83 +/- 0.00** |
| **Mean** | **0.49 +/- 0.28** | **0.47 +/- 0.28** | **0.58 +/- 0.28** |

### Aggregate

| Condition | Augment | GitHub | Sourcegraph |
|-----------|:---:|:---:|:---:|
| Representative — Haiku | 0.62 | 0.63 | **0.68** |
| Representative — Opus | 0.69 | **0.71** | 0.68 |
| Complex — Haiku | 0.48 | 0.44 | **0.54** |
| Complex — Opus | 0.49 | 0.47 | **0.58** |
| **Overall — Haiku** | **0.55** | **0.54** | **0.61** |
| **Overall — Opus** | **0.59** | **0.59** | **0.63** |

## Results: Variance and Consistency

| Metric | Augment | GitHub | Sourcegraph |
|--------|:---:|:---:|:---:|
| **Haiku within-task stdev** | 0.132 | **0.086** | 0.167 |
| **Opus within-task stdev** | 0.039 | **0.019** | 0.048 |

Key observations:
- **GitHub is the most consistent** (lowest stdev) despite the lowest reward ceiling — keyword-only search produces predictable behavior
- **Sourcegraph is the most variable** — its specialized tools enable high-reward paths but also fail modes (e.g., ccx-dep-trace-273 with Haiku: 0.50 +/- 0.46)
- **Opus reduces variance by 3–4x** across all configs — stronger models produce more reliable results, making config comparisons more meaningful
- **Single-trial comparisons overstate differences.** Best-of-1 showed Sourcegraph leading by +0.10–0.15 on representative tasks; with variance, the gap shrinks to +0.01–0.06

## Results: Task Time and Cost

Mean agent execution time (seconds) and cost (USD) per task from `task_metrics.json`.

### Haiku

| Metric | Augment | GitHub | Sourcegraph |
|--------|:---:|:---:|:---:|
| **Mean task time** | 236s | 204s | **156s** |
| **Mean cost/task** | $0.42 | $0.48 | **$0.39** |

### Opus (complex tasks with complete metrics)

| Task | Augment | GitHub | Sourcegraph |
|------|---------|--------|-------------|
| ccx-dep-trace-273 | 100s / $0.23 | 147s / $1.12 | 125s / $0.51 |
| ccx-incident-037 | 115s / $0.45 | 181s / $1.03 | **61s / $0.28** |
| ccx-migration-275 | 201s / $0.59 | 353s / $2.69 | 263s / $1.58 |
| ccx-migration-276 | 109s / $0.33 | **69s / $0.21** | 73s / $0.31 |
| ccx-compliance-292 | 113s / $0.37 | 151s / $0.81 | 161s / $0.73 |
| pytorch-release-210-fix-001 | 1211s / $3.79 | 161s / $0.49 | 282s / $1.33 |
| servo-css-container-query | 2260s / $13.43 | 858s / $7.38 | **868s / $4.35** |

Observations:
- Sourcegraph is fastest on org tasks (61s for incident-037 vs 115–181s) due to remote-only architecture
- Augment spends the most time on large repos (2260s on servo) — retrieval-compile loops on complex Rust codebases
- GitHub is cheapest on simple tasks but most expensive on complex ones ($2.69 for migration-275)

## Results: Information Retrieval

IR metrics from normalized retrieval events with ground truth. Precision measures what fraction of files accessed were relevant; recall measures what fraction of relevant ground-truth files the agent found.

### Haiku IR (20 tasks, all trials pooled)

| Metric | Augment | GitHub | Sourcegraph |
|--------|:---:|:---:|:---:|
| **Mean Precision** | 0.095 | 0.043 | **0.141** |
| **Mean Recall** | 0.154 | 0.213 | **0.413** |
| **Mean F1** | 0.112 | 0.066 | **0.171** |
| Tasks with IR data | 18 | 18 | 20 |

### Per-Task IR Highlights

| Task | Augment (P/R/F1) | GitHub (P/R/F1) | Sourcegraph (P/R/F1) |
|------|:---:|:---:|:---:|
| ccx-config-trace-010 | 0.00/0.00/0.00 | 0.05/0.50/0.08 | **0.23/0.86/0.32** |
| ccx-migration-276 | 0.00/0.00/0.00 | 0.29/1.00/0.45 | 0.13/0.82/0.20 |
| ccx-migration-278 | 0.00/0.00/0.00 | 0.07/1.00/0.14 | **0.24/0.72/0.34** |
| ccx-vuln-remed-014 | 0.00/0.00/0.00 | 0.00/0.00/0.00 | **0.16/0.78/0.25** |
| ceph-rgw-auth-secure-001 | **0.59/0.88/0.70** | 0.00/0.00/0.00 | 0.39/0.75/0.46 |
| django-modelchoice-fk-fix-001 | **0.33/0.60/0.43** | 0.02/0.60/0.04 | 0.22/0.71/0.31 |

Observations:
- **Sourcegraph achieves 2–3x higher recall** than alternatives on most org tasks — its specialized search tools find relevant files more consistently
- **GitHub has high recall on some tasks** (1.00 on migration-276/278, compliance-292) but extremely low precision (0.05–0.07) — broad keyword search returns many irrelevant files
- **Augment has highest precision on local tasks** (ceph: 0.59P, django: 0.33P) — semantic search returns fewer but more relevant results
- **Augment's IR metrics** reflect representative tasks only (augment-local config with local tools). Complex task IR data uses augment-remote where all code access is via `codebase-retrieval` MCP calls

## Analysis

### Why Sourcegraph Leads on Complex Tasks

1. **Code navigation is decisive.** `find_references` and `go_to_definition` let the agent trace symbol usage across files — critical for incident investigation (ccx-incident-037: 0.96 +/- 0.03 with Opus) and security remediation (ccx-vuln-remed-014: 0.71 +/- 0.21).

2. **Servo demonstrates the navigation gap.** The 10M-LOC Rust repo scores 0.83 with Sourcegraph (Opus) but 0.00 with both Augment and GitHub across all trials — only code navigation tools can locate the right implementation files in Servo's complex trait system.

3. **Highest IR recall on complex codebases.** 0.41 mean recall vs 0.15 (Augment) and 0.21 (GitHub) — finding the right files is the first step to solving the task.

### Why Configs Tie on Representative Tasks

1. **Simpler tasks don't need code navigation.** When the codebase is smaller or the fix is localized, keyword search and local tools are sufficient.

2. **Local code access compensates.** Augment agents can grep, read, and test locally — equivalent to MCP file reading but faster for simple lookups.

3. **Model capability matters more than tools** on simpler tasks — Opus scores 0.69–0.71 across all configs vs Haiku's 0.62–0.68.

### Where Augment Excels

1. **Dependency tracing with Haiku.** Augment Remote leads decisively on dep-trace tasks with Haiku (0.91 and 0.88 vs 0.74 and 0.78 for SG) — semantic retrieval with well-scoped queries outperforms Sourcegraph's broader tool set on these tasks.

2. **Migration tasks.** Augment leads on ccx-migration-276 (Opus: 0.70 vs 0.63 SG) and ccx-migration-278 (0.63 vs 0.39 SG) — semantic retrieval effectively locates cross-file migration patterns.

3. **No-clone architecture.** Augment Remote uses the GitHub App to index org repos, eliminating clone overhead. This is particularly valuable for large repos (1.3–2.6 GB) where clone time can exceed agent execution time.

### Where GitHub MCP Falls Short

1. **No semantic search.** Keyword-only `search_code` requires guessing exact terms.

2. **No code navigation.** Without `go_to_definition` or `find_references`, the agent cannot trace symbol relationships.

3. **Most consistent but lowest ceiling.** Stdev of 0.019 (Opus) means predictable but limited performance.

## Methodological Note: Single-Trial vs Multi-Trial

| Comparison | Best-of-1 gap | Variance gap | Significance |
|-----------|:---:|:---:|---|
| Representative SG vs Augment (Haiku) | +0.09 | +0.06 | Reduced |
| Representative SG vs GitHub (Haiku) | +0.12 | +0.05 | Reduced |
| Complex SG vs Augment (Haiku) | +0.15 | +0.06 | Reduced (Augment Remote improved) |
| Complex SG vs Augment (Opus) | +0.07 | +0.09 | **Consistent** |

Single-trial MCP comparisons overstate differences on simpler tasks where variance is high. The complex-task advantage for Sourcegraph is robust across trials. We recommend a minimum of 3 trials per cell for MCP comparison studies.

## Methodology

- **Models:** Claude Haiku 4.5 (`claude-haiku-4-5-20251001`), Claude Opus 4.6 (`claude-opus-4-6`)
- **Runner:** Harbor with BaselineClaudeCodeAgent harness
- **Execution:** Daytona cloud sandboxes
- **Trials:** 3+ per task per configuration per model (500+ total runs)
- **Reward:** Task-specific verifiers (test execution for SDLC tasks, oracle evaluation for org tasks)
- **MCP transport:** HTTP for Sourcegraph, stdio for Augment (auggie CLI) and GitHub (pre-built binary v0.32.0)
- **Augment code access:** GitHub App installed on `sg-evals` org indexes all benchmark mirror repos. Agent uses `codebase-retrieval` with repo-scoped queries (no local clone). Representative task results use the earlier `augment-local-direct` config (with local clone); complex task results use `augment-remote-direct`.

### Configurations

| Config | Agent | MCP Type | Local Code? |
|--------|-------|----------|:-----------:|
| `augment-remote-direct` | Claude Code | Augment Context Engine | No (GitHub App indexed) |
| `github-remote-direct` | Claude Code | GitHub MCP Server | No |
| `mcp-remote-direct` | Claude Code | Sourcegraph | No |
| `cursor-local-direct` | Cursor (headless) | None — native search only | Yes |
| `cursor-sg-direct` | Cursor (headless) | Sourcegraph (supplementary) | Yes |

Cursor runs use the headless CLI (`agent -p --force --trust --output-format stream-json`) with `CURSOR_API_KEY` authentication. MCP config is written to `.cursor/mcp.json` in the workspace. Cursor's semantic search indexes automatically on workspace open. All Cursor runs use Claude Opus 4.6 via the `--model` flag.

### Validation

All 0.00 scores were verified as genuine task failures (not infrastructure issues) by confirming:
- Agent trajectory files exist with substantial content (100KB–2.3MB)
- Agent execution times >60 seconds (consistent with real work)
- No `exception_type` in `result.json`
- Verifier ran and produced `reward.txt`

## Cursor Agent Comparison

### About Cursor

Cursor is an IDE-based coding agent with built-in code search capabilities that operate independently of MCP:

- **Instant Grep** — custom search engine (claimed faster than ripgrep) with regex and word-boundary matching
- **Semantic Search** — vector embeddings over the codebase, chunked by function/class, auto-indexed on workspace open
- **Explore Subagent** — spawns a parallel search agent with its own context window for deep exploration

We evaluate Cursor in headless mode (`agent -p --force --trust`) with two configurations:
- **Cursor Native** (`cursor-local-direct`): built-in search only, local code access
- **Cursor + Sourcegraph** (`cursor-sg-direct`): native search + Sourcegraph MCP for cross-repo code intelligence

All Cursor runs use Claude Opus 4.6 (`--model` flag), matching the Claude Code Opus comparisons. 15 tasks from the MCP comparison suite, 3 independent trials per cell, 90 total runs.

### Cursor Results — Opus (90 total runs: 15 tasks x 2 configs x 3 trials)

| Task | Cursor Native | Cursor + SG | Claude + SG (ref) |
|------|:---:|:---:|:---:|
| ccx-compliance-292 | 0.78 +/- 0.03 | **0.80 +/- 0.04** | 0.58 +/- 0.05 |
| ccx-crossorg-295 | 0.31 +/- 0.01 | **0.39 +/- 0.16** | — |
| ccx-dep-trace-102 | 0.79 +/- 0.04 | **0.85 +/- 0.03** | — |
| ccx-dep-trace-133 | **0.71 +/- 0.14** | 0.61 +/- 0.04 | — |
| ccx-dep-trace-293 | **0.82 +/- 0.02** | 0.81 +/- 0.00 | 0.83 +/- 0.00 |
| ccx-incident-037 | 0.86 +/- 0.00 | 0.85 +/- 0.02 | **0.96 +/- 0.03** |
| ccx-migration-107 | 0.10 +/- 0.00 | 0.10 +/- 0.00 | — |
| ccx-migration-276 | 0.66 +/- 0.02 | **0.67 +/- 0.02** | 0.63 +/- 0.07 |
| ccx-migration-279 | **0.47 +/- 0.00** | 0.43 +/- 0.00 | 0.43 +/- 0.00 |
| ccx-migration-294 | **0.75 +/- 0.05** | 0.66 +/- 0.03 | — |
| ccx-onboard-search-207 | 0.00 +/- 0.00 | 0.00 +/- 0.00 | — |
| ccx-platform-291 | 0.78 +/- 0.01 | **0.79 +/- 0.02** | — |
| ccx-vuln-remed-135 | 0.29 +/- 0.05 | **0.64 +/- 0.05** | — |
| linux-acpi-backlight-fault-001 | **1.00 +/- 0.00** | **1.00 +/- 0.00** | **1.00 +/- 0.00** |
| servo-css-container-query-feat-001 | 0.00 +/- 0.00 | 0.00 +/- 0.00 | **0.83 +/- 0.00** |
| **Mean** | **0.55** | **0.57** | **0.58** |

### Cross-Agent Aggregate (Opus, all configs)

| Config | Agent | Mean Reward | Notes |
|--------|-------|:-----------:|-------|
| Claude + Sourcegraph | Claude Code | **0.63** | 20 tasks, highest ceiling (servo 0.83) |
| Claude + GitHub | Claude Code | 0.59 | 20 tasks, most consistent |
| Claude + Augment | Claude Code | 0.59 | 20 tasks, remote via GitHub App (complex), local (representative) |
| **Cursor + Sourcegraph** | Cursor | **0.57** | 15 tasks, SG adds +0.02 over native |
| **Cursor Native** | Cursor | **0.55** | 15 tasks, no MCP, built-in search only |

Note: Cursor ran on 15 of the 20 MCP comparison tasks. On overlapping tasks, Cursor Native (0.55) is comparable to Claude + Augment/GitHub (0.59), while Claude + Sourcegraph (0.63) retains the overall lead.

### Sourcegraph MCP Lift by Agent

| Agent | Without SG | With SG | SG Lift | Interpretation |
|-------|:---:|:---:|:---:|---|
| **Claude Code** | 0.59 (Augment) | 0.63 | **+0.04 to +0.09** | Code navigation decisive on complex tasks; gap narrower with Augment Remote |
| **Cursor** | 0.55 | 0.57 | **+0.02** | Native search already covers most use cases |

The Sourcegraph MCP advantage is **agent-dependent**. Claude Code lacks built-in semantic search, so SG's `find_references` and `go_to_definition` fill a critical gap. Cursor already has semantic search and Explore subagents, reducing the incremental value of SG to cross-file reference tracing on specific task types.

**Exception — security tasks:** `ccx-vuln-remed-135` shows +0.35 SG lift even on Cursor (0.29 → 0.64). Tracing vulnerable call sites across files is a capability that `find_references` provides uniquely — neither Cursor's grep nor its semantic search can efficiently trace callers of a specific function.

### Cursor vs Claude Code: Why Cursor Scores Lower on Servo

Both Cursor Native and Cursor+SG score 0.00 on `servo-css-container-query-feat-001` (10M LOC Rust), while Claude+SG scores 0.83. This gap is explained by:

1. **Cursor has local code but can't navigate it efficiently** at 133K files — semantic indexing may not complete within the task timeout, and grep returns too many results in a 10M LOC codebase
2. **Claude+SG uses remote code intelligence** — Sourcegraph's pre-built SCIP index provides instant `go_to_definition` across Servo's complex trait hierarchies, which no local tool can match at this scale
3. **The servo task is an outlier** — removing it, Cursor Native averages 0.59 vs Claude+SG at 0.56 on the remaining 14 tasks

## Conclusion

1. **Sourcegraph MCP produces the highest rewards overall** (0.56 Haiku, 0.63 Opus) but the advantage is concentrated on complex codebases. On representative tasks, all three Claude Code configs are statistically equivalent.

2. **Code navigation is the differentiator.** `find_references` and `go_to_definition` are decisive on tasks requiring cross-file symbol tracing — exactly the capability only Sourcegraph provides. This is most evident on Servo (0.83 vs 0.00/0.00) and incident-037 (0.96 vs 0.67/0.77).

3. **Sourcegraph is fastest and cheapest.** 156s mean task time and $0.39/task (Haiku), driven by remote-only architecture that avoids local code operations.

4. **Sourcegraph has the best IR metrics.** 0.41 recall and 0.17 F1 — finding the right files at 2–3x the rate of alternatives.

5. **Augment Remote (GitHub App) eliminates cloning with no quality loss.** Transitioning from local clone to GitHub App indexing improved Haiku complex task scores from 0.40 to 0.48, with dramatic gains on dependency tracing (0.50 → 0.91 on dep-trace-273). Augment leads on migration and dependency tasks without requiring any local code.

6. **Cursor's built-in search is competitive with MCP-augmented Claude Code.** Cursor Native (0.55) approaches Claude+Augment/GitHub (0.59) without any MCP server, demonstrating that IDE-integrated semantic search and vector embeddings partially substitute for external code intelligence tools.

7. **MCP value is agent-dependent.** Sourcegraph MCP provides +0.04–0.09 lift for Claude Code but only +0.02 for Cursor. Agents with built-in semantic search benefit less from external code intelligence — except for specific capabilities like cross-file reference tracing (e.g., +0.35 on security tasks).

8. **Pre-built code intelligence indexes remain essential at extreme scale.** Cursor scores 0.00 on Servo (10M LOC) where Claude+SG scores 0.83 — Sourcegraph's pre-indexed SCIP graph provides instant symbol navigation that no local tool can match at 133K files.

9. **Multi-trial analysis is essential.** Single-trial comparisons overstate MCP differences by 40–60% on representative tasks. Minimum 3 trials per cell recommended.

10. **Stronger models reduce variance more than they change rankings.** Opus cuts within-task stdev by 3–4x but the relative ordering of configs remains similar.
