#!/bin/bash
# Relaunch the 4 remaining SDLC suites that were not run in the original batch.
# Original batch (20260221_174306) completed: document, test, understand, build
# Remaining: debug (20), design (20), fix (25), secure (20) = 85 tasks
#
# Artifact config: baseline-local-artifact + mcp-remote-artifact
# Model: claude-haiku-4-5-20251001
# Parallel: 12 slots (3 accounts x 4 sessions)
#
# Usage: ./configs/rerun_remaining_suites.sh
set -euo pipefail

cd "$(dirname "$0")/.."

MODEL="anthropic/claude-haiku-4-5-20251001"
FULL_CONFIG="mcp-remote-artifact"
PARALLEL=12

for SUITE in ccb_debug ccb_design ccb_fix ccb_secure; do
    echo ""
    echo "=============================================="
    echo "Launching suite: $SUITE"
    echo "=============================================="
    ./configs/run_selected_tasks.sh \
        --benchmark "$SUITE" \
        --full-config "$FULL_CONFIG" \
        --model "$MODEL" \
        --parallel "$PARALLEL" \
        --yes
    echo ""
    echo "=== $SUITE complete ==="
    echo ""
done

echo ""
echo "=============================================="
echo "All 4 remaining suites complete!"
echo "=============================================="
