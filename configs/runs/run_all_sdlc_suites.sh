#!/bin/bash
# Run all 8 SDLC suites sequentially with haiku model.
# Each suite runs paired configs (baseline + MCP) with full parallelism.
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export MODEL=anthropic/claude-haiku-4-5-20251001

SUITES=(build debug document fix secure test understand)

echo "=============================================="
echo "Running all SDLC suites with haiku"
echo "Suites: ${SUITES[*]}"
echo "Model: $MODEL"
echo "=============================================="
echo ""

FAILED_SUITES=()

for suite in "${SUITES[@]}"; do
    echo ""
    echo ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
    echo ">>> Starting suite: csb_sdlc_${suite}"
    echo ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
    echo ""

    if bash "${SCRIPT_DIR}/${suite}_2config.sh"; then
        echo ">>> Suite csb_sdlc_${suite} completed successfully"
    else
        echo ">>> WARNING: Suite csb_sdlc_${suite} had errors (exit code: $?)"
        FAILED_SUITES+=("$suite")
    fi
done

echo ""
echo "=============================================="
echo "All SDLC suites complete!"
echo "=============================================="

if [ ${#FAILED_SUITES[@]} -gt 0 ]; then
    echo "Suites with errors: ${FAILED_SUITES[*]}"
else
    echo "All suites completed successfully"
fi
