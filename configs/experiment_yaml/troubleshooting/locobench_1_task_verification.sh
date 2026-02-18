#!/bin/bash
# LoCoBench-Agent 1-Task Quick Verification Script
#
# Runs both baseline and MCP variants on a single task to verify the adapter works.
#
# Usage:
#   ./configs_v2/examples/locobench_1_task_verification.sh
#
# Prerequisites:
#   - ~/evals/.env.local with ANTHROPIC_API_KEY (required)
#   - SOURCEGRAPH_ACCESS_TOKEN in .env.local (optional, for MCP mode)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/../.."

# ============================================
# LOAD CREDENTIALS
# ============================================
if [ -f ~/evals/.env.local ]; then
    echo "Loading credentials from ~/evals/.env.local..."
    source ~/evals/.env.local
else
    echo "Warning: ~/evals/.env.local not found"
    echo "Please create it with at minimum:"
    echo "  export ANTHROPIC_API_KEY=\"your-api-key\""
    echo ""
fi

# Verify required credentials
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "ERROR: ANTHROPIC_API_KEY is not set"
    echo ""
    echo "Please set it in ~/evals/.env.local:"
    echo "  export ANTHROPIC_API_KEY=\"your-api-key\""
    exit 1
fi

echo "ANTHROPIC_API_KEY: set (${#ANTHROPIC_API_KEY} chars)"
if [ -n "$SOURCEGRAPH_ACCESS_TOKEN" ]; then
    echo "SOURCEGRAPH_ACCESS_TOKEN: set (${#SOURCEGRAPH_ACCESS_TOKEN} chars)"
else
    echo "SOURCEGRAPH_ACCESS_TOKEN: not set (MCP mode will be skipped)"
fi
echo ""

# ============================================
# CONFIGURATION
# ============================================
TASK_ID="python_game_engine_expert_032_architectural_understanding_expert_01"
TASK_PATH="/home/stephanie_jarmak/CodeContextBench/benchmarks/locobench_agent/tasks/${TASK_ID}"
AGENT_PATH="agents.claude_baseline_agent:BaselineClaudeCodeAgent"
MODEL="${MODEL:-anthropic/claude-haiku-4-5-20251001}"
JOBS_DIR="jobs/locobench_verification_$(date +%Y%m%d_%H%M%S)"

# Create jobs directory
mkdir -p "${JOBS_DIR}"

echo "=============================================="
echo "LoCoBench-Agent Quick Verification"
echo "=============================================="
echo "Task: ${TASK_ID}"
echo "Model: ${MODEL}"
echo "Jobs: ${JOBS_DIR}"
echo ""

# ============================================
# RUN BASELINE (no MCP)
# ============================================
echo "[1/2] Running BASELINE (no MCP)..."
BASELINE_MCP_TYPE=none harbor run \
    --path "${TASK_PATH}" \
    --agent-import-path "${AGENT_PATH}" \
    --model "${MODEL}" \
    --jobs-dir "${JOBS_DIR}/baseline" \
    -n 1 \
    --timeout-multiplier 10 \
    2>&1 | tee "${JOBS_DIR}/baseline.log" || true

# ============================================
# RUN DEEPSEARCH (MCP enabled) - only if credentials available
# ============================================
if [ -n "$SOURCEGRAPH_ACCESS_TOKEN" ]; then
    echo ""
    echo "[2/2] Running DEEPSEARCH (MCP enabled)..."
    BASELINE_MCP_TYPE=deepsearch harbor run \
        --path "${TASK_PATH}" \
        --agent-import-path "${AGENT_PATH}" \
        --model "${MODEL}" \
        --jobs-dir "${JOBS_DIR}/deepsearch" \
        -n 1 \
        --timeout-multiplier 10 \
        2>&1 | tee "${JOBS_DIR}/deepsearch.log" || true
else
    echo ""
    echo "[2/2] SKIPPING DEEPSEARCH (SOURCEGRAPH_ACCESS_TOKEN not set)"
fi

echo ""
echo "=============================================="
echo "Verification Complete!"
echo "=============================================="
echo "Results saved to: ${JOBS_DIR}"
echo ""
echo "Check results:"
echo "  cat ${JOBS_DIR}/baseline/*/result.json | jq '.trials[] | {task: .task_name, reward: .verifier_result.rewards.reward}'"
if [ -n "$SOURCEGRAPH_ACCESS_TOKEN" ]; then
    echo "  cat ${JOBS_DIR}/deepsearch/*/result.json | jq '.trials[] | {task: .task_name, reward: .verifier_result.rewards.reward}'"
fi
