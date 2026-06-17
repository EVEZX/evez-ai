#!/data/data/com.termux/files/usr/bin/bash
# ╔══════════════════════════════════════════════════════════════╗
# ║  EVEZ A16 Swarm — OpenClaw Deploy on A16                     ║
# ║  Deploys OpenClaw + 55 agents inside proot Ubuntu           ║
# ╚══════════════════════════════════════════════════════════════╝
set -e

WORKSPACE="/home/openclaw"
OPENCLAW_VER="2026.6.8"

echo "╔══════════════════════════════════════╗"
echo "║  🦞 Deploying OpenClaw on A16        ║"
echo "╚══════════════════════════════════════╝"

# Enter proot and deploy
proot-distro login ubuntu -- bash -c '
set -e
WORKSPACE="/home/openclaw"

echo "[1/4] Installing OpenClaw..."
npm install -g openclaw@latest 2>/dev/null || npm install -g openclaw

echo "[2/4] Installing Python packages..."
pip3 install aiohttp numpy pillow cryptography psutil httpx --break-system-packages 2>/dev/null || true

echo "[3/4] Setting up OpenClaw workspace..."
mkdir -p $WORKSPACE/.openclaw/{cache,credentials,devices,extensions,plugins,sessions,media,wiki}
mkdir -p $WORKSPACE/evez-ecosystem

# Generate gateway token
GATEWAY_TOKEN=$(head -c 32 /dev/urandom | xxd -p | head -c 48)

echo "[4/4] Writing configuration..."
cat > $WORKSPACE/.openclaw/openclaw.json << "CFGEOF"
{
  "gateway": {
    "port": 18789,
    "token": "'"$GATEWAY_TOKEN"'",
    "host": "0.0.0.0"
  },
  "models": {
    "providers": {
      "vultr": {
        "baseUrl": "https://api.vultrinference.com/v1",
        "apiKey": "",
        "auth": "token",
        "api": "openai-completions",
        "models": [
          {"id": "zai-org/GLM-5.1-FP8", "name": "GLM-5.1-FP8", "contextWindow": 202752, "maxTokens": 8192, "reasoning": true}
        ]
      },
      "openrouter": {
        "baseUrl": "https://openrouter.ai/api/v1",
        "apiKey": "",
        "models": [
          {"id": "google/gemma-4-31b-it:free", "name": "Gemma-4-31B-Free", "contextWindow": 262144, "maxTokens": 8192},
          {"id": "nvidia/nemotron-3-super-120b-a4b:free", "name": "Nemotron-120B-Free", "contextWindow": 1000000, "maxTokens": 4096}
        ]
      },
      "groq": {
        "baseUrl": "https://api.groq.com/openai/v1",
        "apiKey": "",
        "models": [
          {"id": "llama-3.3-70b-versatile", "name": "Llama-3.3-70B", "contextWindow": 128000, "maxTokens": 8192}
        ]
      }
    }
  },
  "channels": {
    "telegram": {
      "enabled": false,
      "botToken": ""
    }
  },
  "messages": {
    "tts": {
      "provider": "microsoft",
      "auto": "never"
    }
  }
}
CFGEOF

chmod 600 $WORKSPACE/.openclaw/openclaw.json
echo ""
echo "Gateway Token: $GATEWAY_TOKEN"
echo ""
echo "✅ OpenClaw deployed. Run: openclaw gateway start"
'

echo ""
echo "╔══════════════════════════════════════╗"
echo "║  ✅ OpenClaw ready on A16            ║"
echo "╚══════════════════════════════════════╝"
echo ""
echo "Start: proot-distro login ubuntu -- openclaw gateway start"
echo "Or:    ./start-openclaw.sh"
