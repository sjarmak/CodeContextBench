#!/bin/bash
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SDLC_SUITE="csb_sdlc_test" SDLC_SUITE_LABEL="Test (Quality Assurance)" \
    exec "$SCRIPT_DIR/sdlc_suite_2config.sh" "$@"
