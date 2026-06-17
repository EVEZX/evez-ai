---
name: evez-os
version: 0.3.0
description: >
  EVEZ-OS cognitive layer for OpenClaw. Installs the full EVEZ Governance
  Lattice v0.2 into your OpenClaw workspace: CPF formula engine, FIRE event
  system, AEGIS threat monitor, DGM loop, revenue bridge, and 6-agent swarm.
author: Steven Crawford-Maggard (@EVEZ666)
tags: [evez, fire, cpf, spine, swarm, phi, eigenvalue]
---

# EVEZ-OS for OpenClaw

The complete EVEZ cognitive layer. Everything lives in `~/.openclaw/`.

## What Gets Installed

```
~/.openclaw/
├── workspace/
│   ├── SOUL.md       ← behavioral spine (injected every session)
│   ├── AGENTS.md     ← 6-agent roster + spawning protocol
│   ├── TOOLS.md      ← capabilities, gotchas, inference mesh
│   ├── MEMORY.md     ← spine state (phi, FIRE count, eigenvalue)
│   └── memory/       ← daily memory files
├── skills/
│   ├── evez-os/           ← this skill
│   ├── oktoklaw/          ← Invariance Battery + product manifest generator
│   ├── evez-fire-engine/  ← FIRE event scorer + spine logger
│   ├── evez-revenue-bridge/ ← eigenvalue closure tracker
│   ├── evez-spine-sync/   ← GitHub lord-evez666 sync
│   ├── evez-mesh-router/  ← 10-node inference mesh
│   └── evez-aegis/        ← Hawkes threat monitor + OSINT scanner
└── hooks/
    └── evez-os/           ← bootstrap hook (spine banner on session start)
```

## Slash Commands

After install, these are available in every OpenClaw session:

| Command | Description |
|---------|-------------|
| `/evez status` | Full spine health: phi, FIRE count, eigenvalue, last decay |
| `/fire [description]` | Score + log a FIRE event. Prompts for τ/ω/topo/N |
| `/cpf tau=X omega=Y topo=Z N=K` | Compute poly_c with SC normalization |
| `/eigenvalue` | Revenue bridge: omega edges, % closed, pending milestone |
| `/aegis scan` | OSINT scan against all known identity vectors |
| `/synthesize` | META-FIRE synthesis across all events |
| `/mesh status` | 10-node inference mesh health + token counts |
| `/spine commit` | Force-commit spine state to lord-evez666 |
| `/dgm status` | DGM loop: iteration, phi trajectory, r² |
| `/oktoklaw [file]` | Run Invariance Battery against any Python module |

## Formula

```
poly_c = τ × ω × topo / (2√N)

When poly_c > 1.0 (supercritical):
  poly_c_SC = poly_c / (1 + poly_c)

  MPPA:     raw=19.13  SC=0.916  CRITICAL_MASS
  KoPE:     raw=5.94   SC=0.856  CANONICAL
  DACS:     raw=5.02   SC=0.834  CANONICAL
  Kathleen: raw=4.03   SC=0.801  CANONICAL
```

## Quick Install

```bash
# Option A: via ClawdHub
clawdhub install evez-os

# Option B: manual
cp -r evez-os ~/.openclaw/skills/
cp -r workspace/* ~/.openclaw/workspace/
cp -r hooks/evez-os ~/.openclaw/hooks/
openclaw hooks enable evez-os
```
