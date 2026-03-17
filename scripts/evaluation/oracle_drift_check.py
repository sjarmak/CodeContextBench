#!/usr/bin/env python3
"""Oracle drift detection: verify ground truth file paths exist in source repos.

Parses each task's ground_truth.json for file paths and checks them against
the repo(s) cloned in the task's Dockerfile. Uses GitHub API (gh) for
GitHub-hosted repos; skips non-GitHub sources.

Usage:
    python3 scripts/oracle_drift_check.py                   # check all tasks
    python3 scripts/oracle_drift_check.py --tasks-dir benchmarks/csb/feature  # one category
    python3 scripts/oracle_drift_check.py --verbose          # show per-file results
    python3 scripts/oracle_drift_check.py --json             # machine-readable output
"""

import argparse
import glob
import json
import os
import re
import subprocess
import sys
from typing import Optional

# ── Path extraction ──────────────────────────────────────────────────────────

# Fields containing paths to files that EXIST in the source repo.
# Excludes 'expected_files' — those are files the agent should CREATE, not source files.
PATH_FIELDS = ["files", "buggy_files", "expected_edit_files"]


def _normalize_slug(raw_slug: str) -> str:
    """Normalize a GT repo slug to match Dockerfile clone dir names.

    Handles formats like:
      'kubernetes'                → 'kubernetes'
      'github.com/servo/stylo'   → 'stylo'
      'prometheus/prometheus'     → 'prometheus'
      'kubernetes-client-go'     → 'kubernetes-client-go'
    """
    slug = raw_slug.strip()
    # Strip github.com/ or any domain prefix
    if "/" in slug:
        slug = slug.rsplit("/", 1)[-1]
    return slug


def extract_paths(gt: dict) -> list[tuple[Optional[str], str]]:
    """Extract (repo_slug | None, file_path) tuples from ground truth."""
    paths = []

    # files, buggy_files, expected_edit_files, expected_files — all list[str]
    for field in PATH_FIELDS:
        items = gt.get(field, [])
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, str) or not item.strip():
                continue
            if "::" in item:
                repo_slug, fpath = item.split("::", 1)
                paths.append((_normalize_slug(repo_slug), fpath.strip()))
            else:
                paths.append((None, item.strip()))

    # symbols[].file + symbols[].repo
    for sym in gt.get("symbols", []):
        if not isinstance(sym, dict):
            continue
        fpath = sym.get("file", "")
        repo_full = sym.get("repo")  # e.g. "sg-evals/client-go--v0.32.0" or None
        if fpath:
            # Derive slug from repo field if present
            slug = None
            if repo_full and "/" in repo_full:
                # "sg-evals/client-go--v0.32.0" → "client-go"
                slug = repo_full.split("/", 1)[1].rsplit("--", 1)[0]
            paths.append((slug, fpath.strip()))

    # canonical_path (onboard-search tasks)
    cp = gt.get("canonical_path", "")
    if cp:
        paths.append((None, cp.strip()))

    # Deduplicate while preserving order
    seen = set()
    deduped = []
    for item in paths:
        if item not in seen:
            seen.add(item)
            deduped.append(item)
    return deduped


# ── Dockerfile parsing ───────────────────────────────────────────────────────

# Match: git clone [flags] <url> [dest]
CLONE_RE = re.compile(
    r"git\s+clone\s+"
    r"(?:(?:--\S+\s+(?:\S+\s+)?)*)"  # optional flags
    r"(https?://\S+)"                  # capture URL
)

BRANCH_RE = re.compile(r"--branch\s+(\S+)")


def parse_dockerfile_repos(dockerfile_path: str) -> dict[str, dict]:
    """Parse Dockerfile for git clone URLs. Returns {slug: {url, ref, owner, repo}}."""
    repos = {}
    try:
        with open(dockerfile_path) as f:
            content = f.read()
    except FileNotFoundError:
        return repos

    for line in content.splitlines():
        line = line.strip().rstrip("\\").strip()
        urls = re.findall(r"https?://\S+", line)
        branch_match = BRANCH_RE.search(line)
        ref = branch_match.group(1) if branch_match else None

        for url in urls:
            url = url.rstrip(")")  # strip trailing parens from shell
            # Only handle GitHub URLs
            gh_match = re.match(
                r"https://github\.com/([^/]+)/([^/\s]+?)(?:\.git)?$", url
            )
            if not gh_match:
                continue
            owner = gh_match.group(1)
            repo_name = gh_match.group(2)
            # Derive slug: "client-go--v0.32.0" → "client-go"
            slug = repo_name.rsplit("--", 1)[0] if "--" in repo_name else repo_name
            repos[slug] = {
                "url": url,
                "owner": owner,
                "repo": repo_name,
                "ref": ref or "HEAD",
            }
    return repos


# ── GitHub API file check ────────────────────────────────────────────────────

_cache: dict[str, bool] = {}


def check_file_exists_gh(owner: str, repo: str, ref: str, path: str) -> Optional[bool]:
    """Check if a file exists in a GitHub repo. Returns True/False, or None on error."""
    cache_key = f"{owner}/{repo}@{ref}:{path}"
    if cache_key in _cache:
        return _cache[cache_key]

    try:
        result = subprocess.run(
            ["gh", "api", f"repos/{owner}/{repo}/contents/{path}", "-q", ".type",
             "--header", "Accept: application/vnd.github.v3+json"],
            capture_output=True, text=True, timeout=15,
        )
        if result.returncode != 0 and "rate limit" in result.stderr.lower():
            return None  # Don't cache rate limit errors
        exists = result.returncode == 0 and result.stdout.strip() in ("file", "dir")
        _cache[cache_key] = exists
        return exists
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None


# Batch: use git ls-tree to get all files in one call (much faster for many paths)
_tree_cache: dict[str, set[str]] = {}


def get_repo_tree(owner: str, repo: str, ref: str) -> Optional[set[str]]:
    """Get all file paths in a repo tree. Cached per repo@ref."""
    cache_key = f"{owner}/{repo}@{ref}"
    if cache_key in _tree_cache:
        return _tree_cache[cache_key]

    try:
        # Use recursive tree API — returns all files
        result = subprocess.run(
            ["gh", "api", f"repos/{owner}/{repo}/git/trees/{ref}",
             "-q", ".tree[].path",
             "--paginate",
             "--header", "Accept: application/vnd.github.v3+json",
             "-f", "recursive=1"],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode != 0:
            stderr = result.stderr.lower()
            if "rate limit" in stderr or "403" in stderr:
                # Don't cache rate limit errors — they're transient
                return None
            _tree_cache[cache_key] = None
            return None
        paths = set(result.stdout.strip().splitlines())
        if not paths:
            # Empty tree likely means API error, don't cache
            return None
        _tree_cache[cache_key] = paths
        return paths
    except (subprocess.TimeoutExpired, FileNotFoundError):
        _tree_cache[cache_key] = None
        return None


def check_file_in_tree(
    owner: str, repo: str, ref: str, path: str, use_tree: bool = True
) -> Optional[bool]:
    """Check file existence, preferring tree cache for batch efficiency."""
    if use_tree:
        tree = get_repo_tree(owner, repo, ref)
        if tree is not None:
            if path in tree:
                return True
            # Check if it's a directory prefix (path ends with / or has files under it)
            prefix = path.rstrip("/") + "/"
            if any(p.startswith(prefix) for p in tree):
                return True
            return False
    # Fallback to per-file API
    return check_file_exists_gh(owner, repo, ref, path)


# ── Main logic ───────────────────────────────────────────────────────────────


def _resolve_repo(gt_slug: str, repos: dict) -> Optional[dict]:
    """Resolve a GT repo slug to a Dockerfile repo entry.

    Handles mismatches like:
      GT 'kubernetes-client-go' → Dockerfile 'client-go'
      GT 'stylo'                → Dockerfile 'servo' (via sub-match)
      GT 'prometheus'           → Dockerfile 'prometheus'

    Uses scored matching: longer matches win to avoid ambiguity.
    """
    # Exact match (highest priority)
    if gt_slug in repos:
        return repos[gt_slug]

    # Score-based fuzzy matching: prefer longest matching slug
    candidates = []
    for slug, info in repos.items():
        score = 0
        if slug == gt_slug:
            score = 1000  # exact
        elif gt_slug.endswith(f"-{slug}"):
            # kubernetes-client-go ends with -client-go → matches client-go
            score = 100 + len(slug)
        elif gt_slug.startswith(f"{slug}-"):
            score = 90 + len(slug)
        elif slug.startswith(gt_slug) or gt_slug.startswith(slug):
            score = 50 + min(len(slug), len(gt_slug))
        elif slug in gt_slug:
            score = 30 + len(slug)
        elif gt_slug in slug:
            score = 20 + len(gt_slug)

        if score > 0:
            candidates.append((score, info))

    if candidates:
        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates[0][1]

    return None


def check_task(task_dir: str, verbose: bool = False) -> dict:
    """Check all ground truth paths for a single task."""
    gt_path = os.path.join(task_dir, "tests", "ground_truth.json")
    if not os.path.exists(gt_path):
        return {"task": task_dir, "status": "skip", "reason": "no ground_truth.json"}

    with open(gt_path) as f:
        gt = json.load(f)

    paths = extract_paths(gt)
    if not paths:
        return {"task": task_dir, "status": "skip", "reason": "no file paths in GT"}

    # Find Dockerfile
    dockerfile = os.path.join(task_dir, "environment", "Dockerfile")
    repos = parse_dockerfile_repos(dockerfile)

    if not repos:
        # Check if it's a pre-built image (FROM ghcr.io/...)
        try:
            with open(dockerfile) as f:
                content = f.read()
            if "ghcr.io/" in content or "FROM " in content:
                return {
                    "task": task_dir,
                    "status": "skip",
                    "reason": "pre-built image, no GitHub clone URLs",
                    "paths_count": len(paths),
                }
        except FileNotFoundError:
            pass
        return {
            "task": task_dir,
            "status": "skip",
            "reason": "no Dockerfile or no GitHub repos",
        }

    # Determine which repo each path maps to
    results = {"task": task_dir, "status": "pass", "checked": 0, "missing": [], "skipped": []}

    for repo_slug, fpath in paths:
        if repo_slug:
            # Multi-repo: look up by slug
            repo_info = _resolve_repo(repo_slug, repos)
            if not repo_info:
                results["skipped"].append(
                    {"path": f"{repo_slug}::{fpath}", "reason": f"repo slug '{repo_slug}' not in Dockerfile"}
                )
                continue
        else:
            # Single-repo: use the only repo, or first one
            if len(repos) == 1:
                repo_info = next(iter(repos.values()))
            else:
                # Multiple repos but bare path — can't determine which repo
                results["skipped"].append(
                    {"path": fpath, "reason": "bare path with multiple repos"}
                )
                continue

        exists = check_file_in_tree(
            repo_info["owner"], repo_info["repo"], repo_info["ref"], fpath
        )
        results["checked"] += 1

        if exists is None:
            results["skipped"].append(
                {"path": fpath, "reason": "API error or timeout"}
            )
        elif not exists:
            results["missing"].append({
                "path": fpath,
                "repo": f"{repo_info['owner']}/{repo_info['repo']}",
                "ref": repo_info["ref"],
            })
            results["status"] = "fail"
        elif verbose:
            pass  # Could log pass, but keep output clean

    if results["missing"]:
        results["status"] = "fail"

    return results


def discover_tasks(tasks_dir: str) -> list[str]:
    """Find all task directories under the given path."""
    tasks = []
    # Pattern: benchmarks/csb/<category>/<task-id>/
    for gt in sorted(glob.glob(os.path.join(tasks_dir, "**/tests/ground_truth.json"), recursive=True)):
        task_dir = os.path.dirname(os.path.dirname(gt))
        tasks.append(task_dir)
    return tasks


def main():
    parser = argparse.ArgumentParser(description="Oracle drift detection")
    parser.add_argument(
        "--tasks-dir",
        default="benchmarks/csb",
        help="Root directory to scan for tasks (default: benchmarks/csb)",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Show per-file results")
    parser.add_argument("--json", action="store_true", dest="json_output", help="JSON output")
    parser.add_argument(
        "--skip-api", action="store_true",
        help="Offline mode: only check Dockerfile/GT consistency, skip GitHub API calls",
    )
    parser.add_argument(
        "--limit", type=int, default=0,
        help="Limit number of tasks to check (0 = all)",
    )
    args = parser.parse_args()

    tasks = discover_tasks(args.tasks_dir)
    if args.limit > 0:
        tasks = tasks[: args.limit]

    if not args.json_output:
        print(f"Scanning {len(tasks)} tasks in {args.tasks_dir}...")

    all_results = []
    counters = {"pass": 0, "fail": 0, "skip": 0}

    for i, task_dir in enumerate(tasks):
        task_name = "/".join(task_dir.split("/")[-2:])

        if args.skip_api:
            # Offline mode: just check GT/Dockerfile consistency
            gt_path = os.path.join(task_dir, "tests", "ground_truth.json")
            dockerfile = os.path.join(task_dir, "environment", "Dockerfile")
            if not os.path.exists(gt_path):
                result = {"task": task_name, "status": "skip", "reason": "no GT"}
            else:
                with open(gt_path) as f:
                    gt = json.load(f)
                paths = extract_paths(gt)
                repos = parse_dockerfile_repos(dockerfile) if os.path.exists(dockerfile) else {}
                if not repos:
                    result = {"task": task_name, "status": "skip",
                              "reason": "no GitHub clone URLs in Dockerfile",
                              "paths_count": len(paths)}
                else:
                    # Check slug consistency using _resolve_repo
                    missing_slugs = []
                    for slug, fpath in paths:
                        if slug and not _resolve_repo(slug, repos):
                            missing_slugs.append(f"{slug}::{fpath}")
                    result = {
                        "task": task_name,
                        "status": "fail" if missing_slugs else "pass",
                        "paths_count": len(paths),
                        "repos": list(repos.keys()),
                        "missing_slugs": missing_slugs,
                    }
        else:
            result = check_task(task_dir, verbose=args.verbose)
            result["task"] = task_name

        all_results.append(result)
        counters[result["status"]] += 1

        if not args.json_output:
            status_icon = {"pass": ".", "fail": "F", "skip": "S"}[result["status"]]
            if result["status"] == "fail":
                missing = result.get("missing", result.get("missing_slugs", []))
                print(f"\n{status_icon} {task_name}")
                for m in missing:
                    if isinstance(m, dict):
                        print(f"    MISSING: {m['path']}  (in {m.get('repo', '?')}@{m.get('ref', '?')})")
                    else:
                        print(f"    MISSING SLUG: {m}")
            elif args.verbose:
                print(f"{status_icon} {task_name} ({result.get('checked', 0)} checked)")
            else:
                print(status_icon, end="", flush=True)

    if args.json_output:
        json.dump(
            {"summary": counters, "results": all_results},
            sys.stdout,
            indent=2,
        )
    else:
        print(f"\n\nSummary: {counters['pass']} pass, {counters['fail']} fail, {counters['skip']} skip")
        if counters["fail"] > 0:
            print("\nFailed tasks:")
            for r in all_results:
                if r["status"] == "fail":
                    print(f"  - {r['task']}")

    sys.exit(1 if counters["fail"] > 0 else 0)


if __name__ == "__main__":
    main()
