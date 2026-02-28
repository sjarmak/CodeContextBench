#!/bin/bash
set -euo pipefail

[ -f /tmp/.sg_only_mode ] && [ -f /tests/sgonly_verifier_wrapper.sh ] && source /tests/sgonly_verifier_wrapper.sh

SCORE=0
TOTAL=6
WORKSPACE="${VERIFY_REPO:-/workspace}"

# Check 1: rolling_median function exists
if grep -rq 'rolling_median' "$WORKSPACE/numpy/lib/" 2>/dev/null; then
    SCORE=$((SCORE + 1))
    echo "PASS: rolling_median function exists"
else
    echo "FAIL: rolling_median function exists"
fi

# Check 2: Function definition present
if grep -rq 'def rolling_median' "$WORKSPACE/numpy/lib/" 2>/dev/null; then
    SCORE=$((SCORE + 1))
    echo "PASS: Function definition present"
else
    echo "FAIL: Function definition present"
fi

# Check 3: Accepts window parameter
if grep -rq 'window_size\|window' "$WORKSPACE/numpy/lib/" 2>/dev/null; then
    SCORE=$((SCORE + 1))
    echo "PASS: Accepts window parameter"
else
    echo "FAIL: Accepts window parameter"
fi

# Check 4: Uses dispatch decorator
if grep -rq 'array_function_dispatch\|dispatch' "$WORKSPACE/numpy/lib/" 2>/dev/null; then
    SCORE=$((SCORE + 1))
    echo "PASS: Uses dispatch decorator"
else
    echo "FAIL: Uses dispatch decorator"
fi

# Check 5: Test file exists
if ls $WORKSPACE/numpy/lib/tests/*rolling* 1>/dev/null 2>&1; then
    SCORE=$((SCORE + 1))
    echo "PASS: Test file exists"
else
    echo "FAIL: Test file exists"
fi

# Check 6: Tests reference rolling_median
if grep -rq 'rolling_median\|test_rolling' "$WORKSPACE/numpy/lib/tests/" 2>/dev/null; then
    SCORE=$((SCORE + 1))
    echo "PASS: Tests reference rolling_median"
else
    echo "FAIL: Tests reference rolling_median"
fi

echo ""
echo "Score: $SCORE / $TOTAL"

mkdir -p /logs/verifier
python3 -c "print($SCORE / $TOTAL)" > /logs/verifier/reward.txt
