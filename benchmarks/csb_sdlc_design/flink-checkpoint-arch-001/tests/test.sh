#!/bin/bash
# Reward: ir_checklist (0.0-1.0) — IR metrics + keyword overlap for architectural analysis
# Composite: 0.4 * task_quality + 0.3 * file_recall + 0.2 * file_precision + 0.1 * dep_accuracy

set -e

# sg_only_env: restore full repo before verification (no-op for regular runs)
[ -f /tmp/.sg_only_mode ] && [ -f /tests/sgonly_verifier_wrapper.sh ] && source /tests/sgonly_verifier_wrapper.sh
# Artifact mode: parse answer.json, extract analysis text
if [ -f /tmp/.artifact_only_mode ] && [ -f /tests/answer_json_verifier_lib.sh ]; then
    source /tests/answer_json_verifier_lib.sh
fi

TASK_WORKDIR="${TASK_WORKDIR:-/workspace}"
TASK_REPO_ROOT="${TASK_REPO_ROOT:-${VERIFY_REPO:-$TASK_WORKDIR}}"
VERIFY_REPO="${VERIFY_REPO:-$TASK_REPO_ROOT}"

cd "$TASK_REPO_ROOT"
mkdir -p /logs/verifier

# ── validation_result sidecar ───────────────────────────────────────────────
write_validation_result() {
    local reward="$1"
    python3 - "$reward" "$TASK_QUALITY" "$IR_RECALL" "$IR_PRECISION" "$DEP_ACCURACY" <<'VR_PYEOF'
import json, sys

reward_str = sys.argv[1]
task_quality = sys.argv[2] if len(sys.argv) > 2 else "0"
ir_recall = sys.argv[3] if len(sys.argv) > 3 else "0"
ir_precision = sys.argv[4] if len(sys.argv) > 4 else "0"
dep_accuracy = sys.argv[5] if len(sys.argv) > 5 else "0"

def safe_float(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0

reward = safe_float(reward_str)

sub_scores = {
    "task_quality": safe_float(task_quality),
    "file_recall": safe_float(ir_recall),
    "file_precision": safe_float(ir_precision),
    "dep_accuracy": safe_float(dep_accuracy),
}

payload = {
    "schema_version": "validation_result.v1alpha1",
    "status": "scored",
    "scorable": True,
    "scorer_family": "ir_checklist",
    "reward": reward,
    "pass_threshold": 0.5,
    "passed": reward >= 0.5,
    "output_contract": {
        "mode": "unspecified",
        "primary_path": None,
        "required_artifact": False,
    },
    "sub_scores": sub_scores,
    "failure": None,
}

with open("/logs/verifier/validation_result.json", "w") as f:
    json.dump(payload, f, indent=2)
VR_PYEOF
}

write_invalid_output_vr() {
    local code="$1"
    local message="$2"
    python3 - "$code" "$message" <<'VR_PYEOF'
import json, sys
code, message = sys.argv[1:3]
payload = {
    "schema_version": "validation_result.v1alpha1",
    "status": "invalid_output",
    "scorable": False,
    "scorer_family": "ir_checklist",
    "reward": 0.0,
    "pass_threshold": 0.5,
    "passed": False,
    "output_contract": {
        "mode": "unspecified",
        "primary_path": None,
        "required_artifact": False,
    },
    "sub_scores": {},
    "failure": {"code": code, "message": message, "stage": "output_validation"},
}
with open("/logs/verifier/validation_result.json", "w") as f:
    json.dump(payload, f, indent=2)
VR_PYEOF
}


# Fix git safe.directory
git config --global --add safe.directory "$TASK_REPO_ROOT" 2>/dev/null || true

# ── Source shared verifier library ────────────────────────────────────────
source /tests/verifier_lib.sh

# ── Change detection guard ────────────────────────────────────────────────
SOLUTION_FILE="/logs/agent/solution.md"
# In artifact mode, populate expected output from answer.json analysis
if [ "${ARTIFACT_ONLY:-false}" = "true" ] && [ -f "${ANALYSIS_TEXT_FILE:-}" ]; then
    mkdir -p "/logs/agent"
    cp "$ANALYSIS_TEXT_FILE" "/logs/agent/solution.md"
    echo "[answer_json] Copied analysis text to /logs/agent/solution.md"
fi
if [ ! -f "$SOLUTION_FILE" ]; then
    echo "No solution.md found — agent did not produce output"
    echo "0.0" > /logs/verifier/reward.txt
write_invalid_output_vr "missing_required_output" "Agent did not produce required output"
exit 0
fi

SOLUTION_SIZE=$(wc -c < "$SOLUTION_FILE" 2>/dev/null || echo 0)
if [ "$SOLUTION_SIZE" -lt 200 ]; then
    echo "Solution.md too short ($SOLUTION_SIZE bytes) — likely incomplete"
    echo "0.0" > /logs/verifier/reward.txt
write_invalid_output_vr "missing_required_output" "Agent did not produce required output"
exit 0
fi

echo "Solution file found ($SOLUTION_SIZE bytes)"

# ── IR metrics pipeline ──────────────────────────────────────────────────
run_ir_pipeline "$SOLUTION_FILE" "/tests/ground_truth.json" "/logs/verifier/ir_metrics.json"

# ── Task quality scoring (keyword-based) ─────────────────────────────────
QUALITY_SCORE=0
QUALITY_MAX=10

# Check for required sections
if grep -qiE '^##\s+(Files Examined|Files Analyzed)' "$SOLUTION_FILE"; then
    QUALITY_SCORE=$((QUALITY_SCORE + 2))
    echo "[x] Has 'Files Examined' section"
else
    echo "[ ] Missing 'Files Examined' section"
fi

if grep -qiE '^##\s+(Dependency Chain|Component Relationships)' "$SOLUTION_FILE"; then
    QUALITY_SCORE=$((QUALITY_SCORE + 2))
    echo "[x] Has 'Dependency Chain' section"
else
    echo "[ ] Missing 'Dependency Chain' section"
fi

if grep -qiE '^##\s+(Analysis|Summary|Architecture)' "$SOLUTION_FILE"; then
    QUALITY_SCORE=$((QUALITY_SCORE + 2))
    echo "[x] Has 'Analysis' section"
else
    echo "[ ] Missing 'Analysis' section"
fi

# Flink checkpoint-specific keywords
ARCH_KEYWORDS="CheckpointCoordinator|CheckpointBarrier|PendingCheckpoint|CompletedCheckpoint|triggerCheckpoint|acknowledgeCheckpoint|CheckpointBarrierHandler|SingleCheckpointBarrierHandler|SubtaskCheckpointCoordinator|StreamTask|CheckpointPlan|barrier.alignment|OperatorCoordinator|CheckpointStorage|exactly.once"
KEYWORD_HITS=$(grep -ciE "$ARCH_KEYWORDS" "$SOLUTION_FILE" 2>/dev/null || echo 0)
if [ "$KEYWORD_HITS" -ge 5 ]; then
    QUALITY_SCORE=$((QUALITY_SCORE + 2))
    echo "[x] Architecture keywords found ($KEYWORD_HITS hits)"
elif [ "$KEYWORD_HITS" -ge 2 ]; then
    QUALITY_SCORE=$((QUALITY_SCORE + 1))
    echo "[~] Some architecture keywords found ($KEYWORD_HITS hits)"
else
    echo "[ ] Few architecture keywords ($KEYWORD_HITS hits)"
fi

# Check for sufficient depth (word count proxy)
WORD_COUNT=$(wc -w < "$SOLUTION_FILE" 2>/dev/null || echo 0)
if [ "$WORD_COUNT" -ge 500 ]; then
    QUALITY_SCORE=$((QUALITY_SCORE + 2))
    echo "[x] Sufficient analysis depth ($WORD_COUNT words)"
elif [ "$WORD_COUNT" -ge 200 ]; then
    QUALITY_SCORE=$((QUALITY_SCORE + 1))
    echo "[~] Moderate analysis depth ($WORD_COUNT words)"
else
    echo "[ ] Shallow analysis ($WORD_COUNT words)"
fi

TASK_QUALITY=$(awk "BEGIN {printf \"%.2f\", $QUALITY_SCORE / $QUALITY_MAX}")
echo "Task quality: $TASK_QUALITY ($QUALITY_SCORE / $QUALITY_MAX)"

# ── Composite score ──────────────────────────────────────────────────────
SCORE=$(composite_score "$TASK_QUALITY" "$IR_RECALL" "$IR_PRECISION" "$DEP_ACCURACY")

echo "$SCORE" > /logs/verifier/reward.txt
write_validation_result "$SCORE"
echo ""
echo "[x] Tests completed - Score: $SCORE (quality=$TASK_QUALITY recall=$IR_RECALL precision=$IR_PRECISION dep=$DEP_ACCURACY)"
