#!/bin/bash
# Big Code K8s — "precise" repo name variant
#
# Runs big-code-k8s-001 with SOURCEGRAPH_REPO_NAME=sg-benchmarks/kubernetes--latest--precise
# to test whether the more precise repo name improves MCP search quality.
#
# Results go into the same official run folder as the main comparison,
# with task subfolders suffixed "-precise".

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/../.."

export PYTHONPATH="$(pwd):$PYTHONPATH"

# ============================================
# LOAD CREDENTIALS
# ============================================
if [ -f ~/evals/.env.local ]; then
    echo "Loading credentials from ~/evals/.env.local..."
    source ~/evals/.env.local
fi

if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "ERROR: ANTHROPIC_API_KEY is not set"
    exit 1
fi

if [ -z "$SOURCEGRAPH_ACCESS_TOKEN" ]; then
    echo "ERROR: SOURCEGRAPH_ACCESS_TOKEN is not set (required for MCP)"
    exit 1
fi

echo "ANTHROPIC_API_KEY: set (${#ANTHROPIC_API_KEY} chars)"
echo "SOURCEGRAPH_ACCESS_TOKEN: set (${#SOURCEGRAPH_ACCESS_TOKEN} chars)"
echo ""

# ============================================
# CONFIGURATION
# ============================================
BENCHMARK_DIR="/home/stephanie_jarmak/CodeContextBench/benchmarks/big_code_mcp"
AGENT_PATH="agents.claude_baseline_agent:BaselineClaudeCodeAgent"
MODEL="${MODEL:-anthropic/claude-opus-4-5-20251101}"
CONCURRENCY=1
TIMEOUT_MULTIPLIER=10

# Use the same official run folder as the main comparison if it exists,
# otherwise create a new one
JOBS_BASE="${JOBS_BASE:-runs/official/bigcode_mcp_opus_20260131_130446}"

# Override repo name with the "precise" variant
export SOURCEGRAPH_REPO_NAME="sg-benchmarks/kubernetes--latest--precise"

TASK_DIR="big-code-k8s-001"
TASK_PATH="$BENCHMARK_DIR/$TASK_DIR"

# ============================================
# HELPER
# ============================================
log_section() {
    echo ""
    echo "========================================"
    echo "$1"
    echo "========================================"
    echo ""
}

run_k8s_precise() {
    local mode=$1
    local mcp_type=$2
    # Suffix the jobs subdir with the task name + "-precise"
    local jobs_subdir="${JOBS_BASE}/${mode}"

    log_section "Running K8s Precise — Mode: $mode"

    echo "Configuration:"
    echo "  Mode: $mode"
    echo "  MCP Type: $mcp_type"
    echo "  Model: $MODEL"
    echo "  SOURCEGRAPH_REPO_NAME: $SOURCEGRAPH_REPO_NAME"
    echo "  Jobs directory: $jobs_subdir"
    echo ""

    mkdir -p "$jobs_subdir"

    if [ ! -d "$TASK_PATH" ]; then
        echo "ERROR: Task directory not found: $TASK_PATH"
        return 1
    fi

    echo "Running task: $TASK_DIR ($mode) [precise repo name]"

    BASELINE_MCP_TYPE=$mcp_type harbor run \
        --path "$TASK_PATH" \
        --agent-import-path "$AGENT_PATH" \
        --model "$MODEL" \
        --jobs-dir "$jobs_subdir" \
        -n $CONCURRENCY \
        --timeout-multiplier $TIMEOUT_MULTIPLIER \
        2>&1 | tee "${jobs_subdir}/${TASK_DIR}-precise.log" \
        || {
            echo "WARNING: Task failed (exit code: $?)"
        }

    # Rename the task result folder to include "-precise" suffix
    # Harbor creates: $jobs_subdir/<timestamp>/<task_id>__<hash>/
    # We want to rename the task subfolder to big-code-k8s-001-precise__<hash>
    local latest_run=$(ls -td "$jobs_subdir"/20* 2>/dev/null | head -1)
    if [ -n "$latest_run" ]; then
        for task_folder in "$latest_run"/${TASK_DIR}__*; do
            if [ -d "$task_folder" ]; then
                local dirname=$(dirname "$task_folder")
                local basename=$(basename "$task_folder")
                local new_name="${basename/${TASK_DIR}/${TASK_DIR}-precise}"
                if [ "$basename" != "$new_name" ]; then
                    mv "$task_folder" "$dirname/$new_name"
                    echo "Renamed: $basename -> $new_name"
                fi
            fi
        done
    fi

    echo ""
}

# ============================================
# MAIN
# ============================================
log_section "Big Code K8s — Precise Repo Name Comparison"
echo "Testing SOURCEGRAPH_REPO_NAME=sg-benchmarks/kubernetes--latest--precise"
echo "Results go to: $JOBS_BASE"
echo ""

# Run baseline (no MCP — serves as control, repo name doesn't affect baseline)
run_k8s_precise "baseline" "none"

# Run MCP hybrid with precise repo name
run_k8s_precise "sourcegraph_full" "sourcegraph_full"

log_section "K8s Precise Run Complete"
echo "Results: $JOBS_BASE"
echo ""
echo "Compare precise vs standard hybrid:"
echo "  # Standard results (from main comparison run):"
echo "  ls $JOBS_BASE/sourcegraph_full/*/big-code-k8s-001__*/"
echo ""
echo "  # Precise results:"
echo "  ls $JOBS_BASE/*/big-code-k8s-001-precise__*/ 2>/dev/null"
echo ""
