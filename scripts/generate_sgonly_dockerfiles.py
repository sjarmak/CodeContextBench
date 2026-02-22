#!/usr/bin/env python3
"""Generate Dockerfile.sg_only for all active tasks that don't have one.

Write-only tasks: minimal image with no repo clone.
Build-requiring tasks: original Dockerfile + backup/truncate/marker.

Also injects the verifier wrapper guard into test.sh for build-requiring tasks
and copies sgonly_verifier_wrapper.sh into tests/.

NOTE: This script injects SOURCEGRAPH_REPOS env vars for tasks that have
explicit git clone commands in their Dockerfile (MCP-unique tasks). For SDLC
tasks that use prebuilt images (FROM sweap-images, FROM ccb-linux-base, etc.),
run inject_sg_repo_env.py afterward to add SOURCEGRAPH_REPO_NAME env vars
based on task.toml repo fields and instance_to_mirror.json mappings.

Workflow:
    python3 scripts/generate_sgonly_dockerfiles.py   # create/regenerate Dockerfiles
    python3 scripts/inject_sg_repo_env.py            # add repo env vars for prebuilt-image tasks
"""

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BENCHMARKS = REPO_ROOT / "benchmarks"
WRAPPER_SRC = REPO_ROOT / "scripts" / "sgonly_verifier_wrapper.sh"

# Mapping from upstream GitHub repos (as they appear in Dockerfile git clone URLs)
# to their version-pinned sg-benchmarks mirrors on Sourcegraph.
# Used to inject SOURCEGRAPH_REPOS env var into Dockerfile.sg_only / Dockerfile.artifact_only
# so the agent searches the correct version-pinned mirrors instead of HEAD on public repos.
UPSTREAM_TO_MIRROR = {
    "kubernetes/kubernetes": "sg-benchmarks/kubernetes-kubernetes",
    "etcd-io/etcd": "sg-benchmarks/etcd-io-etcd",
    "grafana/grafana": "sg-benchmarks/grafana",
    "grafana/loki": "sg-benchmarks/grafana-loki",
    "kubernetes/client-go": "sg-benchmarks/kubernetes-client-go",
    "kubernetes/api": "sg-benchmarks/kubernetes-api",
    "scikit-learn/scikit-learn": "sg-benchmarks/scikit-learn",
    "numpy/numpy": "sg-benchmarks/numpy",
    "pandas-dev/pandas": "sg-benchmarks/pandas",
    "scipy/scipy": "sg-benchmarks/scipy",
    "nodejs/node": "sg-benchmarks/nodejs-node",
    "expressjs/express": "sg-benchmarks/expressjs-express",
    "prometheus/prometheus": "sg-benchmarks/prometheus",
}


def extract_mirror_repos(dockerfile_text: str) -> list:
    """Extract upstream repos from git clone commands and map to sg-benchmarks mirrors.

    Parses 'git clone ... https://github.com/{org}/{repo}' lines from the baseline
    Dockerfile to determine which repos are used, then maps each to its sg-benchmarks
    mirror name. Also handles repos already cloned from sg-benchmarks directly.
    """
    mirrors = []
    for line in dockerfile_text.splitlines():
        # Match: git clone ... https://github.com/{org}/{repo}[.git] ...
        match = re.search(r'github\.com/([^/\s]+/[^/\s]+?)(?:\.git)?\s', line)
        if not match:
            # Also try URL at end of line (no trailing space)
            match = re.search(r'github\.com/([^/\s]+/[^/\s]+?)(?:\.git)?$', line.strip())
        if match:
            upstream = match.group(1)
            mirror = UPSTREAM_TO_MIRROR.get(upstream)
            if mirror:
                mirrors.append(mirror)
            elif upstream.startswith("sg-benchmarks/"):
                # Already an sg-benchmarks repo — pass through
                mirrors.append(upstream)
    return sorted(set(mirrors))

GUARD_LINE = '[ -f /tmp/.sg_only_mode ] && [ -f /tests/sgonly_verifier_wrapper.sh ] && source /tests/sgonly_verifier_wrapper.sh'
GUARD_COMMENT = '# sg_only_env: restore full repo before verification (no-op for regular runs)'

# Source file extensions to truncate — must cover ALL readable code/config/doc
# formats so the agent cannot extract information from local files.
TRUNCATE_EXTENSIONS = (
    # Python
    '*.py', '*.pyx', '*.pyi',
    # JavaScript / TypeScript
    '*.js', '*.ts', '*.jsx', '*.tsx', '*.mjs', '*.cjs', '*.mts', '*.cts',
    # Go
    '*.go',
    # Java / JVM
    '*.java', '*.kt', '*.scala', '*.groovy', '*.clj',
    # C / C++ (including .cc used by Envoy, gRPC, Chromium, etc.)
    '*.c', '*.cc', '*.cpp', '*.cxx', '*.h', '*.hh', '*.hpp', '*.hxx',
    # Rust
    '*.rs',
    # Ruby
    '*.rb',
    # C# / .NET
    '*.cs', '*.fs',
    # Swift / Objective-C
    '*.swift', '*.m', '*.mm',
    # Web frameworks
    '*.vue', '*.svelte',
    # Shell
    '*.sh', '*.bash', '*.zsh',
    # Lua
    '*.lua',
    # Protobuf / gRPC / IDL
    '*.proto', '*.thrift', '*.avsc', '*.fbs',
    # Config / data (often contains structural info agents can exploit)
    '*.yaml', '*.yml', '*.toml', '*.json', '*.xml', '*.ini', '*.cfg',
    # Documentation (agents can extract architecture info)
    '*.md', '*.rst', '*.txt', '*.adoc',
    # Build files
    '*.cmake', '*.bzl', '*.bazel',
    # SQL
    '*.sql',
    # Erlang / Elixir
    '*.erl', '*.ex', '*.exs',
    # PHP
    '*.php',
    # Perl
    '*.pl', '*.pm',
    # R
    '*.r', '*.R',
)

# Build the find expression for truncation
def truncate_find_expr(workdir, extra_excludes=None):
    names = ' -o '.join(f'-name "{ext}"' for ext in TRUNCATE_EXTENSIONS)
    excludes = '! -path "*/.git/*"'
    if extra_excludes:
        for ex in extra_excludes:
            excludes += f' ! -path "{ex}"'
    return f'find {workdir} -type f \\( {names} \\) {excludes} -exec truncate -s 0 {{}} \\;'


def get_active_task_ids():
    """Get set of active task IDs from on-disk benchmarks, TASK_CATALOG.md, and swebenchpro MANIFEST."""
    tasks = {}  # task_id -> suite_name

    # Primary: scan benchmarks/ directories on disk (catches newly added tasks)
    for suite_dir in sorted(BENCHMARKS.iterdir()):
        if not suite_dir.is_dir() or not suite_dir.name.startswith('ccb_'):
            continue
        suite_name = suite_dir.name
        for task_dir in sorted(suite_dir.iterdir()):
            if not task_dir.is_dir():
                continue
            # Must have environment/Dockerfile to be a real task
            if (task_dir / "environment" / "Dockerfile").exists():
                tasks[task_dir.name] = suite_name
            # Also check tasks/ subdirectory pattern
            if task_dir.name == "tasks":
                for sub in sorted(task_dir.iterdir()):
                    if sub.is_dir() and (sub / "environment" / "Dockerfile").exists():
                        tasks[sub.name] = suite_name

    # SWE-bench Pro from MANIFEST (may have tasks not on disk)
    manifest_path = BENCHMARKS / "ccb_swebenchpro" / "MANIFEST.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        for tid in manifest.get("task_ids", []):
            if tid not in tasks:
                tasks[tid] = "SWE-bench Pro"

    return tasks


def find_task_dir(task_id):
    """Find the task directory on disk for a given task ID."""
    # Direct match: benchmarks/suite/task_id/
    for d in BENCHMARKS.glob(f"*/{task_id}/environment/Dockerfile"):
        return d.parent.parent
    # Tasks subdirectory: benchmarks/suite/tasks/task_id/
    for d in BENCHMARKS.glob(f"*/tasks/{task_id}/environment/Dockerfile"):
        return d.parent.parent
    # SWE-bench Pro uses different naming (__ vs -, case differences)
    for variant in [task_id, task_id.replace("__", "-")]:
        for d in BENCHMARKS.glob(f"*/tasks/{variant}/environment/Dockerfile"):
            return d.parent.parent
        # Case-insensitive fallback
        lower = variant.lower()
        for d in BENCHMARKS.glob("*/tasks/*/environment/Dockerfile"):
            if d.parent.parent.name.lower() == lower:
                return d.parent.parent
    return None


def detect_workdir(dockerfile_text):
    """Detect the WORKDIR from a Dockerfile."""
    workdirs = re.findall(r'^WORKDIR\s+(\S+)', dockerfile_text, re.MULTILINE)
    return workdirs[-1] if workdirs else '/workspace'


def detect_clone_type(dockerfile_text):
    """Determine if a Dockerfile clones a repo and how."""
    # SWE-bench prebuilt images (FROM jefzda/sweap-images:...)
    if 'sweap-images' in dockerfile_text or 'swebench' in dockerfile_text.lower():
        return 'swebench'
    # ccb-linux-base prebuilt images (contain kernel source at /workspace/)
    if re.search(r'^FROM\s+ccb-linux-base:', dockerfile_text, re.MULTILINE):
        return 'ccb_linux_base'
    # Pre-built base images (FROM harbor-... or FROM ghcr.io/theagentcompany/...)
    if 'harbor-' in dockerfile_text or 'theagentcompany' in dockerfile_text:
        return 'prebuilt'
    # Git clone in the Dockerfile
    if re.search(r'git clone', dockerfile_text):
        return 'clone'
    # COPY repo from build context
    if re.search(r'COPY\s+repo\b', dockerfile_text):
        return 'copy_repo'
    return 'none'


def has_defect_injection(task_dir):
    """Check if the task uses inject_defects.sh (code review tasks)."""
    return (task_dir / "environment" / "inject_defects.sh").exists()


def has_sgonly_wrapper(task_dir):
    """Check if the task already has sgonly_verifier_wrapper.sh in tests/.

    Tasks with this wrapper are build-requiring — the wrapper restores /repo_full
    before verification, which requires the Dockerfile.sg_only to set up /repo_full.
    """
    return (task_dir / "tests" / "sgonly_verifier_wrapper.sh").exists()


def is_write_only_verifier(task_dir):
    """Check if the verifier just checks text output (no compilation/tests).

    Tasks with inject_defects.sh or sgonly_verifier_wrapper.sh are NEVER
    write-only — the verifier checks local source files.
    """
    if has_defect_injection(task_dir):
        return False
    if has_sgonly_wrapper(task_dir):
        return False
    test_sh = task_dir / "tests" / "test.sh"
    if not test_sh.exists():
        return False
    content = test_sh.read_text()
    # Write-only indicators: checks for file existence, grep patterns, LLM judge
    write_indicators = [
        'documentation.md', 'analysis.md', 'report.md', 'answer.md',
        'response.md', 'onboarding', 'handoff', 'review.json',
        'llm_judge', 'openai', 'claude', 'gpt-4',
        'checklist', 'EXPECTED_SECTIONS', 'grep -q',
    ]
    build_indicators = [
        'pytest', 'go test', 'go build', 'make', 'npm test',
        'cargo test', 'dotnet build', 'dotnet test', 'javac',
        'gcc ', 'g++ ', 'cmake', 'git apply', 'git diff',
        'patch ', 'PATCH_APPLY', 'regression_test',
    ]
    write_score = sum(1 for w in write_indicators if w in content)
    build_score = sum(1 for b in build_indicators if b in content)
    return write_score > build_score


def generate_write_only(task_dir, dockerfile_text):
    """Generate a write-only Dockerfile.sg_only (no repo clone)."""
    workdir = detect_workdir(dockerfile_text)
    base_image = 'ubuntu:22.04'

    # Try to detect the base image from original
    m = re.match(r'^FROM\s+(\S+)', dockerfile_text, re.MULTILINE)
    if m:
        orig_base = m.group(1)
        # Use a minimal base, not the original (which may have the repo)
        if 'python' in orig_base.lower():
            base_image = 'python:3.11-slim'
        elif 'golang' in orig_base.lower() or 'go:' in orig_base.lower():
            base_image = 'golang:1.23-bookworm'
        elif 'node' in orig_base.lower():
            base_image = 'node:22-bookworm-slim'
        elif 'eclipse-temurin' in orig_base.lower() or 'java' in orig_base.lower():
            base_image = 'eclipse-temurin:17-jdk'
        elif 'gcc' in orig_base.lower():
            base_image = 'gcc:13'
        elif 'debian' in orig_base.lower() or 'bookworm' in orig_base.lower():
            base_image = 'debian:bookworm-slim'

    task_name = task_dir.name

    # Extract mirror repos from baseline Dockerfile for SOURCEGRAPH_REPOS env var
    mirrors = extract_mirror_repos(dockerfile_text)
    sg_repos_env = ""
    if mirrors:
        sg_repos_env = f'ENV SOURCEGRAPH_REPOS="{",".join(mirrors)}"\n'

    return f"""# {task_name} — sg_only_env variant
# No local repo clone — agent uses Sourcegraph MCP exclusively for code access.

FROM {base_image}

ENV DEBIAN_FRONTEND=noninteractive
{sg_repos_env}
RUN apt-get update && apt-get install -y --no-install-recommends \\
    git \\
    ca-certificates \\
    python3 \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

WORKDIR {workdir}

# Empty git repo so agent can commit work
RUN git init && \\
    git config user.email "agent@example.com" && \\
    git config user.name "Agent"

RUN mkdir -p /logs/agent /logs/verifier

# Mark sg_only mode so verifiers can skip local-path checks
RUN touch /tmp/.sg_only_mode

ENTRYPOINT []
"""


def generate_ccb_linux_base_sgonly(task_dir, dockerfile_text):
    """Generate sg_only for ccb-linux-base tasks (kernel source at /workspace/).

    Uses ubuntu:22.04 instead of ccb-linux-base to avoid Harbor test-upload
    failures that occur with ccb-linux-base derived images. In sg_only mode
    the agent uses Sourcegraph MCP for code access — kernel source not needed.
    Installs gawk for verifier scripts that use awk arithmetic.
    """
    task_name = task_dir.name
    return f"""# {task_name} — sg_only_env variant
# No local repo clone — agent uses Sourcegraph MCP exclusively for code access.
# Uses ubuntu:22.04 (replaces ccb-linux-base to fix Harbor test upload).

FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \\
    git \\
    ca-certificates \\
    python3 \\
    gawk \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# Empty git repo so agent can commit work
RUN git init && \\
    git config user.email "agent@example.com" && \\
    git config user.name "Agent"

RUN mkdir -p /logs/agent /logs/verifier

# Mark sg_only mode so verifiers can skip local-path checks
RUN touch /tmp/.sg_only_mode

ENTRYPOINT []
"""


def generate_build_requiring(task_dir, dockerfile_text):
    """Generate a build-requiring Dockerfile.sg_only from the original."""
    workdir = detect_workdir(dockerfile_text)
    clone_type = detect_clone_type(dockerfile_text)
    lines = dockerfile_text.rstrip().split('\n')

    # Determine extra excludes for truncation
    extra_excludes = []
    if 'node_modules' in dockerfile_text or 'npm install' in dockerfile_text:
        extra_excludes.append('*/node_modules/*')

    # For SWE-bench images, the repo is at /app
    if clone_type == 'swebench':
        repo_dir = '/app'
        workdir = '/app'
    elif clone_type == 'prebuilt':
        repo_dir = workdir
    else:
        repo_dir = workdir

    # Extract mirror repos for SOURCEGRAPH_REPOS env var
    mirrors = extract_mirror_repos(dockerfile_text)
    sg_repos_line = ""
    if mirrors:
        sg_repos_line = f'\nENV SOURCEGRAPH_REPOS="{",".join(mirrors)}"'

    # Build the sg_only section to append
    sg_section = f"""
# --- sg_only_env: back up full repo, then truncate source ---
RUN cp -a {repo_dir} /repo_full
RUN {truncate_find_expr(repo_dir, extra_excludes)}
# Recommit truncated state so git history cannot recover full files.
# Without this, `git show HEAD:<file>` or `git checkout HEAD -- <file>`
# would bypass truncation by reading from the pre-truncation commit.
RUN cd {repo_dir} && git add -A && git commit -m "sg_only truncation" --allow-empty --quiet
RUN touch /tmp/.sg_only_mode && echo '{repo_dir}' > /tmp/.sg_only_workdir{sg_repos_line}
"""

    # Find insertion point: before the last ENTRYPOINT/CMD or at the end
    insert_idx = len(lines)
    for i in range(len(lines) - 1, -1, -1):
        stripped = lines[i].strip()
        if stripped.startswith('ENTRYPOINT') or stripped.startswith('CMD'):
            insert_idx = i
            break

    # Build output
    task_name = task_dir.name
    header = f"# {task_name} — sg_only_env variant\n"
    header += "# Source files truncated so agent must use Sourcegraph MCP for code access.\n"
    header += "# Verifier wrapper restores full repo before running tests.\n\n"

    body_lines = lines[:insert_idx]
    tail_lines = lines[insert_idx:]

    result = header + '\n'.join(body_lines) + '\n' + sg_section
    if tail_lines:
        result += '\n'.join(tail_lines) + '\n'
    else:
        result += f'\nWORKDIR {workdir}\n\nENTRYPOINT []\n'

    return result


def generate_artifact_only_mcp(task_dir, dockerfile_text):
    """Generate a Dockerfile.artifact_only for MCP-unique tasks.

    Identical to the write-only sg_only variant but uses .artifact_only_mode marker
    instead of .sg_only_mode. These are used by the artifact_full config where the
    agent produces answer.json instead of editing source files.
    """
    workdir = detect_workdir(dockerfile_text)
    base_image = 'ubuntu:22.04'

    m = re.match(r'^FROM\s+(\S+)', dockerfile_text, re.MULTILINE)
    if m:
        orig_base = m.group(1)
        if 'python' in orig_base.lower():
            base_image = 'python:3.11-slim'
        elif 'golang' in orig_base.lower() or 'go:' in orig_base.lower():
            base_image = 'golang:1.23-bookworm'
        elif 'node' in orig_base.lower():
            base_image = 'node:22-bookworm-slim'

    task_name = task_dir.name
    mirrors = extract_mirror_repos(dockerfile_text)
    sg_repos_env = ""
    if mirrors:
        sg_repos_env = f'ENV SOURCEGRAPH_REPOS="{",".join(mirrors)}"\n'

    return f"""# {task_name} — artifact_only variant
# No local repo clone — agent uses Sourcegraph MCP exclusively for code access.
# Agent produces answer.json artifact; verifier scores the artifact.

FROM {base_image}

ENV DEBIAN_FRONTEND=noninteractive
{sg_repos_env}
RUN apt-get update && apt-get install -y --no-install-recommends \\
    git \\
    ca-certificates \\
    python3 \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

WORKDIR {workdir}

# Empty workspace — agent discovers code via MCP tools only
RUN git init && \\
    git config user.email "agent@example.com" && \\
    git config user.name "Agent" && \\
    git config --global safe.directory '*'

# Create log directories
RUN mkdir -p /logs/agent /logs/verifier

# Mark artifact-only mode — verifiers and eval scripts check this flag
RUN touch /tmp/.artifact_only_mode

ENTRYPOINT []
"""


def inject_test_guard(task_dir):
    """Add the verifier wrapper guard to test.sh if not already present."""
    test_sh = task_dir / "tests" / "test.sh"
    if not test_sh.exists():
        return False

    content = test_sh.read_text()
    if 'sg_only_mode' in content:
        return False  # Already has guard

    lines = content.split('\n')

    # Find insertion point: after shebang and initial comments
    insert_idx = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('#!') or stripped.startswith('#') or stripped == '':
            insert_idx = i + 1
        else:
            break
    # But also look for 'set -e' which should come before the guard
    for i, line in enumerate(lines):
        if line.strip() == 'set -e':
            insert_idx = i + 1
            break

    guard_block = f'\n{GUARD_COMMENT}\n{GUARD_LINE}\n'
    lines.insert(insert_idx, guard_block)
    test_sh.write_text('\n'.join(lines))
    return True


def copy_wrapper(task_dir):
    """Copy sgonly_verifier_wrapper.sh to the task's tests/ directory."""
    tests_dir = task_dir / "tests"
    if not tests_dir.exists():
        return False
    dest = tests_dir / "sgonly_verifier_wrapper.sh"
    if dest.exists():
        return False
    if WRAPPER_SRC.exists():
        dest.write_text(WRAPPER_SRC.read_text())
        dest.chmod(0o755)
        return True
    return False


def main():
    dry_run = '--dry-run' in sys.argv
    verbose = '--verbose' in sys.argv or '-v' in sys.argv

    active_tasks = get_active_task_ids()
    print(f"Active tasks: {len(active_tasks)}")

    generated = 0
    skipped = 0
    guards_added = 0
    wrappers_copied = 0
    artifact_generated = 0
    errors = []
    write_only_count = 0
    build_count = 0

    for task_id, suite in sorted(active_tasks.items(), key=lambda x: (x[1], x[0])):
        task_dir = find_task_dir(task_id)
        if task_dir is None:
            if verbose:
                print(f"  SKIP {task_id}: not found on disk")
            continue

        env_dir = task_dir / "environment"
        dockerfile = env_dir / "Dockerfile"
        sgonly = env_dir / "Dockerfile.sg_only"
        artifact_only = env_dir / "Dockerfile.artifact_only"

        if sgonly.exists():
            skipped += 1
            # Even if sg_only exists, check if artifact_only needs generation
            # for MCP-unique suites (ccb_mcp_*)
            if suite.startswith("ccb_mcp") and not artifact_only.exists() and dockerfile.exists():
                try:
                    dockerfile_text = dockerfile.read_text()
                    art_content = generate_artifact_only_mcp(task_dir, dockerfile_text)
                    if not dry_run:
                        artifact_only.write_text(art_content)
                        artifact_generated += 1
                        if verbose:
                            print(f"  GENERATED {task_id} (artifact_only)")
                    else:
                        print(f"  {'ARTIFACT-ONLY':>18} {suite:<25} {task_id}")
                except Exception as e:
                    errors.append((task_id, f"artifact_only: {e}"))
            continue

        if not dockerfile.exists():
            if verbose:
                print(f"  SKIP {task_id}: no Dockerfile")
            continue

        dockerfile_text = dockerfile.read_text()
        clone_type = detect_clone_type(dockerfile_text)
        # ccb-linux-base images need special handling: use same base but remove kernel source
        is_linux_base = (clone_type == 'ccb_linux_base')
        # Write-only if: no repo in baseline, OR verifier only checks output
        # (doc-gen, analysis tasks). Write-only gives the agent an empty
        # workspace so it must use MCP — no confusing truncated file trees.
        write_only = (not is_linux_base) and ((clone_type == 'none') or is_write_only_verifier(task_dir))

        try:
            if is_linux_base:
                # ccb-linux-base has Claude Code pre-installed; remove kernel source for sg_only
                content = generate_ccb_linux_base_sgonly(task_dir, dockerfile_text)
                write_only_count += 1
                label = 'linux-base-sgonly'
            elif write_only:
                # No local code needed: minimal image, empty workspace
                content = generate_write_only(task_dir, dockerfile_text)
                write_only_count += 1
                label = 'write-only'
            else:
                # Verifier needs local code (compilation, test execution):
                # keep repo but truncate source files
                content = generate_build_requiring(task_dir, dockerfile_text)
                build_count += 1
                label = 'build-req'

            if dry_run:
                print(f"  {label.upper():>18} {suite:<25} {task_id}")
            else:
                sgonly.write_text(content)
                generated += 1
                if verbose:
                    print(f"  GENERATED {task_id} ({label})")

                # For build-requiring tasks, add verifier guard and wrapper
                if not write_only and not is_linux_base:
                    if inject_test_guard(task_dir):
                        guards_added += 1
                    if copy_wrapper(task_dir):
                        wrappers_copied += 1

            # For MCP-unique suites, also generate Dockerfile.artifact_only
            if suite.startswith("ccb_mcp") and not artifact_only.exists():
                art_content = generate_artifact_only_mcp(task_dir, dockerfile_text)
                if dry_run:
                    print(f"  {'ARTIFACT-ONLY':>18} {suite:<25} {task_id}")
                else:
                    artifact_only.write_text(art_content)
                    artifact_generated += 1
                    if verbose:
                        print(f"  GENERATED {task_id} (artifact_only)")

        except Exception as e:
            errors.append((task_id, str(e)))
            print(f"  ERROR {task_id}: {e}")

    print(f"\n{'DRY RUN - ' if dry_run else ''}Summary:")
    print(f"  Already had sg_only: {skipped}")
    print(f"  Generated sg_only: {generated} ({write_only_count} write-only, {build_count} build-requiring)")
    print(f"  Generated artifact_only: {artifact_generated}")
    print(f"  test.sh guards added: {guards_added}")
    print(f"  Wrappers copied: {wrappers_copied}")
    if errors:
        print(f"  Errors: {len(errors)}")
        for tid, err in errors:
            print(f"    {tid}: {err}")


if __name__ == '__main__':
    main()
