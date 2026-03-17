#!/usr/bin/env python3
"""Assign oracle confidence tiers to ground_truth_meta.json files.

Tiers:
  high   — Human-verified, git-diff-derived, or converted from known schema
           with >=5 file/symbol items
  medium — Curator-generated with >=3 file/symbol items, or has rich
           alternative GT structure (required_findings, scoring_categories, etc.)
  low    — Single keyword/narrow scope (<=2 items), or missing ground truth

Updates ground_truth_meta.json in-place. Prints summary of changes.

Usage:
    python3 scripts/assign_oracle_confidence.py --dry-run    # preview
    python3 scripts/assign_oracle_confidence.py --execute     # update files
    python3 scripts/assign_oracle_confidence.py --json        # machine-readable
"""

import argparse
import glob
import json
import os
import sys


# Keys that indicate rich GT even without files/symbols
RICH_GT_KEYS = {
    "required_findings", "scoring_categories", "required_topics",
    "causal_chain", "data_flow", "extension_points", "steps",
    "expected_keywords", "expected_files",
    "old_symbol", "new_symbol", "expected_refs",
    "entries", "key_fields",
}


def count_gt_items(gt: dict) -> int:
    """Count the number of file/symbol items in ground truth."""
    files = gt.get("files", [])
    symbols = gt.get("symbols", [])
    buggy = gt.get("buggy_files", [])
    edit_files = gt.get("expected_edit_files", [])
    return len(files) + len(symbols) + len(buggy) + len(edit_files)


def has_rich_structure(gt: dict) -> bool:
    """Check if GT has rich alternative structure beyond files/symbols."""
    return bool(RICH_GT_KEYS & set(gt.keys()))


def assign_tier(gt: dict, meta: dict) -> str:
    """Assign confidence tier based on GT content and metadata."""
    source = meta.get("ground_truth_source", "unknown")
    items = count_gt_items(gt)
    rich = has_rich_structure(gt)

    # High confidence: human-verified or schema-converted with substantial items
    if source in ("manual_from_canonical", "converted_from_function_id_schema"):
        return "high"
    if source == "curator_agent" and items >= 5:
        return "high" if items >= 10 else "medium"

    # Medium: curator with decent coverage, or rich checklist GT
    if source == "curator_agent" and items >= 3:
        return "medium"
    if rich and items >= 1:
        return "medium"
    if rich and not items:
        # Checklist-only GT (document, feature, refactor tasks) — medium if structured
        # Count total non-empty GT-relevant fields
        total_checklist = 0
        for key in RICH_GT_KEYS:
            val = gt.get(key)
            if val:
                total_checklist += len(val) if isinstance(val, (list, dict)) else 1
        if total_checklist >= 3:
            return "medium"

    # Low: narrow scope
    if items <= 2 and not rich:
        return "low"
    if items == 0:
        return "low"

    return "medium"


def main():
    parser = argparse.ArgumentParser(description="Assign oracle confidence tiers")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--json", action="store_true", dest="json_output")
    parser.add_argument("--tasks-dir", default="benchmarks/csb")
    args = parser.parse_args()

    results = {"high": [], "medium": [], "low": [], "no_meta": []}
    changes = 0

    for gt_path in sorted(glob.glob(os.path.join(args.tasks_dir, "*/*/tests/ground_truth.json"))):
        task_dir = os.path.dirname(gt_path)
        task_name = "/".join(gt_path.split("/")[-4:-2])
        meta_path = os.path.join(task_dir, "ground_truth_meta.json")

        with open(gt_path) as f:
            gt = json.load(f)

        if not os.path.exists(meta_path):
            results["no_meta"].append(task_name)
            continue

        with open(meta_path) as f:
            meta = json.load(f)

        tier = assign_tier(gt, meta)
        old_tier = meta.get("ground_truth_confidence", "unset")
        items = count_gt_items(gt)

        results[tier].append({"task": task_name, "items": items, "old": old_tier})

        if old_tier != tier:
            changes += 1
            if args.execute:
                meta["ground_truth_confidence"] = tier
                with open(meta_path, "w") as f:
                    json.dump(meta, f, indent=2)
                    f.write("\n")

    if args.json_output:
        summary = {k: len(v) for k, v in results.items()}
        summary["changes"] = changes
        json.dump({"summary": summary, "tiers": results}, sys.stdout, indent=2)
    else:
        for tier in ["high", "medium", "low"]:
            tasks = results[tier]
            print(f"\n{tier.upper()} ({len(tasks)} tasks):")
            if tier == "low":
                for t in tasks:
                    print(f"  {t['task']} (items={t['items']})")
            elif tier == "high" and len(tasks) <= 20:
                for t in tasks:
                    print(f"  {t['task']} (items={t['items']})")
        if results["no_meta"]:
            print(f"\nNO META ({len(results['no_meta'])} tasks):")
            for t in results["no_meta"]:
                print(f"  {t}")

        print(f"\nSummary: {len(results['high'])} high, {len(results['medium'])} medium, "
              f"{len(results['low'])} low, {len(results['no_meta'])} no_meta")
        print(f"Changes needed: {changes}")
        if not args.execute and changes > 0:
            print("Run with --execute to apply changes")


if __name__ == "__main__":
    main()
