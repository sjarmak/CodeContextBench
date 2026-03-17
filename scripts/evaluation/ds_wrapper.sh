#!/bin/bash
# ds_wrapper.sh — Deep Search wrapper for context_retrieval_agent.py
# Starts a Sourcegraph Deep Search query, polls until complete, returns the answer.
#
# Usage: ds_wrapper.sh "What files implement X in repo Y?"
# Requires: SRC_ACCESS_TOKEN env var
#
# Returns the Deep Search answer text on stdout.
# Timeout: 120s (configurable via DS_TIMEOUT_SEC).

set -e

SOURCEGRAPH_URL="${SOURCEGRAPH_URL:-https://sourcegraph.sourcegraph.com}"
DS_TIMEOUT_SEC="${DS_TIMEOUT_SEC:-120}"
POLL_INTERVAL=5

[ -z "$SRC_ACCESS_TOKEN" ] && echo "Error: SRC_ACCESS_TOKEN required" >&2 && exit 1
[ -z "$1" ] && echo "Usage: ds_wrapper.sh \"<question>\"" >&2 && exit 1

QUESTION="$1"

# Start deep search
RESPONSE=$(curl -s -X POST \
  -H "Authorization: token $SRC_ACCESS_TOKEN" \
  -H "X-Requested-With: ds-cli 1.0.0" \
  -H "Content-Type: application/json" \
  -d "{\"question\": $(echo "$QUESTION" | jq -R .)}" \
  "${SOURCEGRAPH_URL}/.api/deepsearch/v1")

CONV_ID=$(echo "$RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('id',''))" 2>/dev/null)

if [ -z "$CONV_ID" ]; then
  echo "Error: Failed to start Deep Search" >&2
  echo "$RESPONSE" >&2
  exit 1
fi

# Poll for completion
ELAPSED=0
while [ "$ELAPSED" -lt "$DS_TIMEOUT_SEC" ]; do
  sleep "$POLL_INTERVAL"
  ELAPSED=$((ELAPSED + POLL_INTERVAL))

  RESULT=$(curl -s -X GET \
    -H "Authorization: token $SRC_ACCESS_TOKEN" \
    -H "X-Requested-With: ds-cli 1.0.0" \
    "${SOURCEGRAPH_URL}/.api/deepsearch/v1/${CONV_ID}")

  STATUS=$(echo "$RESULT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
qs = d.get('questions', [])
print(qs[-1].get('status', 'unknown') if qs else 'no_questions')
" 2>/dev/null)

  if [ "$STATUS" = "completed" ] || [ "$STATUS" = "done" ]; then
    # Extract answer text
    echo "$RESULT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
qs = d.get('questions', [])
if qs:
    q = qs[-1]
    answer = q.get('answer', q.get('response', ''))
    if isinstance(answer, dict):
        print(json.dumps(answer, indent=2))
    else:
        print(str(answer))
" 2>/dev/null
    exit 0
  fi

  if [ "$STATUS" = "failed" ] || [ "$STATUS" = "error" ]; then
    echo "Deep Search failed" >&2
    echo "$RESULT" | python3 -m json.tool 2>/dev/null >&2
    exit 1
  fi
done

echo "Deep Search timed out after ${DS_TIMEOUT_SEC}s (status: $STATUS)" >&2
exit 1
