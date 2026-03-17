#!/usr/bin/env python3
"""Scaffold benchmarks/csb/ — unified dual-score benchmark with merged suites.

Copies all 275 tasks from csb_sdlc_* and csb_org_* into benchmarks/csb/{suite}/
with thematic suite merges. Updates task.toml category fields. Does NOT modify
the original benchmark directories.

Suite merge map:
  security(39)  = sdlc_secure + org_security + org_compliance
  debug(26)     = sdlc_debug + org_incident
  fix(19)       = sdlc_fix
  feature(34)   = sdlc_feature + org_org
  refactor(43)  = sdlc_refactor + org_migration
  understand(44)= sdlc_understand + sdlc_design + org_domain + org_onboarding
  document(11)  = sdlc_document
  test(12)      = sdlc_test
  crossrepo(47) = org_crossrepo + org_crossrepo_tracing + org_crossorg + org_platform
"""

import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "benchmarks")
DST = os.path.join(ROOT, "benchmarks", "csb")

# old_suite_suffix -> new_suite
MERGE_MAP = {
    # security
    "csb_sdlc_secure": "security",
    "csb_org_security": "security",
    "csb_org_compliance": "security",
    # debug
    "csb_sdlc_debug": "debug",
    "csb_org_incident": "debug",
    # fix
    "csb_sdlc_fix": "fix",
    # feature
    "csb_sdlc_feature": "feature",
    "csb_org_org": "feature",
    # refactor
    "csb_sdlc_refactor": "refactor",
    "csb_org_migration": "refactor",
    # understand
    "csb_sdlc_understand": "understand",
    "csb_sdlc_design": "understand",
    "csb_org_domain": "understand",
    "csb_org_onboarding": "understand",
    # document
    "csb_sdlc_document": "document",
    # test
    "csb_sdlc_test": "test",
    # crossrepo
    "csb_org_crossrepo": "crossrepo",
    "csb_org_crossrepo_tracing": "crossrepo",
    "csb_org_crossorg": "crossrepo",
    "csb_org_platform": "crossrepo",
}

NEW_SUITES = sorted(set(MERGE_MAP.values()))


def discover_tasks():
    """Find all task directories in csb_sdlc_* and csb_org_* suites."""
    tasks = []
    for suite_dir in sorted(os.listdir(SRC)):
        if suite_dir not in MERGE_MAP:
            continue
        suite_path = os.path.join(SRC, suite_dir)
        if not os.path.isdir(suite_path):
            continue
        for task_name in sorted(os.listdir(suite_path)):
            task_path = os.path.join(suite_path, task_name)
            if not os.path.isdir(task_path):
                continue
            # Skip non-task dirs (e.g. README.md files)
            if not os.path.exists(os.path.join(task_path, "task.toml")):
                continue
            tasks.append((suite_dir, task_name, task_path))
    return tasks


def update_task_toml(toml_path, new_suite, old_suite):
    """Update category/suite references in task.toml to the new suite name."""
    with open(toml_path, "r") as f:
        content = f.read()

    # Replace category references
    # Common patterns: category = "ccb_xxx", category = "csb_sdlc_xxx", etc.
    replacements = [
        (f'category = "{old_suite}"', f'category = "csb_{new_suite}"'),
        (f'category = "ccb_{old_suite.split("_", 1)[-1] if "_" in old_suite else old_suite}"',
         f'category = "csb_{new_suite}"'),
    ]

    # Also handle legacy ccb_ prefixes
    old_suffix = old_suite.replace("csb_sdlc_", "").replace("csb_org_", "")
    for legacy in [f"ccb_{old_suffix}", f"ccb_mcp_{old_suffix}"]:
        replacements.append(
            (f'category = "{legacy}"', f'category = "csb_{new_suite}"')
        )

    for old, new in replacements:
        content = content.replace(old, new)

    # Add origin_suite metadata if not present, for traceability
    if "origin_suite" not in content:
        # Insert after [metadata] or [task] section
        for section in ["[task.metadata]", "[metadata]", "[task]"]:
            if section in content:
                content = content.replace(
                    section,
                    f'{section}\norigin_suite = "{old_suite}"',
                    1,
                )
                break

    with open(toml_path, "w") as f:
        f.write(content)


def main():
    dry_run = "--dry-run" in sys.argv

    tasks = discover_tasks()
    print(f"Discovered {len(tasks)} tasks across {len(MERGE_MAP)} source suites")

    # Verify counts
    suite_counts = {}
    for suite_dir, task_name, _ in tasks:
        new_suite = MERGE_MAP[suite_dir]
        suite_counts[new_suite] = suite_counts.get(new_suite, 0) + 1

    print("\nMerged suite sizes:")
    total = 0
    for suite in NEW_SUITES:
        count = suite_counts.get(suite, 0)
        total += count
        print(f"  csb/{suite:12s} {count:3d} tasks")
    print(f"  {'':12s} {total:3d} total")

    if dry_run:
        print("\n[DRY RUN] Would create directories and copy tasks. Pass without --dry-run to execute.")
        return

    # Check for name collisions across merged suites
    collisions = {}
    for suite_dir, task_name, _ in tasks:
        new_suite = MERGE_MAP[suite_dir]
        key = (new_suite, task_name)
        if key in collisions:
            print(f"ERROR: Task name collision: {task_name} in {new_suite} "
                  f"(from {collisions[key]} and {suite_dir})")
            sys.exit(1)
        collisions[key] = suite_dir

    # Create directory structure
    os.makedirs(DST, exist_ok=True)
    for suite in NEW_SUITES:
        os.makedirs(os.path.join(DST, suite), exist_ok=True)

    # Copy tasks
    copied = 0
    for suite_dir, task_name, src_path in tasks:
        new_suite = MERGE_MAP[suite_dir]
        dst_path = os.path.join(DST, new_suite, task_name)

        if os.path.exists(dst_path):
            print(f"  SKIP (exists): {dst_path}")
            continue

        shutil.copytree(src_path, dst_path)
        update_task_toml(os.path.join(dst_path, "task.toml"), new_suite, suite_dir)
        copied += 1

    print(f"\nCopied {copied} tasks to benchmarks/csb/")

    # Verify
    verify_count = 0
    for suite in NEW_SUITES:
        suite_path = os.path.join(DST, suite)
        for task_name in os.listdir(suite_path):
            if os.path.isdir(os.path.join(suite_path, task_name)):
                verify_count += 1
    print(f"Verification: {verify_count} task directories in benchmarks/csb/")


if __name__ == "__main__":
    main()
