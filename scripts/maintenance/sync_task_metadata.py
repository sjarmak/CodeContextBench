#!/usr/bin/env python3
"""Reconcile task metadata between selected_benchmark_tasks.json and task.toml files.

Uses selected_benchmark_tasks.json as the authoritative source and checks
that each task's task.toml has matching language, difficulty, and other fields.

Usage:
    # Report mismatches (dry-run)
    python3 scripts/sync_task_metadata.py

    # Auto-fix mismatches in task.toml files
    python3 scripts/sync_task_metadata.py --fix

    # Filter to one suite
    python3 scripts/sync_task_metadata.py --suite ccb_pytorch

    # JSON output
    python3 scripts/sync_task_metadata.py --format json
"""

import argparse
import json
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BENCHMARKS_DIR = PROJECT_ROOT / "benchmarks"
SELECTED_TASKS_PATH = PROJECT_ROOT / "configs" / "selected_benchmark_tasks.json"


def load_selected_tasks() -> list[dict]:
    """Load the authoritative task list."""
    if not SELECTED_TASKS_PATH.is_file():
        print(f"ERROR: {SELECTED_TASKS_PATH} not found", file=sys.stderr)
        sys.exit(1)
    data = json.loads(SELECTED_TASKS_PATH.read_text())
    return data.get("tasks", [])


def find_task_toml(task: dict) -> Path | None:
    """Find the task.toml for a selected task."""
    task_dir = task.get("task_dir", "")
    if task_dir:
        path = BENCHMARKS_DIR / task_dir / "task.toml"
        if path.is_file():
            return path

    # Fallback: search by task_id in benchmark dir
    benchmark = task.get("benchmark", "")
    task_id = task.get("task_id", "")
    if benchmark and task_id:
        path = BENCHMARKS_DIR / benchmark / task_id / "task.toml"
        if path.is_file():
            return path
        # swebenchpro uses tasks/ subdirectory
        path = BENCHMARKS_DIR / benchmark / "tasks" / task_id / "task.toml"
        if path.is_file():
            return path

    return None


def parse_toml_field(content: str, section: str, field: str) -> str | None:
    """Extract a field value from TOML content (simple parser)."""
    in_section = False
    section_pattern = re.compile(rf"^\[{re.escape(section)}\]")

    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("["):
            in_section = bool(section_pattern.match(stripped))
            continue
        if in_section and "=" in stripped:
            key, _, val = stripped.partition("=")
            if key.strip() == field:
                return val.strip().strip('"').strip("'")
    return None


def update_toml_field(content: str, section: str, field: str, new_value: str) -> str:
    """Update a field in TOML content. Returns modified content."""
    lines = content.splitlines(keepends=True)
    in_section = False
    section_pattern = re.compile(rf"^\[{re.escape(section)}\]")

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("["):
            in_section = bool(section_pattern.match(stripped))
            continue
        if in_section and "=" in stripped:
            key, _, _ = stripped.partition("=")
            if key.strip() == field:
                # Preserve indentation
                indent = line[:len(line) - len(line.lstrip())]
                lines[i] = f'{indent}{field} = "{new_value}"\n'
                return "".join(lines)

    return content  # Field not found, return unchanged


def compare_task(task: dict, toml_path: Path) -> list[dict]:
    """Compare selected task metadata against task.toml. Returns mismatches."""
    mismatches = []
    content = toml_path.read_text()

    # Fields to compare: (selected_key, toml_section, toml_field)
    fields = [
        ("language", "task", "language"),
        ("difficulty", "task", "difficulty"),
    ]

    for sel_key, section, field in fields:
        selected_val = task.get(sel_key, "")
        toml_val = parse_toml_field(content, section, field)

        if not selected_val or not toml_val:
            continue

        if selected_val != toml_val:
            mismatches.append({
                "task_id": task.get("task_id", ""),
                "benchmark": task.get("benchmark", ""),
                "field": field,
                "selected_value": selected_val,
                "toml_value": toml_val,
                "toml_path": str(toml_path),
            })

    return mismatches


def fix_mismatch(mismatch: dict) -> bool:
    """Fix a single mismatch by updating task.toml."""
    toml_path = Path(mismatch["toml_path"])
    content = toml_path.read_text()

    new_content = update_toml_field(
        content, "task", mismatch["field"], mismatch["selected_value"]
    )

    if new_content != content:
        toml_path.write_text(new_content)
        return True
    return False


def main():
    parser = argparse.ArgumentParser(
        description="Reconcile task metadata between selection registry and task.toml files."
    )
    parser.add_argument("--suite", default=None,
                        help="Filter to one benchmark suite")
    parser.add_argument("--fix", action="store_true",
                        help="Auto-fix mismatches by updating task.toml")
    parser.add_argument("--format", choices=["table", "json"], default="table")
    args = parser.parse_args()

    tasks = load_selected_tasks()
    if args.suite:
        tasks = [t for t in tasks if t.get("benchmark") == args.suite]

    all_mismatches = []
    missing_toml = []
    checked = 0

    for task in tasks:
        toml_path = find_task_toml(task)
        if toml_path is None:
            missing_toml.append({
                "task_id": task.get("task_id", ""),
                "benchmark": task.get("benchmark", ""),
                "task_dir": task.get("task_dir", ""),
            })
            continue

        checked += 1
        mismatches = compare_task(task, toml_path)
        all_mismatches.extend(mismatches)

    # Apply fixes if requested
    fixed = 0
    if args.fix and all_mismatches:
        for m in all_mismatches:
            if fix_mismatch(m):
                fixed += 1
                m["fixed"] = True
            else:
                m["fixed"] = False

    # Output
    if args.format == "json":
        output = {
            "tasks_checked": checked,
            "tasks_missing_toml": len(missing_toml),
            "mismatches_found": len(all_mismatches),
            "mismatches_fixed": fixed,
            "mismatches": all_mismatches,
            "missing_toml": missing_toml,
        }
        print(json.dumps(output, indent=2))
    else:
        print(f"Metadata Sync: checked {checked} tasks against selected_benchmark_tasks.json")
        print()

        if missing_toml:
            print(f"MISSING task.toml ({len(missing_toml)}):")
            for m in missing_toml:
                print(f"  {m['benchmark']}/{m['task_id']}: no task.toml found")
            print()

        if all_mismatches:
            print(f"MISMATCHES ({len(all_mismatches)}):")
            for m in all_mismatches:
                fixed_str = " -> FIXED" if m.get("fixed") else ""
                print(f"  {m['benchmark']}/{m['task_id']}: "
                      f"{m['field']}='{m['toml_value']}' should be '{m['selected_value']}'{fixed_str}")
            print()

            if not args.fix and all_mismatches:
                print(f"Run with --fix to auto-update {len(all_mismatches)} task.toml file(s).")
        else:
            print("All metadata in sync.")

    sys.exit(1 if all_mismatches and not args.fix else 0)


if __name__ == "__main__":
    main()
