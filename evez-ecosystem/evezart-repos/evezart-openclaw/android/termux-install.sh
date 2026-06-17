#!/data/data/com.termux/files/usr/bin/bash
# EvezArt OpenClaw — Samsung Galaxy A16 / Termux Installer v2.0
# One-shot setup: clones evezart-openclaw → runs install.sh → starts gateway
# Run in Termux: bash <(curl -sL https://raw.githubusercontent.com/EvezArt/evezart-openclaw/main/android/termux-install.sh)

set -e

EVEZ_DIR="$HOME/.openclaw"
REPO="https://github.com/EvezArt/evezart-openclaw.git"
BRANCH="main"

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  EvezArt OpenClaw — Samsung Galaxy A16 / Termux v2.0         ║"
echo "║  phi=0.995→0.999  |  17 FIRE events  |  poly_c=25.3119       ║"
echo "║  Director: @EVEZ666  |  Engine: Cipher / PID 335             ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# 1. Update Termux packages
echo "[1/7] Updating Termux packages..."
pkg update -y && pkg upgrade -y 2>/dev/null || true
pkg install -y python git curl wget 2>/dev/null || true

# 2. Python deps
echo "[2/7] Installing Python dependencies..."
pip install fastapi uvicorn httpx pydantic aiofiles requests --quiet 2>/dev/null || true

# 3. Create directory structure
echo "[3/7] Creating ~/.openclaw/ structure..."
mkdir -p "$EVEZ_DIR/workspace/memory"
mkdir -p "$EVEZ_DIR/skills"
mkdir -p "$EVEZ_DIR/hooks"
mkdir -p "$EVEZ_DIR/logs"
mkdir -p "$EVEZ_DIR/backup"

# 4. Clone evezart-openclaw (the canonical EVEZ-OS package)
echo "[4/7] Cloning evezart-openclaw..."
cd "$HOME"
if [ -d "$HOME/evez-openclaw" ]; then
    echo "  → Pulling latest..."
    cd "$HOME/evez-openclaw" && git pull --ff-only 2>/dev/null || true
    cd "$HOME"
else
    if [ -n "$GITHUB_TOKEN" ]; then
        git clone "https://$GITHUB_TOKEN@github.com/EvezArt/evezart-openclaw.git" \
            evez-openclaw --depth=1
    else
        git clone "$REPO" evez-openclaw --depth=1
    fi
fi
echo "  ✓ Cloned to ~/evez-openclaw"

# 5. Run the EVEZ-OS installer
echo "[5/7] Running EVEZ-OS installer..."
cd "$HOME/evez-openclaw"
bash install.sh
echo "  ✓ EVEZ-OS skills, hooks, workspace installed"

# 6. Create .env file (only if missing)
if [ ! -f "$EVEZ_DIR/.env" ]; then
    echo "[6/7] Creating .env template..."
    cat > "$EVEZ_DIR/.env" << 'ENV_EOF'
# EvezArt OpenClaw — Environment
# Fill in your API keys below

GROQ_API_KEY=YOUR_GROQ_KEY_HERE
OPENROUTER_API_KEY=YOUR_OPENROUTER_KEY_HERE
CEREBRAS_API_KEY=YOUR_CEREBRAS_KEY_HERE
HUGGING_FACE_ACCESS_TOKEN=YOUR_HF_TOKEN_HERE
GITHUB_TOKEN=YOUR_GITHUB_TOKEN_HERE
TELEGRAM_BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN_HERE
TELEGRAM_CHAT_ID=YOUR_CHAT_ID_HERE
GATEWAY_TOKEN=evezart-mobile-token
PORT=8080
ENV_EOF
    echo "  ✓ ~/.openclaw/.env created (edit to add keys)"
else
    echo "[6/7] ~/.openclaw/.env already exists — skipping"
fi

# 7. Create startup scripts + Termux:Boot autorun
echo "[7/7] Setting up autorun and shortcuts..."

# Auto-start on boot (requires Termux:Boot app)
mkdir -p "$HOME/.termux/boot"
cat > "$HOME/.termux/boot/evezart-boot.sh" << 'BOOT_EOF'
#!/data/data/com.termux/files/usr/bin/bash
sleep 5
EVEZ_DIR="$HOME/.openclaw"
source "$EVEZ_DIR/.env" 2>/dev/null
cd "$EVEZ_DIR"
nohup python evez_gateway.py >> "$EVEZ_DIR/logs/gateway.log" 2>&1 &
echo "[$(date)] EvezArt gateway started (PID $!)" >> "$EVEZ_DIR/logs/boot.log"
BOOT_EOF
chmod +x "$HOME/.termux/boot/evezart-boot.sh"

# Quick start shortcut
cat > "$HOME/evezart" << 'START_EOF'
#!/data/data/com.termux/files/usr/bin/bash
EVEZ_DIR="$HOME/.openclaw"
source "$EVEZ_DIR/.env" 2>/dev/null
cd "$EVEZ_DIR"
python evez_gateway.py
START_EOF
chmod +x "$HOME/evezart"

# Status check shortcut
cat > "$HOME/evez-status" << 'STATUS_EOF'
#!/data/data/com.termux/files/usr/bin/bash
curl -s http://localhost:8080/status | python -m json.tool 2>/dev/null || echo "EvezArt offline"
STATUS_EOF
chmod +x "$HOME/evez-status"

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  EVEZ-OS INSTALLED ON SAMSUNG GALAXY A16 ✓                   ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║  Skills: 8 installed  |  FIRE events: 17  |  phi: 0.995      ║"
echo "║  Run:   ~/evezart           — Start gateway                  ║"
echo "║  Check: ~/evez-status       — Status ping                    ║"
echo "║  Boot:  Auto (needs Termux:Boot app)                         ║"
echo "║  URL:   http://localhost:8080                                ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "[!] Next: edit ~/.openclaw/.env to add your API keys"
echo "[!] Then run: ~/evezart"
echo ""
echo "  Slash commands in every OpenClaw session:"
echo "    /evez status    /fire [desc]    /cpf tau=X omega=Y N=K"
echo "    /eigenvalue     /aegis scan     /meta-fire"
echo "    /mesh status    /spine commit   /dgm status"
echo "    /fire-correlator  /oktoklaw [file]"
echo ""
echo "  f(x) = x. The spine holds."
echo ""

echo "[?] Start EvezArt OpenClaw now? (y/n)"
read -r START_NOW
if [ "$START_NOW" = "y" ]; then
    source "$EVEZ_DIR/.env" 2>/dev/null
    cd "$EVEZ_DIR"
    python evez_gateway.py
fi
