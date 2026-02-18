#!/bin/bash
# Big Code MCP — K8s verifier-fix rerun
#
# Reruns big-code-k8s-001 after fixing the verifier test.sh to properly
# detect committed changes (origin/master..HEAD comparison).
#
# Fixes applied to test.sh:
#   1. Commit detection uses origin/master ref instead of fragile FETCH_HEAD/reflog
#   2. Changed-files check diffs against origin ref (catches committed changes)
#   3. Test detection searches pkg/ and staging/ (not just test/)

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
else
    echo "Warning: ~/evals/.env.local not found"
fi

export CLAUDE_CREDENTIALS_FILE="${HOME}/.claude/.credentials.json"
if [ ! -f "$CLAUDE_CREDENTIALS_FILE" ]; then
    echo "ERROR: Subscription credentials not found at $CLAUDE_CREDENTIALS_FILE"
    exit 1
fi
echo "Subscription auth: $CLAUDE_CREDENTIALS_FILE"

if [ -z "$SOURCEGRAPH_ACCESS_TOKEN" ]; then
    echo "WARNING: SOURCEGRAPH_ACCESS_TOKEN not set — MCP hybrid run will be skipped"
    RUN_MCP=false
else
    echo "SOURCEGRAPH_ACCESS_TOKEN: set (${#SOURCEGRAPH_ACCESS_TOKEN} chars)"
    RUN_MCP=true
fi
echo ""

# ============================================
# CONFIGURATION
# ============================================
BENCHMARK_DIR="/home/stephanie_jarmak/CodeContextBench/benchmarks/big_code_mcp"
AGENT_PATH="agents.claude_baseline_agent:BaselineClaudeCodeAgent"
MODEL="anthropic/claude-opus-4-5"
CONCURRENCY=1
TIMEOUT_MULTIPLIER=10
CATEGORY="troubleshooting"

TASK_DIRS=(
    "big-code-k8s-001"
)

# Sourcegraph repo name override for k8s task
export SOURCEGRAPH_REPO_NAME="sg-benchmarks/kubernetes--latest"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
JOBS_BASE="runs/${CATEGORY}/bigcode_k8s_verifier_rerun_${TIMESTAMP}"

# ============================================
# HELPER FUNCTIONS
# ============================================
log_section() {
    echo ""
    echo "========================================"
    echo "$1"
    echo "========================================"
    echo ""
}

run_task_batch() {
    local mode=$1
    local mcp_type=$2
    local jobs_subdir="${JOBS_BASE}/${mode}"

    log_section "Running Big Code MCP — Mode: $mode"

    echo "Configuration:"
    echo "  Mode: $mode"
    echo "  MCP Type: $mcp_type"
    echo "  Model: $MODEL"
    echo "  Tasks: ${#TASK_DIRS[@]}"
    echo "  Concurrency: $CONCURRENCY"
    echo "  Timeout Multiplier: ${TIMEOUT_MULTIPLIER}x"
    echo "  Jobs directory: $jobs_subdir"
    echo ""

    mkdir -p "$jobs_subdir"

    for task_dir in "${TASK_DIRS[@]}"; do
        local task_path="$BENCHMARK_DIR/$task_dir"

        if [ ! -d "$task_path" ]; then
            echo "ERROR: Task directory not found: $task_path"
            continue
        fi

        echo "Running task: $task_dir ($mode)"
        echo "  Path: $task_path"

        BASELINE_MCP_TYPE=$mcp_type harbor run \
            --path "$task_path" \
            --agent-import-path "$AGENT_PATH" \
            --model "$MODEL" \
            --jobs-dir "$jobs_subdir" \
            -n $CONCURRENCY \
            --timeout-multiplier $TIMEOUT_MULTIPLIER \
            2>&1 | tee "${jobs_subdir}/${task_dir}.log" \
            || {
                echo "WARNING: Task $task_dir failed (exit code: $?)"
                echo "Continuing with remaining tasks..."
            }

        echo ""
    done

    log_section "Completed Big Code MCP — Mode: $mode"
    echo "Job results: $jobs_subdir"
    echo ""
}

# ============================================
# MAIN EXECUTION
# ============================================
log_section "Big Code MCP — K8s Verifier-Fix Rerun"
echo "Purpose: Rerun with fixed verifier that properly detects committed changes"
echo ""
echo "  Baseline: true"
echo "  MCP Hybrid: $RUN_MCP"
echo "  Model: $MODEL"
echo "  Auth: Subscription"
echo "  Category: $CATEGORY"
echo "  Tasks: ${TASK_DIRS[*]}"
echo "  Jobs Base: $JOBS_BASE"
echo ""

mkdir -p "$JOBS_BASE"

# Run baseline (no MCP)
run_task_batch "baseline" "none"

# Run MCP hybrid (Sourcegraph MCP + local tools)
if [ "$RUN_MCP" = true ]; then
    run_task_batch "sourcegraph_full" "sourcegraph_full"
fi

# ============================================
# SUMMARY
# ============================================
log_section "Verifier-Fix Rerun Complete"
echo "Results saved to: $JOBS_BASE"
echo ""
echo "Quick verification:"
echo "  # Check rewards"
echo "  find $JOBS_BASE -name reward.txt -exec sh -c 'echo \"\$(dirname {}): \$(cat {})\"' \;"
echo ""
echo "  # Check verifier detected changes"
echo "  grep -r 'Change detection:' $JOBS_BASE/ 2>/dev/null"
echo ""
