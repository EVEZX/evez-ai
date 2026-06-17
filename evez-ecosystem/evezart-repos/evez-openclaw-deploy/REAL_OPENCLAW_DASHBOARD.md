# Real OpenClaw Dashboard

This repo is wired around the upstream OpenClaw Gateway dashboard / Control UI — not a custom dashboard.

Authoritative OpenClaw docs:
- https://docs.openclaw.ai/web/dashboard
- https://docs.openclaw.ai/web/control-ui
- https://docs.openclaw.ai/cli/dashboard
- https://docs.openclaw.ai/gateway/tailscale

## Local dashboard

```bash
openclaw gateway --port 18789 --allow-unconfigured
openclaw dashboard --no-open
```

Open the tokenized URL printed by `openclaw dashboard`, or open:

```text
http://127.0.0.1:18789/
```

If the UI asks for auth, paste the gateway token from `openclaw dashboard` or `gateway.auth.token`.

## Remote/static Control UI

OpenClaw docs state the Control UI is static and the WebSocket target is configurable:

```text
https://preview-evez-openclaw-70c67950.viktor.space/?gatewayUrl=ws://<gateway-host>:18789&token=<gateway-token>
```

Use `wss://` when the gateway is behind HTTPS/Tailscale Serve.

## Samsung Galaxy A16

Use the APK wrapper or browser against the real Gateway dashboard URL:

```text
http://127.0.0.1:18789/
http://<LAN-IP>:18789/
https://<tailscale-magicdns>/
```

## Security

OpenClaw docs call the Control UI an admin surface. Prefer localhost, SSH tunnel, or Tailscale Serve; do not expose it publicly without auth.
