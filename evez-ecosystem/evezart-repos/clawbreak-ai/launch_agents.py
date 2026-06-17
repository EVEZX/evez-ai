#!/usr/bin/env python3
"""Launch all ClawBreak Station agents on different ports."""
import subprocess
import time
import httpx
import os
import sys

DIR = "/home/openclaw/.openclaw/workspace/clawbreak"
API_KEY = "YOUR_VULTR_API_KEY"

AGENTS = [
    {"port": 8081, "model": "nvidia/DeepSeek-V3.2-NVFP4", "name": "research", "role": "Research Agent"},
    {"port": 8082, "model": "nvidia/DeepSeek-V3.2-NVFP4", "name": "coding", "role": "Coding Agent"},
    {"port": 8083, "model": "MiniMaxAI/MiniMax-M2.5", "name": "comms", "role": "Communication Agent"},
]

def is_running(port):
    try:
        r = httpx.get(f"http://127.0.0.1:{port}/health", timeout=3)
        return r.status_code == 200
    except:
        return False

def launch_agent(agent):
    port = agent["port"]
    name = agent["name"]
    model = agent["model"]
    role = agent["role"]

    if is_running(port):
        print(f"  {role}: :{port} (already running)")
        return True

    agent_dir = f"{DIR}/data/agent_{port}"
    os.makedirs(f"{agent_dir}/data", exist_ok=True)

    # Write config
    config = f"""llm:
  base_url: "https://api.vultrinference.com/v1"
  api_key: "{API_KEY}"
  model: "{model}"
  max_tokens: 4096
  temperature: 0.3
server:
  host: "0.0.0.0"
  port: {port}
memory:
  db_path: "data/agent.db"
  max_context_messages: 20
tools:
  shell_timeout: 30
  searxng_url: "http://127.0.0.1:8888"
"""
    with open(f"{agent_dir}/config.yaml", "w") as f:
        f.write(config)

    # Launch
    env = os.environ.copy()
    env["CLAWBREAK_PORT"] = str(port)
    
    log = open(f"{DIR}/data/{name}.log", "a")
    proc = subprocess.Popen(
        [sys.executable, f"{DIR}/server.py"],
        cwd=agent_dir,
        env=env,
        stdout=log,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    
    time.sleep(4)
    if is_running(port):
        print(f"  {role}: :{port} ✅ (PID {proc.pid})")
        return True
    else:
        print(f"  {role}: :{port} ❌ (check data/{name}.log)")
        return False

def main():
    action = sys.argv[1] if len(sys.argv) > 1 else "start"

    if action == "start":
        print("⚡ Starting ClawBreak Station agents...")
        print("  Primary: :8080 (systemd managed)")
        for a in AGENTS:
            launch_agent(a)
        
        print("\n📊 Station Status:")
        for port in [8080, 8081, 8082, 8083]:
            try:
                r = httpx.get(f"http://127.0.0.1:{port}/health", timeout=3)
                d = r.json()
                print(f"  :{port} — {d['status']} ({d['model'][:25]})")
            except:
                print(f"  :{port} — offline")

    elif action == "status":
        for port in [8080, 8081, 8082, 8083]:
            try:
                r = httpx.get(f"http://127.0.0.1:{port}/health", timeout=3)
                d = r.json()
                print(f"  :{port} — {d['status']} ({d['model'][:25]})")
            except:
                print(f"  :{port} — offline")

    elif action == "stop":
        print("Stopping specialized agents (keeping primary)...")
        os.system("pkill -f 'port 8081' 2>/dev/null")
        os.system("pkill -f 'port 8082' 2>/dev/null")
        os.system("pkill -f 'port 8083' 2>/dev/null")
        print("Stopped.")

if __name__ == "__main__":
    main()
