#!/usr/bin/env python3
"""Add [verification] section with reward_type and description to all task.toml files.

For benchmarks that already have [verification] (PyTorch, CodeReview, K8s Docs,
LargeRepo, LinuxFLBench, TAC): adds reward_type and description fields.

For benchmarks with [verifier] or [evaluation]: appends a new [verification]
section without removing existing sections (Harbor reads those).
"""

import glob
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BENCHMARKS_DIR = PROJECT_ROOT / "benchmarks"

# Reward type and description per benchmark
BENCHMARK_META = {
    "ccb_swebenchpro": ("test_ratio", "Fraction of repository tests passing after agent changes"),
    "ccb_pytorch": ("diff_similarity", "Similarity between agent diff and expected ground-truth diff"),
    "ccb_locobench": ("semantic_similarity", "Semantic similarity of agent output to reference answer"),
    "ccb_k8sdocs": ("checklist", "Weighted checklist of required documentation files and patterns"),
    "ccb_largerepo": ("checklist", "Weighted checklist of required code structure and patterns"),
    "ccb_codereview": ("checklist", "F1 score for defect detection plus fix correctness"),
    "ccb_linuxflbench": ("checklist", "10-point rubric for fault localization accuracy"),
    "ccb_tac": ("checklist", "Task-specific evaluation checklist"),
    "ccb_crossrepo": ("semantic_similarity", "Semantic similarity of content, file references, and patterns"),
    "ccb_dibench": ("binary", "Pass or fail for dependency installation correctness"),
    "ccb_repoqa": ("semantic_similarity", "Correct function retrieval similarity score"),
    "ccb_sweperf": ("test_ratio", "Performance test pass rate after optimization"),
    "ccb_dependeval": ("binary", "Correctness of dependency ordering output"),
}

# Benchmarks that already have [verification] section
HAS_VERIFICATION = {"ccb_pytorch", "ccb_codereview", "ccb_k8sdocs", "ccb_largerepo", "ccb_linuxflbench", "ccb_tac"}
# Benchmarks with [verifier] — keep it, add separate [verification]
HAS_VERIFIER = {"ccb_swebenchpro", "ccb_locobench", "ccb_repoqa", "ccb_dibench", "ccb_crossrepo", "ccb_sweperf"}
# Benchmarks with [evaluation] — keep it, add separate [verification]
HAS_EVALUATION = {"ccb_dependeval"}


def add_fields_to_existing_verification(content: str, reward_type: str, description: str) -> str:
    """Add reward_type and description fields to an existing [verification] section."""
    lines = content.splitlines(keepends=True)
    result = []
    in_verification = False
    fields_added = False

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Detect section headers
        if stripped.startswith("[") and not stripped.startswith("[["):
            if stripped == "[verification]":
                in_verification = True
                result.append(line)
                continue
            elif in_verification and not fields_added:
                # We're leaving [verification] — insert fields before this new section
                result.append(f'reward_type = "{reward_type}"\n')
                result.append(f'description = "{description}"\n')
                fields_added = True
                in_verification = False
                result.append(line)
                continue
            else:
                in_verification = False

        # If we're inside [verification] and see existing reward_type, skip
        if in_verification and stripped.startswith("reward_type"):
            # Already has reward_type — replace it
            result.append(f'reward_type = "{reward_type}"\n')
            continue
        if in_verification and stripped.startswith("description") and "=" in stripped:
            # Already has description — replace it
            result.append(f'description = "{description}"\n')
            continue

        result.append(line)

    # If [verification] was the last section and we haven't added fields yet
    if in_verification and not fields_added:
        result.append(f'reward_type = "{reward_type}"\n')
        result.append(f'description = "{description}"\n')
        fields_added = True

    return "".join(result)


def append_verification_section(content: str, reward_type: str, description: str) -> str:
    """Append a new [verification] section to the TOML content.

    Insert it before [environment] if present, otherwise at end.
    """
    verification_block = (
        f'\n[verification]\n'
        f'reward_type = "{reward_type}"\n'
        f'description = "{description}"\n'
    )

    # Try to insert before [environment] section
    env_match = re.search(r'\n\[environment\]', content)
    if env_match:
        pos = env_match.start()
        return content[:pos] + verification_block + content[pos:]

    # Try to insert before [environment.setup_scripts]
    env_match = re.search(r'\n\[environment\.', content)
    if env_match:
        pos = env_match.start()
        return content[:pos] + verification_block + content[pos:]

    # Append at end
    if not content.endswith("\n"):
        content += "\n"
    return content + verification_block


def process_file(filepath: Path, benchmark: str) -> bool:
    """Process a single task.toml file. Returns True if modified."""
    if benchmark not in BENCHMARK_META:
        print(f"  SKIP {filepath}: unknown benchmark {benchmark}", file=sys.stderr)
        return False

    reward_type, description = BENCHMARK_META[benchmark]
    content = filepath.read_text()

    # Check if already has reward_type in [verification]
    if re.search(r'\[verification\].*?reward_type\s*=', content, re.DOTALL):
        return False  # Already done

    if benchmark in HAS_VERIFICATION:
        new_content = add_fields_to_existing_verification(content, reward_type, description)
    else:
        # Has [verifier] or [evaluation] — append new [verification] section
        new_content = append_verification_section(content, reward_type, description)

    if new_content != content:
        filepath.write_text(new_content)
        return True
    return False


def main():
    # Find all non-template task.toml files
    patterns = [
        str(BENCHMARKS_DIR / "ccb_*" / "*" / "task.toml"),
        str(BENCHMARKS_DIR / "ccb_*" / "tasks" / "*" / "task.toml"),
    ]

    all_files = []
    for pattern in patterns:
        all_files.extend(glob.glob(pattern))

    # Filter out templates
    all_files = [f for f in all_files if "/templates/" not in f]

    modified = 0
    skipped = 0
    errors = 0

    for filepath_str in sorted(all_files):
        filepath = Path(filepath_str)
        # Extract benchmark name from path
        rel = filepath.relative_to(BENCHMARKS_DIR)
        benchmark = rel.parts[0]

        try:
            if process_file(filepath, benchmark):
                modified += 1
            else:
                skipped += 1
        except Exception as e:
            print(f"  ERROR {filepath}: {e}", file=sys.stderr)
            errors += 1

    print(f"Done: {modified} modified, {skipped} skipped (already done), {errors} errors")
    print(f"Total files processed: {modified + skipped + errors}")

    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
