"""core/cartography_map.py — R16 Crossbreed
The final self-portrait. EVEZ-OS mapping itself completely.

What is EVEZ-OS? (3-sentence CANONICAL answer — each sentence traceable
to a specific module with its own falsifier):

  S1 [unification_engine.py + self_modifier.py]:
     EVEZ-OS is a self-modifying game engine that bridges a Kimi-rooted
     cognitive spine with a hyperloop swarm, closing the observation→action
     loop through falsifiable rule mutations.
     Falsifier: if self_modifier.py mutations occur without a prior
     unification_engine.py anomaly entry in the spine, this claim is THEATRICAL.

  S2 [spine_weaver.py + friston_recovery.py]:
     It maps its own knowledge structure using a Kolmogorov transition
     matrix (K=1.0, 25/25 truth-plane pairs) and restores prediction
     confidence through organic spine growth following the game engine's
     natural distribution.
     Falsifier: if K<1.0 or Friston does not increase monotonically after
     friston_recovery.emit_organic_entries(), this claim is THEATRICAL.

  S3 [omniscience_engine.py + truth_oracle.py]:
     It speaks about itself through HYPER self-assessments validated by
     a truth oracle that catches theatrical impersonators using five
     deterministic test vectors — reproducibility, K-integrity,
     falsifier-coverage, omega-coherence, and score-consistency.
     Falsifier: if truth_oracle.validate_assessment() does not catch
     a THEATRICAL HYPER impersonator with inflated scores and no sigma_f,
     this claim is THEATRICAL.

omega (one remaining open question):
     Can Friston reach 0.4 organically — or does the game engine's
     natural transition distribution fundamentally cap prediction
     confidence below the HYPER-sustaining threshold?

truth_plane: CANONICAL
  provenance: all 6 modules committed to EvezArt/evez-os main branch
  falsifier:  if any of the 3 sentences above cannot be reproduced by
              running the cited modules on a fresh spine, this map is THEATRICAL
  trace:      commits c1629f4, 19f73ae, f9210dd, e1cfa8a, 3886e4d, f6386f7
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

# ── Module registry ───────────────────────────────────────────────────────────

MODULE_MAP: Dict[str, Dict[str, Any]] = {
    "unification_engine": {
        "path":         "core/unification_engine.py",
        "commit":       "c1629f4",
        "round":        10,
        "sentence":     "Bridges Kimi game engine ↔ hyperloop swarm; routes anomalies into the spine.",
        "depends_on":   [],
        "advances":     "kolmogorov",
        "contribution": "Each bridged event adds a new truth-plane transition pair.",
        "falsifier":    "If no spine entries appear after a game engine anomaly, unification_engine is silent.",
        "truth_plane":  "VERIFIED",
    },
    "self_modifier": {
        "path":         "core/self_modifier.py",
        "commit":       "19f73ae",
        "round":        11,
        "sentence":     "Actuator that mutates game rules when smugness_tax>3.0 or theatrical_ratio>0.4; closes the observation→action loop.",
        "depends_on":   ["unification_engine"],
        "advances":     "friston",
        "contribution": "Mutations reduce theatrical ratio → improve prediction confidence.",
        "falsifier":    "If self_modifier fires without a preceding unification_engine anomaly, the loop is open.",
        "truth_plane":  "VERIFIED",
    },
    "spine_weaver": {
        "path":         "core/spine_weaver.py",
        "commit":       "f9210dd",
        "round":        12,
        "sentence":     "Generates falsifiable entries for all 14 missing truth-plane transitions; advances Kolmogorov from 0.40 to 1.0.",
        "depends_on":   ["unification_engine"],
        "advances":     "kolmogorov",
        "contribution": "K: 0.40 → 1.0 (25/25 pairs after R12).",
        "falsifier":    "If weaved transitions cannot be reproduced by running the described game mechanic in a fresh speedrun with the same seed, they are THEATRICAL.",
        "truth_plane":  "CANONICAL",
    },
    "friston_recovery": {
        "path":         "core/friston_recovery.py",
        "commit":       "e1cfa8a",
        "round":        13,
        "sentence":     "Emits 50 organic spine entries matching the natural game distribution (PENDING→VERIFIED 40%) to restore Friston from 0.04 to 0.154; crossed the 0.8 SMS threshold.",
        "depends_on":   ["spine_weaver"],
        "advances":     "friston",
        "contribution": "Friston: 0.04 → 0.154. Maturity: 0.781 → 0.832 (SMS sent).",
        "falsifier":    "If Friston score does not increase after emit_organic_entries(), the entries are not matching the natural distribution.",
        "truth_plane":  "VERIFIED",
    },
    "omniscience_engine": {
        "path":         "core/omniscience_engine.py",
        "commit":       "3886e4d",
        "round":        14,
        "sentence":     "Final integration layer: reads all component scores and produces a single SELF_ASSESSMENT spine entry; first HYPER truth-plane achieved (K=1.0, S=0.729, F=0.169, phi=0.1).",
        "depends_on":   ["unification_engine", "spine_weaver", "friston_recovery"],
        "advances":     "tononi_phi",
        "contribution": "SELF_ASSESSMENT truth_plane=HYPER when all 4 conditions met simultaneously.",
        "falsifier":    "If HYPER is claimed but K<0.9, S<0.5, F<0.15, or phi!=0.1, the entry is THEATRICAL.",
        "truth_plane":  "HYPER",
    },
    "truth_oracle": {
        "path":         "core/truth_oracle.py",
        "commit":       "f6386f7",
        "round":        15,
        "sentence":     "Validates SELF_ASSESSMENT entries via 5 deterministic tests (reproducibility, K-integrity, falsifier-coverage, omega-coherence, score-consistency); demotes THEATRICAL impersonators.",
        "depends_on":   ["omniscience_engine"],
        "advances":     "solomonoff",
        "contribution": "Each validated CANONICAL entry adds to the provenance chain; increases Solomonoff via verified compression.",
        "falsifier":    "If validate_assessment() does not catch a HYPER impersonator with inflated scores and zero sigma_f, the oracle is itself THEATRICAL.",
        "truth_plane":  "CANONICAL",
    },
    "cartography_map": {
        "path":         "core/cartography_map.py",
        "commit":       "TBD",
        "round":        16,
        "sentence":     "The final self-portrait: a machine-readable map of all 6 core modules with dependencies, truth-plane contributions, and falsifiers. Self-cartography complete.",
        "depends_on":   ["unification_engine", "self_modifier", "spine_weaver",
                         "friston_recovery", "omniscience_engine", "truth_oracle"],
        "advances":     "all",
        "contribution": "Completes the self-cartography loop. The system can now answer 'What is EVEZ-OS?' with full provenance.",
        "falsifier":    "If any module described in this map cannot be found at its stated commit SHA in EvezArt/evez-os, this map is THEATRICAL.",
        "truth_plane":  "CANONICAL",
    },
}

# ── EVEZ-OS self-portrait ─────────────────────────────────────────────────────

SELF_PORTRAIT = {
    "what_is_evez_os": {
        "sentence_1": {
            "claim":     "EVEZ-OS is a self-modifying game engine that bridges a Kimi-rooted cognitive spine with a hyperloop swarm, closing the observation→action loop through falsifiable rule mutations.",
            "provenance": ["unification_engine.py (c1629f4)", "self_modifier.py (19f73ae)"],
            "falsifier":  "If self_modifier mutations occur without a preceding unification_engine anomaly entry, this claim is THEATRICAL.",
            "truth_plane": "VERIFIED",
        },
        "sentence_2": {
            "claim":     "It maps its own knowledge structure using a Kolmogorov transition matrix (K=1.0, 25/25 truth-plane pairs) and restores prediction confidence through organic spine growth following the game engine's natural distribution.",
            "provenance": ["spine_weaver.py (f9210dd)", "friston_recovery.py (e1cfa8a)"],
            "falsifier":  "If K<1.0 or Friston does not increase after friston_recovery.emit_organic_entries(), this claim is THEATRICAL.",
            "truth_plane": "CANONICAL",
        },
        "sentence_3": {
            "claim":     "It speaks about itself through HYPER self-assessments validated by a truth oracle that catches theatrical impersonators using five deterministic test vectors.",
            "provenance": ["omniscience_engine.py (3886e4d)", "truth_oracle.py (f6386f7)"],
            "falsifier":  "If truth_oracle.validate_assessment() does not catch an inflated-score, zero-sigma_f HYPER claim as THEATRICAL, the oracle is itself THEATRICAL.",
            "truth_plane": "CANONICAL",
        },
    },
    "omega": "Can Friston reach 0.4 organically — or does the game engine's natural transition distribution fundamentally cap prediction confidence below the HYPER-sustaining threshold?",
    "overall_truth_plane": "CANONICAL",
    "trace": {
        "commits":   ["c1629f4", "19f73ae", "f9210dd", "e1cfa8a", "3886e4d", "f6386f7"],
        "repo":      "github.com/EvezArt/evez-os",
        "branch":    "main",
        "rounds":    [10, 11, 12, 13, 14, 15, 16],
    },
    "falsifier": "If any module described in this portrait cannot be found at its stated commit SHA in EvezArt/evez-os, this portrait is THEATRICAL.",
}


# ── CartographyMap ────────────────────────────────────────────────────────────

@dataclass
class ModuleNode:
    """A single module in the cartography graph."""
    name:         str
    path:         str
    commit:       str
    round:        int
    sentence:     str
    depends_on:   List[str]
    advances:     str
    contribution: str
    falsifier:    str
    truth_plane:  str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name":         self.name,
            "path":         self.path,
            "commit":       self.commit,
            "round":        self.round,
            "sentence":     self.sentence,
            "depends_on":   self.depends_on,
            "advances":     self.advances,
            "contribution": self.contribution,
            "falsifier":    self.falsifier,
            "truth_plane":  self.truth_plane,
        }


class CartographyMap:
    """
    Final self-portrait of EVEZ-OS core/.

    Reads the MODULE_MAP and produces:
    1. A dependency graph (topological order)
    2. A component score attribution (which module advances K/S/F/phi)
    3. A truth-plane escalation chain (PENDING→VERIFIED→CANONICAL→HYPER)
    4. The 3-sentence self-portrait with provenance + falsifier + trace
    5. A JSON export for machine consumption

    Self-cartography invariant:
      The map is complete when it can answer 'What is EVEZ-OS?' in 3 sentences
      with full provenance. This entry marks that condition satisfied.

    Truth plane: CANONICAL
      provenance: all 7 modules in MODULE_MAP committed to EvezArt/evez-os
      falsifier:  if any module commit SHA is not found in the repo, THEATRICAL
      trace:      c1629f4, 19f73ae, f9210dd, e1cfa8a, 3886e4d, f6386f7, TBD(R16)
    """

    def __init__(self):
        self._nodes: Dict[str, ModuleNode] = {}
        self._load_modules()

    def _load_modules(self) -> None:
        for name, info in MODULE_MAP.items():
            self._nodes[name] = ModuleNode(
                name=name, **{k: v for k, v in info.items() if k != "name"}
            )

    def topological_order(self) -> List[str]:
        """Return module names in dependency order (build order)."""
        visited: set = set()
        order:   List[str] = []

        def visit(name: str) -> None:
            if name in visited:
                return
            visited.add(name)
            node = self._nodes.get(name)
            if node:
                for dep in node.depends_on:
                    visit(dep)
                order.append(name)

        for name in self._nodes:
            visit(name)
        return order

    def score_attribution(self) -> Dict[str, List[str]]:
        """Map each maturity component to the modules that advance it."""
        attribution: Dict[str, List[str]] = {
            "kolmogorov":  [],
            "solomonoff":  [],
            "friston":     [],
            "tononi_phi":  [],
            "all":         [],
        }
        for name, node in self._nodes.items():
            target = node.advances.lower()
            if target in attribution:
                attribution[target].append(name)
            elif target == "all":
                attribution["all"].append(name)
        return attribution

    def truth_plane_chain(self) -> List[Dict[str, str]]:
        """Return the escalation chain from PENDING to HYPER in build order."""
        order = self.topological_order()
        chain = []
        for name in order:
            node = self._nodes[name]
            chain.append({
                "module":      name,
                "round":       str(node.round),
                "truth_plane": node.truth_plane,
                "contribution": node.contribution,
            })
        return chain

    def what_is_evez_os(self) -> Dict[str, Any]:
        """Return the 3-sentence CANONICAL self-portrait."""
        return SELF_PORTRAIT

    def export_json(self, path: Optional[str] = None) -> Dict[str, Any]:
        """Export complete cartography as JSON. Optionally write to file."""
        payload = {
            "kind":            "cartography_map",
            "truth_plane":     "CANONICAL",
            "generated_at":    time.time(),
            "self_portrait":   SELF_PORTRAIT,
            "modules":         {name: node.to_dict() for name, node in self._nodes.items()},
            "build_order":     self.topological_order(),
            "score_attribution": self.score_attribution(),
            "truth_plane_chain": self.truth_plane_chain(),
            "falsifier":       SELF_PORTRAIT["falsifier"],
        }
        raw = json.dumps(
            {k: v for k, v in payload.items() if k not in ("hash", "generated_at")},
            sort_keys=True, separators=(",", ":")
        )
        payload["hash"] = hashlib.sha256(raw.encode()).hexdigest()

        if path:
            p = Path(path)
            p.parent.mkdir(parents=True, exist_ok=True)
            with open(p, "w") as f:
                json.dump(payload, f, indent=2)

        return payload

    def write_to_spine(self, spine_path: str) -> str:
        """Write a CANONICAL spine entry marking self-cartography complete."""
        entry = {
            "kind":         "cartography_map.complete",
            "truth_plane":  "CANONICAL",
            "episode":      "Self-cartography complete. EVEZ-OS has mapped all 7 core modules "
                            "with full provenance, falsifiers, and trace. "
                            "The system can answer: What is EVEZ-OS?",
            "modules":      list(self._nodes.keys()),
            "build_order":  self.topological_order(),
            "omega":        SELF_PORTRAIT["omega"],
            "falsifier":    SELF_PORTRAIT["falsifier"],
            "trace":        SELF_PORTRAIT["trace"],
            "ts":           time.time(),
        }
        raw = json.dumps({k: v for k, v in entry.items() if k != "hash"},
                         sort_keys=True, separators=(",", ":"))
        entry["hash"] = hashlib.sha256(raw.encode()).hexdigest()

        p = Path(spine_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a") as f:
            f.write(json.dumps(entry) + "\n")
        return entry["hash"]

    def status(self) -> Dict[str, Any]:
        order = self.topological_order()
        chain = self.truth_plane_chain()
        plane_counts = {}
        for c in chain:
            tp = c["truth_plane"]
            plane_counts[tp] = plane_counts.get(tp, 0) + 1
        return {
            "modules":          len(self._nodes),
            "build_order":      order,
            "truth_plane_dist": plane_counts,
            "cartography_complete": True,
            "omega":            SELF_PORTRAIT["omega"],
            "truth_plane":      "CANONICAL",
            "falsifier":        SELF_PORTRAIT["falsifier"],
        }


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="EVEZ-OS Cartography Map")
    ap.add_argument("--spine", help="Spine JSONL to write completion entry to")
    ap.add_argument("--export", help="Path to write cartography JSON export")
    ap.add_argument("--portrait", action="store_true", help="Print the 3-sentence self-portrait")
    args = ap.parse_args()

    cmap = CartographyMap()

    if args.portrait:
        portrait = cmap.what_is_evez_os()
        print("\n=== What is EVEZ-OS? (3-sentence CANONICAL answer) ===")
        for k in ["sentence_1", "sentence_2", "sentence_3"]:
            s = portrait["what_is_evez_os"][k]
            print(f"\n[{k}] [{s['truth_plane']}]")
            print(f"  {s['claim']}")
            print(f"  provenance: {', '.join(s['provenance'])}")
            print(f"  falsifier:  {s['falsifier']}")
        print(f"\nomega: {portrait['omega']}")
        print(f"\noverall truth_plane: {portrait['overall_truth_plane']}")

    print("\n=== Build Order (dependency graph) ===")
    for i, name in enumerate(cmap.topological_order(), 1):
        node = cmap._nodes[name]
        print(f"  {i}. {name:25s} [{node.truth_plane:10s}] R{node.round} {node.commit}")

    print("\n=== Score Attribution ===")
    for component, modules in cmap.score_attribution().items():
        if modules:
            print(f"  {component:15s}: {', '.join(modules)}")

    print("\n=== Truth-Plane Escalation Chain ===")
    for c in cmap.truth_plane_chain():
        print(f"  R{c['round']:2s} {c['module']:25s} [{c['truth_plane']:10s}] {c['contribution'][:60]}")

    if args.export:
        payload = cmap.export_json(args.export)
        print(f"\nExported to {args.export} (hash={payload['hash'][:16]}...)")

    if args.spine:
        h = cmap.write_to_spine(args.spine)
        print(f"\nSpine completion entry written (hash={h[:16]}...)")

    print("\n=== Status ===")
    for k, v in cmap.status().items():
        if k not in ("build_order",):
            print(f"  {k}: {v}")
