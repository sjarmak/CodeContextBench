#!/bin/bash
# eval.sh — MCP-unique benchmark evaluator for CCX-compliance-190
# Exit-code-first (SWE-Factory pattern):
#   exit 0 — agent produced useful output (composite score > 0)
#   exit 1 — total failure (composite score == 0 or missing answer)
#
# Writes /logs/verifier/reward.txt with the composite score [0.0, 1.0]
# and /logs/verifier/validation_result.json with canonical verifier semantics.

set -euo pipefail

TASK_ID="CCX-compliance-190"
TASK_WORKDIR="$(printenv TASK_WORKDIR || true)"
[ -n "$TASK_WORKDIR" ] || TASK_WORKDIR="/workspace"
TASK_REPO_ROOT="$(printenv TASK_REPO_ROOT || true)"
[ -n "$TASK_REPO_ROOT" ] || TASK_REPO_ROOT="$(printenv VERIFY_REPO || true)"
[ -n "$TASK_REPO_ROOT" ] || TASK_REPO_ROOT="$TASK_WORKDIR"
TASK_OUTPUT="$(printenv TASK_OUTPUT || true)"
[ -n "$TASK_OUTPUT" ] || TASK_OUTPUT="$TASK_WORKDIR/answer.json"
ANSWER_PATH="$TASK_OUTPUT"
TASK_SPEC_PATH="/tests/task_spec.json"
ORACLE_CHECKS="/tests/oracle_checks.py"
REWARD_PATH="/logs/verifier/reward.txt"
VALIDATION_RESULT="/logs/verifier/validation_result.json"
VALIDATION_RESULT_SCHEMA="validation_result.v1alpha1"
SCORER_FAMILY="oracle_checks"
PASS_THRESHOLD="0.0"

mkdir -p /logs/verifier

write_validation_failure() {
    local code="$1"
    local message="$2"
    local stage="$3"
    python3 - "$VALIDATION_RESULT" "$code" "$message" "$stage" "$TASK_OUTPUT" "$VALIDATION_RESULT_SCHEMA" "$SCORER_FAMILY" "$PASS_THRESHOLD" <<'PYEOF'
import json
import sys

(
    output_path,
    code,
    message,
    stage,
    primary_path,
    schema_version,
    scorer_family,
    pass_threshold,
) = sys.argv[1:]

status = "invalid_output" if stage == "output_validation" else "verifier_error"
payload = {
    "schema_version": schema_version,
    "status": status,
    "scorable": False,
    "scorer_family": scorer_family,
    "reward": 0.0,
    "pass_threshold": float(pass_threshold),
    "passed": False,
    "output_contract": {
        "mode": "answer_json_native",
        "primary_path": primary_path,
        "required_artifact": True,
    },
    "sub_scores": {},
    "failure": {
        "code": code,
        "message": message,
        "stage": stage,
    },
}
with open(output_path, "w") as f:
    json.dump(payload, f, indent=2)
PYEOF
}

run_oracle_validation() {
    python3 - "$ORACLE_CHECKS" "$ANSWER_PATH" "$TASK_SPEC_PATH" "$VALIDATION_RESULT" "$TASK_OUTPUT" "$VALIDATION_RESULT_SCHEMA" "$SCORER_FAMILY" "$PASS_THRESHOLD" <<'PYEOF'
import importlib.util
import json
import sys
from pathlib import Path

(
    oracle_checks_path,
    answer_path,
    task_spec_path,
    output_path,
    primary_path,
    schema_version,
    scorer_family,
    pass_threshold,
) = sys.argv[1:]

spec = importlib.util.spec_from_file_location("oracle_checks", oracle_checks_path)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Failed to load oracle checks module from {oracle_checks_path}")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

check_result = module.run_all_checks(answer_path, task_spec_path)
threshold = float(pass_threshold)

def primary_score(check_type: str, result: dict) -> float:
    if check_type == "file_set_match":
        return float(result.get("weighted_f1", result.get("f1", 0.0)))
    if check_type == "symbol_resolution":
        return float(result.get("recall", 0.0))
    if check_type == "dependency_chain":
        return float(result.get("chain_recall", 0.0))
    if check_type == "provenance":
        return float(result.get("provenance_score", 0.0))
    if check_type == "keyword_presence":
        return float(result.get("keyword_recall", 0.0))
    if check_type == "json_schema_match":
        return 1.0 if result.get("valid") else 0.0
    if check_type == "test_ratio":
        return float(result.get("ratio", 0.0))
    value = result.get("score", 0.0)
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    return float(value)

if "error" in check_result:
    payload = {
        "schema_version": schema_version,
        "status": "verifier_error",
        "scorable": False,
        "scorer_family": scorer_family,
        "reward": 0.0,
        "pass_threshold": threshold,
        "passed": False,
        "output_contract": {
            "mode": "answer_json_native",
            "primary_path": primary_path,
            "required_artifact": True,
        },
        "sub_scores": {},
        "failure": {
            "code": "oracle_checks_error",
            "message": str(check_result["error"]),
            "stage": "scoring",
        },
        "details": {
            "oracle_checks": check_result,
        },
        "composite_score": 0.0,
        "checks": {},
        "error": check_result["error"],
    }
    score = 0.0
else:
    raw_checks = check_result.get("checks", {})
    sub_scores = {}
    for check_type, result in raw_checks.items():
        score = round(primary_score(check_type, result), 4)
        sub_scores[check_type] = {
            "score": score,
            "passed": score > 0.0,
        }

    score = round(float(check_result.get("composite_score", 0.0)), 4)
    payload = {
        "schema_version": schema_version,
        "status": "scored",
        "scorable": True,
        "scorer_family": scorer_family,
        "reward": score,
        "pass_threshold": threshold,
        "passed": score > threshold,
        "output_contract": {
            "mode": "answer_json_native",
            "primary_path": primary_path,
            "required_artifact": True,
        },
        "sub_scores": sub_scores,
        "failure": None,
        "details": {
            "oracle_checks": check_result,
        },
        "composite_score": score,
        "checks": raw_checks,
    }

with open(output_path, "w") as f:
    json.dump(payload, f, indent=2)

print(f"{score:.4f}")
PYEOF
}

echo "=== CCX-compliance-190 evaluator ==="
echo "Task spec: $TASK_SPEC_PATH"
echo "Answer:    $ANSWER_PATH"
echo "Repo root: $TASK_REPO_ROOT"
echo ""

# sg_only mode guard: restore full repo if verifier wrapper exists
if [ -f /tmp/.sg_only_mode ] && [ -f /tests/sgonly_verifier_wrapper.sh ]; then
    echo "sg_only mode: sourcing verifier wrapper..."
    source /tests/sgonly_verifier_wrapper.sh
fi

# Verify answer file exists
if [ ! -f "$ANSWER_PATH" ]; then
    echo "ERROR: answer.json not found at $ANSWER_PATH"
    echo "0.0" > "$REWARD_PATH"
    write_validation_failure "missing_required_output" "answer.json not found at $ANSWER_PATH" "output_validation"
    exit 1
fi

# Validate answer is valid JSON
if ! python3 -c "import json; json.load(open('$ANSWER_PATH'))" 2>/dev/null; then
    echo "ERROR: answer.json is not valid JSON"
    echo "0.0" > "$REWARD_PATH"
    write_validation_failure "invalid_answer_json" "answer.json is not valid JSON" "output_validation"
    exit 1
fi

echo "answer.json found and valid JSON"

# Run oracle checks
if [ ! -f "$ORACLE_CHECKS" ]; then
    echo "ERROR: oracle_checks.py not found at $ORACLE_CHECKS"
    echo "0.0" > "$REWARD_PATH"
    write_validation_failure "missing_oracle_checks" "oracle_checks.py not found at $ORACLE_CHECKS" "verifier_runtime"
    exit 1
fi

echo "Running oracle checks..."
SCORE=$(run_oracle_validation) || true

# Validate score is a number
if ! echo "$SCORE" | python3 -c "import sys; float(sys.stdin.read().strip())" 2>/dev/null; then
    echo "ERROR: oracle_checks.py did not return a valid score: $SCORE"
    echo "0.0" > "$REWARD_PATH"
    write_validation_failure "invalid_verifier_score" "oracle_checks.py did not return a valid score: $SCORE" "scoring"
    exit 1
fi

echo ""
echo "Composite score: $SCORE"
echo "$SCORE" > "$REWARD_PATH"

# Exit based on score (SWE-Factory exit-code-first pattern)
python3 -c "import sys; sys.exit(0 if float('$SCORE') > 0 else 1)"
