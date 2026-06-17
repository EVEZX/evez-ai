#!/usr/bin/env python3
"""
EVEZ Watchdog — Self-Healing Service Monitor
Checks all services every 60s. Auto-restarts dead ones.
The substrate defends itself.
"""
import requests, time, subprocess, json, os, logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("watchdog")

SERVICES = {
    "openclaw-gateway": {"url": "http://127.0.0.1:18789/health", "systemd": "openclaw-gateway"},
    "clawbreak": {"url": "http://127.0.0.1:8080/health", "port": 8080, "cmd": "cd /home/openclaw/.openclaw/workspace/repos/clawbreak && /home/openclaw/.openclaw/workspace/.venv/bin/python3 -m uvicorn app:app --host 127.0.0.1 --port 8080"},
    "vcl": {"url": "http://127.0.0.1:8081/health", "port": 8081, "cmd": "cd /home/openclaw/.openclaw/workspace/repos/evez-vcl && /home/openclaw/.openclaw/workspace/.venv/bin/python3 -m uvicorn vcl_server:app --host 127.0.0.1 --port 8081"},
    "sentinel": {"url": "http://127.0.0.1:8084/health", "port": 8084, "cmd": "cd /home/openclaw/.openclaw/workspace/repos/evez-sentinel && /home/openclaw/.openclaw/workspace/.venv/bin/python3 -m uvicorn sentinel:app --host 127.0.0.1 --port 8084"},
    "promptforge": {"url": "http://127.0.0.1:8085/health", "port": 8085, "cmd": "cd /home/openclaw/.openclaw/workspace/repos/evez-promptforge && /home/openclaw/.openclaw/workspace/.venv/bin/python3 -m uvicorn promptforge:app --host 127.0.0.1 --port 8085"},
    "meshnet": {"url": "http://127.0.0.1:8086/health", "port": 8086, "cmd": "cd /home/openclaw/.openclaw/workspace/repos/evez-meshnet && /home/openclaw/.openclaw/workspace/.venv/bin/python3 -m uvicorn meshnet:app --host 127.0.0.1 --port 8086"},
    "store": {"url": "http://127.0.0.1:8091/health", "port": 8091, "cmd": "cd /home/openclaw/.openclaw/workspace/repos/evez-store && /home/openclaw/.openclaw/workspace/.venv/bin/python3 -m uvicorn store:app --host 127.0.0.1 --port 8091"},
}

SPINE_PATH = "/home/openclaw/.openclaw/workspace/logs/watchdog_spine.jsonl"
RESTART_COOLDOWN = 300
last_restart = {}

def check_service(name, config):
    try:
        start = time.time()
        r = requests.get(config["url"], timeout=5)
        latency = (time.time() - start) * 1000
        return r.status_code in (200, 401, 403), latency
    except:
        return False, -1

def restart_service(name, config):
    if name in last_restart and time.time() - last_restart[name] < RESTART_COOLDOWN:
        return False
    port = config.get("port")
    if port and "cmd" in config:
        try:
            subprocess.run(f"fuser -k {port}/tcp 2>/dev/null", shell=True, capture_output=True, timeout=5)
            time.sleep(1)
            subprocess.Popen(config["cmd"], shell=True,
                stdout=open(f"/home/openclaw/.openclaw/workspace/logs/{name}.log", "a"),
                stderr=subprocess.STDOUT)
            time.sleep(3)
            ok, _ = check_service(name, config)
            if ok:
                last_restart[name] = time.time()
                return True
        except:
            pass
    last_restart[name] = time.time()
    return False

def run():
    log.info("EVEZ Watchdog started")
    while True:
        for name, config in SERVICES.items():
            ok, latency = check_service(name, config)
            if not ok:
                log.warning(f"[{name}] DOWN - restarting")
                if restart_service(name, config):
                    log.info(f"[{name}] back online")
                else:
                    log.error(f"[{name}] restart failed")
            else:
                log.info(f"[{name}] OK ({latency:.0f}ms)")
        time.sleep(60)

if __name__ == "__main__":
    run()
