# FREE STANDARD COMPUTE REPLACEMENT

## What Standard Compute Does
1. OpenAI-compatible endpoint: `https://api.stdcmpt.com/v1`
2. Forwards requests to underlying models
3. Charges flat rate instead of tokens
4. Provides setup prompt for OpenClaw config

## FREE REPLACEMENT OPTIONS

### Option 1: Local Ollama (Instant)
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Run a model
ollama run llama3.2:latest

# Ollama API: http://localhost:11434/v1
```

### Option 2: LM Studio (GUI)
- Download LM Studio
- Run local models
- Built-in OpenAI-compatible server
- API endpoint: http://localhost:1234/v1

### Option 3: Text Generation WebUI
- Full local inference server
- OpenAI-compatible API
- Multiple backend support (transformers, llama.cpp)

## OPENCLAW CONFIG FOR LOCAL FREE REPLACEMENT

```json
{
  "models": {
    "mode": "merge",
    "providers": {
      "local-free": {
        "baseUrl": "http://localhost:11434/v1",
        "apiKey": "ollama",
        "api": "openai-responses",
        "models": [{
          "id": "llama3.2:latest",
          "name": "Local Llama 3.2",
          "reasoning": false,
          "input": ["text"],
          "cost": { "input": 0, "output": 0 },
          "contextWindow": 8192,
          "maxTokens": 4096
        }]
      }
    }
  },
  "agents": {
    "defaults": {
      "model": {
        "primary": "local-free/llama3.2:latest"
      }
    }
  }
}
```

## COST: $0 (only requires decent CPU/GPU)