#!/usr/bin/env python3
"""Batch-customize generated MCP-unique task skeletons.

Adds missing files required by the reference task pattern:
- environment/Dockerfile.artifact_only
- instruction_mcp.md
- tests/test.sh
- tests/sgonly_verifier_wrapper.sh
- Fixes SOURCEGRAPH_REPOS + clone manifest in Dockerfile.sg_only
- Fixes .go template bug in instruction.md for non-Go tasks
"""

import json
import os
import re
import shutil
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# New task IDs to customize (the 20 generated skeletons)
NEW_TASK_IDS = [2, 3, 12, 13, 22, 26, 32, 33, 43, 44, 52, 53, 62, 71, 72, 73, 74, 81, 82, 83]

# Reference task for copying shared files
REFERENCE_TASK = os.path.join(PROJECT_ROOT, "benchmarks/ccb_mcp_crossrepo_tracing/ccx-dep-trace-001")

# Repo set definitions: sg_repos (for artifact_only/MCP search), clone_repos (for sg_only manifest)
REPO_SETS = {
    "apache-kafka-ecosystem": {
        "sg_repos": [
            "sg-benchmarks/kafka--0753c489",
            "sg-benchmarks/flink--0cc95fcc",
            "sg-benchmarks/camel--1006f047",
        ],
        "clone_repos": [
            {"mirror": "sg-benchmarks/kafka--0753c489", "target_dir": "kafka"},
            {"mirror": "sg-benchmarks/flink--0cc95fcc", "target_dir": "flink"},
            {"mirror": "sg-benchmarks/camel--1006f047", "target_dir": "camel"},
        ],
        "language": "Java",
        "file_ext": ".java",
    },
    "envoy-service-mesh": {
        "sg_repos": [
            "sg-benchmarks/envoy--v1.31.2",
            "sg-benchmarks/data-plane-api--84e84367",
            "sg-benchmarks/go-control-plane--71637ad6",
            "sg-benchmarks/grpc--957dba5e",
        ],
        "clone_repos": [
            {"mirror": "sg-benchmarks/envoy--v1.31.2", "target_dir": "envoy"},
            {"mirror": "sg-benchmarks/data-plane-api--84e84367", "target_dir": "data-plane-api"},
            {"mirror": "sg-benchmarks/go-control-plane--71637ad6", "target_dir": "go-control-plane"},
            {"mirror": "sg-benchmarks/grpc--957dba5e", "target_dir": "grpc"},
        ],
        "language": "C++",
        "file_ext": ".cpp",
    },
    "rust-systems": {
        "sg_repos": [
            "sg-benchmarks/rust--01f6ddf7",
            "sg-benchmarks/servo--be6a2f99",
        ],
        "clone_repos": [
            {"mirror": "sg-benchmarks/rust--01f6ddf7", "target_dir": "rust"},
            {"mirror": "sg-benchmarks/servo--be6a2f99", "target_dir": "servo"},
        ],
        "language": "Rust",
        "file_ext": ".rs",
    },
    "kubernetes-ecosystem": {
        # For artifact_only, use the logical SG names (indexed under these names)
        "sg_repos": [
            "sg-benchmarks/kubernetes-kubernetes",
            "sg-benchmarks/kubernetes-client-go",
            "sg-benchmarks/kubernetes-api",
            "sg-benchmarks/etcd-io-etcd",
        ],
        "clone_repos": [
            {"mirror": "sg-benchmarks/kubernetes--v1.32.0", "target_dir": "kubernetes"},
            {"mirror": "sg-benchmarks/client-go--v0.32.0", "target_dir": "client-go"},
            {"mirror": "sg-benchmarks/api--v0.32.0", "target_dir": "api"},
            {"mirror": "sg-benchmarks/etcd-io-etcd", "target_dir": "etcd"},
        ],
        "language": "Go",
        "file_ext": ".go",
    },
}

# Map use_case_id -> task directory and repo_set_id
def load_registry():
    path = os.path.join(PROJECT_ROOT, "configs/use_case_registry.json")
    with open(path) as f:
        data = json.load(f)
    return {uc["use_case_id"]: uc for uc in data["use_cases"]}


def find_task_dir(use_case_id, registry):
    """Find the task directory for a given use case ID."""
    uc = registry[use_case_id]
    suite = uc["mcp_suite"]
    task_id = uc.get("task_id", "")

    # Search benchmarks directory for the task
    benchmarks_dir = os.path.join(PROJECT_ROOT, "benchmarks")
    suite_dir = os.path.join(benchmarks_dir, suite)
    if not os.path.isdir(suite_dir):
        return None

    for entry in os.listdir(suite_dir):
        task_path = os.path.join(suite_dir, entry)
        toml_path = os.path.join(task_path, "task.toml")
        if os.path.isfile(toml_path):
            with open(toml_path) as f:
                content = f.read()
            if f'use_case_id = {use_case_id}' in content:
                return task_path
    return None


def generate_artifact_only_dockerfile(task_dir, sg_repos):
    """Create Dockerfile.artifact_only with SOURCEGRAPH_REPOS env var."""
    task_name = os.path.basename(task_dir)
    repos_str = ",".join(sg_repos)

    content = f"""# {task_name} — artifact_only variant
# No local repo clone — agent uses Sourcegraph MCP exclusively for code access.
# Agent produces answer.json artifact; verifier scores the artifact.

FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV SOURCEGRAPH_REPOS="{repos_str}"

RUN apt-get update && apt-get install -y --no-install-recommends \\
    git \\
    ca-certificates \\
    python3 \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

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
    path = os.path.join(task_dir, "environment", "Dockerfile.artifact_only")
    with open(path, "w") as f:
        f.write(content)
    return path


def update_sg_only_dockerfile(task_dir, sg_repos, clone_repos):
    """Add SOURCEGRAPH_REPOS env var and clone manifest to Dockerfile.sg_only."""
    path = os.path.join(task_dir, "environment", "Dockerfile.sg_only")
    with open(path) as f:
        content = f.read()

    repos_str = ",".join(sg_repos)
    task_name = os.path.basename(task_dir)

    # Build clone manifest as compact JSON
    manifest = {
        "workdir": "/workspace",
        "repos": clone_repos,
    }
    manifest_json = json.dumps(manifest, separators=(",", ":"))

    # Check if SOURCEGRAPH_REPOS already exists
    if "SOURCEGRAPH_REPOS" in content:
        return path  # Already customized

    # Insert SOURCEGRAPH_REPOS after DEBIAN_FRONTEND
    content = content.replace(
        "ENV DEBIAN_FRONTEND=noninteractive",
        f'ENV DEBIAN_FRONTEND=noninteractive\nENV SOURCEGRAPH_REPOS="{repos_str}"',
    )

    # Add clone manifest before ENTRYPOINT
    manifest_line = f"RUN echo '{manifest_json}' > /tmp/.sg_only_clone_manifest.json\n\n"
    content = content.replace("ENTRYPOINT []", manifest_line + "ENTRYPOINT []")

    with open(path, "w") as f:
        f.write(content)
    return path


def create_test_sh(task_dir):
    """Create tests/test.sh (Harbor compatibility wrapper)."""
    content = """#!/bin/bash
# test.sh — Harbor compatibility wrapper
# Harbor requires tests/test.sh for task discovery (TaskPaths.is_valid() check).
# The actual evaluation logic lives in eval.sh (SWE-Factory exit-code-first pattern).

# sg_only_env: restore full repo before verification (no-op for regular runs)
[ -f /tmp/.sg_only_mode ] && [ -f /tests/sgonly_verifier_wrapper.sh ] && source /tests/sgonly_verifier_wrapper.sh

exec bash "$(dirname "$0")/eval.sh" "$@"
"""
    path = os.path.join(task_dir, "tests", "test.sh")
    with open(path, "w") as f:
        f.write(content)
    os.chmod(path, 0o755)
    return path


def copy_sgonly_wrapper(task_dir):
    """Copy sgonly_verifier_wrapper.sh from reference task."""
    src = os.path.join(REFERENCE_TASK, "tests", "sgonly_verifier_wrapper.sh")
    dst = os.path.join(task_dir, "tests", "sgonly_verifier_wrapper.sh")
    shutil.copy2(src, dst)
    os.chmod(dst, 0o755)
    return dst


def generate_instruction_mcp(task_dir, sg_repos, registry_entry):
    """Create instruction_mcp.md with MCP preamble + task content."""
    # Read the task instruction
    instruction_path = os.path.join(task_dir, "instruction.md")
    with open(instruction_path) as f:
        task_content = f.read()

    # Build repo list for MCP header
    repo_lines = []
    for repo in sg_repos:
        repo_lines.append(
            f"- `github.com/{repo}` — use `repo:^github.com/{repo}$` filter"
        )
    repo_list = "\n".join(repo_lines)
    repo_names = ", ".join(f"`github.com/{r}`" for r in sg_repos)

    content = f"""# IMPORTANT: Source Code Access

**Local source files are not present.** Your workspace does not contain source code. You **MUST** use Sourcegraph MCP tools to discover, read, and understand code before making any changes.

**Target Repositories (version-pinned mirrors):**

{repo_list}

Scope ALL keyword_search/nls_search queries to these repos.
Use the repo name as the `repo` parameter for read_file/go_to_definition/find_references.


## Required Workflow

1. **Search first** — Use MCP tools to find relevant files and understand existing patterns
2. **Read remotely** — Use `sg_read_file` to read full file contents from Sourcegraph
3. **Edit locally** — Use Edit, Write, and Bash to create or modify files in your working directory
4. **Verify locally** — Run tests with Bash to check your changes

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
1. Know the exact symbol? -> `sg_keyword_search`
2. Know the concept, not the name? -> `sg_nls_search`
3. Need definition of a symbol? -> `sg_go_to_definition`
4. Need all callers/references? -> `sg_find_references`
5. Need full file content? -> `sg_read_file`

## Scoping (Always Do This)

```
repo:^github.com/ORG/REPO$           # Exact repo (preferred)
repo:github.com/ORG/                 # All repos in org
file:.*\\.ts$                         # TypeScript only
file:src/api/                        # Specific directory
```

Start narrow. Expand only if results are empty.

## Efficiency Rules

- Chain searches logically: search -> read -> references -> definition
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

**Sourcegraph Repositories:** {repo_names}

{task_content}"""

    path = os.path.join(task_dir, "instruction_mcp.md")
    with open(path, "w") as f:
        f.write(content)
    return path


def fix_instruction_template_bugs(task_dir, file_ext, language):
    """Fix template .go extension in instruction.md for non-Go tasks."""
    path = os.path.join(task_dir, "instruction.md")
    with open(path) as f:
        content = f.read()

    original = content

    # Fix .go extension in example JSON
    if file_ext != ".go":
        content = content.replace(
            '"relative/path/to/file.go"',
            f'"relative/path/to/file{file_ext}"',
        )

    if content != original:
        with open(path, "w") as f:
            f.write(content)
        return True
    return False


def main():
    registry = load_registry()
    processed = []
    errors = []

    for uc_id in NEW_TASK_IDS:
        if uc_id not in registry:
            errors.append(f"UC {uc_id}: not found in registry")
            continue

        uc = registry[uc_id]
        repo_set_id = uc.get("repo_set_id", "")

        if repo_set_id not in REPO_SETS:
            errors.append(f"UC {uc_id}: unknown repo_set_id '{repo_set_id}'")
            continue

        task_dir = find_task_dir(uc_id, registry)
        if not task_dir:
            errors.append(f"UC {uc_id}: task directory not found")
            continue

        repo_set = REPO_SETS[repo_set_id]
        sg_repos = repo_set["sg_repos"]
        clone_repos = repo_set["clone_repos"]
        file_ext = repo_set["file_ext"]
        language = repo_set["language"]

        task_name = os.path.basename(task_dir)
        actions = []

        # 1. Create Dockerfile.artifact_only
        artifact_path = os.path.join(task_dir, "environment", "Dockerfile.artifact_only")
        if not os.path.exists(artifact_path):
            generate_artifact_only_dockerfile(task_dir, sg_repos)
            actions.append("created Dockerfile.artifact_only")

        # 2. Update Dockerfile.sg_only with SOURCEGRAPH_REPOS + manifest
        update_sg_only_dockerfile(task_dir, sg_repos, clone_repos)
        actions.append("updated Dockerfile.sg_only")

        # 3. Create test.sh
        test_path = os.path.join(task_dir, "tests", "test.sh")
        if not os.path.exists(test_path):
            create_test_sh(task_dir)
            actions.append("created test.sh")

        # 4. Copy sgonly_verifier_wrapper.sh
        wrapper_path = os.path.join(task_dir, "tests", "sgonly_verifier_wrapper.sh")
        if not os.path.exists(wrapper_path):
            copy_sgonly_wrapper(task_dir)
            actions.append("copied sgonly_verifier_wrapper.sh")

        # 5. Create instruction_mcp.md
        mcp_path = os.path.join(task_dir, "instruction_mcp.md")
        if not os.path.exists(mcp_path):
            generate_instruction_mcp(task_dir, sg_repos, uc)
            actions.append("created instruction_mcp.md")

        # 6. Fix template bugs in instruction.md
        if fix_instruction_template_bugs(task_dir, file_ext, language):
            actions.append(f"fixed .go -> {file_ext} in instruction.md")

        processed.append(f"  {task_name} (UC {uc_id}): {', '.join(actions)}")

    print(f"Customized {len(processed)} tasks:")
    for line in processed:
        print(line)

    if errors:
        print(f"\nErrors ({len(errors)}):")
        for err in errors:
            print(f"  {err}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
