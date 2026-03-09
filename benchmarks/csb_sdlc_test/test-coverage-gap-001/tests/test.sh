#!/bin/bash
# Reward: checklist (0.0-1.0) — coverage gap analysis quality score
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
    echo "No analysis file found"
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

# Component 1: gap identification precision (0.40)
gap_sections = re.findall(r'Gap\s+\d+|###\s+Gap', content)
n_gaps = len(gap_sections)
has_file_refs = bool(re.search(r'source/common/http|conn_manager|filter_manager', content))
has_line_refs = bool(re.search(r'[Ll]ines?\s*[:~]\s*\d+|~\d{3}', content))

print(f"Gaps found: {n_gaps}", file=sys.stderr)

if n_gaps >= 5:
    score += 0.30
elif n_gaps >= 3:
    score += 0.20
elif n_gaps >= 1:
    score += 0.10

if has_file_refs:
    score += 0.06
if has_line_refs:
    score += 0.04

# Component 2: proposed test case feasibility (0.30)
test_proposal_patterns = [
    r'[Pp]roposed [Tt]est|[Tt]est [Cc]ase|[Tt]est [Nn]ame',
    r'TEST_F\s*\(|TEST\s*\(',
    r'EXPECT_|ASSERT_',
    r'[Ss]etup|[Aa]ssert|[Vv]erify',
]
prop_hits = sum(1 for p in test_proposal_patterns if re.search(p, content))
score += min(0.30, prop_hits * 0.08)
print(f"Test proposal hits: {prop_hits}/4", file=sys.stderr)

# Component 3: code reference accuracy (0.30)
ref_patterns = [
    r'conn_manager_impl',
    r'filter_manager|FilterManager',
    r'header_map|HeaderMap',
    r'HIGH|MEDIUM|LOW',
    r'[Ww]hy [Ii]t [Mm]atters|[Ii]mpact|[Rr]isk',
]
ref_hits = sum(1 for p in ref_patterns if re.search(p, content))
score += min(0.30, ref_hits * 0.06)
print(f"Reference hits: {ref_hits}/5", file=sys.stderr)

score = min(1.0, score)
print(f"Final score: {score:.2f}", file=sys.stderr)
print(f"{score:.2f}", end="")
PYEOF
)

echo "$SCORE" > /logs/verifier/reward.txt
echo "Score: $SCORE"
exit 0
