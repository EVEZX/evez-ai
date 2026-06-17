#!/usr/bin/env bash
set -euo pipefail

echo "[postAttach] Starting OpenClaw + Atlas setup..."

if [ -f ".devcontainer/setup-openclaw.sh" ]; then
  chmod +x .devcontainer/setup-openclaw.sh || true
  echo "[postAttach] Running OpenClaw setup..."
  ./.devcontainer/setup-openclaw.sh || true
else
  echo "[postAttach] OpenClaw setup script not found; skipping."
fi

chmod +x .devcontainer/setup-atlas.sh

echo "[postAttach] Running Atlas setup..."
./.devcontainer/setup-atlas.sh

echo "[postAttach] Done."
