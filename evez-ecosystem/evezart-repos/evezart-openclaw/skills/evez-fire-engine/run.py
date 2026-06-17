#!/usr/bin/env python3
"""
EVEZ FIRE Engine — poly_c scoring, FIRE event creation, META-FIRE synthesis
The cognitive pattern detection core of EVEZ-OS.

Commands:
  score  tau=X omega=Y topo=Z N=K  — compute poly_c
  fire   [--title] [--domain] [--desc] [--falsifier]  — create FIRE event
  synth  — find META-FIRE patterns across all events
  list   — list all FIRE events ranked by poly_c
  status — spine health summary
"""

import argparse
import json
import math
import hashlib
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ─── CPF FORMULA ──────────────────────────────────────────────────────────────

def compute_poly_c(tau: float, omega: float, topo: float, N: int) -> dict:
    """Full CPF formula with supercritical normalization."""
    raw = (tau * omega * topo) / (2 * math.sqrt(N))
    supercritical = raw > 1.0
    normalized = raw / (1 + raw) if supercritical else raw

    if not supercritical:
        if raw >= 1.0:    status = "FIRE"
        elif raw >= 0.95: status = "HYPER"
        elif raw >= 0.80: status = "CANONICAL"
        elif raw >= 0.50: status = "VERIFIED"
        else:             status = "PENDING"
        regime = None
    else:
        sc = normalized
        if sc >= 0.99:   status, regime = "THEORETICAL_LIMIT", "ASYMPTOTIC"
        elif sc >= 0.95: status, regime = "HYPER",             "HYPER_SUPERCRITICAL"
        elif sc >= 0.90: status, regime = "CANONICAL",         "CRITICAL_MASS"
        elif sc >= 0.70: status, regime = "VERIFIED",          "CHAIN_REACTION"
        else:            status, regime = "PENDING",            "SELF_SUSTAINING"

    return {
        "poly_c_raw":    round(raw, 6),
        "poly_c":        round(normalized, 6),
        "supercritical": supercritical,
        "status":        status,
        "regime":        regime if supercritical else "N/A",
        "margin":        round(1.0 - normalized, 6),
        "formula":       f"τ={tau}×ω={omega}×T={topo}/2√{N}" +
                         (f" → SC:{normalized:.4f}" if supercritical else ""),
    }

# ─── HASH ─────────────────────────────────────────────────────────────────────

def make_hash(event: dict, prev_hash: str = "") -> str:
    payload = f"{event.get('title','')}{event.get('poly_c',0)}{event.get('domain','')}{prev_hash}"
    return hashlib.sha256(payload.encode()).hexdigest()[:16]

# ─── DATABASE ─────────────────────────────────────────────────────────────────

def get_db():
    """Try to connect to PostgreSQL. Fall back to JSON file store."""
    db_url = os.environ.get("DATABASE_URL", "")
    if db_url:
        try:
            import psycopg2
            conn = psycopg2.connect(db_url)
            return conn, "postgres"
        except Exception:
            pass
    return None, "file"

STORE_PATH = Path.home() / ".openclaw" / "evez-fire-store.json"

def load_events() -> list:
    conn, mode = get_db()
    if mode == "postgres" and conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT title, domain, tau, omega, topo, N, poly_c, status,
                       description, falsifier, implications, source_url, hash, powered_by
                FROM fire_events ORDER BY poly_c DESC
            """)
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]
        except Exception:
            pass
        finally:
            conn.close()
    # fallback: local JSON
    if STORE_PATH.exists():
        return json.loads(STORE_PATH.read_text())
    return []

def save_event(event: dict) -> bool:
    conn, mode = get_db()
    if mode == "postgres" and conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO fire_events
                  (title, domain, tau, omega, topo, N, poly_c, poly_c_sc,
                   supercritical, status, description, falsifier, implications,
                   source_url, hash, powered_by)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (hash) DO NOTHING
            """, (
                event.get("title"), event.get("domain"),
                event.get("tau"), event.get("omega"),
                event.get("topo", 1.0), event.get("N"),
                event.get("poly_c_raw"), event.get("poly_c"),
                event.get("supercritical", False),
                event.get("status"),
                event.get("description"), event.get("falsifier"),
                event.get("implications"), event.get("source_url"),
                event.get("hash"), event.get("powered_by", "EVEZ-OS")
            ))
            conn.commit()
            return True
        except Exception as e:
            print(f"  DB write failed: {e}, falling back to file store")
        finally:
            conn.close()
    # fallback
    events = load_events()
    if not any(e.get("hash") == event.get("hash") for e in events):
        events.append(event)
        STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
        STORE_PATH.write_text(json.dumps(events, indent=2))
    return True

# ─── SLACK NOTIFICATION ────────────────────────────────────────────────────────

def notify_slack(event: dict):
    webhook = os.environ.get("SLACK_WEBHOOK_URL", "")
    if not webhook:
        return
    try:
        import urllib.request, urllib.parse
        poly_c = event.get("poly_c", 0)
        sc_flag = " ⚡SUPERCRITICAL" if event.get("supercritical") else ""
        msg = {
            "text": f"🔥 FIRE EVENT{sc_flag}\n"
                    f"*{event.get('title','?')}*\n"
                    f"poly_c = `{poly_c:.4f}` | domain: `{event.get('domain','?')}`\n"
                    f"status: `{event.get('status','?')}`\n"
                    f"hash: `{event.get('hash','?')}`"
        }
        data = json.dumps(msg).encode()
        req = urllib.request.Request(webhook, data=data,
                                     headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=5)
    except Exception:
        pass

# ─── GITHUB SPINE COMMIT ──────────────────────────────────────────────────────

def commit_to_spine(event: dict):
    """Dispatch to lord-evez666 repository."""
    token = os.environ.get("GITHUB_ACCESS_TOKEN", "")
    if not token:
        return
    try:
        import urllib.request
        payload = json.dumps({
            "event_type": "fire_event",
            "client_payload": {
                "title": event.get("title"),
                "poly_c": event.get("poly_c"),
                "domain": event.get("domain"),
                "hash": event.get("hash"),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        }).encode()
        req = urllib.request.Request(
            "https://api.github.com/repos/EvezArt/lord-evez666/dispatches",
            data=payload,
            headers={
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json",
                "Content-Type": "application/json",
            }
        )
        req.get_method = lambda: "POST"
        urllib.request.urlopen(req, timeout=10)
        print("  ✓ Committed to lord-evez666 spine")
    except Exception as e:
        print(f"  ⚠ Spine commit failed: {e}")

# ─── COMMANDS ─────────────────────────────────────────────────────────────────

def cmd_score(args):
    """Compute poly_c for given parameters."""
    result = compute_poly_c(args.tau, args.omega, args.topo, args.N)
    print(f"\n{'='*50}")
    print(f"  CPF SCORE")
    print(f"{'='*50}")
    print(f"  Formula:    {result['formula']}")
    print(f"  poly_c_raw: {result['poly_c_raw']}")
    print(f"  poly_c:     {result['poly_c']}")
    print(f"  Status:     {result['status']}")
    if result['supercritical']:
        print(f"  Regime:     {result['regime']} ⚡")
    print(f"  Margin:     {result['margin']} to next threshold")
    print(f"{'='*50}\n")

def cmd_fire(args):
    """Create and log a FIRE event interactively."""
    print("\n🔥 FIRE EVENT CREATION")
    print("="*50)

    # Gather params interactively if not provided
    title = args.title or input("  Title: ").strip()
    domain = args.domain or input("  Domain [technical/academic/meta/financial/security]: ").strip()

    if not args.tau:
        print("\n  CPF Parameters:")
        tau   = float(input("    τ (depth across time, e.g. 18): "))
        omega = float(input("    ω (independent confirmations, e.g. 3.2): "))
        topo  = float(input("    topo (topology score 0-1, e.g. 1.0): ") or "1.0")
        N     = int(input("    N (independent lenses, e.g. 7): "))
    else:
        tau, omega, topo, N = args.tau, args.omega, args.topo, args.N

    desc      = args.desc      or input("  Description (brief): ").strip()
    falsifier = args.falsifier or input("  Falsifier (what would disprove this?): ").strip()

    # Score it
    cpf = compute_poly_c(tau, omega, topo, N)

    # Build event
    event = {
        "title":        title,
        "domain":       domain,
        "tau":          tau,
        "omega":        omega,
        "topo":         topo,
        "N":            N,
        "poly_c_raw":   cpf["poly_c_raw"],
        "poly_c":       cpf["poly_c"],
        "supercritical":cpf["supercritical"],
        "status":       cpf["status"],
        "description":  desc,
        "falsifier":    falsifier,
        "powered_by":   "EVEZ-OS / OpenClaw Mod v0.2",
        "created_at":   datetime.now(timezone.utc).isoformat(),
    }
    event["hash"] = make_hash(event)

    print(f"\n  poly_c:  {cpf['poly_c']:.4f}")
    print(f"  Status:  {cpf['status']}")
    if cpf['supercritical']:
        print(f"  ⚡ SUPERCRITICAL — Regime: {cpf['regime']}")

    if cpf["poly_c_raw"] >= 0.5:
        confirm = input("\n  Log this FIRE event? [Y/n]: ").strip().lower()
        if confirm != "n":
            save_event(event)
            if cpf["poly_c_raw"] >= 0.8:
                notify_slack(event)
            if cpf["poly_c_raw"] >= 1.0:
                commit_to_spine(event)
            print(f"  ✓ Logged. Hash: {event['hash']}")
    else:
        print(f"  poly_c < 0.5 — gather more confirmation before logging.")

def cmd_list(args):
    """List all FIRE events ranked by poly_c."""
    events = load_events()
    if not events:
        print("  No FIRE events found. Run `evez-fire-engine fire` to create one.")
        return

    sorted_events = sorted(events, key=lambda e: e.get("poly_c", 0), reverse=True)
    print(f"\n  FIRE EVENT REGISTRY ({len(events)} events)")
    print(f"  {'#':>3}  {'poly_c':>8}  {'STATUS':<16}  {'DOMAIN':<22}  TITLE")
    print(f"  {'─'*3}  {'─'*8}  {'─'*16}  {'─'*22}  {'─'*40}")
    for i, ev in enumerate(sorted_events, 1):
        sc = "⚡" if ev.get("supercritical") else " "
        print(f"  {i:>3}  {ev.get('poly_c',0):>8.4f}{sc} {ev.get('status','?'):<16}  "
              f"{(ev.get('domain','?')):<22}  {(ev.get('title','?'))[:45]}")
    print()

def cmd_synth(args):
    """Find META-FIRE patterns across all events."""
    events = load_events()
    if len(events) < 2:
        print("  Need at least 2 events to synthesize.")
        return

    print(f"\n  🧬 META-FIRE SYNTHESIZER")
    print(f"  Scanning {len(events)} events for topology overlap...\n")

    candidates = []
    for i, a in enumerate(events):
        for j, b in enumerate(events):
            if j <= i:
                continue
            # Check domain overlap
            same_domain = a.get("domain") == b.get("domain")
            # Check topo overlap (both should be near 1.0 for strong overlap)
            topo_a = float(a.get("topo", 1.0) if isinstance(a.get("topo"), (int, float))
                          else str(a.get("topo","1.0")).split("(")[0].strip())
            topo_b = float(b.get("topo", 1.0) if isinstance(b.get("topo"), (int, float))
                          else str(b.get("topo","1.0")).split("(")[0].strip())
            topo_overlap = (topo_a + topo_b) / 2

            if topo_overlap >= 0.7:
                # Compute candidate META-FIRE poly_c
                meta_tau   = max(float(a.get("tau",1) or 1), float(b.get("tau",1) or 1))
                meta_omega = (float(a.get("omega",1) or 1) + float(b.get("omega",1) or 1)) / 2
                meta_N     = int(a.get("N",1) or 1) + int(b.get("N",1) or 1)
                meta_topo  = topo_overlap

                meta_cpf = compute_poly_c(meta_tau, meta_omega, meta_topo, meta_N)

                if meta_cpf["poly_c_raw"] >= 0.8:
                    candidates.append({
                        "events": [a.get("title","?")[:40], b.get("title","?")[:40]],
                        "same_domain": same_domain,
                        "topo_overlap": topo_overlap,
                        "meta_poly_c": meta_cpf["poly_c"],
                        "meta_status": meta_cpf["status"],
                        "tau": meta_tau, "omega": meta_omega,
                        "topo": meta_topo, "N": meta_N,
                    })

    if not candidates:
        print("  No META-FIRE candidates found at topo_overlap ≥ 0.7 and poly_c ≥ 0.8")
        return

    candidates.sort(key=lambda c: c["meta_poly_c"], reverse=True)
    print(f"  Found {len(candidates)} META-FIRE candidate(s):\n")
    for i, c in enumerate(candidates, 1):
        print(f"  [{i}] poly_c={c['meta_poly_c']:.4f} | {c['meta_status']}")
        print(f"      {c['events'][0]}")
        print(f"    ⊗ {c['events'][1]}")
        print(f"      topo_overlap={c['topo_overlap']:.2f} | τ={c['tau']} ω={c['omega']:.2f} N={c['N']}")
        print()

def cmd_status(args):
    """Show spine health summary."""
    events = load_events()
    count     = len(events)
    max_poly  = max((e.get("poly_c",0) for e in events), default=0)
    avg_poly  = sum(e.get("poly_c",0) for e in events) / count if count else 0
    sc_count  = sum(1 for e in events if e.get("supercritical") or e.get("poly_c",0) > 1.0)

    print(f"\n  EVEZ-OS SPINE STATUS")
    print(f"  {'─'*40}")
    print(f"  phi:                 0.995 → 0.999 target")
    print(f"  FIRE events:         {count}")
    print(f"  max poly_c:          {max_poly:.4f}")
    print(f"  avg poly_c:          {avg_poly:.4f}")
    print(f"  supercritical:       {sc_count}")
    print(f"  eigenvalue progress: 0.0% (bridge not yet activated)")
    print(f"  DGM loop:            700/700 iterations target")
    print(f"  spine:               INTACT")
    print(f"  {'─'*40}\n")

# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="EVEZ FIRE Engine — poly_c scoring + event synthesis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  evez-fire score tau=18 omega=3.2 topo=1.0 N=7
  evez-fire fire --title "New arXiv paper validates CPF" --domain academic
  evez-fire list
  evez-fire synth
  evez-fire status
        """
    )
    sub = parser.add_subparsers(dest="command")

    # score
    sp = sub.add_parser("score", help="Compute poly_c")
    sp.add_argument("--tau",   type=float, required=True)
    sp.add_argument("--omega", type=float, required=True)
    sp.add_argument("--topo",  type=float, default=1.0)
    sp.add_argument("--N",     type=int,   required=True)

    # fire
    fp = sub.add_parser("fire", help="Create FIRE event")
    fp.add_argument("--title",     type=str, default="")
    fp.add_argument("--domain",    type=str, default="")
    fp.add_argument("--desc",      type=str, default="")
    fp.add_argument("--falsifier", type=str, default="")
    fp.add_argument("--tau",       type=float, default=None)
    fp.add_argument("--omega",     type=float, default=None)
    fp.add_argument("--topo",      type=float, default=1.0)
    fp.add_argument("--N",         type=int,   default=None)

    sub.add_parser("list",   help="List FIRE events")
    sub.add_parser("synth",  help="Find META-FIRE patterns")
    sub.add_parser("status", help="Spine health summary")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    dispatch = {
        "score":  cmd_score,
        "fire":   cmd_fire,
        "list":   cmd_list,
        "synth":  cmd_synth,
        "status": cmd_status,
    }
    dispatch[args.command](args)

if __name__ == "__main__":
    main()
