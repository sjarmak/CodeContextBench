#!/bin/bash
set -euo pipefail

[ -f /tmp/.sg_only_mode ] && [ -f /tests/sgonly_verifier_wrapper.sh ] && source /tests/sgonly_verifier_wrapper.sh

SCORE=0
TOTAL=6
WORKSPACE="${VERIFY_REPO:-/workspace}"

# Check 1: Named region detection/provider code exists
if grep -rq 'namedRegion\|named.*region\|regionName\|region_name\|NamedFoldingRegion' \
    "$WORKSPACE/src/vs/editor/contrib/folding/" 2>/dev/null; then
    SCORE=$((SCORE + 1))
    echo "PASS: Named region provider code exists"
else
    echo "FAIL: Named region provider not found in folding contrib"
fi

# Check 2: Region name extraction from #region markers
if grep -rq '#region\|region.*marker\|extractRegionName\|regionPattern\|REGION_PATTERN' \
    "$WORKSPACE/src/vs/editor/contrib/folding/" 2>/dev/null; then
    SCORE=$((SCORE + 1))
    echo "PASS: Region name extraction logic exists"
else
    echo "FAIL: Region name extraction not found"
fi

# Check 3: Command registration for Go to Region
if grep -rq 'goToNamedRegion\|goToRegion\|GoToNamedRegion\|go.*to.*region' \
    "$WORKSPACE/src/vs/editor/contrib/folding/" 2>/dev/null; then
    SCORE=$((SCORE + 1))
    echo "PASS: Go to Region command registered"
else
    echo "FAIL: Go to Region command not found"
fi

# Check 4: Quick-pick integration
if grep -rq 'quickInput\|QuickPick\|quickpick\|IQuickInputService\|showQuickPick' \
    "$WORKSPACE/src/vs/editor/contrib/folding/" 2>/dev/null; then
    SCORE=$((SCORE + 1))
    echo "PASS: Quick-pick integration for region navigation"
else
    echo "FAIL: Quick-pick integration not found in folding"
fi

# Check 5: Decoration or placeholder for region names
if grep -rq 'decoration\|Decoration\|placeholder.*region\|region.*label\|foldingDecoration' \
    "$WORKSPACE/src/vs/editor/contrib/folding/" 2>/dev/null; then
    SCORE=$((SCORE + 1))
    echo "PASS: Region name decoration/placeholder exists"
else
    echo "FAIL: Region name decoration not found"
fi

# Check 6: Test file exists
if ls $WORKSPACE/src/vs/editor/contrib/folding/test/*named*region* \
      $WORKSPACE/src/vs/editor/contrib/folding/test/*region*nav* \
      $WORKSPACE/src/vs/editor/contrib/folding/browser/test/*region* 1>/dev/null 2>&1; then
    SCORE=$((SCORE + 1))
    echo "PASS: Test file for named regions exists"
elif grep -rq 'namedRegion\|NamedRegion\|goToRegion' \
    "$WORKSPACE/src/vs/editor/contrib/folding/test/" 2>/dev/null; then
    SCORE=$((SCORE + 1))
    echo "PASS: Named region tests found in existing test files"
else
    echo "FAIL: No test file for named regions found"
fi

echo ""
echo "Score: $SCORE / $TOTAL"

mkdir -p /logs/verifier
python3 -c "print($SCORE / $TOTAL)" > /logs/verifier/reward.txt
