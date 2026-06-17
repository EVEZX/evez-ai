# EVEZ Provider v2 API Documentation

Base URL: `http://localhost:9100` (or Cloudflare tunnel)

## Authentication

All requests require `Authorization: Bearer <API_KEY>` header.

Admin key: configured in `.env` as `ADMIN_KEY`

## Endpoints

### Health Check
```
GET /health
```
Returns: `{"status": "healthy", "provider": "evez-v2", "models": N, "backends": N}`

### List Models
```
GET /v1/models
```
Returns OpenAI-compatible model list.

### Chat Completions
```
POST /v1/chat/completions
Content-Type: application/json

{
  "model": "evez-smart",
  "messages": [{"role": "user", "content": "Hello"}],
  "max_tokens": 1024,
  "temperature": 0.7
}
```

### Add Custom Model
```
POST /admin/models
Content-Type: application/json

{
  "id": "my-model",
  "backend": "openrouter",
  "backend_model": "google/gemma-4-31b-it:free",
  "context_window": 131072
}
```

## Available Models (45 total)

| ID | Backend | Base Model | Context |
|----|---------|------------|---------|
| evez-smart | vultr | GLM-5.1-FP8 | 202K |
| evez-code | vultr | DeepSeek-V3.2-NVFP4 | 128K |
| evez-fast | vultr | MiniMax-M2.7 | 128K |
| evez-vision | vultr | Kimi-K2.6 | 128K |
| or-gemma4-31b | openrouter | Gemma-4-31B | 131K |
| or-nemotron-120b | openrouter | Nemotron-120B | 4K |
| groq-llama31-8b | groq | Llama-3.1-8B | 131K |
| groq-llama33-70b | groq | Llama-3.3-70B | 131K |
| groq-deepseek-r1 | groq | DeepSeek-R1-70B | 131K |
| ... | ... | ... | ... |

Full list: `GET /v1/models`

## Backends

| Backend | Status | Cost | Models |
|---------|--------|------|--------|
| Vultr Inference | ✅ Active | Free | 4 |
| OpenRouter | ✅ Active | Free tier | 6+ |
| Groq | ✅ Active | Free tier | 5 |
| HuggingFace | ⚠️ Credits depleted | Free (monthly) | 7 |
| Google Gemini | ⚠️ Quota exceeded | Free tier | 2 |

## Cost

**$0/month** — All models use free tiers.

## Intelligent Routing

The provider automatically routes requests:
1. Direct model match → use specified backend
2. Fallback chain → try alternative backends if primary fails
3. Cost optimization → prefer $0 backends

## OpenAI Compatibility

All endpoints are OpenAI-compatible. Use any OpenAI SDK:

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:9100/v1",
    api_key="your-admin-key"
)

response = client.chat.completions.create(
    model="evez-smart",
    messages=[{"role": "user", "content": "Hello"}]
)
```
