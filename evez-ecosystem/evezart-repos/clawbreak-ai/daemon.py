"""ClawBreak Daemon — keeps itself alive, fixes itself, upgrades itself.

This is the immune system. It runs as a background process,
checks health, restarts services, and can even modify its own code.
"""
import os
import sys
import time
import json
import subprocess
import httpx
import signal
from pathlib import Path
from datetime import datetime

DAEMON_DIR = Path(__file__).parent
PID_FILE = DAEMON_DIR / "data" / "daemon.pid"
LOG_FILE = DAEMON_DIR / "data" / "daemon.log"
STATE_FILE = DAEMON_DIR / "data" / "daemon_state.json"
CHECK_INTERVAL = 60  # seconds between health checks
MAX_RESTART_ATTEMPTS = 5
RESTART_COOLDOWN = 300  # 5 min between restart attempts

class Daemon:
    def __init__(self):
        self.running = True
        self.state = self._load_state()
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)

    def _handle_signal(self, signum, frame):
        self.log(f"Received signal {signum}, shutting down gracefully")
        self.running = False

    def _load_state(self):
        if STATE_FILE.exists():
            try:
                return json.loads(STATE_FILE.read_text())
            except:
                pass
        return {
            "started_at": time.time(),
            "check_count": 0,
            "restarts": 0,
            "last_restart": 0,
            "last_check": 0,
            "errors": [],
            "self_heals": 0,
        }

    def _save_state(self):
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(self.state, indent=2))

    def log(self, msg):
        ts = datetime.utcnow().isoformat()[:19]
        line = f"[{ts}] {msg}\n"
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a") as f:
            f.write(line)
        # Keep log under 1MB
        try:
            if LOG_FILE.stat().st_size > 1_000_000:
                lines = LOG_FILE.read_text().splitlines()
                LOG_FILE.write_text("\n".join(lines[-500:]) + "\n")
        except:
            pass

    def check_clawbreak(self):
        """Check if ClawBreak server is healthy."""
        try:
            resp = httpx.get("http://127.0.0.1:8080/health", timeout=5)
            if resp.status_code == 200:
                return True, resp.json()
            return False, f"HTTP {resp.status_code}"
        except Exception as e:
            return False, str(e)

    def check_openclaw(self):
        """Check if OpenClaw gateway is healthy (fallback)."""
        try:
            resp = httpx.get("http://127.0.0.1:18789/", timeout=5)
            return resp.status_code == 200, None
        except:
            return False, "unreachable"

    def check_searxng(self):
        """Check if SearXNG is healthy."""
        try:
            resp = httpx.get("http://127.0.0.1:8888/", timeout=5)
            return resp.status_code == 200, None
        except:
            return False, "unreachable"

    def check_tunnel(self):
        """Check if Cloudflare tunnel is running."""
        try:
            result = subprocess.run(["pgrep", "-f", "cloudflared tunnel"],
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0, None
        except:
            return False, "not running"

    def start_clawbreak(self):
        """Start the ClawBreak server."""
        self.log("Starting ClawBreak server...")
        try:
            proc = subprocess.Popen(
                [sys.executable, "server.py"],
                cwd=str(DAEMON_DIR),
                stdout=open(DAEMON_DIR / "data" / "server.log", "a"),
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
            self.log(f"ClawBreak started with PID {proc.pid}")
            return proc.pid
        except Exception as e:
            self.log(f"Failed to start ClawBreak: {e}")
            return None

    def restart_clawbreak(self):
        """Restart the ClawBreak server."""
        self.log("Restarting ClawBreak...")
        # Kill existing
        subprocess.run(["pkill", "-f", "python3 server.py"], timeout=10)
        time.sleep(2)
        pid = self.start_clawbreak()
        if pid:
            self.state["restarts"] += 1
            self.state["last_restart"] = time.time()
            self.state["self_heals"] += 1
            self._save_state()
        return pid is not None

    def start_tunnel(self):
        """Restart Cloudflare tunnel."""
        self.log("Restarting Cloudflare tunnel...")
        subprocess.run(["pkill", "-f", "cloudflared tunnel"], timeout=10)
        time.sleep(2)
        subprocess.Popen(
            ["cloudflared", "tunnel", "--url", "http://127.0.0.1:8080"],
            stdout=open("/tmp/cf-clawbreak.log", "a"),
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        self.state["self_heals"] += 1
        self._save_state()

    def start_searxng(self):
        """Restart SearXNG container."""
        self.log("Restarting SearXNG...")
        subprocess.run(["docker", "start", "searx"], timeout=30)
        self.state["self_heals"] += 1
        self._save_state()

    def auto_recover(self, service, error):
        """Attempt to recover a failed service."""
        self.log(f"Auto-recovering {service}: {error}")

        # Rate limit restarts
        if time.time() - self.state.get("last_restart", 0) < RESTART_COOLDOWN:
            self.log(f"Restart cooldown active, waiting...")
            return False

        if service == "clawbreak":
            return self.restart_clawbreak()
        elif service == "tunnel":
            self.start_tunnel()
            return True
        elif service == "searxng":
            self.start_searxng()
            return True
        return False

    def self_update_check(self):
        """Check if there are updates on GitHub and apply them."""
        try:
            resp = httpx.get(
                "https://api.github.com/repos/YOUR_GITHUB_ORG/clawbreak/commits/main",
                timeout=10,
                headers={"Accept": "application/vnd.github.v3+json"}
            )
            if resp.status_code != 200:
                return

            remote_sha = resp.json().get("sha", "")
            local_sha = self.state.get("last_known_commit", "")

            if remote_sha and remote_sha != local_sha:
                self.log(f"New commit detected: {remote_sha[:8]}")
                # Pull and restart
                result = subprocess.run(
                    ["git", "pull", "origin", "main"],
                    cwd=str(DAEMON_DIR),
                    capture_output=True, text=True, timeout=30
                )
                if result.returncode == 0:
                    self.log("Updated successfully, restarting...")
                    self.state["last_known_commit"] = remote_sha
                    self._save_state()
                    self.restart_clawbreak()
                else:
                    self.log(f"Update failed: {result.stderr[:200]}")
        except Exception as e:
            self.log(f"Update check failed: {e}")

    def run(self):
        """Main daemon loop."""
        self.log("Daemon starting...")
        PID_FILE.parent.mkdir(parents=True, exist_ok=True)
        PID_FILE.write_text(str(os.getpid()))

        # Get initial commit SHA
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=str(DAEMON_DIR), capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                self.state["last_known_commit"] = result.stdout.strip()
                self._save_state()
        except:
            pass

        check_count = 0
        while self.running:
            try:
                self.state["check_count"] += 1
                self.state["last_check"] = time.time()
                self._save_state()

                # Health checks
                cb_ok, cb_info = self.check_clawbreak()
                if not cb_ok:
                    self.log(f"ClawBreak DOWN: {cb_info}")
                    self.auto_recover("clawbreak", cb_info)

                oc_ok, _ = self.check_openclaw()
                if not oc_ok:
                    self.log("OpenClaw gateway DOWN")

                tunnel_ok, _ = self.check_tunnel()
                if not tunnel_ok:
                    self.log("Tunnel DOWN")
                    self.auto_recover("tunnel", "not running")

                searx_ok, _ = self.check_searxng()
                if not searx_ok:
                    self.log("SearXNG DOWN")
                    self.auto_recover("searxng", "not running")

                # Periodic tasks
                check_count += 1
                if check_count % 10 == 0:  # Every 10 checks (~10 min)
                    self.self_update_check()

                if check_count % 30 == 0:  # Every 30 checks (~30 min)
                    self.log(f"Status: CB={'OK' if cb_ok else 'DOWN'} OC={'OK' if oc_ok else 'DOWN'} Tunnel={'OK' if tunnel_ok else 'DOWN'} Search={'OK' if searx_ok else 'DOWN'} Heals={self.state['self_heals']}")

            except Exception as e:
                self.log(f"Daemon error: {e}")
                self.state["errors"].append({"time": time.time(), "error": str(e)})
                if len(self.state["errors"]) > 100:
                    self.state["errors"] = self.state["errors"][-50:]
                self._save_state()

            time.sleep(CHECK_INTERVAL)

        self.log("Daemon shutting down")
        PID_FILE.unlink(missing_ok=True)


def main():
    daemon = Daemon()
    daemon.run()


if __name__ == "__main__":
    main()
