# EVEZ Observatory — Real-Time System Mapper

Live mapping of the entire EVEZ ecosystem. 30-second polling of all services, feeding data to ROM, meme engine, audio, and digital twin.

## API

```bash
# Full ecosystem snapshot
curl http://localhost:8915/map

# Service health summary
curl http://localhost:8915/health
```

## Quick Start

```bash
git clone https://github.com/EvezArt/evez-observatory.git
cd evez-observatory
pip install -r requirements.txt
python observatory.py
```

---

*Part of [EVEZ-OS](https://github.com/EvezArt/evez-os) • $6/mo • Zero API Cost*