#!/bin/bash
set -euo pipefail

[ -f /tmp/.sg_only_mode ] && [ -f /tests/sgonly_verifier_wrapper.sh ] && source /tests/sgonly_verifier_wrapper.sh

SCORE=0
TOTAL=6
WORKSPACE="${VERIFY_REPO:-/workspace}"

# Check 1: Controller file exists
if ls $WORKSPACE/pkg/policy/quota/controller.go $WORKSPACE/pkg/policy/quota/*.go 1>/dev/null 2>&1; then
    SCORE=$((SCORE + 1))
    echo "PASS: Policy quota controller file exists"
else
    echo "FAIL: Policy quota controller file not found"
fi

# Check 2: PolicyQuotaController struct defined
if grep -rq 'PolicyQuotaController' "$WORKSPACE/pkg/policy/quota/" 2>/dev/null; then
    SCORE=$((SCORE + 1))
    echo "PASS: PolicyQuotaController struct defined"
else
    echo "FAIL: PolicyQuotaController not found"
fi

# Check 3: CheckQuota or Run method present
if grep -rq 'CheckQuota\|func.*Run\|func.*Start' "$WORKSPACE/pkg/policy/quota/" 2>/dev/null; then
    SCORE=$((SCORE + 1))
    echo "PASS: Controller methods present"
else
    echo "FAIL: Controller methods missing"
fi

# Check 4: CRD type exists
if grep -rq 'CiliumPolicyQuota\|PolicyQuota' "$WORKSPACE/pkg/k8s/" 2>/dev/null; then
    SCORE=$((SCORE + 1))
    echo "PASS: CRD type defined"
else
    echo "FAIL: CRD type not found"
fi

# Check 5: Uses Cilium patterns (hive/resource/logfields)
if grep -rq 'hive\|resource\.\|logfields\|scopedLog' "$WORKSPACE/pkg/policy/quota/" 2>/dev/null; then
    SCORE=$((SCORE + 1))
    echo "PASS: Uses Cilium framework patterns"
else
    echo "FAIL: Missing Cilium framework usage"
fi

# Check 6: Test file exists
if ls $WORKSPACE/pkg/policy/quota/*test* 1>/dev/null 2>&1 && grep -q 'func Test' $WORKSPACE/pkg/policy/quota/*test* 2>/dev/null; then
    SCORE=$((SCORE + 1))
    echo "PASS: Test file with test functions exists"
else
    echo "FAIL: Test file missing or no test functions"
fi

echo ""
echo "Score: $SCORE / $TOTAL"

mkdir -p /logs/verifier
python3 -c "print($SCORE / $TOTAL)" > /logs/verifier/reward.txt
