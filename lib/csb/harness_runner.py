"""CSB Harness Runner — enforces the PIPELINE_SPEC result contract.

Translates a validated :class:`RunConfig` into harness invocation, enforcing:

* I-1  Results always at absolute CSB_RUNS_DIR path.
* I-2  validation_result.json always written per task.
* I-3  Failures always logged with reason.
* I-6  CSB_RUNS_DIR unset → exit 1.
* I-7  Circuit breaker at MAX_ATTEMPTS=3.

The runner resolves the agent → harness script mapping via
``configs/harness_registry.json`` and delegates execution to the underlying
bash harness, which is the single source of truth for account rotation,
token refresh, and Harbor invocation.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from lib.csb.run_config import RunConfig, AugmentationMode


# ---------------------------------------------------------------------------
# Harness registry
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _load_harness_registry(repo_root: Path) -> dict:
    """Load configs/harness_registry.json, falling back to built-in defaults."""
    registry_path = repo_root / "configs" / "harness_registry.json"
    if registry_path.exists():
        try:
            return json.loads(registry_path.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {}


# Built-in harness defaults (used when registry entry is absent)
_DEFAULT_HARNESS: dict[str, str] = {
    "claude": "configs/harnesses/run_selected_tasks.sh",
    "openhands": "configs/harnesses/openhands_2config.sh",
}


def resolve_harness(agent: str, repo_root: Path) -> Path:
    """Return the absolute path to the harness script for the given agent.

    Raises:
        ValueError: If no harness is registered for the agent.
    """
    registry = _load_harness_registry(repo_root)
    rel_path = (
        registry.get(agent, {}).get("script")
        or _DEFAULT_HARNESS.get(agent)
    )
    if not rel_path:
        raise ValueError(
            f"No harness registered for agent '{agent}'. "
            f"Check configs/harness_registry.json or add a default entry in "
            f"lib/csb/harness_runner.py."
        )
    harness = repo_root / rel_path
    if not harness.exists():
        raise ValueError(f"Harness script not found: {harness}")
    return harness


# ---------------------------------------------------------------------------
# Account auto-detection (PIPELINE_SPEC §5)
# ---------------------------------------------------------------------------

def detect_account_count(real_home: str | None = None) -> int:
    """Count available ~/.claude-homes/account*/ directories."""
    home = real_home or os.environ.get("REAL_HOME") or os.path.expanduser("~")
    claude_homes = Path(home) / ".claude-homes"
    if not claude_homes.is_dir():
        return 1
    return max(1, sum(1 for p in claude_homes.iterdir() if p.is_dir() and p.name.startswith("account")))


def default_parallel_jobs(agent: str, account_count: int) -> int:
    """Return the default parallel job count per PIPELINE_SPEC §5.2.

    * OpenHands: 4 per account.
    * Claude/Daytona: min(account_count × 62, 124).
    * Others: account_count × 4.
    """
    if agent == "openhands":
        return account_count * 4
    if agent == "claude":
        return min(account_count * 62, 124)
    return account_count * 4


# ---------------------------------------------------------------------------
# Env-var builder
# ---------------------------------------------------------------------------

def build_harness_env(config: RunConfig, repo_root: Path) -> dict[str, str]:
    """Build the environment variables dict for the harness subprocess."""
    env = dict(os.environ)

    # I-6: CSB_RUNS_DIR must be set and absolute (already validated, but enforce)
    csb_runs_dir = os.environ.get("CSB_RUNS_DIR", "")
    if not csb_runs_dir or not Path(csb_runs_dir).is_absolute():
        print(
            "ERROR: CSB_RUNS_DIR is not set to an absolute path. "
            "The harness cannot start without it.",
            file=sys.stderr,
        )
        sys.exit(1)

    env["CSB_RUNS_DIR"] = csb_runs_dir
    env["BASELINE_MCP_TYPE"] = config.mcp_type()
    env["CATEGORY"] = config.category.value

    # Normalize model to provider/name form expected by Harbor
    env["MODEL"] = config.model

    # Preamble injection
    if config.preamble:
        preamble_path = Path(config.preamble)
        if preamble_path.is_file():
            env["AGENT_PREAMBLE_FILE"] = str(preamble_path.resolve())
        else:
            env["AGENT_PREAMBLE"] = config.preamble

    # Dry-run flag
    if config.dry_run:
        env["DRY_RUN"] = "1"

    # Skip-completed flag (default on)
    env["SKIP_COMPLETED"] = "1" if config.skip_completed else "0"

    # Suppress interactive confirmation when called from csb run
    env["CSB_SKIP_CONFIRM"] = env.get("CSB_SKIP_CONFIRM", "0")

    return env


# ---------------------------------------------------------------------------
# CLI flag builder
# ---------------------------------------------------------------------------

def build_harness_args(config: RunConfig, repo_root: Path, parallel: int) -> list[str]:
    """Build the positional / flag arguments for the harness script."""
    args: list[str] = []

    # Augmentation → config flag mapping
    aug = config.augmentation
    if aug == AugmentationMode.NONE:
        args += ["--baseline-only"]
    elif aug in (AugmentationMode.SOURCEGRAPH_FULL, AugmentationMode.DEEPSEARCH, AugmentationMode.DEEPSEARCH_HYBRID):
        args += ["--full-only"]

    # Full config name (for harnesses that accept --full-config)
    if aug != AugmentationMode.NONE:
        args += ["--full-config", config.config_name()]

    # Task subset
    subset_path = config.resolved_task_subset(repo_root)
    if subset_path != repo_root / "configs/selected_benchmark_tasks.json":
        args += ["--selection-file", str(subset_path)]

    # Parallel jobs
    args += ["--parallel", str(parallel)]

    # Category
    args += ["--category", config.category.value]

    # Dry-run
    if config.dry_run:
        args += ["--dry-run"]

    # Skip-completed
    if config.skip_completed:
        args += ["--skip-completed"]

    return args


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def launch_run(config: RunConfig, repo_root: Path | None = None) -> int:
    """Launch the harness for the given RunConfig.

    Returns the harness exit code.

    Raises:
        ValueError: If the harness cannot be resolved.
        SystemExit: If CSB_RUNS_DIR enforcement fails.
    """
    if repo_root is None:
        repo_root = _REPO_ROOT

    harness = resolve_harness(config.agent.value, repo_root)

    account_count = detect_account_count()
    parallel = config.parallel or default_parallel_jobs(config.agent.value, account_count)

    env = build_harness_env(config, repo_root)
    args = build_harness_args(config, repo_root, parallel)

    cmd = ["bash", str(harness)] + args

    # Print launch summary
    csb_runs_dir = env.get("CSB_RUNS_DIR", "(not set)")
    subset = config.resolved_task_subset(repo_root)
    print(f"[csb run] Agent:        {config.agent.value}")
    print(f"[csb run] Model:        {config.model}")
    print(f"[csb run] Augmentation: {config.augmentation.value} → {config.config_name()}")
    print(f"[csb run] Category:     {config.category.value}")
    print(f"[csb run] Task subset:  {subset}")
    print(f"[csb run] Parallel:     {parallel} (accounts: {account_count})")
    print(f"[csb run] Output root:  {csb_runs_dir}")
    if config.dry_run:
        print(f"[csb run] DRY RUN — no tasks will execute")
    print(f"[csb run] Harness:      {harness}")
    print()

    result = subprocess.run(cmd, env=env, cwd=str(repo_root))
    return result.returncode
