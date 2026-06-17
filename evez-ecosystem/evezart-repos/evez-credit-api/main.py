"""EVEZ Credit Scoring API — FastAPI Application"""
import time
from collections import defaultdict
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone

import evez_credit_engine as engine
import credit_db
from stripe_billing import router as billing_router

# ─── RATE LIMITER (in-memory, per-key) ─────────────────────────────

_rate_store: dict[str, list[float]] = defaultdict(list)
RATE_LIMITS = {"free": 60, "pro": 300}  # requests per minute
RATE_WINDOW = 60.0  # seconds


def _check_rate(api_key: str, plan: str) -> None:
    now = time.time()
    window = _rate_store[api_key]
    # Prune old entries
    _rate_store[api_key] = [t for t in window if now - t < RATE_WINDOW]
    limit = RATE_LIMITS.get(plan, 60)
    if len(_rate_store[api_key]) >= limit:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded: {limit} requests/minute for {plan} plan"
        )
    _rate_store[api_key].append(now)


# ─── AUTH ───────────────────────────────────────────────────────────

security = HTTPBearer()


def require_auth(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    key = credentials.credentials
    api_key = credit_db.get_api_key(key)
    if not api_key:
        raise HTTPException(status_code=401, detail="Invalid or inactive API key")
    if not api_key["active"]:
        raise HTTPException(status_code=401, detail="API key deactivated")
    if api_key["plan"] == "free" and api_key["credits_remaining"] <= 0:
        raise HTTPException(status_code=403, detail="Monthly credits depleted. Upgrade to Pro for unlimited access.")
    return api_key


# ─── MODELS ─────────────────────────────────────────────────────────

class ApplicantInput(BaseModel):
    id: Optional[str] = None
    payment_history: float = 85.0
    credit_utilization: float = 30.0
    credit_age: float = 5.0
    credit_mix: int = 3
    new_inquiries: int = 1
    dti_ratio: float = 30.0
    derogatory_marks: int = 0
    total_accounts: int = 8
    annual_income: Optional[float] = None
    requested_amount: Optional[float] = None


class BatchRequest(BaseModel):
    applicants: Optional[List[ApplicantInput]] = None
    count: int = 10


class KeyCreateRequest(BaseModel):
    email: str
    plan: str = "free"


# ─── APP ────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    credit_db.init_db()
    yield


app = FastAPI(
    title="EVEZ Credit Scoring API",
    version="2.2.0",
    description="8-factor FICO-equivalent credit scoring (300–850) with ECOA/FCRA compliance, API key auth, rate limiting, and Stripe billing",
    lifespan=lifespan,
)
app.include_router(billing_router)


# ─── LANDING PAGE ───────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def landing():
    from pathlib import Path
    return Path("static/index.html").read_text()


# ─── PUBLIC ENDPOINTS ───────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "version": "2.2.0", "model": "EVEZ-CS-v2.0"}


@app.post("/register")
async def register_key(req: KeyCreateRequest):
    """Register a new API key. For demo — in production, use Stripe checkout."""
    import secrets
    key = f"evez_{secrets.token_hex(24)}"
    credits = 100 if req.plan == "free" else 999999
    credit_db.create_api_key(key, req.email, req.plan, credits)
    return {"api_key": key, "plan": req.plan, "credits": credits}


# ─── AUTHENTICATED ENDPOINTS ────────────────────────────────────────

@app.post("/score")
async def score_applicant(applicant: ApplicantInput, api_key: dict = Depends(require_auth)):
    _check_rate(api_key["key"], api_key["plan"])
    result = engine.score_applicant(applicant.model_dump())
    # Persist
    credit_db.insert_scoring_request(
        applicant_id=result["applicant_id"],
        credit_score=result["credit_score"],
        grade=result["grade"],
        decision=result["decision"],
        factors=result["factor_breakdown"],
    )
    credit_db.log_usage(api_key["key"], "/score")
    if api_key["plan"] == "free":
        credit_db.decrement_credits(api_key["key"])
    return result


@app.post("/batch")
async def batch_score(request: BatchRequest, api_key: dict = Depends(require_auth)):
    _check_rate(api_key["key"], api_key["plan"])
    if request.applicants:
        results = [engine.score_applicant(a.model_dump()) for a in request.applicants]
        for r in results:
            credit_db.insert_scoring_request(
                applicant_id=r["applicant_id"],
                credit_score=r["credit_score"],
                grade=r["grade"],
                decision=r["decision"],
                factors=r["factor_breakdown"],
            )
        credit_db.log_usage(api_key["key"], "/batch", len(results))
        if api_key["plan"] == "free":
            credit_db.decrement_credits(api_key["key"], len(results))
        return {"results": results, "count": len(results)}
    # Generate random applicants
    results = [engine.score_applicant(engine.generate_sample_applicant(seed=i)) for i in range(request.count)]
    for r in results:
        credit_db.insert_scoring_request(
            applicant_id=r["applicant_id"],
            credit_score=r["credit_score"],
            grade=r["grade"],
            decision=r["decision"],
            factors=r["factor_breakdown"],
        )
    credit_db.log_usage(api_key["key"], "/batch", request.count)
    if api_key["plan"] == "free":
        credit_db.decrement_credits(api_key["key"], request.count)
    return {"results": results, "count": len(results)}


@app.get("/model-info")
async def model_info(api_key: dict = Depends(require_auth)):
    _check_rate(api_key["key"], api_key["plan"])
    credit_db.log_usage(api_key["key"], "/model-info")
    return {
        "version": "EVEZ-CS-v2.0",
        "factors": list(engine.RISK_FACTORS.keys()),
        "weights": {k: v["weight"] for k, v in engine.RISK_FACTORS.items()},
        "score_range": list(engine.SCORE_RANGE),
        "grade_thresholds": engine.GRADE_THRESHOLDS,
        "compliance": ["ECOA", "FCRA", "Reg B", "Fair Lending"]
    }


@app.get("/usage")
async def usage_stats(api_key: dict = Depends(require_auth)):
    stats = credit_db.get_usage_stats(api_key["key"])
    monthly = credit_db.get_monthly_usage(api_key["key"])
    return {
        "api_key": api_key["key"][:12] + "...",
        "plan": api_key["plan"],
        "credits_remaining": api_key["credits_remaining"],
        "monthly_requests": monthly,
        "daily_breakdown": stats,
    }
