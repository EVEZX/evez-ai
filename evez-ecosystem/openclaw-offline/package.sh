#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════════╗
# ║  EVEZ OpenClaw — Package Builder                           ║
# ║  Creates self-contained .tar.gz with SHA-256 checksums      ║
# ╚══════════════════════════════════════════════════════════════╝
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VERSION=$(cat "$SCRIPT_DIR/openclaw-core/package.json" 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin)['version'])" 2>/dev/null || echo "unknown")
TIMESTAMP=$(date -u +%Y%m%dT%H%M%SZ)
PKG_NAME="openclaw-offline-secure-${VERSION}-${TIMESTAMP}"
OUTPUT_DIR="${1:-/tmp}"

echo "╔══════════════════════════════════════╗"
echo "║  📦 Building OpenClaw Offline Package ║"
echo "╚══════════════════════════════════════╝"
echo "  Version:  $VERSION"
echo "  Output:   $OUTPUT_DIR/$PKG_NAME.tar.gz"
echo ""

# ─── Step 1: Generate checksums ───
echo "[1/4] Generating SHA-256 checksums..."
cd "$SCRIPT_DIR"
find . -type f ! -name "CHECKSUMS.sha256" ! -name "*.tar.gz" ! -path "*/node_modules/.cache/*" \
    | sort | xargs sha256sum > CHECKSUMS.sha256
echo "  ✓ $(wc -l < CHECKSUMS.sha256) files checksummed"

# ─── Step 2: Strip unnecessary files ───
echo "[2/4] Cleaning package..."
# Remove development artifacts
find . -name ".git" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true
find . -name ".DS_Store" -delete 2>/dev/null || true
echo "  ✓ Cleaned"

# ─── Step 3: Create archive ───
echo "[3/4] Creating tar.gz archive..."
mkdir -p "$OUTPUT_DIR"
cd "$(dirname "$SCRIPT_DIR")"
tar -czf "$OUTPUT_DIR/$PKG_NAME.tar.gz" \
    --exclude="*.tar.gz" \
    --exclude="CHECKSUMS.sha256" \
    "$(basename "$SCRIPT_DIR")"
SIZE=$(du -sh "$OUTPUT_DIR/$PKG_NAME.tar.gz" | cut -f1)
echo "  ✓ Archive: $SIZE"

# ─── Step 4: Generate archive checksum ───
echo "[4/4] Generating archive checksum..."
cd "$OUTPUT_DIR"
sha256sum "$PKG_NAME.tar.gz" > "$PKG_NAME.tar.gz.sha256"
ARCH_SHA=$(cat "$PKG_NAME.tar.gz.sha256" | awk '{print $1}')
echo "  ✓ SHA-256: $ARCH_SHA"

echo ""
echo "╔══════════════════════════════════════╗"
echo "║  ✅ Package built successfully       ║"
echo "╚══════════════════════════════════════╝"
echo ""
echo "  Archive:  $OUTPUT_DIR/$PKG_NAME.tar.gz"
echo "  SHA-256:  $ARCH_SHA"
echo ""
echo "  To install:"
echo "    tar xzf $PKG_NAME.tar.gz"
echo "    cd $(basename "$SCRIPT_DIR")"
echo "    chmod +x install.sh verify.sh"
echo "    sudo ./install.sh /opt/openclaw"
