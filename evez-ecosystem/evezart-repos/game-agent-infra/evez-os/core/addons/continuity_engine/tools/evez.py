#!/usr/bin/env python3
"""
EVEZ Continuity Engine CLI
- append FSC cycles to spine/EVENT_SPINE.jsonl
- validate against schemas/fsc_schema.json
- generate quick diagrams (ASCII + Mermaid + DOT)

Usage:
  python tools/evez.py init
  python tools/evez.py cycle --anomaly "..." --ring R4
  python tools/evez.py diagram
"""
import argparse, json, os, sys, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPINE = ROOT / "spine" / "EVENT_SPINE.jsonl"
SCHEMA = ROOT / "schemas" / "fsc_schema.json"

def utc_now():
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat() + "Z"

def load_schema():
    return json.loads(SCHEMA.read_text(encoding="utf-8"))

def ensure_files():
    SPINE.parent.mkdir(parents=True, exist_ok=True)
    if not SPINE.exists():
        SPINE.write_text("# Append one JSON object per cycle. Keep immutable.\n", encoding="utf-8")

def parse_jsonl(path: Path):
    items = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        items.append(json.loads(line))
    return items

def write_jsonl_append(path: Path, obj: dict):
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")

def validate_minimal(obj: dict):
    # Lightweight validation (no external deps): required top-level keys
    schema = load_schema()
    req = schema.get("required", [])
    missing = [k for k in req if k not in obj]
    if missing:
        raise SystemExit(f"Missing required keys: {missing}")
    return True

def make_cycle(args):
    ensure_files()
    cycle_id = args.cycle_id or f"CYCLE-{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d-%H%M%S')}"
    obj = {
        "cycle_id": cycle_id,
        "timestamp": utc_now(),
        "anomaly": args.anomaly,
        "ring_estimate": args.ring or "unknown",
        "controlled_reduction": {
            "dimensionality_reduction": args.dim_red or "TBD",
            "latency_pressure": args.latency or "TBD",
            "abstraction_stripping": args.strip or "TBD",
            "constraint_tightening": args.tighten or "TBD",
        },
        "Sigma_f": args.sigma_f or [],
        "CS": args.cs or [],
        "PS": args.ps or [],
        "Omega": args.omega or "",
        "tests": args.tests or [],
        "results": args.results or [],
        "measures": {
            "delta_surprise_residue": args.dsr if args.dsr is not None else 0,
            "delta_compression": args.dc if args.dc is not None else 0,
            "stability": args.stability if args.stability is not None else 0,
            "transfer": args.transfer if args.transfer is not None else 0,
            "boundary_clarity": args.boundary if args.boundary is not None else 0,
            "exploit_resistance": args.exploit if args.exploit is not None else 0,
        },
        "provenance": args.provenance or [],
    }
    validate_minimal(obj)
    write_jsonl_append(SPINE, obj)
    print(f"Appended {cycle_id} to {SPINE}")

def diagram(args):
    ensure_files()
    cycles = parse_jsonl(SPINE)
    print("=== ASCII QUICKVIEW (latest 5 cycles) ===")
    for c in cycles[-5:]:
        print(f"- {c.get('cycle_id')} | {c.get('ring_estimate')} | {c.get('anomaly')[:80]}")
        omega = c.get("Omega","")
        if omega:
            print(f"  Ω: {omega[:120]}")
        sf = c.get("Sigma_f", [])
        if sf:
            print(f"  Σf: {', '.join(sf[:6])}{'...' if len(sf)>6 else ''}")
    # Mermaid and DOT templates
    mermaid = ["graph TD", "  classDef ring fill:#fefefe,stroke:#aaa,stroke-width:1px"]
    prev = None
    for c in cycles[-7:]:
        node = c.get("cycle_id","?").replace(" ","_")
        label = (c.get("ring_estimate","unknown") + "\\n" + c.get("anomaly","")).replace('"',"'")
        mermaid.append(f'  {node}["{label}"]:::ring')
        if prev:
            mermaid.append(f"  {prev} --> {node}")
        prev = node
    out_mmd = ROOT / "docs" / "event_spine.mmd"
    out_mmd.write_text("\\n".join(mermaid) + "\\n", encoding="utf-8")
    dot = ["digraph spine {", "  rankdir=LR;", '  node [shape=box];']
    prev = None
    for c in cycles[-7:]:
        node = c.get("cycle_id","?").replace("-","_").replace(" ","_")
        label = (c.get("ring_estimate","unknown") + "\\n" + c.get("anomaly","")[:64]).replace('"',"'")
        dot.append(f'  {node} [label="{label}"];')
        if prev:
            dot.append(f"  {prev} -> {node};")
        prev = node
    dot.append("}")
    out_dot = ROOT / "docs" / "event_spine.dot"
    out_dot.write_text("\\n".join(dot) + "\\n", encoding="utf-8")
    print(f"Wrote {out_mmd} and {out_dot}")

def init(args):
    ensure_files()
    print("Initialized spine. Next: python tools/evez.py cycle --anomaly \"...\" --ring R4")

def main():
    p = argparse.ArgumentParser()
    sp = p.add_subparsers(dest="cmd", required=True)

    p_init = sp.add_parser("init")
    p_init.set_defaults(func=init)

    p_cycle = sp.add_parser("cycle")
    p_cycle.add_argument("--cycle-id", dest="cycle_id")
    p_cycle.add_argument("--anomaly", required=True)
    p_cycle.add_argument("--ring", default="unknown")
    p_cycle.add_argument("--dim-red")
    p_cycle.add_argument("--latency")
    p_cycle.add_argument("--strip")
    p_cycle.add_argument("--tighten")
    p_cycle.add_argument("--sigma-f", nargs="*")
    p_cycle.add_argument("--cs", nargs="*")
    p_cycle.add_argument("--ps", nargs="*")
    p_cycle.add_argument("--omega")
    p_cycle.add_argument("--tests", nargs="*")
    p_cycle.add_argument("--results", nargs="*")
    p_cycle.add_argument("--provenance", nargs="*")
    p_cycle.add_argument("--dsr", type=float)
    p_cycle.add_argument("--dc", type=float)
    p_cycle.add_argument("--stability", type=float)
    p_cycle.add_argument("--transfer", type=float)
    p_cycle.add_argument("--boundary", type=float)
    p_cycle.add_argument("--exploit", type=float)
    p_cycle.set_defaults(func=make_cycle)

    p_diag = sp.add_parser("diagram")
    p_diag.set_defaults(func=diagram)

    args = p.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
