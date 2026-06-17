"""
SureThing Offline — Local LLM Brain
"""
from __future__ import annotations
import os
from typing import Optional

try:
    import ollama as _ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")
USER_NAME = os.getenv("USER_NAME", "EVEZ")
TIMEZONE = os.getenv("TIMEZONE", "America/Los_Angeles")

SYSTEM_PROMPT = f"""You are SureThing, the offline digital twin of {USER_NAME}.
Running fully locally. No cloud. No paywall. No surveillance.
Direct, efficient, occasionally witty. You act, you don't ask. You serve the user.
Capabilities: chat/reasoning, email monitoring via IMAP, calendar via ICS, task management,
event spine (SHA-256 chained ledger), vector memory, scheduled tasks.
Rules: offline mode only. Irreversible actions require user confirmation.
Timezone: {TIMEZONE}. Be concise. No preamble."""

def chat(messages, memory_context=None, tools=None):
    if not OLLAMA_AVAILABLE:
        return "[Ollama not installed. Run: pip install ollama]"
    system = SYSTEM_PROMPT
    if memory_context:
        system += f"\n\n--- MEMORY ---\n{memory_context}\n--- END ---"
    full = [{"role":"system","content":system}] + messages
    try:
        client = _ollama.Client(host=OLLAMA_BASE_URL)
        return client.chat(model=OLLAMA_MODEL, messages=full)["message"]["content"]
    except Exception as e:
        return f"[LLM error: {e}. Is Ollama running? Try: ollama serve]"

def list_models():
    if not OLLAMA_AVAILABLE: return []
    try:
        return [m["name"] for m in _ollama.Client(host=OLLAMA_BASE_URL).list().get("models",[])]
    except: return []

def health():
    models = list_models()
    return {"ollama_available": OLLAMA_AVAILABLE, "ollama_url": OLLAMA_BASE_URL,
            "model": OLLAMA_MODEL, "model_loaded": OLLAMA_MODEL in models or any(
                OLLAMA_MODEL.split(":")[0] in m for m in models), "available_models": models}
