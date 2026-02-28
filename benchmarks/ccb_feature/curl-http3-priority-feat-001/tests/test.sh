#!/bin/bash
set -euo pipefail

[ -f /tmp/.sg_only_mode ] && [ -f /tests/sgonly_verifier_wrapper.sh ] && source /tests/sgonly_verifier_wrapper.sh

SCORE=0
TOTAL=6
WORKSPACE="${VERIFY_REPO:-/workspace}"

# Check 1: CURLOPT_H3_STREAM_PRIORITY defined
if grep -rq 'CURLOPT_H3_STREAM_PRIORITY\|CURLOPT_H3_PRIORITY\|H3_STREAM_PRIORITY' "$WORKSPACE/include/" 2>/dev/null; then
    SCORE=$((SCORE + 1))
    echo "PASS: H3 priority option defined in headers"
else
    echo "FAIL: H3 priority option not found in include/"
fi

# Check 2: Priority fields in urldata.h
if grep -q 'urgency\|h3_priority\|stream_priority' "$WORKSPACE/lib/urldata.h" 2>/dev/null; then
    SCORE=$((SCORE + 1))
    echo "PASS: Priority fields added to urldata.h"
else
    echo "FAIL: Priority fields not found in urldata.h"
fi

# Check 3: setopt.c handles the new option
if grep -rq 'H3.*PRIORITY\|h3_priority\|stream_priority' "$WORKSPACE/lib/setopt.c" 2>/dev/null; then
    SCORE=$((SCORE + 1))
    echo "PASS: setopt.c handles priority option"
else
    echo "FAIL: setopt.c doesn't handle priority"
fi

# Check 4: HTTP/3 backend references priority
if grep -rq 'priority\|urgency\|incremental' "$WORKSPACE/lib/vquic/" 2>/dev/null; then
    SCORE=$((SCORE + 1))
    echo "PASS: HTTP/3 backend references priority"
else
    echo "FAIL: HTTP/3 backend missing priority support"
fi

# Check 5: CLI option exists
if grep -rq 'h3.priority\|h3-priority\|H3_PRIORITY' "$WORKSPACE/src/tool_getparam.c" 2>/dev/null; then
    SCORE=$((SCORE + 1))
    echo "PASS: CLI --h3-priority option exists"
else
    echo "FAIL: CLI option not found"
fi

# Check 6: Test file exists
if ls $WORKSPACE/tests/*h3*priority* $WORKSPACE/tests/unit/*h3*priority* $WORKSPACE/tests/unit/*priority* 1>/dev/null 2>&1; then
    SCORE=$((SCORE + 1))
    echo "PASS: Test file exists"
else
    echo "FAIL: Test file not found"
fi

echo ""
echo "Score: $SCORE / $TOTAL"

mkdir -p /logs/verifier
python3 -c "print($SCORE / $TOTAL)" > /logs/verifier/reward.txt
