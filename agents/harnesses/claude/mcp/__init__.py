"""MCP server configurations for the Claude Code harness.

Each module provides:
- Preamble template(s): instruction text injected for the agent
- System prompt snippet: appended via --append-system-prompt
- setup() coroutine: creates .mcp.json and installs server in the container
"""
