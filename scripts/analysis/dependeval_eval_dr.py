#!/usr/bin/env python3
"""DependEval DR (Dependency Recognition / file ordering) evaluation script.

Scores agent-produced file dependency ordering against DependEval Task 2
ground truth. The ground truth is a list of file paths in correct dependency
order (callees before callers).

Usage inside Harbor task container:
    python3 /tests/eval_scripts/dependeval_eval_dr.py

Expects:
    /workspace/submission.json  — JSON array of file paths in dependency order
    /tests/ground_truth.json    — JSON array of file paths (correct order)

Writes:
    /logs/verifier/reward.txt   — float reward in [0.0, 1.0]

Self-test:
    python3 scripts/dependeval_eval_dr.py --test
"""

from __future__ import annotations

import json
import os
import sys


def normalize_path(p: str) -> str:
    """Strip surrounding quotes and whitespace from a file path string."""
    return p.strip().strip("'\"")


def score_ordering(submission: list[str], ground_truth: list[str]) -> float:
    """Score file ordering by element-wise exact match averaged across positions.

    Both lists are normalized (stripped of surrounding quotes/whitespace).
    If lengths differ, missing positions score 0.
    """
    if not ground_truth:
        return 0.0

    sub_norm = [normalize_path(p) for p in submission]
    gt_norm = [normalize_path(p) for p in ground_truth]

    n = len(gt_norm)
    matches = 0
    for i in range(n):
        if i < len(sub_norm) and sub_norm[i] == gt_norm[i]:
            matches += 1

    return matches / n


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
    """Run DR evaluation and write reward. Returns the reward."""
    # Load ground truth
    gt = load_json(ground_truth_path)
    if not isinstance(gt, list):
        print(f"ERROR: Ground truth at {ground_truth_path} is not a JSON array",
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

    if not isinstance(sub, list):
        print(f"WARNING: Submission is not a JSON array, reward=0.0",
              file=sys.stderr)
        write_reward(0.0, reward_path)
        return 0.0

    reward = score_ordering(sub, gt)
    write_reward(reward, reward_path)
    print(f"DR reward: {reward:.4f} ({len(gt)} positions, "
          f"submission has {len(sub)} entries)")
    return reward


def run_self_test() -> None:
    """Run inline smoke tests."""
    print("Running DR eval self-tests...")

    # Test 1: Perfect match
    gt = ["'repo/a.py'", "'repo/b.py'", "'repo/c.py'"]
    sub = ["'repo/a.py'", "'repo/b.py'", "'repo/c.py'"]
    score = score_ordering(sub, gt)
    assert score == 1.0, f"Test 1 failed: expected 1.0, got {score}"
    print("  [PASS] Test 1: Perfect match -> 1.0")

    # Test 2: Completely wrong order
    sub2 = ["'repo/c.py'", "'repo/a.py'", "'repo/b.py'"]
    score2 = score_ordering(sub2, gt)
    assert score2 == 0.0, f"Test 2 failed: expected 0.0, got {score2}"
    print("  [PASS] Test 2: Wrong order -> 0.0")

    # Test 3: Partial match (first correct)
    sub3 = ["'repo/a.py'", "'repo/c.py'", "'repo/b.py'"]
    score3 = score_ordering(sub3, gt)
    assert abs(score3 - 1 / 3) < 0.01, f"Test 3 failed: expected ~0.333, got {score3}"
    print("  [PASS] Test 3: Partial match -> ~0.333")

    # Test 4: Empty submission
    score4 = score_ordering([], gt)
    assert score4 == 0.0, f"Test 4 failed: expected 0.0, got {score4}"
    print("  [PASS] Test 4: Empty submission -> 0.0")

    # Test 5: Empty ground truth
    score5 = score_ordering(["a.py"], [])
    assert score5 == 0.0, f"Test 5 failed: expected 0.0, got {score5}"
    print("  [PASS] Test 5: Empty ground truth -> 0.0")

    # Test 6: Path normalization (quotes stripped)
    gt6 = ["'repo/a.py'", "'repo/b.py'"]
    sub6 = ["repo/a.py", "repo/b.py"]
    score6 = score_ordering(sub6, gt6)
    assert score6 == 1.0, f"Test 6 failed: expected 1.0, got {score6}"
    print("  [PASS] Test 6: Quote normalization -> 1.0")

    # Test 7: Submission shorter than ground truth
    gt7 = ["'a.py'", "'b.py'", "'c.py'", "'d.py'"]
    sub7 = ["'a.py'", "'b.py'"]
    score7 = score_ordering(sub7, gt7)
    assert abs(score7 - 0.5) < 0.01, f"Test 7 failed: expected 0.5, got {score7}"
    print("  [PASS] Test 7: Short submission -> 0.5")

    # Test 8: Submission longer than ground truth (extra ignored)
    sub8 = ["'a.py'", "'b.py'", "'c.py'", "'d.py'", "'e.py'"]
    score8 = score_ordering(sub8, gt7)
    assert score8 == 1.0, f"Test 8 failed: expected 1.0, got {score8}"
    print("  [PASS] Test 8: Long submission (exact prefix) -> 1.0")

    print("All DR eval self-tests passed!")


if __name__ == "__main__":
    if "--test" in sys.argv:
        run_self_test()
        sys.exit(0)

    evaluate()
