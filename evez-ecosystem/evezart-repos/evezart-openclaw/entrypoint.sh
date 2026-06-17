#!/bin/bash
# EvezArt OpenClaw — Self-Managing Entrypoint

set -e

CONFIG_DIR=${OPENCLAW_CONFIG_DIR:-/root/.openclaw}
PORT=${PORT:-8080}
LOG="$CONFIG_DIR/logs/evez.log"
SPINE="$CONFIG_DIR/spine.jsonl"
RESTART_COUNT=0
MAX_RESTARTS=5

mkdir -p "$CONFIG_DIR/logs" "$CONFIG_DIR/backup"

# Append boot event to spine
append_spine() {
    local EVENT="$1"
    local TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    local PREV_HASH=""
    if [ -f "$SPINE" ]; then
        PREV_HASH=$(tail -1 "$SPINE" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('hash',''))" 2>/dev/null || echo "")
    fi
    local PAYLOAD="{\"ts\":\"$TS\",\"event\":\"$EVENT\",\"prev\":\"$PREV_HASH\"}"
    local HASH=$(echo -n "$PAYLOAD" | sha256sum | cut -d' ' -f1)
    echo "{\"ts\":\"$TS\",\"event\":\"$EVENT\",\"prev_hash\":\"$PREV_HASH\",\"hash\":\"$HASH\"}" >> "$SPINE"
}

append_spine "BOOT_START"
echo "[EVEZART] EvezArt OpenClaw starting on port $PORT..."

# GitHub sync on boot (non-blocking)
if [ -n "$GITHUB_TOKEN" ]; then
    echo "[EVEZART] Syncing workspace from GitHub..."
    cd "$CONFIG_DIR" && git init 2>/dev/null || true
    git remote set-url origin "https://$GITHUB_TOKEN@github.com/EvezArt/game-agent-infra.git" 2>/dev/null || true
    git fetch origin main --depth=1 2>/dev/null || true
    echo "[EVEZART] GitHub sync attempted."
fi &

# Try to launch openclaw gateway
launch_openclaw() {
    if command -v openclaw &> /dev/null; then
        echo "[EVEZART] Launching openclaw gateway..."
        openclaw gateway \
            --config "$CONFIG_DIR/openclaw.json" \
            --bind "0.0.0.0" \
            --port "$PORT" \
            --token "${GATEWAY_TOKEN:-evezart-default-token}"
    elif [ -f "/app/dist/index.js" ]; then
        echo "[EVEZART] Launching from dist/index.js..."
        node /app/dist/index.js gateway \
            --bind "0.0.0.0" \
            --port "$PORT"
    else
        echo "[EVEZART] Launching built-in EvezArt gateway server..."
        python3 /app/evez_gateway.py
    fi
}

# Self-managing restart loop
while [ $RESTART_COUNT -lt $MAX_RESTARTS ]; do
    echo "[EVEZART] Launch attempt $((RESTART_COUNT + 1))/$MAX_RESTARTS"
    append_spine "LAUNCH_ATTEMPT_$((RESTART_COUNT + 1))"
    
    launch_openclaw &
    PID=$!
    
    # Health check loop
    sleep 30
    if kill -0 $PID 2>/dev/null; then
        echo "[EVEZART] Process healthy (PID $PID)"
        append_spine "RUNNING_HEALTHY"
        wait $PID
        EXIT_CODE=$?
    else
        EXIT_CODE=1
    fi
    
    if [ $EXIT_CODE -eq 0 ]; then
        echo "[EVEZART] Clean exit."
        break
    fi
    
    RESTART_COUNT=$((RESTART_COUNT + 1))
    append_spine "RESTART_$RESTART_COUNT"
    echo "[EVEZART] Process exited ($EXIT_CODE). Restarting in 10s..."
    sleep 10
done

append_spine "SHUTDOWN"
echo "[EVEZART] All restarts exhausted or clean exit."
