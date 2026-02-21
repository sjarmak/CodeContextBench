"""Config name utilities for CCB analysis scripts.

Three-dimensional config naming:
  {agent}-{source}-{verifier}
  agent:    baseline (no MCP) | mcp (Sourcegraph MCP)
  source:   local (full source) | remote (source deleted)
  verifier: direct (git changes) | artifact (review.json)

Examples:
  baseline-local-direct   = no MCP, full source, git-change verifier
  mcp-remote-direct       = MCP, source deleted, git-change verifier
  mcp-remote-artifact     = MCP, source deleted, artifact verifier
"""

import re
from pathlib import Path

# Legacy config names from existing run directories
LEGACY_CONFIGS = {
    "baseline", "sourcegraph_full", "sourcegraph_base",
    "sourcegraph_isolated", "sg_only_env",
    "sourcegraph", "deepsearch", "artifact_full",
}

# New three-dimensional config names
NEW_CONFIGS = {
    "baseline-local-direct", "mcp-remote-direct",
    "baseline-local-artifact", "mcp-remote-artifact",
}

ALL_KNOWN_CONFIGS = LEGACY_CONFIGS | NEW_CONFIGS

# Legacy MCP configs (internal mcp_type values that indicate MCP is active)
_MCP_INTERNAL = {
    "sourcegraph_full", "sourcegraph_base", "sourcegraph_isolated",
    "sourcegraph", "artifact_full", "deepsearch", "deepsearch_hybrid",
}

# Batch timestamp dirs: YYYY-MM-DD__HH-MM-SS
_BATCH_TS_RE = re.compile(r"^\d{4}-\d{2}-\d{2}__\d{2}-\d{2}-\d{2}")

# New composite name pattern
_COMPOSITE_RE = re.compile(r"^(baseline|mcp)-(local|remote)-(direct|artifact)$")

# Short display names
_SHORT_NAMES = {
    "baseline": "BL",
    "baseline-local-direct": "BL",
    "baseline-local-artifact": "BL-art",
    "sourcegraph_full": "SG_full",
    "mcp-remote-direct": "MCP",
    "mcp-remote-artifact": "MCP-art",
    "artifact_full": "MCP-art",
    "sourcegraph_base": "SG_base",
    "sourcegraph_isolated": "SG_iso",
}


def is_config_dir(name: str) -> bool:
    """Check if a directory name is a config subdirectory (not a batch timestamp)."""
    if _BATCH_TS_RE.match(name):
        return False
    if name in ALL_KNOWN_CONFIGS:
        return True
    if _COMPOSITE_RE.match(name):
        return True
    return False


def discover_configs(run_dir: Path) -> list[str]:
    """Auto-discover config subdirectories within a run directory.

    Returns sorted list of config names found. Filters out batch timestamp
    dirs, archive dirs, and non-directories.
    """
    run_dir = Path(run_dir)
    if not run_dir.is_dir():
        return []
    configs = []
    for child in run_dir.iterdir():
        if not child.is_dir():
            continue
        if child.name.startswith("archive"):
            continue
        if is_config_dir(child.name):
            configs.append(child.name)
    return sorted(configs)


def is_mcp_config(config_name: str) -> bool:
    """Check if a config name implies MCP tools are available."""
    if config_name.startswith("mcp-"):
        return True
    return config_name in _MCP_INTERNAL


def is_baseline_config(config_name: str) -> bool:
    """Check if a config name is a baseline (no MCP)."""
    return not is_mcp_config(config_name)


def config_short_name(config_name: str) -> str:
    """Abbreviated display name for a config."""
    return _SHORT_NAMES.get(config_name, config_name[:10])
