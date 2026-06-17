# EvezArt Unified Process Mesh

The local "nervous system" of the EvezArt stack. Persistent credential vault, headless browser automation, Telegram command daemon, and systemd persistence layer.

## Architecture

```
[ Telegram Bot ]
      |
+-----+-----+
|           |
[Playwright] [SQLite Vault]
(automater_eye.py)  (nomad_vault.py)
      |
[Telegram Daemon]
(tele_cortex.py / tele_mesh_cortex.py)
      |
+-----+-----+-----+
|           |     |
evez-digital-twin  evez-mesh  project-nomad-evez
```

## Quick Start

```bash
# 1. Bootstrap everything
bash setup_mesh.sh

# 2. Seed credentials (once)
cd ~/evez_stack/evez-mesh
# Edit nomad_vault.py, uncomment save_config() lines, add real tokens
python3 nomad_vault.py

# 3. Test browser eye
python3 automater_eye.py

# 4. Test Telegram daemon
python3 tele_cortex.py

# 5. Install systemd service (Linux)
sudo cp evez_daemon.service /etc/systemd/system/
# Edit: replace YOUR_USER with your username
sudo systemctl enable evez_daemon
sudo systemctl start evez_daemon
sudo systemctl status evez_daemon
```

## Files

| File | Purpose |
|------|--------|
| `setup_mesh.sh` | One-command environment bootstrap |
| `nomad_vault.py` | Fernet-encrypted SQLite credential vault |
| `automater_eye.py` | Playwright persistent browser context |
| `tele_cortex.py` | Telegram command daemon |
| `tele_mesh_cortex.py` | Full mesh daemon (imports vault + browser) |
| `gateway_automation.py` | Headless browser gateway session |
| `evez_daemon.service` | systemd service definition |

## Telegram Commands

| Command | Action |
|---------|-------|
| `/status` | Mesh ONLINE check |
| `/compact` | Trigger mesh compaction |
| `/mesh_status` | Full mesh signal check |
| `/gateway_sync` | Headless browser pass |

## Synapse Integration

Once `evez-synapse-engine` is on GCP:

```bash
# Audit evez-os
curl -X POST $SYNAPSE_URL -H 'Content-Type: application/json' \
  -d '{"action": "audit_all", "repo": "EvezArt/evez-os", "ref": "main"}'

# Create telemetry issue in evez-mesh
curl -X POST $SYNAPSE_URL -H 'Content-Type: application/json' \
  -d '{"action": "create_issue", "repo": "EvezArt/evez-mesh", "title": "Mesh Status", "body": "Telemetry trace."}'
```
