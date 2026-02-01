#!/bin/bash
# Load CodeContextBench environment variables from .env.local
#
# Usage:
#   source infrastructure/load-env.sh
#   # or
#   . infrastructure/load-env.sh
#
# This script:
# 1. Checks if .env.local exists
# 2. Sources .env.local into current shell
# 3. Validates required variables are set
# 4. Provides helpful error messages if missing

# Get the directory where this script is located
# Handle both 'source' and direct execution
if [ -n "${BASH_SOURCE[0]}" ]; then
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
else
    SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
fi

REPO_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_LOCAL="$REPO_ROOT/.env.local"
ENV_EXAMPLE="$REPO_ROOT/.env.local.example"

# Helper function for colored output
_info() { echo "ℹ️  $*" >&2; }
_error() { echo "❌ $*" >&2; }
_success() { echo "✅ $*" >&2; }

# Check if .env.local exists
if [ ! -f "$ENV_LOCAL" ]; then
    _error "Missing .env.local file"
    echo "" >&2
    _info "Create .env.local from the example:"
    echo "  cp .env.local.example .env.local" >&2
    echo "" >&2
    _info "Then edit and fill in your credentials:"
    echo "  ANTHROPIC_API_KEY=sk-ant-..." >&2
    echo "  SRC_ACCESS_TOKEN=sgp_..." >&2
    return 1 2>/dev/null || exit 1
fi

# Load environment variables
_info "Loading environment from $ENV_LOCAL"
set -a  # Export all variables
source "$ENV_LOCAL"
set +a

# Validate required variables
MISSING_VARS=()

if [ -z "$ANTHROPIC_API_KEY" ]; then
    MISSING_VARS+=("ANTHROPIC_API_KEY")
fi

# SRC_ACCESS_TOKEN is only required for Claude+MCP agent
# (Claude baseline can run without it)

if [ ${#MISSING_VARS[@]} -gt 0 ]; then
    _error "Missing required environment variables:"
    printf "  - %s\n" "${MISSING_VARS[@]}" >&2
    echo "" >&2
    _info "Edit .env.local and fill in the values:"
    for var in "${MISSING_VARS[@]}"; do
        echo "  $var=..." >&2
    done
    return 1 2>/dev/null || exit 1
fi

# Validate optional variables have reasonable defaults
: "${SOURCEGRAPH_URL:=https://sourcegraph.sourcegraph.com}"
: "${HARBOR_10FIGURE:=/10figure}"
: "${CONTAINER_RUNTIME:=podman}"

# Export for subshells
export ANTHROPIC_API_KEY
export SRC_ACCESS_TOKEN
export SOURCEGRAPH_URL
export HARBOR_10FIGURE
export CONTAINER_RUNTIME

# Print loaded configuration (masking sensitive values)
_success "Environment loaded successfully"
echo "" >&2
_info "Configuration:"
echo "  ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY:0:4}...${ANTHROPIC_API_KEY: -4}" >&2
[ -n "$SRC_ACCESS_TOKEN" ] && echo "  SRC_ACCESS_TOKEN: ${SRC_ACCESS_TOKEN:0:4}...${SRC_ACCESS_TOKEN: -4}" >&2 || echo "  SRC_ACCESS_TOKEN: (not set)" >&2
echo "  SOURCEGRAPH_URL: $SOURCEGRAPH_URL" >&2
echo "  HARBOR_10FIGURE: $HARBOR_10FIGURE" >&2
echo "  CONTAINER_RUNTIME: $CONTAINER_RUNTIME" >&2
