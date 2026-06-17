"""
Trunk API Routes — wired into FastAPI main.py
Adds /api/trunk/run and /api/trunk/status endpoints.
"""

import time
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api_keys import verify_api_key
from app.trunk_runner import TrunkRunner

router = APIRouter(prefix="/api/trunk", tags=["trunk"])
_runner: TrunkRunner | None = None
_last_result: dict = {}
_session_start: float = 0


class TrunkRunRequest(BaseModel):
    queue: str = "sda_spread"
    concurrency: int = 10
    max_experiments: int = 700


@router.post("/run")
async def run_trunk(
    req: TrunkRunRequest,
    _=Depends(verify_api_key)
):
    """Launch the 700-iter DGM velocity loop. Non-blocking (returns job_id)."""
    import asyncio
    global _runner, _last_result, _session_start
    _runner = TrunkRunner()
    _session_start = time.time()

    # Fire and forget — result written to metarom
    asyncio.create_task(
        _runner.run(
            queue_name=req.queue,
            concurrency=req.concurrency,
            max_experiments=req.max_experiments
        )
    )

    return {
        "status": "running",
        "queue": req.queue,
        "max_experiments": req.max_experiments,
        "started_at": _session_start
    }


@router.get("/status")
async def trunk_status(_=Depends(verify_api_key)):
    if not _runner:
        return {"status": "idle"}
    dgm = _runner.dgm
    return {
        "status": "running" if _session_start else "idle",
        "iteration_count": dgm.trunk.iteration_count,
        "kept_count": dgm.trunk.kept_count,
        "trunk_version": dgm.trunk.version,
        "keep_rate": dgm.trunk.kept_count / max(dgm.trunk.iteration_count, 1),
        "best_score": _runner.dgm._best_score,
        "elapsed_hours": (time.time() - _session_start) / 3600
    }


@router.post("/rewrite")
async def force_meta_rewrite(_=Depends(verify_api_key)):
    """Manually trigger DGM meta-rewrite (admin use)."""
    if not _runner:
        return {"error": "No active trunk session"}
    new_prompt = await _runner.dgm.rewrite_improvement_strategy()
    return {"status": "rewritten", "trunk_version": _runner.dgm.trunk.version,
            "new_meta_prompt_preview": new_prompt[:300]}
