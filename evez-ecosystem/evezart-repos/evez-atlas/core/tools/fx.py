#!/usr/bin/env python3
"""ECB-backed FX snapshot tool.

This module fetches the European Central Bank (ECB) *euro reference exchange rates*
from the primary ECB XML feed and writes a dated snapshot into:
  funding/data_room/

It can also append an "asset" entry into spine/FUNDING_SPINE.jsonl so any funding
math can cite an immutable FX artifact.

Policy: "summon currency ≠ invent it".
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Tuple

ECB_DAILY_XML = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml"

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOM = REPO_ROOT / "funding" / "data_room"
FUNDING_SPINE = REPO_ROOT / "spine" / "FUNDING_SPINE.jsonl"


def _utc_ts() -> str:
    return _dt.datetime.now(timezone.utc).replace(microsecond=0).isoformat() + "Z"


def _ensure_parent(p: Path) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)


def fetch_ecb_daily_xml(timeout_s: int = 20) -> bytes:
    req = urllib.request.Request(
        ECB_DAILY_XML,
        headers={
            "User-Agent": "evez-fx-snapshot/1.0 (+offline-audit)"
        },
    )
    with urllib.request.urlopen(req, timeout=timeout_s) as r:
        return r.read()


def parse_ecb_xml(xml_bytes: bytes) -> Tuple[str, Dict[str, float]]:
    """Return (date_str, rates_by_ccy) where rates are 1 EUR -> CCY."""
    # ECB uses namespaces; simplest is to ignore and just search by local-name.
    root = ET.fromstring(xml_bytes)

    # Find Cube[@time='YYYY-MM-DD']
    date = None
    rates: Dict[str, float] = {}

    # Walk all elements and match tag endings
    for elem in root.iter():
        if elem.tag.endswith("Cube") and "time" in elem.attrib:
            date = elem.attrib["time"]
            # children have currency/rate
            for child in list(elem):
                if not child.tag.endswith("Cube"):
                    continue
                ccy = child.attrib.get("currency")
                rate = child.attrib.get("rate")
                if ccy and rate:
                    try:
                        rates[ccy.upper()] = float(rate)
                    except ValueError:
                        pass
            break

    if not date or not rates:
        raise RuntimeError("Could not parse ECB daily XML (missing date or rates)")
    return date, rates


def compute_conversions(rates_eur_base: Dict[str, float], base: str, symbols: List[str]) -> Dict[str, float]:
    """Convert ECB EUR-base rates into 1 BASE -> SYMBOL rates."""
    base = base.upper()
    symbols = [s.upper() for s in symbols]

    def eur_to(ccy: str) -> float:
        if ccy == "EUR":
            return 1.0
        if ccy not in rates_eur_base:
            raise KeyError(f"ECB feed missing currency {ccy}")
        return rates_eur_base[ccy]

    # If base is not EUR, we need BASE->EUR, then EUR->SYMBOL
    eur_per_base = 1.0 / eur_to(base) if base != "EUR" else 1.0

    out: Dict[str, float] = {}
    for sym in symbols:
        if sym == base:
            out[sym] = 1.0
        else:
            out[sym] = eur_to(sym) * eur_per_base
    return out


def write_snapshot(date: str, base: str, rates_eur_base: Dict[str, float], derived: Dict[str, float]) -> Path:
    DATA_ROOM.mkdir(parents=True, exist_ok=True)
    snap = {
        "schema": "evez.fx.snapshot.v1",
        "ts_utc": _utc_ts(),
        "ecb_feed": ECB_DAILY_XML,
        "ecb_date": date,
        "rates": {
            "base": base.upper(),
            "derived": derived,
            "eur_base": rates_eur_base,
        },
        "provenance": {
            "retrieved_from": ECB_DAILY_XML,
            "retrieved_ts_utc": _utc_ts(),
            "notes": "ECB euro reference exchange rates; derived rates computed from EUR base.",
        },
    }

    fname = f"FX-{date}-{base.upper()}.json"
    path = DATA_ROOM / fname
    path.write_text(json.dumps(snap, indent=2, sort_keys=True), encoding="utf-8")
    return path


def append_funding_spine(asset_path: Path, base: str, symbols: List[str], ecb_date: str) -> None:
    FUNDING_SPINE.parent.mkdir(parents=True, exist_ok=True)
    if not FUNDING_SPINE.exists():
        FUNDING_SPINE.write_text("# Append one JSON object per entry. Keep immutable.\n", encoding="utf-8")

    entry = {
        "ts": _utc_ts(),
        "kind": "asset",
        "truth_plane": "final",
        "title": f"FX snapshot (ECB) {ecb_date} base={base.upper()}",
        "statement": "ECB euro reference rates snapshot with derived base-currency conversions.",
        "metric": "fx_snapshot",
        "unit": "file",
        "value": str(asset_path.relative_to(REPO_ROOT)),
        "provenance": {
            "source": ECB_DAILY_XML,
            "calc": f"Derived rates computed from EUR base; symbols={','.join([s.upper() for s in symbols])}",
        },
        "links": [ECB_DAILY_XML],
    }

    with FUNDING_SPINE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def snapshot(base: str, symbols: List[str], append_spine: bool) -> Path:
    xml_bytes = fetch_ecb_daily_xml()
    date, eur_rates = parse_ecb_xml(xml_bytes)

    # Ensure symbols include base? (derived dict includes symbols as requested)
    derived = compute_conversions(eur_rates, base=base, symbols=symbols)

    path = write_snapshot(date=date, base=base, rates_eur_base=eur_rates, derived=derived)
    if append_spine:
        append_funding_spine(asset_path=path, base=base, symbols=symbols, ecb_date=date)
    return path


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="fx", description="ECB-backed FX snapshot tool")
    p.add_argument("--base", default="USD", help="Base currency for derived rates (default: USD)")
    p.add_argument("--symbols", default="EUR,USD,GBP,JPY", help="Comma-separated symbol list for derived rates")
    p.add_argument("--append-spine", action="store_true", help="Append an asset entry to spine/FUNDING_SPINE.jsonl")
    return p


def main(argv: List[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]
    try:
        out = snapshot(base=args.base, symbols=symbols, append_spine=args.append_spine)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(2)
    print(str(out))


if __name__ == "__main__":
    main()
