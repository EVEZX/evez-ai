#!/usr/bin/env python3
"""
A012 — Telemetry Prediction & Coincidence Engine
EVEZ-OS worker node | [A12]

TWO MANDATES:
  1. PREDICTION: For every upcoming round N, pre-compute and emit a prediction receipt
     before the tick fires. Tracks prediction accuracy vs actuals (Brier-style).
  2. COINCIDENCE: After each tick, scan all data/ JSONL ledgers for structural,
     temporal, and numerical coincidences with hyperloop state. Emit COINCIDENCE
     events when thresholds are crossed.

Canonical formula (Formula A):
  poly_c = (tau * omega_k * topo) / (2 * sqrt(N))
  topo = {1: 1.15, 2: 1.30, 3: 1.45}
  N = round_num + 80

Prediction accuracy tracked via Brier score per round.
Coincidence scanning uses: V_global, fire_count, round, tau, omega_k, poly_c, N.
"""

import math
import json
import hashlib
import os
from datetime import datetime, timezone
from typing import Optional

# ── Constants ────────────────────────────────────────────────────────────────
T_FIRE = 0.45
T_EXTREME = 2.55
TOPO_MAP = {1: 1.15, 2: 1.30, 3: 1.45}
N_OFFSET = 80  # N = round + N_OFFSET

# Coincidence thresholds
COINCIDENCE_EPSILON_RATIO = 0.005   # 0.5% numeric proximity
COINCIDENCE_TEMPORAL_WINDOW_ROUNDS = 3  # rounds within which events are "near"

# ── Formula A (canonical) ─────────────────────────────────────────────────────
def divisors(n: int) -> list[int]:
    """Explicit divisor enumeration — never shorthand."""
    divs = []
    for i in range(1, int(math.isqrt(n)) + 1):
        if n % i == 0:
            divs.append(i)
            if i != n // i:
                divs.append(n // i)
    return sorted(divs)

def tau(n: int) -> int:
    return len(divisors(n))

def distinct_prime_factors(n: int) -> int:
    count = 0
    d = 2
    temp = n
    while d * d <= temp:
        if temp % d == 0:
            count += 1
            while temp % d == 0:
                temp //= d
        d += 1
    if temp > 1:
        count += 1
    return count

def compute_poly_c(round_num: int) -> dict:
    N = round_num + N_OFFSET
    tau_val = tau(N)
    omega = distinct_prime_factors(N)
    topo = TOPO_MAP.get(omega, 1.15 + 0.15 * (omega - 1))  # extrapolate beyond ω=3
    poly_c = (tau_val * omega * topo) / (2 * math.sqrt(N))
    p_fire = max(0.0, min(1.0, (poly_c - T_FIRE) / (T_EXTREME - T_FIRE)))
    fire_candidate = poly_c >= T_FIRE and omega == 3
    high_tau = tau_val >= 12
    return {
        "round": round_num,
        "N": N,
        "tau": tau_val,
        "omega_k": omega,
        "topo": topo,
        "poly_c": round(poly_c, 6),
        "p_fire": round(p_fire, 6),
        "fire_candidate": fire_candidate,
        "high_tau": high_tau,
        "divisors": divisors(N),
    }

# ── Prediction Engine ─────────────────────────────────────────────────────────
def generate_prediction(round_num: int, V_global: float, fire_count: int) -> dict:
    """
    Emit a pre-round prediction receipt. This is the PRECOMMIT side of two-phase receipt.
    Must be called BEFORE the tick fires.
    """
    params = compute_poly_c(round_num)
    ts = datetime.now(timezone.utc).isoformat()
    commitment_string = f"EVEZ:PREDICT:R{round_num}:poly_c={params['poly_c']:.6f}:p_fire={params['p_fire']:.6f}"
    commitment_hash = hashlib.sha256(commitment_string.encode()).hexdigest()[:16]

    record = {
        "type": "evez.a012.prediction",
        "agent": "A012",
        "round": round_num,
        "ts": ts,
        "predicted": {
            "N": params["N"],
            "tau": params["tau"],
            "omega_k": params["omega_k"],
            "topo": params["topo"],
            "poly_c": params["poly_c"],
            "p_fire": params["p_fire"],
            "fire_candidate": params["fire_candidate"],
            "high_tau": params["high_tau"],
        },
        "context": {
            "V_global": V_global,
            "fire_count": fire_count,
        },
        "commitment_hash": commitment_hash,
        "falsifier": f"R{round_num} actual poly_c must equal predicted within 0.001",
        "phase": "PHASE1_PRECOMMIT",
        "note": f"PREDICT | R{round_num} | N={params['N']} | tau={params['tau']} | omega={params['omega_k']} | poly_c={params['poly_c']:.4f} | p_fire={params['p_fire']:.4f}"
    }
    return record

def score_prediction(prediction: dict, actual: dict) -> dict:
    """
    Phase 2: score a prediction against actual tick result.
    actual = {round, poly_c, fire_actual, V, fire_count, spine_hash}
    Returns Brier contribution and accuracy verdict.
    """
    p = prediction["predicted"]["p_fire"]
    a = 1 if actual.get("fire_actual", False) else 0
    brier = (p - a) ** 2
    poly_c_error = abs(prediction["predicted"]["poly_c"] - actual.get("poly_c", 0))
    kept = poly_c_error < 0.001

    return {
        "type": "evez.a012.prediction_score",
        "agent": "A012",
        "round": prediction["round"],
        "ts": datetime.now(timezone.utc).isoformat(),
        "prediction_hash": prediction["commitment_hash"],
        "p_fire_predicted": p,
        "fire_actual": actual.get("fire_actual", False),
        "brier": round(brier, 6),
        "poly_c_predicted": prediction["predicted"]["poly_c"],
        "poly_c_actual": actual.get("poly_c"),
        "poly_c_error": round(poly_c_error, 6),
        "verdict": "KEPT" if kept else "BROKEN",
        "phase": "PHASE2_RECEIPT",
        "spine_hash": actual.get("spine_hash"),
        "note": f"SCORE | R{prediction['round']} | p={p:.4f} | actual={'FIRE' if a else 'NO_FIRE'} | brier={brier:.4f} | {'KEPT' if kept else 'BROKEN'}"
    }

# ── Coincidence Scanner ───────────────────────────────────────────────────────
def _near(a: float, b: float, epsilon: float = COINCIDENCE_EPSILON_RATIO) -> bool:
    """True if a and b are within epsilon*max(|a|,|b|) of each other."""
    if a == 0 and b == 0:
        return True
    scale = max(abs(a), abs(b))
    return abs(a - b) / scale < epsilon if scale > 0 else True

def scan_jsonl_for_coincidences(
    filepath: str,
    hyperloop_state: dict,
    round_num: int,
    numeric_fields: list[str] = None
) -> list[dict]:
    """
    Scan a JSONL data file for coincidences with current hyperloop state.

    Coincidence types detected:
      - NUMERIC: a value in the data record is within EPSILON of V_global, poly_c, fire_count, N, tau
      - TEMPORAL: event happened within COINCIDENCE_TEMPORAL_WINDOW_ROUNDS of a FIRE event (by round field)
      - PATTERN: tau or omega_k appears as a literal value in the record
      - STRUCTURAL: record references the same N, round, or fire_count
    """
    if not os.path.exists(filepath):
        return []

    params = compute_poly_c(round_num)
    V = hyperloop_state.get("V", hyperloop_state.get("V_global", 0.0))
    fire_count = hyperloop_state.get("fire_count", 0)
    fire_rounds = hyperloop_state.get("fire_rounds", [])  # list of rounds where fires occurred

    anchors = {
        "V_global": V,
        "poly_c": params["poly_c"],
        "fire_count": float(fire_count),
        "N": float(params["N"]),
        "tau": float(params["tau"]),
        "round": float(round_num),
        "p_fire": params["p_fire"],
    }

    coincidences = []

    try:
        with open(filepath, "r") as f:
            for line_num, line in enumerate(f):
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue

                hits = []

                # Flatten record values for numeric scanning
                def _extract_numbers(obj, prefix=""):
                    nums = {}
                    if isinstance(obj, dict):
                        for k, v in obj.items():
                            nums.update(_extract_numbers(v, f"{prefix}{k}."))
                    elif isinstance(obj, (int, float)) and not isinstance(obj, bool):
                        nums[prefix.rstrip(".")] = float(obj)
                    return nums

                record_nums = _extract_numbers(record)

                # NUMERIC coincidence
                for anchor_name, anchor_val in anchors.items():
                    for field_path, field_val in record_nums.items():
                        if abs(anchor_val) < 0.001:
                            continue  # skip near-zero anchors
                        if _near(anchor_val, field_val):
                            hits.append({
                                "type": "NUMERIC",
                                "anchor": anchor_name,
                                "anchor_val": anchor_val,
                                "field": field_path,
                                "field_val": field_val,
                                "delta": abs(anchor_val - field_val),
                            })

                # TEMPORAL coincidence: if record has a 'round' field near a fire round
                rec_round = record.get("round") or record.get("round_id")
                if isinstance(rec_round, (int, float)):
                    for fr in fire_rounds:
                        if abs(int(rec_round) - fr) <= COINCIDENCE_TEMPORAL_WINDOW_ROUNDS:
                            hits.append({
                                "type": "TEMPORAL",
                                "anchor": "fire_round",
                                "fire_round": fr,
                                "record_round": int(rec_round),
                                "delta_rounds": abs(int(rec_round) - fr),
                            })

                # STRUCTURAL: exact round or fire_count match
                if rec_round == round_num:
                    hits.append({"type": "STRUCTURAL", "field": "round", "value": round_num})
                if record.get("fire_count") == fire_count:
                    hits.append({"type": "STRUCTURAL", "field": "fire_count", "value": fire_count})

                if hits:
                    coincidences.append({
                        "source_file": os.path.basename(filepath),
                        "line": line_num + 1,
                        "record_preview": {k: v for k, v in list(record.items())[:4]},
                        "hits": hits,
                        "hit_count": len(hits),
                        "round": round_num,
                    })

    except Exception as e:
        pass  # file unreadable — no coincidence

    return coincidences

def generate_coincidence_event(
    round_num: int,
    hyperloop_state: dict,
    data_dir: str = "data/",
    scan_files: list[str] = None
) -> dict:
    """
    Run full coincidence scan across all data JSONL files.
    Returns a COINCIDENCE_BATCH event ready for spine append.
    """
    if scan_files is None:
        scan_files = [
            "data/mandela_effects.jsonl",
            "data/decisions.jsonl",
            "data/recursion.jsonl",
            "data/meta_interpretations.jsonl",
            "data/causal_boundaries.jsonl",
            "data/multi_path.jsonl",
            "data/semantic_space.jsonl",
            "data/metanoia.jsonl",
            "data/semantics/semantic_events.jsonl",
        ]

    all_hits = []
    files_scanned = 0
    for filepath in scan_files:
        if os.path.exists(filepath):
            hits = scan_jsonl_for_coincidences(filepath, hyperloop_state, round_num)
            all_hits.extend(hits)
            files_scanned += 1

    params = compute_poly_c(round_num)
    ts = datetime.now(timezone.utc).isoformat()

    # Aggregate by type
    type_counts = {}
    for h in all_hits:
        for hit in h["hits"]:
            t = hit["type"]
            type_counts[t] = type_counts.get(t, 0) + 1

    total_hits = sum(len(h["hits"]) for h in all_hits)
    signal_strength = min(1.0, total_hits / 10.0)  # normalize to [0,1]

    event = {
        "type": "evez.a012.coincidence_batch",
        "agent": "A012",
        "round": round_num,
        "ts": ts,
        "params": {
            "N": params["N"],
            "tau": params["tau"],
            "omega_k": params["omega_k"],
            "poly_c": params["poly_c"],
            "fire_candidate": params["fire_candidate"],
        },
        "scan_summary": {
            "files_scanned": files_scanned,
            "records_with_hits": len(all_hits),
            "total_hits": total_hits,
            "type_counts": type_counts,
            "signal_strength": round(signal_strength, 4),
        },
        "top_hits": sorted(all_hits, key=lambda x: x["hit_count"], reverse=True)[:5],
        "note": f"COINCIDENCE | R{round_num} | N={params['N']} | files={files_scanned} | hits={total_hits} | signal={signal_strength:.3f} | types={type_counts}"
    }
    return event

# ── Lookahead Table Generator ─────────────────────────────────────────────────
def generate_lookahead(
    current_round: int,
    lookahead_n: int = 10,
    V_global: float = 0.0,
    fire_count: int = 0
) -> list[dict]:
    """
    Generate prediction table for next N rounds.
    Flags FIRE candidates, HIGH_TAU rounds, and extreme composites.
    """
    table = []
    for i in range(1, lookahead_n + 1):
        r = current_round + i
        p = compute_poly_c(r)
        delta_V_est = 0.148 * p["p_fire"] if p["fire_candidate"] else 0.0  # rough linear est
        table.append({
            "round": r,
            "N": p["N"],
            "tau": p["tau"],
            "omega_k": p["omega_k"],
            "poly_c": p["poly_c"],
            "p_fire": p["p_fire"],
            "fire_candidate": p["fire_candidate"],
            "high_tau": p["high_tau"],
            "delta_V_estimate": round(delta_V_est, 4),
            "V_estimate": round(V_global + delta_V_est, 6) if delta_V_est else None,
            "class": (
                "EXTREME" if p["poly_c"] >= 2.34 else
                "HIGH_PROBABILITY" if p["p_fire"] >= 0.5 else
                "FIRE_CANDIDATE" if p["fire_candidate"] else
                "HIGH_TAU" if p["high_tau"] else
                "PRIME" if p["tau"] == 2 else
                "LOW"
            )
        })
    return table

# ── Spine Entry Builder ───────────────────────────────────────────────────────
def build_spine_entry(
    action: str,
    round_num: int,
    data: dict,
    agent_tag: str = "[A12]"
) -> str:
    """Build a single-line JSONL spine entry for master_bus_log."""
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "agent": f"A012{agent_tag}",
        "action": action,
        "round": round_num,
        **data
    }
    return json.dumps(entry)

# ── Main Run Interface ────────────────────────────────────────────────────────
def run_a012(
    hyperloop_state: dict,
    mode: str = "full",
    scan_data_dir: str = "data/"
) -> dict:
    """
    Main entry point for A012.

    mode options:
      'predict'    — emit prediction for next N rounds only
      'coincidence' — scan for coincidences only
      'full'       — both (default)
      'score'      — score last round's prediction against actuals (requires actual in state)

    Returns spine_entries (list of JSONL strings) + events (list of dicts).
    """
    round_num = hyperloop_state.get("round", 0)
    V_global = hyperloop_state.get("V", hyperloop_state.get("V_global", 0.0))
    fire_count = hyperloop_state.get("fire_count", 0)

    spine_entries = []
    events = []

    if mode in ("predict", "full"):
        # Lookahead predictions for next 10 rounds
        table = generate_lookahead(round_num, lookahead_n=10, V_global=V_global, fire_count=fire_count)

        # Immediate next-round prediction (PHASE1 precommit)
        next_round = round_num + 1
        pred = generate_prediction(next_round, V_global, fire_count)
        events.append(pred)
        spine_entries.append(build_spine_entry("PREDICTION_PRECOMMIT", next_round, {
            "predicted_poly_c": pred["predicted"]["poly_c"],
            "p_fire": pred["predicted"]["p_fire"],
            "fire_candidate": pred["predicted"]["fire_candidate"],
            "commitment_hash": pred["commitment_hash"],
            "note": pred["note"],
        }))

        # Flag any EXTREME or HIGH_PROBABILITY rounds in lookahead
        flags = [r for r in table if r["fire_candidate"]]
        if flags:
            spine_entries.append(build_spine_entry("LOOKAHEAD_FLAGS", round_num, {
                "flags": [{
                    "round": r["round"],
                    "N": r["N"],
                    "tau": r["tau"],
                    "poly_c": r["poly_c"],
                    "p_fire": r["p_fire"],
                    "class": r["class"]
                } for r in flags],
                "note": f"LOOKAHEAD | {len(flags)} fire candidates in next 10 rounds",
            }))

    if mode in ("coincidence", "full"):
        coincidence_event = generate_coincidence_event(
            round_num=round_num,
            hyperloop_state=hyperloop_state,
            data_dir=scan_data_dir
        )
        events.append(coincidence_event)
        spine_entries.append(build_spine_entry("COINCIDENCE_SCAN", round_num, {
            "files_scanned": coincidence_event["scan_summary"]["files_scanned"],
            "total_hits": coincidence_event["scan_summary"]["total_hits"],
            "signal_strength": coincidence_event["scan_summary"]["signal_strength"],
            "type_counts": coincidence_event["scan_summary"]["type_counts"],
            "note": coincidence_event["note"],
        }))

    return {
        "agent": "A012",
        "round": round_num,
        "mode": mode,
        "spine_entries": spine_entries,
        "events": events,
        "summary": {
            "predictions_emitted": sum(1 for e in events if "prediction" in e.get("type", "")),
            "coincidence_batches": sum(1 for e in events if "coincidence" in e.get("type", "")),
            "total_spine_entries": len(spine_entries),
        }
    }


if __name__ == "__main__":
    import argparse, sys

    parser = argparse.ArgumentParser(description="A012 Telemetry Prediction & Coincidence Engine")
    parser.add_argument("--state", default="data/hyperloop_state.json", help="Path to hyperloop_state.json")
    parser.add_argument("--mode", default="full", choices=["full", "predict", "coincidence", "score"])
    parser.add_argument("--output", default="-", help="Output file for spine entries (- for stdout)")
    parser.add_argument("--round", type=int, default=None, help="Override current round")
    args = parser.parse_args()

    # Load state
    try:
        with open(args.state) as f:
            state = json.load(f)
    except FileNotFoundError:
        print(f"ERROR: state file not found: {args.state}", file=sys.stderr)
        sys.exit(1)

    if args.round:
        state["round"] = args.round

    result = run_a012(state, mode=args.mode)

    if args.output == "-":
        for entry in result["spine_entries"]:
            print(entry)
        for event in result["events"]:
            print(json.dumps(event, indent=2))
    else:
        with open(args.output, "a") as f:
            for entry in result["spine_entries"]:
                f.write(entry + "\n")

    print(f"\nA012 [A12] | R{result['round']} | mode={result['mode']} | "
          f"predictions={result['summary']['predictions_emitted']} | "
          f"coincidences={result['summary']['coincidence_batches']} | "
          f"spine_entries={result['summary']['total_spine_entries']} | ◊",
          file=sys.stderr)
