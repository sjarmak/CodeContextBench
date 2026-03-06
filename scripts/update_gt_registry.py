#!/usr/bin/env python3
"""Update configs/ground_truth_files.json from GT files in benchmarks/.

Scans all benchmark suites, finds GT files, and writes a registry mapping
task_id to GT file paths. Manual GT takes precedence over curator-generated.

Usage:
    python3 scripts/update_gt_registry.py
    python3 scripts/update_gt_registry.py --dry-run
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BENCHMARKS_DIR = REPO_ROOT / "benchmarks"
REGISTRY_PATH = REPO_ROOT / "configs" / "ground_truth_files.json"

# GT file names in priority order
MANUAL_GT = [
    ("ground_truth.json", "ground_truth_json_files"),
    ("oracle_answer.json", "oracle_answer_json"),
]
CURATOR_GT = [
    ("ground_truth_agent.json", "curator_agent"),
]
ALL_GT = MANUAL_GT + CURATOR_GT


def extract_files(gt_path: Path) -> list[str]:
    """Extract file paths from a GT file."""
    data = json.loads(gt_path.read_text())
    if not isinstance(data, dict):
        return []

    raw = data.get("files", [])
    if not isinstance(raw, list):
        return []

    result = []
    for entry in raw:
        if isinstance(entry, str):
            result.append(entry)
        elif isinstance(entry, dict):
            path = entry.get("path", "")
            if path:
                result.append(path)
    return result


def scan_gt_files() -> dict[str, dict]:
    """Scan benchmarks/ and build registry entries."""
    entries = {}

    for suite_dir in sorted(BENCHMARKS_DIR.iterdir()):
        if not suite_dir.is_dir() or not suite_dir.name.startswith(("csb_", "ccb_")):
            continue

        for task_dir in sorted(suite_dir.iterdir()):
            if not task_dir.is_dir():
                continue

            tests_dir = task_dir / "tests"
            if not tests_dir.is_dir():
                continue

            task_id = task_dir.name
            suite = suite_dir.name

            # Try GT files in priority order (manual first)
            for gt_name, source_label in ALL_GT:
                gt_path = tests_dir / gt_name
                if not gt_path.exists():
                    continue

                files = extract_files(gt_path)
                if not files:
                    continue

                entries[task_id] = {
                    "task_id": task_id,
                    "benchmark": suite,
                    "files": files,
                    "source": source_label,
                    "confidence": "medium",
                }
                break  # Use first valid GT found

    return entries


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Update configs/ground_truth_files.json from GT files"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would change without writing",
    )
    args = parser.parse_args()

    # Load existing registry
    existing = {}
    if REGISTRY_PATH.exists():
        existing = json.loads(REGISTRY_PATH.read_text())

    # Scan for current GT
    new_entries = scan_gt_files()

    # Compute diff
    added = set(new_entries.keys()) - set(existing.keys())
    unchanged = set(new_entries.keys()) & set(existing.keys())
    # We only add, never remove
    merged = dict(existing)
    merged.update(new_entries)

    print(f"Total entries: {len(merged)}")
    print(f"New entries added: {len(added)}")
    print(f"Entries unchanged: {len(unchanged)}")

    if added:
        print(f"\nNew tasks:")
        for tid in sorted(added):
            e = new_entries[tid]
            print(f"  {e['benchmark']}/{tid} ({e['source']}, {len(e['files'])} files)")

    if args.dry_run:
        print("\n[DRY RUN] No files written.")
        return 0

    # Write merged registry (sorted by key for stable diffs)
    sorted_merged = dict(sorted(merged.items()))
    REGISTRY_PATH.write_text(json.dumps(sorted_merged, indent=2) + "\n")
    print(f"\nRegistry written to {REGISTRY_PATH.relative_to(REPO_ROOT)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
