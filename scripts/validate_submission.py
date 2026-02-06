#!/usr/bin/env python3
"""
Validate a submission directory against the result.json JSON Schema.

Walks --submission-dir looking for result.json files, validates each
against schemas/result.schema.json, and reports per-file status.
"""

import argparse
import json
import sys
from pathlib import Path

try:
    import jsonschema
except ImportError:
    print("ERROR: jsonschema package required. Install with: pip install jsonschema", file=sys.stderr)
    sys.exit(1)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = PROJECT_ROOT / "schemas" / "result.schema.json"


def load_schema() -> dict:
    if not SCHEMA_PATH.exists():
        print(f"ERROR: schema not found at {SCHEMA_PATH}", file=sys.stderr)
        sys.exit(1)
    with open(SCHEMA_PATH) as f:
        return json.load(f)


def find_result_files(submission_dir: Path) -> list[Path]:
    """Find all result.json files under submission_dir."""
    return sorted(submission_dir.rglob("result.json"))


def format_validation_error(error: jsonschema.ValidationError) -> str:
    """Format a validation error with JSONPath to the failing field."""
    if error.validator == "required":
        # error.message is like "'verifier_result' is a required property"
        # Build full path: parent path + missing field name
        parent = ".".join(str(p) for p in error.absolute_path) if error.absolute_path else ""
        missing = error.message.split("'")[1] if "'" in error.message else error.message
        full_path = f"{parent}.{missing}" if parent else missing
        return f"missing required field {full_path}"
    path = ".".join(str(p) for p in error.absolute_path) if error.absolute_path else "(root)"
    return f"{path}: {error.message}"


def validate_file(filepath: Path, schema: dict) -> list[str]:
    """Validate a single result.json file. Returns list of error strings."""
    errors = []
    try:
        with open(filepath) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return [f"invalid JSON: {e}"]

    validator = jsonschema.Draft7Validator(schema)
    for error in sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path)):
        errors.append(format_validation_error(error))
    return errors


def main():
    parser = argparse.ArgumentParser(
        description="Validate a submission directory of result.json files against the CCB schema."
    )
    parser.add_argument(
        "--submission-dir",
        type=Path,
        required=True,
        help="Directory containing task subdirectories with result.json files.",
    )
    args = parser.parse_args()

    if not args.submission_dir.is_dir():
        print(f"ERROR: {args.submission_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    schema = load_schema()
    result_files = find_result_files(args.submission_dir)

    if not result_files:
        print(f"WARNING: no result.json files found in {args.submission_dir}", file=sys.stderr)
        sys.exit(1)

    total = len(result_files)
    valid_count = 0
    invalid_count = 0

    for filepath in result_files:
        # Derive task name from parent directory structure
        rel = filepath.relative_to(args.submission_dir)
        task_label = str(rel.parent) if str(rel.parent) != "." else filepath.parent.name

        errors = validate_file(filepath, schema)
        if errors:
            invalid_count += 1
            for err in errors:
                print(f"FAIL  task {task_label}: {err}")
        else:
            valid_count += 1
            print(f"OK    task {task_label}")

    print(f"\n{total} files checked: {valid_count} valid, {invalid_count} invalid")

    if invalid_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
