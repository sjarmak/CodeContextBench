#!/bin/bash
# LoCoBench End-to-End Validation Script
#
# Runs 2 LoCoBench tasks in both baseline and deepsearch_hybrid modes
# for end-to-end pipeline validation.
#
# Tasks:
# - python_game_engine_expert_032_architectural_understanding (Python)
# - csharp_data_warehouse_expert_012_cross_file_refactoring (C#)
#
# Usage:
#   ./configs/troubleshooting/e2e_validation_locobench.sh
#
# Prerequisites:
#   - ~/evals/.env.local with ANTHROPIC_API_KEY (required)
#   - SOURCEGRAPH_ACCESS_TOKEN in .env.local (required for deepsearch_hybrid)

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
    echo "SOURCEGRAPH_ACCESS_TOKEN: not set (deepsearch_hybrid mode will be skipped)"
fi
echo ""

# ============================================
# CONFIGURATION
# ============================================
LOCOBENCH_BASE="/home/stephanie_jarmak/CodeContextBench/benchmarks/locobench_agent/tasks"
TASK_IDS=(
    "python_game_engine_expert_032_architectural_understanding_expert_01"
    "csharp_data_warehouse_expert_012_cross_file_refactoring_expert_01"
)
AGENT_PATH="agents.claude_baseline_agent:BaselineClaudeCodeAgent"
MODEL="${MODEL:-anthropic/claude-opus-4-5-20251101}"
CATEGORY="troubleshooting"
JOBS_DIR="jobs/e2e_validation_locobench_$(date +%Y%m%d_%H%M%S)"

MCP_MODES=("none")
if [ -n "$SOURCEGRAPH_ACCESS_TOKEN" ]; then
    MCP_MODES+=("deepsearch")
fi

# Create jobs directory
mkdir -p "${JOBS_DIR}"

TOTAL_TASKS=${#TASK_IDS[@]}
TOTAL_MODES=${#MCP_MODES[@]}
TOTAL_RUNS=$((TOTAL_TASKS * TOTAL_MODES))
RUN_NUM=0

echo "=============================================="
echo "LoCoBench End-to-End Validation"
echo "=============================================="
echo "Tasks: ${TOTAL_TASKS}"
echo "Modes: ${MCP_MODES[*]}"
echo "Total runs: ${TOTAL_RUNS}"
echo "Model: ${MODEL}"
echo "Jobs: ${JOBS_DIR}"
echo ""

# ============================================
# RUN ALL TASK × MODE COMBINATIONS
# ============================================
for MODE in "${MCP_MODES[@]}"; do
    MODE_LABEL="baseline"
    if [ "$MODE" = "deepsearch" ]; then
        MODE_LABEL="deepsearch_hybrid"
    fi

    for TASK_ID in "${TASK_IDS[@]}"; do
        RUN_NUM=$((RUN_NUM + 1))
        TASK_PATH="${LOCOBENCH_BASE}/${TASK_ID}"

        if [ ! -d "$TASK_PATH" ]; then
            echo "[${RUN_NUM}/${TOTAL_RUNS}] SKIPPING ${TASK_ID} (${MODE_LABEL}) - task directory not found"
            echo "  Expected: ${TASK_PATH}"
            continue
        fi

        echo "[${RUN_NUM}/${TOTAL_RUNS}] Running ${TASK_ID} (${MODE_LABEL})..."
        BASELINE_MCP_TYPE="${MODE}" harbor run \
            --path "${TASK_PATH}" \
            --agent-import-path "${AGENT_PATH}" \
            --model "${MODEL}" \
            --jobs-dir "${JOBS_DIR}/${MODE_LABEL}" \
            -n 1 \
            --timeout-multiplier 10 \
            2>&1 | tee "${JOBS_DIR}/${MODE_LABEL}_${TASK_ID}.log" || true

        echo ""
    done
done

echo "=============================================="
echo "LoCoBench E2E Validation Complete!"
echo "=============================================="
echo "Results saved to: ${JOBS_DIR}"
echo ""
echo "Check results:"
echo "  find ${JOBS_DIR} -name result.json -exec jq '{task: .task_name, mode: .mcp_mode, reward: .verifier_result.rewards.reward}' {} \\;"
echo ""
echo "Run audit:"
echo "  python3 scripts/audit_traces.py ${JOBS_DIR}"
