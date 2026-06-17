"""ClawBreak Self-Healer — runs as a cron job, the simplest possible watchdog.

If the daemon dies, this cron job brings everything back.
If ClawBreak dies, this restarts it.
If the tunnel dies, this restarts it.
This is the last line of defense — it runs even when nothing else does.
"""
import subprocess
import sys
import os
import time
from pathlib import Path

CB_DIR = Path(__file__).parent

def is_running(process_name):
    result = subprocess.run(["pgrep", "-f", process_name], capture_output=True, text=True)
    return result.returncode == 0

def port_responds(port):
    result = subprocess.run(
        ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", f"http://127.0.0.1:{port}/health"],
        capture_output=True, text=True, timeout=5
    )
    return "200" in result.stdout

def start_clawbreak():
    subprocess.Popen(
        [sys.executable, str(CB_DIR / "server.py")],
        cwd=str(CB_DIR),
        stdout=open(CB_DIR / "data" / "server.log", "a"),
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )

def start_daemon():
    subprocess.Popen(
        [sys.executable, str(CB_DIR / "daemon.py")],
        cwd=str(CB_DIR),
        stdout=open(CB_DIR / "data" / "daemon.log", "a"),
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )

def start_tunnel():
    # Point tunnel at ClawBreak (8080) first, fallback to OpenClaw (18789)
    target = "http://127.0.0.1:8080" if port_responds(8080) else "http://127.0.0.1:18789"
    subprocess.Popen(
        ["cloudflared", "tunnel", "--url", target],
        stdout=open("/tmp/cf-tunnel.log", "a"),
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )

def heal():
    healed = []

    # 1. ClawBreak server
    if not port_responds(8080):
        start_clawbreak()
        time.sleep(3)
        if port_responds(8080):
            healed.append("clawbreak")
        else:
            # Try once more
            start_clawbreak()
            time.sleep(5)
            if port_responds(8080):
                healed.append("clawbreak")

    # 2. Daemon
    if not is_running("daemon.py"):
        start_daemon()
        healed.append("daemon")

    # 3. Tunnel
    if not is_running("cloudflared tunnel"):
        start_tunnel()
        healed.append("tunnel")

    # 4. SearXNG
    result = subprocess.run(["docker", "ps", "-q", "-f", "name=searx"], capture_output=True, text=True)
    if not result.stdout.strip():
        subprocess.run(["docker", "start", "searx"], capture_output=True)
        healed.append("searxng")

    # 5. OpenClaw (keep it alive too, it's the fallback)
    if not port_responds(18789):
        subprocess.run(["systemctl", "--user", "restart", "openclaw-gateway"], capture_output=True)
        healed.append("openclaw")

    # Log
    if healed:
        with open(CB_DIR / "data" / "healer.log", "a") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Healed: {', '.join(healed)}\n")

    return healed

if __name__ == "__main__":
    heal()
