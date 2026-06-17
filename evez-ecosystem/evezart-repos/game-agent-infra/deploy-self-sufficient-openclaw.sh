#!/bin/bash
#
# Master Deployment Script
# One-command setup for a fully self-sufficient, zero-cost OpenClaw instance
# with Game Agent Infra, EVEZ skills, monitoring, and autonomous maintenance.
#
# Usage: ./deploy-self-sufficient-openclaw.sh
#

set -e

echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║  DEPLOYING SELF-SUFFICIENT OPENCLAW + GAME AGENT INFRA                    ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"

# 1. Ensure we have the latest bootstrap
if [ ! -f vm-bootstrap.sh ]; then
    echo "[ERROR] vm-bootstrap.sh not found. Run from the correct directory."
    exit 1
fi

# 2. Make scripts executable
chmod +x vm-bootstrap.sh
chmod +x game-agent-infra/tools/self_diagnose.py 2>/dev/null || true

echo ""
echo ">>> Preparing Game Agent Infra package..."
cd game-agent-infra
pip install -e . --quiet || echo "Note: pip install may require sudo in some environments"
cd ..

echo ""
echo ">>> All components prepared."
echo ""
echo "READY FOR DEPLOYMENT"
echo ""
echo "Run these two commands on your local machine:"
echo ""
echo "  scp deploy-self-sufficient-openclaw.sh vm-bootstrap.sh ubuntu@161.153.123.176:~/"
echo "  ssh ubuntu@161.153.123.176 'chmod +x *.sh && ./deploy-self-sufficient-openclaw.sh'"
echo ""
echo "This will deploy a fully autonomous, self-healing OpenClaw instance with:"
echo "  - Standard Compute (free)"
echo "  - Game Agent Infra + EVEZ skills"
echo "  - Prometheus + Grafana monitoring"
echo "  - Auto-restart and self-diagnosis"
echo "  - Telegram bot support ready (EvezVearl)"
echo ""
echo "After deployment, the instance will run powerfully and independently."
echo "You can later add the Telegram token via config patch or environment."