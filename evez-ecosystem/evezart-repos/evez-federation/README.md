# EVEZ Federation Bridge — Multi-Gateway Health + Failover

Coordinates health checks and failover across multiple OpenClaw gateways.

## What It Does
- Monitors primary (:18789) and rescue (:19789) gateways
- Automatic failover on gateway failure
- Health reporting to Observatory and MAES
- Federation protocol for multi-instance coordination

## Quick Start

```bash
git clone https://github.com/EvezArt/evez-federation.git
cd evez-federation
pip install -r requirements.txt
python federation.py
```

---

*Part of [EVEZ-OS](https://github.com/EvezArt/evez-os) • $6/mo • Zero API Cost*