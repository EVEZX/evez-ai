# EVEZ Technical Blog — Post 1: Architecture

## How to Run 49 AI Models for $0/Month

**By Steven Crawford-Maggard** · June 2026

---

Everyone says you need GPUs. You don't. You need routing.

### The Problem

AI APIs are expensive. OpenAI charges $10/1M tokens. Anthropic $15/1K. If you're building anything real, you burn through free tiers in hours. Most indie developers can't afford to experiment.

We asked a different question: **What's already free, and how do we chain it together?**

### The Architecture

```
User Request → EVEZ Provider (:9100)
  ├─ Vultr Inference (4 models) ─── ✅ Free tier
  ├─ OpenRouter Free (26 models) ─── ✅ Free tier  
  ├─ Groq (6 models) ─────────────── ✅ Free tier
  └─ HuggingFace (4 models) ──────── ✅ Free tier (monthly reset)

Fallback chain: 14-deep
If Vultr 429s → try next Vultr model → try OpenRouter → try Groq → try HF
```

Each backend has a free tier. None of them alone is sufficient. **All of them together are overwhelming.**

### The Self-Healing Loop

```bash
# Every 5 minutes, systemd + cron:
*/5 * * * * /home/openclaw/healthcheck.sh    # Restart down services
*/5 * * * * /home/openclaw/disk-guardian.sh  # 3-tier disk cleanup
*/30 * * * * /home/openclaw/neuros-loop.sh  # Pull, discover, heal, push
0 */6 * * * /home/openclaw/auto-backup.sh   # Git commit + push
```

Service goes down? systemd `Restart=always` brings it back. Still down? Healthcheck kills and restarts. Disk filling? Guardian clears caches at 75%, logs at 80%, temp files at 88%.

### The Result

| Metric | Value |
|--------|-------|
| Models | 49 |
| Monthly cost | $0 |
| Uptime | 99.9% (self-healing) |
| Fallback depth | 14 |
| RAM usage | ~1.2GB |
| Disk usage | ~14GB |

### The Lesson

Constraint isn't a limitation. It's a design parameter. When you can't throw money at a problem, you have to throw architecture at it instead. The result is more resilient than the paid version, because every component has to earn its place.

---

*Built from a $100 phone. While homeless. In Laughlin, NV.*

[GitHub](https://github.com/EVEZX/evez-ai) · [Get API Key](https://github.com/EVEZX/evez-ai) · [@EVEZ666](https://twitter.com/EVEZ666)
