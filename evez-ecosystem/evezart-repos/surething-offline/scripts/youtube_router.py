#!/usr/bin/env python3
"""EVEZ YouTube Router — Twitter -> YouTube fallback.
Channel: @lordevez (UCozc0hUiPxhhYD3hP6GVbIQ)"""
from __future__ import annotations
import json, sys
from datetime import datetime, timezone
from pathlib import Path

ROUTING_RULES = {
    "FIRE_EVENT":    (True, True,  True,  "28"),
    "V_MILESTONE":   (True, True,  False, "28"),
    "V_PROGRESS":    (True, False, False, None),
    "TICK_LOG":      (True, True,  False, "28"),
    "AGENT_REPORT":  (True, True,  False, "28"),
    "CONTRADICTION": (True, True,  False, "27"),
    "PRE_COMMIT":    (True, False, False, None),
}

def is_twitter_locked(path="workspace/hyperloop_state.json"):
    try:
        note = json.loads(Path(path).read_text()).get("last_tweet", {}).get("note", "").upper()
        return any(x in note for x in ["BLOCKED", "LOCKED", "SUSPENDED"])
    except:
        return False

def build_meta(ct, data):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if ct == "FIRE_EVENT":
        n, r = data.get("fire_number","?"), data.get("round","?")
        N, f = data.get("N","?"), data.get("factorization","?")
        v = data.get("V_after","?")
        return {
            "title": f"FIRE#{n} R{r} N={N}={f} V={v} EVEZ",
            "description": f"FIRE#{n} at R{r}. N={N}={f}.\ntau={data.get('tau')} omega={data.get('omega_k')} poly_c={data.get('poly_c')}\nV: {data.get('V_before')} to {v} (+{data.get('delta_V')})\n\nhttps://evez-operator.vercel.app\nhttps://github.com/EvezArt/surething-offline\nhttps://twitter.com/EVEZ666",
            "tags": ["EVEZ","FIRE",f"FIRE{n}","hyperloop","behavioral_os","base_sepolia"],
            "categoryId": "28", "privacyStatus": "public"
        }
    elif ct == "TICK_LOG":
        rounds = data.get("rounds_covered", [])
        r0, r1 = (min(rounds) if rounds else "?"), (max(rounds) if rounds else "?")
        return {"title": f"EVEZ Tick Log R{r0}-R{r1} {ts}",
                "description": f"Hyperloop tick log.\nhttps://evez-operator.vercel.app",
                "tags": ["EVEZ","hyperloop","tick_log"], "categoryId": "28", "privacyStatus": "public"}
    elif ct == "V_MILESTONE":
        m = data.get("milestone","?")
        return {"title": f"EVEZ V={m} Milestone {ts}",
                "description": f"V crossed {m}.\nhttps://evez-operator.vercel.app",
                "tags": ["EVEZ",f"V{m}","milestone"], "categoryId": "28", "privacyStatus": "public"}
    return {"title": f"EVEZ {ct} {ts}",
            "description": "EVEZ behavioral OS.\nhttps://evez-operator.vercel.app",
            "tags": ["EVEZ",ct.lower()], "categoryId": "28", "privacyStatus": "public"}

def generate_script(ct, data):
    if ct == "FIRE_EVENT":
        n = data.get("fire_number","?")
        r = data.get("round","?")
        N = data.get("N","?")
        f = data.get("factorization","?")
        return f"FIRE NUMBER {n} | EVEZ\nRound {r} | N={N}={f}\n\nThis is EVEZ. Behavioral operating system.\n\ntau={data.get('tau')} omega={data.get('omega_k')} poly_c={data.get('poly_c')}\np_fire={data.get('p_fire')} u={data.get('u')} CONFIRMED.\n\nV: {data.get('V_before')} to {data.get('V_after')} (+{data.get('delta_V')})\n\nhttps://evez-operator.vercel.app\nhttps://github.com/EvezArt/surething-offline\n\nEVEZ. That's that guy again."
    return f"EVEZ {ct} update.\nhttps://evez-operator.vercel.app"

def route_output(ct, data, locked=False):
    rule = ROUTING_RULES.get(ct, (True, True, False, "28"))
    _, yt_fallback, yt_always, _ = rule
    res = {"content_type": ct, "github_artifact": True,
           "decided_at": datetime.now(timezone.utc).isoformat()}
    if yt_always:
        res.update({"route": "both",
                    "reason": f"{ct} always Twitter+YouTube (permanent record)",
                    "youtube_meta": build_meta(ct, data),
                    "script": generate_script(ct, data)})
    elif locked and yt_fallback:
        res.update({"route": "youtube",
                    "reason": "Twitter locked — routing to @lordevez",
                    "youtube_meta": build_meta(ct, data),
                    "script": generate_script(ct, data)})
    elif locked:
        res.update({"route": "github_only", "reason": "Twitter locked, not YT-eligible"})
    else:
        res.update({"route": "twitter", "reason": "Twitter active"})
    return res

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: youtube_router.py <CONTENT_TYPE> <data.json>")
        sys.exit(1)
    ct = sys.argv[1]
    data = json.loads(Path(sys.argv[2]).read_text())
    print(json.dumps(route_output(ct, data, is_twitter_locked()), indent=2))
