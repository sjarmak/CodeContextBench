#!/usr/bin/env python3
"""Wave 1 integration: Add answer.json support to output-only SDLC suites.

For each task:
1. Copies answer_json_verifier_lib.sh to tests/
2. Adds source block to test.sh (after sg_only line)
3. Adds conditional copy of $ANALYSIS_TEXT_FILE to expected output path

Only modifies text-based verifier tasks (skips JSON-output and git-diff tasks).
"""

import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB_SRC = os.path.join(ROOT, "scripts", "answer_json_verifier_lib.sh")

# Source block to insert
SOURCE_BLOCK = """\

# Artifact mode: parse answer.json, extract analysis text
if [ -f /tmp/.artifact_only_mode ] && [ -f /tests/answer_json_verifier_lib.sh ]; then
    source /tests/answer_json_verifier_lib.sh
fi
"""

# Tasks to skip (JSON-output, git-diff, or special verifiers)
SKIP_TASKS = {
    # Design: structured JSON output
    "etcd-grpc-api-upgrade-001",          # patch.diff
    "django-rate-limit-design-001",       # git diff code changes
    "flipt-protobuf-metadata-design-001", # git diff code changes
    "django-pre-validate-signal-design-001",  # git diff code changes
    "flipt-transitive-deps-001",          # submission.json
    "django-modeladmin-impact-001",       # submission.json
    "k8s-typemeta-dep-chain-001",         # chain.json
    "terraform-provider-iface-sym-001",   # callers.json
    "envoy-routeconfig-dep-chain-001",    # chain.json
    "k8s-sharedinformer-sym-001",         # callers.json
    "envoy-stream-aggregated-sym-001",    # callers.json
    # Understand: git-diff or custom
    "django-template-inherit-recall-001", # git diff code changes
    "django-composite-field-recover-001", # git diff code changes
    "numpy-dtype-localize-001",           # custom semantic matcher
    "k8s-cri-containerd-reason-001",      # flexible file search (REASONING.md)
}


def detect_output_path(test_sh_content, task_name):
    """Detect the expected agent output file path from test.sh content."""
    # Pattern 1: REPORT_PATH="${REPORT_PATH:-/logs/agent/xxx.md}"
    m = re.search(r'REPORT_PATH="\$\{REPORT_PATH:-([^}]+)\}"', test_sh_content)
    if m:
        return m.group(1)

    # Pattern 2: SOLUTION_FILE="/logs/agent/solution.md"
    m = re.search(r'SOLUTION_FILE="([^"]+)"', test_sh_content)
    if m:
        return m.group(1)

    # Pattern 3: DOC="/workspace/documentation.md" or similar
    m = re.search(r'DOC="([^"]+\.md)"', test_sh_content)
    if m:
        return m.group(1)

    # Pattern 4: OUTPUT_FILE="/workspace/xxx.md"
    m = re.search(r'OUTPUT_FILE="([^"]+\.md)"', test_sh_content)
    if m:
        return m.group(1)

    # Pattern 5: DOCUMENTATION_FILE="/workspace/documentation.md"
    m = re.search(r'DOCUMENTATION_FILE="([^"]+)"', test_sh_content)
    if m:
        return m.group(1)

    return None


def build_redirect_block(output_path):
    """Build the conditional copy block for artifact mode."""
    # Ensure parent directory exists for the copy target
    parent_dir = os.path.dirname(output_path)
    mkdir_cmd = ""
    if parent_dir and parent_dir != "/workspace":
        mkdir_cmd = f'    mkdir -p "{parent_dir}"\n'

    return (
        f'\n# In artifact mode, populate expected output from answer.json analysis\n'
        f'if [ "${{ARTIFACT_ONLY:-false}}" = "true" ] && [ -f "${{ANALYSIS_TEXT_FILE:-}}" ]; then\n'
        f'{mkdir_cmd}'
        f'    cp "$ANALYSIS_TEXT_FILE" "{output_path}"\n'
        f'    echo "[answer_json] Copied analysis text to {output_path}"\n'
        f'fi\n'
    )


def find_insertion_point(lines):
    """Find where to insert the source block in test.sh.

    Strategy: insert after the sg_only line, or after 'set -e' if no sg_only.
    """
    sg_only_idx = None
    set_e_idx = None

    for i, line in enumerate(lines):
        if "sg_only_mode" in line and "sgonly_verifier_wrapper" in line:
            sg_only_idx = i
        elif line.strip() == "set -e":
            set_e_idx = i

    if sg_only_idx is not None:
        return sg_only_idx + 1
    elif set_e_idx is not None:
        return set_e_idx + 1
    return 2  # fallback: after shebang + comment


def find_redirect_point(lines, output_path):
    """Find where to insert the redirect block.

    Insert after the variable assignment that sets the output path.
    """
    for i, line in enumerate(lines):
        stripped = line.strip()
        # Match: REPORT_PATH="${REPORT_PATH:-...}"
        if "REPORT_PATH=" in stripped and output_path in stripped:
            return i + 1
        # Match: SOLUTION_FILE="..."
        if "SOLUTION_FILE=" in stripped and output_path in stripped:
            return i + 1
        # Match: DOC="..." or OUTPUT_FILE="..." or DOCUMENTATION_FILE="..."
        if re.match(r'(DOC|OUTPUT_FILE|DOCUMENTATION_FILE)="', stripped) and output_path in stripped:
            return i + 1

    # Fallback: after the source block (which we just inserted)
    for i, line in enumerate(lines):
        if "answer_json_verifier_lib.sh" in line:
            # Find the 'fi' that closes this block
            for j in range(i, min(i + 5, len(lines))):
                if lines[j].strip() == "fi":
                    return j + 1
            return i + 3

    return None


def integrate_task(task_dir, dry_run=False):
    """Add answer.json support to a single task."""
    task_name = os.path.basename(task_dir)
    tests_dir = os.path.join(task_dir, "tests")
    test_sh = os.path.join(tests_dir, "test.sh")

    if not os.path.isfile(test_sh):
        return f"SKIP {task_name}: no test.sh"

    with open(test_sh) as f:
        content = f.read()

    # Already integrated?
    if "answer_json_verifier_lib.sh" in content:
        return f"SKIP {task_name}: already integrated"

    # Detect output path
    output_path = detect_output_path(content, task_name)
    if output_path is None:
        return f"SKIP {task_name}: could not detect output path"

    lines = content.split("\n")

    # Find insertion points
    source_idx = find_insertion_point(lines)
    source_lines = SOURCE_BLOCK.strip().split("\n")

    # Insert source block
    for j, sl in enumerate(source_lines):
        lines.insert(source_idx + j, sl)

    # Find redirect insertion point (after source block insertion)
    redirect_idx = find_redirect_point(lines, output_path)
    if redirect_idx is None:
        # Put redirect right after source block
        redirect_idx = source_idx + len(source_lines) + 1

    redirect_block = build_redirect_block(output_path)
    redirect_lines = redirect_block.strip().split("\n")

    for j, rl in enumerate(redirect_lines):
        lines.insert(redirect_idx + j, rl)

    new_content = "\n".join(lines)

    if dry_run:
        return f"WOULD modify {task_name} (output: {output_path})"

    # Copy library
    lib_dest = os.path.join(tests_dir, "answer_json_verifier_lib.sh")
    shutil.copy2(LIB_SRC, lib_dest)

    # Write modified test.sh
    with open(test_sh, "w") as f:
        f.write(new_content)

    return f"OK {task_name}: integrated (output: {output_path})"


def main():
    dry_run = "--dry-run" in sys.argv

    suites = ["csb_sdlc_design", "csb_sdlc_understand", "csb_sdlc_document",
              "ccb_design", "ccb_understand", "ccb_document"]  # legacy fallbacks
    benchmarks_dir = os.path.join(ROOT, "benchmarks")

    results = {"ok": 0, "skip": 0, "error": 0}

    for suite in suites:
        suite_dir = os.path.join(benchmarks_dir, suite)
        if not os.path.isdir(suite_dir):
            print(f"WARNING: Suite dir not found: {suite_dir}")
            continue

        print(f"\n=== {suite} ===")
        for task_name in sorted(os.listdir(suite_dir)):
            task_dir = os.path.join(suite_dir, task_name)
            if not os.path.isdir(task_dir):
                continue
            if task_name in SKIP_TASKS:
                print(f"  SKIP {task_name} (excluded)")
                results["skip"] += 1
                continue

            try:
                msg = integrate_task(task_dir, dry_run=dry_run)
                print(f"  {msg}")
                if msg.startswith("OK"):
                    results["ok"] += 1
                elif msg.startswith("SKIP"):
                    results["skip"] += 1
                else:
                    results["error"] += 1
            except Exception as e:
                print(f"  ERROR {task_name}: {e}")
                results["error"] += 1

    print(f"\n=== Summary ===")
    print(f"  Integrated: {results['ok']}")
    print(f"  Skipped: {results['skip']}")
    print(f"  Errors: {results['error']}")


if __name__ == "__main__":
    main()
