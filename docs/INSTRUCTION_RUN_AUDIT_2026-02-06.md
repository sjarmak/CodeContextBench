# Instruction & Run Quality Audit — 2026-02-06

## 1. Instruction Consistency Across Configurations

### How Instructions Are Structured

Each task is run under 3 configurations, each with different instruction composition:

| Config | instruction.txt | CLAUDE.md | .mcp.json | Tool Restrictions |
|--------|----------------|-----------|-----------|-------------------|
| **baseline** | Raw `instruction.md` only | None | None | Full tool access |
| **SG_base** | MCP preamble + `instruction.md` | SG tool mapping + repo filter | Full Sourcegraph (14 tools) | Grep/Glob/search BLOCKED |
| **SG_full** | MCP preamble + DS section + `instruction.md` | SG mapping + DS guidance + repo filter | Full Sourcegraph (14 tools) | Full tool access |

### Preamble Content (SG_base + SG_full)

The MCP preamble prepended to instruction.txt contains:
1. **"MANDATORY: Use Sourcegraph MCP Tools"** header
2. Required steps: `sg_list_files` → `sg_keyword_search` → `sg_read_file`
3. **Repository filter**: `repo:^github.com/sg-benchmarks/{mirror_name}$ QUERY`
4. Tool substitution table: Grep→sg_keyword_search, Glob→sg_list_files, etc.

SG_full additionally includes:
5. **"REQUIRED: Use Deep Search"** section with usage guidance
6. Deep Search query patterns and when-to-use guidance

### CLAUDE.md Content (SG_base + SG_full)

Both SG configs upload a CLAUDE.md to `/workspace/CLAUDE.md` containing:
- Tool mapping table (same as preamble)
- **Repository Filter section**: "You are working in: `sg-benchmarks/{mirror_name}`"
- Search instruction: `repo:^github.com/sg-benchmarks/{mirror_name}$ YourSearchTerm`
- "After MCP Search: Verify Locally" guidance

SG_full additionally includes:
- Deep Search section: "MUST use Deep Search as your FIRST tool call"
- DS retry instructions (**NOTE: Current code has 3-retry pattern; Feb 5 runs lack this**)

### Baseline Contamination Check

**RESULT: CLEAN** — No MCP/Sourcegraph references found in any `instruction.md` file.

Grep for `sourcegraph|Sourcegraph|sg_keyword|mcp__sourcegraph|Deep Search|deepsearch` across all `benchmarks/*/instruction.md`: **0 matches**.

The C1 QA audit issue (MCP refs leaking into baseline) has been **resolved**. MCP content is injected only at runtime via the agent preamble system, not baked into instruction.md files.

### Instruction Length Consistency

Example (PyTorch sgt-001):
- Baseline: 59 lines (raw instruction only)
- SG_base: 82 lines (+23 lines preamble)
- SG_full: 106 lines (+47 lines preamble with DS section)

The same core instruction content appears identically across all 3 configs.

---

## 2. MCP Repository Pinning Audit

### Repo Resolution Logic (`_get_repo_display()`)

The agent resolves repo names via this priority chain:
1. `SOURCEGRAPH_REPO_NAME` env var (explicit override)
2. `LOCOBENCH_PROJECT_ID` → `sg-benchmarks/locobench-{prefix}`
3. `SWEBENCH_REPO_COMMIT` → `sg-benchmarks/{repo_info}`
4. Fallback: `"the codebase"`

For most benchmarks, `SWEBENCH_REPO_COMMIT` is set by the config scripts to `{mirror_name}` (e.g., `pytorch--ca246612`), which resolves to `sg-benchmarks/pytorch--ca246612`.

### Pinning Status by Benchmark

| Benchmark | Tasks | Mirror Format | Pinned? | Notes |
|-----------|-------|--------------|---------|-------|
| SWE-bench Pro | 32/36 | `sg-benchmarks/{repo}--{8-char-commit}` | YES | 4 protonmail tasks not indexed |
| PyTorch | 12 | `sg-benchmarks/pytorch--{commit}` | YES | Single mirror per task |
| K8s Docs | 5 | `sg-benchmarks/kubernetes--8c9c67c0` | YES | Shared mirror |
| SWE-Perf | 3 | `sg-benchmarks/{repo}--{commit}` | YES | |
| LargeRepo | 4 | Public GitHub + `git checkout {hash/tag}` | YES | Dockerfiles pin commits |
| CrossRepo | 7 repos | `sg-benchmarks/{repo}--{commit}` | YES | |
| DIBench | 8 | `sg-benchmarks/{repo}--dibench` | YES | Stripped repos |
| LoCoBench | 25 | `sg-benchmarks/locobench-{task_id}` | YES | Synthetic contexts |
| LinuxFLBench | 5 | `sg-benchmarks/linux--{commit}` | YES | Kernel version pinned |
| CodeReview | 3 | `sg-benchmarks/{repo}--{commit}` | YES | Pre-defect commits |
| DependEval | 32 | `sg-benchmarks/dependeval-{lang}-{type}-{hash}` | YES | |
| **TAC** | 2/6 active | `sg-benchmarks/OpenHands--latest` | **NO** | `--latest` fallback |

### Issues Found

**ISSUE P-1: TAC OpenHands repos use `--latest` fallback**
- Tasks: `tac-write-unit-test`, `tac-dependency-change`
- Mirror: `sg-benchmarks/OpenHands--latest` (commit: null)
- Root cause: TAC GitLab commit `bfd78f9` not found in upstream GitHub
- Risk: Sourcegraph searches different code than local Docker environment
- Mitigation: TAC copilot-arena tasks already excluded; OpenHands tasks should be flagged

**ISSUE P-2: 4 protonmail/webclients SWE-bench Pro tasks not indexed**
- `indexed: false` in instance_to_mirror.json
- These tasks cannot benefit from Sourcegraph search
- Low priority: protonmail ghost runs already archived

---

## 3. MCP Usage Compliance

### Tool Call Verification

MCP usage verified by scanning conversation JSONL logs for `mcp__sourcegraph` tool calls:

| Config | MCP Usage | Deep Search Usage |
|--------|-----------|-------------------|
| **Baseline** | 0% (expected) | N/A |
| **SG_base** | **100%** across all benchmarks | N/A |
| **SG_full** | **100%** across all benchmarks | **100%** across all benchmarks |

**All SG-configured runs show proper MCP and Deep Search tool usage.**

### Deep Search Retry Compliance

The QA audit (C9) identified that 70.1% of Deep Search calls returned polling-only responses, with agents giving up after 1-2 polls.

**Current code status**: Retry preamble added to `claude_baseline_agent.py`:
```
**Retry `sg_deepsearch_read` at least 3 times** before giving up — Deep Search takes 50-120 seconds
```

**Deployed run status**: Feb 5 runs do NOT have the retry instruction in CLAUDE.md. The fix is in the code but hasn't been exercised in actual runs yet. **Rerun needed** (tracked as beads-kph).

---

## 4. Run Quality & Archival Status

### Active Run Inventory (30 directories in runs/official/)

**Complete 3-config runs:**
- bigcode_mcp: 3 batch dirs (all 3 configs each)
- k8s_docs: 3 batch dirs (all 3 configs each)
- sweperf: 2 batch dirs
- pytorch_gapfill: 2 batch dirs
- pytorch: 1 batch dir
- crossrepo: 1 batch dir
- dibench: 1 batch dir
- repoqa: 1 batch dir

**Split/partial runs (by design — configs in separate batch dirs):**
- LoCoBench: 3 dirs (baseline/sg_base/sg_full split across timestamps)
- TAC: 4 dirs (baseline×2/sg_base/sg_full split)
- SWE-bench Pro: 4 dirs (main + sg_base rerun + sg_full rerun + gap-fill)
- swebenchpro_gapfill: 2 dirs (baseline+sg_base + sg_full separate)
- swebenchpro_gapfill_sgfull: 2 dirs

**In-progress (baseline only, MCP running):**
- codereview_opus_20260206_155036: baseline only (beads-yk3)
- linuxflbench_opus_20260206_155043: baseline only (beads-9r9)

### Zero-Token Issue

Only **1 task** in non-archived runs reports 0 input tokens:
- `k8s_docs_opus_20260203_160607/sourcegraph_full/__archived_invalid/applyconfig-doc-001` (already in `__archived_invalid/`)

The earlier H3 finding (52 runs with 0 tokens) was largely resolved by archival of old/broken runs.

### Archival Status

**Properly archived (in runs/official/archive/):**
- PyTorch old verifier runs (reward=1.0 bug) ✅
- protonmail/internetarchive/tutanota ghost runs ✅
- CrossRepo docker build failures ✅
- CodeReview SG config failures ✅
- LinuxFLBench task_id mismatch ✅

**Still needs archival (tracked in beads):**
- beads-3c9: 12 stale batches
- beads-yeo: 4 duplicate runs with divergent rewards

---

## 5. Issues Summary & Triage Status

### Already Tracked in Beads

| ID | Issue | Priority | Status |
|----|-------|----------|--------|
| kph | Rerun SG_full with DS retry preamble | P1 | Open |
| 9r9 | Run LinuxFLBench SG configs | P1 | In Progress |
| yk3 | Run CodeReview SG configs | P1 | In Progress |
| rej | Generate final report | P2 | Blocked (7 deps) |
| dfp | Run LoCoBench baseline + SG_full | P2 | Open |
| 99h | Run TAC SG configs | P2 | Open (blocked) |
| 05n | Run DependEval 3 configs | P2 | Open (blocked) |
| aot | Regenerate MANIFEST | P2 | Blocked |
| 3c9 | Archive 12 stale batches | P2 | Open |
| yeo | Resolve 4 duplicate runs | P2 | Open |
| 23c | Update LoCoBench verify.py weights | P3 | Open |
| p3k | Investigate token logging bug | P3 | Open |
| 3e0 | Reclassify context window errors | P3 | Open |

### New Findings (Need Beads Issues)

| Finding | Severity | Description |
|---------|----------|-------------|
| **N1** | P3 | TAC OpenHands `--latest` mirror not commit-pinned (2 tasks) |
| **N2** | P3 | SG_base CLAUDE.md duplicate content in some older runs (cosmetic, not functional) |
| **N3** | INFO | DS retry preamble in code but not validated in runs — covered by kph rerun |

### No Action Needed

- **Instruction contamination (C1)**: RESOLVED — 0 instances found
- **MCP compliance**: EXCELLENT — 100% tool usage in all SG configs
- **Deep Search usage**: EXCELLENT — 100% of SG_full tasks call DS
- **LargeRepo Dockerfiles (C2)**: RESOLVED — all pin specific commit hash or version tag
- **Ghost runs (C4-C5)**: RESOLVED — all archived
- **Zero-token bug (H3)**: Largely resolved (1 remaining in already-archived dir)

---

## 6. Recommendations

### Immediate
1. **Wait for CodeReview + LinuxFLBench SG runs to complete** (beads-yk3, beads-9r9)
2. **Rerun SG_full with DS retry preamble** to validate C9 fix (beads-kph)

### Before Final Report
3. **Complete all P1/P2 beads** — these block report generation
4. **Regenerate MANIFEST.json** after all runs complete (beads-aot)
5. **Archive stale batches** per beads-3c9

### Low Priority
6. **Pin TAC OpenHands mirror** — fork at the specific GitLab commit or document the limitation
7. **Verify DS retry effectiveness** — compare polling success rate in new vs old runs
