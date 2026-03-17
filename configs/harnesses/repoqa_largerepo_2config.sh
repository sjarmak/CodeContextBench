#!/bin/bash
# Run the 28 large-repo RepoQA SR-QA tasks (14 csb_sdlc_understand + 14 csb_org_onboarding).
# Uses paired baseline + MCP execution via sdlc_suite_2config.sh infrastructure.
#
# Usage:
#   bash configs/repoqa_largerepo_2config.sh                     # default: opus
#   bash configs/repoqa_largerepo_2config.sh --model anthropic/claude-haiku-4-5-20251001
#   bash configs/repoqa_largerepo_2config.sh --parallel 4
#   bash configs/repoqa_largerepo_2config.sh --baseline-only

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# --- Part 1: csb_sdlc_understand (14 RepoQA tasks) ---
echo "=== Part 1/2: csb_sdlc_understand RepoQA tasks (14) ==="
SDLC_SUITE="csb_sdlc_understand" SDLC_SUITE_LABEL="Understand — RepoQA Large-Repo" \
    bash "$SCRIPT_DIR/sdlc_suite_2config.sh" \
    --task k8s-scheduler-filter-search-001 \
    --task k8s-eviction-sync-search-001 \
    --task kafka-batch-drain-search-001 \
    --task kafka-assign-handler-search-001 \
    --task rust-type-tests-search-001 \
    --task rust-liveness-gen-search-001 \
    --task firefox-http-response-search-001 \
    --task firefox-cache-race-search-001 \
    --task envoy-retry-eval-search-001 \
    --task envoy-pool-ready-search-001 \
    --task sklearn-fastica-fit-search-001 \
    --task pandas-pivot-internal-search-001 \
    --task vscode-keybinding-merge-search-001 \
    --task grafana-field-calcs-search-001 \
    "$@"

echo ""
echo "=== Part 2/2: csb_org_onboarding RepoQA tasks (14) ==="
SDLC_SUITE="csb_org_onboarding" SDLC_SUITE_LABEL="MCP Onboarding — RepoQA Large-Repo" \
    bash "$SCRIPT_DIR/sdlc_suite_2config.sh" \
    --task ccx-onboard-search-201 \
    --task ccx-onboard-search-202 \
    --task ccx-onboard-search-203 \
    --task ccx-onboard-search-204 \
    --task ccx-onboard-search-205 \
    --task ccx-onboard-search-206 \
    --task ccx-onboard-search-207 \
    --task ccx-onboard-search-208 \
    --task ccx-onboard-search-209 \
    --task ccx-onboard-search-210 \
    --task ccx-onboard-search-211 \
    --task ccx-onboard-search-212 \
    --task ccx-onboard-search-213 \
    --task ccx-onboard-search-214 \
    "$@"

echo ""
echo "=== All 28 RepoQA large-repo tasks complete ==="
