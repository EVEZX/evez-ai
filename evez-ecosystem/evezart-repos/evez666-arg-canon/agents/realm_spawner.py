#!/usr/bin/env python3
"""
agents/realm_spawner.py
Spawns new ARG realms on EXTREME_FIRE events.
"""
import os, json, argparse, hashlib
from datetime import datetime, timezone
from pathlib import Path

def spawn_realm(chapter_n: int, fire_hash: str, tau: int, round_n: int) -> dict:
    realm_id = f"evez666-realm-{chapter_n}"
    realm_url = f"https://{realm_id}.vercel.app"
    realm_record = {
        "chapter": chapter_n, "realm_id": realm_id, "realm_url": realm_url,
        "fire_hash": fire_hash, "tau": tau, "round_n": round_n,
        "spawned_at": datetime.now(timezone.utc).isoformat(),
        "puzzle_lock": hashlib.sha256(f"{fire_hash}:chapter:{chapter_n}".encode()).hexdigest(),
        "status": "active"
    }
    realms_dir = Path("realms")
    realms_dir.mkdir(exist_ok=True)
    realm_file = realms_dir / f"chapter_{chapter_n}.json"
    realm_file.write_text(json.dumps(realm_record, indent=2))
    print(json.dumps({"realm_url": realm_url, "chapter": chapter_n, "status": "spawned"}))
    return realm_record

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--chapter", type=int, required=True)
    parser.add_argument("--fire-hash", type=str, required=True)
    parser.add_argument("--tau", type=int, required=True)
    parser.add_argument("--round", type=int, required=True)
    args = parser.parse_args()
    spawn_realm(args.chapter, args.fire_hash, args.tau, args.round)
