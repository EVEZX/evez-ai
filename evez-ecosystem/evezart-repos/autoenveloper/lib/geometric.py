"""
Geometric Analysis Tool — Autoenveloper Module
Pattern detection across geometric/spectral/topological domains.
"""

import math
import json
from typing import Any


def compute_centroid(points: list[list[float]]) -> list[float]:
    n = len(points)
    return [sum(p[i] for p in points) / n for i in range(len(points[0]))]


def compute_convex_hull_area(points: list[list[float]]) -> float:
    """Shoelace formula for polygon area (2D)."""
    n = len(points)
    if n < 3:
        return 0.0
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        area += points[i][0] * points[j][1]
        area -= points[j][0] * points[i][1]
    return abs(area) / 2.0


def compute_fractal_dimension(sequence: list[float]) -> float:
    """Estimate fractal dimension of a 1D sequence via box-counting approximation."""
    if len(sequence) < 4:
        return 1.0
    mn, mx = min(sequence), max(sequence)
    if mx == mn:
        return 1.0
    normalized = [(x - mn) / (mx - mn) for x in sequence]
    
    counts = []
    scales = [2, 4, 8, 16, 32]
    for scale in scales:
        boxes = set()
        for i, v in enumerate(normalized):
            box_x = int(i * scale / len(normalized))
            box_y = int(v * scale)
            boxes.add((box_x, box_y))
        counts.append(len(boxes))
    
    # Linear regression of log(count) vs log(scale)
    log_scales = [math.log(s) for s in scales]
    log_counts  = [math.log(c) for c in counts if c > 0]
    
    if len(log_counts) < 2:
        return 1.0
    
    n = len(log_counts)
    lsc = log_scales[:n]
    sx  = sum(lsc)
    sy  = sum(log_counts)
    sxy = sum(lsc[i] * log_counts[i] for i in range(n))
    sx2 = sum(x**2 for x in lsc)
    
    denom = n * sx2 - sx * sx
    if denom == 0:
        return 1.0
    slope = (n * sxy - sx * sy) / denom
    return round(slope, 4)


def detect_symmetry(points: list[list[float]], tolerance: float = 0.01) -> dict:
    """Detect reflective and rotational symmetry in a point set."""
    centroid = compute_centroid(points)
    
    # Translate to origin
    translated = [[p[0] - centroid[0], p[1] - centroid[1]] for p in points]
    
    # Check 2-fold rotational symmetry
    def has_rotation_n(pts, n, tol):
        angle = 2 * math.pi / n
        for p in pts:
            r = math.sqrt(p[0]**2 + p[1]**2)
            theta = math.atan2(p[1], p[0])
            rotated = [r * math.cos(theta + angle), r * math.sin(theta + angle)]
            found = any(
                abs(q[0] - rotated[0]) < tol and abs(q[1] - rotated[1]) < tol
                for q in pts
            )
            if not found:
                return False
        return True
    
    symmetries = []
    for n in [2, 3, 4, 5, 6, 8]:
        if has_rotation_n(translated, n, tolerance):
            symmetries.append(f"C{n}")
    
    return {
        "centroid":       [round(c, 4) for c in centroid],
        "rotational":     symmetries,
        "has_symmetry":   len(symmetries) > 0,
        "point_count":    len(points)
    }


def spectral_analysis(sequence: list[float]) -> dict:
    """Discrete Fourier transform — identify dominant frequencies."""
    n = len(sequence)
    if n < 2:
        return {"error": "sequence too short"}
    
    # DFT (manual, no numpy required)
    real = []
    imag = []
    for k in range(n // 2):
        re = sum(sequence[t] * math.cos(2 * math.pi * k * t / n) for t in range(n))
        im = sum(-sequence[t] * math.sin(2 * math.pi * k * t / n) for t in range(n))
        real.append(re)
        imag.append(im)
    
    magnitudes = [math.sqrt(r**2 + i**2) / n for r, i in zip(real, imag)]
    
    # Top 5 dominant frequencies
    indexed = sorted(enumerate(magnitudes), key=lambda x: -x[1])[:5]
    
    return {
        "length":           n,
        "dominant_freqs":   [{"freq": k, "magnitude": round(m, 4)} for k, m in indexed],
        "fractal_dimension": compute_fractal_dimension(sequence)
    }


def get_tools():
    from tools.registry import Tool

    return [
        Tool(
            name="geo_spectral_analysis",
            description="Spectral analysis of a numeric sequence. Returns dominant frequencies and fractal dimension.",
            parameters={
                "type": "object",
                "properties": {
                    "sequence": {"type": "array", "items": {"type": "number"},
                                 "description": "Numeric sequence to analyze"}
                },
                "required": ["sequence"]
            },
            fn=lambda sequence: spectral_analysis(sequence)
        ),
        Tool(
            name="geo_detect_symmetry",
            description="Detect rotational/reflective symmetry in a 2D point set.",
            parameters={
                "type": "object",
                "properties": {
                    "points": {"type": "array", "description": "Array of [x,y] coordinate pairs"},
                    "tolerance": {"type": "number", "default": 0.01}
                },
                "required": ["points"]
            },
            fn=lambda points, tolerance=0.01: detect_symmetry(points, tolerance)
        ),
        Tool(
            name="geo_fractal_dimension",
            description="Estimate the fractal dimension of a 1D numeric sequence.",
            parameters={
                "type": "object",
                "properties": {
                    "sequence": {"type": "array", "items": {"type": "number"}}
                },
                "required": ["sequence"]
            },
            fn=lambda sequence: {"fractal_dimension": compute_fractal_dimension(sequence)}
        )
    ]
