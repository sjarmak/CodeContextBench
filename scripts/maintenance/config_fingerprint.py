#!/usr/bin/env python3
"""Config identity fingerprinting for CodeScaleBench MANIFEST runs.

Computes a SHA-256 fingerprint of the agent harness code (agents/ directory).
Used to detect when MANIFEST run entries are stale — i.e., they were executed
against a different version of the agent harness than what's currently on disk.

Fingerprint approach:
- Hash the entire agents/ directory tree using `git ls-tree -r` (for historical
  commits) or direct file hashing (for the current working tree).
- Build a timeline of fingerprints keyed by commit timestamp.
- For each MANIFEST run entry (which has a started_at timestamp), look up
  which fingerprint was active at that time.
- Runs whose historical fingerprint differs from the current fingerprint are
  flagged as stale.
"""

import hashlib
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


# Directory containing agent harness code.  All files under this directory
# contribute to the fingerprint.  Changing any agent file changes the
# fingerprint, making previously-run benchmarks stale.
AGENT_DIR = "agents"


def _sha256_hex(data: bytes, length: int = 12) -> str:
    return hashlib.sha256(data).hexdigest()[:length]


def _hash_agents_dir_current(repo_root: Path) -> str:
    """Hash all files in agents/ in the current working tree.

    Returns a short (12-char) hex digest that changes whenever any file in
    agents/ changes.
    """
    h = hashlib.sha256()
    agents_path = repo_root / AGENT_DIR
    if not agents_path.exists():
        return "missing"
    for f in sorted(agents_path.rglob("*")):
        if f.is_file():
            h.update(f.relative_to(repo_root).as_posix().encode())
            h.update(b"\x00")
            h.update(f.read_bytes())
    return h.hexdigest()[:12]


def _hash_agents_dir_at_commit(repo_root: Path, commit: str) -> str:
    """Hash the agents/ tree at a specific git commit.

    Uses the same algorithm as _hash_agents_dir_current: iterates files in
    sorted order and hashes relative_path + content bytes.  File content is
    extracted with `git show COMMIT:path`.

    Gets the file list first via `git ls-tree -r` (one command), then fetches
    content for each file.  For the typical ~10-file agents/ tree this is fast.

    Returns a short (12-char) hex digest, or 'error'/'empty' on failure.
    """
    # List all files in agents/ at this commit
    ls_result = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", commit, AGENT_DIR],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    if ls_result.returncode != 0:
        return "error"
    paths = [p for p in ls_result.stdout.strip().splitlines() if p]
    if not paths:
        return "empty"

    h = hashlib.sha256()
    for rel_path in sorted(paths):
        show_result = subprocess.run(
            ["git", "show", f"{commit}:{rel_path}"],
            cwd=repo_root,
            capture_output=True,
        )
        if show_result.returncode != 0:
            continue
        h.update(rel_path.encode())
        h.update(b"\x00")
        h.update(show_result.stdout)
    return h.hexdigest()[:12]


def compute_current_fingerprint(repo_root: Path) -> dict:
    """Compute the fingerprint of the agent harness code as it exists now.

    Returns:
        {
            "fingerprint": "<12-char hex>",   # stable ID of current harness
            "agent_dir": "agents",            # directory that was hashed
        }
    """
    fp = _hash_agents_dir_current(repo_root)
    return {
        "fingerprint": fp,
        "agent_dir": AGENT_DIR,
    }


def build_fingerprint_timeline(repo_root: Path) -> list[dict]:
    """Build a timeline of agent harness fingerprints from git history.

    Walks all commits that touched the agents/ directory and computes the
    fingerprint for each one.  Returns a list sorted newest-first:

        [
            {"timestamp": "2026-03-15T17:30:32+00:00", "fingerprint": "abc123...", "commit": "5c72..."},
            ...
        ]

    The timeline is used by fingerprint_for_timestamp() to look up what
    fingerprint was active at a given run's started_at time.
    """
    # Get all commits touching agents/ with their ISO timestamps
    result = subprocess.run(
        ["git", "log", "--format=%H %aI", "--", AGENT_DIR],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 or not result.stdout.strip():
        return []

    # Deduplicate fingerprints (consecutive identical trees only need one entry)
    timeline = []
    seen_fp: Optional[str] = None

    for line in result.stdout.strip().splitlines():
        parts = line.split(" ", 1)
        if len(parts) != 2:
            continue
        commit_hash, timestamp = parts[0], parts[1]

        fp = _hash_agents_dir_at_commit(repo_root, commit_hash)
        entry = {
            "timestamp": timestamp,
            "fingerprint": fp,
            "commit": commit_hash,
        }
        timeline.append(entry)
        seen_fp = fp

    return timeline  # newest first


def fingerprint_for_timestamp(timeline: list[dict], run_timestamp: str) -> Optional[str]:
    """Find the agent fingerprint that was active at a given run timestamp.

    The timeline is sorted newest-first.  We want the newest commit that is
    older than or equal to the run timestamp — i.e., the code that was on
    disk when the run executed.

    Args:
        timeline: List of {timestamp, fingerprint, commit} sorted newest-first.
        run_timestamp: ISO 8601 string (e.g. "2026-02-03T16:06:16+00:00" or
                       "2026-02-03 16-06-16" as stored in MANIFEST).

    Returns:
        Fingerprint string, or None if the run predates all commits in history.
    """
    if not timeline or not run_timestamp:
        return None

    run_dt = _parse_iso(run_timestamp)
    if run_dt is None:
        return None

    # Walk newest-first; return the first commit that is <= the run time.
    for entry in timeline:
        commit_dt = _parse_iso(entry["timestamp"])
        if commit_dt is None:
            continue
        if commit_dt <= run_dt:
            return entry["fingerprint"]

    # All commits are newer than the run — run predates our git history
    return None


def _parse_iso(ts: str) -> Optional[datetime]:
    """Parse an ISO 8601 timestamp string into a timezone-aware datetime.

    Handles both MANIFEST format ("2026-02-03 16-06-16") and git aI format
    ("2026-03-15T17:30:32+00:00").
    """
    if not ts:
        return None
    # Normalise MANIFEST-style "2026-02-03 16-06-16" → "2026-02-03T16:06:16"
    ts_norm = ts.strip()
    if " " in ts_norm and "T" not in ts_norm:
        date_part, time_part = ts_norm.split(" ", 1)
        time_part = time_part.replace("-", ":")
        ts_norm = f"{date_part}T{time_part}"
    # Handle "Z" suffix
    ts_norm = ts_norm.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(ts_norm)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None
