#!/bin/bash
set -euo pipefail

[ -f /tmp/.sg_only_mode ] && [ -f /tests/sgonly_verifier_wrapper.sh ] && source /tests/sgonly_verifier_wrapper.sh

SCORE=0
TOTAL=6
WORKSPACE="${VERIFY_REPO:-/workspace}"

# Check 1: Old symbol removed from primary definition
OLD_DEF_COUNT=$(grep -r 'class _multi_tensor_\|type _multi_tensor_ struct\|def _multi_tensor_\|function _multi_tensor_' "$WORKSPACE/torch/optim/" 2>/dev/null | grep -v 'alias\|compat\|deprecated\|backward\|#.*_multi_tensor_\|//.*_multi_tensor_' | wc -l)
if [ "$OLD_DEF_COUNT" -eq 0 ]; then
    SCORE=$((SCORE + 1))
    echo "PASS: Old symbol definition removed"
else
    echo "FAIL: Old symbol \"_multi_tensor_\" still defined ($OLD_DEF_COUNT definitions found)"
fi

# Check 2: New symbol exists in definition
NEW_DEF_COUNT=$(grep -r 'class _foreach_optimizer_step\|type _foreach_optimizer_step struct\|def _foreach_optimizer_step\|function _foreach_optimizer_step\|_foreach_optimizer_step' "$WORKSPACE/torch/optim/" 2>/dev/null | wc -l)
if [ "$NEW_DEF_COUNT" -gt 0 ]; then
    SCORE=$((SCORE + 1))
    echo "PASS: New symbol \"_foreach_optimizer_step\" found ($NEW_DEF_COUNT occurrences)"
else
    echo "FAIL: New symbol \"_foreach_optimizer_step\" not found"
fi

# Check 3: Old symbol reference count reduced (allowing aliases/deprecation)
OLD_REF_COUNT=$(grep -r '_multi_tensor_' "$WORKSPACE/torch/optim/" 2>/dev/null | grep -v 'test\|_test\|spec\|alias\|compat\|deprecated\|backward\|#.*_multi_tensor_\|//.*_multi_tensor_\|\.pyc' | wc -l)
if [ "$OLD_REF_COUNT" -le 3 ]; then
    SCORE=$((SCORE + 1))
    echo "PASS: Old symbol references minimized ($OLD_REF_COUNT remaining, max 3)"
else
    echo "FAIL: Too many old symbol references remain ($OLD_REF_COUNT, max 3)"
fi

# Check 4: New symbol used across multiple files
NEW_FILE_COUNT=$(grep -rl '_foreach_optimizer_step' "$WORKSPACE/torch/optim/" 2>/dev/null | wc -l)
if [ "$NEW_FILE_COUNT" -ge 2 ]; then
    SCORE=$((SCORE + 1))
    echo "PASS: New symbol used across $NEW_FILE_COUNT files"
else
    echo "FAIL: New symbol only in $NEW_FILE_COUNT files (need >= 2)"
fi

# Check 5: New symbol call sites meet threshold
NEW_REF_COUNT=$(grep -r '_foreach_optimizer_step' "$WORKSPACE/torch/optim/" 2>/dev/null | wc -l)
if [ "$NEW_REF_COUNT" -ge 4 ]; then
    SCORE=$((SCORE + 1))
    echo "PASS: New symbol has $NEW_REF_COUNT references (>= 4)"
else
    echo "FAIL: New symbol only has $NEW_REF_COUNT references (need >= 4)"
fi

# Check 6: Code changes were actually made (git diff check)
cd "$WORKSPACE"
CHANGED_FILES=$(git diff --name-only 2>/dev/null | wc -l)
COMMITTED_FILES=$(git log --oneline --name-only -1 2>/dev/null | tail -n +2 | wc -l)
TOTAL_CHANGES=$((CHANGED_FILES + COMMITTED_FILES))
if [ "$TOTAL_CHANGES" -ge 2 ]; then
    SCORE=$((SCORE + 1))
    echo "PASS: Multiple files changed ($TOTAL_CHANGES)"
else
    echo "FAIL: Not enough files changed ($TOTAL_CHANGES, need >= 2)"
fi

echo ""
echo "Score: $SCORE / $TOTAL"

mkdir -p /logs/verifier
python3 -c "print($SCORE / $TOTAL)" > /logs/verifier/reward.txt
