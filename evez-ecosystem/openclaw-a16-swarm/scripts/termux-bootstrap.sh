#!/data/data/com.termux/files/usr/bin/bash
# ╔══════════════════════════════════════════════════════════════╗
# ║  EVEZ A16 Swarm — Termux Bootstrap                          ║
# ║  Run this FIRST on your Samsung Galaxy A16                  ║
# ║  Sets up full Linux environment inside Termux               ║
# ╚══════════════════════════════════════════════════════════════╝
set -e

echo "╔══════════════════════════════════════╗"
echo "║  📱 EVEZ A16 Swarm — Bootstrap       ║"
echo "╚══════════════════════════════════════╝"

# Update Termux packages
echo "[1/6] Updating Termux..."
pkg update -y && pkg upgrade -y

# Install core tools
echo "[2/6] Installing core packages..."
pkg install -y nodejs-lts python git openssh termux-api proot proot-distro

# Install proot-distro Ubuntu for full Linux compat
echo "[3/6] Installing Ubuntu (proot)..."
proot-distro install ubuntu

# Setup Ubuntu environment
echo "[4/6] Configuring Ubuntu environment..."
proot-distro login ubuntu -- bash -c "
    apt update && apt upgrade -y
    apt install -y python3 python3-pip curl wget tar gzip
    useradd -m -s /bin/bash openclaw 2>/dev/null || true
"

# Install Node.js in Ubuntu proot
echo "[5/6] Installing Node.js 22..."
proot-distro login ubuntu -- bash -c "
    curl -fsSL https://deb.nodesource.com/setup_22.x | bash -
    apt install -y nodejs
    node --version
    npm --version
"

# Create workspace
echo "[6/6] Creating workspace..."
proot-distro login ubuntu -- bash -c "
    mkdir -p /home/openclaw/.openclaw
    mkdir -p /home/openclaw/evez-ecosystem
"

echo ""
echo "╔══════════════════════════════════════╗"
echo "║  ✅ Bootstrap Complete               ║"
echo "╚══════════════════════════════════════╝"
echo ""
echo "Next: Run ./deploy-openclaw.sh"
