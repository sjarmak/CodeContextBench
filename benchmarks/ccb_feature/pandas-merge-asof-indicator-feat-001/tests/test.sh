#!/bin/bash
set -euo pipefail

[ -f /tmp/.sg_only_mode ] && [ -f /tests/sgonly_verifier_wrapper.sh ] && source /tests/sgonly_verifier_wrapper.sh

SCORE=0
TOTAL=6
WORKSPACE="${VERIFY_REPO:-/workspace}"

# Check 1: merge_asof accepts indicator
if grep -q 'indicator.*merge_asof\|merge_asof.*indicator' "$WORKSPACE/pandas/core/reshape/merge.py" 2>/dev/null; then
    SCORE=$((SCORE + 1))
    echo "PASS: merge_asof accepts indicator"
else
    echo "FAIL: merge_asof accepts indicator"
fi

# Check 2: AsOfMerge handles indicator
if grep -q '_AsOfMerge.*indicator\|indicator.*_AsOfMerge' "$WORKSPACE/pandas/core/reshape/merge.py" 2>/dev/null; then
    SCORE=$((SCORE + 1))
    echo "PASS: AsOfMerge handles indicator"
else
    echo "FAIL: AsOfMerge handles indicator"
fi

# Check 3: Indicator column logic
if grep -rq 'indicator.*column\|_merge.*indicator' "$WORKSPACE/pandas/core/reshape/" 2>/dev/null; then
    SCORE=$((SCORE + 1))
    echo "PASS: Indicator column logic"
else
    echo "FAIL: Indicator column logic"
fi

# Check 4: Indicator values
if grep -rq 'both.*left_only\|left_only.*right_only' "$WORKSPACE/pandas/core/reshape/" 2>/dev/null; then
    SCORE=$((SCORE + 1))
    echo "PASS: Indicator values"
else
    echo "FAIL: Indicator values"
fi

# Check 5: Tests for indicator
if grep -rq 'indicator.*asof\|asof.*indicator\|test.*indicator' "$WORKSPACE/pandas/tests/reshape/merge/" 2>/dev/null; then
    SCORE=$((SCORE + 1))
    echo "PASS: Tests for indicator"
else
    echo "FAIL: Tests for indicator"
fi

# Check 6: Test checks indicator column
if grep -rq '_merge\|indicator' "$WORKSPACE/pandas/tests/reshape/merge/" 2>/dev/null; then
    SCORE=$((SCORE + 1))
    echo "PASS: Test checks indicator column"
else
    echo "FAIL: Test checks indicator column"
fi

echo ""
echo "Score: $SCORE / $TOTAL"

mkdir -p /logs/verifier
python3 -c "print($SCORE / $TOTAL)" > /logs/verifier/reward.txt
