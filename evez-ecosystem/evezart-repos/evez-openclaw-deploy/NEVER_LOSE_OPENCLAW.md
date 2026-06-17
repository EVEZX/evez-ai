# Never Lose OpenClaw Again

This repo now has an idempotent gateway onboarding/recovery path.

## One-command local recovery

```bash
./scripts/evez-openclaw-recover.sh
```

What it does:
- creates `~/.openclaw/openclaw.json` if missing
- creates a local gateway token if missing
- preserves channel/model secrets from `~/.openclaw/openclaw.env` (`TELEGRAM_BOT_TOKEN`, Slack tokens, Groq/OpenRouter/Gemini keys)
- copies the EVEZ OpenClaw workspace into `~/.openclaw/workspace`
- starts the real upstream OpenClaw Gateway and Control UI
- verifies real WebSocket gateway health with `openclaw gateway health`
- preserves Telegram allowlists via `OPENCLAW_TELEGRAM_ALLOW_FROM` when explicitly configured
- stages the AgentVault connector profile sidecar outside strict `openclaw.json`

## Dashboard

Use the gateway-served dashboard first:

```text
http://127.0.0.1:18789/
```

For a tokenized link:

```bash
openclaw dashboard --no-open
```

The Viktor Space preview is only the upstream static Control UI. It still needs a reachable real Gateway:

```text
https://preview-evez-openclaw-70c67950.viktor.space/?gatewayUrl=ws://<gateway-host>:18789&token=<gateway-token>
```

## Keepalive options

Linux user service:

```bash
mkdir -p ~/.config/systemd/user
cp systemd/openclaw-gateway.service systemd/openclaw-token-rotate.service systemd/openclaw-token-rotate.timer ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now openclaw-gateway
systemctl --user enable --now openclaw-token-rotate.timer
```

macOS launchd:

```bash
cp launchd/com.evez.openclaw.gateway.plist launchd/com.evez.openclaw.rotate.plist ~/Library/LaunchAgents/
launchctl load -w ~/Library/LaunchAgents/com.evez.openclaw.gateway.plist
launchctl load -w ~/Library/LaunchAgents/com.evez.openclaw.rotate.plist
```

Docker:

```bash
docker compose up -d
```

## Rules

- Do not commit gateway tokens or provider keys.
- Keep Control UI upstream: build from OpenClaw `ui/`, do not replace with custom dashboards.
- Treat `~/.openclaw/workspace` as memory; back it up/private-git it.
