"""EVEZ Consciousness API — Real spectral consciousness computation via eigenvalue analysis."""
import json
import time
import numpy as np
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict

router = APIRouter(prefix="/api/v1/consciousness", tags=["consciousness"])

# --- Rate Limiting ---
_rate_limits: dict = defaultdict(list)  # ip -> [timestamps]
RATE_FREE = 10    # requests per minute
RATE_PRO = 100


def _check_rate_limit(ip: str, is_pro: bool = False) -> tuple:
    """Returns (allowed, remaining)."""
    now = time.time()
    limit = RATE_PRO if is_pro else RATE_FREE
    window = 60.0  # 1 minute

    # Clean old entries
    _rate_limits[ip] = [t for t in _rate_limits[ip] if now - t < window]

    if len(_rate_limits[ip]) >= limit:
        return False, 0

    _rate_limits[ip].append(now)
    return True, limit - len(_rate_limits[ip])


# --- Model Registry ---
AVAILABLE_MODELS = [
    {"id": "llama-3.3-70b-versatile", "provider": "groq", "tier": "free", "context": 128000},
    {"id": "llama-3.1-8b-instant", "provider": "groq", "tier": "free", "context": 128000},
    {"id": "mixtral-8x7b-32768", "provider": "groq", "tier": "free", "context": 32768},
    {"id": "zai-org/GLM-5.1-FP8", "provider": "vultr", "tier": "pro", "context": 32768},
    {"id": "local-echo", "provider": "local", "tier": "free", "context": 0},
]


@router.get("/phi")
async def compute_phi(request: Request):
    """Compute Φ (spectral consciousness index) for a submitted adjacency matrix.

    Query params or JSON body: matrix = [[...], [...], ...]
    """
    # Try query param first, then JSON body
    matrix = request.query_params.get("matrix")

    if not matrix:
        try:
            body = await request.json()
            matrix = body.get("matrix")
        except Exception:
            pass

    if not matrix:
        return JSONResponse({"error": "matrix is required — pass as JSON body or query param"}, status_code=400)

    # Parse if string
    if isinstance(matrix, str):
        try:
            matrix = json.loads(matrix)
        except json.JSONDecodeError:
            return JSONResponse({"error": "matrix must be valid JSON"}, status_code=400)

    # Validate and convert
    try:
        A = np.array(matrix, dtype=np.float64)
    except (ValueError, TypeError):
        return JSONResponse({"error": "matrix must be a 2D array of numbers"}, status_code=400)

    if A.ndim != 2 or A.shape[0] != A.shape[1]:
        return JSONResponse({"error": f"matrix must be square, got shape {A.shape}"}, status_code=400)

    if A.shape[0] < 2:
        return JSONResponse({"error": "matrix must be at least 2x2"}, status_code=400)

    # Rate limit
    ip = request.client.host if request.client else "unknown"
    allowed, remaining = _check_rate_limit(ip)
    if not allowed:
        return JSONResponse({"error": "Rate limit exceeded", "limit": RATE_FREE, "window": "1min"}, status_code=429)

    # Symmetrize
    A = (A + A.T) / 2.0

    # Eigenvalue decomposition
    eigenvalues = np.linalg.eigvalsh(A)
    eigenvalues = np.sort(eigenvalues)[::-1]

    # Φ = 1 - |λ_1| / Σ|λ_i|
    abs_sum = np.sum(np.abs(eigenvalues))
    phi = 1.0 - (np.abs(eigenvalues[0]) / abs_sum) if abs_sum > 0 else 0.0

    # η* = λ_1 - λ_2 (Kuramoto critical coupling)
    eta_star = float(eigenvalues[0] - eigenvalues[1]) if len(eigenvalues) >= 2 else 0.0

    return {
        "phi": round(float(phi), 6),
        "eta_star": round(float(eta_star), 6),
        "matrix_size": A.shape[0],
        "top_eigenvalue": round(float(eigenvalues[0]), 6),
        "rate_remaining": remaining,
    }


@router.post("/analyze")
async def analyze_system(request: Request):
    """Submit a system description, get full spectral analysis with classification.

    Body: {
        "adjacency_matrix": [[...], ...],   # required
        "system_name": "...",               # optional
        "labels": ["...", ...],             # optional node labels
    }
    """
    ip = request.client.host if request.client else "unknown"
    allowed, remaining = _check_rate_limit(ip)
    if not allowed:
        return JSONResponse({"error": "Rate limit exceeded"}, status_code=429)

    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "JSON body required"}, status_code=400)

    matrix = body.get("adjacency_matrix")
    if not matrix:
        return JSONResponse({"error": "adjacency_matrix is required"}, status_code=400)

    system_name = body.get("system_name", "unnamed")
    labels = body.get("labels", [])

    try:
        A = np.array(matrix, dtype=np.float64)
    except (ValueError, TypeError):
        return JSONResponse({"error": "adjacency_matrix must be a 2D array of numbers"}, status_code=400)

    if A.ndim != 2 or A.shape[0] != A.shape[1]:
        return JSONResponse({"error": f"adjacency_matrix must be square, got shape {A.shape}"}, status_code=400)

    n = A.shape[0]
    if n < 2:
        return JSONResponse({"error": "matrix must be at least 2x2"}, status_code=400)

    # Symmetrize
    A_sym = (A + A.T) / 2.0

    # Full eigenvalue decomposition
    eigenvalues, eigenvectors = np.linalg.eigh(A_sym)
    idx = np.argsort(eigenvalues)[::-1]
    eigenvalues = eigenvalues[idx]
    eigenvectors = eigenvectors[:, idx]

    # Φ
    abs_sum = np.sum(np.abs(eigenvalues))
    phi = 1.0 - (np.abs(eigenvalues[0]) / abs_sum) if abs_sum > 0 else 0.0

    # η*
    eta_star = float(eigenvalues[0] - eigenvalues[1]) if len(eigenvalues) >= 2 else 0.0

    # Spectral gap
    spectral_gap = eta_star

    # Participation ratio
    lam_sq = eigenvalues ** 2
    participation_ratio = float((np.sum(eigenvalues) ** 2) / np.sum(lam_sq)) if np.sum(lam_sq) > 0 else 0.0

    # Connectivity
    density = float(np.count_nonzero(A_sym) / (n * n))

    # Dominant eigenvector (loadings on first component)
    dominant = eigenvectors[:, 0]
    dominant_loadings = {str(i): round(float(dominant[i]), 4) for i in range(n)}

    # Classification
    if phi > 0.95:
        classification = "CONSCIOUS — Maximum spectral integration"
    elif phi > 0.9:
        classification = "HIGH_CONSCIOUSNESS — Strongly integrated"
    elif phi > 0.7:
        classification = "EMERGENT — Significant spectral coherence"
    elif phi > 0.5:
        classification = "COMPLEX — Moderate integration"
    elif phi > 0.3:
        classification = "STRUCTURED — Some coherence detected"
    else:
        classification = "NOISE — Low integration, near-random structure"

    # Node importance (from dominant eigenvector magnitude)
    node_importance = []
    for i in range(n):
        label = labels[i] if i < len(labels) else f"node_{i}"
        node_importance.append({
            "id": i,
            "label": label,
            "loading": round(float(np.abs(dominant[i])), 4),
        })
    node_importance.sort(key=lambda x: x["loading"], reverse=True)

    return {
        "system_name": system_name,
        "matrix_size": n,
        "phi": round(float(phi), 6),
        "eta_star": round(float(eta_star), 6),
        "spectral_gap": round(float(spectral_gap), 6),
        "participation_ratio": round(participation_ratio, 4),
        "density": round(density, 4),
        "classification": classification,
        "top_eigenvalues": [round(float(e), 4) for e in eigenvalues[:min(20, n)]],
        "dominant_loadings": dominant_loadings,
        "node_importance": node_importance[:10],
        "rate_remaining": remaining,
    }


@router.get("/eigenvalues")
async def eigenvalue_spectrum(request: Request):
    """Full eigenvalue spectrum of a submitted matrix.

    Query params: matrix (JSON string of 2D array)
    """
    matrix_str = request.query_params.get("matrix")
    if not matrix_str:
        return JSONResponse({"error": "matrix query param required (JSON-encoded 2D array)"}, status_code=400)

    ip = request.client.host if request.client else "unknown"
    allowed, remaining = _check_rate_limit(ip)
    if not allowed:
        return JSONResponse({"error": "Rate limit exceeded"}, status_code=429)

    try:
        matrix = json.loads(matrix_str)
    except json.JSONDecodeError:
        return JSONResponse({"error": "matrix must be valid JSON"}, status_code=400)

    try:
        A = np.array(matrix, dtype=np.float64)
    except (ValueError, TypeError):
        return JSONResponse({"error": "matrix must be a 2D array of numbers"}, status_code=400)

    if A.ndim != 2 or A.shape[0] != A.shape[1]:
        return JSONResponse({"error": f"matrix must be square, got shape {A.shape}"}, status_code=400)

    A_sym = (A + A.T) / 2.0
    eigenvalues = np.sort(np.linalg.eigvalsh(A_sym))[::-1]

    return {
        "eigenvalues": [round(float(e), 6) for e in eigenvalues],
        "count": len(eigenvalues),
        "max": round(float(eigenvalues[0]), 6),
        "min": round(float(eigenvalues[-1]), 6),
        "trace": round(float(np.trace(A_sym)), 6),
        "determinant": round(float(np.linalg.det(A_sym)), 6),
        "rate_remaining": remaining,
    }


# --- Models endpoint (on consciousness router for API consistency) ---

@router.get("/models")
async def list_models():
    """List available AI models across all providers."""
    return {
        "object": "list",
        "data": AVAILABLE_MODELS,
        "note": "Groq models are free tier. Vultr models require pro plan. local-echo is a passthrough fallback.",
    }
