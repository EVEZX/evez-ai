from __future__ import annotations

import json
from pathlib import Path
from threading import Lock
from typing import Dict


class DebtLedgerRepository:
    """File-backed debt ledger repository for predictable cross-restart state."""

    def __init__(self, path: Path):
        self.path = path
        self._lock = Lock()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write({})

    def _read(self) -> Dict[str, float]:
        with self.path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        return {str(key): float(value) for key, value in payload.items()}

    def _write(self, ledger: Dict[str, float]) -> None:
        temp_path = self.path.with_suffix(f"{self.path.suffix}.tmp")
        with temp_path.open("w", encoding="utf-8") as handle:
            json.dump(ledger, handle, indent=2, sort_keys=True)
        temp_path.replace(self.path)

    def get_balance(self, account_id: str) -> float:
        with self._lock:
            ledger = self._read()
            return float(ledger.get(account_id, 0.0))

    def set_balance(self, account_id: str, amount: float) -> None:
        with self._lock:
            ledger = self._read()
            ledger[account_id] = float(amount)
            self._write(ledger)

    def snapshot(self) -> Dict[str, float]:
        with self._lock:
            return self._read()
