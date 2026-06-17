# EVEZ OpenClaw Gateway Onboarding Runbook

Goal: a real upstream OpenClaw Gateway + Control UI that can be recovered without losing config.

## 1. Host prerequisites

- Node.js 24 LTS or any Node >= 22.12.0
- OpenClaw CLI/binary available as `openclaw`
- `curl`, `openssl` or Python 3
- Optional keepalive: systemd user service, launchd, or Docker

## 2. First boot / full recovery

```bash
cp .env.example .env
# Fill provider/channel keys if you want live LLMs or channels.
./scripts/evez-openclaw-install-host.sh
```

This creates:
- `~/.openclaw/openclaw.json`
- `~/.openclaw/openclaw.env` containing the local gateway token and durable provider/channel env values
- `~/.openclaw/workspace`
- `~/.openclaw/workspace/EVEZ_IDENTITY.md`
- `~/.openclaw/workspace/ecosystem/github-public-repos.json`
- verified Clawhub and Lobster workspace skills
- `~/.openclaw/agentvault-connector.json`
- running Gateway on `ws://127.0.0.1:18789`
- dashboard at `http://127.0.0.1:18789/`

## 3. Dashboard link

```bash
./scripts/evez-openclaw-dashboard-link.sh
```

## 4. Keepalive

Linux:

```bash
mkdir -p ~/.config/systemd/user
cp systemd/openclaw-gateway.service ~/.config/systemd/user/openclaw-gateway.service
cp systemd/openclaw-token-rotate.service ~/.config/systemd/user/openclaw-token-rotate.service
cp systemd/openclaw-token-rotate.timer ~/.config/systemd/user/openclaw-token-rotate.timer
systemctl --user daemon-reload
systemctl --user enable --now openclaw-gateway
systemctl --user enable --now openclaw-token-rotate.timer
```

macOS:

```bash
mkdir -p ~/Library/LaunchAgents
cp launchd/com.evez.openclaw.gateway.plist ~/Library/LaunchAgents/
cp launchd/com.evez.openclaw.rotate.plist ~/Library/LaunchAgents/
launchctl load -w ~/Library/LaunchAgents/com.evez.openclaw.gateway.plist
launchctl load -w ~/Library/LaunchAgents/com.evez.openclaw.rotate.plist
```

Docker:

```bash
docker compose up -d
```

## 5. EVEZ ecosystem sync

Refresh public EvezArt repo context:

```bash
./scripts/evez-openclaw-ecosystem-sync.sh --public-only
```

If `GITHUB_TOKEN` or `GH_TOKEN` is available locally, build a private local-only visible repo inventory:

```bash
./scripts/evez-openclaw-ecosystem-sync.sh --include-private
```

The private inventory is written under `~/.openclaw/workspace/private/` and is git-ignored.

## 6. Verify

```bash
./scripts/evez-openclaw-doctor.sh
openclaw gateway health --url ws://127.0.0.1:18789 --token "$(sed -n 's/^OPENCLAW_GATEWAY_TOKEN=//p' ~/.openclaw/openclaw.env)"
```

## 7. Rotate gateway token

```bash
./scripts/evez-openclaw-vault-rotate.sh
```

## 8. Back up memory/workspace without secrets

```bash
./scripts/evez-openclaw-backup-state.sh
```

## 9. If anything breaks

```bash
./scripts/evez-openclaw-recover.sh
./scripts/evez-openclaw-doctor.sh
```

The recovery path is idempotent: rerun it as many times as needed.
