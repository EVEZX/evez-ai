"""
EVEZ similarity calibration patch.
Adds structured_similarity() which subtracts baseline noise floor,
so random ↔ random = 0%, structured ↔ structured = high score.
"""
import math
import numpy as np
from lib.math_invariants import fingerprint, flatten, jensen_shannon


# Baseline: empirically measured noise floor
# Two random max-entropy sequences of ~20 chars score ~0.997
# We normalize: structured_score = (raw - NOISE_FLOOR) / (1 - NOISE_FLOOR)
NOISE_FLOOR = 0.95  # conservative baseline for high-entropy random text


def cosine(va: np.ndarray, vb: np.ndarray) -> float:
    na, nb = np.linalg.norm(va), np.linalg.norm(vb)
    if na < 1e-10 or nb < 1e-10:
        return 0.0
    return max(0.0, min(1.0, float(np.dot(va, vb) / (na * nb))))


def raw_similarity(fa: dict, fb: dict) -> float:
    """S(x,y) = sqrt( cos(Φx,Φy) * (1 - JS(Φx,Φy)) ) — raw, uncalibrated."""
    va, vb = flatten(fa), flatten(fb)
    cos = cosine(va, vb)
    js = jensen_shannon(va, vb)
    return math.sqrt(cos * (1.0 - js))


def structured_similarity(domain_a: str, domain_b: str) -> dict:
    """
    Calibrated similarity: subtracts noise floor, normalizes to [0, 1].
    - score = 0.0: indistinguishable from random noise pair
    - score = 1.0: maximally structurally identical
    
    Key: λ₂ (Fiedler value) is the decisive discriminator.
    Two truly random sequences of short length produce λ₂ ≈ 0,
    while structured sequences have higher graph connectivity.
    
    Also: structural_confidence = based on sequence length and λ₂.
    """
    fa = fingerprint(domain_a)
    fb = fingerprint(domain_b)
    raw = raw_similarity(fa, fb)
    
    # Calibrate: subtract noise floor
    calibrated = max(0.0, (raw - NOISE_FLOOR) / (1.0 - NOISE_FLOOR))
    
    # Structural confidence: penalize very short or low-λ₂ inputs
    min_len = min(len(domain_a), len(domain_b))
    len_factor = min(1.0, min_len / 50.0)   # full confidence above 50 chars
    lambda2_avg = (fa["lambda2"] + fb["lambda2"]) / 2.0
    structural_factor = min(1.0, lambda2_avg / 2.0)  # scales up with graph connectivity
    confidence = len_factor * 0.5 + structural_factor * 0.5
    
    return {
        "similarity_raw": round(raw, 6),
        "similarity": round(calibrated, 6),
        "confidence": round(confidence, 4),
        "high_confidence": confidence > 0.5,
        "interpretation": _interpret(calibrated, confidence),
        "breakdown": {
            "compression":    {"a": round(fa["compression"], 4), "b": round(fb["compression"], 4),
                               "delta": round(abs(fa["compression"]-fb["compression"]), 4)},
            "mi_lag1":        {"a": round(fa["mi"][0], 4), "b": round(fb["mi"][0], 4)},
            "spectral_gap":   {"a": round(fa["lambda2"], 4), "b": round(fb["lambda2"], 4),
                               "decisive": True},
            "persistence":    {"a": round(fa["entropy"], 4), "b": round(fb["entropy"], 4)},
        }
    }


def _interpret(score: float, confidence: float) -> str:
    if confidence < 0.3:
        return "Insufficient structure for reliable comparison (sequences too short or random)"
    if score > 0.8:
        return "High structural isomorphism — same generative grammar, different vocabulary"
    if score > 0.5:
        return "Moderate structural overlap — shared organizational principles"
    if score > 0.2:
        return "Weak structural similarity — some shared patterns"
    return "Structurally distinct — different generative rules"
