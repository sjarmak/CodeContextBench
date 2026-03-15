#!/bin/bash
set -e
cd "$(dirname "$0")"

source .env.local

export CSB_SKIP_CONFIRM=1

# Override GITHUB_TOKEN with gh OAuth token (has access to sourcegraph/sourcegraph).
# .env.local may set a ghp_ PAT that lacks access to this private repo.
export GITHUB_TOKEN=$(grep 'oauth_token:' ~/.config/gh/hosts.yml 2>/dev/null | awk '{print $2}')
if [ -z "${GITHUB_TOKEN:-}" ]; then
    export GITHUB_TOKEN=$(gh auth status -t 2>&1 | grep -oP 'Token: \K\S+')
fi

if [ -z "${GITHUB_TOKEN:-}" ]; then
    echo "ERROR: Could not extract GITHUB_TOKEN. Set it in the environment before running."
    exit 1
fi
echo "GITHUB_TOKEN: ${#GITHUB_TOKEN} chars (prefix: ${GITHUB_TOKEN:0:4})"

exec bash configs/sourcegraph_2config.sh --model anthropic/claude-sonnet-4-6 "$@"
