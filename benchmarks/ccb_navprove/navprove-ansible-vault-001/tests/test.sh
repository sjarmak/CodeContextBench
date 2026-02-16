#!/usr/bin/env bash
# Verifier for navprove-ansible-vault-001
# Sources the shared find_and_prove_verifier to run 2-phase majority-of-3 verification.

export AGENT_TEST_PATH="/workspace/regression_test.py"
export TEST_COMMAND="python3 -m pytest --timeout=60"
export REFERENCE_PATCH="/tests/reference_fix.patch"
export PATCH_APPLY_DIR="/workspace"

source /tests/find_and_prove_verifier.sh
