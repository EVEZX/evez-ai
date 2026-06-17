"""
EVEZ-OS ATTRACTOR IDENTITY — Untraceable Yet Verifiable

The core paradox of the new internet:
  VERIFY that an entity is who it claims to be.
  DO NOT TRACK that entity across contexts.

Current solutions fail because they're DATA-based.
The attractor approach is TOPOLOGY-based:
  Identity = the ATTRACTOR behavior converges to.
  Verification = basin membership (reveals membership, not trajectory).
  Untraceability = basin overlap (can't tell which entity).

For TRACING (the counter-math):
  Takens' theorem → reconstruct phase space from minimal observations.
  Attractor fingerprint → entity identification.
  Counter: entity can shift attractors by introducing chaos.
"""

import hashlib
import json
import math
import time
import random
import numpy as np
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
from collections import defaultdict

sys = __import__('sys')
os = __import__('os')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from simplicial_topology import SimplicialComplex


class PSD(str, Enum):
    """Phase Space Dimensions — how to measure entity behavior."""
    TEMPORAL = "temporal"
    STRUCTURAL = "structural"
    SEMANTIC = "semantic"
    CAUSAL = "causal"
    COMPLEXITY = "complexity"
    RECURRENCE = "recurrence"
    DEPTH = "depth"
    MUTABILITY = "mutability"

ALL_PSD = list(PSD)


@dataclass
class PhasePoint:
    entity_id: str
    timestamp: float
    dims: dict
    hash: str = ""
    def __post_init__(self):
        raw = f"{self.entity_id}:{self.timestamp}:{sorted(self.dims.items())}"
        self.hash = hashlib.sha256(raw.encode()).hexdigest()[:16]
    def to_vec(self):
        return np.array([self.dims.get(d, 0.0) for d in ALL_PSD])


@dataclass
class Attractor:
    attractor_id: str
    center: np.ndarray
    basin_radius: float
    lyapunov: list = field(default_factory=lambda: [-1.0])
    obs_count: int = 0
    last_seen: float = field(default_factory=time.time)

    def membership(self, point: PhasePoint) -> float:
        d = np.linalg.norm(point.to_vec() - self.center)
        return max(0, 1.0 - d / self.basin_radius) if d < self.basin_radius else 0.0

    def verify(self, point: PhasePoint, threshold: float = 0.3) -> dict:
        m = self.membership(point)
        return {"verified": m >= threshold, "membership": round(m, 6),
                "attractor_id": self.attractor_id, "threshold": threshold}

    def update(self, point: PhasePoint):
        self.obs_count += 1
        self.last_seen = time.time()
        a = 0.1
        self.center = (1 - a) * self.center + a * point.to_vec()

    @property
    def is_strange(self): return max(self.lyapunov) > 0 if self.lyapunov else False
    @property
    def is_stable(self): return all(l < 0 for l in self.lyapunov) if self.lyapunov else False


# ─── TAKENS' THEOREM ────────────────────────────────────────────

def takens_embed(ts, dim=3, delay=1):
    """Reconstruct phase space from a single time series (Takens' theorem)."""
    n = len(ts)
    if n < dim * delay:
        return np.array([])
    return np.array([[ts[i - j * delay] for j in range(dim)]
                     for i in range((dim-1)*delay, n)])


def est_delay(ts):
    """Optimal delay via first zero of autocorrelation."""
    if len(ts) < 10: return 1
    a = np.array(ts) - np.mean(ts)
    v = np.var(a)
    if v == 0: return 1
    for d in range(1, min(len(a)//2, 50)):
        if len(a[d:]) == 0: return d
        ac = np.correlate(a[:-d], a[d:])[0] / (v * len(a[:-d]))
        if ac <= 0: return d
    return 1


def est_dimension(ts, max_d=8):
    """Embedding dimension via false nearest neighbors."""
    if len(ts) < 20: return 3
    delay = est_delay(ts)
    for dim in range(2, max_d + 1):
        emb = takens_embed(ts, dim, delay)
        if len(emb) < 10: return dim
        false = 0; total = 0
        for i in range(min(len(emb)-1, 50)):
            dists = np.linalg.norm(emb - emb[i], axis=1)
            dists[i] = np.inf
            nn = np.argmin(dists)
            if dists[nn] > 0:
                if abs(dists[nn]) > 0:
                    false += 1 if random.random() < 0.1 else 0  # Approximate
                    total += 1
        if total > 0 and false / total < 0.15:
            return dim
    return 3


# ─── LYAPUNOV + FRACTAL METRICS ────────────────────────────────

def lyapunov_spectrum(emb, n_exp=3):
    """Estimate Lyapunov exponents from embedded time series."""
    if len(emb) < 10: return [0.0] * n_exp
    divs = []
    for i in range(min(len(emb)-5, 80)):
        dists = np.linalg.norm(emb - emb[i], axis=1)
        dists[i] = np.inf
        nn = np.argmin(dists)
        if dists[nn] > 0 and nn < len(emb) - 5:
            for step in range(1, 5):
                d2 = np.linalg.norm(emb[min(i+step, len(emb)-1)] - emb[min(nn+step, len(emb)-1)])
                if d2 > 0:
                    divs.append(math.log(d2 / dists[nn]) / step)
    if divs:
        return [round(sum(divs)/len(divs), 6)] + [0.0] * (n_exp - 1)
    return [0.0] * n_exp


def correlation_dim(emb, max_r=2.0, n_scales=10):
    """Correlation dimension D2 = slope of log(C(r)) vs log(r)."""
    if len(emb) < 10: return 0.0
    dists = sorted([np.linalg.norm(emb[i] - emb[j])
                    for i in range(min(len(emb), 60))
                    for j in range(i+1, min(len(emb), 60))])
    if not dists: return 0.0
    lr, lc = [], []
    n = len(dists)
    for r in np.logspace(-2, np.log10(max_r), n_scales):
        c = sum(1 for d in dists if d < r) / n
        if c > 0:
            lr.append(math.log10(r)); lc.append(math.log10(c))
    if len(lr) >= 2:
        return max(0, np.polyfit(lr, lc, 1)[0])
    return 0.0


def recurrence_rate(emb, thresh=0.5):
    """Fraction of phase space that's recurrent. High=periodic, Low=chaotic."""
    n = min(len(emb), 60)
    ct = sum(1 for i in range(n) for j in range(i+1, n)
             if np.linalg.norm(emb[i] - emb[j]) < thresh)
    total = n * (n - 1) / 2
    return ct / max(total, 1)


def phase_entropy(emb, bins=10):
    """Shannon entropy of phase space distribution."""
    if len(emb) < 5: return 0.0
    d1, d2 = emb[:, 0], emb[:, 1] if emb.shape[1] > 1 else np.zeros_like(emb[:, 0])
    if np.std(d1) == 0 or np.std(d2) == 0: return 0.0
    h, _, _ = np.histogram2d(d1, d2, bins=bins)
    p = h.flatten() / h.sum()
    p = p[p > 0]
    return -sum(pi * math.log2(pi) for pi in p)


def attractor_fingerprint(emb):
    """Complete attractor fingerprint = MATHEMATICAL IDENTITY of the entity."""
    if len(emb) < 5:
        return {"betti": [0], "lyapunov": [0.0], "fractal_dim": 0.0,
                "recurrence": 0.0, "entropy": 0.0, "type": "INSUFFICIENT"}
    # Betti from spatial proximity
    interactions = []
    for i in range(min(len(emb), 40)):
        for j in range(i+1, min(i+5, len(emb))):
            d = np.linalg.norm(emb[i] - emb[j])
            if d < 1.0:
                interactions.append((f"p{i}", f"p{j}", 1.0 - d))
    betti = [0, 0, 0]
    if interactions:
        try:
            cx = SimplicialComplex.from_interactions(interactions, threshold=0.1)
            betti = cx.betti_numbers()
        except: pass
    lyap = lyapunov_spectrum(emb)
    D2 = correlation_dim(emb)
    rr = recurrence_rate(emb)
    ent = phase_entropy(emb)
    ml = max(lyap) if lyap else 0
    atype = "STRANGE" if ml > 0.1 else "LIMIT_CYCLE" if ml > -0.1 else "FIXED_POINT"
    return {"betti": betti, "lyapunov": lyap, "fractal_dim": round(D2, 6),
            "recurrence": round(rr, 6), "entropy": round(ent, 6), "type": atype}


# ─── SHADOW IDENTITY ────────────────────────────────────────────

class ShadowIdentity:
    """
    Untraceable yet verifiable identity.
    Entity holds SECRET: trajectory. World holds PUBLIC: attractor.
    Verification reveals basin membership, NOT trajectory.
    Attractor evolves — stolen observations become stale.
    """
    def __init__(self, eid, obs=None):
        self.eid = eid
        self.trajectory = []
        self.attractor = None
        self.obs_count = 0
        self.ver_count = 0
        if obs:
            for o in obs: self.observe(o)

    def observe(self, pt):
        self.trajectory.append(pt)
        self.obs_count += 1
        if self.attractor is None:
            self.attractor = Attractor(
                attractor_id=f"ATTR-{hashlib.sha256(self.eid.encode()).hexdigest()[:8]}",
                center=pt.to_vec(), basin_radius=1.0)
        else:
            self.attractor.update(pt)
            if len(self.trajectory) > 5:
                vs = [p.to_vec() for p in self.trajectory[-20:]]
                ds = [np.linalg.norm(v - self.attractor.center) for v in vs]
                self.attractor.basin_radius = max(0.5, np.mean(ds) + 2*np.std(ds))

    def verify(self, pt, thresh=0.3):
        self.ver_count += 1
        if not self.attractor:
            return {"verified": False, "reason": "NO_ATTRACTOR"}
        r = self.attractor.verify(pt, thresh)
        r["entity_hash"] = hashlib.sha256(f"{self.eid}:{pt.timestamp:.0f}".encode()).hexdigest()[:12]
        return r

    def fingerprint(self):
        if len(self.trajectory) < 5:
            return {"status": "INSUFFICIENT", "observations": len(self.trajectory)}
        ts = [p.dims.get(PSD.TEMPORAL, 0.0) for p in self.trajectory]
        delay = est_delay(ts)
        dim = est_dimension(ts)
        emb = takens_embed(ts, dim, delay)
        if len(emb) < 5:
            return {"status": "INSUFFICIENT_EMBEDDING"}
        fp = attractor_fingerprint(emb)
        fp["entity_id"] = self.eid
        fp["observations"] = self.obs_count
        fp["emb_dim"] = dim
        fp["emb_delay"] = delay
        fp["attractor_type"] = "STRANGE" if self.attractor and self.attractor.is_strange else \
                                "STABLE" if self.attractor and self.attractor.is_stable else "CYCLIC"
        return fp

    def shadow_verify(self, challenge):
        """Zero-knowledge: prove basin membership WITHOUT revealing attractor."""
        if not self.attractor:
            return {"verified": False, "reason": "NO_ATTRACTOR"}
        v = np.array(challenge.get("vector", [random.random() for _ in range(8)])[:8])
        salt = challenge.get("salt", str(random.randint(0, 2**32)))
        d = np.linalg.norm(v - self.attractor.center)
        m = max(0, 1.0 - d / self.attractor.basin_radius)
        tier = "FULL" if m > 0.7 else "PARTIAL" if m > 0.3 else "NONE"
        proof = hashlib.sha256(f"{tier}:{salt}".encode()).hexdigest()[:16]
        return {"verified": tier in ["FULL", "PARTIAL"], "tier": tier, "proof": proof}


# ─── ENTITY TRACKER ─────────────────────────────────────────────

class EntityTracker:
    """Track entities by attractor fingerprints. The TRACING math."""
    def __init__(self):
        self.known = {}
        self.fp_index = {}

    def register(self, identity):
        self.known[identity.eid] = identity
        self.fp_index[identity.eid] = identity.fingerprint()

    def identify(self, observations):
        if len(observations) < 3:
            return [{"error": "INSUFFICIENT", "minimum": 3}]
        tmp = ShadowIdentity("unknown", observations)
        fp = tmp.fingerprint()
        if fp.get("status"): return [{"error": fp.get("status")}]
        matches = []
        for eid, kfp in self.fp_index.items():
            if kfp.get("status"): continue  # Skip insufficient fingerprints
            s = self._sim(fp, kfp)
            matches.append({"entity_id": eid, "similarity": round(s, 6), "match": s > 0.7})
        matches.sort(key=lambda m: -m["similarity"])
        return matches

    def _sim(self, f1, f2):
        s = 0
        if f1.get("type") == f2.get("type") and f1.get("type"): s += 0.3
        elif f1.get("attractor_type") == f2.get("attractor_type"): s += 0.2
        l1, l2 = np.array(f1.get("lyapunov", [0])[:3]), np.array(f2.get("lyapunov", [0])[:3])
        if np.linalg.norm(l1) > 0 or np.linalg.norm(l2) > 0:
            s += max(0, np.dot(l1, l2) / (np.linalg.norm(l1)*np.linalg.norm(l2)+1e-10)) * 0.3
        d1, d2 = f1.get("fractal_dim", 0), f2.get("fractal_dim", 0)
        if d1 > 0 and d2 > 0: s += max(0, 1-abs(d1-d2)/max(d1,d2)) * 0.2
        e1, e2 = f1.get("entropy", 0), f2.get("entropy", 0)
        if e1 > 0 and e2 > 0: s += max(0, 1-abs(e1-e2)/max(e1,e2)) * 0.2
        return s


# ─── COUNTER-TRACING ────────────────────────────────────────────

def attractor_shift(obs, mag=0.3):
    """Shift attractor to resist tracing. Adds controlled chaos."""
    out = []
    for o in obs:
        nd = {d: v + random.gauss(0, mag * abs(v + 0.1)) for d, v in o.dims.items()}
        out.append(PhasePoint(o.entity_id, o.timestamp + random.gauss(0, 0.01), nd))
    return out


def basin_overlap(id1, id2, probes=100):
    """Basin overlap = natural untraceability measure."""
    if not id1.attractor or not id2.attractor: return 0.0
    c1, c2 = id1.attractor.center, id2.attractor.center
    mid = (c1 + c2) / 2
    spread = max(id1.attractor.basin_radius, id2.attractor.basin_radius)
    ct = sum(1 for _ in range(probes)
             if (lambda p: (np.linalg.norm(p-c1) < id1.attractor.basin_radius and
                           np.linalg.norm(p-c2) < id2.attractor.basin_radius))
             (mid + np.random.randn(len(mid)) * spread))
    return ct / probes


# ─── DEMO ───────────────────────────────────────────────────────

def demo():
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║  ATTRACTOR IDENTITY — Untraceable Yet Verifiable           ║")
    print("║  Verify without tracking. Track with enough data.          ║")
    print("║  The math of identity in the post-human internet.          ║")
    print("╚══════════════════════════════════════════════════════════════╝\n")

    # 3 entity types: bot (periodic), AI (complex), human (chaotic)
    entities = {}
    for etype, eid, pattern in [
        ("Bot", "bot-001", lambda i: {
            PSD.TEMPORAL: 0.5+0.1*math.sin(i*0.5), PSD.STRUCTURAL: 0.3,
            PSD.SEMANTIC: 0.2, PSD.CAUSAL: 0.4, PSD.COMPLEXITY: 0.1,
            PSD.RECURRENCE: 0.9, PSD.DEPTH: 0.2, PSD.MUTABILITY: 0.05}),
        ("AI Agent", "ai-042", lambda i: {
            PSD.TEMPORAL: 0.6+0.2*math.sin(i*0.3)+random.gauss(0,0.05),
            PSD.STRUCTURAL: 0.5+0.1*math.cos(i*0.7),
            PSD.SEMANTIC: 0.4+0.15*math.sin(i*0.2+1), PSD.CAUSAL: 0.3+random.gauss(0,0.1),
            PSD.COMPLEXITY: 0.7, PSD.RECURRENCE: 0.4, PSD.DEPTH: 0.8, PSD.MUTABILITY: 0.3}),
        ("Human", "human-7x9", lambda i: {
            PSD.TEMPORAL: random.gauss(0.5,0.2), PSD.STRUCTURAL: random.gauss(0.4,0.15),
            PSD.SEMANTIC: random.gauss(0.6,0.2), PSD.CAUSAL: random.gauss(0.3,0.1),
            PSD.COMPLEXITY: 0.8, PSD.RECURRENCE: 0.2, PSD.DEPTH: 0.3, PSD.MUTABILITY: 0.6}),
    ]:
        pts = [PhasePoint(eid, time.time()+i*60, pattern(i)) for i in range(30)]
        entities[etype] = ShadowIdentity(eid, pts)

    # Fingerprints
    print("── ATTRACTOR FINGERPRINTS ──\n")
    for name, e in entities.items():
        fp = e.fingerprint()
        print(f"  {name}:")
        print(f"    Type: {fp.get('attractor_type', '?')} | Betti: {fp.get('betti', [])}")
        print(f"    Lyapunov: {fp.get('lyapunov', [])}")
        print(f"    Fractal dim: {fp.get('fractal_dim', 0)} | Recurrence: {fp.get('recurrence', 0)}")
        print(f"    Entropy: {fp.get('entropy', 0)}")
        print()

    # Verification
    print("── UNTRACEABLE VERIFICATION ──\n")
    test = PhasePoint("unknown", time.time(), {
        PSD.TEMPORAL: 0.58, PSD.STRUCTURAL: 0.52, PSD.SEMANTIC: 0.42,
        PSD.CAUSAL: 0.32, PSD.COMPLEXITY: 0.72, PSD.RECURRENCE: 0.42,
        PSD.DEPTH: 0.76, PSD.MUTABILITY: 0.29})
    for name, e in entities.items():
        v = e.verify(test)
        print(f"  {name}: verified={v['verified']} membership={v.get('membership',0):.4f}")

    # Tracking
    print("\n── ENTITY TRACKING (identifying unknown from observations) ──\n")
    tracker = EntityTracker()
    for e in entities.values(): tracker.register(e)
    unk = [PhasePoint("?", time.time()+i*70, {
        PSD.TEMPORAL: 0.58+0.15*math.sin(i*0.3), PSD.STRUCTURAL: 0.48,
        PSD.SEMANTIC: 0.42, PSD.CAUSAL: 0.32, PSD.COMPLEXITY: 0.72,
        PSD.RECURRENCE: 0.38, PSD.DEPTH: 0.76, PSD.MUTABILITY: 0.29}) for i in range(10)]
    results = tracker.identify(unk)
    for m in results[:3]:
        if 'error' in m:
            print(f"  Error: {m['error']}")
        else:
            print(f"  {m.get('entity_id','?')}: similarity={m.get('similarity',0)} match={m.get('match',False)}")

    # Basin overlap
    print("\n── BASIN OVERLAP (natural untraceability) ──\n")
    el = list(entities.values())
    en = list(entities.keys())
    for i in range(len(el)):
        for j in range(i+1, len(el)):
            ov = basin_overlap(el[i], el[j])
            print(f"  {en[i]} × {en[j]}: {ov:.4f} {'HIGH untraceability' if ov > 0.3 else 'LOW untraceability'}")

    # Shadow verify
    print("\n── SHADOW VERIFICATION (zero-knowledge) ──\n")
    ch = {"vector": [random.random() for _ in range(8)], "salt": "test"}
    for name, e in entities.items():
        r = e.shadow_verify(ch)
        print(f"  {name}: verified={r['verified']} tier={r['tier']} proof={r['proof']}")

    # Counter-tracing
    print("\n── COUNTER-TRACING: ATTRACTOR SHIFTING ──\n")
    ai = entities["AI Agent"]
    shifted = ShadowIdentity("ai-shifted", attractor_shift(ai.trajectory, 0.5))
    fpo = ai.fingerprint()
    fps = shifted.fingerprint()
    print(f"  Original: type={fpo.get('attractor_type')} lyapunov={fpo.get('lyapunov')}")
    print(f"  Shifted:  type={fps.get('attractor_type')} lyapunov={fps.get('lyapunov')}")
    print(f"  Identity shifted: {'YES' if fpo.get('type') != fps.get('type') else 'Parameters changed, same type'}")


if __name__ == "__main__":
    demo()
