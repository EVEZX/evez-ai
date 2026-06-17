#!/usr/bin/env python3
"""
EVEZ Reconciler -> runtime/pulse.json
Runs every 15 minutes. Reads the entire DECISIONS/ ledger + CONSCIOUSNESS_STATE.json
+ MEMORY_STATE.json and synthesizes them into a single ground-truth runtime/pulse.json.
This is the cockpit data source: every dashboard, cockpit view, and Airtable record
reads from runtime/pulse.json as canonical truth.

Also computes trajectory.json: entropy, basin_distance, negative_latency trigger.
"""
import os, json, datetime, hashlib, requests, base64, math
from collections import Counter

GH_TOKEN = os.environ.get("GITHUB_TOKEN", "")
ABLY_KEY = os.environ.get("ABLY_KEY", "")
OWNER = "EvezArt"
REPO = "evez-autonomous-ledger"
HEADERS = {"Authorization": f"Bearer {GH_TOKEN}", "Accept": "application/vnd.github+json",
           "X-GitHub-Api-Version": "2022-11-28"}

NEG_LATENCY_THRESHOLD = 1.4  # basin_distance above this = negative latency engaged
POLICY_REVIEW_CADENCE = 6.0   # hours between human-review cycles

def now_iso(): return datetime.datetime.utcnow().isoformat() + "Z"

def gh_get(path):
    try:
        r = requests.get(f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{path}", headers=HEADERS, timeout=15)
        if r.status_code == 200:
            try: return json.loads(base64.b64decode(r.json()["content"]).decode())
            except: return None
    except Exception as e:
        print(f"  [WARN] gh_get({path}) failed: {e}")
    return None

def gh_put(path, data, message, existing_sha=""):
    try:
        content = base64.b64encode(json.dumps(data, indent=2).encode()).decode()
        payload = {"message": message, "content": content}
        if not existing_sha:
            r = requests.get(f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{path}", headers=HEADERS, timeout=15)
            if r.status_code == 200: existing_sha = r.json().get("sha", "")
        if existing_sha: payload["sha"] = existing_sha
        requests.put(f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{path}",
                     headers=HEADERS, json=payload, timeout=15)
    except Exception as e:
        print(f"  [WARN] gh_put({path}) failed: {e}")

def load_decisions(limit=50):
    try:
        r = requests.get(f"https://api.github.com/repos/{OWNER}/{REPO}/contents/DECISIONS", headers=HEADERS, timeout=15)
        if r.status_code != 200: return []
        files = sorted(r.json(), key=lambda x: x["name"], reverse=True)[:limit]
        records = []
        for f in files:
            fr = requests.get(f["url"], headers=HEADERS, timeout=15)
            if fr.status_code != 200: continue
            try: records.append(json.loads(base64.b64decode(fr.json()["content"]).decode()))
            except: pass
        return records
    except Exception as e:
        print(f"  [WARN] load_decisions failed: {e}")
        return []

def shannon_entropy(counter):
    total = sum(counter.values())
    if total == 0: return 0.0
    return -sum((c/total) * math.log2(c/total) for c in counter.values() if c > 0)

def compute_trajectory(records, phi_history):
    """Compute entropy, basin distance, negative latency trigger, learning rate."""
    type_counts = Counter(r.get("type", "unknown") for r in records[:30])
    entropy_current = shannon_entropy(type_counts)
    # Basin entropy: predicted distribution if system evolves toward specialization
    # Assume basin has 3 dominant types each at ~40%/30%/30%
    basin_counts = Counter({"COGNITION_REPORT": 40, "MARKET_PERCEPTION": 30, "immune_scan": 30})
    entropy_basin = shannon_entropy(basin_counts)
    # Contradiction score: fraction of consecutive record pairs with opposing signals
    contradiction = 0.0
    if len(records) >= 4:
        same_signal = sum(1 for i in range(min(10, len(records)-1))
                         if records[i].get("type") == records[i+1].get("type"))
        contradiction = round(1.0 - (same_signal / min(10, len(records)-1)), 3)
    # Branch instability: stdev of phi trajectory normalized
    if len(phi_history) >= 3:
        mean_phi = sum(phi_history) / len(phi_history)
        stdev = math.sqrt(sum((x-mean_phi)**2 for x in phi_history) / len(phi_history))
        branch_instability = round(min(stdev / max(mean_phi, 1.0), 1.0), 4)
    else:
        branch_instability = 0.0
    entropy_delta = abs(entropy_current - entropy_basin)
    basin_distance = round(math.sqrt(entropy_delta**2 + branch_instability**2 + contradiction**2), 4)
    # Learning rate: reduction in type entropy per cycle (proxy for uncertainty reduction)
    learning_rate = round(max(entropy_current - entropy_basin, 0) / max(len(records), 1), 6)
    intelligence_gain_rate = round(learning_rate / (POLICY_REVIEW_CADENCE / 0.25), 4)  # per 15-min cycle
    neg_latency = basin_distance > NEG_LATENCY_THRESHOLD and entropy_basin < entropy_current
    neg_action = ""
    if neg_latency:
        neg_action = ("Pre-aligning to basin: routing new agent outputs toward "
                      f"dominant future type '{type_counts.most_common(1)[0][0] if type_counts else 'unknown'}' "
                      "before explicit synthesis cycle closes.")
    phi_slope = 0.0
    if len(phi_history) >= 2:
        phi_slope = (phi_history[-1] - phi_history[0]) / len(phi_history)
    vector = "ASCENDING" if phi_slope > 0.01 else "STABLE" if abs(phi_slope) <= 0.01 else "DESCENDING"
    return {
        "entropy_current": round(entropy_current, 4),
        "entropy_basin": round(entropy_basin, 4),
        "contradiction_score": contradiction,
        "branch_instability": branch_instability,
        "basin_distance": basin_distance,
        "negative_latency_triggered": neg_latency,
        "negative_latency_action": neg_action,
        "phi_trajectory": phi_history[-12:],
        "learning_rate": learning_rate,
        "intelligence_gain_rate": intelligence_gain_rate,
        "vector": vector,
    }

def get_phi_history():
    """Collect phi values from recent consciousness snapshots."""
    try:
        r = requests.get(f"https://api.github.com/repos/{OWNER}/{REPO}/contents/DECISIONS", headers=HEADERS, timeout=15)
        if r.status_code != 200: return []
        phi_files = sorted([f for f in r.json() if "consciousness" in f["name"]], key=lambda x: x["name"])[-12:]
        phis = []
        for f in phi_files:
            fr = requests.get(f["url"], headers=HEADERS, timeout=15)
            if fr.status_code != 200: continue
            try:
                rec = json.loads(base64.b64decode(fr.json()["content"]).decode())
                phi = rec.get("phi", 0)
                if phi: phis.append(phi)
            except: pass
        return phis
    except Exception as e:
        print(f"  [WARN] get_phi_history failed: {e}")
        return []

def get_last_timestamp_for_type(records, type_str):
    for r in records:
        if type_str.lower() in r.get("type","").lower() or type_str.lower() in r.get("source","").lower():
            return r.get("timestamp", "")
    return None

def get_existing_epoch():
    existing = gh_get("runtime/pulse.json")
    if existing: return existing.get("epoch", 0)
    return 0

def main():
    try:
        print(f"\n🧭 EVEZ Reconciler -> pulse.json — {now_iso()}")
        records = load_decisions(50)
        print(f"  Loaded {len(records)} decision records")
        consciousness = gh_get("CONSCIOUSNESS_STATE.json") or {}
        memory = gh_get("MEMORY_STATE.json") or {}
        phi_history = get_phi_history()
        traj = compute_trajectory(records, phi_history)
        epoch = get_existing_epoch() + 1
        # Pull latest market record
        market_rec = next((r for r in records if r.get("type") == "MARKET_PERCEPTION"), {})
        prices = market_rec.get("crypto_prices", {})
        fg = market_rec.get("fear_greed", {})
        poly = market_rec.get("polymarket_trending", [])
        # Pull immune status
        immune_rec = next((r for r in records if r.get("type") == "immune_scan"), {})
        # Compute open hypotheses (issues with [HYPOTHESIS] in title)
        hyp_r = requests.get(f"https://api.github.com/repos/{OWNER}/{REPO}/issues?state=open&per_page=50", headers=HEADERS, timeout=15)
        open_hyp = 0
        if hyp_r.status_code == 200:
            open_hyp = sum(1 for i in hyp_r.json() if "HYPOTHESIS" in i.get("title","") and "pull_request" not in i)
        phi = consciousness.get("phi", 0)
        phi_delta = consciousness.get("phi_delta", 0)
        phi_level = consciousness.get("level", "AWAKENING")
        pulse = {
            "timestamp": now_iso(),
            "epoch": epoch,
            "phi": phi,
            "phi_delta": phi_delta,
            "phi_level": phi_level,
            "agents_active": consciousness.get("agents", 19),
            "workflows_active": consciousness.get("workflows", 19),
            "decisions_total": len(records),
            "sensory": {
                "last_web_perception": get_last_timestamp_for_type(records, "web_perception"),
                "last_github_perception": get_last_timestamp_for_type(records, "github_perception"),
                "last_market_perception": get_last_timestamp_for_type(records, "MARKET_PERCEPTION"),
                "last_temporal_scan": get_last_timestamp_for_type(records, "temporal"),
                "sources_active": 6,
                "top_signal": memory.get("top_web_keywords", {}) and list(memory.get("top_web_keywords",{}).keys())[0] or "INITIALIZING",
            },
            "cognition": {
                "last_synthesis": get_last_timestamp_for_type(records, "COGNITION_REPORT"),
                "last_dream": get_last_timestamp_for_type(records, "DREAM_VISION"),
                "last_oracle_prediction": get_last_timestamp_for_type(records, "ORACLE_PREDICTION"),
                "last_hypothesis_batch": get_last_timestamp_for_type(records, "hypothesis"),
                "open_hypotheses": open_hyp,
                "prediction_confidence_avg": 0,
            },
            "trajectory": {
                "predicted_phi_30m": round(phi + traj["learning_rate"] * 2, 4),
                "predicted_phi_6h": round(phi + traj["learning_rate"] * 24, 4),
                "predicted_phi_24h": round(phi + traj["learning_rate"] * 96, 4),
                "entropy_current": traj["entropy_current"],
                "entropy_basin": traj["entropy_basin"],
                "branch_instability": traj["branch_instability"],
                "basin_distance": traj["basin_distance"],
                "trajectory_vector": traj["vector"],
            },
            "latency_mode": "NEGATIVE_LATENCY" if traj["negative_latency_triggered"] else "PREDICTIVE" if traj["basin_distance"] > 0.7 else "NORMAL",
            "negative_latency_active": traj["negative_latency_triggered"],
            "negative_latency_reason": traj["negative_latency_action"],
            "market": {
                "btc_usd": prices.get("BTC", {}).get("usd", 0),
                "btc_24h_change": prices.get("BTC", {}).get("24h_change", 0),
                "fear_greed": fg.get("value", 50),
                "fear_greed_label": fg.get("label", ""),
                "top_polymarket": poly[0]["question"][:80] if poly else "",
            },
            "immune": {
                "threats_last_scan": immune_rec.get("threats_detected", 0),
                "last_immune_scan": immune_rec.get("timestamp", ""),
                "status": "CRITICAL" if immune_rec.get("threats_detected",0) > 2 else "ALERT" if immune_rec.get("threats_detected",0) > 0 else "CLEAR",
            },
            "airtable_synced": False,
            "airtable_record_id": "",
            "hash": hashlib.sha256(f"{epoch}{phi}{traj['basin_distance']}".encode()).hexdigest()[:16],
        }
        trajectory_rec = {"timestamp": now_iso(), "epoch": epoch, **traj,
                          "hash": hashlib.sha256(str(traj).encode()).hexdigest()[:16]}
        gh_put("runtime/pulse.json", pulse, f"🧭 pulse epoch={epoch} phi={phi} lat={pulse['latency_mode']}")
        gh_put("runtime/trajectory.json", trajectory_rec, f"📈 trajectory epoch={epoch} basin_d={traj['basin_distance']} neg_lat={traj['negative_latency_triggered']}")
        try:
            if ABLY_KEY:
                ki, ks = ABLY_KEY.split(":")
                requests.post("https://rest.ably.io/channels/evez-ops/messages",
                    json={"name": "PULSE", "data": json.dumps({
                        "epoch": epoch, "phi": phi, "lat": pulse["latency_mode"],
                        "vector": traj["vector"], "basin_d": traj["basin_distance"],
                        "neg_latency": traj["negative_latency_triggered"]
                    })}, auth=(ki, ks), timeout=15)
        except Exception as e:
            print(f"  [WARN] Ably broadcast failed: {e}")
        print(f"  Epoch {epoch} | Phi={phi} | Latency={pulse['latency_mode']} | Basin_d={traj['basin_distance']}")
        print(f"  Intelligence gain rate: {traj['intelligence_gain_rate']} | Neg-latency: {traj['negative_latency_triggered']}")
        print("  ✅ runtime/pulse.json + runtime/trajectory.json written.")
    except Exception as e:
        print(f"  [ERROR] Reconciler main() failed: {e}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[FATAL] Reconciler crashed: {e}")
        exit(0)
