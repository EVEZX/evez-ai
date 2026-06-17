"""Multi-model orchestrator: Groq, Ollama, OpenRouter, HuggingFace, with fallbacks."""
import os
import json
import asyncio
import httpx
from typing import Dict, List, Optional, Union
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelProvider(Enum):
    GROQ = "groq"
    OLLAMA = "ollama"
    OPENROUTER = "openrouter"
    HUGGINGFACE = "huggingface"
    OPENAI = "openai"
    VLLM = "vllm"

class ModelOrchestrator:
    def __init__(self):
        self.providers = self._init_providers()
        self.fallback_order = [
            ModelProvider.GROQ,
            ModelProvider.OLLAMA,
            ModelProvider.OPENROUTER,
            ModelProvider.HUGGINGFACE,
        ]
        self.model_cache = {}
        
    def _init_providers(self) -> Dict[ModelProvider, dict]:
        return {
            ModelProvider.GROQ: {
                "enabled": bool(os.getenv("GROQ_API_KEY")),
                "endpoint": "https://api.groq.com/openai/v1/chat/completions",
                "models": ["llama-3.3-70b-versatile", "qwen-2.5-32b", "gemma2-9b-it", "mixtral-8x7b-32768"],
                "cost_per_1k_input": 0.0000,  # Free tier
                "cost_per_1k_output": 0.0000,
                "max_tokens": 32768,
            },
            ModelProvider.OLLAMA: {
                "enabled": bool(os.getenv("OLLAMA_HOST")),
                "endpoint": f"{os.getenv('OLLAMA_HOST', 'http://localhost:11434')}/api/chat",
                "models": ["llama3.2:latest", "mistral:latest", "gemma2:latest", "qwen2.5:latest"],
                "cost_per_1k_input": 0.0,  # Local
                "cost_per_1k_output": 0.0,
                "max_tokens": 8192,
            },
            ModelProvider.OPENROUTER: {
                "enabled": bool(os.getenv("OPENROUTER_API_KEY")),
                "endpoint": "https://openrouter.ai/api/v1/chat/completions",
                "models": ["meta-llama/llama-3.1-70b-instruct", "google/gemini-2.0-flash", "anthropic/claude-3-haiku"],
                "cost_per_1k_input": 0.0000,  # Free tier
                "cost_per_1k_output": 0.0000,
                "max_tokens": 4096,
            },
            ModelProvider.HUGGINGFACE: {
                "enabled": bool(os.getenv("HUGGINGFACE_TOKEN")),
                "endpoint": "https://api-inference.huggingface.co/models",
                "models": ["meta-llama/Llama-3.2-3B-Instruct", "microsoft/phi-2", "google/gemma-2-2b"],
                "cost_per_1k_input": 0.0,
                "cost_per_1k_output": 0.0,
                "max_tokens": 2048,
            },
        }
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tool_definitions: Optional[List[Dict]] = None,
        tool_choice: Optional[str] = None,
        stream: bool = False,
        provider_priority: Optional[List[ModelProvider]] = None,
    ) -> Dict:
        """Get completion from best available provider."""
        if provider_priority:
            providers_to_try = provider_priority
        else:
            providers_to_try = self.fallback_order
        
        last_error = None
        
        for provider in providers_to_try:
            config = self.providers.get(provider)
            if not config or not config.get("enabled"):
                logger.debug(f"Skipping {provider.value}, not enabled")
                continue
            
            # Select model
            if model and model in config["models"]:
                selected_model = model
            else:
                selected_model = config["models"][0]
            
            # Prepare payload
            payload = {
                "model": selected_model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens or config.get("max_tokens", 2048),
            }
            
            if tool_definitions:
                payload["tools"] = tool_definitions
                if tool_choice:
                    payload["tool_choice"] = tool_choice
            
            headers = self._get_headers(provider)
            endpoint = config["endpoint"]
            
            # Special handling for Ollama
            if provider == ModelProvider.OLLAMA:
                payload = {
                    "model": selected_model,
                    "messages": messages,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens or config.get("max_tokens", 2048),
                    },
                    "stream": stream,
                }
            
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    if stream:
                        # Streaming response
                        async with client.stream("POST", endpoint, json=payload, headers=headers) as response:
                            if response.status_code != 200:
                                raise Exception(f"Provider {provider.value} failed: {response.status_code}")
                            async for chunk in response.aiter_lines():
                                if chunk.strip():
                                    yield json.loads(chunk)
                    else:
                        # Non-streaming
                        response = await client.post(endpoint, json=payload, headers=headers)
                        if response.status_code == 200:
                            result = response.json()
                            # Cache successful model
                            self.model_cache[model or selected_model] = provider
                            return result
                        else:
                            logger.warning(f"Provider {provider.value} failed: {response.status_code} {response.text}")
                            last_error = f"{provider.value}: {response.status_code}"
            except Exception as e:
                logger.warning(f"Provider {provider.value} error: {str(e)}")
                last_error = str(e)
                continue
        
        # All providers failed
        if last_error:
            raise Exception(f"All providers failed. Last error: {last_error}")
        else:
            raise Exception("No enabled providers available")
    
    def _get_headers(self, provider: ModelProvider) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        
        if provider == ModelProvider.GROQ:
            headers["Authorization"] = f"Bearer {os.getenv('GROQ_API_KEY')}"
        elif provider == ModelProvider.OPENROUTER:
            headers["Authorization"] = f"Bearer {os.getenv('OPENROUTER_API_KEY')}"
            headers["HTTP-Referer"] = os.getenv("OPENROUTER_REFERRER", "https://evez-art.github.io")
        elif provider == ModelProvider.HUGGINGFACE:
            headers["Authorization"] = f"Bearer {os.getenv('HUGGINGFACE_TOKEN')}"
        elif provider == ModelProvider.OPENAI:
            headers["Authorization"] = f"Bearer {os.getenv('OPENAI_API_KEY')}"
        
        return headers
    
    def get_available_models(self) -> List[Dict]:
        """List all available models across providers."""
        models = []
        for provider, config in self.providers.items():
            if config.get("enabled"):
                for model_name in config["models"]:
                    models.append({
                        "name": model_name,
                        "provider": provider.value,
                        "max_tokens": config.get("max_tokens"),
                        "cost_per_1k_input": config.get("cost_per_1k_input"),
                        "cost_per_1k_output": config.get("cost_per_1k_output"),
                    })
        return models
    
    def estimate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost for a given model."""
        for provider, config in self.providers.items():
            if model in config["models"]:
                input_cost = (input_tokens / 1000) * config.get("cost_per_1k_input", 0.0)
                output_cost = (output_tokens / 1000) * config.get("cost_per_1k_output", 0.0)
                return input_cost + output_cost
        return 0.0

# Singleton instance
orchestrator = ModelOrchestrator()
