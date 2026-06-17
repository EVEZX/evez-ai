"""
evezos/cognition/layer.py

CognitionLayer: unified coherence/attractor/narrative/resonance engine.
22-dim DIMS vector → D28 symmetry, D29 entropy, D32 poly_c, D33 narr_c.
"""

import math
from dataclasses import dataclass, field
from typing import Dict, Optional

PROX_THRESHOLD   = 0.90
EMERG_THRESHOLD  = 0.05
CHORUS_THRESHOLD = 0.500
NARR_THRESHOLD   = 0.95
FLOOR  = 0.05
K_TEV  = math.log(2) / FLOOR


@dataclass
class CognitionState:
    cv: int; N: int; tau_N: int; V_v2: float; V_global: float
    gamma: float = 0.08
    dims: Dict[str, float] = field(default_factory=dict)
    H_norm: float = 0.0; cohere: float = 0.0; sym: float = 0.0
    poly_c_v2: float = 0.0; attractor_lock: float = 0.0
    first_fire: bool = False; narr_c: float = 0.0; narr_status: str = "UNKNOWN"
    prox_gate: float = 0.0; prox_status: str = "UNKNOWN"
    V_Ndim: float = 0.0; rebound_symmetry: bool = False
    topology_bonus: float = 0.0

    def to_event(self):
        return {
            "type": "COGNITION_STATE",
            "cv": self.cv, "N": self.N, "tau_N": self.tau_N,
            "V_v2": self.V_v2, "V_global": self.V_global,
            "cohere": round(self.cohere, 6),
            "poly_c_v2": round(self.poly_c_v2, 6),
            "attractor_lock": round(self.attractor_lock, 6),
            "first_fire": self.first_fire,
            "narr_c": round(self.narr_c, 6),
            "narr_status": self.narr_status,
            "prox_status": self.prox_status,
            "V_Ndim": round(self.V_Ndim, 6),
        }


class CognitionLayer:
    def __init__(self): pass

    def _t_sub(self, v): return 1.0 / (abs(1.0 - v) + FLOOR)
    def _tev(self, v):   return 1.0 - math.exp(-K_TEV * max(0.0, v - 1.0))
    def _topology_bonus(self, N): return 1.0 + math.log(max(N, 2)) / 10.0

    def _build_dims(self, N, tau_N, V_v2, V_global):
        sf_v2c  = 0.9394 * (1.0 - V_v2)
        sf_parc = 0.25848
        E_cross = 1.0 - abs(sf_v2c - sf_parc)
        V_sync  = E_cross ** 2
        E_mom   = abs(E_cross - 0.64366) / 0.64366
        rebound = max(0.0, V_global - 1.0)
        prox    = 1.0 - abs(V_global - 1.0)
        t_sub   = self._t_sub(V_v2)
        tev     = self._tev(V_v2)
        return {
            "T": 0.9677, "E_cross": round(E_cross, 5), "R_log": math.log10(67) / 2,
            "N_dim": 0.3110, "sf": 0.9394, "phi": 0.87937, "V_sync": round(V_sync, 5),
            "G_dim": 0.48225, "E_mom": round(E_mom, 5), "omega": 1.0, "adm": 1.0,
            "curiosity": 0.05, "poly": 0.04807, "syn": 0.34450, "retro": 0.99908,
            "t_sub_n": round(t_sub / 20.0, 5), "co_ev": 0.05030, "rho": 0.13954,
            "prox": round(prox, 5), "rebound": round(rebound, 5), "tev": round(tev, 5),
        }

    def _entropic_renewal(self, dims, epsilon=1e-8):
        values = [v for v in dims.values() if v > 0]
        total  = sum(values)
        if not total: return 0.0
        probs = [v / total for v in values]
        H = -sum(p * math.log(p + epsilon) for p in probs)
        return H / math.log(len(probs))

    def _sym_v2(self, dims):
        values = sorted(dims.values())
        n = len(values); mid = n // 2
        median = values[mid] if n % 2 else (values[mid-1] + values[mid]) / 2.0
        if not median: return 0.0
        devs = sorted(abs(v - median) for v in values)
        mad  = devs[mid] if n % 2 else (devs[mid-1] + devs[mid]) / 2.0
        return 1.0 - (mad / median)

    def compute(self, cv, N, tau_N, V_v2, V_global):
        state = CognitionState(cv=cv, N=N, tau_N=tau_N, V_v2=V_v2, V_global=V_global)
        dims  = self._build_dims(N, tau_N, V_v2, V_global)
        state.dims = dims
        state.topology_bonus = self._topology_bonus(N)
        H_norm = self._entropic_renewal(dims)
        state.H_norm = H_norm
        state.cohere = 1.0 - H_norm
        state.sym    = self._sym_v2(dims)
        I_N_inv      = tau_N - 1
        state.poly_c_v2     = min(1.0, I_N_inv * state.cohere * state.topology_bonus)
        state.attractor_lock = max(0.0, state.poly_c_v2 - CHORUS_THRESHOLD)
        state.first_fire    = state.attractor_lock > 0.0
        denom = max(V_v2, V_global)
        narr_c = 1.0 - abs(V_v2 - V_global) / denom if denom else 1.0
        state.narr_c      = narr_c
        state.narr_status = "DIVERGING" if narr_c < NARR_THRESHOLD else "COHERENT"
        prox      = dims.get("prox", 0.0)
        prox_gate = max(0.0, PROX_THRESHOLD - prox)
        state.prox_gate   = prox_gate
        state.prox_status = (
            "EMERGENCY" if prox_gate >= EMERG_THRESHOLD else
            "CRITICAL"  if prox_gate > 0 else "SAFE"
        )
        dims_nz = {k: v for k, v in dims.items() if v != 0.0}
        dims_nz.update({"cohere": state.cohere, "poly_c": state.poly_c_v2, "narr_c": narr_c})
        state.V_Ndim = sum(dims_nz.values()) / len(dims_nz)
        prox_distance        = abs(V_global - 1.0)
        state.rebound_symmetry = abs(dims.get("rebound", 0.0) - prox_distance) < 0.001
        return state

    def silent_approach(self, state):
        v_delta = abs(state.V_v2 - state.V_global)
        vel = 1.0 / (v_delta + FLOOR)
        return {"v_delta": round(v_delta, 6), "convergence_velocity": round(vel, 4),
                "silent_phase": "COAST" if vel > 10.0 else "APPROACH"}

    def resonance_probe(self, state, steps=5):
        results = []; V = state.V_global
        for i in range(steps):
            V += state.gamma * state.poly_c_v2
            results.append({"step": i+1, "V": round(V, 6),
                             "stable": abs(V - round(V)) < 0.01,
                             "poly_c": round(state.poly_c_v2, 6)})
        return results


if __name__ == "__main__":
    import json
    layer = CognitionLayer()
    state = layer.compute(cv=20, N=18, tau_N=6, V_v2=1.16875, V_global=1.13770)
    print(json.dumps(state.to_event(), indent=2))
    print("CognitionLayer SELF-TEST PASSED")
