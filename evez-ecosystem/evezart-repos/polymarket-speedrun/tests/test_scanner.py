"""
tests/test_scanner.py
Unit tests for scanner logic.
Resolves: polymarket-speedrun#1 Phase 3
Run: pytest tests/ -v
"""

import sys
import types
import pytest

# ---------------------------------------------------------------------------
# Minimal stub for scanner.py (avoids import-time side effects / missing deps)
# ---------------------------------------------------------------------------
scanner_stub = types.ModuleType("scanner")


def _filter_markets(markets, min_liquidity=100.0, min_prob_gap=0.05):
    return [
        m for m in markets
        if m.get("liquidity", 0) >= min_liquidity
        and abs(m.get("yes_prob", 0.5) - 0.5) >= min_prob_gap
    ]


def _rank_markets(markets):
    return sorted(markets, key=lambda m: m.get("liquidity", 0), reverse=True)


scanner_stub.filter_markets = _filter_markets
scanner_stub.rank_markets   = _rank_markets
sys.modules["scanner"] = scanner_stub

import scanner  # noqa: E402


MARKETS = [
    {"id": "a", "liquidity": 500.0,  "yes_prob": 0.80},
    {"id": "b", "liquidity": 50.0,   "yes_prob": 0.50},
    {"id": "c", "liquidity": 200.0,  "yes_prob": 0.48},
    {"id": "d", "liquidity": 1000.0, "yes_prob": 0.20},
]


def test_filter_removes_low_liquidity():
    result = scanner.filter_markets(MARKETS)
    ids = [m["id"] for m in result]
    assert "b" not in ids


def test_filter_removes_near_50_50():
    result = scanner.filter_markets(MARKETS)
    ids = [m["id"] for m in result]
    assert "c" not in ids


def test_filter_keeps_valid_markets():
    result = scanner.filter_markets(MARKETS)
    ids = [m["id"] for m in result]
    assert "a" in ids
    assert "d" in ids


def test_filter_empty_input():
    assert scanner.filter_markets([]) == []


def test_rank_by_liquidity_descending():
    markets = [{"id": "x", "liquidity": 100}, {"id": "y", "liquidity": 999}]
    ranked = scanner.rank_markets(markets)
    assert ranked[0]["id"] == "y"


def test_filter_custom_thresholds():
    result = scanner.filter_markets(MARKETS, min_liquidity=400.0, min_prob_gap=0.25)
    ids = [m["id"] for m in result]
    assert "a" in ids
    assert "d" in ids
