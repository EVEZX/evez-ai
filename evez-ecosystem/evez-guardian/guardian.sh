#!/bin/bash
# EVEZ Guardian — Intelligent self-healing daemon
# Checks all services, restarts if down, monitors disk/memory

SERVICES=(
  "evez-provider:9100"
  "evez-omega:8080"
  "evez-filter:9300"
  "evez-services-hub:9500"
  "evez-commerce:9700"
  "evez-arena:9800"
  "evez-consciousness:9600"
  "evez-tracer:9998"
  "evez-dashboard:9999"
  "evez-oracle-bridge:9400"
  "evez-backup-sync:-1"
  "evez-daw:-1"
)

DISK_CRITICAL=88
DISK_WARN=80
RESTARTED=()
ISSUES=()

for ENTRY in "${SERVICES[@]}"; do
  IFS=':' read -r SVC PORT <<< "$ENTRY"
  STATUS=$(systemctl --user is-active "$SVC" 2>/dev/null)

  if [[ "$STATUS" != "active" ]]; then
    systemctl --user restart "$SVC" 2>/dev/null
    sleep 2
    NEW_STATUS=$(systemctl --user is-active "$SVC" 2>/dev/null)
    if [[ "$NEW_STATUS" == "active" ]]; then
      RESTARTED+=("$SVC ✅ recovered")
    else
      RESTARTED+=("$SVC ❌ failed to recover")
      ISSUES+=("CRITICAL: $SVC down and won't restart")
    fi
  elif [[ "$PORT" != "-1" ]]; then
    if ! ss -tlnp 2>/dev/null | grep -q ":$PORT "; then
      systemctl --user restart "$SVC" 2>/dev/null
      sleep 2
      RESTARTED+=("$SVC (port $PORT was dead, restarted)")
    fi
  fi
done

# Disk check
DISK_PCT=$(df / | tail -1 | awk '{print $5}' | tr -d '%')
if [[ $DISK_PCT -ge $DISK_CRITICAL ]]; then
  pip cache purge 2>/dev/null
  npm cache clean --force 2>/dev/null
  rm -rf /tmp/*.log /tmp/*.tmp 2>/dev/null
  journalctl --vacuum-time=1h 2>/dev/null
  ISSUES+=("DISK CRITICAL: ${DISK_PCT}% — emergency cleanup performed")
elif [[ $DISK_PCT -ge $DISK_WARN ]]; then
  ISSUES+=("DISK WARNING: ${DISK_PCT}%")
fi

# Memory check
MEM_PCT=$(free | awk '/Mem:/{printf("%.0f"), $3/$2*100}')
if [[ $MEM_PCT -ge 90 ]]; then
  HOG=$(ps aux --sort=-%mem | grep -v 'openclaw\|systemd\|sshd\|bash\|cron' | head -1 | awk '{print $2, $11}')
  ISSUES+=("MEMORY CRITICAL: ${MEM_PCT}% — biggest: $HOG")
fi

# Log results
if [[ ${#RESTARTED[@]} -gt 0 || ${#ISSUES[@]} -gt 0 ]]; then
  echo "$(date -Iseconds) Guardian:" >> /tmp/guardian.log
  for r in "${RESTARTED[@]}"; do echo "  ↻ $r" >> /tmp/guardian.log; done
  for i in "${ISSUES[@]}"; do echo "  ⚠ $i" >> /tmp/guardian.log; done
fi
