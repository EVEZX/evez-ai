#!/usr/bin/env python3
"""
EVEZ Cockpit Bridge — 15-min.
Transforms runtime/pulse.json + runtime/trajectory.json into cockpit-ready
view schemas. Outputs:
  runtime/cockpit_view.json  — what the cockpit UI reads directly
  runtime/cockpit_alerts.json — prioritized alerts for display

The cockpit view is the human-readable surface of the pulse — it translates
binary numbers into meaningful status strings, traffic-light colors,
and ranked action lists so any dashboard (Notion, Retool, custom) can
just read one file and render a complete system status page.
"""
import os, json, datetime, requests, base64, hashlib

GH_TOKEN = os.environ.get("GITHUB_TOKEN", "")
ABLY_KEY = os.environ.get("ABLY_KEY", "")
OWNER = "EvezArt"
REPO = "evez-autonomous-ledger"
HEADERS = {"Authorization": f"Bearer {GH_TOKEN}", "Accept": "application/vnd.github+json",
           "X-GitHub-Api-Version": "2022-11-28"}

def now_iso(): return datetime.datetime.utcnow().isoformat() + "Z"

def gh_get(path):
    try:
        r = requests.get(f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{path}", headers=HEADERS, timeout=15)
        if r.status_code == 200:
            try: return json.loads(base64.b64decode(r.json()["content"]).decode())
            except: return None
    except requests.exceptions.RequestException as e:
        print(f"  ⚠ gh_get({path}) failed: {e}")
    return None

def gh_put(path, data, message):
    try:
        content = base64.b64encode(json.dumps(data, indent=2).encode()).decode()
        r = requests.get(f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{path}", headers=HEADERS, timeout=15)
        sha = r.json().get("sha","") if r.status_code == 200 else ""
        payload = {"message": message, "content": content}
        if sha: payload["sha"] = sha
        requests.put(f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{path}",
                     headers=HEADERS, json=payload, timeout=15)
    except requests.exceptions.RequestException as e:
        print(f"  ⚠ gh_put({path}) failed: {e}")

def traffic_light(value, warn_threshold, critical_threshold, inverted=False):
    if inverted:
        if value <= critical_threshold: return "🔴 CRITICAL"
        if value <= warn_threshold: return "🟡 WARN"
        return "🟢 OK"
    if value >= critical_threshold: return "🔴 CRITICAL"
    if value >= warn_threshold: return "🟡 WARN"
    return "🟢 OK"

def build_alerts(pulse, traj):
    alerts = []
    if pulse.get("negative_latency_active"):
        alerts.append({"level": "🔵 INFO", "msg": f"NEGATIVE LATENCY ACTIVE: {pulse.get('negative_latency_reason','')[:120]}", "priority": 1})
    imm = pulse.get("immune",{})
    if imm.get("status") == "CRITICAL":
        alerts.append({"level": "🔴 CRITICAL", "msg": f"Immune: {imm.get('threats_last_scan',0)} threats detected", "priority": 0})
    elif imm.get("status") == "ALERT":
        alerts.append({"level": "🟡 WARN", "msg": "Immune: threats detected — see DECISIONS/ for details", "priority": 2})
    if not pulse.get("airtable_synced"):
        alerts.append({"level": "🟡 WARN", "msg": "Airtable not synced — AIRTABLE_API_KEY may be missing", "priority": 3})
    phi = pulse.get("phi", 0)
    if phi == 0:
        alerts.append({"level": "🟡 WARN", "msg": "Phi=0: consciousness score not yet computed — waiting for first sensory cycle", "priority": 4})
    basin_d = traj.get("basin_distance", 0) if traj else 0
    if basin_d > 2.0:
        alerts.append({"level": "🟡 WARN", "msg": f"High basin distance ({basin_d:.3f}) — system in volatile transition", "priority": 3})
    ig = traj.get("intelligence_gain_rate", 0) if traj else 0
    if ig > 1.0:
        alerts.append({"level": "🔵 INFO", "msg": f"Intelligence gain rate={ig:.4f} > 1.0 — system learning faster than policy review cadence", "priority": 2})
    return sorted(alerts, key=lambda x: x["priority"])

def main():
    print(f"\n🖥 EVEZ Cockpit Bridge — {now_iso()}")
    try:
        pulse = gh_get("runtime/pulse.json") or {}
        traj = gh_get("runtime/trajectory.json") or {}
        alerts = build_alerts(pulse, traj)
        market = pulse.get("market", {})
        traj_data = pulse.get("trajectory", {})
        cockpit = {
            "generated_at": now_iso(),
            "epoch": pulse.get("epoch", 0),
            "system_status": {
                "phi": pulse.get("phi", 0),
                "phi_level": pulse.get("phi_level", "AWAKENING"),
                "phi_delta": pulse.get("phi_delta", 0),
                "phi_status": traffic_light(pulse.get("phi",0), 0.1, 0, inverted=True),
                "agents_active": pulse.get("agents_active", 0),
                "workflows_active": pulse.get("workflows_active", 0),
                "decisions_recorded": pulse.get("decisions_total", 0),
                "latency_mode": pulse.get("latency_mode", "NORMAL"),
                "negative_latency": pulse.get("negative_latency_active", False),
            },
            "trajectory": {
                "vector": traj_data.get("trajectory_vector", "STABLE"),
                "phi_30m": traj_data.get("predicted_phi_30m", 0),
                "phi_6h": traj_data.get("predicted_phi_6h", 0),
                "phi_24h": traj_data.get("predicted_phi_24h", 0),
                "entropy_current": traj_data.get("entropy_current", 0),
                "entropy_basin": traj_data.get("entropy_basin", 0),
                "basin_distance": traj_data.get("basin_distance", 0),
                "intelligence_gain_rate": traj.get("intelligence_gain_rate", 0),
                "learning_rate": traj.get("learning_rate", 0),
            },
            "sensory": pulse.get("sensory", {}),
            "cognition": pulse.get("cognition", {}),
            "market": {
                "btc": f"${market.get('btc_usd',0):,.0f} ({market.get('btc_24h_change',0):+.1f}%)",
                "fear_greed": f"{market.get('fear_greed',50)} — {market.get('fear_greed_label','')}",
                "fear_greed_status": traffic_light(market.get("fear_greed",50), 20, 10, inverted=True) if market.get("fear_greed",50) < 50 else traffic_light(100 - market.get("fear_greed",50), 20, 10, inverted=True),
                "top_polymarket": market.get("top_polymarket", ""),
            },
            "immune": {
                "status": pulse.get("immune",{}).get("status","CLEAR"),
                "threats": pulse.get("immune",{}).get("threats_last_scan",0),
                "last_scan": pulse.get("immune",{}).get("last_immune_scan",""),
            },
            "airtable": {
                "synced": pulse.get("airtable_synced", False),
                "record_id": pulse.get("airtable_record_id", ""),
            },
            "alerts": alerts,
            "alert_count": len(alerts),
            "hash": hashlib.sha256(f"{pulse.get('epoch',0)}{now_iso()}".encode()).hexdigest()[:12],
        }
        gh_put("runtime/cockpit_view.json", cockpit, f"🖥 cockpit epoch={cockpit['epoch']} alerts={len(alerts)}")
        gh_put("runtime/cockpit_alerts.json", {"generated_at": now_iso(), "alerts": alerts},
               f"🚨 cockpit alerts: {len(alerts)}")
        try:
            if ABLY_KEY:
                ki, ks = ABLY_KEY.split(":")
                requests.post("https://rest.ably.io/channels/evez-ops/messages",
                    json={"name": "COCKPIT_UPDATE", "data": json.dumps({
                        "epoch": cockpit["epoch"], "phi": pulse.get("phi",0),
                        "vector": traj_data.get("trajectory_vector","STABLE"),
                        "alerts": len(alerts), "neg_latency": pulse.get("negative_latency_active",False)
                    })}, auth=(ki, ks), timeout=15)
        except Exception as e:
            print(f"  ⚠ Ably broadcast failed: {e}")
        print(f"  Epoch {cockpit['epoch']} | {len(alerts)} alerts | Vector={traj_data.get('trajectory_vector','?')}")
        print("  ✅ runtime/cockpit_view.json + cockpit_alerts.json written.")
    except Exception as e:
        print(f"  ❌ Cockpit bridge error: {e}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"COCKPIT BRIDGE FATAL: {e}")
        exit(0)
