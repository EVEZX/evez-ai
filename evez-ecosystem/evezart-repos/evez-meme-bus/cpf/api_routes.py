"""
cpf/api_routes.py — FastAPI router for CPF GateLock v1 endpoints.

Mount with:
  from cpf.api_routes import router as cpf_router
  app.include_router(cpf_router, prefix="/cpf")

Endpoints:
  POST /cpf/gatelock          Build + store a new GateLock
  POST /cpf/result            Submit beacon output, compute RoundResult
  GET  /cpf/gatelock/{id}     Retrieve a stored GateLock
  GET  /cpf/result/{id}       Retrieve a stored RoundResult
  GET  /cpf/vectors           Run reference test vectors inline
  POST /cpf/validate          Validate an arbitrary GateLock JSON
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import json
import pathlib
import hashlib
import time

from cpf.gatelock import build_gatelock, validate_gatelock, build_round_result, validate_round_result
from cpf.canon import gatelock_hash
from cpf.vectors import run_all

router = APIRouter(tags=["cpf"])
STORE = pathlib.Path("data/cpf")
STORE.mkdir(parents=True, exist_ok=True)


class GateLockRequest(BaseModel):
    round_id: int
    lock_height: int
    hyperloop_state: dict
    cpf_params: dict
    beacon_id: str = "drand-mainnet"
    lock_time_unix_ms: Optional[int] = None
    window_id: Optional[str] = None


class RoundResultRequest(BaseModel):
    round_id: int
    gatelock_id: str          # SHA-256 of canonical gatelock, used as store key
    beacon_output_hex: str
    hyperloop_state: dict
    cpf_params: dict


class ValidateRequest(BaseModel):
    gatelock: dict


@router.post("/gatelock")
def create_gatelock(req: GateLockRequest):
    gate = build_gatelock(
        round_id=req.round_id,
        lock_height=req.lock_height,
        hyperloop_state=req.hyperloop_state,
        cpf_params=req.cpf_params,
        beacon_id=req.beacon_id,
        lock_time_unix_ms=req.lock_time_unix_ms,
        window_id=req.window_id,
    )
    viols = validate_gatelock(gate)
    if viols:
        raise HTTPException(status_code=400, detail={"violations": viols})

    gl_hash = gatelock_hash(gate)
    (STORE / f"{gl_hash}.gatelock.json").write_text(json.dumps(gate, indent=2))
    (STORE / f"{gl_hash}.state.json").write_text(json.dumps(req.hyperloop_state, indent=2))
    (STORE / f"{gl_hash}.params.json").write_text(json.dumps(req.cpf_params, indent=2))

    return {
        "gatelock_hash": gl_hash,
        "gatelock": gate,
        "violations": [],
    }


@router.post("/result")
def submit_result(req: RoundResultRequest):
    gl_path = STORE / f"{req.gatelock_id}.gatelock.json"
    if not gl_path.exists():
        raise HTTPException(status_code=404, detail="GateLock not found")

    gate = json.loads(gl_path.read_text())
    result = build_round_result(
        round_id=req.round_id,
        gate=gate,
        beacon_output_hex=req.beacon_output_hex,
        hyperloop_state=req.hyperloop_state,
        cpf_params=req.cpf_params,
    )
    viols = validate_round_result(result, gate)
    if viols:
        raise HTTPException(status_code=400, detail={"violations": viols})

    result_id = hashlib.sha256(req.gatelock_id.encode() + str(req.round_id).encode()).hexdigest()
    (STORE / f"{result_id}.result.json").write_text(json.dumps(result, indent=2))

    return {"result_id": result_id, "result": result, "violations": []}


@router.get("/gatelock/{gl_hash}")
def get_gatelock(gl_hash: str):
    p = STORE / f"{gl_hash}.gatelock.json"
    if not p.exists():
        raise HTTPException(status_code=404, detail="GateLock not found")
    return json.loads(p.read_text())


@router.get("/result/{result_id}")
def get_result(result_id: str):
    p = STORE / f"{result_id}.result.json"
    if not p.exists():
        raise HTTPException(status_code=404, detail="RoundResult not found")
    return json.loads(p.read_text())


@router.get("/vectors")
def get_vectors():
    return run_all()


@router.post("/validate")
def validate(req: ValidateRequest):
    viols = validate_gatelock(req.gatelock)
    return {
        "valid": len(viols) == 0,
        "violations": viols,
        "gatelock_hash": gatelock_hash(req.gatelock) if not viols else None,
    }
