#!/usr/bin/env bash
# run_forever.sh — moltbot-live
# Wraps main moltbot process with infinite restart + exponential backoff.
# Resolves: moltbot-live#1 Phase 3
#
# Usage: bash run_forever.sh
# Set MOLTBOT_CMD to override the command (default: python main.py)

MOLTBOT_CMD="${MOLTBOT_CMD:-python main.py}"
MAX_BACKOFF="${MAX_BACKOFF:-300}"
LOG_DIR="logs"
RESTART_LOG="$LOG_DIR/restarts.jsonl"

mkdir -p "$LOG_DIR"

crash_count=0

while true; do
    echo "[run_forever] Starting: $MOLTBOT_CMD (run #$((crash_count+1)))"
    $MOLTBOT_CMD
    EXIT_CODE=$?

    if [ $EXIT_CODE -eq 0 ]; then
        crash_count=0
        echo "[run_forever] Exited cleanly. Restarting..."
        sleep 2
        continue
    fi

    crash_count=$((crash_count+1))
    backoff=$((2**crash_count))
    [ $backoff -gt $MAX_BACKOFF ] && backoff=$MAX_BACKOFF

    ts=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    echo "{\"ts\":\"$ts\",\"crash\":$crash_count,\"exit_code\":$EXIT_CODE,\"backoff_s\":$backoff}" >> "$RESTART_LOG"

    echo "[run_forever] Crash #$crash_count (exit $EXIT_CODE). Restarting in ${backoff}s..."
    sleep $backoff
done
