#!/bin/bash
# Re-run tasks affected by the ralph/benchmark-task-fixes branch.
#
# Affected benchmarks and tasks:
#   - crossrepo:  all 5 tasks (ground truth rewritten)
#   - largerepo:  all 4 tasks (test.sh compilation checks added)
#   - pytorch:    sgt-005, sgt-008, sgt-009, sgt-010, sgt-016, sgt-025 (metadata fixes)
#   - k8sdocs:    pkg-doc-001 only (ground truth expanded)
#
# Total: 16 tasks x 3 configs = 48 runs
#
# This script:
#   1. Archives existing results for affected tasks into runs/official/archive/pre_fix_<date>/
#   2. Re-runs all 48 task+config pairs with the fixed task definitions
#   3. Extracts metrics after each benchmark completes

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
ARCHIVE_DIR="runs/official/archive/pre_fix_${TIMESTAMP}"

# Output directories
CROSSREPO_JOBS="runs/official/crossrepo_opus_${TIMESTAMP}"
LARGEREPO_JOBS="runs/official/bigcode_mcp_opus_${TIMESTAMP}"
PYTORCH_JOBS="runs/official/pytorch_opus_${TIMESTAMP}"
K8SDOCS_JOBS="runs/official/k8s_docs_opus_${TIMESTAMP}"

# ============================================
# Sourcegraph repo name mappings
# ============================================
declare -A CROSSREPO_SG=(
    ["api_upgrade_01"]="sg-benchmarks/etcd--d89978e8"
    ["bug_localization_01"]="sg-benchmarks/scikit-learn--cb7e82dd"
    ["cross_file_reasoning_01"]="sg-benchmarks/kubernetes--8c9c67c0"
    ["refactor_rename_01"]="sg-benchmarks/django--674eda1c"
    ["simple_test_01"]="sg-benchmarks/kubernetes--8c9c67c0"
)

declare -A LARGEREPO_SG=(
    ["big-code-k8s-001"]="sg-benchmarks/kubernetes--latest"
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
# Phase 1: Archive existing affected results
# ============================================
echo "=============================================="
echo "Phase 1: Archiving affected results"
echo "=============================================="
echo "Archive directory: ${ARCHIVE_DIR}"
mkdir -p "${ARCHIVE_DIR}"

# Archive crossrepo results
for d in runs/official/crossrepo_opus_*/; do
    if [ -d "$d" ] && [ "$d" != "${CROSSREPO_JOBS}/" ]; then
        dest="${ARCHIVE_DIR}/crossrepo/$(basename $d)"
        echo "  Archiving $d -> $dest"
        mkdir -p "$(dirname "$dest")"
        mv "$d" "$dest"
    fi
done

# Archive largerepo results
for d in runs/official/bigcode_mcp_opus_*/; do
    if [ -d "$d" ] && [ "$d" != "${LARGEREPO_JOBS}/" ]; then
        dest="${ARCHIVE_DIR}/largerepo/$(basename $d)"
        echo "  Archiving $d -> $dest"
        mkdir -p "$(dirname "$dest")"
        mv "$d" "$dest"
    fi
done

# Archive affected pytorch task results (move entire run dirs that contain affected tasks)
# We archive the full run dirs; unaffected tasks within them remain accessible in archive
for d in runs/official/pytorch_opus_*/; do
    if [ -d "$d" ] && [ "$d" != "${PYTORCH_JOBS}/" ]; then
        dest="${ARCHIVE_DIR}/pytorch/$(basename $d)"
        echo "  Archiving $d -> $dest"
        mkdir -p "$(dirname "$dest")"
        cp -r "$d" "$dest"
        # Remove only affected task results from the live directory
        for task in sgt-005 sgt-008 sgt-009 sgt-010 sgt-016 sgt-025; do
            for config in baseline sourcegraph_base sourcegraph_full; do
                # Remove result directories matching affected tasks
                find "$d/$config/" -name "result.json" -exec grep -l "\"$task\"" {} \; 2>/dev/null | while read f; do
                    trial_dir=$(dirname "$f")
                    echo "    Removing affected result: $trial_dir"
                    rm -rf "$trial_dir" 2>/dev/null || sudo rm -rf "$trial_dir" 2>/dev/null || echo "    WARNING: Could not remove $trial_dir (permission denied, skipping)"
                done
                # Remove task logs
                rm -f "$d/$config/${task}"*.log 2>/dev/null
            done
        done
    fi
done

# Archive k8sdocs pkg-doc-001 results only (keep other task results in place)
for d in runs/official/k8s_docs_opus_*/; do
    if [ -d "$d" ] && [ "$d" != "${K8SDOCS_JOBS}/" ]; then
        dest="${ARCHIVE_DIR}/k8sdocs/$(basename $d)"
        echo "  Archiving pkg-doc-001 from $d -> $dest"
        mkdir -p "$dest"
        for config in baseline sourcegraph_base sourcegraph_full; do
            find "$d/$config/" -name "result.json" -exec grep -l "pkg-doc-001" {} \; 2>/dev/null | while read f; do
                trial_dir=$(dirname "$f")
                cp -r "$trial_dir" "$dest/$(basename $trial_dir)"
                echo "    Archived: $trial_dir"
                rm -rf "$trial_dir" 2>/dev/null || sudo rm -rf "$trial_dir" 2>/dev/null || echo "    WARNING: Could not remove $trial_dir (permission denied, skipping)"
            done
        done
    fi
done

echo ""
echo "Archive complete: ${ARCHIVE_DIR}"
echo ""

# ============================================
# Phase 2: Re-run affected tasks
# ============================================
TOTAL=48
N=0

echo "=============================================="
echo "Phase 2: Re-running 48 task+config pairs"
echo "=============================================="
echo "Outputs:"
echo "  crossrepo -> ${CROSSREPO_JOBS}"
echo "  largerepo -> ${LARGEREPO_JOBS}"
echo "  pytorch   -> ${PYTORCH_JOBS}"
echo "  k8sdocs   -> ${K8SDOCS_JOBS}"
echo ""

# --- CrossRepo: 5 tasks x 3 configs = 15 ---
CROSSREPO_TASKS=(api_upgrade_01 bug_localization_01 cross_file_reasoning_01 refactor_rename_01 simple_test_01)
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

# --- LargeRepo: 4 tasks x 3 configs = 12 ---
LARGEREPO_TASKS=(big-code-k8s-001 big-code-servo-001 big-code-trt-001 big-code-vsc-001)
for task in "${LARGEREPO_TASKS[@]}"; do
    for config in "${CONFIGS[@]}"; do
        N=$((N + 1))
        mcp=$(mcp_type_for_config "$config")
        run_task "[$N/$TOTAL] $task (largerepo $config)" \
            "${BENCH_DIR}/ccb_largerepo/${task}" \
            "$mcp" \
            "${LARGEREPO_SG[$task]}" \
            "${LARGEREPO_JOBS}/${config}"
    done
done

for config in "${CONFIGS[@]}"; do
    extract_metrics "${LARGEREPO_JOBS}/${config}" "ccb_largerepo" "$config"
done

# --- PyTorch: 6 tasks x 3 configs = 18 ---
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

# --- K8sDocs: pkg-doc-001 x 3 configs = 3 ---
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
echo "  ${CROSSREPO_JOBS}/{baseline,sourcegraph_base,sourcegraph_full}/"
echo "  ${LARGEREPO_JOBS}/{baseline,sourcegraph_base,sourcegraph_full}/"
echo "  ${PYTORCH_JOBS}/{baseline,sourcegraph_base,sourcegraph_full}/"
echo "  ${K8SDOCS_JOBS}/{baseline,sourcegraph_base,sourcegraph_full}/"
echo ""
echo "Archived pre-fix results:"
echo "  ${ARCHIVE_DIR}/"
echo ""
echo "Quick reward check:"
for d in "$CROSSREPO_JOBS" "$LARGEREPO_JOBS" "$PYTORCH_JOBS" "$K8SDOCS_JOBS"; do
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
