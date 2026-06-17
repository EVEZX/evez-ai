#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
: "${OPENCLAW_BIN:=openclaw}"
if ! command -v node >/dev/null 2>&1; then
  echo "Node.js >=22.12.0 is required. Install Node 24 LTS, then rerun." >&2
  exit 1
fi
NODE_MAJOR="$(node -p 'Number(process.versions.node.split(".")[0])')"
if [[ "$NODE_MAJOR" -lt 22 ]]; then
  echo "Node.js >=22.12.0 is required; found $(node --version). Install Node 24 LTS." >&2
  exit 1
fi
if ! command -v "$OPENCLAW_BIN" >/dev/null 2>&1; then
  echo "OpenClaw CLI not found as '$OPENCLAW_BIN'. Install OpenClaw, or set OPENCLAW_BIN=/path/to/openclaw." >&2
  echo "If using a source checkout: OPENCLAW_BIN=/path/to/openclaw.mjs ./scripts/evez-openclaw-install-host.sh" >&2
  exit 127
fi
"$ROOT/scripts/evez-openclaw-onboard.sh"
"$ROOT/scripts/evez-openclaw-ecosystem-sync.sh" --public-only || true
"$ROOT/scripts/evez-openclaw-recover.sh"
"$ROOT/scripts/evez-openclaw-doctor.sh" || true
cat <<OUT
Host install complete.
Next: install keepalive if desired:
  Linux:  cp systemd/openclaw-gateway.service ~/.config/systemd/user/openclaw-gateway.service && systemctl --user daemon-reload && systemctl --user enable --now openclaw-gateway
  macOS:  cp launchd/com.evez.openclaw.gateway.plist ~/Library/LaunchAgents/ && launchctl load -w ~/Library/LaunchAgents/com.evez.openclaw.gateway.plist
OUT
