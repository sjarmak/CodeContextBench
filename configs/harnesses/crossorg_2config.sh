#!/bin/bash
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SDLC_SUITE="csb_org_crossorg" SDLC_SUITE_LABEL="Org Cross-Org" \
    exec "$SCRIPT_DIR/sdlc_suite_2config.sh" "$@"
