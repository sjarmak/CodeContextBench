#!/bin/bash
# Reward: checklist (0.0-1.0) — weighted documentation file and pattern checks
# Test script for apiserver-doc-001: API Server Library Documentation
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

TARGET_FILE="staging/src/k8s.io/apiserver/doc.go"
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
if echo "$DOC_CONTENT" | grep -q "^package apiserver"; then
    echo "PASS: Valid Go package declaration"
    SCORE=$((SCORE + 1))
else
    echo "FAIL: Missing or incorrect package declaration"
fi

# Check 3: References GenericAPIServer (1 point)
if context_grep "GenericAPIServer" "$DOC_CONTENT"; then
    echo "PASS: References GenericAPIServer"
    SCORE=$((SCORE + 1))
else
    echo "WARN: Does not reference GenericAPIServer"
fi

# Check 4: References admission control (1 point)
if context_grep "admission" "$DOC_CONTENT"; then
    echo "PASS: References admission control"
    SCORE=$((SCORE + 1))
else
    echo "WARN: Does not reference admission control"
fi

# Check 5: References authentication/authorization (1 point)
if context_grep "authentication\|authorization" "$DOC_CONTENT"; then
    echo "PASS: References authentication/authorization"
    SCORE=$((SCORE + 1))
else
    echo "WARN: Does not reference authentication/authorization"
fi

# Check 6: References API aggregation or extension (1 point)
if context_grep "aggregat\|extension.*api.*server\|APIService" "$DOC_CONTENT"; then
    echo "PASS: References API aggregation/extension"
    SCORE=$((SCORE + 1))
else
    echo "WARN: Does not reference API aggregation"
fi

# Check 7: References CRDs as preferred alternative (1 point)
if context_grep "CustomResource\|CRD" "$DOC_CONTENT"; then
    echo "PASS: References CRDs as preferred alternative"
    SCORE=$((SCORE + 1))
else
    echo "WARN: Does not reference CRDs"
fi

# Check 8: Sub-package references verified in workspace (1 point)
REF_COUNT=0
for subpkg in "pkg/server" "pkg/admission" "pkg/endpoints" "pkg/registry"; do
    full_path="staging/src/k8s.io/apiserver/${subpkg}"
    if echo "$DOC_CONTENT" | grep -qi "$subpkg" && [ -d "$full_path" ]; then
        REF_COUNT=$((REF_COUNT + 1))
    fi
done
if [ "$REF_COUNT" -ge 3 ]; then
    echo "PASS: References $REF_COUNT sub-packages (verified in workspace)"
    SCORE=$((SCORE + 1))
else
    echo "WARN: Only $REF_COUNT verified sub-package references"
fi

# Convert to decimal score
FINAL_SCORE=$(awk "BEGIN {printf \"%.1f\", $SCORE / $MAX_SCORE}")

echo "$FINAL_SCORE" > /logs/verifier/reward.txt
echo ""
echo "Tests completed - Score: $FINAL_SCORE (${SCORE}/${MAX_SCORE} checks passed)"
