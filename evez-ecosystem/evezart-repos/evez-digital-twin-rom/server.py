#!/usr/bin/env python3
"""EVEZ Digital Twin ROM — Data-as-terrain game engine + Crime Cross-Analytics. Port 8898"""
from fastapi import FastAPI
import time
app = FastAPI(title="EVEZ Digital Twin ROM", version="1.0.0")

INTERVENTIONS = [
    {"id": "mobile_crisis", "name": "Mobile Crisis Team", "phone": "951-686-4357", "safe_outcome": 0.80, "risk": "low"},
    {"id": "outreach_worker", "name": "Homeless Outreach Worker", "phone": "760-329-2904", "safe_outcome": 0.65, "risk": "low"},
    {"id": "plainclothes_social", "name": "Plainclothes Social Worker", "phone": "800-491-7123", "safe_outcome": 0.60, "risk": "medium"},
    {"id": "uniformed_crisis", "name": "Crisis Team + Uniformed Backup", "phone": "911", "safe_outcome": 0.30, "risk": "high"},
    {"id": "uniformed_patrol", "name": "Uniformed Patrol", "phone": "911", "safe_outcome": 0.15, "risk": "critical"},
]

RYAN_PROFILE = {"name": "Ryan Robert Maggard", "age": 21, "location": "Desert Hot Springs, CA", "conditions": ["severe TBI", "PTSD", "schizophrenia-spectrum"]}

LOCATIONS = ["gateway_lobby", "cognition_lab", "factory_floor", "vault_chamber", "mesh_nexus", "bridge_deck", "psyche_garden", "observatory_hill", "meme_archive", "stream_bank", "ledger_vault", "research_library", "omega_core", "commerce_bazaar", "search_index", "cloud_nimbus", "guard_bastion", "federation_hall", "profit_mint", "game_arena", "song_forge", "twin_mirror"]

@app.get("/health")
def health(): return {"status": "ok", "version": "1.0.0", "service": "evez-digital-twin-rom", "ts": int(time.time())}

@app.get("/")
def root(): return {"service": "EVEZ Digital Twin ROM", "version": "1.0.0", "port": 8898, "endpoints": ["/health", "/crime/speedrun-summary", "/crime/audit", "/crime/compare", "/crime/optimize-welfare-check", "/game/state", "/game/locations"]}

@app.get("/crime/speedrun-summary")
def crime_summary():
    best = INTERVENTIONS[0]
    worst = INTERVENTIONS[-1]
    return {"subject": RYAN_PROFILE, "recommended": {"method": best["name"], "phone": best["phone"], "safe_outcome": f"{int(best['safe_outcome']*100)}%"}, "worst": {"method": worst["name"], "safe_outcome": f"{int(worst['safe_outcome']*100)}%"}, "bottom_line": "Mobile Crisis Team (951-686-4357) is the ONLY safe approach. 80% vs 15% for uniformed patrol."}

@app.get("/crime/audit")
def crime_audit():
    contradictions = [
        {"id": 1, "type": "falsification", "claim": "Welfare check ensures safety", "reality": "Uniformed welfare check triggers fight-or-flight in TBI subjects", "severity": "critical"},
        {"id": 2, "type": "falsification", "claim": "Family will advocate", "reality": "Janeé blocked Steven, email bouncing", "severity": "critical"},
        {"id": 3, "type": "survival", "claim": "Ryan can seek help", "reality": "Schizophrenia + TBI = impaired help-seeking", "severity": "critical"},
    ]
    return {"audit_type": "FSC Doctrine", "contradictions_found": len(contradictions), "contradictions": contradictions}

@app.get("/crime/compare")
def crime_compare():
    return {"comparisons": INTERVENTIONS, "passing": [i for i in INTERVENTIONS if i["safe_outcome"] > 0.5], "failing": [i for i in INTERVENTIONS if i["safe_outcome"] <= 0.5]}

@app.get("/crime/optimize-welfare-check")
def crime_optimize():
    return {"steps": [{"step": 1, "action": "Call Mobile Crisis Team (951-686-4357)"}, {"step": 2, "action": "Have Steven on phone (307-677-5504)"}, {"step": 3, "action": "Approach in plain clothes, no sirens"}, {"step": 4, "action": "Approach slowly, identify by name"}, {"step": 5, "action": "Do NOT chase if Ryan flees"}, {"step": 6, "action": "Offer water and shade, not commands"}]}

@app.get("/game/state")
def game_state():
    return {"day": 1, "locations": len(LOCATIONS), "player": {"hp": 100, "sanity": 85, "cash": 47.50}, "terrain": "procedural"}

@app.get("/game/locations")
def game_locations():
    return {"locations": LOCATIONS, "total": len(LOCATIONS)}
