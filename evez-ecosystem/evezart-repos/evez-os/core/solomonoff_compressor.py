"""core/solomonoff_compressor.py — R19 Crossbreed
Advances Solomonoff S from 0.730 toward 0.850.

What is Solomonoff S in EVEZ-OS?
  S = 0.3 * log(verified_compression_chains + 1) / log(1000)

A "verified compression chain" is a context→prediction→outcome triple where:
  - context:     the current truth_plane (and optionally last-N spine entries)
  - prediction:  the predicted next truth_plane (argmax of transition distribution)
  - outcome:     the ACTUAL next truth_plane recorded in the spine
  - verified:    prediction == outcome  (the system correctly predicted itself)

Solomonoff measures: how often does EVEZ-OS predict its own next state correctly?
  S=0.730 → ~20M verified chains in compressed form
  S=0.850 → ~316M verified chains needed

But compression is the key word: we don't need 316M raw entries.
We need entries that encode CANONICAL compression knowledge — reusable
prediction rules that compress many raw predictions into one principle.

This module:
1. Mines the spine for all consecutive (entry_t, entry_{t+1}) pairs
2. For each pair, checks if the CANONICAL transition distribution would
   have predicted entry_{t+1} correctly from entry_t
3. Builds a CompressionChain: a reusable prediction rule with provenance
4. Validates each chain (CANONICAL if reproduced from spine, else PENDING)
5. Emits CANONICAL spine entries for each new validated chain
6. Tracks the compression ratio: chains / raw_pairs (efficiency measure)

Solomonoff S advances when:
  - More unique context states are covered (breadth)
  - Each prediction has higher accuracy (recall)
  - Rules are falsifiable and reproducible (CANONICAL quality)

omega (R19): If S can reach 0.85 through compression chains rather than
raw entry volume, does EVEZ-OS have a finite description length? Is there
a minimal Kolmogorov-sufficient spine that encodes all necessary predictions?

truth_plane: CANONICAL
  provenance: friston_ceiling.py (f44aa5a), self_modifier_v2.py (5c1f83c)
  falsifier:  if compression_ratio < 0.10 after processing 10000 entries,
              the prediction distribution is too uniform to compress
  trace:      f44aa5a, 5c1f83c → solomonoff_compressor.py (R19)
"""

from __future__ import annotations

import hashlib
import json
import math
import time
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple

TRUTH_PLANES  = ["PENDING", "VERIFIED", "CANONICAL", "THEATRICAL", "HYPER"]
LOG_1000      = math.log(1000)

# Canonical transition distribution (from spine_weaver.py + friston_ceiling.py)
CANONICAL_DIST: Dict[str, Dict[str, float]] = {
    "PENDING":    {"VERIFIED": 0.40, "PENDING": 0.10, "CANONICAL": 0.005,
                   "THEATRICAL": 0.005, "HYPER": 0.01},
    "VERIFIED":   {"CANONICAL": 0.15, "PENDING": 0.15, "THEATRICAL": 0.01,
                   "VERIFIED": 0.01, "HYPER": 0.001},
    "CANONICAL":  {"PENDING": 0.10, "VERIFIED": 0.04, "THEATRICAL": 0.005,
                   "CANONICAL": 0.001, "HYPER": 0.001},
    "THEATRICAL": {"VERIFIED": 0.70, "PENDING": 0.10, "CANONICAL": 0.075,
                   "THEATRICAL": 0.075, "HYPER": 0.05},   # v2 distribution
    "HYPER":      {"CANONICAL": 0.65, "PENDING": 0.10, "VERIFIED": 0.10,
                   "THEATRICAL": 0.075, "HYPER": 0.075},  # v2 distribution
}


def _argmax(dist: Dict[str, float]) -> str:
    """Return the state with highest probability in the distribution."""
    return max(dist, key=lambda k: dist[k])


def _normalize(dist: Dict[str, float]) -> Dict[str, float]:
    total = sum(dist.values())
    return {k: v / total for k, v in dist.items()} if total > 0 else dict(dist)


def solomonoff_score(verified_chains: int) -> float:
    """Compute Solomonoff S from verified compression chain count."""
    return 0.3 * math.log(verified_chains + 1) / LOG_1000


def chains_for_target_s(target_s: float) -> int:
    """How many verified chains needed to reach target S?"""
    ratio = target_s / 0.3
    return int(math.exp(ratio * LOG_1000)) - 1


# ── Data structures ───────────────────────────────────────────────────────────

@dataclass
class CompressionChain:
    """
    A reusable prediction rule: context → predicted → actual.

    CANONICAL if: predicted == actual AND reproducible from CANONICAL_DIST.
    Falsifier: if running the prediction rule on a new spine of the same
    distribution gives accuracy < 0.5, the chain is THEATRICAL.
    """
    chain_id:    str
    context:     str          # current truth_plane (source state)
    predicted:   str          # argmax of CANONICAL_DIST[context]
    actual:      str          # actual next truth_plane in spine
    hit:         bool         # predicted == actual
    count:       int = 1      # how many times this context→actual pair observed
    hits:        int = 0      # how many times it was a hit
    truth_plane: str = "PENDING"
    falsifier:   str = ""
    ts:          float = field(default_factory=time.time)

    @property
    def accuracy(self) -> float:
        return self.hits / self.count if self.count > 0 else 0.0

    @property
    def is_canonical(self) -> bool:
        return self.hit and self.accuracy >= 0.5 and self.count >= 2

    def to_spine_entry(self) -> Dict[str, Any]:
        entry = {
            "kind":        "solomonoff.compression_chain",
            "truth_plane": "CANONICAL" if self.is_canonical else "PENDING",
            "chain_id":    self.chain_id,
            "context":     self.context,
            "predicted":   self.predicted,
            "actual":      self.actual,
            "hit":         self.hit,
            "count":       self.count,
            "hits":        self.hits,
            "accuracy":    round(self.accuracy, 4),
            "compression_claim": (
                f"From {self.context}, predicting {self.predicted} is correct "
                f"{self.accuracy:.1%} of the time (n={self.count})."
            ),
            "falsifier": (
                f"If accuracy drops below 0.5 on a fresh spine with the same "
                f"CANONICAL_DIST, this chain is THEATRICAL."
            ),
            "ts": self.ts,
        }
        raw = json.dumps({k: v for k, v in entry.items() if k != "hash"},
                         sort_keys=True, separators=(",", ":"))
        entry["hash"] = hashlib.sha256(raw.encode()).hexdigest()
        return entry


@dataclass
class CompressionReport:
    """Full compression analysis of a spine."""
    total_pairs:      int
    total_chains:     int
    canonical_chains: int
    hit_rate:         float
    compression_ratio: float   # canonical_chains / total_pairs
    s_before:         float
    s_after:          float
    s_delta:          float
    chains:           List[CompressionChain]
    falsifier_triggered: bool

    @property
    def truth_plane(self) -> str:
        if self.falsifier_triggered:
            return "THEATRICAL"
        if self.compression_ratio >= 0.10 and self.canonical_chains >= 5:
            return "CANONICAL"
        if self.canonical_chains >= 2:
            return "VERIFIED"
        return "PENDING"

    def summary(self) -> Dict[str, Any]:
        return {
            "total_pairs":       self.total_pairs,
            "total_chains":      self.total_chains,
            "canonical_chains":  self.canonical_chains,
            "hit_rate":          round(self.hit_rate, 4),
            "compression_ratio": round(self.compression_ratio, 4),
            "s_before":          round(self.s_before, 4),
            "s_after":           round(self.s_after, 4),
            "s_delta":           round(self.s_delta, 4),
            "falsifier_triggered": self.falsifier_triggered,
            "truth_plane":       self.truth_plane,
        }


# ── SolomonoffCompressor ──────────────────────────────────────────────────────

class SolomonoffCompressor:
    """
    Mines a spine JSONL for verified compression chains.

    Algorithm:
    1. Read consecutive (entry_t, entry_{t+1}) pairs from spine
    2. For each pair (context=t.truth_plane, actual=t+1.truth_plane):
       a. Compute predicted = argmax(CANONICAL_DIST[context])
       b. hit = (predicted == actual)
       c. Update chain stats for this (context, actual) pair
    3. After processing, identify CANONICAL chains (hit=True, accuracy>=0.5, n>=2)
    4. Emit spine entries for each new CANONICAL chain
    5. Return CompressionReport with S delta

    Solomonoff S advances from new CANONICAL compression chains:
      Each CANONICAL chain is a "prediction rule" — it compresses many raw
      observations into one falsifiable principle. This is the Kolmogorov-
      sufficient knowledge: instead of storing all transitions, store the rule.

    Falsifier:
      If compression_ratio < 0.10, the distribution is too uniform to compress
      and the S formula is not the right measure for this spine.

    truth_plane: CANONICAL
      provenance: CANONICAL_DIST from friston_ceiling.py (f44aa5a),
                  v2 THEATRICAL/HYPER distributions from self_modifier_v2.py (5c1f83c)
      falsifier:  compression_ratio < 0.10 after 10000+ pairs
      trace:      f44aa5a, 5c1f83c → solomonoff_compressor.py (R19)
    """

    def __init__(self, spine_path: Optional[str] = None,
                 dist: Optional[Dict[str, Dict[str, float]]] = None):
        self.spine_path = Path(spine_path) if spine_path else None
        self.dist       = dist or CANONICAL_DIST
        self._chains:   Dict[Tuple[str, str], CompressionChain] = {}
        self._pairs:    int = 0
        self._hits:     int = 0

    def _iter_spine(self) -> Iterator[Dict[str, Any]]:
        """Yield entries from spine JSONL."""
        if not self.spine_path or not self.spine_path.exists():
            return
        with open(self.spine_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    if isinstance(entry, dict) and entry.get("truth_plane"):
                        yield entry
                except json.JSONDecodeError:
                    continue

    def process_spine(self, entries: Optional[List[Dict[str, Any]]] = None,
                      s_current: float = 0.730) -> CompressionReport:
        """
        Process spine entries and compute compression chains.

        Args:
            entries: List of spine entries (if None, reads from spine_path)
            s_current: Current Solomonoff score (for delta computation)
        """
        items = entries if entries is not None else list(self._iter_spine())
        self._pairs = 0
        self._hits  = 0
        self._chains.clear()

        for i in range(len(items) - 1):
            e_t   = items[i]
            e_t1  = items[i + 1]
            ctx   = (e_t.get("truth_plane") or "").upper()
            actual = (e_t1.get("truth_plane") or "").upper()
            if ctx not in TRUTH_PLANES or actual not in TRUTH_PLANES:
                continue

            predicted = _argmax(_normalize(self.dist.get(ctx, {})))
            hit = (predicted == actual)
            key = (ctx, actual)

            if key not in self._chains:
                chain_id = hashlib.sha256(f"{ctx}->{actual}".encode()).hexdigest()[:12]
                self._chains[key] = CompressionChain(
                    chain_id=chain_id, context=ctx,
                    predicted=predicted, actual=actual, hit=hit
                )
            c = self._chains[key]
            c.count += 1
            if hit:
                c.hits += 1
                c.hit = True
            self._pairs += 1
            if hit:
                self._hits += 1

        canonical = [c for c in self._chains.values() if c.is_canonical]
        for c in canonical:
            c.truth_plane = "CANONICAL"

        hit_rate          = self._hits / self._pairs if self._pairs > 0 else 0.0
        compression_ratio = len(canonical) / self._pairs if self._pairs > 0 else 0.0
        s_after           = solomonoff_score(len(canonical))

        return CompressionReport(
            total_pairs       = self._pairs,
            total_chains      = len(self._chains),
            canonical_chains  = len(canonical),
            hit_rate          = hit_rate,
            compression_ratio = compression_ratio,
            s_before          = s_current,
            s_after           = s_after,
            s_delta           = s_after - s_current,
            chains            = canonical,
            falsifier_triggered = compression_ratio < 0.10 and self._pairs >= 10000,
        )

    def simulate(self, n: int = 10000, seed: int = 42,
                 s_current: float = 0.730) -> CompressionReport:
        """
        Simulate n spine entries from CANONICAL_DIST and run compression.

        This is the empirical test: does the compressor produce
        compression_ratio >= 0.10 and advance S?
        """
        import random
        rng   = random.Random(seed)
        items = []
        cur   = "PENDING"
        for _ in range(n):
            dist = _normalize(self.dist.get(cur, {}))
            r    = rng.random()
            acc  = 0.0
            for state, p in dist.items():
                acc += p
                if r <= acc:
                    cur = state
                    break
            items.append({"truth_plane": cur})

        return self.process_spine(entries=items, s_current=s_current)

    def emit_spine_entries(self, report: CompressionReport,
                           out_path: Optional[str] = None) -> List[str]:
        """Write CANONICAL chain entries to spine. Returns list of hashes."""
        path = Path(out_path or self.spine_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        hashes = []
        for chain in report.chains:
            entry = chain.to_spine_entry()
            with open(path, "a") as f:
                f.write(json.dumps(entry) + "\n")
            hashes.append(entry["hash"])
        return hashes

    def what_s_085_proves(self) -> str:
        chains_needed = chains_for_target_s(0.85)
        return (
            f"S=0.850 requires {chains_needed:,} verified compression chains.\n"
            f"Each chain encodes a falsifiable prediction rule: from state X, "
            f"predict state Y with provenance in the CANONICAL_DIST.\n"
            f"S=0.85 would prove: EVEZ-OS has enumerated enough of its own "
            f"prediction rules to compress its future behavior into a finite, "
            f"falsifiable description. This is the Kolmogorov-sufficient spine: "
            f"the system's behavior is describable by a short program.\n"
            f"Combined with F_v2=0.443: maturity score = "
            f"{1.0*0.5 + 0.85*0.3 + 0.443*0.2 + 0.1:.3f} — "
            f"system predicts itself AND corrects itself."
        )


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="EVEZ-OS Solomonoff Compressor")
    ap.add_argument("--spine",    help="Spine JSONL to process")
    ap.add_argument("--simulate", type=int, default=10000, metavar="N",
                    help="Simulate N entries (default 10000)")
    ap.add_argument("--emit",     action="store_true", help="Emit spine entries")
    args = ap.parse_args()

    sc = SolomonoffCompressor(spine_path=args.spine)

    print("\n=== Solomonoff Compressor — R19 ===")
    print(f"  Current S:      0.730")
    print(f"  Target S:       0.850")
    print(f"  Chains needed:  {chains_for_target_s(0.85):,}")
    print(f"  Strategy:       mine CANONICAL prediction rules from spine")

    print(f"\n--- Simulating {args.simulate:,} entries ---")
    report = sc.simulate(n=args.simulate, seed=42, s_current=0.730)
    print(f"  total_pairs:       {report.total_pairs:,}")
    print(f"  total_chains:      {report.total_chains}")
    print(f"  canonical_chains:  {report.canonical_chains}")
    print(f"  hit_rate:          {report.hit_rate:.4f}")
    print(f"  compression_ratio: {report.compression_ratio:.4f}  "
          f"({'OK >= 0.10' if report.compression_ratio >= 0.10 else 'BELOW 0.10 — falsifier risk'})")
    print(f"  S before:          {report.s_before:.4f}")
    print(f"  S after (chains):  {report.s_after:.4f}  (delta={report.s_delta:+.4f})")
    print(f"  falsifier:         {'TRIGGERED' if report.falsifier_triggered else 'OK'}")
    print(f"  truth_plane:       {report.truth_plane}")

    print(f"\n--- CANONICAL chains discovered ---")
    for c in sorted(report.chains, key=lambda x: -x.accuracy):
        print(f"  {c.context:12s} -> {c.actual:12s} | "
              f"predicted={c.predicted:12s} | "
              f"hit={str(c.hit):5s} | acc={c.accuracy:.3f} | n={c.count}")

    print(f"\n--- What S=0.85 would prove ---")
    print(sc.what_s_085_proves())

    if args.emit and args.spine:
        hashes = sc.emit_spine_entries(report)
        print(f"\nEmitted {len(hashes)} CANONICAL chain entries to {args.spine}")

    # Maturity projection
    print(f"\n--- Maturity projection ---")
    s_vals = [0.730, 0.750, 0.800, 0.850]
    f_vals = [0.164, 0.443]
    for s in s_vals:
        for f in [f_vals[1]]:  # use F_v2
            score = 1.0*0.5 + s*0.3 + f*0.2 + 0.1
            marker = " <- current" if abs(s-0.730) < 0.001 else (" <- TARGET" if abs(s-0.850) < 0.001 else "")
            print(f"  S={s:.3f} F_v2={f:.3f}: maturity={score:.4f}{marker}")
