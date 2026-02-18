"""MCP Configurator - manages per-run MCP configuration.

Handles the injection and removal of MCP configuration for each run,
ensuring clean baseline vs MCP comparisons.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from lib.mcp.templates import (
    build_deepsearch_config,
    build_sourcegraph_config,
    build_custom_mcp_config,
)


@dataclass
class MCPConfigResult:
    """Result of MCP configuration for a run."""
    mcp_enabled: bool
    mcp_mode: str
    mcp_config_path: Path | None = None
    mcp_config_hash: str | None = None
    mcp_servers: list[str] = field(default_factory=list)
    env_vars: dict[str, str] = field(default_factory=dict)
    claude_md_path: Path | None = None


class MCPConfigurator:
    """Manages MCP configuration injection/removal per run.
    
    This class ensures:
    - Baseline runs have NO MCP configuration (clean state)
    - MCP runs have proper .mcp.json and environment variables
    - Configuration is deterministic and hashable
    """
    
    BASELINE_MODES = {"baseline", "none"}
    BUILTIN_MCP_MODES = {"deepsearch", "deepsearch_hybrid", "sourcegraph", "sourcegraph_full", "sourcegraph_base"}
    
    def __init__(self, logs_dir: Path | None = None):
        """Initialize the configurator.
        
        Args:
            logs_dir: Directory for temporary config files
        """
        self.logs_dir = logs_dir or Path.cwd() / ".v2_mcp_configs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
    
    def configure_for_run(
        self,
        workspace_dir: Path,
        mcp_mode: str,
        mcp_server_config: dict[str, Any] | None = None,
        workdir: str | None = None
    ) -> MCPConfigResult:
        """Configure MCP for a run.
        
        For baseline mode:
          - Ensures no .mcp.json exists
          - Sets BASELINE_MCP_TYPE=none
          
        For MCP modes:
          - Writes .mcp.json with server configs
          - Sets appropriate environment variables
          - Optionally writes CLAUDE.md with instructions
        
        Args:
            workspace_dir: Directory where .mcp.json should be written
            mcp_mode: The MCP mode (baseline, deepsearch, deepsearch_hybrid, etc.)
            mcp_server_config: Custom MCP server configuration
            workdir: Working directory for {workdir} templating
            
        Returns:
            MCPConfigResult with configuration details
        """
        workspace_dir = Path(workspace_dir)
        workspace_dir.mkdir(parents=True, exist_ok=True)
        
        if mcp_mode.lower() in self.BASELINE_MODES:
            return self._configure_baseline(workspace_dir)
        else:
            return self._configure_mcp(
                workspace_dir, mcp_mode, mcp_server_config, workdir
            )
    
    def _configure_baseline(self, workspace_dir: Path) -> MCPConfigResult:
        """Configure for baseline (no MCP) run.
        
        Ensures clean state with no MCP configuration.
        """
        mcp_json_path = workspace_dir / ".mcp.json"
        if mcp_json_path.exists():
            mcp_json_path.unlink()
        
        claude_md_path = workspace_dir / "CLAUDE.md"
        if claude_md_path.exists():
            existing_content = claude_md_path.read_text()
            if "MCP" in existing_content or "Deep Search" in existing_content:
                claude_md_path.unlink()
        
        return MCPConfigResult(
            mcp_enabled=False,
            mcp_mode="baseline",
            mcp_config_path=None,
            mcp_config_hash=None,
            mcp_servers=[],
            env_vars={
                "BASELINE_MCP_TYPE": "none"
            }
        )
    
    def _configure_mcp(
        self,
        workspace_dir: Path,
        mcp_mode: str,
        mcp_server_config: dict[str, Any] | None,
        workdir: str | None
    ) -> MCPConfigResult:
        """Configure for MCP-enabled run.
        
        Writes .mcp.json and sets environment variables.
        """
        if mcp_mode in ("deepsearch", "deepsearch_hybrid"):
            mcp_config = build_deepsearch_config(workdir=workdir)
        elif mcp_mode in ("sourcegraph", "sourcegraph_full", "sourcegraph_base"):
            mcp_config = build_sourcegraph_config()
        elif mcp_server_config:
            mcp_config = build_custom_mcp_config(
                server_name=mcp_mode,
                server_config=mcp_server_config,
                workdir=workdir
            )
        else:
            raise ValueError(f"Unknown MCP mode and no server config: {mcp_mode}")
        
        mcp_json_path = workspace_dir / ".mcp.json"
        with open(mcp_json_path, "w") as f:
            json.dump(mcp_config, f, indent=2)
        
        config_hash = hashlib.sha256(
            json.dumps(mcp_config, sort_keys=True).encode()
        ).hexdigest()
        
        env_vars = {
            "BASELINE_MCP_TYPE": mcp_mode,
            "NODE_TLS_REJECT_UNAUTHORIZED": "0"
        }
        
        claude_md_path = self._write_claude_md(workspace_dir, mcp_mode)
        
        servers = list(mcp_config.get("mcpServers", {}).keys())
        
        return MCPConfigResult(
            mcp_enabled=True,
            mcp_mode=mcp_mode,
            mcp_config_path=mcp_json_path,
            mcp_config_hash=f"sha256:{config_hash}",
            mcp_servers=servers,
            env_vars=env_vars,
            claude_md_path=claude_md_path
        )
    
    def _write_claude_md(self, workspace_dir: Path, mcp_mode: str) -> Path | None:
        """Write CLAUDE.md with MCP-specific instructions."""
        if mcp_mode == "deepsearch":
            content = self._get_deepsearch_claude_md()
        elif mcp_mode == "deepsearch_hybrid":
            content = self._get_deepsearch_hybrid_claude_md()
        elif mcp_mode == "sourcegraph":
            content = self._get_sourcegraph_claude_md()
        elif mcp_mode in ("sourcegraph_full", "sourcegraph_base"):
            content = self._get_sourcegraph_full_claude_md()
        else:
            return None
        
        claude_md_path = workspace_dir / "CLAUDE.md"
        with open(claude_md_path, "w") as f:
            f.write(content)
        
        return claude_md_path
    
    def _get_deepsearch_claude_md(self) -> str:
        """Get CLAUDE.md content for deepsearch mode."""
        return """# Deep Search MCP: Code Discovery Workflow

## Available Tools

You have **only** these tools available for this task:
- `Bash` - For running commands (tests, compilation)
- `Read` - For reading files
- `Edit` - For editing files

**Note:** Grep, Glob, and shell search commands (grep/rg/ag/find/fd) are NOT available.

## MCP Tool (use this for code discovery)

- `mcp__deepsearch__deepsearch` - Deep semantic code search (understands relationships and context)

## Recommended Workflow

1. **Start with Deep Search** to understand the codebase and locate relevant code
   - Call `mcp__deepsearch__deepsearch(query="...")` with a description of what you need to find
   - Deep Search returns relevant code snippets and file locations
   - Example: `mcp__deepsearch__deepsearch(query="Where is the bug handling for TypeErrors?")`

2. **Read relevant files** using the `Read` tool
   - Only open files identified by Deep Search results
   - Avoid random exploration (search tools are blocked)

3. **Make changes** using the `Edit` tool

4. **Verify** using the `Bash` tool (tests, compilation)

## Why Deep Search First?

1. The codebase is fully indexed in Sourcegraph
2. Deep Search understands semantic code relationships and context
3. Local grep only does pattern matching and cannot understand relationships
4. Deep Search finds the right code immediately without random file exploration

## Important Notes

- You MUST use Deep Search before trying to read many files
- Search commands are blocked in Bash (you can't use grep, rg, find, etc.)
- This forces strategic code exploration via Deep Search MCP
"""

    def _get_deepsearch_hybrid_claude_md(self) -> str:
        """Get CLAUDE.md content for deepsearch_hybrid mode."""
        return """# Deep Search MCP with Hybrid Strategy: Code Discovery Workflow

## Available Tools

You have **ALL** of these tools available:
- `Bash` - For running commands (tests, compilation, local search)
- `Read` - For reading files
- `Edit` - For editing files
- `Grep` - For local pattern matching
- `Glob` - For local file pattern matching
- `mcp__deepsearch__deepsearch` - For deep semantic code search

## Strategic Hybrid Approach

Use this decision logic to pick the right tool:

### When to Use Deep Search MCP First:
1. **Understanding relationships** - "Where is this feature implemented across multiple files?"
2. **Architecture questions** - "How do components A and B interact?"
3. **Finding implementations** - "Where is the handler for X functionality?"
4. **Context-dependent queries** - "What's the pattern for error handling in this codebase?"
5. **Semantic understanding** - "Find all places where this concept is used"

### When to Use Local Search (Grep/Glob/Bash):
1. **Quick file lookups** - "Does src/module.ts exist?"
2. **Pattern verification** - "Is the string 'TODO' in this file?"
3. **File type filtering** - "Find all .test.ts files"
4. **Quick path checks** - Verify locations already identified by Deep Search
5. **Rapid iteration** - Fast verification during implementation

## Recommended Workflow

1. **Start with Deep Search for codebase exploration**
   - Call `mcp__deepsearch__deepsearch(query="...")` with your question
   - Deep Search returns relevant code snippets and file locations with context

2. **Use local search for quick verification and tactical lookups**
   - Use `Grep` or `Bash grep` to verify patterns
   - Use `Glob` or `Bash find` to quickly locate files by name/pattern
   - Use `Read` to open files identified by Deep Search

3. **Make changes using the `Edit` tool**

4. **Verify using the `Bash` tool**
   - Run tests, compile, validate your fixes

## Why This Hybrid Approach Works

1. **Deep Search provides semantic understanding** - Understands code relationships, not just text patterns
2. **Local tools provide speed** - Grep and Glob are extremely fast for simple pattern matching
3. **Agent decides strategically** - You pick the right tool for each question
4. **Combined strengths** - Semantic understanding + local efficiency = optimal performance
"""

    def _get_sourcegraph_claude_md(self) -> str:
        """Get CLAUDE.md content for sourcegraph mode."""
        return """# Sourcegraph MCP: Code Discovery Workflow

## Available Tools

You have **only** these tools available for this task:
- `Bash` - For running commands (tests, compilation)
- `Read` - For reading files
- `Edit` - For editing files

**Note:** Grep, Glob, and shell search commands are NOT available.

## MCP Tools (use these for code discovery)

- `mcp__sourcegraph__sg_keyword_search` - Exact string/regex matching (use for specific symbols)
- `mcp__sourcegraph__sg_nls_search` - Natural language search (use for conceptual queries)
- `mcp__sourcegraph__sg_read_file` - Read indexed files
- `mcp__sourcegraph__sg_deepsearch` - Deep semantic code search

## Recommended Workflow

1. **Run Sourcegraph MCP search** to find candidate files/locations
2. **Open only the relevant files/regions** needed to implement the fix
3. If MCP search returns no results, broaden the search query before opening more files
4. **Make changes** using the `Edit` tool
5. **Verify** using the `Bash` tool

## Important Notes

- You MUST use Sourcegraph MCP search before trying to read many files
- Search commands are blocked in Bash
- This forces strategic code exploration via Sourcegraph MCP
"""

    def _get_sourcegraph_full_claude_md(self) -> str:
        """Get CLAUDE.md content for sourcegraph_full mode."""
        return """# MANDATORY: Use Sourcegraph MCP for Code Navigation

You MUST use Sourcegraph MCP tools as your PRIMARY method for code discovery.
Local search tools (Grep, Glob) are available ONLY for quick verification.

**Performance data:** Aggressive MCP usage is 40% faster than local-only search.

## Sourcegraph MCP Tool Selection Guide

| Goal | Tool | Example |
|------|------|---------|
| Find exact symbol/string | `mcp__sourcegraph__sg_keyword_search` | "func handleAuth", "ErrorCode" |
| Conceptual/semantic search | `mcp__sourcegraph__sg_nls_search` | "authentication middleware" |
| Deep semantic analysis | `mcp__sourcegraph__sg_deepsearch` | "How does auth flow work?" |
| Read indexed file | `mcp__sourcegraph__sg_read_file` | Read a file from the index |
| Jump to definition | `mcp__sourcegraph__sg_go_to_definition` | Find where a function is defined |
| Find all references | `mcp__sourcegraph__sg_find_references` | Find all callers of a function |
| List files in path | `mcp__sourcegraph__sg_list_files` | Browse directory structure |
| Search commits | `mcp__sourcegraph__sg_commit_search` | Find when a change was introduced |
| Search diffs | `mcp__sourcegraph__sg_diff_search` | Find what changed in a commit |
| Compare revisions | `mcp__sourcegraph__sg_compare_revisions` | See differences between versions |

## Decision Logic

BEFORE using any local search tool, ask:
1. "Can sg_keyword_search find this exact string?" → YES → use it
2. "Do I need to understand relationships?" → YES → use sg_nls_search or sg_deepsearch
3. "Do I need the definition of this symbol?" → YES → use sg_go_to_definition
4. "Do I need all callers/references?" → YES → use sg_find_references

Use local tools (Grep, Glob) ONLY for:
- Quick verification of MCP results in local files
- Checking if a specific file exists locally
- Running tests (Bash)

## Anti-Patterns (DO NOT DO THESE)

- ❌ Using Grep/rg/find BEFORE trying Sourcegraph MCP
- ❌ Randomly exploring directories instead of using sg_list_files
- ❌ Using Bash grep when sg_keyword_search would work
- ❌ Ignoring MCP tools and defaulting to local-only workflow

## Important Notes

- You MUST use Sourcegraph MCP as your first choice for ALL code discovery
- Local search is available but should be secondary
- Verify MCP results against local files (local code is authoritative)
"""

    def get_env_for_run(self, result: MCPConfigResult) -> dict[str, str]:
        """Get full environment variables for a run.
        
        Combines MCP-specific vars with API keys from current environment.
        """
        env = dict(result.env_vars)
        
        if os.environ.get("ANTHROPIC_API_KEY"):
            env["ANTHROPIC_API_KEY"] = os.environ["ANTHROPIC_API_KEY"]
        if os.environ.get("OPENAI_API_KEY"):
            env["OPENAI_API_KEY"] = os.environ["OPENAI_API_KEY"]
        if os.environ.get("SOURCEGRAPH_ACCESS_TOKEN"):
            env["SOURCEGRAPH_ACCESS_TOKEN"] = os.environ["SOURCEGRAPH_ACCESS_TOKEN"]
        
        return env
    
    def cleanup(self, workspace_dir: Path) -> None:
        """Clean up MCP configuration from a workspace."""
        mcp_json = workspace_dir / ".mcp.json"
        if mcp_json.exists():
            mcp_json.unlink()
        
        claude_md = workspace_dir / "CLAUDE.md"
        if claude_md.exists():
            claude_md.unlink()
