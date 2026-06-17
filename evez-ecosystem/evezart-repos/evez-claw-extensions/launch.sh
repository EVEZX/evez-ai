#!/bin/bash

echo "CriticalMind Launch Sequence"
echo "============================"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 not found"
    exit 1
fi

echo "✓ Python found: $(python3 --version)"

# Check dependencies
echo ""
echo "Checking dependencies..."
pip list | grep -E "numpy|scipy|playwright" > /dev/null
if [ $? -eq 0 ]; then
    echo "✓ Core dependencies installed"
else
    echo "Installing dependencies..."
    pip install -r requirements.txt
    playwright install chromium
fi

# Run demo
echo ""
echo "Launching demo..."
cd src
python3 demo_quick.py

echo ""
echo "Launch complete. Check demo_spine.json for event log."
