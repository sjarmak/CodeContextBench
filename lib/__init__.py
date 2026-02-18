"""V2 Evaluation Runner - Parallel scaffolding for MCP vs baseline comparisons.

This module provides a new evaluation runner that:
1. Expands experiment matrices (benchmark × model × mcp_mode × seed)
2. Pairs MCP and baseline runs with strict invariant matching
3. Produces canonical, self-describing output artifacts
4. Operates headlessly with per-run MCP configuration

Usage:
    run-eval run -c configs/experiment.yaml
    run-eval dry-run -c configs/experiment.yaml
    run-eval export -m runs/<experiment_id>/manifest.json
"""

__version__ = "1.0.0"
__all__ = [
    "ExperimentConfig",
    "MatrixExpander",
    "MCPConfigurator",
    "HarborExecutor",
    "V2Exporter",
]


def __getattr__(name):
    """Lazy import to avoid circular dependencies."""
    if name == "ExperimentConfig":
        from lib.config.schema import ExperimentConfig
        return ExperimentConfig
    elif name == "MatrixExpander":
        from lib.matrix.expander import MatrixExpander
        return MatrixExpander
    elif name == "MCPConfigurator":
        from lib.mcp.configurator import MCPConfigurator
        return MCPConfigurator
    elif name == "HarborExecutor":
        from lib.runner.executor import HarborExecutor
        return HarborExecutor
    elif name == "V2Exporter":
        from lib.exporter.canonical import V2Exporter
        return V2Exporter
    raise AttributeError(f"module 'v2' has no attribute '{name}'")
