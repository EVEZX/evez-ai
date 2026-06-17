#!/bin/bash
set -e

echo "╔══════════════════════════════════════════╗"
echo "║   EVEZ-OPENCLAW MESH SETUP v2.0          ║"
echo "║   CLAW GOBLIN MODE                       ║"
echo "╚══════════════════════════════════════════╝"

# ── 1. Check requirements ──────────────────────────────────────────────────────
echo ">> Checking requirements..."
command -v node >/dev/null 2>&1 || { echo "!! Node.js required. Install from nodejs.org"; exit 1; }
command -v git  >/dev/null 2>&1 || { echo "!! git required."; exit 1; }
NODE_VER=$(node -e "process.stdout.write(process.version)")
echo "   Node: $NODE_VER ✓"

# ── 2. Install OpenClaw ────────────────────────────────────────────────────────
echo ">> Installing OpenClaw CLI..."
npm install -g @anthropic-ai/claude-code 2>/dev/null || true
# OpenClaw is the Claude Code fork — install and configure
npm install -g openclaw 2>/dev/null || echo "   (openclaw package not yet published — using claude-code path)"

# ── 3. Clone repos ────────────────────────────────────────────────────────────
echo ">> Syncing EvezArt repos..."
mkdir -p ~/evez_stack && cd ~/evez_stack

REPOS=(
  "https://github.com/EvezArt/evez-os.git"
  "https://github.com/EvezArt/evez-openclaw-mesh.git"
  "https://github.com/EvezArt/evezart-openclaw.git"
  "https://github.com/EvezArt/evez-synapse-engine.git"
  "https://github.com/EvezArt/evez-api-gateway.git"
)

for repo in "${REPOS[@]}"; do
  dir=$(basename "$repo" .git)
  if [ -d "$dir" ]; then
    echo "   Pulling $dir..."
    (cd "$dir" && git pull --quiet)
  else
    echo "   Cloning $dir..."
    git clone --quiet "$repo"
  fi
done

# ── 4. Copy openclaw config ───────────────────────────────────────────────────
echo ">> Installing OpenClaw config..."
mkdir -p ~/.openclaw
cp ~/evez_stack/evez-openclaw-mesh/openclaw.json ~/.openclaw/openclaw.json
echo "   Config installed at ~/.openclaw/openclaw.json ✓"

# ── 5. Set up .env ─────────────────────────────────────────────────────────────
if [ ! -f ~/.evez.env ]; then
  echo ">> Creating env template at ~/.evez.env..."
  cat > ~/.evez.env << 'ENVEOF'
# EvezArt OpenClaw Mesh — Environment Variables
# Fill these in then: source ~/.evez.env

export OPENROUTER_API_KEY=""
export GROQ_API_KEY=""
export GITHUB_PAT=""
export VERCEL_TOKEN=""
export CLOUDFLARE_API_TOKEN=""
export CLOUDFLARE_ACCOUNT_ID=""
export FLY_API_TOKEN=""
export TELEGRAM_BOT_TOKEN=""
export TELEGRAM_CHAT_ID=""
export MEM0_API_KEY=""
export STRIPE_SECRET_KEY=""
export NGROK_AUTHTOKEN=""
export OPENCLAW_GATEWAY_TOKEN="$(openssl rand -hex 32)"
export MEM0_USER_ID="evez666"
ENVEOF
  echo "   Edit ~/.evez.env with your keys, then: source ~/.evez.env"
else
  echo "   ~/.evez.env already exists ✓"
fi

# ── 6. Install venv for Python services ───────────────────────────────────────
echo ">> Setting up Python environment..."
cd ~/evez_stack/evez-openclaw-mesh
python3 -m venv venv 2>/dev/null || true
source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null || true
pip install --quiet --upgrade pip
pip install --quiet python-telegram-bot playwright requests cryptography PyGithub google-cloud-secret-manager

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║   SETUP COMPLETE                         ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo "  1. Edit ~/.evez.env with your API keys"
echo "  2. source ~/.evez.env"
echo "  3. openclaw --profile goblin"
echo "  OR"
echo "  3. docker compose up -d  (from evez-openclaw-mesh/)"
echo ""
echo "Gateway will be live at: http://localhost:18789"
echo "Ngrok tunnel: http://localhost:4040"