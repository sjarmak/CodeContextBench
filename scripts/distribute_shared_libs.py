#!/usr/bin/env python3
"""Distribute shared verifier libraries to all task tests/ directories.

Copies canonical versions from benchmarks/shared/ into each task's tests/ dir.
Ensures all tasks have the same version of shared libraries.

Usage:
    python3 scripts/distribute_shared_libs.py --dry-run    # preview
    python3 scripts/distribute_shared_libs.py --execute     # copy files
    python3 scripts/distribute_shared_libs.py --check       # verify consistency
"""

import argparse
import glob
import hashlib
import os
import shutil
import sys

SHARED_DIR = "benchmarks/shared"
TASKS_DIR = "benchmarks/csb"

# Libraries to distribute (source name → target name)
SHARED_LIBS = {
    "verifier_harness.sh": "verifier_harness.sh",
}


def sha256(path: str) -> str:
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def find_task_test_dirs() -> list[str]:
    """Find all task tests/ directories."""
    dirs = []
    for gt in sorted(glob.glob(os.path.join(TASKS_DIR, "*/*/tests"))):
        if os.path.isdir(gt):
            dirs.append(gt)
    return dirs


def main():
    parser = argparse.ArgumentParser(description="Distribute shared verifier libs")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--check", action="store_true", help="Check consistency only")
    args = parser.parse_args()

    if not any([args.dry_run, args.execute, args.check]):
        parser.print_help()
        return

    test_dirs = find_task_test_dirs()
    print(f"Found {len(test_dirs)} task test directories")

    for lib_src, lib_dst in SHARED_LIBS.items():
        src_path = os.path.join(SHARED_DIR, lib_src)
        if not os.path.exists(src_path):
            print(f"ERROR: Source {src_path} not found")
            sys.exit(1)

        src_hash = sha256(src_path)
        copied = 0
        up_to_date = 0
        missing = 0

        for test_dir in test_dirs:
            dst_path = os.path.join(test_dir, lib_dst)
            task_name = "/".join(test_dir.split("/")[-3:-1])

            if os.path.exists(dst_path):
                dst_hash = sha256(dst_path)
                if dst_hash == src_hash:
                    up_to_date += 1
                    continue
                else:
                    if args.check:
                        print(f"  STALE: {task_name}/{lib_dst}")
                    elif args.dry_run:
                        print(f"  UPDATE: {task_name}/{lib_dst}")
                    elif args.execute:
                        shutil.copy2(src_path, dst_path)
                        copied += 1
            else:
                missing += 1
                if args.check:
                    print(f"  MISSING: {task_name}/{lib_dst}")
                elif args.dry_run:
                    print(f"  COPY: {task_name}/{lib_dst}")
                elif args.execute:
                    shutil.copy2(src_path, dst_path)
                    copied += 1

        print(f"\n{lib_dst}: {up_to_date} up-to-date, {copied} copied, {missing} missing")

    if args.check and missing > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
