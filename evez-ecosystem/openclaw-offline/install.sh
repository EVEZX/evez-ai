#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════════╗
# ║  EVEZ OpenClaw — Offline Secure Install                    ║
# ║  Self-contained, zero-dependency, air-gapped deployment    ║
# ║  Version: 2026.6.8 | Built: $(date -u +%Y-%m-%d)                     ║
# ╚══════════════════════════════════════════════════════════════╝
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
INSTALL_DIR="${1:-/opt/openclaw}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo -e "${CYAN}╔══════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║  🦞 EVEZ OpenClaw — Offline Secure Install      ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════╝${NC}"

# ─── Pre-flight checks ───
echo -e "${YELLOW}[1/8] Pre-flight checks...${NC}"
command -v tar >/dev/null 2>&1 || { echo -e "${RED}tar required${NC}"; exit 1; }
command -v gzip >/dev/null || { echo -e "${RED}gzip required${NC}"; exit 1; }
[ -f "$SCRIPT_DIR/openclaw-core/openclaw.mjs" ] || { echo -e "${RED}Core package missing${NC}"; exit 1; }
echo -e "  ${GREEN}✓${NC} Pre-flight passed"

# ─── Create directory structure ───
echo -e "${YELLOW}[2/8] Creating directory structure...${NC}"
sudo mkdir -p "$INSTALL_DIR"/{bin,config,skills,logs,media,wiki,state}
sudo mkdir -p "$INSTALL_DIR"/.openclaw/{cache,credentials,devices,extensions,plugins,sessions}
echo -e "  ${GREEN}✓${NC} Directories created at $INSTALL_DIR"

# ─── Copy Node.js runtime ───
echo -e "${YELLOW}[3/8] Installing Node.js runtime...${NC}"
if [ -f "$SCRIPT_DIR/bin/node" ]; then
    sudo cp "$SCRIPT_DIR/bin/node" "$INSTALL_DIR/bin/node"
    sudo chmod +x "$INSTALL_DIR/bin/node"
    echo -e "  ${GREEN}✓${NC} Node.js $(($INSTALL_DIR/bin/node --version 2>/dev/null || echo 'bundled'))"
else
    echo -e "  ${YELLOW}⚠${NC} Using system Node.js (requires node >= 22)"
    command -v node >/dev/null 2>&1 || { echo -e "${RED}Node.js 22+ required${NC}"; exit 1; }
fi

# ─── Copy OpenClaw core ───
echo -e "${YELLOW}[4/8] Installing OpenClaw core...${NC}"
sudo cp -r "$SCRIPT_DIR/openclaw-core" "$INSTALL_DIR/openclaw"
sudo chmod -R 755 "$INSTALL_DIR/openclaw"
echo -e "  ${GREEN}✓${NC} Core installed ($(du -sh "$INSTALL_DIR/openclaw" | cut -f1))"

# ─── Install skills ───
echo -e "${YELLOW}[5/8] Installing skills...${NC}"
SKILL_COUNT=0
for skilldir in "$SCRIPT_DIR/skills/"*/; do
    [ -d "$skilldir" ] || continue
    name=$(basename "$skilldir")
    sudo cp -r "$skilldir" "$INSTALL_DIR/skills/$name" 2>/dev/null
    SKILL_COUNT=$((SKILL_COUNT + 1))
done
echo -e "  ${GREEN}✓${NC} $SKILL_COUNT skill packages installed"

# ─── Configure ───
echo -e "${YELLOW}[6/8] Generating secure configuration...${NC}"
if [ -f "$SCRIPT_DIR/config/openclaw.template.json" ]; then
    # Generate random gateway token
    GATEWAY_TOKEN=$(openssl rand -hex 24 2>/dev/null || head -c 48 /dev/urandom | xxd -p)
    
    # Replace template variables with real values or env vars
    CONFIG=$(cat "$SCRIPT_DIR/config/openclaw.template.json")
    CONFIG=$(echo "$CONFIG" | sed "s/{{VULTR_API_KEY}}/${VULTR_API_KEY:-CHANGE_ME}/g")
    CONFIG=$(echo "$CONFIG" | sed "s/{{OPENROUTER_API_KEY}}/${OPENROUTER_API_KEY:-CHANGE_ME}/g")
    CONFIG=$(echo "$CONFIG" | sed "s/{{GROQ_API_KEY}}/${GROQ_API_KEY:-CHANGE_ME}/g")
    
    echo "$CONFIG" | sudo tee "$INSTALL_DIR/.openclaw/openclaw.json" > /dev/null
    sudo chmod 600 "$INSTALL_DIR/.openclaw/openclaw.json"
    echo -e "  ${GREEN}✓${NC} Configuration generated (token: ${GATEWAY_TOKEN:0:8}...)"
else
    echo -e "  ${YELLOW}⚠${NC} No template found — run openclaw setup manually"
fi

# ─── Systemd service ───
echo -e "${YELLOW}[7/8] Installing systemd service...${NC}"
sudo tee /etc/systemd/system/openclaw-offline.service > /dev/null << SVC
[Unit]
Description=OpenClaw Offline — AI Assistant Gateway
After=network.target

[Service]
Type=simple
User=openclaw
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/bin/node $INSTALL_DIR/openclaw/openclaw.mjs
Restart=always
RestartSec=5
Environment=NODE_ENV=production
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
SVC
sudo systemctl daemon-reload
sudo systemctl enable openclaw-offline
echo -e "  ${GREEN}✓${NC} Service installed (openclaw-offline.service)"

# ─── Security hardening ───
echo -e "${YELLOW}[8/8] Applying security hardening...${NC}"
sudo chmod -R o-rwx "$INSTALL_DIR/.openclaw"
sudo chmod 600 "$INSTALL_DIR/.openclaw/openclaw.json" 2>/dev/null
[ -f "$INSTALL_DIR/.openclaw/credentials" ] && sudo chmod 700 "$INSTALL_DIR/.openclaw/credentials"
echo -e "  ${GREEN}✓${NC} Permissions hardened (0600 config, 0700 credentials)"

# ─── Done ───
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  🦞 EVEZ OpenClaw — Installation Complete        ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════╝${NC}"
echo ""
echo "Start:    sudo systemctl start openclaw-offline"
echo "Status:   sudo systemctl status openclaw-offline"
echo "Logs:     journalctl -u openclaw-offline -f"
echo "Config:   $INSTALL_DIR/.openclaw/openclaw.json"
echo ""
echo -e "${YELLOW}Next: Edit config to add your API keys, then start the service.${NC}"
