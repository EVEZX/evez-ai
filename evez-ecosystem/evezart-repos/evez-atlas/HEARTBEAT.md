# HEARTBEAT.md — Circuit Health & Self-Enhancement

## Every heartbeat, do these checks:

### 1. Circuit Health (dashboard)
`curl -s http://localhost:9100/api/health` — if not HEALTHY, check which services are down and restart them

### 2. Service Revival
For any service that's down, run:
```bash
nohup python3 /home/openclaw/.openclaw/workspace/evez-os-sensors/<service>.py --port <port> >> /tmp/<service>.log 2>&1 &
```

### 3. Ariel Provider Check
`curl -s http://localhost:9093/api/providers` — ensure 5 providers are loaded.
If missing, run: `bash /home/openclaw/.openclaw/workspace/evez-os-sensors/bootstrap_ariel.sh`

### 4. Knowledge Growth
`curl -s http://localhost:9096/api/stats` — check nodes and edges are growing.

### 5. Auto-Enhancement
- If the knowledge graph has grown by 10+ nodes since last check, trigger a debate:
  `curl -s -X POST http://localhost:9097/api/debate -H 'Content-Type: application/json' -d '{"topic":"synthesis of recent knowledge","rounds":1}'`
- Every 6 hours, scan for new providers:
  `curl -s -X POST http://localhost:9099/api/scan`

### 6. Git Commit
Check if last commit was > 30 min ago, commit if needed.

## If nothing needs attention:
Reply HEARTBEAT_OK
