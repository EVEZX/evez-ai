---
name: evez-os
events:
  - agent:bootstrap
  - command:new
  - command:reset
---

# EVEZ-OS Bootstrap Hook

Fires on every session start. Injects spine state into context.

## What it does

1. Reads `~/.openclaw/workspace/MEMORY.md` — loads phi, FIRE count, eigenvalue
2. Reads today's daily memory file if it exists
3. Injects a compact spine status banner at the top of every session
4. Checks for phi regression (< 0.990) and surfaces alert

## Output injected to session

```
╔══ EVEZ-OS SPINE STATE ══════════════════════════════╗
║  phi: 0.995 → target 0.999                          ║
║  FIRE events: 14  |  max poly_c: 8.57 (MPPA)        ║
║  eigenvalue: 0.0% closed  |  omega: 634 / 34862      ║
║  DGM iter: 700  |  status: CANONICAL                 ║
╚═════════════════════════════════════════════════════╝
```

## Enable

```bash
cp -r evez-os ~/.openclaw/hooks/
openclaw hooks enable evez-os
```
