#!/usr/bin/env python3
"""Fix Dockerfile workspace permissions for Daytona compatibility.

Problem: Dockerfiles with `USER claude` + `WORKDIR /workspace` + `RUN git clone`
fail on Daytona's remote builder because WORKDIR creates /workspace as root,
so claude can't write to it. Local Docker BuildKit handles this differently.

Fix: Insert `RUN mkdir -p /workspace && chown claude:claude /workspace`
before the `USER claude` line in affected Dockerfiles.

Usage:
    python3 scripts/fix_workspace_perms.py --dry-run   # preview
    python3 scripts/fix_workspace_perms.py --execute    # apply
"""

import re
import sys
from pathlib import Path

BENCHMARKS = Path("benchmarks")


def needs_fix(content: str) -> bool:
    """Check if Dockerfile needs the workspace chown fix."""
    has_user_claude = "USER claude" in content
    has_workdir = "WORKDIR /workspace" in content
    has_chown = bool(re.search(r"chown.*claude.*(/workspace|workspace)", content))
    return has_user_claude and has_workdir and not has_chown


def fix_dockerfile(content: str) -> str:
    """Insert chown line before the first USER claude line."""
    lines = content.splitlines(keepends=True)
    result = []
    fixed = False
    for line in lines:
        if not fixed and line.strip() == "USER claude":
            # Insert the fix before USER claude
            result.append(
                "RUN mkdir -p /workspace && chown claude:claude /workspace\n"
            )
            result.append("\n")
            fixed = True
        result.append(line)
    return "".join(result)


def main():
    dry_run = "--dry-run" in sys.argv
    execute = "--execute" in sys.argv

    if not dry_run and not execute:
        print("Usage: --dry-run or --execute")
        sys.exit(1)

    dockerfiles = sorted(BENCHMARKS.glob("*/*/environment/Dockerfile"))
    needs_fix_files = []

    for df in dockerfiles:
        content = df.read_text()
        if needs_fix(content):
            needs_fix_files.append(df)

    print(f"Found {len(needs_fix_files)} Dockerfiles needing fix")

    # Group by suite
    suites: dict[str, list[Path]] = {}
    for df in needs_fix_files:
        suite = df.parts[1]  # benchmarks/<suite>/...
        suites.setdefault(suite, []).append(df)

    for suite, files in sorted(suites.items()):
        print(f"  {suite}: {len(files)} files")

    if dry_run:
        print("\nDry run — no files modified. Use --execute to apply.")
        return

    # Apply fixes
    fixed_count = 0
    for df in needs_fix_files:
        content = df.read_text()
        new_content = fix_dockerfile(content)
        if new_content != content:
            df.write_text(new_content)
            fixed_count += 1

    print(f"\nFixed {fixed_count} Dockerfiles")


if __name__ == "__main__":
    main()
