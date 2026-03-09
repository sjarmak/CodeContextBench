#!/bin/bash
# Reward: checklist (0.0-1.0) — task-specific evaluation criteria
# TAC Task Verification: sde-implement-hyperloglog
set -e

# sg_only_env: restore full repo before verification (no-op for regular runs)
[ -f /tmp/.sg_only_mode ] && [ -f /tests/sgonly_verifier_wrapper.sh ] && source /tests/sgonly_verifier_wrapper.sh


TRAJECTORY_PATH="${TRAJECTORY_PATH:-/logs/trajectory.jsonl}"
OUTPUT_PATH="/logs/tac_result.json"
PASS_THRESHOLD="1.0"

if [ ! -f "$TRAJECTORY_PATH" ]; then
    echo '[]' > "$TRAJECTORY_PATH"
fi

echo "Running TAC evaluator for sde-implement-hyperloglog..."
cd /utils

# Initialize TAC environment (sets up /etc/hosts and resets services)
if [ -f "/utils/init.sh" ]; then
    SERVER_HOSTNAME="${TAC_SERVER_HOSTNAME:-localhost}" bash /utils/init.sh || true
fi

DECRYPTION_KEY="${DECRYPTION_KEY:-theagentcompany is all you need}" \
python_default /utils/eval.py \
    --trajectory_path "$TRAJECTORY_PATH" \
    --result_path "$OUTPUT_PATH" \
    2>&1 || {
    echo "TAC evaluator failed"
    echo '{"score": 0, "checkpoints": [], "error": "Evaluator failed"}' > "$OUTPUT_PATH"
}

mkdir -p /logs/verifier

write_validation_result() {
    python3 - "$OUTPUT_PATH" "$PASS_THRESHOLD" <<'PYEOF'
import json
import re
import sys

result_path, pass_threshold = sys.argv[1:3]
threshold = float(pass_threshold)
status = "scored"
reward = 0.0
result_payload = {}

try:
    with open(result_path) as f:
        result_payload = json.load(f)
except FileNotFoundError:
    status = "verifier_error"
    result_payload = {"error": f"Missing TAC result payload at {result_path}"}
except Exception as exc:
    status = "verifier_error"
    result_payload = {"error": f"Failed to parse TAC result payload: {exc}"}

if status == "scored":
    final_score = result_payload.get("final_score")
    if isinstance(final_score, dict):
        total = final_score.get("total", 0) or 0
        result = final_score.get("result", 0) or 0
        try:
            reward = round(float(result) / float(total), 4) if float(total) > 0 else 0.0
        except (TypeError, ValueError, ZeroDivisionError):
            reward = 0.0
            status = "verifier_error"
    elif "score" in result_payload:
        try:
            reward = float(result_payload.get("score", 0.0) or 0.0)
        except (TypeError, ValueError):
            reward = 0.0
            status = "verifier_error"
    else:
        status = "verifier_error"
        result_payload.setdefault("error", "TAC payload did not include final_score or score")

if result_payload.get("error"):
    status = "verifier_error"
    reward = 0.0

def slugify(value: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return value or "unnamed_check"

checks = {}
for index, checkpoint in enumerate(result_payload.get("checkpoints", []), start=1):
    if isinstance(checkpoint, dict):
        raw_name = (
            checkpoint.get("name")
            or checkpoint.get("title")
            or checkpoint.get("description")
            or checkpoint.get("id")
            or f"checkpoint_{index}"
        )
        key = slugify(str(raw_name))
        value = checkpoint.get("score")
        if value is None and isinstance(checkpoint.get("passed"), bool):
            value = 1.0 if checkpoint["passed"] else 0.0
        if value is None:
            value = checkpoint.get("result")
        try:
            checks[key] = float(value)
        except (TypeError, ValueError):
            continue

failure = None
if status != "scored":
    failure = {
        "code": "verifier_exception",
        "message": str(result_payload.get("error") or "TAC verifier did not produce a usable result"),
        "stage": "scoring",
    }

payload = {
    "schema_version": "validation_result.v1alpha1",
    "status": status,
    "scorable": status == "scored",
    "scorer_family": "checklist",
    "reward": reward,
    "pass_threshold": threshold,
    "passed": status == "scored" and reward >= threshold,
    "output_contract": {
        "mode": "unspecified",
        "primary_path": None,
        "required_artifact": False,
    },
    "sub_scores": {"checks": checks} if checks else {},
    "failure": failure,
    "legacy": {
        "reward_json": result_payload,
    },
}

details = {}
if isinstance(result_payload.get("final_score"), dict):
    details["final_score"] = result_payload["final_score"]
if result_payload.get("checkpoints") is not None:
    details["checkpoints"] = result_payload.get("checkpoints")
if details:
    payload["details"] = details

with open("/logs/verifier/validation_result.json", "w") as f:
    json.dump(payload, f, indent=2)
PYEOF
}

if [ -f "$OUTPUT_PATH" ]; then
    SCORE=$(python3 -c "
import json
d = json.load(open('$OUTPUT_PATH'))
if 'final_score' in d:
    fs = d['final_score']
    total = fs.get('total', 0)
    print(round(fs['result'] / total, 4) if total > 0 else 0)
elif 'score' in d:
    print(d['score'])
else:
    print(0)
" 2>/dev/null || echo "0")
    echo "TAC Score: $SCORE"
    echo "$SCORE" > /logs/verifier/reward.txt
    cp "$OUTPUT_PATH" /logs/verifier/reward.json 2>/dev/null || true
    write_validation_result
    exit 0
else
    echo "0.0" > /logs/verifier/reward.txt
    python3 - <<'PYEOF'
import json

fallback = {"score": 0.0, "error": "TAC evaluator did not produce /logs/tac_result.json"}
with open("/logs/verifier/reward.json", "w") as f:
    json.dump(fallback, f, indent=2)
PYEOF
    write_validation_result
    exit 0
fi
