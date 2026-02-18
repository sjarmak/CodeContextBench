"""MCP configuration templates.

Provides pre-built configurations for common MCP servers.
"""

from __future__ import annotations

import os
import re


def expand_template_vars(template: str, extra_vars: dict[str, str] | None = None) -> str:
    """Expand ${VAR} placeholders with environment variables.
    
    Args:
        template: String with ${VAR} placeholders
        extra_vars: Additional variables to use (override env vars)
        
    Returns:
        Expanded string
    """
    vars_dict = dict(os.environ)
    if extra_vars:
        vars_dict.update(extra_vars)
    
    def replace(match):
        var_name = match.group(1)
        return vars_dict.get(var_name, match.group(0))
    
    return re.sub(r'\$\{([^}]+)\}', replace, template)


def build_deepsearch_config(
    workdir: str | None = None,
    url: str | None = None,
    token: str | None = None
) -> dict:
    """Build Deep Search MCP configuration.
    
    Args:
        workdir: Working directory (for {workdir} templating)
        url: Deep Search URL (defaults to Sourcegraph)
        token: Authentication token
        
    Returns:
        MCP configuration dict for .mcp.json
    """
    if url is None:
        sg_url = os.environ.get(
            "SOURCEGRAPH_URL",
            os.environ.get("SRC_ENDPOINT", "https://sourcegraph.sourcegraph.com")
        )
        if not sg_url.startswith(("http://", "https://")):
            sg_url = f"https://{sg_url}"
        url = f"{sg_url.rstrip('/')}/.api/mcp/deepsearch"
    
    if token is None:
        token = os.environ.get(
            "SOURCEGRAPH_ACCESS_TOKEN",
            os.environ.get("SRC_ACCESS_TOKEN", "")
        )
    
    if not token:
        raise ValueError("No token provided and SOURCEGRAPH_ACCESS_TOKEN not set")
    
    return {
        "mcpServers": {
            "deepsearch": {
                "type": "http",
                "url": url,
                "headers": {"Authorization": f"token {token}"}
            }
        }
    }


def build_sourcegraph_config(
    url: str | None = None,
    token: str | None = None
) -> dict:
    """Build full Sourcegraph MCP configuration.
    
    Args:
        url: Sourcegraph MCP URL
        token: Authentication token
        
    Returns:
        MCP configuration dict for .mcp.json
    """
    if url is None:
        sg_url = os.environ.get(
            "SOURCEGRAPH_URL",
            os.environ.get("SRC_ENDPOINT", "https://sourcegraph.sourcegraph.com")
        )
        if not sg_url.startswith(("http://", "https://")):
            sg_url = f"https://{sg_url}"
        url = f"{sg_url.rstrip('/')}/.api/mcp/v1"
    
    if token is None:
        token = os.environ.get(
            "SOURCEGRAPH_ACCESS_TOKEN",
            os.environ.get("SRC_ACCESS_TOKEN", "")
        )
    
    if not token:
        raise ValueError("No token provided and SOURCEGRAPH_ACCESS_TOKEN not set")
    
    return {
        "mcpServers": {
            "sourcegraph": {
                "type": "http",
                "url": url,
                "headers": {"Authorization": f"token {token}"}
            }
        }
    }


def build_custom_mcp_config(
    server_name: str,
    server_config: dict,
    workdir: str | None = None
) -> dict:
    """Build MCP configuration from a custom server config.
    
    Args:
        server_name: Name for the MCP server
        server_config: Server configuration dict
        workdir: Working directory for {workdir} templating
        
    Returns:
        MCP configuration dict for .mcp.json
    """
    config = {}
    
    if server_config.get("type") == "http":
        url_template = server_config.get("url_template", "")
        url = expand_template_vars(url_template)
        
        headers = {}
        for key, value in server_config.get("headers", {}).items():
            headers[key] = expand_template_vars(value)
        
        config = {
            "type": "http",
            "url": url,
            "headers": headers
        }
    
    elif server_config.get("type") == "stdio":
        command = server_config.get("command", "")
        args = server_config.get("args", [])
        
        if workdir:
            args = [arg.replace("{workdir}", workdir) for arg in args]
        
        env = {}
        for key, value in server_config.get("env", {}).items():
            env[key] = expand_template_vars(value)
        
        config = {
            "command": command,
            "args": args,
            "env": env
        }
    
    return {
        "mcpServers": {
            server_name: config
        }
    }
