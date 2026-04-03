#!/usr/bin/env python3
"""Validate a CodeScaleBench submission JSON against the submission schema.

Usage:
    python3 scripts/evaluation/validate_submission.py results.json
    python3 scripts/evaluation/validate_submission.py --help

Exit codes:
    0 — valid submission
    1 — invalid submission (errors printed to stderr)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_SCHEMA_PATH = _REPO_ROOT / "schemas" / "submission.schema.json"


def _validate_with_jsonschema(data: dict, schema: dict) -> list[str]:
    """Validate using jsonschema library if available."""
    import jsonschema  # type: ignore[import-untyped]

    validator = jsonschema.Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path))
    return [
        f"  {'.'.join(str(p) for p in e.absolute_path) or '(root)'}: {e.message}"
        for e in errors
    ]


def _validate_manually(data: dict, schema: dict) -> list[str]:
    """Minimal manual validation when jsonschema is not installed."""
    errors: list[str] = []

    # Check required top-level keys
    for key in schema.get("required", []):
        if key not in data:
            errors.append(f"  (root): Missing required field '{key}'")

    # Check types of top-level fields
    if "csb_score" in data:
        if not isinstance(data["csb_score"], (int, float)):
            errors.append("  csb_score: Must be a number")
        elif not (0 <= data["csb_score"] <= 100):
            errors.append("  csb_score: Must be between 0 and 100")

    if "results" in data:
        if not isinstance(data["results"], list):
            errors.append("  results: Must be an array")
        else:
            for i, result in enumerate(data["results"]):
                if not isinstance(result, dict):
                    errors.append(f"  results.{i}: Must be an object")
                    continue
                if "task_name" not in result:
                    errors.append(f"  results.{i}: Missing required field 'task_name'")
                if "reward" not in result:
                    errors.append(f"  results.{i}: Missing required field 'reward'")
                elif not isinstance(result["reward"], (int, float)):
                    errors.append(f"  results.{i}.reward: Must be a number")
                elif not (0.0 <= result["reward"] <= 1.0):
                    errors.append(f"  results.{i}.reward: Must be between 0.0 and 1.0")

    if "metadata" in data:
        if not isinstance(data["metadata"], dict):
            errors.append("  metadata: Must be an object")
        else:
            for key in ("timestamp", "csb_version"):
                if key not in data["metadata"]:
                    errors.append(f"  metadata: Missing required field '{key}'")

    if "agent_info" in data:
        if not isinstance(data["agent_info"], dict):
            errors.append("  agent_info: Must be an object")
        elif "name" not in data["agent_info"]:
            errors.append("  agent_info: Missing required field 'name'")

    return errors


def validate_submission(submission_path: str | Path) -> list[str]:
    """Validate a submission JSON file against the schema.

    Returns a list of error strings (empty if valid).
    """
    submission_path = Path(submission_path)

    if not submission_path.exists():
        return [f"File not found: {submission_path}"]

    try:
        with open(submission_path) as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        return [f"Invalid JSON: {exc}"]

    if not _SCHEMA_PATH.exists():
        return [f"Schema not found: {_SCHEMA_PATH}"]

    with open(_SCHEMA_PATH) as f:
        schema = json.load(f)

    try:
        return _validate_with_jsonschema(data, schema)
    except ImportError:
        return _validate_manually(data, schema)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate a CodeScaleBench submission JSON against the submission schema.",
    )
    parser.add_argument(
        "submission",
        help="Path to the submission JSON file to validate.",
    )
    args = parser.parse_args(argv)

    errors = validate_submission(args.submission)

    if not errors:
        print(f"[OK] {args.submission} is a valid submission.")
        return 0

    print(f"[INVALID] {args.submission} has {len(errors)} error(s):", file=sys.stderr)
    for err in errors:
        print(err, file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
