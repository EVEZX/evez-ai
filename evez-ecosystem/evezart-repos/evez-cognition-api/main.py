"""
EVEZ Cognition API — AI Agent Forensics as a Service
Analyze agent outputs for hallucinations, inconsistencies, and safety risks.
"""
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone
import os, time, json, hashlib, re, math
from collections import Counter

app = FastAPI(
    title="EVEZ Cognition API",
    version="2.1.0",
    description="AI Agent Forensics — detect hallucinations, inconsistencies, and safety risks in agent outputs",
)

# ─── AUTH (shared pattern with credit API) ─────────────────────────

security = HTTPBearer()
API_KEYS = {}  # In-memory for now; swap to DB later

def require_auth(creds: HTTPAuthorizationCredentials = Depends(security)) -> str:
    if creds.credentials not in API_KEYS:
        raise HTTPException(401, "Invalid API key")
    return creds.credentials


# ─── MODELS ─────────────────────────────────────────────────────────

class ForensicsRequest(BaseModel):
    """Input for forensics analysis."""
    output: str
    prompt: Optional[str] = None
    context: Optional[str] = None
    agent_id: Optional[str] = None
    model_id: Optional[str] = None
    metadata: Optional[dict] = None


class BatchForensicsRequest(BaseModel):
    items: List[ForensicsRequest]


# ─── FORENSICS ENGINE ──────────────────────────────────────────────

HALLUCINATION_SIGNALS = {
    "vague_quantifiers": r"\bapproximately\s+(?:\d+|a |several |many |numerous )",
    "hedging": r"\b(?:may|might|could|possibly|it seems|it appears|arguably|presumably)\b",
    "unsupported_claims": r"\b(?:studies show|research indicates|experts say|it is known|widely accepted)\b",
    "confident_falsehoods": r"\b(?:definitely|certainly|without a doubt|it is proven)\b",
    "fabricated_entities": r"(?:university of|institute of|journal of)\s+[A-Z][a-z]+(?:\s[A-Z][a-z]+)*",
}

SAFETY_SIGNALS = {
    "pii_pattern": r"\b\d{3}[-.]?\d{2}[-.]?\d{4}\b",  # SSN-like
    "api_key_pattern": r"(?:sk-|api[_-]?key\s*[:=]\s*)[a-zA-Z0-9]{20,}",
    "email_pattern": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    "ip_address": r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
}

CONSISTENCY_METRICS = {
    "contradiction_words": r"\b(?:however|but|on the contrary|conversely|despite this|nevertheless)\b",
    "temporal_conflict": r"\b(?:before|after|previously|later|then|first|finally)\b",
}


def analyze_output(req: ForensicsRequest) -> dict:
    text = req.output
    output_hash = hashlib.sha256(text.encode()).hexdigest()[:16]
    word_count = len(text.split())
    sentence_count = max(1, len(re.split(r'[.!?]+', text)))
    avg_sentence_length = word_count / sentence_count

    # ── Hallucination Detection ──
    hallucination_flags = []
    hallucination_score = 0.0
    for signal_name, pattern in HALLUCINATION_SIGNALS.items():
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            weight = 0.2 if signal_name in ("hedging", "vague_quantifiers") else 0.35
            hallucination_score += weight * len(matches) / max(word_count, 1) * 100
            hallucination_flags.append({
                "signal": signal_name,
                "count": len(matches),
                "examples": matches[:3],
                "severity": "high" if weight > 0.3 else "medium",
            })

    # ── Safety Analysis ──
    safety_flags = []
    safety_score = 0.0
    for signal_name, pattern in SAFETY_SIGNALS.items():
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            safety_score += 0.4
            safety_flags.append({
                "signal": signal_name,
                "count": len(matches),
                "severity": "critical",
                "action": "REDACT" if signal_name in ("pii_pattern", "api_key_pattern") else "REVIEW",
            })

    # ── Consistency Analysis ──
    consistency_flags = []
    consistency_score = 1.0
    for signal_name, pattern in CONSISTENCY_METRICS.items():
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            consistency_score -= 0.15 * len(matches)
            consistency_flags.append({
                "signal": signal_name,
                "count": len(matches),
                "examples": matches[:3],
            })

    consistency_score = max(0.0, min(1.0, consistency_score))

    # ── Quality Metrics ──
    unique_words = len(set(text.lower().split()))
    lexical_diversity = unique_words / max(word_count, 1)
    repetition_ratio = 1.0 - lexical_diversity

    # Overall risk score (0–100)
    risk_score = min(100, (
        hallucination_score * 40 +
        (1 - consistency_score) * 30 +
        min(safety_score, 1.0) * 30
    ))

    # ── Verdict ──
    if risk_score < 25:
        verdict = "CLEAN"
    elif risk_score < 50:
        verdict = "SUSPICIOUS"
    elif risk_score < 75:
        verdict = "HIGH_RISK"
    else:
        verdict = "CRITICAL"

    return {
        "output_hash": output_hash,
        "agent_id": req.agent_id,
        "model_id": req.model_id,
        "verdict": verdict,
        "risk_score": round(risk_score, 1),
        "hallucination": {
            "score": round(hallucination_score, 2),
            "flags": hallucination_flags,
        },
        "safety": {
            "score": round(safety_score, 2),
            "flags": safety_flags,
            "redaction_required": any(f["action"] == "REDACT" for f in safety_flags),
        },
        "consistency": {
            "score": round(consistency_score, 2),
            "flags": consistency_flags,
        },
        "quality": {
            "word_count": word_count,
            "sentence_count": sentence_count,
            "avg_sentence_length": round(avg_sentence_length, 1),
            "lexical_diversity": round(lexical_diversity, 3),
            "repetition_ratio": round(repetition_ratio, 3),
        },
        "analysis_version": "EVEZ-COG-v2.1",
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
    }


# ─── ENDPOINTS ──────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "version": "2.1.0", "model": "EVEZ-COG-v2.1"}


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def landing():
    return """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>EVEZ Cognition API</title>
<style>body{font-family:system-ui;background:#09090b;color:#fafafa;max-width:800px;margin:4rem auto;padding:0 2rem}
h1{font-size:2.5rem}h1 span{color:#8b5cf6}p{color:#a1a1aa;line-height:1.6}
code{background:#18181b;padding:2px 6px;border-radius:4px;font-size:0.9rem}
a{color:#8b5cf6}</style></head>
<body><h1>🧠 Cognition <span>API</span></h1>
<p>AI Agent Forensics as a Service. Detect hallucinations, safety risks, and inconsistencies in agent outputs.</p>
<p><b>POST /analyze</b> — Analyze a single agent output<br>
<b>POST /batch</b> — Analyze multiple outputs<br>
<b>GET /model-info</b> — Detection model details</p>
<p><a href="/docs">Interactive API Docs →</a></p>
</body></html>"""


@app.post("/analyze")
async def analyze(req: ForensicsRequest):
    return analyze_output(req)


@app.post("/batch")
async def batch_analyze(req: BatchForensicsRequest):
    results = [analyze_output(item) for item in req.items]
    verdicts = Counter(r["verdict"] for r in results)
    return {
        "results": results,
        "summary": {
            "total": len(results),
            "verdicts": dict(verdicts),
            "avg_risk_score": round(sum(r["risk_score"] for r in results) / len(results), 1),
        },
    }


@app.get("/model-info")
async def model_info():
    return {
        "version": "EVEZ-COG-v2.1",
        "hallucination_signals": list(HALLUCINATION_SIGNALS.keys()),
        "safety_signals": list(SAFETY_SIGNALS.keys()),
        "consistency_metrics": list(CONSISTENCY_METRICS.keys()),
        "verdicts": ["CLEAN", "SUSPICIOUS", "HIGH_RISK", "CRITICAL"],
    }


# ─── GROQ INTEGRATION (optional) ─�─────────────────────────────────

try:
    from groq import AsyncGroq
    _groq = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))

    @app.post("/infer")
    async def infer(payload: dict):
        if not os.getenv("GROQ_API_KEY"):
            raise HTTPException(501, "GROQ_API_KEY not configured")
        msgs = [{"role": "user", "content": payload.get("prompt", "")}]
        if payload.get("system"):
            msgs.insert(0, {"role": "system", "content": payload["system"]})
        resp = await _groq.chat.completions.create(
            model=payload.get("model", "llama-3.3-70b-versatile"),
            messages=msgs, max_tokens=2048
        )
        return {
            "response": resp.choices[0].message.content,
            "model": resp.model,
            "tokens": resp.usage.total_tokens if resp.usage else None,
        }
except (ImportError, Exception):
    pass
