#!/usr/bin/env python3
"""Daytona cost guardrails for batch benchmark launches.

This script combines three views of Daytona spend risk:
1. Live Daytona account state (active sandboxes, snapshots, storage burn)
2. Historical task runtimes from local Harbor results
3. Launch-time cost estimation for a selected benchmark batch

The estimates are intentionally conservative but not exact billing replicas.
They are meant to stop obviously risky launches before they happen.
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
RUN_ROOTS = [
    REPO_ROOT / "runs" / "official" / "_raw",
    REPO_ROOT / "runs" / "staging",
    REPO_ROOT / "runs" / "experimental",
    REPO_ROOT / "runs" / "sg_validation",
    REPO_ROOT / "runs" / "validation",
]
CACHE_PATH = REPO_ROOT / "runs" / "analysis" / "daytona_cost_history_cache.json"
REGISTRY_PATH = REPO_ROOT / "scripts" / "daytona_task_registry.json"
DEFAULT_OPENHANDS_ROUTING_POLICY = REPO_ROOT / "configs" / "openhands_daytona_routing.json"
CACHE_VERSION = 1

CPU_HOURLY_USD = 0.0504
MEMORY_GIB_HOURLY_USD = 0.0162
STORAGE_GIB_HOURLY_USD = 0.000108
FREE_STORAGE_GIB = 5.0
DEFAULT_CPUS = 2
DEFAULT_MEMORY_GIB = 4.0
DEFAULT_STORAGE_GIB = 10.0
DEFAULT_UNLABELED_STALE_HOURS = 0.5
DEFAULT_ORPHANED_RUN_STALE_HOURS = 1.0
DEFAULT_FAILED_SANDBOX_STALE_HOURS = 0.25
DEFAULT_MANAGED_TIMEOUT_GRACE_HOURS = 0.5
DEFAULT_MISSING_TASK_RECORD_STALE_HOURS = 1.0

DEFAULT_POLICY: dict[str, Any] = {
    "monthly_budget_usd": 300.0,
    "warn_fraction_of_monthly_budget": 0.50,
    "block_fraction_of_monthly_budget": 1.00,
    "warn_active_sandboxes": 5,
    "block_active_sandboxes": 15,
    "warn_active_hourly_burn_usd": 0.50,
    "block_active_hourly_burn_usd": 1.25,
    "warn_snapshot_storage_gb": 25.0,
    "block_snapshot_storage_gb": 75.0,
    "warn_unlabeled_active_sandboxes": 0,
    "block_unlabeled_active_sandboxes": 5,
    "warn_launch_estimate_usd": 20.0,
    "block_launch_estimate_usd": 60.0,
    "warn_timeout_ceiling_usd": 100.0,
    "block_timeout_ceiling_usd": 250.0,
    "warn_cold_task_configs": 30,
    "block_cold_task_configs": 90,
    "warn_parallel_tasks": 60,
    "block_parallel_tasks": 100,
}

ENV_OVERRIDE_MAP = {
    "DAYTONA_MONTHLY_BUDGET_USD": "monthly_budget_usd",
    "DAYTONA_WARN_ACTIVE_SANDBOXES": "warn_active_sandboxes",
    "DAYTONA_BLOCK_ACTIVE_SANDBOXES": "block_active_sandboxes",
    "DAYTONA_WARN_ACTIVE_HOURLY_BURN_USD": "warn_active_hourly_burn_usd",
    "DAYTONA_BLOCK_ACTIVE_HOURLY_BURN_USD": "block_active_hourly_burn_usd",
    "DAYTONA_WARN_SNAPSHOT_STORAGE_GB": "warn_snapshot_storage_gb",
    "DAYTONA_BLOCK_SNAPSHOT_STORAGE_GB": "block_snapshot_storage_gb",
    "DAYTONA_WARN_UNLABELED_ACTIVE_SANDBOXES": "warn_unlabeled_active_sandboxes",
    "DAYTONA_BLOCK_UNLABELED_ACTIVE_SANDBOXES": "block_unlabeled_active_sandboxes",
    "DAYTONA_WARN_LAUNCH_ESTIMATE_USD": "warn_launch_estimate_usd",
    "DAYTONA_BLOCK_LAUNCH_ESTIMATE_USD": "block_launch_estimate_usd",
    "DAYTONA_WARN_TIMEOUT_CEILING_USD": "warn_timeout_ceiling_usd",
    "DAYTONA_BLOCK_TIMEOUT_CEILING_USD": "block_timeout_ceiling_usd",
    "DAYTONA_WARN_COLD_TASK_CONFIGS": "warn_cold_task_configs",
    "DAYTONA_BLOCK_COLD_TASK_CONFIGS": "block_cold_task_configs",
    "DAYTONA_WARN_PARALLEL_TASKS": "warn_parallel_tasks",
    "DAYTONA_BLOCK_PARALLEL_TASKS": "block_parallel_tasks",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Estimate Daytona launch cost and enforce repo policy thresholds.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    summary_parser = subparsers.add_parser("summary", help="Show live Daytona cost state.")
    summary_parser.add_argument("--policy", default=str(REPO_ROOT / "configs" / "daytona_cost_policy.json"))
    summary_parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")

    teardown_parser = subparsers.add_parser(
        "teardown-candidates",
        help="Interactively delete teardown candidates surfaced by the cost guard.",
    )
    teardown_parser.add_argument("--policy", default=str(REPO_ROOT / "configs" / "daytona_cost_policy.json"))
    teardown_parser.add_argument("--limit", type=int, default=10, help="Max candidates to act on when no --name filter is provided.")
    teardown_parser.add_argument("--name", action="append", dest="names", default=[], help="Specific sandbox name/id to delete. Pass multiple times.")
    teardown_parser.add_argument("--dry-run", action="store_true", help="Show candidates without deleting.")
    teardown_parser.add_argument("--yes", action="store_true", help="Skip interactive confirmation.")

    preflight_parser = subparsers.add_parser(
        "preflight",
        help="Estimate a selected batch and fail when policy thresholds are exceeded.",
    )
    preflight_parser.add_argument("--selection-file", default="")
    preflight_parser.add_argument("--task-id", action="append", dest="task_ids", default=[])
    preflight_parser.add_argument("--task-id-file", default="")
    preflight_parser.add_argument("--suite", default="")
    preflight_parser.add_argument("--benchmark", default="")
    preflight_parser.add_argument("--use-case-category", default="")
    preflight_parser.add_argument(
        "--config",
        action="append",
        dest="configs",
        default=[],
        help="Config name to estimate. Pass multiple times for paired runs.",
    )
    preflight_parser.add_argument("--parallel-tasks", type=int, default=1)
    preflight_parser.add_argument("--concurrency", type=int, default=1)
    preflight_parser.add_argument("--policy", default=str(REPO_ROOT / "configs" / "daytona_cost_policy.json"))
    preflight_parser.add_argument("--routing-policy", default=str(DEFAULT_OPENHANDS_ROUTING_POLICY))
    preflight_parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    return parser.parse_args()


def load_env_var(name: str) -> str:
    value = os.environ.get(name, "")
    if value:
        return value

    env_path = REPO_ROOT / ".env.local"
    if not env_path.exists():
        return ""

    for raw_line in env_path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :]
        if "=" not in line:
            continue
        key, raw_value = line.split("=", 1)
        if key.strip() != name:
            continue
        value = raw_value.strip().strip('"').strip("'")
        if value:
            return value
    return ""


def load_policy(path: str) -> dict[str, Any]:
    policy = dict(DEFAULT_POLICY)
    policy_path = Path(path)
    if policy_path.exists():
        try:
            loaded = json.loads(policy_path.read_text())
        except json.JSONDecodeError as exc:
            raise SystemExit(f"Invalid JSON in policy file {policy_path}: {exc}") from exc
        if not isinstance(loaded, dict):
            raise SystemExit(f"Policy file must contain a JSON object: {policy_path}")
        policy.update(loaded)

    for env_name, policy_key in ENV_OVERRIDE_MAP.items():
        raw_value = os.environ.get(env_name)
        if raw_value is None:
            continue
        base_value = policy.get(policy_key)
        if isinstance(base_value, int):
            policy[policy_key] = int(raw_value)
        else:
            policy[policy_key] = float(raw_value)

    return policy


def load_routing_policy(path: str) -> dict[str, Any]:
    if not path:
        return {}

    policy_path = Path(path)
    if not policy_path.exists():
        raise SystemExit(f"Routing policy file not found: {policy_path}")

    try:
        loaded = json.loads(policy_path.read_text())
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in routing policy file {policy_path}: {exc}") from exc
    if not isinstance(loaded, dict):
        raise SystemExit(f"Routing policy file must contain a JSON object: {policy_path}")
    return loaded


def format_currency(value: float) -> str:
    return f"${value:,.2f}"


def month_key(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m")


def parse_iso8601(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def runtime_cost_usd(cpus: float, memory_gib: float, storage_gib: float, duration_seconds: float) -> float:
    hourly = (
        cpus * CPU_HOURLY_USD
        + memory_gib * MEMORY_GIB_HOURLY_USD
        + max(storage_gib - FREE_STORAGE_GIB, 0.0) * STORAGE_GIB_HOURLY_USD
    )
    return hourly * (duration_seconds / 3600.0)


def parse_any_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc)
    if isinstance(value, str):
        return parse_iso8601(value)
    return None


def load_json_file(path: Path) -> dict[str, Any]:
    try:
        loaded = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return {}
    return loaded if isinstance(loaded, dict) else {}


def local_run_index() -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for root in RUN_ROOTS:
        if not root.exists():
            continue
        for path in root.iterdir():
            if not path.is_dir():
                continue
            if path.name in {"archive", "_raw"}:
                continue
            index[path.name] = {
                "path": str(path),
                "mtime": datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc),
                "root": str(root.relative_to(REPO_ROOT)),
            }
    return index


def sandbox_run_id(labels: dict[str, Any]) -> str:
    for key in ("label_run_id", "run_id", "label_job_name", "job_name"):
        value = labels.get(key)
        if value:
            return str(value)
    return ""


def sandbox_managed(labels: dict[str, Any]) -> bool:
    if not labels:
        return False
    if labels.get("managed_by"):
        return True
    if any(key.startswith("label_") for key in labels):
        return True
    return False


def sandbox_task_id(labels: dict[str, Any]) -> str:
    for key in ("label_task_id", "task_id"):
        value = labels.get(key)
        if value:
            return str(value)
    return ""


def sandbox_config_name(labels: dict[str, Any]) -> str:
    for key in ("label_config", "config"):
        value = labels.get(key)
        if value:
            return str(value)
    return ""


def task_id_from_job_config(job_config: dict[str, Any]) -> str:
    environment = job_config.get("environment") or {}
    kwargs = environment.get("kwargs") or {}
    task_id = kwargs.get("label_task_id")
    if task_id:
        return str(task_id)

    task_source_dir = kwargs.get("task_source_dir")
    if task_source_dir:
        return Path(str(task_source_dir)).name

    tasks = job_config.get("tasks") or []
    if tasks:
        task_path = (tasks[0] or {}).get("path")
        if task_path:
            return Path(str(task_path)).name

    task = job_config.get("task") or {}
    task_path = task.get("path")
    if task_path:
        return Path(str(task_path)).name
    return ""


def local_task_state(
    run_id: str,
    config_name: str,
    task_id: str,
    run_index: dict[str, dict[str, Any]],
    registry: dict[str, dict[str, Any]],
    cache: dict[tuple[str, str, str], dict[str, Any] | None],
) -> dict[str, Any] | None:
    cache_key = (run_id, config_name, task_id)
    if cache_key in cache:
        return cache[cache_key]

    local_run = run_index.get(run_id)
    if local_run is None:
        cache[cache_key] = None
        return None

    config_root = Path(local_run["path"]) / config_name
    state: dict[str, Any] = {
        "found": False,
        "job_dir": "",
        "trial_dir": "",
        "result_exists": False,
        "last_local_activity_at": None,
        "effective_timeout_hours": None,
    }
    if not config_root.exists():
        cache[cache_key] = state
        return state

    for job_config_path in sorted(config_root.glob("*/config.json")):
        job_config = load_json_file(job_config_path)
        if task_id_from_job_config(job_config) != task_id:
            continue

        job_dir = job_config_path.parent
        trial_dirs = [
            child for child in job_dir.iterdir()
            if child.is_dir() and child.name not in {"agent", "verifier"}
        ]
        trial_dir = trial_dirs[0] if trial_dirs else None

        candidate_files: list[Path] = [job_config_path, job_dir / "job.log", job_dir / "result.json"]
        if trial_dir is not None:
            candidate_files.extend(
                [
                    trial_dir / "config.json",
                    trial_dir / "trial.log",
                    trial_dir / "result.json",
                ]
            )

        existing_files = [path for path in candidate_files if path.exists()]
        latest_local_activity_at = None
        if existing_files:
            latest_path = max(existing_files, key=lambda path: path.stat().st_mtime)
            latest_local_activity_at = datetime.fromtimestamp(latest_path.stat().st_mtime, tz=timezone.utc)

        task_meta = registry.get(task_id, {})
        timeouts = task_meta.get("timeouts") or {}
        timeout_multiplier = float(job_config.get("timeout_multiplier") or 1.0)
        agent_multiplier = float(job_config.get("agent_timeout_multiplier") or timeout_multiplier)
        build_multiplier = float(job_config.get("environment_build_timeout_multiplier") or timeout_multiplier)
        agent_timeout_sec = float(timeouts.get("agent_sec", 1800.0)) * agent_multiplier
        build_timeout_sec = float(timeouts.get("build_sec", 300.0)) * build_multiplier

        state = {
            "found": True,
            "job_dir": str(job_dir),
            "trial_dir": str(trial_dir) if trial_dir is not None else "",
            "result_exists": any(path.name == "result.json" for path in existing_files),
            "last_local_activity_at": latest_local_activity_at,
            "effective_timeout_hours": (agent_timeout_sec + build_timeout_sec) / 3600.0,
        }
        cache[cache_key] = state
        return state

    cache[cache_key] = state
    return state


def teardown_candidates(
    sandbox_details: list[dict[str, Any]],
    run_index: dict[str, dict[str, Any]],
    registry: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    now = datetime.now(timezone.utc)
    candidates: list[dict[str, Any]] = []
    task_state_cache: dict[tuple[str, str, str], dict[str, Any] | None] = {}

    for sandbox in sandbox_details:
        labels = sandbox.get("labels") or {}
        state = str(sandbox.get("state") or "")
        created_at = parse_any_datetime(sandbox.get("created_at"))
        event_at = parse_any_datetime(sandbox.get("updated_at")) or created_at
        if not event_at:
            continue

        age_hours = max((now - event_at).total_seconds(), 0.0) / 3600.0
        runtime_anchor = created_at or event_at
        runtime_hours = max((now - runtime_anchor).total_seconds(), 0.0) / 3600.0
        run_id = sandbox_run_id(labels)
        task_id = sandbox_task_id(labels)
        config_name = sandbox_config_name(labels)
        managed = sandbox_managed(labels)
        reason = ""
        local_run = run_index.get(run_id) if run_id else None
        task_state = None

        if run_id and task_id and config_name and local_run is not None:
            task_state = local_task_state(
                run_id=run_id,
                config_name=config_name,
                task_id=task_id,
                run_index=run_index,
                registry=registry,
                cache=task_state_cache,
            )

        if "BUILD_FAILED" in state or state.endswith("FAILED"):
            if age_hours >= DEFAULT_FAILED_SANDBOX_STALE_HOURS:
                if managed:
                    reason = (
                        f"failed sandbox older than {DEFAULT_FAILED_SANDBOX_STALE_HOURS:.2f}h"
                    )
                else:
                    reason = (
                        f"unlabeled failed sandbox older than {DEFAULT_FAILED_SANDBOX_STALE_HOURS:.2f}h"
                    )
        elif not managed and age_hours >= DEFAULT_UNLABELED_STALE_HOURS:
            reason = f"unlabeled active sandbox older than {DEFAULT_UNLABELED_STALE_HOURS:.1f}h"
        elif run_id and local_run is None and age_hours >= DEFAULT_ORPHANED_RUN_STALE_HOURS:
            reason = f"run_id {run_id} not found under local run roots"
        elif task_state:
            if task_state["result_exists"]:
                reason = "local result exists but sandbox is still active"
            elif not task_state["found"] and runtime_hours >= DEFAULT_MISSING_TASK_RECORD_STALE_HOURS:
                reason = (
                    "managed sandbox has no matching local task record after "
                    f"{DEFAULT_MISSING_TASK_RECORD_STALE_HOURS:.1f}h"
                )
            else:
                effective_timeout_hours = task_state.get("effective_timeout_hours")
                if (
                    effective_timeout_hours is not None
                    and runtime_hours >= effective_timeout_hours + DEFAULT_MANAGED_TIMEOUT_GRACE_HOURS
                ):
                    reason = (
                        "task exceeded effective timeout budget "
                        f"({effective_timeout_hours:.2f}h + {DEFAULT_MANAGED_TIMEOUT_GRACE_HOURS:.2f}h grace) "
                        "without result.json"
                    )

        if not reason:
            continue

        candidates.append(
            {
                "id": sandbox.get("id", ""),
                "name": sandbox["name"],
                "state": state,
                "created_at": parse_any_datetime(sandbox.get("created_at")).isoformat()
                if parse_any_datetime(sandbox.get("created_at"))
                else "",
                "updated_at": parse_any_datetime(sandbox.get("updated_at")).isoformat()
                if parse_any_datetime(sandbox.get("updated_at"))
                else "",
                "age_hours": age_hours,
                "runtime_hours": runtime_hours,
                "hourly_burn_usd": sandbox["hourly_burn_usd"],
                "reason": reason,
                "run_id": run_id,
                "task_id": task_id,
                "config": config_name,
                "local_run_path": local_run["path"] if local_run else "",
                "local_job_dir": (task_state or {}).get("job_dir", ""),
                "local_trial_dir": (task_state or {}).get("trial_dir", ""),
                "effective_timeout_hours": (task_state or {}).get("effective_timeout_hours"),
                "labels": labels,
            }
        )

    candidates.sort(key=lambda item: (item["hourly_burn_usd"], item["age_hours"]), reverse=True)
    return candidates


def task_resources(task_meta: dict[str, Any] | None) -> tuple[float, float, float]:
    resources = (task_meta or {}).get("resources", {})
    cpus = float(resources.get("cpus", DEFAULT_CPUS))
    memory_gib = float(resources.get("memory_mb", DEFAULT_MEMORY_GIB * 1024.0)) / 1024.0
    storage_gib = float(resources.get("storage_mb", DEFAULT_STORAGE_GIB * 1024.0)) / 1024.0
    return cpus, memory_gib, storage_gib


def task_timeout_seconds(task_meta: dict[str, Any] | None) -> float:
    timeouts = (task_meta or {}).get("timeouts", {})
    agent_timeout = float(timeouts.get("agent_sec", 1800))
    build_timeout = float(timeouts.get("build_sec", 300))
    return agent_timeout + build_timeout


def load_task_registry() -> dict[str, dict[str, Any]]:
    registry = json.loads(REGISTRY_PATH.read_text())
    return {task["task_id"]: task for task in registry["tasks"]}


def resolve_registry_task_id(
    raw_candidates: list[str],
    registry: dict[str, dict[str, Any]],
    registry_keys_by_length: list[str],
) -> str | None:
    cleaned_candidates: list[str] = []
    for raw_candidate in raw_candidates:
        if not raw_candidate:
            continue
        candidate = raw_candidate
        if candidate.startswith("mcp_"):
            candidate = candidate[len("mcp_") :]
        cleaned_candidates.append(candidate)

    for candidate in cleaned_candidates:
        if candidate in registry:
            return candidate
        if "_" in candidate:
            stripped = candidate.rsplit("_", 1)[0]
            if stripped in registry:
                return stripped

    for candidate in cleaned_candidates:
        for known_task_id in registry_keys_by_length:
            if candidate.startswith(f"{known_task_id}_") or candidate.startswith(f"{known_task_id}-"):
                return known_task_id

    return None


def result_file_paths(root: Path) -> list[Path]:
    result_paths: list[Path] = []
    if not root.exists():
        return result_paths

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [dirname for dirname in dirnames if dirname not in {"agent", "verifier"}]
        if "result.json" in filenames:
            result_paths.append(Path(dirpath) / "result.json")
    return result_paths


def cache_fingerprint() -> dict[str, float | None]:
    fingerprint: dict[str, float | None] = {}
    for root in RUN_ROOTS:
        key = str(root.relative_to(REPO_ROOT))
        fingerprint[key] = root.stat().st_mtime if root.exists() else None
    return fingerprint


def build_history_cache(registry: dict[str, dict[str, Any]]) -> dict[str, Any]:
    by_task_config: dict[str, list[float]] = defaultdict(list)
    by_task: dict[str, list[float]] = defaultdict(list)
    by_suite_config: dict[str, list[float]] = defaultdict(list)
    monthly_runtime_lower_bound: dict[str, float] = defaultdict(float)
    registry_keys_by_length = sorted(registry.keys(), key=len, reverse=True)

    for root in RUN_ROOTS:
        for result_path in result_file_paths(root):
            if "__" not in result_path.parent.name:
                continue

            config_path = result_path.parent / "config.json"
            if not config_path.exists():
                continue

            try:
                result = json.loads(result_path.read_text())
                config = json.loads(config_path.read_text())
            except Exception:
                continue

            environment_type = (config.get("environment") or {}).get("type")
            if environment_type != "daytona":
                continue

            started_at = parse_iso8601(result.get("started_at"))
            finished_at = parse_iso8601(result.get("finished_at"))
            if not started_at or not finished_at:
                continue

            duration_seconds = max((finished_at - started_at).total_seconds(), 0.0)
            config_name = result_path.parent.parent.parent.name

            trial_dir_name = result_path.parent.name
            trial_task_id = trial_dir_name.split("__", 1)[0]
            task_name = str(result.get("task_name", "") or "")
            config_task_path = str(((result.get("config") or {}).get("task") or {}).get("path", "") or "")
            config_task_basename = Path(config_task_path).name if config_task_path else ""

            task_id = resolve_registry_task_id(
                raw_candidates=[trial_task_id, task_name, config_task_basename],
                registry=registry,
                registry_keys_by_length=registry_keys_by_length,
            )

            task_meta = registry.get(task_id) if task_id else None
            suite = (task_meta or {}).get("suite")
            if not suite:
                continue

            by_task_config[f"{task_id}|{config_name}"].append(duration_seconds)
            by_task[task_id].append(duration_seconds)
            by_suite_config[f"{suite}|{config_name}"].append(duration_seconds)

            cpus, memory_gib, storage_gib = task_resources(task_meta)
            monthly_runtime_lower_bound[month_key(started_at)] += runtime_cost_usd(
                cpus=cpus,
                memory_gib=memory_gib,
                storage_gib=storage_gib,
                duration_seconds=duration_seconds,
            )

    def summarize(values_by_key: dict[str, list[float]]) -> dict[str, dict[str, float]]:
        return {
            key: {
                "median_seconds": statistics.median(values),
                "samples": len(values),
            }
            for key, values in values_by_key.items()
            if values
        }

    cache = {
        "cache_version": CACHE_VERSION,
        "fingerprint": cache_fingerprint(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "task_config": summarize(by_task_config),
        "task": summarize(by_task),
        "suite_config": summarize(by_suite_config),
        "monthly_runtime_lower_bound": monthly_runtime_lower_bound,
    }
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(cache, indent=2, sort_keys=True))
    return cache


def load_history_cache(registry: dict[str, dict[str, Any]]) -> dict[str, Any]:
    if CACHE_PATH.exists():
        try:
            cached = json.loads(CACHE_PATH.read_text())
        except json.JSONDecodeError:
            cached = None
        if (
            cached
            and cached.get("cache_version") == CACHE_VERSION
            and cached.get("fingerprint") == cache_fingerprint()
        ):
            return cached
    return build_history_cache(registry)


def select_tasks(
    selection_file: str,
    benchmark_filter: str,
    use_case_category_filter: str,
    task_ids_filter: set[str] | None = None,
) -> list[dict[str, str]]:
    data = json.loads(Path(selection_file).read_text())
    selected: list[dict[str, str]] = []
    for task in data.get("tasks", []):
        suite = task.get("benchmark") or task.get("mcp_suite", "")
        if not suite:
            continue
        if benchmark_filter and suite != benchmark_filter:
            continue
        if use_case_category_filter and task.get("use_case_category", "") != use_case_category_filter:
            continue
        if task_ids_filter and task["task_id"] not in task_ids_filter:
            continue
        selected.append(
            {
                "task_id": task["task_id"],
                "selection_suite": suite,
                "repo": task.get("repo", ""),
            }
        )
    return selected


def select_tasks_from_ids(task_ids: list[str], suite_hint: str, registry: dict[str, dict[str, Any]]) -> list[dict[str, str]]:
    selected: list[dict[str, str]] = []
    for task_id in task_ids:
        task_meta = registry.get(task_id, {})
        suite = task_meta.get("suite") or suite_hint
        selected.append(
            {
                "task_id": task_id,
                "selection_suite": suite,
                "repo": task_meta.get("repo", ""),
            }
        )
    return selected


CONFIG_DOCKERFILE_VARIANT = {
    "baseline-local-direct": "baseline",
    "mcp-remote-direct": "sg_only",
}


def daytona_routing_decision(
    task_meta: dict[str, Any] | None,
    selected_task: dict[str, str],
    config_name: str,
    routing_policy: dict[str, Any],
) -> tuple[str, str]:
    if not routing_policy:
        return "daytona", ""

    docker_variant = CONFIG_DOCKERFILE_VARIANT.get(config_name)
    docker_meta = (((task_meta or {}).get("dockerfiles") or {}).get(docker_variant) or {})
    from_images = docker_meta.get("from_images") or []
    skip_prefixes = routing_policy.get("skip_daytona_from_prefixes") or []
    for prefix in skip_prefixes:
        if not isinstance(prefix, str) or not prefix:
            continue
        if any(isinstance(image, str) and image.startswith(prefix) for image in from_images):
            return "skip", f"blocked_image_prefix:{prefix}"

    config_rules = (routing_policy.get("local_docker_by_config") or {}).get(config_name) or {}
    repo = str((task_meta or {}).get("repo") or selected_task.get("repo") or "")
    for routed_repo in config_rules.get("repos", []):
        if isinstance(routed_repo, str) and routed_repo == repo:
            return "local-docker", f"repo:{repo}"

    return "daytona", ""


def launch_estimate(
    selected_tasks: list[dict[str, str]],
    configs: list[str],
    concurrency: int,
    history_cache: dict[str, Any],
    registry: dict[str, dict[str, Any]],
    routing_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    total_estimate_usd = 0.0
    total_timeout_ceiling_usd = 0.0
    cold_task_configs = 0
    estimate_sources: dict[str, int] = defaultdict(int)
    excluded_routes: dict[str, int] = defaultdict(int)
    task_estimates: list[dict[str, Any]] = []

    for task in selected_tasks:
        task_id = task["task_id"]
        task_meta = registry.get(task_id)
        if not task_meta:
            continue

        suite = task_meta.get("suite", task["selection_suite"])
        cpus, memory_gib, storage_gib = task_resources(task_meta)
        timeout_seconds = task_timeout_seconds(task_meta)

        for config_name in configs:
            route, route_reason = daytona_routing_decision(
                task_meta=task_meta,
                selected_task=task,
                config_name=config_name,
                routing_policy=routing_policy or {},
            )
            if route != "daytona":
                excluded_routes[f"{route}:{route_reason or 'policy'}"] += 1
                continue

            estimate_seconds = None
            estimate_source = "timeout_fallback"

            task_config_key = f"{task_id}|{config_name}"
            suite_config_key = f"{suite}|{config_name}"
            task_config_stats = (history_cache.get("task_config") or {}).get(task_config_key)
            task_stats = (history_cache.get("task") or {}).get(task_id)
            suite_config_stats = (history_cache.get("suite_config") or {}).get(suite_config_key)

            if task_config_stats:
                estimate_seconds = float(task_config_stats["median_seconds"])
                estimate_source = "task_config_median"
            elif task_stats:
                estimate_seconds = float(task_stats["median_seconds"])
                estimate_source = "task_median"
            elif suite_config_stats:
                estimate_seconds = float(suite_config_stats["median_seconds"])
                estimate_source = "suite_config_median"
            else:
                cold_task_configs += 1
                conservative_seconds = min(max(timeout_seconds * 0.40, 600.0), timeout_seconds)
                estimate_seconds = conservative_seconds

            estimate_sources[estimate_source] += 1

            estimate_usd = runtime_cost_usd(
                cpus=cpus,
                memory_gib=memory_gib,
                storage_gib=storage_gib,
                duration_seconds=estimate_seconds,
            ) * concurrency
            timeout_ceiling_usd = runtime_cost_usd(
                cpus=cpus,
                memory_gib=memory_gib,
                storage_gib=storage_gib,
                duration_seconds=timeout_seconds,
            ) * concurrency

            total_estimate_usd += estimate_usd
            total_timeout_ceiling_usd += timeout_ceiling_usd
            task_estimates.append(
                {
                    "task_id": task_id,
                    "suite": suite,
                    "config": config_name,
                    "estimate_seconds": estimate_seconds,
                    "estimate_usd": estimate_usd,
                    "timeout_ceiling_usd": timeout_ceiling_usd,
                    "source": estimate_source,
                }
            )

    task_estimates.sort(key=lambda item: item["estimate_usd"], reverse=True)
    return {
        "selected_tasks": len(selected_tasks),
        "configs": configs,
        "task_config_count": len(task_estimates),
        "concurrency": concurrency,
        "estimated_launch_usd": total_estimate_usd,
        "timeout_ceiling_usd": total_timeout_ceiling_usd,
        "cold_task_configs": cold_task_configs,
        "excluded_task_configs": sum(excluded_routes.values()),
        "excluded_routes": dict(sorted(excluded_routes.items())),
        "estimate_sources": dict(sorted(estimate_sources.items())),
        "top_task_estimates": task_estimates[:10],
    }


def unwrap_items(result: Any) -> tuple[list[Any], int]:
    if result is None:
        return [], 0
    items = getattr(result, "items", None)
    total = getattr(result, "total", None)
    if items is not None:
        items_list = list(items)
        return items_list, int(total if total is not None else len(items_list))
    if isinstance(result, list):
        return result, len(result)
    if isinstance(result, tuple) and len(result) == 2 and result[0] == "items":
        items_list = list(result[1])
        return items_list, len(items_list)
    return [], 0


def daytona_client() -> Any:
    api_key = load_env_var("DAYTONA_API_KEY")
    if not api_key:
        raise SystemExit("DAYTONA_API_KEY not set and not found in .env.local.")
    try:
        from daytona_sdk import Daytona, DaytonaConfig
    except ImportError as exc:
        raise SystemExit("daytona_sdk not installed. Run: pip install daytona-sdk") from exc

    return Daytona(
        DaytonaConfig(
            api_key=api_key,
            api_url=load_env_var("DAYTONA_API_URL") or "https://app.daytona.io/api",
            target=load_env_var("DAYTONA_TARGET") or "us",
        )
    )


def fetch_daytona_inventory(client: Any) -> tuple[list[Any], list[Any]]:
    sandboxes: list[Any] = []
    page = 1
    while True:
        sandboxes_page = client.list(page=page, limit=100)
        page_items, total = unwrap_items(sandboxes_page)
        if not page_items:
            break
        sandboxes.extend(page_items)
        if len(sandboxes) >= total or len(page_items) < 100:
            break
        page += 1

    snapshots: list[Any] = []
    page = 1
    while True:
        snapshot_page = client.snapshot.list(page=page, limit=100)
        page_items, total = unwrap_items(snapshot_page)
        if not page_items:
            break
        snapshots.extend(page_items)
        if len(snapshots) >= total or len(page_items) < 100:
            break
        page += 1

    return sandboxes, snapshots


def live_inventory() -> dict[str, Any]:
    client = daytona_client()
    run_index = local_run_index()
    registry = load_task_registry()
    sandboxes, snapshots = fetch_daytona_inventory(client)

    started_sandboxes = []
    failed_sandboxes = []
    for sandbox in sandboxes:
        state = str(getattr(sandbox, "state", "")).lower()
        if "started" in state:
            started_sandboxes.append(sandbox)
        elif "failed" in state:
            failed_sandboxes.append(sandbox)

    def sandbox_hourly_burn(sandbox: Any) -> float:
        cpus = float(getattr(sandbox, "cpu", 0.0) or 0.0)
        memory_gib = float(getattr(sandbox, "memory", 0.0) or 0.0)
        storage_gib = float(getattr(sandbox, "disk", 0.0) or 0.0)
        return runtime_cost_usd(cpus, memory_gib, storage_gib, 3600.0)

    snapshot_storage_gb = 0.0
    error_snapshots = 0
    largest_snapshots: list[dict[str, Any]] = []
    unlabeled_active_sandboxes = 0
    for snapshot in snapshots:
        size_gb = float(getattr(snapshot, "size", 0.0) or getattr(snapshot, "size_gb", 0.0) or 0.0)
        snapshot_storage_gb += size_gb
        state = str(getattr(snapshot, "state", "")).lower()
        if state == "error":
            error_snapshots += 1
        largest_snapshots.append(
            {
                "name": getattr(snapshot, "name", ""),
                "state": getattr(snapshot, "state", ""),
                "size_gb": size_gb,
                "updated_at": getattr(snapshot, "updated_at", None),
            }
        )
    largest_snapshots.sort(key=lambda item: item["size_gb"], reverse=True)

    sandbox_details = []
    for sandbox in sandboxes:
        labels = getattr(sandbox, "labels", None) or {}
        created_at = getattr(sandbox, "created_at", None)
        state = str(getattr(sandbox, "state", ""))
        if "started" in state.lower() and not sandbox_managed(labels):
            unlabeled_active_sandboxes += 1
        sandbox_details.append(
            {
                "id": str(getattr(sandbox, "id", "")),
                "name": getattr(sandbox, "name", ""),
                "state": state,
                "cpu": getattr(sandbox, "cpu", None),
                "memory_gib": getattr(sandbox, "memory", None),
                "disk_gib": getattr(sandbox, "disk", None),
                "created_at": created_at.isoformat() if isinstance(created_at, datetime) else created_at,
                "updated_at": (
                    getattr(sandbox, "updated_at", None).isoformat()
                    if isinstance(getattr(sandbox, "updated_at", None), datetime)
                    else getattr(sandbox, "updated_at", None)
                ),
                "labels": labels,
                "hourly_burn_usd": sandbox_hourly_burn(sandbox) if "started" in state.lower() else 0.0,
            }
        )
    sandbox_details.sort(key=lambda item: item["hourly_burn_usd"], reverse=True)
    candidates = teardown_candidates(sandbox_details, run_index, registry)

    return {
        "active_sandboxes": len(started_sandboxes),
        "failed_sandboxes": len(failed_sandboxes),
        "active_hourly_burn_usd": sum(item["hourly_burn_usd"] for item in sandbox_details),
        "unlabeled_active_sandboxes": unlabeled_active_sandboxes,
        "teardown_candidate_count": len(candidates),
        "teardown_candidates": candidates[:15],
        "started_sandboxes": sandbox_details[:10],
        "snapshots_total": len(snapshots),
        "snapshot_storage_gb": snapshot_storage_gb,
        "snapshot_monthly_storage_usd": snapshot_storage_gb * STORAGE_GIB_HOURLY_USD * 24.0 * 30.0,
        "error_snapshots": error_snapshots,
        "largest_snapshots": largest_snapshots[:10],
    }


def live_teardown_candidates(client: Any | None = None) -> list[dict[str, Any]]:
    active_client = client or daytona_client()
    run_index = local_run_index()
    registry = load_task_registry()
    sandboxes, _snapshots = fetch_daytona_inventory(active_client)

    def sandbox_hourly_burn(sandbox: Any) -> float:
        cpus = float(getattr(sandbox, "cpu", 0.0) or 0.0)
        memory_gib = float(getattr(sandbox, "memory", 0.0) or 0.0)
        storage_gib = float(getattr(sandbox, "disk", 0.0) or 0.0)
        return runtime_cost_usd(cpus, memory_gib, storage_gib, 3600.0)

    sandbox_details: list[dict[str, Any]] = []
    for sandbox in sandboxes:
        state = str(getattr(sandbox, "state", ""))
        created_at = getattr(sandbox, "created_at", None)
        sandbox_details.append(
            {
                "id": str(getattr(sandbox, "id", "")),
                "name": getattr(sandbox, "name", ""),
                "state": state,
                "cpu": getattr(sandbox, "cpu", None),
                "memory_gib": getattr(sandbox, "memory", None),
                "disk_gib": getattr(sandbox, "disk", None),
                "created_at": created_at.isoformat() if isinstance(created_at, datetime) else created_at,
                "updated_at": (
                    getattr(sandbox, "updated_at", None).isoformat()
                    if isinstance(getattr(sandbox, "updated_at", None), datetime)
                    else getattr(sandbox, "updated_at", None)
                ),
                "labels": getattr(sandbox, "labels", None) or {},
                "hourly_burn_usd": sandbox_hourly_burn(sandbox) if "started" in state.lower() else 0.0,
            }
        )
    sandbox_details.sort(key=lambda item: item["hourly_burn_usd"], reverse=True)
    return teardown_candidates(sandbox_details, run_index, registry)


def evaluate_policy(
    policy: dict[str, Any],
    inventory: dict[str, Any],
    month_runtime_lower_bound_usd: float,
    estimate: dict[str, Any] | None,
    parallel_tasks: int | None,
) -> dict[str, list[str]]:
    warnings: list[str] = []
    blockers: list[str] = []

    def check(metric_name: str, value: float, label: str) -> None:
        warn_key = f"warn_{metric_name}"
        block_key = f"block_{metric_name}"
        warn_threshold = policy.get(warn_key)
        block_threshold = policy.get(block_key)
        if block_threshold is not None and value > float(block_threshold):
            blockers.append(f"{label} {value:.2f} exceeds block threshold {block_threshold}.")
        elif warn_threshold is not None and value > float(warn_threshold):
            warnings.append(f"{label} {value:.2f} exceeds warn threshold {warn_threshold}.")

    check("active_sandboxes", float(inventory["active_sandboxes"]), "Active sandboxes")
    check("active_hourly_burn_usd", float(inventory["active_hourly_burn_usd"]), "Active hourly burn")
    check("snapshot_storage_gb", float(inventory["snapshot_storage_gb"]), "Snapshot storage")
    check(
        "unlabeled_active_sandboxes",
        float(inventory["unlabeled_active_sandboxes"]),
        "Unlabeled active sandboxes",
    )

    if parallel_tasks is not None:
        check("parallel_tasks", float(parallel_tasks), "Parallel tasks")

    if estimate is not None:
        check("launch_estimate_usd", float(estimate["estimated_launch_usd"]), "Launch estimate")
        check("timeout_ceiling_usd", float(estimate["timeout_ceiling_usd"]), "Timeout ceiling")
        check("cold_task_configs", float(estimate["cold_task_configs"]), "Cold task/config count")

        monthly_budget = float(policy.get("monthly_budget_usd", 0.0) or 0.0)
        if monthly_budget > 0:
            projected_lower_bound = month_runtime_lower_bound_usd + float(estimate["estimated_launch_usd"])
            warn_budget = monthly_budget * float(policy.get("warn_fraction_of_monthly_budget", 0.50))
            block_budget = monthly_budget * float(policy.get("block_fraction_of_monthly_budget", 1.00))
            if projected_lower_bound > block_budget:
                blockers.append(
                    "Projected lower-bound month spend "
                    f"{format_currency(projected_lower_bound)} exceeds budget gate {format_currency(block_budget)}."
                )
            elif projected_lower_bound > warn_budget:
                warnings.append(
                    "Projected lower-bound month spend "
                    f"{format_currency(projected_lower_bound)} exceeds warn gate {format_currency(warn_budget)}."
                )

    return {"warnings": warnings, "blockers": blockers}


def print_summary(
    inventory: dict[str, Any],
    month_runtime_lower_bound_usd: float,
    estimate: dict[str, Any] | None,
    policy: dict[str, Any],
    evaluation: dict[str, list[str]],
) -> None:
    print("Daytona Cost Guard")
    print("------------------")
    print(
        "Live account: "
        f"{inventory['active_sandboxes']} active sandboxes, "
        f"{format_currency(inventory['active_hourly_burn_usd'])}/hr active burn"
    )
    print(f"Failed sandboxes: {inventory.get('failed_sandboxes', 0)}")
    print(f"Unlabeled active sandboxes: {inventory['unlabeled_active_sandboxes']}")
    print(
        "Snapshots: "
        f"{inventory['snapshots_total']} total, "
        f"{inventory['snapshot_storage_gb']:.1f} GiB stored, "
        f"{format_currency(inventory['snapshot_monthly_storage_usd'])}/month storage burn"
    )
    print(
        "Observed lower-bound runtime spend this month: "
        f"{format_currency(month_runtime_lower_bound_usd)}"
    )
    if estimate is not None:
        print(
            "Launch estimate: "
            f"{estimate['task_config_count']} task/config runs, "
            f"{format_currency(estimate['estimated_launch_usd'])} estimated, "
            f"{format_currency(estimate['timeout_ceiling_usd'])} timeout ceiling"
        )
        if estimate.get("excluded_task_configs"):
            print(
                "Excluded from Daytona estimate: "
                f"{estimate['excluded_task_configs']} task/config runs"
            )
        print(
            "Estimate sources: "
            + ", ".join(f"{source}={count}" for source, count in estimate["estimate_sources"].items())
        )
        if estimate.get("excluded_routes"):
            print(
                "Routing exclusions: "
                + ", ".join(
                    f"{reason}={count}" for reason, count in estimate["excluded_routes"].items()
                )
            )
        if estimate["cold_task_configs"]:
            print(f"Cold task/config pairs: {estimate['cold_task_configs']}")

        monthly_budget = float(policy.get("monthly_budget_usd", 0.0) or 0.0)
        if monthly_budget > 0:
            projected = month_runtime_lower_bound_usd + float(estimate["estimated_launch_usd"])
            print(
                "Projected lower-bound month spend after launch: "
                f"{format_currency(projected)} / {format_currency(monthly_budget)}"
            )

    if inventory["started_sandboxes"]:
        print("Top active sandboxes:")
        for sandbox in inventory["started_sandboxes"][:5]:
            labels = sandbox["labels"] or {}
            label_hint = sandbox_run_id(labels) or labels.get("label_benchmark") or labels.get("suite") or "unlabeled"
            print(
                f"  {sandbox['name']}  {sandbox['cpu']} CPU / {sandbox['memory_gib']} GiB / "
                f"{sandbox['disk_gib']} GiB  {format_currency(sandbox['hourly_burn_usd'])}/hr  {label_hint}"
            )

    if inventory.get("teardown_candidates"):
        print("Teardown candidates:")
        for sandbox in inventory["teardown_candidates"][:5]:
            run_hint = f" run_id={sandbox['run_id']}" if sandbox.get("run_id") else ""
            print(
                f"  {sandbox['name']}  state={sandbox.get('state','')} age={sandbox['age_hours']:.1f}h  "
                f"{format_currency(sandbox['hourly_burn_usd'])}/hr  "
                f"{sandbox['reason']}{run_hint}"
            )

    if inventory["largest_snapshots"]:
        print("Largest snapshots:")
        for snapshot in inventory["largest_snapshots"][:5]:
            print(
                f"  {snapshot['name']}  {snapshot['size_gb']:.2f} GiB  "
                f"state={snapshot['state']}  updated={snapshot['updated_at']}"
            )

    if estimate is not None and estimate["top_task_estimates"]:
        print("Top estimated task/config spend:")
        for task in estimate["top_task_estimates"][:5]:
            print(
                f"  {task['task_id']} [{task['config']}]  "
                f"{format_currency(task['estimate_usd'])}  source={task['source']}"
            )

    if evaluation["warnings"]:
        print("Warnings:")
        for warning in evaluation["warnings"]:
            print(f"  - {warning}")
    if evaluation["blockers"]:
        print("Blockers:")
        for blocker in evaluation["blockers"]:
            print(f"  - {blocker}")
        if inventory.get("teardown_candidate_count", 0) > 0:
            print(
                "Recommendation: investigate teardown candidates before waiting; "
                "the current block may be caused by stale active sandboxes."
            )


def emit_json(
    inventory: dict[str, Any],
    month_runtime_lower_bound_usd: float,
    estimate: dict[str, Any] | None,
    policy: dict[str, Any],
    evaluation: dict[str, list[str]],
) -> None:
    payload = {
        "inventory": inventory,
        "month_runtime_lower_bound_usd": month_runtime_lower_bound_usd,
        "estimate": estimate,
        "policy": policy,
        "evaluation": evaluation,
    }
    print(json.dumps(payload, indent=2, sort_keys=True, default=str))


def print_teardown_candidates(candidates: list[dict[str, Any]]) -> None:
    if not candidates:
        print("No teardown candidates matched the current filters.")
        return

    print("Selected teardown candidates:")
    for idx, sandbox in enumerate(candidates, start=1):
        run_hint = f" run_id={sandbox['run_id']}" if sandbox.get("run_id") else ""
        print(
            f"  {idx}. {sandbox['name']}  state={sandbox.get('state','')} age={sandbox['age_hours']:.1f}h  "
            f"{format_currency(sandbox['hourly_burn_usd'])}/hr  "
            f"{sandbox['reason']}{run_hint}"
        )


def teardown_candidate_sandboxes(args: argparse.Namespace) -> int:
    client = daytona_client()
    candidates = live_teardown_candidates(client)

    if args.names:
        wanted = set(args.names)
        candidates = [candidate for candidate in candidates if candidate["name"] in wanted]
    else:
        candidates = candidates[: max(args.limit, 0)]

    print_teardown_candidates(candidates)
    if not candidates:
        return 0

    if args.dry_run:
        print("Dry run only. No sandboxes deleted.")
        return 0

    if not args.yes:
        try:
            confirm = input("Type DELETE to remove these sandboxes: ").strip()
        except EOFError:
            confirm = ""
        if confirm != "DELETE":
            print("Aborted.")
            return 1

    sandboxes, _snapshots = fetch_daytona_inventory(client)
    deletable_by_ref = {}
    for sandbox in sandboxes:
        state = str(getattr(sandbox, "state", "")).lower()
        if "started" not in state and "failed" not in state:
            continue
        name = str(getattr(sandbox, "name", ""))
        sid = str(getattr(sandbox, "id", ""))
        if name:
            deletable_by_ref[name] = sandbox
        if sid:
            deletable_by_ref[sid] = sandbox

    deleted = 0
    failed = 0
    for candidate in candidates:
        ref = candidate.get("id") or candidate["name"]
        name = candidate["name"]
        sandbox = deletable_by_ref.get(ref) or deletable_by_ref.get(name)
        if sandbox is None:
            print(f"Skipped: {name} is no longer deletable")
            continue
        try:
            client.delete(sandbox)
            print(f"Deleted: {name}")
            deleted += 1
        except Exception as exc:
            print(f"Failed to delete {name}: {exc}")
            failed += 1

    print(f"Deleted {deleted} sandbox(es); {failed} failed.")
    return 0 if failed == 0 else 1


def main() -> int:
    args = parse_args()
    if args.command == "teardown-candidates":
        return teardown_candidate_sandboxes(args)

    policy = load_policy(args.policy)
    routing_policy = load_routing_policy(args.routing_policy) if getattr(args, "routing_policy", "") else {}
    registry = load_task_registry()
    history_cache = load_history_cache(registry)
    current_month = datetime.now(timezone.utc).strftime("%Y-%m")
    month_runtime_lower_bound_usd = float(
        (history_cache.get("monthly_runtime_lower_bound") or {}).get(current_month, 0.0)
    )
    inventory = live_inventory()

    estimate = None
    if args.command == "preflight":
        if not args.configs:
            raise SystemExit("At least one --config must be provided for preflight.")
        task_ids = list(args.task_ids)
        if args.task_id_file:
            task_ids.extend(
                [
                    line.strip()
                    for line in Path(args.task_id_file).read_text().splitlines()
                    if line.strip()
                ]
            )
        task_ids_filter = set(task_ids) if task_ids else None
        if args.selection_file:
            selected_tasks = select_tasks(
                selection_file=args.selection_file,
                benchmark_filter=args.benchmark,
                use_case_category_filter=args.use_case_category,
                task_ids_filter=task_ids_filter,
            )
        elif task_ids:
            selected_tasks = select_tasks_from_ids(task_ids, args.suite, registry)
        else:
            raise SystemExit("Preflight requires either --selection-file or at least one --task-id/--task-id-file.")
        estimate = launch_estimate(
            selected_tasks=selected_tasks,
            configs=args.configs,
            concurrency=args.concurrency,
            history_cache=history_cache,
            registry=registry,
            routing_policy=routing_policy,
        )
        parallel_tasks = args.parallel_tasks
    else:
        parallel_tasks = None

    evaluation = evaluate_policy(
        policy=policy,
        inventory=inventory,
        month_runtime_lower_bound_usd=month_runtime_lower_bound_usd,
        estimate=estimate,
        parallel_tasks=parallel_tasks,
    )

    if args.json:
        emit_json(
            inventory=inventory,
            month_runtime_lower_bound_usd=month_runtime_lower_bound_usd,
            estimate=estimate,
            policy=policy,
            evaluation=evaluation,
        )
    else:
        print_summary(
            inventory=inventory,
            month_runtime_lower_bound_usd=month_runtime_lower_bound_usd,
            estimate=estimate,
            policy=policy,
            evaluation=evaluation,
        )

    return 2 if evaluation["blockers"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
