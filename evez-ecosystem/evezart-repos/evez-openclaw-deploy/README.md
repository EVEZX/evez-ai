# EVEZ OpenClaw Deploy

Real upstream OpenClaw Gateway + Control UI deployment kit for EVEZ.

This repo is configured to keep OpenClaw recoverable instead of losing gateway/channel state: host onboarding, gateway recovery, doctor checks, Docker/Fly surfaces, Telegram allowlisting, AgentVault connector profile staging, provider auth bootstrapping, ClawHub/Lobster workspace skills, EVEZ identity/repo ecosystem seeding, token rotation, and backup scripts.

## Current verified baseline

- Gateway mode: `local`
- Default port: `18789`
- Default bind: loopback for host installs, LAN for container/cloud surfaces
- Dashboard: upstream OpenClaw Control UI served by the Gateway at `/`
- Telegram allowlist: set `OPENCLAW_TELEGRAM_ALLOW_FROM` in local/private env when needed
- AgentVault connector profile: `agentvault-connector` v1.3.5 staged outside `openclaw.json` because OpenClaw rejects unknown config keys

## Fast host install / recovery

```bash
git clone https://github.com/EvezArt/evez-openclaw-deploy.git
cd evez-openclaw-deploy
cp .env.example .env
# Fill provider/channel keys when available.
./scripts/evez-openclaw-install-host.sh
```

Useful commands:

```bash
./scripts/evez-openclaw-recover.sh        # idempotent gateway recovery
./scripts/evez-openclaw-doctor.sh         # config + WS health + channel checks
./scripts/evez-openclaw-dashboard-link.sh # prints local/static Control UI links
./scripts/evez-openclaw-vault-rotate.sh   # rotate gateway token and recover
./scripts/evez-openclaw-backup-state.sh   # secret-excluding state backup
```

## Docker

```bash
cp .env.example .env
# Required for Docker/Control UI access:
# OPENCLAW_GATEWAY_TOKEN=<strong-token>
# Optional live channels/providers: TELEGRAM_BOT_TOKEN, GROQ_API_KEY, OPENROUTER_API_KEY, etc.
docker compose up -d --build
docker compose ps
```

## Fly.io

```bash
fly launch --config fly.toml
fly volumes create openclaw_data --region iad --size 1
fly secrets set OPENCLAW_GATEWAY_TOKEN=<strong-token> TELEGRAM_BOT_TOKEN=<telegram-token> GROQ_API_KEY=<groq-key> OPENROUTER_API_KEY=<openrouter-key>
fly deploy
```

The Fly image bakes in the repo config and copies it into `/data` on first boot, while keeping runtime state on the persistent volume.

## Keepalive

Linux systemd user service:

```bash
mkdir -p ~/.config/systemd/user
cp systemd/openclaw-gateway.service systemd/openclaw-token-rotate.service systemd/openclaw-token-rotate.timer ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now openclaw-gateway
systemctl --user enable --now openclaw-token-rotate.timer
```

macOS launchd:

```bash
mkdir -p ~/Library/LaunchAgents
cp launchd/com.evez.openclaw.gateway.plist launchd/com.evez.openclaw.rotate.plist ~/Library/LaunchAgents/
launchctl load -w ~/Library/LaunchAgents/com.evez.openclaw.gateway.plist
launchctl load -w ~/Library/LaunchAgents/com.evez.openclaw.rotate.plist
```

## Surface Deployments

OpenClaw is packaged for EVEZ surfaces:

- Desktop/server: Gateway + upstream Control UI
- Docker: recoverable container with state volume and WS healthcheck
- Fly.io: persistent `/data` volume config
- Galaxy A16: Termux bootstrap + Android/WebView/PWA links
- Channels: Telegram allowlist and Slack config slots
- EVEZ apps: EVEZ Station, evezart-openclaw, ClawBreak, NEXUS, and VCL link back to this gateway surface

See [SURFACES.md](SURFACES.md) and [ONBOARDING_RUNBOOK.md](ONBOARDING_RUNBOOK.md).

## Real OpenClaw Dashboard

This deployment uses the upstream OpenClaw Gateway dashboard / Control UI. See `REAL_OPENCLAW_DASHBOARD.md` and official docs:

- https://docs.openclaw.ai/web/dashboard
- https://docs.openclaw.ai/web/control-ui
- https://docs.openclaw.ai/cli/dashboard

Static Control UI preview:

```text
https://preview-evez-openclaw-70c67950.viktor.space/?gatewayUrl=ws://<gateway-host>:18789&token=<gateway-token>
```

## EVEZ ecosystem bootstrap

OpenClaw now starts with EVEZ identity/repo context and ClawHub/Lobster workflow skills in its workspace. See [EVEZ_ECOSYSTEM_BOOTSTRAP.md](EVEZ_ECOSYSTEM_BOOTSTRAP.md).

Refresh public repo context:

```bash
./scripts/evez-openclaw-ecosystem-sync.sh --public-only
```

If a local GitHub token is present and you want OpenClaw to know private repo metadata locally without committing it:

```bash
OPENCLAW_STATE_DIR=~/.openclaw ./scripts/evez-openclaw-ecosystem-sync.sh --include-private
```

## Telegram setup

Set `OPENCLAW_TELEGRAM_ALLOW_FROM` in `.env` or host env for private Telegram allowlisting when needed.

For a live Telegram bot:

1. Create/get bot token from BotFather.
2. Put it in `.env` or host env as `TELEGRAM_BOT_TOKEN=...`.
3. Run `./scripts/evez-openclaw-recover.sh`.
4. If Telegram asks for pairing, approve with `openclaw pairing approve telegram <code>`.

## AgentVault connector

See [AGENTVAULT_CONNECTOR.md](AGENTVAULT_CONNECTOR.md). The connector profile is copied to OpenClaw state as a sidecar file rather than embedded in `openclaw.json` so strict OpenClaw config validation remains valid.

## Built by Viktor AI for EVEZ
