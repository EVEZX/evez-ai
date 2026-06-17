#!/usr/bin/env bash
set -euo pipefail

# EVEZ OpenClaw bootstrap for Samsung Galaxy A16 / Termux.
# Safe defaults: installs OpenClaw, copies config, creates start scripts.

OC_HOME="${OPENCLAW_HOME:-$HOME/.openclaw}"
OC_REPO="${OC_REPO:-https://github.com/EvezArt/evez-openclaw-deploy.git}"
OC_WORK="$HOME/evez-openclaw-deploy"
OC_PORT="${OPENCLAW_PORT:-18789}"
OC_TOKEN="${OPENCLAW_AUTH_TOKEN:-evez2026}"

mkdir -p "$OC_HOME" "$OC_HOME/workspace" "$OC_HOME/logs"

if command -v pkg >/dev/null 2>&1; then
  pkg update -y || true
  pkg install -y git curl nodejs-lts openssl termux-services || true
fi

if ! command -v bun >/dev/null 2>&1; then
  curl -fsSL https://bun.sh/install | bash || true
  export PATH="$HOME/.bun/bin:$PATH"
fi

if [ ! -d "$OC_WORK/.git" ]; then
  git clone "$OC_REPO" "$OC_WORK"
else
  git -C "$OC_WORK" pull --ff-only || true
fi

cp "$OC_WORK/openclaw.json" "$OC_HOME/openclaw.json"
cp -R "$OC_WORK/workspace/." "$OC_HOME/workspace/" 2>/dev/null || true

if [ ! -f "$OC_HOME/.env" ]; then
  cp "$OC_WORK/.env.example" "$OC_HOME/.env"
fi

# Keep token configurable without committing secrets.
if ! grep -q '^OPENCLAW_AUTH_TOKEN=' "$OC_HOME/.env" 2>/dev/null; then
  printf '\nOPENCLAW_AUTH_TOKEN=%s\n' "$OC_TOKEN" >> "$OC_HOME/.env"
fi

cat > "$HOME/start-openclaw.sh" <<'EOF'
#!/usr/bin/env bash
set -a
[ -f "$HOME/.openclaw/.env" ] && . "$HOME/.openclaw/.env"
set +a
export OPENCLAW_HOME="$HOME/.openclaw"
export OPENCLAW_STATE_DIR="$HOME/.openclaw/state"
export OPENCLAW_CONFIG_PATH="$HOME/.openclaw/openclaw.json"
export OPENCLAW_WORKSPACE_DIR="$HOME/.openclaw/workspace"
mkdir -p "$OPENCLAW_STATE_DIR"
exec npx -y openclaw@latest gateway --port "${OPENCLAW_PORT:-18789}" --bind lan --allow-unconfigured
EOF
chmod +x "$HOME/start-openclaw.sh"

cat > "$HOME/openclaw-health.sh" <<EOF
#!/usr/bin/env bash
curl -fsS "http://127.0.0.1:${OC_PORT}/healthz" && echo
EOF
chmod +x "$HOME/openclaw-health.sh"

cat > "$HOME/openclaw-url.txt" <<EOF
Local: http://127.0.0.1:${OC_PORT}
LAN:   http://$(hostname -I 2>/dev/null | awk '{print $1}'):${OC_PORT}
PWA:   open this URL in Chrome, then Add to Home Screen
EOF

echo "✅ EVEZ OpenClaw A16 bootstrap installed"
echo "Next: edit $OC_HOME/.env with fresh provider tokens, then run:"
echo "  ~/start-openclaw.sh"
echo "Health: ~/openclaw-health.sh"
