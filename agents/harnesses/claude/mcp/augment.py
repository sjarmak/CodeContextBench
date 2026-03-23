"""Augment Context Engine MCP configuration.

Provides semantic code search via a single `codebase-retrieval` tool that
indexes the local workspace using Augment's proprietary retrieval model.

Transport: stdio via `auggie --mcp --mcp-auto-workspace`
Code access: Local (augment-local-direct) or remote (augment-remote-direct).
Auth: AUGMENT_SESSION_AUTH (JSON) or AUGMENT_API_TOKEN + AUGMENT_API_URL.
"""

import json
import logging
import os
from pathlib import Path

from harbor.environments.base import BaseEnvironment

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Preamble templates
# ---------------------------------------------------------------------------

LOCAL_PREAMBLE_TEMPLATE = """# Augment Context Engine (supplementary MCP tool)

Your workspace contains the full source code. You have all standard local tools
(Read, Edit, Write, Grep, Glob, Bash). In addition, you have access to Augment's
Context Engine via the `mcp__auggie__codebase-retrieval` MCP tool, which provides
**semantic code search** over your local workspace.

{repo_scope}

## When to Use `codebase-retrieval`

| Situation | Tool |
|-----------|------|
| Know the exact symbol or filename | Grep, Glob, or Read |
| Need all occurrences of an identifier | Grep |
| Exploring unfamiliar code — "how does X work?" | `codebase-retrieval` |
| Finding related code across files/modules | `codebase-retrieval` |
| Understanding architecture or data flow | `codebase-retrieval` |
| Quick file pattern match (`*.test.ts`) | Glob |

**Decision logic:**
1. Exact identifier lookup → Grep/Glob (faster, precise)
2. Conceptual / architectural question → `codebase-retrieval` (semantic understanding)
3. Cross-file relationships or "where is this pattern used?" → `codebase-retrieval`
4. Verification of a specific file → Read

## Query Best Practices

- **Be specific**: Include exact identifiers, symbol names, error text, file paths
  - Good: "Where is the JWT validation middleware defined?"
  - Good: "How does the UserService handle password reset?"
  - Bad: "Tell me about the codebase" (too vague)
- **Start narrow**, broaden only if results are sparse
- Augment returns semantically relevant snippets — treat them as **navigation context**,
  then use Read to see the full file before editing

## Workflow

1. Use local tools (Grep, Glob, Read) for direct lookups
2. Use `codebase-retrieval` when you need to understand relationships or explore unfamiliar areas
3. Edit and verify locally (Edit, Bash for tests)
4. After completing edits, write `/workspace/answer.json` summarizing your work

---

"""

REMOTE_PREAMBLE_TEMPLATE = """# IMPORTANT: Source Code Access

**Local source files are not present.** Your workspace does not contain the full source code. You **MUST** use Augment's `codebase-retrieval` MCP tool to discover and understand code before making changes.

{repo_scope}

## Required Workflow

1. **Search first** — Use `codebase-retrieval` to locate relevant files, symbols, and patterns
2. **Read retrieved context carefully** — Treat retrieved snippets and references as discovery context
3. **Edit locally** — Use Edit, Write, and Bash to create or modify files in your working directory
4. **Verify locally** — Run tests with Bash to check your changes
5. **Produce answer.json** — After completing your edits, also write `/workspace/answer.json` summarizing your work

## Augment Retrieval Guidance

- Use `mcp__auggie__codebase-retrieval` for code discovery and cross-file understanding
- Include exact identifiers in your query: repo name, file path, symbol names, error text, API names
- If the tool accepts `directory_path`, set it to your current workspace root
- Start with a specific query, then broaden only if results are weak
- Treat retrieval output as navigation context, not as code to copy blindly

---

"""


def build_system_prompt_local(repo_display: str) -> str:
    """Build system prompt for augment-local (baseline + context engine)."""
    return (
        "You have full local source code plus the Augment Context Engine MCP tool "
        "for semantic code search.\n\n"
        "Available MCP tool:\n"
        "- `mcp__auggie__codebase-retrieval` — semantic search over your local workspace\n\n"
        "Use `codebase-retrieval` for architectural questions, cross-file relationships, "
        "and exploring unfamiliar areas.\n"
        "Use Grep/Glob/Read for exact identifier lookups and quick file access.\n"
        "Combine both: codebase-retrieval for discovery, local tools for precision."
    )


def build_system_prompt_remote(repo_display: str) -> str:
    """Build system prompt for augment-remote (no local code)."""
    if repo_display != "the codebase":
        repo_hint = f"Target repository: github.com/{repo_display}"
    else:
        repo_hint = "Determine the exact target repository before broadening retrieval."

    return (
        "IMPORTANT: Local source files are not present. You MUST use Augment's "
        "MCP retrieval tool for code discovery before making changes.\n\n"
        "Available MCP tool:\n"
        "- `mcp__auggie__codebase-retrieval` — retrieve relevant code context "
        "across the indexed repository\n\n"
        f"{repo_hint}\n\n"
        "Workflow:\n"
        "1) Use `mcp__auggie__codebase-retrieval` first to locate relevant code and patterns\n"
        "2) If the tool supports `directory_path`, pass your current workspace root\n"
        "3) Use specific queries with exact identifiers, symbols, error text, and repository names\n"
        "4) Edit and verify locally after you understand the retrieved context\n\n"
        "IMPORTANT: Augment retrieval may return broad or synthesized context if your query "
        "is vague. Narrow queries with exact identifiers are preferred."
    )


def _get_auth_env() -> dict:
    """Return environment variables for Augment authentication."""
    session_auth = os.environ.get("AUGMENT_SESSION_AUTH") or ""
    token = os.environ.get("AUGMENT_API_TOKEN") or ""
    url = os.environ.get("AUGMENT_API_URL") or ""

    if session_auth:
        return {"AUGMENT_SESSION_AUTH": session_auth}
    elif token and url:
        return {"AUGMENT_API_TOKEN": token, "AUGMENT_API_URL": url}
    return {}


async def setup(agent, environment: BaseEnvironment) -> None:
    """Configure Augment MCP in the container (stdio transport via auggie CLI)."""
    env_vars = _get_auth_env()
    if not env_vars:
        logger.warning(
            "Augment MCP credentials not found. "
            "Set AUGMENT_SESSION_AUTH or both AUGMENT_API_TOKEN and AUGMENT_API_URL."
        )
        return

    await environment.exec("mkdir -p /logs/agent/sessions")

    mcp_config = {
        "mcpServers": {
            "auggie": {
                "type": "stdio",
                "command": "auggie",
                "args": ["--mcp", "--mcp-auto-workspace"],
                "env": env_vars,
            }
        }
    }

    mcp_config_path = agent.logs_dir / ".mcp.json"
    with open(mcp_config_path, "w") as f:
        json.dump(mcp_config, f, indent=2)

    await environment.upload_file(
        source_path=mcp_config_path, target_path="/logs/agent/sessions/.mcp.json"
    )
    logger.info("Augment MCP configured at /logs/agent/sessions/ via stdio server")


async def install_cli(agent, environment: BaseEnvironment) -> None:
    """Install the Auggie CLI inside the container."""
    logger.info("Installing Auggie CLI")
    result = await environment.exec(
        "npm install -g @augmentcode/auggie@latest && auggie --version",
        timeout_sec=300,
    )
    setup_dir = agent.logs_dir / "setup-auggie"
    setup_dir.mkdir(parents=True, exist_ok=True)
    (setup_dir / "return-code.txt").write_text(str(result.return_code))
    if result.stdout:
        (setup_dir / "stdout.txt").write_text(result.stdout)
    if result.stderr:
        (setup_dir / "stderr.txt").write_text(result.stderr)
    if result.return_code != 0:
        raise RuntimeError(
            f"Auggie install failed (exit {result.return_code}). See {setup_dir}"
        )
