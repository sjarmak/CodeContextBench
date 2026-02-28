#!/bin/bash
set -euo pipefail

[ -f /tmp/.sg_only_mode ] && [ -f /tests/sgonly_verifier_wrapper.sh ] && source /tests/sgonly_verifier_wrapper.sh

SCORE=0
TOTAL=6
WORKSPACE="${VERIFY_REPO:-/workspace}"

# Check 1: RateLimitMiddleware file exists
if [ -f "$WORKSPACE/django/middleware/ratelimit.py" ]; then
    SCORE=$((SCORE + 1))
    echo "PASS: RateLimitMiddleware file exists"
else
    echo "FAIL: RateLimitMiddleware file exists"
fi

# Check 2: RateLimitMiddleware class defined
if grep -q 'class RateLimitMiddleware' "$WORKSPACE/django/middleware/ratelimit.py" 2>/dev/null; then
    SCORE=$((SCORE + 1))
    echo "PASS: RateLimitMiddleware class defined"
else
    echo "FAIL: RateLimitMiddleware class defined"
fi

# Check 3: process_request method present
if grep -q 'process_request' "$WORKSPACE/django/middleware/ratelimit.py" 2>/dev/null; then
    SCORE=$((SCORE + 1))
    echo "PASS: process_request method present"
else
    echo "FAIL: process_request method present"
fi

# Check 4: Uses cache framework
if grep -q 'cache' "$WORKSPACE/django/middleware/ratelimit.py" 2>/dev/null; then
    SCORE=$((SCORE + 1))
    echo "PASS: Uses cache framework"
else
    echo "FAIL: Uses cache framework"
fi

# Check 5: Returns 429 response
if grep -q '429\|HttpResponseTooManyRequests\|TooManyRequests' "$WORKSPACE/django/middleware/ratelimit.py" 2>/dev/null; then
    SCORE=$((SCORE + 1))
    echo "PASS: Returns 429 response"
else
    echo "FAIL: Returns 429 response"
fi

# Check 6: Test file exists
if [ -f "$WORKSPACE/tests/middleware/test_ratelimit.py" ]; then
    SCORE=$((SCORE + 1))
    echo "PASS: Test file exists"
else
    echo "FAIL: Test file exists"
fi

echo ""
echo "Score: $SCORE / $TOTAL"

mkdir -p /logs/verifier
python3 -c "print($SCORE / $TOTAL)" > /logs/verifier/reward.txt
