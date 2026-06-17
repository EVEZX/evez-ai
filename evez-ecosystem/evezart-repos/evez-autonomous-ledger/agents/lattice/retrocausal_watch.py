#!/usr/bin/env python3
"""
agents/lattice/retrocausal_watch.py
Lattice v0.2 - retrocausal threshold decay agent.
Fits evez-autonomous-ledger agent runner pattern.
"""
import json, os, hashlib
from pathlib import Path
from datetime import datetime, timezone

SPINE_PATH   = Path("DECISIONS/retrocausal")
FIRE_PATH    = Path("DECISIONS/fire_events")
DECAY_FACTOR = 0.95
PHI_TARGET   = float(os.environ.get("PHI_TARGET", "0.995"))

def ts(): return datetime.now(timezone.utc).isoformat()
def sha(d): return hashlib.sha256(json.dumps(d, sort_keys=True).encode()).hexdigest()[:16]

def load_fire_events():
    if not FIRE_PATH.exists(): return []
    events = []
    for f in FIRE_PATH.glob("*.json"):
        try: events.append(json.loads(f.read_text()))
        except: pass
    return events

def apply_decay(fire_events):
    thresholds, decays = {}, []
    for event in fire_events:
        domain = event.get("domain", "general")
        key = f"threshold_{domain}"
        old = thresholds.get(key, 1.0)
        new = round(old * DECAY_FACTOR, 4)
        thresholds[key] = new
        decays.append({"event": event.get("title", "?")[:60], "domain": domain,
                        "poly_c": event.get("poly_c", 0.5),
                        "threshold_old": old, "threshold_new": new})
    return thresholds, decays

def run():
    SPINE_PATH.mkdir(parents=True, exist_ok=True)
    fire_events = load_fire_events()
    thresholds, decays = apply_decay(fire_events)
    decisions_count = sum(1 for _ in Path("DECISIONS").rglob("*.json")) if Path("DECISIONS").exists() else 0
    phi = round(min(PHI_TARGET, 0.5 + (decisions_count / (decisions_count + 100)) * 0.495), 4)
    poly_c_max = max((e.get("poly_c", 0) for e in fire_events), default=0.0)
    report = {
        "ts": ts(), "phi": phi, "poly_c_max": poly_c_max,
        "fire_events_processed": len(fire_events),
        "thresholds": thresholds, "decay_log": decays[:10],
        "formula": "poly_c=tau*omega*topo/2*sqrt(N)",
        "status": "SUPERCRITICAL" if phi >= 0.99 else "CANONICAL" if phi >= 0.9 else "ACTIVE",
    }
    report["hash"] = sha(report)
    ts_safe = ts().replace(":", "-").replace(".", "-")
    (SPINE_PATH / f"{ts_safe}_decay.json").write_text(json.dumps(report, indent=2))
    print(f"[retrocausal_watch] phi={phi} | poly_c_max={poly_c_max} | {len(decays)} decays | {report['status']}")
    return report

if __name__ == "__main__": run()
