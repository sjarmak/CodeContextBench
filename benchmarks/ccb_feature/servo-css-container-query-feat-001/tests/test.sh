#!/bin/bash
set -euo pipefail

[ -f /tmp/.sg_only_mode ] && [ -f /tests/sgonly_verifier_wrapper.sh ] && source /tests/sgonly_verifier_wrapper.sh

SCORE=0
TOTAL=6
WORKSPACE="${VERIFY_REPO:-/workspace}"

# Check 1: container-type property defined
if grep -rq 'container.type\|container_type\|ContainerType' \
    "$WORKSPACE/components/style/properties/" 2>/dev/null; then
    SCORE=$((SCORE + 1))
    echo "PASS: container-type property defined"
else
    echo "FAIL: container-type property not found in style properties"
fi

# Check 2: container-name property defined
if grep -rq 'container.name\|container_name\|ContainerName' \
    "$WORKSPACE/components/style/properties/" 2>/dev/null; then
    SCORE=$((SCORE + 1))
    echo "PASS: container-name property defined"
else
    echo "FAIL: container-name property not found in style properties"
fi

# Check 3: Container query condition types defined
if grep -rq 'ContainerCondition\|ContainerQuery\|ContainerSizeQuery\|container_condition' \
    "$WORKSPACE/components/style/" 2>/dev/null; then
    SCORE=$((SCORE + 1))
    echo "PASS: Container query condition types defined"
else
    echo "FAIL: Container query condition types not found"
fi

# Check 4: @container at-rule parsing
if grep -rq '@container\|AtRuleContainer\|CssRuleType.*Container\|container_rule' \
    "$WORKSPACE/components/style/stylesheets/" 2>/dev/null; then
    SCORE=$((SCORE + 1))
    echo "PASS: @container at-rule parsing exists"
else
    echo "FAIL: @container at-rule parsing not found"
fi

# Check 5: Size query evaluation logic
if grep -rq 'min.width\|max.width\|evaluate.*container\|container.*size\|query.*dimension' \
    "$WORKSPACE/components/style/" 2>/dev/null; then
    # Verify it's new container query code, not just existing media query code
    if grep -rq 'container.*evaluat\|evaluat.*container\|ContainerSizeFeature\|container.*query.*match' \
        "$WORKSPACE/components/style/" 2>/dev/null; then
        SCORE=$((SCORE + 1))
        echo "PASS: Container size query evaluation logic exists"
    else
        echo "FAIL: Size query logic found but no container-specific evaluation"
    fi
else
    echo "FAIL: No size query evaluation logic found"
fi

# Check 6: Integration with style matching
if grep -rq 'container.*match\|match.*container\|container.*cascade\|container.*rule.*apply' \
    "$WORKSPACE/components/style/matching.rs" \
    "$WORKSPACE/components/style/stylist.rs" \
    "$WORKSPACE/components/style/rule_tree/" 2>/dev/null; then
    SCORE=$((SCORE + 1))
    echo "PASS: Container query integrated with style matching"
else
    echo "FAIL: No container query integration in style matching"
fi

echo ""
echo "Score: $SCORE / $TOTAL"

mkdir -p /logs/verifier
python3 -c "print($SCORE / $TOTAL)" > /logs/verifier/reward.txt
