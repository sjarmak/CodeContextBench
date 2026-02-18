#!/bin/bash
# Test flipt-aebaecd with RUNTIME permission fix
# Fixes /app permissions during agent setup phase

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

export PYTHONPATH="$(pwd):$PYTHONPATH"

if [ -f ~/evals/.env.local ]; then
    source ~/evals/.env.local
fi

if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "ERROR: ANTHROPIC_API_KEY is not set"
    exit 1
fi

AGENT_PATH="agents.claude_baseline_agent:BaselineClaudeCodeAgent"
MODEL="anthropic/claude-opus-4-5-20251101"
CONCURRENCY=1
TIMEOUT_MULTIPLIER=10
TASK_ID="instance_flipt-io__flipt-aebaecd026f752b187f11328b0d464761b15d2ab"
CATEGORY="${CATEGORY:-troubleshooting}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
JOBS_BASE="runs/${CATEGORY}/swebenchpro_test_flipt_runtime_${TIMESTAMP}"

echo "=============================================="
echo "SWE-bench Pro Test: flipt-aebaecd (RUNTIME FIX)"
echo "=============================================="
echo "FIX: Agent setup() runs: sudo chown -R 1001:1001 /app"
echo "FIX: This happens BEFORE Claude Code starts"
echo ""

mkdir -p "${JOBS_BASE}"

BASELINE_MCP_TYPE=none harbor run \
    --dataset swebenchpro \
    -t "${TASK_ID}" \
    --agent-import-path "${AGENT_PATH}" \
    --model "${MODEL}" \
    --jobs-dir "${JOBS_BASE}/baseline" \
    -n ${CONCURRENCY} \
    --timeout-multiplier ${TIMEOUT_MULTIPLIER} \
    2>&1 | tee "${JOBS_BASE}/baseline.log"

echo ""
echo "=============================================="
echo "Test Complete!"
echo "=============================================="
echo ""
echo "Check results:"
echo "  grep 'FIXING /app PERMISSIONS' ${JOBS_BASE}/baseline.log"
echo "  grep -i 'permission denied' ${JOBS_BASE}/baseline/*/instance_*/agent/claude-code.txt | wc -l"
echo "  cat ${JOBS_BASE}/baseline/*/instance_*/result.json | jq -r '.verifier_result.rewards.reward'"
