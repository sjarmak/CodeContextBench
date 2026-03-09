#!/bin/bash

# sg_only_env: restore full repo before verification (no-op for regular runs)
[ -f /tmp/.sg_only_mode ] && [ -f /tests/sgonly_verifier_wrapper.sh ] && source /tests/sgonly_verifier_wrapper.sh

set -eo pipefail
# RepoQA SR-QA Verification Script

# SR-QA tasks: verifier only does JSON string matching (function name + path).
# sgonly_verifier_wrapper clone is NOT needed — skipped to avoid 39+ min
# Firefox mirror clone that causes VerifierTimeoutError on MCP runs.

echo "Starting RepoQA verifier..." 1>&2
TASK_WORKDIR="${TASK_WORKDIR:-/app}"
TASK_REPO_ROOT="${TASK_REPO_ROOT:-$TASK_WORKDIR}"
TASK_OUTPUT="${TASK_OUTPUT:-$TASK_WORKDIR/solution.json}"
cd "$TASK_REPO_ROOT" || { echo "ERROR: Cannot cd to $TASK_REPO_ROOT"; exit 1; }
mkdir -p /logs/verifier

if [ ! -f /tests/ground_truth.json ]; then
    echo "ERROR: No ground_truth.json found at /tests/ground_truth.json"
    echo '{"score": 0.0}' > /logs/verifier/reward.json
    echo "0.0" > /logs/verifier/reward.txt
    exit 0
fi

SOLUTION_FILE="$TASK_OUTPUT"
if [ ! -f "$SOLUTION_FILE" ]; then
    echo "ERROR: Agent did not create solution.json in /app/"
    echo '{"score": 0.0}' > /logs/verifier/reward.json
    echo "0.0" > /logs/verifier/reward.txt
    exit 0
fi

VERIFY_SCRIPT="$(mktemp /logs/verifier/verify_XXXXXX.py)"
cat > "$VERIFY_SCRIPT" << 'PYEOF'
import json, os, sys, re
sys.path.insert(0, "/tests")
from verifiers import SemanticRetrievalQAVerifier

try:
    with open("/tests/ground_truth.json") as f:
        ground_truth = json.load(f)
    with open(os.environ.get("TASK_OUTPUT", "/app/solution.json")) as f:
        raw = f.read()
    matches = re.findall(r"```(?:json)?\s*\n(.*?)```", raw, re.DOTALL)
    if matches:
        raw = matches[-1].strip()
    agent_output = json.loads(raw)

    verifier = SemanticRetrievalQAVerifier(ground_truth)
    result = verifier.verify(agent_output)
    reward = {"score": float(result.correct_function)}

    print(f"Correct Function: {result.correct_function:.2f}")
    print(f"Correct Path: {result.correct_path:.2f}")
    print(f"Justification: {result.justification_score:.2f}")
    print(f"Details: {result.reasoning}")

    with open("/logs/verifier/reward.json", "w") as f:
        json.dump(reward, f, indent=2)
    with open("/logs/verifier/reward.txt", "w") as f:
        f.write(str(reward["score"]))
except Exception as e:
    import traceback
    print(f"ERROR: {e}")
    traceback.print_exc()
    with open("/logs/verifier/reward.json", "w") as f:
        json.dump({"score": 0.0}, f)
    with open("/logs/verifier/reward.txt", "w") as f:
        f.write("0.0")
PYEOF

python3 "$VERIFY_SCRIPT" 2>&1 | tee /logs/verifier/verify-debug.log
exit 0
rm -f "$VERIFY_SCRIPT"
