#!/bin/bash
# Create sg-benchmarks repos for TAC tasks with pinned commits
#
# TAC task repos are cloned at runtime from TAC's private GitLab.
# This script queries the TAC GitLab API to get exact commit hashes,
# then clones the corresponding public upstream repos at those commits
# and pushes them to sg-benchmarks for Sourcegraph indexing.
#
# Prerequisites:
#   - TAC server running (GitLab at the-agent-company.com:8929)
#   - gh CLI authenticated with push access to sg-benchmarks org
#   - git configured
#
# Usage:
#   ./scripts/create_sg_tac_repos.sh [--dry-run] [--repo REPO_NAME]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORK_DIR="${WORK_DIR:-/tmp/sg-tac-repos}"
SG_ORG="sg-benchmarks"
DRY_RUN=false
ONLY_REPO=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --repo)
            ONLY_REPO="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# TAC GitLab API base
TAC_GITLAB="http://the-agent-company.com:8929"

# Verify TAC GitLab is reachable
if ! curl -sf --max-time 5 "${TAC_GITLAB}/" >/dev/null 2>&1; then
    echo "ERROR: TAC GitLab not reachable at ${TAC_GITLAB}"
    echo "Please ensure the TAC server is running."
    exit 1
fi

# Map: TAC GitLab project path -> upstream GitHub repo
declare -A UPSTREAM_MAP=(
    ["root/bustub"]="cmu-db/bustub"
    ["root/llama.cpp"]="ggerganov/llama.cpp"
    ["root/copilot-arena-server"]="lmarena/copilot-arena"
    ["root/openhands"]="All-Hands-AI/OpenHands"
)

# Map: TAC GitLab project path -> tasks that use this repo
declare -A TASK_MAP=(
    ["root/bustub"]="tac-buffer-pool-manager,tac-implement-hyperloglog"
    ["root/llama.cpp"]="tac-find-in-codebase-1,tac-find-in-codebase-2"
    ["root/copilot-arena-server"]="tac-copilot-arena-endpoint,tac-troubleshoot-dev-setup"
    ["root/openhands"]="tac-write-unit-test,tac-dependency-change"
)

echo "=============================================="
echo "Create sg-benchmarks repos for TAC tasks"
echo "=============================================="
echo "Dry run: ${DRY_RUN}"
echo ""

# Step 1: Extract commits from TAC GitLab
echo "--- Extracting commits from TAC GitLab ---"
declare -A COMMITS

for project in "${!UPSTREAM_MAP[@]}"; do
    encoded=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$project', safe=''))")
    commit=$(curl -sf "${TAC_GITLAB}/api/v4/projects/${encoded}/repository/branches/main" 2>/dev/null \
        | python3 -c "import sys,json; print(json.load(sys.stdin)['commit']['id'])" 2>/dev/null) || {
        # Try master branch if main doesn't exist
        commit=$(curl -sf "${TAC_GITLAB}/api/v4/projects/${encoded}/repository/branches/master" 2>/dev/null \
            | python3 -c "import sys,json; print(json.load(sys.stdin)['commit']['id'])" 2>/dev/null) || {
            echo "  WARNING: Could not get commit for ${project}"
            continue
        }
    }
    COMMITS[$project]="$commit"
    short="${commit:0:8}"
    upstream="${UPSTREAM_MAP[$project]}"
    repo_name=$(basename "$upstream")
    echo "  ${project} -> ${upstream} @ ${short} (${commit})"
    echo "    sg-benchmarks/${repo_name}--${short}"
    echo "    Tasks: ${TASK_MAP[$project]}"
done

echo ""

if [ ${#COMMITS[@]} -eq 0 ]; then
    echo "ERROR: No commits extracted. Is the TAC GitLab populated?"
    exit 1
fi

# Step 2: Create repos
mkdir -p "$WORK_DIR"
declare -A CLONED_SOURCES

N=0
SUCCESS=0
FAILED=0

for project in "${!COMMITS[@]}"; do
    upstream="${UPSTREAM_MAP[$project]}"
    commit="${COMMITS[$project]}"
    short="${commit:0:8}"
    repo_name=$(basename "$upstream")
    sg_name="${repo_name}--${short}"

    # Filter by --repo if specified
    if [ -n "$ONLY_REPO" ] && [ "$sg_name" != "$ONLY_REPO" ]; then
        continue
    fi

    N=$((N + 1))
    echo ""
    echo "[$N] Creating ${SG_ORG}/${sg_name}..."
    echo "  Source: ${upstream} @ ${commit}"

    if [ "$DRY_RUN" = true ]; then
        echo "  [DRY RUN] Would clone, checkout, create repo, push"
        SUCCESS=$((SUCCESS + 1))
        continue
    fi

    source_dir="${WORK_DIR}/sources/${upstream}"
    repo_dir="${WORK_DIR}/repos/${sg_name}"

    # Clone source repo (reuse if already cloned)
    if [ -z "${CLONED_SOURCES[$upstream]+_}" ]; then
        echo "  Cloning source ${upstream}..."
        mkdir -p "$(dirname "$source_dir")"
        if [ ! -d "$source_dir" ]; then
            git clone --bare "https://github.com/${upstream}.git" "$source_dir" 2>&1 || {
                echo "  ERROR: Failed to clone ${upstream}"
                FAILED=$((FAILED + 1))
                continue
            }
        fi
        CLONED_SOURCES[$upstream]=1
    fi

    # Create working copy at specific commit
    rm -rf "$repo_dir"
    mkdir -p "$repo_dir"
    git clone "$source_dir" "$repo_dir" 2>&1 || {
        echo "  ERROR: Failed to clone from bare repo"
        FAILED=$((FAILED + 1))
        continue
    }

    cd "$repo_dir"
    git checkout "$commit" 2>&1 || {
        echo "  ERROR: Commit $commit not found in ${upstream}"
        cd - > /dev/null
        FAILED=$((FAILED + 1))
        continue
    }
    git checkout --detach HEAD 2>/dev/null || true

    # Create GitHub repo
    if gh repo view "${SG_ORG}/${sg_name}" &>/dev/null; then
        echo "  Repo already exists on GitHub"
    else
        gh repo create "${SG_ORG}/${sg_name}" --public \
            --description "TAC: ${upstream} @ ${short}" 2>&1 || {
            echo "  ERROR: Failed to create repo"
            cd - > /dev/null
            FAILED=$((FAILED + 1))
            continue
        }
    fi

    # Push
    git remote remove sg-target 2>/dev/null || true
    git remote add sg-target "https://github.com/${SG_ORG}/${sg_name}.git"
    git push sg-target HEAD:refs/heads/main --force 2>&1 || {
        echo "  ERROR: Failed to push"
        cd - > /dev/null
        FAILED=$((FAILED + 1))
        continue
    }

    cd - > /dev/null
    echo "  SUCCESS: ${SG_ORG}/${sg_name}"
    SUCCESS=$((SUCCESS + 1))

    # Clean up working copy
    rm -rf "$repo_dir"
done

echo ""
echo "=============================================="
echo "Results"
echo "=============================================="
echo "Processed: $N"
echo "Succeeded: $SUCCESS"
echo "Failed: $FAILED"
echo ""

# Output the mapping for tac_3config.sh
echo "--- SG repo mappings for tac_3config.sh ---"
for project in "${!COMMITS[@]}"; do
    upstream="${UPSTREAM_MAP[$project]}"
    commit="${COMMITS[$project]}"
    short="${commit:0:8}"
    repo_name=$(basename "$upstream")
    sg_name="${repo_name}--${short}"
    tasks="${TASK_MAP[$project]}"

    IFS=',' read -ra task_list <<< "$tasks"
    for task in "${task_list[@]}"; do
        echo "    [\"${task}\"]=\"${SG_ORG}/${sg_name}\""
    done
done

echo ""
echo "Next steps:"
echo "  1. Wait for Sourcegraph to index (10-30 min)"
echo "  2. Update TASK_SG_REPO_NAMES in configs/tac_3config.sh"
echo "  3. Update configs/sg_indexing_list.json"
