#!/usr/bin/env python3
"""Build file manifests for benchmark tasks using GitHub tree API.

Generates per-task repo_manifest.json containing the complete file tree
at the pinned commit. Used by the symbol hallucination detector to
distinguish real vs hallucinated file paths.

Usage:
    python3 scripts/build_repo_manifests.py                    # all tasks
    python3 scripts/build_repo_manifests.py --missing-only     # skip existing
    python3 scripts/build_repo_manifests.py --suite csb_org_onboarding
    python3 scripts/build_repo_manifests.py --task ccx-onboard-search-213
    python3 scripts/build_repo_manifests.py --dry-run          # preview only
"""

import argparse
import json
import logging
import re
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parent.parent
BENCHMARKS_DIRS = [
    REPO_ROOT / "benchmarks" / "csb",
    REPO_ROOT / "benchmarks" / "csb_org_onboarding",
]

# Repo cache: sg-evals/repo--commit -> file tree
_repo_cache: dict[str, list[str]] = {}

# Rate limit tracking
_api_calls = 0
_api_calls_since_sleep = 0


def _gh_api(endpoint: str, max_retries: int = 3) -> dict:
    """Call GitHub API via gh CLI with retry."""
    global _api_calls, _api_calls_since_sleep
    for attempt in range(max_retries):
        _api_calls += 1
        _api_calls_since_sleep += 1
        # Gentle rate limiting: pause every 30 calls
        if _api_calls_since_sleep >= 30:
            log.debug("Rate limit pause (1s after 30 calls)")
            time.sleep(1)
            _api_calls_since_sleep = 0
        try:
            result = subprocess.run(
                ["gh", "api", endpoint],
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.returncode == 0:
                return json.loads(result.stdout)
            if "rate limit" in result.stderr.lower() or "403" in result.stderr:
                wait = 2 ** (attempt + 1)
                log.warning(f"Rate limited, waiting {wait}s (attempt {attempt+1})")
                time.sleep(wait)
                continue
            if "404" in result.stderr or "Not Found" in result.stderr:
                return {"error": "not_found", "message": result.stderr.strip()}
            log.error(f"gh api failed: {result.stderr.strip()}")
        except subprocess.TimeoutExpired:
            log.warning(f"API timeout on {endpoint}")
        except json.JSONDecodeError:
            log.warning(f"Invalid JSON from {endpoint}")
    return {"error": "max_retries", "message": f"Failed after {max_retries} attempts"}


def get_file_tree(repo_slug: str) -> list[str]:
    """Get recursive file tree for a repo via GitHub API.

    Args:
        repo_slug: e.g. "sg-evals/envoy--v1.33.0"

    Returns:
        List of file paths (blobs only, no trees/dirs).
    """
    if repo_slug in _repo_cache:
        return _repo_cache[repo_slug]

    endpoint = f"repos/{repo_slug}/git/trees/HEAD?recursive=1"
    data = _gh_api(endpoint)

    if "error" in data:
        log.warning(f"Cannot fetch tree for {repo_slug}: {data.get('message', '')}")
        _repo_cache[repo_slug] = []
        return []

    if data.get("truncated"):
        log.warning(f"Tree truncated for {repo_slug} — file list may be incomplete")

    files = [
        item["path"]
        for item in data.get("tree", [])
        if item.get("type") == "blob"
    ]
    _repo_cache[repo_slug] = files
    log.info(f"  {repo_slug}: {len(files)} files")
    return files


def extract_repos_from_dockerfile(dockerfile_path: Path) -> list[dict]:
    """Extract repo slugs and workspace paths from Dockerfile git clone commands.

    Returns list of {slug, workspace_path, clone_url}.
    """
    if not dockerfile_path.is_file():
        return []

    content = dockerfile_path.read_text()
    repos = []

    # Pattern: git clone ... https://github.com/sg-evals/REPO.git [path]
    for m in re.finditer(
        r"git\s+clone\s+.*?https://github\.com/(sg-evals/[^\s.]+?)(?:\.git)?\s+(\S+)",
        content,
    ):
        slug = m.group(1)
        ws_path = m.group(2) if m.group(2) else "/workspace"
        # Clean trailing slashes, pipes, parens, etc
        ws_path = ws_path.rstrip("\\|&;)(")
        repos.append({"slug": slug, "workspace_path": ws_path, "clone_url": m.group(0)})

    # Also try non-sg-evals repos
    for m in re.finditer(
        r"git\s+clone\s+.*?https://github\.com/(?!sg-evals/)([^\s.]+?)(?:\.git)?\s+(\S+)",
        content,
    ):
        slug = m.group(1)
        ws_path = m.group(2) if m.group(2) else "/workspace"
        ws_path = ws_path.rstrip("\\|&;)(")
        repos.append({"slug": slug, "workspace_path": ws_path, "clone_url": m.group(0)})

    # Deduplicate by slug
    seen_slugs = set()
    unique_repos = []
    for r in repos:
        if r["slug"] not in seen_slugs:
            seen_slugs.add(r["slug"])
            unique_repos.append(r)

    return unique_repos


def extract_symbols_from_filenames(files: list[str], language: str) -> list[dict]:
    """Extract likely symbols from file paths (module names, package names).

    This is a lightweight extraction — not parsing source code.
    """
    symbols = []
    seen = set()

    for f in files:
        stem = Path(f).stem
        suffix = Path(f).suffix

        # Skip test files, vendor, generated
        if any(
            skip in f
            for skip in ("/vendor/", "/node_modules/", "/third_party/", "/.git/", "/testdata/")
        ):
            continue

        # Extract module/package names from source files
        if suffix in (".go", ".py", ".java", ".ts", ".js", ".rs", ".cpp", ".c", ".h"):
            # Package/module name from directory
            parts = Path(f).parts
            if len(parts) >= 2:
                pkg = parts[-2]
                if pkg not in seen and not pkg.startswith("."):
                    seen.add(pkg)
                    symbols.append({
                        "symbol": pkg,
                        "kind": "package",
                        "file": f,
                    })

            # File stem as a potential type/module name
            if stem not in seen and not stem.startswith("_") and stem != "index":
                seen.add(stem)
                symbols.append({
                    "symbol": stem,
                    "kind": "module",
                    "file": f,
                })

    return symbols


def detect_language(files: list[str]) -> str:
    """Detect dominant language from file extensions."""
    ext_counts: dict[str, int] = defaultdict(int)
    for f in files:
        suffix = Path(f).suffix
        if suffix:
            ext_counts[suffix] += 1

    lang_map = {
        ".go": "go", ".py": "python", ".java": "java",
        ".ts": "typescript", ".js": "javascript", ".rs": "rust",
        ".cpp": "cpp", ".c": "c", ".rb": "ruby",
    }

    best_ext = max(ext_counts, key=ext_counts.get, default="")
    return lang_map.get(best_ext, "unknown")


def build_manifest_for_task(task_dir: Path, dry_run: bool = False) -> dict | None:
    """Build repo manifest for a single task.

    Returns manifest dict or None if no repos found.
    """
    task_name = task_dir.name

    # Find Dockerfile
    dockerfile = task_dir / "environment" / "Dockerfile"
    if not dockerfile.is_file():
        # Try alternate locations
        for alt in ["environment/Dockerfile.baseline", "Dockerfile"]:
            alt_path = task_dir / alt
            if alt_path.is_file():
                dockerfile = alt_path
                break
        else:
            log.debug(f"  {task_name}: no Dockerfile found")
            return None

    repos = extract_repos_from_dockerfile(dockerfile)
    if not repos:
        log.debug(f"  {task_name}: no repos in Dockerfile")
        return None

    if dry_run:
        log.info(f"  {task_name}: would fetch {len(repos)} repo(s): {[r['slug'] for r in repos]}")
        return {"task": task_name, "repos": [r["slug"] for r in repos], "dry_run": True}

    manifest = {
        "task_id": task_name,
        "repos": [],
        "total_files": 0,
    }

    for repo_info in repos:
        slug = repo_info["slug"]
        files = get_file_tree(slug)
        if not files:
            continue

        language = detect_language(files)
        symbols = extract_symbols_from_filenames(files, language)

        repo_manifest = {
            "repo": slug,
            "workspace_path": repo_info["workspace_path"],
            "file_count": len(files),
            "language": language,
            "files": files,
            "filename_symbols": symbols[:500],  # Cap to avoid huge files
        }
        manifest["repos"].append(repo_manifest)
        manifest["total_files"] += len(files)

    if not manifest["repos"]:
        return None

    return manifest


def discover_tasks(
    suite_filter: str | None = None,
    task_filter: str | None = None,
) -> list[Path]:
    """Find all task directories matching filters."""
    tasks = []
    for bench_root in BENCHMARKS_DIRS:
        if not bench_root.is_dir():
            continue
        for suite_dir in sorted(bench_root.iterdir()):
            if not suite_dir.is_dir():
                continue
            if suite_filter and suite_filter not in suite_dir.name:
                continue
            for task_dir in sorted(suite_dir.iterdir()):
                if not task_dir.is_dir():
                    continue
                if task_filter and task_filter != task_dir.name:
                    continue
                if (task_dir / "task.toml").is_file():
                    tasks.append(task_dir)
    return tasks


def main():
    parser = argparse.ArgumentParser(description="Build repo file manifests for benchmark tasks")
    parser.add_argument("--suite", help="Filter to specific suite")
    parser.add_argument("--task", help="Filter to specific task")
    parser.add_argument("--missing-only", action="store_true", help="Skip tasks with existing manifests")
    parser.add_argument("--dry-run", action="store_true", help="Preview without fetching")
    parser.add_argument("--output-dir", help="Override output location (default: per-task tests/)")
    args = parser.parse_args()

    tasks = discover_tasks(suite_filter=args.suite, task_filter=args.task)
    log.info(f"Found {len(tasks)} tasks")

    if args.missing_only:
        tasks = [
            t for t in tasks
            if not (t / "tests" / "repo_manifest.json").is_file()
        ]
        log.info(f"  {len(tasks)} missing manifests")

    stats = {"total": len(tasks), "built": 0, "skipped": 0, "failed": 0}

    for i, task_dir in enumerate(tasks):
        task_name = task_dir.name
        log.info(f"[{i+1}/{len(tasks)}] {task_name}")

        manifest = build_manifest_for_task(task_dir, dry_run=args.dry_run)

        if manifest is None:
            stats["skipped"] += 1
            continue

        if args.dry_run:
            stats["built"] += 1
            continue

        # Write manifest
        if args.output_dir:
            out_path = Path(args.output_dir) / f"{task_name}_manifest.json"
        else:
            out_path = task_dir / "tests" / "repo_manifest.json"

        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(manifest, indent=2) + "\n")
        stats["built"] += 1
        log.info(f"  Wrote {out_path.name}: {manifest['total_files']} files across {len(manifest['repos'])} repo(s)")

    log.info(f"\nDone: {stats['built']} built, {stats['skipped']} skipped, {stats['failed']} failed")
    log.info(f"Total GitHub API calls: {_api_calls}")


if __name__ == "__main__":
    main()
