#!/bin/bash
# Indestructible Stack — keeps OpenClaw alive no matter what
# Run via: nohup bash /home/openclaw/.openclaw/workspace/scripts/indestructible.sh &

LOG="/tmp/openclaw-indestructible.log"
GATEWAY="openclaw-gateway.service"
HEARTBEAT_URL="http://127.0.0.1:18789/api/health"

log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $1" >> "$LOG"; }

log "Indestructible watcher started (PID $$)"

while true; do
    # 1. Check systemd service
    if ! systemctl --user is-active "$GATEWAY" &>/dev/null; then
        log "Gateway DOWN — restarting via systemctl"
        systemctl --user restart "$GATEWAY"
        sleep 10
        continue
    fi

    # 2. Check health endpoint
    HEALTH=$(curl -sf "$HEARTBEAT_URL" 2>/dev/null)
    if [ $? -ne 0 ]; then
        log "Health check FAILED — restarting gateway"
        systemctl --user restart "$GATEWAY"
        sleep 10
        continue
    fi

    # 3. Check Telegram specifically
    if ! echo "$HEALTH" | grep -q "telegram"; then
        log "Telegram not in health — reloading config"
        systemctl --user restart "$GATEWAY"
        sleep 10
        continue
    fi

    # 4. Ensure linger is enabled (survives logout)
    if [ ! -f /var/lib/systemd/linger/openclaw ]; then
        loginctl enable-linger openclaw 2>/dev/null || true
    fi

    sleep 30
done
