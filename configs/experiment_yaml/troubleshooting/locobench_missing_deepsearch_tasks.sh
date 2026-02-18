#!/bin/bash
# LoCoBench-Agent Missing DeepSearch Tasks
#
# Runs the 25 tasks that were not completed in the deepsearch run from
# runs/locobench_50_tasks_20260127_170300/deepsearch/
#
# Original run breakdown (28 attempted):
#   - 25 successful (scored)
#   - 1 failed (AddTestsDirError - RETRYING in this run)
#   - 2 incomplete (no result.json - INCLUDED in this run)
# Plus 22 never started tasks
#
# This run: 1 failed + 2 incomplete + 22 never started = 25 tasks
# Final total: 25 + 25 = 50 scored tasks
#
# Usage:
#   ./configs/locobench_missing_deepsearch_tasks.sh
#
# Prerequisites:
#   - ~/evals/.env.local with ANTHROPIC_API_KEY (required)
#   - SOURCEGRAPH_ACCESS_TOKEN in .env.local (required for DeepSearch)

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
    echo "Please create it with at minimum:"
    echo "  export ANTHROPIC_API_KEY=\"your-api-key\""
    echo "  export SOURCEGRAPH_ACCESS_TOKEN=\"your-sourcegraph-token\""
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

if [ -z "$SOURCEGRAPH_ACCESS_TOKEN" ]; then
    echo "ERROR: SOURCEGRAPH_ACCESS_TOKEN is not set (required for DeepSearch)"
    echo ""
    echo "Please set it in ~/evals/.env.local:"
    echo "  export SOURCEGRAPH_ACCESS_TOKEN=\"your-sourcegraph-token\""
    exit 1
fi

echo "ANTHROPIC_API_KEY: set (${#ANTHROPIC_API_KEY} chars)"
echo "SOURCEGRAPH_ACCESS_TOKEN: set (${#SOURCEGRAPH_ACCESS_TOKEN} chars)"
echo ""

# ============================================
# CONFIGURATION
# ============================================
TASKS_DIR="/home/stephanie_jarmak/CodeContextBench/benchmarks/locobench_agent/tasks"
AGENT_PATH="agents.claude_baseline_agent:BaselineClaudeCodeAgent"
MODEL="${MODEL:-anthropic/claude-opus-4-5-20251101}"
CONCURRENCY=2
TIMEOUT_MULTIPLIER=10

# Use the existing run directory from the incomplete run
JOBS_BASE="runs/locobench_50_tasks_20260127_170300"

# The 25 missing task IDs (tasks NOT completed in the original deepsearch run)
# This INCLUDES the 1 failed task to retry it
# Running these 25 will give us 25 + 25 = 50 total scored tasks
MISSING_TASK_IDS=(
    # Failed task (AddTestsDirError) - 1 task - RETRYING
    "cpp_web_blog_expert_040_cross_file_refactoring_expert_01"              # FAILED - RETRYING

    # Incomplete tasks (started but no result.json) - 2 tasks
    "java_api_rest_expert_006_architectural_understanding_expert_01"        # INCOMPLETE
    "rust_web_social_expert_073_bug_investigation_expert_01"                # INCOMPLETE

    # Never started tasks - 22 tasks
    "c_api_graphql_expert_079_architectural_understanding_expert_01"
    "c_api_microservice_expert_080_architectural_understanding_expert_01"
    "cpp_data_analytics_expert_010_architectural_understanding_expert_01"
    "cpp_system_security_expert_064_architectural_understanding_expert_01"
    "cpp_web_dashboard_expert_039_architectural_understanding_expert_01"
    "csharp_mobile_game_expert_024_architectural_understanding_expert_01"
    "csharp_web_blog_expert_076_architectural_understanding_expert_01"
    "java_web_ecommerce_expert_000_architectural_understanding_expert_01"
    "python_data_streaming_expert_085_architectural_understanding_expert_01"
    "python_desktop_development_expert_021_architectural_understanding_expert_01"
    "python_game_engine_expert_032_architectural_understanding_expert_01"
    "rust_blockchain_nft_expert_071_architectural_understanding_expert_01"
    "rust_web_social_expert_073_architectural_understanding_expert_01"
    "typescript_desktop_productivity_expert_055_architectural_understanding_expert_01"
    "typescript_system_monitoring_expert_061_architectural_understanding_expert_01"
    "c_api_microservice_expert_080_cross_file_refactoring_expert_01"
    "c_blockchain_nft_expert_071_cross_file_refactoring_expert_01"
    "python_data_streaming_expert_085_cross_file_refactoring_expert_01"
    "python_game_engine_expert_032_cross_file_refactoring_expert_01"
    "rust_data_streaming_expert_013_cross_file_refactoring_expert_01"
    "typescript_system_monitoring_expert_061_cross_file_refactoring_expert_01"
    "c_blockchain_nft_expert_071_bug_investigation_expert_01"
)

echo "=============================================="
echo "LoCoBench-Agent Missing DeepSearch Tasks"
echo "=============================================="
echo "Model: ${MODEL}"
echo "Tasks to run: ${#MISSING_TASK_IDS[@]} (1 failed + 2 incomplete + 22 never started)"
echo "Concurrency: ${CONCURRENCY}"
echo "Jobs directory: ${JOBS_BASE}/deepsearch"
echo ""
echo "This will give 50 total scored tasks (25 existing + 25 new)"
echo ""

# Run each missing task individually to avoid symlink issues
# This ensures Harbor processes each task cleanly without directory hashing problems

TOTAL_TASKS=${#MISSING_TASK_IDS[@]}
CURRENT_TASK=0

for task_id in "${MISSING_TASK_IDS[@]}"; do
    CURRENT_TASK=$((CURRENT_TASK + 1))
    echo ""
    echo "=============================================="
    echo "Task ${CURRENT_TASK}/${TOTAL_TASKS}: ${task_id}"
    echo "=============================================="

    BASELINE_MCP_TYPE=deepsearch harbor run \
        --path "${TASKS_DIR}/${task_id}" \
        --agent-import-path "${AGENT_PATH}" \
        --model "${MODEL}" \
        --jobs-dir "${JOBS_BASE}/deepsearch" \
        -n 1 \
        --timeout-multiplier ${TIMEOUT_MULTIPLIER} \
        2>&1 | tee -a "${JOBS_BASE}/deepsearch_missing.log"

    if [ $? -ne 0 ]; then
        echo "WARNING: Task ${task_id} failed or had errors"
    fi
done

echo ""
echo "=============================================="
echo "Missing Tasks Complete!"
echo "=============================================="
echo "Results saved to: ${JOBS_BASE}/deepsearch"
echo ""
echo "Note: Harbor will create a new timestamped subdirectory."
echo "You may need to manually merge/consolidate the results."
echo ""
