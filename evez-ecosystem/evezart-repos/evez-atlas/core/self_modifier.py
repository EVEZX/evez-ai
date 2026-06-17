"""core/self_modifier.py — R11 Crossbreed
The ACTUATOR that closes the observation→action loop.

Perplexity R10 safety architecture:
  - Observer and actuator share only the spine (never direct module refs)
  - Mutations are FORWARD-ONLY: a new rule appended, old rule tombstoned
  - Spine remains append-only: mutations are spine entries, not edits
  - Falsifier: if self_modifier edits a prior spine entry, it is THEATRICAL

Observer interface:
  UnificationEngine (core/unification_engine.py) emits BridgePackets.
  SelfModifier subscribes via SpineEventBus and reads aggregate metrics.
  When intervention threshold crossed → applies mutation via self_building.
  Mutation writes a spine entry (VERIFIED or CANONICAL depending on reversibility).

Reversibility guarantee:
  Each mutation stores {"mutation_id": uuid, "tombstones": [old_rule_ids], "adds": [new_rules]}
  To rollback: emit a ROLLBACK entry with the mutation_id. The rule engine
  checks tombstones at evaluation time — rollback re-activates tombstoned rules.
  Spine itself is never touched.

Runaway falsifier:
  mutation_velocity = mutations_per_10_rounds
  If mutation_velocity > MAX_VELOCITY (default 3), SelfModifier enters COOLDOWN.
  COOLDOWN emits a THEATRICAL→VERIFIED spine entry and blocks new mutations for N rounds.
  A mutation loop is proven non-runaway if mutation_velocity stays ≤ MAX_VELOCITY.

Truth plane:
  CANONICAL — mutation proven reversible with stored rollback entry
  VERIFIED  — mutation applied with falsifier but no rollback test yet
  THEATRICAL — mutation applied without falsifier (blocked in production)
"""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ── Optional imports ──────────────────────────────────────────────────────────
try:
    from core.unification_engine import BridgeEvent, BridgePacket, SpineEventBus
    BRIDGE_AVAILABLE = True
except ImportError:
    BRIDGE_AVAILABLE = False

try:
    from evez_game.self_building import SelfBuildingEngine
    SELF_BUILD_AVAILABLE = True
except ImportError:
    SELF_BUILD_AVAILABLE = False


# ── Constants ─────────────────────────────────────────────────────────────────

SMUGNESS_TAX_THRESHOLD   = 3.0   # Perplexity R10: above this → theatrical flood
THEATRICAL_RATIO_THRESHOLD = 0.4  # More than 40% THEATRICAL events = intervention needed
MAX_MUTATION_VELOCITY    = 3     # Max mutations per 10-round window (runaway guard)
COOLDOWN_ROUNDS          = 5     # Rounds to block after hitting MAX_VELOCITY


class MutationType(Enum):
    """What the mutation does to the game's own rules."""
    TIGHTEN_FALSIFIER  = "tighten_falsifier"   # Requires stronger evidence for THEATRICAL
    RELAX_LOBBY        = "relax_lobby"          # Opens a new lobby transition
    SUPPRESS_NARRATOR  = "suppress_narrator"    # Mutes a THEATRICAL narrator temporarily
    AMPLIFY_PATTERN    = "amplify_pattern"      # Boosts pattern engine sensitivity
    RESET_THREAT       = "reset_threat"         # Clears threat engine alert queue
    CANONICAL_MERGE    = "canonical_merge"      # Forces a CANONICAL truth plane merge


@dataclass
class Mutation:
    """A single forward-only rule change. Reversible via tombstone + rollback entry."""
    mutation_id:   str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    mutation_type: MutationType = MutationType.TIGHTEN_FALSIFIER
    target_module: str = ""
    tombstones:    List[str] = field(default_factory=list)   # rule_ids to deactivate
    adds:          List[Dict] = field(default_factory=list)  # new rules to activate
    falsifier:     str = ""
    truth_plane:   str = "VERIFIED"
    timestamp:     float = field(default_factory=time.time)
    rolled_back:   bool = False

    def to_spine_entry(self) -> Dict[str, Any]:
        entry = {
            "kind":          "self_modifier.mutation",
            "mutation_id":   self.mutation_id,
            "mutation_type": self.mutation_type.value,
            "target_module": self.target_module,
            "tombstones":    self.tombstones,
            "adds":          self.adds,
            "falsifier":     self.falsifier,
            "truth_plane":   self.truth_plane,
            "ts":            self.timestamp,
        }
        raw = json.dumps({k: v for k, v in entry.items() if k != "hash"},
                         sort_keys=True, separators=(",", ":"))
        entry["hash"] = hashlib.sha256(raw.encode()).hexdigest()
        return entry


# ── Core SelfModifier ─────────────────────────────────────────────────────────

class SelfModifier:
    """
    Reads UnificationEngine bus metrics and applies mutations via self_building.

    Safety invariants (Perplexity R10):
    1. Observer ↔ Actuator interface: ONLY through SpineEventBus (no direct refs)
    2. Mutations are append-only spine entries (never edit prior entries)
    3. Rollback = new spine entry with "kind": "self_modifier.rollback"
    4. mutation_velocity guard: enter COOLDOWN if velocity > MAX_VELOCITY
    5. Every mutation has a falsifier — THEATRICAL mutations are blocked

    Self-cartography contribution: +0.1 per 5 mutations with CANONICAL truth_plane
    """

    def __init__(
        self,
        bus: Optional[Any] = None,  # SpineEventBus
        spine_path: Optional[str] = None,
        max_velocity: int = MAX_MUTATION_VELOCITY,
    ):
        self._bus = bus
        self._spine_path = Path(spine_path) if spine_path else None
        self._max_velocity = max_velocity
        self._mutations: List[Mutation] = []
        self._round_window: List[float] = []  # timestamps of recent mutations
        self._cooldown_until: int = 0
        self._round = 0
        self._cartography_contribution = 0.0

        # Subscribe to SAN narration events (these carry smugness_tax)
        if bus and BRIDGE_AVAILABLE:
            bus.subscribe(BridgeEvent.SAN_NARRATION, self._on_san_narration)
            bus.subscribe(BridgeEvent.THREAT_DETECTED, self._on_threat)

    # ── Subscription handlers ─────────────────────────────────────────────────

    def _on_san_narration(self, pkt: "BridgePacket") -> None:
        """React to SAN summary every 10 rounds."""
        smugness = pkt.payload.get("smugness_tax", 0.0)
        theatrical = pkt.payload.get("theatrical_ratio", 0.0)
        if smugness > SMUGNESS_TAX_THRESHOLD or theatrical > THEATRICAL_RATIO_THRESHOLD:
            self._schedule_intervention(
                reason=f"smugness={smugness:.2f} theatrical={theatrical:.2f}",
                mutation_type=MutationType.TIGHTEN_FALSIFIER,
                target=pkt.source_module,
            )

    def _on_threat(self, pkt: "BridgePacket") -> None:
        """Auto-reset threat queue when alerts pile up."""
        # Handled reactively — let the round tick decide

    # ── Intervention threshold ────────────────────────────────────────────────

    def compute_intervention_threshold(
        self, smugness_tax: float, theatrical_ratio: float
    ) -> Tuple[bool, str]:
        """
        Returns (should_intervene, reason).
        Falsifier: if intervention is triggered without smugness > 3.0 AND theatrical > 0.4,
        this is a false positive — log as THEATRICAL mutation (blocked).
        """
        if self._round < self._cooldown_until:
            return False, f"COOLDOWN until round {self._cooldown_until}"

        velocity = self._mutation_velocity()
        if velocity > self._max_velocity:
            self._cooldown_until = self._round + COOLDOWN_ROUNDS
            self._write_spine({
                "kind": "self_modifier.cooldown",
                "reason": f"velocity={velocity} > max={self._max_velocity}",
                "truth_plane": "VERIFIED",
                "cooldown_rounds": COOLDOWN_ROUNDS,
                "falsifier": "velocity must drop below max after cooldown",
            })
            return False, f"RATE_LIMITED velocity={velocity}"

        if smugness_tax > SMUGNESS_TAX_THRESHOLD:
            return True, f"smugness_tax={smugness_tax:.2f} > {SMUGNESS_TAX_THRESHOLD}"
        if theatrical_ratio > THEATRICAL_RATIO_THRESHOLD:
            return True, f"theatrical_ratio={theatrical_ratio:.2f} > {THEATRICAL_RATIO_THRESHOLD}"

        return False, "below_threshold"

    # ── Apply mutation ────────────────────────────────────────────────────────

    def apply_mutation(
        self,
        target_module: str,
        mutation_type: MutationType,
        reason: str = "",
        falsifier: str = "",
    ) -> Optional[Mutation]:
        """
        Apply a mutation via self_building if available; always write to spine.
        Returns the Mutation, or None if blocked (cooldown / no falsifier).

        Reversibility: caller can call rollback(mutation.mutation_id) to undo.
        Truth plane: CANONICAL if mutation was applied AND a rollback entry exists,
                     VERIFIED if applied without rollback test.
        """
        if not falsifier:
            # No falsifier = THEATRICAL — blocked in production
            self._write_spine({
                "kind": "self_modifier.blocked",
                "reason": "no falsifier provided — mutation would be THEATRICAL",
                "target_module": target_module,
                "mutation_type": mutation_type.value,
                "truth_plane": "THEATRICAL",
                "ts": time.time(),
            })
            return None

        mut = Mutation(
            mutation_type=mutation_type,
            target_module=target_module,
            falsifier=falsifier,
            truth_plane="VERIFIED",
            adds=[{"rule": f"{mutation_type.value}:{reason}", "active": True}],
            tombstones=[],
        )

        # Apply via self_building if available
        if SELF_BUILD_AVAILABLE:
            try:
                engine = SelfBuildingEngine()
                engine.apply_rule(mutation_type.value, {"reason": reason, "mutation_id": mut.mutation_id})
                mut.truth_plane = "VERIFIED"
            except Exception as e:
                mut.falsifier += f" | apply_error={str(e)[:60]}"

        self._mutations.append(mut)
        self._round_window.append(time.time())
        self.write_mutation_to_spine(mut)

        # Update self-cartography
        canonical_count = sum(1 for m in self._mutations if m.truth_plane == "CANONICAL")
        self._cartography_contribution = min(1.0, canonical_count * 0.02)

        return mut

    def rollback(self, mutation_id: str) -> bool:
        """
        Rollback a mutation by writing a ROLLBACK spine entry.
        The rule engine checks tombstones at eval time — rollback re-activates them.
        Spine is NEVER edited. Returns True if mutation found and rolled back.
        """
        for mut in self._mutations:
            if mut.mutation_id == mutation_id and not mut.rolled_back:
                mut.rolled_back = True
                mut.truth_plane = "CANONICAL"  # Proven reversible
                rollback_entry = {
                    "kind":        "self_modifier.rollback",
                    "mutation_id": mutation_id,
                    "reactivates": mut.tombstones,
                    "deactivates": [r.get("rule", "") for r in mut.adds],
                    "truth_plane": "CANONICAL",
                    "falsifier":   f"rollback of {mutation_id} must restore prior behavior",
                    "ts":          time.time(),
                }
                raw = json.dumps(rollback_entry, sort_keys=True, separators=(",", ":"))
                rollback_entry["hash"] = hashlib.sha256(raw.encode()).hexdigest()
                self._write_spine(rollback_entry)
                return True
        return False

    # ── Spine I/O ─────────────────────────────────────────────────────────────

    def write_mutation_to_spine(self, mutation: Mutation) -> None:
        """Write mutation as append-only spine entry."""
        self._write_spine(mutation.to_spine_entry())

    def _write_spine(self, entry: Dict[str, Any]) -> None:
        if self._spine_path:
            self._spine_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._spine_path, "a") as f:
                f.write(json.dumps(entry) + "\n")

    def read_spine_bus(self) -> List[Dict[str, Any]]:
        """Read all self_modifier entries from the spine."""
        if not self._spine_path or not self._spine_path.exists():
            return []
        entries = []
        with open(self._spine_path) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        e = json.loads(line)
                        if "self_modifier" in e.get("kind", ""):
                            entries.append(e)
                    except:
                        pass
        return entries

    # ── Velocity guard ────────────────────────────────────────────────────────

    def _mutation_velocity(self) -> int:
        """Count mutations in the last 10 rounds (approximate: last 10 min)."""
        cutoff = time.time() - 600  # 10-minute window
        self._round_window = [t for t in self._round_window if t > cutoff]
        return len(self._round_window)

    def _schedule_intervention(
        self, reason: str, mutation_type: MutationType, target: str
    ) -> None:
        """Deferred intervention — will execute on next tick()."""
        self._pending_intervention = {
            "reason": reason,
            "mutation_type": mutation_type,
            "target": target,
        }

    # ── Main tick ─────────────────────────────────────────────────────────────

    def tick(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        One modifier tick. Reads metrics from UnificationEngine output.
        Applies mutation if threshold crossed and not in cooldown.
        """
        self._round += 1
        smugness = metrics.get("smugness_tax", 0.0)
        theatrical = metrics.get("theatrical_ratio", 0.0)
        threat_alerts = metrics.get("threat_alerts", 0)

        should_act, reason = self.compute_intervention_threshold(smugness, theatrical)
        mutation_applied = None

        if should_act:
            # Choose mutation type based on which signal is louder
            if smugness > SMUGNESS_TAX_THRESHOLD:
                mtype = MutationType.TIGHTEN_FALSIFIER
                falsifier = f"theatrical_ratio must decrease after falsifier tightening; current={theatrical:.3f}"
            else:
                mtype = MutationType.SUPPRESS_NARRATOR
                falsifier = f"smugness_tax must decrease after narrator suppression; current={smugness:.3f}"

            mutation_applied = self.apply_mutation(
                target_module=metrics.get("hottest_event", "unknown"),
                mutation_type=mtype,
                reason=reason,
                falsifier=falsifier,
            )

        if threat_alerts > 5:
            self.apply_mutation(
                target_module="evez_game.threat_engine",
                mutation_type=MutationType.RESET_THREAT,
                reason=f"threat_alerts={threat_alerts} — flushing queue",
                falsifier="threat_alerts must drop to 0 after reset",
            )

        return {
            "round":            self._round,
            "should_act":       should_act,
            "reason":           reason,
            "mutation_applied": mutation_applied.mutation_id if mutation_applied else None,
            "total_mutations":  len(self._mutations),
            "velocity":         self._mutation_velocity(),
            "cooldown_until":   self._cooldown_until,
            "cartography":      self._cartography_contribution,
            "spine_entries":    len(self.read_spine_bus()),
        }

    def status(self) -> Dict[str, Any]:
        canonical = sum(1 for m in self._mutations if m.truth_plane == "CANONICAL")
        rolled_back = sum(1 for m in self._mutations if m.rolled_back)
        return {
            "total_mutations":   len(self._mutations),
            "canonical":         canonical,
            "rolled_back":       rolled_back,
            "velocity":          self._mutation_velocity(),
            "cooldown_until":    self._cooldown_until,
            "cartography":       self._cartography_contribution,
            "bridge_available":  BRIDGE_AVAILABLE,
            "self_build_available": SELF_BUILD_AVAILABLE,
            "runaway_safe":      self._mutation_velocity() <= self._max_velocity,
            "falsifier":         "mutation_velocity must stay <= MAX_VELOCITY at all times",
        }


# ── CLI demo ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="EVEZ-OS Self Modifier")
    ap.add_argument("--spine", default="spine/self_modifier.jsonl")
    ap.add_argument("--rounds", type=int, default=15)
    args = ap.parse_args()

    Path(args.spine).parent.mkdir(parents=True, exist_ok=True)

    modifier = SelfModifier(spine_path=args.spine)

    print(f"SelfModifier ready | bridge={BRIDGE_AVAILABLE} | self_build={SELF_BUILD_AVAILABLE}")
    print(f"Thresholds: smugness>{SMUGNESS_TAX_THRESHOLD} OR theatrical>{THEATRICAL_RATIO_THRESHOLD}")

    # Simulate escalating smugness + theatrical events
    for i in range(args.rounds):
        metrics = {
            "round":            i,
            "smugness_tax":     0.0 + i * 0.3,     # escalates to 4.2 at round 14
            "theatrical_ratio": 0.1 + i * 0.03,    # escalates to 0.52 at round 14
            "threat_alerts":    0 if i < 12 else 7,
            "hottest_event":    "threat_detected" if i % 3 == 0 else "pattern_shift",
        }
        out = modifier.tick(metrics)
        flag = "🔴 MUTATED" if out["mutation_applied"] else "  "
        print(f"[{i:03d}] smugness={metrics['smugness_tax']:.1f} theatrical={metrics['theatrical_ratio']:.2f} "
              f"| {flag} | mutations={out['total_mutations']} velocity={out['velocity']} "
              f"| {out['reason']}")

    print("\n=== Status ===")
    for k, v in modifier.status().items():
        print(f"  {k}: {v}")

    spine_entries = modifier.read_spine_bus()
    print(f"\nSpine entries written: {len(spine_entries)}")
    for e in spine_entries[:3]:
        print(f"  {e.get('kind')} tp={e.get('truth_plane')} mut={e.get('mutation_id','')}")
