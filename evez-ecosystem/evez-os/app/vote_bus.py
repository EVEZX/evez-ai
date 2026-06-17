"""WF-09 — Collective Vote Bus: confidence-weighted consensus on FIRE_VOTE_REQUEST"""
import asyncio, httpx, os
from typing import Callable, Dict
from app.fire import fire, on_fire

METAROM_URL    = os.environ.get("METAROM_URL", "https://metarom.onrender.com")
CONSENSUS_HIGH = float(os.environ.get("CONSENSUS_HIGH", "0.66"))
CONSENSUS_LOW  = float(os.environ.get("CONSENSUS_LOW",  "0.33"))

_voters: Dict[str, Callable] = {}

def register_voter(agent_id: str, vote_fn: Callable):
    """Call this from any agent __init__ to join the vote pool."""
    _voters[agent_id] = vote_fn

@on_fire("FIRE_VOTE_REQUEST")
async def handle_vote_request(payload: dict):
    proposal = payload.get("proposal", "")
    vote_id  = payload.get("vote_id", "unknown")

    results  = await asyncio.gather(
        *[_collect(aid, fn, proposal) for aid, fn in _voters.items()],
        return_exceptions=True,
    )
    votes = [v for v in results if isinstance(v, dict)]

    if not votes:
        await fire("FIRE_VOTE_FAILED", {"vote_id": vote_id, "reason": "no registered voters"})
        return

    total_w  = sum(v["confidence"] for v in votes)
    w_avg    = sum(v["vote"] * v["confidence"] for v in votes) / total_w if total_w else 0.5
    outcome  = "EXECUTE" if w_avg > CONSENSUS_HIGH else ("REJECT" if w_avg < CONSENSUS_LOW else "CAIN_OVERRIDE")

    record = {
        "vote_id": vote_id, "proposal": proposal,
        "outcome": outcome, "weighted_avg": round(w_avg, 4),
        "votes": votes, "voter_count": len(votes),
    }

    async with httpx.AsyncClient(timeout=5) as client:
        await client.post(f"{METAROM_URL}/memory/write", json={
            "agent_id": "vote_bus", "event_type": "FIRE_VOTE_COMPLETE", "content": record
        })

    await fire("FIRE_VOTE_COMPLETE", record)

async def _collect(agent_id: str, vote_fn: Callable, proposal: str) -> dict:
    try:
        r = await vote_fn(proposal)
        return {
            "agent_id":  agent_id,
            "vote":      float(r.get("vote",       0.5)),
            "confidence":float(r.get("confidence", 0.5)),
            "reasoning": r.get("reasoning", ""),
        }
    except Exception as exc:
        return {"agent_id": agent_id, "vote": 0.5, "confidence": 0.1, "reasoning": str(exc)}
