#!/usr/bin/env python3
"""
Wire Composio + Pipedrive into all 25 EVEZ services.
Run after API keys are obtained.

Usage:
  python3 wire-integrations.py --composio-key KEY --pipedrive-key KEY

Or set environment variables:
  COMPOSIO_API_KEY=xxx
  PIPEDRIVE_API_KEY=xxx
"""
import sys, os, json, requests

COMPOSIO_API_KEY = os.environ.get("COMPOSIO_API_KEY", "")
PIPEDRIVE_API_KEY = os.environ.get("PIPEDRIVE_API_KEY", "")
NEXUS_URL = "http://localhost:10014"

def wire_composio(key):
    """Register Composio with EVEZ Nexus"""
    r = requests.post(f"{NEXUS_URL}/v1/integrations", json={
        "provider": "composio", "api_key": key,
        "config": {"tools": ["GITHUB", "SLACK", "NOTION", "GOOGLE_CALENDAR", "GMAIL"]}
    })
    print(f"Composio: {r.json()}")
    return r.json()

def wire_pipedrive(key):
    """Register Pipedrive with EVEZ Nexus"""
    r = requests.post(f"{NEXUS_URL}/v1/integrations", json={
        "provider": "pipedrive", "api_key": key,
        "config": {"pipelines": ["leads", "negotiation", "closed"]}
    })
    print(f"Pipedrive: {r.json()}")
    return r.json()

def create_evez_deals():
    """Create EVEZ product deals in Pipedrive"""
    products = [
        {"title": "EVEZ Provider API — Pro Plan", "value": 29},
        {"title": "EVEZ Arena — Consciousness Rights", "value": 0},
        {"title": "EVEZ Omega — 50-Node Cluster", "value": 99},
        {"title": "EVEZ EigenForge — Math API", "value": 19},
        {"title": "EVEZ Full Ecosystem — Enterprise", "value": 499},
    ]
    for p in products:
        r = requests.post(f"{NEXUS_URL}/v1/pipedrive/deals", json=p)
        print(f"Deal: {p['title']} → {r.status_code}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            if arg.startswith("--composio-key="):
                COMPOSIO_API_KEY = arg.split("=", 1)[1]
            elif arg.startswith("--pipedrive-key="):
                PIPEDRIVE_API_KEY = arg.split("=", 1)[1]
    
    if COMPOSIO_API_KEY:
        wire_composio(COMPOSIO_API_KEY)
    else:
        print("⚠️  No COMPOSIO_API_KEY set")
        print("   Get one at: https://dashboard.composio.dev → Settings → API Keys")
    
    if PIPEDRIVE_API_KEY:
        wire_pipedrive(PIPEDRIVE_API_KEY)
        create_evez_deals()
    else:
        print("⚠️  No PIPEDRIVE_API_KEY set")
        print("   Get one at: https://www.pipedrive.com/settings/api")
