#!/usr/bin/env bash
set -euo pipefail
echo "🚀 EVEZ-OS Oracle Cloud Deploy"
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl git
curl -fsSL https://raw.githubusercontent.com/openclaw/openclaw/main/install.sh | bash
git clone https://github.com/EVEZX/evez-openclaw-infra.git /tmp/infra
cd /tmp/infra && bash migrate-local.sh
echo "✅ Done"
