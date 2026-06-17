# Hermetic Console Operations (Local-Only)

## Run Steps

1) Deploy and start the causal chain server:

```bash
./scripts/deploy-all.sh
```

2) Start the local monitor server:

```bash
python tools/monitor_server.py --port 8001
```

3) Open the forwarded port 8001 in your browser and use the console.

4) Run the audit analyzer against the local API:

```bash
python tools/audit_analyzer.py --api-key tier3_director --api-base http://localhost:8000
```

## Notes

- The hermetic console is local-only and uses in-memory identity seeds.
- The audit analyzer writes outputs to `tools/out/` without contacting external services.
