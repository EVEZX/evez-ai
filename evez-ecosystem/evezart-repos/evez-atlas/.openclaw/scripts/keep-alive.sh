#!/bin/bash
# Ensures OpenClaw runs continuously in Codespaces

while true; do
  # Check if gateway is running
  if ! openclaw gateway status > /dev/null 2>&1; then
    echo "⚠️ Gateway down, restarting..."
    openclaw gateway start --detach
    sleep 10
  fi
  
  # Health check
  if openclaw health | grep -q "unhealthy"; then
    echo "⚠️ Unhealthy state detected, restarting..."
    openclaw gateway restart
    sleep 10
  fi
  
  # Check recursion depth
  DEPTH=$(openclaw config get deepclaw.currentDepth)
  if [ "$DEPTH" -lt 1 ]; then
    echo "🌀 Restarting recursive loop..."
    openclaw skills execute deepclaw-integration recursiveLoop
  fi
  
  sleep 30
done