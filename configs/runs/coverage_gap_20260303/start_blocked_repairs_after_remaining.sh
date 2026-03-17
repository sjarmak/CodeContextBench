#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

LOG_DIR="$ROOT_DIR/logs/flagged_reruns_20260303"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/blocked_repairs_nohup.out"

TARGET='configs/coverage_gap_20260303/run_daytona_remaining_and_unmapped.sh'

echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] waiting for remaining/unmapped wave chain to finish..." | tee -a "$LOG_FILE"
while pgrep -af "$TARGET" >/dev/null; do
  sleep 30
done

echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] remaining/unmapped chain finished, starting blocked repairs..." | tee -a "$LOG_FILE"
exec "$ROOT_DIR/configs/coverage_gap_20260303/run_daytona_blocked_repairs.sh" >> "$LOG_FILE" 2>&1
