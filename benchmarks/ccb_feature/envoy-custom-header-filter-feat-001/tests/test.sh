#!/bin/bash
set -euo pipefail

[ -f /tmp/.sg_only_mode ] && [ -f /tests/sgonly_verifier_wrapper.sh ] && source /tests/sgonly_verifier_wrapper.sh

SCORE=0
TOTAL=6
WORKSPACE="${VERIFY_REPO:-/workspace}"

# Check 1: Filter header exists
if ls $WORKSPACE/source/extensions/filters/http/custom_header_injection/*.h 1>/dev/null 2>&1; then
    SCORE=$((SCORE + 1))
    echo "PASS: Filter header exists"
else
    echo "FAIL: Filter header exists"
fi

# Check 2: Filter implementation exists
if ls $WORKSPACE/source/extensions/filters/http/custom_header_injection/*.cc 1>/dev/null 2>&1; then
    SCORE=$((SCORE + 1))
    echo "PASS: Filter implementation exists"
else
    echo "FAIL: Filter implementation exists"
fi

# Check 3: Filter methods present
if grep -rq 'decodeHeaders\|encodeHeaders' "$WORKSPACE/source/extensions/filters/http/custom_header_injection/" 2>/dev/null; then
    SCORE=$((SCORE + 1))
    echo "PASS: Filter methods present"
else
    echo "FAIL: Filter methods present"
fi

# Check 4: Inherits filter interfaces
if grep -rq 'StreamDecoderFilter\|StreamEncoderFilter' "$WORKSPACE/source/extensions/filters/http/custom_header_injection/" 2>/dev/null; then
    SCORE=$((SCORE + 1))
    echo "PASS: Inherits filter interfaces"
else
    echo "FAIL: Inherits filter interfaces"
fi

# Check 5: Filter name registered
if grep -rq 'custom_header_injection' "$WORKSPACE/source/extensions/filters/http/custom_header_injection/" 2>/dev/null; then
    SCORE=$((SCORE + 1))
    echo "PASS: Filter name registered"
else
    echo "FAIL: Filter name registered"
fi

# Check 6: Test file exists
if ls $WORKSPACE/test/extensions/filters/http/custom_header_injection/*test* 1>/dev/null 2>&1; then
    SCORE=$((SCORE + 1))
    echo "PASS: Test file exists"
else
    echo "FAIL: Test file exists"
fi

echo ""
echo "Score: $SCORE / $TOTAL"

mkdir -p /logs/verifier
python3 -c "print($SCORE / $TOTAL)" > /logs/verifier/reward.txt
