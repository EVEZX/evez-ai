#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
# EVEZ-OS Migration Script — One command, full migration
# Usage: bash migrate.sh <VULTR_IP> <SSH_KEY_PATH>
# Or run locally: bash migrate.sh
# ═══════════════════════════════════════════════════════════════
set -euo pipefail

VULTR_IP="${1:-}"
SSH_KEY="${2:-$HOME/.ssh/id_ed25519}"
MIGRATE_USER="openclaw"
REMOTE_DIR="/tmp/evez-migration"

echo "🚀 EVEZ-OS Migration Script"
echo "============================"

if [ -z "$VULTR_IP" ]; then
  echo "📦 Local mode — packing migration bundle"
  tar -czf evez-migration-bundle.tar.gz -C "$(dirname "$0")" .
  echo "✅ Bundle: $(pwd)/evez-migration-bundle.tar.gz"
  echo ""
  echo "To deploy on a new VPS:"
  echo "  1. scp evez-migration-bundle.tar.gz newhost:/tmp/"
  echo "  2. ssh newhost 'cd /tmp && tar -xzf evez-migration-bundle.tar.gz && bash migrate-local.sh'"
  exit 0
fi

echo "📡 Connecting to current Vultr host: $VULTR_IP"
echo "📦 Packing and transferring migration bundle..."

# Transfer the migration pack to the new host
ssh -i "$SSH_KEY" "${MIGRATE_USER}@${VULTR_IP}" "mkdir -p ${REMOTE_DIR}"
scp -i "$SSH_KEY" "$(dirname "$0")"/* "${MIGRATE_USER}@${VULTR_IP}:${REMOTE_DIR}/"

echo "✅ Migration pack transferred"
echo ""
echo "Next: On the NEW host, run:"
echo "  cd ${REMOTE_DIR} && bash migrate-local.sh"
