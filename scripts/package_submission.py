#!/usr/bin/env python3
"""
Package benchmark results into a validated submission archive.

Validates each result.json against the CCB schema, checks for required
trajectory files, and bundles everything into a .tar.gz submission package.
"""

import argparse
import json
import sys
import tarfile
from pathlib import Path

try:
    import jsonschema
except ImportError:
    print("ERROR: jsonschema package required. Install with: pip install jsonschema", file=sys.stderr)
    sys.exit(1)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = PROJECT_ROOT / "schemas" / "result.schema.json"

TRAJECTORY_FILES = {"trajectory.json", "trajectory.txt"}


def load_schema() -> dict:
    if not SCHEMA_PATH.exists():
        print(f"ERROR: schema not found at {SCHEMA_PATH}", file=sys.stderr)
        sys.exit(1)
    with open(SCHEMA_PATH) as f:
        return json.load(f)


def validate_result(filepath: Path, schema: dict) -> list[str]:
    """Validate a single result.json. Returns list of error strings."""
    errors = []
    try:
        with open(filepath) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return [f"invalid JSON: {e}"]

    validator = jsonschema.Draft7Validator(schema)
    for error in sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path)):
        if error.validator == "required":
            parent = ".".join(str(p) for p in error.absolute_path) if error.absolute_path else ""
            missing = error.message.split("'")[1] if "'" in error.message else error.message
            full_path = f"{parent}.{missing}" if parent else missing
            errors.append(f"missing required field {full_path}")
        else:
            path = ".".join(str(p) for p in error.absolute_path) if error.absolute_path else "(root)"
            errors.append(f"{path}: {error.message}")
    return errors


def find_task_dirs(results_dir: Path) -> list[Path]:
    """Find task subdirectories containing result.json."""
    task_dirs = []
    for result_file in sorted(results_dir.rglob("result.json")):
        task_dirs.append(result_file.parent)
    return task_dirs


def main():
    parser = argparse.ArgumentParser(
        description="Package benchmark results into a validated submission .tar.gz archive."
    )
    parser.add_argument(
        "--results-dir",
        type=Path,
        required=True,
        help="Directory with task subdirs, each containing result.json + trajectory file.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Output path for the .tar.gz submission archive.",
    )
    args = parser.parse_args()

    if not args.results_dir.is_dir():
        print(f"ERROR: {args.results_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    schema = load_schema()
    task_dirs = find_task_dirs(args.results_dir)

    if not task_dirs:
        print(f"ERROR: no result.json files found in {args.results_dir}", file=sys.stderr)
        sys.exit(1)

    errors = []
    validated_dirs = []

    for task_dir in task_dirs:
        rel = task_dir.relative_to(args.results_dir)
        task_label = str(rel)

        # Validate result.json
        result_path = task_dir / "result.json"
        validation_errors = validate_result(result_path, schema)
        for err in validation_errors:
            errors.append(f"task {task_label}: {err}")

        # Check for trajectory file
        has_trajectory = any((task_dir / name).exists() for name in TRAJECTORY_FILES)
        if not has_trajectory:
            errors.append(f"task {task_label}: missing trajectory file (need trajectory.json or trajectory.txt)")

        if not validation_errors and has_trajectory:
            validated_dirs.append(task_dir)

    if errors:
        print("Validation failed:\n", file=sys.stderr)
        for err in errors:
            print(f"  {err}", file=sys.stderr)
        print(f"\n{len(errors)} error(s) found across {len(task_dirs)} tasks", file=sys.stderr)
        sys.exit(1)

    # Package into tar.gz
    output_path = args.output
    if not output_path.name.endswith(".tar.gz"):
        output_path = output_path.with_suffix(".tar.gz")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with tarfile.open(output_path, "w:gz") as tar:
        for task_dir in validated_dirs:
            rel = task_dir.relative_to(args.results_dir)
            for filepath in sorted(task_dir.rglob("*")):
                if filepath.is_file():
                    arcname = str(rel / filepath.relative_to(task_dir))
                    tar.add(filepath, arcname=arcname)

    print(f"Packaged {len(validated_dirs)} tasks into {output_path}")


if __name__ == "__main__":
    main()
