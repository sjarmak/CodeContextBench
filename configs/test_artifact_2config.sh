#!/bin/bash
# Artifact-only evaluation: ccb_test suite (baseline-local-artifact + mcp-remote-artifact).
#
# baseline-local-artifact: full local repo, no MCP. Agent produces review.json artifact.
# mcp-remote-artifact:     source deleted + Sourcegraph MCP. Agent produces review.json artifact.
# Verifier scores artifact applied to clean /repo_full copy.
#
# Usage:
#   ./configs/test_artifact_2config.sh [--baseline-only|--full-only] [--task TASK_ID] [--parallel N]

export SDLC_SUITE="ccb_test"
export SDLC_SUITE_LABEL="Test (Artifact-Only)"
export FULL_CONFIG="mcp-remote-artifact"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$SCRIPT_DIR/sdlc_suite_2config.sh" "$@"
