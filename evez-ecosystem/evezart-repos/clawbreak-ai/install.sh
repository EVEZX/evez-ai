#!/bin/bash
# ═══════════════════════════════════════════════════════════
# ClawBreak One-Liner Installer
# Usage: bash <(curl -fsSL https://raw.githubusercontent.com/EvezArt/clawbreak-ai/main/install.sh)
# ═══════════════════════════════════════════════════════════
set -e

BOLD='\033[1m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${BOLD}⚡ ClawBreak Installer${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━"

# Check for Python
if ! command -v python3 &>/dev/null; then
    echo "Installing Python3..."
    sudo apt-get update -qq && sudo apt-get install -y python3 python3-pip
fi

# Check for pip
if ! python3 -c "import pip" &>/dev/null; then
    echo "Installing pip..."
    sudo apt-get install -y python3-pip
fi

# Install
echo "Installing ClawBreak..."
pip3 install --break-system-packages clawbreak 2>/dev/null || {
    # Fallback: install from git
    pip3 install --break-system-packages fastapi uvicorn httpx pyyaml
    sudo git clone https://github.com/EvezArt/clawbreak-ai.git /opt/clawbreak 2>/dev/null || true
    cd /opt/clawbreak
}

# Set up systemd
echo "Setting up service..."
sudo tee /etc/systemd/system/clawbreak.service << SVC
[Unit]
Description=ClawBreak AI Agent
After=network-online.target

[Service]
Type=simple
WorkingDirectory=/opt/clawbreak
ExecStart=/usr/bin/python3 /opt/clawbreak/server.py
Restart=always
RestartSec=5
Environment=HOME=/root
Environment=CLAWBREAK_LLM_API_KEY=\${CLAWBREAK_LLM_API_KEY:-}

[Install]
WantedBy=multi-user.target
SVC

sudo systemctl daemon-reload
sudo systemctl enable clawbreak

# Open firewall
sudo ufw allow 8080/tcp 2>/dev/null || true
sudo iptables -I INPUT -p tcp --dport 8080 -j ACCEPT 2>/dev/null || true

echo ""
echo -e "${GREEN}${BOLD}✅ ClawBreak installed!${NC}"
echo ""
echo "Next steps:"
echo "  1. Set your API key: export CLAWBREAK_LLM_API_KEY=your_key"
echo "  2. Edit config: nano /opt/clawbreak/config.yaml"
echo "  3. Start: sudo systemctl start clawbreak"
echo "  4. Open: http://$(curl -s ifconfig.me 2>/dev/null || echo 'YOUR_IP'):8080/"
