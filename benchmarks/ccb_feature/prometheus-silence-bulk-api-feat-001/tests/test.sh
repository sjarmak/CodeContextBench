#!/bin/bash
set -euo pipefail

[ -f /tmp/.sg_only_mode ] && [ -f /tests/sgonly_verifier_wrapper.sh ] && source /tests/sgonly_verifier_wrapper.sh

SCORE=0
TOTAL=6
WORKSPACE="${VERIFY_REPO:-/workspace}"

# Check 1: Bulk endpoint handler exists
if grep -rq 'silences/bulk\|silencesBulk\|BulkSilence' "$WORKSPACE/web/api/v1/" 2>/dev/null; then
    SCORE=$((SCORE + 1))
    echo "PASS: Bulk endpoint handler exists"
else
    echo "FAIL: Bulk endpoint handler exists"
fi

# Check 2: Route registered
if grep -rq 'silences/bulk' "$WORKSPACE/web/api/v1/" 2>/dev/null; then
    SCORE=$((SCORE + 1))
    echo "PASS: Route registered"
else
    echo "FAIL: Route registered"
fi

# Check 3: Bulk handler function defined
if grep -rqE 'func.*bulk\|func.*Bulk' "$WORKSPACE/web/api/v1/" 2>/dev/null; then
    SCORE=$((SCORE + 1))
    echo "PASS: Bulk handler function defined"
else
    echo "FAIL: Bulk handler function defined"
fi

# Check 4: Accepts array input
if grep -rq '\[\].*Silence\|silences.*\[\]' "$WORKSPACE/web/api/v1/" 2>/dev/null; then
    SCORE=$((SCORE + 1))
    echo "PASS: Accepts array input"
else
    echo "FAIL: Accepts array input"
fi

# Check 5: Test file exists
if ls $WORKSPACE/web/api/v1/*bulk*test* 1>/dev/null 2>&1; then
    SCORE=$((SCORE + 1))
    echo "PASS: Test file exists"
else
    echo "FAIL: Test file exists"
fi

# Check 6: Test functions present
if grep -rq 'func Test.*[Bb]ulk' "$WORKSPACE/web/api/v1/" 2>/dev/null; then
    SCORE=$((SCORE + 1))
    echo "PASS: Test functions present"
else
    echo "FAIL: Test functions present"
fi

echo ""
echo "Score: $SCORE / $TOTAL"

mkdir -p /logs/verifier
python3 -c "print($SCORE / $TOTAL)" > /logs/verifier/reward.txt
