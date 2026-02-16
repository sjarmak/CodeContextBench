#!/usr/bin/env bash
# Verifier for navprove-tutanota-search-001
# Sources the shared find_and_prove_verifier to run 2-phase majority-of-3 verification.

export AGENT_TEST_PATH="/workspace/regression_test.test.ts"
export TEST_COMMAND="npx jest --timeout=60000"
export REFERENCE_PATCH="/tests/reference_fix.patch"
export PATCH_APPLY_DIR="/workspace"

source /tests/find_and_prove_verifier.sh
