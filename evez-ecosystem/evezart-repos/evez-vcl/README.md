# EVEZ Visual Cognition Layer

> Perceptual Reasoning Artifacts for Agent Trust, Audit & Education

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)

## What is this?

EVEZ generates **visual cognition artifacts** from AI agent interactions — making agent reasoning visible, auditable, and trustworthy.

| Artifact | What It Shows | Format |
|----------|--------------|--------|
| **Seed Memory Anchor** | Stable memory state burned into pixels | PNG |
| **Attention Overlay** | What the agent paid attention to | PNG |
| **Cognition Flow** | Dynamic thought trace as animated flow field | MP4 |
| **Best Layout** | Compressed concept map — the "mind snapshot" | PNG |
| **Manifest** | Machine-readable provenance + metadata | JSON |

## Quick Start

```bash
pip install -r requirements.txt
python3 tools/evez.py init
python3 tools/run_all.py --seed --mode spicy
```

## Play Forever

```bash
python3 tools/evez.py play --loop --steps 14
```

The game can't end because the attack surface can't end.

## Who This Is For

- **AI Safety teams** — attention traces for alignment review
- **Education** — visual reasoning for teaching
- **Enterprise** — audit artifacts for compliance
- **Product teams** — trust UX for end users

## Deployment

Runs fully offline. Zero cloud dependencies. Python 3.10+.

| Option | Model | Best For |
|--------|-------|----------|
| Self-hosted | License | Air-gapped / on-prem / regulated |
| SaaS | Per-seat | Teams wanting managed infrastructure |
| Embedded | OEM | Building into your own product |

## Commercial License

This software is dual-licensed:

- **Community:** [AGPL-3.0](LICENSE) — free, copyleft, attribution required
- **Commercial:** Removes copyleft obligations — [contact for pricing](mailto:rubikspubes69@gmail.com)

Enterprise licenses, pilot packages, and integration support available.

📧 rubikspubes69@gmail.com
🐦 [@EVEZ666](https://twitter.com/EVEZ666)
🛒 [rubikspubes.gumroad.com](https://rubikspubes.gumroad.com)

---

*Powered by EVEZ Visual Cognition Layer*
*© 2026 Steven Crawford-Maggard. All rights reserved.*

---

## ⚡ OpenClaw Surface

This project now exposes/links into the EVEZ OpenClaw stack.

- Main deploy repo: https://github.com/EvezArt/evez-openclaw-deploy
- Android/A16 app: https://github.com/EvezArt/evez-openclaw-apk
- Local dashboard: `http://localhost:18789`
- Termux bootstrap: `scripts/a16-termux-bootstrap.sh` in the deploy repo

Run the OpenClaw gateway once, then point this surface at the same gateway URL so EVEZ Station, VCL, NEXUS, ClawBreak, Telegram, Slack, PWA, and Android all hit the same brain.
