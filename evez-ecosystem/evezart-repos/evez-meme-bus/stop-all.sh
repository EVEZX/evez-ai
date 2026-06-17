#!/usr/bin/env bash
echo "■ Stopping all EVEZ Meme Bus processes..."
for pidfile in logs/*.pid; do
  pid=$(cat "$pidfile" 2>/dev/null) && kill "$pid" 2>/dev/null && echo "  stopped PID $pid ($pidfile)"
  rm -f "$pidfile"
done
echo "■ Done."
