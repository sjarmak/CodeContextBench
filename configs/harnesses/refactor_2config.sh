#!/bin/bash
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SDLC_SUITE="csb_sdlc_refactor" SDLC_SUITE_LABEL="Cross-File Refactoring" \
    exec "$SCRIPT_DIR/sdlc_suite_2config.sh" "$@"
