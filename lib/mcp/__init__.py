"""MCP configuration module."""

from lib.mcp.configurator import MCPConfigurator, MCPConfigResult
from lib.mcp.templates import (
    build_deepsearch_config,
    build_sourcegraph_config,
    expand_template_vars,
)

__all__ = [
    "MCPConfigurator",
    "MCPConfigResult",
    "build_deepsearch_config",
    "build_sourcegraph_config",
    "expand_template_vars",
]
