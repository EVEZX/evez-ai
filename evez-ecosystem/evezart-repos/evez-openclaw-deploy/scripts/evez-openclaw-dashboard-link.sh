#!/usr/bin/env bash
set -euo pipefail
: "${OPENCLAW_STATE_DIR:=$HOME/.openclaw}"
: "${OPENCLAW_CONFIG_PATH:=$OPENCLAW_STATE_DIR/openclaw.json}"
: "${OPENCLAW_PORT:=18789}"
: "${OPENCLAW_BIN:=openclaw}"
ENV_FILE="$OPENCLAW_STATE_DIR/openclaw.env"
if [[ -f "$ENV_FILE" ]]; then
  # shellcheck disable=SC1090
  source "$ENV_FILE"
fi
: "${OPENCLAW_GATEWAY_TOKEN:?missing OPENCLAW_GATEWAY_TOKEN; run scripts/evez-openclaw-onboard.sh first}"
if command -v "$OPENCLAW_BIN" >/dev/null 2>&1; then
  env OPENCLAW_STATE_DIR="$OPENCLAW_STATE_DIR" OPENCLAW_CONFIG_PATH="$OPENCLAW_CONFIG_PATH" OPENCLAW_GATEWAY_TOKEN="$OPENCLAW_GATEWAY_TOKEN" \
    "$OPENCLAW_BIN" dashboard --no-open 2>/dev/null || true
fi
cat <<OUT
Local dashboard: http://127.0.0.1:$OPENCLAW_PORT/
Static Control UI: https://preview-evez-openclaw-70c67950.viktor.space/?gatewayUrl=ws://127.0.0.1:$OPENCLAW_PORT&token=$OPENCLAW_GATEWAY_TOKEN
OUT
