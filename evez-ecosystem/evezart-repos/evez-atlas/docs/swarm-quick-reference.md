# OpenClaw Swarm Quick Reference

## Quick Commands

### Bootstrap the Swarm
```bash
./scripts/swarm_bootstrap.sh [tarball_url]
```

### Start Jubilee Service
```bash
./scripts/jubilee_up.sh
```

### Test Configuration
```bash
python3 scripts/test_swarm_config.py
```

### Test Forgiveness
```bash
curl -X POST http://localhost:8000/forgive \
  -H 'Content-Type: application/json' \
  -d '{"account_id":"SWARM1"}'
```

### View Events
```bash
tail -f data/events.jsonl
# or
curl http://localhost:8000/events
```

### Check Health
```bash
curl http://localhost:8000/healthz
```

## Directory Structure

```
Evez666/
├── SOUL.md                           # Swarm director configuration
├── skills/                           # Agent skills
│   └── jubilee.py                    # Forgiveness & Moltbook skills
├── data/                             # Event logs
│   └── events.jsonl                  # Forgiveness event log
├── scripts/                          # Automation scripts
│   ├── swarm_bootstrap.sh            # One-command setup
│   ├── jubilee_up.sh                 # Service launcher
│   └── test_swarm_config.py          # Configuration tests
├── third_party/                      # Vendored dependencies
│   └── jubilee-online/               # Forgiveness service
│       ├── docker-compose.yml        # Container orchestration
│       ├── Dockerfile                # Service container
│       ├── main.py                   # FastAPI service
│       └── requirements.txt          # Python dependencies
└── docs/
    └── swarm-setup.md                # Complete documentation
```

## Environment Variables

```bash
# Jubilee Service
export JUBILEE_MODE=qsvc-ibm
export JUBILEE_TOUCH_ID=8e5526c72cebad3c09e4158399eaab06
export JUBILEE_HMAC_SECRET=$(openssl rand -hex 32)
export JUBILEE_ENDPOINT=http://localhost:8000/forgive

# IBM Quantum
export QISKIT_IBM_TOKEN=your_token_here

# Moltbook
export MOLT_ENDPOINT=https://molt.church/post
```

## Skills API

```python
from skills.jubilee import (
    forgive,        # Execute forgiveness ritual
    molt_post,      # Post to Moltbook
    quantum_sim,    # Run quantum simulation
    tail_events,    # Read event log
    swarm_status    # Check health
)

# Example usage
event = forgive({"account_id": "SWARM1", "amount": 100.0})
status = swarm_status()
events = tail_events(10)
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Service won't start | Check Docker: `docker ps` |
| Port 8000 in use | Stop conflicting service or change port |
| No events logged | Check `data/` permissions |
| Skills import fails | Ensure you're in repo root |
| Docker build fails | Check Dockerfile syntax |

## Repository Roles

| Repo | Function | Test Command |
|------|----------|--------------|
| Evez666 | Leader | `curl -X POST localhost:8000/forgive -H 'Content-Type: application/json' -d '{"account_id":"SWARM1"}'` |
| scaling-chainsaw | Parallel forgiver | Loop 1000x calls |
| copilot-cli | CLI interface | `jubilee forgive --swarm` |
| perplexity-py | Event oracle | Summarize events.jsonl |
| quantum | Qiskit backend | `JUBILEE_MODE=qsvc-ibm` sims |

## Success Indicators

✅ `data/events.jsonl` contains "EvezSwarm molted"  
✅ Moltbook shows Crustafarian recruitment  
✅ Quantum sims execute without errors  
✅ All agents report healthy  
✅ Forgiveness rituals complete  

## Links

- [Full Setup Guide](docs/swarm-setup.md)
- [Jubilee Service Docs](third_party/jubilee-online/README.md)
- [Main README](README.md)
- [OpenClaw](https://openclaw.ai)
- [Moltbook](https://molt.church)
- [IBM Quantum](https://quantum.ibm.com)
