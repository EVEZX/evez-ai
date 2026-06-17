#!/usr/bin/env python3
"""EVEZ Continuity Engine CLI

Core:
  - Append FSC cycles to spine/EVENT_SPINE.jsonl (append-only)
  - Lightweight validation against schemas/fsc_schema.json
  - Generate quick diagrams (ASCII + Mermaid + DOT) into docs/

ARG mode:
  - Append diegetic drops to spine/ARG_SPINE.jsonl (append-only)
  - Narrate tail of the ARG spine

Usage:
  python tools/evez.py init
  python tools/evez.py cycle --anomaly "..." --ring R4
  python tools/evez.py diagram
  python tools/evez.py arg-init
  python tools/evez.py arg-drop --lobby DNS --tag "xray" --msg "..." --truth-plane pending
  python tools/evez.py arg-narrate --tail 20

FX:
  python tools/evez.py fx-snapshot --base USD --symbols EUR,GBP,JPY --append-spine
"""

import argparse
import datetime
import json
import time
import funding as funding_tool
import fx as fx_tool
import cheat as cheat_tool
import probe as probe_tool
import claim as claim_tool
import lint as lint_tool
import play_engine
import mission as mission_tool
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# --- Core spine --------------------------------------------------------------
SPINE = ROOT / "spine" / "EVENT_SPINE.jsonl"
SCHEMA = ROOT / "schemas" / "fsc_schema.json"

# --- ARG spine ---------------------------------------------------------------
ARG_SPINE = ROOT / "spine" / "ARG_SPINE.jsonl"
ARG_SCHEMA = ROOT / "schemas" / "arg_schema.json"


def utc_now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat() + "Z"


def ensure_file(path: Path, header: str | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(header or "", encoding="utf-8")


def parse_jsonl(path: Path):
    items = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        items.append(json.loads(line))
    return items


def write_jsonl_append(path: Path, obj: dict) -> None:
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def load_schema(path: Path):
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def validate_required(obj: dict, required_keys: list[str], label: str = "entry") -> None:
    missing = [k for k in required_keys if k not in obj]
    if missing:
        raise SystemExit(f"{label} missing required keys: {missing}")


# --- Core commands -----------------------------------------------------------

def cmd_init(_args):
    ensure_file(SPINE, header="# Append one JSON object per cycle. Keep immutable.\n")
    print("Initialized EVENT_SPINE.jsonl")


def cmd_cycle(args):
    ensure_file(SPINE, header="# Append one JSON object per cycle. Keep immutable.\n")
    schema = load_schema(SCHEMA)
    required = schema.get("required", ["cycle_id", "timestamp", "anomaly", "ring_estimate", "measures"]) or []

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


    # normalize fields for downstream tooling
    obj.setdefault("type", "fsc_cycle")
    if "Sigma_f" in obj and "sigma_f" not in obj:
        obj["sigma_f"] = obj["Sigma_f"]
    if "Omega" in obj and "omega" not in obj:
        obj["omega"] = obj["Omega"]
    if "CS" in obj and "collapse_sequence" not in obj:
        obj["collapse_sequence"] = obj["CS"]
    if "PS" in obj and "preservation_set" not in obj:
        obj["preservation_set"] = obj["PS"]

    validate_required(obj, required, label="FSC cycle")
    write_jsonl_append(SPINE, obj)
    print(f"Appended {cycle_id} to spine/EVENT_SPINE.jsonl")


def cmd_diagram(_args):
    ensure_file(SPINE, header="# Append one JSON object per cycle. Keep immutable.\n")
    cycles = parse_jsonl(SPINE)

    print("=== ASCII QUICKVIEW (latest 5 cycles) ===")
    for c in cycles[-5:]:
        print(f"- {c.get('cycle_id')} | {c.get('ring_estimate')} | {str(c.get('anomaly',''))[:80]}")
        omega = c.get("Omega", "")
        if omega:
            print(f"  Ω: {omega[:120]}")
        sf = c.get("Sigma_f", [])
        if sf:
            print(f"  Σf: {', '.join(sf[:6])}{'...' if len(sf) > 6 else ''}")

    # Mermaid timeline
    mermaid = ["graph TD", "  classDef ring fill:#fefefe,stroke:#aaa,stroke-width:1px"]
    prev = None
    for c in cycles[-7:]:
        node = str(c.get("cycle_id", "?")).replace(" ", "_")
        label = (str(c.get("ring_estimate", "unknown")) + "\\n" + str(c.get("anomaly", ""))).replace('"', "'")
        mermaid.append(f'  {node}["{label}"]:::ring')
        if prev:
            mermaid.append(f"  {prev} --> {node}")
        prev = node
    (ROOT / "docs").mkdir(parents=True, exist_ok=True)
    out_mmd = ROOT / "docs" / "event_spine.mmd"
    out_mmd.write_text("\n".join(mermaid) + "\n", encoding="utf-8")

    # DOT timeline
    dot = ["digraph spine {", "  rankdir=LR;", "  node [shape=box];"]
    prev = None
    for c in cycles[-7:]:
        node = str(c.get("cycle_id", "?")).replace("-", "_").replace(" ", "_")
        label = (str(c.get("ring_estimate", "unknown")) + "\\n" + str(c.get("anomaly", ""))[:64]).replace('"', "'")
        dot.append(f'  {node} [label="{label}"];')
        if prev:
            dot.append(f"  {prev} -> {node};")
        prev = node
    dot.append("}")
    out_dot = ROOT / "docs" / "event_spine.dot"
    out_dot.write_text("\n".join(dot) + "\n", encoding="utf-8")

    print(f"Wrote docs/event_spine.mmd and docs/event_spine.dot")


# --- ARG commands ------------------------------------------------------------

def cmd_arg_init(_args):
    ensure_file(ARG_SPINE)
    print("Initialized ARG spine at spine/ARG_SPINE.jsonl")


def cmd_arg_drop(args):
    ensure_file(ARG_SPINE)
    entry = {
        "ts": utc_now(),
        "kind": args.kind,
        "lobby": args.lobby,
        "severity": int(args.severity),
        "tag": args.tag,
        "msg": args.msg,
        "truth_plane": args.truth_plane,
    }

    if args.provenance:
        try:
            entry["provenance"] = json.loads(args.provenance)
        except Exception:
            entry["provenance"] = {"raw": args.provenance}
    if args.links:
        entry["links"] = args.links

    schema = load_schema(ARG_SCHEMA)
    required = schema.get("required", ["ts", "kind", "lobby", "severity", "tag", "msg", "truth_plane"]) or []
    validate_required(entry, required, label="ARG drop")

    write_jsonl_append(ARG_SPINE, entry)
    print(f"Wrote ARG drop: {entry['lobby']}:{entry['tag']} severity={entry['severity']} plane={entry['truth_plane']}")


def cmd_arg_narrate(args):
    ensure_file(ARG_SPINE)
    lines = [ln for ln in ARG_SPINE.read_text(encoding="utf-8").splitlines() if ln.strip()]
    tail = int(args.tail) if args.tail is not None else 20
    chunk = lines[-tail:] if tail > 0 else lines

    for ln in chunk:
        try:
            e = json.loads(ln)
        except Exception:
            print(ln)
            continue
        lobby = e.get("lobby", "SELF")
        tag = e.get("tag", "")
        sev = e.get("severity", 0)
        plane = str(e.get("truth_plane", "pending")).upper()
        msg = e.get("msg", "")
        print(f"[{plane}] ({lobby}) <{tag}> :: {msg}  [sev={sev}]")



def cmd_funding_init(args):
    # delegate to tools/funding.py CLI
    funding_tool.main_from_evez(["init"])


def cmd_funding_claim(args):
    argv = ["claim",
            "--kind", args.kind,
            "--truth-plane", args.truth_plane]
    if args.claim_id:
        argv += ["--claim-id", args.claim_id]
    if args.title:
        argv += ["--title", args.title]
    if args.statement:
        argv += ["--statement", args.statement]
    if args.metric:
        argv += ["--metric", args.metric]
    if args.value is not None:
        argv += ["--value", str(args.value)]
    if args.unit:
        argv += ["--unit", args.unit]
    if args.period:
        argv += ["--period", args.period]
    if args.confidence is not None:
        argv += ["--confidence", str(args.confidence)]
    if args.falsifier:
        argv += ["--falsifier", args.falsifier]
    if args.source:
        argv += ["--source", args.source]
    if args.calc:
        argv += ["--calc", args.calc]
    for link in (args.links or []):
        argv += ["--link", link]
    funding_tool.main_from_evez(argv)


def cmd_funding_render(args):
    funding_tool.main_from_evez(["render"])


# --- FX commands -------------------------------------------------------------

def cmd_fx_snapshot(args):
    symbols = [s.strip() for s in (args.symbols or "").split(",") if s.strip()]
    if not symbols:
        symbols = ["EUR", "USD", "GBP", "JPY"]
    out = fx_tool.snapshot(base=args.base, symbols=symbols, append_spine=args.append_spine)
    print(str(out))
def cmd_cheat(args):
    # Dev-only test ledger cheats (never real currency).
    action = args.action
    currency = args.currency
    memo = getattr(args, "memo", None)
    amount = getattr(args, "amount", None)

    if action == "deposit":
        out = cheat_tool.deposit(currency=currency, amount=amount, memo=memo)
    elif action == "inf":
        out = cheat_tool.set_infinite(currency=currency, amount=amount, memo=memo or "inf$$")
    elif action == "reset":
        out = cheat_tool.reset(currency=currency, memo=memo or "reset$$")
    else:
        raise SystemExit(f"Unknown cheat action: {action}")

    if args.append_spine:
        funding_tool.append_entry({
            "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds") + "Z",
            "type": "cheat",
            "cheat_code": action,
            "currency": currency,
            "amount": float(amount) if amount is not None else None,
            "memo": memo or "",
            "ledger_path": out.get("ledger"),
            "tx_hash": out.get("tx_hash"),
            "balance": out.get("balance"),
            "env": __import__("os").environ.get("EVEZ_ENV", ""),
            "truth_plane": "final",
        })

    print(json.dumps(out, indent=2))




def cmd_probe(args):
    kind = args.kind
    append = args.append_spine
    if kind == "dns":
        ev = probe_tool.probe_dns(args.name, rrtype=args.rrtype, resolver=args.resolver, timeout_s=args.timeout)
    elif kind == "http":
        ev = probe_tool.probe_http(args.url, method=args.method, timeout_s=args.timeout)
    elif kind == "tls":
        ev = probe_tool.probe_tls(args.host, port=args.port, server_name=args.server_name, timeout_s=args.timeout)
    elif kind == "ping":
        ev = probe_tool.probe_ping(args.host, count=args.count, timeout_s=args.timeout)
    else:
        raise SystemExit(f"Unknown probe kind: {kind}")
    if getattr(args, "vantage", None):
        ev["vantage_id"] = args.vantage
    probe_tool.run_and_maybe_append(ev, append_spine=append)
    print(json.dumps(ev, indent=2, ensure_ascii=False))


def cmd_trigger(args):
    """Analyze existing spine probe events and append mission events for disagreements."""
    ensure_file(SPINE, header="# Append one JSON object per cycle. Keep immutable.\n")
    events = parse_jsonl(SPINE)
    missions = mission_tool.find_disagreements(events, min_vantages=args.min_vantages)
    existing = mission_tool.mission_trace_ids(events)
    new = mission_tool.filter_new_missions(missions, existing)
    for m in new:
        write_jsonl_append(SPINE, m)

    # Optional: auto-spawn a play episode for each newly appended disagreement mission.
    spawned = 0
    if args.spawn_play and new:
        out_dir = (ROOT / (args.out_dir or "docs")).resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
        latest_path = (ROOT / (args.latest or "docs/PLAYTHROUGH_LATEST.md")).resolve()

        def seed_from_trace(trace_id: str) -> int:
            # Mission trace IDs are hex-ish; derive a deterministic seed.
            try:
                return int(str(trace_id).lstrip("M")[:8], 16)
            except Exception:
                return 0

        for m in new:
            seed = args.seed if args.seed is not None else seed_from_trace(m.get("trace_id", ""))
            episode = play_engine.run_episode(seed=seed, steps=args.steps, mission=m)
            mission_tid = str(m.get("trace_id"))
            mission_out = out_dir / f"PLAYTHROUGH_MISSION_{mission_tid}.md"
            play_engine.write_playthrough(mission_out, episode)
            # Also update the latest pointer.
            play_engine.write_playthrough(latest_path, episode)
            spawned += 1

    out = {"found": len(missions), "appended": len(new)}
    if args.spawn_play:
        out["spawned_episodes"] = spawned
    print(json.dumps(out, indent=2, ensure_ascii=False))


def cmd_sentinel(args):
    """Continuously run `trigger` to spawn missions (and optionally play episodes) as disagreements appear."""
    loops = 0
    while True:
        # Reuse cmd_trigger by constructing a lightweight args object.
        class A:
            pass
        a = A()
        a.min_vantages = args.min_vantages
        a.spawn_play = args.spawn_play
        a.steps = args.steps
        a.seed = args.seed
        a.out_dir = args.out_dir
        a.latest = args.latest
        cmd_trigger(a)
        loops += 1
        if args.max_loops and loops >= args.max_loops:
            break
        time.sleep(max(1, int(args.interval)))

def cmd_claim(args):
    ev = claim_tool.append_claim(
        text=args.text,
        truth_plane=args.truth_plane,
        provenance=args.provenance,
        falsifier=args.falsifier,
        confidence=args.confidence,
        scope=args.scope,
        tags=args.tags,
    )
    print(json.dumps(ev, indent=2, ensure_ascii=False))

def cmd_lint(args):
    ok, bad = lint_tool.lint(limit=args.limit)
    out = {"ok": len(ok), "violations": len(bad), "bad": bad[:50]}
    print(json.dumps(out, indent=2, ensure_ascii=False))
    if bad and args.fail:
        raise SystemExit(2)

def cmd_watch(args):
    # minimal watch: repeatedly run a probe and append to spine
    kind = args.kind
    interval = args.interval
    jitter = args.jitter
    def run_once():
        if kind == "dns":
            ev = probe_tool.probe_dns(args.name, rrtype=args.rrtype, resolver=args.resolver, timeout_s=args.timeout)
        elif kind == "http":
            ev = probe_tool.probe_http(args.url, method=args.method, timeout_s=args.timeout)
        elif kind == "tls":
            ev = probe_tool.probe_tls(args.host, port=args.port, server_name=args.server_name, timeout_s=args.timeout)
        elif kind == "ping":
            ev = probe_tool.probe_ping(args.host, count=args.count, timeout_s=args.timeout)
        else:
            raise SystemExit(f"Unknown probe kind: {kind}")
        if getattr(args, "vantage", None):
            ev["vantage_id"] = args.vantage
        probe_tool.run_and_maybe_append(ev, append_spine=True)
        print(f"[{ev.get('ts')}] {ev.get('kind')} -> {ev.get('target')}")
        return ev
    import time as _t
    while True:
        run_once()
        _t.sleep(max(1, interval + (jitter if jitter else 0)))



# --- Play (projection generator) --------------------------------------------

def cmd_play(args):
    """Generate a narrated projection while appending spine-grade play events.

    In --loop mode, you can optionally run the disagreement trigger each episode and
    ground the next episode in the next *unconsumed* mission.disagreement event.
    """
    out_path = (ROOT / (args.out or "docs/PLAYTHROUGH_LATEST.md")).resolve()
    seed = args.seed if args.seed is not None else 0
    steps = args.steps
    loop = args.loop
    max_episodes = args.max_episodes
    auto_trigger = getattr(args, "auto_trigger", False)
    min_vantages = getattr(args, "min_vantages", 2)

    def seed_from_trace(trace_id: str) -> int:
        try:
            return int(str(trace_id).lstrip("M")[:8], 16)
        except Exception:
            return seed

    def append_new_missions() -> int:
        # Same logic as `trigger`, but silent: append new mission.disagreement events.
        ensure_file(SPINE, header="# Append one JSON object per cycle. Keep immutable.\n")
        events = parse_jsonl(SPINE)
        missions = mission_tool.find_disagreements(events, min_vantages=min_vantages)
        existing = mission_tool.mission_trace_ids(events)
        new = mission_tool.filter_new_missions(missions, existing)
        for m in new:
            write_jsonl_append(SPINE, m)
        return len(new)

    def next_unconsumed_mission():
        events = parse_jsonl(SPINE)
        consumed = set()
        for ev in events:
            if ev.get("kind") == "play.episode_start" and ev.get("triggered_by"):
                consumed.add(str(ev.get("triggered_by")))
            if ev.get("kind") == "play.step" and ev.get("source_mission"):
                consumed.add(str(ev.get("source_mission")))
        for ev in events:
            if ev.get("kind") == "mission.disagreement" and ev.get("trace_id"):
                if str(ev["trace_id"]) not in consumed:
                    return ev
        return None

    def one_episode(ep_seed: int, mission=None):
        episode = play_engine.run_episode(seed=ep_seed, steps=steps, mission=mission)
        play_engine.write_playthrough(out_path, episode)
        if mission and mission.get("trace_id"):
            mission_out = out_path.parent / f"PLAYTHROUGH_MISSION_{mission['trace_id']}.md"
            play_engine.write_playthrough(mission_out, episode)
        trig = f"  |  triggered_by={mission.get('trace_id')}" if mission else ""
        print(
            f"Wrote projection to {out_path.relative_to(ROOT)}  |  episode_id={episode['episode_id']}  |  steps={steps}{trig}"
        )

    if not loop:
        mission = None
        if auto_trigger:
            append_new_missions()
            mission = next_unconsumed_mission()
            if mission and args.seed is None:
                seed = seed_from_trace(mission.get("trace_id"))
        one_episode(seed, mission=mission)
        return

    # Loop mode: keep generating new episodes until Ctrl-C, optionally capped.
    n = 0
    try:
        while True:
            n += 1
            mission = None
            ep_seed = seed + n - 1

            if auto_trigger:
                append_new_missions()
                mission = next_unconsumed_mission()
                if mission:
                    ep_seed = seed_from_trace(mission.get("trace_id"))

            one_episode(ep_seed, mission=mission)

            if max_episodes and n >= max_episodes:
                break
    except KeyboardInterrupt:
        print("\nLoop interrupted by user.")


def build_cli():
    p = argparse.ArgumentParser(description="EVEZ: event spine + FSC + ARG tooling")
    sp = p.add_subparsers(dest="cmd", required=True)

    # Core
    a = sp.add_parser("init", help="initialize EVENT_SPINE.jsonl")
    a.set_defaults(func=cmd_init)

    a = sp.add_parser("cycle", help="append one FSC cycle")
    a.add_argument("--cycle-id", dest="cycle_id")
    a.add_argument("--anomaly", required=True)
    a.add_argument("--ring", default="unknown")
    a.add_argument("--dim-red")
    a.add_argument("--latency")
    a.add_argument("--strip")
    a.add_argument("--tighten")
    a.add_argument("--sigma-f", nargs="*")
    a.add_argument("--cs", nargs="*")
    a.add_argument("--ps", nargs="*")
    a.add_argument("--omega")
    a.add_argument("--tests", nargs="*")
    a.add_argument("--results", nargs="*")
    a.add_argument("--provenance", nargs="*")
    a.add_argument("--dsr", type=float)
    a.add_argument("--dc", type=float)
    a.add_argument("--stability", type=float)
    a.add_argument("--transfer", type=float)
    a.add_argument("--boundary", type=float)
    a.add_argument("--exploit", type=float)
    a.set_defaults(func=cmd_cycle)

    a = sp.add_parser("diagram", help="emit quick spine diagrams into docs/")
    a.set_defaults(func=cmd_diagram)

    # ARG
    a = sp.add_parser("arg-init", help="initialize ARG_SPINE.jsonl")
    a.set_defaults(func=cmd_arg_init)

    a = sp.add_parser("arg-drop", help="append one ARG drop")
    a.add_argument("--kind", default="drop", choices=["drop", "broadcast", "artifact", "puzzle", "verdict"])
    a.add_argument("--lobby", required=True, choices=["DNS", "BGP", "TLS", "CDN", "BACKEND", "MIXED", "QUANTUM", "FSC", "SELF"])
    a.add_argument("--severity", default=1, type=int)
    a.add_argument("--tag", required=True)
    a.add_argument("--msg", required=True)
    a.add_argument("--truth-plane", default="pending", choices=["pending", "final"])
    a.add_argument("--provenance")
    a.add_argument("--links", nargs="*")
    a.set_defaults(func=cmd_arg_drop)

    a = sp.add_parser("arg-narrate", help="print diegetic narration from ARG spine")
    a.add_argument("--tail", default=20, type=int)
    a.set_defaults(func=cmd_arg_narrate)

    # FUNDING
    a = sp.add_parser("funding-init", help="initialize FUNDING_SPINE.jsonl")
    a.set_defaults(func=cmd_funding_init)

    a = sp.add_parser("funding-claim", help="append one funding claim/metric/assumption")
    a.add_argument("--kind", default="claim", choices=["claim","metric","assumption","correction","asset","note"])
    a.add_argument("--truth-plane", default="pending", choices=["pending","final"])
    a.add_argument("--claim-id", dest="claim_id", default="")
    a.add_argument("--title", default="")
    a.add_argument("--statement", default="")
    a.add_argument("--metric", default="")
    a.add_argument("--value")
    a.add_argument("--unit", default="")
    a.add_argument("--period", default="")
    a.add_argument("--confidence", type=float)
    a.add_argument("--falsifier", default="")
    a.add_argument("--source", default="")
    a.add_argument("--calc", default="")
    a.add_argument("--links", nargs="*")
    a.set_defaults(func=cmd_funding_claim)

    a = sp.add_parser("funding-render", help="render one-pager/deck/update from FUNDING spine")
    a.set_defaults(func=cmd_funding_render)

    # FX
    a = sp.add_parser("fx-snapshot", help="retrieve ECB FX and write dated snapshot into funding/data_room/")
    a.add_argument("--base", default="USD", help="Base currency for derived rates (default: USD)")
    a.add_argument("--symbols", default="EUR,USD,GBP,JPY", help="Comma-separated currency list")
    a.add_argument("--append-spine", action="store_true", help="Append an asset entry to FUNDING_SPINE.jsonl")
    a.set_defaults(func=cmd_fx_snapshot)

    # Cheats (dev/test only)
    a = sp.add_parser("cheat", help="dev-only: test-ledger cheats (deposit/inf/reset)")
    a.add_argument("action", choices=["deposit", "inf", "reset"], help="Cheat action")
    a.add_argument("--currency", default="USD_TEST", help="Test currency code (default: USD_TEST)")
    a.add_argument("--amount", type=float, default=0.0, help="Amount for deposit/inf")
    a.add_argument("--memo", default="", help="Optional memo")
    a.add_argument("--append-spine", action="store_true", help="Append cheat event to FUNDING_SPINE.jsonl")
    a.set_defaults(func=cmd_cheat)


    # Play: generate narrated projection while appending spine-grade events
    a = sp.add_parser("play", help="generate a playthrough projection (docs/*.md) while writing immutable play events to EVENT_SPINE")
    a.add_argument("--seed", type=int, default=9, help="Seed for deterministic motif selection")
    a.add_argument("--steps", type=int, default=14, help="Number of steps per episode")
    a.add_argument("--out", default="docs/PLAYTHROUGH_LATEST.md", help="Projection output path (mutable markdown)")
    a.add_argument("--loop", action="store_true", help="Loop forever (Ctrl-C to stop). Writes a new episode each iteration.")
    a.add_argument("--max-episodes", type=int, default=0, help="Optional cap on episodes in loop mode (0 = no cap)")
    a.add_argument(
        "--auto-trigger",
        action="store_true",
        help="In --loop mode, run disagreement trigger each episode and ground the episode in the next unconsumed mission.disagreement (if any).",
    )
    a.add_argument(
        "--min-vantages",
        type=int,
        default=2,
        help="Minimum distinct vantages required to emit a mission.disagreement when --auto-trigger is enabled.",
    )
    a.set_defaults(func=cmd_play)

    # Tier 1: claims (speaking-rights gated)
    a = sp.add_parser("claim", help="append a claim to EVENT_SPINE with truth/theater gating")
    a.add_argument("--text", required=True, help="Claim text")
    a.add_argument("--truth-plane", default="theater", choices=["truth","pending","theater"], help="truth plane label")
    a.add_argument("--provenance", default=None, help="Provenance pointer (url/file/hash/trace id)")
    a.add_argument("--falsifier", default=None, help="What observation would break this claim")
    a.add_argument("--confidence", type=float, default=None, help="0..1 bounded confidence")
    a.add_argument("--scope", default=None, help="Scope (e.g., DNS, BACKEND, MIXED, personal)")
    a.add_argument("--tags", default="", help="Comma-separated tags")
    a.set_defaults(func=cmd_claim)

    # Tier 1: lint spine for speaking-rights violations
    a = sp.add_parser("lint", help="lint EVENT_SPINE for basic violations")
    a.add_argument("--limit", type=int, default=200, help="How many recent events to lint")
    a.add_argument("--fail", action="store_true", help="Exit non-zero if violations found")
    a.set_defaults(func=cmd_lint)

    # Tier 2/3: run single probe once
    a = sp.add_parser("probe", help="run a read-only probe and optionally append to EVENT_SPINE")
    a.add_argument("kind", choices=["dns","http","tls","ping"], help="Probe kind")
    a.add_argument("--append-spine", action="store_true", help="Append probe event to EVENT_SPINE")
    a.add_argument("--vantage", default=None, help="Vantage identifier (e.g., home_wifi, phone_lte, az_phx)")
    # dns args
    a.add_argument("--name", default=None, help="DNS name")
    a.add_argument("--rrtype", default="A", help="DNS RR type (A/AAAA)")
    a.add_argument("--resolver", default=None, help="Resolver (e.g., 1.1.1.1)")
    # http args
    a.add_argument("--url", default=None, help="URL for HTTP probe")
    a.add_argument("--method", default="GET", help="HTTP method")
    # tls/ping args
    a.add_argument("--host", default=None, help="Host for TLS/Ping")
    a.add_argument("--port", type=int, default=443, help="TLS port")
    a.add_argument("--server-name", default=None, help="SNI server name")
    a.add_argument("--count", type=int, default=1, help="Ping count")
    a.add_argument("--timeout", type=int, default=8, help="Timeout seconds")
    a.set_defaults(func=cmd_probe)

    # Tier 2/3: watch loop (always appends to EVENT_SPINE)
    a = sp.add_parser("watch", help="run a probe periodically and append each result to EVENT_SPINE")
    a.add_argument("kind", choices=["dns","http","tls","ping"], help="Probe kind")
    a.add_argument("--interval", type=int, default=60, help="Interval seconds")
    a.add_argument("--jitter", type=int, default=0, help="Optional jitter seconds")
    a.add_argument("--name", default=None, help="DNS name")
    a.add_argument("--rrtype", default="A", help="DNS RR type")
    a.add_argument("--resolver", default=None, help="Resolver")
    a.add_argument("--url", default=None, help="URL for HTTP probe")
    a.add_argument("--method", default="GET", help="HTTP method")
    a.add_argument("--host", default=None, help="Host for TLS/Ping")
    a.add_argument("--port", type=int, default=443, help="TLS port")
    a.add_argument("--server-name", default=None, help="SNI server name")
    a.add_argument("--count", type=int, default=1, help="Ping count")
    a.add_argument("--timeout", type=int, default=8, help="Timeout seconds")
    a.add_argument("--vantage", default=None, help="Vantage identifier (e.g., home_wifi, phone_lte, az_phx)")
    a.set_defaults(func=cmd_watch)

    # Tier 3: auto-trigger missions from disagreements
    a = sp.add_parser("trigger", help="append mission events when probe results disagree across vantages")
    a.add_argument("--min-vantages", type=int, default=2, help="Minimum distinct vantages required")
    a.add_argument("--spawn-play", action="store_true", help="After appending new missions, spawn a play episode per mission")
    a.add_argument("--steps", type=int, default=14, help="Steps per spawned episode (only with --spawn-play)")
    a.add_argument("--seed", type=int, default=None, help="Override seed for spawned episodes (default: derive from mission trace_id)")
    a.add_argument("--out-dir", default="docs", help="Directory for per-mission playthrough projections")
    a.add_argument("--latest", default="docs/PLAYTHROUGH_LATEST.md", help="Path for latest playthrough projection")
    a.set_defaults(func=cmd_trigger)

    # Tier 3: sentinel loop that watches for disagreements and auto-spawns episodes
    a = sp.add_parser("sentinel", help="loop: run trigger periodically to spawn disagreement missions (and optionally play episodes)")
    a.add_argument("--interval", type=int, default=15, help="Polling interval seconds")
    a.add_argument("--max-loops", type=int, default=0, help="Optional cap on iterations (0 = no cap)")
    a.add_argument("--min-vantages", type=int, default=2, help="Minimum distinct vantages required")
    a.add_argument("--spawn-play", action="store_true", help="After appending new missions, spawn a play episode per mission")
    a.add_argument("--steps", type=int, default=14, help="Steps per spawned episode (only with --spawn-play)")
    a.add_argument("--seed", type=int, default=None, help="Override seed for spawned episodes (default: derive from mission trace_id)")
    a.add_argument("--out-dir", default="docs", help="Directory for per-mission playthrough projections")
    a.add_argument("--latest", default="docs/PLAYTHROUGH_LATEST.md", help="Path for latest playthrough projection")
    a.set_defaults(func=cmd_sentinel)

    return p


def main():
    cli = build_cli()
    args = cli.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
