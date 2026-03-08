from __future__ import annotations

import re
import secrets
from pathlib import Path

from harbor.environments.daytona import DaytonaEnvironment


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
        # Reserve 5 chars for random suffix (-xxxx) to prevent collisions
        # when long task names truncate to the same prefix.
        sandbox_name_core = _sanitize_label_value(sandbox_name_core, max_length=40)
        rand_suffix = secrets.token_hex(2)  # 4 hex chars
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

    async def _create_sandbox(self, params):
        labels = dict(getattr(params, "labels", None) or {})
        labels.update(self._ccb_labels)
        params.labels = labels
        if not getattr(params, "name", None):
            params.name = self._ccb_sandbox_name
        await super()._create_sandbox(params)
