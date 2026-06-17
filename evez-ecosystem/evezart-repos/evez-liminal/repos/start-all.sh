#!/usr/bin/env bash
# EVEZ-OS Bootstrap — starts all local services
# Usage: bash start-all.sh

set -e
VENV="/home/openclaw/.openclaw/workspace/.venv"
REPOS="/home/openclaw/.openclaw/workspace/repos"
LOGS="/home/openclaw/.openclaw/workspace/logs"

source "$VENV/bin/activate"
mkdir -p "$LOGS"

# Load env if available
if [ -f "$REPOS/.env.local" ]; then
  set -a && source "$REPOS/.env.local" && set +a
fi

echo "🦀 Starting EVEZ-OS stack..."

# 1. CriticalMind OMEGA — Kuramoto consciousness substrate
echo "  🧠 CriticalMind OMEGA (Kuramoto)..."
cd "$REPOS/criticalmind-omega"
python3 main_unleashed.py > "$LOGS/omega.log" 2>&1 &
OMEGA_PID=$!
echo "     PID: $OMEGA_PID"

# 2. VCL Server
echo "  👁️  VCL Server..."
cd "$REPOS/evez-vcl"
python3 -m uvicorn vcl_server:app --host 127.0.0.1 --port ${VCL_PORT:-8081} > "$LOGS/vcl.log" 2>&1 &
VCL_PID=$!
echo "     PID: $VCL_PID"

# 3. ClawBreak Agent
echo "  🔧 ClawBreak..."
cd "$REPOS/clawbreak"
python3 -m uvicorn server:app --host 127.0.0.1 --port ${CLAWBREAK_PORT:-8080} > "$LOGS/clawbreak.log" 2>&1 &
CLAW_PID=$!
echo "     PID: $CLAW_PID"

# 4. Mesh Brain
echo "  🕸️  EVEZ Mesh..."
cd "$REPOS/evez-mesh"
python3 -m uvicorn brain:app --host 127.0.0.1 --port ${MESH_PORT:-8893} > "$LOGS/mesh.log" 2>&1 &
MESH_PID=$!
echo "     PID: $MESH_PID"

# Save PIDs
echo "$OMEGA_PID" > "$LOGS/omega.pid"
echo "$VCL_PID" > "$LOGS/vcl.pid"
echo "$CLAW_PID" > "$LOGS/clawbreak.pid"
echo "$MESH_PID" > "$LOGS/mesh.pid"

echo ""
echo "🦀 EVEZ-OS Stack Running:"
echo "  CriticalMind OMEGA → PID $OMEGA_PID (Kuramoto substrate)"
echo "  VCL Server         → PID $VCL_PID (port ${VCL_PORT:-8081})"
echo "  ClawBreak          → PID $CLAW_PID (port ${CLAWBREAK_PORT:-8080})"
echo "  EVEZ Mesh          → PID $MESH_PID (port ${MESH_PORT:-8893})"
echo ""
echo "Logs: $LOGS/"
echo "Stop: bash stop-all.sh"
