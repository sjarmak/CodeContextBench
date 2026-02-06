#!/usr/bin/env python3
"""Materialize DependEval instances into Git repos for Sourcegraph indexing.

Reads selected instances from configs/dependeval_selected_instances.json,
extracts source code from the DependEval JSON data files, creates proper
file trees, and initializes Git repos with a single commit.

Each repo is named: dependeval-{lang}-{task_type}-{instance_id}
  e.g. dependeval-python-me-a3f2c1b8

Output directory: vendor/dependeval_repos/ (configurable via --output-dir)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_OUTPUT_DIR = Path("vendor/dependeval_repos")
DEFAULT_SELECTION = Path("configs/dependeval_selected_instances.json")
DEFAULT_DATA_DIR = Path("vendor/DependEval/data")

# Data file naming patterns (same as select_dependeval_tasks.py)
ME_FILE_PATTERN = "task1_{lang}.json"
DR_FILE_PATTERN = "task2_{lang}_final.json"

# Regex to match file header lines: 'repo_name/path/to/file.ext'
FILE_HEADER_RE = re.compile(r"^'([^']+/[^']+)'$")


# ---------------------------------------------------------------------------
# Content parsing
# ---------------------------------------------------------------------------

def parse_content_files(content: str) -> dict[str, str]:
    """Parse DependEval content field into a dict of {filepath: code}.

    Content format:
        'repo_name/path/file.ext'
        :first_line_of_code
        rest_of_code...
        'repo_name/path/another_file.ext'
        :first_line_of_that_file
        ...

    Returns a dict mapping file paths (without repo prefix) to code strings.
    """
    files: dict[str, str] = {}
    current_path: str | None = None
    current_lines: list[str] = []

    for line in content.splitlines():
        m = FILE_HEADER_RE.match(line.strip())
        if m:
            # Save previous file
            if current_path is not None:
                files[current_path] = "\n".join(current_lines)
            # Start new file — strip the repo_name/ prefix to get relative path
            full_path = m.group(1)
            # Remove repo name (first component before /)
            parts = full_path.split("/", 1)
            current_path = parts[1] if len(parts) > 1 else full_path
            current_lines = []
        elif current_path is not None:
            # Strip leading colon from first code line
            if not current_lines and line.startswith(":"):
                current_lines.append(line[1:])
            else:
                current_lines.append(line)

    # Save last file
    if current_path is not None:
        files[current_path] = "\n".join(current_lines)

    return files


def instance_id_from_content(content: str) -> str:
    """Return first 8 hex chars of SHA-256 of the content string."""
    import hashlib
    return hashlib.sha256(content.encode("utf-8", errors="replace")).hexdigest()[:8]


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def find_instance_in_data(
    data_dir: Path, language: str, task_type: str, target_id: str
) -> dict | None:
    """Find the instance with matching instance_id in the data file."""
    if task_type == "ME":
        filepath = data_dir / language / ME_FILE_PATTERN.format(lang=language)
    else:
        filepath = data_dir / language / DR_FILE_PATTERN.format(lang=language)

    if not filepath.exists():
        print(f"  WARNING: Data file not found: {filepath}", file=sys.stderr)
        return None

    with open(filepath) as f:
        raw = json.load(f)

    for inst in raw:
        content = inst.get("content", "")
        iid = instance_id_from_content(content)
        if iid == target_id:
            return inst

    return None


# ---------------------------------------------------------------------------
# Repo creation
# ---------------------------------------------------------------------------

def create_repo(
    output_dir: Path,
    repo_name: str,
    files: dict[str, str],
    commit_msg: str,
    dry_run: bool = False,
) -> bool:
    """Create a Git repo with the given files and a single commit.

    Returns True on success, False on failure.
    """
    repo_dir = output_dir / repo_name

    if dry_run:
        print(f"  [DRY RUN] Would create: {repo_dir}")
        for fpath in sorted(files.keys()):
            size = len(files[fpath])
            print(f"    {fpath} ({size} chars)")
        return True

    if repo_dir.exists():
        print(f"  SKIP: {repo_dir} already exists")
        return True

    # Create directory and write files
    repo_dir.mkdir(parents=True, exist_ok=True)

    for fpath, code in files.items():
        full_path = repo_dir / fpath
        full_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            full_path.write_text(code, encoding="utf-8")
        except Exception as e:
            print(f"  WARNING: Could not write {full_path}: {e}", file=sys.stderr)
            # Try with replacement encoding
            full_path.write_bytes(code.encode("utf-8", errors="replace"))

    # Initialize Git repo
    try:
        subprocess.run(
            ["git", "init"], cwd=repo_dir, check=True,
            capture_output=True, text=True,
        )
        subprocess.run(
            ["git", "add", "-A"], cwd=repo_dir, check=True,
            capture_output=True, text=True,
        )
        subprocess.run(
            ["git", "commit", "-m", commit_msg],
            cwd=repo_dir, check=True,
            capture_output=True, text=True,
            env={**os.environ, "GIT_AUTHOR_NAME": "DependEval",
                 "GIT_AUTHOR_EMAIL": "dependeval@benchmark",
                 "GIT_COMMITTER_NAME": "DependEval",
                 "GIT_COMMITTER_EMAIL": "dependeval@benchmark"},
        )
    except subprocess.CalledProcessError as e:
        print(f"  ERROR: Git init/commit failed for {repo_dir}: {e.stderr}",
              file=sys.stderr)
        return False

    return True


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Materialize DependEval instances into Git repos.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  %(prog)s                    # Materialize all selected instances
  %(prog)s --dry-run          # Show what would be created
  %(prog)s --output-dir /tmp/repos  # Custom output directory
""",
    )
    parser.add_argument(
        "--selection",
        type=Path,
        default=DEFAULT_SELECTION,
        help=f"Path to selected instances JSON (default: {DEFAULT_SELECTION})",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DEFAULT_DATA_DIR,
        help=f"Path to DependEval data directory (default: {DEFAULT_DATA_DIR})",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory for Git repos (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be created without writing to disk",
    )
    args = parser.parse_args()

    # Load selected instances
    if not args.selection.exists():
        print(f"ERROR: Selection file not found: {args.selection}", file=sys.stderr)
        print("Run scripts/select_dependeval_tasks.py first.", file=sys.stderr)
        sys.exit(1)

    with open(args.selection) as f:
        selected = json.load(f)

    if not args.data_dir.exists():
        print(f"ERROR: Data directory not found: {args.data_dir}", file=sys.stderr)
        sys.exit(1)

    print(f"DependEval Repo Materialization")
    print(f"  Selection: {args.selection} ({len(selected)} instances)")
    print(f"  Data dir:  {args.data_dir}")
    print(f"  Output:    {args.output_dir}")
    print(f"  Dry run:   {args.dry_run}")
    print("=" * 70)

    if not args.dry_run:
        args.output_dir.mkdir(parents=True, exist_ok=True)

    success_count = 0
    fail_count = 0
    skip_count = 0

    for iid, meta in sorted(selected.items()):
        lang = meta["language"]
        task_type = meta["task_type"]
        repo_name_source = meta["repo_name"]
        repo_name = f"dependeval-{lang}-{task_type.lower()}-{iid}"

        print(f"\n[{iid}] {lang}/{task_type} ({repo_name_source})")
        print(f"  -> {repo_name}")

        # Find instance in source data
        inst = find_instance_in_data(args.data_dir, lang, task_type, iid)
        if inst is None:
            print(f"  ERROR: Instance {iid} not found in {lang}/{task_type} data",
                  file=sys.stderr)
            fail_count += 1
            continue

        # Parse content into files
        content = inst.get("content", "")
        files = parse_content_files(content)

        if not files:
            print(f"  WARNING: No files extracted from content (length={len(content)})",
                  file=sys.stderr)
            fail_count += 1
            continue

        print(f"  Extracted {len(files)} files")

        # Create repo
        commit_msg = (
            f"DependEval {task_type} instance: {repo_name_source}\n\n"
            f"Language: {lang}\n"
            f"Task type: {task_type}\n"
            f"Instance ID: {iid}\n"
            f"Source: DependEval dataset (https://github.com/ink7-sudo/DependEval)"
        )

        ok = create_repo(args.output_dir, repo_name, files, commit_msg, args.dry_run)
        if ok:
            success_count += 1
        else:
            fail_count += 1

    print(f"\n{'=' * 70}")
    print(f"Results: {success_count} created, {fail_count} failed, {skip_count} skipped")
    if fail_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
