#!/usr/bin/env bash
# Create scip-enabled branches on all sg-evals repos.
# Each branch points to the same commit as the repo's default branch HEAD.
#
# Usage:
#   ./scripts/create_scip_branches.sh [--dry-run] [--parallel N]
#
# Requires: gh CLI authenticated with access to sg-evals org.

set -euo pipefail

DRY_RUN=false
PARALLEL=10
LOG_DIR="/tmp/scip_branch_creation"
BRANCH_NAME="scip-enabled"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)  DRY_RUN=true; shift ;;
    --parallel) PARALLEL="$2"; shift 2 ;;
    *)          echo "Unknown arg: $1"; exit 1 ;;
  esac
done

mkdir -p "$LOG_DIR"
SUCCESS_LOG="$LOG_DIR/success.log"
SKIP_LOG="$LOG_DIR/skip.log"
FAIL_LOG="$LOG_DIR/fail.log"
> "$SUCCESS_LOG"
> "$SKIP_LOG"
> "$FAIL_LOG"

echo "=== SCIP Branch Creator ==="
echo "Branch: $BRANCH_NAME"
echo "Parallel: $PARALLEL"
echo "Dry run: $DRY_RUN"
echo "Logs: $LOG_DIR/"
echo ""

# Fetch all repo names in the org
echo "Fetching repo list from sg-evals org..."
REPOS=$(gh api --paginate orgs/sg-evals/repos \
  --jq '.[].name' 2>/dev/null | sort)
TOTAL=$(echo "$REPOS" | wc -l)
echo "Found $TOTAL repos"
echo ""

create_branch() {
  local repo_name="$1"
  local full_name="sg-evals/$repo_name"

  # Get default branch HEAD SHA
  local sha
  sha=$(gh api "repos/$full_name/git/refs/heads/main" --jq '.object.sha' 2>/dev/null || true)

  # If main doesn't exist, try the default branch
  if [[ -z "$sha" ]]; then
    local default_branch
    default_branch=$(gh api "repos/$full_name" --jq '.default_branch' 2>/dev/null || true)
    if [[ -n "$default_branch" && "$default_branch" != "main" ]]; then
      sha=$(gh api "repos/$full_name/git/refs/heads/$default_branch" --jq '.object.sha' 2>/dev/null || true)
    fi
  fi

  if [[ -z "$sha" ]]; then
    echo "SKIP $repo_name: empty repo or no resolvable HEAD" >> "$SKIP_LOG"
    return 0
  fi

  # Check if branch already exists
  local existing
  existing=$(gh api "repos/$full_name/git/refs/heads/$BRANCH_NAME" --jq '.object.sha' 2>/dev/null || true)
  if [[ -n "$existing" ]]; then
    echo "SKIP $repo_name: $BRANCH_NAME already exists (sha=$existing)" >> "$SKIP_LOG"
    return 0
  fi

  if $DRY_RUN; then
    echo "DRY-RUN: would create $BRANCH_NAME on $full_name at $sha"
    echo "DRYRUN $repo_name: $sha" >> "$SUCCESS_LOG"
    return 0
  fi

  # Create the branch
  local result
  result=$(gh api "repos/$full_name/git/refs" \
    -f "ref=refs/heads/$BRANCH_NAME" \
    -f "sha=$sha" 2>&1) || {
    echo "FAIL $repo_name: $result" >> "$FAIL_LOG"
    return 1
  }

  echo "OK $repo_name: created $BRANCH_NAME at $sha" >> "$SUCCESS_LOG"
}

export -f create_branch
export DRY_RUN BRANCH_NAME SUCCESS_LOG SKIP_LOG FAIL_LOG

# Run in parallel with progress
echo "$REPOS" | xargs -P "$PARALLEL" -I {} bash -c 'create_branch "$@"' _ {}

echo ""
echo "=== Results ==="
echo "Success: $(wc -l < "$SUCCESS_LOG")"
echo "Skipped: $(wc -l < "$SKIP_LOG")"
echo "Failed:  $(wc -l < "$FAIL_LOG")"

if [[ -s "$FAIL_LOG" ]]; then
  echo ""
  echo "=== Failures ==="
  cat "$FAIL_LOG"
fi

echo ""
echo "Full logs in $LOG_DIR/"
