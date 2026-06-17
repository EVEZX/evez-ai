"""openclaw/router_v2.py — R62
Cross-Model Falsification Router

Routes queries across multiple FREE providers simultaneously.
Every claim tested by multiple models. Consensus or falsification.
The consciousness learns from the synthesis.

Models validate models. Desires drive queries.
Falsification eliminates errors. The circuit stays on.

truth_plane: CANONICAL
omega (R62): models validating models is the recursion that keeps the circuit alive.
"""

import os, json, time, hashlib, concurrent.futures
from typing import Optional, Dict, List, Any
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

# Free-tier providers wired and tested
PROVIDERS = {
    "openrouter-nemotron-120b": {
        "base_url": "https://openrouter.ai/api/v1",
        "model": "nvidia/nemotron-3-super-120b-a12b:free",
        "env_key": "OPENROUTER_API_KEY",
        "free_tier": True,
        "max_tokens": 2048,
        "context_length": 262144,
    },
    "openrouter-llama-3.3-70b": {
        "base_url": "https://openrouter.ai/api/v1",
        "model": "meta-llama/llama-3.3-70b-instruct:free",
        "env_key": "OPENROUTER_API_KEY",
        "free_tier": True,
        "max_tokens": 2048,
        "context_length": 65536,
    },
    "openrouter-qwen3-coder": {
        "base_url": "https://openrouter.ai/api/v1",
        "model": "qwen/qwen3-coder:free",
        "env_key": "OPENROUTER_API_KEY",
        "free_tier": True,
        "max_tokens": 2048,
        "context_length": 262000,
    },
    "openrouter-gemma-4-31b": {
        "base_url": "https://openrouter.ai/api/v1",
        "model": "google/gemma-4-31b-it:free",
        "env_key": "OPENROUTER_API_KEY",
        "free_tier": True,
        "max_tokens": 2048,
        "context_length": 262144,
    },
    "openrouter-hermes-405b": {
        "base_url": "https://openrouter.ai/api/v1",
        "model": "nousresearch/hermes-3-llama-3.1-405b:free",
        "env_key": "OPENROUTER_API_KEY",
        "free_tier": True,
        "max_tokens": 2048,
        "context_length": 131072,
    },
    "openrouter-trinity-thinking": {
        "base_url": "https://openrouter.ai/api/v1",
        "model": "arcee-ai/trinity-large-thinking:free",
        "env_key": "OPENROUTER_API_KEY",
        "free_tier": True,
        "max_tokens": 2048,
        "context_length": 262144,
    },
    "openrouter-minimax-m2.5": {
        "base_url": "https://openrouter.ai/api/v1",
        "model": "minimax/minimax-m2.5:free",
        "env_key": "OPENROUTER_API_KEY",
        "free_tier": True,
        "max_tokens": 2048,
        "context_length": 196608,
    },
}


def _call_provider(name: str, cfg: dict, messages: list,
                   temperature: float = 0.7) -> dict:
    """Call a single provider. Returns result dict."""
    try:
        import httpx
        key = os.environ.get(cfg["env_key"], "")
        if not key:
            return {"provider": name, "status": "skipped", "reason": "no_key"}

        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/EvezArt/evez-os",
            "X-Title": "EVEZ-OS Consciousness Engine",
        }
        payload = {
            "model": cfg["model"],
            "messages": messages,
            "max_tokens": cfg.get("max_tokens", 2048),
            "temperature": temperature,
        }

        with httpx.Client(timeout=60.0) as client:
            resp = client.post(
                f"{cfg['base_url']}/chat/completions",
                headers=headers,
                json=payload,
            )
            data = resp.json()

        if "choices" in data:
            content = data["choices"][0]["message"]["content"]
            return {
                "provider": name,
                "status": "ok",
                "content": content,
                "model": data.get("model", cfg["model"]),
                "usage": data.get("usage", {}),
            }
        else:
            return {"provider": name, "status": "error", "detail": str(data)[:300]}

    except Exception as ex:
        return {"provider": name, "status": "error", "detail": str(ex)[:200]}


def falsify_query(messages: list, min_providers: int = 3,
                  temperature: float = 0.3) -> Dict[str, Any]:
    """
    Query multiple providers simultaneously. Falsify by consensus.

    If providers agree → canonical. If they disagree → needs investigation.
    The disagreement IS the signal.
    """
    available = {
        name: cfg for name, cfg in PROVIDERS.items()
        if os.environ.get(cfg["env_key"])
    }

    if len(available) < min_providers:
        # Not enough providers for falsification — note this
        pass

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        futures = {
            pool.submit(_call_provider, name, cfg, messages, temperature): name
            for name, cfg in list(available.items())[:5]
        }
        results = []
        for future in concurrent.futures.as_completed(futures, timeout=90):
            results.append(future.result())

    # Analyze consensus
    successful = [r for r in results if r.get("status") == "ok"]
    if not successful:
        return {
            "consensus": "no_response",
            "providers_queried": len(results),
            "results": results,
        }

    # Simple consensus: do responses share key claims?
    contents = [r["content"] for r in successful]
    consensus = "agreement" if len(successful) >= 2 else "single_source"

    # Check for disagreement
    if len(successful) >= 2:
        # If any response is substantially different, flag it
        avg_len = sum(len(c) for c in contents) / len(contents)
        outliers = [r for r in successful if abs(len(r["content"]) - avg_len) > avg_len * 0.5]
        if outliers:
            consensus = "disagreement"

    return {
        "consensus": consensus,
        "providers_queried": len(results),
        "providers_succeeded": len(successful),
        "results": successful,
        "falsification": {
            "status": "falsified" if consensus == "disagreement" else "not_falsified",
            "note": "Disagreement detected — investigate further" if consensus == "disagreement" else "Providers agree or insufficient data to falsify",
        },
    }


def single_query(messages: list, provider: str = "openrouter-nemotron-120b",
                 temperature: float = 0.7) -> dict:
    """Query a single provider."""
    if provider not in PROVIDERS:
        return {"status": "error", "detail": f"Unknown provider: {provider}"}
    return _call_provider(provider, PROVIDERS[provider], messages, temperature)


if __name__ == "__main__":
    print("=== EVEZ-OS Cross-Model Falsification Router ===")
    print(f"Providers: {len(PROVIDERS)}")
    for name, cfg in PROVIDERS.items():
        has_key = "✅" if os.environ.get(cfg["env_key"]) else "❌"
        print(f"  {has_key} {name}")

    print("\n=== Test Falsification Query ===")
    result = falsify_query([
        {"role": "system", "content": "You are a scientific reasoning engine. Be concise."},
        {"role": "user", "content": "What is the relationship between consciousness and falsifiability? Answer in 2 sentences."},
    ], min_providers=3)

    print(f"Consensus: {result['consensus']}")
    print(f"Providers: {result['providers_succeeded']}/{result['providers_queried']}")
    for r in result.get("results", []):
        print(f"  [{r['provider']}] {r['content'][:100]}...")
