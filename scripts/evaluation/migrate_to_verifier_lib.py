#!/usr/bin/env python3
"""Migrate test.sh files to use shared verifier_harness.sh.

Analyzes existing test.sh files, extracts the task-specific check section,
and rewrites them to source verifier_harness.sh instead of inline boilerplate.

Usage:
    python3 scripts/migrate_to_verifier_lib.py --dry-run          # preview changes
    python3 scripts/migrate_to_verifier_lib.py --task feature/django-rate-limit-middleware-feat-001
    python3 scripts/migrate_to_verifier_lib.py --all --execute     # migrate all eligible
"""

import argparse
import glob
import os
import re
import sys

# Markers that delimit the end of boilerplate and start of task-specific checks
BOILERPLATE_END_MARKERS = [
    # Early exit blocks — task checks come after these
    r"exit 0\s*\nfi\s*\n",                          # end of artifact_only early exit
    r"echo \"No code changes detected\"",             # no-changes guard
    # Explicit task-section markers
    r"# Check 1",
    r"# ── Checks",
    r"echo \"Running .+ verification",
    r"SCORE_NUMERATOR=0",
]

# Markers for the end of task-specific checks (before finalization)
FINALIZE_MARKERS = [
    r"write_scored_result",
    r"write_validation_result",
    r"dual_score_lib\.sh",
    r"echo \"\$SCORE\".*reward\.txt",
]


def classify_test_sh(content: str) -> dict:
    """Classify a test.sh file's structure."""
    info = {
        "has_verifier_lib": "source /tests/verifier_harness.sh" in content,
        "has_write_scored": "write_scored_result" in content,
        "has_write_validation": "write_validation_result" in content,
        "has_no_changes_guard": "no_changes_guard" in content,
        "has_sg_only": "sg_only_mode" in content,
        "has_artifact": "artifact_only_mode" in content,
        "has_dual_score": "dual_score_lib" in content,
        "total_lines": content.count("\n"),
        "boilerplate_pattern": "unknown",
    }

    # Determine boilerplate pattern
    if info["has_write_scored"] and info["has_no_changes_guard"]:
        info["boilerplate_pattern"] = "full_scored_ncg"
    elif info["has_write_scored"]:
        info["boilerplate_pattern"] = "scored_no_ncg"
    elif info["has_write_validation"]:
        info["boilerplate_pattern"] = "validation_result"
    elif "reward.txt" in content and not info["has_write_scored"]:
        info["boilerplate_pattern"] = "direct_reward"
    else:
        info["boilerplate_pattern"] = "minimal"

    return info


def find_check_section(content: str) -> tuple[int, int, str]:
    """Find the task-specific check section boundaries.

    Returns (start_line, end_line, extracted_checks) or raises ValueError.
    """
    lines = content.splitlines()

    # Find start of checks: look for first "# Check" or score accumulation
    check_start = -1
    for i, line in enumerate(lines):
        stripped = line.strip()
        if any(re.search(marker, stripped) for marker in [
            r"^# Check \d",
            r"^# ── Checks",
            r"^echo \"Running .+ verification",
            r"^SCORE_NUMERATOR=0$",
            r"^SCORE=0$",
        ]):
            # Walk back to include SCORE=0/TOTAL=N declarations
            start = i
            for j in range(max(0, i - 10), i):
                if re.match(r"^(SCORE|TOTAL|SCORE_NUMERATOR)\s*=", lines[j].strip()):
                    start = j
                    break
            check_start = start
            break

    if check_start == -1:
        raise ValueError("Could not find check section start")

    # Find end of checks: look for write_scored_result or finalization
    check_end = len(lines)
    for i in range(check_start, len(lines)):
        stripped = lines[i].strip()
        if any(re.search(marker, stripped) for marker in [
            r"^write_scored_result",
            r"^write_validation_result",
            r"^FINAL_SCORE=",
            r"SCORE=\$\(awk",
            r"SCORE=\$\(python3 -c",
        ]):
            check_end = i
            break

    checks = "\n".join(lines[check_start:check_end])
    return check_start, check_end, checks


def extract_config(content: str) -> dict:
    """Extract configurable values (TOTAL, PASS_THRESHOLD, etc.)."""
    config = {}
    for pattern, key in [
        (r"TOTAL=(\d+)", "total"),
        (r'PASS_THRESHOLD="([0-9.]+)"', "pass_threshold"),
        (r"SCORE_NUMERATOR=0", "weighted"),
    ]:
        m = re.search(pattern, content)
        if m:
            if key == "weighted":
                config["weighted"] = True
            else:
                config[key] = m.group(1)
    return config


def generate_migrated(content: str, task_name: str) -> str:
    """Generate a migrated test.sh using verifier_harness.sh."""
    info = classify_test_sh(content)
    config = extract_config(content)

    # Already migrated
    if info["has_verifier_lib"]:
        return content

    try:
        check_start, check_end, checks = find_check_section(content)
    except ValueError:
        return None  # Can't migrate automatically

    # Extract any comments at the top
    lines = content.splitlines()
    header_lines = []
    for line in lines:
        if line.startswith("#") or line.strip() == "" or line.startswith("set "):
            header_lines.append(line)
        else:
            break

    # Build migrated version
    header = "\n".join(header_lines[:5])  # Keep first few comment lines
    total = config.get("total", "0")
    threshold = config.get("pass_threshold", "0.7")
    is_weighted = config.get("weighted", False)

    # Remove SCORE=0 and TOTAL=N from checks since verifier_finalize handles them
    check_lines = checks.splitlines()
    filtered_checks = []
    for line in check_lines:
        stripped = line.strip()
        if re.match(r"^TOTAL=\d+$", stripped):
            continue
        if stripped == "SCORE=0" or stripped == "SCORE_NUMERATOR=0":
            continue
        filtered_checks.append(line)
    checks_body = "\n".join(filtered_checks).strip()

    if is_weighted:
        finalize = f'verifier_finalize_weighted "$SCORE_NUMERATOR" 100'
        score_init = "SCORE_NUMERATOR=0"
    else:
        finalize = f'verifier_finalize "$SCORE" "$TOTAL"'
        score_init = f"TOTAL={total}\nSCORE=0"

    migrated = f"""{header}
source /tests/verifier_harness.sh
PASS_THRESHOLD="{threshold}"
verifier_init

{score_init}

{checks_body}

{finalize}
"""
    return migrated


def main():
    parser = argparse.ArgumentParser(description="Migrate test.sh to verifier_harness.sh")
    parser.add_argument("--task", help="Migrate a specific task (category/task-id)")
    parser.add_argument("--all", action="store_true", help="Migrate all eligible tasks")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    parser.add_argument("--execute", action="store_true", help="Actually write changes")
    parser.add_argument("--analyze", action="store_true", help="Just analyze, don't migrate")
    parser.add_argument("--tasks-dir", default="benchmarks/csb")
    args = parser.parse_args()

    if args.analyze:
        # Analyze all test.sh files
        patterns = {}
        for f in sorted(glob.glob(os.path.join(args.tasks_dir, "*/*/tests/test.sh"))):
            with open(f) as fh:
                content = fh.read()
            info = classify_test_sh(content)
            pat = info["boilerplate_pattern"]
            patterns.setdefault(pat, []).append(f)

        for pat, files in sorted(patterns.items(), key=lambda x: -len(x[1])):
            print(f"{len(files):3d} tasks: {pat}")
        print(f"\nTotal: {sum(len(v) for v in patterns.values())} test.sh files")
        return

    if args.task:
        test_sh = os.path.join(args.tasks_dir, args.task, "tests", "test.sh")
        files = [test_sh] if os.path.exists(test_sh) else []
    elif args.all:
        files = sorted(glob.glob(os.path.join(args.tasks_dir, "*/*/tests/test.sh")))
    else:
        parser.print_help()
        return

    migrated = 0
    skipped = 0
    for f in files:
        with open(f) as fh:
            content = fh.read()

        info = classify_test_sh(content)
        if info["has_verifier_lib"]:
            skipped += 1
            continue

        result = generate_migrated(content, f)
        if result is None:
            print(f"SKIP (can't auto-migrate): {f}")
            skipped += 1
            continue

        task = "/".join(f.split("/")[-4:-2])
        if args.dry_run or not args.execute:
            print(f"WOULD MIGRATE: {task} ({info['total_lines']} → {result.count(chr(10))} lines)")
            if args.task:
                print("--- MIGRATED VERSION ---")
                print(result)
                print("--- END ---")
        elif args.execute:
            with open(f, "w") as fh:
                fh.write(result)
            print(f"MIGRATED: {task}")
            migrated += 1

    print(f"\nTotal: {migrated} migrated, {skipped} skipped")


if __name__ == "__main__":
    main()
