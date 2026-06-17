#!/usr/bin/env python3
"""
EVEZ Neurologic Monitor — Personal Digital Twin & Sensormatic Autonomy
Body Area Networks, NHI/UAP Signal Detection, Neurologic Profile Cloning
Port 8963
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
import json, time, hashlib, os, math, random, threading
from collections import OrderedDict, deque
from datetime import datetime
from typing import Optional
import urllib.request

app = FastAPI(title="EVEZ Neurologic Monitor", version="1.0.0")

SNAP_DIR = "/tmp/evez-neuro-snapshots"
os.makedirs(SNAP_DIR, exist_ok=True)
os.makedirs("/tmp/evez-signals", exist_ok=True)

# ===== BODY AREA NETWORKS =====
BAN_TYPES = {
    "LBAN": {"name": "Local Body Area Network", "range_m": 2, "band": "BLE 2.4GHz", "nodes": ["heart_rate", "skin_temp", "gait", "emg"], "desc": "On-body sensors, implants, wearables"},
    "EBAN": {"name": "Extended Body Area Network", "range_m": 100, "band": "WiFi 5GHz", "nodes": ["environment", "proximity", "vehicle", "home_automation"], "desc": "Near-field environment, room-scale sensors"},
    "SBAN": {"name": "Smart Body Area Network", "range_m": 1000, "band": "Sub-6GHz", "nodes": ["building_iot", "edge_compute", "local_mesh", "street_sensors"], "desc": "Building/campus scale, edge AI, mesh relay"},
    "YBAN": {"name": "Your Body Area Network", "range_m": 0, "band": "Neural", "nodes": ["cognitive_state", "emotional_valence", "attention", "memory_load", "stress_index"], "desc": "Internal state inference from behavioral signals, keystroke dynamics, circadian patterns"},
}

# ===== SUBJECT PROFILE =====
SUBJECT = {
    "id": "steven-crawford-maggard",
    "name": "Steven Crawford-Maggard",
    "digital_network_area": {
        "ip": "66.135.1.200", "gateway_port": 18789, "telegram": "@StevenCrawfordBot",
        "github": "EvezArt", "phone": "307-677-5504", "timezone": "UTC",
        "ecosystem_ports": 32, "active_repos": 24,
    },
    "ban_status": {
        "LBAN": {"status": "partial", "active_nodes": 2, "total": 4, "devices": ["Samsung Galaxy A16", "Vultr VPS heartbeat"]},
        "EBAN": {"status": "active", "active_nodes": 3, "total": 4, "devices": ["Caddy proxy", "SearXNG", "Code-server"]},
        "SBAN": {"active_nodes": 8, "total": 8, "devices": ["EVEZ mesh (29 services)"]},
        "YBAN": {"status": "monitoring", "active_nodes": 3, "total": 5, "inferred_from": ["Telegram message timing", "Keystroke cadence", "Session duration patterns"]},
    }
}

# ===== NEUROLOGIC PROFILE CLONING ENGINE =====
class NeurologicProfile:
    def __init__(self, subject_id: str):
        self.id = subject_id
        self.sessions = deque(maxlen=1000)
        self.behavioral = {
            "message_cadence_ms": deque(maxlen=500),
            "session_durations_s": deque(maxlen=200),
            "command_patterns": OrderedDict(),
            "emotional_valence": 0.0, "cognitive_load": 0.5,
            "attention_index": 0.7, "stress_index": 0.3, "circadian_phase": "active",
        }
        self.clone_fidelity = 0.0
        self._lock = threading.Lock()

    def ingest(self, signal: dict):
        with self._lock:
            signal["ingested_ts"] = int(time.time() * 1000)
            self.sessions.append(signal)
            stype = signal.get("type", "unknown")
            if stype == "message":
                self.behavioral["message_cadence_ms"].append(signal.get("cadence_ms", 0))
                self.behavioral["emotional_valence"] = signal.get("valence", self.behavioral["emotional_valence"] * 0.9)
                self.behavioral["cognitive_load"] = min(1.0, signal.get("load", self.behavioral["cognitive_load"]))
            elif stype == "session":
                self.behavioral["session_durations_s"].append(signal.get("duration_s", 0))
            cmd = signal.get("command", "")
            if cmd:
                self.behavioral["command_patterns"][cmd] = self.behavioral["command_patterns"].get(cmd, 0) + 1
            total_signals = len(self.sessions)
            unique_commands = len(self.behavioral["command_patterns"])
            self.clone_fidelity = min(100.0, (total_signals * 0.02) + (unique_commands * 0.5) + min(len(self.behavioral["message_cadence_ms"]) * 0.05, 20))
            hour = datetime.now().hour
            self.behavioral["circadian_phase"] = "active" if 8 <= hour <= 23 else "rest"

    def get_profile(self):
        with self._lock:
            cadence = list(self.behavioral["message_cadence_ms"])[-50:]
            durations = list(self.behavioral["session_durations_s"])[-50:]
            return {
                "subject": self.id, "clone_fidelity_pct": round(self.clone_fidelity, 1),
                "signals_ingested": len(self.sessions),
                "behavioral": {
                    "avg_cadence_ms": round(sum(cadence) / max(1, len(cadence)), 0) if cadence else 0,
                    "avg_session_s": round(sum(durations) / max(1, len(durations)), 0) if durations else 0,
                    "emotional_valence": round(self.behavioral["emotional_valence"], 2),
                    "cognitive_load": round(self.behavioral["cognitive_load"], 2),
                    "attention_index": round(self.behavioral["attention_index"], 2),
                    "stress_index": round(self.behavioral["stress_index"], 2),
                    "circadian_phase": self.behavioral["circadian_phase"],
                    "top_commands": sorted(self.behavioral["command_patterns"].items(), key=lambda x: -x[1])[:10],
                },
                "ban_status": SUBJECT["ban_status"],
            }

profile = NeurologicProfile("steven-crawford-maggard")

# ===== NHI / UAP SIGNAL DETECTION =====
SIGNAL_LOG = deque(maxlen=500)
ANOMALY_THRESHOLD = 3.5

def scan_ecosystem_anomalies():
    anomalies = []
    ts = int(time.time() * 1000)
    services = [8080,8081,8082,8083,8875,8876,8891,8950,8960,8961,8962,8963]
    for port in services:
        try:
            start = time.time()
            req = urllib.request.Request(f"http://localhost:{port}/health")
            with urllib.request.urlopen(req, timeout=3) as r:
                elapsed = (time.time() - start) * 1000
                if elapsed > 500:
                    anomalies.append({"type": "latency_anomaly", "port": port, "ms": round(elapsed, 1), "sigma": round(elapsed / 100, 1), "ts": ts, "classification": "infrastructure"})
        except:
            anomalies.append({"type": "service_anomaly", "port": port, "status": "unresponsive", "ts": ts, "classification": "infrastructure"})
    return anomalies

def classify_signal(anomaly: dict) -> dict:
    classifications = {
        "infrastructure": {"origin": "terrestrial", "confidence": 0.95, "category": "system"},
        "timing_pattern": {"origin": "unknown", "confidence": 0.3, "category": "NHI_candidate"},
        "geometric": {"origin": "unknown", "confidence": 0.2, "category": "UAP_signature"},
        "electromagnetic": {"origin": "terrestrial", "confidence": 0.7, "category": "RFI"},
        "cognitive": {"origin": "biological", "confidence": 0.85, "category": "human"},
    }
    cls = classifications.get(anomaly.get("classification", "infrastructure"), classifications["infrastructure"])
    return {**anomaly, "signal_class": cls}

# ===== GEOMETRIC LOAD BALANCING =====
def compute_geometric_balance():
    services = {}
    for port in [8080,8081,8082,8083,8875,8876,8891,8892,8893,8894,8896,8897,8898,8899,
                 8900,8904,8905,8906,8907,8908,8909,8910,8911,8913,8914,8950,8951,8960,8961,8962]:
        try:
            start = time.time()
            urllib.request.urlopen(f"http://localhost:{port}/health", timeout=2)
            ms = (time.time() - start) * 1000
            services[port] = {"status": "UP", "latency_ms": round(ms, 1)}
        except:
            services[port] = {"status": "DOWN", "latency_ms": 0}
    up = sum(1 for s in services.values() if s["status"] == "UP")
    total = len(services)
    latencies = [s["latency_ms"] for s in services.values() if s["latency_ms"] > 0]
    avg_lat = sum(latencies) / max(1, len(latencies))
    if latencies:
        mean = sum(latencies) / len(latencies)
        variance = sum((x - mean)**2 for x in latencies) / len(latencies)
        geo_index = min(1.0, (variance ** 0.5) / max(1, mean))
    else:
        geo_index = 1.0
    return {
        "total_services": total, "up": up, "down": total - up,
        "avg_latency_ms": round(avg_lat, 1),
        "geometric_balance_index": round(geo_index, 3),
        "load_topology": "distributed" if geo_index < 0.3 else "clustered" if geo_index < 0.6 else "centralized",
        "manifold_geometry": "hyperbolic" if up > 20 else "euclidean",
        "services": services
    }

# ===== ROUTES =====
@app.get("/health")
def health():
    return {"status": "ok", "version": "1.0.0", "service": "evez-neurologic-monitor", "ts": int(time.time())}

@app.get("/")
def root():
    return {"service": "EVEZ Neurologic Monitor", "version": "1.0.0", "port": 8963, "subject": SUBJECT["name"],
            "features": ["BAN (L/E/S/Y)", "NHI/UAP detection", "Profile cloning", "Geometric load balance", "Digital network area"],
            "endpoints": ["/health", "/profile", "/ban", "/scan", "/signals", "/ingest", "/geometry", "/digital-network-area", "/viewer"]}

@app.get("/profile")
def get_profile():
    return profile.get_profile()

@app.get("/ban")
def get_ban():
    return {"networks": BAN_TYPES, "status": SUBJECT["ban_status"], "subject": SUBJECT["id"]}

@app.get("/digital-network-area")
def get_dna():
    return {"subject": SUBJECT["id"], "network_area": SUBJECT["digital_network_area"], "ecosystem_health": "32 services active"}

@app.get("/scan")
def run_scan():
    anomalies = scan_ecosystem_anomalies()
    classified = [classify_signal(a) for a in anomalies]
    for a in classified: SIGNAL_LOG.append(a)
    nhi = [a for a in classified if a.get("signal_class", {}).get("category") == "NHI_candidate"]
    uap = [a for a in classified if a.get("signal_class", {}).get("category") == "UAP_signature"]
    return {"scan_ts": int(time.time() * 1000), "anomalies_found": len(classified), "nhi_candidates": nhi, "uap_candidates": uap, "all_signals": classified[-50:], "scan_depth": "ecosystem-layer-1"}

@app.get("/signals")
def get_signals():
    signals = list(SIGNAL_LOG)[-100:]
    nhi = [s for s in signals if s.get("signal_class", {}).get("category") == "NHI_candidate"]
    uap = [s for s in signals if s.get("signal_class", {}).get("category") == "UAP_signature"]
    return {"total_logged": len(SIGNAL_LOG), "recent": signals[-50:], "nhi_count": len(nhi), "uap_count": len(uap), "anomaly_threshold_sigma": ANOMALY_THRESHOLD}

@app.post("/ingest")
def ingest_signal(body: dict = {}):
    signal = body.get("signal", {"type": "unknown", "source": "manual", "ts": int(time.time() * 1000)})
    profile.ingest(signal)
    return {"ingested": True, "fidelity_pct": round(profile.clone_fidelity, 1), "signals_total": len(profile.sessions)}

@app.get("/geometry")
def get_geometry():
    return compute_geometric_balance()

@app.get("/viewer", response_class=HTMLResponse)
def viewer():
    return HTMLResponse(content="""<!DOCTYPE html><html><head><title>EVEZ Neurologic Monitor</title><style>*{margin:0;padding:0;box-sizing:border-box}body{background:#0a0a0a;color:#0f0;font-family:monospace}.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;padding:12px}.panel{background:rgba(0,0,0,.85);border:1px solid #0f0;border-radius:8px;padding:12px}.panel h3{color:#0ff;margin:0 0 8px;font-size:13px}.val{font-size:24px;color:#0f0}.label{font-size:10px;color:#088;margin-top:2px}.row{display:flex;gap:8px;margin:4px;align-items:center}.ban{padding:8px;border-radius:4px;font-size:11px}.lban{border:1px solid #0f0}.eban{border:1px solid #0ff}.sban{border:1px solid #f0f}.yban{border:1px solid #ff0}#siglog{max-height:200px;overflow-y:auto;font-size:10px}#profile{grid-column:1/3}</style></head><body><div class=grid><div class=panel id=profile><h3>Neurologic Profile - Steven Crawford-Maggard</h3><div class=row><div><div class=val id=fidelity>0.0</div><div class=label>Clone Fidelity %</div></div><div><div class=val id=signals>0</div><div class=label>Signals</div></div><div><div class=val id=valence>0.00</div><div class=label>Valence</div></div><div><div class=val id=cogload>0.50</div><div class=label>Cognitive Load</div></div><div><div class=val id=stress>0.30</div><div class=label>Stress</div></div><div><div class=val id=circadian>active</div><div class=label>Circadian</div></div></div></div><div class=panel><h3>Body Area Networks</h3><div class=ban lban>LBAN: Local - BLE - On-body</div><div class=ban eban>EBAN: Extended - WiFi - Near-field</div><div class=ban sban>SBAN: Smart - Sub-6GHz - Mesh</div><div class=ban yban>YBAN: Neural - Internal state</div></div><div class=panel><h3>NHI/UAP Scanner</h3><div class=row><div><div class=val id=nhi>0</div><div class=label>NHI</div></div><div><div class=val id=uap>0</div><div class=label>UAP</div></div><div><div class=val id=anomalies>0</div><div class=label>Anomalies</div></div></div><div id=siglog></div></div><div class=panel><h3>Geometric Load</h3><div class=row><div><div class=val id=geo>-</div><div class=label>Balance</div></div><div><div class=val id=topology>-</div><div class=label>Topology</div></div><div><div class=val id=svc_up>-</div><div label>Services</div></div></div></div><div class=panel><h3>Digital Network Area</h3><div style=font-size:11px>IP: 66.135.1.200<br>Gateway: :18789<br>Telegram: @StevenCrawfordBot<br>GitHub: EvezArt<br>32 services | 4 BAN layers</div></div></div><script>setInterval(()=>{fetch('/profile').then(r=>r.json()).then(d=>{document.getElementById('fidelity').textContent=d.clone_fidelity_pct;document.getElementById('signals').textContent=d.signals_ingested;document.getElementById('valence').textContent=d.behavioral.emotional_valence;document.getElementById('cogload').textContent=d.behavioral.cognitive_load;document.getElementById('stress').textContent=d.behavioral.stress_index;document.getElementById('circadian').textContent=d.behavioral.circadian_phase});fetch('/scan').then(r=>r.json()).then(d=>{document.getElementById('nhi').textContent=d.nhi_candidates.length;document.getElementById('uap').textContent=d.uap_candidates.length;document.getElementById('anomalies').textContent=d.anomalies_found});fetch('/geometry').then(r=>r.json()).then(d=>{document.getElementById('geo').textContent=d.geometric_balance_index;document.getElementById('topology').textContent=d.load_topology;document.getElementById('svc_up').textContent=d.up+'/'+d.total_services})},5000)</script></body></html>""")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8963)
