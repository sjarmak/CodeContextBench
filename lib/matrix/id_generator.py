"""Deterministic ID generation for v2 runs and pairs.

All IDs are derived from invariant properties using SHA256 hashing,
ensuring reproducibility and uniqueness.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime


def generate_experiment_id(
    experiment_name: str,
    config_hash: str,
    timestamp: str | None = None
) -> str:
    """Generate a deterministic experiment ID.
    
    Format: exp_<name_short>_<date>_<hash6>
    Example: exp_swebenchpro_2026-01-19_abc123
    
    Args:
        experiment_name: Name from config
        config_hash: SHA256 hash of config file
        timestamp: ISO timestamp (defaults to now)
        
    Returns:
        Deterministic experiment ID
    """
    if timestamp is None:
        timestamp = datetime.utcnow().isoformat()
    
    date_str = timestamp.split("T")[0]
    
    name_short = experiment_name.replace("_", "").replace("-", "")[:15].lower()
    
    hash_input = f"{experiment_name}|{config_hash}|{date_str}"
    hash_suffix = hashlib.sha256(hash_input.encode()).hexdigest()[:6]
    
    return f"exp_{name_short}_{date_str}_{hash_suffix}"


def generate_run_id(
    mcp_mode: str,
    model: str,
    task_id: str,
    seed: int,
    experiment_id: str
) -> str:
    """Generate a deterministic run ID from invariants.
    
    Format: run_<mcp_mode>_<model_short>_<task_short>_seed<N>_<hash6>
    Example: run_baseline_opus_navidrome_seed0_a1b2c3
    
    Args:
        mcp_mode: MCP mode (baseline, deepsearch_hybrid, etc.)
        model: Full model identifier (e.g., anthropic/claude-opus-4-5)
        task_id: Full task ID
        seed: Random seed
        experiment_id: Parent experiment ID
        
    Returns:
        Deterministic run ID
    """
    model_short = _shorten_model(model)
    
    task_short = _shorten_task(task_id)
    
    invariant_str = f"{mcp_mode}|{model}|{task_id}|{seed}|{experiment_id}"
    hash_suffix = hashlib.sha256(invariant_str.encode()).hexdigest()[:6]
    
    return f"run_{mcp_mode}_{model_short}_{task_short}_seed{seed}_{hash_suffix}"


def generate_pair_id(
    baseline_run_id: str,
    mcp_run_id: str
) -> str:
    """Generate a pair ID from two run IDs.
    
    Format: pair_<model_short>_<task_short>_seed<N>_<hash6>
    Example: pair_opus_navidrome_seed0_g7h8i9
    
    Args:
        baseline_run_id: ID of the baseline run
        mcp_run_id: ID of the MCP run
        
    Returns:
        Deterministic pair ID
    """
    combined = f"{baseline_run_id}|{mcp_run_id}"
    hash_suffix = hashlib.sha256(combined.encode()).hexdigest()[:6]
    
    parts = baseline_run_id.split("_")
    if len(parts) >= 5:
        model_short = parts[2]
        task_short = parts[3]
        seed_part = parts[4]
    else:
        model_short = "unknown"
        task_short = "unknown"
        seed_part = "seed0"
    
    return f"pair_{model_short}_{task_short}_{seed_part}_{hash_suffix}"


def compute_invariant_hash(
    benchmark: str,
    benchmark_version: str,
    task_ids: list[str],
    model: str,
    seed: int,
    agent_import_path: str,
    environment_type: str = "docker"
) -> str:
    """Compute hash of all invariants that must match between paired runs.
    
    This hash captures everything that should be identical between a baseline
    and MCP run. The mcp_mode is NOT included since that's the variable.
    
    Args:
        benchmark: Benchmark name
        benchmark_version: Benchmark version
        task_ids: List of task IDs being run
        model: Model identifier
        seed: Random seed
        agent_import_path: Agent import path
        environment_type: Environment type (docker, local)
        
    Returns:
        Invariant hash string (sha256:...)
    """
    invariants = {
        "benchmark": benchmark,
        "benchmark_version": benchmark_version,
        "task_ids": sorted(task_ids),
        "model": model,
        "seed": seed,
        "agent_import_path": agent_import_path,
        "environment_type": environment_type
    }
    
    canonical = json.dumps(invariants, sort_keys=True, separators=(",", ":"))
    hash_value = hashlib.sha256(canonical.encode()).hexdigest()
    
    return f"sha256:{hash_value}"


def _shorten_model(model: str) -> str:
    """Shorten model name for use in IDs.
    
    Examples:
        anthropic/claude-opus-4-5 -> opus
        anthropic/claude-sonnet-4-20250514 -> sonnet
        openai/gpt-4o -> gpt4o
    """
    name = model.split("/")[-1].lower()
    
    name = name.replace("claude-", "").replace("claude_", "")
    
    if "opus" in name:
        return "opus"
    if "sonnet" in name:
        return "sonnet"
    if "haiku" in name:
        return "haiku"
    if "gpt-4o" in name or "gpt4o" in name:
        return "gpt4o"
    if "gpt-4" in name:
        return "gpt4"
    
    return name[:8].replace("-", "").replace("_", "")


def _shorten_task(task_id: str) -> str:
    """Shorten task ID for use in IDs.
    
    Examples:
        instance_navidrome__navidrome-bf2bcb12... -> navidrome
        instance_ansible__ansible-4c5ce5a1... -> ansible
    """
    parts = task_id.split("_")
    if len(parts) >= 2:
        repo_part = parts[1]
        if "__" in task_id:
            repo_part = task_id.split("__")[0].split("_")[-1]
        return repo_part[:10].lower()
    
    return task_id[:10].lower().replace("-", "").replace("_", "")
