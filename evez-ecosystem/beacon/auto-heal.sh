#!/bin/bash
# EVEZ Auto-Heal — check all services, restart dead ones
# Runs every 15 min via cron
HEALTH_URL="http://localhost:10016/v1/check"
RESTART_LOG="/home/openclaw/evez-ecosystem/beacon/heal-log.txt"

RESULT=$(curl -s "$HEALTH_URL" 2>/dev/null)
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) Health check" >> "$RESTART_LOG"

# Check each service via systemd
for svc in evez-provider evez-omega evez-filter evez-services-hub evez-neuros evez-commerce evez-arena evez-tracer evez-dns-shield evez-pulse evez-vault evez-proxy evez-cipher evez-relay evez-eigenforge evez-grimoire evez-sentinel evez-chrono evez-mirror evez-aether evez-scribe evez-nexus evez-orchestrate evez-beacon evez-herald evez-dashboard; do
    if ! systemctl is-active $svc &>/dev/null; then
        echo "  RESTARTING: $svc" >> "$RESTART_LOG"
        sudo systemctl restart $svc 2>/dev/null
    fi
done
