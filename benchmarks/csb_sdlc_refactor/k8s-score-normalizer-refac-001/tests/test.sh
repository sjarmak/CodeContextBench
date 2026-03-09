#!/bin/bash
# Reward: ir_checklist (0.0-1.0) — IR metrics + completeness check for cross-file refactoring
# Composite: 0.4 * task_quality + 0.3 * file_recall + 0.2 * file_precision + 0.1 * dep_accuracy

set -e

# sg_only_env: restore full repo before verification (no-op for regular runs)
[ -f /tmp/.sg_only_mode ] && [ -f /tests/sgonly_verifier_wrapper.sh ] && source /tests/sgonly_verifier_wrapper.sh
# Artifact mode: parse answer.json, extract analysis text, apply diffs
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


git config --global --add safe.directory "$TASK_REPO_ROOT" 2>/dev/null || true

# ── Source shared verifier library ────────────────────────────────────────
source /tests/verifier_lib.sh

# ── Change detection guard ────────────────────────────────────────────────
# Refactoring tasks require actual code changes OR a detailed solution.md
SOLUTION_FILE="/logs/agent/solution.md"
# In artifact mode, populate expected output from answer.json analysis
if [ "${ARTIFACT_ONLY:-false}" = "true" ] && [ -f "${ANALYSIS_TEXT_FILE:-}" ]; then
    mkdir -p "/logs/agent"
    cp "$ANALYSIS_TEXT_FILE" "/logs/agent/solution.md"
    echo "[answer_json] Copied analysis text to /logs/agent/solution.md"
fi
UNSTAGED_COUNT=$(git diff --stat 2>/dev/null | wc -l)
STAGED_COUNT=$(git diff --cached --stat 2>/dev/null | wc -l)
UNTRACKED_COUNT=$(git ls-files --others --exclude-standard 2>/dev/null | wc -l)

ORIGIN_REF=""
for ref in origin/master origin/main origin/HEAD; do
    if git rev-parse "$ref" >/dev/null 2>&1; then
        ORIGIN_REF="$ref"; break
    fi
done
COMMIT_COUNT=0
if [ -n "$ORIGIN_REF" ]; then
    COMMIT_COUNT=$(git log --oneline "$ORIGIN_REF..HEAD" 2>/dev/null | wc -l)
    # Guard: if commit count is very high, these are repo-setup commits
    # (e.g., tagged release ahead of origin/master), not agent work
    if [ "$COMMIT_COUNT" -gt 5 ]; then
        echo "[info] $COMMIT_COUNT commits from $ORIGIN_REF..HEAD — baseline offset, not agent work"
        COMMIT_COUNT=0
    fi
fi

HAS_CHANGES=0
if [ "$UNSTAGED_COUNT" -gt 0 ] || [ "$STAGED_COUNT" -gt 0 ] || [ "$UNTRACKED_COUNT" -gt 0 ] || [ "$COMMIT_COUNT" -gt 0 ]; then
    HAS_CHANGES=1
fi
HAS_SOLUTION=0
if [ -f "$SOLUTION_FILE" ] && [ "$(wc -c < "$SOLUTION_FILE" 2>/dev/null || echo 0)" -ge 200 ]; then
    HAS_SOLUTION=1
fi

if [ "$HAS_CHANGES" -eq 0 ] && [ "$HAS_SOLUTION" -eq 0 ]; then
    echo "No code changes and no solution.md — agent did not execute"
    echo "0.0" > /logs/verifier/reward.txt
write_invalid_output_vr "missing_required_output" "Agent did not produce required output"
exit 0
fi

# ── IR metrics pipeline ──────────────────────────────────────────────────
if [ "$HAS_SOLUTION" -eq 1 ]; then
    run_ir_pipeline "$SOLUTION_FILE" "/tests/ground_truth.json" "/logs/verifier/ir_metrics.json"
else
    # Extract files from git diff if no solution.md
    load_ground_truth "/tests/ground_truth.json"
    AGENT_FILES=()
    while IFS= read -r f; do
        [ -n "$f" ] && AGENT_FILES+=("$f")
    done < <(git diff --name-only 2>/dev/null; git diff --cached --name-only 2>/dev/null)
    if [ -n "$ORIGIN_REF" ]; then
        while IFS= read -r f; do
            [ -n "$f" ] && AGENT_FILES+=("$f")
        done < <(git diff --name-only "$ORIGIN_REF..HEAD" 2>/dev/null)
    fi
    compute_ir_metrics "/tests/ground_truth.json"
    compute_dep_accuracy
    write_ir_metrics "/logs/verifier/ir_metrics.json"
fi

# ── Task quality scoring ─────────────────────────────────────────────────
QUALITY_SCORE=0
QUALITY_MAX=10

# Check for code changes (refactoring should produce actual changes)
if [ "$HAS_CHANGES" -eq 1 ]; then
    QUALITY_SCORE=$((QUALITY_SCORE + 3))
    echo "[x] Code changes detected"
else
    echo "[ ] No code changes (solution.md only)"
fi

# Check for structured output
if [ "$HAS_SOLUTION" -eq 1 ]; then
    if grep -qiE '^##\s+Code Changes' "$SOLUTION_FILE"; then
        QUALITY_SCORE=$((QUALITY_SCORE + 2))
        echo "[x] Has 'Code Changes' section"
    else
        echo "[ ] Missing 'Code Changes' section"
    fi

    # Check completeness: no stale references mentioned
    if grep -qiE '(stale|remaining|TODO|FIXME|not.updated)' "$SOLUTION_FILE"; then
        echo "[~] Possible incomplete refactoring noted"
    else
        QUALITY_SCORE=$((QUALITY_SCORE + 2))
        echo "[x] No stale reference warnings"
    fi

    if grep -qiE '^##\s+(Analysis|Verification)' "$SOLUTION_FILE"; then
        QUALITY_SCORE=$((QUALITY_SCORE + 1))
        echo "[x] Has 'Analysis' section"
    fi
fi

# Check compilation (Go)
COMPILE_CMD="go build ./pkg/scheduler/..."
if eval "$COMPILE_CMD" 2>/logs/verifier/build_errors.txt; then
    QUALITY_SCORE=$((QUALITY_SCORE + 2))
    echo "[x] Compilation passed"
else
    echo "[ ] Compilation failed"
fi

TASK_QUALITY=$(awk "BEGIN {printf \"%.2f\", $QUALITY_SCORE / $QUALITY_MAX}")
echo "Task quality: $TASK_QUALITY ($QUALITY_SCORE / $QUALITY_MAX)"

# ── Composite score ──────────────────────────────────────────────────────
SCORE=$(composite_score "$TASK_QUALITY" "$IR_RECALL" "$IR_PRECISION" "$DEP_ACCURACY")

echo "$SCORE" > /logs/verifier/reward.txt
write_validation_result "$SCORE"
echo ""
echo "[x] Tests completed - Score: $SCORE (quality=$TASK_QUALITY recall=$IR_RECALL precision=$IR_PRECISION dep=$DEP_ACCURACY)"
