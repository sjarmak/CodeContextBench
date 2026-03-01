#!/bin/bash
set -euo pipefail

[ -f /tmp/.sg_only_mode ] && [ -f /tests/sgonly_verifier_wrapper.sh ] && source /tests/sgonly_verifier_wrapper.sh

SCORE=0
TOTAL=6
WORKSPACE="${VERIFY_REPO:-/workspace}"

# Check 1: Grammar updated with HEADER MATCH
if grep -rq 'HEADER.*MATCH\|header_match\|COPY_HEADER_MATCH' "$WORKSPACE/src/backend/parser/gram.y" 2>/dev/null; then
    SCORE=$((SCORE + 1))
    echo "PASS: Grammar updated with HEADER MATCH option"
else
    echo "FAIL: HEADER MATCH not found in gram.y"
fi

# Check 2: CopyHeaderChoice enum extended or equivalent flag
if grep -rq 'COPY_HEADER_MATCH\|header_match\|HeaderMatch\|HEADER_MATCH' \
    "$WORKSPACE/src/include/commands/copy.h" \
    "$WORKSPACE/src/backend/commands/copy.c" \
    "$WORKSPACE/src/backend/commands/copyfrom.c" 2>/dev/null; then
    SCORE=$((SCORE + 1))
    echo "PASS: Header match enum/flag defined"
else
    echo "FAIL: Header match enum/flag not found"
fi

# Check 3: Option processing handles HEADER MATCH
if grep -rq 'header.*match\|HEADER_MATCH\|header_match' \
    "$WORKSPACE/src/backend/commands/copy.c" \
    "$WORKSPACE/src/backend/commands/copyfrom.c" 2>/dev/null; then
    SCORE=$((SCORE + 1))
    echo "PASS: COPY option processing handles HEADER MATCH"
else
    echo "FAIL: Option processing for HEADER MATCH not found"
fi

# Check 4: Header validation logic (compare column names)
if grep -rq 'column.*name\|header.*validat\|mismatch\|attname\|NameStr' \
    "$WORKSPACE/src/backend/commands/copyfrom.c" 2>/dev/null; then
    # Check for actual comparison logic, not just existing code
    if grep -cq 'header_match\|HEADER_MATCH\|match.*column\|column.*match' \
        "$WORKSPACE/src/backend/commands/copyfrom.c" 2>/dev/null; then
        SCORE=$((SCORE + 1))
        echo "PASS: Header validation logic implemented in copyfrom.c"
    else
        echo "FAIL: Header validation logic not found in copyfrom.c"
    fi
else
    echo "FAIL: No column name comparison logic found"
fi

# Check 5: Error message for mismatch
if grep -rq 'mismatch\|does not match\|header.*match.*error\|column.*match' \
    "$WORKSPACE/src/backend/commands/copyfrom.c" \
    "$WORKSPACE/src/backend/commands/copy.c" 2>/dev/null; then
    SCORE=$((SCORE + 1))
    echo "PASS: Error message for header mismatch exists"
else
    echo "FAIL: No mismatch error message found"
fi

# Check 6: Regression test exists
if ls $WORKSPACE/src/test/regress/sql/*copy*header* \
      $WORKSPACE/src/test/regress/sql/copy*.sql 1>/dev/null 2>&1; then
    if grep -rq 'HEADER MATCH\|header match' "$WORKSPACE/src/test/regress/sql/" 2>/dev/null; then
        SCORE=$((SCORE + 1))
        echo "PASS: Regression test with HEADER MATCH exists"
    else
        echo "FAIL: Regression test found but no HEADER MATCH test cases"
    fi
else
    echo "FAIL: No regression test file found"
fi

echo ""
echo "Score: $SCORE / $TOTAL"

mkdir -p /logs/verifier
python3 -c "print($SCORE / $TOTAL)" > /logs/verifier/reward.txt
