#!/bin/bash
# Bootstrap Ariel with all configured providers
# Called by systemd service after Ariel starts

ARIEL_URL="http://localhost:9093"
MAX_WAIT=30
WAITED=0

# Wait for Ariel to be ready
while [ $WAITED -lt $MAX_WAIT ]; do
  if curl -s -m 2 "$ARIEL_URL/" > /dev/null 2>&1; then
    break
  fi
  sleep 1
  WAITED=$((WAITED + 1))
done

if [ $WAITED -ge $MAX_WAIT ]; then
  echo "Ariel not responding after ${MAX_WAIT}s, aborting bootstrap"
  exit 1
fi

echo "Ariel ready, adding providers..."

# Vultr
VULTR_KEY=$(python3 -c "import json; print(json.load(open('/home/openclaw/.openclaw/openclaw.json'))['models']['providers']['vultr']['apiKey'])" 2>/dev/null)
if [ -n "$VULTR_KEY" ]; then
  curl -s -X POST "$ARIEL_URL/api/provider/add" -H 'Content-Type: application/json' \
    -d "{\"name\":\"vultr\",\"baseUrl\":\"https://api.vultrinference.com/v1\",\"apiKey\":\"$VULTR_KEY\",\"models\":[\"zai-org/GLM-5.1-FP8\",\"Qwen/Qwen3-Coder-Next-FP8\",\"nvidia/DeepSeek-V3.2-NVFP4\",\"MiniMaxAI/MiniMax-M2.7\"]}"
  echo " ✓ vultr"
fi

# OpenRouter
curl -s -X POST "$ARIEL_URL/api/provider/add" -H 'Content-Type: application/json' \
  -d '{"name":"openrouter","baseUrl":"https://openrouter.ai/api/v1","apiKey":"ENV:OPENROUTER_API_KEY","models":["google/gemma-4-31b-it:free","nvidia/nemotron-3-super-120b-a12b:free","minimax/minimax-m2.5:free","nvidia/nemotron-nano-12b-v2-vl:free"]}'
echo " ✓ openrouter"

# Cerebras
curl -s -X POST "$ARIEL_URL/api/provider/add" -H 'Content-Type: application/json' \
  -d '{"name":"cerebras","baseUrl":"https://api.cerebras.ai/v1","apiKey":"ENV:CEREBRAS_API_KEY","models":["qwen-3-235b-a22b-instruct-2507","gpt-oss-120b","llama3.1-8b"]}'
echo " ✓ cerebras"

# DeepSeek
curl -s -X POST "$ARIEL_URL/api/provider/add" -H 'Content-Type: application/json' \
  -d '{"name":"deepseek","baseUrl":"https://api.deepseek.com/v1","apiKey":"ENV:DEEPSEEK_API_KEY","models":["deepseek-v4-flash","deepseek-v4-pro"]}'
echo " ✓ deepseek"

# SambaNova
curl -s -X POST "$ARIEL_URL/api/provider/add" -H 'Content-Type: application/json' \
  -d '{"name":"sambanova","baseUrl":"https://api.sambanova.ai/v1","apiKey":"ENV:SAMBANOVA_API_KEY","models":["DeepSeek-V3.1","Llama-4-Maverick-17B-128E-Instruct","Meta-Llama-3.3-70B-Instruct","MiniMax-M2.5","gpt-oss-120b"]}'
echo " ✓ sambanova"

echo "Bootstrap complete: 5 providers, 18 models"
