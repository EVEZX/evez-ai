---
name: evez-mesh-router
version: 0.2.0
description: 10-node inference mesh router. Routes tasks to the right model based on poly_c tier, domain, and daily token budgets. Fallback chain automatic.
tags: [evez, mesh, inference, routing, llm]
---

# EVEZ Inference Mesh Router

Routes every LLM call to the right node based on task type and poly_c score.
Tracks daily token budgets. Auto-fallback when limits hit.

## Node Registry

| ID | Provider | Model | Daily Limit | Specialty |
|----|----------|-------|-------------|-----------|
| 0 | groq | llama-3.3-70b | 1K req | Speed — 300+ t/s |
| 1 | groq | llama-3.1-8b | 14.4K req | High-frequency |
| 2 | cerebras | llama-3.3-70b | 1K req | Fastest 70B on planet |
| 3 | gemini | gemini-2.0-flash | 1,500 req | Long context, multimodal |
| 4 | gemini | gemini-2.5-pro | 50 req | Deep analysis (save for poly_c≥5) |
| 5 | github | gpt-4o | 50 req | FIRE synthesis (save for poly_c≥5) |
| 6 | github | gpt-4.1 | 50 req | Code generation |
| 7 | github | o3 | 50 req | Reasoning (save for poly_c≥8) |
| 8 | sambanova | llama-405b | $5 credit | Max reasoning (MPPA-tier only) |
| 9 | openrouter | auto | 50 req/day | Free fallback |

## Routing Logic

```python
def route(task_type, poly_c):
    if poly_c >= 8.0:  return ["github/o3", "sambanova/405b"]
    if poly_c >= 5.0:  return ["github/gpt-4o", "gemini-2.5-pro"]
    if poly_c >= 0.9:  return ["groq/70b", "cerebras", "gemini-flash"]
    if task_type == "code": return ["github/gpt-4.1", "groq", "openrouter"]
    return ["groq", "cerebras", "gemini-flash", "openrouter"]
```

## Usage in session

```
/mesh status
→ groq/70b: 234/1000 req today
→ cerebras: 89/1000 req today
→ gemini-flash: 312/1500 req today
→ github/gpt-4o: 3/50 req today ← CONSERVE
→ github/o3: 0/50 req today ← CONSERVE (poly_c≥8.0 only)
```
