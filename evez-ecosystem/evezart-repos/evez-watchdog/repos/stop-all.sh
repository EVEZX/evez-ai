#!/usr/bin/env bash
# EVEZ-OS — Stop all services
LOGS="/home/openclaw/.openclaw/workspace/logs"

for svc in omega vcl clawbreak mesh; do
  PIDFILE="$LOGS/${svc}.pid"
  if [ -f "$PIDFILE" ]; then
    PID=$(cat "$PIDFILE")
    if kill -0 "$PID" 2>/dev/null; then
      kill "$PID"
      echo "🛑 Stopped $svc (PID $PID)"
    else
      echo "  $svc already stopped"
    fi
    rm "$PIDFILE"
  else
    echo "  $svc — no PID file"
  fi
done
