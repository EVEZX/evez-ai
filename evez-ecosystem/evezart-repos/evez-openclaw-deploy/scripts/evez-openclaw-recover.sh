#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
: "${OPENCLAW_STATE_DIR:=$HOME/.openclaw}"
: "${OPENCLAW_CONFIG_PATH:=$OPENCLAW_STATE_DIR/openclaw.json}"
: "${OPENCLAW_PORT:=18789}"
: "${OPENCLAW_BIND:=loopback}"
: "${OPENCLAW_BIN:=openclaw}"
"$ROOT/scripts/evez-openclaw-onboard.sh" >/dev/null
ENV_FILE="$OPENCLAW_STATE_DIR/openclaw.env"
# shellcheck disable=SC1090
source "$ENV_FILE"
LOG="$OPENCLAW_STATE_DIR/logs/gateway-recover.log"
PIDFILE="$OPENCLAW_STATE_DIR/run/gateway.pid"
if env OPENCLAW_STATE_DIR="$OPENCLAW_STATE_DIR" OPENCLAW_CONFIG_PATH="$OPENCLAW_CONFIG_PATH" OPENCLAW_GATEWAY_TOKEN="${OPENCLAW_GATEWAY_TOKEN:-}" "$OPENCLAW_BIN" gateway health --url "ws://127.0.0.1:$OPENCLAW_PORT" --token "${OPENCLAW_GATEWAY_TOKEN:-}" --timeout 5000 >/dev/null 2>&1; then
  echo "OpenClaw gateway already healthy on $OPENCLAW_PORT"
  exit 0
fi
if [[ -f "$PIDFILE" ]] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
  kill "$(cat "$PIDFILE")" 2>/dev/null || true
  sleep 2
fi
ENV_ARGS=(
  OPENCLAW_STATE_DIR="$OPENCLAW_STATE_DIR"
  OPENCLAW_CONFIG_PATH="$OPENCLAW_CONFIG_PATH"
  OPENCLAW_GATEWAY_TOKEN="$OPENCLAW_GATEWAY_TOKEN"
  TELEGRAM_BOT_TOKEN="${TELEGRAM_BOT_TOKEN:-}"
  SLACK_BOT_TOKEN="${SLACK_BOT_TOKEN:-}"
  SLACK_APP_TOKEN="${SLACK_APP_TOKEN:-}"
  GROQ_API_KEY="${GROQ_API_KEY:-}"
  OPENROUTER_API_KEY="${OPENROUTER_API_KEY:-}"
  GEMINI_API_KEY="${GEMINI_API_KEY:-}"
  GOOGLE_API_KEY="${GOOGLE_API_KEY:-}"
)
if [[ -n "${OPENCLAW_SKIP_CHANNELS:-}" ]]; then
  ENV_ARGS+=(OPENCLAW_SKIP_CHANNELS="$OPENCLAW_SKIP_CHANNELS" CLAWDBOT_SKIP_CHANNELS="$OPENCLAW_SKIP_CHANNELS")
fi
nohup env "${ENV_ARGS[@]}" \
  "$OPENCLAW_BIN" gateway --port "$OPENCLAW_PORT" --bind "$OPENCLAW_BIND" --token "$OPENCLAW_GATEWAY_TOKEN" \
  > "$LOG" 2>&1 &
echo $! > "$PIDFILE"
for i in $(seq 1 40); do
  if env OPENCLAW_STATE_DIR="$OPENCLAW_STATE_DIR" OPENCLAW_CONFIG_PATH="$OPENCLAW_CONFIG_PATH" OPENCLAW_GATEWAY_TOKEN="$OPENCLAW_GATEWAY_TOKEN" "$OPENCLAW_BIN" gateway health --url "ws://127.0.0.1:$OPENCLAW_PORT" --token "$OPENCLAW_GATEWAY_TOKEN" --timeout 5000 >/dev/null 2>&1; then
    echo "OpenClaw gateway healthy on http://127.0.0.1:$OPENCLAW_PORT/"
    exit 0
  fi
  sleep 1
done
echo "OpenClaw gateway did not become healthy. Last log lines:" >&2
tail -80 "$LOG" >&2 || true
exit 1
