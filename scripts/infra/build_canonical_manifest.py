#!/usr/bin/env python3
"""
Build canonical manifest of all CSB benchmarks.

Scans benchmarks/csb_*/ directories, extracts metadata from task.toml files,
and generates a canonical manifest JSON at benchmarks/CANONICAL.json.

This manifest serves as the authoritative registry of all benchmark tasks,
their properties, locations, and metadata.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore


def is_canonical_task(task_dir: Path) -> bool:
    """
    Check if a task is canonical (has dual verifiers).

    Canonical tasks are those with dual_score_lib.sh in the tests directory,
    indicating they have both local and Sourcegraph verification.
    """
    dual_verifier = task_dir / "tests" / "dual_score_lib.sh"
    return dual_verifier.exists()


def load_task_metadata(task_dir: Path) -> Dict[str, Any]:
    """
    Load metadata from a task's task.toml file.

    Returns dict with task properties, or None if task.toml not found.
    """
    task_toml = task_dir / "task.toml"
    if not task_toml.exists():
        return None

    try:
        with open(task_toml, "rb") as f:
            data = tomllib.load(f)
        return data
    except Exception as e:
        print(f"Error parsing {task_toml}: {e}", file=sys.stderr)
        return None


def scan_benchmark_categories(repo_root: Path) -> Dict[str, List[Dict[str, Any]]]:
    """
    Scan all benchmarks/csb_*/ directories and collect task metadata.

    Returns dict mapping category -> list of task records.
    Category names derived from directory names (e.g., csb_sdlc_debug -> sdlc_debug).
    """
    benchmarks_dir = repo_root / "benchmarks"
    if not benchmarks_dir.exists():
        print(f"Error: benchmarks directory not found at {benchmarks_dir}", file=sys.stderr)
        sys.exit(1)

    categories = {}

    # Find all csb_*/ and csb/ directories
    for cat_dir in sorted(benchmarks_dir.glob("csb*")):
        if not cat_dir.is_dir():
            continue

        # Derive category name: csb_sdlc_debug -> sdlc_debug, csb -> base
        if cat_dir.name == "csb":
            category_name = "base"
        else:
            # Remove 'csb_' prefix
            category_name = cat_dir.name[4:] if cat_dir.name.startswith("csb_") else cat_dir.name

        tasks = []

        # Scan subdirectories within each category for task.toml files
        # Tasks can be directly in cat_dir or in subcategories (like csb/debug/)
        if cat_dir.name == "csb":
            # csb/ has subcategories like csb/debug/, csb/feature/, etc.
            for subcat_dir in sorted(cat_dir.iterdir()):
                if not subcat_dir.is_dir():
                    continue

                # Each directory under the subcategory is a task
                for task_dir in sorted(subcat_dir.iterdir()):
                    if task_dir.is_dir():
                        # Only include canonical tasks (with dual verifiers)
                        if not is_canonical_task(task_dir):
                            continue
                        metadata = load_task_metadata(task_dir)
                        if metadata:
                            task_record = {
                                "id": task_dir.name,
                                "path": str(task_dir.relative_to(repo_root)),
                                "category": category_name,
                                "subcategory": subcat_dir.name,
                                "is_canonical": True,
                                **metadata
                            }
                            tasks.append(task_record)
        else:
            # csb_org_*/ and csb_sdlc_*/ have tasks directly as subdirectories
            # Skip these - only canonical (dual-verified) tasks from csb/ are included
            pass

        if tasks:
            categories[category_name] = tasks

    return categories


def build_canonical_manifest(repo_root: Path) -> Dict[str, Any]:
    """
    Build the complete canonical manifest structure.

    Only includes canonical tasks (those with dual verifiers: local + Sourcegraph).
    """
    categories = scan_benchmark_categories(repo_root)

    # Build manifest
    manifest = {
        "version": "1.0",
        "description": "Canonical benchmark tasks with dual verification (local + Sourcegraph)",
        "timestamp": None,  # Will be set at write time
        "categories": categories,
        "statistics": {
            "total_tasks": sum(len(tasks) for tasks in categories.values()),
            "categories": len(categories),
            "by_language": {},
            "by_difficulty": {},
            "by_verification_type": {}
        }
    }

    # Compute statistics
    for category_tasks in categories.values():
        for task in category_tasks:
            # Count by language
            language = task.get("task", {}).get("language", "unknown")
            manifest["statistics"]["by_language"][language] = \
                manifest["statistics"]["by_language"].get(language, 0) + 1

            # Count by difficulty
            difficulty = task.get("task", {}).get("difficulty", "unknown")
            manifest["statistics"]["by_difficulty"][difficulty] = \
                manifest["statistics"]["by_difficulty"].get(difficulty, 0) + 1

            # Count by verification type
            verification = task.get("verification", {})
            v_type = verification.get("type", "unknown") if verification else "unknown"
            manifest["statistics"]["by_verification_type"][v_type] = \
                manifest["statistics"]["by_verification_type"].get(v_type, 0) + 1

    return manifest


def main():
    """Main entry point."""
    repo_root = Path(__file__).parent.parent

    print(f"Scanning benchmarks in {repo_root}/benchmarks/...", file=sys.stderr)

    manifest = build_canonical_manifest(repo_root)

    output_file = repo_root / "benchmarks" / "CANONICAL.json"

    print(f"Writing manifest to {output_file}...", file=sys.stderr)

    with open(output_file, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"✓ Canonical manifest created", file=sys.stderr)
    print(f"  Total tasks: {manifest['statistics']['total_tasks']}", file=sys.stderr)
    print(f"  Categories: {manifest['statistics']['categories']}", file=sys.stderr)
    print(f"  Written to: {output_file}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
