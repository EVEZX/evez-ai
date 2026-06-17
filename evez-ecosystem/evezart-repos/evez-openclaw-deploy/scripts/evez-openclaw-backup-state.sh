#!/usr/bin/env bash
set -euo pipefail
: "${OPENCLAW_STATE_DIR:=$HOME/.openclaw}"
: "${OPENCLAW_BACKUP_DIR:=$HOME/openclaw-backups}"
mkdir -p "$OPENCLAW_BACKUP_DIR"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="$OPENCLAW_BACKUP_DIR/openclaw-state-$STAMP.tgz"
tar \
  --exclude='openclaw.env' \
  --exclude='*.token' \
  --exclude='credentials' \
  --exclude='oauth.json' \
  -C "$(dirname "$OPENCLAW_STATE_DIR")" \
  -czf "$OUT" "$(basename "$OPENCLAW_STATE_DIR")"
chmod 600 "$OUT"
echo "$OUT"
