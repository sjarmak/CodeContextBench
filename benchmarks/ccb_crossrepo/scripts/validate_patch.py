#!/usr/bin/env python3
"""Validate a unified diff patch against expected_changes.json.

Usage:
    python3 validate_patch.py <patch_file> --expected <expected_changes.json> --output <result.json>

Or from test.sh:
    python3 validate_patch.py <patch_file> --expected /task/tests/expected_changes.json --output /logs/verifier/validation_result.json

The validator checks:
1. Which expected files were actually modified in the patch
2. Whether removed patterns are absent (or reduced) in the patched content
3. Whether added patterns are present in the patched content
4. Overall score as weighted combination of file coverage and pattern matching
"""

import argparse
import json
import re
import sys
from pathlib import Path


def parse_unified_diff(patch_text: str) -> dict[str, dict]:
    """Parse unified diff into per-file changes.

    Returns dict mapping filename -> {added_lines: [...], removed_lines: [...], raw: str}
    """
    files = {}
    current_file = None
    current_raw = []

    for line in patch_text.splitlines():
        # Detect file header: diff --git a/path b/path or --- a/path or +++ b/path
        if line.startswith("diff --git "):
            if current_file:
                files[current_file]["raw"] = "\n".join(current_raw)
            # Extract b/path
            parts = line.split(" b/", 1)
            if len(parts) == 2:
                current_file = parts[1]
                files[current_file] = {"added_lines": [], "removed_lines": [], "raw": ""}
                current_raw = [line]
            continue
        elif line.startswith("+++ b/"):
            # Alternative file detection for patches without diff --git header
            fname = line[6:]
            if fname and current_file is None:
                current_file = fname
                files[current_file] = {"added_lines": [], "removed_lines": [], "raw": ""}
                current_raw = [line]
            continue

        if current_file:
            current_raw.append(line)
            if line.startswith("+") and not line.startswith("+++"):
                files[current_file]["added_lines"].append(line[1:])
            elif line.startswith("-") and not line.startswith("---"):
                files[current_file]["removed_lines"].append(line[1:])

    if current_file and current_raw:
        files[current_file]["raw"] = "\n".join(current_raw)

    return files


def check_file_coverage(patch_files: dict, expected_files: list[str]) -> tuple[float, list[str], list[str]]:
    """Check how many expected files were modified.

    Handles path prefix variations: expected might be 'src/etcd/client/v3/client.go'
    but patch might have just 'client/v3/client.go'.
    """
    matched = []
    missing = []

    for expected in expected_files:
        found = False
        for patch_file in patch_files:
            # Exact match
            if patch_file == expected:
                found = True
                break
            # Suffix match (patch may have shorter or longer path)
            if patch_file.endswith(expected) or expected.endswith(patch_file):
                found = True
                break
            # Basename + parent match
            ep = Path(expected)
            pp = Path(patch_file)
            if ep.name == pp.name and (
                str(ep.parent).endswith(str(pp.parent))
                or str(pp.parent).endswith(str(ep.parent))
            ):
                found = True
                break
        if found:
            matched.append(expected)
        else:
            missing.append(expected)

    coverage = len(matched) / len(expected_files) if expected_files else 1.0
    return coverage, matched, missing


def check_patterns(patch_files: dict, expected_patterns: dict) -> tuple[float, dict]:
    """Check removed/added patterns against the patch content."""
    results = {"removed": {}, "added": {}}
    scores = []

    # Collect all added and removed lines across all files
    all_added = []
    all_removed = []
    for fdata in patch_files.values():
        all_added.extend(fdata["added_lines"])
        all_removed.extend(fdata["removed_lines"])

    all_added_text = "\n".join(all_added)
    all_removed_text = "\n".join(all_removed)

    # Check removed patterns appear in removed lines (agent removed them)
    for pattern in expected_patterns.get("removed", []):
        try:
            found = bool(re.search(pattern, all_removed_text))
        except re.error:
            found = pattern in all_removed_text
        results["removed"][pattern] = found
        scores.append(1.0 if found else 0.0)

    # Check added patterns appear in added lines (agent added them)
    for pattern in expected_patterns.get("added", []):
        try:
            found = bool(re.search(pattern, all_added_text))
        except re.error:
            found = pattern in all_added_text
        results["added"][pattern] = found
        scores.append(1.0 if found else 0.0)

    pattern_score = sum(scores) / len(scores) if scores else 1.0
    return pattern_score, results


def validate_patch(patch_path: str, expected_path: str) -> dict:
    """Main validation: score a patch against expected_changes.json."""
    with open(patch_path) as f:
        patch_text = f.read()

    with open(expected_path) as f:
        expected = json.load(f)

    patch_files = parse_unified_diff(patch_text)

    if not patch_files:
        return {
            "overall_score": 0.0,
            "file_coverage": 0.0,
            "pattern_score": 0.0,
            "files_matched": [],
            "files_missing": expected.get("expected_files", []),
            "pattern_results": {},
            "error": "No files found in patch",
        }

    # File coverage (40% weight)
    file_cov, matched, missing = check_file_coverage(
        patch_files, expected.get("expected_files", [])
    )

    # Pattern matching (60% weight)
    pattern_score, pattern_results = check_patterns(
        patch_files, expected.get("expected_patterns", {})
    )

    overall = 0.4 * file_cov + 0.6 * pattern_score

    return {
        "overall_score": round(overall, 4),
        "file_coverage": round(file_cov, 4),
        "pattern_score": round(pattern_score, 4),
        "files_in_patch": list(patch_files.keys()),
        "files_matched": matched,
        "files_missing": missing,
        "pattern_results": pattern_results,
    }


def main():
    parser = argparse.ArgumentParser(description="Validate crossrepo patch")
    parser.add_argument("patch_file", help="Path to unified diff patch")
    parser.add_argument("--expected", required=True, help="Path to expected_changes.json")
    parser.add_argument("--output", required=True, help="Path to write validation_result.json")
    args = parser.parse_args()

    if not Path(args.patch_file).exists():
        result = {"overall_score": 0.0, "error": f"Patch file not found: {args.patch_file}"}
    elif not Path(args.expected).exists():
        result = {"overall_score": 0.0, "error": f"Expected changes not found: {args.expected}"}
    else:
        result = validate_patch(args.patch_file, args.expected)

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(result, f, indent=2)

    print(json.dumps(result, indent=2))
    return 0 if result["overall_score"] > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
