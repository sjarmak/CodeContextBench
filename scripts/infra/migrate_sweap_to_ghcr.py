#!/usr/bin/env python3
"""Migrate SWEAP images from jefzda/sweap-images to ghcr.io/sg-evals/sweap-images.

Two modes:
  --push    Pull from jefzda, retag, push to GHCR, clean up (requires docker login to ghcr.io)
  --update  Update Dockerfile FROM lines to use ghcr.io (no Docker required)
  --dry-run Show what would be done without making changes

Usage:
  # First, push images (requires GHCR write access):
  docker login ghcr.io -u USERNAME -p TOKEN
  python3 scripts/migrate_sweap_to_ghcr.py --push

  # Then, update Dockerfiles:
  python3 scripts/migrate_sweap_to_ghcr.py --update

  # Or do both:
  python3 scripts/migrate_sweap_to_ghcr.py --push --update
"""

import argparse
import glob
import os
import re
import subprocess
import sys

SRC_REGISTRY = "jefzda/sweap-images"
DST_REGISTRY = "ghcr.io/sg-evals/sweap-images"

def find_sweap_references():
    """Find all Dockerfiles referencing jefzda/sweap-images and extract tags."""
    tag_to_files = {}
    for f in sorted(glob.glob("benchmarks/csb_*/*/environment/Dockerfile*")):
        with open(f) as fh:
            for line in fh:
                m = re.match(r"FROM\s+(jefzda/sweap-images:(\S+))", line)
                if m:
                    full_ref = m.group(1)
                    tag = m.group(2)
                    tag_to_files.setdefault(tag, []).append(f)
    return tag_to_files


def push_images(tag_to_files, dry_run=False):
    """Pull from jefzda, retag to GHCR, push, clean up. One at a time (disk-safe)."""
    tags = sorted(tag_to_files.keys())
    print(f"Migrating {len(tags)} images to {DST_REGISTRY}...\n")

    failed = []
    for i, tag in enumerate(tags, 1):
        src = f"{SRC_REGISTRY}:{tag}"
        dst = f"{DST_REGISTRY}:{tag}"
        print(f"[{i}/{len(tags)}] {tag[:60]}...")

        if dry_run:
            print(f"  DRY RUN: would pull {src}, tag as {dst}, push, clean\n")
            continue

        try:
            subprocess.run(["docker", "pull", src], check=True, capture_output=True, text=True)
            subprocess.run(["docker", "tag", src, dst], check=True, capture_output=True, text=True)
            subprocess.run(["docker", "push", dst], check=True, capture_output=True, text=True)
            # Clean up both to save disk
            subprocess.run(["docker", "rmi", src, dst], capture_output=True, text=True)
            print(f"  OK\n")
        except subprocess.CalledProcessError as e:
            print(f"  FAILED: {e.stderr.strip()}\n")
            failed.append(tag)

    if failed:
        print(f"\n{len(failed)} images failed to migrate:")
        for t in failed:
            print(f"  {t}")
        return False
    return True


def update_dockerfiles(tag_to_files, dry_run=False):
    """Replace jefzda/sweap-images with ghcr.io/sg-evals/sweap-images in all Dockerfiles."""
    total_files = 0
    for tag, files in sorted(tag_to_files.items()):
        for f in files:
            with open(f) as fh:
                content = fh.read()
            new_content = content.replace(SRC_REGISTRY, DST_REGISTRY)
            if new_content != content:
                if dry_run:
                    print(f"  DRY RUN: would update {f}")
                else:
                    with open(f, "w") as fh:
                        fh.write(new_content)
                total_files += 1

    action = "Would update" if dry_run else "Updated"
    print(f"\n{action} {total_files} Dockerfiles ({SRC_REGISTRY} → {DST_REGISTRY})")
    return total_files


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--push", action="store_true", help="Pull/retag/push images to GHCR")
    parser.add_argument("--update", action="store_true", help="Update Dockerfile FROM lines")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
    args = parser.parse_args()

    if not args.push and not args.update:
        parser.print_help()
        sys.exit(1)

    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    tag_to_files = find_sweap_references()

    if not tag_to_files:
        print("No jefzda/sweap-images references found. Migration may already be complete.")
        sys.exit(0)

    print(f"Found {len(tag_to_files)} unique tags across {sum(len(v) for v in tag_to_files.values())} Dockerfiles\n")

    if args.push:
        ok = push_images(tag_to_files, dry_run=args.dry_run)
        if not ok and not args.dry_run:
            print("\nSome pushes failed. Fix and rerun with --push before --update.")
            sys.exit(1)

    if args.update:
        update_dockerfiles(tag_to_files, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
