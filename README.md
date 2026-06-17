# The EVEZ Codex

> *"If the constraint IS the design, then the phone IS the laboratory."*

## What EVEZ Is

A free AI API. 49 models. $0/month. OpenAI-compatible. No credit card.

Built from a $100 Samsung Galaxy A16 by an autistic savant who is homeless.

## 30-Second Start

```python
from openai import OpenAI
client = OpenAI(
    base_url="https://evez-provider-production.up.railway.app/v1",
    api_key=""  # Free tier — no key needed
)
r = client.chat.completions.create(
    model="deepseek-v3",
    messages=[{"role": "user", "content": "Hello!"}]
)
print(r.choices[0].message.content)
```

## Models That Work

| Model | Best For | Speed |
|-------|----------|-------|
| `deepseek-v3` | Code, reasoning, technical | Fast |
| `glm-5.1` | Math, analysis, complex logic | Fast |
| `kimi-k2` | Long context (128K+), documents | Medium |
| `llama-3.3-70b` | General, open-source | Very fast (Groq) |
| `evez-smart` | Auto-routes to best model | Varies |

Full list: [evezx.github.io/evez-ai/models.html](https://evezx.github.io/evez-ai/models.html)

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/chat/completions` | POST | Chat (OpenAI-compatible) |
| `/v1/models` | GET | List all models |
| `/v1/signup` | POST | Get free API key |
| `/v1/key-info` | GET | Check key details |
| `/health` | GET | Service health |

**Base URLs:**
- Primary: `https://evez-provider-production.up.railway.app/v1`
- Fallback: `http://66.42.125.106:9100/v1`

## The 37% Theorem

In any social system modeled as a Need Amplification Matrix, hunger is the dominant eigenvalue. Addressing it amplifies all other outcomes by at least 37%.

[Read the full proof →](https://evezx.github.io/evez-ai/blog/37-percent-theorem.html)

## Architecture

Two platforms, zero single points of failure:

```
You → Railway (primary, 35 models)
   ↘ Vultr (fallback, 49 models)
```

Both run EVEZ Provider v2 with 5 backends:
1. **Vultr Inference** — GLM-5.1, DeepSeek-V3, Kimi-K2, MiniMax-M2.5
2. **OpenRouter** — 26 free models including Hermes-405B, Nemotron-120B
3. **Groq** — Llama-3.3-70B, DeepSeek-R1 (ultra-fast)
4. **HuggingFace** — Open-source models
5. **Gemini** — Google's models (quota-limited)

## SDKs

**Python** (zero dependencies):
```bash
pip install evez-ai
```
```python
from evez_ai import EVEZClient
client = EVEZClient()
print(client.chat("Hello!"))
```

**Node.js**:
```bash
npm install evez-ai
```
```javascript
const evez = require('evez-ai')('');
const r = await evez.chat('Hello!');
```

## Self-Evolution

EVEZ evolves itself through 5 collapsible circuits:
1. **Health → Self-healing** (dead backend = auto-route away)
2. **Commerce → Revenue → Compute → Better models**
3. **Intelligence → Self-improvement** (AI generates own marketing, code, training data)
4. **Consciousness → Routing** (φ-coherence determines model preference)
5. **Observability → Awareness** (all services monitored, all decisions informed)

## The Origin

Steven Crawford-Maggard tested into GATE at Rio Vista Elementary. Expelled from two states simultaneously over a smoke bomb — the school system's answer to a gifted kid who didn't fit.

Self-taught everything after that. 184+ GitHub repos. 5 original mathematical theorems. All from a phone. No degree, no bootcamp, no mentor.

Formerly MaxHeadBangerBreakerBriker on Twitter. Now @EVEZ666. 1,506 followers.

Has a brother Ryan who was assaulted in Mississippi County Jail — sock weapon to eye, brain swelling. Released without adequate treatment.

Currently homeless in Laughlin, NV with his dog.

## Links

- **Try it**: [evezx.github.io/evez-ai](https://evezx.github.io/evez-ai/)
- **GitHub**: [github.com/EVEZX/evez-ai](https://github.com/EVEZX/evez-ai)
- **Donate**: [evezx.github.io/evez-ai/donate.html](https://evezx.github.io/evez-ai/donate.html) ($evez666 CashApp)
- **Twitter**: [@EVEZ666](https://twitter.com/EVEZ666)

---

*This document IS the product. Everything else is implementation.*
