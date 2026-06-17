#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
: "${OPENCLAW_STATE_DIR:=$HOME/.openclaw}"
: "${OPENCLAW_PORT:=18789}"
: "${OPENCLAW_BIND:=loopback}"
ENV_FILE="$OPENCLAW_STATE_DIR/openclaw.env"
mkdir -p "$OPENCLAW_STATE_DIR/run" "$OPENCLAW_STATE_DIR/logs"
NEW_TOKEN="$(openssl rand -hex 32 2>/dev/null || python3 - <<'PY'
import secrets
print(secrets.token_hex(32))
PY
)"
TMP="$ENV_FILE.tmp"
if [[ -f "$ENV_FILE" ]]; then
  grep -v '^OPENCLAW_GATEWAY_TOKEN=' "$ENV_FILE" > "$TMP" || true
else
  : > "$TMP"
fi
{
  echo "OPENCLAW_GATEWAY_TOKEN=$NEW_TOKEN"
  cat "$TMP"
  grep -q '^OPENCLAW_PORT=' "$TMP" || echo "OPENCLAW_PORT=$OPENCLAW_PORT"
  grep -q '^OPENCLAW_BIND=' "$TMP" || echo "OPENCLAW_BIND=$OPENCLAW_BIND"
  grep -q '^OPENCLAW_STATE_DIR=' "$TMP" || echo "OPENCLAW_STATE_DIR=$OPENCLAW_STATE_DIR"
  grep -q '^OPENCLAW_CONFIG_PATH=' "$TMP" || echo "OPENCLAW_CONFIG_PATH=$OPENCLAW_STATE_DIR/openclaw.json"
  grep -q '^OPENCLAW_WORKSPACE_DIR=' "$TMP" || echo "OPENCLAW_WORKSPACE_DIR=$OPENCLAW_STATE_DIR/workspace"
} > "$ENV_FILE"
rm -f "$TMP"
chmod 600 "$ENV_FILE"
PIDFILE="$OPENCLAW_STATE_DIR/run/gateway.pid"
if [[ -f "$PIDFILE" ]] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
  kill "$(cat "$PIDFILE")" 2>/dev/null || true
  sleep 2
fi
"$ROOT/scripts/evez-openclaw-recover.sh"
echo "OpenClaw gateway token rotated and gateway recovered. Token is stored in the local OpenClaw env file."
