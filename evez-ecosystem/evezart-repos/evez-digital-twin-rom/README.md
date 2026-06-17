# EVEZ Digital Twin ROM v2 — Data-as-Terrain

Procedural terrain generated from real EVEZ telemetry. 24 service locations, 8 zones, telemetry polling, save states, cheat codes, screenshot renderer.

## Crime Cross-Analytics Engine

Simulates intervention outcomes for vulnerable adults caught between the justice and medical systems.

### Endpoints
```bash
# CAIN FSC audit of Ryan's case
curl http://localhost:8898/crime/audit

# Compare all intervention types
curl http://localhost:8898/crime/compare

# Full speedrun: audit + comparison + optimization
curl http://localhost:8898/crime/speedrun

# One-liner summary
curl http://localhost:8898/crime/speedrun-summary

# The 911 trap analysis
curl http://localhost:8898/crime/911-trap

# Generate safest welfare check approach
curl http://localhost:8898/crime/optimize-welfare-check
```

## Quick Start

```bash
git clone https://github.com/EvezArt/evez-digital-twin-rom.git
cd evez-digital-twin-rom
pip install -r requirements.txt
python rom_engine.py
```

---

*Part of [EVEZ-OS](https://github.com/EvezArt/evez-os) • $6/mo • Zero API Cost*