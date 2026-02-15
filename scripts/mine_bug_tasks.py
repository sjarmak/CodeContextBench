#!/usr/bin/env python3
"""Mine candidate bug investigation tasks from GitHub closed issues.

Queries the GitHub API for closed issues labeled 'bug' that have linked
merged PRs touching multiple files across multiple directories. Outputs
JSON candidates suitable for ccb_largerepo bug_investigation task scaffolding.

Usage:
    python3 scripts/mine_bug_tasks.py --repo django/django --min-files 5 --max-files 20
    python3 scripts/mine_bug_tasks.py --repo kubernetes/kubernetes --limit 10

Requires GITHUB_TOKEN env var for authenticated requests (higher rate limits).
Uses only stdlib — no external packages.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

GITHUB_API = "https://api.github.com"
PER_PAGE = 100  # max for GitHub API
DEFAULT_MIN_FILES = 5
DEFAULT_MAX_FILES = 30
DEFAULT_LIMIT = 20
RATE_LIMIT_SLEEP = 60  # seconds to wait on rate limit


# ---------------------------------------------------------------------------
# GitHub API helpers
# ---------------------------------------------------------------------------


def _build_headers() -> dict[str, str]:
    """Build HTTP headers, including auth token if available."""
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "CodeContextBench-mine-bug-tasks/1.0",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _api_get(url: str, headers: dict[str, str]) -> tuple[Any, dict[str, str]]:
    """Make a GET request to the GitHub API with rate-limit handling.

    Returns (parsed_json, response_headers).
    """
    req = urllib.request.Request(url, headers=headers)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req) as resp:
                resp_headers = {k.lower(): v for k, v in resp.getheaders()}
                body = json.loads(resp.read().decode())
                return body, resp_headers
        except urllib.error.HTTPError as e:
            if e.code == 403:
                # Check for rate limiting
                retry_after = e.headers.get("Retry-After")
                remaining = e.headers.get("X-RateLimit-Remaining", "?")
                if retry_after or remaining == "0":
                    wait = int(retry_after) if retry_after else RATE_LIMIT_SLEEP
                    print(
                        f"Rate limited. Waiting {wait}s... (attempt {attempt + 1}/3)",
                        file=sys.stderr,
                    )
                    time.sleep(wait)
                    continue
            if e.code == 422:
                # Unprocessable — usually means search query issue
                return [], {}
            raise
    raise RuntimeError(f"Failed after 3 attempts: {url}")


def _get_next_page_url(resp_headers: dict[str, str]) -> str | None:
    """Parse Link header for next page URL."""
    link = resp_headers.get("link", "")
    for part in link.split(","):
        if 'rel="next"' in part:
            url = part.split(";")[0].strip().strip("<>")
            return url
    return None


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------


def fetch_closed_bug_items(
    repo: str, headers: dict[str, str], max_pages: int = 10
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Fetch closed items labeled 'bug' from a repo.

    Returns (issues, prs) — issues are items without a pull_request key,
    PRs are items with one. Many repos label PRs directly with 'bug'.
    """
    issues: list[dict[str, Any]] = []
    prs: list[dict[str, Any]] = []
    url: str | None = (
        f"{GITHUB_API}/repos/{repo}/issues"
        f"?labels=bug&state=closed&sort=updated&direction=desc"
        f"&per_page={PER_PAGE}"
    )
    page = 0
    while url and page < max_pages:
        page += 1
        print(f"  Fetching issues page {page}...", file=sys.stderr)
        data, resp_headers = _api_get(url, headers)
        if not data:
            break
        for item in data:
            if "pull_request" in item:
                prs.append(item)
            else:
                issues.append(item)
        url = _get_next_page_url(resp_headers)
    return issues, prs


def find_linked_pr(
    repo: str, issue_number: int, headers: dict[str, str]
) -> dict[str, Any] | None:
    """Find a merged PR linked to an issue via timeline events."""
    url = (
        f"{GITHUB_API}/repos/{repo}/issues/{issue_number}/timeline"
        f"?per_page={PER_PAGE}"
    )
    try:
        events, _ = _api_get(url, headers)
    except Exception:
        return None

    if not isinstance(events, list):
        return None

    for event in events:
        if event.get("event") == "cross-referenced":
            source = event.get("source", {}).get("issue", {})
            pr = source.get("pull_request", {})
            if pr.get("merged_at"):
                # This is a merged PR that references this issue
                pr_number = source.get("number")
                if pr_number:
                    return _fetch_pr_details(repo, pr_number, headers)

        # Also check for "connected" events (newer GitHub linking)
        if event.get("event") == "connected":
            # Connected events don't include PR details directly,
            # but the commit may reference a PR
            pass

    # Fallback: search for PRs that mention the issue number
    return _search_linked_pr(repo, issue_number, headers)


def _fetch_pr_details(
    repo: str, pr_number: int, headers: dict[str, str]
) -> dict[str, Any] | None:
    """Fetch PR details including merge status."""
    url = f"{GITHUB_API}/repos/{repo}/pulls/{pr_number}"
    try:
        pr, _ = _api_get(url, headers)
        if pr.get("merged_at"):
            return pr
    except Exception:
        pass
    return None


def _search_linked_pr(
    repo: str, issue_number: int, headers: dict[str, str]
) -> dict[str, Any] | None:
    """Search for merged PRs that reference an issue number."""
    query = f"repo:{repo} is:pr is:merged {issue_number}"
    url = (
        f"{GITHUB_API}/search/issues"
        f"?q={urllib.request.quote(query)}&per_page=5&sort=updated"
    )
    try:
        result, _ = _api_get(url, headers)
        items = result.get("items", [])
        for item in items:
            # Verify it actually mentions the issue
            body = (item.get("body") or "").lower()
            title = (item.get("title") or "").lower()
            ref = f"#{issue_number}"
            if ref in body or ref in title or str(issue_number) in title:
                pr_number = item.get("number")
                if pr_number:
                    return _fetch_pr_details(repo, pr_number, headers)
    except Exception:
        pass
    return None


def get_pr_files(
    repo: str, pr_number: int, headers: dict[str, str]
) -> list[dict[str, Any]]:
    """Get the list of files changed in a PR."""
    files: list[dict[str, Any]] = []
    url: str | None = (
        f"{GITHUB_API}/repos/{repo}/pulls/{pr_number}/files"
        f"?per_page={PER_PAGE}"
    )
    while url:
        data, resp_headers = _api_get(url, headers)
        if not data:
            break
        files.extend(data)
        url = _get_next_page_url(resp_headers)
    return files


def compute_directory_spread(file_paths: list[str]) -> int:
    """Count unique top-level directories across file paths."""
    dirs: set[str] = set()
    for path in file_paths:
        parts = path.split("/")
        if len(parts) >= 2:
            dirs.add(parts[0])
        else:
            dirs.add(".")
    return len(dirs)


def _check_pr_candidate(
    repo: str,
    pr_number: int,
    description: str,
    issue_url: str,
    pr_url: str,
    min_files: int,
    max_files: int,
    headers: dict[str, str],
) -> dict[str, Any] | None:
    """Check if a PR meets file count and directory spread criteria."""
    files = get_pr_files(repo, pr_number, headers)
    file_paths = [f["filename"] for f in files]
    file_count = len(file_paths)

    if file_count < min_files or file_count > max_files:
        return None

    dir_spread = compute_directory_spread(file_paths)
    if dir_spread < 2:
        return None

    return {
        "issue_url": issue_url,
        "pr_url": pr_url,
        "files_changed": file_paths,
        "file_count": file_count,
        "directory_spread": dir_spread,
        "description": description,
    }


def mine_candidates(
    repo: str,
    min_files: int,
    max_files: int,
    limit: int,
) -> list[dict[str, Any]]:
    """Mine bug task candidates from a GitHub repo.

    Returns a list of candidate dicts with issue/PR metadata and file lists.
    Handles two patterns:
      1. Issues labeled 'bug' with linked merged PRs
      2. PRs directly labeled 'bug' that are merged
    """
    headers = _build_headers()
    candidates: list[dict[str, Any]] = []

    print(f"Mining bug tasks from {repo}...", file=sys.stderr)
    issues, bug_prs = fetch_closed_bug_items(repo, headers)
    print(
        f"  Found {len(issues)} closed bug issues, {len(bug_prs)} closed bug PRs",
        file=sys.stderr,
    )

    # First: process PRs directly labeled 'bug' (more common pattern)
    for pr_item in bug_prs:
        if len(candidates) >= limit:
            break

        pr_number = pr_item["number"]
        pr_meta = pr_item.get("pull_request", {})

        # Check if merged (the issues endpoint includes merged_at in pull_request)
        if not pr_meta.get("merged_at"):
            # Need to fetch full PR details to check
            pr_detail = _fetch_pr_details(repo, pr_number, headers)
            if not pr_detail:
                continue
        print(
            f"  Checking bug PR #{pr_number}: {pr_item.get('title', '')[:60]}...",
            file=sys.stderr,
        )

        candidate = _check_pr_candidate(
            repo=repo,
            pr_number=pr_number,
            description=pr_item.get("title", ""),
            issue_url=pr_item["html_url"],
            pr_url=pr_item["html_url"],
            min_files=min_files,
            max_files=max_files,
            headers=headers,
        )
        if candidate:
            candidates.append(candidate)
            print(
                f"    -> Candidate! {candidate['file_count']} files, "
                f"{candidate['directory_spread']} dirs",
                file=sys.stderr,
            )

    # Second: process issues and find linked PRs
    for issue in issues:
        if len(candidates) >= limit:
            break

        issue_number = issue["number"]
        print(
            f"  Checking issue #{issue_number}: {issue.get('title', '')[:60]}...",
            file=sys.stderr,
        )

        pr = find_linked_pr(repo, issue_number, headers)
        if not pr:
            continue

        candidate = _check_pr_candidate(
            repo=repo,
            pr_number=pr["number"],
            description=issue.get("title", ""),
            issue_url=issue["html_url"],
            pr_url=pr["html_url"],
            min_files=min_files,
            max_files=max_files,
            headers=headers,
        )
        if candidate:
            candidates.append(candidate)
            print(
                f"    -> Candidate! {candidate['file_count']} files, "
                f"{candidate['directory_spread']} dirs",
                file=sys.stderr,
            )

    return candidates


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Mine candidate bug investigation tasks from GitHub repos.",
    )
    parser.add_argument(
        "--repo",
        required=True,
        help="GitHub repo (e.g., django/django)",
    )
    parser.add_argument(
        "--min-files",
        type=int,
        default=DEFAULT_MIN_FILES,
        help=f"Minimum files changed in PR (default: {DEFAULT_MIN_FILES})",
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=DEFAULT_MAX_FILES,
        help=f"Maximum files changed in PR (default: {DEFAULT_MAX_FILES})",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_LIMIT,
        help=f"Max candidates to return (default: {DEFAULT_LIMIT})",
    )

    args = parser.parse_args()

    candidates = mine_candidates(
        repo=args.repo,
        min_files=args.min_files,
        max_files=args.max_files,
        limit=args.limit,
    )

    json.dump(candidates, sys.stdout, indent=2)
    print(file=sys.stdout)  # trailing newline

    print(f"\nFound {len(candidates)} candidates", file=sys.stderr)


if __name__ == "__main__":
    main()
