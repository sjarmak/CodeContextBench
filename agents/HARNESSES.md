# Agent Harnesses

CodeScaleBench evaluates AI coding agents via **harnesses** — adapter modules that wrap each agent's CLI or API into Harbor's trial execution contract. Each harness handles agent installation, MCP configuration, instruction delivery, and result collection.

## Available Harnesses

| Harness | Agent | Location | MCP Support |
|---------|-------|----------|:-----------:|
| **Claude Code** | Claude Code CLI | `agents/claude_baseline_agent.py` | Sourcegraph, Augment, GitHub, Deep Search |
| **OpenHands** | OpenHands CodeAct | `agents/harnesses/openhands/` | Sourcegraph |
| **Codex** | OpenAI Codex CLI | `agents/harnesses/codex/` | — |
| **Copilot** | GitHub Copilot | `agents/harnesses/copilot/` | — |
| **Cursor** | Cursor Agent | `agents/harnesses/cursor/` | — |
| **Gemini** | Google Gemini CLI | `agents/harnesses/gemini/` | — |

The Claude Code harness is the primary evaluation harness and supports the widest range of MCP configurations.

## Claude Code Harness

The Claude Code harness (`agents/claude_baseline_agent.py`) extends Harbor's base agent to support:
- Multiple MCP server configurations (see [MCP Configurations](#mcp-configurations))
- Subscription-based OAuth authentication (multi-account)
- Instruction preamble injection with MCP-specific guidance
- Non-root execution inside Docker containers
- Auggie CLI installation for Augment MCP mode

### Evaluation Configurations

Each configuration determines how the agent accesses source code and what tools are available:

| Config Name | Code Access | MCP Server | Use Case |
|-------------|------------|------------|----------|
| `baseline-local-direct` | Full local clone | None | Baseline: agent uses only built-in tools |
| `mcp-remote-direct` | Remote only | Sourcegraph | Measures Sourcegraph MCP impact |
| `augment-local-direct` | Full local clone | Augment Context Engine | Measures Augment MCP as supplement to local tools |
| `github-remote-direct` | Remote only | GitHub MCP Server | Measures GitHub API-based code access |

The `-direct` suffix means the verifier runs test scripts directly in the container.
`-artifact` variants (not shown) use oracle-based artifact evaluation instead.

---

## MCP Configurations

### Sourcegraph MCP (`mcp-remote-direct`)

**What it provides:** 14 specialized code intelligence tools — keyword search, semantic search, file reading, symbol navigation (go-to-definition, find-references), commit/diff search, and deep semantic analysis.

**Transport:** stdio via `npx @sourcegraph/mcp-server`

**Code access:** Remote only. The agent's workspace contains no source code. All code discovery and reading goes through Sourcegraph's indexed repository.

**Tools available:**
| Tool | Purpose |
|------|---------|
| `keyword_search` | Exact pattern/symbol search across files |
| `nls_search` | Natural language semantic search |
| `read_file` | Read file contents from indexed repo |
| `list_files` | Browse directory structure |
| `go_to_definition` | Jump to symbol definition (cross-repo) |
| `find_references` | Find all usages of a symbol |
| `commit_search` | Search commit history by message/author |
| `diff_search` | Search code changes (added/removed lines) |
| `compare_revisions` | Compare branches/commits/tags |
| `deepsearch` | AI-powered deep semantic analysis |
| `deepsearch_read` | Read deep search results |

**Auth:** `SOURCEGRAPH_ACCESS_TOKEN` environment variable.

**Preamble:** The agent receives a structured instruction preamble with:
- Tool selection guide (when to use keyword vs semantic search)
- Repository scoping instructions (`repo:^github.com/ORG/REPO$`)
- Efficiency rules (chain searches, don't over-read)

---

### Augment Context Engine (`augment-local-direct`)

**What it provides:** One semantic code search tool (`codebase-retrieval`) that indexes the local workspace and provides natural-language code understanding.

**Transport:** stdio via `auggie --mcp --mcp-auto-workspace`

**Code access:** Full local clone. The agent has all standard local tools (Read, Edit, Grep, Glob, Bash) plus the Augment MCP tool as a supplement. This is the closest to baseline — the agent works locally but can use semantic search for architectural questions and cross-file understanding.

**Tools available:**
| Tool | Purpose |
|------|---------|
| `codebase-retrieval` | Semantic code search over local workspace |

**Auth:** `AUGMENT_SESSION_AUTH` (JSON with accessToken and tenantURL) or `AUGMENT_API_TOKEN` + `AUGMENT_API_URL`.

**When to use codebase-retrieval vs local tools:**
| Situation | Recommended Tool |
|-----------|-----------------|
| Know exact symbol or filename | Grep, Glob, Read |
| Exploring unfamiliar code | `codebase-retrieval` |
| Cross-file relationships | `codebase-retrieval` |
| Architecture/data flow questions | `codebase-retrieval` |
| Quick file pattern match | Glob |

**Key difference from Sourcegraph:** Augment has one tool (semantic search) vs Sourcegraph's 14 specialized tools. Augment works on local code; Sourcegraph works on remotely indexed repos.

---

### GitHub MCP Server (`github-remote-direct`)

**What it provides:** GitHub's official MCP server exposing repository operations — code search, file reading, tree browsing, commit history, and branch/tag operations via the GitHub API.

**Transport:** stdio via `github-mcp-server` binary (pre-built Go binary from [github/github-mcp-server](https://github.com/github/github-mcp-server))

**Code access:** Remote only (same as Sourcegraph). The agent has no local source code and must use GitHub API tools for all code discovery and reading.

**Tools available:**
| Tool | Purpose |
|------|---------|
| `search_code` | Keyword search with GitHub code search syntax |
| `get_file_contents` | Read file from repository |
| `get_repository_tree` | Browse directory structure |
| `search_repositories` | Find repositories |
| `list_commits` | View commit history |
| `get_commit` | View commit details and diff |
| `list_branches` | List branches |
| `list_tags` | List tags |

**Auth:** `GITHUB_TOKEN` (Personal Access Token with `repo` scope).

**Search syntax:** GitHub code search uses qualifiers:
```
repo:OWNER/REPO          # Scope to specific repository (always do this)
language:python           # Filter by language
path:src/api/             # Filter by directory
content:"exact phrase"    # Exact string match
NOT test                  # Exclude terms
```

**Key differences from Sourcegraph:**
- Keyword search only (no semantic/NL search)
- No code navigation (no go-to-definition, find-references)
- No commit content search or diff search
- No deep semantic analysis
- Simpler setup (single binary, GitHub PAT)

---

## Comparison Summary

| Capability | Sourcegraph | Augment | GitHub |
|-----------|:-----------:|:-------:|:------:|
| Keyword search | `keyword_search` | — | `search_code` |
| Semantic search | `nls_search` | `codebase-retrieval` | — |
| Read files | `read_file` | Local Read tool | `get_file_contents` |
| Browse structure | `list_files` | Local Glob tool | `get_repository_tree` |
| Go to definition | `go_to_definition` | — | — |
| Find references | `find_references` | — | — |
| Commit search | `commit_search` | — | `list_commits` |
| Diff search | `diff_search` | — | — |
| Deep analysis | `deepsearch` | — | — |
| Local code access | No | Yes | No |
| Tool count | 14 | 1 | 8 |

## Adding a New MCP Configuration

To add a new MCP server:

1. **Agent code** (`agents/claude_baseline_agent.py`):
   - Add a preamble template constant (instruction text for the agent)
   - Add a `_setup_{name}_mcp()` method (creates `.mcp.json`, installs server)
   - Add routing in `setup()` and `create_run_agent_commands()`

2. **Config mapping** (`configs/_common.sh`):
   - Add to `config_to_mcp_type()` case statement
   - Add to `validate_config_name()` whitelist

3. **Standalone runner** (`scripts/running/daytona_runner.py`):
   - Add to `CONFIG_DOCKERFILE_MAP` and `CONFIG_INSTRUCTION_MAP`
   - Add `_configure_{name}_mcp()` method
   - Add credential loading

4. **IR metrics** (`scripts/evaluation/normalize_retrieval_events.py`):
   - Add tool name mappings to `_MCP_TOOL_CATEGORIES`
   - Update `_is_mcp()` and `_is_retrieval_tool()`
