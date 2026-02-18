#!/bin/bash
# Test flipt-aebaecd with PATCHED Harbor (docker exec as root)
# This should finally allow agents to write to /app

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
JOBS_BASE="runs/${CATEGORY}/swebenchpro_test_flipt_FINAL_${TIMESTAMP}"

echo "=============================================="
echo "SWE-bench Pro Test: flipt-aebaecd (HARBOR PATCHED)"
echo "=============================================="
echo "FIX: Harbor docker.py patched to run: docker exec --user root"
echo "FIX: This allows agent to write to /app owned by root"
echo ""
echo "Expected results:"
echo "  - NO permission denied errors"
echo "  - Agent edits save to /app/internal/storage/fs/cache.go"
echo "  - Tests compile successfully"
echo "  - Reward > 0.0 (PASSING!)"
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
echo "  # Permission errors (should be 0)"
echo "  grep -i 'permission denied' ${JOBS_BASE}/baseline/*/instance_*/agent/claude-code.txt | wc -l"
echo ""
echo "  # Final reward (should be > 0)"
echo "  cat ${JOBS_BASE}/baseline/*/instance_*/result.json | jq -r '.verifier_result.rewards.reward'"
echo ""
echo "  # Edit tool errors (should be 0)"
echo "  grep -i 'EACCES' ${JOBS_BASE}/baseline/*/instance_*/agent/claude-code.txt | wc -l"
