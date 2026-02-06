#!/bin/bash
set -e

# DependEval DR Test Script
# Runs the evaluation script and writes reward to /logs/verifier/reward.txt

mkdir -p /logs/verifier

# Run evaluation
python3 /tests/eval_scripts/eval_dr.py

# Ensure we always exit 0 (Harbor requirement)
exit 0
