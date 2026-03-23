#!/usr/bin/env python3
"""Verify snapshot integrity: check symlinks, summaries, and suite coverage.

Usage:
    python3 scripts/publishing/verify_snapshot.py runs/snapshots/csb-v1-mixed371--haiku45--030326
    python3 scripts/publishing/verify_snapshot.py --all
"""
import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SNAPSHOTS_DIR = REPO_ROOT / "runs" / "snapshots"


def verify_snapshot(snap_dir: Path) -> tuple[int, int]:
    """Verify one snapshot. Returns (errors, warnings)."""
    errors = 0
    warnings = 0

    manifest_path = snap_dir / "SNAPSHOT.json"
    if not manifest_path.exists():
        print(f"  ERROR: Missing SNAPSHOT.json")
        return 1, 0

    manifest = json.load(open(manifest_path))
    snap_id = manifest.get("snapshot_id", snap_dir.name)
    print(f"Verifying: {snap_id}")

    # Check required fields
    for field in ["snapshot_id", "suite_id", "model", "configs", "task_count"]:
        if field not in manifest:
            print(f"  ERROR: Missing field '{field}' in SNAPSHOT.json")
            errors += 1

    # Check traces directory
    traces_dir = snap_dir / "traces"
    if not traces_dir.is_dir():
        print(f"  ERROR: Missing traces/ directory")
        errors += 1
    else:
        for config in manifest.get("configs", []):
            config_dir = traces_dir / config
            if not config_dir.is_dir():
                print(f"  WARNING: Missing traces/{config}/ directory")
                warnings += 1
                continue

            # Check symlinks
            total = 0
            broken = 0
            for link in sorted(config_dir.iterdir()):
                total += 1
                if link.is_symlink() and not link.resolve().exists():
                    broken += 1
                    if broken <= 3:
                        print(f"  ERROR: Broken symlink: traces/{config}/{link.name}")
                    errors += 1

            print(f"  traces/{config}/: {total} tasks, {broken} broken symlinks")

    # Check summary files
    summary_dir = snap_dir / "summary"
    for fname in ["rewards.json", "aggregate.json"]:
        fpath = summary_dir / fname
        if not fpath.exists():
            print(f"  WARNING: Missing summary/{fname}")
            warnings += 1

    # Check browse.html
    if not (snap_dir / "browse.html").exists():
        print(f"  WARNING: Missing browse.html")
        warnings += 1

    return errors, warnings


def main():
    parser = argparse.ArgumentParser(description="Verify snapshot integrity")
    parser.add_argument("snapshot", nargs="?", help="Path to snapshot directory")
    parser.add_argument("--all", action="store_true", help="Verify all snapshots")
    args = parser.parse_args()

    if args.all:
        snap_dirs = sorted(d for d in SNAPSHOTS_DIR.iterdir() if d.is_dir())
    elif args.snapshot:
        snap_dirs = [Path(args.snapshot)]
    else:
        parser.error("Provide a snapshot path or --all")

    total_errors = 0
    total_warnings = 0
    for snap_dir in snap_dirs:
        e, w = verify_snapshot(snap_dir)
        total_errors += e
        total_warnings += w
        print()

    print(f"Total: {len(snap_dirs)} snapshots, {total_errors} errors, {total_warnings} warnings")
    sys.exit(1 if total_errors > 0 else 0)


if __name__ == "__main__":
    main()
