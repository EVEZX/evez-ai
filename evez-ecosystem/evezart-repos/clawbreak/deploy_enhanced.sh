#!/bin/bash
# Deploy Enhanced ClawBreak with all improvements
set -e

echo "🚀 Deploying Enhanced ClawBreak v0.5.0..."

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Step 1: Install dependencies ===${NC}"
cd /home/openclaw/.openclaw/workspace/repos/clawbreak

# Install enhanced dependencies
pip3 install -r requirements.txt
pip3 install sentence-transformers psutil httpx[cli]

echo -e "${BLUE}=== Step 2: Set up environment variables ===${NC}"
if [ ! -f ".env.enhanced" ]; then
    cat > .env.enhanced << 'EOF'
# Enhanced ClawBreak Environment
GROQ_API_KEY=${GROQ_API_KEY:-}
OPENROUTER_API_KEY=${OPENROUTER_API_KEY:-}
HUGGINGFACE_TOKEN=${HUGGINGFACE_TOKEN:-}
GITHUB_TOKEN=${GITHUB_TOKEN:-}
TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN:-}
STRIPE_SECRET_KEY=${STRIPE_SECRET_KEY:-}
OLLAMA_HOST=${OLLAMA_HOST:-http://localhost:11434}

# Model defaults
DEFAULT_MODEL=llama-3.3-70b-versatile
DEFAULT_TEMPERATURE=0.7

# Memory settings
EMBEDDING_MODEL=all-MiniLM-L6-v2
MEMORY_DB_PATH=./data/memory.db

# Server settings
PORT=8080
HOST=0.0.0.0
WORKERS=4
LOG_LEVEL=info
EOF
    echo -e "${YELLOW}Created .env.enhanced file - please fill in your API keys${NC}"
fi

echo -e "${BLUE}=== Step 3: Create systemd service ===${NC}"
sudo tee /etc/systemd/system/clawbreak-enhanced.service << EOF
[Unit]
Description=ClawBreak Enhanced AI Agent
After=network.target
Requires=network.target

[Service]
Type=exec
User=openclaw
Group=openclaw
WorkingDirectory=/home/openclaw/.openclaw/workspace/repos/clawbreak
EnvironmentFile=/home/openclaw/.openclaw/workspace/repos/clawbreak/.env.enhanced
ExecStart=/usr/bin/python3 /home/openclaw/.openclaw/workspace/repos/clawbreak/enhanced_server.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=clawbreak-enhanced

# Security
NoNewPrivileges=true
ProtectSystem=strict
PrivateTmp=true
PrivateDevices=true
ProtectHome=true
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true
RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6
RestrictNamespaces=true
RestrictRealtime=true
SystemCallFilter=@system-service
SystemCallArchitectures=native

[Install]
WantedBy=multi-user.target
EOF

echo -e "${BLUE}=== Step 4: Enable and start service ===${NC}"
sudo systemctl daemon-reload
sudo systemctl enable clawbreak-enhanced.service
sudo systemctl restart clawbreak-enhanced.service

echo -e "${BLUE}=== Step 5: Update Caddy config ===${NC}"
sudo tee -a /etc/caddy/Caddyfile << 'EOF'

# Enhanced ClawBreak
api.clawbreak.evez.local {
    reverse_proxy localhost:8080
    header Access-Control-Allow-Origin *
    header Cache-Control "no-cache"
}

# EVEZ Dashboard
dashboard.evez.local {
    reverse_proxy localhost:8099 {
        header_up X-Real-IP {remote_host}
    }
    file_server browse {
        root /home/openclaw/.openclaw/workspace/repos/clawbreak/enhanced
    }
}
EOF

echo -e "${BLUE}=== Step 6: Reload Caddy ===${NC}"
sudo systemctl reload caddy

echo -e "${BLUE}=== Step 7: Test deployment ===${NC}"
sleep 3

echo -e "${YELLOW}Testing health endpoint...${NC}"
if curl -s http://localhost:8080/health | grep -q "healthy"; then
    echo -e "${GREEN}✓ Enhanced ClawBreak is running${NC}"
else
    echo -e "${RED}✗ Health check failed${NC}"
    sudo journalctl -u clawbreak-enhanced.service -n 20 --no-pager
fi

echo -e "${YELLOW}Testing enhanced features...${NC}"
if curl -s http://localhost:8080/models | grep -q "models"; then
    echo -e "${GREEN}✓ Model endpoint working${NC}"
else
    echo -e "${YELLOW}⚠ Model endpoint may not be enhanced${NC}"
fi

echo -e "${BLUE}=== Step 8: Create quick test script ===${NC}"
cat > test_enhanced.sh << 'EOF'
#!/bin/bash
echo "🧪 Testing Enhanced ClawBreak..."
echo "1. Health:"
curl -s http://localhost:8080/health | jq . 2>/dev/null || curl -s http://localhost:8080/health
echo ""
echo "2. Available models:"
curl -s http://localhost:8080/models | jq '.models[].name' 2>/dev/null || echo "Cannot list models"
echo ""
echo "3. Simple chat test:"
curl -s -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, who are you?", "session_id": "test123"}' | jq '.response' 2>/dev/null || echo "Chat test failed"
echo ""
echo "4. Ecosystem status:"
curl -s http://localhost:8080/evez/ecosystem | jq '.online' 2>/dev/null || echo "Ecosystem check failed"
EOF
chmod +x test_enhanced.sh

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Enhanced ClawBreak deployed!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}Endpoints:${NC}"
echo -e "  API:      http://localhost:8080"
echo -e "  Health:   http://localhost:8080/health"
echo -e "  Dashboard: http://localhost:8080/"
echo -e "  Models:   http://localhost:8080/models"
echo -e "  WebSocket: ws://localhost:8080/ws"
echo ""
echo -e "${BLUE}Quick test:${NC}"
echo -e "  ./test_enhanced.sh"
echo ""
echo -e "${BLUE}Logs:${NC}"
echo -e "  sudo journalctl -u clawbreak-enhanced.service -f"
echo ""
echo -e "${BLUE}Configuration:${NC}"
echo -e "  Edit API keys in: .env.enhanced"
echo -e "  Service config: /etc/systemd/system/clawbreak-enhanced.service"
echo ""
echo -e "${YELLOW}⚠ Next steps:${NC}"
echo -e "  1. Fill in API keys in .env.enhanced"
echo -e "  2. Restart service: sudo systemctl restart clawbreak-enhanced"
echo -e "  3. Test with: ./test_enhanced.sh"
echo -e "  4. Check enhanced features at: http://localhost:8080/"