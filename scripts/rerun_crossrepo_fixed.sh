#!/bin/bash
# Re-run the 4 substantive crossrepo tasks after fixing evaluation infrastructure.
#
# Fixes applied:
#   - Created validate_patch.py (was missing entirely)
#   - Rewrote test.sh for patch tasks (api_upgrade_01, refactor_rename_01) with
#     fallback diff collection from git repos
#   - Rewrote test.sh for analysis tasks (bug_localization_01, cross_file_reasoning_01)
#     to validate markdown output against expected keywords/file references
#   - Added patch output instructions to api_upgrade_01 and refactor_rename_01
#
# Previous run (crossrepo_opus_20260204_023501__broken_verifier/) scored 0.0 on
# all substantive tasks due to: missing validate_patch.py + no patch collection
# + wrong evaluation type for analysis tasks.
#
# simple_test_01 is excluded — it already passed 1.0 across all 3 configs.
#
# Total: 4 tasks x 3 configs = 12 pairs

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

BENCH_DIR="$(pwd)/benchmarks"

# Agent module
AGENT_DIR="${AGENT_DIR:-$HOME/evals/custom_agents/agents/claudecode}"
export PYTHONPATH="${AGENT_DIR}:$(pwd):${PYTHONPATH:-}"

# Shared config: subscription mode + token refresh
source "$(pwd)/configs/_common.sh"

# Load credentials
if [ -f ~/evals/.env.local ]; then
    echo "Loading credentials from ~/evals/.env.local..."
    source ~/evals/.env.local
else
    echo "ERROR: ~/evals/.env.local not found"
    exit 1
fi

# Common parameters
MODEL="anthropic/claude-opus-4-5-20251101"
AGENT_PATH="agents.claude_baseline_agent:BaselineClaudeCodeAgent"
TIMEOUT_MULTIPLIER=10
CONCURRENCY=2
SELECTION_FILE="configs/selected_benchmark_tasks.json"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
CROSSREPO_JOBS="runs/official/crossrepo_opus_${TIMESTAMP}"

# Sourcegraph repo name mappings
declare -A CROSSREPO_SG=(
    ["api_upgrade_01"]="sg-benchmarks/etcd--d89978e8"
    ["bug_localization_01"]="sg-benchmarks/scikit-learn--cb7e82dd"
    ["cross_file_reasoning_01"]="sg-benchmarks/kubernetes--8c9c67c0"
    ["refactor_rename_01"]="sg-benchmarks/django--674eda1c"
)

CONFIGS=("baseline" "sourcegraph_base" "sourcegraph_full")

# ============================================
# Helper functions
# ============================================
run_task() {
    local label=$1
    local task_path=$2
    local mcp_type=$3
    local sg_repo=$4
    local jobs_subdir=$5

    echo ""
    echo "--- ${label} ---"
    ensure_fresh_token

    mkdir -p "$jobs_subdir"

    local sg_env=""
    if [ -n "$sg_repo" ] && [ "$mcp_type" != "none" ]; then
        echo "  SOURCEGRAPH_REPO_NAME=${sg_repo}"
        sg_env="SOURCEGRAPH_REPO_NAME=$sg_repo"
    fi

    local task_name
    task_name=$(basename "$task_path")

    env $sg_env BASELINE_MCP_TYPE=$mcp_type harbor run \
        --path "$task_path" \
        --agent-import-path "$AGENT_PATH" \
        --model "$MODEL" \
        --jobs-dir "$jobs_subdir" \
        -n $CONCURRENCY \
        --timeout-multiplier $TIMEOUT_MULTIPLIER \
        2>&1 | tee "${jobs_subdir}/${task_name}_${mcp_type}.log" || true
}

extract_metrics() {
    local jobs_dir=$1
    local benchmark=$2
    local config=$3
    echo "Extracting metrics from $jobs_dir..."
    for result_dir in "$jobs_dir"/*/*/; do
        if [ -f "$result_dir/result.json" ] && [ ! -f "$result_dir/task_metrics.json" ]; then
            python3 scripts/extract_task_metrics.py \
                --task-dir "$result_dir" \
                --benchmark "$benchmark" \
                --config "$config" \
                --selected-tasks "$SELECTION_FILE" \
                2>&1 || echo "  WARNING: metrics extraction failed for $(basename $result_dir)"
        fi
    done
}

mcp_type_for_config() {
    case "$1" in
        baseline)          echo "none" ;;
        sourcegraph_base)  echo "sourcegraph_base" ;;
        sourcegraph_full)  echo "sourcegraph_full" ;;
    esac
}

# ============================================
# Pre-flight checks
# ============================================
echo "=============================================="
echo "Re-running 4 crossrepo tasks x 3 configs = 12 pairs"
echo "=============================================="
echo "Token status:"
ensure_fresh_token
echo ""
echo "Output: ${CROSSREPO_JOBS}"
echo ""

TOTAL=12
N=0

# ============================================
# Run 4 substantive tasks (skip simple_test_01)
# ============================================
CROSSREPO_TASKS=(api_upgrade_01 bug_localization_01 cross_file_reasoning_01 refactor_rename_01)
for task in "${CROSSREPO_TASKS[@]}"; do
    for config in "${CONFIGS[@]}"; do
        N=$((N + 1))
        mcp=$(mcp_type_for_config "$config")
        run_task "[$N/$TOTAL] $task (crossrepo $config)" \
            "${BENCH_DIR}/ccb_crossrepo/${task}" \
            "$mcp" \
            "${CROSSREPO_SG[$task]}" \
            "${CROSSREPO_JOBS}/${config}"
    done
done

for config in "${CONFIGS[@]}"; do
    extract_metrics "${CROSSREPO_JOBS}/${config}" "ccb_crossrepo" "$config"
done

# ============================================
# Summary
# ============================================
echo ""
echo "=============================================="
echo "All $TOTAL crossrepo re-runs complete!"
echo "=============================================="
echo ""
echo "Results: ${CROSSREPO_JOBS}/{baseline,sourcegraph_base,sourcegraph_full}/"
echo ""
echo "Quick reward check:"
for config in baseline sourcegraph_base sourcegraph_full; do
    for f in "$CROSSREPO_JOBS/$config"/*/*/result.json "$CROSSREPO_JOBS/$config"/*/result.json; do
        if [ -f "$f" ]; then
            task=$(python3 -c "import json; d=json.load(open('$f')); print(d.get('task_id', d.get('name','?')))" 2>/dev/null)
            reward=$(python3 -c "import json; d=json.load(open('$f')); t=d.get('trials',[{}]); print(t[0].get('verifier_result',{}).get('rewards',{}).get('reward','?') if t else '?')" 2>/dev/null)
            echo "  crossrepo/$config/$task: reward=$reward"
        fi
    done
done
echo ""
echo "Previous broken-verifier results preserved at:"
echo "  runs/official/crossrepo_opus_20260204_023501__broken_verifier/"
