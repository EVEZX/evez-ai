"""ClawBreak LLM Client — multi-provider with automatic fallback."""
import httpx
import json
import time
from config import Config

class LLMClient:
    """Chat with multiple LLM providers, falling back on failure."""
    
    def __init__(self, config: Config):
        self.config = config
        self.providers = self._load_providers()
        self.errors = {}  # track per-provider errors

    def _load_providers(self):
        """Load provider chain from config."""
        providers = []
        
        # Primary: whatever's in config
        primary = {
            "name": "vultr-primary",
            "base_url": self.config.get("llm", "base_url"),
            "api_key": self.config.get("llm", "api_key"),
            "model": self.config.get("llm", "model"),
            "auth": "bearer",
        }
        providers.append(primary)
        
        # Additional providers from config
        extra = self.config.data.get("llm", {}).get("providers", [])
        for p in extra:
            providers.append(p)
        
        # Free fallbacks
        providers.append({
            "name": "vultr-deepseek",
            "base_url": "https://api.vultrinference.com/v1",
            "api_key": self.config.get("llm", "api_key"),
            "model": "nvidia/DeepSeek-V3.2-NVFP4",
            "auth": "bearer",
        })
        providers.append({
            "name": "vultr-minimax",
            "base_url": "https://api.vultrinference.com/v1",
            "api_key": self.config.get("llm", "api_key"),
            "model": "MiniMaxAI/MiniMax-M2.5",
            "auth": "bearer",
        })
        providers.append({
            "name": "vultr-kimi",
            "base_url": "https://api.vultrinference.com/v1",
            "api_key": self.config.get("llm", "api_key"),
            "model": "moonshotai/Kimi-K2.5",
            "auth": "bearer",
        })
        
        return providers

    async def chat(self, messages, stream=False, tools=None):
        """Send a chat request, falling through providers on failure."""
        last_error = None
        
        for provider in self.providers:
            # Skip providers that errored recently (5 min cooldown)
            last_err = self.errors.get(provider["name"], 0)
            if time.time() - last_err < 300 and last_error is not None:
                continue
                
            try:
                result = await self._call_provider(provider, messages, stream, tools)
                # Success — clear error
                self.errors.pop(provider["name"], None)
                return result
            except Exception as e:
                last_error = e
                self.errors[provider["name"]] = time.time()
                continue
        
        return {"error": f"All LLM providers failed. Last error: {last_error}"}

    async def _call_provider(self, provider, messages, stream=False, tools=None):
        """Call a single provider."""
        headers = {"Content-Type": "application/json"}
        if provider.get("auth") == "bearer":
            headers["Authorization"] = f"Bearer {provider['api_key']}"
        elif provider.get("auth") == "api-key":
            headers["x-api-key"] = provider["api_key"]
        
        payload = {
            "model": provider["model"],
            "messages": messages,
            "max_tokens": provider.get("max_tokens", self.config.get("llm", "max_tokens")),
            "temperature": provider.get("temperature", self.config.get("llm", "temperature")),
            "stream": stream,
        }
        
        if tools:
            payload["tools"] = tools

        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{provider['base_url']}/chat/completions",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            return resp.json()

    async def chat_stream(self, messages):
        """Stream chat from primary provider, fallback on error."""
        for provider in self.providers:
            last_err = self.errors.get(provider["name"], 0)
            if time.time() - last_err < 300:
                continue
                
            try:
                async for chunk in self._stream_provider(provider, messages):
                    yield chunk
                return
            except Exception as e:
                self.errors[provider["name"]] = time.time()
                continue
        
        yield f"data: {json.dumps({'error': 'All providers failed'})}\n\n"

    async def _stream_provider(self, provider, messages):
        headers = {"Content-Type": "application/json"}
        if provider.get("auth") == "bearer":
            headers["Authorization"] = f"Bearer {provider['api_key']}"
        
        payload = {
            "model": provider["model"],
            "messages": messages,
            "max_tokens": provider.get("max_tokens", 4096),
            "temperature": provider.get("temperature", 0.7),
            "stream": True,
        }

        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream("POST", f"{provider['base_url']}/chat/completions",
                                     headers=headers, json=payload) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data.strip() == "[DONE]":
                            yield "data: [DONE]\n\n"
                            return
                        try:
                            chunk = json.loads(data)
                            delta = chunk.get("choices", [{}])[0].get("delta", {})
                            if "content" in delta and delta["content"]:
                                yield f"data: {json.dumps({'content': delta['content'], 'model': provider['model'], 'provider': provider['name']})}\n\n"
                        except json.JSONDecodeError:
                            pass

    def get_active_provider(self):
        """Return the name of the current working provider."""
        for p in self.providers:
            if time.time() - self.errors.get(p["name"], 0) > 300:
                return p["name"]
        return "none"
