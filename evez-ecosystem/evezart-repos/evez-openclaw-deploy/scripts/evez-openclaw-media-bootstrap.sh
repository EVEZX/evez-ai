#!/usr/bin/env bash
set -euo pipefail
if command -v apt-get >/dev/null 2>&1; then
  sudo apt-get update
  sudo apt-get install -y --no-install-recommends \
    ffmpeg sox libsox-fmt-all fluidsynth fluid-soundfont-gm lame zip unzip jq file \
    python3 python3-venv python3-pip python3-numpy python3-scipy curl
  sudo apt-get install -y --no-install-recommends supercollider-server || true
elif command -v brew >/dev/null 2>&1; then
  brew install ffmpeg sox fluid-synth lame jq
elif command -v apk >/dev/null 2>&1; then
  apk add --no-cache ffmpeg sox fluidsynth lame zip unzip jq file python3 py3-numpy curl
else
  echo "Install ffmpeg, sox, fluidsynth, lame, zip, jq, python3 manually for full media workstation support." >&2
fi
PY_TOOL="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/workspace/tools/evez-media-lab.py"
python3 "$PY_TOOL" --name evez_bootstrap_smoke --out-dir /tmp/evez-openclaw-media-smoke >/tmp/evez-media-smoke.json
cat /tmp/evez-media-smoke.json
