# Nonlocal Linux/Ubuntu OpenClaw Matrix

This repo can now run the real upstream OpenClaw gateway/control runtime on multiple nonlocal Linux environments, with the same EVEZ workspace, provider keys, Telegram allowlist, Lobster/Clawdhub tooling, and gateway token wiring.

## Surfaces included

| Surface | Runtime | Default host port | Purpose |
|---|---:|---:|---|
| Docker matrix | Ubuntu 24.04 | `18789` | Primary nonlocal Linux runtime |
| Docker matrix | Ubuntu 22.04 | `18790` | Older LTS compatibility runtime |
| Docker matrix | Debian 12 slim | `18791` | Generic Linux compatibility runtime |
| Remote SSH bootstrap | Any Ubuntu/Debian VPS with SSH | same as above | Uploads this kit, installs Docker, starts the matrix |
| Cloud-init | Ubuntu 24.04 VPS | same as above | One-shot VPS bring-up from user-data |

## Fast start on any Linux host

```bash
cp .env.example .env
openssl rand -hex 32   # paste into OPENCLAW_GATEWAY_TOKEN
# add GROQ_API_KEY, GITHUB_TOKEN/GH_TOKEN, TELEGRAM_BOT_TOKEN, OPENCLAW_TELEGRAM_ALLOW_FROM, CK_TOKEN if applicable
./scripts/evez-openclaw-linux-matrix.sh up
./scripts/evez-openclaw-linux-matrix.sh doctor
```

Dashboard URLs:

- Ubuntu 24.04: `http://<host>:18789/`
- Ubuntu 22.04: `http://<host>:18790/`
- Debian 12: `http://<host>:18791/`

Use the real upstream Control UI with:

```text
https://preview-evez-openclaw-70c67950.viktor.space/?gatewayUrl=ws://<host>:18789&token=<gateway-token>
```

Prefer Tailscale, WireGuard, or SSH tunnels for admin access. Do not expose the gateway to the open internet without a reverse proxy and access control.

## Remote Ubuntu/VPS bootstrap

```bash
./scripts/evez-openclaw-remote-ubuntu.sh --host user@your-vps --sync-env
```

`--sync-env` copies local `.env` to the remote with mode `600`. Omit it if you prefer to create `.env` manually on the server.

## Credential wiring

- `OPENCLAW_GATEWAY_TOKEN` is the real gateway/control token.
- `OPENCLAW_URL`/`OPENCLAW_TOKEN` are exported for Lobster `openclaw.invoke` and `llm.invoke --provider openclaw`.
- `CLAWD_URL`/`CLAWD_TOKEN` remain available for backwards-compatible Clawd/Lobster integrations.
- `CK_TOKEN`/`EVEZ_CK_TOKEN` are persisted as generic `ck_...` credentials for workflows that need them. ClawHub CLI currently expects `clh_...`; a tested `ck_...` token was rejected there, so this kit does not pretend it is a valid ClawHub login.
- `GITHUB_TOKEN` and `GH_TOKEN` both feed GitHub inventory/tools.
- Provider keys are written into OpenClaw `auth-profiles.json` at runtime, never into git.

## Health checks

```bash
./scripts/evez-openclaw-linux-matrix.sh status
./scripts/evez-openclaw-linux-matrix.sh doctor
./scripts/evez-openclaw-linux-matrix.sh logs openclaw-ubuntu-2404
```

The doctor checks gateway WebSocket health and verifies the Lobster → OpenClaw HTTP tool bridge with `agents_list` without printing secrets.
