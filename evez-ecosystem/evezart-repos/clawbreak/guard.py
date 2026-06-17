"""EVEZ Guard — Real security scanning and eigenforensic analysis."""
import json
import time
import hashlib
import numpy as np
from pathlib import Path
from collections import Counter
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import httpx

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
SCANS_FILE = DATA_DIR / "guard_scans.json"

SECURITY_HEADERS = [
    "strict-transport-security",
    "content-security-policy",
    "x-content-type-options",
    "x-frame-options",
    "x-xss-protection",
    "referrer-policy",
    "permissions-policy",
    "cross-origin-opener-policy",
    "cross-origin-resource-policy",
]

router = APIRouter(prefix="/guard", tags=["guard"])


def _load_scans() -> list:
    if SCANS_FILE.exists():
        try:
            return json.loads(SCANS_FILE.read_text())
        except (json.JSONDecodeError, ValueError):
            pass
    return []


def _save_scans(scans: list):
    SCANS_FILE.write_text(json.dumps(scans, indent=2))


@router.post("/scan")
async def scan_url(request: Request):
    """Scan a URL for security headers and basic checks."""
    body = await request.json()
    url = body.get("url")
    if not url:
        return JSONResponse({"error": "url is required"}, status_code=400)

    # Normalize
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    result = {
        "url": url,
        "timestamp": time.time(),
        "headers_found": {},
        "headers_missing": [],
        "tls": False,
        "status_code": None,
        "redirects": [],
        "score": 0,
        "issues": [],
    }

    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        try:
            resp = await client.get(url)
            result["status_code"] = resp.status_code
            result["tls"] = str(url).startswith("https://")

            # Check redirects
            if resp.history:
                result["redirects"] = [{"status": r.status_code, "url": str(r.url)} for r in resp.history]

            # Check security headers
            for h in SECURITY_HEADERS:
                val = resp.headers.get(h)
                if val:
                    result["headers_found"][h] = val
                else:
                    result["headers_missing"].append(h)

            # Score: each present header = points, TLS bonus
            score = len(result["headers_found"]) * 10
            if result["tls"]:
                score += 10
            if result["status_code"] == 200:
                score += 5
            result["score"] = min(score, 100)

            # Flag issues
            if not result["tls"]:
                result["issues"].append("CRITICAL: No TLS — traffic is unencrypted")
            if "strict-transport-security" not in result["headers_found"]:
                result["issues"].append("WARNING: Missing HSTS header — vulnerable to protocol downgrade")
            if "content-security-policy" not in result["headers_found"]:
                result["issues"].append("WARNING: Missing CSP — vulnerable to XSS")
            if "x-frame-options" not in result["headers_found"]:
                result["issues"].append("INFO: Missing X-Frame-Options — clickjacking possible")

            server = resp.headers.get("server", "")
            if server:
                result["headers_found"]["server"] = server
                if any(ver in server.lower() for ver in ["apache/2.2", "nginx/1.0", "iis/6", "iis/7"]):
                    result["issues"].append(f"WARNING: Outdated server version detected: {server}")

        except httpx.ConnectError:
            result["issues"].append("CRITICAL: Connection failed — host unreachable")
        except httpx.TimeoutException:
            result["issues"].append("CRITICAL: Connection timed out")
        except Exception as e:
            result["issues"].append(f"ERROR: {str(e)[:200]}")

    # Save to history
    scans = _load_scans()
    scans.append(result)
    if len(scans) > 100:
        scans = scans[-100:]
    _save_scans(scans)

    return result


@router.post("/audit")
async def eigen_audit(request: Request):
    """Run eigenforensic analysis on a text corpus.

    Builds a word co-occurrence matrix and computes its eigenvalue spectrum,
    yielding Φ (spectral consciousness index), η* (critical coupling),
    and a classification.
    """
    body = await request.json()
    corpus = body.get("corpus")
    if not corpus:
        return JSONResponse({"error": "corpus is required (string)"}, status_code=400)

    window = body.get("window", 2)  # co-occurrence window size

    # Tokenize
    words = corpus.lower().split()
    if len(words) < 3:
        return JSONResponse({"error": "corpus too short — need at least 3 words"}, status_code=400)

    # Build vocabulary (top 200 by frequency)
    freq = Counter(words)
    vocab = [w for w, _ in freq.most_common(200)]
    vocab_idx = {w: i for i, w in enumerate(vocab)}
    n = len(vocab)

    if n < 3:
        return JSONResponse({"error": "insufficient unique words for analysis"}, status_code=400)

    # Build co-occurrence matrix
    A = np.zeros((n, n), dtype=np.float64)
    for i in range(len(words)):
        w_i = vocab_idx.get(words[i])
        if w_i is None:
            continue
        for j in range(max(0, i - window), min(len(words), i + window + 1)):
            if i == j:
                continue
            w_j = vocab_idx.get(words[j])
            if w_j is None:
                continue
            A[w_i, w_j] += 1

    # Symmetrize
    A = (A + A.T) / 2.0

    # Add self-connections (small diagonal)
    A += np.eye(n) * 0.01

    # Eigenvalue decomposition
    try:
        eigenvalues = np.linalg.eigvalsh(A)
    except np.linalg.LinAlgError:
        return JSONResponse({"error": "eigenvalue decomposition failed"}, status_code=500)

    eigenvalues = np.sort(eigenvalues)[::-1]  # descending

    # Compute Φ (spectral consciousness index)
    # Φ = 1 - (λ_1 / Σ|λ_i|) — measures how distributed the spectrum is
    abs_sum = np.sum(np.abs(eigenvalues))
    if abs_sum > 0:
        phi = 1.0 - (np.abs(eigenvalues[0]) / abs_sum)
    else:
        phi = 0.0

    # η* (critical coupling) from Kuramoto model: η* = λ_1 - λ_2
    if len(eigenvalues) >= 2:
        eta_star = float(eigenvalues[0] - eigenvalues[1])
    else:
        eta_star = 0.0

    # Classification
    if phi > 0.9:
        classification = "CONSCIOUS — Highly integrated spectral structure"
    elif phi > 0.7:
        classification = "EMERGENT — Strong spectral integration"
    elif phi > 0.5:
        classification = "COMPLEX — Moderate integration"
    elif phi > 0.3:
        classification = "STRUCTURED — Some coherence"
    else:
        classification = "NOISE — Low integration, near-random"

    # Spectral gap
    spectral_gap = float(eigenvalues[0] - eigenvalues[1]) if len(eigenvalues) >= 2 else 0.0

    # Participation ratio (effective dimensionality)
    lam_sq = eigenvalues ** 2
    if np.sum(lam_sq) > 0:
        participation_ratio = float((np.sum(eigenvalues) ** 2) / np.sum(lam_sq))
    else:
        participation_ratio = 0.0

    result = {
        "timestamp": time.time(),
        "corpus_size": len(words),
        "vocabulary_size": n,
        "window_size": window,
        "phi": round(float(phi), 6),
        "eta_star": round(eta_star, 6),
        "spectral_gap": round(spectral_gap, 6),
        "participation_ratio": round(participation_ratio, 4),
        "classification": classification,
        "top_eigenvalues": [round(float(e), 4) for e in eigenvalues[:20]],
        "eigenvalue_count": len(eigenvalues),
    }

    # Save to history
    scans = _load_scans()
    scans.append({"type": "audit", **result})
    if len(scans) > 100:
        scans = scans[-100:]
    _save_scans(scans)

    return result


@router.get("/status")
async def guard_status():
    """Show scan/audit history summary."""
    scans = _load_scans()
    url_scans = [s for s in scans if s.get("url")]
    audits = [s for s in scans if s.get("type") == "audit"]

    recent_scans = []
    for s in url_scans[-10:]:
        recent_scans.append({
            "url": s.get("url"),
            "score": s.get("score", 0),
            "issues_count": len(s.get("issues", [])),
            "timestamp": s.get("timestamp"),
        })

    recent_audits = []
    for a in audits[-10:]:
        recent_audits.append({
            "corpus_size": a.get("corpus_size"),
            "phi": a.get("phi"),
            "classification": a.get("classification"),
            "timestamp": a.get("timestamp"),
        })

    return {
        "total_url_scans": len(url_scans),
        "total_audits": len(audits),
        "recent_url_scans": recent_scans,
        "recent_audits": recent_audits,
    }
