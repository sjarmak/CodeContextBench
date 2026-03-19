"""CSB Run Configuration Schema.

Defines the typed, schema-validated config file format consumed by `csb run`.

Config files are YAML with the following top-level fields::

    agent: claude          # required — "claude" | "openhands" | ...
    model: claude-sonnet-4-6   # required — short model name or full path
    augmentation: none     # optional — "none" | "sourcegraph_full" | "deepsearch"
    preamble: null         # optional — path to a custom preamble file or inline text
    task_subset: null      # optional — path to a selection JSON (default: selected_benchmark_tasks.json)
    category: staging      # optional — "staging" | "official" | "experiment"

Example minimal config::

    agent: claude
    model: claude-haiku-4-5-20251001

Example full config::

    agent: openhands
    model: claude-sonnet-4-6
    augmentation: sourcegraph_full
    task_subset: configs/smoke_test_csb_3tasks.json
    category: staging
"""

from __future__ import annotations

import os
from enum import Enum
from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field, model_validator


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class AgentName(str, Enum):
    CLAUDE = "claude"
    OPENHANDS = "openhands"
    CODEX = "codex"
    GEMINI = "gemini"
    COPILOT = "copilot"
    CURSOR = "cursor"


class AugmentationMode(str, Enum):
    NONE = "none"
    SOURCEGRAPH_FULL = "sourcegraph_full"
    DEEPSEARCH = "deepsearch"
    DEEPSEARCH_HYBRID = "deepsearch_hybrid"


class RunCategory(str, Enum):
    STAGING = "staging"
    OFFICIAL = "official"
    EXPERIMENT = "experiment"


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

# Default task subset path (relative to repo root)
_DEFAULT_SUBSET = "configs/selected_benchmark_tasks.json"

# Canonical mapping from config name to BASELINE_MCP_TYPE env var value
AUGMENTATION_TO_MCP_TYPE: dict[AugmentationMode, str] = {
    AugmentationMode.NONE: "none",
    AugmentationMode.SOURCEGRAPH_FULL: "sourcegraph_full",
    AugmentationMode.DEEPSEARCH: "deepsearch",
    AugmentationMode.DEEPSEARCH_HYBRID: "deepsearch_hybrid",
}

# Canonical config name derived from augmentation mode (matches PIPELINE_SPEC §2.1)
AUGMENTATION_TO_CONFIG_NAME: dict[AugmentationMode, str] = {
    AugmentationMode.NONE: "baseline-local-direct",
    AugmentationMode.SOURCEGRAPH_FULL: "mcp-remote-direct",
    AugmentationMode.DEEPSEARCH: "mcp-remote-direct",
    AugmentationMode.DEEPSEARCH_HYBRID: "mcp-remote-direct",
}


class RunConfig(BaseModel):
    """Typed configuration for a single CSB run.

    Agents and operators create a config file and call ``csb run config.yaml``.
    They do NOT need to know bash flags, env vars, or directory layouts.
    """

    agent: AgentName = Field(
        ...,
        description="Agent identifier (e.g. 'claude', 'openhands').",
    )
    model: str = Field(
        ...,
        description=(
            "Model short name or full provider path "
            "(e.g. 'claude-sonnet-4-6' or 'anthropic/claude-sonnet-4-6')."
        ),
    )
    augmentation: AugmentationMode = Field(
        default=AugmentationMode.NONE,
        description="MCP augmentation mode for the run.",
    )
    preamble: Optional[str] = Field(
        default=None,
        description=(
            "Path to a custom agent preamble file, or inline preamble text. "
            "Passed to the harness as AGENT_PREAMBLE env var."
        ),
    )
    task_subset: Optional[str] = Field(
        default=None,
        description=(
            "Path to a task selection JSON file "
            "(default: configs/selected_benchmark_tasks.json)."
        ),
    )
    category: RunCategory = Field(
        default=RunCategory.STAGING,
        description="Run category label written into the result directory path.",
    )
    parallel: Optional[int] = Field(
        default=None,
        description=(
            "Max concurrent task slots. Default: auto-detect from accounts "
            "(4 per available account for OpenHands, 62 per account for Claude/Daytona)."
        ),
        ge=1,
    )
    dry_run: bool = Field(
        default=False,
        description="Print planned tasks without executing.",
    )
    skip_completed: bool = Field(
        default=True,
        description=(
            "Skip tasks where validation_result.json has status=scored. "
            "Enabled by default to support safe resume."
        ),
    )

    @model_validator(mode="after")
    def normalize_model(self) -> "RunConfig":
        """Ensure the model identifier is in provider/name form."""
        model = self.model
        if "/" not in model and not model.startswith("anthropic"):
            # Normalize bare short names to full form
            if model.startswith("claude-"):
                object.__setattr__(self, "model", f"anthropic/{model}")
        return self

    def config_name(self) -> str:
        """Return the canonical config name for this run (§2.1)."""
        return AUGMENTATION_TO_CONFIG_NAME[self.augmentation]

    def mcp_type(self) -> str:
        """Return the BASELINE_MCP_TYPE value for this run."""
        return AUGMENTATION_TO_MCP_TYPE[self.augmentation]

    def resolved_task_subset(self, repo_root: Path) -> Path:
        """Resolve the task subset path to an absolute Path."""
        if self.task_subset:
            p = Path(self.task_subset)
            if not p.is_absolute():
                p = repo_root / p
        else:
            p = repo_root / _DEFAULT_SUBSET
        return p


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------

class RunConfigError(Exception):
    """Raised when a run config cannot be loaded or validated."""


def load_run_config(config_path: str | Path) -> RunConfig:
    """Load and validate a run config YAML file.

    Args:
        config_path: Path to the YAML config file.

    Returns:
        Validated :class:`RunConfig`.

    Raises:
        RunConfigError: If the file is missing, malformed, or fails schema validation.
    """
    from pydantic import ValidationError

    path = Path(config_path)
    if not path.exists():
        raise RunConfigError(f"Config file not found: {path}")
    if path.suffix.lower() not in (".yaml", ".yml"):
        raise RunConfigError(f"Config file must be YAML (.yaml/.yml): {path}")

    try:
        with open(path) as f:
            raw = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        raise RunConfigError(f"Invalid YAML in {path}: {exc}") from exc

    if raw is None:
        raise RunConfigError(f"Empty config file: {path}")
    if not isinstance(raw, dict):
        raise RunConfigError(f"Config must be a YAML mapping, got: {type(raw).__name__}")

    # Expand ${ENV_VAR} placeholders
    raw = _expand_env_vars(raw)

    try:
        return RunConfig.model_validate(raw)
    except ValidationError as exc:
        lines = []
        for err in exc.errors():
            loc = ".".join(str(x) for x in err["loc"])
            lines.append(f"  - {loc}: {err['msg']}")
        raise RunConfigError(f"Invalid config {path}:\n" + "\n".join(lines)) from exc


def validate_run_config_env(config: RunConfig) -> list[str]:
    """Check runtime environment requirements.

    Returns a list of warning strings (empty if all OK).

    Raises:
        RunConfigError: For hard failures (e.g. CSB_RUNS_DIR unset).
    """
    errors: list[str] = []
    warnings: list[str] = []

    # I-6: CSB_RUNS_DIR is mandatory
    csb_runs_dir = os.environ.get("CSB_RUNS_DIR", "")
    if not csb_runs_dir:
        errors.append(
            "CSB_RUNS_DIR is not set. "
            "Set it to an absolute path for result output (e.g. export CSB_RUNS_DIR=/home/user/runs)."
        )
    elif not Path(csb_runs_dir).is_absolute():
        errors.append(
            f"CSB_RUNS_DIR must be an absolute path, got: {csb_runs_dir!r}. "
            "Relative paths silently produce wrong result locations in worktrees."
        )

    # MCP augmentation requires SG token
    if config.augmentation != AugmentationMode.NONE:
        if not os.environ.get("SOURCEGRAPH_ACCESS_TOKEN"):
            errors.append(
                f"SOURCEGRAPH_ACCESS_TOKEN not set but required for augmentation={config.augmentation.value}"
            )

    if errors:
        raise RunConfigError(
            "Environment validation failed:\n" + "\n".join(f"  ✗ {e}" for e in errors)
        )

    return warnings


def _expand_env_vars(obj: object) -> object:
    """Recursively expand ${ENV_VAR} in strings."""
    import re

    if isinstance(obj, str):
        return re.sub(
            r"\$\{([^}]+)\}",
            lambda m: os.environ.get(m.group(1), m.group(0)),
            obj,
        )
    if isinstance(obj, dict):
        return {k: _expand_env_vars(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_expand_env_vars(item) for item in obj]
    return obj
