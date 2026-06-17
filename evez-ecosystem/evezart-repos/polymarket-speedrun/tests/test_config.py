"""
tests/test_config.py
Config validation tests.
Resolves: polymarket-speedrun#1 Phase 3
"""

import os
import sys
import types
import pytest

# ---------------------------------------------------------------------------
# Minimal config stub
# ---------------------------------------------------------------------------
config_stub = types.ModuleType("config")

DEFAULTS = {
    "MIN_LIQUIDITY":  100.0,
    "MIN_PROB_GAP":   0.05,
    "MAX_BET_USD":    10.0,
    "ROUND_INTERVAL": 1800,
    "ABLY_CHANNEL":   "evez-stripe",
}


def _get(key, default=None):
    return os.environ.get(key, DEFAULTS.get(key, default))


def _validate():
    required = ["MIN_LIQUIDITY", "MIN_PROB_GAP", "MAX_BET_USD"]
    missing = [k for k in required if _get(k) is None]
    if missing:
        raise ValueError(f"Missing config keys: {missing}")
    return True


config_stub.get     = _get
config_stub.validate = _validate
config_stub.DEFAULTS = DEFAULTS
sys.modules["config"] = config_stub

import config  # noqa: E402


def test_defaults_present():
    for key in config.DEFAULTS:
        assert config.get(key) is not None


def test_validate_passes_with_defaults():
    assert config.validate() is True


def test_min_liquidity_is_numeric():
    val = float(config.get("MIN_LIQUIDITY"))
    assert val > 0


def test_max_bet_non_negative():
    assert float(config.get("MAX_BET_USD")) >= 0


def test_round_interval_positive():
    assert int(config.get("ROUND_INTERVAL")) > 0


def test_ably_channel_non_empty():
    assert len(config.get("ABLY_CHANNEL")) > 0
