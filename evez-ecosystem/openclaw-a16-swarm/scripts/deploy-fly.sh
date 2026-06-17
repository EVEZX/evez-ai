#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════════╗
# ║  EVEZ A16 — Deploy 6 Agents to Fly.io                       ║
# ║  Free: 3 shared VMs, global edge, WebSocket support        ║
# ║  Requires: flyctl auth login                                  ║
# ╚══════════════════════════════════════════════════════════════╝
set -e

echo "╔══════════════════════════════════════╗"
echo "║  🪰 Deploying to Fly.io              ║"
echo "╚══════════════════════════════════════╝"

flyctl auth status || { echo "Not logged in! Run: flyctl auth login"; exit 1; }

# 1. DNS Shield
mkdir -p /tmp/fly-dns-shield && cd /tmp/fly-dns-shield
cat > Dockerfile << 'DKF'
FROM python:3.12-slim
WORKDIR /app
RUN pip install aiohttp
COPY dns-shield.py .
EXPOSE 10001
CMD ["python3", "dns-shield.py"]
DKF
cp /home/openclaw/evez-ecosystem/dns-shield/dns-shield.py . 2>/dev/null || true

echo "  ✅ DNS Shield Dockerfile ready"
echo ""
echo "To deploy:"
echo "  flyctl launch --name evez-dns-shield --region sjc --free"
echo "  flyctl deploy"

# 2. Aether WebSocket Bus
echo ""
echo "  To deploy Aether WS bus:"
echo "  flyctl launch --name evez-aether --region sjc --free"
echo "  flyctl deploy"
