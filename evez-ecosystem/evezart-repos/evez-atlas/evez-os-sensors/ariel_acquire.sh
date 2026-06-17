#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# ARIEL ACQUISITION — Register for every free AI API
#
# This script automates what it can and provides URLs for manual signup.
# After running, all keys are added to Intelligence Unit Ariel.
#
# Usage: bash ariel_acquire.sh
# ═══════════════════════════════════════════════════════════════

ARIEL_URL="http://localhost:9093"

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  ARIEL ACQUISITION — Free AI API Registration               ║"
echo "║  12 providers, 50+ models, $0 cost                          ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Check for existing keys in environment
add_provider() {
    local name=$1 url=$2 key=$3
    shift 3
    local models=("$@")
    
    if [ -z "$key" ]; then
        echo "  ⏳ $name: No key found. Sign up at:"
        echo "     $url"
        echo "     Then: curl -s -X POST $ARIEL_URL/api/provider/add -H 'Content-Type: application/json' -d '{\"name\":\"$name\",\"baseUrl\":\"$2\",\"apiKey\":\"YOUR_KEY\",\"models\":[\"model-id\"]}'"
        return
    fi
    
    local models_json=$(printf '%s\n' "${models[@]}" | jq -R . | jq -s .)
    local result=$(curl -s -X POST "$ARIEL_URL/api/provider/add" \
        -H "Content-Type: application/json" \
        -d "{\"name\":\"$name\",\"baseUrl\":\"$2\",\"apiKey\":\"$key\",\"models\":$models_json}")
    echo "  ✓ $name: $result"
}

# 1. VULTR (already configured)
echo "[1/12] Vultr..."
VULTR_KEY=$(cat /home/openclaw/.openclaw/openclaw.json | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['models']['providers']['vultr']['apiKey'])" 2>/dev/null)
add_provider "vultr" "https://api.vultrinference.com/v1" "$VULTR_KEY" \
    "zai-org/GLM-5.1-FP8" "meta-llama/Meta-Llama-3.1-8B-Instruct" "mistralai/Mistral-7B-Instruct-v0.3" "Qwen/Qwen2.5-7B-Instruct"

# 2. GOOGLE AI STUDIO (Gemini 2.5 Pro — BEST free tier)
echo ""
echo "[2/12] Google AI Studio (Gemini 2.5 Pro)..."
echo "  ⏳ Sign up at: https://aistudio.google.com/apikey"
echo "  FREE: 15 RPM, 1M TPM, Gemini 2.5 Pro + Flash"
echo "  After getting key:"
echo '  export GOOGLE_API_KEY=your_key'
echo '  curl -s -X POST localhost:9093/api/provider/add -H "Content-Type: application/json" -d '"'"'{"name":"google","baseUrl":"https://generativelanguage.googleapis.com/v1beta/openai","apiKey":"YOUR_KEY","models":["gemini-2.5-pro","gemini-2.5-flash","gemma-3-27b-it"]}'"'"''

# 3. GROQ (FASTEST)
echo ""
echo "[3/12] Groq (Llama 3.3 70B, Llama 4 Scout)..."
if [ -n "$GROQ_API_KEY" ]; then
    add_provider "groq" "https://api.groq.com/openai/v1" "$GROQ_API_KEY" \
        "llama-3.3-70b-versatile" "llama-4-scout-17b-16e-instruct" "deepseek-r1-distill-llama-70b" "mixtral-8x7b-32768"
else
    echo "  ⏳ Sign up at: https://console.groq.com/keys"
    echo "  FREE: 30 RPM, fastest inference, no CC"
fi

# 4. OPENROUTER (50+ models)
echo ""
echo "[4/12] OpenRouter (50+ models)..."
if [ -n "$OPENROUTER_API_KEY" ]; then
    add_provider "openrouter" "https://openrouter.ai/api/v1" "$OPENROUTER_API_KEY" \
        "meta-llama/llama-3.3-70b-instruct:free" "deepseek/deepseek-chat:free" "google/gemma-2-9b-it:free"
else
    echo "  ⏳ Sign up at: https://openrouter.ai/keys"
    echo "  FREE: GitHub OAuth signup, 20 RPM free tier"
fi

# 5. CEREBRAS (ultra-fast)
echo ""
echo "[5/12] Cerebras (Llama 3.3 70B, Qwen 2.5 32B)..."
if [ -n "$CEREBRAS_API_KEY" ]; then
    add_provider "cerebras" "https://api.cerebras.ai/v1" "$CEREBRAS_API_KEY" \
        "llama-3.3-70b" "qwen-2.5-32b"
else
    echo "  ⏳ Sign up at: https://cloud.cerebras.ai/"
    echo "  FREE: 30 RPM, no CC"
fi

# 6. MISTRAL (1B tokens/mo free)
echo ""
echo "[6/12] Mistral (Mistral Large, Codestral)..."
if [ -n "$MISTRAL_API_KEY" ]; then
    add_provider "mistral" "https://api.mistral.ai/v1" "$MISTRAL_API_KEY" \
        "mistral-large-latest" "codestral-latest" "mistral-small-latest"
else
    echo "  ⏳ Sign up at: https://console.mistral.ai/api-keys/"
    echo "  FREE: 1B tokens/month, Codestral for code"
fi

# 7. DEEPSEEK (5M tokens free)
echo ""
echo "[7/12] DeepSeek (V3, R1)..."
if [ -n "$DEEPSEEK_API_KEY" ]; then
    add_provider "deepseek" "https://api.deepseek.com/v1" "$DEEPSEEK_API_KEY" \
        "deepseek-chat" "deepseek-reasoner"
else
    echo "  ⏳ Sign up at: https://platform.deepseek.com/api_keys"
    echo "  FREE: 5M tokens on signup, DeepSeek R1 reasoning"
fi

# 8. GITHUB MODELS (GPT-4o, Llama 405B)
echo ""
echo "[8/12] GitHub Models (GPT-4o, Llama 405B)..."
GH_TOKEN=$(gh auth token 2>/dev/null)
if [ -n "$GH_TOKEN" ]; then
    echo "  ⚠ GitHub token found but needs 'models' permission"
    echo "  Update PAT at: https://github.com/settings/personal-access-tokens"
    echo "  Add: Models (read) permission"
    echo "  Then: curl -s -X POST localhost:9093/api/provider/add ..."
else
    echo "  ⏳ Install gh CLI and run: gh auth login"
fi

# 9. SAMBANOVA ($5 credits)
echo ""
echo "[9/12] SambaNova (Llama 3.3 70B)..."
if [ -n "$SAMBANOVA_API_KEY" ]; then
    add_provider "sambanova" "https://api.sambanova.ai/v1" "$SAMBANOVA_API_KEY" \
        "Meta-Llama-3.3-70B-Instruct"
else
    echo "  ⏳ Sign up at: https://cloud.sambanova.ai/"
    echo "  FREE: $5 credits on signup"
fi

# 10. SILICONFLOW (20+ free models)
echo ""
echo "[10/12] SiliconFlow (DeepSeek V3, Llama 405B, Qwen 72B)..."
if [ -n "$SILICONFLOW_API_KEY" ]; then
    add_provider "siliconflow" "https://api.siliconflow.cn/v1" "$SILICONFLOW_API_KEY" \
        "deepseek-ai/DeepSeek-V3" "meta-llama/Meta-Llama-3.1-405B-Instruct" "Qwen/Qwen2.5-72B-Instruct"
else
    echo "  ⏳ Sign up at: https://cloud.siliconflow.cn/"
    echo "  FREE: 20+ models, no CC"
fi

# 11. XAI (Grok 4 — $25 credits)
echo ""
echo "[11/12] xAI (Grok 4)..."
if [ -n "$XAI_API_KEY" ]; then
    add_provider "xai" "https://api.x.ai/v1" "$XAI_API_KEY" \
        "grok-4" "grok-4-mini"
else
    echo "  ⏳ Sign up at: https://console.x.ai/"
    echo "  FREE: $25 credits on signup"
fi

# 12. COHERE (Command R+)
echo ""
echo "[12/12] Cohere (Command R+, Embed)..."
if [ -n "$COHERE_API_KEY" ]; then
    add_provider "cohere" "https://api.cohere.com/v1" "$COHERE_API_KEY" \
        "command-r-plus" "command-r"
else
    echo "  ⏳ Sign up at: https://dashboard.cohere.com/api-keys"
    echo "  FREE: 1K requests/month, trial key"
fi

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  ARIEL STATUS                                                ║"
echo "╚══════════════════════════════════════════════════════════════╝"
curl -s "$ARIEL_URL/api/status" | python3 -m json.tool 2>/dev/null || echo "Ariel not running"

echo ""
echo "To add a key after signup:"
echo "  curl -s -X POST localhost:9093/api/provider/add -H 'Content-Type: application/json' \\"
echo '    -d '"'"'{"name":"PROVIDER","baseUrl":"URL","apiKey":"YOUR_KEY","models":["model1","model2"]}'"'"''
echo ""
echo "Or set the environment variable and re-run this script."
