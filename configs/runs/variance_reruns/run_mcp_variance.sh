#!/bin/bash
# MCP-unique variance reruns — 3-pass launcher
#
# Pass 1: all 187 gap tasks (everyone gets 1 more pair)
# Pass 2: 51 tasks needing >= 2 more pairs (zero-pair + one-pair)
# Pass 3: 43 tasks needing 3 more pairs (zero-pair only)
#
# Total: 281 paired runs (562 agent runs)
#
# Prerequisites:
#   source .env.local && export HARBOR_ENV=daytona && export DAYTONA_OVERRIDE_STORAGE=10240
#
# Usage:
#   bash configs/variance_reruns/run_mcp_variance.sh [--pass N] [--dry-run]
#
#   --pass N    Run only pass N (1, 2, or 3). Default: all 3 sequentially.
#   --dry-run   Dry-run all passes without launching.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$SCRIPT_DIR/../.."
cd "$REPO_ROOT"

PASS_FILTER=""
DRY_RUN_FLAG=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --pass)   PASS_FILTER="$2"; shift 2 ;;
        --dry-run) DRY_RUN_FLAG="--dry-run"; shift ;;
        *)        echo "Unknown option: $1"; exit 1 ;;
    esac
done

# Validate environment
if [ "${HARBOR_ENV:-}" != "daytona" ]; then
    echo "ERROR: HARBOR_ENV must be 'daytona'. Run:"
    echo "  source .env.local && export HARBOR_ENV=daytona && export DAYTONA_OVERRIDE_STORAGE=10240"
    exit 1
fi

CONFIGS=(
    "configs/variance_reruns/variance_gap_mcp_unique.json"   # Pass 1: 187 tasks
    "configs/variance_reruns/variance_gap_mcp_pass2.json"    # Pass 2: 51 tasks
    "configs/variance_reruns/variance_gap_mcp_pass3.json"    # Pass 3: 43 tasks
)

PASS_NAMES=("Pass 1 (all 187 tasks)" "Pass 2 (51 tasks, need >=2)" "Pass 3 (43 tasks, need 3)")

for i in 0 1 2; do
    pass_num=$(( i + 1 ))

    # Skip if --pass filter is set and doesn't match
    if [ -n "$PASS_FILTER" ] && [ "$PASS_FILTER" != "$pass_num" ]; then
        continue
    fi

    config="${CONFIGS[$i]}"
    name="${PASS_NAMES[$i]}"

    echo "=============================================="
    echo "  ${name}"
    echo "  Config: ${config}"
    echo "=============================================="
    echo ""

    if [ ! -f "$config" ]; then
        echo "ERROR: Config not found: $config"
        exit 1
    fi

    bash configs/run_selected_tasks.sh \
        --selection-file "$config" \
        --skip-prebuild \
        $DRY_RUN_FLAG

    if [ -z "$DRY_RUN_FLAG" ]; then
        echo ""
        echo "${name} complete. Waiting 10s before next pass..."
        sleep 10
    fi
done

echo ""
echo "All passes complete."
