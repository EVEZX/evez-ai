#!/usr/bin/env python3
"""
EVEZ-OS MetaBus v1.0
Observes all bus logs. Detects bottlenecks, drift, stalls, and capability gaps.
Emits MetaReport to master_bus_log.jsonl and updates meta_bus_report.json.
The only bus that reads ALL other buses' state and makes cross-bus recommendations.
"""
import json, os
from datetime import datetime, timezone, timedelta
from collections import Counter

CELL = "/cells/599dc7f9-0b2b-4460-b917-5104fcbb91ef/workspace"
LOG_FILE      = f"{CELL}/master_bus_log.jsonl"
META_REPORT   = f"{CELL}/meta_bus_report.json"
STATE_FILE    = f"{CELL}/hyperloop_state.json"
SPAWN_LOG     = f"{CELL}/spawn_bus_state.json"
CAP_STATE     = f"{CELL}/capability_bus_state.json"
VAL_STATE     = f"{CELL}/validator_bus_state.json"

def load_bus_log():
    if not os.path.exists(LOG_FILE): return []
    entries = []
    with open(LOG_FILE) as f:
        for line in f:
            line = line.strip()
            if line:
                try: entries.append(json.loads(line))
                except: pass
    return entries

def emit_log(event_type, data):
    entry = {"ts": datetime.now(timezone.utc).isoformat(),
             "bus": "MetaBus", "event": event_type, **data}
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")

def run():
    now = datetime.now(timezone.utc)
    state = json.load(open(STATE_FILE))

    report = {
        "ts": now.isoformat(),
        "current_round": state["current_round"],
        "V_global": state["V_global"],
        "ceiling_tick": state["ceiling_tick"],
        "v_progress_pct": round(state["V_global"] / 6.0 * 100, 1),
        "buses": {}, "bottlenecks": [], "recommendations": [], "health": "GREEN"
    }

    # ── Analyze bus log ────────────────────────────────────────────────────
    entries = load_bus_log()
    by_bus = Counter(e["bus"] for e in entries)
    by_event = Counter(e["event"] for e in entries)
    recent = [e for e in entries
              if (now - datetime.fromisoformat(e["ts"])).total_seconds() < 3600]
    rejects = [e for e in entries if "REJECTED" in e.get("event", "")]

    report["buses"]["event_counts"] = dict(by_bus)
    report["buses"]["recent_1h"] = len(recent)
    report["buses"]["total_events"] = len(entries)
    report["buses"]["rejections"] = len(rejects)

    # ── SpawnBus health ────────────────────────────────────────────────────
    if os.path.exists(SPAWN_LOG):
        spawn = json.load(open(SPAWN_LOG))
        lag = state["current_round"] - spawn.get("last_spawned_round", 0)
        report["buses"]["spawn"] = {
            "last_spawned_round": spawn.get("last_spawned_round"),
            "lag_rounds": lag,
            "status": "LAGGING" if lag > 1 else "OK"
        }
        if lag > 1:
            report["bottlenecks"].append(f"SpawnBus lag: {lag} rounds behind current")
            report["recommendations"].append(f"SpawnBus: run immediately — {lag} rounds unspawned")

    # ── CapabilityBus health ───────────────────────────────────────────────
    if os.path.exists(CAP_STATE):
        cap = json.load(open(CAP_STATE))
        report["buses"]["capability"] = {
            "total_registered": cap.get("total_registered", 0),
            "total_active": cap.get("total_active", 0),
            "total_blocked": cap.get("total_blocked", 0),
            "blocked_apps": [b["app"] for b in cap.get("blocked", [])]
        }
        critical_blocked = [b for b in cap.get("blocked", [])
                            if b["app"] in ["ably", "elevenlabs", "ai_ml_api"]]
        if critical_blocked:
            for b in critical_blocked:
                report["bottlenecks"].append(f"CapabilityBus BLOCKED: {b['app']} — {b['blocker']}")
                report["recommendations"].append(f"Unblock {b['app']}: {b.get('blocker', 'check config')}")

    # ── ValidatorBus health ────────────────────────────────────────────────
    if os.path.exists(VAL_STATE):
        val = json.load(open(VAL_STATE))
        last_probe = val.get("last_probe_validation", {})
        report["buses"]["validator"] = {
            "last_probe_verdict": last_probe.get("verdict"),
            "last_probe_drift": last_probe.get("drift"),
            "total_rejections": len(val.get("rejected", [])),
            "capability_gate_active": len(val.get("capability_gate", {}).get("active", [])),
            "capability_gate_blocked": len(val.get("capability_gate", {}).get("blocked", [])),
        }
        if last_probe.get("verdict") == "REJECTED":
            report["bottlenecks"].append(f"ValidatorBus: probe REJECTED drift={last_probe.get('drift')}")
            report["health"] = "RED"
            report["recommendations"].append("Probe drift exceeds tolerance — re-run probe before commit")

    # ── Revenue gap ────────────────────────────────────────────────────────
    report["revenue"] = {"status": "$0", "blocker": "GitHub Sponsors SSN enrollment (Steven action required)"}
    report["bottlenecks"].append("Revenue: $0 — GitHub Sponsors enrollment gate (SSN + banking, Steven action)")

    # ── x402 wallet health ─────────────────────────────────────────────────
    try:
        import sys; sys.path.insert(0, CELL)
        from http_client import x402_status
        x402 = x402_status()
        report["buses"]["x402"] = {
            "wallet": x402.get("wallet", "unknown"),
            "funded": x402.get("funded", False),
            "balance_usd": x402.get("balance_usd", 0),
            "active": x402.get("active", False),
        }
        if not x402.get("funded"):
            report["bottlenecks"].append("x402 wallet unfunded — USDC on Base needed for autonomous API payments")
            report["recommendations"].append(
                "Fund x402 wallet: send USDC on Base to 0xFb756fc5Fe01FB982E5d63Db3A8b787B6fDE8692 ($5 minimum)"
            )
        elif (x402.get("balance_usd") or 0) < 1.0:
            report["recommendations"].append(
                f"x402 wallet low (${x402.get('balance_usd', 0):.4f}) — refill USDC on Base soon"
            )
    except Exception as _e:
        report["buses"]["x402"] = {"error": str(_e)}

    report["recommendations"].append("PRIORITY: Complete github.com/sponsors/accounts enrollment to unblock revenue")

    # ── Fire watch ────────────────────────────────────────────────────────
    rounds_to_fire_watch = 144 - state["current_round"]
    if rounds_to_fire_watch <= 5:
        report["fire_watch"] = {
            "round": 144, "rounds_away": rounds_to_fire_watch,
            "N": 96, "N_str": "2^5x3", "tau": 12, "poly_c_est": 0.685,
            "alert": "FIRE #13 LIKELY"
        }
        report["recommendations"].insert(0, f"FIRE WATCH: R144 in {rounds_to_fire_watch} rounds — N=96=2⁵×3 tau=12 poly_c≈0.685 — prep video reply")

    # ── Overall health ─────────────────────────────────────────────────────
    if len(report["bottlenecks"]) == 0:
        report["health"] = "GREEN"
    elif report["health"] != "RED":
        report["health"] = "YELLOW" if len(report["bottlenecks"]) < 3 else "ORANGE"

    with open(META_REPORT, "w") as f:
        json.dump(report, f, indent=2)

    emit_log("META_REPORT", {
        "health": report["health"],
        "bottleneck_count": len(report["bottlenecks"]),
        "recommendation_count": len(report["recommendations"]),
        "current_round": state["current_round"],
        "V_global": state["V_global"],
        "v_progress_pct": report["v_progress_pct"],
        "top_reco": report["recommendations"][0] if report["recommendations"] else "none"
    })

    print(f"MetaBus: health={report['health']} bottlenecks={len(report['bottlenecks'])} round={state['current_round']} V={state['V_global']}")
    for b in report["bottlenecks"][:3]:
        print(f"  ⚠ {b}")
    for r in report["recommendations"][:3]:
        print(f"  → {r}")

    return report

if __name__ == "__main__":
    run()
