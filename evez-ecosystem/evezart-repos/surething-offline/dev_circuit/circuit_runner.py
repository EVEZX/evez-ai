#!/usr/bin/env python3
"""EVEZ Development Circuit Runner
Orchestrates: THINK (Groq/OpenAI) -> WRITE (GitHub) -> WITNESS (Spine + Airtable)

Usage:
  python circuit_runner.py --task DCT-001
  python circuit_runner.py --all
  python circuit_runner.py --list
"""
from __future__ import annotations
import argparse, hashlib, json, os, sys, time, unicodedata
from datetime import datetime, timezone
from typing import Any

def nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s)

def canon(obj: Any) -> tuple[str, str]:
    import math
    def _n(o, p=""):
        if isinstance(o, str): return nfc(o)
        if isinstance(o, bool): return o
        if isinstance(o, float):
            if math.isnan(o) or math.isinf(o): raise ValueError(f"Poison at {p}")
            return round(o, 6)
        if isinstance(o, int): return o
        if isinstance(o, dict): return {nfc(k): _n(v, f"{p}.{k}") for k, v in sorted(o.items())}
        if isinstance(o, list): return [_n(v, f"{p}[{i}]") for i, v in enumerate(o)]
        if o is None: return None
        raise TypeError(f"Unsupported at {p}: {type(o)}")
    jcs = json.dumps(_n(obj), ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return jcs, hashlib.sha256(jcs.encode()).hexdigest()

class ThinkStation:
    def __init__(self):
        self.groq_key = os.environ.get("GROQ_API_KEY", "")
        self.openai_key = os.environ.get("OPENAI_API_KEY", "")

    def generate(self, task: dict) -> dict:
        model = task.get("model", "groq")
        spec = task.get("spec", "")
        system = """You are EVEZ Code Generator. Output ONLY the file content — no markdown fences, no explanation.
Rules: typed hints, docstrings, no mutable globals, include CLI, # EVEZ-GENERATED comment at top."""
        prompt = f"Repo: {task.get('repo')}\nFile: {task.get('target_file')}\nTask: {spec}\n\nGenerate complete file content."
        if model.startswith("groq"):
            return self._groq(system, prompt, task, model)
        return self._openai(system, prompt, task)

    def _groq(self, system, prompt, task, model_name="groq") -> dict:
        import requests
        model_id = "llama-3.3-70b-versatile" if model_name == "groq" else model_name.replace("groq/", "")
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {self.groq_key}", "Content-Type": "application/json"},
            json={"model": model_id, "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}], "temperature": 0.2, "max_tokens": 8192},
            timeout=60,
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        _, eh = canon({"content": content, "task_id": task.get("task_id"), "model": model_id})
        return {"content": content, "evidence_hash": eh, "model": f"groq/{model_id}"}

    def _openai(self, system, prompt, task) -> dict:
        import requests
        resp = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {self.openai_key}", "Content-Type": "application/json"},
            json={"model": "gpt-4o", "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}], "temperature": 0.2},
            timeout=120,
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        _, eh = canon({"content": content, "task_id": task.get("task_id"), "model": "gpt-4o"})
        return {"content": content, "evidence_hash": eh, "model": "gpt-4o"}

class WriteStation:
    def __init__(self):
        self.token = os.environ.get("GITHUB_TOKEN", "")
        self.headers = {"Authorization": f"Bearer {self.token}", "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}

    def commit(self, repo: str, file_path: str, content: str, message: str, branch: str = "main") -> dict:
        import requests, base64
        owner, repo_name = repo.split("/", 1)
        url = f"https://api.github.com/repos/{owner}/{repo_name}/contents/{file_path}"
        get_resp = requests.get(url, headers=self.headers, params={"ref": branch})
        sha = get_resp.json().get("sha") if get_resp.status_code == 200 else None
        payload = {"message": message, "content": base64.b64encode(content.encode()).decode(), "branch": branch}
        if sha: payload["sha"] = sha
        put_resp = requests.put(url, headers=self.headers, json=payload)
        put_resp.raise_for_status()
        return {"commit_sha": put_resp.json().get("commit", {}).get("sha", ""), "file_path": file_path}

class WitnessStation:
    def __init__(self):
        self.spine_url = os.environ.get("EVEZ_SPINE_URL", "https://evez-operator.vercel.app")

    def emit(self, event_type: str, lane: str, payload: dict) -> dict:
        import requests
        try:
            resp = requests.post(f"{self.spine_url}/spine/event", json={"event_type": event_type, "lane": lane, "payload": payload}, timeout=15)
            return resp.json() if resp.ok else {"error": f"HTTP {resp.status_code}"}
        except Exception as e:
            return {"error": str(e)}

class DevCircuit:
    def __init__(self):
        self.think = ThinkStation()
        self.write = WriteStation()
        self.witness = WitnessStation()

    def run_task(self, task: dict) -> dict:
        tid = task.get("task_id", "?")
        print(f"\n[CIRCUIT] {tid}: {task.get('title', '')}")
        results: dict = {"task_id": tid, "stations": {}}

        # THINK
        print(f"  [THINK] {task.get('model', 'groq')}...")
        try:
            tr = self.think.generate(task)
            results["stations"]["think"] = {"status": "ok", **tr}
            print(f"  [THINK] ✓ {tr['model']} evidence:{tr['evidence_hash'][:12]}")
        except Exception as e:
            results["stations"]["think"] = {"status": "error", "error": str(e)}
            print(f"  [THINK] ✗ {e}")
            results["overall"] = "failed"
            return results

        # WRITE
        print(f"  [WRITE] {task.get('repo')}/{task.get('target_file')}...")
        try:
            msg = f"evez-circuit/{tid}: {task.get('title','generated')}\n\nevidence_hash: {tr['evidence_hash']}\nmodel: {tr['model']}"
            wr = self.write.commit(repo=task.get("repo"), file_path=task.get("target_file"), content=tr["content"], message=msg, branch=task.get("branch", "main"))
            results["stations"]["write"] = {"status": "ok", **wr}
            print(f"  [WRITE] ✓ commit:{wr['commit_sha'][:12]}")
        except Exception as e:
            results["stations"]["write"] = {"status": "error", "error": str(e)}
            print(f"  [WRITE] ✗ {e}")

        # WITNESS
        payload = {"task_id": tid, "repo": task.get("repo"), "file": task.get("target_file"), "evidence_hash": tr.get("evidence_hash"), "model": tr.get("model"), "commit_sha": results["stations"].get("write", {}).get("commit_sha")}
        spine_result = self.witness.emit("transformation", "empirical", payload)
        results["stations"]["witness"] = {"status": "ok", "spine": spine_result}
        if "event_hash" in spine_result:
            print(f"  [WITNESS] ✓ spine:{spine_result['event_hash'][:12]}")

        results["overall"] = "ok" if results["stations"].get("think", {}).get("status") == "ok" else "failed"
        return results

SAMPLE_TASKS = [
    {"task_id": "DCT-001", "title": "EVEZ health check endpoint", "repo": "EvezArt/surething-offline", "target_file": "api/health.py", "model": "groq", "branch": "main", "spec": "FastAPI health endpoint returning uptime, spine_height, active contradictions count, git commit hash. Returns JSON with 'healthy': true if spine reachable."},
    {"task_id": "DCT-002", "title": "Hyperloop tick compute module", "repo": "EvezArt/surething-offline", "target_file": "dev_circuit/hyperloop_tick.py", "model": "groq", "branch": "main", "spec": "Pure Python: compute_tick(round) -> dict with N, factors, tau, omega_k, topo, poly_c, x, p_fire, u, FIRE. Explicit divisor enumeration. CLI: python hyperloop_tick.py 502"},
    {"task_id": "DCT-003", "title": "Backendless spine mirror", "repo": "EvezArt/surething-offline", "target_file": "dev_circuit/backendless_mirror.py", "model": "groq", "branch": "main", "spec": "Mirror spine events to Backendless EVEZ_SPINE table. Paginate, idempotent, --dry-run flag. Env: BACKENDLESS_APP_ID, BACKENDLESS_API_KEY."},
    {"task_id": "DCT-004", "title": "Airtable circuit task poller", "repo": "EvezArt/surething-offline", "target_file": "dev_circuit/airtable_poller.py", "model": "groq", "branch": "main", "spec": "Poll Airtable DEV_CIRCUIT_TASKS for pending tasks, run circuit_runner logic, update status. Env: AIRTABLE_API_KEY, AIRTABLE_BASE_ID."},
    {"task_id": "DCT-005", "title": "ElevenLabs FIRE voice announcer", "repo": "EvezArt/surething-offline", "target_file": "dev_circuit/voice_announcer.py", "model": "groq", "branch": "main", "spec": "ElevenLabs TTS for FIRE event announcements. Input fire_data dict. Output MP3 file. Text: 'FIRE number N. Round R. V score V_after. Evidence anchored.' Env: ELEVENLABS_API_KEY."},
]

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="EVEZ Dev Circuit")
    parser.add_argument("--task", help="Task ID")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.list:
        for t in SAMPLE_TASKS: print(f"  {t['task_id']:10} [{t['model']:6}] {t['title']}")
    elif args.task:
        task = next((t for t in SAMPLE_TASKS if t["task_id"] == args.task), None)
        if not task: print(f"Not found: {args.task}"); sys.exit(1)
        if args.dry_run: print(json.dumps(task, indent=2)); sys.exit(0)
        result = DevCircuit().run_task(task)
        print(json.dumps(result, indent=2, default=str))
    elif args.all:
        circuit = DevCircuit()
        results = []
        for task in SAMPLE_TASKS:
            if args.dry_run: print(f"{task['task_id']}: {task['title']}"); continue
            results.append(circuit.run_task(task))
            time.sleep(2)
        ok = sum(1 for r in results if r.get("overall") == "ok")
        print(f"\nCIRCUIT: {ok}/{len(results)} OK")
    else:
        parser.print_help()
