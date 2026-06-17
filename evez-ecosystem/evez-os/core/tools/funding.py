#!/usr/bin/env python3
"""
Funding assets toolchain.

Goal: keep investor materials as projections, renderable from an immutable spine:
  spine/FUNDING_SPINE.jsonl

This is intentionally lightweight: JSONL append + simple template rendering.
"""
from __future__ import annotations
import argparse, json, os, re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
SPINE_PATH = REPO_ROOT / "spine" / "FUNDING_SPINE.jsonl"
OUT_DIR = REPO_ROOT / "funding" / "out"
TEMPLATE_DIR = REPO_ROOT / "funding" / "templates"

def _utc_ts() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds") + "Z"

def ensure_spine() -> None:
    SPINE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not SPINE_PATH.exists():
        SPINE_PATH.write_text("# Append one JSON object per entry. Keep immutable.\n", encoding="utf-8")

def append_entry(entry: Dict[str, Any]) -> None:
    ensure_spine()
    line = json.dumps(entry, ensure_ascii=False)
    with SPINE_PATH.open("a", encoding="utf-8") as f:
        f.write(line + "\n")

def load_entries() -> List[Dict[str, Any]]:
    ensure_spine()
    entries: List[Dict[str, Any]] = []
    with SPINE_PATH.open("r", encoding="utf-8") as f:
        for raw in f:
            raw = raw.strip()
            if not raw or raw.startswith("#"):
                continue
            try:
                entries.append(json.loads(raw))
            except json.JSONDecodeError:
                # allow occasional human notes; ignore
                continue
    return entries

def latest_field(entries: List[Dict[str, Any]], field: str, default: str="") -> str:
    for e in reversed(entries):
        v = e.get(field)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return default

def latest_blocks(entries: List[Dict[str, Any]], kind: str) -> List[Dict[str, Any]]:
    return [e for e in entries if e.get("kind")==kind]

def render_template(template_text: str, ctx: Dict[str, str]) -> str:
    def repl(m: re.Match) -> str:
        key = m.group(1)
        return ctx.get(key, m.group(0))
    return re.sub(r"\{\{([a-zA-Z0-9_]+)\}\}", repl, template_text)

def build_ctx(entries: List[Dict[str, Any]]) -> Dict[str, str]:
    # Minimal default context; fill with latest statements if present.
    ctx: Dict[str, str] = {
        "company_name": latest_field(entries, "company_name", "YOUR_COMPANY"),
        "tagline": latest_field(entries, "tagline", "Short, sharp positioning line."),
        "problem": latest_field(entries, "problem", "Describe the painful, expensive problem."),
        "solution": latest_field(entries, "solution", "Describe what you built and why it works."),
        "why_now": latest_field(entries, "why_now", "Explain timing (tech, market, regulation, behavior)."),
        "product": latest_field(entries, "product", "What the product is and how it behaves."),
        "business_model": latest_field(entries, "business_model", "How you make money (pricing + unit economics)."),
        "market": latest_field(entries, "market", "TAM/SAM/SOM with provenance."),
        "competition": latest_field(entries, "competition", "Alternatives + why you win."),
        "moat": latest_field(entries, "moat", "Why this compounds and stays hard to copy."),
        "gtm": latest_field(entries, "gtm", "How you acquire and expand customers."),
        "team": latest_field(entries, "team", "Why this team is inevitable."),
        "ask": latest_field(entries, "ask", "Round size, runway, milestones."),
        "links": latest_field(entries, "links", ""),
        "month_year": datetime.now(timezone.utc).strftime("%B %Y"),
    }

    # Traction block from metrics entries (final preferred, fallback pending)
    metrics = [e for e in entries if e.get("kind") in ("metric","claim")]
    # pick recent 6 with values
    lines=[]
    for e in reversed(metrics):
        title=e.get("title") or e.get("metric") or e.get("statement")
        val=e.get("value")
        unit=e.get("unit","")
        tp=e.get("truth_plane","pending")
        if title and val is not None:
            lines.append(f"- {title}: {val} {unit} ({tp})")
        if len(lines)>=6:
            break
    ctx["traction_block"] = "\n".join(reversed(lines)) if lines else "- (add metric entries to FUNDING_SPINE.jsonl)"

    # Financials block from metric entries named revenue/burn/runway etc.
    fin=[]
    for e in reversed(metrics):
        m=(e.get("metric") or e.get("title") or "").lower()
        if any(k in m for k in ["revenue","arr","mrr","burn","runway","cash","margin","cogs"]):
            title=e.get("title") or e.get("metric") or "Metric"
            val=e.get("value")
            unit=e.get("unit","")
            tp=e.get("truth_plane","pending")
            fin.append(f"- {title}: {val} {unit} ({tp})")
        if len(fin)>=8:
            break
    ctx["financials_block"] = "\n".join(reversed(fin)) if fin else "- (add financial metric entries to FUNDING_SPINE.jsonl)"

    # Proof pack: list links
    proof=[]
    for e in entries:
        for link in e.get("links",[]) if isinstance(e.get("links"),list) else []:
            proof.append(link)
    ctx["proof_pack"] = "\n".join(f"- {p}" for p in sorted(set(proof))) if proof else "- DR-XXXX items go here"
    return ctx

def cmd_init(_: argparse.Namespace) -> None:
    ensure_spine()
    if SPINE_PATH.read_text(encoding="utf-8").strip().endswith("immutable.\n"):
        pass
    # seed a tiny example entry so rendering works
    append_entry({
        "ts": _utc_ts(),
        "kind": "note",
        "truth_plane": "pending",
        "title": "funding spine initialized",
        "statement": "Add claims/metrics/assumptions here; render projections from it.",
    })
    print(f"Initialized {SPINE_PATH}")

def cmd_claim(args: argparse.Namespace) -> None:
    entry = {
        "ts": _utc_ts(),
        "kind": args.kind,
        "truth_plane": args.truth_plane,
        "claim_id": args.claim_id,
        "title": args.title,
        "statement": args.statement,
        "metric": args.metric,
        "value": args.value,
        "unit": args.unit,
        "period": args.period,
        "confidence": args.confidence,
        "falsifier": args.falsifier,
        "provenance": {
            "source": args.source,
            "calc": args.calc,
        },
        "links": [s for s in (args.link or []) if s],
    }
    # drop empty keys to keep spine tidy
    entry = {k:v for k,v in entry.items() if v not in (None,"",[],{})}
    append_entry(entry)
    print("Appended entry to FUNDING_SPINE.jsonl")

def cmd_render(_: argparse.Namespace) -> None:
    entries = load_entries()
    ctx = build_ctx(entries)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for name in ["ONE_PAGER_TEMPLATE.md","PITCH_OUTLINE_TEMPLATE.md","INVESTOR_UPDATE_TEMPLATE.md"]:
        tpl_path = TEMPLATE_DIR / name
        if not tpl_path.exists():
            continue
        rendered = render_template(tpl_path.read_text(encoding="utf-8"), ctx)
        out_name = name.replace("_TEMPLATE","").replace("PITCH_OUTLINE","PITCH_OUTLINE_RENDERED")
        (OUT_DIR / out_name).write_text(rendered, encoding="utf-8")
        print(f"Rendered {out_name} -> funding/out/")

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="funding", description="Funding assets spine tool")
    sp = p.add_subparsers(dest="cmd", required=True)

    s0 = sp.add_parser("init", help="initialize funding spine")
    s0.set_defaults(fn=cmd_init)

    s1 = sp.add_parser("claim", help="append a claim/metric/assumption entry")
    s1.add_argument("--kind", choices=["claim","metric","assumption","correction","asset","note"], default="claim")
    s1.add_argument("--truth-plane", choices=["pending","final"], default="pending")
    s1.add_argument("--claim-id", default="")
    s1.add_argument("--title", default="")
    s1.add_argument("--statement", default="")
    s1.add_argument("--metric", default="")
    s1.add_argument("--value", default=None)
    s1.add_argument("--unit", default="")
    s1.add_argument("--period", default="")
    s1.add_argument("--confidence", type=float, default=None)
    s1.add_argument("--falsifier", default="")
    s1.add_argument("--source", default="")
    s1.add_argument("--calc", default="")
    s1.add_argument("--link", action="append", default=[])
    s1.set_defaults(fn=cmd_claim)

    s2 = sp.add_parser("render", help="render funding projections from spine")
    s2.set_defaults(fn=cmd_render)

    return p

def main_from_evez(argv=None) -> None:
    p = build_parser()
    args = p.parse_args(argv)
    args.fn(args)


def main() -> None:
    main_from_evez(None)

if __name__ == "__main__":
    main()
