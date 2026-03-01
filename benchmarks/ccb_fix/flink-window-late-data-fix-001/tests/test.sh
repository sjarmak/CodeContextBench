#!/bin/bash
set -euo pipefail

[ -f /tmp/.sg_only_mode ] && [ -f /tests/sgonly_verifier_wrapper.sh ] && source /tests/sgonly_verifier_wrapper.sh

SCORE=0
TOTAL=6
WORKSPACE="${VERIFY_REPO:-/workspace}"

WINDOW_OP_DIR="$WORKSPACE/flink-streaming-java/src/main/java/org/apache/flink/streaming/runtime/operators/windowing"
WINDOW_TEST_DIR="$WORKSPACE/flink-streaming-java/src/test/java/org/apache/flink/streaming/runtime/operators/windowing"

# Check 1: WindowOperator.processElement modified (late element handling)
if grep -q 'isElementLate\|lateElement\|sideOutputLateData\|late.*data' \
    "$WINDOW_OP_DIR/WindowOperator.java" 2>/dev/null; then
    # Check for modification: look for changes near the late element handling
    if git -C "$WORKSPACE" diff HEAD -- "$(realpath --relative-to="$WORKSPACE" "$WINDOW_OP_DIR/WindowOperator.java")" 2>/dev/null | grep -q '+.*late\|+.*merge\|+.*sideOutput\|+.*OutputTag'; then
        SCORE=$((SCORE + 1))
        echo "PASS: WindowOperator.processElement modified for late data handling"
    elif grep -q 'merge.*late\|late.*merge\|sideOutput.*late\|lateOutputTag' \
        "$WINDOW_OP_DIR/WindowOperator.java" 2>/dev/null; then
        SCORE=$((SCORE + 1))
        echo "PASS: WindowOperator has late data + merge handling"
    else
        echo "FAIL: WindowOperator found but no late data fix detected"
    fi
else
    echo "FAIL: WindowOperator.processElement not found or missing late data handling"
fi

# Check 2: Late element check reordered or merge-aware
if grep -rq 'merge.*before.*late\|late.*after.*merge\|mergingWindows.*isElementLate\|!isElementLate\|isCleanupTime' \
    "$WINDOW_OP_DIR/WindowOperator.java" 2>/dev/null; then
    SCORE=$((SCORE + 1))
    echo "PASS: Late element check interacts with merge logic"
else
    echo "FAIL: No merge-aware late element check found"
fi

# Check 3: OutputTag correctly wired for side output
if grep -rq 'OutputTag\|lateDataOutputTag\|sideOutput.*late\|output.*tag.*late' \
    "$WINDOW_OP_DIR/WindowOperator.java" 2>/dev/null; then
    SCORE=$((SCORE + 1))
    echo "PASS: OutputTag wiring for late data side output exists"
else
    echo "FAIL: OutputTag wiring for late data not found"
fi

# Check 4: Side output emission in late path
if grep -rq 'sideOutput\|collect.*outputTag\|output\.collect.*Tag' \
    "$WINDOW_OP_DIR/WindowOperator.java" 2>/dev/null; then
    SCORE=$((SCORE + 1))
    echo "PASS: Side output emission in late element path"
else
    echo "FAIL: No side output emission found in window operator"
fi

# Check 5: Test case for late data with session/merging windows
if grep -rq 'sideOutputLateData\|lateData.*session\|session.*late\|merging.*late.*output\|OutputTag.*late' \
    "$WINDOW_TEST_DIR/" 2>/dev/null; then
    if git -C "$WORKSPACE" diff HEAD -- \
        "$(realpath --relative-to="$WORKSPACE" "$WINDOW_TEST_DIR")" 2>/dev/null | grep -q '+.*late\|+.*sideOutput\|+.*session'; then
        SCORE=$((SCORE + 1))
        echo "PASS: New test case for late data with session windows"
    elif grep -cq 'lateData.*Merging\|session.*late.*side\|testLateSideOutput' \
        "$WINDOW_TEST_DIR/"*.java 2>/dev/null; then
        SCORE=$((SCORE + 1))
        echo "PASS: Test case for merging window late data exists"
    else
        echo "FAIL: Late data tests found but no new session/merge-specific test"
    fi
else
    echo "FAIL: No test case for late data side output found"
fi

# Check 6: Solution documentation
if [ -f /logs/agent/solution.md ] || [ -f /logs/agent/analysis.md ]; then
    if grep -rq 'root.cause\|late.*data\|side.*output\|merging' /logs/agent/ 2>/dev/null; then
        SCORE=$((SCORE + 1))
        echo "PASS: Solution documentation with root cause analysis"
    else
        echo "FAIL: Solution file exists but lacks root cause details"
    fi
else
    # Also accept if the code changes are clear enough
    if git -C "$WORKSPACE" diff HEAD 2>/dev/null | wc -l | grep -qv '^0$'; then
        SCORE=$((SCORE + 1))
        echo "PASS: Code changes present (implicit fix documentation)"
    else
        echo "FAIL: No solution documentation or code changes found"
    fi
fi

echo ""
echo "Score: $SCORE / $TOTAL"

mkdir -p /logs/verifier
python3 -c "print($SCORE / $TOTAL)" > /logs/verifier/reward.txt
