#!/bin/bash
# Reward: checklist (0.0-1.0) — weighted documentation file and pattern checks
# Test script for fairqueuing-doc-001: Fair Queuing QueueSet Package Documentation
# Signal 1: File-reference validation (harbor reward)

set -e

cd /workspace

# Create log directories
mkdir -p /logs/verifier

# Fix git safe.directory
git config --global --add safe.directory /workspace 2>/dev/null || true

# Guard: if no code changes were made, the agent didn't execute successfully
UNSTAGED_COUNT=$(git diff --stat 2>/dev/null | wc -l)
STAGED_COUNT=$(git diff --cached --stat 2>/dev/null | wc -l)
UNTRACKED_COUNT=$(git ls-files --others --exclude-standard 2>/dev/null | wc -l)
COMMIT_COUNT=0
ORIGIN_REF=""
for ref in origin/master origin/main origin/HEAD; do
    if git rev-parse "$ref" >/dev/null 2>&1; then
        ORIGIN_REF="$ref"
        break
    fi
done
if [ -n "$ORIGIN_REF" ]; then
    COMMIT_COUNT=$(git log --oneline "$ORIGIN_REF..HEAD" 2>/dev/null | wc -l)
elif git rev-parse FETCH_HEAD >/dev/null 2>&1; then
    COMMIT_COUNT=$(git log --oneline FETCH_HEAD..HEAD 2>/dev/null | wc -l)
else
    TOTAL_COMMITS=$(git log --oneline 2>/dev/null | wc -l)
    if [ "$TOTAL_COMMITS" -gt 1 ]; then
        COMMIT_COUNT=$((TOTAL_COMMITS - 1))
    fi
fi
echo "Change detection: unstaged=$UNSTAGED_COUNT staged=$STAGED_COUNT untracked=$UNTRACKED_COUNT commits=$COMMIT_COUNT"
if [ "$UNSTAGED_COUNT" -eq 0 ] && [ "$STAGED_COUNT" -eq 0 ] && [ "$UNTRACKED_COUNT" -eq 0 ] && [ "$COMMIT_COUNT" -eq 0 ]; then
    echo "No code changes detected - agent did not execute successfully"
    echo "0.0" > /logs/verifier/reward.txt
    echo ""
    echo "Tests completed - Score: 0.0 (no changes)"
    exit 0
fi

# Context-aware keyword check: matches keyword only in non-negated context
# Finds lines containing the pattern, then excludes lines where it appears
# after "not ", "no ", "isn't ", or "doesn't " — preventing false positives
# from sentences like "X is not relevant" still matching on "X"
# Usage: context_grep "pattern" "$CONTENT"
context_grep() {
    local pattern="$1"
    local content="$2"
    echo "$content" | grep -i "$pattern" | grep -ivq "not .*\($pattern\)\|no .*\($pattern\)\|isn't .*\($pattern\)\|doesn't .*\($pattern\)"
}

TARGET_FILE="staging/src/k8s.io/apiserver/pkg/util/flowcontrol/fairqueuing/queueset/doc.go"
echo "Evaluating ${TARGET_FILE}..."

SCORE=0
MAX_SCORE=10

# Check 1: File exists (1 point)
if [ -f "$TARGET_FILE" ]; then
    echo "PASS: ${TARGET_FILE} exists"
    SCORE=$((SCORE + 1))
else
    echo "FAIL: ${TARGET_FILE} not found"
    echo "0.0" > /logs/verifier/reward.txt
    echo ""
    echo "Tests completed - Score: 0.0 (file not created)"
    exit 0
fi

DOC_CONTENT=$(cat "$TARGET_FILE")

# Check 1b: Minimum content length gate (1 point)
# Count words excluding the package declaration line
WORD_COUNT=$(echo "$DOC_CONTENT" | grep -v '^package ' | wc -w)
if [ "$WORD_COUNT" -ge 50 ]; then
    echo "PASS: Document has $WORD_COUNT words of content (>= 50 minimum)"
    SCORE=$((SCORE + 1))
else
    echo "FAIL: Document has only $WORD_COUNT words of content (< 50 minimum)"
    echo "0.1" > /logs/verifier/reward.txt
    echo ""
    echo "Tests completed - Score: 0.1 (file exists but insufficient content)"
    exit 0
fi

# Check 2: Valid Go package declaration (1 point)
if echo "$DOC_CONTENT" | grep -q "^package queueset"; then
    echo "PASS: Valid Go package declaration"
    SCORE=$((SCORE + 1))
else
    echo "FAIL: Missing or incorrect package declaration"
fi

# Check 3: Mentions fair queuing (1 point)
if context_grep "fair queuing\|fair queueing" "$DOC_CONTENT"; then
    echo "PASS: References fair queuing"
    SCORE=$((SCORE + 1))
else
    echo "WARN: Does not reference fair queuing"
fi

# Check 4: Mentions virtual time (1 point)
if context_grep "virtual time\|R(t)" "$DOC_CONTENT"; then
    echo "PASS: References virtual time / R(t)"
    SCORE=$((SCORE + 1))
else
    echo "WARN: Does not reference virtual time"
fi

# Check 5: Mentions concurrency limit (1 point)
if context_grep "concurrency\|concurrent" "$DOC_CONTENT"; then
    echo "PASS: References concurrency"
    SCORE=$((SCORE + 1))
else
    echo "WARN: Does not reference concurrency"
fi

# Check 6: Mentions service time or duration (1 point)
if context_grep "service time\|duration\|execution time" "$DOC_CONTENT"; then
    echo "PASS: References service time"
    SCORE=$((SCORE + 1))
else
    echo "WARN: Does not reference service time"
fi

# Check 7: Mentions queue management concepts (1 point)
if context_grep "dispatch\|dequeue\|enqueue\|queue.*set\|QueueSet" "$DOC_CONTENT"; then
    echo "PASS: References queue management"
    SCORE=$((SCORE + 1))
else
    echo "WARN: Does not reference queue management"
fi

# Check 8: References networking origins or papers (1 point)
if context_grep "network\|packet\|WFQ\|weighted fair\|paper\|acm.org\|wikipedia" "$DOC_CONTENT"; then
    echo "PASS: References networking origins"
    SCORE=$((SCORE + 1))
else
    echo "WARN: Does not reference networking origins"
fi

# Convert to decimal score
FINAL_SCORE=$(awk "BEGIN {printf \"%.1f\", $SCORE / $MAX_SCORE}")

echo "$FINAL_SCORE" > /logs/verifier/reward.txt
echo ""
echo "Tests completed - Score: $FINAL_SCORE (${SCORE}/${MAX_SCORE} checks passed)"
