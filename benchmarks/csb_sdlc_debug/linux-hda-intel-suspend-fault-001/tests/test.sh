#!/bin/bash
# Reward: checklist (0.0-1.0) — fault localization accuracy rubric
# Test script for lfl-sound-53441: HDA Intel sound fails after suspend
# Ground truth: sound/pci/hda/hda_intel.c :: DEFINE_PCI_DEVICE_TABLE

set -e
# Artifact mode: parse answer.json, extract analysis text, apply diffs
if [ -f /tmp/.artifact_only_mode ] && [ -f /tests/answer_json_verifier_lib.sh ]; then
    source /tests/answer_json_verifier_lib.sh
fi

TASK_WORKDIR="${TASK_WORKDIR:-/workspace}"
TASK_REPO_ROOT="${TASK_REPO_ROOT:-${VERIFY_REPO:-$TASK_WORKDIR}}"
VERIFY_REPO="${VERIFY_REPO:-$TASK_REPO_ROOT}"

cd "$TASK_REPO_ROOT"

# Create log directories
mkdir -p /logs/verifier

# ── validation_result sidecar ───────────────────────────────────────────────
write_validation_result() {
    local reward="$1"
    local sub_scores_json="${2:-{\}}"
    local details_json="${3:-null}"
    local status="${4:-scored}"
    local failure_json="${5:-null}"
    python3 - "$reward" "$sub_scores_json" "$details_json" "$status" "$failure_json" <<'VR_PYEOF'
import json, sys

reward_str, sub_scores_raw, details_raw, status, failure_raw = sys.argv[1:6]
try:
    reward = float(reward_str)
except (TypeError, ValueError):
    reward = 0.0
try:
    sub_scores = json.loads(sub_scores_raw)
except Exception:
    sub_scores = {}
try:
    details = json.loads(details_raw) if details_raw != "null" else None
except Exception:
    details = None
try:
    failure = json.loads(failure_raw) if failure_raw != "null" else None
except Exception:
    failure = None

if status != "scored":
    failure = failure or {
        "code": "missing_required_output",
        "message": "Agent did not produce required output",
        "stage": "output_validation",
    }

payload = {
    "schema_version": "validation_result.v1alpha1",
    "status": status,
    "scorable": status == "scored",
    "scorer_family": "checklist",
    "reward": reward,
    "pass_threshold": 0.5,
    "passed": status == "scored" and reward >= 0.5,
    "output_contract": {
        "mode": "unspecified",
        "primary_path": None,
        "required_artifact": False,
    },
    "sub_scores": sub_scores,
    "failure": failure,
}
if details:
    payload["details"] = details

with open("/logs/verifier/validation_result.json", "w") as f:
    json.dump(payload, f, indent=2)
VR_PYEOF
}


# Check that the agent produced a result file
if [ ! -f "/workspace/fault_localization_result.json" ]; then
    echo "FAIL: /workspace/fault_localization_result.json not found"
    echo "0.0" > /logs/verifier/reward.txt
write_validation_result "0.0" "{}" "null" "invalid_output"
exit 0
fi

# Validate JSON
if ! python3 -c "import json; json.load(open('/workspace/fault_localization_result.json'))" 2>/dev/null; then
    echo "FAIL: fault_localization_result.json is not valid JSON"
    echo "0.0" > /logs/verifier/reward.txt
write_validation_result "0.0" "{}" "null" "invalid_output"
exit 0
fi

# ── Scoring ──────────────────────────────────────────────
SCORE=0
MAX_SCORE=10

# Load ground truth from JSON (accepts both the macro name and the actual table name)
GT_FILE=$(python3 -c "import json; d=json.load(open('/tests/ground_truth.json')); print(d['buggy_files'][0])")
GT_METHODS=($(python3 -c "import json; d=json.load(open('/tests/ground_truth.json')); print(' '.join(d['buggy_functions']))"))


# Extract agent predictions
PREDICTED_FILES=$(python3 -c "
import json
data = json.load(open('/workspace/fault_localization_result.json'))
files = data.get('buggy_files', [])
for f in files:
    print(f)
" 2>/dev/null)

PREDICTED_METHODS=$(python3 -c "
import json
data = json.load(open('/workspace/fault_localization_result.json'))
methods = data.get('buggy_functions', [])
for m in methods:
    print(m)
" 2>/dev/null)

HAS_REASONING=$(python3 -c "
import json
data = json.load(open('/workspace/fault_localization_result.json'))
r = data.get('reasoning', '')
print('yes' if len(str(r)) > 10 else 'no')
" 2>/dev/null)

# Check 1: Result file has required fields (1 point)
HAS_FIELDS=$(python3 -c "
import json
data = json.load(open('/workspace/fault_localization_result.json'))
has = all(k in data for k in ['buggy_files', 'buggy_functions'])
print('yes' if has else 'no')
" 2>/dev/null)

if [ "$HAS_FIELDS" = "yes" ]; then
    echo "PASS: Result file has required fields"
    SCORE=$((SCORE + 1))
else
    echo "FAIL: Result file missing required fields (buggy_files, buggy_functions)"
fi

# Check 2: File-level localization - first prediction exact match (4 points)
FIRST_FILE=$(echo "$PREDICTED_FILES" | head -n1 | sed 's|^/workspace/||' | sed 's|^\./||')
if [ "$FIRST_FILE" = "$GT_FILE" ]; then
    FILE_MATCH="exact"
    echo "PASS: First predicted file is correct: $GT_FILE"
    SCORE=$((SCORE + 4))
else
    FILE_MATCH="no"
fi

# Check 3: File-level localization - file in top-5 (1 point, only if not first)
if [ "$FILE_MATCH" = "no" ]; then
    FILE_COUNT=0
    while IFS= read -r pred_file; do
        pred_file=$(echo "$pred_file" | sed 's|^/workspace/||' | sed 's|^\./||')
        FILE_COUNT=$((FILE_COUNT + 1))
        if [ "$pred_file" = "$GT_FILE" ] && [ "$FILE_COUNT" -le 5 ]; then
            FILE_MATCH="top5"
            echo "PASS: Buggy file found at position $FILE_COUNT in predictions"
            SCORE=$((SCORE + 1))
            break
        fi
    done <<< "$PREDICTED_FILES"
    if [ "$FILE_MATCH" = "no" ]; then
        echo "FAIL: Did not identify buggy file: $GT_FILE"
        echo "  Predicted files: $PREDICTED_FILES"
    fi
fi

# Check 4: Method-level localization (3 points)
# Accept any of the ground truth method names
METHOD_MATCH="no"
for gt_method in "${GT_METHODS[@]}"; do
    while IFS= read -r pred_method; do
        if [ "$pred_method" = "$gt_method" ]; then
            METHOD_MATCH="yes"
            break 2
        fi
    done <<< "$PREDICTED_METHODS"
done

if [ "$METHOD_MATCH" = "yes" ]; then
    echo "PASS: Correctly identified buggy function/struct"
    SCORE=$((SCORE + 3))
else
    echo "FAIL: Did not identify buggy function/struct: ${GT_METHODS[*]}"
    echo "  Predicted methods: $PREDICTED_METHODS"
fi

# Check 5: Reasoning provided (1 point)
if [ "$HAS_REASONING" = "yes" ]; then
    echo "PASS: Reasoning provided"
    SCORE=$((SCORE + 1))
else
    echo "FAIL: No reasoning provided"
fi

# Check 6: Confidence score provided and valid (1 point)
HAS_CONFIDENCE=$(python3 -c "
import json
data = json.load(open('/workspace/fault_localization_result.json'))
c = data.get('confidence', None)
print('yes' if isinstance(c, (int, float)) and 0 <= c <= 1 else 'no')
" 2>/dev/null)

if [ "$HAS_CONFIDENCE" = "yes" ]; then
    echo "PASS: Valid confidence score provided"
    SCORE=$((SCORE + 1))
else
    echo "FAIL: Missing or invalid confidence score (expected 0.0-1.0)"
fi

# Convert to decimal score (0.0 - 1.0)
FINAL_SCORE=$(awk "BEGIN {printf \"%.1f\", $SCORE / $MAX_SCORE}")

echo "$FINAL_SCORE" > /logs/verifier/reward.txt
write_validation_result "${FINAL_SCORE:-$SCORE}" "{}" "null" "scored"
echo ""
echo "Tests completed - Score: $FINAL_SCORE (${SCORE}/${MAX_SCORE} checks passed)"
