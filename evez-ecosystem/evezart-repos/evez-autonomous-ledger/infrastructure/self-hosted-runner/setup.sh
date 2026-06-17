#!/usr/bin/env bash
# EvezArt Self-Hosted GitHub Actions Runner — One-Command Bootstrap
# Usage: GITHUB_TOKEN=ghp_xxx ./setup.sh [ORG] [RUNNER_NAME]
set -euo pipefail

ORG="${1:-EvezArt}"
RUNNER_NAME="${2:-$(hostname)}"
RUNNER_VERSION="2.321.0"
RUNNER_DIR="$HOME/actions-runner"

if [ -z "${GITHUB_TOKEN:-}" ]; then
  echo "ERROR: GITHUB_TOKEN env var is required (needs admin:org scope)"
  echo "Usage: GITHUB_TOKEN=ghp_xxx $0 [ORG] [RUNNER_NAME]"
  exit 1
fi

echo "==> Installing dependencies..."
sudo apt-get update -qq
sudo apt-get install -y -qq curl jq tar python3.11 python3-pip nodejs npm docker.io

echo "==> Downloading GitHub Actions Runner v${RUNNER_VERSION}..."
mkdir -p "$RUNNER_DIR" && cd "$RUNNER_DIR"
curl -sL "https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz" | tar xz

echo "==> Fetching registration token for org: ${ORG}..."
REG_TOKEN=$(curl -sX POST \
  -H "Authorization: token ${GITHUB_TOKEN}" \
  -H "Accept: application/vnd.github.v3+json" \
  "https://api.github.com/orgs/${ORG}/actions/runners/registration-token" \
  | jq -r .token)

if [ "$REG_TOKEN" = "null" ] || [ -z "$REG_TOKEN" ]; then
  echo "ERROR: Failed to get registration token. Check GITHUB_TOKEN permissions."
  exit 1
fi

echo "==> Configuring runner '${RUNNER_NAME}' for org '${ORG}'..."
./config.sh \
  --url "https://github.com/${ORG}" \
  --token "$REG_TOKEN" \
  --name "$RUNNER_NAME" \
  --labels "self-hosted,linux,x64,evez" \
  --unattended \
  --replace

echo "==> Installing as systemd service..."
sudo ./svc.sh install
sudo ./svc.sh start

echo ""
echo "Runner '${RUNNER_NAME}' is registered and running."
echo "To use it, set the org/repo variable:  RUNNER_LABEL=self-hosted"
echo "Workflows will automatically pick it up via: vars.RUNNER_LABEL"
