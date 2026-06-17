#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
# EVEZ-OS Local Migration — Run this on the NEW host
# Expects migration-pack contents in current directory
# ═══════════════════════════════════════════════════════════════
set -euo pipefail

echo "🚀 EVEZ-OS Local Migration"
echo "==========================="

# 1. Install OpenClaw
echo ""
echo "⏳ Step 1/5: Installing OpenClaw..."
if ! command -v openclaw &>/dev/null; then
  curl -fsSL https://raw.githubusercontent.com/openclaw/openclaw/main/install.sh | bash
else
  echo "  OpenClaw already installed, skipping."
fi

# 2. Restore OpenClaw config
echo ""
echo "⏳ Step 2/5: Restoring OpenClaw configuration..."
mkdir -p "$HOME/.openclaw"
if [ -f openclaw-config.tar.gz ]; then
  tar -xzf openclaw-config.tar.gz -C "$HOME/"
  echo "  ✅ Config restored"
else
  echo "  ⚠️  No config bundle found, using defaults"
fi

# 3. Restore workspace
echo ""
echo "⏳ Step 3/5: Restoring workspace..."
if [ -f workspace.tar.gz ]; then
  tar -xzf workspace.tar.gz -C "$HOME/"
  echo "  ✅ Workspace restored (AGENTS.md, SOUL.md, memory/, skills/)"
else
  echo "  ⚠️  No workspace bundle found"
fi

# 4. Restore SSH keys
echo ""
echo "⏳ Step 4/5: Restoring SSH keys..."
if [ -f ssh-keys.tar.gz ]; then
  mkdir -p "$HOME/.ssh"
  tar -xzf ssh-keys.tar.gz -C "$HOME/"
  chmod 700 "$HOME/.ssh"
  chmod 600 "$HOME/.ssh/"*
  echo "  ✅ SSH keys restored"
else
  echo "  ⚠️  No SSH key bundle found"
fi

# 5. Restart OpenClaw
echo ""
echo "⏳ Step 5/5: Starting OpenClaw..."
openclaw gateway restart

echo ""
echo "════════════════════════════════════"
echo "✅ MIGRATION COMPLETE"
echo "════════════════════════════════════"
echo ""
echo "Your EVEZ-OS is now running on this host."
echo "Re-pair your nodes by scanning the QR code in the OpenClaw app."
echo ""
echo "Remember to:"
echo "  • Update DNS if using a custom domain"
echo "  • Re-pair phone/node devices"
echo "  • Decommission the old Vultr instance"
echo ""
echo "🫡 Long live EVEZ-OS"
