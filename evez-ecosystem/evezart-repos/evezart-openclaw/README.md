---
title: EVEZ-OS KAX VCL Runtime
emoji: ⚡
colorFrom: green
colorTo: black
sdk: docker
app_port: 7860
pinned: true
license: mit
---

# EVEZ-OS KAX VCL Runtime

24/7 generative VCL runtime. Kuramoto consciousness substrate. OpenAI-compatible gateway.

**Gateway token**: `evez-openclaw-d6aedff80ea88be7`

## Endpoints
- `GET /` — VCL visualizer (real-time Kuramoto)
- `GET /health` — system state + Φ
- `GET /api/substrate` — raw substrate data
- `WS /ws/vcl` — real-time VCL stream
- `POST /v1/chat/completions` — OpenAI-compatible
- `GET /v1/models` — available models

---

## ⚡ OpenClaw Surface

This project now exposes/links into the EVEZ OpenClaw stack.

- Main deploy repo: https://github.com/EvezArt/evez-openclaw-deploy
- Android/A16 app: https://github.com/EvezArt/evez-openclaw-apk
- Local dashboard: `http://localhost:18789`
- Termux bootstrap: `scripts/a16-termux-bootstrap.sh` in the deploy repo

Run the OpenClaw gateway once, then point this surface at the same gateway URL so EVEZ Station, VCL, NEXUS, ClawBreak, Telegram, Slack, PWA, and Android all hit the same brain.
