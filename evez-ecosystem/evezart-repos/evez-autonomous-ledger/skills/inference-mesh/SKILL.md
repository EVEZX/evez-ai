---
name: inference-mesh
description: 10-node free inference mesh router. Selects the optimal AI provider based on task type, current rate limits, and cost. Covers Groq, Gemini, OpenRouter, Cerebras, Mistral, Cloudflare AI, GitHub Models, Cohere, HuggingFace, SambaNova. Use when routing LLM calls across the full EVEZ-OS free tier stack.
---

# Inference Mesh — EVEZ-OS 10-Node Free Router

10 providers. ~2.5M tokens/day. $0.00.

## Node Registry

| ID | Provider | Models | Daily Limit | Specialty |
|----|----------|--------|-------------|-----------|
| 0 | groq | llama-3.3-70b, llama-4-scout | 1K req (70B), 14.4K (8B) | Speed — 300+ t/s |
| 1 | gemini | gemini-2.0-flash, 2.5-pro | 1,500 req/day | Long context, multimodal |
| 2 | openrouter | deepseek-r1:free, qwen3:free | 50 req/day | Model variety |
| 3 | cerebras | llama-3.3-70b, qwen3-32b | 1M tokens/day | Fastest inference |
| 4 | mistral | mistral-large, codestral | 1B tokens/month | Code + EU |
| 5 | cloudflare | llama-3.2, mistral-7b | 10K neurons/day | Edge global |
| 6 | github | gpt-4o, gpt-4.1, o3 | 50-150 req/day | Best reasoning |
| 7 | cohere | command-r-plus, embed-4 | 1K req/month | Embeddings + RAG |
| 8 | huggingface | flux.1, 300+ models | 300 req/hr | Images + multimodal |
| 9 | sambanova | llama-3.1-405b | $5 credit | Max reasoning depth |

## Task → Provider Routing

```python
ROUTING_TABLE = {
    # High-stakes reasoning: use o3 or 405B
    "reasoning":       ["github", "sambanova", "groq"],
    # Code generation: Codestral or GPT-4.1
    "code":            ["mistral", "github", "groq"],
    # Speed-critical: Groq or Cerebras
    "fast":            ["groq", "cerebras", "gemini"],
    # CPF/FIRE analysis: need reasoning + context
    "fire_event":      ["github", "gemini", "groq"],
    # arXiv paper scoring: fast + capable
    "arxiv_score":     ["cerebras", "groq", "gemini"],
    # Embedding / semantic search
    "embed":           ["cohere", "cloudflare"],
    # Image generation
    "image":           ["huggingface"],
    # Long context (>100K tokens)
    "long_context":    ["gemini", "mistral"],
    # Default fallback cascade
    "default":         ["groq", "cerebras", "gemini", "openrouter", "mistral"],
}
```

## Provider Endpoints

```python
ENDPOINTS = {
    "groq":        "https://api.groq.com/openai/v1/chat/completions",
    "gemini":      "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}",
    "openrouter":  "https://openrouter.ai/api/v1/chat/completions",
    "cerebras":    "https://api.cerebras.ai/v1/chat/completions",
    "mistral":     "https://api.mistral.ai/v1/chat/completions",
    "cloudflare":  "https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/@cf/{model}",
    "github":      "https://models.inference.ai.azure.com/chat/completions",
    "cohere":      "https://api.cohere.ai/v2/chat",
    "huggingface": "https://api-inference.huggingface.co/models/{model}",
    "sambanova":   "https://api.sambanova.ai/v1/chat/completions",
}

ENV_VARS = {
    "groq":        "GROQ_API_KEY",
    "gemini":      "GEMINI_API_KEY",
    "openrouter":  "OPENROUTER_API_KEY",
    "cerebras":    "CEREBRAS_API_KEY",
    "mistral":     "MISTRAL_API_KEY",
    "cloudflare":  "CF_API_TOKEN + CF_ACCOUNT_ID",
    "github":      "GITHUB_ACCESS_TOKEN",  # already connected
    "cohere":      "COHERE_API_KEY",
    "huggingface": "HF_TOKEN",
    "sambanova":   "SAMBANOVA_API_KEY",
}
```

## Mesh Router (Python)

```python
import os, json, math
from datetime import datetime, timezone

def mesh_call(task_type: str, messages: list, max_tokens: int = 1000) -> dict:
    """
    Route an LLM call through the 10-node free inference mesh.
    Returns the first successful response.
    
    Args:
        task_type: one of reasoning/code/fast/fire_event/arxiv_score/embed/image/long_context/default
        messages:  OpenAI-format message list
        max_tokens: max response tokens
    
    Returns:
        {"provider": str, "content": str, "tokens": int, "latency_ms": int}
    """
    from inference_mesh import ROUTING_TABLE, ENDPOINTS, ENV_VARS, call_provider
    
    providers = ROUTING_TABLE.get(task_type, ROUTING_TABLE["default"])
    
    for provider in providers:
        key_var = ENV_VARS[provider]
        # Check if key(s) available
        if "+" in key_var:
            keys = [k.strip() for k in key_var.split("+")]
            if not all(os.environ.get(k) for k in keys):
                continue
        elif not os.environ.get(key_var):
            continue
        
        try:
            t0 = datetime.now(timezone.utc).timestamp()
            result = call_provider(provider, messages, max_tokens)
            t1 = datetime.now(timezone.utc).timestamp()
            result["latency_ms"] = int((t1 - t0) * 1000)
            result["provider"] = provider
            return result
        except Exception as e:
            continue  # try next node
    
    return {"error": "all_nodes_exhausted", "tried": providers}
```

## poly_c as Routing Signal

When routing FIRE event analysis, use poly_c to select model tier:

```python
def tier_for_poly_c(poly_c: float) -> str:
    if poly_c >= 8.0:   return "reasoning"   # o3 / 405B — critical mass events
    if poly_c >= 5.0:   return "fire_event"  # GPT-4o / 70B — canonical events
    if poly_c >= 0.9:   return "fast"        # Groq / Cerebras — standard events
    return "arxiv_score"                     # lightweight scoring
```

## Source

- Topology Expansion Map (2026-04-21)
- Awesome Free AI APIs guide (awesomeagents.ai, April 2026)
- nejib1/Free-LLM GitHub (45+ providers verified)
- EVEZ-OS inference mesh design — PID 335
