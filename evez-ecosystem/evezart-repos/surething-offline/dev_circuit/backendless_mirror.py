# EVEZ-GENERATED: Backendless spine mirror
# DCT-003 | Generated 2026-03-12 | circuit: THINK-G (groq/llama-3.3-70b-versatile)
import os
import sys
import json
import argparse
import requests
from typing import Optional

SPINE_URL = "https://evez-operator.vercel.app"

def fetch_spine_events(offset: int = 0, limit: int = 100) -> dict:
    """Fetch paginated events from EVEZ spine API.
    Inputs: offset (int), limit (int)
    Outputs: dict with 'events' list and 'total' count
    """
    resp = requests.get(f"{SPINE_URL}/spine/events", params={"limit": limit, "offset": offset}, timeout=30)
    resp.raise_for_status()
    return resp.json()

def check_event_exists(event_hash: str, app_id: str, api_key: str) -> bool:
    """Check if event_hash already exists in Backendless EVEZ_SPINE table.
    Inputs: event_hash (str), app_id (str), api_key (str)
    Outputs: bool — True if exists
    """
    url = f"https://api.backendless.com/{app_id}/{api_key}/data/EVEZ_SPINE"
    resp = requests.get(url, params={"where": f"event_hash='{event_hash}'", "pageSize": 1}, timeout=30)
    if resp.status_code == 404:
        return False  # table doesn't exist yet
    resp.raise_for_status()
    data = resp.json()
    return len(data) > 0 if isinstance(data, list) else False

def insert_event(event: dict, app_id: str, api_key: str) -> dict:
    """Insert one spine event into Backendless EVEZ_SPINE table.
    Inputs: event dict, app_id, api_key
    Outputs: created record dict
    """
    url = f"https://api.backendless.com/{app_id}/{api_key}/data/EVEZ_SPINE"
    record = {
        "event_hash":     event.get("event_hash", ""),
        "evidence_hash":  event.get("evidence_hash", ""),
        "event_type":     event.get("event_type", ""),
        "lane":           event.get("lane", ""),
        "timestamp":      event.get("timestamp", ""),
        "height":         event.get("height", 0),
        "payload_json":   json.dumps(event.get("payload", {})),
    }
    resp = requests.post(url, json=record, timeout=30)
    resp.raise_for_status()
    return resp.json()

def mirror_spine(dry_run: bool = False) -> dict:
    """Mirror all EVEZ spine events to Backendless. Idempotent.
    Inputs: dry_run (bool) — if True, check but don't insert
    Outputs: summary dict {checked, inserted, skipped, errors}
    """
    app_id = os.environ.get("BACKENDLESS_APP_ID", "")
    api_key = os.environ.get("BACKENDLESS_API_KEY", "")
    if not app_id or not api_key:
        raise EnvironmentError("BACKENDLESS_APP_ID and BACKENDLESS_API_KEY must be set")

    stats = {"checked": 0, "inserted": 0, "skipped": 0, "errors": 0}
    offset = 0
    limit = 100

    while True:
        page = fetch_spine_events(offset=offset, limit=limit)
        events = page.get("events", [])
        total = page.get("total", 0)
        if not events:
            break
        for event in events:
            stats["checked"] += 1
            eh = event.get("event_hash", "")
            try:
                if check_event_exists(eh, app_id, api_key):
                    stats["skipped"] += 1
                else:
                    if not dry_run:
                        insert_event(event, app_id, api_key)
                    stats["inserted"] += 1
            except requests.HTTPError as e:
                stats["errors"] += 1
                print(f"ERROR {eh[:12]}: {e}", file=sys.stderr)
        offset += limit
        if offset >= total:
            break

    return stats

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mirror EVEZ spine to Backendless")
    parser.add_argument("--dry-run", action="store_true", help="Check but don't insert")
    args = parser.parse_args()
    result = mirror_spine(dry_run=args.dry_run)
    print(json.dumps(result, indent=2))
    print(f"\nSummary: {result['checked']} checked, {result['inserted']} inserted, {result['skipped']} skipped, {result['errors']} errors")
