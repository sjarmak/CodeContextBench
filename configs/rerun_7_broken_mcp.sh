#!/bin/bash
# MCP-only rerun of 7 tasks that failed due to the git config bug (fixed in 043ade96e).
# Baselines succeeded — only MCP needs rerunning.
#
# Tasks:
#   ccb_build: cgen-deps-install-001
#   ccb_test:  numpy-array-sum-perf-001, sklearn-kmeans-perf-001,
#              pandas-groupby-perf-001, llamacpp-context-window-search-001,
#              llamacpp-file-modify-search-001, openhands-search-file-test-001
#
# Usage: ./configs/rerun_7_broken_mcp.sh
set -euo pipefail

cd "$(dirname "$0")/.."
source configs/_common.sh

MODEL="anthropic/claude-haiku-4-5-20251001"
FULL_CONFIG="mcp-remote-artifact"
AGENT_PATH="agents.claude_baseline_agent:BaselineClaudeCodeAgent"
TIMEOUT_MULT=10
FULL_MCP_TYPE=$(config_to_mcp_type "$FULL_CONFIG")

load_credentials
enforce_subscription_mode
setup_multi_accounts
ensure_fresh_token_all

# Jobs dirs match the original batch where baselines already exist
BUILD_JOBS="runs/staging/ccb_build_haiku_20260221_174306/mcp-remote-artifact"
TEST_JOBS="runs/staging/ccb_test_haiku_20260221_174306/mcp-remote-artifact"

# Ensure jobs dirs exist
mkdir -p "$BUILD_JOBS" "$TEST_JOBS"

# Task list: suite_jobs_dir|task_path
TASKS=(
    "$BUILD_JOBS|benchmarks/ccb_build/cgen-deps-install-001"
    "$TEST_JOBS|benchmarks/ccb_test/numpy-array-sum-perf-001"
    "$TEST_JOBS|benchmarks/ccb_test/sklearn-kmeans-perf-001"
    "$TEST_JOBS|benchmarks/ccb_test/pandas-groupby-perf-001"
    "$TEST_JOBS|benchmarks/ccb_test/llamacpp-context-window-search-001"
    "$TEST_JOBS|benchmarks/ccb_test/llamacpp-file-modify-search-001"
    "$TEST_JOBS|benchmarks/ccb_test/openhands-search-file-test-001"
)

PIDS=()
TEMP_DIRS=()
ACCOUNT_IDX=0
NUM_ACCOUNTS=${#CLAUDE_HOMES[@]}

echo "=============================================="
echo "MCP-Only Rerun: 7 Broken Tasks (git config fix)"
echo "=============================================="
echo "Model:    $MODEL"
echo "Config:   $FULL_CONFIG (mcp_type=$FULL_MCP_TYPE)"
echo "Accounts: $NUM_ACCOUNTS"
echo ""

for entry in "${TASKS[@]}"; do
    IFS='|' read -r jobs_dir task_path <<< "$entry"
    task_name=$(basename "$task_path")
    abs_path="$(pwd)/$task_path"

    # Create temp copy with Dockerfile.sg_only swapped in
    mcp_temp=$(mktemp -d "/tmp/mcp_${task_name}_XXXXXX")
    cp -a "$abs_path/." "$mcp_temp/"
    if [ -f "$mcp_temp/environment/Dockerfile.sg_only" ]; then
        cp "$mcp_temp/environment/Dockerfile.sg_only" "$mcp_temp/environment/Dockerfile"
        echo "[sg_only] $task_name: Using empty-workspace Dockerfile"
    else
        echo "WARNING: No Dockerfile.sg_only for $task_name"
    fi
    TEMP_DIRS+=("$mcp_temp")

    # Pick account round-robin
    account_home="${CLAUDE_HOMES[$ACCOUNT_IDX]}"
    ACCOUNT_IDX=$(( (ACCOUNT_IDX + 1) % NUM_ACCOUNTS ))

    # Launch MCP run
    (
        export HOME="$account_home"
        BASELINE_MCP_TYPE=$FULL_MCP_TYPE harbor run \
            --path "$mcp_temp" \
            --agent-import-path "$AGENT_PATH" \
            --model "$MODEL" \
            --jobs-dir "$jobs_dir" \
            -n 1 \
            --timeout-multiplier "$TIMEOUT_MULT" \
            2>&1 | tee -a "${jobs_dir}.rerun.log" \
            || echo "WARNING: MCP rerun failed: $task_name"
    ) &
    PIDS+=($!)
    echo "  Started $task_name (PID $!, HOME=$(basename "$account_home"))"
    sleep 2
done

echo ""
echo "=== Waiting for all 7 MCP reruns... ==="
for pid in "${PIDS[@]}"; do
    wait "$pid" 2>/dev/null || true
done

# Cleanup temp dirs
for d in "${TEMP_DIRS[@]}"; do
    rm -rf "$d" 2>/dev/null || true
done

echo ""
echo "=============================================="
echo "All 7 MCP reruns complete!"
echo "=============================================="
echo "Results in:"
echo "  $BUILD_JOBS"
echo "  $TEST_JOBS"
