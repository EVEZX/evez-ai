#!/bin/bash
# ══════════════════════════════════════════════════════════
# ClawBreak Bootstrap — one command to bring everything alive
# Usage: bash boot.sh
# ══════════════════════════════════════════════════════════
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "⚡ ClawBreak Bootstrap"
echo "━━━━━━━━━━━━━━━━━━━━━"

# 1. Install Python deps
echo "[1/5] Installing Python dependencies..."
pip3 install --break-system-packages -q fastapi uvicorn httpx pyyaml 2>/dev/null || pip install -q fastapi uvicorn httpx pyyaml 2>/dev/null || true

# 2. Create data directory
mkdir -p data

# 3. Kill old instances
echo "[2/5] Cleaning old processes..."
pkill -f "python3 server.py" 2>/dev/null || true
pkill -f "daemon.py" 2>/dev/null || true
sleep 2

# 4. Start ClawBreak
echo "[3/5] Starting ClawBreak server on port 8080..."
nohup python3 server.py > data/server.log 2>&1 &
CB_PID=$!
sleep 3

# Verify
if curl -s -o /dev/null http://127.0.0.1:8080/health 2>/dev/null; then
    echo "  ✅ ClawBreak running (PID $CB_PID)"
else
    echo "  ⚠ Server may need a moment... waiting..."
    sleep 5
    if curl -s -o /dev/null http://127.0.0.1:8080/health 2>/dev/null; then
        echo "  ✅ ClawBreak running"
    else
        echo "  ❌ Server failed. Check data/server.log"
        cat data/server.log | tail -20
        exit 1
    fi
fi

# 5. Start daemon
echo "[4/5] Starting self-healing daemon..."
nohup python3 daemon.py > data/daemon.log 2>&1 &
DAEMON_PID=$!
sleep 1
echo "  ✅ Daemon running (PID $DAEMON_PID)"

# 6. Install crontab watchdog (the last line of defense)
echo "[5/5] Installing crontab watchdog..."
HEALER_CMD="cd $SCRIPT_DIR && python3 healer.py"
(crontab -l 2>/dev/null | grep -v "healer.py"; echo "*/3 * * * * $HEALER_CMD") | crontab -

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║  ⚡ ClawBreak is LIVE and SELF-HEALING           ║"
echo "╠══════════════════════════════════════════════════╣"
echo "║  Server:   http://127.0.0.1:8080                ║"
echo "║  Web UI:   http://127.0.0.1:8080/               ║"
echo "║  API:      http://127.0.0.1:8080/chat           ║"
echo "║  Health:   http://127.0.0.1:8080/health         ║"
echo "║  Daemon:   PID $DAEMON_PID (self-heals)         ║"
echo "║  Watchdog: crontab every 3 min (last defense)   ║"
echo "╚══════════════════════════════════════════════════╝"
