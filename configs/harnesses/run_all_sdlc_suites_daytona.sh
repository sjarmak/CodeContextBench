#!/bin/bash
# Re-run all SDLC and org suites via Daytona (2-config: baseline + MCP).
# Created to restart batch after VM spindown on 2026-03-17.
# Usage: HARBOR_ENV=daytona bash configs/harnesses/run_all_sdlc_suites_daytona.sh
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export HARBOR_ENV="${HARBOR_ENV:-daytona}"
export MODEL="${MODEL:-anthropic/claude-haiku-4-5-20251001}"

SDLC_SUITES=(debug design document feature fix refactor secure test understand)
ORG_SUITES=(compliance crossorg)

ALL_SUITES=("${SDLC_SUITES[@]}" "${ORG_SUITES[@]}")

echo "=============================================="
echo "Running all SDLC + Org suites via Daytona"
echo "Suites: ${ALL_SUITES[*]}"
echo "Model: $MODEL"
echo "HARBOR_ENV: $HARBOR_ENV"
echo "=============================================="
echo ""

FAILED_SUITES=()

for suite in "${ALL_SUITES[@]}"; do
    echo ""
    echo ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
    echo ">>> Starting suite: ${suite}"
    echo ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
    echo ""

    wrapper="${SCRIPT_DIR}/${suite}_2config.sh"
    if [ ! -f "$wrapper" ]; then
        echo ">>> ERROR: No wrapper found for suite: ${suite} (expected $wrapper)"
        FAILED_SUITES+=("$suite")
        continue
    fi

    if bash "$wrapper"; then
        echo ">>> Suite ${suite} completed successfully"
    else
        echo ">>> WARNING: Suite ${suite} had errors (exit code: $?)"
        FAILED_SUITES+=("$suite")
    fi
done

echo ""
echo "=============================================="
echo "All suites complete!"
echo "=============================================="

if [ ${#FAILED_SUITES[@]} -gt 0 ]; then
    echo "Suites with errors: ${FAILED_SUITES[*]}"
    exit 1
else
    echo "All suites completed successfully"
fi
