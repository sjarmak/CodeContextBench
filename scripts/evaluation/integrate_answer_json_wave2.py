#!/usr/bin/env python3
"""Wave 2 integration: Add answer.json support to ccb_debug and ccb_test suites.

Categories handled:
  ccb_debug:
    - checklist (6): REPORT_PATH redirect (same as Wave 1)
    - fault-loc (5): analysis → fault_localization_result.json (handled by lib)
    - find-and-prove (9): changes[] → new-file extraction to /workspace/ (handled by lib)

  ccb_test:
    - code-review (8): changes[] → synthetic review.json (handled by lib),
                        replace artifact_verifier_lib.sh sourcing
    - coverage-gap (2): OUTPUT_FILE redirect
    - unit-gen (4): changes[] → new-file extraction (handled by lib)
    - perf (3): changes[] → patch application (handled by lib)
    - TAC (3): external evaluator — skip for now

Each task gets:
1. answer_json_verifier_lib.sh copied to tests/
2. Source block added to test.sh
3. Task-specific redirects for scoring inputs
"""

import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB_SRC = os.path.join(ROOT, "scripts", "answer_json_verifier_lib.sh")

# Source block to insert
SOURCE_BLOCK = """\

# Artifact mode: parse answer.json, extract analysis text, apply diffs
if [ -f /tmp/.artifact_only_mode ] && [ -f /tests/answer_json_verifier_lib.sh ]; then
    source /tests/answer_json_verifier_lib.sh
fi
"""

# Tasks to skip entirely
SKIP_TASKS = {
    # ccb_test TAC tasks: external evaluator (/utils/eval.py), complex integration
    "openhands-search-file-test-001",
    "llamacpp-file-modify-search-001",
    "llamacpp-context-window-search-001",
}

# ── Categorization ──────────────────────────────────────────────────────────

# Debug: checklist tasks (REPORT_PATH → ANALYSIS_TEXT_FILE copy)
DEBUG_CHECKLIST = {
    "prometheus-queue-reshard-debug-001",
    "envoy-duplicate-headers-debug-001",
    "istio-xds-destrul-debug-001",
    "terraform-phantom-update-debug-001",
    "django-admins-migration-audit-001",
    "grafana-table-panel-regression-001",
}

# Debug: fault-loc tasks (lib auto-generates fault_localization_result.json)
DEBUG_FAULTLOC = {
    "linux-acpi-backlight-fault-001",
    "linux-nfs-inode-revalidate-fault-001",
    "linux-ssd-trim-timeout-fault-001",
    "linux-hda-intel-suspend-fault-001",
    "linux-iwlwifi-subdevice-fault-001",
}

# Debug: find-and-prove tasks (lib extracts new-file diffs to /workspace/)
DEBUG_FINDPROVE = {
    "ansible-galaxy-tar-regression-prove-001",
    "flipt-auth-cookie-regression-prove-001",
    "qutebrowser-hsv-color-regression-prove-001",
    "qutebrowser-adblock-cache-regression-prove-001",
    "qutebrowser-darkmode-threshold-regression-prove-001",
    "qutebrowser-url-regression-prove-001",
    "teleport-ssh-regression-prove-001",
    "tutanota-search-regression-prove-001",
    "vuls-oval-regression-prove-001",
}

# Test: code-review tasks (lib generates synthetic review.json)
TEST_CODEREVIEW = {
    "calcom-code-review-001",
    "envoy-code-review-001",
    "curl-security-review-001",
    "ghost-code-review-001",
    "kafka-security-review-001",
    "terraform-code-review-001",
    "vscode-code-review-001",
    "aspnetcore-code-review-001",
}

# Test: coverage-gap tasks (OUTPUT_FILE → ANALYSIS_TEXT_FILE copy)
TEST_COVERAGE = {
    "test-coverage-gap-001",
    "test-coverage-gap-002",
}

# Test: unit-gen tasks (lib extracts test files to /workspace/)
TEST_UNITGEN = {
    "test-unitgen-go-001",
    "test-unitgen-py-001",
    "test-integration-001",
    "test-integration-002",
}

# Test: perf tasks (lib applies patches to verify_repo)
TEST_PERF = {
    "sklearn-kmeans-perf-001",
    "numpy-array-sum-perf-001",
    "pandas-groupby-perf-001",
}


def find_insertion_point(lines):
    """Find where to insert source block — after sg_only line or after set -e."""
    sg_only_idx = None
    set_e_idx = None

    for i, line in enumerate(lines):
        if "sg_only_mode" in line and "sgonly_verifier_wrapper" in line:
            sg_only_idx = i
        if line.strip() in ("set -e", "set -euo pipefail", "set -uo pipefail"):
            set_e_idx = i

    if sg_only_idx is not None:
        return sg_only_idx + 1
    elif set_e_idx is not None:
        return set_e_idx + 1
    return 2  # fallback


def detect_output_path(content, task_name):
    """Detect expected output path from test.sh for text-based verifiers."""
    # REPORT_PATH pattern
    m = re.search(r'REPORT_PATH="\$\{REPORT_PATH:-([^}]+)\}"', content)
    if m:
        return m.group(1)
    # OUTPUT_FILE pattern
    m = re.search(r'OUTPUT_FILE="([^"]+\.md)"', content)
    if m:
        return m.group(1)
    return None


def build_redirect_block(output_path):
    """Build conditional copy block for text-based redirects."""
    parent_dir = os.path.dirname(output_path)
    mkdir_cmd = ""
    if parent_dir and parent_dir not in ("/workspace", ""):
        mkdir_cmd = f'    mkdir -p "{parent_dir}"\n'

    return (
        f'\n# In artifact mode, populate expected output from answer.json analysis\n'
        f'if [ "${{ARTIFACT_ONLY:-false}}" = "true" ] && [ -f "${{ANALYSIS_TEXT_FILE:-}}" ]; then\n'
        f'{mkdir_cmd}'
        f'    cp "$ANALYSIS_TEXT_FILE" "{output_path}"\n'
        f'    echo "[answer_json] Copied analysis text to {output_path}"\n'
        f'fi\n'
    )


def find_redirect_point(lines, output_path):
    """Find where to insert redirect block — after the output file variable."""
    for i, line in enumerate(lines):
        stripped = line.strip()
        if output_path in stripped:
            # Match variable assignments
            if re.match(r'(REPORT_PATH|OUTPUT_FILE|DOCUMENTATION_FILE|SOLUTION_FILE)=', stripped):
                return i + 1
    # Fallback: after the source block
    for i, line in enumerate(lines):
        if "answer_json_verifier_lib.sh" in line:
            for j in range(i, min(i + 5, len(lines))):
                if lines[j].strip() == "fi":
                    return j + 1
    return None


def integrate_debug_checklist(task_dir, task_name, dry_run=False):
    """Integrate checklist debug task (same pattern as Wave 1)."""
    tests_dir = os.path.join(task_dir, "tests")
    test_sh = os.path.join(tests_dir, "test.sh")

    with open(test_sh) as f:
        content = f.read()

    if "answer_json_verifier_lib.sh" in content:
        return f"SKIP {task_name}: already integrated"

    output_path = detect_output_path(content, task_name)
    if output_path is None:
        return f"SKIP {task_name}: could not detect output path"

    lines = content.split("\n")
    source_idx = find_insertion_point(lines)
    source_lines = SOURCE_BLOCK.strip().split("\n")
    for j, sl in enumerate(source_lines):
        lines.insert(source_idx + j, sl)

    redirect_idx = find_redirect_point(lines, output_path)
    if redirect_idx is None:
        redirect_idx = source_idx + len(source_lines) + 1

    redirect_block = build_redirect_block(output_path)
    redirect_lines = redirect_block.strip().split("\n")
    for j, rl in enumerate(redirect_lines):
        lines.insert(redirect_idx + j, rl)

    if dry_run:
        return f"WOULD modify {task_name} (checklist → {output_path})"

    shutil.copy2(LIB_SRC, os.path.join(tests_dir, "answer_json_verifier_lib.sh"))
    with open(test_sh, "w") as f:
        f.write("\n".join(lines))
    return f"OK {task_name}: integrated (checklist → {output_path})"


def integrate_debug_faultloc(task_dir, task_name, dry_run=False):
    """Integrate fault-loc debug task.

    The lib auto-generates /workspace/fault_localization_result.json from
    analysis fields. We just need to add the source block.
    """
    tests_dir = os.path.join(task_dir, "tests")
    test_sh = os.path.join(tests_dir, "test.sh")

    with open(test_sh) as f:
        content = f.read()

    if "answer_json_verifier_lib.sh" in content:
        return f"SKIP {task_name}: already integrated"

    lines = content.split("\n")
    # Insert source block early — before the fault_localization check
    # Find "set -e" or first non-comment line
    insert_idx = 2  # after shebang + comment
    for i, line in enumerate(lines):
        if line.strip() == "set -e":
            insert_idx = i + 1
            break

    source_lines = SOURCE_BLOCK.strip().split("\n")
    for j, sl in enumerate(source_lines):
        lines.insert(insert_idx + j, sl)

    if dry_run:
        return f"WOULD modify {task_name} (fault-loc)"

    shutil.copy2(LIB_SRC, os.path.join(tests_dir, "answer_json_verifier_lib.sh"))
    with open(test_sh, "w") as f:
        f.write("\n".join(lines))
    return f"OK {task_name}: integrated (fault-loc)"


def integrate_debug_findprove(task_dir, task_name, dry_run=False):
    """Integrate find-and-prove debug task.

    The lib auto-extracts new-file diffs to /workspace/ (e.g., regression_test.py).
    We add the source block before the find_and_prove_verifier.sh sourcing.
    """
    tests_dir = os.path.join(task_dir, "tests")
    test_sh = os.path.join(tests_dir, "test.sh")

    with open(test_sh) as f:
        content = f.read()

    if "answer_json_verifier_lib.sh" in content:
        return f"SKIP {task_name}: already integrated"

    lines = content.split("\n")

    # Find sg_only line or first export line
    insert_idx = None
    for i, line in enumerate(lines):
        if "sg_only_mode" in line and "sgonly_verifier_wrapper" in line:
            insert_idx = i + 1
            break

    if insert_idx is None:
        # Insert after shebang + comments
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and not stripped.startswith("!"):
                insert_idx = i
                break
        if insert_idx is None:
            insert_idx = 2

    source_lines = SOURCE_BLOCK.strip().split("\n")
    for j, sl in enumerate(source_lines):
        lines.insert(insert_idx + j, sl)

    if dry_run:
        return f"WOULD modify {task_name} (find-and-prove)"

    shutil.copy2(LIB_SRC, os.path.join(tests_dir, "answer_json_verifier_lib.sh"))
    with open(test_sh, "w") as f:
        f.write("\n".join(lines))
    return f"OK {task_name}: integrated (find-and-prove)"


def integrate_test_codereview(task_dir, task_name, dry_run=False):
    """Integrate code-review test task.

    These already source artifact_verifier_lib.sh. We add answer_json sourcing
    BEFORE the artifact_verifier_lib.sh line. The lib generates synthetic
    review.json from changes[], so existing F1 scoring works unchanged.
    """
    tests_dir = os.path.join(task_dir, "tests")
    test_sh = os.path.join(tests_dir, "test.sh")

    with open(test_sh) as f:
        content = f.read()

    if "answer_json_verifier_lib.sh" in content:
        return f"SKIP {task_name}: already integrated"

    lines = content.split("\n")

    # Find the artifact_verifier_lib.sh line or sg_only line
    insert_idx = None
    for i, line in enumerate(lines):
        if "artifact_verifier_lib.sh" in line:
            insert_idx = i
            break
    if insert_idx is None:
        for i, line in enumerate(lines):
            if "sg_only_mode" in line:
                insert_idx = i + 1
                break
    if insert_idx is None:
        insert_idx = find_insertion_point(lines)

    source_lines = SOURCE_BLOCK.strip().split("\n")
    for j, sl in enumerate(source_lines):
        lines.insert(insert_idx + j, sl)

    if dry_run:
        return f"WOULD modify {task_name} (code-review)"

    shutil.copy2(LIB_SRC, os.path.join(tests_dir, "answer_json_verifier_lib.sh"))
    with open(test_sh, "w") as f:
        f.write("\n".join(lines))
    return f"OK {task_name}: integrated (code-review)"


def integrate_test_coverage(task_dir, task_name, dry_run=False):
    """Integrate coverage-gap test task (OUTPUT_FILE redirect)."""
    tests_dir = os.path.join(task_dir, "tests")
    test_sh = os.path.join(tests_dir, "test.sh")

    with open(test_sh) as f:
        content = f.read()

    if "answer_json_verifier_lib.sh" in content:
        return f"SKIP {task_name}: already integrated"

    output_path = detect_output_path(content, task_name)
    if output_path is None:
        # Coverage tasks use OUTPUT_FILE="/workspace/coverage_analysis.md"
        output_path = "/workspace/coverage_analysis.md"

    lines = content.split("\n")
    source_idx = find_insertion_point(lines)
    source_lines = SOURCE_BLOCK.strip().split("\n")
    for j, sl in enumerate(source_lines):
        lines.insert(source_idx + j, sl)

    redirect_idx = find_redirect_point(lines, output_path)
    if redirect_idx is None:
        redirect_idx = source_idx + len(source_lines) + 1

    redirect_block = build_redirect_block(output_path)
    redirect_lines = redirect_block.strip().split("\n")
    for j, rl in enumerate(redirect_lines):
        lines.insert(redirect_idx + j, rl)

    if dry_run:
        return f"WOULD modify {task_name} (coverage → {output_path})"

    shutil.copy2(LIB_SRC, os.path.join(tests_dir, "answer_json_verifier_lib.sh"))
    with open(test_sh, "w") as f:
        f.write("\n".join(lines))
    return f"OK {task_name}: integrated (coverage → {output_path})"


def integrate_simple_source_only(task_dir, task_name, category, dry_run=False):
    """Integrate task that only needs the source block (lib handles the rest).

    Used for unit-gen (lib extracts test files) and perf (lib applies patches).
    """
    tests_dir = os.path.join(task_dir, "tests")
    test_sh = os.path.join(tests_dir, "test.sh")

    with open(test_sh) as f:
        content = f.read()

    if "answer_json_verifier_lib.sh" in content:
        return f"SKIP {task_name}: already integrated"

    lines = content.split("\n")
    source_idx = find_insertion_point(lines)
    source_lines = SOURCE_BLOCK.strip().split("\n")
    for j, sl in enumerate(source_lines):
        lines.insert(source_idx + j, sl)

    if dry_run:
        return f"WOULD modify {task_name} ({category})"

    shutil.copy2(LIB_SRC, os.path.join(tests_dir, "answer_json_verifier_lib.sh"))
    with open(test_sh, "w") as f:
        f.write("\n".join(lines))
    return f"OK {task_name}: integrated ({category})"


def integrate_task(task_dir, task_name, dry_run=False):
    """Route task to appropriate integration function."""
    if task_name in DEBUG_CHECKLIST:
        return integrate_debug_checklist(task_dir, task_name, dry_run)
    elif task_name in DEBUG_FAULTLOC:
        return integrate_debug_faultloc(task_dir, task_name, dry_run)
    elif task_name in DEBUG_FINDPROVE:
        return integrate_debug_findprove(task_dir, task_name, dry_run)
    elif task_name in TEST_CODEREVIEW:
        return integrate_test_codereview(task_dir, task_name, dry_run)
    elif task_name in TEST_COVERAGE:
        return integrate_test_coverage(task_dir, task_name, dry_run)
    elif task_name in TEST_UNITGEN:
        return integrate_simple_source_only(task_dir, task_name, "unit-gen", dry_run)
    elif task_name in TEST_PERF:
        return integrate_simple_source_only(task_dir, task_name, "perf", dry_run)
    else:
        return f"SKIP {task_name}: uncategorized"


def main():
    dry_run = "--dry-run" in sys.argv

    suites = ["csb_sdlc_debug", "csb_sdlc_test",
              "ccb_debug", "ccb_test"]  # legacy fallbacks
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

            test_sh = os.path.join(task_dir, "tests", "test.sh")
            if not os.path.isfile(test_sh):
                print(f"  SKIP {task_name}: no test.sh")
                results["skip"] += 1
                continue

            try:
                msg = integrate_task(task_dir, task_name, dry_run=dry_run)
                print(f"  {msg}")
                if msg.startswith("OK"):
                    results["ok"] += 1
                elif msg.startswith("SKIP"):
                    results["skip"] += 1
                else:
                    results["error"] += 1
            except Exception as e:
                print(f"  ERROR {task_name}: {e}")
                import traceback
                traceback.print_exc()
                results["error"] += 1

    print(f"\n=== Summary ===")
    print(f"  Integrated: {results['ok']}")
    print(f"  Skipped: {results['skip']}")
    print(f"  Errors: {results['error']}")


if __name__ == "__main__":
    main()
