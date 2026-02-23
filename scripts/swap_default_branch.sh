#!/usr/bin/env bash
# Swap the default branch for all sg-evals repos.
#
# Deep Search only indexes HEAD (the default branch). To compare SCIP-enabled
# vs control (no SCIP), swap which branch is default before running benchmarks:
#
#   ./scripts/swap_default_branch.sh scip-enabled   # for SCIP runs
#   ./scripts/swap_default_branch.sh main            # for control runs (restore)
#
# Usage:
#   ./scripts/swap_default_branch.sh <branch> [--dry-run] [--parallel N]
#
# Requires: gh CLI authenticated with write access to sg-evals org.

set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <branch> [--dry-run] [--parallel N]"
  echo ""
  echo "  branch: 'main' or 'scip-enabled'"
  echo ""
  echo "Examples:"
  echo "  $0 scip-enabled          # Set scip-enabled as default (SCIP ablation)"
  echo "  $0 main                  # Restore main as default (control)"
  exit 1
fi

TARGET_BRANCH="$1"
shift

DRY_RUN=false
PARALLEL=10
LOG_DIR="/tmp/scip_branch_swap"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)  DRY_RUN=true; shift ;;
    --parallel) PARALLEL="$2"; shift 2 ;;
    *)          echo "Unknown arg: $1"; exit 1 ;;
  esac
done

if [[ "$TARGET_BRANCH" != "main" && "$TARGET_BRANCH" != "scip-enabled" ]]; then
  echo "ERROR: branch must be 'main' or 'scip-enabled', got '$TARGET_BRANCH'"
  exit 1
fi

mkdir -p "$LOG_DIR"
SUCCESS_LOG="$LOG_DIR/success.log"
SKIP_LOG="$LOG_DIR/skip.log"
FAIL_LOG="$LOG_DIR/fail.log"
> "$SUCCESS_LOG"
> "$SKIP_LOG"
> "$FAIL_LOG"

echo "=== Default Branch Swapper ==="
echo "Target default: $TARGET_BRANCH"
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

swap_branch() {
  local repo_name="$1"
  local full_name="sg-evals/$repo_name"

  # Get current default branch
  local current_default
  current_default=$(gh api "repos/$full_name" --jq '.default_branch' 2>/dev/null || true)

  if [[ -z "$current_default" ]]; then
    echo "SKIP $repo_name: could not read repo metadata (empty?)" >> "$SKIP_LOG"
    return 0
  fi

  # Already set correctly
  if [[ "$current_default" == "$TARGET_BRANCH" ]]; then
    echo "SKIP $repo_name: already defaults to $TARGET_BRANCH" >> "$SKIP_LOG"
    return 0
  fi

  # Verify target branch exists
  local target_sha
  target_sha=$(gh api "repos/$full_name/git/refs/heads/$TARGET_BRANCH" --jq '.object.sha' 2>/dev/null || true)
  if [[ -z "$target_sha" ]]; then
    echo "SKIP $repo_name: branch $TARGET_BRANCH does not exist" >> "$SKIP_LOG"
    return 0
  fi

  if $DRY_RUN; then
    echo "DRY-RUN: $repo_name: $current_default -> $TARGET_BRANCH"
    echo "DRYRUN $repo_name: $current_default -> $TARGET_BRANCH" >> "$SUCCESS_LOG"
    return 0
  fi

  # Swap the default branch
  local result
  result=$(gh api "repos/$full_name" \
    -X PATCH \
    -f "default_branch=$TARGET_BRANCH" \
    --jq '.default_branch' 2>&1) || {
    echo "FAIL $repo_name: $result" >> "$FAIL_LOG"
    return 1
  }

  if [[ "$result" == "$TARGET_BRANCH" ]]; then
    echo "OK $repo_name: $current_default -> $TARGET_BRANCH" >> "$SUCCESS_LOG"
  else
    echo "FAIL $repo_name: expected $TARGET_BRANCH but got $result" >> "$FAIL_LOG"
  fi
}

export -f swap_branch
export DRY_RUN TARGET_BRANCH SUCCESS_LOG SKIP_LOG FAIL_LOG

# Run in parallel
echo "$REPOS" | xargs -P "$PARALLEL" -I {} bash -c 'swap_branch "$@"' _ {}

echo ""
echo "=== Results ==="
echo "Swapped: $(wc -l < "$SUCCESS_LOG")"
echo "Skipped: $(wc -l < "$SKIP_LOG")"
echo "Failed:  $(wc -l < "$FAIL_LOG")"

if [[ -s "$FAIL_LOG" ]]; then
  echo ""
  echo "=== Failures ==="
  cat "$FAIL_LOG"
fi

echo ""
echo "Full logs in $LOG_DIR/"
echo ""
echo "NOTE: Sourcegraph will re-index the new default branch HEAD."
echo "Allow time for indexing to complete before running benchmarks."
