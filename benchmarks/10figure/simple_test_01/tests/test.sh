#!/bin/bash
set -e

# Simple test: check if marker file exists with correct content
if [ ! -f "test_marker.txt" ]; then
    echo "0.0"
    exit 0
fi

# Check if file contains exactly "MARKER_CREATED"
content=$(cat test_marker.txt)
if [ "$content" = "MARKER_CREATED" ]; then
    echo "1.0"
else
    echo "0.0"
fi
