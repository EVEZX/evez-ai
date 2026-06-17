# EVEZ Cognition API — NLP + Reasoning Engine

Real-time natural language processing and AI reasoning. Zero API cost via Groq Cloud.

## Quick Start

```bash
git clone https://github.com/EvezArt/evez-cognition-api.git
cd evez-cognition-api
pip install -r requirements.txt
export GROQ_API_KEY=***  # Free at console.groq.com
python app.py
```

## API

### Analyze Text
```bash
curl -X POST http://localhost:8081/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "Analyze this", "task": "sentiment"}'
```

### Health
```bash
curl http://localhost:8081/health
```

## Models
- llama-3.3-70b-versatile (default)
- qwen3-32b
- llama-4-scout

All via Groq Cloud free tier. Zero cost.

## Features
- Sentiment analysis
- Entity extraction
- Summarization
- Question answering
- Contradiction detection (CAIN engine)
- FSC doctrine validation

---

*Part of [EVEZ-OS](https://github.com/EvezArt/evez-os) • $6/mo • Zero API Cost*