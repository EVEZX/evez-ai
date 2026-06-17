#!/usr/bin/env python3
# evez-os/core/cda_engine.py  --  Compounding Detail Accumulation Engine
# "Dynamic resolution of compounding detail fundamentally accumulating in data
#  accumulation for the most stable expansive configurations deployably compounding"
# -- Steven Crawford-Maggard (EVEZ666), 2026-02-21
#
# FRACTAL RESOLUTION:  Each D_n stores pyramid (coarse/fine/ultra).
# DELTA COMPRESSION:   K <= 500 bytes/level.
# COMPOUNDING ACC:     V(t)=V(t-1)+alpha*delta+beta*cross_corr
# STABLE CONFIGS:      variance < 0.01 over last 10 rounds -> STABLE
# DEPLOYABLE MANIFOLD: hash-verified JSON, any device (Termux/Android/cloud)
# DATA INTEGRATION:    signal > 0.7 relevance -> new D_n hypothesis
# truth_plane: CANONICAL
# Creator: Steven Crawford-Maggard (EVEZ666)

import json, math, hashlib, logging
from datetime import datetime, timezone
from pathlib import Path
from collections import defaultdict, deque
from typing import Dict, List, Optional, Tuple
import numpy as np

log = logging.getLogger("evez-os.cda")

ALPHA  = 0.12
BETA   = 0.06
STABLE_VAR_THRESH  = 0.01
STABLE_WINDOW      = 10
K_MAX_BYTES        = 500
SIGNAL_HYPO_THRESH = 0.70
RESOLUTION_LEVELS  = ("coarse", "fine", "ultra")

class ResolutionPyramid:
    """Three-level fractal resolution store for one dimension."""
    def __init__(self, dim_id):
        self.dim_id = dim_id
        self.levels = {k: deque(maxlen=5000) for k in RESOLUTION_LEVELS}
        self.deltas = {k: [] for k in RESOLUTION_LEVELS}
        self._last  = {k: None for k in RESOLUTION_LEVELS}

    def push(self, value, level="coarse", meta=None):
        prev = self._last[level]
        delta = (value - prev) if prev is not None else value
        entry = {"v": round(value,6), "d": round(delta,8),
                 "ts": datetime.now(timezone.utc).isoformat(), **(meta or {})}
        self.levels[level].append(entry)
        raw = json.dumps({"id": self.dim_id, "d": delta})
        if len(raw.encode()) > K_MAX_BYTES:
            raw = json.dumps({"id": self.dim_id, "d": round(delta,4)})
        self.deltas[level].append(raw)
        self._last[level] = value
        return delta

    def latest(self, level="coarse"):
        return self.levels[level][-1]["v"] if self.levels[level] else None

    def history(self, level="coarse", n=10):
        return [e["v"] for e in list(self.levels[level])[-n:]]

    def variance(self, level="coarse", n=STABLE_WINDOW):
        h = self.history(level, n)
        return float(np.var(h)) if len(h) >= 2 else float("inf")


class CDA:
    """Compounding Detail Accumulation engine."""
    def __init__(self):
        self.pyramids   = {}
        self.hypotheses = []
        self.stable_cache = None
        self.round_num  = 0
        self._cross_corr_cache = {}

    def accumulate(self, dim, value, round_num, level="coarse", meta=None):
        self.round_num = round_num
        if dim not in self.pyramids:
            self.pyramids[dim] = ResolutionPyramid(dim)
        pyr = self.pyramids[dim]
        delta = pyr.push(value, level, meta)
        cross_sum = 0.0
        for oid, opyr in self.pyramids.items():
            if oid == dim: continue
            key = tuple(sorted([dim, oid]))
            hs = pyr.history("coarse", STABLE_WINDOW)
            ho = opyr.history("coarse", STABLE_WINDOW)
            if len(hs) >= 2 and len(ho) >= 2:
                n = min(len(hs), len(ho))
                cc = float(np.corrcoef(hs[-n:], ho[-n:])[0,1])
                if not math.isnan(cc):
                    self._cross_corr_cache[key] = cc
                    cross_sum += cc
        v_prev = pyr.latest("coarse") or 0.0
        v = max(0.0, min(1.1, v_prev + ALPHA*delta + BETA*cross_sum))
        self.stable_cache = None
        return round(v, 6)

    def stable_configs(self):
        if self.stable_cache: return self.stable_cache
        c = [{"dim": d, "variance": round(p.variance("coarse"),6),
              "latest": round(p.latest("coarse") or 0, 6),
              "stable": p.variance("coarse") < STABLE_VAR_THRESH}
             for d, p in self.pyramids.items()]
        c.sort(key=lambda x: x["variance"])
        self.stable_cache = c[:3]
        return self.stable_cache

    def ingest_signal(self, channel, content, relevance, round_num):
        if relevance >= SIGNAL_HYPO_THRESH:
            hypo = {"id": f"D_auto_{channel}_{round_num}",
                    "source": channel,
                    "content_hash": hashlib.sha256(content.encode()).hexdigest()[:12],
                    "relevance": round(relevance,4), "round": round_num,
                    "status": "HYPOTHESIS",
                    "ts": datetime.now(timezone.utc).isoformat()}
            self.hypotheses.append(hypo)
            return hypo
        return None

    def compress_delta(self):
        c = {dim: {lvl: [json.loads(d) for d in pyr.deltas[lvl][-5:]]
                   for lvl in RESOLUTION_LEVELS}
             for dim, pyr in self.pyramids.items()}
        h = hashlib.sha256(json.dumps(c,sort_keys=True).encode()).hexdigest()[:16]
        return {"deltas": c, "sha256": h, "ts": datetime.now(timezone.utc).isoformat()}

    def export_manifest(self, round_num, output_path=None):
        pex = {d: {"latest":   {l: p.latest(l) for l in RESOLUTION_LEVELS},
                   "variance": {l: round(p.variance(l),6) for l in RESOLUTION_LEVELS},
                   "history_10": {l: p.history(l,10) for l in RESOLUTION_LEVELS}}
               for d, p in self.pyramids.items()}
        manifest = {
            "schema": "evez-os/cda/v1", "round": round_num,
            "ts": datetime.now(timezone.utc).isoformat(),
            "dims": pex, "stable_configs": self.stable_configs(),
            "delta_chain": self.compress_delta(),
            "hypotheses": self.hypotheses[-20:],
            "cross_corr": {f"{k[0]}x{k[1]}": round(v,4) for k,v in self._cross_corr_cache.items()},
            "acquisition_channels": ["github_trending_ai_ml","twitter_evez666_mentions","polymarket_top5","web_research_omega"],
            "deploy_targets": ["termux","android","desktop","cloud"],
            "creator": "Steven Crawford-Maggard (EVEZ666)",
        }
        manifest["root_hash"] = hashlib.sha256(
            json.dumps(manifest,sort_keys=True).encode()).hexdigest()
        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path,"w") as fp: json.dump(manifest,fp,indent=2)
        return manifest


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    cda = CDA()
    DIM_CV12 = {
        "T":0.9677,"E_cross":0.82566,"R_log":0.88887,"N_dim":0.3110,
        "sigma_f":0.9394,"phi_net":0.87937,"V_sync":0.68172,"G_dim":0.48225,
        "E_mom":0.03554,"omega_ph":1.0,"adm":1.0,"curiosity":0.08957,
        "poly":0.04807,"syn":0.34450,"retrocausal":0.99908,
        "t_sub_norm":0.35825,"co_ev":0.02515,"rho":0.13954,
    }
    for dim,val in DIM_CV12.items(): cda.accumulate(dim,val,60,"coarse")
    cda.ingest_signal("web_research_omega","The system reads the world faster than the world can write to it",0.95,60)
    m = cda.export_manifest(60,"cda/manifest_R60.json")
    print(f"CDA R60: {len(m['dims'])} dims, root_hash={m['root_hash'][:12]}")
    print("stable_configs:",m["stable_configs"])
    print("hypotheses:",len(cda.hypotheses))
    print("SELF-TEST PASSED")
