#!/bin/bash
# Reward: diff_similarity (0.0-1.0) — diff match to expected patch
set -e

# Create logs directory
mkdir -p /logs/verifier
PRE_FIX_REV="3ecf7c3d79894f8aa7e05aaacd288781c6e5da51"

# Run actual tests with partial credit
echo "Running test command: make test"
make test 2>&1 | tee /logs/verifier/test_output.log
TEST_EXIT_CODE=${PIPESTATUS[0]}

if [ "$TEST_EXIT_CODE" -eq 0 ]; then
    echo "[PASS] Tests passed"
    echo "1.0" > /logs/verifier/reward.txt
    exit 0
else
    # Attempt partial credit by parsing pytest output
    REWARD="0.0"
    if [ -f /logs/verifier/test_output.log ]; then
        PYTEST_LINE=$(grep -E '[0-9]+ passed' /logs/verifier/test_output.log 2>/dev/null | tail -1)
        if [ -n "$PYTEST_LINE" ]; then
            PASSED=$(echo "$PYTEST_LINE" | grep -oP '\d+(?= passed)' || echo "0")
            FAILED=$(echo "$PYTEST_LINE" | grep -oP '\d+(?= failed)' || echo "0")
            ERRORS=$(echo "$PYTEST_LINE" | grep -oP '\d+(?= error)' || echo "0")
            TOTAL=$((PASSED + FAILED + ERRORS))
            if [ "$TOTAL" -gt 0 ] 2>/dev/null; then
                REWARD=$(awk "BEGIN {printf \"%.4f\", $PASSED / $TOTAL}")
            fi
        fi
    fi
    echo "$REWARD" > /logs/verifier/reward.txt
    echo "[PARTIAL] Tests partially passed: $REWARD"
    exit 1
fi
