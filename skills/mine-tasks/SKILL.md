---
name: mine-tasks
description: Analyze a codebase (via repo URL or local path) and propose benchmark tasks for CodeScaleBench. Mines GitHub issues/PRs for SDLC tasks and analyzes codebase structure for org-scale tasks. Outputs proposals compatible with /scaffold-task. Triggers on mine tasks, propose tasks, discover tasks, find tasks, analyze repo for tasks.
user-invocable: true
---

# Mine Tasks

Analyze a user-provided codebase to automatically discover and propose benchmark tasks for CodeScaleBench. Supports two modes:

- **SDLC mining**: Finds closed GitHub issues resolved by merged PRs — real bug fixes, features, and refactors suitable for "can the agent reproduce this fix?" benchmarks.
- **Org-scale mining**: Analyzes codebase structure (cross-repo dependencies, config patterns, API surfaces, import graphs) to propose discovery/tracing/compliance tasks.

Output is a set of task proposals that can be directly fed to `/scaffold-task`.

---

## Phase 1: Codebase Input

Ask the user:

**Question 1** — Header: "Codebase source"
- Question: "How should I access the codebase?"
- Options:
  - **GitHub repo URL** — "e.g., https://github.com/envoyproxy/envoy or envoyproxy/envoy"
  - **Multiple GitHub repos** — "Comma-separated list of owner/repo (for org-scale cross-repo analysis)"
  - **Local path** — "Absolute path to a locally cloned repo"

Collect the repo URL(s) or path. For GitHub URLs, extract `owner/repo`. Validate that the repo exists (use `gh repo view owner/repo --json name` or check the local path exists).

**Question 2** — Header: "Mining mode"
- Question: "What kind of benchmark tasks should I look for?"
- Options:
  - **SDLC tasks** — "Mine closed issues/PRs for real bug fixes, features, and refactors (agent must reproduce the code change)"
  - **Org-scale tasks** — "Analyze codebase structure for discovery, tracing, compliance, and comprehension tasks (agent produces answer artifacts)"
  - **Both** — "Run both analyses and propose a mixed set"

**Question 3** — Header: "Constraints"
- Question: "Any constraints on what to look for?"
- Options:
  - **Auto-discover** — "Let me analyze the repo and propose the best candidates"
  - **Specific area** — "Focus on a specific package, module, or subsystem (I'll specify)"
  - **Use cases provided** — "I have specific scenarios I want turned into tasks (I'll list them)"

If "Specific area", prompt for the package/module path.
If "Use cases provided", prompt for a list of use case descriptions (free text).

---

## Phase 2: Codebase Reconnaissance

Before mining, gather structural information about the repo(s). This informs both SDLC and org-scale mining.

### Step 2a: Repo Metadata

For each repo, collect:

```bash
# Via GitHub API
gh repo view owner/repo --json name,primaryLanguage,languages,defaultBranchRef,diskUsage,stargazerCount,description

# Or for local repos
git log --oneline -1
wc -l $(find . -name '*.go' -o -name '*.py' -o -name '*.ts' -o -name '*.java' -o -name '*.cpp' -o -name '*.rs' | head -500) 2>/dev/null | tail -1
```

Record: primary language, approximate size (LOC / disk), default branch, description.

### Step 2b: Structure Analysis

For local repos or after cloning:

```bash
# Top-level directory structure
ls -d */

# Find key patterns
find . -name 'go.mod' -o -name 'package.json' -o -name 'Cargo.toml' -o -name 'setup.py' -o -name 'pyproject.toml' | head -20

# For Go: module path and key packages
head -5 go.mod 2>/dev/null
ls cmd/ pkg/ internal/ 2>/dev/null

# For multi-repo: cross-repo import analysis
rg -l 'import.*other-repo-module' --type go 2>/dev/null | head -20
```

### Step 2c: Sourcegraph / Deep Search (when available)

If Sourcegraph MCP tools are available (`SOURCEGRAPH_ACCESS_TOKEN` set), use them for deeper analysis:

```
# Semantic search for architecture patterns
mcp__sourcegraph__sg_nls_search: "main entry points and API surface in repo:owner/repo"

# Keyword search for cross-repo dependencies
mcp__sourcegraph__sg_keyword_search: "repo:^github.com/owner/repo$ import.*other-org"
```

If Deep Search CLI is available (`SRC_ACCESS_TOKEN` set):

```bash
bash ds start --question "What are the main subsystems and their dependencies in this codebase?"
```

If neither is available, fall back to local `rg`/`grep` analysis.

---

## Phase 3: SDLC Task Mining

Skip this phase if user selected "Org-scale tasks" only.

### Step 3a: Find Candidate Issues/PRs

Use the GitHub API to find closed issues with merged PRs:

```bash
# Find recently merged PRs with linked issues (last 6 months, sorted by comments)
gh pr list --repo owner/repo --state merged --limit 100 --json number,title,body,labels,files,additions,deletions,closedAt,mergedAt

# Filter for good benchmark candidates:
# - Has a clear problem description (bug report or feature request)
# - Patch touches 1-15 files (not too small, not too large)
# - Has test changes (indicates verifiable fix)
# - Not a dependency bump, CI change, or trivial typo fix
```

### Step 3b: Score and Rank Candidates

For each candidate PR, compute a suitability score based on:

| Criterion | Weight | Scoring |
|-----------|--------|---------|
| Patch size (files changed) | 0.25 | 1-3 files: 1.0, 4-8: 0.8, 9-15: 0.6, >15: 0.2 |
| Has test changes | 0.20 | Yes with fail-to-pass: 1.0, Yes: 0.7, No: 0.2 |
| Issue quality | 0.20 | Clear repro steps: 1.0, Good description: 0.7, Minimal: 0.3 |
| Code complexity | 0.15 | Non-trivial logic: 1.0, Config/docs: 0.3, Trivial: 0.1 |
| Language diversity | 0.10 | Underrepresented in CSB: 1.0, Well-covered: 0.5 |
| Recency | 0.10 | <3 months: 1.0, 3-6 months: 0.8, 6-12 months: 0.6 |

### Step 3c: Classify SDLC Phase

For each candidate, classify into an SDLC phase based on PR content:

| Signal | Phase | Category |
|--------|-------|----------|
| Labels: bug, fix, hotfix, regression | Implementation (bug fix) | `bug_fix` |
| Labels: feature, enhancement, feat | Implementation (feature) | `feature` |
| Labels: refactor, cleanup, tech-debt | Implementation (refactoring) | `refactoring` |
| Labels: test, testing, coverage | Testing & QA | `test` |
| Labels: docs, documentation | Documentation | `documentation` |
| Labels: security, CVE, vulnerability | Maintenance | `security` |
| PR title: "fix", "resolve", "patch" | Implementation (bug fix) | `bug_fix` |
| PR title: "add", "implement", "support" | Implementation (feature) | `feature` |
| PR title: "refactor", "clean", "simplify" | Implementation (refactoring) | `refactoring` |

### Step 3d: Extract Task Details

For the top candidates (up to 10), extract:

```bash
# Get the exact pre-fix commit (parent of first PR commit)
gh pr view NUMBER --repo owner/repo --json mergeCommit,baseRefOid

# Get the patch (files changed)
gh pr diff NUMBER --repo owner/repo

# Get linked issue body for instruction text
gh issue view ISSUE_NUMBER --repo owner/repo --json body,title,labels
```

Build a task proposal for each:

```json
{
  "task_id": "{repo_name}-{slug}-{phase}-001",
  "mode": "sdlc",
  "benchmark": "csb_sdlc_{phase_suite}",
  "repo": "owner/repo",
  "commit": "{pre_fix_commit_sha}",
  "ground_truth_rev": "{merge_commit_sha}",
  "language": "{primary_language}",
  "difficulty": "{estimated_difficulty}",
  "sdlc_phase": "{phase}",
  "category": "{category}",
  "description": "{issue_title}: {issue_body_summary}",
  "files_changed": ["path/to/file1", "path/to/file2"],
  "patch_stats": {"additions": N, "deletions": M, "files": K},
  "source_pr": "https://github.com/owner/repo/pull/NUMBER",
  "source_issue": "https://github.com/owner/repo/issues/ISSUE_NUMBER",
  "suitability_score": 0.85,
  "scoring_breakdown": {"patch_size": 1.0, "has_tests": 0.7, ...}
}
```

### Step 3e: Extract Reviewer Information

For each candidate PR, extract reviewer and contributor metadata for `reviewers.json`:

```bash
# Get PR reviewer details
gh pr view NUMBER --repo owner/repo --json author,mergedBy,reviews

# Get reviews with reviewer logins
gh api repos/owner/repo/pulls/NUMBER/reviews --jq '.[].user.login'
```

Also query top contributors for the code areas touched by the PR:

```bash
# For each changed directory, find frequent committers
gh api "repos/owner/repo/commits?path=pkg/changed_dir/&per_page=30" --jq '.[].author.login' | sort | uniq -c | sort -rn | head -5
```

Add a `reviewers` field to the task proposal:

```json
{
  "reviewers": {
    "source_pr": {
      "number": NUMBER,
      "url": "https://github.com/owner/repo/pull/NUMBER",
      "author": "pr_author_login",
      "merged_by": "merger_login",
      "reviewers": ["reviewer1", "reviewer2"]
    },
    "top_contributors": [
      {"login": "contributor1", "commits": 15},
      {"login": "contributor2", "commits": 8}
    ],
    "code_areas": ["pkg/changed_dir/", "internal/module/"],
    "suggested_reviewers": ["reviewer1", "contributor1", "pr_author"],
    "discovery_method": "source_pr"
  }
}
```

Filter out bot accounts (dependabot, renovate, bors, k8s-ci-robot, etc.) from all contributor/reviewer lists.

### Difficulty Estimation (SDLC)

| Files Changed | Lines Changed | Cross-Package | Difficulty |
|---------------|---------------|---------------|------------|
| 1-2 | <50 | No | medium |
| 1-3 | 50-200 | No | hard |
| 3-8 | 50-500 | Yes | hard |
| 4-10 | 200-1000 | Yes | very_hard |
| 10+ | 500+ | Yes | expert |

---

## Phase 4: Org-Scale Task Mining

Skip this phase if user selected "SDLC tasks" only.

### Step 4a: Cross-Repo Dependency Analysis

For multi-repo inputs, identify cross-repo relationships:

```bash
# Go: find cross-module imports
rg 'import.*"(other-org/other-repo)' --type go -l

# Python: find cross-package imports
rg 'from (other_package) import|import (other_package)' --type py -l

# Proto/gRPC: find proto imports across repos
rg 'import ".*\.proto"' --type proto -l

# JS/TS: find cross-package requires/imports
rg "require\('(@other-org|other-package)" --type js -l
```

For single repos, analyze internal module boundaries:

```bash
# Go: list internal packages and their importers
go list ./... 2>/dev/null | head -50
rg 'import.*".*internal/' --type go -l | head -20

# Find interface definitions (potential tracing targets)
rg '(type|interface|trait|abstract class)\s+\w+' --type go --type java --type py -l | head -30
```

### Step 4b: Identify Org-Scale Task Patterns

Scan for patterns that make good org-scale benchmark tasks:

| Pattern | Task Family | Detection Method |
|---------|-------------|-----------------|
| Shared proto/IDL definitions | `cross-repo-dep-trace` | Find `.proto` files imported across repos |
| Shared library packages | `cross-repo-dep-trace` | Find packages imported by 3+ consumers |
| Config propagation chains | `cross-repo-config-trace` | Find config structs used across module boundaries |
| API surface definitions | `onboarding-comprehension` | Find exported interfaces/types in `pkg/` or `api/` |
| Deprecated APIs | `migration-inventory` | Find `@Deprecated`, `// Deprecated:`, `#[deprecated]` |
| Security-sensitive patterns | `compliance-audit` | Find TLS configs, auth middleware, secret handling |
| Error handling chains | `incident-debug` | Find error types that propagate across packages |
| Plugin/extension points | `platform-knowledge` | Find plugin registries, factory patterns, hook systems |
| Domain model relationships | `domain-lineage` | Find entity types and their relationships |

### Step 4c: Generate Org-Scale Proposals

For each identified pattern, propose a task:

```json
{
  "task_id": "CCX-{family_short}-{NNN}",
  "mode": "org",
  "benchmark": "csb_org_{suite}",
  "repos": [
    {"full_name": "owner/repo1", "commit_or_tag": "v1.0.0"},
    {"full_name": "owner/repo2", "commit_or_tag": "main"}
  ],
  "language": "{primary_language}",
  "difficulty": "{estimated_difficulty}",
  "category": "{task_family}",
  "description": "{generated_task_description}",
  "customer_prompt": "{natural_language_question}",
  "oracle_type": "deterministic_json",
  "oracle_check_types": ["file_set_match", "symbol_resolution"],
  "evidence": {
    "pattern_type": "shared_library",
    "files_found": ["repo1/pkg/shared.go", "repo2/internal/consumer.go"],
    "cross_repo_refs": 5,
    "confidence": "high"
  },
  "reviewers": {
    "repos": ["owner/repo1", "owner/repo2"],
    "top_contributors": [
      {"login": "maintainer1", "commits": 20},
      {"login": "maintainer2", "commits": 12}
    ],
    "code_areas": ["pkg/shared/", "internal/consumer/"],
    "suggested_reviewers": ["maintainer1", "maintainer2"],
    "discovery_method": "git_log_frequency"
  }
}
```

### Step 4c-extra: Extract Reviewer Information for Org Tasks

For each org-scale proposal, identify code owners and top contributors using git log frequency analysis:

```bash
# For each repo and code area, find top committers
for repo in owner/repo1 owner/repo2; do
  for area in pkg/shared/ internal/consumer/; do
    gh api "repos/$repo/commits?path=$area&per_page=30" --jq '.[].author.login' | sort | uniq -c | sort -rn | head -5
  done
done
```

Aggregate contributors across all repos in the task. The `suggested_reviewers` list should contain the top 3-5 contributors (excluding bots like dependabot, renovate, bors, k8s-ci-robot).

### Step 4d: Customer Prompt Generation

For each org-scale proposal, generate a natural-language task prompt following the use_case_registry.json style:

- **Cross-repo dep trace**: "Which {language} source files in the `{package}/` tree of `{repo}` directly import `{dependency}`?"
- **Config trace**: "Trace how the `{ConfigType}` configuration defined in `{repo1}` gets consumed by `{repo2}`. Find the definition file, the parsing code, and the runtime application."
- **Compliance audit**: "Find all files in `{repo}` that configure TLS/SSL settings. Report the file path, the configuration type, and whether it enforces minimum TLS 1.2."
- **Migration inventory**: "Find all uses of the deprecated `{API}` across `{repo1}` and `{repo2}`. For each usage, report the file, line, and the recommended replacement."
- **Incident debug**: "Given that `{ErrorType}` is being thrown at runtime, trace the error origin across `{repo1}` and `{repo2}`. Find all files in the error propagation chain."
- **Onboarding comprehension**: "Explain the architecture of the `{subsystem}` in `{repo}`. Identify the main components, their interfaces, and the data flow between them."

---

## Phase 5: Feasibility Checks

Before presenting proposals, validate each one:

### SDLC Feasibility

For each SDLC proposal:

1. **Commit exists**: Verify the pre-fix commit is accessible
   ```bash
   gh api repos/owner/repo/commits/SHA --jq '.sha' 2>/dev/null
   ```

2. **Repo is cloneable**: Check that a shallow clone works
   ```bash
   git ls-remote https://github.com/owner/repo.git HEAD 2>/dev/null
   ```

3. **Patch is self-contained**: Check that the diff doesn't depend on external services, CI artifacts, or database migrations that can't be reproduced in a container.

4. **No secrets in patch**: Verify the PR diff doesn't contain API keys, tokens, or credentials.

Mark proposals as `feasible: true/false` with a reason.

### Org-Scale Feasibility

For each org-scale proposal:

1. **Repos accessible**: All referenced repos exist and are public (or the user has access).

2. **Oracle is deterministic**: The question has a concrete, verifiable answer (file lists, symbol names) — not subjective opinions.

3. **Sourcegraph indexing**: If SG tools are available, verify the repos are indexed:
   ```
   mcp__sourcegraph__sg_keyword_search: "repo:^github.com/owner/repo$ count:1"
   ```

4. **Task is non-trivial**: The answer requires searching/reading at least 3 files (not answerable from a single README).

---

## Phase 6: Present Proposals

Present the proposals in a structured summary table, grouped by type:

```
=== SDLC Task Proposals ===

| # | Task ID | Suite | Difficulty | Files | Score | Source |
|---|---------|-------|------------|-------|-------|--------|
| 1 | envoy-dfp-leak-fix-001 | csb_sdlc_fix | hard | 3 | 0.92 | PR #31433 |
| 2 | envoy-cors-header-feat-001 | csb_sdlc_feature | medium | 2 | 0.85 | PR #28901 |
| ... | | | | | | |

=== Org-Scale Task Proposals ===

| # | Task ID | Suite | Difficulty | Repos | Pattern | Confidence |
|---|---------|-------|------------|-------|---------|------------|
| 1 | CCX-dep-trace-301 | csb_org_crossrepo | hard | 3 | shared_lib | high |
| 2 | CCX-compliance-301 | csb_org_compliance | medium | 1 | tls_config | high |
| ... | | | | | | |
```

For each proposal, show:
- Task ID and proposed suite
- Brief description (1 line)
- Source (PR link for SDLC, evidence summary for org-scale)
- Feasibility status

Then ask:

**Question** — Header: "Selection"
- Question: "Which proposals should I scaffold? (Enter numbers, 'all', or 'none')"

---

## Phase 7: Scaffold Selected Tasks

For each selected proposal, invoke `/scaffold-task` with the pre-filled values. The agent should:

1. Skip Phase 1 and 2 of scaffold-task (mode and details already known).
2. Go directly to Phase 3 (task-specific inputs) with values pre-populated.
3. Generate all files via Phase 4.
4. Register via Phase 5.
5. Validate via Phase 6.

Alternatively, write the proposals to a JSON file for batch processing:

```bash
# Write proposals to file
cat > /tmp/mined_tasks.json << 'EOF'
{
  "proposals": [...],
  "source_repos": ["owner/repo"],
  "mined_at": "2026-03-07T...",
  "mining_mode": "both"
}
EOF
```

Then the user can review and selectively scaffold with:
```
/scaffold-task  # and provide values from the proposal
```

---

## Phase 8: Summary

After scaffolding, print:

```
Mining Summary
  Source:     owner/repo (+ N other repos)
  Language:   Go
  Analyzed:   147 merged PRs, 23 cross-repo patterns

  SDLC proposals:     8 found, 5 feasible, 3 scaffolded
  Org-scale proposals: 4 found, 4 feasible, 2 scaffolded

Scaffolded tasks:
  1. envoy-dfp-leak-fix-001       → benchmarks/csb_sdlc_fix/envoy-dfp-leak-fix-001/
  2. envoy-cors-header-feat-001   → benchmarks/csb_sdlc_feature/envoy-cors-header-feat-001/
  3. CCX-dep-trace-301            → benchmarks/csb_org_crossrepo/ccx-dep-trace-301/

Next steps:
  1. Review instruction.md for each task — fill in TODOs
  2. Review reviewers.json — verify suggested reviewers are accurate
  3. Customize test.sh / oracle_checks.py with task-specific verification
  4. For SDLC tasks: verify the ground_truth_rev produces a passing test
  5. For org-scale tasks: populate task_spec.json with oracle checks
  6. Run /validate-tasks on each scaffolded task
  7. Optionally run curator: python3 scripts/context_retrieval_agent.py --task-dir <path>
```

---

## Fallback Strategies

### No GitHub API access (`gh` not authenticated)
- Skip SDLC mining (requires PR/issue data).
- Org-scale mining works with local repo analysis only.
- Suggest: `gh auth login` and retry.

### No Sourcegraph access
- Use local `rg`/`grep` for all code analysis.
- Cross-repo analysis limited to repos available locally.
- Deep Search unavailable — rely on structural analysis.

### Single repo provided for org-scale
- Analyze internal module boundaries as "cross-package" tasks.
- Propose comprehension, audit, and incident-debug tasks within a single repo.
- Suggest additional repos in the same ecosystem for cross-repo tasks.

### Very large repo (>5GB)
- Use `--depth 1` shallow clone for analysis.
- Limit PR scanning to last 3 months.
- Focus on specific subsystems if user provided a focus area.

### No merged PRs found
- Fall back to analyzing recent commits directly.
- Look for commits with messages containing "fix", "bug", "resolve".
- Propose tasks based on commit diffs instead of PR metadata.
