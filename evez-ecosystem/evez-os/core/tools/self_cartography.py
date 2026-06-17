#!/usr/bin/env python3
"""Generate self-cartography maps from EVENT_SPINE and ARG_SPINE.

We map traces, not minds.

- ARG lobbies are rooms.
- Consecutive ARG drops define directed edges.
- EVENT_SPINE FSC cycles become pressure notes.

Outputs:
  docs/SELF_CARTOGRAPHY.mmd (Mermaid)
  docs/SELF_CARTOGRAPHY.dot (Graphviz DOT)
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPINE = ROOT / "spine" / "EVENT_SPINE.jsonl"
ARG_SPINE = ROOT / "spine" / "ARG_SPINE.jsonl"
OUT_MMD = ROOT / "docs" / "SELF_CARTOGRAPHY.mmd"
OUT_DOT = ROOT / "docs" / "SELF_CARTOGRAPHY.dot"


def read_jsonl(path: Path):
    if not path.exists():
        return []
    out = []
    for ln in path.read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if not ln:
            continue
        try:
            out.append(json.loads(ln))
        except Exception:
            continue
    return out


def build_edges(drops):
    edges = defaultdict(int)
    seq = [d.get("lobby", "SELF") for d in drops]
    for a, b in zip(seq, seq[1:]):
        edges[(a, b)] += 1
    return edges


def pressure_notes(events, max_notes=8):
    notes = []
    for e in events:
        if e.get("type") != "fsc_cycle":
            continue
        anomaly = e.get("anomaly", "")
        sigma = e.get("sigma_f", [])
        omega = e.get("omega", "")
        s = f"anomaly={anomaly} | Σf={', '.join(sigma)[:80]} | Ω={omega}"
        notes.append(s)
    return notes[-max_notes:]


def write_mermaid(edges, notes):
    lines = []
    lines.append("flowchart TD")
    lines.append("  classDef room fill:#0b1020,stroke:#7dd3fc,stroke-width:1px,color:#e5e7eb;")
    rooms = set()
    for (a, b) in edges:
        rooms.add(a)
        rooms.add(b)
    for r in sorted(rooms):
        lines.append(f"  {r}([{r}]):::room")
    for (a, b), w in sorted(edges.items(), key=lambda x: (-x[1], x[0][0], x[0][1])):
        label = f"{w}x"
        lines.append(f"  {a} -->|{label}| {b}")
    if notes:
        lines.append("  NOTE[\"Pressure Notes (FSC)\\n" + "\\n".join(n.replace('"','\\\"') for n in notes) + "\"]")
        if rooms:
            anchor = sorted(rooms)[0]
            lines.append(f"  {anchor} -.-> NOTE")
    return "\n".join(lines) + "\n"


def write_dot(edges, notes):
    lines = []
    lines.append("digraph SELF_CARTOGRAPHY {")
    lines.append("  rankdir=LR;")
    lines.append("  node [shape=box,style=rounded];")
    for (a, b), w in edges.items():
        lines.append(f"  \"{a}\" -> \"{b}\" [label=\"{w}x\"]; ")
    if notes:
        joined = "\\n".join(notes).replace('"','\\\"')
        lines.append(f"  NOTE [shape=note,label=\"{joined}\"]; ")
    lines.append("}")
    return "\n".join(lines) + "\n"


def main():
    drops = read_jsonl(ARG_SPINE)
    events = read_jsonl(SPINE)
    edges = build_edges(drops)
    notes = pressure_notes(events)
    ROOT.joinpath("docs").mkdir(parents=True, exist_ok=True)
    OUT_MMD.write_text(write_mermaid(edges, notes), encoding="utf-8")
    OUT_DOT.write_text(write_dot(edges, notes), encoding="utf-8")
    print(f"wrote {OUT_MMD}")
    print(f"wrote {OUT_DOT}")


if __name__ == "__main__":
    main()
