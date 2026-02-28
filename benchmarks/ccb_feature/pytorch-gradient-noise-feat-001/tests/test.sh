#!/bin/bash
set -euo pipefail

[ -f /tmp/.sg_only_mode ] && [ -f /tests/sgonly_verifier_wrapper.sh ] && source /tests/sgonly_verifier_wrapper.sh

SCORE=0
TOTAL=6
WORKSPACE="${VERIFY_REPO:-/workspace}"

# Check 1: GradientNoiseInjector exists
if grep -rq 'GradientNoiseInjector' "$WORKSPACE/torch/optim/" 2>/dev/null; then
    SCORE=$((SCORE + 1))
    echo "PASS: GradientNoiseInjector exists"
else
    echo "FAIL: GradientNoiseInjector exists"
fi

# Check 2: Class defined
if grep -rq 'class GradientNoiseInjector' "$WORKSPACE/torch/optim/" 2>/dev/null; then
    SCORE=$((SCORE + 1))
    echo "PASS: Class defined"
else
    echo "FAIL: Class defined"
fi

# Check 3: step method present
if grep -rq 'def step' "$WORKSPACE/torch/optim/" 2>/dev/null; then
    SCORE=$((SCORE + 1))
    echo "PASS: step method present"
else
    echo "FAIL: step method present"
fi

# Check 4: Noise parameters present
if grep -rq 'eta\|gamma\|noise' "$WORKSPACE/torch/optim/" 2>/dev/null; then
    SCORE=$((SCORE + 1))
    echo "PASS: Noise parameters present"
else
    echo "FAIL: Noise parameters present"
fi

# Check 5: Noise generation
if grep -rq 'randn_like\|normal_\|noise' "$WORKSPACE/torch/optim/" 2>/dev/null; then
    SCORE=$((SCORE + 1))
    echo "PASS: Noise generation"
else
    echo "FAIL: Noise generation"
fi

# Check 6: Test file exists
if ls $WORKSPACE/test/optim/*gradient_noise*\|test/optim/*noise* 1>/dev/null 2>&1; then
    SCORE=$((SCORE + 1))
    echo "PASS: Test file exists"
else
    echo "FAIL: Test file exists"
fi

echo ""
echo "Score: $SCORE / $TOTAL"

mkdir -p /logs/verifier
python3 -c "print($SCORE / $TOTAL)" > /logs/verifier/reward.txt
