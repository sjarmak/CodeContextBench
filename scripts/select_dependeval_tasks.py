#!/usr/bin/env python3
"""Select representative DependEval instances for the CCB benchmark.

Reads DependEval JSON data files from vendor/DependEval/data/ for Python,
JavaScript, TypeScript, and Java. Applies quality/diversity filters, then
selects 4 instances per language per task type (ME and DR) for a total of 32
tasks by default.

Output: configs/dependeval_selected_instances.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from random import Random

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

RANDOM_SEED = 42
LANGUAGES = ["python", "java", "javascript", "typescript"]
INSTANCES_PER_GROUP = 4  # per language per task type

# Content length bounds (chars)
MIN_CONTENT_LENGTH = 2_000
MAX_CONTENT_LENGTH = 20_000

# DR minimum file count
MIN_DR_FILES = 3

# Data file naming patterns
ME_FILE_PATTERN = "task1_{lang}.json"
DR_FILE_PATTERN = "task2_{lang}_final.json"


def instance_id(content: str) -> str:
    """Return first 8 hex chars of SHA-256 of the content string."""
    return hashlib.sha256(content.encode("utf-8", errors="replace")).hexdigest()[:8]


def count_files_in_content(content: str) -> int:
    """Count file headers in DependEval content format ('repo/path/file.ext' lines)."""
    count = 0
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("'") and stripped.endswith("'") and "/" in stripped:
            count += 1
    return count


def extract_repo_name(content: str) -> str:
    """Extract repo name from the first file path in content."""
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("'") and stripped.endswith("'") and "/" in stripped:
            # e.g. 'repo_name/path/file.py' -> repo_name
            inner = stripped.strip("'")
            return inner.split("/")[0]
    return "unknown"


def load_me_instances(data_dir: Path, lang: str) -> list[dict]:
    """Load and filter ME (Method Extension) instances for a language."""
    filepath = data_dir / lang / ME_FILE_PATTERN.format(lang=lang)
    if not filepath.exists():
        print(f"WARNING: {filepath} not found, skipping", file=sys.stderr)
        return []

    with open(filepath) as f:
        raw = json.load(f)

    candidates = []
    for inst in raw:
        content = inst.get("content", "")
        clen = len(content)

        # Filter: content length within bounds
        if clen < MIN_CONTENT_LENGTH or clen > MAX_CONTENT_LENGTH:
            continue

        # Filter: non-empty modified_complete_code
        mcc = inst.get("modified_complete_code", {})
        if not mcc or not isinstance(mcc, dict):
            continue

        # Filter: must have a feature description
        fdesc = inst.get("feature_description", "")
        if not fdesc or not fdesc.strip():
            continue

        iid = instance_id(content)
        repo = inst.get("repo", extract_repo_name(content))
        file_count = count_files_in_content(content)

        candidates.append({
            "instance_id": iid,
            "language": lang,
            "task_type": "ME",
            "repo_name": repo,
            "content_length": clen,
            "file_count": file_count,
            "feature_description": fdesc.strip()[:200],
        })

    return candidates


def load_dr_instances(data_dir: Path, lang: str) -> list[dict]:
    """Load and filter DR (Dependency Recognition) instances for a language."""
    filepath = data_dir / lang / DR_FILE_PATTERN.format(lang=lang)
    if not filepath.exists():
        print(f"WARNING: {filepath} not found, skipping", file=sys.stderr)
        return []

    with open(filepath) as f:
        raw = json.load(f)

    candidates = []
    for inst in raw:
        content = inst.get("content", "")
        clen = len(content)

        # Filter: content length within bounds
        if clen < MIN_CONTENT_LENGTH or clen > MAX_CONTENT_LENGTH:
            continue

        # Filter: DR instances must have 3+ files
        files = inst.get("files", [])
        if len(files) < MIN_DR_FILES:
            continue

        # Filter: must have ground truth ordering
        gt = inst.get("gt", [])
        if not gt:
            continue

        iid = instance_id(content)
        repo = extract_repo_name(content)
        file_count = len(files)

        candidates.append({
            "instance_id": iid,
            "language": lang,
            "task_type": "DR",
            "repo_name": repo,
            "content_length": clen,
            "file_count": file_count,
        })

    return candidates


def select_instances(
    candidates: list[dict], n: int, rng: Random
) -> list[dict]:
    """Select n instances from candidates, preferring median content lengths."""
    if len(candidates) <= n:
        return candidates

    # Sort by content length to pick from different size buckets
    sorted_cands = sorted(candidates, key=lambda x: x["content_length"])

    # Stratified sampling: pick evenly spaced from the sorted list
    step = len(sorted_cands) / n
    indices = [int(i * step + step / 2) for i in range(n)]
    # Clamp indices
    indices = [min(i, len(sorted_cands) - 1) for i in indices]

    selected = [sorted_cands[i] for i in indices]

    # Deduplicate by instance_id (unlikely but safe)
    seen = set()
    deduped = []
    for s in selected:
        if s["instance_id"] not in seen:
            seen.add(s["instance_id"])
            deduped.append(s)

    # If dedup reduced count, fill from remaining
    if len(deduped) < n:
        remaining = [c for c in sorted_cands if c["instance_id"] not in seen]
        rng.shuffle(remaining)
        for r in remaining:
            if len(deduped) >= n:
                break
            deduped.append(r)
            seen.add(r["instance_id"])

    return deduped


def main():
    parser = argparse.ArgumentParser(
        description="Select representative DependEval instances for CCB benchmark.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  %(prog)s                          # Select 32 tasks, write to configs/
  %(prog)s --dry-run                # Print summary without writing files
  %(prog)s --instances-per-group 3  # Select 24 tasks (3 per lang per type)
""",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("vendor/DependEval/data"),
        help="Path to DependEval data directory (default: vendor/DependEval/data)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("configs/dependeval_selected_instances.json"),
        help="Output JSON file path (default: configs/dependeval_selected_instances.json)",
    )
    parser.add_argument(
        "--instances-per-group",
        type=int,
        default=INSTANCES_PER_GROUP,
        help=f"Instances per language per task type (default: {INSTANCES_PER_GROUP})",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=RANDOM_SEED,
        help=f"Random seed for reproducibility (default: {RANDOM_SEED})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print summary without writing output file",
    )
    args = parser.parse_args()

    rng = Random(args.seed)

    if not args.data_dir.exists():
        print(f"ERROR: Data directory not found: {args.data_dir}", file=sys.stderr)
        print("Run US-002 first to clone the DependEval dataset.", file=sys.stderr)
        sys.exit(1)

    all_selected: list[dict] = []
    total_candidates = 0

    print(f"DependEval Task Selection (seed={args.seed}, {args.instances_per_group}/group)")
    print("=" * 70)

    for lang in LANGUAGES:
        # ME instances
        me_cands = load_me_instances(args.data_dir, lang)
        me_selected = select_instances(me_cands, args.instances_per_group, rng)
        total_candidates += len(me_cands)

        # DR instances
        dr_cands = load_dr_instances(args.data_dir, lang)
        dr_selected = select_instances(dr_cands, args.instances_per_group, rng)
        total_candidates += len(dr_cands)

        all_selected.extend(me_selected)
        all_selected.extend(dr_selected)

        print(f"\n  {lang}:")
        print(f"    ME: {len(me_cands):3d} candidates -> {len(me_selected)} selected")
        print(f"    DR: {len(dr_cands):3d} candidates -> {len(dr_selected)} selected")

        if me_selected:
            lengths = [s["content_length"] for s in me_selected]
            print(f"        ME content lengths: {min(lengths)}-{max(lengths)} chars")
        if dr_selected:
            lengths = [s["content_length"] for s in dr_selected]
            fcounts = [s["file_count"] for s in dr_selected]
            print(f"        DR content lengths: {min(lengths)}-{max(lengths)} chars, files: {min(fcounts)}-{max(fcounts)}")

    print(f"\n{'=' * 70}")
    print(f"Total: {total_candidates} candidates -> {len(all_selected)} selected")

    # Build output mapping: instance_id -> metadata
    output = {}
    for s in all_selected:
        iid = s["instance_id"]
        output[iid] = {
            "language": s["language"],
            "task_type": s["task_type"],
            "repo_name": s["repo_name"],
            "content_length": s["content_length"],
            "file_count": s["file_count"],
        }

    if args.dry_run:
        print("\n[DRY RUN] Would write to:", args.output)
        print(f"[DRY RUN] {len(output)} instances selected")
        for iid, meta in sorted(output.items(), key=lambda x: (x[1]["language"], x[1]["task_type"])):
            print(f"  {iid}: {meta['language']}/{meta['task_type']} "
                  f"repo={meta['repo_name']} "
                  f"len={meta['content_length']} "
                  f"files={meta['file_count']}")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w") as f:
            json.dump(output, f, indent=2)
        print(f"\nWrote {len(output)} instances to {args.output}")


if __name__ == "__main__":
    main()
