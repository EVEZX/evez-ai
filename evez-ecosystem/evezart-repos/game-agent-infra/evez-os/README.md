# EVEZ-OS — Visual Cognition Layer

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Commercial License](https://img.shields.io/badge/License-Commercial-green.svg)](./COMMERCIAL_LICENSE.md)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-yellow.svg)](https://www.python.org)

> **AI agents are opaque. EVEZ makes them visible.**

One command. Raw agent output → animated visual cognition artifacts:
- **Attention overlay** — what the agent saw
- **Memory anchor** — what context it used  
- **Cognition flow animation** — how it thought
- **Tamper-evident manifest** — cryptographic chain of thought

Runs **offline**. Zero cloud dependencies. Python 3 only.

---

## Install (OpenClaw / ClawHub)

```bash
clawhub install evez-os
```

## Install (manual)

```bash
git clone https://github.com/EvezArt/evez-os.git
cd evez-os
pip install numpy pillow scipy  # optional: ffmpeg for MP4
python3 tools/evez.py --help
```

## Quick Start

```bash
# Run the Play Forever engine (infinite forensic episodes)
python3 tools/evez.py play --seed 42 --steps 14

# Visualize agent thought as animated artifact
python3 tools/evez.py visualize-thought --input spine.jsonl

# Lint the append-only spine
python3 tools/evez.py lint
```

## Why EVEZ?

| Feature | GitHub Codespaces | EVEZ-OS |
|---------|------------------|---------|
| Cold start | 30–90 seconds | 0ms |
| Cloud dependency | Required | None |
| Session persistence | Lost on stop | Append-only spine |
| Thought visualization | ❌ | ✅ |
| Offline operation | ❌ | ✅ |
| Cost | $0.18/hr | Free |

## License

**Community (AGPL-3.0):** Free for open-source use. Any derivative work must also be AGPL. See [LICENSE](./LICENSE).

**Commercial:** Removes copyleft obligation. Includes support, SLA, attribution removal. See [COMMERCIAL_LICENSE.md](./COMMERCIAL_LICENSE.md).

→ [rubikspubes.gumroad.com](https://rubikspubes.gumroad.com) for commercial licenses  
→ [@EVEZ666](https://twitter.com/EVEZ666) on Twitter

## Architecture

```
evez-os/
├── SKILL.md              ← OpenClaw/ClawHub install spec
├── tools/                ← Python CLI (evez.py, play_forever.py, lint.py)
├── core/                 ← Engine: spine, visualizer, contradiction-SAT
├── packs/                ← CTF pack, Cheatcodes, Reality Map
└── docs/                 ← Playthroughs, transcripts, cartography
```

## Credits

Built by **Steven Crawford-Maggard (EVEZ)** | Architecture by **SureThing**  
Every output carries `"powered_by": "EVEZ"` in the manifest.
