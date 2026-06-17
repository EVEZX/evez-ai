# tools/distribution_engine.py
# Max-entropy constrained scenario selector + bias audit generator.

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Tuple, Any
import math
import random

def _tv(p: Dict[str,float], q: Dict[str,float]) -> float:
    keys = set(p) | set(q)
    return 0.5 * sum(abs(p.get(k,0.0) - q.get(k,0.0)) for k in keys)

def _kl(p: Dict[str,float], q: Dict[str,float], eps: float = 1e-12) -> float:
    s = 0.0
    for k, pv in p.items():
        if pv <= 0:
            continue
        qv = q.get(k, eps)
        s += pv * math.log((pv + eps) / (qv + eps))
    return max(0.0, s)

def empirical_distribution(zs: List[Dict[str,Any]], axis: str) -> Dict[str,float]:
    counts: Dict[str,int] = {}
    for z in zs:
        v = z.get(axis)
        if v is None:
            continue
        counts[v] = counts.get(v, 0) + 1
    n = sum(counts.values()) or 1
    return {k: v/n for k, v in counts.items()}

def per_axis_deviation(emp: Dict[str,float], tgt: Dict[str,float]) -> float:
    keys = set(emp) | set(tgt)
    return max(abs(emp.get(k,0.0) - tgt.get(k,0.0)) for k in keys) if keys else 0.0

@dataclass
class Constitution:
    target: Dict[str,Dict[str,float]]
    drift_bounds: Dict[str,Any]
    selector: Dict[str,Any]

def candidate_penalty(current_emp: Dict[str,Dict[str,float]], target: Dict[str,Dict[str,float]], cand: Dict[str,Any]) -> float:
    penalty = 0.0
    for axis, tgt in target.items():
        v = cand.get(axis)
        if v is None:
            continue
        emp = current_emp.get(axis, {})
        emp2 = dict(emp)
        emp2[v] = emp2.get(v, 0.0) + 1e-3
        dev_now = per_axis_deviation(emp, tgt)
        dev_next = per_axis_deviation(emp2, tgt)
        penalty += max(0.0, dev_next - dev_now)
    return penalty

def select_scenario(constitution: Constitution, recent_z: List[Dict[str,Any]], candidates: List[Dict[str,Any]], rng: random.Random | None = None) -> Dict[str,Any]:
    rng = rng or random.Random()
    target = constitution.target
    lam = float(constitution.selector.get("lambda", 6.0))
    current_emp = {axis: empirical_distribution(recent_z, axis) for axis in target.keys()}

    scored: List[Tuple[float, Dict[str,Any]]] = []
    for cand in candidates:
        pen = candidate_penalty(current_emp, target, cand)
        w = math.exp(-lam * pen)
        scored.append((w, cand))

    total = sum(w for w,_ in scored) or 1.0
    r = rng.random() * total
    acc = 0.0
    for w, cand in scored:
        acc += w
        if acc >= r:
            return cand
    return scored[-1][1]

def make_bias_audit(constitution: Constitution, recent_z: List[Dict[str,Any]], from_round: str, to_round: str) -> Dict[str,Any]:
    target = constitution.target
    emp = {axis: empirical_distribution(recent_z, axis) for axis in target.keys()}
    kl = 0.0
    tv = 0.0
    per_axis = {}
    violations = []
    eps_kl = float(constitution.drift_bounds.get("epsilon_kl", 0.035))
    eps_tv = float(constitution.drift_bounds.get("epsilon_tv", 0.06))
    eps_axis = float(constitution.drift_bounds.get("per_axis_max_deviation", 0.08))

    for axis, tgt in target.items():
        e = emp.get(axis, {})
        per_axis[axis] = {
            "max_dev": per_axis_deviation(e, tgt),
            "kl": _kl(e, tgt),
            "tv": _tv(e, tgt)
        }
        kl += per_axis[axis]["kl"]
        tv += per_axis[axis]["tv"]
        if per_axis[axis]["max_dev"] > eps_axis:
            violations.append(f"axis_dev:{axis}:{per_axis[axis]['max_dev']:.3f}")

    if kl > eps_kl:
        violations.append(f"kl:{kl:.3f}")
    if tv > eps_tv:
        violations.append(f"tv:{tv:.3f}")

    recs = []
    if violations:
        for axis, tgt in target.items():
            e = emp.get(axis, {})
            best_k = None
            best_gap = 0.0
            for k, tvv in tgt.items():
                gap = tvv - e.get(k, 0.0)
                if gap > best_gap:
                    best_gap = gap
                    best_k = k
            if best_k and best_gap > 0.03:
                recs.append(f"repair:oversample {axis}={best_k} for next window")

    return {
        "audit_id": f"BA-{from_round}-{to_round}",
        "window": {"rounds": len(recent_z), "from_round": from_round, "to_round": to_round},
        "empirical": emp,
        "target": target,
        "divergence": {"kl": kl, "tv": tv, "per_axis": per_axis},
        "violations": violations,
        "recommendations": recs
    }
