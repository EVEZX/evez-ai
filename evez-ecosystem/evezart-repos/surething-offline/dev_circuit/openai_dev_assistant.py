#!/usr/bin/env python3
"""EVEZ OpenAI Dev Assistant
Persistent gpt-4o assistant (asst_lyxTcUn0Bv2t7F6aJepN2ULT) for complex code gen.

Usage:
  python openai_dev_assistant.py --run "task spec"
  python openai_dev_assistant.py --create  # re-create if needed
"""
from __future__ import annotations
import argparse, json, os, sys, time
from pathlib import Path

ASSISTANT_ID = "asst_lyxTcUn0Bv2t7F6aJepN2ULT"  # EVEZ Dev Assistant
ASSISTANT_ID_FILE = Path(__file__).parent / "assistant_id.txt"

EVEZ_INSTRUCTIONS = """You are EVEZ Dev Assistant — production-ready Python code generator for EVEZ.
Rules: typed hints, docstrings, # EVEZ-GENERATED at top, explicit error handling, CLI entrypoint.
EVEZ: canonicalize before hash (NFC->types->RFC3339/Z->JCS->SHA-256), spine append-only, defense-only.
Output ONLY file content — no markdown fences, no explanation."""

def get_assistant_id() -> str:
    if ASSISTANT_ID_FILE.exists():
        aid = ASSISTANT_ID_FILE.read_text().strip()
        if aid: return aid
    return ASSISTANT_ID

def create_assistant(key: str) -> str:
    import requests
    h = {"Authorization": f"Bearer {key}", "Content-Type": "application/json", "OpenAI-Beta": "assistants=v2"}
    resp = requests.post("https://api.openai.com/v1/assistants", headers=h, json={
        "model": "gpt-4o", "name": "EVEZ Dev Assistant",
        "instructions": EVEZ_INSTRUCTIONS, "tools": [{"type": "code_interpreter"}],
        "metadata": {"system": "evez", "circuit_node": "THINK-O"}
    }, timeout=30)
    resp.raise_for_status()
    aid = resp.json()["id"]
    ASSISTANT_ID_FILE.write_text(aid)
    print(f"Created: {aid}")
    return aid

def run_task(spec: str, key: str, assistant_id: str = None) -> dict:
    import requests
    aid = assistant_id or get_assistant_id()
    h = {"Authorization": f"Bearer {key}", "Content-Type": "application/json", "OpenAI-Beta": "assistants=v2"}
    base = "https://api.openai.com/v1"
    # Create thread
    t = requests.post(f"{base}/threads", headers=h, json={"messages": [{"role": "user", "content": spec}]}, timeout=30)
    t.raise_for_status()
    tid = t.json()["id"]
    # Create run
    r = requests.post(f"{base}/threads/{tid}/runs", headers=h, json={"assistant_id": aid, "temperature": 0.2}, timeout=30)
    r.raise_for_status()
    rid = r.json()["id"]
    # Poll
    for _ in range(60):
        time.sleep(3)
        s = requests.get(f"{base}/threads/{tid}/runs/{rid}", headers=h, timeout=30).json().get("status")
        if s in ("completed", "failed", "cancelled", "expired"): break
    # Get messages
    msgs = requests.get(f"{base}/threads/{tid}/messages", headers=h, params={"order": "asc"}, timeout=30).json().get("data", [])
    response = "".join(b["text"]["value"] for m in msgs if m["role"] == "assistant" for b in m.get("content", []) if b.get("type") == "text")
    return {"thread_id": tid, "run_id": rid, "status": s, "response": response.strip()}

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--create", action="store_true")
    p.add_argument("--run", type=str)
    p.add_argument("--id", type=str)
    args = p.parse_args()
    key = os.environ.get("OPENAI_API_KEY", "")
    if not key: print("Set OPENAI_API_KEY"); sys.exit(1)
    if args.create: create_assistant(key)
    elif args.run:
        result = run_task(args.run, key, args.id)
        print(json.dumps(result, indent=2))
    else: p.print_help()
