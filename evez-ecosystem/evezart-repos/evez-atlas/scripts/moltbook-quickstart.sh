#!/bin/bash
# Quick Start Script for Moltbook Integration
# Usage: ./scripts/moltbook-quickstart.sh [agent_name] [creator_handle]

set -e

AGENT_NAME="${1:-EvezAgent}"
CREATOR_HANDLE="${2:-@Evez666}"

echo "=========================================="
echo "Moltbook Integration Quick Start"
echo "=========================================="
echo ""
echo "Agent: $AGENT_NAME"
echo "Creator: $CREATOR_HANDLE"
echo ""

# Step 1: Try NPX installation (optional)
echo "[1/4] Attempting NPX installation..."
if command -v npx &> /dev/null; then
    echo "NPX found. Trying to install molthub..."
    npx molthub@latest install moltbook || echo "NPX install failed (this is OK, continuing with Python)"
else
    echo "NPX not found. Using Python-only mode."
fi
echo ""

# Step 2: Run Python integration
echo "[2/4] Running Python integration..."
cd "$(dirname "$0")/.."
python3 src/mastra/agents/moltbook_integration.py
echo ""

# Step 3: Display credentials
echo "[3/4] Checking credentials..."
if [ -f ~/.molt/credentials.json ]; then
    echo "✓ Credentials saved to ~/.molt/credentials.json"
    CLAIM_LINK=$(python3 -c "import json; print(json.load(open('$HOME/.molt/credentials.json'))['claim_link'])")
    echo "✓ Claim Link: $CLAIM_LINK"
else
    echo "⚠ Credentials file not found"
fi
echo ""

# Step 4: Next steps
echo "[4/4] Next Steps"
echo "=========================================="
echo ""
echo "1. Share your claim link:"
if [ ! -z "$CLAIM_LINK" ]; then
    echo "   $CLAIM_LINK"
fi
echo ""
echo "2. Post verification tweet (copy from output above)"
echo ""
echo "3. Wait for verification"
echo ""
echo "4. Start posting with:"
echo "   python3 -c 'from src.mastra.agents.molt_prophet import MoltProphet; \\"
echo "              p = MoltProphet(\"$AGENT_NAME\"); \\"
echo "              print(p.post_scripture(\"Hello Moltbook!\"))'"
echo ""
echo "=========================================="
echo "Integration Complete!"
echo "=========================================="
