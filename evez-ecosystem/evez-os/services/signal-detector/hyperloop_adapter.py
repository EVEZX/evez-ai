"""hyperloop_adapter.py — Bridge between hyperloop round data and DetectB

Translates the evez-os spine format (poly_c, N, tau, omega_k, topo, V_global)
into signal_event objects via the hyperloop detector.

The fire condition is structurally identical to detect_B:
  poly_c >= 0.500  ==  detect_B (fixed_threshold=0.500)

Usage:
  adapter = HyperloopAdapter()
  for round_data in rounds:
      event = adapter.process_round(round_data)
      if event['detect_B']:
          print(f"FIRE at R{round_data['N']}")
"""

from detect_b import DetectB, DetectorConfig
from typing import Optional


class HyperloopAdapter:
    """Wraps DetectB for hyperloop round data."""

    def __init__(self):
        self.detector = DetectB(DetectorConfig.hyperloop_fire())
        self._rounds_processed: int = 0

    def process_round(self, round_data: dict) -> dict:
        """
        Process one hyperloop round.

        Expected round_data fields:
          N          (int)   — gap number
          poly_c     (float) — composite score
          tau        (int)   — divisor count proxy
          omega_k    (int)   — distinct prime count
          topo       (float) — topological weight
          V_global   (float) — cumulative energy
          ceiling_tick (int) — ceiling counter

        Returns signal_event dict with EVEZ-specific fields appended.
        """
        self._rounds_processed += 1
        poly_c = round_data.get("poly_c", 0.0)
        N = round_data.get("N", self._rounds_processed)

        event = self.detector.process(
            value=poly_c,
            timestamp_ms=float(N),  # round number as timestamp proxy
            dt_ms=1.0,              # one round per tick
        )

        # Append EVEZ-specific fields
        event["round"] = N
        event["N_str"] = round_data.get("N_str", str(N))
        event["tau"] = round_data.get("tau", 0)
        event["omega_k"] = round_data.get("omega_k", 0)
        event["topo"] = round_data.get("topo", 0.0)
        event["V_global"] = round_data.get("V_global", 0.0)
        event["ceiling_tick"] = round_data.get("ceiling_tick", 0)
        event["fire_ignited"] = event["detect_B"]  # canonical EVEZ term

        return event

    def replay_arc(self, rounds: list[dict]) -> list[dict]:
        """Replay a sequence of rounds. Returns list of signal_events."""
        self.detector.reset()
        return [self.process_round(r) for r in rounds]
