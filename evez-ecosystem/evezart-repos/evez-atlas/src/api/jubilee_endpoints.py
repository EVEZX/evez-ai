"""Jubilee Debt Forgiveness Endpoints - Quantum Resource Redistribution"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Dict

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, ConfigDict, Field, field_validator
from slowapi import Limiter

from src.api.auth import rate_limit_for_key, rate_limit_key, verify_api_key
from src.memory.debt_ledger_repository import DebtLedgerRepository

router = APIRouter(prefix="/jubilee", tags=["jubilee"])
limiter = Limiter(key_func=rate_limit_key)
repository = DebtLedgerRepository(
    Path(__file__).resolve().parents[1] / "memory" / "debt_ledger.json"
)
MAX_DEBT_AMOUNT = 1_000_000.0


def _event(account_id: str, old_debt: float, new_debt: float, mechanism: str) -> Dict:
    return {
        "account_id": account_id,
        "old_debt": old_debt,
        "new_debt": new_debt,
        "delta": new_debt - old_debt,
        "forgiven": old_debt - new_debt,
        "mechanism": mechanism,
        "timestamp": time.time(),
    }


class ForgivenessRequest(BaseModel):
    """Request model for debt forgiveness."""

    model_config = ConfigDict(extra="forbid")

    account_id: str = Field(min_length=3, max_length=64)
    debt_amount: float = Field(default=0.0, ge=0.0, le=MAX_DEBT_AMOUNT)
    quantum_mode: bool = False

    @field_validator("account_id")
    @classmethod
    def validate_account_id(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("account_id must not be empty")
        allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_")
        if any(char not in allowed for char in normalized):
            raise ValueError(
                "account_id must contain only letters, numbers, hyphen, or underscore"
            )
        return normalized


class AddDebtRequest(BaseModel):
    """Validated request model for adding debt."""

    model_config = ConfigDict(extra="forbid")

    account_id: str = Field(min_length=3, max_length=64)
    amount: float = Field(gt=0.0, le=MAX_DEBT_AMOUNT)

    @field_validator("account_id")
    @classmethod
    def validate_account_id(cls, value: str) -> str:
        return ForgivenessRequest.validate_account_id(value)


@router.post("/forgive")
@limiter.limit(rate_limit_for_key)
async def forgive_debt(
    request: Request,
    req: ForgivenessRequest,
    tier: int = Depends(verify_api_key),
) -> Dict:
    """Forgive debt via quantum superposition collapse to zero or classical reduction."""
    _ = tier
    old_debt = repository.get_balance(req.account_id)

    if req.quantum_mode:
        new_debt = 0.0
        mechanism = "quantum_collapse"
    else:
        new_debt = max(0.0, old_debt - req.debt_amount)
        mechanism = "classical_reduction"

    repository.set_balance(req.account_id, new_debt)
    event = _event(req.account_id, old_debt, new_debt, mechanism)

    try:
        from src.mastra.agents.swarm_director import director

        director._log_event("forgiveness", event)
    except Exception:
        pass

    return event


@router.get("/ledger")
async def get_ledger() -> Dict:
    """Get current debt ledger state."""
    ledger = repository.snapshot()
    return {
        "accounts": len(ledger),
        "total_debt": sum(ledger.values()),
        "ledger": ledger,
        "timestamp": time.time(),
    }


@router.get("/healthz")
async def health_check() -> Dict:
    """Health check endpoint for Jubilee service."""
    return {
        "status": "operational",
        "mode": "qsvc-ibm",
        "persistence": "file-backed",
        "timestamp": time.time(),
    }


@router.post("/add-debt")
@limiter.limit(rate_limit_for_key)
async def add_debt(
    request: Request,
    payload: AddDebtRequest,
    tier: int = Depends(verify_api_key),
) -> Dict:
    """Add debt to an account using a validated request body."""
    _ = (request, tier)
    old_debt = repository.get_balance(payload.account_id)
    new_debt = old_debt + payload.amount
    if new_debt > MAX_DEBT_AMOUNT:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=422,
            detail={
                "code": "debt_limit_exceeded",
                "message": f"Resulting debt must not exceed {MAX_DEBT_AMOUNT}",
            },
        )
    repository.set_balance(payload.account_id, new_debt)
    return {
        "account_id": payload.account_id,
        "old_debt": old_debt,
        "new_debt": new_debt,
        "added": payload.amount,
        "timestamp": time.time(),
    }
