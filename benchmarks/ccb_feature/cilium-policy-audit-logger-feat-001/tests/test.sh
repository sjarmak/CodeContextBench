#!/bin/bash
set -euo pipefail

[ -f /tmp/.sg_only_mode ] && [ -f /tests/sgonly_verifier_wrapper.sh ] && source /tests/sgonly_verifier_wrapper.sh

SCORE=0
TOTAL=6
WORKSPACE="${VERIFY_REPO:-/workspace}"

# Check 1: Audit logger file exists
if [ -f "$WORKSPACE/pkg/policy/audit_logger.go" ]; then
    SCORE=$((SCORE + 1))
    echo "PASS: Audit logger file exists"
else
    echo "FAIL: Audit logger file exists"
fi

# Check 2: PolicyAuditLogger struct defined
if grep -q 'PolicyAuditLogger' "$WORKSPACE/pkg/policy/audit_logger.go" 2>/dev/null; then
    SCORE=$((SCORE + 1))
    echo "PASS: PolicyAuditLogger struct defined"
else
    echo "FAIL: PolicyAuditLogger struct defined"
fi

# Check 3: LogDecision method present
if grep -q 'LogDecision\|logDecision' "$WORKSPACE/pkg/policy/audit_logger.go" 2>/dev/null; then
    SCORE=$((SCORE + 1))
    echo "PASS: LogDecision method present"
else
    echo "FAIL: LogDecision method present"
fi

# Check 4: Uses logging framework
if grep -q 'logrus\|scopedLog\|log\.' "$WORKSPACE/pkg/policy/audit_logger.go" 2>/dev/null; then
    SCORE=$((SCORE + 1))
    echo "PASS: Uses logging framework"
else
    echo "FAIL: Uses logging framework"
fi

# Check 5: Test file exists
if [ -f "$WORKSPACE/pkg/policy/audit_logger_test.go" ]; then
    SCORE=$((SCORE + 1))
    echo "PASS: Test file exists"
else
    echo "FAIL: Test file exists"
fi

# Check 6: Test functions present
if grep -q 'func Test' "$WORKSPACE/pkg/policy/audit_logger_test.go" 2>/dev/null; then
    SCORE=$((SCORE + 1))
    echo "PASS: Test functions present"
else
    echo "FAIL: Test functions present"
fi

echo ""
echo "Score: $SCORE / $TOTAL"

mkdir -p /logs/verifier
python3 -c "print($SCORE / $TOTAL)" > /logs/verifier/reward.txt
