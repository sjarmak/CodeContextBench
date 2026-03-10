#!/bin/bash
# Reward: checklist (0.0-1.0) — weighted structure and correctness checks
# Test script for VS Code stale diagnostics after git branch switch
# Verifies that:
# 1. TypeScript code compiles (type-checks)
# 2. Diagnostics-related files were modified
# 3. TypeScript language features contain git/branch awareness
# 4. No regressions in diagnostics pipeline
#
# NOTE: This task also ships a static rubric JSON file with additional manual
# evaluation criteria (e.g., architecture_understanding, code_quality).
# Those rubric criteria are descriptive only; this verifier scores automated
# repo-state checks and emits the canonical validation_result sidecar.

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
TASK_OUTPUT="${TASK_OUTPUT:-/workspace/answer.json}"
PASS_THRESHOLD="0.7"
ARTIFACT_REQUIRED=false
if [ "${ARTIFACT_ONLY:-false}" = "true" ]; then
    ARTIFACT_REQUIRED=true
fi

cd "$TASK_REPO_ROOT"

# Create log directories
mkdir -p /logs/verifier

CHANGES_MADE=0
TS_CHANGES=0
TYPE_CHECK_OK=0
UNIT_TEST_PASS=0

write_invalid_output() {
    local code="$1"
    local message="$2"
    python3 - "$code" "$message" "$TASK_OUTPUT" "$ARTIFACT_REQUIRED" "$PASS_THRESHOLD" <<'PYEOF'
import json
import sys

code, message, primary_path, required_artifact, pass_threshold = sys.argv[1:6]
payload = {
    "schema_version": "validation_result.v1alpha1",
    "status": "invalid_output",
    "scorable": False,
    "scorer_family": "repo_state_heuristic",
    "reward": 0.0,
    "pass_threshold": float(pass_threshold),
    "passed": False,
    "output_contract": {
        "mode": "answer_json_bridge",
        "primary_path": primary_path,
        "required_artifact": required_artifact == "true",
    },
    "sub_scores": {},
    "failure": {
        "code": code,
        "message": message,
        "stage": "output_validation",
    },
}
with open("/logs/verifier/validation_result.json", "w") as f:
    json.dump(payload, f, indent=2)
PYEOF
    echo "0.0" > /logs/verifier/reward.txt
}

write_scored_result() {
    local score="$1"
    local reason="${2:-}"
    VALIDATION_SCORE="$score" \
    VALIDATION_REASON="$reason" \
    UNSTAGED_COUNT="${UNSTAGED_COUNT:-0}" \
    STAGED_COUNT="${STAGED_COUNT:-0}" \
    UNTRACKED_COUNT="${UNTRACKED_COUNT:-0}" \
    COMMIT_COUNT="${COMMIT_COUNT:-0}" \
    python3 - "$TASK_OUTPUT" "$ARTIFACT_REQUIRED" "$PASS_THRESHOLD" <<'PYEOF'
import json
import os
import sys

primary_path, required_artifact, pass_threshold = sys.argv[1:4]
reward = float(os.environ.get("VALIDATION_SCORE", "0.0"))
threshold = float(pass_threshold)
checks = {
    "changes_made": float(os.environ.get("CHANGES_MADE", "0") or 0),
    "ts_changes": float(os.environ.get("TS_CHANGES", "0") or 0),
    "type_check_ok": float(os.environ.get("TYPE_CHECK_OK", "0") or 0),
    "unit_test_pass": float(os.environ.get("UNIT_TEST_PASS", "0") or 0),
}
details = {
    "check_weights": {
        "changes_made": 0.2,
        "ts_changes": 0.2,
        "type_check_ok": 0.3,
        "unit_test_pass": 0.3,
    },
    "change_detection": {
        "unstaged": int(os.environ.get("UNSTAGED_COUNT", "0") or 0),
        "staged": int(os.environ.get("STAGED_COUNT", "0") or 0),
        "untracked": int(os.environ.get("UNTRACKED_COUNT", "0") or 0),
        "commits": int(os.environ.get("COMMIT_COUNT", "0") or 0),
    },
}
reason = os.environ.get("VALIDATION_REASON")
if reason:
    details["reason"] = reason
payload = {
    "schema_version": "validation_result.v1alpha1",
    "status": "scored",
    "scorable": True,
    "scorer_family": "repo_state_heuristic",
    "reward": reward,
    "pass_threshold": threshold,
    "passed": reward >= threshold,
    "output_contract": {
        "mode": "answer_json_bridge",
        "primary_path": primary_path,
        "required_artifact": required_artifact == "true",
    },
    "sub_scores": {
        "checks": checks,
    },
    "failure": None,
    "details": details,
}
with open("/logs/verifier/validation_result.json", "w") as f:
    json.dump(payload, f, indent=2)
PYEOF
    echo "$score" > /logs/verifier/reward.txt
}

# Fix git safe.directory: the repo was cloned as root during Docker build,
# but the verifier may run as a different user. Without this, all git
# commands silently fail due to CVE-2022-24765 ownership checks.
git config --global --add safe.directory "$TASK_REPO_ROOT" 2>/dev/null || true

if [ "${ARTIFACT_ONLY:-false}" = "true" ] && [ ! -f "${ANSWER_JSON:-$TASK_OUTPUT}" ]; then
    echo "Required answer.json artifact missing at ${ANSWER_JSON:-$TASK_OUTPUT}"
    write_invalid_output "missing_required_output" \
        "answer.json not found at ${ANSWER_JSON:-$TASK_OUTPUT}"
    exit 0
fi

# Guard: if no code changes were made, the agent didn't execute successfully
# Check unstaged changes, staged changes, untracked files, AND new commits
UNSTAGED_COUNT=$(git diff --stat 2>/dev/null | wc -l)
STAGED_COUNT=$(git diff --cached --stat 2>/dev/null | wc -l)
UNTRACKED_COUNT=$(git ls-files --others --exclude-standard 2>/dev/null | wc -l)
# Detect new commits: compare HEAD to the original clone point
# Use origin refs (most reliable for shallow clones created by git clone --depth 1)
COMMIT_COUNT=0
ORIGIN_REF=""
for ref in origin/master origin/main origin/HEAD; do
    if git rev-parse "$ref" >/dev/null 2>&1; then
        ORIGIN_REF="$ref"
        break
    fi
done
if [ -n "$ORIGIN_REF" ]; then
    COMMIT_COUNT=$(git log --oneline "$ORIGIN_REF..HEAD" 2>/dev/null | wc -l)
elif git rev-parse FETCH_HEAD >/dev/null 2>&1; then
    COMMIT_COUNT=$(git log --oneline FETCH_HEAD..HEAD 2>/dev/null | wc -l)
else
    # Fallback: in a --depth 1 clone there is 1 commit; more means agent committed
    TOTAL_COMMITS=$(git log --oneline 2>/dev/null | wc -l)
    if [ "$TOTAL_COMMITS" -gt 1 ]; then
        COMMIT_COUNT=$((TOTAL_COMMITS - 1))
    fi
fi
echo "Change detection: unstaged=$UNSTAGED_COUNT staged=$STAGED_COUNT untracked=$UNTRACKED_COUNT commits=$COMMIT_COUNT (origin_ref=${ORIGIN_REF:-none})"
if [ "$UNSTAGED_COUNT" -eq 0 ] && [ "$STAGED_COUNT" -eq 0 ] && [ "$UNTRACKED_COUNT" -eq 0 ] && [ "$COMMIT_COUNT" -eq 0 ]; then
    echo "No code changes detected — agent did not execute successfully"
    write_scored_result "0.0" "no_code_changes"
    echo ""
    echo "[ ] Tests completed - Score: 0.0 (no changes)"
    exit 0
fi

echo "Running VS Code test suite..."

# ── Install dependencies if missing (needed after sg_only clone-at-verify) ─
if [ ! -d "node_modules" ] && [ -f "package.json" ]; then
    echo "Installing npm dependencies (post-clone)..."
    npm install --legacy-peer-deps 2>&1 | tail -5 || true
fi

# ── TypeScript type-check ────────────────────────────────────────────────
# VS Code uses its own tsconfig files. Run tsc --noEmit to verify the
# modified TypeScript still type-checks. If it fails, score is 0.
echo "Running TypeScript type-check..."
TYPE_CHECK_OK=1
# VS Code has multiple tsconfig projects; check the most relevant ones for
# the diagnostics task (extensions and src). Use --noEmit to avoid codegen.
# Try the specific tsconfig for typescript-language-features first, then
# fall back to a broader check on modified files only.
if [ -f "extensions/typescript-language-features/tsconfig.json" ]; then
    ./node_modules/.bin/tsc --noEmit -p extensions/typescript-language-features/tsconfig.json 2>/logs/verifier/typecheck_errors.txt && TSC_RC=0 || TSC_RC=$?
    if [ "$TSC_RC" -ne 0 ]; then
        echo "FAIL: TypeScript type-check failed for typescript-language-features"
        TYPE_CHECK_OK=0
    fi
fi

# Note: src/tsconfig.json covers all of VS Code (>300k TS lines) and OOMs in
# the container; we only need the extension-level check for this task.

# Fallback: if no specific tsconfig was found, do a syntax-only check on
# modified .ts files using tsc --noEmit --isolatedModules
if [ "$TYPE_CHECK_OK" -eq 1 ] && [ ! -f "extensions/typescript-language-features/tsconfig.json" ]; then
    # Collect modified .ts files (committed + unstaged + staged)
    MODIFIED_TS=""
    if [ -n "$ORIGIN_REF" ]; then
        MODIFIED_TS=$(git diff --name-only "$ORIGIN_REF..HEAD" -- '*.ts' 2>/dev/null || true)
    fi
    MODIFIED_TS="$MODIFIED_TS
$(git diff --name-only -- '*.ts' 2>/dev/null || true)
$(git diff --cached --name-only -- '*.ts' 2>/dev/null || true)"
    MODIFIED_TS=$(echo "$MODIFIED_TS" | sort -u | grep -v '^$' || true)

    if [ -n "$MODIFIED_TS" ]; then
        echo "Checking $(echo "$MODIFIED_TS" | wc -l) modified .ts files..."
        echo "$MODIFIED_TS" | while read -r tsfile; do
            if [ -f "$tsfile" ]; then
                ./node_modules/.bin/tsc --noEmit --isolatedModules --skipLibCheck "$tsfile" 2>>/logs/verifier/typecheck_errors.txt || {
                    echo "FAIL: Type-check failed for $tsfile"
                    # Signal failure via a marker file since we're in a subshell
                    touch /logs/verifier/typecheck_failed
                }
            fi
        done
        if [ -f /logs/verifier/typecheck_failed ]; then
            TYPE_CHECK_OK=0
            rm -f /logs/verifier/typecheck_failed
        fi
    fi
fi

if [ "$TYPE_CHECK_OK" -eq 0 ]; then
    echo "TypeScript type-check failed — score set to 0.0"
    write_scored_result "0.0" "type_check_failure"
    echo ""
    echo "[ ] Tests completed - Score: 0.0 (type-check failure)"
    exit 0
fi
echo "[x] TypeScript type-check passed"

# ── Unit tests (best-effort) ────────────────────────────────────────────
# Run tests for the typescript-language-features extension if available.
# Failures reduce score but don't zero it out.
UNIT_TEST_PASS=1
if [ -f "extensions/typescript-language-features/package.json" ]; then
    # VS Code extensions use npm test or a custom test runner
    cd extensions/typescript-language-features
    timeout 600 npm test 2>/logs/verifier/test_errors.txt && TEST_RC=0 || TEST_RC=$?
    cd "$TASK_REPO_ROOT"
    if [ "$TEST_RC" -eq 0 ]; then
        echo "[x] TypeScript language features tests passed"
    else
        echo "NOTE: TypeScript language features tests failed (rc=$TEST_RC)"
        UNIT_TEST_PASS=0
    fi
else
    echo "NOTE: No typescript-language-features package.json found, skipping tests"
fi

# ── Keyword-based scoring (secondary signal) ─────────────────────────────
# Check if diagnostics-related changes were made (unstaged OR committed)
DIFF_REF=""
if [ -n "$ORIGIN_REF" ]; then
    DIFF_REF="$ORIGIN_REF..HEAD"
fi
CHANGED_FILES=""
if [ -n "$DIFF_REF" ]; then
    CHANGED_FILES=$(git diff --name-only "$DIFF_REF" 2>/dev/null)
fi
# Also include any unstaged/staged changes
CHANGED_FILES="$CHANGED_FILES
$(git diff --name-only 2>/dev/null)
$(git diff --cached --name-only 2>/dev/null)"

RELEVANT_FILES=$(echo "$CHANGED_FILES" | grep -E "(diagnostics|extension)" | sort -u || true)
RELEVANT_COUNT=$(echo "$RELEVANT_FILES" | grep -v '^$' | wc -l)
if [ "$RELEVANT_COUNT" -ge 2 ]; then
    echo "[x] Diagnostics-related files modified ($RELEVANT_COUNT files)"
    echo "$RELEVANT_FILES" | head -5
    CHANGES_MADE=1
elif [ "$RELEVANT_COUNT" -eq 1 ]; then
    echo "NOTE: Only 1 diagnostics-related file changed (need >= 2 for cross-module fix)"
    CHANGES_MADE=0
else
    echo "NOTE: No diagnostics-related changes detected"
    CHANGES_MADE=0
fi

# Check for specific TypeScript service modifications
if grep -r "git\|branch\|refresh" src/vs/workbench/contrib/typescript-language-features 2>/dev/null | head -3; then
    echo "[x] TypeScript language features contain relevant code"
    TS_CHANGES=1
else
    echo "NOTE: No TypeScript service changes for git awareness"
    TS_CHANGES=0
fi

# ── Calculate reward ─────────────────────────────────────────────────────
# Weights: diagnostics changes=0.2, TS service changes=0.2, type-check=0.3, unit tests=0.3
SCORE_NUMERATOR=0
if [ "$CHANGES_MADE" -eq 1 ]; then
    SCORE_NUMERATOR=$((SCORE_NUMERATOR + 2))  # 0.2 * 10
fi
if [ "$TS_CHANGES" -eq 1 ]; then
    SCORE_NUMERATOR=$((SCORE_NUMERATOR + 2))  # 0.2 * 10
fi
# Type-check always passes at this point (failure exits early with 0.0)
SCORE_NUMERATOR=$((SCORE_NUMERATOR + 3))  # 0.3 * 10
if [ "$UNIT_TEST_PASS" -eq 1 ]; then
    SCORE_NUMERATOR=$((SCORE_NUMERATOR + 3))  # 0.3 * 10
fi

# Convert back to decimal (using awk for portable floating point)
SCORE=$(awk "BEGIN {printf \"%.1f\", $SCORE_NUMERATOR / 10}")

write_scored_result "$SCORE" "completed"
echo ""
echo "[x] Tests completed - Score: $SCORE"
