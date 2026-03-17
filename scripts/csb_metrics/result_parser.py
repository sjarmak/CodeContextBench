"""Unified result.json parser with schema awareness.

Provides consistent parsing of result.json files across all pipelines with proper
error handling and schema validation.
"""

import json
from pathlib import Path
from typing import Any, Optional


class ResultParser:
    """Unified parser for result.json files with schema awareness and error handling.

    Handles:
    - Loading result.json from task directories
    - Schema validation (checks for required fields)
    - Extracting common fields (task_name, config, verifier_result, etc.)
    - Safe access with sensible defaults
    """

    def __init__(self, result_path: Path | str):
        """Initialize parser with a result.json file path.

        Args:
            result_path: Path to result.json file

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is not valid JSON
        """
        self.path = Path(result_path)
        if not self.path.is_file():
            raise FileNotFoundError(f"result.json not found: {self.path}")

        try:
            self.data = json.loads(self.path.read_text())
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {self.path}: {e}")

        if not isinstance(self.data, dict):
            raise ValueError(f"result.json must be an object, got {type(self.data).__name__}")

    @property
    def is_valid_trial(self) -> bool:
        """Check if result.json looks like a valid trial result.

        A valid trial has:
        - Task identity (task_name, task_id, or trial_name)
        - Trial payload (agent_result, verifier_result, or config)
        """
        has_task_identity = any(
            self.data.get(key) for key in ("task_name", "task_id", "trial_name")
        )
        has_trial_payload = any(
            key in self.data for key in ("agent_result", "verifier_result", "config")
        )
        return has_task_identity and has_trial_payload

    def get_task_name(self) -> Optional[str]:
        """Extract task name from result.json."""
        return self.data.get("task_name") or self.data.get("task_id")

    def get_config(self) -> dict:
        """Extract config object from result.json."""
        return self.data.get("config", {})

    def get_model_name(self) -> str:
        """Extract model name from config in result.json."""
        config = self.get_config()
        agent = config.get("agent", {})
        return agent.get("model_name", "unknown")

    def get_verifier_result(self) -> dict:
        """Extract verifier_result from result.json."""
        return self.data.get("verifier_result", {})

    def get_agent_result(self) -> dict:
        """Extract agent_result from result.json."""
        return self.data.get("agent_result", {})

    def get_reward(self) -> Optional[float]:
        """Extract reward score from result.json with fallback to score field.

        Checks:
        1. verifier_result.rewards.reward
        2. verifier_result.rewards.score
        3. Other common field names
        """
        verifier = self.get_verifier_result()
        rewards = verifier.get("rewards", {})

        reward = rewards.get("reward")
        if reward is not None:
            return float(reward)

        reward = rewards.get("score")
        if reward is not None:
            return float(reward)

        # Fallback: check for top-level score field
        if "score" in self.data:
            try:
                return float(self.data["score"])
            except (TypeError, ValueError):
                pass

        return None

    def get_timing(self, phase: str) -> Optional[float]:
        """Extract timing for a specific phase.

        Args:
            phase: Phase name (e.g., 'agent_execution', 'environment_setup')

        Returns:
            Duration in seconds, or None if not found
        """
        # Check trajectory.json format (phases.XXX.duration_seconds)
        phases = self.data.get("phases", {})
        if phase in phases:
            return phases[phase].get("duration_seconds")

        # Check legacy format (XXX_seconds at top level)
        key = f"{phase}_seconds"
        if key in self.data:
            return self.data.get(key)

        return None

    def get_exception_info(self) -> Optional[str]:
        """Extract exception information if task failed."""
        return self.data.get("exception_info")

    def get_started_at(self) -> str:
        """Extract task start timestamp."""
        return self.data.get("started_at", "")

    def get_finished_at(self) -> str:
        """Extract task end timestamp."""
        return self.data.get("finished_at", "")

    def get_field(self, key: str, default: Any = None) -> Any:
        """Safely get any field from result.json.

        Args:
            key: Field name (supports nested keys with dot notation, e.g. 'config.agent.model_name')
            default: Value to return if key not found

        Returns:
            Field value or default
        """
        if "." not in key:
            return self.data.get(key, default)

        # Handle nested keys
        parts = key.split(".")
        current = self.data
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
                if current is None:
                    return default
            else:
                return default
        return current

    @classmethod
    def load_all_in_directory(
        cls, directory: Path | str, recursive: bool = True
    ) -> list["ResultParser"]:
        """Load all result.json files in a directory.

        Args:
            directory: Root directory to search
            recursive: If True, search subdirectories recursively

        Returns:
            List of successfully loaded ResultParser instances
        """
        root = Path(directory)
        parsers = []

        glob_pattern = "**/*.json" if recursive else "*.json"
        for result_file in sorted(root.glob(glob_pattern)):
            if result_file.name != "result.json":
                continue
            try:
                parser = cls(result_file)
                if parser.is_valid_trial:
                    parsers.append(parser)
            except (FileNotFoundError, ValueError):
                # Skip files that can't be parsed
                pass

        return parsers
