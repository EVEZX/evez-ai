#!/usr/bin/env bash
set -euo pipefail

PID_FILE="/tmp/uvicorn.pid"

if [[ ! -f "$PID_FILE" ]]; then
  echo "No PID file found at $PID_FILE"
  exit 0
fi

PID="$(cat "$PID_FILE")"
if kill -0 "$PID" 2>/dev/null; then
  kill "$PID"
  echo "Stopped server process $PID"
else
  echo "Process $PID not running"
fi

rm -f "$PID_FILE"
