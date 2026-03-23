"""Sourcegraph MCP server configuration.

Provides code intelligence via 14 specialized tools: keyword search, semantic
search, file reading, symbol navigation, commit/diff search, and deep analysis.

Transport: HTTP (to Sourcegraph instance) or stdio (npx @sourcegraph/mcp-server)
Code access: Remote only — agent workspace has no local source code.
Auth: SOURCEGRAPH_ACCESS_TOKEN or SRC_ACCESS_TOKEN environment variable.
"""

import json
import logging
import os
from pathlib import Path

from harbor.environments.base import BaseEnvironment

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Preamble & system prompt templates
# ---------------------------------------------------------------------------

TOOL_REFERENCE = """# Sourcegraph MCP Tools

Available tools for searching the remote repository:

- `keyword_search` — exact keyword/pattern search across files. Use `repo:^<repo>$` filter.
- `nls_search` — semantic/fuzzy search (broader matching, good for exploratory queries)
- `read_file` — read file contents from the indexed repository
- `list_files` — list directory contents
- `list_repos` — search and list available repositories
- `go_to_definition` — jump to a symbol's definition (cross-repo support)
- `find_references` — find all usages of a symbol
- `commit_search` — search commit history by message, author, or content
- `diff_search` — search code changes (added/removed lines)
- `compare_revisions` — compare two branches/commits/tags
- `deepsearch` — AI-powered deep analysis (async: returns a polling link)
- `deepsearch_read` — read Deep Search results (call 60+ seconds after deepsearch)

Note: Sourcegraph indexes the remote repository. Local source files are not present — use Sourcegraph to read code.
"""

PREAMBLE_TEMPLATE = """# IMPORTANT: Source Code Access

**Local source files are not present.** Your workspace does not contain source code. You **MUST** use Sourcegraph MCP tools to discover, read, and understand code before making any changes.

{repo_scope}

## Required Workflow

1. **Search first** — Use MCP tools to find relevant files and understand existing patterns
2. **Read remotely** — Use `sg_read_file` to read full file contents from Sourcegraph
{workflow_tail}

## Tool Selection

| Goal | Tool |
|------|------|
| Exact symbol/string | `sg_keyword_search` |
| Concepts/semantic search | `sg_nls_search` |
| Trace usage/callers | `sg_find_references` |
| See implementation | `sg_go_to_definition` |
| Read full file | `sg_read_file` |
| Browse structure | `sg_list_files` |
| Find repos | `sg_list_repos` |
| Search commits | `sg_commit_search` |
| Track changes | `sg_diff_search` |
| Compare versions | `sg_compare_revisions` |

**Decision logic:**
1. Know the exact symbol? → `sg_keyword_search`
2. Know the concept, not the name? → `sg_nls_search`
3. Need definition of a symbol? → `sg_go_to_definition`
4. Need all callers/references? → `sg_find_references`
5. Need full file content? → `sg_read_file`

## Scoping (Always Do This)

```
repo:^github.com/ORG/REPO$           # Exact repo (preferred)
repo:github.com/ORG/                 # All repos in org
file:.*\\.ts$                         # TypeScript only
file:src/api/                        # Specific directory
```

Start narrow. Expand only if results are empty.

## Efficiency Rules

- Chain searches logically: search → read → references → definition
- Don't re-search for the same pattern; use results from prior calls
- Prefer `sg_keyword_search` over `sg_nls_search` when you have exact terms
- Read 2-3 related files before synthesising, rather than one at a time
- Don't read 20+ remote files without writing code — once you understand the pattern, start implementing

## If Stuck

If MCP search returns no results:
1. Broaden the search query (synonyms, partial identifiers)
2. Try `sg_nls_search` for semantic matching
3. Use `sg_list_files` to browse the directory structure
4. Use `sg_list_repos` to verify the repository name

---

"""


def build_system_prompt(repo_display: str, repo_list: list[str] | None = None) -> str:
    """Build the system prompt snippet for Sourcegraph MCP."""
    if repo_list:
        lines = ["Sourcegraph repositories (version-pinned mirrors):"]
        for repo in repo_list:
            lines.append(f"  - github.com/{repo} (filter: repo:^github.com/{repo}$)")
        repo_filter = "\n".join(lines)
    elif repo_display != "the codebase":
        repo_filter = (
            f"Sourcegraph repository: github.com/{repo_display}\n"
            f"For keyword_search: repo:^github.com/{repo_display}$ YourSearchTerm"
        )
    else:
        repo_filter = "Use list_repos to discover available repositories first."

    return (
        "IMPORTANT: Local source files are not present. You MUST use Sourcegraph MCP tools "
        "to discover and read code, then create or edit local files based on what you learn. "
        "Run tests locally to verify your changes. After completing edits, also write "
        '/workspace/answer.json with "analysis" (summary, files_examined, reasoning) '
        'and "changes" (file, description, diff) arrays.\n\n'
        f"{repo_filter}"
    )


async def setup(agent, environment: BaseEnvironment) -> None:
    """Configure Sourcegraph MCP in the container (HTTP transport)."""
    sg_url = (
        os.environ.get("SOURCEGRAPH_URL")
        or os.environ.get("SRC_ENDPOINT")
        or "https://sourcegraph.sourcegraph.com"
    )
    sg_token = (
        os.environ.get("SOURCEGRAPH_ACCESS_TOKEN")
        or os.environ.get("SRC_ACCESS_TOKEN")
        or ""
    )

    if not sg_token:
        logger.warning("SOURCEGRAPH_ACCESS_TOKEN not found. Skipping MCP setup.")
        return

    if not sg_url.startswith(("http://", "https://")):
        sg_url = f"https://{sg_url}"
    sg_url = sg_url.rstrip("/")

    await environment.exec("export NODE_TLS_REJECT_UNAUTHORIZED=0")
    await environment.exec("mkdir -p /logs/agent/sessions")

    mcp_config = {
        "mcpServers": {
            "sourcegraph": {
                "type": "http",
                "url": f"{sg_url}/.api/mcp/v1",
                "headers": {"Authorization": f"token {sg_token}"},
            }
        }
    }

    mcp_config_path = agent.logs_dir / ".mcp.json"
    with open(mcp_config_path, "w") as f:
        json.dump(mcp_config, f, indent=2)

    await environment.upload_file(
        source_path=mcp_config_path, target_path="/logs/agent/sessions/.mcp.json"
    )
    logger.info(f"Sourcegraph MCP configured at /logs/agent/sessions/ ({sg_url})")
