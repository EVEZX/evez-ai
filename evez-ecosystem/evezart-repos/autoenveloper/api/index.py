"""
EVEZ Autoenveloper API v2 — Full Mathematical Surface
ChatGPT-compatible via OpenAPI schema + ai-plugin.json

Endpoints:
  POST /isomorphism    — Φ(x) fingerprint + S(x,y) similarity
  POST /ricci-flow     — Curvature smoothing on embedding vectors
  POST /entropy-field  — Local entropy tensor over sequence
  POST /gradient-tunnel — Loss surface tunneling escape
  POST /horizon        — Context event horizon + Hawking radiation
  POST /cipher         — Cipher gen + structural isomorphism (legacy)
  POST /geometric      — Fractal dimension, spectral, symmetry
  POST /linguistic     — N-gram, authorship fingerprint, PII mask
  GET  /health         — System status
  GET  /openapi.json   — OpenAPI 3.1 schema
  GET  /.well-known/ai-plugin.json — ChatGPT plugin manifest
"""
import os, sys, time, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

# ── Math modules
from lib.math_invariants import fingerprint, similarity, flatten
from lib.spacetime_ops import (
    ricci_flow, entropy_field, gradient_tunnel, context_horizon
)

# ── Legacy modules (if present)
try:
    from lib.ciphage_gen import (
        generate_substitution_cipher, generate_polyalphabetic_cipher,
        generate_transposition_cipher, generate_lsystem_fractal,
        generate_numeric_sequence, detect_structural_isomorphism
    )
    CIPHAGE_AVAILABLE = True
except ImportError:
    CIPHAGE_AVAILABLE = False

try:
    from lib.geometric import (
        compute_fractal_dimension, compute_spectral_analysis,
        compute_rotational_symmetry, compute_convex_hull_area,
        compute_centroid
    )
    GEOMETRIC_AVAILABLE = True
except ImportError:
    GEOMETRIC_AVAILABLE = False

try:
    from lib.linguistic import (
        compute_ngram_profile, compute_authorship_fingerprint,
        anonymize_pii
    )
    LINGUISTIC_AVAILABLE = True
except ImportError:
    LINGUISTIC_AVAILABLE = False


# ══════════════════════════════════════════════════════════════
app = FastAPI(
    title="EVEZ Autoenveloper",
    description="Multi-basis structural invariant detector + spacetime operators. "
                "Fingerprints any sequence with compression, mutual information, "
                "spectral gap, and persistence entropy. Cross-domain isomorphism "
                "detection, Ricci flow, entropy fields, gradient tunneling.",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

START_TIME = time.time()


# ══════════════════════════════════════════════════════════════
# SCHEMAS
# ══════════════════════════════════════════════════════════════

class IsoRequest(BaseModel):
    domain_a: str = Field(..., description="First domain / sequence to fingerprint")
    domain_b: str = Field(..., description="Second domain / sequence to fingerprint")

class IsoResponse(BaseModel):
    similarity: float = Field(..., description="S(x,y) in [0,1], 1=structurally identical")
    vector_a: List[float]
    vector_b: List[float]
    breakdown: Dict[str, Any]

class RicciRequest(BaseModel):
    embeddings: List[List[float]] = Field(...,
        description="List of embedding vectors (token/concept representations)")
    iterations: int = Field(10, ge=1, le=50)
    dt: float = Field(0.01, gt=0, le=0.1, description="Flow step size")

class EntropyRequest(BaseModel):
    sequence: str = Field(..., description="Token sequence or text")
    window_size: int = Field(16, ge=4, le=256)
    stride: int = Field(4, ge=1, le=64)

class TunnelRequest(BaseModel):
    loss_surface: List[float] = Field(...,
        description="Sampled loss values along a 1D slice")
    noise_scale: float = Field(0.1, gt=0, le=2.0)
    hessian_approx: bool = True

class HorizonRequest(BaseModel):
    sequence: str = Field(..., description="Long sequence to bifurcate at context boundary")
    window_size: int = Field(512, ge=16, le=8192)
    radiation_dims: int = Field(32, ge=4, le=128)

class CipherRequest(BaseModel):
    mode: str = Field("substitution",
        description="Mode: substitution | polyalphabetic | transposition | lsystem | numeric | isomorphism")
    text: Optional[str] = None
    seed: Optional[str] = None
    domain_a: Optional[str] = None
    domain_b: Optional[str] = None
    sequence_type: Optional[str] = None
    rule: Optional[str] = None
    steps: Optional[int] = None
    n: Optional[int] = None

class GeometricRequest(BaseModel):
    mode: str = Field("fractal",
        description="Mode: fractal | spectral | symmetry | hull | centroid")
    points: Optional[List[List[float]]] = None
    sequence: Optional[str] = None
    signal: Optional[List[float]] = None

class LinguisticRequest(BaseModel):
    mode: str = Field("ngram", description="Mode: ngram | authorship | anonymize")
    text: str
    n: Optional[int] = 2


# ══════════════════════════════════════════════════════════════
# ENDPOINTS
# ══════════════════════════════════════════════════════════════

@app.get("/health")
def health():
    return {
        "status": "ok",
        "version": "2.0.0",
        "uptime_s": round(time.time() - START_TIME, 1),
        "modules": {
            "math_invariants": True,
            "spacetime_ops": True,
            "ciphage": CIPHAGE_AVAILABLE,
            "geometric": GEOMETRIC_AVAILABLE,
            "linguistic": LINGUISTIC_AVAILABLE,
        }
    }


@app.post("/isomorphism", response_model=IsoResponse)
def isomorphism(req: IsoRequest):
    """
    Compute Φ(x) fingerprint vectors and S(x,y) structural similarity.

    Φ(x) = [C(x), I₁..I₅(x), λ₂(x), Hₚ(x)]
    S(x,y) = √( cos(Φx,Φy) · (1 - JS(Φx,Φy)) )

    Cross-domain: code ↔ finance ↔ biology ↔ language.
    """
    try:
        fa = fingerprint(req.domain_a)
        fb = fingerprint(req.domain_b)
        score, va, vb = similarity(fa, fb)
        return IsoResponse(
            similarity=round(float(score), 6),
            vector_a=va.tolist(),
            vector_b=vb.tolist(),
            breakdown={
                "compression":   {"a": fa["compression"], "b": fb["compression"]},
                "mi_profile":    {"a": fa["mi"], "b": fb["mi"]},
                "spectral_gap":  {"a": fa["lambda2"], "b": fb["lambda2"]},
                "persistence":   {"a": fa["entropy"], "b": fb["entropy"]},
                "note": (
                    "Hybrid invariant: C=LZ77 K(x) bound, MI=dependency structure, "
                    "λ₂=algebraic connectivity class, Hₚ=Lipschitz-stable topology"
                )
            }
        )
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/ricci-flow")
def ricci_flow_endpoint(req: RicciRequest):
    """
    Discrete Ollivier-Ricci flow on embedding neighborhood graph.
    Redistributes curvature so overloaded semantic regions flatten,
    sparse regions contract. Implements Semantic Ricci Flow (SRF).
    """
    try:
        return ricci_flow(req.embeddings, req.iterations, req.dt)
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/entropy-field")
def entropy_field_endpoint(req: EntropyRequest):
    """
    Local entropy tensor H(t) over a sequence.
    Returns inflation mask: high-entropy regions expand (creative),
    low-entropy regions contract (precise). Backs Semantic Inflation Fields (SIF).
    """
    try:
        return entropy_field(req.sequence, req.window_size, req.stride)
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/gradient-tunnel")
def gradient_tunnel_endpoint(req: TunnelRequest):
    """
    Gradient Tunneling Resonance (GTR): inject stochastic resonance
    noise tuned to local Hessian eigenvalues to escape flat loss basins.
    Returns perturbed surface + escape path coordinates.
    """
    try:
        return gradient_tunnel(req.loss_surface, req.noise_scale, req.hessian_approx)
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/horizon")
def horizon_endpoint(req: HorizonRequest):
    """
    Token Horizon Bifurcation (THB) + Context Event Horizon (CEH).
    Splits at context boundary. Exterior tokens become Hawking radiation:
    a compressed entropy signature that reconstructs "forgotten" context.
    """
    try:
        return context_horizon(req.sequence, req.window_size, req.radiation_dims)
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/cipher")
def cipher(req: CipherRequest):
    """
    Cipher generation + cross-domain structural isomorphism (legacy).
    Modes: substitution, polyalphabetic, transposition, lsystem, numeric, isomorphism.
    """
    if req.mode == "isomorphism":
        if not req.domain_a or not req.domain_b:
            raise HTTPException(400, "domain_a and domain_b required for isomorphism mode")
        fa = fingerprint(req.domain_a)
        fb = fingerprint(req.domain_b)
        score, va, vb = similarity(fa, fb)
        return {
            "mode": "isomorphism",
            "similarity": round(float(score) * 100, 2),
            "vector_a": va.tolist(), "vector_b": vb.tolist(),
        }

    if not CIPHAGE_AVAILABLE:
        raise HTTPException(501, "ciphage_gen module not available")
    
    text = req.text or "EVEZ"
    seed = req.seed or "evez666"
    
    if req.mode == "substitution":
        return generate_substitution_cipher(text, seed)
    elif req.mode == "polyalphabetic":
        return generate_polyalphabetic_cipher(text, seed)
    elif req.mode == "transposition":
        return generate_transposition_cipher(text, seed)
    elif req.mode == "lsystem":
        return generate_lsystem_fractal(req.rule or "F+F-F-F+F", req.steps or 3)
    elif req.mode == "numeric":
        return generate_numeric_sequence(req.sequence_type or "collatz", req.n or 10)
    else:
        raise HTTPException(400, f"Unknown mode: {req.mode}")


@app.post("/geometric")
def geometric(req: GeometricRequest):
    """
    Geometric / spectral / fractal analysis.
    Modes: fractal (box-counting), spectral (DFT), symmetry (rotational), hull, centroid.
    """
    if not GEOMETRIC_AVAILABLE:
        # Fallback: basic geometric computations
        if req.points:
            pts = req.points
            cx = sum(p[0] for p in pts) / len(pts)
            cy = sum(p[1] for p in pts) / len(pts)
            return {"mode": req.mode, "centroid": [cx, cy], "count": len(pts)}
        raise HTTPException(501, "geometric module not available")
    
    if req.mode == "fractal":
        return compute_fractal_dimension(req.points or [])
    elif req.mode == "spectral":
        return compute_spectral_analysis(req.signal or [])
    elif req.mode == "symmetry":
        return compute_rotational_symmetry(req.points or [])
    elif req.mode == "hull":
        return compute_convex_hull_area(req.points or [])
    elif req.mode == "centroid":
        return compute_centroid(req.points or [])
    else:
        raise HTTPException(400, f"Unknown mode: {req.mode}")


@app.post("/linguistic")
def linguistic(req: LinguisticRequest):
    """
    Linguistic pattern analysis: n-gram profiles, authorship fingerprinting, PII anonymization.
    """
    if not LINGUISTIC_AVAILABLE:
        # Fallback: basic n-gram
        from collections import Counter
        tokens = req.text.split()
        n = req.n or 2
        ngrams = [" ".join(tokens[i:i+n]) for i in range(len(tokens)-n+1)]
        return {"mode": req.mode, "ngrams": Counter(ngrams).most_common(20)}
    
    if req.mode == "ngram":
        return compute_ngram_profile(req.text, req.n or 2)
    elif req.mode == "authorship":
        return compute_authorship_fingerprint(req.text)
    elif req.mode == "anonymize":
        return anonymize_pii(req.text)
    else:
        raise HTTPException(400, f"Unknown mode: {req.mode}")


# ══════════════════════════════════════════════════════════════
# CHATGPT PLUGIN MANIFESTS
# ══════════════════════════════════════════════════════════════

@app.get("/.well-known/ai-plugin.json")
def plugin_manifest():
    base = os.getenv("VERCEL_URL", "autoenveloper.vercel.app")
    if not base.startswith("http"):
        base = f"https://{base}"
    return JSONResponse({
        "schema_version": "v1",
        "name_for_human": "EVEZ Autoenveloper",
        "name_for_model": "autoenveloper",
        "description_for_human": "Cross-domain structural isomorphism detector + spacetime operators. Fingerprints any text with compression, mutual information, spectral gap, persistence entropy.",
        "description_for_model": "Mathematical invariant API. Use /isomorphism to compare structural similarity across any domains (code, finance, biology, language). Use /ricci-flow, /entropy-field, /gradient-tunnel, /horizon for spacetime field operations on sequences and embeddings.",
        "auth": {"type": "none"},
        "api": {"type": "openapi", "url": f"{base}/openapi.json"},
        "logo_url": f"{base}/logo.png",
        "contact_email": "fiersteity@gmail.com",
        "legal_info_url": f"{base}/legal"
    })


@app.get("/openapi.json")
def openapi():
    return app.openapi()
