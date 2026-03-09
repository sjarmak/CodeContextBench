#!/bin/bash
# Reward: checklist (0.0-1.0) — Kafka coverage gap analysis quality score
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

OUTPUT_FILE="/workspace/coverage_analysis.md"
# In artifact mode, populate expected output from answer.json analysis
if [ "${ARTIFACT_ONLY:-false}" = "true" ] && [ -f "${ANALYSIS_TEXT_FILE:-}" ]; then
    cp "$ANALYSIS_TEXT_FILE" "/workspace/coverage_analysis.md"
    echo "[answer_json] Copied analysis text to /workspace/coverage_analysis.md"
fi

if [ ! -f "$OUTPUT_FILE" ]; then
    ALT=$(find /workspace -maxdepth 2 -name "*.md" ! -name "README*" 2>/dev/null | head -1)
    OUTPUT_FILE="${ALT:-$OUTPUT_FILE}"
fi

if [ ! -f "$OUTPUT_FILE" ]; then
    echo "0.0" > /logs/verifier/reward.txt
    exit 0
fi

echo "Scoring: $OUTPUT_FILE"

SCORE=$(python3 - "$OUTPUT_FILE" <<'PYEOF'
import sys, re

path = sys.argv[1]
try:
    content = open(path).read()
except Exception:
    print("0.0", end="")
    sys.exit(0)

score = 0.0

# Component 1: failure mode recall (0.40)
failure_sections = re.findall(r'[Ff]ailure [Mm]ode\s+\d+|###\s+[Ff]ailure', content)
n_failures = len(failure_sections)
has_locations = bool(re.search(r'GroupCoordinator|GroupMetadata|GroupCoordinatorTest', content))
print(f"Failure modes: {n_failures}", file=sys.stderr)

if n_failures >= 5:
    score += 0.30
elif n_failures >= 3:
    score += 0.20
elif n_failures >= 1:
    score += 0.10

if has_locations:
    score += 0.10

# Component 2: proposed test correctness (0.30)
test_patterns = [
    r'@Test|def test|testXxx|public void test',
    r'assert|Assert|assertEquals',
    r'mock|Mock|stub|Stub|when\(',
    r'[Pp]roposed [Tt]est|[Tt]est [Mm]ethod',
]
test_hits = sum(1 for p in test_patterns if re.search(p, content))
score += min(0.30, test_hits * 0.08)
print(f"Test proposal hits: {test_hits}/4", file=sys.stderr)

# Component 3: coverage delta estimate (0.30)
coverage_patterns = [
    r'[Cc]overage [Dd]elta|[Cc]ode [Pp]ath',
    r'HIGH|MEDIUM|LOW',
    r'~line\s+\d+|line\s+~\d+|\.scala\s*~',
    r'partition|rebalance|heartbeat|offset|join group',
]
cov_hits = sum(1 for p in coverage_patterns if re.search(p, content))
score += min(0.30, cov_hits * 0.08)
print(f"Coverage delta hits: {cov_hits}/4", file=sys.stderr)

score = min(1.0, score)
print(f"Final score: {score:.2f}", file=sys.stderr)
print(f"{score:.2f}", end="")
PYEOF
)

echo "$SCORE" > /logs/verifier/reward.txt
echo "Score: $SCORE"
exit 0
