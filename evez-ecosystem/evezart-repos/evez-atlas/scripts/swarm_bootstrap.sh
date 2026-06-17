#!/usr/bin/env bash
#
# OpenClaw Swarm Bootstrap Script
# Sets up the complete EvezArt repository swarm environment
#
# Usage: ./scripts/swarm_bootstrap.sh [tarball_url]
#

set -euo pipefail

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configuration
export WORK="${HOME}/evez-swarm"
REPOS=(scaling-chainsaw copilot-cli perplexity-py quantum Evez666)
TARBALL_URL="${1:-}"

info "Starting OpenClaw Swarm Bootstrap..."
info "Work directory: ${WORK}"

# Create work directory
mkdir -p "${WORK}"
cd "${WORK}"

# Clone or initialize repositories
info "Cloning/initializing repositories..."
for repo in "${REPOS[@]}"; do
    if [ -d "${repo}" ]; then
        warn "Repository ${repo} already exists, skipping..."
    else
        if git clone "https://github.com/EvezArt/${repo}.git" 2>/dev/null; then
            info "Cloned ${repo}"
        else
            warn "Could not clone ${repo}, initializing empty repo..."
            git init "${repo}"
        fi
    fi
done

# Handle Jubilee vendoring if tarball URL provided
if [ -n "${TARBALL_URL}" ]; then
    info "Downloading and vendoring Jubilee..."
    
    # Download tarball
    if wget -O jubilee.tgz "${TARBALL_URL}" 2>/dev/null || curl -L -o jubilee.tgz "${TARBALL_URL}"; then
        info "Downloaded Jubilee tarball"
        
        # Vendor into each repository
        for repo in "${REPOS[@]}"; do
            info "Vendoring Jubilee into ${repo}..."
            mkdir -p "${repo}/third_party/jubilee-online"
            tar -xzf jubilee.tgz --strip=1 -C "${repo}/third_party/jubilee-online/" 2>/dev/null || true
            
            # Update .gitignore
            {
                echo ""
                echo "# Jubilee"
                echo "third_party/jubilee-online/data/"
                echo "third_party/jubilee-online/**/__pycache__/"
            } >> "${repo}/.gitignore"
            
            info "Vendored into ${repo}"
        done
        
        info "Jubilee vendoring complete!"
        info "To commit: git -C Evez666 add . && git commit -m 'Swarm v3'"
    else
        warn "Could not download tarball from ${TARBALL_URL}"
        warn "You can manually place jubilee.tgz in ${WORK} and re-run"
    fi
else
    info "No tarball URL provided, skipping Jubilee vendoring"
    info "To vendor later, run: $0 <tarball_url>"
fi

# Setup directory structure in each repo
info "Setting up directory structure..."
for repo in "${REPOS[@]}"; do
    mkdir -p "${repo}/skills" "${repo}/data"
done

# Copy SOUL.md and skills to repos if in Evez666
if [ -f "${WORK}/Evez666/SOUL.md" ] && [ -f "${WORK}/Evez666/skills/jubilee.py" ]; then
    info "Distributing SOUL.md and skills to repositories..."
    for repo in "${REPOS[@]}"; do
        if [ "${repo}" != "Evez666" ]; then
            cp "${WORK}/Evez666/SOUL.md" "${repo}/" 2>/dev/null || true
            cp "${WORK}/Evez666/skills/jubilee.py" "${repo}/skills/" 2>/dev/null || true
        fi
    done
fi

info ""
info "✓ Bootstrap complete!"
info ""
info "Next steps:"
info "1. Navigate to Evez666: cd ${WORK}/Evez666"
info "2. Install OpenClaw: curl -sSL https://openclaw.ai/install.sh | bash"
info "3. Launch swarm: openclaw --soul SOUL.md --skills jubilee,molt_post"
info "4. Start Jubilee service: ./scripts/jubilee_up.sh"
info ""
info "Repository locations:"
for repo in "${REPOS[@]}"; do
    info "  - ${WORK}/${repo}"
done
