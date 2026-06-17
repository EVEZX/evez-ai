# EvezOS Immortality Watchdog

The immortality watchdog supervises all core EvezBrain services:

- consciousness API
- mesh network
- memory graph
- reward loop
- emotion core

If any one crashes, it is restarted automatically with exponential backoff.

## Run locally

```bash
python core/tools/immortality_watchdog.py --config core/infra/evezbrain_services.json
```

Tunable knobs:

- `--base-backoff` initial restart delay in seconds (default `1`)
- `--max-backoff` cap for restart delay (default `60`)
- `--poll-interval` monitor loop cadence (default `1`)

## Whole-system resurrection

When the full stack is unavailable, `.github/workflows/immortality-redeploy.yml`
runs every 15 minutes and calls `scripts/redeploy_stack.sh` on the deployment host.
The script resets to the latest `stable` branch and re-runs Docker Compose for the
entire stack.

Required GitHub secrets for the redeploy job:

- `DEPLOY_HOST`
- `DEPLOY_USER`
- `DEPLOY_KEY` (private SSH key)
- `DEPLOY_PATH` (remote checkout directory)
