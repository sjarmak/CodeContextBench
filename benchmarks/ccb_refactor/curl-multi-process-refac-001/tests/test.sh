#!/bin/bash
set -euo pipefail

[ -f /tmp/.sg_only_mode ] && [ -f /tests/sgonly_verifier_wrapper.sh ] && source /tests/sgonly_verifier_wrapper.sh

SCORE=0
TOTAL=6
WORKSPACE="${VERIFY_REPO:-/workspace}"

# Check 1: Old symbol removed from primary definition
OLD_DEF_COUNT=$( (grep -r 'process_pending_handles' "$WORKSPACE/lib/" 2>/dev/null | grep -v 'multi_activate_pending\|alias\|compat\|deprecated\|backward\|/\*.*process_pending_handles\|//.*process_pending_handles' || true) | wc -l)
if [ "$OLD_DEF_COUNT" -eq 0 ]; then
    SCORE=$((SCORE + 1))
    echo "PASS: Old symbol definition removed"
else
    echo "FAIL: Old symbol \"process_pending_handles\" still found ($OLD_DEF_COUNT references)"
fi

# Check 2: New symbol exists in definition
NEW_DEF_COUNT=$( (grep -r 'multi_activate_pending' "$WORKSPACE/lib/" 2>/dev/null || true) | wc -l)
if [ "$NEW_DEF_COUNT" -gt 0 ]; then
    SCORE=$((SCORE + 1))
    echo "PASS: New symbol \"multi_activate_pending\" found ($NEW_DEF_COUNT occurrences)"
else
    echo "FAIL: New symbol \"multi_activate_pending\" not found"
fi

# Check 3: Old symbol completely gone (no non-comment references)
OLD_REF_COUNT=$( (grep -r 'process_pending_handles' "$WORKSPACE/lib/" 2>/dev/null | grep -v 'multi_activate_pending\|test\|_test\|spec\|alias\|compat\|deprecated\|/\*.*process_pending_handles\|//.*process_pending_handles' || true) | wc -l)
if [ "$OLD_REF_COUNT" -le 3 ]; then
    SCORE=$((SCORE + 1))
    echo "PASS: Old symbol references minimized ($OLD_REF_COUNT remaining, max 3)"
else
    echo "FAIL: Too many old symbol references remain ($OLD_REF_COUNT, max 3)"
fi

# Check 4: New symbol used in multiple places (function def + call sites)
NEW_REF_COUNT=$( (grep -r 'multi_activate_pending' "$WORKSPACE/lib/" 2>/dev/null || true) | wc -l)
if [ "$NEW_REF_COUNT" -ge 2 ]; then
    SCORE=$((SCORE + 1))
    echo "PASS: New symbol has $NEW_REF_COUNT references (>= 2)"
else
    echo "FAIL: New symbol only has $NEW_REF_COUNT references (need >= 2)"
fi

# Check 5: Function is static in multi.c
if grep -q 'static.*multi_activate_pending' "$WORKSPACE/lib/multi.c" 2>/dev/null; then
    SCORE=$((SCORE + 1))
    echo "PASS: Function is static in multi.c"
else
    echo "FAIL: Function not found as static in multi.c"
fi

# Check 6: Code changes were actually made (git diff check)
cd "$WORKSPACE"
CHANGED_FILES=$(git diff --name-only 2>/dev/null | wc -l)
COMMITTED_FILES=$(git log --oneline --name-only -1 2>/dev/null | tail -n +2 | wc -l)
TOTAL_CHANGES=$((CHANGED_FILES + COMMITTED_FILES))
if [ "$TOTAL_CHANGES" -ge 1 ]; then
    SCORE=$((SCORE + 1))
    echo "PASS: Files changed ($TOTAL_CHANGES)"
else
    echo "FAIL: No files changed"
fi

echo ""
echo "Score: $SCORE / $TOTAL"

mkdir -p /logs/verifier
python3 -c "print($SCORE / $TOTAL)" > /logs/verifier/reward.txt
