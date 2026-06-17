#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# EVEZ-OS RESURRECTION — Full cold-boot recovery (v2)
# 11 services, 5 model providers, 5 mini-APIs
# ═══════════════════════════════════════════════════════════════

SENSORS="/home/openclaw/.openclaw/workspace/evez-os-sensors"
LOG="/tmp/evez-resurrect.log"

echo "[$(date)] Resurrection v2 starting..." >> $LOG
sleep 15  # wait for network

SERVICES=(
  "openclaw_health.py|9091|health"
  "recursion_circuit.py --port 9092 --interval 30|9092|circuit"
  "intelligence_unit_ariel.py --port 9093|9093|ariel"
  "cognizer_fabric.py --port 9094 --ariel-url http://localhost:9093|9094|cognizer"
  "cognizer_cycler.py --port 9095 --interval 120|9095|cycler"
  "knowledge_graph.py --port 9096|9096|knowledge"
  "debate_engine.py --port 9097|9097|debate"
  "evolutionary_forge.py --port 9098|9098|forge"
  "api_scanner.py --port 9099 --ariel-url http://localhost:9093|9099|scanner"
  "dashboard.py --port 9100|9100|dashboard"
  "autonomous_daemon.py --interval 60||daemon"
  "github_push_daemon.py --port 9101|9101|push"
)

for entry in "${SERVICES[@]}"; do
  IFS='|' read -r script port name <<< "$entry"
  if ! pgrep -f "$name" > /dev/null 2>&1; then
    cd "$SENSORS"
    nohup python3 $script >> /tmp/evez-${name}.log 2>&1 &
    echo "[$(date)] Started $name on :${port:-internal} (PID $!)" >> $LOG
    sleep 2
  else
    echo "[$(date)] $name already running" >> $LOG
  fi
done

# Bootstrap Ariel providers
sleep 5
bash "$SENSORS/bootstrap_ariel.sh" >> $LOG 2>&1

echo "[$(date)] Resurrection complete — 11 services, 5 providers" >> $LOG
