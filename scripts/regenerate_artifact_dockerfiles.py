#!/usr/bin/env python3
"""Regenerate Dockerfile.artifact_only to ensure correct verifier routing.

Three categories:
  1. STUBS with repo base images (39): Add /repo_full backup + chmod 700 + workdir marker
  2. Build-requiring sg_only + stub artifact_only (10): Transform sg_only → artifact sentinel
  3. Existing correct files (70): Add chmod 700 /repo_full if missing

Does NOT touch write-only stubs (81) — they have no repo base image and
verifier scores output only.

Usage:
  python3 scripts/regenerate_artifact_dockerfiles.py [--dry-run] [--verbose]
"""

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BENCHMARKS = REPO_ROOT / "benchmarks"

# Base image patterns that indicate a repo is cloned in the image
REPO_IMAGE_PATTERNS = (
    r"^ccb-repo-",
    r"^jefzda/sweap-images:",
    r"sweap-images:",
)


def has_repo_base_image(dockerfile_text: str) -> bool:
    """Check if the Dockerfile uses a repo-containing base image."""
    m = re.search(r"^FROM\s+(\S+)", dockerfile_text, re.MULTILINE)
    if not m:
        return False
    image = m.group(1)
    return any(re.search(p, image) for p in REPO_IMAGE_PATTERNS)


def detect_workdir(dockerfile_text: str, fallback: str = "/app") -> str:
    """Detect the last WORKDIR from a Dockerfile."""
    workdirs = re.findall(r"^WORKDIR\s+(\S+)", dockerfile_text, re.MULTILINE)
    return workdirs[-1] if workdirs else fallback


def has_repo_full(dockerfile_text: str) -> bool:
    """Check if Dockerfile actually backs up to /repo_full (not just a comment mention)."""
    return bool(re.search(r"^RUN\s+cp\s+-a\s+\S+\s+/repo_full", dockerfile_text, re.MULTILINE))


def has_chmod_repo_full(dockerfile_text: str) -> bool:
    """Check if Dockerfile already has chmod 700 /repo_full."""
    return "chmod 700 /repo_full" in dockerfile_text or "chmod 0700 /repo_full" in dockerfile_text


def fix_stub_with_repo_image(task_name: str, text: str, workdir: str) -> str:
    """Transform a stub artifact_only (repo base image, no backup) into a proper one.

    Adds /repo_full backup, chmod 700, and workdir marker.
    """
    # Update header comment
    text = text.replace("(write-only)", "(build-requiring)")
    text = text.replace(
        "Verifier scores agent output only — no repo restore needed.",
        "Verifier applies patches from answer.json to /repo_full copy for scoring.",
    )

    # Replace the artifact section
    old_section = (
        "# --- artifact_only mode ---\n"
        "# Sentinel flag for artifact-based verification.\n"
        "# Source stays readable for baseline agent; MCP agent deletes at runtime.\n"
        "RUN touch /tmp/.artifact_only_mode"
    )
    new_section = (
        f"# --- artifact_only: backup full repo for verifier scoring ---\n"
        f"# Source stays in {workdir} (readable by baseline agent).\n"
        f"# MCP agent deletes source files at runtime via agent startup script.\n"
        f"RUN cp -a {workdir} /repo_full\n"
        f"RUN chmod 700 /repo_full\n"
        f"RUN touch /tmp/.artifact_only_mode && echo '{workdir}' > /tmp/.artifact_only_workdir"
    )

    if old_section in text:
        text = text.replace(old_section, new_section)
    else:
        # Fallback: insert before the sentinel line
        text = re.sub(
            r"RUN touch /tmp/\.artifact_only_mode\s*\n",
            f"RUN cp -a {workdir} /repo_full\n"
            f"RUN chmod 700 /repo_full\n"
            f"RUN touch /tmp/.artifact_only_mode && echo '{workdir}' > /tmp/.artifact_only_workdir\n",
            text,
        )

    return text


def transform_sgonly_to_artifact(text: str) -> str:
    """Transform a build-requiring Dockerfile.sg_only into artifact_only.

    Swaps sentinel from .sg_only_mode to .artifact_only_mode and adds chmod.
    """
    # Swap sentinel
    text = text.replace("touch /tmp/.sg_only_mode", "touch /tmp/.artifact_only_mode")
    text = text.replace(".sg_only_workdir", ".artifact_only_workdir")

    # Update comments
    text = text.replace("sg_only_env variant", "artifact_only variant (build-requiring)")
    text = text.replace(
        "Source files truncated so agent must use Sourcegraph MCP for code access.",
        "Source files truncated so agent must use Sourcegraph MCP for code access.\n"
        "# Verifier applies patches from answer.json to /repo_full copy for scoring.",
    )
    text = text.replace(
        "Verifier wrapper restores full repo before running tests.",
        "Verifier applies patches from answer.json to /repo_full copy for scoring.",
    )

    # Add chmod 700 after cp -a ... /repo_full if not already present
    if not has_chmod_repo_full(text):
        text = re.sub(
            r"(RUN cp -a \S+ /repo_full)\n",
            r"\1\nRUN chmod 700 /repo_full\n",
            text,
        )

    # Remove sg_only-specific lines (recommit for git history bypass)
    # Keep the truncation — it's still needed for artifact mode
    # Remove the sgonly_verifier_wrapper reference if present
    text = text.replace(
        '# sg_only_env: restore full repo before verification (no-op for regular runs)',
        '# artifact_only: verifier applies diffs from answer.json',
    )

    return text


def add_chmod_to_existing(text: str) -> str:
    """Add chmod 700 /repo_full to an existing correct artifact_only file."""
    if has_chmod_repo_full(text):
        return text

    # Insert after the cp -a line
    text = re.sub(
        r"(RUN cp -a \S+ /repo_full)\n",
        r"\1\nRUN chmod 700 /repo_full\n",
        text,
    )
    return text


def main():
    dry_run = "--dry-run" in sys.argv
    verbose = "--verbose" in sys.argv or "-v" in sys.argv

    stats = {
        "stubs_fixed": 0,
        "sgonly_transformed": 0,
        "chmod_added": 0,
        "already_correct": 0,
        "write_only_skipped": 0,
        "errors": [],
    }

    for suite_dir in sorted(BENCHMARKS.iterdir()):
        if not suite_dir.is_dir() or not suite_dir.name.startswith("ccb_"):
            continue

        for task_dir in sorted(suite_dir.iterdir()):
            if not task_dir.is_dir():
                continue

            env_dir = task_dir / "environment"
            artifact_only = env_dir / "Dockerfile.artifact_only"
            sg_only = env_dir / "Dockerfile.sg_only"
            original = env_dir / "Dockerfile"

            if not artifact_only.exists():
                continue

            text = artifact_only.read_text()
            task_name = task_dir.name
            task_path = f"{suite_dir.name}/{task_name}"

            # Case 1: Already has /repo_full — check if needs chmod
            if has_repo_full(text):
                if not has_chmod_repo_full(text):
                    new_text = add_chmod_to_existing(text)
                    if new_text != text:
                        if not dry_run:
                            artifact_only.write_text(new_text)
                        stats["chmod_added"] += 1
                        if verbose:
                            print(f"  CHMOD   {task_path}")
                    else:
                        stats["already_correct"] += 1
                else:
                    stats["already_correct"] += 1
                continue

            # Case 2: Stub with repo base image — add backup
            if has_repo_base_image(text):
                # Detect workdir from original Dockerfile or stub
                workdir = detect_workdir(text)
                if workdir == "/app" and original.exists():
                    # Double-check from original
                    orig_wd = detect_workdir(original.read_text(), fallback="/app")
                    workdir = orig_wd

                new_text = fix_stub_with_repo_image(task_name, text, workdir)

                if not dry_run:
                    artifact_only.write_text(new_text)
                stats["stubs_fixed"] += 1
                if verbose:
                    print(f"  FIXED   {task_path} (workdir={workdir})")
                continue

            # Case 3: Stub without repo base image — check if sg_only has /repo_full
            if sg_only.exists() and has_repo_full(sg_only.read_text()):
                sg_text = sg_only.read_text()
                new_text = transform_sgonly_to_artifact(sg_text)

                if not dry_run:
                    artifact_only.write_text(new_text)
                stats["sgonly_transformed"] += 1
                if verbose:
                    print(f"  XFORM   {task_path} (from sg_only)")
                continue

            # Case 4: Write-only (no repo base, no build-requiring sg_only) — skip
            stats["write_only_skipped"] += 1
            if verbose:
                print(f"  SKIP    {task_path} (write-only)")

    prefix = "DRY RUN — " if dry_run else ""
    print(f"\n{prefix}Summary:")
    print(f"  Stubs fixed (backup added):     {stats['stubs_fixed']}")
    print(f"  Transformed from sg_only:       {stats['sgonly_transformed']}")
    print(f"  Chmod added to existing:        {stats['chmod_added']}")
    print(f"  Already correct:                {stats['already_correct']}")
    print(f"  Write-only skipped:             {stats['write_only_skipped']}")
    if stats["errors"]:
        print(f"  Errors:                         {len(stats['errors'])}")
        for err in stats["errors"]:
            print(f"    {err}")


if __name__ == "__main__":
    main()
