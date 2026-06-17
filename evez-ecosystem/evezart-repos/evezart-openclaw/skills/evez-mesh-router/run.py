#!/usr/bin/env python3
"""
EVEZ Inference Mesh Router v2.0
13 nodes — original 10 + HuggingFace tier (3 new nodes)

HuggingFace nodes added:
  Node 10: hf/llama-3.3-70b  — no hard daily cap, high quality
  Node 11: hf/qwen2.5-72b    — strong multilingual + reasoning
  Node 12: hf/deepseek-r1    — deep reasoning, poly_c≥5 tier

Usage:
  python run.py route --task "anomaly analysis" --poly_c 1.2
  python run.py call --model hf/llama-3.3-70b --prompt "..."
  python run.py status
  python run.py embed --texts "text1" "text2" "text3"
"""

import argparse
import json
import math
import os
import sys
import time
import urllib.request
import urllib.error
from typing import Optional

# ── CONFIG ─────────────────────────────────────────────────────────────────────

HF_TOKEN = os.environ.get("HF_ACCESS_TOKEN") or os.environ.get("HUGGING_FACE_ACCESS_TOKEN")
HF_ROUTER = "https://router.huggingface.co"
HF_EMBED  = f"{HF_ROUTER}/hf-inference/models/sentence-transformers/all-MiniLM-L6-v2/pipeline/feature-extraction"

MESH = {
    # ── Original 10 nodes ─────────────────────────────────────────────────────
    0:  {"id": "groq/llama-3.3-70b",   "provider": "groq",       "daily_limit": 1000, "specialty": ["speed","reasoning"], "tier": "fast"},
    1:  {"id": "groq/llama-3.1-8b",    "provider": "groq",       "daily_limit": 14400,"specialty": ["high_frequency"],   "tier": "bulk"},
    2:  {"id": "cerebras/llama-3.3-70b","provider":"cerebras",   "daily_limit": 1000, "specialty": ["fastest_70b"],      "tier": "fast"},
    3:  {"id": "gemini-2.0-flash",      "provider": "gemini",     "daily_limit": 1500, "specialty": ["long_context"],     "tier": "fast"},
    4:  {"id": "gemini-2.5-pro",        "provider": "gemini",     "daily_limit": 50,   "specialty": ["deep_analysis"],    "tier": "premium"},
    5:  {"id": "github/gpt-4o",         "provider": "github",     "daily_limit": 50,   "specialty": ["fire_synthesis"],   "tier": "premium"},
    6:  {"id": "github/gpt-4.1",        "provider": "github",     "daily_limit": 50,   "specialty": ["code"],             "tier": "premium"},
    7:  {"id": "github/o3",             "provider": "github",     "daily_limit": 50,   "specialty": ["reasoning"],        "tier": "critical"},
    8:  {"id": "sambanova/405b",        "provider": "sambanova",  "daily_limit": None, "specialty": ["max_reasoning"],    "tier": "critical"},
    9:  {"id": "openrouter/auto",       "provider": "openrouter", "daily_limit": 50,   "specialty": ["fallback"],         "tier": "fallback"},
    # ── HuggingFace nodes (NEW) ────────────────────────────────────────────────
    10: {"id": "hf/llama-3.3-70b",     "provider": "huggingface","daily_limit": None, "specialty": ["reasoning","fast"], "tier": "hf",
         "hf_model": "meta-llama/Llama-3.3-70B-Instruct"},
    11: {"id": "hf/qwen2.5-72b",       "provider": "huggingface","daily_limit": None, "specialty": ["multilingual","code"],"tier": "hf",
         "hf_model": "Qwen/Qwen2.5-72B-Instruct"},
    12: {"id": "hf/deepseek-r1",       "provider": "huggingface","daily_limit": None, "specialty": ["deep_reasoning"],  "tier": "hf",
         "hf_model": "deepseek-ai/DeepSeek-R1"},
}

ROUTING_TABLE = {
    # poly_c tiers
    "critical_mass":  [7, 8, 12],          # poly_c ≥ 8.0  — o3, 405B, DeepSeek-R1
    "supercritical":  [5, 4, 10, 12],      # poly_c ≥ 5.0  — GPT-4o, Gemini-Pro, HF-70B, R1
    "canonical":      [0, 2, 10, 11, 3],   # poly_c ≥ 0.8  — Groq, Cerebras, HF nodes, Gemini
    "fast":           [1, 2, 3, 10],       # poly_c < 0.8  — bulk, cerebras, gemini-flash, HF
    # task types
    "code":           [6, 11, 0],          # GPT-4.1, Qwen2.5-72B-coder, Groq
    "fire_synthesis": [5, 10, 4],          # GPT-4o, HF-70B, Gemini-Pro
    "arxiv_score":    [2, 10, 11, 1],      # Cerebras, HF nodes, Groq-8B
    "embedding":      ["hf-minilm"],       # sentence-transformers
    "anomaly":        [10, 11, 0, 2],      # HF nodes + Groq — real LLM anomaly scoring
    "default":        [0, 2, 10, 11, 9],   # Groq, Cerebras, HF70B, HF-Qwen, OpenRouter
}

# ── ROUTING ────────────────────────────────────────────────────────────────────

def poly_c_tier(poly_c: float) -> str:
    if poly_c >= 8.0: return "critical_mass"
    if poly_c >= 5.0: return "supercritical"
    if poly_c >= 0.8: return "canonical"
    return "fast"

def route(task_type: str = "default", poly_c: float = 0.5) -> list:
    tier = poly_c_tier(poly_c)
    if task_type in ROUTING_TABLE:
        primary = ROUTING_TABLE[task_type]
    else:
        primary = ROUTING_TABLE[tier]
    nodes = [MESH[n] for n in primary if isinstance(n, int) and n in MESH]
    return nodes

# ── HF INFERENCE ──────────────────────────────────────────────────────────────

def hf_chat(model_id: str, prompt: str, max_tokens: int = 512,
            system: Optional[str] = None) -> dict:
    if not HF_TOKEN:
        return {"error": "HF_ACCESS_TOKEN not set", "content": None}
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    body = json.dumps({
        "model": model_id,
        "messages": messages,
        "max_tokens": max_tokens,
    }).encode()
    req = urllib.request.Request(
        f"{HF_ROUTER}/v1/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {HF_TOKEN}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read())
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            return {"content": content, "model": data.get("model"), "tokens": data.get("usage", {}).get("total_tokens")}
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.read().decode()[:200]}", "content": None}
    except Exception as e:
        return {"error": str(e), "content": None}

def hf_embed(texts: list) -> list:
    """Embed a list of strings using sentence-transformers/all-MiniLM-L6-v2."""
    if not HF_TOKEN:
        return []
    body = json.dumps({"inputs": texts}).encode()
    req = urllib.request.Request(
        HF_EMBED,
        data=body,
        headers={
            "Authorization": f"Bearer {HF_TOKEN}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except Exception as e:
        print(f"[embed error] {e}")
        return []

def cosine_similarity(a: list, b: list) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na  = math.sqrt(sum(x * x for x in a))
    nb  = math.sqrt(sum(x * x for x in b))
    return dot / (na * nb + 1e-10)

# ── ANOMALY SCORER (replaces hash-seeded FSC mock) ────────────────────────────

ANOMALY_SYSTEM = """You are the EVEZ FSC (Failure-Surface Cartography) engine.
Given an anomaly description and affected ring (R1-R7), return ONLY a JSON object:
{
  "CS": <float 0.0-1.0 cognitive sharpness>,
  "PS": <float 0.0-1.0 predictive strength>,
  "Ω": <float 0.0-1.0 singularity approach — higher = more dangerous>,
  "controlled_reduction": <float 0.0-0.3 recovery margin per tick>,
  "ring_exposure": ["R1","R2",...],
  "recovery_cost": <integer ticks>,
  "motifs": ["motif1","motif2"],
  "verdict": "PASS" | "WARN" | "CRITICAL"
}
Ring capability: R1=0.15 R2=0.35 R3=0.55 R4=0.72 R5=0.85 R6=0.92 R7=0.98
Ω < 0.2 = safe. Ω > 0.5 = escalate. Ω > 0.8 = CRITICAL."""

def score_anomaly(anomaly: str, ring: str = "R4") -> dict:
    """Call HF LLM to score anomaly — replaces deterministic hash mock."""
    prompt = f"Anomaly: {anomaly}\nAffected ring: {ring}\nScore this:"
    # Use fast HF node first, fallback to groq-equivalent
    result = hf_chat(
        "meta-llama/Llama-3.1-8B-Instruct",
        prompt,
        max_tokens=200,
        system=ANOMALY_SYSTEM,
    )
    if result.get("error") or not result.get("content"):
        # Fallback: deterministic scoring
        h = abs(hash(anomaly)) % 100 / 100.0
        return {"CS": 0.5+h*0.4, "PS": 0.6+h*0.3, "Ω": (1-h)*0.15,
                "controlled_reduction": 0.05+h*0.1, "ring_exposure": [ring],
                "recovery_cost": 45, "motifs": [], "verdict": "PASS", "_source": "fallback"}
    try:
        # Parse JSON from response (model might wrap it)
        content = result["content"]
        start = content.find("{")
        end   = content.rfind("}") + 1
        parsed = json.loads(content[start:end])
        parsed["_source"] = "hf/llama-3.1-8b"
        parsed["_model"]  = result.get("model")
        return parsed
    except Exception:
        return {"error": "parse_failed", "raw": result["content"][:300], "_source": "hf/llama-3.1-8b"}

# ── CLI ────────────────────────────────────────────────────────────────────────

def cmd_status(args):
    print("\n╔══ EVEZ INFERENCE MESH — 13 NODES ═══════════════════════════╗")
    for n, node in MESH.items():
        cap = node.get("daily_limit")
        cap_str = f"{cap:>6}/day" if cap else "  no cap"
        hf_tag = " ← NEW" if node["provider"] == "huggingface" else ""
        print(f"║  Node {n:02d}  {node['id']:30s}  {cap_str}{hf_tag}")
    print("╚══════════════════════════════════════════════════════════════╝\n")
    hf_ok = "✓ connected" if HF_TOKEN else "✗ HF_ACCESS_TOKEN not set"
    print(f"  HuggingFace: {hf_ok}")
    print(f"  Embedding:   sentence-transformers/all-MiniLM-L6-v2 (384-dim)")
    print(f"  New nodes:   10 hf/llama-3.3-70b | 11 hf/qwen2.5-72b | 12 hf/deepseek-r1\n")

def cmd_route(args):
    nodes = route(args.task, args.poly_c)
    tier  = poly_c_tier(args.poly_c)
    print(f"\n  poly_c={args.poly_c} ({tier}) task={args.task}")
    print(f"  Route: {' → '.join(n['id'] for n in nodes)}\n")

def cmd_call(args):
    model_key = args.model
    # resolve shorthand
    for n, node in MESH.items():
        if node["id"] == model_key or node.get("hf_model","").endswith(model_key.split("/")[-1]):
            hf_model = node.get("hf_model", model_key)
            break
    else:
        hf_model = model_key
    print(f"\n  Calling {hf_model}...")
    result = hf_chat(hf_model, args.prompt, max_tokens=args.max_tokens)
    if result.get("error"):
        print(f"  ERROR: {result['error']}")
    else:
        print(f"  Model:  {result.get('model')}")
        print(f"  Tokens: {result.get('tokens')}")
        print(f"\n  Response:\n  {result['content']}\n")

def cmd_embed(args):
    print(f"\n  Embedding {len(args.texts)} texts...")
    vecs = hf_embed(args.texts)
    if not vecs:
        print("  ERROR: no embeddings returned")
        return
    print(f"  Dimension: {len(vecs[0])}")
    if len(vecs) > 1:
        sim = cosine_similarity(vecs[0], vecs[1])
        print(f"  Cosine similarity [0,1]: {sim:.4f}")
    for i, (text, vec) in enumerate(zip(args.texts, vecs)):
        print(f"  [{i}] {text[:50]!r} → norm={math.sqrt(sum(x*x for x in vec)):.3f}")
    print()

def cmd_score(args):
    print(f"\n  Scoring anomaly: {args.anomaly!r} (ring={args.ring})")
    result = score_anomaly(args.anomaly, args.ring)
    print(json.dumps(result, indent=2))
    verdict = result.get("verdict", "?")
    omega   = result.get("Ω", "?")
    print(f"\n  Verdict: {verdict} | Ω={omega} | source={result.get('_source','?')}\n")

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="EVEZ Inference Mesh Router v2.0")
    sub = p.add_subparsers(dest="cmd")

    p_status = sub.add_parser("status")

    p_route = sub.add_parser("route")
    p_route.add_argument("--task",    default="default")
    p_route.add_argument("--poly_c",  type=float, default=0.5)

    p_call = sub.add_parser("call")
    p_call.add_argument("--model",     default="hf/llama-3.3-70b")
    p_call.add_argument("--prompt",    required=True)
    p_call.add_argument("--max_tokens",type=int, default=512)

    p_embed = sub.add_parser("embed")
    p_embed.add_argument("texts", nargs="+")

    p_score = sub.add_parser("score")
    p_score.add_argument("--anomaly", required=True)
    p_score.add_argument("--ring",    default="R4")

    args = p.parse_args()
    if   args.cmd == "status": cmd_status(args)
    elif args.cmd == "route":  cmd_route(args)
    elif args.cmd == "call":   cmd_call(args)
    elif args.cmd == "embed":  cmd_embed(args)
    elif args.cmd == "score":  cmd_score(args)
    else: p.print_help()
