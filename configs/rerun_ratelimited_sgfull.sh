#!/bin/bash
# Rerun 3 SG_full tasks that were killed due to account3 rate limit exhaustion.
# These go into the same jobs dirs as the wave2_3 run so results merge naturally.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."
source configs/_common.sh

load_credentials
export SKIP_ACCOUNTS="account1 account3"
setup_multi_accounts

MODEL="anthropic/claude-sonnet-4-6"
AGENT_PATH="agents.claude_baseline_agent:BaselineClaudeCodeAgent"
BENCHMARK_DIR="benchmarks"
CONCURRENCY=2
TIMEOUT_MULTIPLIER=10

run_sgfull_task() {
    local suite=$1       # e.g. ccb_build
    local task_id=$2     # e.g. flipt-dep-refactor-001
    local jobs_base=$3   # e.g. runs/staging/build_sonnet_20260219_133554
    local task_path="${BENCHMARK_DIR}/${suite}/${task_id}"
    local jobs_subdir="${jobs_base}/sourcegraph_full"

    local sgonly="${task_path}/environment/Dockerfile.sg_only"
    if [ ! -f "$sgonly" ]; then
        echo "ERROR: Missing Dockerfile.sg_only for $task_id"
        return 1
    fi

    local temp_task_dir
    temp_task_dir=$(mktemp -d "/tmp/rerun_${task_id}_XXXXXX")
    cp -a "${task_path}/." "${temp_task_dir}/"
    cp "${temp_task_dir}/environment/Dockerfile.sg_only" "${temp_task_dir}/environment/Dockerfile"

    local suite_stem="${suite#ccb_}"
    local job_name="${suite}_${task_id}_sourcegraph_full"
    job_name="${job_name//[^[:alnum:]_.-]/-}"
    job_name=$(echo "$job_name" | tr '[:upper:]' '[:lower:]')

    echo "[$(date +%H:%M:%S)] Running SG_full: $task_id"

    BASELINE_MCP_TYPE=sourcegraph_full harbor run \
        --job-name "$job_name" \
        --path "$temp_task_dir" \
        --agent-import-path "$AGENT_PATH" \
        --model "$MODEL" \
        --jobs-dir "$jobs_subdir" \
        -n $CONCURRENCY \
        --timeout-multiplier $TIMEOUT_MULTIPLIER \
        2>&1 | tee "${jobs_subdir}/${task_id}_rerun.log" \
        || echo "WARNING: $task_id SG_full failed (exit $?)"

    rm -rf "$temp_task_dir"
    echo "[$(date +%H:%M:%S)] Done: $task_id"
}

echo "=============================================="
echo "Rerunning 4 rate-limited SG_full tasks"
echo "Account: account2 only"
echo "=============================================="

ensure_fresh_token_all

# Run sequentially to stay within account2 rate limits
run_sgfull_task ccb_build flipt-dep-refactor-001 runs/staging/build_sonnet_20260219_133554
run_sgfull_task ccb_build k8s-noschedule-taint-feat-001 runs/staging/build_sonnet_20260219_133554
run_sgfull_task ccb_build k8s-score-normalizer-refac-001 runs/staging/build_sonnet_20260219_133554
run_sgfull_task ccb_debug prometheus-queue-reshard-debug-001 runs/staging/debug_sonnet_20260219_133554

echo "=============================================="
echo "All 4 reruns complete at $(date)"
echo "=============================================="
