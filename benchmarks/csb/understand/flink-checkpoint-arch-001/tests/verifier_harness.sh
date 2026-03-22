#!/bin/bash
# verifier_harness.sh — Shared verifier boilerplate for CodeScaleBench tasks.
#
# Provides mode handling (sg_only, artifact_only), result writing with
# no-changes guard, and dual-score finalization. Task-specific test.sh
# files source this and only define their checks.
#
# Usage in test.sh:
#   #!/bin/bash
#   source /tests/verifier_harness.sh
#   verifier_init          # handles sg_only, artifact_only, creates /logs/verifier
#
#   TOTAL=7
#   SCORE=0
#
#   # ... task-specific checks that increment SCORE ...
#
#   verifier_finalize "$SCORE" "$TOTAL"    # writes score, runs dual-score
#
# For weighted scoring (score out of 100, not N/TOTAL):
#   verifier_finalize_weighted "$SCORE_NUMERATOR" 100
#
# Configurable variables (set BEFORE calling verifier_init):
#   PASS_THRESHOLD    — minimum score to pass (default: 0.7)
#   TASK_OUTPUT       — answer.json path (default: /workspace/answer.json)
#   VERIFY_WORKSPACE  — workspace root (default: /workspace)
#
# ── Guard: only load once ────────────────────────────────────────────────────
[ "${_VERIFIER_HARNESS_LOADED:-}" = "1" ] && return 0
_VERIFIER_HARNESS_LOADED=1

# ── Defaults ─────────────────────────────────────────────────────────────────
TASK_OUTPUT="${TASK_OUTPUT:-/workspace/answer.json}"
PASS_THRESHOLD="${PASS_THRESHOLD:-0.7}"
VERIFY_WORKSPACE="${VERIFY_WORKSPACE:-/workspace}"
OUTPUT_CONTRACT_MODE="${OUTPUT_CONTRACT_MODE:-answer_json_bridge}"
OUTPUT_PRIMARY_PATH="${OUTPUT_PRIMARY_PATH:-$TASK_OUTPUT}"
ARTIFACT_REQUIRED="${ARTIFACT_REQUIRED:-false}"

# ── verifier_init ────────────────────────────────────────────────────────────
# Handles mode sourcing (sg_only, artifact_only), creates log dirs,
# and exits early if artifact is missing/empty.
verifier_init() {
    set -euo pipefail

    # Create log directory
    mkdir -p /logs/verifier

    # Restore full repo if sg_only mode
    if [ -f /tmp/.sg_only_mode ] && [ -f /tests/sgonly_verifier_wrapper.sh ]; then
        source /tests/sgonly_verifier_wrapper.sh
    fi

    # Parse answer.json if artifact_only mode
    if [ -f /tmp/.artifact_only_mode ] && [ -f /tests/answer_json_verifier_harness.sh ]; then
        source /tests/answer_json_verifier_harness.sh
    fi

    # Set WORKSPACE from VERIFY_REPO (set by artifact lib) or default
    WORKSPACE="${VERIFY_REPO:-$VERIFY_WORKSPACE}"
    export WORKSPACE

    # Update contract mode if artifact_only
    if [ "$OUTPUT_CONTRACT_MODE" = "repo_state" ]; then
        OUTPUT_PRIMARY_PATH=""
    elif [ "${ARTIFACT_ONLY:-false}" = "true" ]; then
        ARTIFACT_REQUIRED=true
    fi

    # Git safe directory
    git config --global --add safe.directory "$WORKSPACE" 2>/dev/null || true

    # Early exit: artifact mode but answer.json missing
    if [ "${ARTIFACT_ONLY:-false}" = "true" ] && [ "${ANSWER_JSON_MISSING:-false}" = "true" ]; then
        write_invalid_output "missing_required_output" \
            "answer.json not found at ${ANSWER_JSON:-$TASK_OUTPUT}"
        exit 0
    fi

    # Early exit: artifact mode but no code changes in answer.json
    if [ "${ARTIFACT_ONLY:-false}" = "true" ] && [ "${ANSWER_JSON_NO_CHANGES:-false}" = "true" ]; then
        write_scored_result "0.0" "no_code_changes" "0" "0"
        exit 0
    fi
}

# ── write_invalid_output ─────────────────────────────────────────────────────
# Called when the agent's output is missing or invalid.
# Args: $1=error_code $2=error_message
write_invalid_output() {
    local code="$1"
    local message="$2"
    python3 - "$code" "$message" "$OUTPUT_CONTRACT_MODE" "$OUTPUT_PRIMARY_PATH" "$ARTIFACT_REQUIRED" "$PASS_THRESHOLD" <<'PYEOF'
import json
import sys

code, message, mode, primary_path, required_artifact, pass_threshold = sys.argv[1:7]
payload = {
    "schema_version": "validation_result.v1alpha1",
    "status": "invalid_output",
    "scorable": False,
    "scorer_family": "repo_state_heuristic",
    "reward": 0.0,
    "pass_threshold": float(pass_threshold),
    "passed": False,
    "output_contract": {
        "mode": mode,
        "primary_path": primary_path or None,
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
with open("/logs/verifier/reward.txt", "w") as f:
    f.write("0.0000\n")
PYEOF
}

# ── write_scored_result ──────────────────────────────────────────────────────
# Writes validation_result.json and reward.txt with no-changes guard.
# Args: $1=score $2=reason(opt) $3=passed_checks(opt) $4=total_checks(opt)
write_scored_result() {
    local score="$1"
    local reason="${2:-}"
    local passed_checks="${3:-}"
    local total_checks="${4:-}"
    env \
        VALIDATION_SCORE="$score" \
        VALIDATION_REASON="$reason" \
        VALIDATION_PASSED_CHECKS="$passed_checks" \
        VALIDATION_TOTAL_CHECKS="$total_checks" \
        CHANGE_UNSTAGED="${UNSTAGED_COUNT:-${UNSTAGED:-0}}" \
        CHANGE_STAGED="${STAGED_COUNT:-${STAGED:-0}}" \
        CHANGE_UNTRACKED="${UNTRACKED_COUNT:-${UNTRACKED:-0}}" \
        CHANGE_COMMITS="${COMMIT_COUNT:-${COMMITS:-0}}" \
        VALIDATION_OUTPUT_PATH="${VALIDATION_OUTPUT_PATH:-}" \
        python3 - "$OUTPUT_CONTRACT_MODE" "$OUTPUT_PRIMARY_PATH" "$ARTIFACT_REQUIRED" "$PASS_THRESHOLD" <<'PYEOF'
import json
import os
import sys

mode, primary_path, required_artifact, pass_threshold = sys.argv[1:5]
reward = float(os.environ.get("VALIDATION_SCORE", "0.0") or 0.0)
threshold = float(pass_threshold)
checks = {"heuristic_score": reward}
details = {}
reason = os.environ.get("VALIDATION_REASON")
if reason:
    details["reason"] = reason
passed_checks_raw = os.environ.get("VALIDATION_PASSED_CHECKS", "")
total_checks_raw = os.environ.get("VALIDATION_TOTAL_CHECKS", "")
if passed_checks_raw and total_checks_raw:
    try:
        passed_checks = float(passed_checks_raw)
        total_checks = float(total_checks_raw)
    except ValueError:
        passed_checks = None
        total_checks = None
    if passed_checks is not None and total_checks and total_checks > 0:
        checks["passed_checks_ratio"] = round(passed_checks / total_checks, 4)
        details["passed_checks"] = int(passed_checks) if passed_checks == int(passed_checks) else passed_checks
        details["total_checks"] = int(total_checks) if total_checks == int(total_checks) else total_checks
change_detection = {
    "unstaged": int(os.environ.get("CHANGE_UNSTAGED", "0") or 0),
    "staged": int(os.environ.get("CHANGE_STAGED", "0") or 0),
    "untracked": int(os.environ.get("CHANGE_UNTRACKED", "0") or 0),
    "commits": int(os.environ.get("CHANGE_COMMITS", "0") or 0),
}
if any(change_detection.values()):
    checks["change_detected"] = 1.0
    details["change_detection"] = change_detection
else:
    # No-changes guard: verify via git that the agent actually modified the repo.
    # If not, force reward to 0.0 to prevent false-positive scores on unmodified repos.
    import subprocess as _sp
    _verify = os.environ.get("VERIFY_REPO") or os.environ.get("TASK_REPO_ROOT") or "/workspace"
    try:
        _has_changes = False
        _d = _sp.run(["git", "diff", "HEAD", "--stat"], capture_output=True, text=True, cwd=_verify, timeout=5)
        if _d.stdout.strip():
            _has_changes = True
        _u = _sp.run(["git", "ls-files", "--others", "--exclude-standard"], capture_output=True, text=True, cwd=_verify, timeout=5)
        if _u.stdout.strip():
            _has_changes = True
        if not _has_changes:
            for _ref in ["origin/HEAD", "origin/main", "origin/master"]:
                _rv = _sp.run(["git", "rev-parse", "--verify", _ref], capture_output=True, text=True, cwd=_verify, timeout=5)
                if _rv.returncode == 0:
                    _cd = _sp.run(["git", "diff", _ref, "HEAD", "--stat"], capture_output=True, text=True, cwd=_verify, timeout=5)
                    if _cd.stdout.strip():
                        _has_changes = True
                    break
        if not _has_changes:
            reward = 0.0
            checks["no_changes_guard"] = 0.0
            details["no_changes_guard"] = "git confirmed zero agent changes"
    except Exception:
        pass
output_path = os.environ.get("VALIDATION_OUTPUT_PATH")
if output_path:
    details["output_path"] = output_path
payload = {
    "schema_version": "validation_result.v1alpha1",
    "status": "scored",
    "scorable": True,
    "scorer_family": "repo_state_heuristic",
    "reward": reward,
    "pass_threshold": threshold,
    "passed": reward >= threshold,
    "output_contract": {
        "mode": mode,
        "primary_path": primary_path or None,
        "required_artifact": required_artifact == "true",
    },
    "sub_scores": {"checks": checks},
    "failure": None,
}
if details:
    payload["details"] = details
with open("/logs/verifier/validation_result.json", "w") as f:
    json.dump(payload, f, indent=2)
with open("/logs/verifier/reward.txt", "w") as f:
    f.write(f'{payload["reward"]:.4f}\n')
PYEOF
}

# ── verifier_finalize ────────────────────────────────────────────────────────
# Computes final score from SCORE/TOTAL, writes result, runs dual-score.
# Args: $1=score(int) $2=total(int)
verifier_finalize() {
    local score="$1"
    local total="$2"

    local final_score
    final_score=$(python3 -c "print(round($score / $total, 4))" 2>/dev/null || echo "0.0")

    echo "Score: $score / $total ($final_score)"
    write_scored_result "$final_score" "" "$score" "$total"

    # Dual-score: independently score both direct edits and answer.json
    [ -f /tests/dual_score_lib.sh ] && source /tests/dual_score_lib.sh
}

# ── verifier_finalize_weighted ───────────────────────────────────────────────
# For weighted scoring where score is already 0.0-1.0 or numerator/denominator.
# Args: $1=score_numerator $2=denominator (default: 100)
verifier_finalize_weighted() {
    local numerator="$1"
    local denominator="${2:-100}"

    local final_score
    final_score=$(python3 -c "print(round($numerator / $denominator, 4))" 2>/dev/null || echo "0.0")

    echo "Score: $numerator / $denominator ($final_score)"
    write_scored_result "$final_score"

    # Dual-score
    [ -f /tests/dual_score_lib.sh ] && source /tests/dual_score_lib.sh
}
