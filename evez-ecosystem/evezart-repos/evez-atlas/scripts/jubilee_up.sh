#!/usr/bin/env bash
#
# Jubilee Service Launcher
# Starts the Jubilee forgiveness service with IBM Quantum integration
#
# Usage: ./scripts/jubilee_up.sh
#

set -euo pipefail

# Color output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Navigate to Jubilee directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "${SCRIPT_DIR}")"
JUBILEE_DIR="${ROOT_DIR}/third_party/jubilee-online"

info "Starting Jubilee service..."

# Check if Jubilee directory exists
if [ ! -d "${JUBILEE_DIR}" ]; then
    error "Jubilee directory not found: ${JUBILEE_DIR}"
    error "Please run swarm_bootstrap.sh first to vendor Jubilee"
    exit 1
fi

# Generate HMAC secret if not set
if [ -z "${JUBILEE_HMAC_SECRET:-}" ]; then
    export JUBILEE_HMAC_SECRET=$(openssl rand -hex 32)
    warn "Generated new HMAC secret: ${JUBILEE_HMAC_SECRET}"
    warn "Set JUBILEE_HMAC_SECRET environment variable to persist"
fi

# Set Jubilee mode and touch ID
export JUBILEE_MODE="${JUBILEE_MODE:-qsvc-ibm}"
export JUBILEE_TOUCH_ID="${JUBILEE_TOUCH_ID:-8e5526c72cebad3c09e4158399eaab06}"

info "Configuration:"
info "  Mode: ${JUBILEE_MODE}"
info "  Touch ID: ${JUBILEE_TOUCH_ID}"
info "  HMAC Secret: ${JUBILEE_HMAC_SECRET:0:8}..."

# Check for Docker
if ! command -v docker &> /dev/null; then
    error "Docker is not installed"
    exit 1
fi

# Check for docker-compose
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    error "Docker Compose is not installed"
    exit 1
fi

# Change to Jubilee directory
cd "${JUBILEE_DIR}"

# Build and start services
info "Building and starting Docker containers..."
if docker compose version &> /dev/null; then
    docker compose up -d --build
else
    docker-compose up -d --build
fi

# Wait for service to be ready
info "Waiting for service to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:8000/healthz > /dev/null 2>&1; then
        info "✓ Jubilee service is ready!"
        info ""
        info "Service endpoints:"
        info "  Health: http://localhost:8000/healthz"
        info "  Forgive: http://localhost:8000/forgive"
        info ""
        info "Test forgiveness:"
        info "  curl -X POST http://localhost:8000/forgive -H 'Content-Type: application/json' -d '{\"account_id\":\"SWARM1\"}'"
        exit 0
    fi
    sleep 1
done

warn "Service did not become ready in 30 seconds"
warn "Check logs with: docker compose logs -f"
exit 1
