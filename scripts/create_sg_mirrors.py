#!/usr/bin/env python3
"""Create sg-evals mirrors on GitHub for reproducible Sourcegraph indexing.

Reads configs/mirror_creation_manifest.json and creates GitHub repos under
the sg-evals organization, pinned to specific commits.

Approach per mirror:
1. Create GitHub repo sg-evals/{name} (public)
2. Download source snapshot via GitHub archive API (no history needed)
3. Init fresh git repo, commit all files, push as main branch

For tags (v1.30.0), uses the tag name directly.
For commit hashes, resolves short hashes to full via GitHub API first.

Usage:
    python3 scripts/create_sg_mirrors.py [--dry-run] [--mirror NAME] [--skip-existing]
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = REPO_ROOT / "configs" / "mirror_creation_manifest.json"
ORG = "sg-evals"


def run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    """Run a command, returning CompletedProcess."""
    try:
        return subprocess.run(cmd, capture_output=True, text=True, **kwargs)
    except subprocess.TimeoutExpired as e:
        # Return a synthetic failed result on timeout
        return subprocess.CompletedProcess(
            cmd, returncode=124,
            stdout=e.stdout or "",
            stderr=f"timed out after {e.timeout}s",
        )


def repo_exists(mirror_name: str) -> bool:
    """Check if a GitHub repo already exists."""
    r = run(["gh", "repo", "view", f"{ORG}/{mirror_name}", "--json", "name"])
    return r.returncode == 0


def resolve_commit(upstream: str, ref: str) -> str | None:
    """Resolve a short hash or tag to a full commit SHA via GitHub API.

    Returns the full SHA, or None if resolution fails.
    """
    org_repo = upstream.replace("github.com/", "")
    r = run(["gh", "api", f"repos/{org_repo}/commits/{ref}", "--jq", ".sha"])
    if r.returncode == 0 and r.stdout.strip():
        return r.stdout.strip()
    return None


def create_mirror(entry: dict, dry_run: bool = False) -> tuple[bool, str]:
    """Create a single sg-evals mirror.

    Returns (success, message).
    """
    mirror_name = entry["mirror"].replace(f"{ORG}/", "")
    upstream = entry["upstream"]
    commit = entry["commit"]
    org_repo = upstream.replace("github.com/", "")

    # Check if already exists and has content
    if repo_exists(mirror_name):
        # Check if it has any commits (might be empty from a failed prior run)
        r = run(["gh", "api", f"repos/{ORG}/{mirror_name}/commits",
                 "--jq", "length", "-q"])
        if r.returncode == 0 and r.stdout.strip() not in ("0", ""):
            return True, "already exists"
        # Empty repo — delete and recreate
        if not dry_run:
            run(["gh", "repo", "delete", f"{ORG}/{mirror_name}", "--confirm"])

    # Resolve short hashes to full (archive API needs >= 7 chars, but let's be safe)
    is_tag = not all(c in "0123456789abcdef" for c in commit.lower())
    archive_ref = commit

    if not is_tag and len(commit) < 40:
        full_sha = resolve_commit(upstream, commit)
        if full_sha:
            archive_ref = full_sha
        else:
            return False, f"could not resolve short hash {commit}"

    if dry_run:
        return True, f"would create from {org_repo}@{archive_ref[:12]}"

    # Create the GitHub repo
    desc = f"Mirror of {org_repo} at {commit}"
    r = run(["gh", "repo", "create", f"{ORG}/{mirror_name}",
             "--public", "--description", desc])
    if r.returncode != 0:
        return False, f"gh repo create failed: {r.stderr.strip()}"

    # Small delay for GitHub to register the repo
    time.sleep(2)

    # Disable push protection (upstream repos may contain test/doc secrets)
    run(["gh", "api", f"repos/{ORG}/{mirror_name}",
         "-X", "PATCH",
         "-f", "security_and_analysis.secret_scanning_push_protection.status=disabled",
         "--silent"])

    # Download archive to temp dir
    workdir = tempfile.mkdtemp(prefix=f"sgmirror-{mirror_name}-")
    try:
        archive_url = f"https://github.com/{org_repo}/archive/{archive_ref}.tar.gz"
        r = run(["curl", "-sSL", "--fail", "-o", f"{workdir}/archive.tar.gz", archive_url],
                timeout=1800)  # 30 min for very large repos
        if r.returncode != 0:
            return False, f"archive download failed: {r.stderr.strip()}"

        # Extract
        r = run(["tar", "xzf", f"{workdir}/archive.tar.gz", "-C", workdir],
                timeout=600)  # 10 min for large extractions
        if r.returncode != 0:
            return False, f"tar extract failed: {r.stderr.strip()}"

        # Find the extracted directory (GitHub names it {repo}-{ref}/)
        os.remove(f"{workdir}/archive.tar.gz")
        extracted = [d for d in os.listdir(workdir) if os.path.isdir(f"{workdir}/{d}")]
        if not extracted:
            return False, "no directory found after extraction"
        src_dir = f"{workdir}/{extracted[0]}"

        # Init git repo and commit
        env = {**os.environ, "GIT_AUTHOR_NAME": "sg-evals",
               "GIT_AUTHOR_EMAIL": "benchmarks@sourcegraph.com",
               "GIT_COMMITTER_NAME": "sg-evals",
               "GIT_COMMITTER_EMAIL": "benchmarks@sourcegraph.com"}

        r = run(["git", "init", "-b", "main"], cwd=src_dir, env=env)
        if r.returncode != 0:
            return False, f"git init failed: {r.stderr.strip()}"

        r = run(["git", "add", "-A"], cwd=src_dir, env=env, timeout=300)
        if r.returncode != 0:
            return False, f"git add failed: {r.stderr.strip()}"

        commit_msg = f"Mirror of {org_repo} at {commit}\n\nUpstream: https://github.com/{org_repo}\nRef: {archive_ref}"
        r = run(["git", "commit", "-m", commit_msg], cwd=src_dir, env=env, timeout=120)
        if r.returncode != 0:
            return False, f"git commit failed: {r.stderr.strip()}"

        # Push
        remote_url = f"https://github.com/{ORG}/{mirror_name}.git"
        r = run(["git", "remote", "add", "origin", remote_url], cwd=src_dir, env=env)
        if r.returncode != 0:
            return False, f"git remote add failed: {r.stderr.strip()}"

        r = run(["git", "push", "-u", "origin", "main"], cwd=src_dir, env=env, timeout=1800)
        if r.returncode != 0:
            return False, f"git push failed: {r.stderr.strip()}"

        return True, "created successfully"

    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Create sg-evals mirrors from manifest")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
    parser.add_argument("--mirror", type=str, help="Create a single mirror by name")
    parser.add_argument("--skip-existing", action="store_true", default=True,
                        help="Skip mirrors that already exist (default: true)")
    args = parser.parse_args()

    manifest = json.loads(MANIFEST_PATH.read_text())
    entries = manifest["mirrors"]

    if args.mirror:
        entries = [e for e in entries if e["mirror"].endswith(args.mirror) or e["mirror"] == args.mirror]
        if not entries:
            print(f"ERROR: No mirror matching '{args.mirror}' in manifest", file=sys.stderr)
            sys.exit(1)

    # Filter out already-existing
    if args.skip_existing and not args.dry_run:
        print("Checking which mirrors already exist...")
        r = run(["gh", "repo", "list", ORG, "--limit", "300", "--json", "name", "--jq", ".[].name"])
        existing = set(r.stdout.strip().split("\n")) if r.returncode == 0 else set()
        to_create = [e for e in entries if e["mirror"].replace(f"{ORG}/", "") not in existing]
        skipped = len(entries) - len(to_create)
        print(f"  {len(existing)} repos exist, {skipped} mirrors already done, {len(to_create)} to create\n")
        entries = to_create

    created = 0
    failed = []
    skipped_count = 0

    mode = "DRY RUN" if args.dry_run else "CREATING"
    print(f"=== {mode}: {len(entries)} mirrors ===\n")

    for i, entry in enumerate(entries, 1):
        mirror = entry["mirror"]
        upstream_short = entry["upstream"].replace("github.com/", "")
        ref_short = entry["commit"][:12] if len(entry["commit"]) > 12 else entry["commit"]

        print(f"[{i}/{len(entries)}] {mirror} ← {upstream_short}@{ref_short} ... ", end="", flush=True)

        ok, msg = create_mirror(entry, dry_run=args.dry_run)
        if ok:
            if "already exists" in msg:
                print(f"SKIP ({msg})")
                skipped_count += 1
            else:
                print(f"OK ({msg})")
                created += 1
        else:
            print(f"FAIL ({msg})")
            failed.append((mirror, msg))

    print(f"\n=== Summary: {created} created, {skipped_count} skipped, {len(failed)} failed ===")
    if failed:
        print("\nFailed mirrors:")
        for mirror, msg in failed:
            print(f"  {mirror}: {msg}")
        sys.exit(1)


if __name__ == "__main__":
    main()
