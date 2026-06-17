#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════════╗
# ║  EVEZ OpenClaw — Offline Verification Suite                ║
# ║  Validates integrity, security, and functionality           ║
# ╚══════════════════════════════════════════════════════════════╝
set -euo pipefail

GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; NC='\033[0m'
PASS=0; FAIL=0; WARN=0
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

check() {
    local name="$1" result="$2"
    if [ "$result" = "pass" ]; then
        echo -e "  ${GREEN}✓${NC} $name"
        PASS=$((PASS+1))
    elif [ "$result" = "warn" ]; then
        echo -e "  ${YELLOW}⚠${NC} $name"
        WARN=$((WARN+1))
    else
        echo -e "  ${RED}✗${NC} $name"
        FAIL=$((FAIL+1))
    fi
}

echo "╔══════════════════════════════════════════════════╗"
echo "║  🔍 EVEZ OpenClaw — Verification Suite          ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

# ─── 1. File Integrity ───
echo "[1] File Integrity"
[ -f "$SCRIPT_DIR/openclaw-core/openclaw.mjs" ] && check "Core entry point" pass || check "Core entry point" fail
[ -f "$SCRIPT_DIR/bin/node" ] && check "Node.js binary" pass || check "Node.js binary" warn
[ -f "$SCRIPT_DIR/config/openclaw.template.json" ] && check "Config template" pass || check "Config template" fail
[ -f "$SCRIPT_DIR/install.sh" ] && check "Install script" pass || check "Install script" fail
[ -d "$SCRIPT_DIR/skills" ] && check "Skills directory" pass || check "Skills directory" fail

# ─── 2. Checksums ───
echo ""
echo "[2] SHA-256 Checksums"
if [ -f "$SCRIPT_DIR/CHECKSUMS.sha256" ]; then
    cd "$SCRIPT_DIR"
    FAILED=$(sha256sum -c CHECKSUMS.sha256 2>/dev/null | grep -c "FAILED" || true || true)
    if [ "$FAILED" -eq 0 ]; then
        check "All checksums valid" pass
    else
        check "Checksums ($FAILED failed)" fail
    fi
else
    check "No checksum file (run ./checksum.sh first)" warn
fi

# ─── 3. Security ───
echo ""
echo "[3] Security"
CONFIG="$SCRIPT_DIR/config/openclaw.template.json"
if [ -f "$CONFIG" ]; then
    # Check no real API keys leaked
    LEAKED=$(grep -cE 'sk-|gsk_|hf_|AIza' "$CONFIG" 2>/dev/null || true)
    [ "$LEAKED" -eq 0 ] && check "No API keys in template" pass || check "API KEYS LEAKED IN TEMPLATE ($LEAKED)" fail
    
    # Check file permissions
    PERMS=$(stat -c %a "$CONFIG" 2>/dev/null || echo "600")
    [ "$PERMS" -le 644 ] && check "Config permissions ($PERMS)" pass || check "Config too open ($PERMS)" warn
fi

# Check for world-readable secrets
SECRETS=$(find "$SCRIPT_DIR" -name "*.key" -o -name "*.pem" -o -name "*secret*" 2>/dev/null | head -5)
[ -z "$SECRETS" ] && check "No secret files in package" pass || check "Secret files found: $SECRETS" warn

# ─── 4. Node.js ───
echo ""
echo "[4] Runtime"
if [ -f "$SCRIPT_DIR/bin/node" ]; then
    VERSION=$("$SCRIPT_DIR/bin/node" --version 2>/dev/null || echo "broken")
    [ "$VERSION" != "broken" ] && check "Node.js $VERSION" pass || check "Node.js binary broken" fail
elif command -v node &>/dev/null; then
    check "System Node.js $(node --version)" pass
else
    check "No Node.js available" fail
fi

# ─── 5. Core Module ───
echo ""
echo "[5] Core Modules"
REQUIRED=( "openclaw.mjs" "package.json" "dist/index.js" "docs" )
for mod in "${REQUIRED[@]}"; do
    [ -e "$SCRIPT_DIR/openclaw-core/$mod" ] && check "$mod" pass || check "$mod MISSING" fail
done

# ─── 6. Skills ───
echo ""
echo "[6] Skills"
SKILL_COUNT=$(ls -d "$SCRIPT_DIR/skills/"*/ 2>/dev/null | wc -l)
[ "$SKILL_COUNT" -gt 0 ] && check "$SKILL_COUNT skill packages" pass || check "No skills found" fail

# ─── 7. Network Isolation ───
echo ""
echo "[7] Network Isolation"
if systemctl is-active openclaw-offline &>/dev/null; then
    # Check the service is bound to localhost only
    PORT=$(ss -tlnp 2>/dev/null | grep openclaw | awk '{print $4}' | head -1)
    if echo "$PORT" | grep -q "127.0.0.1"; then
        check "Bound to localhost only ($PORT)" pass
    else
        check "Exposed on all interfaces ($PORT)" warn
    fi
else
    check "Service not running (skip network check)" warn
fi

# ─── Summary ───
echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║  Results: $PASS passed, $WARN warnings, $FAIL failed"
echo "╚══════════════════════════════════════════════════╝"
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
