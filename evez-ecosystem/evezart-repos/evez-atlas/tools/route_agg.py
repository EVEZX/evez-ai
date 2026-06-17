#!/usr/bin/env python3
"""tools/route_agg.py — Multi-vantage Route Aggregator

Run route_opt.py on multiple machines with different EVEZ_VANTAGE values
and --append-spine. Then merge all EVENT_SPINE.jsonl files and run this
script to find the best vantage per target (lowest latency route).

Usage:
    python3 tools/route_agg.py spine/EVENT_SPINE.jsonl
    python3 tools/route_agg.py merged_spine.jsonl
"""

import json
import sys
import os


def score(c: dict) -> tuple:
    """Conservative score: (p95_ms, loss_rate, median_ms)."""
    return (
        c.get("p95_ms", 1e9),
        c.get("loss_rate", 1.0),
        c.get("median_ms", 1e9),
    )


def aggregate(spine_path: str) -> None:
    best = {}  # (section, name) -> (score_tuple, vantage, candidate)

    with open(spine_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            if e.get("kind") != "route.snapshot":
                continue

            v = e.get("vantage_id", "default")
            for section, rows in (e.get("results") or {}).items():
                for c in rows:
                    k = (section, c["name"])
                    s = score(c)
                    cur = best.get(k)
                    if cur is None or s < cur[0]:
                        best[k] = (s, v, c)

    if not best:
        print("No route.snapshot entries found in spine.")
        return

    print(f"\n=== Multi-Vantage Route Aggregation ===")
    print(f"Source : {spine_path}")
    print(f"\n{'Section':<6}  {'Target':<40}  {'Best Vantage':<18}  {'p95':>8}ms  {'loss':>6}  {'med':>8}ms")
    print(f"{'-'*6}  {'-'*40}  {'-'*18}  {'-'*8}   {'-'*6}  {'-'*8}")

    for (section, name), (s, vantage, c) in sorted(
        best.items(), key=lambda kv: kv[1][0]
    ):
        p95 = s[0]
        loss = s[1]
        med = s[2]
        p95_str = f"{p95:8.1f}" if p95 < 1e8 else "  TIMEOUT"
        med_str = f"{med:8.1f}" if med < 1e8 else "  TIMEOUT"
        print(f"{section:<6}  {name:<40}  {vantage:<18}  {p95_str}   {loss:6.4f}  {med_str}")

    print(f"\nTotal unique targets: {len(best)}")


def main():
    if len(sys.argv) < 2:
        default = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "spine", "EVENT_SPINE.jsonl"
        )
        if os.path.exists(default):
            aggregate(default)
        else:
            print("Usage: python3 tools/route_agg.py <spine_file>")
            sys.exit(1)
    else:
        aggregate(sys.argv[1])


if __name__ == "__main__":
    main()
