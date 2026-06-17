"""
api/fork.py — EVEZ-OS Gen 3 /fork endpoint
POST /api/fork → creates a per-user EVEZ-OS instance from a canonical checkpoint.
Deploy via Vercel serverless function.
"""
import json

CANONICAL = {
    168: {"V": 5.555132, "fire_count": 26, "ceiling_tick": 86},
    167: {"V": 5.491990, "fire_count": 25, "ceiling_tick": 85},
    165: {"V": 5.420190, "fire_count": 25, "ceiling_tick": 83},
}

def handler(request):
    if request.method != "POST":
        return {"statusCode": 405, "body": "Method Not Allowed"}
    try:
        body = json.loads(request.body)
    except Exception:
        return {"statusCode": 400, "body": "Invalid JSON"}
    user_id = body.get("user_id")
    checkpoint_round = body.get("checkpoint_round", 168)
    skin_id = body.get("skin_id", "terminal-canonical")
    if not user_id:
        return {"statusCode": 400, "body": "user_id required"}
    checkpoint = CANONICAL.get(checkpoint_round, CANONICAL[168])
    # In production: INSERT INTO player_instances via Supabase client
    instance = {
        "instance_id": f"fork_{user_id}_{checkpoint_round}",
        "user_id": user_id,
        "fork_round": checkpoint_round,
        "fork_V": checkpoint["V"],
        "fire_count": checkpoint["fire_count"],
        "current_round": checkpoint_round,
        "V_global": checkpoint["V"],
        "skin_id": skin_id,
        "truth_plane": "CANONICAL",
        "reality_module": "number_theory_v1",
        "epoch": 6,
    }
    return {
        "statusCode": 200,
        "body": json.dumps(instance),
        "headers": {"Content-Type": "application/json"}
    }
