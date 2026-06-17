from __future__ import annotations

from fastapi import APIRouter

from agents.mesh.pusher import ImmortalStatePusher
from agents.mesh.recovery import MeshRecoveryDaemon
from agents.mesh.registry import MeshRegistry

router = APIRouter(prefix="/api/mesh", tags=["mesh"])


class _NoopBus:
    def emit(self, _event: str, _payload: dict) -> None:
        return None


_CURRENT_STATE = {
    "agent_version": "bootstrap",
    "temporal_chain_tip": "genesis",
    "memory_snapshot": {},
    "gnn_topology": {},
    "eban_state": {},
    "lban_state": {},
    "wormhole_blob": {},
}


registry = MeshRegistry()
pusher = ImmortalStatePusher(registry=registry, state_provider=lambda: _CURRENT_STATE)
recovery = MeshRecoveryDaemon(registry=registry, event_bus=_NoopBus(), restore_fn=lambda recovered: _CURRENT_STATE.update(recovered))


@router.get("/status")
async def mesh_status() -> dict:
    peers = [peer.to_bootstrap_dict() for peer in registry.peers]
    healthy_count = sum(1 for p in peers if p.get("last_sync_ts", 0) > 0)
    return {
        "peers": peers,
        "healthy_count": healthy_count,
        "last_push_ts": pusher.last_push_ts,
        "recovery_mode_active": recovery.local_only_mode,
    }


@router.get("/history")
async def mesh_history() -> dict:
    return {"events": pusher.history()[-100:]}


@router.post("/force_push")
async def force_push() -> dict:
    event = await pusher.push_once()
    return {
        "timestamp_ns": event.timestamp_ns,
        "peer_results": event.peer_results,
        "success_count": event.success_count,
    }
