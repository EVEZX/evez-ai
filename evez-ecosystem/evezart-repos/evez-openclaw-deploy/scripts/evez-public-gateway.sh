#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
# EVEZ OpenClaw — expose local gateway as public wss:// URL
# Uses cloudflared Quick Tunnel (free, no Cloudflare account needed)
# After running: paste the trycloudflare.com URL into the Space UI
# ═══════════════════════════════════════════════════════════════
set -euo pipefail

PORT="${OPENCLAW_PORT:-18789}"

# Install cloudflared if missing
if ! command -v cloudflared &>/dev/null; then
  echo "Installing cloudflared..."
  if command -v apt-get &>/dev/null; then
    curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg | tee /usr/share/keyrings/cloudflare-main.gpg >/dev/null
    echo 'deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] https://pkg.cloudflare.com/cloudflared jammy main' \
      | tee /etc/apt/sources.list.d/cloudflared.list
    apt-get update -q && apt-get install -y cloudflared
  elif command -v brew &>/dev/null; then
    brew install cloudflare/cloudflare/cloudflared
  else
    echo "Download cloudflared: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/"
    exit 1
  fi
fi

echo "Tunneling gateway port $PORT → public HTTPS..."
echo "Look for 'trycloudflare.com' in the output."
echo "Use wss://<your-subdomain>.trycloudflare.com as the gateway URL in the Space."
echo ""
cloudflared tunnel --url "http://127.0.0.1:$PORT"
