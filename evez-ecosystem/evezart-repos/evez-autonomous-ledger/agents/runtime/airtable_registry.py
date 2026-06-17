#!/usr/bin/env python3
"""
EVEZ Airtable Registry — hourly.
Pushes live pulse.json state into two Airtable tables:
  1. EVEZ_SYSTEM_LOG — append-only pulse record per epoch
  2. EVEZ_BLOCKERS — upserts current open issues tagged [BLOCKER] or [BUILD]
     including the Botpress blockage as a first-class registered item.

Requires AIRTABLE_API_KEY and AIRTABLE_BASE_ID secrets.
Gracefully no-ops if secrets are absent (system continues without Airtable).
"""
import os, json, datetime, requests, base64

GH_TOKEN = os.environ.get("GITHUB_TOKEN", "")
AIRTABLE_KEY = os.environ.get("AIRTABLE_API_KEY", "")
AIRTABLE_BASE = os.environ.get("AIRTABLE_BASE_ID", "")
ABLY_KEY = os.environ.get("ABLY_KEY", "")
OWNER = "EvezArt"
REPO = "evez-autonomous-ledger"
GH_HEADERS = {"Authorization": f"Bearer {GH_TOKEN}", "Accept": "application/vnd.github+json",
              "X-GitHub-Api-Version": "2022-11-28"}

WATCHED_REPOS = ["evez-autonomous-ledger","evez-agentnet","agentvault","evez-meme-bus","Evez666","evez-os"]

# Known blockers to always register (even without an open issue)
SEED_BLOCKERS = [
    {"title": "[BLOCKER] Botpress integration not wired to evez-agentnet",
     "repo": "evez-agentnet", "priority": "HIGH",
     "description": "Botpress chatbot pipeline has no live connection to agentnet. Blocks conversational interface layer."},
    {"title": "[BLOCKER] ANTHROPIC_API_KEY not set in all target repos",
     "repo": "evez-autonomous-ledger", "priority": "CRITICAL",
     "description": "Cognition loop, hypothesis engine, dream engine, oracle, PR drafter all require this secret."},
    {"title": "[BLOCKER] AIRTABLE_API_KEY not configured",
     "repo": "evez-autonomous-ledger", "priority": "HIGH",
     "description": "Airtable registry agent is running but cannot push records without this secret."},
]

def now_iso(): return datetime.datetime.utcnow().isoformat() + "Z"

def get_pulse():
    try:
        r = requests.get(f"https://api.github.com/repos/{OWNER}/{REPO}/contents/runtime/pulse.json", headers=GH_HEADERS, timeout=15)
        if r.status_code == 200:
            try: return json.loads(base64.b64decode(r.json()["content"]).decode())
            except: pass
    except Exception as e:
        print(f"  ⚠️  get_pulse failed: {e}")
    return {}

def get_open_blockers():
    blockers = []
    try:
        for repo in WATCHED_REPOS:
            url = f"https://api.github.com/repos/{OWNER}/{repo}/issues?state=open&per_page=30"
            r = requests.get(url, headers=GH_HEADERS, timeout=15)
            if r.status_code != 200: continue
            for issue in r.json():
                if "pull_request" in issue: continue
                title = issue.get("title","")
                if any(tag in title for tag in ["[BLOCKER]","[BUILD]","[HYPOTHESIS]","[EVOLUTION]","[IMMUNE"]):
                    blockers.append({
                        "title": title[:100],
                        "repo": repo,
                        "url": issue.get("html_url",""),
                        "state": "open",
                        "created_at": issue.get("created_at",""),
                        "priority": "CRITICAL" if "IMMUNE" in title or "BLOCKER" in title else "HIGH" if "BUILD" in title else "NORMAL",
                    })
    except Exception as e:
        print(f"  ⚠️  get_open_blockers failed: {e}")
    return blockers

def push_to_airtable(table, records):
    if not AIRTABLE_KEY or not AIRTABLE_BASE:
        print(f"  ⚠️  Airtable not configured — skipping push to {table}")
        return []
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE}/{table}"
    headers = {"Authorization": f"Bearer {AIRTABLE_KEY}", "Content-Type": "application/json"}
    created = []
    for i in range(0, len(records), 10):  # Airtable batch limit = 10
        batch = records[i:i+10]
        try:
            r = requests.post(url, headers=headers, json={"records": [{"fields": rec} for rec in batch]}, timeout=15)
            if r.status_code in (200, 201):
                created.extend(r.json().get("records", []))
        except Exception as e:
            print(f"  ⚠️  push_to_airtable batch failed: {e}")
    return created

def update_pulse_with_airtable_id(record_id):
    try:
        r = requests.get(f"https://api.github.com/repos/{OWNER}/{REPO}/contents/runtime/pulse.json", headers=GH_HEADERS, timeout=15)
        if r.status_code != 200: return
        pulse = json.loads(base64.b64decode(r.json()["content"]).decode())
        sha = r.json().get("sha","")
        pulse["airtable_synced"] = True
        pulse["airtable_record_id"] = record_id
        content = base64.b64encode(json.dumps(pulse, indent=2).encode()).decode()
        requests.put(f"https://api.github.com/repos/{OWNER}/{REPO}/contents/runtime/pulse.json",
            headers=GH_HEADERS, json={"message": f"🗂 airtable sync confirmed: {record_id}", "content": content, "sha": sha}, timeout=15)
    except Exception as e:
        print(f"  ⚠️  update_pulse_with_airtable_id failed: {e}")

def main():
    try:
        print(f"\n🗂 EVEZ Airtable Registry — {now_iso()}")
        pulse = get_pulse()
        print(f"  Pulse epoch: {pulse.get('epoch','?')} | Phi: {pulse.get('phi','?')}")
        # Push pulse as system log record
        log_record = {
            "Epoch": pulse.get("epoch", 0),
            "Timestamp": pulse.get("timestamp", now_iso()),
            "Phi": pulse.get("phi", 0),
            "Phi Level": pulse.get("phi_level", ""),
            "Latency Mode": pulse.get("latency_mode", ""),
            "Agents Active": pulse.get("agents_active", 0),
            "Decisions Total": pulse.get("decisions_total", 0),
            "Trajectory Vector": pulse.get("trajectory", {}).get("trajectory_vector", ""),
            "Basin Distance": pulse.get("trajectory", {}).get("basin_distance", 0),
            "Immune Status": pulse.get("immune", {}).get("status", ""),
            "BTC USD": pulse.get("market", {}).get("btc_usd", 0),
            "Fear Greed": pulse.get("market", {}).get("fear_greed", 0),
            "Hash": pulse.get("hash", ""),
        }
        log_results = push_to_airtable("EVEZ_SYSTEM_LOG", [log_record])
        if log_results:
            record_id = log_results[0].get("id", "")
            update_pulse_with_airtable_id(record_id)
            print(f"  ✅ System log pushed: {record_id}")
        # Collect and push blockers
        blockers = get_open_blockers()
        # Merge in seed blockers if not already present by title
        existing_titles = {b["title"] for b in blockers}
        for seed in SEED_BLOCKERS:
            if seed["title"] not in existing_titles:
                blockers.append({**seed, "url": "", "state": "open", "created_at": now_iso()})
        print(f"  Blockers to register: {len(blockers)}")
        blocker_records = [{
            "Title": b["title"],
            "Repo": b["repo"],
            "URL": b.get("url",""),
            "Priority": b.get("priority","NORMAL"),
            "State": b.get("state","open"),
            "Description": b.get("description",""),
            "Registered At": now_iso(),
        } for b in blockers]
        blocker_results = push_to_airtable("EVEZ_BLOCKERS", blocker_records)
        print(f"  {'✅' if blocker_results else '⚠️ '} {len(blocker_results)} blocker records pushed")
        try:
            if ABLY_KEY:
                ki, ks = ABLY_KEY.split(":")
                requests.post("https://rest.ably.io/channels/evez-ops/messages",
                    json={"name": "AIRTABLE_SYNC", "data": json.dumps({
                        "epoch": pulse.get("epoch"), "log_records": len(log_results),
                        "blockers": len(blocker_results)
                    })}, auth=(ki, ks), timeout=15)
        except Exception as e:
            print(f"  ⚠️  Ably broadcast failed: {e}")
        print("  ✅ Airtable registry cycle complete.")
    except Exception as e:
        print(f"  ❌ main() failed: {e}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ airtable_registry crashed: {e}")
        exit(0)
