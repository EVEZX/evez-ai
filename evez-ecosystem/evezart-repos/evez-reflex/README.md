# EVEZ Reflex Engine

Closed loop: Awareness → Decision → Action → Learning → Awareness

When the body feels pain, it reaches. When it sees drift, it corrects. When it learns, it remembers.

## Endpoints
```bash
curl http://localhost:8953/reflex           # Evaluate and execute safe reflexes
curl http://localhost:8953/reflex/dry-run   # Evaluate only
curl http://localhost:8953/reflex/trigger/mesh_brain?action=restart
curl http://localhost:8953/learn?learning=... # Store learning
curl http://localhost:8953/memory             # View reflex memory
curl http://localhost:8953/log                 # Recent actions
```

## Doctrine Boundaries
- ✅ Safe actions auto-execute: restart, check, log, learn
- ❌ Dangerous actions require approval: email, public post, delete, kill, firewall

---
*Part of [EVEZ-OS](https://github.com/EvezArt/evez-os) • $6/mo • Zero API Cost*