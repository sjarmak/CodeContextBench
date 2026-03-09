#!/bin/bash
# Reward: checklist (0.0-1.0) — weighted pattern matching against ground_truth.json
# Shared checklist verifier with soft length scaling and optional canonical-SHA bypass.

set -e

# sg_only_env: restore full repo before verification (no-op for regular runs)
[ -f /tmp/.sg_only_mode ] && [ -f /tests/sgonly_verifier_wrapper.sh ] && source /tests/sgonly_verifier_wrapper.sh
# Artifact mode: parse answer.json, extract analysis text
if [ -f /tmp/.artifact_only_mode ] && [ -f /tests/answer_json_verifier_lib.sh ]; then
    source /tests/answer_json_verifier_lib.sh
fi


REPORT_PATH="${REPORT_PATH:-/logs/agent/investigation.md}"
# In artifact mode, populate expected output from answer.json analysis
if [ "${ARTIFACT_ONLY:-false}" = "true" ] && [ -f "${ANALYSIS_TEXT_FILE:-}" ]; then
    mkdir -p "/logs/agent"
    cp "$ANALYSIS_TEXT_FILE" "/logs/agent/investigation.md"
    echo "[answer_json] Copied analysis text to /logs/agent/investigation.md"
fi
GROUND_TRUTH="${GROUND_TRUTH:-/tests/ground_truth.json}"
REWARD_FILE="/logs/verifier/reward.txt"
MIN_REPORT_BYTES="${MIN_REPORT_BYTES:-100}"
# Below this, output is treated as effectively missing / unusable.
MIN_ABS_BYTES="${MIN_ABS_BYTES:-24}"

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


if [ ! -f "$GROUND_TRUTH" ]; then
    echo "ERROR: ground_truth.json not found at $GROUND_TRUTH"
    echo "0.0" > "$REWARD_FILE"
    exit 0
fi

if [ ! -f "$REPORT_PATH" ]; then
    echo "No agent output found at $REPORT_PATH"
    echo "0.0" > "$REWARD_FILE"
    exit 0
fi

REPORT_SIZE=$(wc -c < "$REPORT_PATH")
if [ "$REPORT_SIZE" -lt "$MIN_ABS_BYTES" ]; then
    echo "Agent output too small (${REPORT_SIZE} bytes, minimum usable ${MIN_ABS_BYTES})."
    echo "0.0" > "$REWARD_FILE"
    exit 0
fi

echo "Scoring agent output ($REPORT_SIZE bytes)..."
echo "Report: $REPORT_PATH"
echo "Ground truth: $GROUND_TRUTH"
echo ""

REPORT_PATH="$REPORT_PATH" GROUND_TRUTH="$GROUND_TRUTH" REWARD_FILE="$REWARD_FILE" REPORT_SIZE="$REPORT_SIZE" MIN_REPORT_BYTES="$MIN_REPORT_BYTES" python3 << 'PYEOF'
import hashlib
import json
import os
import re

REPORT_PATH = os.environ["REPORT_PATH"]
GT_PATH = os.environ["GROUND_TRUTH"]
REWARD_PATH = os.environ["REWARD_FILE"]
REPORT_SIZE = int(os.environ["REPORT_SIZE"])
MIN_REPORT_BYTES = max(1, int(os.environ["MIN_REPORT_BYTES"]))

with open(REPORT_PATH) as f:
    report = f.read()
with open(GT_PATH) as f:
    gt = json.load(f)

# Canonical source (when provided) should always score 1.0 if text is exact.
doc_sha = hashlib.sha256(report.encode("utf-8")).hexdigest().lower()
canonical_sha = ((((gt.get("ground_truth_provenance") or {}).get("canonical_source") or {}).get("sha256") or "").lower())
if canonical_sha and doc_sha == canonical_sha:
    print("Canonical source SHA match: awarding 1.0")
    with open(REWARD_PATH, "w") as f:
        f.write("1.00\n")
    raise SystemExit(0)


def check_any_pattern(patterns, text):
    for p in patterns:
        try:
            if re.search(p, text, re.IGNORECASE):
                return True
        except re.error:
            if p.lower() in text.lower():
                return True
    return False


def check_all_patterns(patterns, text):
    for p in patterns:
        try:
            if not re.search(p, text, re.IGNORECASE):
                return False
        except re.error:
            if p.lower() not in text.lower():
                return False
    return True


def score_category(items, label, use_all=False, negate=False):
    print(f"=== {label} ===")
    score = 0.0
    total = 0.0
    for item in items:
        w = float(item["weight"])
        total += w
        matched = check_all_patterns(item["patterns"], report) if use_all else check_any_pattern(item["patterns"], report)
        passed = (not matched) if negate else matched
        if passed:
            score += w
            print(f"  [x] {item['description']} (weight: {w})")
        else:
            msg = " -- wrong conclusion found" if negate else ""
            prefix = "FAIL: " if negate else ""
            print(f"  [ ] {prefix}{item['description']} (weight: {w}){msg}")
    ratio = score / total if total > 0 else (1.0 if negate else 0.0)
    print(f"  Score: {score:.2f} / {total:.2f} = {ratio:.2f}")
    print()
    return ratio


f_ratio = score_category(gt.get("required_findings", []), "Required Findings")
r_ratio = score_category(gt.get("file_references", []), "File References")
c_ratio = score_category(gt.get("causal_chain", []), "Causal Chain", use_all=True)
n_ratio = score_category(gt.get("negative_checks", []), "Negative Checks", negate=True)

weights = gt.get("weights", {
    "required_findings": 0.40,
    "file_references": 0.30,
    "causal_chain": 0.20,
    "negative_checks": 0.10,
})
base = (
    f_ratio * float(weights.get("required_findings", 0.40))
    + r_ratio * float(weights.get("file_references", 0.30))
    + c_ratio * float(weights.get("causal_chain", 0.20))
    + n_ratio * float(weights.get("negative_checks", 0.10))
)

# Soft length scaling: avoid hard 0 for concise but correct outputs.
length_factor = min(1.0, REPORT_SIZE / float(MIN_REPORT_BYTES))
final = max(0.0, min(1.0, base * length_factor))

print("=== Final Score ===")
print(f"  Base checklist: {base:.3f}")
print(f"  Length factor:  min(1.0, {REPORT_SIZE}/{MIN_REPORT_BYTES}) = {length_factor:.3f}")
print(f"  TOTAL:          {final:.2f}")

with open(REWARD_PATH, "w") as f:
    f.write(f"{final:.2f}\n")

print()
print(f"Tests completed - Score: {final:.2f}")
PYEOF
