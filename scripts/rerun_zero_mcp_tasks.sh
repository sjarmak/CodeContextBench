#!/bin/bash
# Re-run tasks that had mcp_ratio=0 in MCP config runs.
#
# These 14 task+config combinations never used MCP tools despite having them
# available. The instruction preamble has been strengthened to require MCP
# as a mandatory first step (explore codebase via Sourcegraph before any edits).
#
# Results are written to per-benchmark directories matching the standard naming
# convention: runs/official/<benchmark>_opus_<timestamp>/sourcegraph_{base,full}/
# so that the analysis pipeline picks them up correctly.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

BENCH_DIR="/home/stephanie_jarmak/CodeContextBench/benchmarks"

# Agent code lives in-repo under agents/
export PYTHONPATH="$(pwd):${PYTHONPATH:-}"

# Shared config: subscription mode + token refresh
source "$(pwd)/configs/_common.sh"

# Load credentials
load_credentials

# Common parameters
MODEL="anthropic/claude-opus-4-5-20251101"
AGENT_PATH="agents.claude_baseline_agent:BaselineClaudeCodeAgent"
TIMEOUT_MULTIPLIER=10
CONCURRENCY=2

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
SELECTION_FILE="configs/selected_benchmark_tasks.json"

# Per-benchmark output directories (standard naming convention)
CROSSREPO_JOBS="runs/official/crossrepo_opus_${TIMESTAMP}"
DIBENCH_JOBS="runs/official/dibench_opus_${TIMESTAMP}"
LOCOBENCH_JOBS="runs/official/locobench_selected_opus_${TIMESTAMP}"
PYTORCH_JOBS="runs/official/pytorch_opus_${TIMESTAMP}"
SWEPERF_JOBS="runs/official/sweperf_opus_${TIMESTAMP}"

echo "=============================================="
echo "Re-running 14 zero-MCP task+config pairs"
echo "=============================================="
echo "Outputs:"
echo "  crossrepo -> ${CROSSREPO_JOBS}"
echo "  dibench   -> ${DIBENCH_JOBS}"
echo "  locobench -> ${LOCOBENCH_JOBS}"
echo "  pytorch   -> ${PYTORCH_JOBS}"
echo "  sweperf   -> ${SWEPERF_JOBS}"
echo ""

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
    if [ -n "$sg_repo" ]; then
        echo "  SOURCEGRAPH_REPO_NAME=${sg_repo}"
        sg_env="SOURCEGRAPH_REPO_NAME=$sg_repo"
    fi

    env $sg_env BASELINE_MCP_TYPE=$mcp_type harbor run \
        --path "$task_path" \
        --agent-import-path "$AGENT_PATH" \
        --model "$MODEL" \
        --jobs-dir "$jobs_subdir" \
        -n $CONCURRENCY \
        --timeout-multiplier $TIMEOUT_MULTIPLIER \
        2>&1 | tee "${jobs_subdir}/$(basename $task_path)_${mcp_type}.log" || true
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

# ============================================
# 1. CrossRepo: simple_test_01 (SB + SF)
# ============================================
run_task "[1/14] simple_test_01 (crossrepo SB)" \
    "${BENCH_DIR}/ccb_crossrepo/simple_test_01" \
    "sourcegraph_full" \
    "sg-evals/kubernetes--8c9c67c0" \
    "${CROSSREPO_JOBS}/sourcegraph_full"

run_task "[2/14] simple_test_01 (crossrepo SF)" \
    "${BENCH_DIR}/ccb_crossrepo/simple_test_01" \
    "sourcegraph_full" \
    "sg-evals/kubernetes--8c9c67c0" \
    "${CROSSREPO_JOBS}/sourcegraph_full"

extract_metrics "${CROSSREPO_JOBS}/sourcegraph_full" "ccb_crossrepo" "sourcegraph_full"
extract_metrics "${CROSSREPO_JOBS}/sourcegraph_full" "ccb_crossrepo" "sourcegraph_full"

# ============================================
# 2. DIBench: 4 tasks SB, 4 tasks SF
# ============================================
run_task "[3/14] dibench-python-inducer-cgen (SB)" \
    "${BENCH_DIR}/ccb_dibench/dibench-python-inducer-cgen" \
    "sourcegraph_full" \
    "sg-evals/cgen--dibench" \
    "${DIBENCH_JOBS}/sourcegraph_full"

run_task "[4/14] dibench-python-rhinosec-iamactionhunter (SB)" \
    "${BENCH_DIR}/ccb_dibench/dibench-python-rhinosec-iamactionhunter" \
    "sourcegraph_full" \
    "sg-evals/IAMActionHunter--dibench" \
    "${DIBENCH_JOBS}/sourcegraph_full"

run_task "[5/14] dibench-rust-rusticata-pcap-parser (SB)" \
    "${BENCH_DIR}/ccb_dibench/dibench-rust-rusticata-pcap-parser" \
    "sourcegraph_full" \
    "sg-evals/pcap-parser--dibench" \
    "${DIBENCH_JOBS}/sourcegraph_full"

run_task "[6/14] dibench-csharp-dotnetkoans (SB)" \
    "${BENCH_DIR}/ccb_dibench/dibench-csharp-dotnetkoans" \
    "sourcegraph_full" \
    "sg-evals/DotNetKoans--dibench" \
    "${DIBENCH_JOBS}/sourcegraph_full"

run_task "[7/14] dibench-python-inducer-cgen (SF)" \
    "${BENCH_DIR}/ccb_dibench/dibench-python-inducer-cgen" \
    "sourcegraph_full" \
    "sg-evals/cgen--dibench" \
    "${DIBENCH_JOBS}/sourcegraph_full"

run_task "[8/14] dibench-python-rhinosec-iamactionhunter (SF)" \
    "${BENCH_DIR}/ccb_dibench/dibench-python-rhinosec-iamactionhunter" \
    "sourcegraph_full" \
    "sg-evals/IAMActionHunter--dibench" \
    "${DIBENCH_JOBS}/sourcegraph_full"

run_task "[9/14] dibench-rust-mitsuhiko-similar-asserts (SF)" \
    "${BENCH_DIR}/ccb_dibench/dibench-rust-mitsuhiko-similar-asserts" \
    "sourcegraph_full" \
    "sg-evals/similar-asserts--dibench" \
    "${DIBENCH_JOBS}/sourcegraph_full"

run_task "[10/14] dibench-csharp-dotnetkoans (SF)" \
    "${BENCH_DIR}/ccb_dibench/dibench-csharp-dotnetkoans" \
    "sourcegraph_full" \
    "sg-evals/DotNetKoans--dibench" \
    "${DIBENCH_JOBS}/sourcegraph_full"

extract_metrics "${DIBENCH_JOBS}/sourcegraph_full" "ccb_dibench" "sourcegraph_full"
extract_metrics "${DIBENCH_JOBS}/sourcegraph_full" "ccb_dibench" "sourcegraph_full"

# ============================================
# 3. LoCoBench: 2 tasks (SF only)
# ============================================
run_task "[11/14] python_data_streaming_expert_085 (locobench SF)" \
    "${BENCH_DIR}/ccb_locobench/tasks/python_data_streaming_expert_085_cross_file_refactoring_expert_01" \
    "sourcegraph_full" \
    "sg-evals/locobench-python_data_streaming_expert_085" \
    "${LOCOBENCH_JOBS}/sourcegraph_full"

run_task "[12/14] python_desktop_development_expert_021 (locobench SF)" \
    "${BENCH_DIR}/ccb_locobench/tasks/python_desktop_development_expert_021_cross_file_refactoring_expert_01" \
    "sourcegraph_full" \
    "sg-evals/locobench-python_desktop_development_expert_021" \
    "${LOCOBENCH_JOBS}/sourcegraph_full"

extract_metrics "${LOCOBENCH_JOBS}/sourcegraph_full" "ccb_locobench" "sourcegraph_full"

# ============================================
# 4. PyTorch: sgt-008 (SB only)
# ============================================
run_task "[13/14] sgt-008 (pytorch SB)" \
    "${BENCH_DIR}/ccb_pytorch/sgt-008" \
    "sourcegraph_full" \
    "sg-evals/pytorch--863edc78" \
    "${PYTORCH_JOBS}/sourcegraph_full"

extract_metrics "${PYTORCH_JOBS}/sourcegraph_full" "ccb_pytorch" "sourcegraph_full"

# ============================================
# 5. SWE-Perf: sweperf-001 (SB only)
# ============================================
run_task "[14/14] sweperf-001 (sweperf SB)" \
    "${BENCH_DIR}/ccb_sweperf/tasks/sweperf-001" \
    "sourcegraph_full" \
    "sg-evals/numpy--a639fbf5" \
    "${SWEPERF_JOBS}/sourcegraph_full"

extract_metrics "${SWEPERF_JOBS}/sourcegraph_full" "ccb_sweperf" "sourcegraph_full"

# ============================================
# Summary
# ============================================
echo ""
echo "=============================================="
echo "Zero-MCP re-runs complete!"
echo "=============================================="
echo ""
echo "Results by benchmark:"
echo "  ${CROSSREPO_JOBS}/sourcegraph_{base,full}/"
echo "  ${DIBENCH_JOBS}/sourcegraph_{base,full}/"
echo "  ${LOCOBENCH_JOBS}/sourcegraph_full/"
echo "  ${PYTORCH_JOBS}/sourcegraph_full/"
echo "  ${SWEPERF_JOBS}/sourcegraph_full/"
echo ""
echo "Check MCP usage:"
for d in "$CROSSREPO_JOBS" "$DIBENCH_JOBS" "$LOCOBENCH_JOBS" "$PYTORCH_JOBS" "$SWEPERF_JOBS"; do
    for f in "$d"/sourcegraph_*/*/task_metrics.json "$d"/sourcegraph_*/*/*/task_metrics.json; do
        if [ -f "$f" ]; then
            task=$(python3 -c "import json; print(json.load(open('$f')).get('task_name','?'))")
            ratio=$(python3 -c "import json; print(json.load(open('$f')).get('mcp_ratio','?'))")
            echo "  $task -> mcp_ratio=$ratio"
        fi
    done
done
