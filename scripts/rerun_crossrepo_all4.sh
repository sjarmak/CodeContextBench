#!/bin/bash
# Re-run ALL 4 crossrepo tasks x 3 configs = 12 pairs
#
# All 4 crossrepo test.sh scripts had verifier issues:
# - api_upgrade_01, refactor_rename_01: corpus validate_patch.py doesn't accept --expected
# - bug_localization_01, cross_file_reasoning_01: reward.txt left empty on fallback
#
# All 4 test.sh files have been fixed to use inline validation only with
# defensive reward.txt writes.
#
# Results go into the existing crossrepo_opus_20260204_133742 directory
# (latest batch wins for deduplication in the discovery pipeline).

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

# Use existing run directory so discovery deduplicates
CROSSREPO_JOBS="runs/official/crossrepo_opus_20260204_133742"

# Sourcegraph repo name mappings for all 4 tasks
declare -A CROSSREPO_SG=(
    ["api_upgrade_01"]="sg-benchmarks/etcd--d89978e8"
    ["bug_localization_01"]="sg-benchmarks/scikit-learn--cb7e82dd"
    ["cross_file_reasoning_01"]="sg-benchmarks/kubernetes--8c9c67c0"
    ["refactor_rename_01"]="sg-benchmarks/django--9e8f0953"
)

CONFIGS=("baseline" "sourcegraph_base" "sourcegraph_full")

# Helper functions
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

# Pre-flight
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

echo ""
echo "=============================================="
echo "All $TOTAL re-runs complete!"
echo "=============================================="
echo ""
echo "Results: ${CROSSREPO_JOBS}/{baseline,sourcegraph_base,sourcegraph_full}/"
echo ""
echo "Quick reward check:"
for config in baseline sourcegraph_base sourcegraph_full; do
    for f in "$CROSSREPO_JOBS/$config"/*/*/result.json; do
        if [ -f "$f" ]; then
            task=$(python3 -c "import json; d=json.load(open('$f')); print(d.get('task_name','?'))" 2>/dev/null)
            reward=$(python3 -c "import json; d=json.load(open('$f')); print(d.get('verifier_result',{}).get('rewards',{}).get('reward','?'))" 2>/dev/null)
            echo "  crossrepo/$config/$task: reward=$reward"
        fi
    done
done
