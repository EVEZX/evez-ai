#!/bin/bash
# ╔════════════════════════════════════════════════════════════╗
# ║  EVEZ ONE-COMMAND DEPLOY — Works on any Linux machine    ║
# ║  $ bash deploy-anywhere.sh                               ║
# ╚════════════════════════════════════════════════════════════╝
set -e

echo "🚀 EVEZ Universal Deploy"
echo "========================="

# Install deps
echo "[1/6] Installing dependencies..."
pip install -q aiohttp numpy scipy 2>/dev/null || pip3 install -q aiohttp numpy scipy 2>/dev/null || { echo "Install python3-pip first"; exit 1; }

# Clone repos
echo "[2/6] Cloning EVEZ ecosystem..."
mkdir -p ~/evez && cd ~/evez
git clone https://github.com/EVEZX/evez-ai.git 2>/dev/null || (cd evez-ai && git pull)
git clone https://github.com/EVEZX/neuros.git 2>/dev/null || (cd neuros && git pull)

# Configure API keys (from env or prompt)
echo "[3/6] Configuring API keys..."
export VULTR_API_KEY="${VULTR_API_KEY:-placeholder}"
export OPENROUTER_API_KEY="${OPENROUTER_API_KEY:-placeholder}"
export GROQ_API_KEY="${GROQ_API_KEY:-placeholder}"
export GEMINI_API_KEY="${GEMINI_API_KEY:-placeholder}"
export PROVIDER_PORT=9100

# Start services
echo "[4/6] Starting EVEZ Provider (port 9100)..."
cd ~/evez/evez-ai
nohup python3 provider/gateway-v2.py > /tmp/evez-provider.log 2>&1 &
sleep 3

echo "[5/6] Starting EVEZ Arena (port 9800)..."
nohup python3 arena/arena.py > /tmp/evez-arena.log 2>&1 &
sleep 3

echo "[6/6] Starting EVEZ Commerce (port 9700)..."
nohup python3 commerce/commerce.py > /tmp/evez-commerce.log 2>&1 &
sleep 3

# Verify
echo ""
echo "=== HEALTH CHECK ==="
for port in 9100 9800 9700; do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 3 http://localhost:$port/health 2>/dev/null)
  if [ "$STATUS" != "000" ]; then
    echo "✅ Port $port: UP"
  else
    echo "❌ Port $port: DOWN"
  fi
done

echo ""
echo "🟢 EVEZ Ecosystem deployed!"
echo "Provider: http://localhost:9100"
echo "Arena:    http://localhost:9800"
echo "Commerce: http://localhost:9700"
