#!/usr/bin/env python3
"""DependEval ME (Multi-file Editing) evaluation script.

Scores agent-produced code modifications against DependEval Task 1
ground truth. The ground truth is a dict mapping file identifiers to
modified code strings. Keys may be '#file N', 'fileN', 'file_N',
'name.ext', or 'path/name.ext' (inconsistent across instances).

The agent submission is a dict mapping file paths to modified code strings.
We match ground truth entries to submission entries by:
  1. Direct key match
  2. Filename match (basename)
  3. Positional order (as last resort)

Metric: average difflib.SequenceMatcher ratio per matched file.

Usage inside Harbor task container:
    python3 /tests/eval_scripts/dependeval_eval_me.py

Expects:
    /workspace/submission.json  — JSON dict {filepath: modified_code_string}
    /tests/ground_truth.json    — JSON dict {key: expected_code_string}

Writes:
    /logs/verifier/reward.txt   — float reward in [0.0, 1.0]

Self-test:
    python3 scripts/dependeval_eval_me.py --test
"""

from __future__ import annotations

import difflib
import json
import os
import re
import sys


def normalize_code(code: str) -> str:
    """Normalize code for comparison: strip trailing whitespace per line."""
    lines = code.splitlines()
    return "\n".join(line.rstrip() for line in lines)


def string_similarity(a: str, b: str) -> float:
    """Compute string similarity using SequenceMatcher ratio."""
    a_norm = normalize_code(a)
    b_norm = normalize_code(b)
    if not a_norm and not b_norm:
        return 1.0
    if not a_norm or not b_norm:
        return 0.0
    return difflib.SequenceMatcher(None, a_norm, b_norm).ratio()


def extract_basename(key: str) -> str | None:
    """Extract a filename from a ground truth key if it looks like a path."""
    # 'repo/path/file.ext' or 'path/file.ext' or 'file.ext'
    key = key.strip().strip("'\"")
    if "/" in key:
        return key.rsplit("/", 1)[-1]
    if "." in key and not key.startswith("#") and not key.startswith("file"):
        return key
    return None


def is_positional_key(key: str) -> bool:
    """Check if key is a positional placeholder like '#file 1', 'file1', 'file_1'."""
    return bool(re.match(r'^(#file\s*\d+|file_?\d+)$', key, re.IGNORECASE))


def match_gt_to_submission(
    gt_keys: list[str],
    gt_values: list[str],
    sub_keys: list[str],
    sub_values: list[str],
) -> list[tuple[str, str]]:
    """Match ground truth entries to submission entries.

    Returns a list of (gt_value, sub_value) pairs. Unmatched GT entries
    get paired with empty string.

    Strategy:
      1. If GT keys are direct matches to submission keys, use those.
      2. If GT keys have filenames that match submission basenames, use those.
      3. Fall back to positional matching (GT order = submission order).
    """
    pairs: list[tuple[str, str]] = []
    sub_map = {k: v for k, v in zip(sub_keys, sub_values)}
    sub_basename_map: dict[str, str] = {}
    for k, v in zip(sub_keys, sub_values):
        basename = k.rsplit("/", 1)[-1] if "/" in k else k
        sub_basename_map[basename] = v

    used_sub_keys: set[str] = set()

    for i, gt_key in enumerate(gt_keys):
        gt_val = gt_values[i]

        # Strategy 1: Direct key match
        if gt_key in sub_map and gt_key not in used_sub_keys:
            pairs.append((gt_val, sub_map[gt_key]))
            used_sub_keys.add(gt_key)
            continue

        # Strategy 2: Basename match
        gt_basename = extract_basename(gt_key)
        if gt_basename and gt_basename in sub_basename_map:
            # Find the full submission key for this basename
            for sk in sub_keys:
                bn = sk.rsplit("/", 1)[-1] if "/" in sk else sk
                if bn == gt_basename and sk not in used_sub_keys:
                    pairs.append((gt_val, sub_map[sk]))
                    used_sub_keys.add(sk)
                    break
            else:
                # Basename found but all instances used
                pairs.append((gt_val, ""))
            continue

        # Strategy 3: Positional match (for '#file N', 'fileN', etc.)
        if is_positional_key(gt_key) and i < len(sub_values):
            # Use positional index — match GT item i to submission item i
            sk = sub_keys[i] if i < len(sub_keys) else None
            if sk and sk not in used_sub_keys:
                pairs.append((gt_val, sub_values[i]))
                used_sub_keys.add(sk)
                continue

        # No match found
        pairs.append((gt_val, ""))

    return pairs


def score_me(submission: dict, ground_truth: dict) -> float:
    """Score multi-file editing by average per-file string similarity."""
    if not ground_truth:
        return 0.0

    gt_keys = list(ground_truth.keys())
    gt_values = list(ground_truth.values())
    sub_keys = list(submission.keys())
    sub_values = list(submission.values())

    pairs = match_gt_to_submission(gt_keys, gt_values, sub_keys, sub_values)

    if not pairs:
        return 0.0

    similarities = []
    for gt_val, sub_val in pairs:
        sim = string_similarity(str(gt_val), str(sub_val))
        similarities.append(sim)

    return sum(similarities) / len(similarities)


def load_json(path: str) -> object:
    """Load a JSON file, returning None on any error."""
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None


def write_reward(reward: float, reward_path: str) -> None:
    """Write reward float to the reward file."""
    os.makedirs(os.path.dirname(reward_path), exist_ok=True)
    with open(reward_path, "w") as f:
        f.write(str(reward))


def evaluate(
    submission_path: str = "/workspace/submission.json",
    ground_truth_path: str = "/tests/ground_truth.json",
    reward_path: str = "/logs/verifier/reward.txt",
) -> float:
    """Run ME evaluation and write reward. Returns the reward."""
    # Load ground truth
    gt = load_json(ground_truth_path)
    if not isinstance(gt, dict):
        print(f"ERROR: Ground truth at {ground_truth_path} is not a JSON dict",
              file=sys.stderr)
        write_reward(0.0, reward_path)
        return 0.0

    # Load submission
    sub = load_json(submission_path)
    if sub is None:
        print(f"WARNING: No valid submission at {submission_path}, reward=0.0",
              file=sys.stderr)
        write_reward(0.0, reward_path)
        return 0.0

    if not isinstance(sub, dict):
        print(f"WARNING: Submission is not a JSON dict, reward=0.0",
              file=sys.stderr)
        write_reward(0.0, reward_path)
        return 0.0

    reward = score_me(sub, gt)
    write_reward(reward, reward_path)
    print(f"ME reward: {reward:.4f} ({len(gt)} ground truth files, "
          f"{len(sub)} submission files)")
    return reward


def run_self_test() -> None:
    """Run inline smoke tests."""
    print("Running ME eval self-tests...")

    # Test 1: Perfect match with positional keys
    gt1 = {"#file 1": "def foo():\n    return 1", "#file 2": "def bar():\n    return 2"}
    sub1 = {"src/foo.py": "def foo():\n    return 1", "src/bar.py": "def bar():\n    return 2"}
    score1 = score_me(sub1, gt1)
    assert score1 == 1.0, f"Test 1 failed: expected 1.0, got {score1}"
    print("  [PASS] Test 1: Perfect match (positional) -> 1.0")

    # Test 2: Perfect match with filename keys
    gt2 = {"foo.py": "def foo():\n    return 1", "bar.py": "def bar():\n    return 2"}
    sub2 = {"src/foo.py": "def foo():\n    return 1", "lib/bar.py": "def bar():\n    return 2"}
    score2 = score_me(sub2, gt2)
    assert score2 == 1.0, f"Test 2 failed: expected 1.0, got {score2}"
    print("  [PASS] Test 2: Perfect match (basename) -> 1.0")

    # Test 3: Empty submission
    score3 = score_me({}, gt1)
    assert score3 == 0.0, f"Test 3 failed: expected 0.0, got {score3}"
    print("  [PASS] Test 3: Empty submission -> 0.0")

    # Test 4: Empty ground truth
    score4 = score_me(sub1, {})
    assert score4 == 0.0, f"Test 4 failed: expected 0.0, got {score4}"
    print("  [PASS] Test 4: Empty ground truth -> 0.0")

    # Test 5: Partial similarity
    gt5 = {"#file 1": "def foo():\n    return 1\n\ndef extra():\n    pass"}
    sub5 = {"main.py": "def foo():\n    return 1"}
    score5 = score_me(sub5, gt5)
    assert 0.0 < score5 < 1.0, f"Test 5 failed: expected partial score, got {score5}"
    print(f"  [PASS] Test 5: Partial similarity -> {score5:.4f}")

    # Test 6: Direct key match (path keys)
    gt6 = {"repo/src/index.js": "console.log('hello')", "repo/test/test.js": "test('ok')"}
    sub6 = {"repo/src/index.js": "console.log('hello')", "repo/test/test.js": "test('ok')"}
    score6 = score_me(sub6, gt6)
    assert score6 == 1.0, f"Test 6 failed: expected 1.0, got {score6}"
    print("  [PASS] Test 6: Direct key match -> 1.0")

    # Test 7: fileN keys (no underscore)
    gt7 = {"file1": "code1", "file2": "code2"}
    sub7 = {"a.py": "code1", "b.py": "code2"}
    score7 = score_me(sub7, gt7)
    assert score7 == 1.0, f"Test 7 failed: expected 1.0, got {score7}"
    print("  [PASS] Test 7: fileN positional keys -> 1.0")

    # Test 8: file_N keys (with underscore)
    gt8 = {"file_1": "code1", "file_2": "code2"}
    sub8 = {"a.py": "code1", "b.py": "code2"}
    score8 = score_me(sub8, gt8)
    assert score8 == 1.0, f"Test 8 failed: expected 1.0, got {score8}"
    print("  [PASS] Test 8: file_N positional keys -> 1.0")

    # Test 9: Trailing whitespace normalization
    gt9 = {"#file 1": "def foo():  \n    return 1  "}
    sub9 = {"foo.py": "def foo():\n    return 1"}
    score9 = score_me(sub9, gt9)
    assert score9 == 1.0, f"Test 9 failed: expected 1.0, got {score9}"
    print("  [PASS] Test 9: Whitespace normalization -> 1.0")

    # Test 10: Mixed — some match, some don't
    gt10 = {"#file 1": "aaa", "#file 2": "bbb", "#file 3": "ccc"}
    sub10 = {"x.py": "aaa", "y.py": "zzz"}  # file 1 matches, file 2 doesn't, file 3 missing
    score10 = score_me(sub10, gt10)
    # file 1: 1.0, file 2: low similarity, file 3: 0.0
    assert 0.0 < score10 < 1.0, f"Test 10 failed: expected partial, got {score10}"
    print(f"  [PASS] Test 10: Mixed match -> {score10:.4f}")

    print("All ME eval self-tests passed!")


if __name__ == "__main__":
    if "--test" in sys.argv:
        run_self_test()
        sys.exit(0)

    evaluate()
