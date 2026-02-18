"""V2 Configuration Loader.

Loads and validates experiment YAML files.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from lib.config.schema import ExperimentConfig


# Default env file location — project root .env.local
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent  # lib/config/loader.py -> project root
DEFAULT_ENV_FILE = PROJECT_ROOT / ".env.local"


def load_env_file(env_path: Path | str | None = None) -> bool:
    """Load environment variables from a .env file.
    
    Mimics v1's `set -a; source ~/.../env.local; set +a` pattern.
    Variables are exported to os.environ.
    
    Args:
        env_path: Path to env file. Defaults to <project_root>/.env.local
        
    Returns:
        True if file was loaded, False if file not found.
    """
    path = Path(env_path) if env_path else DEFAULT_ENV_FILE
    
    if not path.exists():
        return False
    
    with open(path) as f:
        for line in f:
            line = line.strip()
            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue
            # Handle export VAR=value syntax
            if line.startswith("export "):
                line = line[7:]
            # Parse VAR=value
            if "=" in line:
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip()
                # Remove surrounding quotes if present
                if (value.startswith('"') and value.endswith('"')) or \
                   (value.startswith("'") and value.endswith("'")):
                    value = value[1:-1]
                os.environ[key] = value
    
    return True


class ConfigError(Exception):
    """Configuration loading or validation error."""
    pass


def load_config(config_path: str | Path) -> ExperimentConfig:
    """Load and validate an experiment configuration file.
    
    Args:
        config_path: Path to the YAML configuration file.
        
    Returns:
        Validated ExperimentConfig object.
        
    Raises:
        ConfigError: If the file cannot be loaded or validated.
    """
    path = Path(config_path)
    
    if not path.exists():
        raise ConfigError(f"Configuration file not found: {path}")
    
    if not path.suffix.lower() in (".yaml", ".yml"):
        raise ConfigError(f"Configuration file must be YAML: {path}")
    
    try:
        with open(path) as f:
            raw_config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigError(f"Invalid YAML in {path}: {e}")
    
    if raw_config is None:
        raise ConfigError(f"Empty configuration file: {path}")
    
    raw_config = _expand_env_vars(raw_config)
    
    try:
        config = ExperimentConfig.model_validate(raw_config)
    except ValidationError as e:
        errors = []
        for err in e.errors():
            loc = ".".join(str(x) for x in err["loc"])
            errors.append(f"  - {loc}: {err['msg']}")
        raise ConfigError(
            f"Invalid configuration in {path}:\n" + "\n".join(errors)
        )
    
    return config


def validate_config(config: ExperimentConfig) -> list[str]:
    """Validate configuration for runtime requirements.
    
    Args:
        config: The configuration to validate.
        
    Returns:
        List of warning messages (empty if all OK).
        
    Raises:
        ConfigError: If validation fails.
    """
    warnings = []
    errors = []
    
    if "baseline" not in config.mcp_modes and config.pairing.enabled:
        errors.append(
            "Pairing enabled but 'baseline' not in mcp_modes. "
            f"Baseline mode is set to '{config.pairing.baseline_mode}'."
        )
    
    for mode in config.mcp_modes:
        if mode != "baseline" and mode not in config.mcp_servers:
            if mode in ("deepsearch", "deepsearch_hybrid", "sourcegraph"):
                pass
            else:
                warnings.append(
                    f"MCP mode '{mode}' not found in mcp_servers config"
                )
    
    for model in config.models:
        if "anthropic" in model.lower() or "claude" in model.lower():
            if not os.environ.get("ANTHROPIC_API_KEY"):
                errors.append(
                    f"ANTHROPIC_API_KEY not set but required for model: {model}"
                )
        if "openai" in model.lower() or "gpt" in model.lower():
            if not os.environ.get("OPENAI_API_KEY"):
                errors.append(
                    f"OPENAI_API_KEY not set but required for model: {model}"
                )
    
    for mode in config.mcp_modes:
        if mode in ("deepsearch", "deepsearch_hybrid", "sourcegraph"):
            if not os.environ.get("SOURCEGRAPH_ACCESS_TOKEN"):
                errors.append(
                    f"SOURCEGRAPH_ACCESS_TOKEN not set but required for mode: {mode}"
                )
    
    agent_path = config.agent.import_path.split(":")[0].replace(".", "/") + ".py"
    if not Path(agent_path).exists():
        errors.append(f"Agent module not found: {agent_path}")
    
    if errors:
        raise ConfigError("Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors))
    
    return warnings


def _expand_env_vars(obj: Any) -> Any:
    """Recursively expand ${ENV_VAR} placeholders in strings."""
    if isinstance(obj, str):
        import re
        def replace_env(match):
            var_name = match.group(1)
            return os.environ.get(var_name, match.group(0))
        return re.sub(r'\$\{([^}]+)\}', replace_env, obj)
    elif isinstance(obj, dict):
        return {k: _expand_env_vars(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_expand_env_vars(item) for item in obj]
    return obj


def get_config_hash(config_path: str | Path) -> str:
    """Compute SHA256 hash of config file contents."""
    import hashlib
    content = Path(config_path).read_bytes()
    return hashlib.sha256(content).hexdigest()
