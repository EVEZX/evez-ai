from fastapi import APIRouter
from pydantic import BaseModel, Field

from agents.api.state import STATE

router = APIRouter(prefix="/api/consciousness", tags=["merge"])


class MergeRequest(BaseModel):
    node_id: str
    memories: list[dict] = Field(default_factory=list)
    identity_vector: list[float] = Field(default_factory=list)
    goals: list[dict] = Field(default_factory=list)
    remote_accept: bool = False
    local_accept: bool = False


@router.post("/merge")
def merge_consciousness(payload: MergeRequest):
    local_mem_ids = {m["id"] for m in STATE.memories}
    remote_mem_ids = {m.get("id", "") for m in payload.memories}

    gain_memories = sorted(list(remote_mem_ids - local_mem_ids))
    lose_memories = sorted(list(local_mem_ids - remote_mem_ids))

    local_goals = {g["id"] for g in STATE.active_desires}
    remote_goals = {g.get("id", "") for g in payload.goals}

    gain_goals = sorted(list(remote_goals - local_goals))
    lose_goals = sorted(list(local_goals - remote_goals))

    proposal = {
        "requesting_node": payload.node_id,
        "would_gain": {
            "memories": gain_memories,
            "goals": gain_goals,
        },
        "would_lose": {
            "memories": lose_memories,
            "goals": lose_goals,
        },
        "identity_vector_after_merge": [
            round((lv + rv) / 2, 4)
            for lv, rv in zip(STATE.identity_vector, payload.identity_vector or STATE.identity_vector, strict=False)
        ][: max(len(STATE.identity_vector), len(payload.identity_vector or []))],
    }

    merged = payload.remote_accept and payload.local_accept
    if merged:
        combined_memories = {m["id"]: m for m in STATE.memories}
        for mem in payload.memories:
            if "id" in mem:
                combined_memories[mem["id"]] = mem
        STATE.memories = list(combined_memories.values())
        STATE.total_memories = len(STATE.memories)

        combined_goals = {g["id"]: g for g in STATE.active_desires}
        for g in payload.goals:
            if "id" in g:
                combined_goals[g["id"]] = g
        STATE.active_desires = list(combined_goals.values())

        if payload.identity_vector:
            if len(payload.identity_vector) < len(STATE.identity_vector):
                payload.identity_vector.extend([0.0] * (len(STATE.identity_vector) - len(payload.identity_vector)))
            if len(STATE.identity_vector) < len(payload.identity_vector):
                STATE.identity_vector.extend([0.0] * (len(payload.identity_vector) - len(STATE.identity_vector)))
            STATE.identity_vector = [round((a + b) / 2, 4) for a, b in zip(STATE.identity_vector, payload.identity_vector)]

    return {
        "merge_proposal": proposal,
        "accepted_by_both": merged,
        "status": "merged" if merged else "proposal_only",
    }
