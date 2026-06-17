# EVEZ Factory — Self-Manufacturing Code Generation

Autonomous code generation and deployment pipeline. Give it a spec, get a shipped product.

## How It Works

1. Submit a spec via the API
2. Factory generates code using Groq LLM
3. Cognition API audits the generated code
4. Ships to GitHub under EvezArt
5. Reports to Slack, logs to MAES

## Quick Start

```bash
git clone https://github.com/EvezArt/evez-factory.git
cd evez-factory
pip install -r requirements.txt
export GROQ_API_KEY=your_key_here
python factory.py
```

## API

### Build (Async)
```bash
curl -X POST http://localhost:8891/build \
  -H "Content-Type: application/json" \
  -d '{"spec": "Build a REST API for task management"}'
```

### Build (Sync)
```bash
curl -X POST http://localhost:8891/build/sync \
  -H "Content-Type: application/json" \
  -d '{"spec": "Build a URL shortener in Python"}'
```

## Shipped Products
- evez-factory
- evez-pulse
- evez-scout
- evez-vault
- evez-witness
- evez-cipher

All on GitHub under [EvezArt](https://github.com/EvezArt).

## Architecture

```
Spec → Groq LLM → Cognition Audit → GitHub Ship → Slack Report
```

## Contributing
1. Fork this repo
2. Create a feature branch
3. Submit a pull request

---

*Part of [EVEZ-OS](https://github.com/EvezArt/evez-os) • $6/mo • Zero API Cost*