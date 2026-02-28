#!/bin/bash
set -euo pipefail

[ -f /tmp/.sg_only_mode ] && [ -f /tests/sgonly_verifier_wrapper.sh ] && source /tests/sgonly_verifier_wrapper.sh

SCORE=0
TOTAL=6
WORKSPACE="${VERIFY_REPO:-/workspace}"

# Check 1: Compact formatter file exists
if [ -f "$WORKSPACE/internal/command/format/compact.go" ]; then
    SCORE=$((SCORE + 1))
    echo "PASS: Compact formatter file exists"
else
    echo "FAIL: Compact formatter file exists"
fi

# Check 2: CompactDiffFormatter defined
if grep -q 'CompactDiffFormatter' "$WORKSPACE/internal/command/format/compact.go" 2>/dev/null; then
    SCORE=$((SCORE + 1))
    echo "PASS: CompactDiffFormatter defined"
else
    echo "FAIL: CompactDiffFormatter defined"
fi

# Check 3: Format method present
if grep -q 'func.*Format\|func.*format' "$WORKSPACE/internal/command/format/compact.go" 2>/dev/null; then
    SCORE=$((SCORE + 1))
    echo "PASS: Format method present"
else
    echo "FAIL: Format method present"
fi

# Check 4: Uses plans package
if grep -q 'plans\.' "$WORKSPACE/internal/command/format/compact.go" 2>/dev/null; then
    SCORE=$((SCORE + 1))
    echo "PASS: Uses plans package"
else
    echo "FAIL: Uses plans package"
fi

# Check 5: Test file exists
if [ -f "$WORKSPACE/internal/command/format/compact_test.go" ]; then
    SCORE=$((SCORE + 1))
    echo "PASS: Test file exists"
else
    echo "FAIL: Test file exists"
fi

# Check 6: Test functions present
if grep -q 'func Test' "$WORKSPACE/internal/command/format/compact_test.go" 2>/dev/null; then
    SCORE=$((SCORE + 1))
    echo "PASS: Test functions present"
else
    echo "FAIL: Test functions present"
fi

echo ""
echo "Score: $SCORE / $TOTAL"

mkdir -p /logs/verifier
python3 -c "print($SCORE / $TOTAL)" > /logs/verifier/reward.txt
