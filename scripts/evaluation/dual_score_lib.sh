#!/bin/bash
# dual_score_lib.sh — Produces two independent scores per task run.
#
# Source this at the END of test.sh / eval.sh, AFTER the primary verifier
# has written /logs/verifier/reward.txt with the direct-edit score.
#
# This library:
#   1. Reads the already-written reward.txt as reward_direct
#   2. Independently scores /workspace/answer.json as reward_artifact
#   3. Writes:
#      - /logs/verifier/reward_direct.txt  (score from agent's file edits)
#      - /logs/verifier/reward_artifact.txt (score from answer.json)
#      - Updates /logs/verifier/validation_result.json with both sub-scores
#      - reward.txt is LEFT AS-IS (backward compat)
#
# Usage in test.sh:
#   #!/bin/bash
#   set -euo pipefail
#   # ... existing verifier logic ...
#   # (writes reward.txt as usual)
#   #
#   # Dual-score: independently score answer.json
#   [ -f /tests/dual_score_lib.sh ] && source /tests/dual_score_lib.sh
#
# For eval.sh tasks (Org), append at the bottom after the existing score write.
#
# Environment variables (set by caller or defaults):
#   ANSWER_JSON_PATH  — path to answer.json (default: /workspace/answer.json)
#   TASK_SPEC_PATH    — path to task_spec.json for oracle checks (optional)
#   ORACLE_CHECKS     — path to oracle_checks.py (optional)
#   PROMOTED_VERIFIER — path to promoted_verifier.py (optional)
#   TARGET_SUITE      — suite name for promoted_verifier weights (optional)
#   DUAL_SCORE_SKIP   — set to "true" to skip dual scoring (for debugging)

if [ "${DUAL_SCORE_SKIP:-false}" = "true" ]; then
    return 0 2>/dev/null || true
fi

ANSWER_JSON_PATH="${ANSWER_JSON_PATH:-/workspace/answer.json}"
REWARD_PATH="/logs/verifier/reward.txt"
REWARD_DIRECT_PATH="/logs/verifier/reward_direct.txt"
REWARD_ARTIFACT_PATH="/logs/verifier/reward_artifact.txt"

mkdir -p /logs/verifier

# ── Step 1: Capture direct score from existing reward.txt ─────────────────
_REWARD_DIRECT="0.0"
if [ -f "$REWARD_PATH" ]; then
    _REWARD_DIRECT="$(cat "$REWARD_PATH" | head -1 | tr -d '[:space:]')"
fi
# Validate it's a number
if ! python3 -c "float('$_REWARD_DIRECT')" 2>/dev/null; then
    _REWARD_DIRECT="0.0"
fi
echo "$_REWARD_DIRECT" > "$REWARD_DIRECT_PATH"
echo "[dual_score] reward_direct = $_REWARD_DIRECT" >&2

# ── Step 2: Score answer.json independently ───────────────────────────────
_REWARD_ARTIFACT="0.0"

if [ ! -f "$ANSWER_JSON_PATH" ]; then
    echo "[dual_score] answer.json not found at $ANSWER_JSON_PATH — reward_artifact = 0.0" >&2
    echo "0.0" > "$REWARD_ARTIFACT_PATH"
else
    echo "[dual_score] Scoring answer.json independently..." >&2

    # Strategy: use the best available scorer
    # Priority: promoted_verifier.py > oracle_checks.py > structural heuristic
    _ARTIFACT_SCORED=false

    # Try promoted_verifier.py (suite-weighted oracle checks)
    if [ "$_ARTIFACT_SCORED" = "false" ] && \
       [ -f "${PROMOTED_VERIFIER:-/tests/promoted_verifier.py}" ] && \
       [ -f "${TASK_SPEC_PATH:-/tests/task_spec.json}" ] && \
       [ -n "${TARGET_SUITE:-}" ]; then
        _PV="${PROMOTED_VERIFIER:-/tests/promoted_verifier.py}"
        _TS="${TASK_SPEC_PATH:-/tests/task_spec.json}"
        _ARTIFACT_RESULT="/logs/verifier/artifact_validation_result.json"
        _REWARD_ARTIFACT=$(python3 "$_PV" \
            --answer "$ANSWER_JSON_PATH" \
            --spec "$_TS" \
            --suite "$TARGET_SUITE" \
            --output "$_ARTIFACT_RESULT" \
            2>/dev/null | tail -1) || true
        if python3 -c "float('${_REWARD_ARTIFACT}')" 2>/dev/null; then
            _ARTIFACT_SCORED=true
            echo "[dual_score] Scored via promoted_verifier ($TARGET_SUITE)" >&2
        else
            _REWARD_ARTIFACT="0.0"
        fi
    fi

    # Try oracle_checks.py (equal-weight oracle checks)
    if [ "$_ARTIFACT_SCORED" = "false" ] && \
       [ -f "${ORACLE_CHECKS:-/tests/oracle_checks.py}" ] && \
       [ -f "${TASK_SPEC_PATH:-/tests/task_spec.json}" ]; then
        _OC="${ORACLE_CHECKS:-/tests/oracle_checks.py}"
        _TS="${TASK_SPEC_PATH:-/tests/task_spec.json}"
        _REWARD_ARTIFACT=$(python3 "$_OC" \
            --answer "$ANSWER_JSON_PATH" \
            --spec "$_TS" \
            2>/dev/null | tail -1) || true
        if python3 -c "float('${_REWARD_ARTIFACT}')" 2>/dev/null; then
            _ARTIFACT_SCORED=true
            echo "[dual_score] Scored via oracle_checks" >&2
        else
            _REWARD_ARTIFACT="0.0"
        fi
    fi

    # Fallback: structural heuristic (answer.json exists and has content)
    if [ "$_ARTIFACT_SCORED" = "false" ]; then
        _REWARD_ARTIFACT=$(python3 - "$ANSWER_JSON_PATH" <<'PYEOF'
import json, sys, re

path = sys.argv[1]
try:
    with open(path) as f:
        raw = f.read()
    # Strip markdown fences
    m = re.search(r'```(?:json)?\s*\n(.*?)```', raw, re.DOTALL)
    if m:
        raw = m.group(1).strip()
    data = json.loads(raw)
    if not isinstance(data, dict):
        print("0.0")
        sys.exit(0)
except (json.JSONDecodeError, FileNotFoundError, ValueError):
    print("0.0")
    sys.exit(0)

score = 0.0
components = 0

# Has analysis with content?
analysis = data.get("analysis", {})
if isinstance(analysis, dict):
    if analysis.get("summary") or analysis.get("reasoning"):
        score += 0.3
        components += 1
    files_examined = analysis.get("files_examined", [])
    if isinstance(files_examined, list) and len(files_examined) > 0:
        score += 0.2
        components += 1

# Has changes with diffs?
changes = data.get("changes", [])
if isinstance(changes, list) and len(changes) > 0:
    valid_changes = sum(1 for c in changes if c.get("file") and c.get("diff"))
    if valid_changes > 0:
        score += 0.3
        components += 1

# Has files/symbols/chain (oracle-style answer)?
for key in ("files", "symbols", "chain", "dependency_chain", "answer", "text"):
    if key in data and data[key]:
        score += 0.2
        components += 1
        break

# Cap at 1.0
score = min(score, 1.0)
print(f"{score:.4f}")
PYEOF
        ) || _REWARD_ARTIFACT="0.0"
        echo "[dual_score] Scored via structural heuristic" >&2
    fi

    echo "$_REWARD_ARTIFACT" > "$REWARD_ARTIFACT_PATH"
fi

echo "[dual_score] reward_artifact = $_REWARD_ARTIFACT" >&2

# ── Step 3: Update validation_result.json with both scores ────────────────
python3 - "$REWARD_DIRECT_PATH" "$REWARD_ARTIFACT_PATH" <<'PYEOF'
import json
import sys

direct_path, artifact_path = sys.argv[1], sys.argv[2]
vr_path = "/logs/verifier/validation_result.json"

# Read scores
try:
    with open(direct_path) as f:
        reward_direct = float(f.read().strip())
except (FileNotFoundError, ValueError):
    reward_direct = 0.0

try:
    with open(artifact_path) as f:
        reward_artifact = float(f.read().strip())
except (FileNotFoundError, ValueError):
    reward_artifact = 0.0

# Read existing validation_result.json (from primary verifier)
try:
    with open(vr_path) as f:
        vr = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    vr = {}

# Add dual scores
vr["reward_direct"] = round(reward_direct, 4)
vr["reward_artifact"] = round(reward_artifact, 4)
vr.setdefault("dual_score", {})
vr["dual_score"] = {
    "reward_direct": round(reward_direct, 4),
    "reward_artifact": round(reward_artifact, 4),
    "scorer_direct": "primary_verifier",
    "scorer_artifact": vr.get("dual_score", {}).get("scorer_artifact", "auto"),
}

with open(vr_path, "w") as f:
    json.dump(vr, f, indent=2)

print(f"[dual_score] Updated validation_result.json (direct={reward_direct:.4f}, artifact={reward_artifact:.4f})")
PYEOF

echo "[dual_score] Done." >&2
