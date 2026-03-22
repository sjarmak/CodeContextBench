from __future__ import annotations

import logging
import os
import re
import secrets
from pathlib import Path

from daytona import DaytonaError
from harbor.environments.daytona import DaytonaEnvironment

logger = logging.getLogger(__name__)

# Host env vars to forward into docker-compose builds inside Daytona DinD.
# These appear as ${VAR} in docker-compose.yaml build.args sections.
_COMPOSE_PASSTHROUGH_ENV_VARS = ("GITHUB_TOKEN",)


def _sanitize_label_value(value: str, max_length: int = 63) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9_.-]+", "-", value.strip()).strip("-.")
    if not normalized:
        return ""
    return normalized[:max_length]


class GuardedDaytonaEnvironment(DaytonaEnvironment):
    """Repo-local Daytona environment with stable labels and sandbox names."""

    def __init__(
        self,
        *args,
        label_launcher: str | None = None,
        label_run_id: str | None = None,
        label_benchmark: str | None = None,
        label_task_id: str | None = None,
        label_config: str | None = None,
        label_job_name: str | None = None,
        label_category: str | None = None,
        label_model: str | None = None,
        label_mcp_type: str | None = None,
        task_source_dir: str | None = None,
        **kwargs,
    ):
        task_source_path = Path(task_source_dir) if task_source_dir else None
        derived_task_id = label_task_id or (
            task_source_path.name if task_source_path and task_source_path.name else None
        )
        derived_benchmark = label_benchmark or (
            task_source_path.parent.name if task_source_path and task_source_path.parent.name else None
        )

        self._ccb_labels = {
            "managed_by": "codescalebench",
            "launcher": label_launcher or "unknown",
            "run_id": label_run_id or "",
            "benchmark": derived_benchmark or "",
            "task_id": derived_task_id or "",
            "config": label_config or "",
            "job_name": label_job_name or "",
            "category": label_category or "",
            "model": label_model or "",
            "mcp_type": label_mcp_type or "",
        }
        self._ccb_labels = {
            key: sanitized
            for key, value in self._ccb_labels.items()
            if (sanitized := _sanitize_label_value(str(value)))
        }

        sandbox_name_parts = [
            self._ccb_labels.get("benchmark", ""),
            self._ccb_labels.get("task_id", ""),
            self._ccb_labels.get("config", ""),
        ]
        sandbox_name_core = "-".join(part for part in sandbox_name_parts if part)
        # Reserve 9 chars for random suffix (-xxxxxxxx) to make collisions
        # between concurrent runs near-impossible.
        sandbox_name_core = _sanitize_label_value(sandbox_name_core, max_length=40)
        rand_suffix = secrets.token_hex(4)  # 8 hex chars
        session_hint = kwargs.get("session_id", "")
        session_hint = _sanitize_label_value(str(session_hint), max_length=12)
        if sandbox_name_core:
            self._ccb_sandbox_name = f"ccb-{sandbox_name_core}-{rand_suffix}"
            if session_hint:
                self._ccb_sandbox_name = f"{self._ccb_sandbox_name}-{session_hint}"
        else:
            self._ccb_sandbox_name = f"ccb-{session_hint or 'sandbox'}-{rand_suffix}"
        self._ccb_sandbox_name = _sanitize_label_value(self._ccb_sandbox_name, max_length=63)

        super().__init__(*args, **kwargs)

        # Patch the DinD strategy's _compose_env_vars to forward host env vars
        # (e.g. GITHUB_TOKEN) into docker-compose builds.  Harbor's upstream
        # _DaytonaDinD._compose_env_vars only includes its own internal vars;
        # tasks that need GITHUB_TOKEN as a Docker build arg would fail.
        strategy = getattr(self, "_strategy", None)
        logger.debug(
            "strategy=%s, has_compose_env_vars=%s",
            strategy.__class__.__name__ if strategy else None,
            hasattr(strategy, "_compose_env_vars") if strategy else False,
        )
        if strategy is not None and hasattr(strategy, "_compose_env_vars"):
            _original_compose_env_vars = strategy._compose_env_vars

            def _patched_compose_env_vars() -> dict[str, str]:
                env_vars = _original_compose_env_vars()
                for var_name in _COMPOSE_PASSTHROUGH_ENV_VARS:
                    val = os.environ.get(var_name, "")
                    if val:
                        env_vars[var_name] = val
                        logger.debug("Forwarding %s to compose env", var_name)
                return env_vars

            strategy._compose_env_vars = _patched_compose_env_vars
            logger.info(
                "Patched _compose_env_vars to forward: %s",
                ", ".join(_COMPOSE_PASSTHROUGH_ENV_VARS),
            )

    async def _create_sandbox(self, params):
        labels = dict(getattr(params, "labels", None) or {})
        labels.update(self._ccb_labels)
        params.labels = labels
        if not getattr(params, "name", None):
            params.name = self._ccb_sandbox_name

        max_retries = 3
        for attempt in range(max_retries + 1):
            try:
                await super()._create_sandbox(params)
                return
            except DaytonaError as exc:
                if "already exists" not in str(exc):
                    raise
                if attempt >= max_retries:
                    raise

                sandbox_name = getattr(params, "name", "")

                # Check if the existing sandbox is failed/stale before deleting.
                # Never delete actively running sandboxes from concurrent batches.
                _deleted = False
                try:
                    daytona = await self._client_manager.get_client()
                    stale = await daytona.get(sandbox_name)
                    stale_state = str(getattr(stale, "state", ""))
                    if "FAILED" in stale_state or "ERROR" in stale_state:
                        logger.warning(
                            "Sandbox %r is %s — deleting stale sandbox",
                            sandbox_name,
                            stale_state,
                        )
                        await daytona.delete(stale, timeout=60)
                        _deleted = True
                    else:
                        logger.info(
                            "Sandbox %r exists and is %s (not stale) — "
                            "retrying with new name",
                            sandbox_name,
                            stale_state,
                        )
                except Exception as lookup_err:
                    logger.warning(
                        "Could not inspect sandbox %r: %s",
                        sandbox_name,
                        lookup_err,
                    )

                # Always generate a fresh random suffix for the retry,
                # whether or not we deleted the old sandbox.
                new_suffix = secrets.token_hex(4)
                new_name = re.sub(
                    r"-[0-9a-f]{8}(-|$)",
                    f"-{new_suffix}\\1",
                    sandbox_name,
                    count=1,
                )
                if new_name == sandbox_name:
                    # Also handle old 4-char suffixes from pre-existing runs.
                    new_name = re.sub(
                        r"-[0-9a-f]{4}(-|$)",
                        f"-{new_suffix}\\1",
                        sandbox_name,
                        count=1,
                    )
                if new_name == sandbox_name:
                    new_name = _sanitize_label_value(
                        f"{sandbox_name}-{new_suffix}", max_length=63
                    )
                params.name = new_name
                self._ccb_sandbox_name = new_name
                logger.info(
                    "Retry %d/%d: creating sandbox as %r",
                    attempt + 1,
                    max_retries,
                    new_name,
                )
