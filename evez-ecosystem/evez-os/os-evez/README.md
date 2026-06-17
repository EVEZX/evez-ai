# OS-EVEZ

**OpenClaw + AutoClaw + EVEZOS + OpenGarden — unified Termux-first OS layer**

Creator: Steven Crawford-Maggard (EVEZ666)
Repo: github.com/EvezArt/evez-os
License: AGPL-3.0

---

## Quick Start (Termux)

```bash
# 1. Bootstrap (one-time)
bash scripts/termux_bootstrap.sh

# 2. Start everything
bash scripts/termux_start_all.sh

# 3. Demo flow (upload fixtures, enable scheduler, discover assets)
bash scripts/termux_demo.sh
```

Then open in browser:
- http://127.0.0.1:8080/arcade
- http://127.0.0.1:8080/market
- http://127.0.0.1:8080/public-key.html
- http://127.0.0.1:8080/assets/map.html

---

## Architecture

```
scripts/
  termux_bootstrap.sh   # one-time setup
  termux_start_all.sh   # tmux session: redis | api | worker | scheduler | speeddaemon | autoclaw
  termux_demo.sh        # demo: upload fixtures -> enable scheduler -> discover assets -> player sync
evezos/                 # spine.py, manifest.py, object_store.py, replay.py, verify.py, viz.py
opengarden/app/         # FastAPI server: /arcade /market /latest /free /maps /assets /players
openclaw/               # policy gate, tool runner, model client (server-side), CLI
openplanter/            # DAG scheduler + budgets
autoclaw/               # bounded loop scheduler + runner
tests/                  # pytest: chain, manifest, replay, signature, scope
```

## Safety

See SECURITY.md. Summary:
- Default-deny capabilities (FS_READ/WRITE/SHELL/NET_OUT)
- Kill switch: `touch $OG_DATA_DIR/STOP`
- Budgets: max_disk_mb, max_runs, retention_runs
- API keys: server-side only, never committed, never in browser/mobile

## Loop Control

```bash
# Enable scheduler (10-min interval, keep 80 runs, stop at 4GB)
curl -X POST http://127.0.0.1:8080/schedule \
  -H "Content-Type: application/json" \
  -d '"'"'{"enabled":true,"interval_seconds":600,"max_runs":1000000,"max_disk_mb":4096,"retention_runs":80}'"'"'

# Stop everything NOW
touch $OG_DATA_DIR/STOP
# or:
curl -X POST http://127.0.0.1:8080/schedule/stop
```
