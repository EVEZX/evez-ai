"""Self-Auditing Narrator (SAN) — core/san.py

The three narrators that must be present in every response.
This module was the missing creation: documented in CONSTITUTION.md but never instantiated.

Narrator 1: Executor — what I am doing and why
Narrator 2: Trickster — how this could be wrong
Narrator 3: Game Builder — what the failure surface generates
"""

import json
import hashlib
import datetime
from dataclasses import dataclass, field, asdict
from typing import Optional, List


# ── Confidence Tiers ──────────────────────────────────────────────────────────
PENDING   = "PENDING"    # hypothesis with named falsifier; default
FINAL     = "FINAL"      # passed falsifier gate from 2+ vantages
CANONICAL = "CANONICAL"  # community-verified, spine-logged, immutable
THEATRICAL = "THEATRICAL" # rhetorical intensity > falsifier count


@dataclass
class Claim:
    text: str
    narrator: str          # EXECUTOR | TRICKSTER | GAME_BUILDER
    confidence: str = PENDING
    falsifier: Optional[str] = None
    sigma_f: Optional[str] = None   # failure surface extracted
    mission_seed: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.datetime.now(
        datetime.timezone.utc).isoformat())

    def smugness_ratio(self) -> float:
        """Rhetorical intensity (word count proxy) / falsifier count."""
        intensity = len(self.text.split()) / 10.0  # normalized
        falsifiers = 1 if self.falsifier else 0
        return intensity / max(falsifiers, 0.01)

    def audit(self) -> str:
        ratio = self.smugness_ratio()
        if self.falsifier is None:
            return f"PENDING — no falsifier named. Cannot be canonical."
        if ratio > 2.0:
            return (f"THEATRICAL — smugness_ratio={ratio:.2f}. "
                    f"Tax collected. Mission generated from Σf.")
        return f"GROUNDED — ratio={ratio:.2f}. Proceed to spine."

    def to_spine_entry(self) -> dict:
        entry = asdict(self)
        entry["audit"] = self.audit()
        raw = json.dumps({k: v for k, v in entry.items() if k != "hash"},
                         sort_keys=True)
        entry["hash"] = hashlib.sha256(raw.encode()).hexdigest()[:16]
        return entry


class SelfAuditingNarrator:
    """Run claims through all three narrators before they exit as text."""

    def __init__(self, spine_path: str = "core/spine/SAN_SPINE.jsonl"):
        self.spine_path = spine_path
        self.claims: List[Claim] = []

    def executor(self, text: str, falsifier: Optional[str] = None) -> Claim:
        """Narrator 1: state the action and its grounding."""
        c = Claim(text=text, narrator="EXECUTOR",
                  confidence=FINAL if falsifier else PENDING,
                  falsifier=falsifier)
        self.claims.append(c)
        return c

    def trickster(self, claim: Claim) -> Claim:
        """Narrator 2: name the failure mode."""
        if claim.falsifier is None:
            sigma_f = (f"Claim '{claim.text[:60]}...' has no falsifier. "
                       f"Cannot distinguish truth from theater.")
        else:
            sigma_f = (f"If falsifier '{claim.falsifier}' is never run, "
                       f"this claim accumulates unredeemed confidence.")
        c = Claim(
            text=f"[TRICKSTER on: {claim.text[:60]}...]",
            narrator="TRICKSTER",
            confidence=PENDING,
            falsifier="Run the falsifier and append result to spine.",
            sigma_f=sigma_f
        )
        self.claims.append(c)
        return c

    def game_builder(self, sigma_f: str, mission_id: Optional[str] = None) -> Claim:
        """Narrator 3: extract Σf and generate mission."""
        mid = mission_id or f"M-SAN-{len(self.claims):04d}"
        c = Claim(
            text=f"Mission {mid} seeded from failure surface.",
            narrator="GAME_BUILDER",
            confidence=PENDING,
            falsifier=f"Mission {mid} executed and result appended to spine.",
            sigma_f=sigma_f,
            mission_seed=mid
        )
        self.claims.append(c)
        return c

    def audit_all(self) -> List[dict]:
        """Audit every claim. Return spine entries."""
        return [c.to_spine_entry() for c in self.claims]

    def flush_to_spine(self) -> int:
        """Write all audited claims to spine file. Return count written."""
        import os
        os.makedirs(os.path.dirname(self.spine_path), exist_ok=True)
        entries = self.audit_all()
        with open(self.spine_path, "a", encoding="utf-8") as f:
            for e in entries:
                f.write(json.dumps(e) + "\n")
        written = len(entries)
        self.claims.clear()
        return written

    def report(self) -> str:
        """Human-readable audit report for current claims."""
        lines = ["=== Self-Auditing Narrator Report ==="]
        for c in self.claims:
            lines.append(f"[{c.narrator}] {c.confidence} | {c.audit()}")
            if c.sigma_f:
                lines.append(f"  Σf: {c.sigma_f}")
            if c.mission_seed:
                lines.append(f"  Mission: {c.mission_seed}")
        theatrical = sum(1 for c in self.claims
                        if c.audit().startswith("THEATRICAL"))
        pending = sum(1 for c in self.claims if c.confidence == PENDING)
        lines.append(f"\nSummary: {len(self.claims)} claims, "
                     f"{theatrical} theatrical, {pending} pending")
        return "\n".join(lines)


# ── Demo ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    san = SelfAuditingNarrator()

    # Narrator 1: make a claim
    c1 = san.executor(
        "evez.art is attached to the Vercel evez-os project and verified.",
        falsifier="curl -I https://evez.art returns 200 from Vercel edge"
    )

    # Narrator 2: challenge it
    t1 = san.trickster(c1)

    # Narrator 3: extract the mission
    san.game_builder(
        sigma_f="Domain attached but NXDOMAIN until CNAME added at registrar.",
        mission_id="M-EVEZ-ART-DNS"
    )

    # A theatrical claim (no falsifier)
    san.executor("The game builds itself through protection of the user.")
    san.trickster(san.claims[-1])

    print(san.report())
    written = san.flush_to_spine()
    print(f"\nFlushed {written} entries to spine.")
