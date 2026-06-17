#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# ClawBreak Oracle Cloud Free Tier Installer
# Run on a fresh Ubuntu ARM64 instance (4 OCPU, 24GB RAM = FREE)
# Usage: bash <(curl -fsSL https://raw.githubusercontent.com/EvezArt/clawbreak-ai/main/install-oracle.sh)
# ═══════════════════════════════════════════════════════════════
set -e

echo "⚡ ClawBreak Oracle Cloud Installer"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 1. System prep
echo "[1/6] Updating system..."
sudo apt-get update -qq && sudo apt-get upgrade -y -qq

# 2. Install Python 3.12
echo "[2/6] Installing Python..."
sudo apt-get install -y python3 python3-pip python3-venv

# 3. Clone ClawBreak
echo "[3/6] Cloning ClawBreak..."
cd /opt
sudo git clone https://github.com/EvezArt/clawbreak-ai.git clawbreak
cd /opt/clawbreak

# 4. Install dependencies
echo "[4/6] Installing dependencies..."
sudo pip3 install --break-system-packages fastapi uvicorn httpx pyyaml

# 5. Set up service
echo "[5/6] Installing as systemd service..."
sudo useradd -m -s /bin/bash clawbreak 2>/dev/null || true
sudo chown -R clawbreak:clawbreak /opt/clawbreak

sudo tee /etc/systemd/system/clawbreak.service << 'SVC'
[Unit]
Description=ClawBreak AI Agent
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=clawbreak
WorkingDirectory=/opt/clawbreak
ExecStart=/usr/bin/python3 /opt/clawbreak/server.py
Restart=always
RestartSec=5
Environment=HOME=/home/clawbreak
Environment=CLAWBREAK_LLM_API_KEY=GUNQBRQVDGXAPZDCOLYE7XKMZRAN4ZOQNYHA
Environment=CLAWBREAK_PORT=8080

[Install]
WantedBy=multi-user.target
SVC

sudo systemctl daemon-reload
sudo systemctl enable clawbreak
sudo systemctl start clawbreak

# 6. Firewall
echo "[6/6] Opening firewall..."
sudo iptables -I INPUT 6 -p tcp --dport 8080 -j ACCEPT
sudo netfilter-persistent save 2>/dev/null || true

# Wait and verify
sleep 5
if curl -s http://127.0.0.1:8080/health | grep -q "ok"; then
    IP=$(curl -s ifconfig.me 2>/dev/null || echo "YOUR_IP")
    echo ""
    echo "╔══════════════════════════════════════════════════╗"
    echo "║  ⚡ ClawBreak is LIVE on Oracle Cloud!            ║"
    echo "║  Web UI: http://${IP}:8080/                       ║"
    echo "║  Health: http://${IP}:8080/health                 ║"
    echo "╚══════════════════════════════════════════════════╝"
else
    echo "⚠ Server may need a moment. Check: sudo systemctl status clawbreak"
fi
