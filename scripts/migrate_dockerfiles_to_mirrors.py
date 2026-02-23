#!/usr/bin/env python3
"""Migrate Dockerfiles to clone from sg-evals mirrors instead of github.com.

Rewrites `git clone` commands in baseline Dockerfiles so both baseline and MCP
configs pull from the same pinned sg-evals mirror repositories. Benefits:
  1. Content consistency: baseline code = same bytes SG indexes for MCP
  2. Faster builds: --depth 1 on single-commit mirrors is much faster
  3. Reproducibility: no dependency on upstream github.com availability

Scope:
  Layer 1 - 14 base_images/Dockerfile.* files
  Layer 2 - ~80 benchmarks/*/environment/Dockerfile files with direct git clones

Not affected (no git clone to rewrite):
  - FROM ccb-repo-* (45 tasks, inherit from base images)
  - FROM ccb-linux-base:* (5 tasks, separate build script)
  - FROM sweap-images / ghcr.io / harbor-* (32 tasks, external pre-built)
  - COPY repo (8 dibench tasks, bundled source)

Usage:
    python3 scripts/migrate_dockerfiles_to_mirrors.py              # dry-run (default)
    python3 scripts/migrate_dockerfiles_to_mirrors.py --execute    # apply changes
    python3 scripts/migrate_dockerfiles_to_mirrors.py --file PATH  # single file
    python3 scripts/migrate_dockerfiles_to_mirrors.py --verbose    # show diffs
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = REPO_ROOT / "configs" / "mirror_creation_manifest.json"
INSTANCE_MAP_PATH = REPO_ROOT / "configs" / "instance_to_mirror.json"

SG_ORG = "sg-evals"
SG_BASE = f"https://github.com/{SG_ORG}"

# ─────────────────────────────────────────────────────────────
# URL aliases: non-GitHub hosts that have sg-evals mirrors
# ─────────────────────────────────────────────────────────────
URL_ALIASES = {
    # go.googlesource.com/X mirrors github.com/golang/X
    "go.googlesource.com/net": "golang/net",
    # No mirror exists for crypto yet
    "go.googlesource.com/crypto": None,
}


# ═════════════════════════════════════════════════════════════
#  MIRROR LOOKUP TABLE
# ═════════════════════════════════════════════════════════════

def build_mirror_lookup() -> dict[tuple[str, str], str]:
    """Build (org_repo, ref) -> mirror_name lookup from all sources.

    Keys are (normalized_org_repo, ref) where ref can be a full commit hash,
    short hash, or tag. Multiple key variants are stored for flexible matching.
    """
    lookup: dict[tuple[str, str], str] = {}

    def add(org_repo: str, ref: str, mirror: str):
        """Add lookup entries for a given upstream + ref -> mirror mapping."""
        org_repo = org_repo.lower().rstrip("/")
        mirror_name = mirror.replace(f"{SG_ORG}/", "")
        # Exact ref
        lookup[(org_repo, ref.lower())] = mirror_name
        # If ref is a long hex hash, also add short prefix entries
        if len(ref) >= 12 and all(c in "0123456789abcdef" for c in ref.lower()):
            for n in (7, 8, 10, 12):
                lookup[(org_repo, ref[:n].lower())] = mirror_name

    # Source 1: mirror_creation_manifest.json
    if MANIFEST_PATH.exists():
        manifest = json.loads(MANIFEST_PATH.read_text())
        for entry in manifest.get("mirrors", []):
            upstream = entry["upstream"].replace("github.com/", "")
            add(upstream, entry["commit"], entry["mirror"])

    # Source 2: instance_to_mirror.json (has additional mirrors)
    # This file has diverse nesting patterns — recursively walk to find
    # all dicts that contain (mirror_name + repo + commit/tag).
    if INSTANCE_MAP_PATH.exists():
        imap = json.loads(INSTANCE_MAP_PATH.read_text())

        def _extract_mirrors(obj: object) -> None:
            """Recursively find mirror entries in any nested structure."""
            if not isinstance(obj, dict):
                return
            # Check if this dict itself is a mirror entry
            mirror_name = obj.get("mirror_name", obj.get("mirror", ""))
            repo = obj.get("repo", obj.get("upstream", ""))
            commit = obj.get("commit", "")
            tag = obj.get("tag", "")
            ref = commit or tag
            if (mirror_name and repo and ref
                    and isinstance(mirror_name, str)
                    and mirror_name.startswith(f"{SG_ORG}/")):
                org_repo = repo.replace("github.com/", "")
                add(org_repo, ref, mirror_name)
                # If both commit and tag exist, also register the tag as lookup key
                if commit and tag:
                    add(org_repo, tag, mirror_name)
            # Recurse into all dict values
            for val in obj.values():
                if isinstance(val, dict):
                    _extract_mirrors(val)

        _extract_mirrors(imap)

    return lookup


def lookup_mirror(lookup: dict, org_repo: str, ref: str) -> str | None:
    """Look up mirror name for a given org/repo + ref.

    Tries exact match, then progressively shorter prefixes.
    """
    org_repo = org_repo.lower().rstrip("/")
    ref_lower = ref.lower()

    # Exact match
    result = lookup.get((org_repo, ref_lower))
    if result:
        return result

    # Try prefix matches for hex hashes
    if len(ref) >= 7 and all(c in "0123456789abcdef" for c in ref_lower):
        for n in (8, 7, 10, 12):
            if n <= len(ref):
                result = lookup.get((org_repo, ref_lower[:n]))
                if result:
                    return result

    return None


# ═════════════════════════════════════════════════════════════
#  DOCKERFILE PARSING
# ═════════════════════════════════════════════════════════════

@dataclass
class CloneOp:
    """A single git clone/fetch operation parsed from a Dockerfile."""
    upstream_url: str       # full URL as written in Dockerfile
    org_repo: str           # normalized: "django/django"
    ref: str                # commit hash or tag
    target_dir: str         # clone destination (".", "repo-name", "/path")
    mirror: str | None      # matched mirror name (without sg-evals/ prefix)
    is_parent: bool = False  # True if ref has ~1 (parent commit)
    has_sparse: bool = False # True if sparse-checkout follows
    has_worktree: bool = False
    has_fallback: bool = False  # True if || fallback pattern
    block_start: int = 0    # first line index in original file
    block_end: int = 0      # last line index (inclusive)
    original_lines: list[str] = field(default_factory=list)


@dataclass
class MigrationPlan:
    """Migration plan for a single Dockerfile."""
    path: Path
    category: str           # "base_image" | "task_clone" | "skip"
    clone_ops: list[CloneOp] = field(default_factory=list)
    flags: list[str] = field(default_factory=list)
    can_auto_migrate: bool = True
    original_content: str = ""
    post_clone_cmds: dict[int, list[str]] = field(default_factory=dict)


def normalize_github_url(url: str) -> str | None:
    """Extract org/repo from a git clone URL. Returns None if not GitHub."""
    # Handle go.googlesource.com aliases
    for alias_url, mapped_repo in URL_ALIASES.items():
        if alias_url in url:
            return mapped_repo  # may be None

    m = re.search(r'github\.com/([^/\s]+/[^/\s]+?)(?:\.git)?(?:\s|$|")', url + " ")
    if m:
        return m.group(1)
    return None


def extract_ref_from_line(line: str) -> str | None:
    """Extract a git ref (commit hash or tag) from a Dockerfile RUN line."""
    # Pattern: git checkout HASH
    m = re.search(r'git\s+checkout\s+(?:--[^\s]+\s+)*([a-fA-F0-9]{7,40}(?:~\d+)?)\b', line)
    if m:
        return m.group(1)
    # Pattern: git checkout TAG (v1.30.0, 3.9.0, curl-8_12_0, etc.)
    m = re.search(r'git\s+checkout\s+(?:--[^\s]+\s+)*(v?[\d][^\s&|\\]*)\b', line)
    if m:
        return m.group(1)
    # Pattern: git fetch ... origin HASH
    m = re.search(r'git\s+fetch\s+[^\n]*?origin\s+([a-fA-F0-9]{7,40})\b', line)
    if m:
        return m.group(1)
    # Pattern: --branch TAG
    m = re.search(r'--branch\s+(\S+)', line)
    if m:
        return m.group(1)
    # Pattern: FETCH_HEAD (used with git fetch, ref is in the fetch command)
    if 'FETCH_HEAD' in line:
        m = re.search(r'git\s+fetch\s+[^\n]*?origin\s+([a-fA-F0-9]{7,40})\b', line)
        if m:
            return m.group(1)
    return None


def extract_clone_target(line: str, org_repo: str) -> str:
    """Extract the clone target directory from a git clone/init line."""
    repo_name = org_repo.split("/")[-1] if org_repo else "repo"

    # Handle git init <path> pattern (used instead of git clone in some tasks)
    m = re.search(r'git\s+init\s+(\S+)', line)
    if m:
        init_target = m.group(1)
        # Skip flags (--bare) and shell operators (&& || | ;)
        if (not init_target.startswith("-")
                and init_target not in ("&&", "||", "|", ";", "\\")):
            return init_target

    # Match: git clone [FLAGS] URL TARGET
    m = re.search(
        r'git\s+clone\s+.*?(?:github\.com|go\.googlesource\.com)/\S+?(?:\.git)?\s+'
        r'(\S+?)(?:\s|$|&&|\\|\|)',
        line
    )
    if m:
        target = m.group(1)
        if not target.startswith("-") and target not in ("&&", "||", "|", ";", "\\"):
            return target

    # Check if clone has ". " indicating current directory
    if re.search(r'\.git\s+\.\s*(?:&&|\\|$)', line) or re.search(r'\.git\s+\.$', line.rstrip()):
        return "."
    if re.search(r'/\S+\s+\.\s*(?:&&|\\|$)', line):
        return "."

    # git init with no path = current directory
    if re.search(r'git\s+init\s*(?:&&|\\|$)', line):
        return "."

    # Default: git clone creates dir named after repo
    return repo_name


def join_continuation_lines(lines: list[str]) -> list[tuple[str, int, int]]:
    """Join backslash-continuation lines into logical lines.

    Returns list of (joined_line, start_idx, end_idx).
    """
    result = []
    i = 0
    while i < len(lines):
        start = i
        parts = [lines[i]]
        while i < len(lines) and lines[i].rstrip().endswith("\\"):
            i += 1
            if i < len(lines):
                parts.append(lines[i])
        joined = " ".join(p.rstrip(" \\") for p in parts)
        result.append((joined, start, i))
        i += 1
    return result


def scan_dockerfile(path: Path, mirror_lookup: dict) -> MigrationPlan:
    """Scan a Dockerfile and build a migration plan."""
    content = path.read_text()
    lines = content.splitlines()
    logical_lines = join_continuation_lines(lines)

    # Determine category
    is_base_image = "base_images" in str(path)
    category = "base_image" if is_base_image else "task_clone"

    plan = MigrationPlan(
        path=path,
        category=category,
        original_content=content,
    )

    for joined, start_idx, end_idx in logical_lines:
        # Skip non-RUN lines and lines without git operations
        stripped = joined.strip()
        if not stripped.startswith("RUN ") and not stripped.startswith("RUN\t"):
            # Also check for git sparse-checkout on its own RUN
            if "git sparse-checkout" in joined:
                # Mark this block for removal
                plan.clone_ops.append(CloneOp(
                    upstream_url="",
                    org_repo="",
                    ref="",
                    target_dir="",
                    mirror=None,
                    has_sparse=True,
                    block_start=start_idx,
                    block_end=end_idx,
                    original_lines=lines[start_idx:end_idx + 1],
                ))
            continue

        # Look for github.com or googlesource.com URLs in git context
        urls_found = re.findall(
            r'(?:https?://)?(?:github\.com|go\.googlesource\.com)/([^\s"]+)',
            joined
        )
        if not urls_found:
            continue

        # Check for patterns we flag but don't auto-migrate
        has_parent = bool(re.search(r'~\d+', joined))
        has_worktree = "git worktree" in joined
        # True fallback: two git clone commands separated by ||
        has_fallback = bool(re.search(r'git\s+clone\s+.*\|\|\s*.*git\s+clone', joined))
        has_sparse = "sparse-checkout" in joined

        # For each URL found, create a clone op
        for url_match in urls_found:
            # Clean up the URL match — use removesuffix, NOT rstrip
            # (rstrip(".git") strips individual chars, eating "flipt" → "flip")
            raw_url = url_match
            if raw_url.endswith(".git"):
                raw_url = raw_url[:-4]
            raw_url = raw_url.rstrip("/")
            parts = raw_url.split("/")
            if len(parts) < 2:
                continue
            org_repo = "/".join(parts[:2])

            # Try URL alias
            full_url_domain = None
            if "go.googlesource.com" in joined:
                repo_name = parts[0] if "go.googlesource.com" in url_match else None
                if repo_name:
                    alias_key = f"go.googlesource.com/{repo_name}"
                    mapped = URL_ALIASES.get(alias_key)
                    if mapped is None:
                        plan.flags.append(
                            f"NO MIRROR: go.googlesource.com/{repo_name} (no sg-evals mirror)"
                        )
                        plan.can_auto_migrate = False
                        continue
                    org_repo = mapped
                    full_url_domain = "go.googlesource.com"

            # Skip if this is already an sg-evals URL
            if org_repo.startswith(f"{SG_ORG}/") or "sg-evals" in org_repo:
                continue

            # Extract the ref
            ref = extract_ref_from_line(joined)
            if not ref:
                plan.flags.append(f"NO REF: could not extract commit/tag for {org_repo}")
                plan.can_auto_migrate = False
                continue

            # Check for parent commit pattern
            is_parent = "~" in ref
            clean_ref = ref.split("~")[0] if is_parent else ref

            # Look up mirror
            mirror = lookup_mirror(mirror_lookup, org_repo, clean_ref)

            # Extract target directory
            target_dir = extract_clone_target(joined, org_repo)

            op = CloneOp(
                upstream_url=f"github.com/{org_repo}" if not full_url_domain else f"{full_url_domain}/{parts[0]}",
                org_repo=org_repo,
                ref=ref,
                target_dir=target_dir,
                mirror=mirror,
                is_parent=is_parent,
                has_sparse=has_sparse,
                has_worktree=has_worktree,
                has_fallback=has_fallback,
                block_start=start_idx,
                block_end=end_idx,
                original_lines=lines[start_idx:end_idx + 1],
            )
            plan.clone_ops.append(op)

            # Flag issues
            if is_parent:
                plan.flags.append(
                    f"PARENT COMMIT: {org_repo}@{ref} - mirror is at {clean_ref}, "
                    f"task needs parent. Needs separate mirror or manual handling."
                )
                plan.can_auto_migrate = False
            if has_worktree:
                plan.flags.append(
                    f"WORKTREE: {org_repo} uses git worktree - needs rewrite to "
                    f"separate clone commands per version."
                )
                plan.can_auto_migrate = False
            if has_fallback:
                plan.flags.append(
                    f"FALLBACK: {org_repo} uses || fallback clone - "
                    f"needs manual simplification to single mirror clone."
                )
                plan.can_auto_migrate = False
            if not mirror:
                plan.flags.append(
                    f"NO MIRROR: {org_repo}@{clean_ref} - no sg-evals mirror found"
                )
                plan.can_auto_migrate = False

    return plan


# ═════════════════════════════════════════════════════════════
#  DOCKERFILE REWRITING
# ═════════════════════════════════════════════════════════════

def generate_clone_cmd(mirror: str, target: str) -> str:
    """Generate the replacement git clone command."""
    return f"git clone --depth 1 {SG_BASE}/{mirror}.git {target}"


def rewrite_base_image(plan: MigrationPlan) -> str | None:
    """Rewrite a base_images/Dockerfile.* file.

    Base images have a consistent pattern:
      RUN git clone --filter=blob:none --no-checkout URL . && \\
          git checkout HASH && \\
          git config ...

    Replaced with:
      RUN git clone --depth 1 MIRROR_URL . && \\
          git config ...
    """
    if not plan.can_auto_migrate:
        return None

    lines = plan.original_content.splitlines()
    result_lines = []
    skip_until = -1

    for i, line in enumerate(lines):
        if i <= skip_until:
            continue

        # Check if this line starts a git clone block
        clone_op = None
        for op in plan.clone_ops:
            if op.block_start == i and op.mirror:
                clone_op = op
                break

        if clone_op is None:
            result_lines.append(line)
            continue

        # Rewrite the clone block
        skip_until = clone_op.block_end

        # Build the new clone command, preserving post-clone commands
        original_block = "\n".join(clone_op.original_lines)

        # Extract git config and other post-clone commands to keep
        keep_cmds = []
        for part in re.split(r'\s*&&\s*', original_block):
            part_clean = re.sub(r'^\s*(?:RUN\s+)?', '', part).strip(" \\\n\t")
            if not part_clean:
                continue
            # Skip git clone, checkout, fetch, sparse-checkout
            if any(part_clean.startswith(cmd) for cmd in [
                "git clone", "git checkout", "git fetch",
                "git sparse-checkout", "cd ",
            ]):
                continue
            # Keep everything else (git config, pip install, etc.)
            if part_clean:
                keep_cmds.append(part_clean)

        new_clone = generate_clone_cmd(clone_op.mirror, clone_op.target_dir)
        if keep_cmds:
            all_cmds = [new_clone] + keep_cmds
            # Format as multi-line with continuation
            formatted = "RUN " + " && \\\n    ".join(all_cmds)
        else:
            formatted = f"RUN {new_clone}"

        result_lines.append(formatted)

    return "\n".join(result_lines) + "\n" if result_lines else None


def rewrite_task_dockerfile(plan: MigrationPlan) -> str | None:
    """Rewrite a task Dockerfile with direct git clone commands.

    Handles multiple clone operations per file (multi-repo tasks).
    """
    if not plan.can_auto_migrate:
        return None

    lines = plan.original_content.splitlines()
    result_lines = []
    skip_until = -1

    # Group clone ops by block range for efficient lookup
    ops_by_start = {}
    for op in plan.clone_ops:
        if op.block_start not in ops_by_start:
            ops_by_start[op.block_start] = []
        ops_by_start[op.block_start].append(op)

    for i, line in enumerate(lines):
        if i <= skip_until:
            continue

        ops = ops_by_start.get(i)
        if ops is None:
            # Check for standalone sparse-checkout blocks to remove
            sparse_op = None
            for op in plan.clone_ops:
                if op.has_sparse and not op.org_repo and op.block_start == i:
                    sparse_op = op
                    break
            if sparse_op:
                skip_until = sparse_op.block_end
                result_lines.append(
                    f"# [migrated] sparse-checkout removed (full tree from mirror)"
                )
                continue

            result_lines.append(line)
            continue

        # Skip the original block
        skip_until = max(op.block_end for op in ops)

        for op in ops:
            if not op.mirror:
                # No mirror — keep original lines
                result_lines.extend(op.original_lines)
                continue

            if op.has_sparse and not op.org_repo:
                # Standalone sparse-checkout block — remove
                result_lines.append(
                    "# [migrated] sparse-checkout removed (full tree from mirror)"
                )
                continue

            # Build the replacement
            original_block = "\n".join(op.original_lines)

            # Extract commands to preserve (git config, pip install, mkdir, etc.)
            keep_cmds = []
            for part in re.split(r'\s*&&\s*', original_block):
                part_clean = re.sub(r'^\s*(?:RUN\s+)?', '', part).strip(" \\\n\t")
                if not part_clean:
                    continue
                # Skip git clone, checkout, fetch, sparse-checkout, cd, init, remote add
                skip_patterns = [
                    "git clone", "git checkout", "git fetch",
                    "git sparse-checkout", "git init", "git remote add",
                    "git worktree",
                ]
                if any(part_clean.startswith(p) for p in skip_patterns):
                    continue
                # Skip cd commands that navigate into the cloned dir
                if re.match(r'^cd\s+\S+\s*$', part_clean):
                    continue
                # Skip rm -rf of temp clones
                if re.match(r'^(?:cd\s+/\S+\s*&&\s*)?rm\s+-rf\s', part_clean):
                    continue
                # Skip git log verification (used to verify upstream checkout)
                if "git log" in part_clean and "grep" in part_clean:
                    continue
                # Skip echo verification messages
                if re.match(r'^echo\s+"(?:Checked out|Pinned to|Failed to verify)', part_clean):
                    continue
                keep_cmds.append(part_clean)

            new_clone = generate_clone_cmd(op.mirror, op.target_dir)

            if keep_cmds:
                all_cmds = [new_clone] + keep_cmds
                formatted = "RUN " + " && \\\n    ".join(all_cmds)
            else:
                formatted = f"RUN {new_clone}"

            result_lines.append(formatted)

    return "\n".join(result_lines) + "\n" if result_lines else None


def rewrite_dockerfile(plan: MigrationPlan) -> str | None:
    """Generate the migrated Dockerfile content."""
    if not plan.can_auto_migrate or not plan.clone_ops:
        return None

    # Filter to ops with mirrors
    migratable_ops = [op for op in plan.clone_ops if op.mirror]
    if not migratable_ops:
        return None

    if plan.category == "base_image":
        return rewrite_base_image(plan)
    else:
        return rewrite_task_dockerfile(plan)


# ═════════════════════════════════════════════════════════════
#  DISCOVERY
# ═════════════════════════════════════════════════════════════

def find_all_dockerfiles() -> list[tuple[Path, str]]:
    """Find all Dockerfiles that may need migration.

    Returns list of (path, category) tuples.
    """
    results = []

    # Layer 1: base images
    base_dir = REPO_ROOT / "base_images"
    if base_dir.exists():
        for df in sorted(base_dir.glob("Dockerfile.*")):
            if df.name.startswith("Dockerfile.") and not df.name.endswith((".md", ".bak")):
                results.append((df, "base_image"))

    # Layer 2: task Dockerfiles with direct git clones
    benchmarks_dir = REPO_ROOT / "benchmarks"
    if benchmarks_dir.exists():
        for df in sorted(benchmarks_dir.glob("*/*/environment/Dockerfile")):
            # Skip sg_only and artifact_only variants
            if df.name != "Dockerfile":
                continue
            # Quick check: does this file contain a github.com git clone?
            content = df.read_text()
            has_github_clone = (
                "github.com" in content
                and ("git clone" in content or "git fetch" in content or "git init" in content)
            )
            has_googlesource = "googlesource.com" in content and "git clone" in content
            if has_github_clone or has_googlesource:
                results.append((df, "task_clone"))

    return results


# ═════════════════════════════════════════════════════════════
#  REPORTING
# ═════════════════════════════════════════════════════════════

def format_diff(original: str, migrated: str, path: Path) -> str:
    """Generate a simple diff showing changes."""
    orig_lines = original.splitlines()
    new_lines = migrated.splitlines()

    diff_parts = [f"--- {path}", f"+++ {path} (migrated)"]

    # Simple line-by-line diff (not a real unified diff, but readable)
    import difflib
    diff = difflib.unified_diff(
        orig_lines, new_lines,
        fromfile=str(path),
        tofile=f"{path} (migrated)",
        lineterm="",
    )
    return "\n".join(diff)


def print_report(plans: list[MigrationPlan], verbose: bool = False):
    """Print the dry-run report."""
    auto = [p for p in plans if p.can_auto_migrate and p.clone_ops]
    manual = [p for p in plans if not p.can_auto_migrate and p.clone_ops]
    no_ops = [p for p in plans if not p.clone_ops]

    # Count clone operations
    total_ops = sum(len(p.clone_ops) for p in plans)
    auto_ops = sum(len(p.clone_ops) for p in auto)
    manual_ops = sum(len(p.clone_ops) for p in manual)
    mirrors_found = sum(
        1 for p in plans for op in p.clone_ops if op.mirror
    )
    mirrors_missing = sum(
        1 for p in plans for op in p.clone_ops
        if not op.mirror and op.org_repo  # exclude sparse-only ops
    )

    print("=" * 70)
    print("  Dockerfile Mirror Migration — Dry Run Report")
    print("=" * 70)
    print()

    # ── Auto-migratable files ──
    print(f"AUTO-MIGRATE ({len(auto)} files, {auto_ops} clone operations):")
    print("-" * 60)
    base_auto = [p for p in auto if p.category == "base_image"]
    task_auto = [p for p in auto if p.category == "task_clone"]

    if base_auto:
        print(f"\n  Layer 1: Base Images ({len(base_auto)} files)")
        for plan in base_auto:
            for op in plan.clone_ops:
                if op.mirror:
                    rel = plan.path.relative_to(REPO_ROOT)
                    print(f"    {rel}")
                    print(f"      {op.org_repo}@{op.ref[:12]}")
                    print(f"      -> {SG_ORG}/{op.mirror}")

    if task_auto:
        print(f"\n  Layer 2: Task Dockerfiles ({len(task_auto)} files)")
        for plan in task_auto:
            rel = plan.path.relative_to(REPO_ROOT)
            task_id = plan.path.parent.parent.name
            ops_desc = []
            for op in plan.clone_ops:
                if op.mirror and op.org_repo:
                    ops_desc.append(f"{op.org_repo}@{op.ref[:12]} -> {SG_ORG}/{op.mirror}")
            if ops_desc:
                print(f"    {task_id}")
                for desc in ops_desc:
                    print(f"      {desc}")

    # ── Manual review needed ──
    if manual:
        print(f"\nMANUAL REVIEW ({len(manual)} files):")
        print("-" * 60)
        for plan in manual:
            rel = plan.path.relative_to(REPO_ROOT)
            task_id = plan.path.parent.parent.name if plan.category != "base_image" else plan.path.name
            print(f"  {task_id}  ({rel})")
            for flag in plan.flags:
                print(f"    ! {flag}")

    # ── Verbose diffs ──
    if verbose:
        print(f"\nDIFFS:")
        print("-" * 60)
        for plan in auto:
            migrated = rewrite_dockerfile(plan)
            if migrated and migrated != plan.original_content:
                diff = format_diff(plan.original_content, migrated, plan.path)
                if diff:
                    print(diff)
                    print()

    # ── Summary ──
    print(f"\nSUMMARY:")
    print("-" * 60)
    print(f"  Files scanned:          {len(plans)}")
    print(f"  Clone operations found: {total_ops}")
    print(f"  Mirrors matched:        {mirrors_found}")
    print(f"  Mirrors missing:        {mirrors_missing}")
    print(f"  Auto-migratable files:  {len(auto)}")
    print(f"    Base images:          {len(base_auto)}")
    print(f"    Task Dockerfiles:     {len(task_auto)}")
    print(f"  Manual review needed:   {len(manual)}")
    if no_ops:
        print(f"  No clone ops (false positive): {len(no_ops)}")

    # List unique mirrors that would be used
    all_mirrors = sorted(set(
        op.mirror for p in plans for op in p.clone_ops if op.mirror
    ))
    print(f"\n  Unique sg-evals mirrors used: {len(all_mirrors)}")

    print()
    if auto and not verbose:
        print("  Run with --verbose to see diffs, or --execute to apply changes.")
    elif auto:
        print("  Run with --execute to apply changes.")


# ═════════════════════════════════════════════════════════════
#  MAIN
# ═════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Migrate Dockerfiles to clone from sg-evals mirrors"
    )
    parser.add_argument(
        "--execute", action="store_true",
        help="Apply the migration (default is dry-run)"
    )
    parser.add_argument(
        "--file", type=Path,
        help="Process a single Dockerfile instead of all"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Show unified diffs for all changes"
    )
    args = parser.parse_args()

    # Build mirror lookup
    print("Building mirror lookup table...", end=" ", flush=True)
    mirror_lookup = build_mirror_lookup()
    print(f"{len(mirror_lookup)} entries")

    # Find Dockerfiles
    if args.file:
        fpath = args.file.resolve()
        if not fpath.exists():
            print(f"ERROR: {args.file} not found", file=sys.stderr)
            sys.exit(1)
        dockerfiles = [(fpath, "base_image" if "base_images" in str(fpath) else "task_clone")]
    else:
        dockerfiles = find_all_dockerfiles()

    print(f"Scanning {len(dockerfiles)} Dockerfiles...")
    print()

    # Scan all Dockerfiles
    plans = []
    for path, category in dockerfiles:
        plan = scan_dockerfile(path, mirror_lookup)
        plans.append(plan)

    if not args.execute:
        # Dry-run: print report
        print_report(plans, verbose=args.verbose)
        return

    # Execute: apply changes
    modified = 0
    skipped = 0
    errors = 0

    for plan in plans:
        if not plan.can_auto_migrate or not plan.clone_ops:
            skipped += 1
            continue

        migrated = rewrite_dockerfile(plan)
        if not migrated or migrated == plan.original_content:
            skipped += 1
            continue

        try:
            plan.path.write_text(migrated)
            modified += 1
            rel = plan.path.relative_to(REPO_ROOT)
            mirrors = [op.mirror for op in plan.clone_ops if op.mirror]
            print(f"  MIGRATED {rel}  ({', '.join(mirrors)})")
        except Exception as e:
            errors += 1
            print(f"  ERROR {plan.path}: {e}")

    print()
    print(f"Migration complete: {modified} files modified, {skipped} skipped, {errors} errors")

    # Also print manual review items
    manual = [p for p in plans if not p.can_auto_migrate and p.clone_ops]
    if manual:
        print(f"\n{len(manual)} files still need manual review:")
        for plan in manual:
            task_id = plan.path.parent.parent.name if plan.category != "base_image" else plan.path.name
            flags = "; ".join(plan.flags)
            print(f"  {task_id}: {flags}")


if __name__ == "__main__":
    main()
