#!/bin/bash
# Stop and clean up a specific task or all tasks matching a pattern
#
# Usage:
#   ./scripts/stop_task.sh sgt-001          # Stop specific task
#   ./scripts/stop_task.sh sgt-             # Stop all sgt-* tasks  
#   ./scripts/stop_task.sh --all            # Stop all harbor tasks
#   ./scripts/stop_task.sh --list           # Just list running tasks

set -e

PATTERN="${1:-}"

if [[ -z "$PATTERN" ]]; then
    echo "Usage: $0 <task-pattern|--all|--list>"
    echo ""
    echo "Examples:"
    echo "  $0 sgt-001        # Stop task sgt-001"
    echo "  $0 sgt-           # Stop all sgt-* tasks"
    echo "  $0 --all          # Stop all harbor tasks"
    echo "  $0 --list         # List running tasks"
    exit 1
fi

if [[ "$PATTERN" == "--list" ]]; then
    echo "=== Running Harbor Processes ==="
    ps aux | grep "harbor run" | grep -v grep | awk '{print $2, $NF}' || echo "  (none)"
    echo ""
    echo "=== Running Docker Containers ==="
    docker ps --format 'table {{.Names}}\t{{.Status}}' | grep -E "^(NAMES|.*__(main|verifier))" || echo "  (none)"
    exit 0
fi

echo "=== Stopping tasks matching: $PATTERN ==="

# Kill harbor processes
if [[ "$PATTERN" == "--all" ]]; then
    PIDS=$(ps aux | grep "harbor run" | grep -v grep | awk '{print $2}')
else
    PIDS=$(ps aux | grep "harbor run.*$PATTERN" | grep -v grep | awk '{print $2}')
fi

if [[ -n "$PIDS" ]]; then
    echo "Killing PIDs: $PIDS"
    echo "$PIDS" | xargs -r kill 2>/dev/null || true
    sleep 1
    echo "$PIDS" | xargs -r kill -9 2>/dev/null || true
else
    echo "No matching harbor processes found"
fi

# Stop and remove Docker containers
if [[ "$PATTERN" == "--all" ]]; then
    CONTAINERS=$(docker ps -a --format '{{.Names}}' | grep -E "__" || true)
else
    CONTAINERS=$(docker ps -a --format '{{.Names}}' | grep -i "$PATTERN" || true)
fi

if [[ -n "$CONTAINERS" ]]; then
    echo "Stopping containers: $(echo $CONTAINERS | tr '\n' ' ')"
    echo "$CONTAINERS" | xargs -r docker stop 2>/dev/null || true
    echo "$CONTAINERS" | xargs -r docker rm 2>/dev/null || true
else
    echo "No matching containers found"
fi

echo "Done."
