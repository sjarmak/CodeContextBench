#!/bin/bash
# Reward: checklist (0.0-1.0) — unit test generation quality score
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

TARGET_FILE="/workspace/staging/src/k8s.io/apiserver/pkg/storage/value/value_test.go"

# Check for any *_test.go file in the package dir
ALT_FILE=$(find /workspace/staging/src/k8s.io/apiserver/pkg/storage/value/ -name "*_test.go" 2>/dev/null | head -1)
if [ -z "$ALT_FILE" ] && [ ! -f "$TARGET_FILE" ]; then
    # Also check /workspace root
    ALT_FILE=$(find /workspace -maxdepth 3 -name "value_test.go" -o -name "transformer_test.go" 2>/dev/null | head -1)
fi
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
except Exception as e:
    print(f"0.0", end="")
    sys.exit(0)

score = 0.0

# Component 1: file presence (0.25) — already satisfied by getting here
score += 0.25

# Component 2: test function coverage (0.40)
test_funcs = re.findall(r'func\s+(Test\w+)\s*\(', content)
n = len(test_funcs)
if n >= 8:
    score += 0.40
elif n >= 5:
    score += 0.30
elif n >= 3:
    score += 0.20
elif n >= 1:
    score += 0.10

print(f"Test functions found: {test_funcs}", file=sys.stderr)

# Component 3: edge case detection (0.20)
edge_patterns = [
    r'error|Error|err\b',
    r'nil\b',
    r'empty|Empty',
    r'mismatch|Mismatch|invalid|Invalid|corrupt|stale',
    r'prefix|Prefix',
]
edge_hits = sum(1 for p in edge_patterns if re.search(p, content))
score += min(0.20, edge_hits * 0.04)
print(f"Edge case hits: {edge_hits}/5", file=sys.stderr)

# Component 4: table-driven test pattern (0.15)
if re.search(r't\.Run\s*\(', content):
    score += 0.15
    print("Table-driven tests: PASS", file=sys.stderr)
else:
    print("Table-driven tests: FAIL", file=sys.stderr)

print(f"Final score: {score:.2f}", file=sys.stderr)
print(f"{score:.2f}", end="")
PYEOF
)

echo "$SCORE" > /logs/verifier/reward.txt
echo "Score: $SCORE"
exit 0
