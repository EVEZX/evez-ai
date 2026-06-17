#!/usr/bin/env python3
"""
agents/story_protocol.py
Story Protocol IP registration stub for FIRE events.
"""
import os, json, hashlib
from datetime import datetime, timezone

class StoryProtocolAgent:
    def __init__(self):
        self.api_key = os.environ.get("STORY_PROTOCOL_API_KEY", "")
        self.enabled = bool(self.api_key)

    def register_fire_event(self, round_n: int, fire_hash: str, tau: int,
                            fire_type: str, wallet_address: str) -> dict:
        metadata_hash = hashlib.sha256(
            f"EVEZ666:R{round_n}:{fire_hash}:{fire_type}:tau={tau}".encode()
        ).hexdigest()
        record = {
            "registered": False,
            "round": round_n, "fire_type": fire_type, "tau": tau,
            "metadata_hash": metadata_hash, "wallet_address": wallet_address,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "provenance": f"evez-os:spine:R{round_n}:{fire_hash[:16]}",
            "story_tx": None
        }
        if not self.enabled:
            print(f"Story Protocol: no API key, skipping R{round_n}")
            record["note"] = "pending_key"
            return record
        try:
            import requests
            r = requests.post(
                "https://rpc.story.foundation/v1/ip/register",
                json={
                    "ipType": "creative_work",
                    "title": f"EVEZ666 FIRE R{round_n} — {fire_type}",
                    "mediaHash": metadata_hash,
                    "creator": wallet_address,
                    "metadata": {"round": round_n, "tau": tau, "fire_type": fire_type, "spine_hash": fire_hash}
                },
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=30
            )
            if r.status_code == 200:
                data = r.json()
                record["registered"] = True
                record["story_tx"] = data.get("txHash")
                print(f"Story Protocol: R{round_n} registered tx={record['story_tx']}")
            else:
                print(f"Story Protocol: {r.status_code}")
        except Exception as e:
            print(f"Story Protocol error: {e}")
        return record
