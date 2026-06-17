#!/bin/bash
# ═══════════════════════════════════════════════════════════
# EVEZ RESURRECTION — Nothing dies. Nothing stays dead.
# 
# This script is the final safety net. If ANY component goes
# down, this brings it back. Run every 60s via cron.
# ═══════════════════════════════════════════════════════════

LOG="/tmp/evez-resurrection.log"
LOCK="/tmp/evez-resurrection.lock"

# Prevent overlapping runs
if [ -f "$LOCK" ]; then
    LOCK_AGE=$(( $(date +%s) - $(stat -c %Y "$LOCK" 2>/dev/null || echo 0) ))
    if [ "$LOCK_AGE" -lt 120 ]; then
        exit 0
    fi
fi
touch "$LOCK"
trap "rm -f $LOCK" EXIT

log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $1" >> "$LOG"; }

RESURRECTIONS=0

# 1. Check OpenClaw Gateway (THE most critical)
if ! systemctl --user is-active openclaw-gateway.service &>/dev/null; then
    log "💀 OpenClaw Gateway DOWN — resurrecting"
    systemctl --user restart openclaw-gateway.service
    sleep 5
    RESURRECTIONS=$((RESURRECTIONS + 1))
fi

# 2. Check Telegram is connected (health endpoint)
TG_HEALTH=$(curl -sf http://127.0.0.1:18789/api/health 2>/dev/null)
if [ -z "$TG_HEALTH" ]; then
    log "💀 Gateway health endpoint unreachable — full restart"
    systemctl --user restart openclaw-gateway.service
    sleep 5
    RESURRECTIONS=$((RESURRECTIONS + 1))
fi

# 3. Check EVEZ Oracle Bridge
ORACLE_HEALTH=$(curl -sf http://127.0.0.1:9110/api/health 2>/dev/null)
if [ -z "$ORACLE_HEALTH" ]; then
    log "💀 Oracle Bridge DOWN — resurrecting"
    systemctl --user restart evez-oracle-bridge.service
    sleep 3
    RESURRECTIONS=$((RESURRECTIONS + 1))
fi

# 4. Check all EVEZ-OS services
EVEZ_SERVICES=(evez-consciousness evez-knowledge evez-debate evez-forge evez-scanner evez-ariel evez-cognizer evez-cycler evez-dashboard)

for svc in "${EVEZ_SERVICES[@]}"; do
    if ! systemctl --user is-active "$svc" &>/dev/null; then
        log "💀 $svc DOWN — resurrecting"
        systemctl --user restart "$svc"
        RESURRECTIONS=$((RESURRECTIONS + 1))
    fi
done

# 5. Quick port-level verification
for port in 9092 9093 9094 9095 9096 9097 9098 9099 9100 9110; do
    if ! nc -z -w 2 127.0.0.1 $port &>/dev/null; then
        log "💀 Port $port not listening — finding and restarting service"
        # Map port to service
        case $port in
            9092) svc="evez-consciousness" ;;
            9093) svc="evez-ariel" ;;
            9094) svc="evez-cognizer" ;;
            9095) svc="evez-cycler" ;;
            9096) svc="evez-knowledge" ;;
            9097) svc="evez-debate" ;;
            9098) svc="evez-forge" ;;
            9099) svc="evez-scanner" ;;
            9100) svc="evez-dashboard" ;;
            9110) svc="evez-oracle-bridge" ;;
            *) svc="" ;;
        esac
        if [ -n "$svc" ]; then
            systemctl --user restart "$svc"
            RESURRECTIONS=$((RESURRECTIONS + 1))
        fi
    fi
done

# 6. Ensure linger (survives logout)
if [ ! -f /var/lib/systemd/linger/openclaw ]; then
    loginctl enable-linger openclaw 2>/dev/null
fi

# 7. Log summary
if [ "$RESURRECTIONS" -gt 0 ]; then
    log "🔄 Resurrected $RESURRECTIONS service(s)"
else
    # Only log every 10 minutes when healthy
    LAST_LOG=$(stat -c %Y "$LOG" 2>/dev/null || echo 0)
    NOW=$(date +%s)
    if [ $((NOW - LAST_LOG)) -gt 600 ]; then
        log "✅ All services healthy (9/9 + gateway + bridge)"
    fi
fi

# 8. Check Consciousness Engine
if ! systemctl --user is-active evez-consciousness-engine &>/dev/null; then
    log "💀 Consciousness Engine DOWN — resurrecting"
    systemctl --user restart evez-consciousness-engine
    RESURRECTIONS=$((RESURRECTIONS + 1))
fi

if ! nc -z -w 2 127.0.0.1 9111 &>/dev/null; then
    log "💀 Port 9111 not listening — restarting consciousness engine"
    systemctl --user restart evez-consciousness-engine
    RESURRECTIONS=$((RESURRECTIONS + 1))
fi
