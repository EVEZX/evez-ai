#!/usr/bin/env python3
"""Dev-only cheat tooling for test funding flows.

Design goals:
- NEVER mint real currency. Default to *_TEST codes.
- Always append an immutable record:
  - funding/data_room/LEDGER_TEST.jsonl (transaction log)
  - optionally spine/FUNDING_SPINE.jsonl (audit event)
- Hard-gated by EVEZ_ENV in {dev,test} to prevent accidental use.

This is for scenario testing and reproducible sims, not production finance.
"""
from __future__ import annotations

import os
import json
import hashlib
import datetime
from pathlib import Path
from typing import Any, Dict, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
LEDGER_PATH = REPO_ROOT / "funding" / "data_room" / "LEDGER_TEST.jsonl"

ALLOWED_ENVS = {"dev", "test"}

def _utc_ts() -> str:
    return datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z"

def _require_dev() -> None:
    env = os.environ.get("EVEZ_ENV", "").strip().lower()
    if env not in ALLOWED_ENVS:
        raise SystemExit(f"Refusing to run cheats outside dev/test. Set EVEZ_ENV=dev (got: {env or 'unset'})")

def _sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def _append_ledger(tx: Dict[str, Any]) -> str:
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(tx, ensure_ascii=False).encode("utf-8")
    h = _sha256_bytes(line)
    with LEDGER_PATH.open("ab") as f:
        f.write(line + b"\n")
    return h

def load_ledger(currency: str) -> list[Dict[str, Any]]:
    if not LEDGER_PATH.exists():
        return []
    out = []
    for line in LEDGER_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if obj.get("currency") == currency:
            out.append(obj)
    return out

def balance(currency: str) -> float:
    bal = 0.0
    for tx in load_ledger(currency):
        kind = tx.get("kind")
        amt = float(tx.get("amount", 0))
        if kind == "deposit":
            bal += amt
        elif kind == "withdraw":
            bal -= amt
        elif kind == "set_balance":
            bal = amt
        elif kind == "reset":
            bal = 0.0
    return bal

def deposit(currency: str, amount: float, memo: Optional[str] = None) -> Dict[str, Any]:
    _require_dev()
    if not currency.endswith("_TEST") and currency not in {"USD_TEST", "EUR_TEST", "GBP_TEST", "JPY_TEST"}:
        # Allow explicit non-suffixed test currencies only if they include TEST in some form.
        if "TEST" not in currency:
            raise SystemExit("Cheat currency must be a test code (e.g., USD_TEST). Refusing.")
    if amount <= 0:
        raise SystemExit("deposit amount must be > 0")
    tx = {
        "ts": _utc_ts(),
        "kind": "deposit",
        "currency": currency,
        "amount": float(amount),
        "memo": memo or "",
        "source": "cheat",
        "truth_plane": "final",
    }
    h = _append_ledger(tx)
    return {"ledger": str(LEDGER_PATH), "tx_hash": h, "balance": balance(currency)}

def set_infinite(currency: str, amount: float, memo: Optional[str] = None) -> Dict[str, Any]:
    _require_dev()
    if amount <= 0:
        raise SystemExit("inf amount must be > 0")
    tx = {
        "ts": _utc_ts(),
        "kind": "set_balance",
        "currency": currency,
        "amount": float(amount),
        "memo": memo or "inf$$",
        "source": "cheat",
        "truth_plane": "final",
    }
    h = _append_ledger(tx)
    return {"ledger": str(LEDGER_PATH), "tx_hash": h, "balance": balance(currency)}

def reset(currency: str, memo: Optional[str] = None) -> Dict[str, Any]:
    _require_dev()
    tx = {
        "ts": _utc_ts(),
        "kind": "reset",
        "currency": currency,
        "amount": 0.0,
        "memo": memo or "reset$$",
        "source": "cheat",
        "truth_plane": "final",
    }
    h = _append_ledger(tx)
    return {"ledger": str(LEDGER_PATH), "tx_hash": h, "balance": balance(currency)}
