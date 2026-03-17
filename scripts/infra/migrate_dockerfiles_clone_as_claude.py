#!/usr/bin/env python3
"""Migrate baseline Dockerfiles from clone-as-root to clone-as-claude pattern.

Converts Dockerfiles under benchmarks/csb_org_*/*/environment/Dockerfile from
the old pattern (clone repos as root, then chown) to the new pattern (create
claude user first, USER claude, then git clone).

The new pattern avoids a massive chown -R layer that doubles image size and
takes 15-30 min on overlay2 (copy-on-write duplicates every inode).

Reference: benchmarks/csb_org_domain/ccx-domain-071/environment/Dockerfile

Usage:
    # Dry run (default) -- show what would change
    python3 scripts/migrate_dockerfiles_clone_as_claude.py

    # Actually write changes
    python3 scripts/migrate_dockerfiles_clone_as_claude.py --execute
"""

from __future__ import annotations

import argparse
import difflib
import glob
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
REFERENCE_FILE = (
    REPO_ROOT
    / "benchmarks"
    / "csb_org_domain"
    / "ccx-domain-071"
    / "environment"
    / "Dockerfile"
)

# ---------------------------------------------------------------------------
# Detection helpers
# ---------------------------------------------------------------------------

# Matches the old chown optimization block (2-4 lines).
# Captures the full block including preceding comment lines.
OLD_CHOWN_BLOCK_RE = re.compile(
    r"(?:# Pre-create claude user.*\n"
    r"(?:#.*\n)*"  # optional extra comment lines
    r")?RUN \(adduser --disabled-password --gecos '' claude 2>/dev/null \|\| true\) &&\s*\\\n"
    r"\s+for d in /workspace /app /testbed /logs; do \[ -d \"\$d\" \] && chown -R claude:claude \"\$d\"; done \|\| true\n",
    re.MULTILINE,
)

# Matches a standalone "RUN mkdir -p /logs/agent /logs/verifier" line.
STANDALONE_MKDIR_LOGS_RE = re.compile(
    r"(?:# Create log directories\n)?RUN mkdir -p /logs/agent /logs/verifier\n",
    re.MULTILINE,
)

# Matches the first git clone line (to find insertion point).
FIRST_GIT_CLONE_RE = re.compile(
    r"^RUN git clone .*$", re.MULTILINE
)

# Matches any git clone line.
GIT_CLONE_LINE_RE = re.compile(
    r"^RUN git clone .*$", re.MULTILINE
)

# Matches the git config block (identity setup).
GIT_CONFIG_BLOCK_RE = re.compile(
    r"(?:# Initialize git identity.*\n)?"
    r"RUN git config --global user\.email \"agent@example\.com\" &&\s*\\\n"
    r"\s+git config --global user\.name \"Agent\" &&\s*\\\n"
    r"\s+git config --global safe\.directory '\*'\n",
    re.MULTILINE,
)

# Detect already-converted files (have "USER claude" before a git clone).
ALREADY_CONVERTED_RE = re.compile(
    r"USER claude\n.*?RUN git clone", re.DOTALL
)


def is_already_converted(content: str) -> bool:
    """Return True if the Dockerfile already uses the clone-as-claude pattern.

    Detection criteria (any of):
    - Has "USER claude" followed by "RUN git clone" (with-clones pattern)
    - Has "USER claude" and "USER root" with NO old chown block (no-clone pattern)
    """
    if ALREADY_CONVERTED_RE.search(content):
        return True
    # No-clone variant: USER claude appears, USER root appears, no old chown block
    if (
        "USER claude" in content
        and "USER root" in content
        and not has_old_chown_block(content)
        and not has_git_clone(content)
    ):
        return True
    return False


def has_git_clone(content: str) -> bool:
    """Return True if the Dockerfile contains at least one git clone command."""
    return bool(GIT_CLONE_LINE_RE.search(content))


def has_old_chown_block(content: str) -> bool:
    """Return True if the Dockerfile has the old adduser+chown block."""
    return bool(OLD_CHOWN_BLOCK_RE.search(content))


# ---------------------------------------------------------------------------
# Transformation for Dockerfiles WITH git clone commands
# ---------------------------------------------------------------------------

def transform_with_clones(content: str) -> str:
    """Transform a Dockerfile that has git clone commands.

    Strategy:
    1. Remove the old chown block (if present).
    2. Remove the standalone mkdir logs line (it gets folded into the new block).
    3. Remove the existing git config block (it will be re-inserted after clones).
    4. Find the WORKDIR /workspace line preceding clones.
    5. Before WORKDIR, insert:
       - adduser claude
       - mkdir + chown for /workspace and /logs
    6. Insert USER claude before WORKDIR.
    7. After last git clone, insert git config block.
    8. Insert USER root before ENTRYPOINT [].
    """
    lines = content.splitlines(keepends=True)
    result_lines: list[str] = []

    # --- Phase 1: Parse the file into sections ---
    # We need to identify line indices for key sections.

    # Find indices of important lines/blocks.
    first_clone_idx: int | None = None
    last_clone_idx: int | None = None
    workdir_before_clone_idx: int | None = None
    git_config_start: int | None = None
    git_config_end: int | None = None
    chown_block_start: int | None = None
    chown_block_end: int | None = None
    mkdir_logs_idx: int | None = None
    mkdir_logs_comment_idx: int | None = None
    entrypoint_idx: int | None = None

    i = 0
    while i < len(lines):
        stripped = lines[i].rstrip("\n")

        # Detect git clone lines
        if stripped.startswith("RUN git clone "):
            if first_clone_idx is None:
                first_clone_idx = i
            last_clone_idx = i

        # Detect WORKDIR /workspace before first clone
        if stripped == "WORKDIR /workspace" and first_clone_idx is None:
            workdir_before_clone_idx = i

        # Detect git config block
        if stripped.startswith("RUN git config --global user.email"):
            git_config_start = i
            # Check for comment line before it
            if i > 0 and lines[i - 1].strip().startswith("# Initialize git identity"):
                git_config_start = i - 1
            # Find end of this multi-line RUN (lines ending with \)
            j = i
            while j < len(lines) and lines[j].rstrip("\n").endswith("\\"):
                j += 1
            git_config_end = j  # inclusive

        # Detect old chown block
        if "RUN (adduser --disabled-password" in stripped and "claude" in stripped:
            chown_block_start = i
            # Check for comment lines before it
            ci = i - 1
            while ci >= 0 and lines[ci].strip().startswith("#") and (
                "Pre-create claude" in lines[ci]
                or "runtime chown" in lines[ci]
            ):
                chown_block_start = ci
                ci -= 1
            # Find end of this multi-line RUN
            j = i
            while j < len(lines) and lines[j].rstrip("\n").endswith("\\"):
                j += 1
            chown_block_end = j  # inclusive

        # Detect standalone mkdir logs
        if stripped == "RUN mkdir -p /logs/agent /logs/verifier":
            mkdir_logs_idx = i
            if i > 0 and lines[i - 1].strip() == "# Create log directories":
                mkdir_logs_comment_idx = i - 1

        # Detect ENTRYPOINT
        if stripped == "ENTRYPOINT []":
            entrypoint_idx = i

        i += 1

    if first_clone_idx is None:
        # No git clone -- should not reach here, caller checks
        return content

    # --- Phase 2: Build the set of line indices to skip ---
    skip_indices: set[int] = set()

    # Skip old chown block
    if chown_block_start is not None and chown_block_end is not None:
        for idx in range(chown_block_start, chown_block_end + 1):
            skip_indices.add(idx)
        # Also skip blank line after chown block if present
        if chown_block_end + 1 < len(lines) and lines[chown_block_end + 1].strip() == "":
            skip_indices.add(chown_block_end + 1)

    # Skip standalone mkdir logs (and its comment)
    if mkdir_logs_idx is not None:
        skip_indices.add(mkdir_logs_idx)
        if mkdir_logs_comment_idx is not None:
            skip_indices.add(mkdir_logs_comment_idx)
        # Also skip blank line after mkdir if present
        next_idx = mkdir_logs_idx + 1
        if next_idx < len(lines) and lines[next_idx].strip() == "":
            skip_indices.add(next_idx)

    # Skip existing git config block (we'll re-insert it in the right place)
    if git_config_start is not None and git_config_end is not None:
        for idx in range(git_config_start, git_config_end + 1):
            skip_indices.add(idx)
        # Also skip blank line after git config block if present
        next_idx = git_config_end + 1
        if next_idx < len(lines) and lines[next_idx].strip() == "":
            skip_indices.add(next_idx)

    # Skip the WORKDIR /workspace line (we'll re-insert it after USER claude)
    if workdir_before_clone_idx is not None:
        skip_indices.add(workdir_before_clone_idx)
        # Skip blank line after WORKDIR if the next line is a comment about cloning
        next_idx = workdir_before_clone_idx + 1
        if next_idx < len(lines) and lines[next_idx].strip() == "":
            skip_indices.add(next_idx)

    # --- Phase 3: Rebuild the file ---
    # New blocks to insert
    user_setup_block = (
        "# Create claude user BEFORE cloning so files are owned correctly from the\n"
        "# start.  This avoids a post-clone chown -R layer that doubles image size\n"
        "# and takes 15-30 min on overlay2 (copy-on-write duplicates every inode).\n"
        "RUN adduser --disabled-password --gecos '' claude 2>/dev/null || true\n"
        "RUN mkdir -p /workspace /logs/agent /logs/verifier && \\\n"
        "    chown -R claude:claude /workspace /logs\n"
        "\n"
        "# Clone as claude \N{EM DASH} files land claude-owned, no separate chown layer needed.\n"
        "USER claude\n"
        "WORKDIR /workspace\n"
    )

    git_config_new_block = (
        "\n"
        "# Initialize git identity for agent commits\n"
        "RUN git config --global user.email \"agent@example.com\" && \\\n"
        "    git config --global user.name \"Agent\" && \\\n"
        "    git config --global safe.directory '*'\n"
    )

    user_root_block = (
        "\n"
        "# Switch back to root for Harbor's runtime setup\n"
        "USER root\n"
    )

    # Determine the insertion point for user setup block.
    # We want to insert it right before the first clone comment or clone line.
    # First, check if there's a comment line directly before the first clone.
    insert_before_idx = first_clone_idx
    ci = first_clone_idx - 1
    while ci >= 0 and ci not in skip_indices:
        stripped_ci = lines[ci].strip()
        if stripped_ci.startswith("#") and (
            "clone" in stripped_ci.lower()
            or "checkout" in stripped_ci.lower()
            or "fixture" in stripped_ci.lower()
            or "local" in stripped_ci.lower()
            or "baseline" in stripped_ci.lower()
        ):
            insert_before_idx = ci
            ci -= 1
        elif stripped_ci == "":
            # Skip blank lines above clone comments too
            insert_before_idx = ci
            ci -= 1
        else:
            break

    # Also skip the blank line between WORKDIR and the clone comment if WORKDIR is being moved
    if workdir_before_clone_idx is not None:
        # The insert_before_idx might be the blank line after WORKDIR which is already skipped
        pass

    # Now build output
    i = 0
    inserted_user_setup = False
    inserted_git_config = False
    inserted_user_root = False

    while i < len(lines):
        # Skip lines marked for removal
        if i in skip_indices:
            i += 1
            continue

        # Insert user setup block before the first clone (or its preceding comment)
        if i == insert_before_idx and not inserted_user_setup:
            result_lines.append(user_setup_block)
            inserted_user_setup = True

        # After the last clone line, insert git config
        if i == last_clone_idx and not inserted_git_config:
            result_lines.append(lines[i])
            result_lines.append(git_config_new_block)
            inserted_git_config = True
            i += 1
            continue

        # Before ENTRYPOINT, insert USER root (if not already done)
        if i == entrypoint_idx and not inserted_user_root:
            result_lines.append(user_root_block)
            result_lines.append("\n")
            inserted_user_root = True

        result_lines.append(lines[i])
        i += 1

    output = "".join(result_lines)

    # Clean up excessive blank lines (collapse 2+ blank lines to 1 blank line)
    output = re.sub(r"\n{3,}", "\n\n", output)

    # Ensure file ends with exactly one newline
    output = output.rstrip("\n") + "\n"

    return output


# ---------------------------------------------------------------------------
# Transformation for Dockerfiles WITHOUT git clone commands
# ---------------------------------------------------------------------------

def transform_without_clones(content: str) -> str:
    """Transform a Dockerfile that has no git clone commands.

    These files just need:
    1. Replace the old chown block with the simpler adduser + mkdir/chown.
    2. Ensure git config runs as claude (USER claude before, USER root after).
    3. Ensure USER root before ENTRYPOINT.
    """
    lines = content.splitlines(keepends=True)

    # Find key indices
    git_config_start: int | None = None
    git_config_end: int | None = None
    chown_block_start: int | None = None
    chown_block_end: int | None = None
    mkdir_logs_idx: int | None = None
    mkdir_logs_comment_idx: int | None = None
    entrypoint_idx: int | None = None
    workdir_idx: int | None = None

    i = 0
    while i < len(lines):
        stripped = lines[i].rstrip("\n")

        if stripped == "WORKDIR /workspace":
            workdir_idx = i

        if stripped.startswith("RUN git config --global user.email"):
            git_config_start = i
            if i > 0 and lines[i - 1].strip().startswith("# Initialize git identity"):
                git_config_start = i - 1
            j = i
            while j < len(lines) and lines[j].rstrip("\n").endswith("\\"):
                j += 1
            git_config_end = j

        if "RUN (adduser --disabled-password" in stripped and "claude" in stripped:
            chown_block_start = i
            ci = i - 1
            while ci >= 0 and lines[ci].strip().startswith("#") and (
                "Pre-create claude" in lines[ci]
                or "runtime chown" in lines[ci]
            ):
                chown_block_start = ci
                ci -= 1
            j = i
            while j < len(lines) and lines[j].rstrip("\n").endswith("\\"):
                j += 1
            chown_block_end = j

        if stripped == "RUN mkdir -p /logs/agent /logs/verifier":
            mkdir_logs_idx = i
            if i > 0 and lines[i - 1].strip() == "# Create log directories":
                mkdir_logs_comment_idx = i - 1

        if stripped == "ENTRYPOINT []":
            entrypoint_idx = i

        i += 1

    # Build skip set
    skip_indices: set[int] = set()

    if chown_block_start is not None and chown_block_end is not None:
        for idx in range(chown_block_start, chown_block_end + 1):
            skip_indices.add(idx)
        if chown_block_end + 1 < len(lines) and lines[chown_block_end + 1].strip() == "":
            skip_indices.add(chown_block_end + 1)

    if mkdir_logs_idx is not None:
        skip_indices.add(mkdir_logs_idx)
        if mkdir_logs_comment_idx is not None:
            skip_indices.add(mkdir_logs_comment_idx)
        next_idx = mkdir_logs_idx + 1
        if next_idx < len(lines) and lines[next_idx].strip() == "":
            skip_indices.add(next_idx)

    # Skip existing git config block -- will be re-inserted under USER claude
    if git_config_start is not None and git_config_end is not None:
        for idx in range(git_config_start, git_config_end + 1):
            skip_indices.add(idx)
        next_idx = git_config_end + 1
        if next_idx < len(lines) and lines[next_idx].strip() == "":
            skip_indices.add(next_idx)

    # Skip WORKDIR -- will be re-inserted
    if workdir_idx is not None:
        skip_indices.add(workdir_idx)
        next_idx = workdir_idx + 1
        if next_idx < len(lines) and lines[next_idx].strip() == "":
            skip_indices.add(next_idx)

    # Determine where to insert the new user setup block.
    # For no-clone files, insert after the last RUN apt-get block.
    # Find the line after the apt-get install block.
    insert_after_apt = None
    for idx, line in enumerate(lines):
        if "rm -rf /var/lib/apt/lists" in line:
            insert_after_apt = idx
            break

    if insert_after_apt is None:
        # Fallback: insert before WORKDIR
        insert_after_apt = workdir_idx - 1 if workdir_idx else 0

    # Also skip the "# Clone local checkout repos" comment and the "# No local checkout"
    # comment lines that appear in no-clone Dockerfiles
    for idx, line in enumerate(lines):
        stripped_l = line.strip()
        if (
            stripped_l.startswith("# Clone local checkout")
            or stripped_l.startswith("# No local checkout")
            or stripped_l.startswith("# Clone all fixture")
        ):
            skip_indices.add(idx)
            # Skip blank line after
            if idx + 1 < len(lines) and lines[idx + 1].strip() == "":
                skip_indices.add(idx + 1)

    # Build the new block
    user_setup_block = (
        "\n"
        "# Create claude user BEFORE any work so files are owned correctly from the\n"
        "# start.  This avoids a post-clone chown -R layer that doubles image size\n"
        "# and takes 15-30 min on overlay2 (copy-on-write duplicates every inode).\n"
        "RUN adduser --disabled-password --gecos '' claude 2>/dev/null || true\n"
        "RUN mkdir -p /workspace /logs/agent /logs/verifier && \\\n"
        "    chown -R claude:claude /workspace /logs\n"
        "\n"
        "USER claude\n"
        "WORKDIR /workspace\n"
    )

    git_config_new_block = (
        "\n"
        "# Initialize git identity for agent commits\n"
        "RUN git config --global user.email \"agent@example.com\" && \\\n"
        "    git config --global user.name \"Agent\" && \\\n"
        "    git config --global safe.directory '*'\n"
    )

    user_root_block = (
        "\n"
        "# Switch back to root for Harbor's runtime setup\n"
        "USER root\n"
    )

    # Rebuild
    result_lines: list[str] = []
    inserted_setup = False
    inserted_user_root = False

    for i, line in enumerate(lines):
        if i in skip_indices:
            continue

        result_lines.append(line)

        # Insert user setup after apt-get line
        if i == insert_after_apt and not inserted_setup:
            result_lines.append(user_setup_block)
            result_lines.append(git_config_new_block)
            inserted_setup = True

        # Insert USER root before ENTRYPOINT
        if i == entrypoint_idx:
            # Already appended the ENTRYPOINT line -- need to insert before it
            pass

    # If we haven't inserted USER root before ENTRYPOINT, do it now
    # Re-scan the result to insert USER root before ENTRYPOINT []
    final_lines: list[str] = []
    for line in result_lines:
        if line.strip() == "ENTRYPOINT []" and not inserted_user_root:
            final_lines.append(user_root_block)
            final_lines.append("\n")
            inserted_user_root = True
        final_lines.append(line)

    output = "".join(final_lines)
    # Clean up excessive blank lines (collapse 2+ blank lines to 1 blank line)
    output = re.sub(r"\n{3,}", "\n\n", output)
    output = output.rstrip("\n") + "\n"

    return output


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def find_dockerfiles() -> list[Path]:
    """Find all baseline Dockerfiles under benchmarks/csb_org_* (and legacy ccb_mcp_*)."""
    pattern = str(REPO_ROOT / "benchmarks" / "csb_org_*" / "*" / "environment" / "Dockerfile")
    paths = sorted(glob.glob(pattern))
    # Exclude Dockerfile.sg_only and Dockerfile.artifact_only (those are separate files,
    # but the glob only matches "Dockerfile" exactly, so this is just a safety check).
    return [Path(p) for p in paths if p.endswith("/Dockerfile")]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Migrate csb_org_* Dockerfiles to clone-as-claude pattern.",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually write changes (default is dry-run).",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show full diff for each changed file.",
    )
    args = parser.parse_args()

    if not args.execute:
        print("=== DRY RUN (pass --execute to write changes) ===\n")

    # Validate reference file exists and is already in new format
    if not REFERENCE_FILE.exists():
        print(f"ERROR: Reference file not found: {REFERENCE_FILE}", file=sys.stderr)
        sys.exit(1)
    ref_content = REFERENCE_FILE.read_text()
    if not is_already_converted(ref_content):
        print(
            f"WARNING: Reference file does not appear to be in new format: {REFERENCE_FILE}",
            file=sys.stderr,
        )

    dockerfiles = find_dockerfiles()
    print(f"Found {len(dockerfiles)} Dockerfiles under benchmarks/csb_org_*/\n")

    stats = {
        "converted": 0,
        "skipped_already_new": 0,
        "skipped_no_change": 0,
        "with_clones": 0,
        "without_clones": 0,
        "errors": 0,
    }

    for dockerfile in dockerfiles:
        rel_path = dockerfile.relative_to(REPO_ROOT)
        content = dockerfile.read_text()

        # Check if already converted
        if is_already_converted(content):
            stats["skipped_already_new"] += 1
            if args.verbose:
                print(f"  SKIP (already converted): {rel_path}")
            continue

        # Apply transformation
        try:
            if has_git_clone(content):
                new_content = transform_with_clones(content)
                stats["with_clones"] += 1
            else:
                new_content = transform_without_clones(content)
                stats["without_clones"] += 1
        except Exception as exc:
            print(f"  ERROR: {rel_path}: {exc}", file=sys.stderr)
            stats["errors"] += 1
            continue

        # Check if anything changed
        if new_content == content:
            stats["skipped_no_change"] += 1
            if args.verbose:
                print(f"  SKIP (no change needed): {rel_path}")
            continue

        stats["converted"] += 1
        print(f"  {'WRITE' if args.execute else 'WOULD WRITE'}: {rel_path}")

        if args.verbose:
            # Show a simple before/after comparison
            diff = difflib.unified_diff(
                content.splitlines(keepends=True),
                new_content.splitlines(keepends=True),
                fromfile=f"a/{rel_path}",
                tofile=f"b/{rel_path}",
                n=3,
            )
            sys.stdout.writelines(diff)
            print()

        if args.execute:
            dockerfile.write_text(new_content)

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Total Dockerfiles scanned:    {len(dockerfiles)}")
    print(f"  Converted (with clones):      {stats['with_clones']}")
    print(f"  Converted (without clones):   {stats['without_clones']}")
    print(f"  Total converted:              {stats['converted']}")
    print(f"  Skipped (already new format): {stats['skipped_already_new']}")
    print(f"  Skipped (no change):          {stats['skipped_no_change']}")
    print(f"  Errors:                       {stats['errors']}")

    if not args.execute and stats["converted"] > 0:
        print(f"\nRun with --execute to apply {stats['converted']} change(s).")


if __name__ == "__main__":
    main()
