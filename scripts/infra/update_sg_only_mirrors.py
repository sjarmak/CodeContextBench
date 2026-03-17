#!/usr/bin/env python3
"""Update Dockerfile.sg_only files to use sg-evals mirrors instead of github.com/ repos.

Reads the mirror_creation_manifest.json to build a task→repo→mirror mapping,
then rewrites SOURCEGRAPH_REPO_NAME and SOURCEGRAPH_REPOS env vars in each
Dockerfile.sg_only to point to the pinned sg-evals mirrors.

Usage:
    python3 scripts/update_sg_only_mirrors.py [--dry-run] [--verbose]
"""

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = REPO_ROOT / "configs" / "mirror_creation_manifest.json"
BENCHMARKS_DIR = REPO_ROOT / "benchmarks"


def build_task_mapping(manifest: dict) -> dict[str, dict[str, str]]:
    """Build task_id → {github_repo → sg-evals/mirror} mapping.

    Returns e.g. {"ccb_fix/django-select-for-update-fix-001":
                   {"github.com/django/django": "sg-evals/django--674eda1c"}}
    """
    task_map: dict[str, dict[str, str]] = {}
    for entry in manifest["mirrors"]:
        upstream = entry["upstream"]      # e.g. "github.com/django/django"
        mirror = entry["mirror"]          # e.g. "sg-evals/django--674eda1c"
        for task_id in entry["tasks"]:
            if task_id not in task_map:
                task_map[task_id] = {}
            task_map[task_id][upstream] = mirror
    return task_map


def update_dockerfile(task_dir: Path, repo_replacements: dict[str, str],
                      dry_run: bool, verbose: bool) -> str:
    """Update the SOURCEGRAPH_* env vars in Dockerfile.sg_only.

    Returns "updated", "unchanged", or "error:<msg>".
    """
    sg_only = task_dir / "environment" / "Dockerfile.sg_only"
    if not sg_only.exists():
        return "error:no Dockerfile.sg_only"

    original = sg_only.read_text()
    text = original

    # Handle SOURCEGRAPH_REPOS (multi-repo, comma-separated)
    m_repos = re.search(r'(ENV\s+SOURCEGRAPH_REPOS[= ])"?([^"\n]+)"?', text)
    if m_repos:
        prefix = m_repos.group(1)
        repos_str = m_repos.group(2).strip()
        repos = [r.strip() for r in repos_str.split(",") if r.strip()]

        new_repos = []
        for repo in repos:
            # Normalize to full github.com/ form for lookup
            normalized = repo
            if not normalized.startswith("github.com/") and not normalized.startswith("sg-evals/"):
                normalized = f"github.com/{repo}"

            if normalized in repo_replacements:
                new_repos.append(repo_replacements[normalized])
            else:
                # Already pinned or not in manifest
                new_repos.append(repo)

        new_repos_str = ",".join(new_repos)
        new_line = f'{prefix}"{new_repos_str}"'
        text = text[:m_repos.start()] + new_line + text[m_repos.end():]

    # Handle SOURCEGRAPH_REPO_NAME (single-repo)
    m_name = re.search(r'(ENV\s+SOURCEGRAPH_REPO_NAME[= ])"?([^"\n]+)"?', text)
    if m_name:
        prefix = m_name.group(1)
        repo = m_name.group(2).strip()

        normalized = repo
        if not normalized.startswith("github.com/") and not normalized.startswith("sg-evals/"):
            normalized = f"github.com/{repo}"

        if normalized in repo_replacements:
            new_repo = repo_replacements[normalized]
            new_line = f'{prefix}"{new_repo}"'
            text = text[:m_name.start()] + new_line + text[m_name.end():]

    if text == original:
        return "unchanged"

    if verbose:
        task_id = f"{task_dir.parent.name}/{task_dir.name}"
        print(f"  {task_id}: updating {len(repo_replacements)} repo(s)")
        for old, new in repo_replacements.items():
            print(f"    {old} → {new}")

    if not dry_run:
        sg_only.write_text(text)

    return "updated"


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Update Dockerfile.sg_only files to use sg-evals mirrors")
    parser.add_argument("--dry-run", action="store_true", help="Show what would change without writing")
    parser.add_argument("--verbose", action="store_true", help="Show per-task details")
    args = parser.parse_args()

    manifest = json.loads(MANIFEST_PATH.read_text())
    task_map = build_task_mapping(manifest)

    mode = "DRY RUN" if args.dry_run else "UPDATING"
    print(f"=== {mode}: Dockerfile.sg_only mirror references ===\n")
    print(f"Manifest: {len(manifest['mirrors'])} mirrors, {len(task_map)} tasks to update\n")

    updated = 0
    unchanged = 0
    errors = []

    for task_id, replacements in sorted(task_map.items()):
        # Parse suite/task from task_id
        parts = task_id.split("/")
        if len(parts) != 2:
            errors.append((task_id, f"unexpected task_id format: {task_id}"))
            continue

        task_dir = BENCHMARKS_DIR / parts[0] / parts[1]
        if not task_dir.exists():
            errors.append((task_id, f"task directory not found: {task_dir}"))
            continue

        result = update_dockerfile(task_dir, replacements, args.dry_run, args.verbose)
        if result == "updated":
            updated += 1
        elif result == "unchanged":
            unchanged += 1
        elif result.startswith("error:"):
            errors.append((task_id, result[6:]))
            print(f"  ERROR: {task_id}: {result[6:]}", file=sys.stderr)

    verb = "Would update" if args.dry_run else "Updated"
    print(f"\n{verb} {updated} Dockerfile.sg_only files ({unchanged} unchanged, {len(errors)} errors)")

    if errors:
        print("\nErrors:", file=sys.stderr)
        for task_id, msg in errors:
            print(f"  {task_id}: {msg}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
