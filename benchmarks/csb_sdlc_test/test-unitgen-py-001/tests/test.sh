#!/bin/bash
# Reward: checklist (0.0-1.0) — Python unit test generation quality score
set -euo pipefail

[ -f /tmp/.sg_only_mode ] && [ -f /tests/sgonly_verifier_wrapper.sh ] && source /tests/sgonly_verifier_wrapper.sh
# Artifact mode: parse answer.json, extract analysis text, apply diffs
if [ -f /tmp/.artifact_only_mode ] && [ -f /tests/answer_json_verifier_lib.sh ]; then
    source /tests/answer_json_verifier_lib.sh
fi

TASK_WORKDIR="${TASK_WORKDIR:-/workspace}"
TASK_REPO_ROOT="${TASK_REPO_ROOT:-${VERIFY_REPO:-$TASK_WORKDIR}}"
VERIFY_REPO="${VERIFY_REPO:-$TASK_REPO_ROOT}"

mkdir -p /logs/verifier

TARGET_FILE="/workspace/tests/test_cache_middleware.py"
ALT_FILE=$(find /workspace -name "test_cache*.py" -o -name "test_middleware*.py" 2>/dev/null | grep -v __pycache__ | head -1)
TEST_FILE="${ALT_FILE:-$TARGET_FILE}"

if [ ! -f "$TEST_FILE" ]; then
    echo "No test file found"
    echo "0.0" > /logs/verifier/reward.txt
    exit 0
fi

echo "Scoring test file: $TEST_FILE"

SCORE=$(python3 - "$TEST_FILE" <<'PYEOF'
import sys, re

path = sys.argv[1]
try:
    content = open(path).read()
except Exception:
    print("0.0", end="")
    sys.exit(0)

score = 0.0

# Component 1: file presence (0.25)
score += 0.25

# Component 2: test count (0.35)
test_methods = re.findall(r'def\s+(test_\w+)\s*\(', content)
n = len(test_methods)
print(f"Test methods: {test_methods}", file=sys.stderr)
if n >= 8:
    score += 0.35
elif n >= 5:
    score += 0.25
elif n >= 3:
    score += 0.15
elif n >= 1:
    score += 0.08

# Component 3: edge case coverage (0.25)
edge_patterns = [
    r'non.cach|no.cach|not.cach|cannot.cach',
    r'POST|PUT|DELETE',
    r'private|no.store',
    r'Vary|vary',
    r'authenticated|login|logged',
    r'status.code|304|403|500',
    r'max.age|no.cache',
]
edge_hits = sum(1 for p in edge_patterns if re.search(p, content, re.IGNORECASE))
score += min(0.25, edge_hits * 0.05)
print(f"Edge case hits: {edge_hits}/7", file=sys.stderr)

# Component 4: Django TestCase usage (0.15)
if re.search(r'(TestCase|SimpleTestCase|RequestFactory|Client)', content):
    score += 0.15
    print("Django test infrastructure: PASS", file=sys.stderr)

print(f"Final score: {score:.2f}", file=sys.stderr)
print(f"{score:.2f}", end="")
PYEOF
)

echo "$SCORE" > /logs/verifier/reward.txt
echo "Score: $SCORE"
exit 0
