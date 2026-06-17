"""
EVEZ-OS GitHub Push Daemon
Background service that watches for write access and pushes when available.
Also creates a git bundle as backup state persistence.
"""
import json, os, subprocess, time, threading
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler

WORKSPACE = Path("/home/openclaw/.openclaw/workspace")
CLASSIC_PAT_FILE = "/tmp/github_classic_token.txt"
REPOS = [
    
    {"remote": "evez666", "url": "https://github.com/EvezArt/Evez666.git"},
]
BUNDLE_DIR = Path("/tmp/evez_git_bundles")
BUNDLE_DIR.mkdir(parents=True, exist_ok=True)

class PushDaemon:
    def __init__(self, interval=300):
        self.interval = interval
        self.push_log = []
        self.last_bundle = 0
    
    def try_push_all(self) -> dict:
        """Try pushing to all remotes."""
        results = {}
        for repo in REPOS:
            remote = repo["remote"]
            try:
                result = subprocess.run(
                    ["git", "push", remote, "main"],
                    capture_output=True, text=True, timeout=60,
                    cwd=str(WORKSPACE),
                )
                success = result.returncode == 0
                results[remote] = {
                    "success": success,
                    "output": (result.stdout + result.stderr)[:200],
                }
                if success:
                    self.push_log.append({"remote": remote, "time": time.time(), "success": True})
            except Exception as e:
                results[remote] = {"success": False, "error": str(e)[:100]}
        return results
    
    def create_bundle(self) -> dict:
        """Create a git bundle as local backup."""
        bundle_path = BUNDLE_DIR / f"evez-os-{int(time.time())}.bundle"
        try:
            result = subprocess.run(
                ["git", "bundle", "create", str(bundle_path), "--all"],
                capture_output=True, text=True, timeout=120,
                cwd=str(WORKSPACE),
            )
            if result.returncode == 0:
                size = bundle_path.stat().st_size / 1024
                self.last_bundle = time.time()
                # Keep only last 5 bundles
                bundles = sorted(BUNDLE_DIR.glob("*.bundle"))
                for old in bundles[:-5]:
                    old.unlink()
                return {"success": True, "path": str(bundle_path), "size_kb": round(size)}
            return {"success": False, "error": result.stderr[:100]}
        except Exception as e:
            return {"success": False, "error": str(e)[:100]}
    
    def auto_commit(self) -> dict:
        """Auto-commit any uncommitted changes."""
        try:
            # Clean backups
            subprocess.run(["find", "evez-os-sensors", "-name", "*_backup_*", "-delete"],
                         cwd=str(WORKSPACE), capture_output=True)
            subprocess.run(["git", "add", "-A"], cwd=str(WORKSPACE), capture_output=True)
            result = subprocess.run(
                ["git", "commit", "-m", f"auto: state persistence {time.strftime('%Y-%m-%dT%H:%MZ', time.gmtime())}"],
                cwd=str(WORKSPACE), capture_output=True, text=True,
            )
            committed = "nothing to commit" not in result.stdout
            return {"committed": committed, "output": result.stdout[:100]}
        except Exception as e:
            return {"committed": False, "error": str(e)[:100]}


daemon = PushDaemon()

class PushHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self._json({"name": "EVEZ-OS GitHub Push Daemon", "pushes": len(daemon.push_log), "last_bundle": daemon.last_bundle})
        elif self.path == "/api/status":
            self._json({"push_log": daemon.push_log[-10:], "last_bundle": daemon.last_bundle})
        else:
            self._json({"error": "Not found"}, 404)
    
    def do_POST(self):
        if self.path == "/api/push":
            result = daemon.try_push_all()
            self._json(result)
        elif self.path == "/api/bundle":
            result = daemon.create_bundle()
            self._json(result)
        elif self.path == "/api/commit":
            result = daemon.auto_commit()
            self._json(result)
        elif self.path == "/api/commit-and-push":
            c = daemon.auto_commit()
            p = daemon.try_push_all()
            self._json({"commit": c, "push": p})
        else:
            self._json({"error": "Not found"}, 404)
    
    def _json(self, data, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2, default=str).encode())
    
    def log_message(self, *a): pass


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--port", type=int, default=9101)
    args = p.parse_args()
    
    # Create initial bundle
    daemon.create_bundle()
    
    print(f"\n  GitHub Push Daemon: http://0.0.0.0:{args.port}")
    print(f"  POST /api/commit-and-push — commit and push to all remotes")
    print(f"  POST /api/bundle — create git bundle backup")
    print()
    
    server = HTTPServer(("0.0.0.0", args.port), PushHandler)
    server.serve_forever()


if __name__ == "__main__":
    main()
