#!/usr/bin/env python3
"""
openclaw/router.py
OpenClaw Free-Tier Ensemble Router

Routes queries across multiple FREE providers simultaneously.
No OpenAI dependency. No paywall. No API key required to READ results.
Providers: AI/ML API (deepseek-r1), Groq (llama-3.3-70b), Perplexity.
Results logged to spine for full provenance.

Creator: Steven Crawford-Maggard EVEZ666
github.com/EvezArt/evez-os
License: AGPL-3.0
truth_plane: CANONICAL
"""
import os, json, time, hashlib, concurrent.futures
from typing import Optional
from pathlib import Path

PROVIDERS = {
    "deepseek-r1": {
        "base_url": "https://api.aimlapi.com/v1",
        "model": "deepseek/deepseek-r1",
        "env_key": "AIML_API_KEY",
        "free_tier": True,
        "max_tokens": 2048,
    },
    "llama-3.3-70b": {
        "base_url": "https://api.groq.com/openai/v1",
        "model": "llama-3.3-70b-versatile",
        "env_key": "GROQ_API_KEY",
        "free_tier": True,
        "max_tokens": 2048,
    },
    "mistral-small": {
        "base_url": "https://openrouter.ai/api/v1",
        "model": "mistralai/mistral-small",
        "env_key": "OPENROUTER_API_KEY",
        "free_tier": True,
        "max_tokens": 2048,
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
        }
        payload = {
            "model": cfg["model"],
            "messages": messages,
            "temperature": temperature,
            "max_tokens": cfg["max_tokens"],
        }
        t0 = time.time()
        resp = httpx.post(
            f"{cfg['base_url']}/chat/completions",
            json=payload,
            headers=headers,
            timeout=45.0,
        )
        elapsed = round(time.time() - t0, 3)
        if resp.status_code == 200:
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            return {
                "provider": name,
                "model": cfg["model"],
                "status": "ok",
                "content": content,
                "elapsed_s": elapsed,
                "tokens": data.get("usage", {}),
            }
        else:
            return {
                "provider": name,
                "status": "error",
                "code": resp.status_code,
                "body": resp.text[:200],
            }
    except Exception as e:
        return {"provider": name, "status": "exception", "error": str(e)}


def ensemble_query(messages: list, temperature: float = 0.7,
                   providers: Optional[list] = None) -> dict:
    """
    Query all configured free-tier providers in parallel.
    Returns: {
        results: [{provider, status, content, ...}],
        best: {provider, content},
        consensus_hash: sha256 of sorted successful contents,
        timestamp: unix,
    }
    """
    selected = {k: v for k, v in PROVIDERS.items()
                if providers is None or k in providers}

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(selected)) as ex:
        futures = {
            ex.submit(_call_provider, name, cfg, messages, temperature): name
            for name, cfg in selected.items()
        }
        results = []
        for f in concurrent.futures.as_completed(futures):
            results.append(f.result())

    ok = [r for r in results if r.get("status") == "ok"]
    ok.sort(key=lambda r: -len(r.get("content", "")))

    best = ok[0] if ok else {"provider": "none", "content": ""}

    consensus_input = json.dumps(
        sorted([r.get("content", "") for r in ok])
    ).encode()
    consensus_hash = hashlib.sha256(consensus_input).hexdigest()[:16]

    return {
        "results": results,
        "best": best,
        "ok_count": len(ok),
        "total_count": len(results),
        "consensus_hash": consensus_hash,
        "timestamp": time.time(),
    }


def log_to_spine(spine_path: Path, query: str, result: dict) -> str:
    """Append ensemble result to spine.jsonl. Returns event hash."""
    prev_hash = "0" * 64
    if spine_path.exists():
        lines = spine_path.read_text().strip().splitlines()
        if lines:
            try:
                prev_hash = json.loads(lines[-1]).get("chain_hash", "0" * 64)
            except Exception:
                pass

    event = {
        "type": "ensemble_query",
        "query_preview": query[:100],
        "ok_count": result["ok_count"],
        "total_count": result["total_count"],
        "consensus_hash": result["consensus_hash"],
        "best_provider": result["best"].get("provider", "none"),
        "timestamp": result["timestamp"],
    }
    event_json = json.dumps(event, sort_keys=True)
    chain_input = (prev_hash + event_json).encode()
    chain_hash = hashlib.sha256(chain_input).hexdigest()

    record = {
        "chain_hash": chain_hash,
        "event": event,
        "spine_v": "1.0",
    }
    spine_path.parent.mkdir(parents=True, exist_ok=True)
    with open(spine_path, "a") as f:
        f.write(json.dumps(record) + "\n")

    return chain_hash


if __name__ == "__main__":
    # Demo: query all free providers with a single prompt
    messages = [
        {"role": "system", "content": "You are EVEZ666. Terse. Dense. Truth only."},
        {"role": "user", "content":
         "In 3 sentences: what is the most radical thing an open-source AI "
         "OS can do that no paywall provider can match?"},
    ]
    print("Querying free-tier ensemble...")
    result = ensemble_query(messages, temperature=0.8)
    print(f"\nProviders responded: {result['ok_count']}/{result['total_count']}")
    print(f"Consensus hash: {result['consensus_hash']}")
    print()
    for r in result["results"]:
        status = r.get("status", "?")
        provider = r.get("provider", "?")
        if status == "ok":
            print(f"[{provider}] ({r.get('elapsed_s', '?')}s):")
            print(r["content"][:400])
        else:
            print(f"[{provider}] {status}: {r.get('reason', r.get('error', ''))}")
        print()

    print(f"BEST: [{result['best'].get('provider')}]")
    print(result["best"].get("content", "")[:600])
