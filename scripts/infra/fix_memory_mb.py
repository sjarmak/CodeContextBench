#!/usr/bin/env python3
"""Add missing memory_mb field to task.toml files across canonical benchmark suites."""

import os
import re
import glob

BENCHMARKS_DIR = "/home/stephanie_jarmak/CodeScaleBench/benchmarks"

def has_memory_field(content: str) -> bool:
    """Check if any line has memory_mb or memory as a key (not in description text)."""
    for line in content.splitlines():
        stripped = line.strip()
        # Match memory_mb = ... or memory = ... as TOML keys
        if re.match(r'^memory_mb\s*=', stripped):
            return True
        if re.match(r'^memory\s*=', stripped):
            return True
    return False


def get_language(content: str) -> str:
    """Extract language field value from task.toml."""
    for line in content.splitlines():
        m = re.match(r'^language\s*=\s*["\']?(\w+)["\']?', line.strip())
        if m:
            return m.group(1).lower()
    return ""


def is_ts_js(language: str) -> bool:
    return language in ("typescript", "javascript")


def add_memory_mb(content: str, value: int) -> str:
    """Add memory_mb = value to content at the right location."""
    lines = content.splitlines(keepends=True)

    # Strategy: find the best insertion point
    # Priority 1: after timeout_seconds or timeout or time_limit_sec line (top-level or in [task])
    # Priority 2: after language line
    # Priority 3: end of [task] section or before first section

    insert_after = None
    language_line = None
    timeout_line = None

    current_section = None

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Track sections
        section_match = re.match(r'^\[([^\]]+)\]', stripped)
        if section_match:
            current_section = section_match.group(1)
            continue

        # Look for timeout fields (top-level or in [task])
        if current_section in (None, 'task') and re.match(r'^(timeout_seconds|timeout|time_limit_sec)\s*=', stripped):
            timeout_line = i

        # Look for language field
        if re.match(r'^language\s*=', stripped):
            language_line = i

    if timeout_line is not None:
        insert_after = timeout_line
    elif language_line is not None:
        insert_after = language_line
    else:
        # Fallback: insert before first section or at end
        for i, line in enumerate(lines):
            if re.match(r'^\[', line.strip()) and i > 0:
                insert_after = i - 1
                break
        if insert_after is None:
            insert_after = len(lines) - 1

    # Build the new line
    new_line = f"memory_mb = {value}\n"

    # Insert after the chosen line
    lines.insert(insert_after + 1, new_line)

    return "".join(lines)


def main():
    # Find all canonical suite dirs
    suite_dirs = sorted(
        glob.glob(os.path.join(BENCHMARKS_DIR, "csb_sdlc_*"))
        + glob.glob(os.path.join(BENCHMARKS_DIR, "csb_org_*"))
    )

    # Filter to actual directories (not files)
    suite_dirs = [d for d in suite_dirs if os.path.isdir(d)]

    total = 0
    modified = 0
    skipped = 0
    ts_js_count = 0
    other_count = 0

    for suite_dir in suite_dirs:
        task_tomls = glob.glob(os.path.join(suite_dir, "*/task.toml"))
        for toml_path in sorted(task_tomls):
            total += 1

            with open(toml_path, "r") as f:
                content = f.read()

            if has_memory_field(content):
                skipped += 1
                continue

            language = get_language(content)
            if is_ts_js(language):
                value = 8192
                ts_js_count += 1
            else:
                value = 4096
                other_count += 1

            new_content = add_memory_mb(content, value)

            with open(toml_path, "w") as f:
                f.write(new_content)

            modified += 1

    print(f"Total task.toml files scanned: {total}")
    print(f"Already had memory field (skipped): {skipped}")
    print(f"Modified: {modified}")
    print(f"  - TS/JS tasks (memory_mb = 8192): {ts_js_count}")
    print(f"  - Other tasks (memory_mb = 4096): {other_count}")


if __name__ == "__main__":
    main()
