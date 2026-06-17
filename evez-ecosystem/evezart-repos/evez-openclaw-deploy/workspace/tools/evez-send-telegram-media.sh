#!/usr/bin/env bash
set -euo pipefail
FILE="${1:-}"
CAPTION="${2:-OpenClaw media artifact}"
CHAT_ID="${TELEGRAM_CHAT_ID:-${OPENCLAW_TELEGRAM_ALLOW_FROM%%,*}}"
TOKEN="${TELEGRAM_BOT_TOKEN:-}"
[[ -n "$FILE" && -f "$FILE" ]] || { echo "Usage: TELEGRAM_BOT_TOKEN=... OPENCLAW_TELEGRAM_ALLOW_FROM=745... $0 path [caption]" >&2; exit 64; }
[[ -n "$TOKEN" ]] || { echo "ERROR: TELEGRAM_BOT_TOKEN missing" >&2; exit 64; }
[[ -n "$CHAT_ID" ]] || { echo "ERROR: TELEGRAM_CHAT_ID or OPENCLAW_TELEGRAM_ALLOW_FROM missing" >&2; exit 64; }
case "${FILE,,}" in
  *.jpg|*.jpeg|*.png|*.webp) METHOD=sendPhoto; FIELD=photo ;;
  *.mp4|*.mov|*.mkv|*.webm) METHOD=sendVideo; FIELD=video ;;
  *.mp3|*.wav|*.flac|*.m4a|*.ogg) METHOD=sendAudio; FIELD=audio ;;
  *) METHOD=sendDocument; FIELD=document ;;
esac
curl -fsS "https://api.telegram.org/bot${TOKEN}/${METHOD}" \
  -F "chat_id=${CHAT_ID}" \
  -F "caption=${CAPTION}" \
  -F "${FIELD}=@${FILE}" >/tmp/evez-telegram-send-response.json
python3 - <<'PY'
import json
r=json.load(open('/tmp/evez-telegram-send-response.json'))
print(json.dumps({'ok': bool(r.get('ok')), 'message_id': (r.get('result') or {}).get('message_id'), 'method': 'telegram_media_send'}, indent=2))
PY
