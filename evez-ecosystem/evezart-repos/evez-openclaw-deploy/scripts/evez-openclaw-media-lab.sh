#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export OPENCLAW_MEDIA_DIR="${OPENCLAW_MEDIA_DIR:-${OPENCLAW_STATE_DIR:-$HOME/.openclaw}/media}"
exec python3 "$ROOT/workspace/tools/evez-media-lab.py" "$@"
