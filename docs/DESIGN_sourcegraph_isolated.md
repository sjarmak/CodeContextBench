# Design: sourcegraph_isolated Config

**Beads Issue**: CodeContextBench-8hb
**Status**: Design
**Author**: Claude Code
**Date**: 2026-02-12

## Problem

Current benchmark configs give the agent full local access to the entire repository. This means local `grep`/`Glob`/`Read` can discover cross-package relationships without MCP. In monorepo workflows (K8s, large codebases), developers typically work within a single package and rely on code search tools to understand cross-package dependencies. Our benchmarks don't measure this.

## Goal

Create a `sourcegraph_isolated` config that mounts **only the target package** locally, forcing the agent to use Sourcegraph MCP tools for all cross-package discovery. This measures MCP's value in the realistic monorepo developer workflow where you can edit your package but must search remotely to understand how it fits into the broader codebase.

## Scope: Proof of Concept

**Phase 1 (5 tasks)**: K8s Docs — ideal because each task targets a specific `staging/src/k8s.io/*` package and explicitly requires reading OTHER packages to understand conventions.

**Phase 2 (4 tasks)**: LargeRepo — more complex, changes span multiple modules, but same principle applies.

## How It Works

```
BASELINE (current):     Full K8s repo → /workspace/  (1.8GB, all packages)
SOURCEGRAPH_ISOLATED:   Only target pkg → /workspace/ (few MB, one package)
                        + Sourcegraph MCP for everything else
```

### K8s Docs Example: apiserver-doc-001

| Config | Local Access | Remote Access | What Agent Must Do |
|--------|-------------|---------------|-------------------|
| baseline | Full repo (all staging/src/k8s.io/*) | None | `grep -r "doc.go" staging/` to find examples |
| SG_base | Full repo | Sourcegraph (optional) | Can use either local or MCP |
| **SG_isolated** | **Only staging/src/k8s.io/apiserver/** | **Sourcegraph (required)** | **Must use `keyword_search("doc.go")` to find examples from other packages** |

## Implementation Plan

### 1. New Dockerfiles (per-task, in `environment/`)

Create `Dockerfile.isolated` alongside existing `Dockerfile` for each task. Uses git sparse-checkout to mount only the target directory.

```dockerfile
FROM golang:1.23-bookworm
WORKDIR /workspace

RUN apt-get update && apt-get install -y git curl python3 npm ripgrep
RUN npm install -g @anthropic-ai/claude-code

# Clone repo structure but only checkout target package
RUN git clone --filter=blob:none --no-checkout https://github.com/kubernetes/kubernetes.git . && \
    git sparse-checkout init --cone && \
    git sparse-checkout set staging/src/k8s.io/apiserver && \
    git checkout 8c9c67c000104450cfc5a5f48053a9a84b73cf93 && \
    git config user.email "agent@example.com" && \
    git config user.name "Agent"

# Same surgical removal as original task
RUN rm -f staging/src/k8s.io/apiserver/doc.go
RUN find staging/src/k8s.io/apiserver -maxdepth 1 -name "*.go" -exec sed -i '/^\/\/ Package/d' {} +

RUN mkdir -p /workspace/tests /app
```

**Key**: `git sparse-checkout set <path>` keeps the directory tree structure intact (Go imports resolve correctly) but only has files for the target package. All sibling packages are empty directories.

### Target packages per task

| Task | Sparse Checkout Path | What's Locally Available |
|------|---------------------|-------------------------|
| apiserver-doc-001 | `staging/src/k8s.io/apiserver` | apiserver Go files (~200 files) |
| applyconfig-doc-001 | `staging/src/k8s.io/client-go/applyconfigurations` | applyconfig Go files |
| client-go-doc-001 | `staging/src/k8s.io/client-go` | client-go Go files |
| fairqueuing-doc-001 | `staging/src/k8s.io/apiserver/pkg/util/flowcontrol/fairqueuing/queueset` | queueset Go files only |
| pkg-doc-001 | `pkg/kubelet/cm` | container manager Go files |

### 2. Agent Config: New MCP Mode in claude_baseline_agent.py

Add `sourcegraph_isolated` to the mode handling (~30 lines):

```python
# In create_run_agent_commands(), after line 535
if mcp_type == "sourcegraph_isolated":
    # Stronger preamble: agent MUST use MCP for cross-package context
    mcp_preamble = f"""## CRITICAL: Limited Local Access — Sourcegraph REQUIRED

You have LOCAL ACCESS to ONLY the target package directory. All other packages
in this repository are NOT available locally.

To understand cross-package dependencies, imports, callers, conventions, and
patterns from OTHER packages, you MUST use Sourcegraph MCP tools:
- `keyword_search` to find code patterns across the full repository
- `go_to_definition` / `find_references` to trace symbols across packages
- `read_file` to read files from packages NOT available locally
- `list_files` to browse directories outside your local scope

{repo_line}

**WORKFLOW:**
1. Read the task requirements
2. Explore your LOCAL package to understand what you're working with
3. Use Sourcegraph to understand how your package relates to others
4. Implement your changes using local tools (Read, Edit, Bash)

---

"""
    instruction = mcp_preamble + instruction
```

Tool restrictions: Same as `sourcegraph_full` (all tools allowed). The isolation comes from the filesystem, not tool blocking. The agent CAN use local Grep/Glob but they'll only find files in the target package — which is the desired behavior.

### 3. Config Script: `configs/isolated_3config.sh`

Runs only 2 configs per task (not 3):
- **sourcegraph_isolated**: Sparse checkout + full MCP
- **sourcegraph_full**: Full repo + full MCP (existing, for comparison)

No baseline needed — we're comparing isolated-MCP vs full-access-MCP to measure how much the agent relies on MCP when local access is limited.

```bash
# Isolated run: uses Dockerfile.isolated
BASELINE_MCP_TYPE=sourcegraph_isolated \
SOURCEGRAPH_REPO_NAME="kubernetes/kubernetes" \
HARBOR_DOCKERFILE=Dockerfile.isolated \
harbor run --path "${TASK_DIR}" ...

# Full-access comparison: uses standard Dockerfile
BASELINE_MCP_TYPE=sourcegraph_full \
SOURCEGRAPH_REPO_NAME="kubernetes/kubernetes" \
harbor run --path "${TASK_DIR}" ...
```

### 4. Harbor Dockerfile Selection

Harbor normally uses `environment/Dockerfile`. We need to either:

**Option A (Preferred)**: Name the file `Dockerfile.isolated` and add a pre-run step that copies it to `Dockerfile` when `BASELINE_MCP_TYPE=sourcegraph_isolated`. This avoids Harbor changes.

**Option B**: Use a symlink or wrapper script that selects the Dockerfile based on env var.

**Option C**: Just create separate task directories (`apiserver-doc-001-isolated/`) with their own Dockerfiles. Most explicit but duplicates task.toml and tests.

**Recommendation**: Option A. Add to `_common.sh`:
```bash
if [ "$BASELINE_MCP_TYPE" = "sourcegraph_isolated" ]; then
    cp "$TASK_DIR/environment/Dockerfile.isolated" "$TASK_DIR/environment/Dockerfile.bak"
    cp "$TASK_DIR/environment/Dockerfile.isolated" "$TASK_DIR/environment/Dockerfile"
    trap "mv '$TASK_DIR/environment/Dockerfile.bak' '$TASK_DIR/environment/Dockerfile'" EXIT
fi
```

## What This Measures

### Primary Metric: MCP Tool Usage Rate
- **Isolated**: Expect 60-80% of code discovery through MCP (can't find other packages locally)
- **Full-access**: Expect 20-40% MCP usage (agent can grep locally)

### Secondary Metrics
- **Task success rate**: Does isolation hurt outcomes? (If so, MCP isn't providing enough cross-package context)
- **Token efficiency**: More MCP calls = more tokens, but possibly faster discovery
- **Search pattern quality**: What queries does the agent form when forced to use MCP?

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Go builds fail without sibling packages | sparse-checkout keeps directory structure; only needs source files for reading, not building |
| Agent tries to `git checkout` full repo | Preamble explicitly says "limited local access"; sparse-checkout prevents accidental expansion |
| K8s Docs tasks don't require building | Low risk — these tasks only write doc.go, no compilation needed |
| Sourcegraph mirror doesn't have target commit | K8s is on public GitHub, always indexed; LargeRepo has sg-benchmarks mirrors |

## LargeRepo Phase 2 Notes

LargeRepo is harder because tasks require building/testing, not just writing docs. Sparse checkout may break builds. For Phase 2, consider:
- Mount target package + explicit dependency packages (from go.mod/package.json)
- Or use a "gutted repo" approach: full directory tree but only source files in target packages, stub files elsewhere

## Files to Create/Modify

| File | Action | Lines |
|------|--------|-------|
| `benchmarks/ccb_k8sdocs/*/environment/Dockerfile.isolated` | Create (5 files) | ~30 each |
| `agents/claude_baseline_agent.py` | Add isolated mode handling | ~30 |
| `configs/isolated_3config.sh` | Create config script | ~150 |
| `configs/_common.sh` | Add Dockerfile swap logic | ~10 |

**Total estimated effort**: ~350 lines of code across 8 files.
