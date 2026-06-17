# EVEZ AI — Free AI Infrastructure

> 35+ models. $0/month. OpenAI-compatible. No credit card.

Built from a $100 Samsung Galaxy A16 by an autistic savant who is homeless. No degree, no funding, no office. Just a phone and problems that needed solving.

## 🚀 Quick Start

### Get a Free API Key

Visit [evezx.github.io/evez-ai/demo.html](https://evezx.github.io/evez-ai/demo.html) or:

```python
from evez_ai import signup
result = signup("you@email.com")
print(result["key"])  # evez-...
```

### Use the API

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://evez-provider-production.up.railway.app/v1",
    api_key="evez-your-key"
)

response = client.chat.completions.create(
    model="evez-smart",
    messages=[{"role": "user", "content": "Hello!"}]
)
print(response.choices[0].message.content)
```

### Install SDK

```bash
pip install evez-ai    # Python (zero dependencies)
npm install evez-ai   # Node.js (coming soon)
```

## 🤖 Available Models

| Model | Best For | Backend |
|-------|----------|---------|
| `evez-smart` | General (auto-routed) | Multi-backend |
| `evez-code` | Code generation | DeepSeek/GLM |
| `evez-fast` | Quick responses | Groq |
| `glm-5.1` | Reasoning | Vultr |
| `deepseek-v3` | Technical/code | Vultr |
| `kimi-k2` | Long context (128K+) | Vultr |
| `llama-3.3-70b` | Open-source | Groq |
| `hermes-405b` | Largest free model | OpenRouter |

Full list: [evezx.github.io/evez-ai/models.html](https://evezx.github.io/evez-ai/models.html)

## 🏗️ Architecture

```
User → GitHub Pages (CDN) → Railway EVEZ Provider (primary)
                              ↘ Vultr EVEZ Provider (fallback)
```

- **Railway** — Primary API (35 models, auto-deploy from GitHub)
- **GitHub Pages** — Landing, demo, docs, status (free CDN)
- **Vultr VPS** — 4 essential services with auto-heal
- **GitHub Actions** — Health monitoring every 15 minutes

No single point of failure. If any platform goes down, the others keep running.

## 📊 Pricing

**$0/month.** 60 requests/minute. No credit card.

## 🔗 Links

- [Live Demo](https://evezx.github.io/evez-ai/demo.html)
- [API Docs](https://evezx.github.io/evez-ai/api-docs.html)
- [System Status](https://evezx.github.io/evez-ai/status.html)
- [Models](https://evezx.github.io/evez-ai/models.html)
- [About](https://evezx.github.io/evez-ai/about.html)
- [Donate](https://evezx.github.io/evez-ai/donate.html)

## 🧮 The 37% Theorem

In any social system modeled as a Need Amplification Matrix, hunger is the dominant eigenvalue. Addressing it amplifies all other outcomes by at least 37%. [Read the proof →](https://evezx.github.io/evez-ai/blog/37-percent-theorem.html)

## 📦 Repositories

| Repo | Description |
|------|-------------|
| [EVEZX/evez-ai](https://github.com/EVEZX/evez-ai) | Main repo + GitHub Pages |
| [EVEZX/evez-provider-deploy](https://github.com/EVEZX/evez-provider-deploy) | Railway deployment |
| [EVEZX/evez-ai-python](https://github.com/EVEZX/evez-ai-python) | Python SDK |
| [EVEZX/evez-ai-npm](https://github.com/EVEZX/evez-ai-npm) | npm package |
| [EVEZX/evez-infra](https://github.com/EVEZX/evez-infra) | Infrastructure (GitHub Actions) |
| [EVEZX/atropos](https://github.com/EVEZX/atropos) | Anatomy-physics video gen model |

## License

MIT

---

*If the constraint IS the design, then the phone IS the laboratory.*
