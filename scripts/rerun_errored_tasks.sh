#!/bin/bash
# Re-run the 29 task+config pairs that errored with RuntimeError (token expiry)
# during the rerun_fixed_tasks.sh execution on 2026-02-04.
#
# Errored pairs:
#   - largerepo:  servo SB/SF, trt BL/SB/SF, vsc BL/SB/SF  (8 pairs)
#   - pytorch:    sgt-005/008/009/010/016/025 x BL/SB/SF    (18 pairs)
#   - k8sdocs:    pkg-doc-001 x BL/SB/SF                    (3 pairs)
#
# Total: 29 task+config pairs
#
# NOT included:
#   - crossrepo: All 15 runs completed but scored 0.0 due to evaluation
#     infrastructure issues (missing validate_patch.py + no patch collection
#     in agent instructions). Requires separate fix.
#   - largerepo k8s: All 3 configs completed OK (scored 0.0).
#   - largerepo servo baseline: Completed OK (scored 0.0).

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

# Output directories — use new timestamp to avoid colliding with prior run
LARGEREPO_JOBS="runs/official/bigcode_mcp_opus_${TIMESTAMP}"
PYTORCH_JOBS="runs/official/pytorch_opus_${TIMESTAMP}"
K8SDOCS_JOBS="runs/official/k8s_docs_opus_${TIMESTAMP}"

# ============================================
# Sourcegraph repo name mappings
# ============================================
declare -A LARGEREPO_SG=(
    ["big-code-servo-001"]="sg-benchmarks/servo--latest"
    ["big-code-trt-001"]="sg-benchmarks/TensorRT-LLM--latest"
    ["big-code-vsc-001"]="sg-benchmarks/vscode--latest"
)

declare -A PYTORCH_SG=(
    ["sgt-005"]="sg-benchmarks/pytorch--ca246612"
    ["sgt-008"]="sg-benchmarks/pytorch--863edc78"
    ["sgt-009"]="sg-benchmarks/pytorch--863edc78"
    ["sgt-010"]="sg-benchmarks/pytorch--5811a8d7"
    ["sgt-016"]="sg-benchmarks/pytorch--cbe1a35d"
    ["sgt-025"]="sg-benchmarks/pytorch--e8ca8cc3"
)

K8SDOCS_SG="sg-benchmarks/kubernetes--8c9c67c0"

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
echo "Re-running 29 errored task+config pairs"
echo "=============================================="
echo "Token status:"
ensure_fresh_token
echo ""
echo "Outputs:"
echo "  largerepo -> ${LARGEREPO_JOBS}"
echo "  pytorch   -> ${PYTORCH_JOBS}"
echo "  k8sdocs   -> ${K8SDOCS_JOBS}"
echo ""

TOTAL=29
N=0

# ============================================
# LargeRepo: 8 errored pairs
#   servo: BL completed (0.0), SB/SF errored
#   trt:   BL/SB/SF all errored
#   vsc:   BL/SB/SF all errored
# ============================================

# servo: only SB and SF
for config in "sourcegraph_base" "sourcegraph_full"; do
    N=$((N + 1))
    mcp=$(mcp_type_for_config "$config")
    run_task "[$N/$TOTAL] big-code-servo-001 (largerepo $config)" \
        "${BENCH_DIR}/ccb_largerepo/big-code-servo-001" \
        "$mcp" \
        "${LARGEREPO_SG[big-code-servo-001]}" \
        "${LARGEREPO_JOBS}/${config}"
done

# trt: all 3 configs
for config in "${CONFIGS[@]}"; do
    N=$((N + 1))
    mcp=$(mcp_type_for_config "$config")
    run_task "[$N/$TOTAL] big-code-trt-001 (largerepo $config)" \
        "${BENCH_DIR}/ccb_largerepo/big-code-trt-001" \
        "$mcp" \
        "${LARGEREPO_SG[big-code-trt-001]}" \
        "${LARGEREPO_JOBS}/${config}"
done

# vsc: all 3 configs
for config in "${CONFIGS[@]}"; do
    N=$((N + 1))
    mcp=$(mcp_type_for_config "$config")
    run_task "[$N/$TOTAL] big-code-vsc-001 (largerepo $config)" \
        "${BENCH_DIR}/ccb_largerepo/big-code-vsc-001" \
        "$mcp" \
        "${LARGEREPO_SG[big-code-vsc-001]}" \
        "${LARGEREPO_JOBS}/${config}"
done

for config in "${CONFIGS[@]}"; do
    extract_metrics "${LARGEREPO_JOBS}/${config}" "ccb_largerepo" "$config"
done

# ============================================
# PyTorch: 18 errored pairs (all 6 tasks x 3 configs)
# ============================================
PYTORCH_TASKS=(sgt-005 sgt-008 sgt-009 sgt-010 sgt-016 sgt-025)
for task in "${PYTORCH_TASKS[@]}"; do
    for config in "${CONFIGS[@]}"; do
        N=$((N + 1))
        mcp=$(mcp_type_for_config "$config")
        run_task "[$N/$TOTAL] $task (pytorch $config)" \
            "${BENCH_DIR}/ccb_pytorch/${task}" \
            "$mcp" \
            "${PYTORCH_SG[$task]}" \
            "${PYTORCH_JOBS}/${config}"
    done
done

for config in "${CONFIGS[@]}"; do
    extract_metrics "${PYTORCH_JOBS}/${config}" "ccb_pytorch" "$config"
done

# ============================================
# K8sDocs: 3 errored pairs (pkg-doc-001 x 3 configs)
# ============================================
for config in "${CONFIGS[@]}"; do
    N=$((N + 1))
    mcp=$(mcp_type_for_config "$config")
    sg_env=""
    if [ "$mcp" != "none" ]; then
        sg_env="$K8SDOCS_SG"
    fi
    run_task "[$N/$TOTAL] pkg-doc-001 (k8sdocs $config)" \
        "${BENCH_DIR}/ccb_k8sdocs/pkg-doc-001" \
        "$mcp" \
        "$sg_env" \
        "${K8SDOCS_JOBS}/${config}"
done

for config in "${CONFIGS[@]}"; do
    extract_metrics "${K8SDOCS_JOBS}/${config}" "ccb_k8sdocs" "$config"
done

# ============================================
# Summary
# ============================================
echo ""
echo "=============================================="
echo "All $TOTAL re-runs complete!"
echo "=============================================="
echo ""
echo "Results:"
echo "  ${LARGEREPO_JOBS}/{baseline,sourcegraph_base,sourcegraph_full}/"
echo "  ${PYTORCH_JOBS}/{baseline,sourcegraph_base,sourcegraph_full}/"
echo "  ${K8SDOCS_JOBS}/{baseline,sourcegraph_base,sourcegraph_full}/"
echo ""
echo "Quick reward check:"
for d in "$LARGEREPO_JOBS" "$PYTORCH_JOBS" "$K8SDOCS_JOBS"; do
    bench=$(basename "$d" | sed 's/_opus_.*//')
    for config in baseline sourcegraph_base sourcegraph_full; do
        for f in "$d/$config"/*/*/result.json "$d/$config"/*/result.json; do
            if [ -f "$f" ]; then
                task=$(python3 -c "import json; d=json.load(open('$f')); print(d.get('task_id', d.get('name','?')))" 2>/dev/null)
                reward=$(python3 -c "import json; d=json.load(open('$f')); t=d.get('trials',[{}]); print(t[0].get('verifier_result',{}).get('rewards',{}).get('reward','?') if t else '?')" 2>/dev/null)
                echo "  $bench/$config/$task: reward=$reward"
            fi
        done
    done
done
echo ""
echo "NOTE: Crossrepo tasks were NOT re-run. They require evaluation"
echo "infrastructure fixes (validate_patch.py + patch collection) first."
