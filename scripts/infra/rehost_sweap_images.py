#!/usr/bin/env python3
"""Re-host jefzda/sweap-images from Docker Hub to GHCR for Daytona compatibility.

Daytona's remote builder cannot pull from Docker Hub (auth error on public images).
This script re-hosts all sweap-images used by benchmark tasks to ghcr.io/sg-evals/sweap-images.

Usage:
    python3 scripts/rehost_sweap_images.py --dry-run     # list what would be done
    python3 scripts/rehost_sweap_images.py --pull-push   # pull+tag+push to GHCR
    python3 scripts/rehost_sweap_images.py --update-dockerfiles  # update FROM lines
    python3 scripts/rehost_sweap_images.py --all         # do everything
    python3 scripts/rehost_sweap_images.py --dry-run --task-id webclients-excessive-repeated-api-fix-001
    python3 scripts/rehost_sweap_images.py --pull-push --tag protonmail.webclients-...
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

SOURCE_REGISTRY = "jefzda/sweap-images"
TARGET_REGISTRY = "ghcr.io/sg-evals/sweap-images"

BENCHMARKS = Path("benchmarks")


def find_sweap_references(
    include_task_ids: set[str] | None = None,
    include_tags: set[str] | None = None,
) -> dict[str, list[Path]]:
    """Find all Dockerfiles referencing sweap-images, grouped by tag."""
    tags: dict[str, list[Path]] = {}
    for df in sorted(BENCHMARKS.glob("*/*/environment/Dockerfile*")):
        if include_task_ids is not None and df.parts[2] not in include_task_ids:
            continue
        content = df.read_text()
        for m in re.finditer(r"FROM jefzda/sweap-images:(\S+)", content):
            tag = m.group(1)
            if include_tags is not None and tag not in include_tags:
                continue
            tags.setdefault(tag, []).append(df)
    return tags


def pull_and_push(tags: dict[str, list[Path]]) -> list[str]:
    """Pull from Docker Hub, tag for GHCR, push to GHCR."""
    failed = []
    for i, tag in enumerate(sorted(tags.keys()), 1):
        source = f"{SOURCE_REGISTRY}:{tag}"
        target = f"{TARGET_REGISTRY}:{tag}"
        print(f"[{i}/{len(tags)}] {tag}")

        # Pull
        r = subprocess.run(["docker", "pull", source], capture_output=True, text=True)
        if r.returncode != 0:
            print(f"  PULL FAILED: {r.stderr.strip()}")
            failed.append(tag)
            continue
        print(f"  Pulled {source}")

        # Tag
        subprocess.run(["docker", "tag", source, target], check=True)
        print(f"  Tagged -> {target}")

        # Push
        r = subprocess.run(["docker", "push", target], capture_output=True, text=True)
        if r.returncode != 0:
            print(f"  PUSH FAILED: {r.stderr.strip()}")
            failed.append(tag)
            continue
        print(f"  Pushed {target}")

    return failed


def update_dockerfiles(tags: dict[str, list[Path]]) -> int:
    """Update FROM lines in all affected Dockerfiles."""
    count = 0
    for tag, files in sorted(tags.items()):
        old = f"FROM {SOURCE_REGISTRY}:{tag}"
        new = f"FROM {TARGET_REGISTRY}:{tag}"
        for df in files:
            content = df.read_text()
            if old in content:
                df.write_text(content.replace(old, new))
                count += 1
    return count


def main():
    parser = argparse.ArgumentParser(description="Re-host sweap images to GHCR")
    parser.add_argument("--dry-run", action="store_true", help="List discovered tags/files")
    parser.add_argument("--pull-push", action="store_true", help="Pull from source + push to GHCR")
    parser.add_argument("--update-dockerfiles", action="store_true", help="Update FROM lines to GHCR")
    parser.add_argument("--all", action="store_true", help="Run pull/push + update dockerfiles")
    parser.add_argument(
        "--task-id",
        action="append",
        default=[],
        help="Restrict to a specific benchmark task id (repeatable)",
    )
    parser.add_argument(
        "--tag",
        action="append",
        default=[],
        help="Restrict to an exact sweap image tag (repeatable)",
    )
    args = parser.parse_args()

    dry_run = args.dry_run
    pull_push = args.pull_push
    update = args.update_dockerfiles
    do_all = args.all

    if not any([dry_run, pull_push, update, do_all]):
        print("Usage: --dry-run | --pull-push | --update-dockerfiles | --all")
        sys.exit(1)

    include_task_ids = set(args.task_id) if args.task_id else None
    include_tags = set(args.tag) if args.tag else None
    tags = find_sweap_references(include_task_ids=include_task_ids, include_tags=include_tags)
    if not tags:
        print("No sweap image references matched the requested filters.")
        return

    total_files = sum(len(f) for f in tags.values())
    print(f"Found {len(tags)} unique sweap-images tags across {total_files} Dockerfiles\n")

    if dry_run:
        for tag, files in sorted(tags.items()):
            print(f"  {SOURCE_REGISTRY}:{tag}")
            print(f"    -> {TARGET_REGISTRY}:{tag}")
            for f in files:
                print(f"       {f}")
        return

    if pull_push or do_all:
        print("=== Pull + Push to GHCR ===")
        failed = pull_and_push(tags)
        if failed:
            print(f"\nFailed tags: {failed}")
        else:
            print(f"\nAll {len(tags)} images re-hosted successfully")

    if update or do_all:
        print("\n=== Updating Dockerfiles ===")
        count = update_dockerfiles(tags)
        print(f"Updated {count} Dockerfiles")


if __name__ == "__main__":
    main()
