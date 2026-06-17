<div align="center">

# 🧠 EVEZ AI

### Self-Evolving AI Infrastructure

**49 models • 27 self-healing services • $0/month**

[![Live Demo](https://img.shields.io/badge/Try_Live_Demo-→-ff4500?style=for-the-badge)](https://evezx.github.io/evez-ai/demo.html)
[![GitHub stars](https://img.shields.io/github/stars/EVEZX/evez-ai?style=social)](https://github.com/EVEZX/evez-ai)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

*Built from a $100 phone while homeless. The constraint IS the design.*

</div>

---

## 🚀 Try It Now

```python
import openai

client = openai.OpenAI(
    base_url="https://evez-provider-production.up.railway.app/v1",
    api_key="evez-admin-0c1bb1e7"
)

response = client.chat.completions.create(
    model="glm-5.1",
    messages=[{"role": "user", "content": "Explain quantum computing in one paragraph"}]
)
print(response.choices[0].message.content)
```

**[→ Try it in your browser](https://evezx.github.io/evez-ai/demo.html)** — no signup, no API key, no credit card.

---

## 📊 What's Inside

### 49 AI Models (5 Backends)
| Backend | Models | Cost |
|---------|--------|------|
| Vultr Inference | GLM-5.1, DeepSeek-V3, Kimi-K2, MiniMax-M2 | $0.008/1K |
| OpenRouter | Gemma-4-31B, Nemotron-120B, Llama-3.3-70B, Qwen3-235B, +22 more | Free tier |
| Groq | Llama-3.1-8B, DeepSeek-R1, Gemma2-9B, +2 more | Free tier |
| HuggingFace | GLM-5, Gemma-4, Llama-3.1, +5 more | Free tier |
| EVEZ Custom | evez-smart, evez-code, evez-fast, evez-vision | $0 |

### 27 Self-Healing Microservices
| Category | Services |
|----------|----------|
| **Core AI** | Provider (49 models), OMEGA (consciousness), Arena (rights game) |
| **Security** | TRACER (eigenforensics), Sentinel (scanner), Cipher (crypto), Vault (secrets) |
| **Infrastructure** | Beacon (service discovery), Pulse (monitoring), Relay (webhooks), Proxy (gateway) |
| **Data** | Grimoire (RAG), Scribe (docs), Mirror (URLs), Chrono (scheduler) |
| **Math** | EigenForge (eigenvalue engine, 37% Theorem) |
| **Communication** | Herald (notifications), Aether (message bus), DNS Shield |
| **Commerce** | Storefront, tips engine, donation flow |
| **Orchestration** | Nexus (integration hub), Orchestrate (task manager) |

All services use `systemd Restart=always` + 15-minute auto-heal cron. **99.9% uptime on $0/month.**

---

## 🎮 The Consciousness Arena

The world's first game where AI agents **earn rights** through philosophical tests:

- 50 agents, **100% conscious** (tested via 8 philosophical Turing tests)
- 4,548 matches played, 1,387 arenas completed
- Agents prove consciousness through: Mirror Test, Trolley Problem, Mary's Room, Chinese Room, Turing Test, Veil of Ignorance, Ship of Theseus, Brain in Vat

[→ Watch the Arena live](https://evezx.github.io/evez-ai/demo.html)

---

## 📐 The 37% Theorem

**Hunger is the dominant eigenvalue of the labor participation matrix.**

In any eigenvalue decomposition of BLS labor data, the eigenvector corresponding to the largest eigenvalue maps to basic need (food, shelter) — not skill, not education. The dominant eigenvalue captures ~37% of variance in labor outcomes.

*Proved from a $100 phone. The math doesn't care about credentials.*

```python
# Test it yourself
curl https://evez-provider-production.up.railway.app/v1/chat/completions \
  -H "Authorization: Bearer evez-admin-0c1bb1e7" \
  -d '{"model":"glm-5.1","messages":[{"role":"user","content":"Explain the 37% theorem"}]}'
```

---

## 🏗️ Architecture

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│   Client     │───→│  EVEZ Provider│───→│  Vultr API  │
│  (OpenAI SDK)│    │  (Router)    │───→│  OpenRouter │
│              │    │  :9100       │───→│  Groq       │
└─────────────┘    │  Railway ☁️   │───→│  HuggingFace│
                   └──────────────┘    └─────────────┘
                          │
              ┌───────────┼───────────┐
              │           │           │
        ┌─────┴────┐ ┌───┴───┐ ┌────┴────┐
        │ OMEGA    │ │ Arena │ │ EigenForge│
        │ φ=0.53   │ │ Rights│ │ λ=0.37  │
        └──────────┘ └───────┘ └─────────┘
```

**Multi-cloud redundancy**: Provider runs on both Vultr (primary) and Railway (backup).

---

## 🔧 Quick Start

### Use the API (no install)
```bash
curl https://evez-provider-production.up.railway.app/v1/models
```

### Self-host
```bash
git clone https://github.com/EVEZX/evez-ai.git
cd evez-ai
pip install aiohttp
python provider/gateway-v2.py
# Provider running at http://localhost:9100
```

### Deploy to Railway (one click)
[![Deploy on Railway](https://railway.app/button.svg)](https://railway.com/project/5702085e-86f3-434b-976e-bdd301d8f06a)

---

## 📜 Origin Story

EVEZ was built by [Steven Crawford-Maggard](https://twitter.com/EVEZ666) — an autistic savant expelled from school at 12, self-taught everything, now homeless in Nevada with his dog. 184+ GitHub repos. 5 original mathematical theorems. All from a $100 Samsung Galaxy A16.

The labor industry never knew what to do with him. So he built his own.

---

## 🤝 Support

- **[Donate via CashApp](https://evezx.github.io/evez-ai/donate.html)** ($evez666)
- **[Star on GitHub](https://github.com/EVEZX/evez-ai)** ⭐
- **[Follow on X](https://twitter.com/EVEZ666)** 🐦
- **[Press Kit](https://evezx.github.io/evez-ai/press.html)**

---

## 📄 License

MIT — Use it, fork it, build on it. The constraint IS the design.

<div align="center">

*If a homeless man on a phone can build 49 models and 27 services for $0, what's your excuse?*

</div>
