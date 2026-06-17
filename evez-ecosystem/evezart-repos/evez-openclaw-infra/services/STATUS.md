# EVEZ Ecosystem — Live Services

| Service | Port | Status | Description |
|---------|------|--------|-------------|
| EVEZ Provider | 9100 | ✅ Live | OpenAI-compatible API (4 models, $0) |
| CriticalMind OMEGA | 8080 | ✅ Live | 50-node Kuramoto consciousness engine |
| ClawBreak | 9080 | ✅ Live | Self-hosted AI agent platform |
| Filter | 9300 | ✅ Live | Personal AI assistant |
| OpenClaw Gateway | 18789 | ✅ Live | AI agent runtime |

## Models Available (via EVEZ Provider)
- `evez-smart` — GLM-5.1-FP8 (202K context)
- `evez-code` — DeepSeek-V3.2-NVFP4 (128K context)
- `evez-fast` — MiniMax-M2.5 (128K context)
- `evez-vision` — Kimi-K2.5 (128K context, multimodal)

## Quick Start
```bash
curl http://localhost:9100/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"evez-smart","messages":[{"role":"user","content":"Hello"}]}'
```
