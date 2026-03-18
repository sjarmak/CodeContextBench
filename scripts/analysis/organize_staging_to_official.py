#!/usr/bin/env python3
"""
Organize valid staging runs into official directory with clean structure.

Target layout:
  runs/official/{suite}_{model}_{MMDDYY}/
    baseline/
      {task_dir}/          # full task directory tree (copied)
    mcp/
      {task_dir}/          # full task directory tree (copied)

Only tasks with NO infrastructure errors are copied.
Excluded: Docker compose failures, RewardFileNotFoundError.
Kept: clean tasks AND agent timeouts (real performance signals).
"""

import json
import os
import re
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
STAGING = REPO_ROOT / "runs" / "staging"
OFFICIAL = REPO_ROOT / "runs" / "official"

# Runs to skip
SKIP_PREFIXES = ("__archived_", "__broken_verifier_")

# Config -> subfolder mapping
BASELINE_CONFIGS = {"baseline-local-direct", "baseline-local-artifact"}
MCP_CONFIGS = {"mcp-remote-direct", "mcp-remote-artifact"}

REJECTED_RATE_LIMIT_PATTERNS = (
    '"type":"rate_limit_event"',
    '"status":"rejected"',
    '"error":"rate_limit"',
    "You've hit your limit",
)


def has_rejected_rate_limit_marker(result_path: Path) -> bool:
    """Return True when the adjacent transcript shows a rejected Claude rate limit."""
    transcript_path = result_path.parent / "agent" / "claude-code.txt"
    if not transcript_path.exists():
        return False

    try:
        transcript = transcript_path.read_text(errors="ignore")
    except OSError:
        return False

    return all(pattern in transcript for pattern in REJECTED_RATE_LIMIT_PATTERNS[:2]) or any(
        pattern in transcript for pattern in REJECTED_RATE_LIMIT_PATTERNS[2:]
    )


def should_exclude(result_path: Path) -> str | None:
    """Return exclusion reason or None if task is valid."""
    try:
        with open(result_path) as f:
            data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        return f"unreadable result.json: {e}"

    if has_rejected_rate_limit_marker(result_path):
        return "rate_limited: rejected Claude runtime quota"

    exc = data.get("exception_info")
    if not exc:
        return None  # Clean task

    exc_type = exc.get("exception_type", "") or ""
    exc_msg = exc.get("exception_message", "") or ""

    # Docker infrastructure failure
    if exc_type == "RuntimeError" and "Docker compose command failed" in exc_msg:
        return f"docker_failure: {exc_msg[:80]}"

    # Reward file not found (verifier bug)
    if exc_type == "RewardFileNotFoundError":
        return f"reward_file_missing: {exc_msg[:80]}"

    # Rate limiting
    if any(term in exc_msg.lower() for term in ["rate limit", "429", "quota exceeded"]):
        return f"rate_limited: {exc_msg[:80]}"

    # Keep everything else (including AgentTimeoutError — real signal)
    return None


def parse_run_name(run_dir_name: str) -> tuple[str, str, str] | None:
    """
    Extract (suite_name, model, date_MMDDYY) from a run directory name.

    Examples:
        build_haiku_20260223_124805         -> (ccb_build, haiku, 022326)
        ccb_mcp_onboarding_haiku_20260221_140913 -> (ccb_mcp_onboarding, haiku, 022126)
        ccb_secure_opus_20260223_210902     -> (ccb_secure, opus, 022326)
    """
    # Match model + timestamp at end: _{model}_YYYYMMDD_HHMMSS
    # Supports model variants like sonnet46, opus45 etc.
    m = re.search(r"_(haiku|opus|sonnet\d*)_(\d{4})(\d{2})(\d{2})_\d{6}$", run_dir_name)
    if not m:
        return None
    model = m.group(1)
    year, month, day = m.group(2), m.group(3), m.group(4)
    date_str = f"{month}{day}{year[2:]}"  # MMDDYY

    # Extract suite: everything before _{model}_{timestamp}
    prefix = re.sub(r"_(haiku|opus|sonnet\d*)_\d{8}_\d{6}$", "", run_dir_name)

    # Normalize: SDLC phases without prefix get csb_sdlc_ added
    sdlc_phases = {"build", "debug", "design", "document", "fix", "secure", "test", "understand",
                   "feature", "refactor"}
    if prefix in sdlc_phases:
        suite = f"csb_sdlc_{prefix}"
    elif prefix.startswith(("csb_", "ccb_", "openhands")):
        suite = prefix
    else:
        suite = f"csb_sdlc_{prefix}"

    return suite, model, date_str


def find_trial_results_sdlc(config_dir: Path) -> list[tuple[Path, Path]]:
    """
    For SDLC (direct) configs, find trial-level result.json files.
    Returns list of (task_dir, trial_result_json) pairs.

    Structure: config_dir/ccb_{suite}_{taskname}_{config}/{taskname}__{id}/result.json
    """
    results = []
    for task_dir in config_dir.iterdir():
        if not task_dir.is_dir() or task_dir.name.startswith("."):
            continue
        # Find trial subdirectories (contain __ in name)
        for trial_dir in task_dir.iterdir():
            if trial_dir.is_dir() and "__" in trial_dir.name:
                result_file = trial_dir / "result.json"
                if result_file.exists():
                    results.append((task_dir, result_file))
    return results


def find_trial_results_artifact(config_dir: Path) -> list[tuple[Path, Path]]:
    """
    For artifact (MCP-unique) configs, find trial-level result.json files.
    Returns list of (task_dir_within_batch, trial_result_json) pairs.

    Structure: config_dir/YYYY-MM-DD__HH-MM-SS/{taskname}__{id}/result.json
    """
    results = []
    for batch_dir in config_dir.iterdir():
        if not batch_dir.is_dir():
            continue
        # Batch dirs look like 2026-02-21__14-42-26 or are task dirs
        for task_or_trial in batch_dir.iterdir():
            if task_or_trial.is_dir() and "__" in task_or_trial.name:
                result_file = task_or_trial / "result.json"
                if result_file.exists():
                    # The "task_dir" for artifact mode is the batch parent + trial
                    # We'll copy from the batch level
                    results.append((batch_dir, result_file))
    return results


def extract_task_name_from_result(result_path: Path) -> str:
    """Get the task_name from a result.json file."""
    try:
        with open(result_path) as f:
            data = json.load(f)
        return data.get("task_name", "unknown")
    except Exception:
        return "unknown"


def main():
    dry_run = "--dry-run" in sys.argv
    verbose = "--verbose" in sys.argv or dry_run

    if dry_run:
        print("=== DRY RUN (no files will be copied) ===\n")

    stats = {
        "runs_scanned": 0,
        "tasks_valid": 0,
        "tasks_excluded": 0,
        "exclusion_reasons": {},
        "suites_created": set(),
    }

    # Collect all work: {(suite, date): {subfolder: [(src_task_dir, task_name)]}}
    work = {}

    for run_dir in sorted(STAGING.iterdir()):
        if not run_dir.is_dir():
            continue
        if any(run_dir.name.startswith(p) for p in SKIP_PREFIXES):
            continue

        parsed = parse_run_name(run_dir.name)
        if not parsed:
            print(f"  SKIP (can't parse): {run_dir.name}")
            continue

        suite, model, date_str = parsed
        stats["runs_scanned"] += 1
        official_name = f"{suite}_{model}_{date_str}"

        if verbose:
            print(f"\nProcessing: {run_dir.name} -> {official_name}")

        for config_name in sorted(os.listdir(run_dir)):
            config_dir = run_dir / config_name
            if not config_dir.is_dir():
                continue

            # Determine if baseline or MCP
            if config_name in BASELINE_CONFIGS:
                subfolder = "baseline"
            elif config_name in MCP_CONFIGS:
                subfolder = "mcp"
            else:
                continue  # skip retrieval_events, etc.

            # Determine if direct or artifact mode
            is_artifact = "artifact" in config_name

            if is_artifact:
                trial_results = find_trial_results_artifact(config_dir)
            else:
                trial_results = find_trial_results_sdlc(config_dir)

            for task_dir, result_path in trial_results:
                task_name = extract_task_name_from_result(result_path)
                reason = should_exclude(result_path)

                if reason:
                    stats["tasks_excluded"] += 1
                    stats["exclusion_reasons"][reason] = stats["exclusion_reasons"].get(reason, 0) + 1
                    if verbose:
                        print(f"  EXCLUDE [{subfolder}] {task_name}: {reason}")
                    continue

                stats["tasks_valid"] += 1
                stats["suites_created"].add(official_name)

                key = (official_name, subfolder)
                if key not in work:
                    work[key] = []

                # For SDLC direct mode, copy the whole task_dir (ccb_suite_task_config/)
                # For artifact mode, copy the trial dir directly
                if is_artifact:
                    # trial dir is result_path.parent
                    trial_dir = result_path.parent
                    work[key].append((trial_dir, task_name))
                else:
                    work[key].append((task_dir, task_name))

    # Now execute the copies
    print(f"\n{'=' * 60}")
    print(f"SUMMARY")
    print(f"{'=' * 60}")
    print(f"Runs scanned:    {stats['runs_scanned']}")
    print(f"Tasks valid:     {stats['tasks_valid']}")
    print(f"Tasks excluded:  {stats['tasks_excluded']}")
    print(f"Suites created:  {len(stats['suites_created'])}")
    print(f"\nTarget suites:")
    for s in sorted(stats["suites_created"]):
        print(f"  {s}")

    if stats["exclusion_reasons"]:
        print(f"\nExclusion reasons:")
        for reason, count in sorted(stats["exclusion_reasons"].items(), key=lambda x: -x[1]):
            print(f"  [{count:3d}] {reason}")

    print(f"\nCopy plan:")
    for (official_name, subfolder), tasks in sorted(work.items()):
        # Deduplicate by task_name (keep last occurrence = most recent)
        seen = {}
        for src, tname in tasks:
            seen[tname] = src
        unique_count = len(seen)
        print(f"  {official_name}/{subfolder}: {unique_count} tasks")

    if dry_run:
        print("\n=== DRY RUN COMPLETE (no files copied) ===")
        return

    # Confirm
    print(f"\nProceed with copy to {OFFICIAL}? [y/N] ", end="", flush=True)
    answer = input().strip().lower()
    if answer != "y":
        print("Aborted.")
        return

    # Execute copies
    copied = 0
    for (official_name, subfolder), tasks in sorted(work.items()):
        dest_base = OFFICIAL / official_name / subfolder
        dest_base.mkdir(parents=True, exist_ok=True)

        # Deduplicate by task_name (keep last = most recent)
        seen = {}
        for src, tname in tasks:
            seen[tname] = src

        for tname, src_dir in seen.items():
            dest_dir = dest_base / src_dir.name
            if dest_dir.exists():
                if verbose:
                    print(f"  EXISTS (skip): {dest_dir.relative_to(OFFICIAL)}")
                continue
            shutil.copytree(
                src_dir, dest_dir,
                symlinks=True,
                ignore_dangling_symlinks=True,
                ignore=shutil.ignore_patterns("sessions"),
            )
            copied += 1
            if verbose:
                print(f"  COPIED: {dest_dir.relative_to(OFFICIAL)}")

    print(f"\nDone! Copied {copied} task directories to {OFFICIAL}")


if __name__ == "__main__":
    main()
