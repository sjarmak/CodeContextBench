#!/usr/bin/env python3
"""Generate instruction_mcp.md files for all benchmark tasks with Dockerfile.sg_only.

Each instruction_mcp.md = V5 MCP preamble (with repo scope filled in) + original
instruction.md content. This captures the exact instruction text the MCP agent
receives at runtime, making it transparent and inspectable.

The V5 preamble template and repo-scope rendering logic are copied from
agents/claude_baseline_agent.py (V5_PREAMBLE_TEMPLATE, lines 109-172, and
_prepare_instruction repo_scope logic, lines 516-569). Keep in sync if the
agent preamble changes.

Usage:
    python3 scripts/generate_instruction_mcp.py [--dry-run] [--task TASK_ID] [--verbose]
"""

import argparse
import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
BENCHMARKS_DIR = REPO_ROOT / "benchmarks"

# ---------------------------------------------------------------------------
# V5 Preamble Template — copied from agents/claude_baseline_agent.py:109-172
# ---------------------------------------------------------------------------
V5_PREAMBLE_TEMPLATE = """\
# IMPORTANT: Source Code Access

**Local source files are not present.** Your workspace does not contain source code. You **MUST** use Sourcegraph MCP tools to discover, read, and understand code before making any changes.

{repo_scope}

## Required Workflow

1. **Search first** — Use MCP tools to find relevant files and understand existing patterns
2. **Read remotely** — Use `sg_read_file` to read full file contents from Sourcegraph
{workflow_tail}

## Tool Selection

| Goal | Tool |
|------|------|
| Exact symbol/string | `sg_keyword_search` |
| Concepts/semantic search | `sg_nls_search` |
| Trace usage/callers | `sg_find_references` |
| See implementation | `sg_go_to_definition` |
| Read full file | `sg_read_file` |
| Browse structure | `sg_list_files` |
| Find repos | `sg_list_repos` |
| Search commits | `sg_commit_search` |
| Track changes | `sg_diff_search` |
| Compare versions | `sg_compare_revisions` |

**Decision logic:**
1. Know the exact symbol? → `sg_keyword_search`
2. Know the concept, not the name? → `sg_nls_search`
3. Need definition of a symbol? → `sg_go_to_definition`
4. Need all callers/references? → `sg_find_references`
5. Need full file content? → `sg_read_file`

## Scoping (Always Do This)

```
repo:^github.com/ORG/REPO$           # Exact repo (preferred)
repo:github.com/ORG/                 # All repos in org
file:.*\\.ts$                         # TypeScript only
file:src/api/                        # Specific directory
```

Start narrow. Expand only if results are empty.

## Efficiency Rules

- Chain searches logically: search → read → references → definition
- Don't re-search for the same pattern; use results from prior calls
- Prefer `sg_keyword_search` over `sg_nls_search` when you have exact terms
- Read 2-3 related files before synthesising, rather than one at a time
- Don't read 20+ remote files without writing code — once you understand the pattern, start implementing

## If Stuck

If MCP search returns no results:
1. Broaden the search query (synonyms, partial identifiers)
2. Try `sg_nls_search` for semantic matching
3. Use `sg_list_files` to browse the directory structure
4. Use `sg_list_repos` to verify the repository name

---

"""

# Workflow tail for direct configs (mcp-remote-direct / sourcegraph_full).
# Matches agents/claude_baseline_agent.py:563-569.
WORKFLOW_TAIL_DIRECT = (
    "3. **Edit locally** — Use Edit, Write, and Bash to "
    "create or modify files in your working directory\n"
    "4. **Verify locally** — Run tests with Bash to check "
    "your changes"
)


def extract_repo_info(dockerfile_path: Path) -> tuple[str | None, list[str] | None]:
    """Extract SOURCEGRAPH_REPO_NAME and/or SOURCEGRAPH_REPOS from a Dockerfile.

    Returns (repo_name, repo_list) where at most one is set.
    """
    text = dockerfile_path.read_text()

    # Multi-repo: SOURCEGRAPH_REPOS (may be quoted or unquoted)
    m = re.search(r'ENV\s+SOURCEGRAPH_REPOS[= ]"?([^"\n]+)"?', text)
    if m:
        repos_str = m.group(1).strip()
        repo_list = [r.strip() for r in repos_str.split(",") if r.strip()]
        if repo_list:
            return None, repo_list

    # Single-repo: SOURCEGRAPH_REPO_NAME
    m = re.search(r'ENV\s+SOURCEGRAPH_REPO_NAME[= ]"?([^"\n]+)"?', text)
    if m:
        return m.group(1).strip(), None

    return None, None


def build_repo_scope(repo_name: str | None, repo_list: list[str] | None) -> str:
    """Build the {repo_scope} text matching claude_baseline_agent.py:516-539."""
    if repo_list:
        # Multi-repo format
        scope_lines = ["**Target Repositories (version-pinned mirrors):**\n"]
        for repo in repo_list:
            # Strip github.com/ prefix if already present, then re-add
            display = repo
            if display.startswith("github.com/"):
                display = display[len("github.com/"):]
            sg_full = f"github.com/{display}"
            scope_lines.append(
                f"- `{sg_full}` — use `repo:^{sg_full}$` filter"
            )
        scope_lines.append("")
        scope_lines.append(
            "Scope ALL keyword_search/nls_search queries to these repos."
        )
        scope_lines.append(
            "Use the repo name as the `repo` parameter for "
            "read_file/go_to_definition/find_references."
        )
        return "\n".join(scope_lines) + "\n"

    if repo_name:
        # Single-repo format — strip github.com/ prefix then re-add
        display = repo_name
        if display.startswith("github.com/"):
            display = display[len("github.com/"):]
        sg_repo_full = f"github.com/{display}"
        return (
            f"**Target Repository:** `{sg_repo_full}`\n"
            f"- Use `repo:^{sg_repo_full}$` filter in keyword_search\n"
            f"- Use `{sg_repo_full}` as the `repo` parameter for "
            f"go_to_definition/find_references/read_file\n"
        )

    # Fallback (shouldn't happen — all Dockerfiles have env vars)
    return (
        "Use `sg_list_repos` to discover available repositories "
        "before searching.\n"
    )


def render_preamble(repo_name: str | None, repo_list: list[str] | None) -> str:
    """Render the full V5 preamble with repo scope and direct workflow tail."""
    repo_scope = build_repo_scope(repo_name, repo_list)
    return V5_PREAMBLE_TEMPLATE.format(
        repo_scope=repo_scope,
        workflow_tail=WORKFLOW_TAIL_DIRECT,
    )


def _sg_display_name(repo_name: str | None, repo_list: list[str] | None) -> str:
    """Return the primary SG display name for use in instruction body rewrites."""
    if repo_name:
        if repo_name.startswith("github.com/"):
            return repo_name[len("github.com/"):]
        return repo_name
    if repo_list:
        return repo_list[0]  # primary repo for multi-repo tasks
    return ""


def rewrite_repo_references(text: str, sg_display: str) -> str:
    """Replace original repo references in instruction body with SG mirror name.

    Only rewrites for sg-evals/* mirrors where the SG name differs from
    what's in the instruction. Detects and replaces these patterns:
      - **Repository**: org/repo (lang, ~NLOC)
      - **Repository:** org/repo
      - **Repo:** `org/repo`
    """
    if not sg_display or not sg_display.startswith("sg-evals/"):
        return text

    sg_full = f"github.com/{sg_display}"

    # Pattern 1: **Repository**: slug or **Repository:** slug  (with or without leading "- ")
    # Captures the repo slug (word/word or just word) after the bold label
    def _replace_repository(m: re.Match) -> str:
        prefix = m.group(1)  # e.g. "- **Repository**: " or "**Repository:** "
        old_slug = m.group(2)  # e.g. "torvalds/linux" or "flipt-io/flipt"
        suffix = m.group(3)  # e.g. " (Python, ~350K LOC)" or ""
        return f"{prefix}{sg_full} (mirror of {old_slug}){suffix}"

    text = re.sub(
        r'(\*\*Repository\*?\*?:?\*?\*?\s*)'  # bold "Repository" with colon variants
        r'([\w.-]+(?:/[\w.-]+)?)'               # repo slug: "org/repo" or "repo"
        r'((?:\s+\([^)]*\))?)',                 # optional parenthetical like " (Java, ~2M LOC)"
        _replace_repository,
        text,
    )

    # Pattern 2: **Repo:** `org/repo`  (backtick-wrapped)
    def _replace_repo_backtick(m: re.Match) -> str:
        prefix = m.group(1)
        old_slug = m.group(2)
        return f"{prefix}`{sg_full}` (mirror of `{old_slug}`)"

    text = re.sub(
        r'(\*\*Repo:\*\*\s*)`([\w.-]+(?:/[\w.-]+)?)`',
        _replace_repo_backtick,
        text,
    )

    return text


def inject_repo_context(text: str, repo_name: str | None, repo_list: list[str] | None) -> str:
    """Inject a Sourcegraph repository context line if the instruction body lacks one.

    ~57 tasks have no structured **Repository:** or **Repo:** line. For these,
    prepend a context block so the agent sees the repo info in the task body,
    not just in the preamble header.
    """
    # Check if the body already has a repo reference
    if re.search(r'\*\*Repo(sitory)?', text):
        return text

    # Build the context line(s)
    if repo_list:
        sg_names = []
        for r in repo_list:
            d = r[len("github.com/"):] if r.startswith("github.com/") else r
            sg_names.append(f"`github.com/{d}`")
        context = f"**Sourcegraph Repositories:** {', '.join(sg_names)}\n\n"
    elif repo_name:
        display = repo_name
        if display.startswith("github.com/"):
            display = display[len("github.com/"):]
        context = f"**Sourcegraph Repository:** `github.com/{display}`\n\n"
    else:
        return text

    return context + text


def find_tasks() -> list[Path]:
    """Find all task directories with both Dockerfile.sg_only and instruction.md."""
    tasks = []
    for suite_dir in sorted(BENCHMARKS_DIR.iterdir()):
        if not suite_dir.is_dir() or suite_dir.name.startswith("."):
            continue
        for task_dir in sorted(suite_dir.iterdir()):
            if not task_dir.is_dir():
                continue
            sg_only = task_dir / "environment" / "Dockerfile.sg_only"
            instruction = task_dir / "instruction.md"
            if sg_only.exists() and instruction.exists():
                tasks.append(task_dir)
    return tasks


def process_task(task_dir: Path, dry_run: bool, verbose: bool) -> str:
    """Generate instruction_mcp.md for a single task.

    Returns: "generated", "skipped", or "error:<msg>"
    """
    sg_only = task_dir / "environment" / "Dockerfile.sg_only"
    instruction = task_dir / "instruction.md"

    repo_name, repo_list = extract_repo_info(sg_only)
    if not repo_name and not repo_list:
        return "error:no SOURCEGRAPH env var found in Dockerfile.sg_only"

    preamble = render_preamble(repo_name, repo_list)
    original = instruction.read_text()

    # Rewrite repo references in instruction body for sg-evals mirrors
    sg_display = _sg_display_name(repo_name, repo_list)
    original = rewrite_repo_references(original, sg_display)

    # Inject repo context line if instruction body lacks a structured reference
    original = inject_repo_context(original, repo_name, repo_list)

    content = preamble + original

    output_path = task_dir / "instruction_mcp.md"
    if dry_run:
        if verbose:
            repo_desc = repo_name or ",".join(repo_list or [])
            print(f"  would write {output_path.relative_to(REPO_ROOT)} (repo: {repo_desc})")
        return "generated"

    output_path.write_text(content)
    if verbose:
        repo_desc = repo_name or ",".join(repo_list or [])
        print(f"  wrote {output_path.relative_to(REPO_ROOT)} (repo: {repo_desc})")
    return "generated"


def main():
    parser = argparse.ArgumentParser(
        description="Generate instruction_mcp.md files for MCP benchmark tasks"
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be generated without writing files")
    parser.add_argument("--task", type=str, default=None,
                        help="Process a single task by ID (e.g. django-select-for-update-fix-001)")
    parser.add_argument("--verbose", action="store_true",
                        help="Print each file as it's processed")
    args = parser.parse_args()

    if args.task:
        # Find the specific task
        matches = list(BENCHMARKS_DIR.glob(f"*/{args.task}"))
        if not matches:
            print(f"ERROR: Task '{args.task}' not found under {BENCHMARKS_DIR}", file=sys.stderr)
            sys.exit(1)
        tasks = [m for m in matches if (m / "environment" / "Dockerfile.sg_only").exists()
                 and (m / "instruction.md").exists()]
        if not tasks:
            print(f"ERROR: Task '{args.task}' has no Dockerfile.sg_only or instruction.md", file=sys.stderr)
            sys.exit(1)
    else:
        tasks = find_tasks()

    generated = 0
    skipped = 0
    errors = []

    mode = "DRY RUN" if args.dry_run else "GENERATING"
    print(f"=== {mode}: instruction_mcp.md for {len(tasks)} tasks ===\n")

    for task_dir in tasks:
        result = process_task(task_dir, args.dry_run, args.verbose)
        if result == "generated":
            generated += 1
        elif result == "skipped":
            skipped += 1
        elif result.startswith("error:"):
            errors.append((task_dir.name, result[6:]))
            print(f"  ERROR: {task_dir.name}: {result[6:]}", file=sys.stderr)

    print(f"\n{'Would generate' if args.dry_run else 'Generated'} {generated} instruction_mcp.md files"
          f" ({skipped} skipped, {len(errors)} errors)")

    if errors:
        print("\nErrors:", file=sys.stderr)
        for task_id, msg in errors:
            print(f"  {task_id}: {msg}", file=sys.stderr)
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
