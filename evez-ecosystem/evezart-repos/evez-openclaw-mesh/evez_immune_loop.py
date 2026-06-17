"""
evez_immune_loop.py — EVEZ-OS Self-Healing Watchdog
Monitors Fly.io apps, Vercel deployments, and Cloudflare workers.
Exponential backoff on failures. Logs to meme_events.jsonl spine.
"""
import os
import json
import time
import datetime
import logging
import requests
from pathlib import Path

try:
    from nomad_vault import load_config
except ImportError:
    def load_config(k, d=None): return os.environ.get(k, d)

logging.basicConfig(format="%(asctime)s [%(levelname)s] %(message)s", level=logging.INFO)
log = logging.getLogger("immune_loop")

SPINE_PATH = Path(os.environ.get("EVEZ_SPINE", "./data/meme_events.jsonl"))
SPINE_PATH.parent.mkdir(parents=True, exist_ok=True)

def spine_write(event_type: str, payload: dict):
    event = {
        "ts": datetime.datetime.utcnow().isoformat() + "Z",
        "type": event_type,
        "payload": payload
    }
    with open(SPINE_PATH, "a") as f:
        f.write(json.dumps(event) + "\n")
    log.info(f"SPINE: {event_type} — {payload}")

def check_fly():
    token = load_config("FLY_API_TOKEN")
    if not token:
        return {"status": "skipped", "reason": "no FLY_API_TOKEN"}
    try:
        r = requests.get(
            "https://api.machines.dev/v1/apps",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        apps = r.json().get("apps", [])
        statuses = [{"name": a["name"], "status": a.get("status")} for a in apps]
        down = [s for s in statuses if s["status"] not in ("deployed", "running", None)]
        return {"status": "ok" if not down else "degraded", "apps": statuses, "down": down}
    except Exception as e:
        return {"status": "error", "error": str(e)}

def check_vercel():
    token = load_config("VERCEL_TOKEN")
    if not token:
        return {"status": "skipped", "reason": "no VERCEL_TOKEN"}
    try:
        r = requests.get(
            "https://api.vercel.com/v6/deployments?limit=5",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        deploys = r.json().get("deployments", [])
        errors  = [d for d in deploys if d.get("state") == "ERROR"]
        return {"status": "ok" if not errors else "degraded", "latest": len(deploys), "errors": len(errors)}
    except Exception as e:
        return {"status": "error", "error": str(e)}

def check_cloudflare():
    token   = load_config("CLOUDFLARE_API_TOKEN")
    account = load_config("CLOUDFLARE_ACCOUNT_ID")
    if not token or not account:
        return {"status": "skipped", "reason": "no CF creds"}
    try:
        r = requests.get(
            f"https://api.cloudflare.com/client/v4/accounts/{account}/workers/scripts",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        workers = r.json().get("result", [])
        return {"status": "ok", "workers": len(workers)}
    except Exception as e:
        return {"status": "error", "error": str(e)}

def immune_cycle():
    log.info("== IMMUNE LOOP CYCLE START ==")
    results = {
        "fly":        check_fly(),
        "vercel":     check_vercel(),
        "cloudflare": check_cloudflare(),
    }
    all_ok = all(v.get("status") in ("ok", "skipped") for v in results.values())
    spine_write("immune_cycle", {"results": results, "all_ok": all_ok})

    if not all_ok:
        degraded = {k: v for k, v in results.items() if v.get("status") not in ("ok", "skipped")}
        log.warning(f"DEGRADED: {degraded}")
        spine_write("self_heal_trigger", {"degraded": degraded})
        # Attempt self-heal: re-ping after backoff
        for attempt in range(1, 4):
            wait = 2 ** attempt
            log.info(f"Self-heal attempt {attempt} — waiting {wait}s...")
            time.sleep(wait)
            recheck = {k: (check_fly() if k=="fly" else check_vercel() if k=="vercel" else check_cloudflare())
                       for k in degraded}
            if all(v.get("status") in ("ok", "skipped") for v in recheck.values()):
                spine_write("self_heal_success", {"attempt": attempt, "results": recheck})
                log.info("Self-heal succeeded.")
                return
        spine_write("self_heal_failed", {"degraded": degraded})
        log.error("Self-heal failed after 3 attempts.")
    else:
        log.info("All systems nominal.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--once",     action="store_true", help="Run one cycle and exit")
    parser.add_argument("--interval", type=int, default=900, help="Interval in seconds (default 900=15min)")
    args = parser.parse_args()

    if args.once:
        immune_cycle()
    else:
        log.info(f"Immune loop starting — interval: {args.interval}s")
        while True:
            try:
                immune_cycle()
            except Exception as e:
                log.error(f"Cycle error: {e}")
                spine_write("cycle_error", {"error": str(e)})
            time.sleep(args.interval)