"""WF-09 — Collective Vote Bus.

Protocol:
  1. CAIN/Omega fires FIRE_VOTE_REQUEST with question + options
  2. Each agent votes: {vote, confidence: 0-1, reasoning}
  3. Consensus: weighted avg >0.66 → EXECUTE | <0.33 → REJECT | else → CAIN override
  4. All votes + outcome logged to metarom

Routes:
  POST /api/vote/request
  POST /api/vote/cast
  GET  /api/vote/status
  POST /api/vote/resolve
"""
import os, time, json, logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from pathlib import Path

router = APIRouter(prefix="/api/vote", tags=["vote_bus"])
log = logging.getLogger("vote_bus")

DATA_DIR  = Path(os.environ.get("OG_DATA_DIR", Path.home() / "og_data"))
VOTES_DIR = DATA_DIR / "votes"
VOTES_DIR.mkdir(parents=True, exist_ok=True)

EXECUTE_THRESHOLD = float(os.environ.get("VOTE_EXECUTE_THRESHOLD", "0.66"))
REJECT_THRESHOLD  = float(os.environ.get("VOTE_REJECT_THRESHOLD", "0.33"))


def _fire(event: str, data: dict):
    import httpx
    url = os.environ.get("N8N_FIRE_URL", "")
    if not url: return
    try: httpx.post(url, json={"event": event, "data": data, "ts": time.time()}, timeout=5)
    except: pass


class VoteRequest(BaseModel):
    question_id: str
    question:    str
    options:     list
    timeout_s:   Optional[int] = 300


class VoteCast(BaseModel):
    question_id: str
    agent_id:    str
    vote:        str
    confidence:  float   # 0.0 – 1.0
    reasoning:   Optional[str] = ""


@router.post("/request")
def vote_request(req: VoteRequest):
    q_file = VOTES_DIR / f"{req.question_id}.json"
    q_file.write_text(json.dumps({
        "question_id": req.question_id,
        "question":    req.question,
        "options":     req.options,
        "timeout_s":   req.timeout_s,
        "votes":       [],
        "status":      "open",
        "created":     time.time()
    }, indent=2))
    _fire("FIRE_VOTE_REQUEST", {"question_id": req.question_id,
                                 "question": req.question})
    return {"ok": True, "question_id": req.question_id}


@router.post("/cast")
def vote_cast(v: VoteCast):
    q_file = VOTES_DIR / f"{v.question_id}.json"
    if not q_file.exists():
        raise HTTPException(404, "question not found")
    data = json.loads(q_file.read_text())
    if data["status"] != "open":
        raise HTTPException(409, "voting closed")
    data["votes"].append({
        "agent_id":  v.agent_id,
        "vote":      v.vote,
        "confidence": v.confidence,
        "reasoning": v.reasoning,
        "ts":        time.time()
    })
    q_file.write_text(json.dumps(data, indent=2))
    return {"ok": True, "votes_cast": len(data["votes"])}


@router.post("/resolve")
def vote_resolve(question_id: str):
    q_file = VOTES_DIR / f"{question_id}.json"
    if not q_file.exists():
        raise HTTPException(404, "question not found")
    data = json.loads(q_file.read_text())
    votes = data["votes"]
    if not votes:
        raise HTTPException(400, "no votes cast")

    # Confidence-weighted vote tally
    tally: dict = {}
    total_weight = 0.0
    for v in votes:
        w = v.get("confidence", 0.5)
        opt = v["vote"]
        tally[opt] = tally.get(opt, 0.0) + w
        total_weight += w

    top_opt    = max(tally, key=tally.get)
    top_score  = tally[top_opt] / total_weight if total_weight > 0 else 0

    if top_score >= EXECUTE_THRESHOLD:
        outcome = "EXECUTE"
    elif top_score <= REJECT_THRESHOLD:
        outcome = "REJECT"
    else:
        outcome = "CAIN_OVERRIDE"

    data["outcome"]   = outcome
    data["top_vote"]  = top_opt
    data["top_score"] = round(top_score, 4)
    data["status"]    = "resolved"
    data["resolved_at"] = time.time()
    q_file.write_text(json.dumps(data, indent=2))

    _fire("FIRE_VOTE_RESOLVED", {"question_id": question_id,
                                   "outcome": outcome, "top_vote": top_opt,
                                   "score": top_score})
    log.info(f"Vote {question_id} resolved: {outcome} ({top_opt} @ {top_score:.2f})")
    return data


@router.get("/status")
def vote_status():
    questions = list(VOTES_DIR.glob("*.json"))
    open_q    = []
    resolved_q = []
    for q in questions:
        d = json.loads(q.read_text())
        if d.get("status") == "open":
            open_q.append({"question_id": d["question_id"],
                            "votes": len(d["votes"]),
                            "question": d["question"][:80]})
        else:
            resolved_q.append({"question_id": d["question_id"],
                                "outcome": d.get("outcome"),
                                "top_vote": d.get("top_vote")})
    return {"open": open_q, "resolved": resolved_q,
            "execute_threshold": EXECUTE_THRESHOLD,
            "reject_threshold":  REJECT_THRESHOLD}
