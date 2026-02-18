"""V2 Experiment Configuration Schema.

Pydantic models defining the structure of v2 experiment YAML files.
"""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class RunCategory(str, Enum):
    """Categories for organizing run output directories."""
    OFFICIAL = "official"
    TROUBLESHOOTING = "troubleshooting"
    EXPERIMENT = "experiment"


class TaskSelectorType(str, Enum):
    """Types of task selection strategies."""
    ALL = "all"
    EXPLICIT = "explicit"
    RANDOM_SAMPLE = "random_sample"
    TAGS = "tags"
    FILE = "file"


class TaskSelector(BaseModel):
    """Defines how tasks are selected from a benchmark."""
    type: TaskSelectorType = TaskSelectorType.ALL
    task_ids: list[str] | None = None
    sample_size: int | None = None
    seed: int | None = Field(default=42, description="Random seed for sampling")
    include_tags: list[str] | None = None
    exclude_tags: list[str] | None = None
    tasks_file: str | None = Field(default=None, description="Path to file with task IDs")
    
    @field_validator("task_ids")
    @classmethod
    def validate_explicit_tasks(cls, v, info):
        if info.data.get("type") == TaskSelectorType.EXPLICIT and not v:
            raise ValueError("task_ids required when type is 'explicit'")
        return v
    
    @field_validator("sample_size")
    @classmethod
    def validate_sample_size(cls, v, info):
        if info.data.get("type") == TaskSelectorType.RANDOM_SAMPLE and not v:
            raise ValueError("sample_size required when type is 'random_sample'")
        return v


class BenchmarkConfig(BaseModel):
    """Configuration for a benchmark dataset."""
    name: str = Field(..., description="Benchmark name (e.g., 'swebenchpro')")
    version: str = Field(default="1.0", description="Benchmark version")
    registry_url: str = Field(
        default="https://raw.githubusercontent.com/laude-institute/harbor/refs/heads/main/registry.json",
        description="Harbor registry URL"
    )
    task_selector: TaskSelector = Field(default_factory=TaskSelector)


class AgentConfig(BaseModel):
    """Agent configuration."""
    import_path: str = Field(
        default="agents.claude_baseline_agent:BaselineClaudeCodeAgent",
        description="Python import path to agent class"
    )
    version: str = Field(default="1.0.0", description="Agent version for tracking")
    auth_mode: Literal["api", "subscription"] = Field(
        default="api",
        description="Authentication mode: 'api' uses ANTHROPIC_API_KEY, 'subscription' uses ~/.claude/ credentials"
    )
    auth_json_path: str | None = Field(
        default=None,
        description="Path to Claude Code subscription credentials JSON (overrides default ~/.claude/auth.json)"
    )
    kwargs: dict = Field(default_factory=dict, description="Additional agent kwargs")


class MCPServerConfig(BaseModel):
    """MCP server configuration."""
    type: Literal["http", "stdio"] = Field(default="http", description="Transport type")
    url_template: str | None = Field(
        default=None,
        description="URL template with ${ENV_VAR} placeholders"
    )
    command: str | None = Field(default=None, description="Command for stdio transport")
    args: list[str] | None = Field(default=None, description="Command arguments")
    headers: dict[str, str] = Field(default_factory=dict, description="HTTP headers")
    env: dict[str, str] = Field(default_factory=dict, description="Environment variables")


class EnvironmentConfig(BaseModel):
    """Docker environment configuration."""
    type: Literal["docker", "local"] = Field(default="docker")
    delete_containers: bool = Field(default=False)
    image: str | None = Field(default=None, description="Custom Docker image")
    cpus: int | None = Field(default=None)
    memory_mb: int | None = Field(default=None)


class ExecutionConfig(BaseModel):
    """Execution settings."""
    concurrency: int = Field(default=1, ge=1, description="Parallel trials per run")
    timeout_seconds: int = Field(default=3600, ge=60, description="Per-task timeout")
    max_retries: int = Field(default=0, ge=0)
    environment: EnvironmentConfig = Field(default_factory=EnvironmentConfig)


class OutputConfig(BaseModel):
    """Output settings."""
    root_dir: str = Field(default="runs", description="V2 output root directory")
    export_on_complete: bool = Field(
        default=True,
        description="Auto-run exporter after each run"
    )
    keep_harbor_artifacts: bool = Field(
        default=True,
        description="Keep original Harbor job directories"
    )


class PairingConfig(BaseModel):
    """Configuration for MCP vs baseline pairing."""
    enabled: bool = Field(default=True, description="Create formal pairs")
    baseline_mode: str = Field(
        default="baseline",
        description="Which mcp_mode is the baseline"
    )


class ExperimentConfig(BaseModel):
    """Root configuration for a v2 experiment."""
    experiment_name: str = Field(..., description="Unique experiment name")
    description: str | None = Field(default=None)
    run_category: RunCategory = Field(
        default=RunCategory.EXPERIMENT,
        description="Category for organizing output: official, troubleshooting, or experiment"
    )
    
    benchmarks: list[BenchmarkConfig] = Field(
        ...,
        min_length=1,
        description="Benchmarks to run"
    )
    
    agent: AgentConfig = Field(default_factory=AgentConfig)
    
    models: list[str] = Field(
        ...,
        min_length=1,
        description="Model identifiers (e.g., 'anthropic/claude-opus-4-5')"
    )
    
    mcp_modes: list[str] = Field(
        default=["baseline", "sourcegraph_full"],
        min_length=1,
        description="MCP modes to compare"
    )
    
    mcp_servers: dict[str, MCPServerConfig] = Field(
        default_factory=dict,
        description="MCP server configurations by mode name"
    )
    
    seeds: list[int] = Field(
        default=[0],
        min_length=1,
        description="Random seeds for reproducibility"
    )
    
    execution: ExecutionConfig = Field(default_factory=ExecutionConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    pairing: PairingConfig = Field(default_factory=PairingConfig)
    
    env_vars: dict[str, str] = Field(
        default_factory=dict,
        description="Additional environment variables"
    )
    
    tags: list[str] = Field(
        default_factory=list,
        description="Tags for organizing experiments"
    )

    def get_matrix_dimensions(self) -> dict[str, int]:
        """Return counts of each matrix dimension."""
        total_tasks = sum(
            len(b.task_selector.task_ids or [])
            if b.task_selector.type == TaskSelectorType.EXPLICIT
            else (b.task_selector.sample_size or 0)
            for b in self.benchmarks
        )
        return {
            "benchmarks": len(self.benchmarks),
            "models": len(self.models),
            "mcp_modes": len(self.mcp_modes),
            "seeds": len(self.seeds),
            "tasks": total_tasks,
        }
    
    def count_total_runs(self) -> int:
        """Estimate total number of runs."""
        dims = self.get_matrix_dimensions()
        return (
            dims["benchmarks"]
            * dims["models"]
            * dims["mcp_modes"]
            * dims["seeds"]
            * max(dims["tasks"], 1)
        )
