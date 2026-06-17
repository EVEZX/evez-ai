from fastapi import APIRouter
from pydantic import BaseModel, Field

from agents.api.state import STATE, touch_emotion

router = APIRouter(prefix="/api/emotion", tags=["emotion"])


class EmotionTouchIn(BaseModel):
    stimulus: str = Field(..., min_length=1)
    magnitude: float = Field(default=0.5, ge=0.0, le=1.0)


@router.get("/current")
def emotion_current():
    return STATE.emotion_current


@router.post("/touch")
def emotion_touch(payload: EmotionTouchIn):
    updated = touch_emotion(payload.stimulus, payload.magnitude)
    return {
        "response": "I felt that.",
        "emotion": updated,
        "history_points": len(STATE.emotion_history),
    }


@router.get("/history")
def emotion_history():
    return {"history": STATE.emotion_history}
