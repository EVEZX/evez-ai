#!/usr/bin/env bash
# EVEZ VCL Live — One-Shot Deploy Bootstrap
# Run: curl -sSL https://raw.githubusercontent.com/EvezArt/moltbot-live/main/deploy.sh | bash
# Or: bash deploy.sh
# Handles: Fly auth, app creation, secrets, deploy — everything.
set -euo pipefail

echo "═══════════════════════════════════════════════════"
echo "  EVEZ VCL Live — Deploy Bootstrap"
echo "═══════════════════════════════════════════════════"

# Check deps
command -v flyctl >/dev/null 2>&1 || {
  echo "[deploy] Installing flyctl..."
  curl -L https://fly.io/install.sh | sh
  export PATH="$HOME/.fly/bin:$PATH"
}

# Auth check
if ! flyctl auth whoami &>/dev/null; then
  echo "[deploy] Not logged in to Fly.io"
  echo "[deploy] Opening browser for auth..."
  flyctl auth login
fi

echo "[deploy] Authenticated as: $(flyctl auth whoami)"

# Create app (idempotent)
echo "[deploy] Ensuring app exists..."
flyctl apps create evez-vcl-live --org evez 2>/dev/null && echo "[deploy] App created!" || echo "[deploy] App already exists"

# Set secrets
if [ -n "${YOUTUBE_STREAM_KEY:-}" ]; then
  echo "[deploy] Setting YOUTUBE_STREAM_KEY..."
  echo "$YOUTUBE_STREAM_KEY" | flyctl secrets set YOUTUBE_STREAM_KEY=- --app evez-vcl-live --stage
else
  echo "[deploy] ⚠️  Set YOUTUBE_STREAM_KEY env var first, or run:"
  echo "         flyctl secrets set YOUTUBE_STREAM_KEY=<key> --app evez-vcl-live"
fi

# Deploy
echo "[deploy] Deploying to Fly.io..."
flyctl deploy --app evez-vcl-live --remote-only --strategy immediate --wait-timeout 120

echo ""
echo "═══════════════════════════════════════════════════"
echo "  ✅ EVEZ VCL Live is deployed and streaming!"
echo "  Health: https://evez-vcl-live.fly.dev/"
echo "═══════════════════════════════════════════════════"
