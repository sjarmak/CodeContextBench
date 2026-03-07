# Core Retrieval Benchmark Spec

## Goal

Define the primary CodeScaleBench benchmark for identifying the impact of context retrieval on reward outcomes for enterprise software development tasks, especially in large and distributed repositories.

## Canonical Analytical Variables

- `repo_approx_loc`
  - Source: `cloc`
  - Meaning: canonical codebase scale variable for benchmark design and reporting
- `n_repos`
  - Source: task environment / Dockerfile clone topology
  - Meaning: canonical repository-distribution variable

## Secondary Operational Variables

- `repo_size_mb`
  - Keep for image/build/runtime planning only
  - Do not use as the primary scientific scale variable in benchmark design, sampling, or reporting
- `repo_complexity`
  - Keep as a secondary moderator
  - Use only after LOC and repo topology are complete

## Canonical LOC Bands

- `<400K`
- `400K-2M`
- `2M-8M`
- `8M-40M`
- `>40M`
- `unknown`

These bands are defined directly on `repo_approx_loc`, not inferred from repository storage size.

## Core Benchmark Inclusion Rubric

A task is eligible for the canonical core benchmark if and only if it satisfies **all** of the following hard gates:

| # | Gate | Criterion |
|---|------|-----------|
| G1 | Paired coverage | Task has at least 3 valid paired (baseline + MCP) scored runs in `runs/official/`. |
| G2 | Scale metadata | `repo_approx_loc` is populated (cloc-backed). This is the primary scale variable; `repo_size_mb` is operational-only. |
| G3 | Topology metadata | `n_repos` is populated (derived from environment Dockerfile clone topology). |
| G4 | Verifier quality | Task verifier is classified `core_ready` or `conditional` (see Verifier-Quality Classification). Tasks classified `extension_only` are excluded. |

Tasks that pass all hard gates are then **ranked** by retrieval sensitivity. The core benchmark preferentially includes tasks where retrieval plausibly changes success:

- Multi-repo discovery and cross-repo tracing
- Incident debugging in large codebases
- Security review and compliance auditing
- Migration inventory across distributed services
- Onboarding in unfamiliar large codebases
- Retrieval-bound fix and understand tasks

Tasks from low-retrieval-sensitivity suites (`csb_sdlc_design`, `csb_sdlc_refactor`, `csb_sdlc_debug`, `csb_sdlc_document`, `csb_org_platform`) are included as a smaller **control slice** for generalization checks, not as the benchmark center of gravity.

### Extension Benchmark Policy

Non-canonical valid tasks are **never deleted**. They remain in the full task pool as an extension benchmark for secondary analyses, generalization checks, and future promotion if verifier quality or retrieval sensitivity improves. The canonical core manifest and the extension set are disjoint partitions of the full pool.

## Recommended Core Benchmark Size

- Statistical floor for overall paired MCP effect: about `80` paired tasks
- Practical minimum for a defensible enterprise benchmark: about `200` paired tasks
- Recommended primary benchmark: about `220` paired tasks

## Recommended 220-Task Allocation

- `csb_org_security`: `28`
- `csb_org_incident`: `20`
- `csb_org_migration`: `22`
- `csb_org_crossrepo_tracing`: `18`
- `csb_org_onboarding`: `16`
- `csb_org_compliance`: `12`
- `csb_org_crossorg`: `10`
- `csb_org_domain`: `10`
- `csb_org_org`: `10`
- `csb_org_crossrepo`: `8`
- `csb_org_platform`: `6`
- `csb_sdlc_fix`: `18`
- `csb_sdlc_understand`: `8`
- `csb_sdlc_secure`: `6`
- `csb_sdlc_test`: `6`
- `csb_sdlc_feature`: `6`
- `csb_sdlc_debug`: `4`
- `csb_sdlc_design`: `4`
- `csb_sdlc_document`: `4`
- `csb_sdlc_refactor`: `4`

## Scale-Back Rules

- Do not expand abstract category buckets just to balance counts.
- Do not prioritize MB-based size coverage.
- Do not prioritize additional single-repo org tasks unless they are clearly retrieval-bound.
- Keep low-retrieval suites as controls and generalization checks, not as the benchmark center of gravity.

## Immediate Cleanup Checklist

- Finish the remaining unpaired tasks.
- Backfill all missing `repo_approx_loc`.
- Add explicit `n_repos` metadata.
- Repair weak verifiers before expanding task count.
- Keep the full task pool as an extension set; use the core benchmark for primary harness comparisons.
