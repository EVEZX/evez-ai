---
name: evez-os
description: >
  Forensic game engine with immutable audit spine, FSC (Failure-Surface Compression),
  contradiction detection SAT solver, self-play loop, and visual cognition mapping.
  Runs offline. Zero dependencies beyond Python 3. ClawHub-ready.
version: 1.0.0
metadata:
  openclaw:
    requires:
      bins:
        - python3
    emoji: "\U0001F52C"
    homepage: https://github.com/EvezArt/evez-os
    os:
      - linux
      - macos
---

# EVEZ OS — Forensic Game Engine

> "The game can\'t end because the attack surface can\'t end."

A self-auditing forensic game engine that probes systems, detects contradictions,
maps failure surfaces, and generates infinite adversarial missions from its own traces.

## Quick Start

```bash
cd core
python3 tools/evez.py init
python3 tools/evez.py play --seed 42 --steps 14
```

## One-Command Demo

```bash
cd core && python3 tools/run_all.py --seed --mode spicy
```

## Play Forever

```bash
python3 tools/evez.py play --loop --steps 14
```

## Android (Termux)

```bash
pkg install python
git clone https://github.com/EvezArt/evez-os.git
cd evez-os/core
python tools/evez.py init
python tools/run_all.py --seed --mode spicy
```

Add to Termux:Boot for autorun — see ANDROID.md.

## All Commands

| Command | What It Does |
|---------|-------------|
| `evez.py init` | Initialize event + ARG spines |
| `evez.py play --seed N --steps N` | Generate forensic episode |
| `evez.py play --loop` | Infinite self-play |
| `evez.py cycle --ring R4 --anomaly "desc"` | Log FSC cycle |
| `evez.py lint` | Audit spine for violations |
| `evez.py arg-init` | Initialize ARG spine |
| `evez.py arg-narrate --tail N` | Narrate from spine tail |
| `evez.py trigger` | Auto-generate missions |
| `self_cartography.py` | Mermaid + DOT diagrams |
| `run_all.py --seed --mode spicy` | Full demo |

## Packs

- **CTF** (`packs/ctf/`) — 6 forensic challenges + contradiction engine (SAT solver)
- **Cheatcodes** (`packs/cheatcodes/`) — 5 cognitive debugging tools
- **Reality Map** (`packs/reality_map/`) — Architecture diagrams

## Truth Planes

- **PERCEPTION** — One vantage. Never trust alone.
- **PENDING** — Hypothesis with named falsifier. Default.
- **FINAL** — Passed falsifier gate from 2+ vantages.
- **CANON** — Community-verified, spine-logged.

## License

AGPL-3.0 — Community edition. Commercial license available.

## Author

Steven Crawford-Maggard (EVEZ) — @EVEZ666
