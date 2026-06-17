#!/usr/bin/env bash
set -euo pipefail

# Phone-first: make the Codespace boot into a working, clickable game + API.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "[atlas-setup] Installing Node deps (if needed)..."
if [ ! -d node_modules ]; then
  npm install
else
  echo "[atlas-setup] node_modules already present."
fi

echo "[atlas-setup] Installing Python deps (if needed)..."
python3 -m pip install --upgrade pip >/dev/null 2>&1 || true
pip3 install -r fsc/requirements.txt >/dev/null 2>&1 || true

echo "[atlas-setup] Starting Atlas spine HTTP server on port 7777 (background)..."

PID_FILE=".atlas-spine.pid"
LOG_FILE="atlas-spine.log"

# If we already started it, don't start again.
if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
  echo "[atlas-setup] Spine already running (PID $(cat "$PID_FILE"))."
  exit 0
fi

# Start server.
nohup npm run atlas:spine:http > "$LOG_FILE" 2>&1 &
echo $! > "$PID_FILE"

echo "[atlas-setup] Spine PID: $(cat "$PID_FILE")"

echo "[atlas-setup] Waiting for server..."
sleep 2

# Best-effort readiness check.
if command -v curl >/dev/null 2>&1; then
  if curl -s "http://localhost:7777/verify" >/dev/null 2>&1; then
    echo "[atlas-setup] ✅ Spine is responding at http://localhost:7777"
  else
    echo "[atlas-setup] ⚠️ Spine not reachable yet; check $LOG_FILE"
  fi
fi
