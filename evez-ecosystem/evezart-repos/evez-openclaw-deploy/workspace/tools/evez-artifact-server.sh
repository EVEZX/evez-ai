#!/usr/bin/env bash
set -euo pipefail
DIR="${1:-${OPENCLAW_MEDIA_DIR:-./media-out}}"
PORT="${2:-${OPENCLAW_ARTIFACT_PORT:-18888}}"
mkdir -p "$DIR"
cd "$DIR"
echo "Serving OpenClaw media artifacts from $PWD on http://0.0.0.0:$PORT/" >&2
exec python3 -m http.server "$PORT" --bind 0.0.0.0
