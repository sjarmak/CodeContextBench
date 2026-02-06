#!/usr/bin/env python3
"""
Ingest per-task LLM judge results into a centralized judge_scores.json.

Scans judge_results/{benchmark}/{config}/{task_id}_judge_result.json files,
validates against the schema, and outputs a single index file for efficient
downstream consumption by generate_manifest.py and generate_leaderboard.py.

Usage:
    python3 scripts/ingest_judge_results.py
    python3 scripts/ingest_judge_results.py --judge-results-dir ./judge_results --output ./judge_scores.json
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = PROJECT_ROOT / "schemas" / "judge_result.schema.json"


def load_schema() -> dict | None:
    """Load the judge_result schema for validation. Returns None if unavailable."""
    if not SCHEMA_PATH.exists():
        return None
    try:
        return json.loads(SCHEMA_PATH.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def validate_judge_result(data: dict, schema: dict | None) -> list[str]:
    """Validate a judge result dict. Returns list of error strings."""
    errors = []

    # Check required fields manually (no jsonschema dependency required)
    required = ["task_id", "benchmark", "config", "judge_score", "judge_model", "judged_at"]
    for field in required:
        if field not in data:
            errors.append(f"missing required field: {field}")

    # Validate judge_score range
    score = data.get("judge_score")
    if score is not None:
        if not isinstance(score, (int, float)):
            errors.append(f"judge_score must be a number, got {type(score).__name__}")
        elif not (0.0 <= score <= 1.0):
            errors.append(f"judge_score must be 0.0-1.0, got {score}")

    # Validate rubric scores if present
    rubric = data.get("rubric")
    if rubric is not None:
        if not isinstance(rubric, dict):
            errors.append(f"rubric must be an object, got {type(rubric).__name__}")
        else:
            for dim, val in rubric.items():
                if not isinstance(val, (int, float)):
                    errors.append(f"rubric.{dim} must be a number, got {type(val).__name__}")
                elif not (0.0 <= val <= 1.0):
                    errors.append(f"rubric.{dim} must be 0.0-1.0, got {val}")

    # If jsonschema is available and schema loaded, do full validation
    if schema is not None:
        try:
            import jsonschema
            validator = jsonschema.Draft7Validator(schema)
            for error in validator.iter_errors(data):
                path = ".".join(str(p) for p in error.absolute_path) if error.absolute_path else "(root)"
                errors.append(f"schema: {path}: {error.message}")
        except ImportError:
            pass  # jsonschema not installed, manual validation above is sufficient

    return errors


def ingest(judge_results_dir: Path) -> dict:
    """Scan judge result files and build the centralized index.

    Looks for files matching:
        {judge_results_dir}/{benchmark}/{config}/{task_id}_judge_result.json

    Also accepts judge_result.json files placed directly in Harbor task dirs
    (for the alternative discovery path).

    Returns the judge_scores index dict.
    """
    schema = load_schema()
    scores: dict[str, dict] = {}
    judge_model = None
    errors_total = 0
    files_scanned = 0

    if not judge_results_dir.is_dir():
        print(f"Warning: judge results directory not found: {judge_results_dir}", file=sys.stderr)
        return _build_output(scores, judge_model)

    # Walk the directory tree looking for *_judge_result.json or judge_result.json
    for json_file in sorted(judge_results_dir.rglob("*judge_result.json")):
        files_scanned += 1
        try:
            data = json.loads(json_file.read_text())
        except (json.JSONDecodeError, OSError) as e:
            print(f"  SKIP {json_file}: {e}", file=sys.stderr)
            errors_total += 1
            continue

        # Validate
        validation_errors = validate_judge_result(data, schema)
        if validation_errors:
            print(f"  INVALID {json_file}:", file=sys.stderr)
            for err in validation_errors:
                print(f"    - {err}", file=sys.stderr)
            errors_total += 1
            continue

        # Extract key fields
        benchmark = data["benchmark"]
        config = data["config"]
        task_id = data["task_id"]
        key = f"{benchmark}/{config}/{task_id}"

        entry: dict = {"judge_score": data["judge_score"]}
        if data.get("rubric"):
            entry["rubric"] = data["rubric"]
        if data.get("rationale"):
            entry["rationale"] = data["rationale"]
        if data.get("judged_at"):
            entry["judged_at"] = data["judged_at"]

        scores[key] = entry

        # Track judge model (use the first one seen; warn if mixed)
        model = data.get("judge_model")
        if model:
            if judge_model is None:
                judge_model = model
            elif model != judge_model:
                print(f"  Warning: mixed judge models: {judge_model} vs {model}", file=sys.stderr)

    print(f"Scanned {files_scanned} files, {len(scores)} valid, {errors_total} errors")
    return _build_output(scores, judge_model)


def _build_output(scores: dict, judge_model: str | None) -> dict:
    return {
        "generated": datetime.now(timezone.utc).isoformat(),
        "judge_model": judge_model,
        "total_judged": len(scores),
        "scores": scores,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Ingest per-task LLM judge results into centralized judge_scores.json",
    )
    parser.add_argument(
        "--judge-results-dir",
        type=Path,
        default=PROJECT_ROOT / "judge_results",
        help="Directory containing judge result files (default: ./judge_results)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "judge_scores.json",
        help="Output path for centralized judge scores (default: ./judge_scores.json)",
    )
    args = parser.parse_args()

    result = ingest(args.judge_results_dir)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(result, f, indent=2)

    print(f"Wrote {args.output}")
    print(f"  Total judged: {result['total_judged']}")
    print(f"  Judge model: {result['judge_model'] or '(none)'}")


if __name__ == "__main__":
    main()
