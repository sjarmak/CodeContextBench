#!/bin/bash
# Test flipt-aebaecd with FIXED /app permissions
# Tests if making /app writable allows the agent to save edits properly

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

# Add claudecode directory to PYTHONPATH for agent imports
export PYTHONPATH="$(pwd):$PYTHONPATH"

# ============================================
# LOAD CREDENTIALS
# ============================================
if [ -f ~/evals/.env.local ]; then
    echo "Loading credentials from ~/evals/.env.local..."
    source ~/evals/.env.local
else
    echo "Warning: ~/evals/.env.local not found"
fi

# Verify required credentials
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "ERROR: ANTHROPIC_API_KEY is not set"
    exit 1
fi

echo "ANTHROPIC_API_KEY: set (${#ANTHROPIC_API_KEY} chars)"
echo ""

# ============================================
# CONFIGURATION
# ============================================
AGENT_PATH="agents.claude_baseline_agent:BaselineClaudeCodeAgent"
MODEL="anthropic/claude-opus-4-5-20251101"
CONCURRENCY=1
TIMEOUT_MULTIPLIER=10

# Single task to test
TASK_ID="instance_flipt-io__flipt-aebaecd026f752b187f11328b0d464761b15d2ab"

CATEGORY="${CATEGORY:-troubleshooting}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
JOBS_BASE="runs/${CATEGORY}/swebenchpro_test_flipt_fixed_${TIMESTAMP}"

echo "=============================================="
echo "SWE-bench Pro Test: flipt-aebaecd (FIXED PERMISSIONS)"
echo "=============================================="
echo "Model: ${MODEL}"
echo "Task: ${TASK_ID}"
echo "Concurrency: ${CONCURRENCY}"
echo "Timeout multiplier: ${TIMEOUT_MULTIPLIER}x"
echo "Jobs directory: ${JOBS_BASE}"
echo ""
echo "FIX: Dockerfile updated to make /app writable (chown 1001:1001)"
echo "FIX: Force rebuilding Docker image with --force-build"
echo ""

# Create jobs directory
mkdir -p "${JOBS_BASE}"

# ============================================
# RUN BASELINE WITH FORCE BUILD
# ============================================
echo ""
echo "[BASELINE] Starting baseline run with FIXED permissions..."
echo ""

# Use --force-build to rebuild with the patched Dockerfile
BASELINE_MCP_TYPE=none harbor run \
    --dataset swebenchpro \
    -t "${TASK_ID}" \
    --agent-import-path "${AGENT_PATH}" \
    --model "${MODEL}" \
    --jobs-dir "${JOBS_BASE}/baseline" \
    -n ${CONCURRENCY} \
    --timeout-multiplier ${TIMEOUT_MULTIPLIER} \
    --force-build \
    2>&1 | tee "${JOBS_BASE}/baseline.log"

echo ""
echo "=============================================="
echo "Test Complete!"
echo "=============================================="
echo "Results saved to: ${JOBS_BASE}"
echo ""
echo "To check if the fix worked:"
echo "  # Check for permission denied errors"
echo "  grep -i 'permission denied' ${JOBS_BASE}/baseline/*/instance_*/agent/claude-code.txt"
echo ""
echo "  # Check final reward"
echo "  cat ${JOBS_BASE}/baseline/*/instance_*/result.json | jq -r '.verifier_result.rewards.reward'"
