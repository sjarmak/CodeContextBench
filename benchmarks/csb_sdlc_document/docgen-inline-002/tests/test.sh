#!/bin/bash
# Reward: checklist (0.0-1.0) — documentation quality score
set -euo pipefail

[ -f /tmp/.sg_only_mode ] && [ -f /tests/sgonly_verifier_wrapper.sh ] && source /tests/sgonly_verifier_wrapper.sh
# Artifact mode: parse answer.json, extract analysis text
if [ -f /tmp/.artifact_only_mode ] && [ -f /tests/answer_json_verifier_lib.sh ]; then
    source /tests/answer_json_verifier_lib.sh
fi

TASK_WORKDIR="${TASK_WORKDIR:-/workspace}"
TASK_REPO_ROOT="${TASK_REPO_ROOT:-${VERIFY_REPO:-$TASK_WORKDIR}}"
VERIFY_REPO="${VERIFY_REPO:-$TASK_REPO_ROOT}"

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


OUTPUT_FILE="/workspace/documentation.md"
# In artifact mode, populate expected output from answer.json analysis
if [ "${ARTIFACT_ONLY:-false}" = "true" ] && [ -f "${ANALYSIS_TEXT_FILE:-}" ]; then
    cp "$ANALYSIS_TEXT_FILE" "/workspace/documentation.md"
    echo "[answer_json] Copied analysis text to /workspace/documentation.md"
fi
EXTRA_FILES=""

# Fallback: search for any .md file the agent wrote
if [ ! -f "$OUTPUT_FILE" ]; then
    ALT=$(find /workspace -maxdepth 2 -name "*.md" ! -name "README*" ! -name "CONTRIBUTING*" 2>/dev/null | head -1)
    OUTPUT_FILE="${ALT:-$OUTPUT_FILE}"
fi

if [ ! -f "$OUTPUT_FILE" ]; then
    echo "No output file found at /workspace/documentation.md"
    echo "0.0" > /logs/verifier/reward.txt
write_validation_result "0.0" "{}" "null" "invalid_output"
exit 0
fi

# Write scorer script
cat > /tmp/_scorer.py << 'SCOREEOF'
import sys, re, json, os

output_path = sys.argv[1]
extra_paths = sys.argv[2:-1]
gt_path = sys.argv[-1]

try:
    content = open(output_path).read()
    gt = json.load(open(gt_path))
except Exception as e:
    print(f"Error reading files: {e}", file=sys.stderr)
    print("0.0", end="")
    sys.exit(0)

# Also read any extra source files (for inline doc tasks)
extra_content = ""
for ep in extra_paths:
    if ep != gt_path and os.path.isfile(ep):
        try:
            extra_content += "\n" + open(ep).read()
        except Exception:
            pass

full_content = content + "\n" + extra_content

weights = gt.get("weights", {})

def check_section(section_items):
    if not section_items:
        return 0.0
    total_weight = sum(item.get("weight", 1.0 / len(section_items)) for item in section_items)
    section_score = 0.0
    for item in section_items:
        item_weight = item.get("weight", 1.0 / len(section_items))
        patterns = item.get("patterns", [])
        matched = False
        for p in patterns:
            try:
                if re.search(p, full_content, re.MULTILINE | re.IGNORECASE):
                    matched = True
                    break
            except re.error:
                if p.lower() in full_content.lower():
                    matched = True
                    break
        if matched:
            section_score += item_weight / total_weight if total_weight > 0 else 0.0
            print(f"  PASS: {item['description']}", file=sys.stderr)
        else:
            print(f"  FAIL: {item['description']}", file=sys.stderr)
    return section_score

total_score = 0.0
for section_key, section_weight in weights.items():
    section_items = gt.get(section_key, [])
    section_score = check_section(section_items)
    contribution = section_score * float(section_weight)
    total_score += contribution
    print(f"Section '{section_key}': {section_score:.2f} * {section_weight} = {contribution:.3f}", file=sys.stderr)

total_score = min(1.0, max(0.0, total_score))
print(f"Total score: {total_score:.2f}", file=sys.stderr)
print(f"{total_score:.2f}", end="")

SCOREEOF

SCORE=$(python3 /tmp/_scorer.py "$OUTPUT_FILE" $EXTRA_FILES /tests/ground_truth.json 2>&1 | tail -1)
# Re-run to get clean score (stderr goes to log, stdout is score)
SCORE=$(python3 /tmp/_scorer.py "$OUTPUT_FILE" $EXTRA_FILES /tests/ground_truth.json 2>/dev/null)

echo "$SCORE" > /logs/verifier/reward.txt
write_validation_result "${FINAL_SCORE:-$SCORE}" "{}" "null" "scored"
echo "Score: $SCORE"
exit 0
