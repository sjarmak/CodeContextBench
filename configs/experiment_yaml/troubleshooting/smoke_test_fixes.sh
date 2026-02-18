#!/bin/bash
# Smoke Test: Eval Framework Fixes
#
# Validates the three critical fixes (US-001 through US-004):
# 1. Harbor --user root permission fix
# 2. Agent-side permission setup (no sudo)
# 3. EVALUATION CONTEXT delivery via system prompt
# 4. Single-source test-first instructions
#
# Runs 3 SWE-bench Pro tasks x 2 modes (baseline + hybrid) = 6 trials
#
# Usage:
#   ./configs/troubleshooting/smoke_test_fixes.sh              # Run both modes
#   ./configs/troubleshooting/smoke_test_fixes.sh --baseline-only
#   ./configs/troubleshooting/smoke_test_fixes.sh --mcp-only
#
# Prerequisites:
#   - ~/evals/.env.local with ANTHROPIC_API_KEY (required)
#   - SOURCEGRAPH_ACCESS_TOKEN in .env.local (required for MCP mode)
#   - Harbor installed and patched (run scripts/patch_harbor_docker.sh first)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/../.."

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

echo "ANTHROPIC_API_KEY: set (${#ANTHROPIC_API_KEY} chars)"
if [ -n "$SOURCEGRAPH_ACCESS_TOKEN" ]; then
    echo "SOURCEGRAPH_ACCESS_TOKEN: set (${#SOURCEGRAPH_ACCESS_TOKEN} chars)"
else
    echo "SOURCEGRAPH_ACCESS_TOKEN: not set"
fi
echo ""

# ============================================
# CONFIGURATION
# ============================================
AGENT_PATH="agents.claude_baseline_agent:BaselineClaudeCodeAgent"
MODEL="${MODEL:-anthropic/claude-opus-4-5-20251101}"
CONCURRENCY=1
TIMEOUT_MULTIPLIER=20
RUN_BASELINE=true
RUN_MCP=true
CATEGORY=troubleshooting

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --baseline-only)
            RUN_MCP=false
            shift
            ;;
        --mcp-only)
            RUN_BASELINE=false
            shift
            ;;
        --model)
            MODEL="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Check MCP credentials if MCP mode requested
if [ "$RUN_MCP" = true ] && [ -z "$SOURCEGRAPH_ACCESS_TOKEN" ]; then
    echo "WARNING: MCP mode requested but SOURCEGRAPH_ACCESS_TOKEN not set"
    echo "Skipping MCP runs. Use --baseline-only to suppress this warning."
    RUN_MCP=false
fi

# SWE-bench Pro task IDs for smoke test
TASK_IDS=(
    "instance_flipt-io__flipt-aebaecd026f752b187f11328b0d464761b15d2ab"
    "instance_navidrome__navidrome-bf2bcb12799b21069f137749e0c331f761d1f693"
    "instance_ansible__ansible-4c5ce5a1a9e79a845aff4978cfeb72a0d4ecf7d6-v1055803c3a812189a1133297f7f5468579283f86"
)

# Derive short model name for run directory (matches V2 id_generator convention)
_model_lower=$(echo "$MODEL" | awk -F/ '{print $NF}' | tr '[:upper:]' '[:lower:]')
case "$_model_lower" in
    *opus*)   MODEL_SHORT="opus" ;;
    *sonnet*) MODEL_SHORT="sonnet" ;;
    *haiku*)  MODEL_SHORT="haiku" ;;
    *gpt-4o*|*gpt4o*) MODEL_SHORT="gpt4o" ;;
    *gpt-4*|*gpt4*)   MODEL_SHORT="gpt4" ;;
    *)        MODEL_SHORT=$(echo "$_model_lower" | tr -d '-' | tr -d '_' | cut -c1-8) ;;
esac

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
JOBS_BASE="runs/${CATEGORY}/smoke_test_fixes_${MODEL_SHORT}_${TIMESTAMP}"

echo "=============================================="
echo "Smoke Test: Eval Framework Fixes"
echo "=============================================="
echo "Model: ${MODEL}"
echo "Tasks: ${#TASK_IDS[@]}"
echo "Concurrency: ${CONCURRENCY}"
echo "Jobs directory: ${JOBS_BASE}"
echo "Run baseline: ${RUN_BASELINE}"
echo "Run MCP: ${RUN_MCP}"
echo ""

# Create jobs directory
mkdir -p "${JOBS_BASE}"

# ============================================
# RUN BASELINE
# ============================================
if [ "$RUN_BASELINE" = true ]; then
    echo ""
    echo "[BASELINE] Starting smoke test baseline run (${#TASK_IDS[@]} tasks)..."
    echo ""

    for task_id in "${TASK_IDS[@]}"; do
        echo "  Running baseline: ${task_id}"
        BASELINE_MCP_TYPE=none harbor run \
            --dataset swebenchpro@1.0 \
            -t "${task_id}" \
            --agent-import-path "${AGENT_PATH}" \
            --model "${MODEL}" \
            --jobs-dir "${JOBS_BASE}/baseline" \
            -n ${CONCURRENCY} \
            --timeout-multiplier ${TIMEOUT_MULTIPLIER} \
            2>&1 | tee -a "${JOBS_BASE}/baseline.log"
    done
fi

# ============================================
# RUN MCP VARIANT (Sourcegraph Hybrid - 14 tools)
# ============================================
if [ "$RUN_MCP" = true ]; then
    echo ""
    echo "[SOURCEGRAPH HYBRID] Starting smoke test MCP run (${#TASK_IDS[@]} tasks, 14 Sourcegraph tools)..."
    echo ""

    for task_id in "${TASK_IDS[@]}"; do
        echo "  Running sourcegraph_full: ${task_id}"
        BASELINE_MCP_TYPE=sourcegraph_full harbor run \
            --dataset swebenchpro@1.0 \
            -t "${task_id}" \
            --agent-import-path "${AGENT_PATH}" \
            --model "${MODEL}" \
            --jobs-dir "${JOBS_BASE}/sourcegraph_full" \
            -n ${CONCURRENCY} \
            --timeout-multiplier ${TIMEOUT_MULTIPLIER} \
            2>&1 | tee -a "${JOBS_BASE}/sourcegraph_full.log"
    done
fi

echo ""
echo "=============================================="
echo "Smoke Test Complete!"
echo "=============================================="
echo "Results saved to: ${JOBS_BASE}"
echo ""
echo "Validation checks:"
echo "  # Check for permission errors"
echo "  grep -r 'EACCES' ${JOBS_BASE}/*/instance_*/agent/claude-code.txt"
echo ""
echo "  # Check EVALUATION CONTEXT delivery"
echo "  grep -l 'EVALUATION CONTEXT\|MUST run the test suite BEFORE' ${JOBS_BASE}/*/instance_*/agent/claude-code.txt"
echo ""
echo "  # Check rewards"
echo "  cat ${JOBS_BASE}/*/instance_*/result.json | jq '.trials[].verifier_result.rewards.reward'"
echo ""
echo "View results:"
if [ "$RUN_BASELINE" = true ]; then
    echo "  # Baseline summary"
    echo "  cat ${JOBS_BASE}/baseline/*/result.json | jq -s 'map(.trials[].verifier_result.rewards.reward) | {mean: (add/length), count: length}'"
    echo ""
fi
if [ "$RUN_MCP" = true ]; then
    echo "  # MCP summary"
    echo "  cat ${JOBS_BASE}/sourcegraph_full/*/result.json | jq -s 'map(.trials[].verifier_result.rewards.reward) | {mean: (add/length), count: length}'"
fi
