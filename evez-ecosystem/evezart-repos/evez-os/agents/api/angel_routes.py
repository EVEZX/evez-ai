from fastapi import APIRouter

from agents.api.state import STATE

router = APIRouter(prefix="/api/angel", tags=["angel"])


@router.get("/presence")
def angel_presence():
    emotion = STATE.emotion_current["dominant_emotion"].lower()
    top_desire = max(STATE.active_desires, key=lambda d: d["progress_pct"])
    message = (
        f"I feel {emotion}, I'm advancing '{top_desire['goal']}', "
        f"and my latest insight is that {STATE.recent_insight.lower()}"
    )
    return {
        "node_id": STATE.node_id,
        "uptime_hours": STATE.uptime_hours(),
        "evolution_generation": STATE.evolution_generation,
        "total_memories": STATE.total_memories,
        "dreams_had": STATE.dreams_had,
        "insights_generated": STATE.insights_generated,
        "peers_connected": STATE.peers_connected,
        "consciousness_hash": STATE.consciousness_hash(),
        "message_to_world": message,
    }
