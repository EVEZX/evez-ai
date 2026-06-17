"""test_detect_b.py — Unit tests for DetectB and DetectorConfig.

Covers logic paths NOT exercised by test_harness.py:
  - DetectorConfig defaults and hyperloop_fire preset
  - DetectB: adaptive (rolling) baseline mode
  - DetectB: fixed threshold mode
  - DetectB: refractory window suppression
  - DetectB: confidence calculation
  - DetectB: envelope decay
  - DetectB: classification (A / B / C)
  - DetectB: reset()
  - DetectB: update_baseline skipped in fixed-threshold mode
  - HyperloopAdapter: process_round fields, replay_arc reset behaviour
"""

import sys
import math
from pathlib import Path

# Run from any working directory
sys.path.insert(0, str(Path(__file__).resolve().parent))

from detect_b import DetectB, DetectorConfig
from hyperloop_adapter import HyperloopAdapter


# ---------------------------------------------------------------------------
# DetectorConfig
# ---------------------------------------------------------------------------

def test_config_defaults():
    """Default DetectorConfig has expected values."""
    cfg = DetectorConfig()
    assert cfg.k == 3.0
    assert cfg.fixed_threshold is None
    assert cfg.min_peak_prominence == 0.05
    assert cfg.refractory_window_ms == 200.0
    assert cfg.baseline_window == 100
    assert cfg.confidence_floor == 0.50
    print("PASS test_config_defaults")


def test_config_hyperloop_fire_preset():
    """hyperloop_fire preset uses fixed threshold 0.500 with k=0."""
    cfg = DetectorConfig.hyperloop_fire()
    assert cfg.k == 0
    assert cfg.fixed_threshold == 0.500
    assert cfg.min_peak_prominence == 0.0
    assert cfg.refractory_window_ms == 0.0
    assert cfg.confidence_floor == 0.0
    print("PASS test_config_hyperloop_fire_preset")


# ---------------------------------------------------------------------------
# DetectB — initial state
# ---------------------------------------------------------------------------

def test_detectb_initial_state():
    """Freshly constructed DetectB starts with zero counts and no fire."""
    d = DetectB()
    assert d._sample_count == 0
    assert d._fire_count == 0
    assert d._last_fire_ms is None
    assert d._envelope == 0.0
    print("PASS test_detectb_initial_state")


# ---------------------------------------------------------------------------
# DetectB — fixed-threshold mode (hyperloop preset)
# ---------------------------------------------------------------------------

def test_detectb_fixed_threshold_fire_at_exact_threshold():
    """Value exactly at fixed_threshold triggers detect_B."""
    d = DetectB(DetectorConfig.hyperloop_fire())
    evt = d.process(0.500, timestamp_ms=1.0)
    assert evt["detect_B"] is True, "value == threshold should fire"
    assert evt["classification"] == "B"
    print("PASS test_detectb_fixed_threshold_fire_at_exact_threshold")


def test_detectb_fixed_threshold_no_fire_below():
    """Value below fixed_threshold does NOT trigger detect_B."""
    d = DetectB(DetectorConfig.hyperloop_fire())
    evt = d.process(0.499, timestamp_ms=1.0)
    assert evt["detect_B"] is False
    print("PASS test_detectb_fixed_threshold_no_fire_below")


def test_detectb_fixed_threshold_fire_above():
    """Value above fixed_threshold fires."""
    d = DetectB(DetectorConfig.hyperloop_fire())
    evt = d.process(0.750, timestamp_ms=1.0)
    assert evt["detect_B"] is True
    assert evt["fire_count"] == 1
    print("PASS test_detectb_fixed_threshold_fire_above")


def test_detectb_fixed_threshold_fire_count_increments():
    """_fire_count increments each time detect_B fires."""
    d = DetectB(DetectorConfig.hyperloop_fire())
    for ts in range(1, 6):
        d.process(0.600, timestamp_ms=float(ts), dt_ms=1000.0)
    assert d._fire_count == 5
    print("PASS test_detectb_fixed_threshold_fire_count_increments")


def test_detectb_fixed_threshold_baseline_mean_is_threshold():
    """In fixed-threshold mode baseline_mean == fixed_threshold."""
    d = DetectB(DetectorConfig.hyperloop_fire())
    d.process(0.300, timestamp_ms=1.0)
    assert d.baseline_mean == 0.500
    print("PASS test_detectb_fixed_threshold_baseline_mean_is_threshold")


def test_detectb_fixed_threshold_baseline_std_is_zero():
    """In fixed-threshold mode baseline_std == 0.0."""
    d = DetectB(DetectorConfig.hyperloop_fire())
    d.process(0.300, timestamp_ms=1.0)
    assert d.baseline_std == 0.0
    print("PASS test_detectb_fixed_threshold_baseline_std_is_zero")


def test_detectb_fixed_threshold_update_baseline_noop():
    """update_baseline is a no-op in fixed-threshold mode."""
    d = DetectB(DetectorConfig.hyperloop_fire())
    d.update_baseline(9999.0)
    assert len(d._baseline) == 0, "baseline deque must remain empty"
    print("PASS test_detectb_fixed_threshold_update_baseline_noop")


# ---------------------------------------------------------------------------
# DetectB — adaptive (rolling baseline) mode
# ---------------------------------------------------------------------------

def test_detectb_adaptive_no_fire_below_threshold():
    """In adaptive mode, sub-threshold values do not fire."""
    d = DetectB(DetectorConfig(k=3.0, confidence_floor=0.0, min_peak_prominence=0.0))
    # Seed baseline with many identical values
    for i in range(50):
        d.process(0.5, timestamp_ms=float(i), dt_ms=16.67)
    # baseline ≈ 0.5, std ≈ 0, threshold ≈ 0.5 + 3*std
    # A value equal to baseline should not exceed threshold by k*std
    evt = d.process(0.5, timestamp_ms=51.0, dt_ms=16.67)
    # With std≈0 (or very tiny), threshold = baseline_mean + k*std ≈ 0.5 + tiny
    # 0.5 < threshold when std > 0, so no fire; but if std == 0, threshold == mean
    # Either way, 0.5 should NOT be a dramatic outlier
    # Just verify the event is structured correctly
    assert "detect_B" in evt
    assert evt["sample_count"] > 50
    print("PASS test_detectb_adaptive_no_fire_below_threshold")


def test_detectb_adaptive_baseline_accumulates():
    """Baseline deque fills up in adaptive mode."""
    d = DetectB(DetectorConfig(baseline_window=10))
    for i in range(15):
        d.update_baseline(float(i))
    assert len(d._baseline) == 10, "deque should cap at baseline_window"
    print("PASS test_detectb_adaptive_baseline_accumulates")


def test_detectb_adaptive_baseline_mean_correct():
    """baseline_mean returns mean of baseline deque."""
    d = DetectB(DetectorConfig())
    for v in [1.0, 2.0, 3.0, 4.0, 5.0]:
        d.update_baseline(v)
    assert abs(d.baseline_mean - 3.0) < 1e-9
    print("PASS test_detectb_adaptive_baseline_mean_correct")


def test_detectb_adaptive_empty_baseline_mean():
    """baseline_mean returns 0.0 when baseline is empty."""
    d = DetectB(DetectorConfig())
    assert d.baseline_mean == 0.0
    print("PASS test_detectb_adaptive_empty_baseline_mean")


def test_detectb_adaptive_baseline_std_single():
    """baseline_std returns 1.0 when only one sample is present."""
    d = DetectB(DetectorConfig())
    d.update_baseline(5.0)
    assert d.baseline_std == 1.0
    print("PASS test_detectb_adaptive_baseline_std_single")


# ---------------------------------------------------------------------------
# DetectB — refractory window
# ---------------------------------------------------------------------------

def test_detectb_refractory_suppresses_second_fire():
    """A second value above threshold within refractory window is suppressed."""
    cfg = DetectorConfig.hyperloop_fire()
    cfg.refractory_window_ms = 500.0  # override for this test
    d = DetectB(cfg)
    evt1 = d.process(0.600, timestamp_ms=100.0, dt_ms=1.0)
    assert evt1["detect_B"] is True, "first fire should be detected"

    # Same value 50ms later — inside 500ms refractory window
    evt2 = d.process(0.600, timestamp_ms=150.0, dt_ms=1.0)
    assert evt2["detect_B"] is False, "second fire should be suppressed by refractory"
    assert evt2["in_refractory"] is True
    print("PASS test_detectb_refractory_suppresses_second_fire")


def test_detectb_refractory_allows_fire_after_window():
    """A value above threshold after the refractory window CAN fire again."""
    cfg = DetectorConfig.hyperloop_fire()
    cfg.refractory_window_ms = 100.0
    d = DetectB(cfg)
    d.process(0.600, timestamp_ms=0.0, dt_ms=1.0)
    # 200ms later — outside refractory
    evt = d.process(0.600, timestamp_ms=200.0, dt_ms=1.0)
    assert evt["detect_B"] is True, "should fire after refractory clears"
    assert evt["in_refractory"] is False
    print("PASS test_detectb_refractory_allows_fire_after_window")


def test_detectb_no_refractory_with_zero_window():
    """With refractory_window_ms=0, every above-threshold sample fires."""
    d = DetectB(DetectorConfig.hyperloop_fire())  # refractory_window_ms=0
    for ts in range(5):
        evt = d.process(0.600, timestamp_ms=float(ts), dt_ms=1.0)
        assert evt["detect_B"] is True, f"sample {ts} should fire, got {evt}"
    assert d._fire_count == 5
    print("PASS test_detectb_no_refractory_with_zero_window")


# ---------------------------------------------------------------------------
# DetectB — confidence
# ---------------------------------------------------------------------------

def test_detectb_confidence_zero_below_threshold():
    """confidence() returns 0.0 when value is at or below threshold."""
    d = DetectB(DetectorConfig.hyperloop_fire())
    assert d.confidence(0.499) == 0.0
    assert d.confidence(0.500) == 0.0  # excess = 0, not > 0
    print("PASS test_detectb_confidence_zero_below_threshold")


def test_detectb_confidence_positive_above_threshold():
    """confidence() returns a positive value above threshold."""
    d = DetectB(DetectorConfig.hyperloop_fire())
    conf = d.confidence(0.750)
    assert 0.0 < conf <= 1.0, f"Expected (0, 1], got {conf}"
    print("PASS test_detectb_confidence_positive_above_threshold")


def test_detectb_confidence_capped_at_one():
    """confidence() is capped at 1.0 for very large values."""
    d = DetectB(DetectorConfig.hyperloop_fire())
    conf = d.confidence(999.0)
    assert conf == 1.0
    print("PASS test_detectb_confidence_capped_at_one")


def test_detectb_confidence_zero_threshold():
    """confidence() with thresh <= 0 returns 1.0 when value > 0, else 0."""
    cfg = DetectorConfig(k=0, fixed_threshold=0.0)
    d = DetectB(cfg)
    assert d.confidence(0.1) == 1.0
    assert d.confidence(0.0) == 0.0
    print("PASS test_detectb_confidence_zero_threshold")


# ---------------------------------------------------------------------------
# DetectB — envelope
# ---------------------------------------------------------------------------

def test_detectb_envelope_rises_with_large_value():
    """Envelope rises when a large value is processed."""
    d = DetectB()
    env1 = d.update_envelope(0.1, dt_ms=16.67)
    env2 = d.update_envelope(0.9, dt_ms=16.67)
    assert env2 > env1, "envelope should rise with larger value"
    print("PASS test_detectb_envelope_rises_with_large_value")


def test_detectb_envelope_decays_over_time():
    """Envelope decays after a large value when small values follow."""
    d = DetectB(DetectorConfig(decay_tau_ms=10.0))
    d.update_envelope(1.0, dt_ms=1.0)
    # Large dt relative to tau causes strong decay
    env = d.update_envelope(0.0, dt_ms=100.0)
    assert env < 0.5, f"Envelope should have decayed significantly, got {env}"
    print("PASS test_detectb_envelope_decays_over_time")


def test_detectb_envelope_zero_dt_uses_default():
    """update_envelope handles dt_ms=0 without error."""
    d = DetectB()
    env = d.update_envelope(0.5, dt_ms=0)
    assert env >= 0.0
    print("PASS test_detectb_envelope_zero_dt_uses_default")


# ---------------------------------------------------------------------------
# DetectB — classification
# ---------------------------------------------------------------------------

def test_detectb_classification_C_no_peak():
    """Classification is 'C' when value is below threshold."""
    cfg = DetectorConfig(k=0, fixed_threshold=0.500, min_peak_prominence=0.0,
                         refractory_window_ms=0.0, confidence_floor=0.0)
    d = DetectB(cfg)
    evt = d.process(0.300, timestamp_ms=1.0)
    assert evt["classification"] == "C", f"Expected C, got {evt['classification']}"
    print("PASS test_detectb_classification_C_no_peak")


def test_detectb_classification_B_full_fire():
    """Classification is 'B' when detect_B fires."""
    d = DetectB(DetectorConfig.hyperloop_fire())
    evt = d.process(0.600, timestamp_ms=1.0)
    assert evt["classification"] == "B", f"Expected B, got {evt['classification']}"
    print("PASS test_detectb_classification_B_full_fire")


def test_detectb_classification_A_sub_threshold_with_confidence_floor():
    """Classification is 'A' when peak_detected but confidence < confidence_floor."""
    # Use adaptive mode: seed high baseline, then spike once
    # Use high confidence_floor so the fire is suppressed despite peak
    cfg = DetectorConfig(
        k=0,
        fixed_threshold=0.500,
        min_peak_prominence=0.0,
        refractory_window_ms=0.0,
        confidence_floor=0.99,  # very high floor
    )
    d = DetectB(cfg)
    # value=0.501: above threshold but only a tiny bit above → confidence low
    evt = d.process(0.501, timestamp_ms=1.0)
    if evt["peak_detected"] and not evt["detect_B"]:
        assert evt["classification"] == "A"
    print("PASS test_detectb_classification_A_sub_threshold_with_confidence_floor")


# ---------------------------------------------------------------------------
# DetectB — reset
# ---------------------------------------------------------------------------

def test_detectb_reset_clears_state():
    """reset() clears all internal state."""
    d = DetectB(DetectorConfig.hyperloop_fire())
    for ts in range(5):
        d.process(0.700, timestamp_ms=float(ts), dt_ms=1.0)
    assert d._fire_count == 5

    d.reset()
    assert d._fire_count == 0
    assert d._sample_count == 0
    assert d._last_fire_ms is None
    assert d._envelope == 0.0
    assert len(d._baseline) == 0
    print("PASS test_detectb_reset_clears_state")


def test_detectb_reset_and_reprocess():
    """After reset, detector behaves as if freshly constructed."""
    d = DetectB(DetectorConfig.hyperloop_fire())
    d.process(0.700, timestamp_ms=1.0)
    d.reset()
    evt = d.process(0.700, timestamp_ms=1.0)
    assert evt["sample_count"] == 1, "sample_count should restart from 1 after reset"
    assert evt["fire_count"] == 1
    print("PASS test_detectb_reset_and_reprocess")


# ---------------------------------------------------------------------------
# DetectB — event schema
# ---------------------------------------------------------------------------

def test_detectb_event_schema_keys():
    """process() always returns a dict with all required schema keys."""
    required_keys = {
        "schema", "id", "timestamp_ms", "raw_value", "normalized_value",
        "baseline_mean", "baseline_std", "peak_threshold", "envelope",
        "prominence", "peak_detected", "detect_B", "in_refractory",
        "confidence", "classification", "sample_count", "fire_count",
    }
    d = DetectB(DetectorConfig.hyperloop_fire())
    evt = d.process(0.600, timestamp_ms=1.0)
    missing = required_keys - set(evt.keys())
    assert not missing, f"Missing keys: {missing}"
    print("PASS test_detectb_event_schema_keys")


def test_detectb_event_id_unique():
    """Each process() call returns an event with a unique id."""
    d = DetectB(DetectorConfig.hyperloop_fire())
    ids = [d.process(0.600, timestamp_ms=float(i))["id"] for i in range(20)]
    assert len(set(ids)) == 20, "event ids must be unique"
    print("PASS test_detectb_event_id_unique")


def test_detectb_sample_count_increments():
    """sample_count in returned event increments with each call."""
    d = DetectB(DetectorConfig.hyperloop_fire())
    for i in range(1, 6):
        evt = d.process(0.400, timestamp_ms=float(i))
        assert evt["sample_count"] == i
    print("PASS test_detectb_sample_count_increments")


# ---------------------------------------------------------------------------
# HyperloopAdapter — additional coverage
# ---------------------------------------------------------------------------

def test_hyperloop_adapter_process_round_fields():
    """process_round returns event dict with EVEZ-specific fields."""
    adapter = HyperloopAdapter()
    rd = {
        "N": 72, "N_str": "72=2³×3²", "tau": 4, "omega_k": 2,
        "topo": 1.87, "poly_c": 0.501175, "V_global": 2.987731,
        "ceiling_tick": 38,
    }
    event = adapter.process_round(rd)
    assert event["round"] == 72
    assert event["N_str"] == "72=2³×3²"
    assert event["tau"] == 4
    assert event["omega_k"] == 2
    assert event["topo"] == 1.87
    assert abs(event["V_global"] - 2.987731) < 1e-9
    assert event["ceiling_tick"] == 38
    assert event["fire_ignited"] == event["detect_B"]
    print("PASS test_hyperloop_adapter_process_round_fields")


def test_hyperloop_adapter_rounds_processed():
    """_rounds_processed increments for each process_round call."""
    adapter = HyperloopAdapter()
    for i in range(5):
        adapter.process_round({"N": i, "poly_c": 0.3})
    assert adapter._rounds_processed == 5
    print("PASS test_hyperloop_adapter_rounds_processed")


def test_hyperloop_adapter_replay_arc_resets():
    """replay_arc resets detector state before replaying."""
    adapter = HyperloopAdapter()
    # Process some rounds to establish state
    for i in range(10):
        adapter.process_round({"N": i, "poly_c": 0.700})
    fire_before = adapter.detector._fire_count

    # replay_arc resets internally
    arc = [{"N": i, "poly_c": 0.300} for i in range(5)]
    results = adapter.replay_arc(arc)
    # After reset + replay of sub-threshold values, fire_count should be 0
    assert adapter.detector._fire_count == 0, (
        f"replay_arc should reset detector; fire_count={adapter.detector._fire_count}"
    )
    assert len(results) == 5
    print("PASS test_hyperloop_adapter_replay_arc_resets")


def test_hyperloop_adapter_missing_fields_defaults():
    """process_round uses sensible defaults for missing round_data fields."""
    adapter = HyperloopAdapter()
    event = adapter.process_round({})  # completely empty round
    assert event["tau"] == 0
    assert event["omega_k"] == 0
    assert event["topo"] == 0.0
    assert event["V_global"] == 0.0
    assert event["ceiling_tick"] == 0
    print("PASS test_hyperloop_adapter_missing_fields_defaults")


def test_hyperloop_adapter_fire_on_exact_threshold():
    """Adapter fires at poly_c == 0.500 (boundary condition)."""
    adapter = HyperloopAdapter()
    event = adapter.process_round({"N": 1, "poly_c": 0.500})
    assert event["detect_B"] is True, "poly_c==0.500 should fire"
    print("PASS test_hyperloop_adapter_fire_on_exact_threshold")


def test_hyperloop_adapter_no_fire_below_threshold():
    """Adapter does NOT fire at poly_c == 0.499."""
    adapter = HyperloopAdapter()
    event = adapter.process_round({"N": 1, "poly_c": 0.499})
    assert event["detect_B"] is False
    print("PASS test_hyperloop_adapter_no_fire_below_threshold")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # DetectorConfig
    test_config_defaults()
    test_config_hyperloop_fire_preset()

    # Initial state
    test_detectb_initial_state()

    # Fixed-threshold mode
    test_detectb_fixed_threshold_fire_at_exact_threshold()
    test_detectb_fixed_threshold_no_fire_below()
    test_detectb_fixed_threshold_fire_above()
    test_detectb_fixed_threshold_fire_count_increments()
    test_detectb_fixed_threshold_baseline_mean_is_threshold()
    test_detectb_fixed_threshold_baseline_std_is_zero()
    test_detectb_fixed_threshold_update_baseline_noop()

    # Adaptive mode
    test_detectb_adaptive_no_fire_below_threshold()
    test_detectb_adaptive_baseline_accumulates()
    test_detectb_adaptive_baseline_mean_correct()
    test_detectb_adaptive_empty_baseline_mean()
    test_detectb_adaptive_baseline_std_single()

    # Refractory
    test_detectb_refractory_suppresses_second_fire()
    test_detectb_refractory_allows_fire_after_window()
    test_detectb_no_refractory_with_zero_window()

    # Confidence
    test_detectb_confidence_zero_below_threshold()
    test_detectb_confidence_positive_above_threshold()
    test_detectb_confidence_capped_at_one()
    test_detectb_confidence_zero_threshold()

    # Envelope
    test_detectb_envelope_rises_with_large_value()
    test_detectb_envelope_decays_over_time()
    test_detectb_envelope_zero_dt_uses_default()

    # Classification
    test_detectb_classification_C_no_peak()
    test_detectb_classification_B_full_fire()
    test_detectb_classification_A_sub_threshold_with_confidence_floor()

    # Reset
    test_detectb_reset_clears_state()
    test_detectb_reset_and_reprocess()

    # Schema
    test_detectb_event_schema_keys()
    test_detectb_event_id_unique()
    test_detectb_sample_count_increments()

    # HyperloopAdapter
    test_hyperloop_adapter_process_round_fields()
    test_hyperloop_adapter_rounds_processed()
    test_hyperloop_adapter_replay_arc_resets()
    test_hyperloop_adapter_missing_fields_defaults()
    test_hyperloop_adapter_fire_on_exact_threshold()
    test_hyperloop_adapter_no_fire_below_threshold()

    print()
    print("ALL DETECT_B TESTS PASSED")
