#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REMOTE=""
REMOTE_DIR="~/evez-openclaw-deploy"
SYNC_ENV=0
START=1
while [[ $# -gt 0 ]]; do
  case "$1" in
    --host) REMOTE="$2"; shift 2 ;;
    --dir) REMOTE_DIR="$2"; shift 2 ;;
    --sync-env) SYNC_ENV=1; shift ;;
    --no-start) START=0; shift ;;
    -h|--help)
      cat <<USAGE
Usage: $0 --host user@server [--dir ~/evez-openclaw-deploy] [--sync-env] [--no-start]

Bootstraps a nonlocal Ubuntu/Linux host over SSH:
  1. installs Docker Engine + Compose plugin when missing
  2. uploads this deploy kit
  3. optionally uploads local .env with mode 600 (--sync-env)
  4. starts the Ubuntu/Debian runtime matrix remotely
USAGE
      exit 0 ;;
    *) echo "Unknown arg: $1" >&2; exit 64 ;;
  esac
done
[[ -n "$REMOTE" ]] || { echo "ERROR: --host user@server is required" >&2; exit 64; }
TMP_TAR="$(mktemp)"
trap 'rm -f "$TMP_TAR"' EXIT
(
  cd "$ROOT"
  tar --exclude .git --exclude .env --exclude 'workspace/private' -czf "$TMP_TAR" .
)
ssh "$REMOTE" "mkdir -p $REMOTE_DIR"
scp "$TMP_TAR" "$REMOTE:$REMOTE_DIR/evez-openclaw-deploy.tgz" >/dev/null
ssh "$REMOTE" "cd $REMOTE_DIR && tar -xzf evez-openclaw-deploy.tgz && rm evez-openclaw-deploy.tgz && chmod +x scripts/*.sh"
if [[ "$SYNC_ENV" == "1" ]]; then
  [[ -f "$ROOT/.env" ]] || { echo "ERROR: --sync-env requested but local .env is missing" >&2; exit 64; }
  scp "$ROOT/.env" "$REMOTE:$REMOTE_DIR/.env" >/dev/null
  ssh "$REMOTE" "chmod 600 $REMOTE_DIR/.env"
fi
ssh "$REMOTE" <<'REMOTE_SH'
set -euo pipefail
if ! command -v docker >/dev/null 2>&1; then
  if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update
    sudo apt-get install -y ca-certificates curl gnupg
    sudo install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg || \
      curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    . /etc/os-release
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/${ID} ${VERSION_CODENAME} stable" | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    sudo usermod -aG docker "$USER" || true
  else
    echo "Docker missing and apt-get unavailable; install Docker manually." >&2
    exit 127
  fi
fi
REMOTE_SH
if [[ "$START" == "1" ]]; then
  ssh "$REMOTE" "cd $REMOTE_DIR && ./scripts/evez-openclaw-linux-matrix.sh up && ./scripts/evez-openclaw-linux-matrix.sh status"
else
  echo "Uploaded to $REMOTE:$REMOTE_DIR. Start remotely with: ./scripts/evez-openclaw-linux-matrix.sh up"
fi
