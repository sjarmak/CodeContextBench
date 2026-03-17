#!/bin/bash
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SDLC_SUITE="csb_sdlc_secure" SDLC_SUITE_LABEL="Secure (Security & Compliance)" \
    exec "$SCRIPT_DIR/sdlc_suite_2config.sh" "$@"
