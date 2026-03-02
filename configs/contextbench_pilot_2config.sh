#!/bin/bash
# ContextBench Cross-Validation Pilot: baseline + MCP (50 tasks)
#
# Runs Harbor task-solving agent on ContextBench SWE-bench tasks in both
# baseline (full local code) and MCP (Sourcegraph) configurations.
#
# Prerequisites:
#   1. Run scripts/select_contextbench_pilot.py to select tasks
#   2. Run scripts/create_sg_mirrors.py to create mirrors
#   3. Wait 24-48h for Sourcegraph indexing
#   4. Run scripts/scaffold_contextbench_tasks.py to create task dirs
#
# Usage:
#   source .env.local && export HARBOR_ENV=daytona && export DAYTONA_OVERRIDE_STORAGE=10240
#   bash configs/contextbench_pilot_2config.sh

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

source "$SCRIPT_DIR/_common.sh"
load_credentials
enforce_subscription_mode

# Selection file produced by scaffold_contextbench_tasks.py
export SELECTION_FILE="$REPO_ROOT/configs/contextbench_run_selection.json"
export CATEGORY="staging"
export MODEL="${MODEL:-anthropic/claude-haiku-4-5-20251001}"

if [ ! -f "$SELECTION_FILE" ]; then
    echo "ERROR: Selection file not found: $SELECTION_FILE"
    echo "Run: python3 scripts/scaffold_contextbench_tasks.py first"
    exit 1
fi

TASK_COUNT=$(python3 -c "import json; print(len(json.load(open('$SELECTION_FILE'))))")
echo "=== ContextBench Cross-Validation Pilot ==="
echo "Tasks:    $TASK_COUNT"
echo "Configs:  baseline-local-direct + mcp-remote-direct"
echo "Category: $CATEGORY"
echo "Model:    $MODEL"
echo "Env:      ${HARBOR_ENV:-local}"
echo ""

"$SCRIPT_DIR/run_selected_tasks.sh" \
    --selection-file "$SELECTION_FILE" \
    --benchmark ccb_contextbench \
    --full-config mcp-remote-direct \
    --category "$CATEGORY"
