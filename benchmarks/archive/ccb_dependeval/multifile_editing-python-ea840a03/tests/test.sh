#!/bin/bash
# Reward: binary (0.0-1.0) — dependency ordering correctness
set -e

# DependEval ME Test Script
# Runs the evaluation script and writes reward to /logs/verifier/reward.txt

mkdir -p /logs/verifier

# Run evaluation
python3 /tests/eval_scripts/eval_me.py

# Ensure we always exit 0 (Harbor requirement)
exit 0
