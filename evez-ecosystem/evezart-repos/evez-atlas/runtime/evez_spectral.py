#!/usr/bin/env python3
"""
evez_spectral.py — Spectral network decomposition for the EVEZ agent ecosystem.

Decomposes the agent network into eigenvalues, communities, and signal flows.
Legitimate graph analysis — no offensive capabilities.

Usage:
  python3 evez_spectral.py
  python3 evez_spectral.py --json > network_analysis.json
"""

import numpy as np
import json
from dataclasses import dataclass, asdict
from typing import Optional

EVEZ_NODES = {
    0:  ("PHONE",        "interface",    "#FFD700"),
    1:  ("server.py",    "gateway",      "#00FFFF"),
    2:  ("MobBoss",      "orchestrator", "#BF5FFF"),
    3:  ("Scout",        "worker",       "#BF5FFF"),
    4:  ("L1_Witness",   "truth",        "#00FF88"),
    5:  ("CAIN",         "audit",        "#FF3333"),
    6:  ("Bookkeeper",   "ledger",       "#00FFCC"),
    7:  ("EVENT_SPINE",  "core",         "#FFD700"),
    8:  ("signer.py",    "security",     "#FF8800"),
    9:  ("PRIV_KEY",     "security",     "#FF8800"),
    10: ("claude_fast",  "model",        "#00FFFF"),
    11: ("CAIN_store",   "storage",      "#FF3333"),
    12: ("ReviewQueue",  "gate",         "#FFD700"),
    13: ("AgentVault",   "vault",        "#FF8800"),
    14: ("OpenClaw_GW",  "gateway",      "#BF5FFF"),
}

EVEZ_EDGES = [
    (0, 1, 1.0, "HTTPS"),
    (1, 2, 1.0, "dispatch"),
    (2, 3, 0.8, "plasma_beam"),
    (2, 4, 0.9, "witness_req"),
    (2, 5, 0.9, "audit_req"),
    (2, 6, 0.7, "ledger_req"),
    (2, 10, 0.6, "fast_lane"),
    (2, 12, 1.0, "review_gate"),
    (3, 7, 0.8, "observation"),
    (4, 7, 0.9, "consensus"),
    (5, 7, 1.0, "audit_seal"),
    (5, 11, 1.0, "store"),
    (6, 7, 0.8, "receipt"),
    (8, 7, 1.0, "sign"),
    (9, 8, 0.5, "key_access"),
    (10, 4, 0.7, "fast_result"),
    (12, 7, 1.0, "approved_action"),
    (13, 7, 0.9, "vault_event"),
    (14, 1, 0.9, "ws_relay"),
    (7, 6, 0.9, "spine_receipt"),
    (7, 5, 0.8, "spine_audit"),
    (7, 13, 0.7, "vault_store"),
]


def build_adjacency(nodes, edges):
    n = len(nodes)
    A = np.zeros((n, n))
    for (src, dst, weight, _) in edges:
        if src < n and dst < n:
            A[src][dst] = weight
    return A


def spectral_decompose(A, nodes):
    A_sym = (A + A.T) / 2
    degree = A_sym.sum(axis=1)
    D_inv_sqrt = np.diag(1.0 / np.sqrt(np.where(degree > 0, degree, 1)))
    L = D_inv_sqrt @ (np.diag(degree) - A_sym) @ D_inv_sqrt
    eigenvalues, eigenvectors = np.linalg.eigh(L)
    idx = np.argsort(eigenvalues)
    eigenvalues = eigenvalues[idx]
    eigenvectors = eigenvectors[:, idx]
    num_components = max(1, int(np.sum(eigenvalues < 1e-8)))
    alg_connectivity = float(eigenvalues[1]) if len(eigenvalues) > 1 else 0.0
    fiedler = eigenvectors[:, 1].tolist() if len(eigenvalues) > 1 else []
    spectral_gap = float(eigenvalues[2] - eigenvalues[1]) if len(eigenvalues) > 2 else 0.0
    assignments = ["A" if v >= 0 else "B" for v in fiedler] if fiedler else ["A"] * len(nodes)
    return {
        "eigenvalues": eigenvalues[:6].tolist(),
        "algebraic_connectivity": round(alg_connectivity, 6),
        "spectral_gap": round(spectral_gap, 6),
        "num_components": num_components,
        "fiedler_partition": {
            "A": [nodes[i][0] for i, v in enumerate(assignments) if v == "A"],
            "B": [nodes[i][0] for i, v in enumerate(assignments) if v == "B"],
        }
    }


def signal_flow(nodes, A):
    results = []
    for nid, (label, layer, _) in nodes.items():
        in_d = float(A[:, nid].sum())
        out_d = float(A[nid, :].sum())
        btw = in_d * out_d / max(1, (in_d + out_d))
        results.append({
            "node": label, "layer": layer,
            "in_degree": round(in_d, 3), "out_degree": round(out_d, 3),
            "betweenness": round(btw, 3),
            "is_bottleneck": btw > 0.5 and in_d > 0 and out_d > 0
        })
    return sorted(results, key=lambda x: x["betweenness"], reverse=True)


def run():
    A = build_adjacency(EVEZ_NODES, EVEZ_EDGES)
    spectral = spectral_decompose(A, EVEZ_NODES)
    flows = signal_flow(EVEZ_NODES, A)
    result = {
        "timestamp": __import__("datetime").datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "nodes": len(EVEZ_NODES),
        "edges": len(EVEZ_EDGES),
        "spectral": spectral,
        "signal_flow_top5": flows[:5],
        "bottlenecks": [f["node"] for f in flows if f["is_bottleneck"]]
    }
    return result


if __name__ == "__main__":
    import sys
    result = run()
    if "--json" in sys.argv:
        print(json.dumps(result, indent=2))
    else:
        print(f"Nodes: {result['nodes']} | Edges: {result['edges']}")
        print(f"Algebraic connectivity: {result['spectral']['algebraic_connectivity']}")
        print(f"Spectral gap: {result['spectral']['spectral_gap']}")
        print(f"Bottlenecks: {result['bottlenecks']}")
        print("\nTop signal flow nodes:")
        for n in result["signal_flow_top5"]:
            print(f"  {n['node']:20s} in={n['in_degree']:.2f} out={n['out_degree']:.2f} btw={n['betweenness']:.3f}")
