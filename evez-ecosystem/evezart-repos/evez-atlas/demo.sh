#!/bin/bash

set -e

echo "🧠 Atlas v3 Kernel Demo - Starting in 3 seconds..."
sleep 3

echo ""
echo "=== PHASE 1: Installing Dependencies ==="
if ! command -v npm &> /dev/null; then
    echo "❌ npm not found. Install Node.js first: https://nodejs.org"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "❌ python3 not found. Install Python 3.11+"
    exit 1
fi

echo "Installing Node packages..."
npm install --quiet

echo "Installing Python packages..."
pip3 install -r fsc/requirements.txt --quiet

echo ""
echo "=== PHASE 2: Testing Recursion Loop ==="
echo "Running dry-run recursion (generates 3 hypotheses)..."
ATLAS_TARGET=Evez666 ATLAS_INVARIANTS='coverage>0.8,no_blind_spots' npm run atlas:recursion 2>&1 | head -n 50

echo ""
echo "✅ Recursion loop executed successfully!"
echo ""
echo "=== PHASE 3: Starting HTTP Spine Server ==="
echo "Starting spine on port 7777 (background)..."
npm run atlas:spine:http > spine.log 2>&1 &
SPINE_PID=$!

echo "Waiting for spine to initialize..."
sleep 3

if ! curl -s http://localhost:7777/events > /dev/null; then
    echo "❌ Spine failed to start. Check spine.log"
    kill $SPINE_PID 2>/dev/null || true
    exit 1
fi

echo "✅ Spine server running at http://localhost:7777"
echo ""
echo "=== PHASE 4: Running FSC Experiment ==="
echo "Testing failure-surface cartography..."
ATLAS_URL=http://localhost:7777 python3 fsc/runner.py demo_model

echo ""
echo "=== PHASE 5: Verifying Spine Integrity ==="
INTEGRITY=$(curl -s http://localhost:7777/verify)
echo "Integrity check: $INTEGRITY"

echo ""
echo "=== PHASE 6: Viewing Projections ==="
echo "Atlas projection:"
curl -s http://localhost:7777/projections/atlas | jq -r '.events[0:3][] | "  - \(.kind) at \(.timestamp)"' 2>/dev/null || echo "  (No atlas events yet)"

echo ""
echo "FSC projection:"
curl -s http://localhost:7777/projections/fsc | jq -r '.events[0:3][] | "  - \(.kind): prune_ratio=\(.payload.prune_ratio // "N/A")"' 2>/dev/null || curl -s http://localhost:7777/projections/fsc | head -n 10

echo ""
echo "=== 🎉 DEMO COMPLETE ==="
echo ""
echo "Atlas v3 is now running! Try these commands:"
echo ""
echo "  curl http://localhost:7777/events           # View all events"
echo "  curl http://localhost:7777/projections      # Aggregate view"
echo "  curl http://localhost:7777/verify           # Check integrity"
echo ""
echo "  python3 fsc/runner.py my_model              # Run FSC experiment"
echo ""
echo "To stop the spine server:"
echo "  kill $SPINE_PID"
echo ""
echo "Logs available at: ./spine.log"
echo ""
echo "✅ System operational. Spine PID: $SPINE_PID"
