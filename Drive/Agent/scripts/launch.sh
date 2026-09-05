#!/bin/bash
set -e

DRIVE_ROOT=$(cd "$(dirname "$0")/.." && pwd)

echo "=== STARTING AGENT LAUNCH SEQUENCE ==="
"$DRIVE_ROOT/scripts/bootstrap.sh"

echo "=== CHECKING FOR INTERRUPTED SESSIONS ==="
LAST_SESSION=$("$DRIVE_ROOT/bin/agent" status | grep "Status" | grep -v "SUCCESS" | grep -v "MAX_ITERATIONS" || true)

if [[ ! -z "$LAST_SESSION" ]]; then
    echo "================================================"
    echo "          INTERRUPTED SESSION FOUND             "
    echo "================================================"
    "$DRIVE_ROOT/bin/agent" status
    echo "------------------------------------------------"
    echo "Do you want to RESUME this session? (y/N)"
    read -r response </dev/tty || response="y"
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        export AGENT_WORKSPACE="/content/workspace"
        "$DRIVE_ROOT/bin/agent" resume
        exit 0
    fi
    echo "Starting fresh session."
fi

echo "Ready. Use 'agent start <task>' to begin."
