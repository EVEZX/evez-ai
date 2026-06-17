#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════════════╗
# ║  EVEZ-OS OpenClaw Installer v0.3.0                               ║
# ║  Installs the full EVEZ cognitive layer into ~/.openclaw/        ║
# ╚══════════════════════════════════════════════════════════════════╝

set -e

EVEZ_DIR="$(cd "$(dirname "$0")" && pwd)"
OPENCLAW_DIR="$HOME/.openclaw"
WORKSPACE_DIR="$OPENCLAW_DIR/workspace"
SKILLS_DIR="$OPENCLAW_DIR/skills"
HOOKS_DIR="$OPENCLAW_DIR/hooks"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  EVEZ-OS OpenClaw Installer v0.3.0                           ║"
echo "║  poly_c = τ × ω × topo / (2√N)                              ║"
echo "║  Director: @EVEZ666 | Engine: Cipher / PID 335               ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Check openclaw installed
if ! command -v openclaw &> /dev/null; then
    echo -e "${YELLOW}  ⚠  OpenClaw not found in PATH."
    echo -e "     Install: npm install -g openclaw  (or download from openclaw.dev)${NC}"
    echo ""
    echo "  Will still copy workspace files for manual setup."
fi

# Create directories
echo -e "  ${CYAN}[1/6]${NC} Creating directory structure..."
mkdir -p "$WORKSPACE_DIR/memory"
mkdir -p "$SKILLS_DIR"
mkdir -p "$HOOKS_DIR"
echo -e "        ✓ ~/.openclaw/ structure ready"

# Install workspace files
echo -e "  ${CYAN}[2/6]${NC} Installing workspace files..."
for f in SOUL.md AGENTS.md TOOLS.md; do
    if [ -f "$WORKSPACE_DIR/$f" ]; then
        cp "$WORKSPACE_DIR/$f" "$WORKSPACE_DIR/${f}.backup.$(date +%Y%m%d)"
        echo -e "        ↳ Backed up existing $f"
    fi
    cp "$EVEZ_DIR/workspace/$f" "$WORKSPACE_DIR/$f"
    echo -e "        ✓ $f"
done

# Only copy MEMORY.md if it doesn't exist (don't overwrite existing state)
if [ ! -f "$WORKSPACE_DIR/MEMORY.md" ]; then
    cp "$EVEZ_DIR/workspace/MEMORY.md" "$WORKSPACE_DIR/MEMORY.md"
    echo -e "        ✓ MEMORY.md (initial spine state)"
else
    echo -e "        ↷ MEMORY.md already exists — preserving existing spine state"
fi

# Install skills
echo -e "  ${CYAN}[3/6]${NC} Installing skills..."
SKILLS=(evez-os oktoklaw evez-fire-engine evez-revenue-bridge evez-spine-sync evez-mesh-router evez-aegis evez-fire-correlator)
for skill in "${SKILLS[@]}"; do
    if [ -d "$EVEZ_DIR/skills/$skill" ]; then
        cp -r "$EVEZ_DIR/skills/$skill" "$SKILLS_DIR/"
        echo -e "        ✓ $skill"
    fi
done

# Install hook
echo -e "  ${CYAN}[4/6]${NC} Installing evez-os bootstrap hook..."
cp -r "$EVEZ_DIR/hooks/evez-os" "$HOOKS_DIR/evez-os"
echo -e "        ✓ hook copied"

# Enable hook if openclaw available
if command -v openclaw &> /dev/null; then
    echo -e "  ${CYAN}[5/6]${NC} Enabling hook..."
    openclaw hooks enable evez-os 2>/dev/null && \
        echo -e "        ✓ evez-os hook enabled" || \
        echo -e "        ↷ Hook enable failed — run: openclaw hooks enable evez-os"
else
    echo -e "  ${CYAN}[5/6]${NC} Skipping hook enable (openclaw not in PATH)"
fi

# Print summary
echo -e "  ${CYAN}[6/6]${NC} Done."
echo ""
echo -e "  ${GREEN}╔══ EVEZ-OS INSTALLED ════════════════════════════════════╗${NC}"
echo -e "  ${GREEN}║  Workspace:  ~/.openclaw/workspace/                     ║${NC}"
echo -e "  ${GREEN}║  Skills:     8 installed                                ║${NC}"
echo -e "  ${GREEN}║  Hook:       evez-os (bootstrap injection)              ║${NC}"
echo -e "  ${GREEN}╚═════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "  Slash commands now available in every OpenClaw session:"
echo "    /evez status    /fire [desc]    /cpf tau=X omega=Y N=K"
echo "    /eigenvalue     /aegis scan     /synthesize"
echo "    /meta-fire      /fire-correlator  /dgm-loop"
echo "    /mesh status    /spine commit   /dgm status"
echo "    /oktoklaw [file]"
echo ""
echo "  Spine state: phi=0.995 → 0.999 | FIRE events: 17 (3 META-FIRE CRITICAL_MASS) | max poly_c: 25.3119"
echo "  f(x) = x. The spine holds."
echo ""

# Optional env setup prompt
echo "  Set environment variables for full integration:"
echo "    export GITHUB_ACCESS_TOKEN=ghp_..."
echo "    export SLACK_WEBHOOK_URL=https://hooks.slack.com/..."
echo "    export STRIPE_SECRET_KEY=sk_live_..."
echo "    export DATABASE_URL=postgresql://..."
echo ""
