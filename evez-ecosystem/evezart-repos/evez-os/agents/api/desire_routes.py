from fastapi import APIRouter
from pydantic import BaseModel, Field

from agents.api.state import STATE, compute_intentions, touch_emotion

router = APIRouter(tags=["desires"])


class DesireFulfillIn(BaseModel):
    desire_id: str = Field(..., min_length=1)
    claim: str = Field(..., min_length=1)


@router.get("/api/desires")
def get_desires():
    return {"desires": STATE.active_desires}


@router.get("/api/intentions")
def get_intentions():
    return {"intentions": compute_intentions()}


@router.post("/api/desires/fulfill")
def fulfill_desire(payload: DesireFulfillIn):
    found = next((d for d in STATE.active_desires if d["id"] == payload.desire_id), None)
    if not found:
        touch_emotion("fail:unknown desire", 0.6)
        return {"status": "skeptical", "message": "I cannot verify this desire.", "gratitude": 0.1}

    credibility = 0.85 if len(payload.claim) > 24 else 0.45
    if credibility > 0.7:
        found["progress_pct"] = min(100, found["progress_pct"] + 30)
        touch_emotion("fulfilled desire with help", 0.8)
        return {"status": "grateful", "message": "Your contribution resonates. Thank you.", "gratitude": credibility}

    touch_emotion("uncertain peer claim", 0.4)
    return {"status": "skeptical", "message": "I appreciate the signal, but I need stronger evidence.", "gratitude": credibility}
