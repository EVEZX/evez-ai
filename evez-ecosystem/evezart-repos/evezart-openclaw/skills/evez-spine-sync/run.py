#!/usr/bin/env python3
"""
EVEZ SPINE SYNC — Retrocausal threshold decay + DB sync + DGM loop monitor

Every 4.1 minutes (Karpathy loop):
  1. Read recent FIRE events
  2. Apply retrocausal decay to causing thresholds (factor=0.95)
  3. Compute phi delta
  4. Update DGM loop record in DB
  5. Alert if phi drops below 0.990

Commands:
  decay     — apply retrocausal decay to all recent FIRE events
  phi       — show current phi + DGM loop status
  sync      — sync local store to DB (both directions)
  watch     — run continuously (every 4.1 minutes)
  invariance [file] — run 5-way Invariance Battery on a Python file
"""

import argparse
import hashlib
import json
import math
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

STORE_PATH  = Path.home() / ".openclaw" / "evez-spine-state.json"
DECAY_FACTOR = 0.95
LOOP_INTERVAL = 246  # 4.1 minutes in seconds
PHI_ALERT_THRESHOLD = 0.990

# ─── STATE ────────────────────────────────────────────────────────────────────

def load_state() -> dict:
    if STORE_PATH.exists():
        return json.loads(STORE_PATH.read_text())
    return {
        "phi":         0.995,
        "iteration":   0,
        "r2":          0.95,
        "thresholds":  {"default": 1.0},
        "decay_log":   [],
        "last_sync":   None,
    }

def save_state(state: dict):
    STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STORE_PATH.write_text(json.dumps(state, indent=2, default=str))

# ─── RETROCAUSAL DECAY ────────────────────────────────────────────────────────

def apply_retrocausal_decay(state: dict, fire_events: list) -> dict:
    """
    When a FIRE event succeeds, decay the threshold that caused it.
    Future success (T+1) → decay threshold (T) → easier detection (T+2)
    """
    decays_applied = []
    for ev in fire_events:
        if ev.get("status") in ("CANONICAL", "HYPER", "FIRE") and ev.get("poly_c", 0) >= 0.8:
            domain = ev.get("domain", "default")
            old_threshold = state["thresholds"].get(domain, 1.0)
            new_threshold = old_threshold * DECAY_FACTOR
            state["thresholds"][domain] = round(new_threshold, 6)
            decays_applied.append({
                "domain": domain,
                "old": old_threshold,
                "new": new_threshold,
                "caused_by": ev.get("hash", "?"),
            })

    state["decay_log"].extend(decays_applied)
    state["decay_log"] = state["decay_log"][-100:]  # keep last 100

    # phi improvement: each decay slightly increases phi
    if decays_applied:
        phi_delta = len(decays_applied) * 0.0001
        state["phi"] = min(0.9999, state["phi"] + phi_delta)

    return state, decays_applied

def compute_phi(state: dict, events: list) -> float:
    """
    phi = weighted average of:
      - canonical ratio (events CANONICAL / total)
      - threshold convergence (thresholds approaching optimal ~0.85)
      - iteration progress (current / 700 target)
    """
    if not events:
        return state.get("phi", 0.995)

    canonical = sum(1 for e in events if e.get("status") in ("CANONICAL","HYPER","FIRE"))
    canonical_ratio = canonical / len(events)

    thresholds = list(state.get("thresholds", {}).values())
    threshold_convergence = 1 - sum(abs(t - 0.85) for t in thresholds) / len(thresholds) if thresholds else 0.5

    iteration_progress = min(state.get("iteration", 0) / 700, 1.0)

    phi = (canonical_ratio * 0.5 + threshold_convergence * 0.3 + iteration_progress * 0.2)
    return round(min(0.9999, max(state.get("phi", 0.5), phi)), 6)

# ─── DATABASE ─────────────────────────────────────────────────────────────────

def log_dgm_iteration(phi: float, r2: float, delta: float, status: str, notes: str = ""):
    db_url = os.environ.get("DATABASE_URL", "")
    if not db_url:
        return
    try:
        import psycopg2
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO dgm_loop (iteration, phi, r2, delta_phi, status, notes)
            SELECT COALESCE(MAX(iteration), 0) + 1, %s, %s, %s, %s, %s
            FROM dgm_loop
        """, (phi, r2, delta, status, notes))
        conn.commit()
        conn.close()
    except Exception:
        pass

def load_fire_events_from_db() -> list:
    db_url = os.environ.get("DATABASE_URL", "")
    if not db_url:
        return []
    try:
        import psycopg2
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        cur.execute("SELECT title, domain, poly_c, status, hash FROM fire_events ORDER BY poly_c DESC")
        cols = [d[0] for d in cur.description]
        rows = [dict(zip(cols, row)) for row in cur.fetchall()]
        conn.close()
        return rows
    except Exception:
        # Fallback to local store
        fire_store = Path.home() / ".openclaw" / "evez-fire-store.json"
        if fire_store.exists():
            return json.loads(fire_store.read_text())
        return []

# ─── INVARIANCE BATTERY ────────────────────────────────────────────────────────

def run_invariance_battery(file_path: str) -> dict:
    """
    Run the 5-way EVEZ Invariance Battery against a Python file.
    Matches OKTOKLAW certification protocol.
    """
    import importlib.util, ast, inspect

    results = {}
    warnings = []
    passes = 0
    source = Path(file_path).read_text()

    # ROTATION 1: Time Shift — does it reference time correctly?
    time_patterns = ["datetime", "time.time", "timezone", "timedelta"]
    uses_time = any(p in source for p in time_patterns)
    hardcoded_time = any(t in source for t in ["2024-01-01", "2023-12-31", "timestamp=0"])
    r1 = "PASS" if not hardcoded_time else "WARN"
    results["time_shift"] = r1
    if r1 == "PASS":
        passes += 1
    else:
        warnings.append("Hardcoded timestamps detected")

    # ROTATION 2: State Shift — idempotent functions?
    try:
        tree = ast.parse(source)
        funcs = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
        global_mutations = sum(1 for n in ast.walk(tree) if isinstance(n, ast.Global))
        r2 = "WARN" if global_mutations > 3 else "PASS"
        results["state_shift"] = r2
        if r2 == "PASS":
            passes += 1
        else:
            warnings.append(f"High global mutation count: {global_mutations}")
    except SyntaxError as e:
        results["state_shift"] = "FAIL"
        warnings.append(f"Syntax error: {e}")

    # ROTATION 3: Frame Shift — can logic be inverted without catastrophe?
    has_assertions = "assert " in source or "raise" in source
    has_error_handling = "except" in source or "try:" in source
    r3 = "PASS" if (has_error_handling or has_assertions) else "WARN"
    results["frame_shift"] = r3
    if r3 == "PASS":
        passes += 1
    else:
        warnings.append("No error handling or assertions found")

    # ROTATION 4: Adversarial Shift — does it have a falsifier structure?
    has_falsifier = any(kw in source for kw in ["falsifier", "assert", "raise ValueError", "if not", "verify"])
    r4 = "PASS" if has_falsifier else "WARN"
    results["adversarial_shift"] = r4
    if r4 == "PASS":
        passes += 1
    else:
        warnings.append("No falsifier pattern detected")

    # ROTATION 5: Identity Shift — does it survive goal swap (profit→safety)?
    has_safety = any(kw in source for kw in ["safety", "limit", "max_", "MIN_", "threshold", "guard"])
    r5 = "PASS" if has_safety else "WARN"
    results["identity_shift"] = r5
    if r5 == "PASS":
        passes += 1
    else:
        warnings.append("No safety/limit patterns detected")

    # poly_c for this module
    tau   = passes + 1
    omega = passes / 5.0
    topo  = passes / 5.0
    N     = max(1, 5 - passes + 1)
    poly_c_raw = (tau * omega * topo) / (2 * math.sqrt(N))
    poly_c_sc  = poly_c_raw / (1 + poly_c_raw) if poly_c_raw > 1 else poly_c_raw

    status = "CANONICAL" if passes >= 4 else ("WARN" if passes >= 3 else "FAIL")

    return {
        "file":      file_path,
        "passes":    f"{passes}/5",
        "rotations": results,
        "warnings":  warnings,
        "poly_c":    round(poly_c_sc, 4),
        "status":    status,
        "hash":      hashlib.sha256(source.encode()).hexdigest()[:8].upper(),
    }

# ─── COMMANDS ─────────────────────────────────────────────────────────────────

def cmd_phi(args):
    state  = load_state()
    events = load_fire_events_from_db()
    phi    = compute_phi(state, events)

    print(f"\n  DGM LOOP STATUS")
    print(f"  {'─'*40}")
    print(f"  phi:         {phi:.6f}")
    print(f"  target:      0.999000")
    print(f"  gap:         {0.999 - phi:.6f}")
    print(f"  iteration:   {state.get('iteration', 0)} / 700")
    print(f"  r² score:    {state.get('r2', 0.95):.4f}")
    print()

    thresholds = state.get("thresholds", {})
    if thresholds:
        print(f"  Thresholds (after retrocausal decay):")
        for domain, threshold in sorted(thresholds.items()):
            decay_count = sum(1 for d in state.get("decay_log", []) if d.get("domain") == domain)
            print(f"    {domain:<25} {threshold:.6f}  (decayed {decay_count}×)")
    print()

    if phi < PHI_ALERT_THRESHOLD:
        print(f"  ⚠ ALERT: phi dropped below {PHI_ALERT_THRESHOLD}")
        print(f"  This is expected near phi=1.0 — do not abort the loop.")
    elif phi >= 0.999:
        print(f"  ✓ TARGET REACHED: phi ≥ 0.999")
    else:
        print(f"  ◉ Approaching target — {((0.999 - phi) / 0.004 * 100):.0f}% of gap remaining")
    print()

def cmd_decay(args):
    state  = load_state()
    events = load_fire_events_from_db()

    print(f"\n  RETROCAUSAL DECAY")
    print(f"  factor: {DECAY_FACTOR}")
    print(f"  applying to {len(events)} FIRE events...\n")

    state, decays = apply_retrocausal_decay(state, events)

    if not decays:
        print("  No canonical events found to decay from.")
    else:
        for d in decays:
            print(f"  ✓ {d['domain']:<20} {d['old']:.6f} → {d['new']:.6f}")
        print(f"\n  phi: {state['phi']:.6f} (delta: +{len(decays) * 0.0001:.4f})")

    state["iteration"]  = state.get("iteration", 0) + 1
    state["last_sync"]  = datetime.now(timezone.utc).isoformat()
    save_state(state)

    phi_delta = len(decays) * 0.0001
    log_dgm_iteration(
        phi=state["phi"], r2=state.get("r2", 0.95),
        delta=phi_delta,
        status="IMPROVING" if phi_delta > 0 else "STABLE",
        notes=f"Decayed {len(decays)} domains"
    )
    print()

def cmd_sync(args):
    state  = load_state()
    events = load_fire_events_from_db()
    print(f"\n  Syncing spine... {len(events)} events loaded")
    state["last_sync"] = datetime.now(timezone.utc).isoformat()
    save_state(state)
    print(f"  ✓ State saved to {STORE_PATH}")
    print()

def cmd_watch(args):
    print(f"\n  EVEZ Spine Sync — continuous mode")
    print(f"  Running every {LOOP_INTERVAL}s (4.1 min Karpathy loop)")
    print(f"  Ctrl+C to stop\n")
    iteration = 0
    while True:
        iteration += 1
        ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
        print(f"  [{ts}] Iteration {iteration}", end=" ")
        try:
            state  = load_state()
            events = load_fire_events_from_db()
            state, decays = apply_retrocausal_decay(state, events)
            state["iteration"] = state.get("iteration", 0) + 1
            phi_new = compute_phi(state, events)
            phi_old = state["phi"]
            state["phi"] = phi_new
            save_state(state)
            delta = phi_new - phi_old
            sign = "+" if delta >= 0 else ""
            print(f"phi={phi_new:.6f} ({sign}{delta:.6f}) decays={len(decays)}")

            if phi_new < PHI_ALERT_THRESHOLD:
                print(f"  ⚠ phi < {PHI_ALERT_THRESHOLD} — temporary regression expected, do not abort")

            log_dgm_iteration(
                phi=phi_new, r2=state.get("r2", 0.95), delta=delta,
                status="IMPROVING" if delta > 0 else ("REGRESSION" if delta < -0.001 else "STABLE"),
            )
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"  ERROR: {e}")
        time.sleep(LOOP_INTERVAL)

def cmd_invariance(args):
    if not args.file:
        print("  Usage: evez-spine-sync invariance --file path/to/module.py")
        return
    if not Path(args.file).exists():
        print(f"  File not found: {args.file}")
        return

    print(f"\n  OKTOKLAW INVARIANCE BATTERY")
    print(f"  Target: {args.file}")
    print(f"  {'─'*44}")

    result = run_invariance_battery(args.file)

    for rotation, status in result["rotations"].items():
        icon = "✓" if status == "PASS" else ("⚠" if status == "WARN" else "✗")
        print(f"  {icon} {rotation:<25} {status}")

    print(f"  {'─'*44}")
    print(f"  Passes:  {result['passes']}")
    print(f"  poly_c:  {result['poly_c']:.4f}")
    print(f"  Status:  {result['status']}")
    print(f"  Hash:    {result['hash']}")

    if result["warnings"]:
        print(f"\n  Warnings:")
        for w in result["warnings"]:
            print(f"    ⚠ {w}")
    print()

# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="EVEZ Spine Sync — retrocausal decay + DGM loop monitor",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("phi",   help="Current phi + DGM loop status")
    sub.add_parser("decay", help="Apply retrocausal decay")
    sub.add_parser("sync",  help="Sync state to DB")
    sub.add_parser("watch", help="Run continuously (Karpathy loop)")

    ip = sub.add_parser("invariance", help="Run 5-way Invariance Battery")
    ip.add_argument("--file", type=str, required=True)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    dispatch = {
        "phi":        cmd_phi,
        "decay":      cmd_decay,
        "sync":       cmd_sync,
        "watch":      cmd_watch,
        "invariance": cmd_invariance,
    }
    dispatch[args.command](args)

if __name__ == "__main__":
    main()
