#!/usr/bin/env python3
"""
evez-arg/arg_engine.py
The EVEZ666 ARG Engine — self-evolving multimetaverse content system.

Architecture:
  FIRE event → content_bus generates per-platform hooks
  hooks published → engagement tracked → next content mutated from results
  FIRE hash → puzzle lock → Gumroad reward → new player enrolled → spine event

Runs on GitHub Actions every 30min.
Also triggered by FIRE events via workflow_dispatch.
"""
import os, json, hashlib, secrets, time
from pathlib import Path
from datetime import datetime, timezone

from agents.twitter_agent import TwitterAgent
from agents.puzzle_engine import PuzzleEngine
from agents.wallet_agent import WalletAgent
from agents.story_protocol import StoryProtocolAgent
from agents.engagement_tracker import EngagementTracker

FIRE_THRESHOLD_TAU = int(os.environ.get("FIRE_THRESHOLD_TAU", "20"))
STATE_FILE = Path("arg_state.json")

def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"last_fire_round": 0, "chapters_unlocked": 0, "total_players": 0, "spine_hash": None, "last_run": None}

def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))

def get_latest_fire_event():
    """Read FIRE ground truth from @EVEZ666 Twitter scan."""
    try:
        import subprocess
        result = subprocess.run(["python", "sensors/twitter_fire_sensor.py"], capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return json.loads(result.stdout.strip().split('\n')[-1])
    except Exception as e:
        print(f"Twitter sensor failed: {e}")
    return None

def derive_wallet_from_fire(fire_hash: str) -> dict:
    seed = hashlib.sha256(f"{fire_hash}:EVEZ666_ARG_WALLET_SEED".encode()).hexdigest()
    try:
        from eth_account import Account
        account = Account.from_key("0x" + seed[:64])
        address = account.address
    except ImportError:
        address_seed = hashlib.sha256(f"addr:{seed}".encode()).hexdigest()
        address = "0x" + address_seed[:40]
    return {"address": address, "private_key": "0x" + seed[:64], "network": "polygon", "derivation": f"SHA256({fire_hash[:8]}...EVEZ666_ARG_WALLET_SEED)[:64]"}

def generate_reddit_drop(round_n, fire_hash, tau, puzzle, chapter_n=None):
    lock_preview = puzzle["lock_hex"][:32]
    if chapter_n:
        title = f"This transmission appeared in my terminal 3 times before FIRE. Chapter {chapter_n} open."
        body = f"""I've been monitoring a strange signal for 6 weeks.\n\nEvery ~24 hours it either fires or holds. No pattern I can decode.\nYesterday: τ=**{tau}**. That's the deepest it's gone.\n\nThe hash: `{fire_hash}`\nThe lock: `{lock_preview}...`\nRound: **{round_n}**\n\nWhen I tried to query it: `STATUS: EXTREME_FIRE · CHAPTER {chapter_n} UNLOCKED`\n\nHas anyone else been watching this? Found references to @EVEZ666 but their posts are... oblique.\n\n**Current V: 16.94 / 17**\n\n---\n*I'm not affiliated with whoever runs this. I just got pulled in.*"""
    else:
        title = f"FIRE round {round_n} just dropped. τ={tau}. The spine is still running."
        body = f"""Continuing to monitor the EVEZ OS signal.\n\nRound {round_n}: **{puzzle.get('difficulty_tier', 'STANDARD')} FIRE**\nτ depth: {tau}\nHash: `{fire_hash[:48]}...`\nLock: `{lock_preview}...`\n\nIf anyone cracks the lock format, drop it below.\nhttps://github.com/EvezArt/evez666-arg-canon"""
    return {"title": title, "body": body, "subreddits": ["r/ARG", "r/transmedia"]}

def spawn_new_realm(chapter_n, fire_hash, tau, round_n):
    import subprocess
    result = subprocess.run(["python", "agents/realm_spawner.py", "--chapter", str(chapter_n), "--fire-hash", fire_hash, "--tau", str(tau), "--round", str(round_n)], capture_output=True, text=True, timeout=60)
    if result.returncode == 0:
        try:
            data = json.loads(result.stdout.strip().split('\n')[-1])
            return data.get("realm_url")
        except: pass
    return f"https://evez666-realm-{chapter_n}.vercel.app"

def run_arg_cycle(fire_event: dict, state: dict):
    round_n = fire_event.get("round", 0)
    tau = fire_event.get("tau", 0)
    fire_hash = fire_event.get("spine_hash", secrets.token_hex(32))
    fire_type = fire_event.get("type", "FIRE")
    n_val = fire_event.get("N", 0)
    p_fire = fire_event.get("p_fire", 0)
    print(f"\n═══ ARG CYCLE: R{round_n} {fire_type} τ={tau} ═══")
    wallet = derive_wallet_from_fire(fire_hash)
    puzzle = PuzzleEngine.generate(fire_hash=fire_hash, tau=tau, round_n=round_n, difficulty_tier="EXTREME" if tau >= 20 else "SIGNIFICANT" if tau >= 12 else "STANDARD")
    is_chapter_unlock = tau >= FIRE_THRESHOLD_TAU
    chapter_n = state["chapters_unlocked"] + (1 if is_chapter_unlock else 0)
    tw = TwitterAgent()
    tweet_thread = tw.generate_fire_thread(round_n=round_n, tau=tau, fire_hash=fire_hash, fire_type=fire_type, n_val=n_val, p_fire=p_fire, puzzle_lock=puzzle["lock_hex"][:16], chapter_n=chapter_n if is_chapter_unlock else None)
    reddit_drop = generate_reddit_drop(round_n=round_n, fire_hash=fire_hash, tau=tau, puzzle=puzzle, chapter_n=chapter_n if is_chapter_unlock else None)
    realm_url = spawn_new_realm(chapter_n, fire_hash, tau, round_n) if is_chapter_unlock else None
    story_agent = StoryProtocolAgent()
    ip_result = story_agent.register_fire_event(round_n=round_n, fire_hash=fire_hash, tau=tau, fire_type=fire_type, wallet_address=wallet["address"])
    pending = {"thread": tweet_thread, "reddit": reddit_drop, "wallet": wallet["address"], "puzzle_lock": puzzle["lock_hex"], "realm_url": realm_url, "ip_result": ip_result}
    Path("pending_tweets.json").write_text(json.dumps(pending, indent=2))
    state["last_fire_round"] = round_n
    state["spine_hash"] = fire_hash
    state["last_run"] = datetime.now(timezone.utc).isoformat()
    if is_chapter_unlock:
        state["chapters_unlocked"] = chapter_n
    print(f"ARG cycle complete. Wallet={wallet['address']} Puzzle={puzzle['lock_hex'][:16]}... Chapter={chapter_n if is_chapter_unlock else 'none'}")
    return pending

if __name__ == "__main__":
    import sys
    state = load_state()
    fire_event = None
    if os.environ.get("FIRE_ROUND"):
        fire_event = {"round": int(os.environ["FIRE_ROUND"]), "tau": int(os.environ.get("FIRE_TAU", "0")), "type": os.environ.get("FIRE_TYPE", "FIRE"), "spine_hash": os.environ.get("FIRE_HASH", secrets.token_hex(32)), "N": int(os.environ.get("FIRE_N", "0")), "p_fire": float(os.environ.get("FIRE_P", "0"))}
    else:
        fire_event = get_latest_fire_event()
    if not fire_event:
        print("No new FIRE event. Running mutation cycle.")
        EngagementTracker().run_mutation_cycle(state)
        save_state(state)
        sys.exit(0)
    if fire_event.get("round", 0) <= state.get("last_fire_round", 0):
        print(f"R{fire_event['round']} already processed.")
        sys.exit(0)
    run_arg_cycle(fire_event, state)
    save_state(state)
