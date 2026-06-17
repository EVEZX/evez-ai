#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
# EVEZ OpenClaw Gateway — one-shot start on local machine or VPS
# Sets env vars, fixes config, starts gateway on port 18789
# ═══════════════════════════════════════════════════════════════
set -euo pipefail

: "${OPENCLAW_GATEWAY_TOKEN:?Set OPENCLAW_GATEWAY_TOKEN in your env}"
export OPENCLAW_STATE_DIR="${OPENCLAW_STATE_DIR:-$HOME/.openclaw}"
export OPENCLAW_GATEWAY_TOKEN

# Validate Node.js >=22.12.0
NODE_VER=$(node --version 2>/dev/null | sed 's/v//')
MAJOR="${NODE_VER%%.*}"
if [ "${MAJOR:-0}" -lt 22 ]; then
  echo "ERROR: Node.js >=22.12.0 required. Install Node 24:"
  echo "  curl -fsSL https://deb.nodesource.com/setup_24.x | bash && apt install nodejs"
  exit 1
fi
echo "✓ Node v${NODE_VER}"

# Install OpenClaw if missing
if ! command -v openclaw &>/dev/null; then
  echo "Installing @openclaw/openclaw ..."
  npm install -g @openclaw/openclaw
fi

# Fix invalid dmPolicy if present (allow -> allowlist)
CFG="$OPENCLAW_STATE_DIR/openclaw.json"
if [ -f "$CFG" ] && command -v python3 &>/dev/null; then
  python3 - <<PY
import json
try:
  c = json.load(open('$CFG'))
  tg = c.setdefault('channels', {}).setdefault('telegram', {})
  if tg.get('dmPolicy') not in ('pairing','allowlist','open','disabled',None,''):
    tg['dmPolicy'] = 'allowlist'
    json.dump(c, open('$CFG','w'), indent=2)
    print('  Config: fixed dmPolicy -> allowlist')
except Exception as e:
  print(f'  Config check skipped: {e}')
PY
fi

echo "Starting OpenClaw gateway on port 18789..."
echo "  Control UI: http://127.0.0.1:18789/"
echo "  EVEZ Space: https://preview-evez-openclaw-70c67950.viktor.space"
exec openclaw gateway --port 18789 --allow-unconfigured
