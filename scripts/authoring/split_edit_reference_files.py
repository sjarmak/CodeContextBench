#!/usr/bin/env python3
"""Split ground truth 'files' into 'edit_files' and 'reference_files'.

For tasks that already have 'expected_edit_files', computes:
  reference_files = files - expected_edit_files

For tasks with only 'files', reports them as needing manual classification.

Schema extension:
  edit_files      — Files the agent should create or modify (implementation targets)
  reference_files — Files the agent should read for context (IR recall targets)

The original 'files' field is preserved for backward compatibility.

Usage:
    python3 scripts/split_edit_reference_files.py --dry-run    # preview
    python3 scripts/split_edit_reference_files.py --execute     # update files
    python3 scripts/split_edit_reference_files.py --stats       # distribution stats
"""

import argparse
import glob
import json
import os
import sys


def normalize_path(path: str) -> str:
    """Normalize path for comparison (strip repo:: prefix)."""
    if "::" in path:
        return path.split("::", 1)[1]
    return path


def split_files(gt: dict) -> dict | None:
    """Compute reference_files from files and expected_edit_files.

    Returns updated GT dict, or None if no split possible.
    """
    files = gt.get("files", [])
    edit_files = gt.get("expected_edit_files", [])

    if not files or not edit_files:
        return None

    # Already has reference_files
    if "reference_files" in gt:
        return None

    # Normalize edit_files for comparison
    edit_normalized = {normalize_path(e) for e in edit_files}

    reference = []
    for f in files:
        f_normalized = normalize_path(f)
        if f_normalized not in edit_normalized:
            reference.append(f)

    gt["reference_files"] = reference
    return gt


def main():
    parser = argparse.ArgumentParser(description="Split edit/reference files in GT")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--stats", action="store_true")
    parser.add_argument("--tasks-dir", default="benchmarks/csb")
    args = parser.parse_args()

    gt_files = sorted(glob.glob(os.path.join(args.tasks_dir, "*/*/tests/ground_truth.json")))
    print(f"Scanning {len(gt_files)} ground_truth.json files...")

    splittable = []
    already_split = []
    needs_manual = []
    no_files = []

    for gt_path in gt_files:
        task_name = "/".join(gt_path.split("/")[-4:-2])
        with open(gt_path) as f:
            gt = json.load(f)

        files = gt.get("files", [])
        edit_files = gt.get("expected_edit_files", [])
        has_reference = "reference_files" in gt

        if has_reference:
            already_split.append(task_name)
        elif files and edit_files:
            splittable.append((task_name, gt_path, gt))
        elif files:
            needs_manual.append((task_name, len(files)))
        else:
            no_files.append(task_name)

    if args.stats:
        print(f"\nAlready split: {len(already_split)}")
        print(f"Splittable (have both files + expected_edit_files): {len(splittable)}")
        print(f"Needs manual classification (files only): {len(needs_manual)}")
        print(f"No files field: {len(no_files)}")
        print(f"\nSplittable tasks:")
        for name, path, gt in splittable:
            files = gt.get("files", [])
            edits = gt.get("expected_edit_files", [])
            ref_count = len(files) - len(set(normalize_path(e) for e in edits) & set(normalize_path(f) for f in files))
            print(f"  {name}: {len(files)} files, {len(edits)} edit, ~{ref_count} reference")
        return

    updated = 0
    for name, path, gt in splittable:
        result = split_files(gt)
        if result is None:
            continue

        ref = result["reference_files"]
        edit = result["expected_edit_files"]

        if args.dry_run:
            print(f"WOULD SPLIT: {name} → {len(edit)} edit, {len(ref)} reference")
        elif args.execute:
            with open(path, "w") as f:
                json.dump(result, f, indent=2)
                f.write("\n")
            print(f"SPLIT: {name} → {len(edit)} edit, {len(ref)} reference")
            updated += 1

    print(f"\nTotal: {updated} updated, {len(already_split)} already split, "
          f"{len(needs_manual)} need manual classification")


if __name__ == "__main__":
    main()
