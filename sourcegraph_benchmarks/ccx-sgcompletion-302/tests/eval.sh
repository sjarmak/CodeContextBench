#!/bin/bash
# eval.sh — org-scale benchmark evaluator
set -euo pipefail

TASK_ID="ccx-sgcompletion-302"
TASK_WORKDIR="${TASK_WORKDIR:-/workspace}"
TASK_REPO_ROOT="${TASK_REPO_ROOT:-$TASK_WORKDIR}"
ANSWER_PATH="${TASK_OUTPUT:-$TASK_WORKDIR/answer.json}"
ORACLE_PATH="/tests/oracle_answer.json"
REWARD_PATH="/logs/verifier/reward.txt"

mkdir -p /logs/verifier
trap 'if [ ! -f "$REWARD_PATH" ]; then echo "0.0" > "$REWARD_PATH"; fi' EXIT

echo "=== ${TASK_ID} evaluator ==="

# Verify answer file exists
if [ ! -f "$ANSWER_PATH" ]; then
    echo "ERROR: answer.json not found at $ANSWER_PATH"
    echo "0.0" > "$REWARD_PATH"
    exit 1
fi

# Validate answer is valid JSON
if ! python3 -c "import json; json.load(open('$ANSWER_PATH'))" 2>/dev/null; then
    echo "ERROR: answer.json is not valid JSON"
    echo "0.0" > "$REWARD_PATH"
    exit 1
fi

echo "answer.json found and valid JSON"

# Verify oracle exists
if [ ! -f "$ORACLE_PATH" ]; then
    echo "ERROR: oracle_answer.json not found at $ORACLE_PATH"
    echo "0.0" > "$REWARD_PATH"
    exit 1
fi

# Compare files found by agent vs oracle
echo "Comparing agent answer to oracle..."
SCORE=$(python3 - "$ANSWER_PATH" "$ORACLE_PATH" <<'PYEOF'
import json, sys

answer_path, oracle_path = sys.argv[1], sys.argv[2]

with open(answer_path) as f:
    answer = json.load(f)
with open(oracle_path) as f:
    oracle = json.load(f)

# Extract file sets
def extract_files(data):
    files = set()
    for entry in data.get("files", []):
        path = entry.get("path", "")
        if path:
            files.add(path)
    return files

agent_files = extract_files(answer)
oracle_files = extract_files(oracle)

if not oracle_files:
    print("0.0")
    sys.exit(0)

# File recall and precision
if agent_files:
    recall = len(agent_files & oracle_files) / len(oracle_files)
    precision = len(agent_files & oracle_files) / len(agent_files)
    if recall + precision > 0:
        f1 = 2 * precision * recall / (precision + recall)
    else:
        f1 = 0.0
else:
    f1 = 0.0

# Symbol bonus (0.2 weight)
def extract_symbols(data):
    syms = set()
    for entry in data.get("symbols", []):
        sym = entry.get("symbol", "")
        path = entry.get("path", "")
        if sym and path:
            syms.add(f"{path}::{sym}")
    return syms

agent_syms = extract_symbols(answer)
oracle_syms = extract_symbols(oracle)

sym_score = 0.0
if oracle_syms and agent_syms:
    sym_recall = len(agent_syms & oracle_syms) / len(oracle_syms)
    sym_score = sym_recall

# Composite: 80% file F1 + 20% symbol recall
composite = 0.8 * f1 + 0.2 * sym_score
print(f"{composite:.4f}")

# Debug output
print(f"DEBUG: agent_files={len(agent_files)}, oracle_files={len(oracle_files)}, "
      f"overlap={len(agent_files & oracle_files)}, F1={f1:.4f}, sym_score={sym_score:.4f}",
      file=sys.stderr)
PYEOF
)

echo "Score: $SCORE"

# Validate score is a number
if echo "$SCORE" | python3 -c "import sys; float(sys.stdin.read().strip())" 2>/dev/null; then
    echo "$SCORE" > "$REWARD_PATH"
else
    echo "ERROR: evaluator did not return a valid score: $SCORE"
    echo "0.0" > "$REWARD_PATH"
    exit 1
fi

if python3 -c "import sys; sys.exit(0 if float('$SCORE') > 0 else 1)"; then
    echo "PASSED (score > 0)"
    exit 0
else
    echo "FAILED (score = 0)"
    exit 1
fi
