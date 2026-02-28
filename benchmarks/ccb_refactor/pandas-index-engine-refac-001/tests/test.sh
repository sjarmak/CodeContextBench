#!/bin/bash
set -euo pipefail

[ -f /tmp/.sg_only_mode ] && [ -f /tests/sgonly_verifier_wrapper.sh ] && source /tests/sgonly_verifier_wrapper.sh

SCORE=0
TOTAL=6
WORKSPACE="${VERIFY_REPO:-/workspace}"

# Check 1: Old symbol removed from primary definition
OLD_DEF_COUNT=$( (grep -r 'class _engine\|type _engine struct\|def _engine\|function _engine' "$WORKSPACE/pandas/core/indexes/" 2>/dev/null | grep -v 'alias\|compat\|deprecated\|backward\|#.*_engine\|//.*_engine' || true) | wc -l)
if [ "$OLD_DEF_COUNT" -eq 0 ]; then
    SCORE=$((SCORE + 1))
    echo "PASS: Old symbol definition removed"
else
    echo "FAIL: Old symbol \"_engine\" still defined ($OLD_DEF_COUNT definitions found)"
fi

# Check 2: New symbol exists in definition
NEW_DEF_COUNT=$( (grep -r 'class _index_engine\|type _index_engine struct\|def _index_engine\|function _index_engine\|_index_engine' "$WORKSPACE/pandas/core/indexes/" 2>/dev/null || true) | wc -l)
if [ "$NEW_DEF_COUNT" -gt 0 ]; then
    SCORE=$((SCORE + 1))
    echo "PASS: New symbol \"_index_engine\" found ($NEW_DEF_COUNT occurrences)"
else
    echo "FAIL: New symbol \"_index_engine\" not found"
fi

# Check 3: Old symbol reference count reduced (allowing aliases/deprecation)
OLD_REF_COUNT=$( (grep -r '_engine' "$WORKSPACE/pandas/core/indexes/" 2>/dev/null | grep -v 'test\|_test\|spec\|alias\|compat\|deprecated\|backward\|#.*_engine\|//.*_engine\|\.pyc' || true) | wc -l)
if [ "$OLD_REF_COUNT" -le 3 ]; then
    SCORE=$((SCORE + 1))
    echo "PASS: Old symbol references minimized ($OLD_REF_COUNT remaining, max 3)"
else
    echo "FAIL: Too many old symbol references remain ($OLD_REF_COUNT, max 3)"
fi

# Check 4: New symbol used across multiple files
NEW_FILE_COUNT=$( (grep -rl '_index_engine' "$WORKSPACE/pandas/core/indexes/" 2>/dev/null || true) | wc -l)
if [ "$NEW_FILE_COUNT" -ge 2 ]; then
    SCORE=$((SCORE + 1))
    echo "PASS: New symbol used across $NEW_FILE_COUNT files"
else
    echo "FAIL: New symbol only in $NEW_FILE_COUNT files (need >= 2)"
fi

# Check 5: New symbol call sites meet threshold
NEW_REF_COUNT=$( (grep -r '_index_engine' "$WORKSPACE/pandas/core/indexes/" 2>/dev/null || true) | wc -l)
if [ "$NEW_REF_COUNT" -ge 10 ]; then
    SCORE=$((SCORE + 1))
    echo "PASS: New symbol has $NEW_REF_COUNT references (>= 10)"
else
    echo "FAIL: New symbol only has $NEW_REF_COUNT references (need >= 10)"
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
