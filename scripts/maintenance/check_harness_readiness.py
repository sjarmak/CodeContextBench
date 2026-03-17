#!/usr/bin/env python3
"""Preflight harness readiness checks for multi-harness benchmark runs.

Validates:
- `configs/harness_registry.json` exists and has required structure
- required harness registry keys and rollout MCP constraints
- required environment variables for selected harnesses

Usage:
    python3 scripts/check_harness_readiness.py
    python3 scripts/check_harness_readiness.py --harness codex
    python3 scripts/check_harness_readiness.py --format json
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_REGISTRY = ROOT / "configs" / "harness_registry.json"

REQUIRED_HARNESSES = ["codex", "cursor", "gemini", "copilot", "openhands"]
REQUIRED_ENTRY_KEYS = [
    "harness_name",
    "agent_import_path",
    "default_model",
    "allowed_mcp_modes",
]
REQUIRED_MCP_MODES = {"none", "sourcegraph_full"}

# Global env needed for MCP-enabled runs in this rollout.
GLOBAL_REQUIRED_ENVS = ["SOURCEGRAPH_ACCESS_TOKEN"]

# Harness-specific auth env guards. If optional marker files are present, auth can be file-backed.
HARNESS_REQUIRED_ENVS: dict[str, list[str]] = {
    "codex": ["OPENAI_API_KEY", "CODEX_API_KEY"],
    "gemini": ["GEMINI_API_KEY", "GOOGLE_API_KEY"],
}

HARNESS_AUTH_MARKER_FILES: dict[str, list[Path]] = {
    "codex": [Path.home() / ".codex" / "auth.json"],
}


@dataclass
class CheckResult:
    ok: bool
    errors: list[str]
    warnings: list[str]
    checked_harnesses: list[str]


def _load_registry(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    errors: list[str] = []
    if not path.is_file():
        return None, [f"Registry file not found: {path}"]

    try:
        data = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError) as exc:
        return None, [f"Failed to parse registry JSON: {exc}"]

    if not isinstance(data, dict):
        errors.append("Registry root must be a JSON object keyed by harness id")
        return None, errors

    return data, errors


def _validate_registry_structure(
    registry: dict[str, Any],
    selected_harnesses: list[str],
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    missing_harnesses = sorted(set(REQUIRED_HARNESSES) - set(registry.keys()))
    if missing_harnesses:
        errors.append(
            "Registry missing required harness entries: " + ", ".join(missing_harnesses)
        )

    for harness in selected_harnesses:
        entry = registry.get(harness)
        if entry is None:
            errors.append(f"Harness '{harness}' not found in registry")
            continue

        if not isinstance(entry, dict):
            errors.append(f"Harness '{harness}' entry must be an object")
            continue

        for key in REQUIRED_ENTRY_KEYS:
            if key not in entry:
                errors.append(f"Harness '{harness}' missing required field '{key}'")

        if not isinstance(entry.get("harness_name"), str):
            errors.append(f"Harness '{harness}' field 'harness_name' must be a string")
        elif entry["harness_name"] != harness:
            errors.append(
                f"Harness '{harness}' has harness_name='{entry['harness_name']}' (must match key)"
            )

        if not isinstance(entry.get("agent_import_path"), str):
            errors.append(f"Harness '{harness}' field 'agent_import_path' must be a string")

        if not isinstance(entry.get("default_model"), str):
            errors.append(f"Harness '{harness}' field 'default_model' must be a string")

        mcp_modes = entry.get("allowed_mcp_modes")
        if not isinstance(mcp_modes, list) or not all(
            isinstance(mode, str) for mode in mcp_modes
        ):
            errors.append(
                f"Harness '{harness}' field 'allowed_mcp_modes' must be a list of strings"
            )
        elif set(mcp_modes) != REQUIRED_MCP_MODES:
            errors.append(
                f"Harness '{harness}' allowed_mcp_modes must be exactly "
                f"{sorted(REQUIRED_MCP_MODES)}"
            )

        unknown_keys = sorted(set(entry.keys()) - set(REQUIRED_ENTRY_KEYS))
        if unknown_keys:
            warnings.append(
                f"Harness '{harness}' has extra keys (allowed but ignored): "
                + ", ".join(unknown_keys)
            )

    return errors, warnings


def _has_auth_marker(harness: str) -> bool:
    markers = HARNESS_AUTH_MARKER_FILES.get(harness, [])
    return any(marker.exists() for marker in markers)


def _validate_env(selected_harnesses: list[str]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    for env_var in GLOBAL_REQUIRED_ENVS:
        if not os.environ.get(env_var):
            errors.append(f"Missing required env var: {env_var}")

    for harness in selected_harnesses:
        any_of_envs = HARNESS_REQUIRED_ENVS.get(harness)
        if not any_of_envs:
            continue

        if _has_auth_marker(harness):
            warnings.append(
                f"Harness '{harness}' auth marker file found; skipping strict env auth check"
            )
            continue

        if not any(os.environ.get(env_var) for env_var in any_of_envs):
            errors.append(
                f"Harness '{harness}' requires one of env vars: {', '.join(any_of_envs)}"
            )

    return errors, warnings


def evaluate_readiness(registry_path: Path, harness: str | None) -> CheckResult:
    selected_harnesses = [harness] if harness else REQUIRED_HARNESSES

    registry, load_errors = _load_registry(registry_path)
    errors = list(load_errors)
    warnings: list[str] = []

    if registry is not None:
        structure_errors, structure_warnings = _validate_registry_structure(
            registry,
            selected_harnesses,
        )
        errors.extend(structure_errors)
        warnings.extend(structure_warnings)

    env_errors, env_warnings = _validate_env(selected_harnesses)
    errors.extend(env_errors)
    warnings.extend(env_warnings)

    return CheckResult(
        ok=not errors,
        errors=errors,
        warnings=warnings,
        checked_harnesses=selected_harnesses,
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate harness registry and environment readiness before runs.",
    )
    parser.add_argument(
        "--registry",
        default=str(DEFAULT_REGISTRY),
        help=f"Path to harness registry JSON (default: {DEFAULT_REGISTRY})",
    )
    parser.add_argument(
        "--harness",
        choices=REQUIRED_HARNESSES,
        help="Validate a single harness instead of all harnesses",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format (default: text)",
    )
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    result = evaluate_readiness(Path(args.registry), args.harness)

    if args.format == "json":
        print(
            json.dumps(
                {
                    "ok": result.ok,
                    "checked_harnesses": result.checked_harnesses,
                    "errors": result.errors,
                    "warnings": result.warnings,
                },
                indent=2,
            )
        )
    else:
        print(f"Harness readiness: {'OK' if result.ok else 'FAILED'}")
        print("Checked harnesses: " + ", ".join(result.checked_harnesses))
        if result.errors:
            print("Errors:")
            for err in result.errors:
                print(f"  - {err}")
        if result.warnings:
            print("Warnings:")
            for warn in result.warnings:
                print(f"  - {warn}")

    return 0 if result.ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
