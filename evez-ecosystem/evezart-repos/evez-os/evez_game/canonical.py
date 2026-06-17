"""Canonical JSON utilities for stable hashing."""

from __future__ import annotations

import json
from typing import Any


def canonical_dumps(obj: Any) -> str:
    """Serialize to deterministic JSON."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def canonical_bytes(obj: Any) -> bytes:
    """Serialize to deterministic UTF-8 bytes."""
    return canonical_dumps(obj).encode("utf-8")
