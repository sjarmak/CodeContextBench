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

Runtime watchdog
----------------
``launch_run`` wraps the harness subprocess with a background watchdog thread
that monitors ``CSB_RUNS_DIR`` for new ``validation_result.json`` files.
If more than 50 % of the last ``WATCHDOG_WINDOW`` results are ``invalid_output``
or ``no_status``, the watchdog probes all account tokens.  If any token is
expired the harness process is killed and the run exits with a non-zero code so
the operator can refresh tokens and restart.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
from collections import deque
from pathlib import Path
from typing import Deque

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

    * OpenHands: 6 per account.
    * Claude/Daytona: min(account_count × 62, 124).
    * Others: account_count × 6.
    """
    if agent == "openhands":
        return account_count * 6
    if agent == "claude":
        return min(account_count * 62, 124)
    return account_count * 6


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
# Runtime watchdog
# ---------------------------------------------------------------------------

#: How many recent results to keep in the sliding window.
WATCHDOG_WINDOW = 10
#: Fraction of bad results that triggers a token probe (0.5 = 50 %).
WATCHDOG_ERROR_THRESHOLD = 0.5
#: Seconds between directory scans.
WATCHDOG_POLL_INTERVAL = 60


def _probe_token_health(real_home: str | None = None) -> tuple[bool, list[str]]:
    """Check OAuth token validity for all account homes.

    Returns:
        (all_ok, messages) where all_ok is False if any token is expired.
    """
    # Import here to avoid circular imports and keep the dependency optional.
    try:
        from scripts.infra.account_health import read_token_status  # type: ignore[import]
    except ImportError:
        # If the module isn't importable, fall through gracefully.
        return True, ["[watchdog] account_health module not importable; skipping token probe"]

    home = real_home or os.environ.get("REAL_HOME") or os.path.expanduser("~")
    claude_homes = Path(home) / ".claude-homes"
    messages: list[str] = []
    all_ok = True

    if not claude_homes.is_dir():
        # Single-account setup — check ~/.claude directly
        status = read_token_status(Path(home))
        state = status.get("token_state", "unknown")
        rem = status.get("remaining_minutes")
        rem_text = f"{rem}m remaining" if rem is not None else "unknown expiry"
        messages.append(f"[watchdog] account {home}: token={state} ({rem_text})")
        if state in ("expired", "expiring_now", "missing_credentials", "missing_oauth", "corrupt_credentials"):
            all_ok = False
        return all_ok, messages

    for account_dir in sorted(claude_homes.iterdir()):
        if not account_dir.is_dir() or not account_dir.name.startswith("account"):
            continue
        status = read_token_status(account_dir)
        state = status.get("token_state", "unknown")
        rem = status.get("remaining_minutes")
        rem_text = f"{rem}m remaining" if rem is not None else "unknown expiry"
        messages.append(f"[watchdog] {account_dir.name}: token={state} ({rem_text})")
        if state in ("expired", "expiring_now", "missing_credentials", "missing_oauth", "corrupt_credentials"):
            all_ok = False

    return all_ok, messages


class _RuntimeWatchdog(threading.Thread):
    """Background thread that monitors validation results and kills the harness on bad-token conditions.

    The watchdog:
    1. Scans CSB_RUNS_DIR every WATCHDOG_POLL_INTERVAL seconds for new
       ``validation_result.json`` files.
    2. Maintains a sliding window (deque) of the last WATCHDOG_WINDOW statuses.
    3. If more than WATCHDOG_ERROR_THRESHOLD of the window is ``invalid_output``
       (or missing a status entirely), probes account tokens.
    4. If any token is expired, sends SIGTERM to the harness process, sets
       ``self.killed_reason``, and exits.
    """

    def __init__(self, proc: subprocess.Popen, csb_runs_dir: Path) -> None:
        super().__init__(name="csb-watchdog", daemon=True)
        self._proc = proc
        self._runs_dir = csb_runs_dir
        self._stop_event = threading.Event()
        #: Set to a non-empty string if the watchdog killed the process.
        self.killed_reason: str = ""
        # Track which files we've already seen so we only process new results.
        self._seen: set[Path] = set()
        self._window: Deque[str] = deque(maxlen=WATCHDOG_WINDOW)

    def stop(self) -> None:
        """Signal the watchdog to exit its poll loop."""
        self._stop_event.set()

    def _collect_new_results(self) -> list[str]:
        """Return statuses from validation_result.json files not yet seen."""
        new_statuses: list[str] = []
        for result_file in self._runs_dir.rglob("validation_result.json"):
            if result_file in self._seen:
                continue
            self._seen.add(result_file)
            try:
                data = json.loads(result_file.read_text())
                status = data.get("status", "no_status")
            except (json.JSONDecodeError, OSError):
                status = "no_status"
            new_statuses.append(status)
        return new_statuses

    def _error_rate(self) -> float:
        if not self._window:
            return 0.0
        bad = sum(1 for s in self._window if s in ("invalid_output", "no_status"))
        return bad / len(self._window)

    def run(self) -> None:
        while not self._stop_event.is_set():
            # Collect any new validation results written since last scan.
            new_statuses = self._collect_new_results()
            for s in new_statuses:
                self._window.append(s)

            if len(self._window) >= WATCHDOG_WINDOW:
                rate = self._error_rate()
                if rate > WATCHDOG_ERROR_THRESHOLD:
                    print(
                        f"[watchdog] ERROR RATE ALERT: {rate:.0%} of last "
                        f"{len(self._window)} results are bad "
                        f"(invalid_output/no_status). Probing tokens...",
                        flush=True,
                    )
                    all_ok, messages = _probe_token_health()
                    for msg in messages:
                        print(msg, flush=True)
                    if not all_ok:
                        self.killed_reason = (
                            f"Watchdog killed harness: {rate:.0%} error rate "
                            f"with expired/invalid tokens. Refresh tokens and restart."
                        )
                        print(
                            f"[watchdog] KILLING HARNESS — {self.killed_reason}",
                            file=sys.stderr,
                            flush=True,
                        )
                        try:
                            self._proc.terminate()
                        except OSError:
                            pass
                        return
                    else:
                        print(
                            "[watchdog] Tokens look healthy; high error rate may be a task issue.",
                            flush=True,
                        )
                        # Reset window so we don't fire again immediately.
                        self._window.clear()

            self._stop_event.wait(WATCHDOG_POLL_INTERVAL)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def launch_run(config: RunConfig, repo_root: Path | None = None) -> int:
    """Launch the harness for the given RunConfig with a runtime watchdog.

    The harness subprocess is monitored for error-rate spikes that indicate
    expired OAuth tokens.  If the watchdog detects that >50 % of the last 10
    results are ``invalid_output`` AND token probing confirms at least one
    expired token, the harness is killed and this function returns 2.

    Returns the harness exit code (0 = success, non-zero = failure/killed).

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
    csb_runs_dir_str = env.get("CSB_RUNS_DIR", "(not set)")
    subset = config.resolved_task_subset(repo_root)
    print(f"[csb run] Agent:        {config.agent.value}")
    print(f"[csb run] Model:        {config.model}")
    print(f"[csb run] Augmentation: {config.augmentation.value} → {config.config_name()}")
    print(f"[csb run] Category:     {config.category.value}")
    print(f"[csb run] Task subset:  {subset}")
    print(f"[csb run] Parallel:     {parallel} (accounts: {account_count})")
    print(f"[csb run] Output root:  {csb_runs_dir_str}")
    if config.dry_run:
        print(f"[csb run] DRY RUN — no tasks will execute")
    print(f"[csb run] Harness:      {harness}")
    print(f"[csb run] Watchdog:     enabled (window={WATCHDOG_WINDOW}, threshold={WATCHDOG_ERROR_THRESHOLD:.0%})")
    print()

    csb_runs_dir = Path(csb_runs_dir_str) if csb_runs_dir_str != "(not set)" else Path(".")

    proc = subprocess.Popen(cmd, env=env, cwd=str(repo_root))

    watchdog = _RuntimeWatchdog(proc, csb_runs_dir)
    watchdog.start()

    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()
        proc.wait()
    finally:
        watchdog.stop()
        watchdog.join(timeout=5)

    if watchdog.killed_reason:
        print(
            f"\n[csb run] Run aborted by watchdog: {watchdog.killed_reason}",
            file=sys.stderr,
        )
        return 2

    return proc.returncode
