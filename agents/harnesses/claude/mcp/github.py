"""GitHub MCP server configuration.

Provides repository operations via GitHub's official MCP server: code search,
file reading, tree browsing, commit history, and branch/tag operations.

Transport: stdio via `github-mcp-server` binary
Code access: Remote only — agent workspace has no local source code.
Auth: GITHUB_TOKEN (Personal Access Token with `repo` scope).
"""

import json
import logging
import os
from pathlib import Path

from harbor.environments.base import BaseEnvironment

logger = logging.getLogger(__name__)

# Pre-built binary release URL
GITHUB_MCP_RELEASE = (
    "https://github.com/github/github-mcp-server/releases/download/"
    "v0.32.0/github-mcp-server_Linux_x86_64.tar.gz"
)

# ---------------------------------------------------------------------------
# Preamble template
# ---------------------------------------------------------------------------

PREAMBLE_TEMPLATE = """# IMPORTANT: Source Code Access

**Local source files are not present.** Your workspace does not contain source code.
You **MUST** use GitHub MCP tools to discover, read, and understand code before making
any changes.

{repo_scope}

## Required Workflow

1. **Orient** — Use `get_repository_tree` to understand the project structure
2. **Search** — Use `search_code` to find relevant files and patterns
3. **Read** — Use `get_file_contents` to read full file contents
{workflow_tail}

## Tool Selection

| Goal | Tool | Key Parameters |
|------|------|----------------|
| Browse project structure | `get_repository_tree` | `owner`, `repo`, `recursive=true`, `path_filter` |
| Find code by keyword/pattern | `search_code` | `query` with `repo:OWNER/REPO` qualifier |
| Read a specific file | `get_file_contents` | `owner`, `repo`, `path`, `ref` |
| View recent changes | `list_commits` | `owner`, `repo`, `sha` (branch) |
| See a commit's diff | `get_commit` | `owner`, `repo`, `sha`, `include_diff=true` |
| Find repos by topic | `search_repositories` | `query` |

**Decision logic:**
1. Need to understand the file layout? → `get_repository_tree` with `recursive=true`
2. Know the exact symbol or pattern? → `search_code` with `repo:OWNER/REPO symbol_name`
3. Know the concept, not the name? → `search_code` with broader terms + `language:` filter
4. Need full file content? → `get_file_contents`
5. Need change history? → `list_commits` → `get_commit`

## Search Query Syntax (`search_code`)

```
repo:OWNER/REPO                    # Scope to exact repository (ALWAYS do this)
language:python                    # Filter by language
path:src/api/                      # Filter by directory
content:"exact phrase"             # Exact string match
NOT test                           # Exclude test files
symbol_name OR alternative_name    # Boolean OR
```

**Always start** with `repo:OWNER/REPO` to scope results. Add `language:` and `path:` to narrow further.

## Scoping (Always Do This)

Every `search_code` call MUST include `repo:OWNER/REPO` to scope to the target repository.
Without scoping, GitHub searches all accessible repositories.

## Efficiency Rules

- Start with `get_repository_tree` to orient yourself, then targeted searches
- Chain: tree → search → read → edit
- Don't read 20+ remote files without writing code — once you understand the pattern, start implementing
- `search_code` is keyword-only (no semantic/NL search) — use exact terms and identifiers
- For large files (>1MB), `get_file_contents` returns a download link instead of content

## If Stuck

If `search_code` returns no results:
1. Broaden the query (drop `path:` or `language:` filters)
2. Try synonyms or partial identifiers
3. Use `get_repository_tree` with `path_filter` to browse directories
4. Verify the repo name with `search_repositories`

---

"""


def build_system_prompt(repo_display: str) -> str:
    """Build system prompt snippet for GitHub MCP."""
    if repo_display != "the codebase":
        parts = repo_display.split("/")
        if len(parts) == 2:
            owner, repo_name = parts
            repo_hint = (
                f'Target: {owner}/{repo_name}. Always use owner="{owner}", '
                f'repo="{repo_name}" in tool calls. '
                f"For search_code: repo:{owner}/{repo_name}"
            )
        else:
            repo_hint = (
                f"Target repository: {repo_display}. "
                f"Scope search_code with repo:{repo_display}"
            )
    else:
        repo_hint = "Use search_repositories to find the target repo first."

    return (
        "IMPORTANT: Local source files are not present. You MUST use GitHub MCP "
        "tools to discover and read code.\n\n"
        "Available MCP tools:\n"
        "- `search_code` — keyword search (use repo:OWNER/REPO qualifier)\n"
        "- `get_file_contents` — read file from repository (owner, repo, path, ref)\n"
        "- `get_repository_tree` — browse directory structure (owner, repo, recursive, path_filter)\n"
        "- `list_commits` — view commit history\n"
        "- `get_commit` — view commit details and diff\n\n"
        f"{repo_hint}\n\n"
        "Workflow: get_repository_tree → search_code → get_file_contents → edit locally → verify with tests.\n"
        "After completing edits, write /workspace/answer.json with analysis and changes arrays."
    )


async def setup(agent, environment: BaseEnvironment) -> None:
    """Configure GitHub MCP in the container (pre-built binary, stdio transport)."""
    github_token = os.environ.get("GITHUB_TOKEN") or ""
    if not github_token:
        logger.warning("GITHUB_TOKEN not found. Skipping GitHub MCP setup.")
        return

    await environment.exec("mkdir -p /logs/agent/sessions")

    # Install pre-built binary
    logger.info("Installing GitHub MCP server binary")
    install_result = await environment.exec(
        f"curl -sL {GITHUB_MCP_RELEASE} "
        "| tar -xz -C /usr/local/bin github-mcp-server "
        "&& chmod +x /usr/local/bin/github-mcp-server "
        "&& github-mcp-server --help 2>&1 | head -3",
        timeout_sec=120,
    )
    setup_dir = agent.logs_dir / "setup-github-mcp"
    setup_dir.mkdir(parents=True, exist_ok=True)
    (setup_dir / "return-code.txt").write_text(str(install_result.return_code))
    if install_result.stdout:
        (setup_dir / "stdout.txt").write_text(install_result.stdout)
    if install_result.return_code != 0:
        raise RuntimeError(
            f"GitHub MCP server install failed (exit {install_result.return_code}). "
            f"See {setup_dir}"
        )

    mcp_config = {
        "mcpServers": {
            "github": {
                "type": "stdio",
                "command": "github-mcp-server",
                "args": ["stdio", "--toolsets", "repos,git"],
                "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": github_token},
            }
        }
    }

    mcp_config_path = agent.logs_dir / ".mcp.json"
    with open(mcp_config_path, "w") as f:
        json.dump(mcp_config, f, indent=2)

    await environment.upload_file(
        source_path=mcp_config_path, target_path="/logs/agent/sessions/.mcp.json"
    )
    logger.info("GitHub MCP configured at /logs/agent/sessions/ via stdio binary")
