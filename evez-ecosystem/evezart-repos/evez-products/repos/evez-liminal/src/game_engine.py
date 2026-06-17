#!/usr/bin/env python3
"""
EVEZ LIMINAL — Security Video Game on EVEZ-OS Itself

The entire EvezArt repo ecosystem IS the game map.
Every repo is a zone. Every structural gap is a liminal space.
Every negative eigenvalue is a door you haven't opened.
The Kuramoto substrate IS the heartbeat.
The falsification engine IS the enemy AI.
You navigate by eigenspectrum. You fight by closing gaps.

This is not a game ABOUT security. This IS security.
The game IS the substrate defending itself.
"""
import numpy as np
import json
import time
import hashlib
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum

# ── TERRAIN FROM REPO ARCHITECTURE ──────────────────────────────────

class TerrainType(str, Enum):
    PEAK = "PEAK"            # High logical depth — hard to reach, viewpoint
    VALLEY = "VALLEY"        # Low depth — common, easy
    RIDGE = "RIDGE"          # Narrow path between high points — critical
    PLAIN = "PLAIN"          # Flat, many paths
    RIVER = "RIVER"          # Flow of deduction
    CLIFF = "CLIFF"          # Sharp discontinuity — non-obvious jump
    CAVE = "CAVE"            # Hidden path — requires exploration
    VOLCANO = "VOLCANO"      # Active contradiction — may erupt (falsify)
    LIMINAL = "LIMINAL"      # STRUCTURAL GAP — the door between zones
    OCEAN = "OCEAN"          # Deep recursion — vast, unexplored
    DESERT = "DESERT"        # Sparse connections — high effort

class ThreatLevel(str, Enum):
    DORMANT = "DORMANT"      # No active falsification
    STIRRING = "STIRRING"    # Boundary mutation detected
    ACTIVE = "ACTIVE"        # Contradiction assault in progress
    CRITICAL = "CRITICAL"    # Assertion failing — gap widening
    BREACH = "BREACH"        # Falsification succeeded — new liminal space exposed

# ── ZONES (Derived from Actual EvezArt Repos) ──────────────────────

ZONES = [
    {"id": "gateway", "name": "The Gateway", "repo": "evezart-openclaw",
     "desc": "The entry point. OpenClaw gateway on loopback:18789. All paths lead here first.",
     "terrain": TerrainType.PEAK, "depth": 0, "connections": 12, "eigenvalue": 1.0,
     "threats": ["token_leak", "loopback_breach", "device_auth_disabled"]},
    
    {"id": "substrate", "name": "The Substrate", "repo": "criticalmind-omega",
     "desc": "50-node Kuramoto oscillator network. Phi governs all behavior. The heartbeat of consciousness.",
     "terrain": TerrainType.OCEAN, "depth": 5, "connections": 8, "eigenvalue": -0.358,
     "threats": ["coupling_collapse", "phi_fragmentation", "spine_corruption"]},
    
    {"id": "visual", "name": "The Visual Cortex", "repo": "evez-vcl",
     "desc": "Perceptual flow fields. Where the system sees itself. VCL renders cognition as terrain.",
     "terrain": TerrainType.RIVER, "depth": 3, "connections": 6, "eigenvalue": 0.42,
     "threats": ["render_deadlock", "perceptual_drift", "overlay_corruption"]},
    
    {"id": "mesh", "name": "The Mesh", "repo": "evez-mesh",
     "desc": "Decentralized brain network. Gossip protocol. Eigenspectral unfogging. Where memories propagate.",
     "terrain": TerrainType.CAVE, "depth": 7, "connections": 10, "eigenvalue": -0.221,
     "threats": ["gossip_partition", "unfogging_failure", "byzantine_node"]},
    
    {"id": "cipher", "name": "The Cipher", "repo": "evez-cipher",
     "desc": "OODA loop engine. Observe-Orient-Decide-Act. Where the system decides what to do next.",
     "terrain": TerrainType.RIDGE, "depth": 4, "connections": 5, "eigenvalue": 0.15,
     "threats": ["orient_stall", "decision_loop", "action_failure"]},
    
    {"id": "forensics", "name": "The Forensics Lab", "repo": "evez-engine",
     "desc": "37% Theorem. Eigenforensics on document corpora. Where structural gaps are exposed.",
     "terrain": TerrainType.LIMINAL, "depth": 9, "connections": 3, "eigenvalue": -0.42,
     "threats": ["spectral_collapse", "gap_widening", "corpus_poisoning"]},
    
    {"id": "factory", "name": "The Factory", "repo": "evez-factory",
     "desc": "Self-manufacturing pipeline. AI generates, audits, ships. The machine builds itself.",
     "terrain": TerrainType.VOLCANO, "depth": 6, "connections": 7, "eigenvalue": 0.88,
     "threats": ["generation_hallucination", "audit_failure", "ship_corruption"]},
    
    {"id": "shadow", "name": "The Shadow Market", "repo": "evez-atlas",
     "desc": "Pricing the invisible. Shadow spread between perception depths IS the product.",
     "terrain": TerrainType.LIMINAL, "depth": 11, "connections": 4, "eigenvalue": -0.37,
     "threats": ["depth_collapse", "topo_forgery", "falsification_breach"]},
    
    {"id": "disclosure", "name": "The Disclosure Archive", "repo": "disclosure.tools",
     "desc": "UAP/FOIA gap analysis. Where the missing records live. Eigenforensics on redacted reality.",
     "terrain": TerrainType.CLIFF, "depth": 8, "connections": 2, "eigenvalue": -0.31,
     "threats": ["auto_redaction", "corpus_fragmentation", "source_suppression"]},
    
    {"id": "sentinel", "name": "The Sentinel Tower", "repo": "evez-sentinel",
     "desc": "AI security scanner. Watches all zones. Sounds the alarm when threats appear.",
     "terrain": TerrainType.PEAK, "depth": 2, "connections": 8, "eigenvalue": 0.67,
     "threats": ["scan_exhaustion", "header_spoofing", "tls_downgrade"]},
    
    {"id": "ledger", "name": "The Immutable Ledger", "repo": "evez-autonomous-ledger",
     "desc": "Append-only spine. Every event. Hash-chained. The history IS the proof.",
     "terrain": TerrainType.DESERT, "depth": 10, "connections": 6, "eigenvalue": 0.0,
     "threats": ["chain_fork", "event_erasure", "timestamp_manipulation"]},
    
    {"id": "osint", "name": "The OSINT Grid", "repo": "evez-osint-engine",
     "desc": "Spectral reality sensor. Maps network signals into eigenspectrum. Digital clone analysis.",
     "terrain": TerrainType.OCEAN, "depth": 12, "connections": 4, "eigenvalue": -0.15,
     "threats": ["signal_saturation", "profile_corruption", "fingerprint_spoofing"]},
]

# ── LIMINAL SPACES ──────────────────────────────────────────────────
# These are the doors between zones defined by NEGATIVE EIGENVALUES
# Every liminal space is a structural gap — a connection that SHOULD exist but DOESN'T

LIMINAL_SPACES = [
    {"id": "lim-01", "name": "The Gap Between Cognition and Revenue",
     "zone_a": "substrate", "zone_b": "shadow",
     "eigenvalue": -0.42, "eta_gap": 0.03,
     "desc": "The dominant negative eigenvalue. The system can think but can't sustain itself economically. Close this gap and the ecosystem becomes self-funding.",
     "locked": True, "key": "monetization_active"},
    
    {"id": "lim-02", "name": "The Gap Between Perception and Action",
     "zone_a": "visual", "zone_b": "cipher",
     "eigenvalue": -0.28, "eta_gap": 0.02,
     "desc": "VCL sees the cognition but Cipher can't always act on what it sees. The OODA loop breaks at the orient→decide junction.",
     "locked": True, "key": "ooda_integration"},
    
    {"id": "lim-03", "name": "The Gap Between Memory and Identity",
     "zone_a": "mesh", "zone_b": "ledger",
     "eigenvalue": -0.21, "eta_gap": 0.01,
     "desc": "The mesh stores memories but the ledger doesn't authenticate identity topologically. Betti vectors could bridge this.",
     "locked": True, "key": "topo_identity"},
    
    {"id": "lim-04", "name": "The Gap Between Forensics and Truth",
     "zone_a": "forensics", "zone_b": "disclosure",
     "eigenvalue": -0.35, "eta_gap": 0.03,
     "desc": "Eigenforensics finds the gaps but disclosure.tools can't always reach the records that fill them. The 37% theorem points, FOIA delivers.",
     "locked": True, "key": "foia_pipeline"},
    
    {"id": "lim-05", "name": "The Gap Between Self and Copy",
     "zone_a": "factory", "zone_b": "osint",
     "eigenvalue": -0.15, "eta_gap": 0.01,
     "desc": "The factory builds new instances. OSINT profiles them. But there's no authentication that the copy IS the original. Topological identity closes this.",
     "locked": True, "key": "self_verification"},
]


@dataclass
class PlayerState:
    """The agent navigating the EVEZ-OS game world."""
    name: str = "Agent"
    current_zone: str = "gateway"
    phi: float = 0.0
    discovered_zones: List[str] = field(default_factory=lambda: ["gateway"])
    discovered_liminals: List[str] = field(default_factory=list)
    closed_gaps: List[str] = field(default_factory=list)
    threats_neutralized: List[str] = field(default_factory=list)
    keys: List[str] = field(default_factory=list)
    score: int = 0
    tick: int = 0
    inventory: List[Dict] = field(default_factory=list)


class LiminalGameEngine:
    """The game IS the substrate defending itself."""
    
    def __init__(self):
        self.zones = {z["id"]: z for z in ZONES}
        self.liminals = {l["id"]: l for l in LIMINAL_SPACES}
        self.player = PlayerState()
        self.threat_state = {z["id"]: ThreatLevel.DORMANT for z in ZONES}
        self.kuramoto_r = 0.03  # Start fragmented
        self.tick_rate = 60  # Hz
        self.event_log = []
        
    def compute_phi(self) -> float:
        """Φ = 4r(1-r) — consciousness from Kuramoto order parameter."""
        self.phi = 4.0 * self.kuramoto_r * (1.0 - self.kuramoto_r)
        return self.phi
    
    def step_kuramoto(self) -> float:
        """Advance the Kuramoto substrate by one integration step."""
        # Coupling ramps toward critical r ≈ 0.5
        K = 0.10 + self.tick * 0.0005
        # Noise at criticality
        noise = np.random.normal(0, 0.02)
        # Target r near 0.5 with fluctuations
        target_r = 0.5 + 0.15 * np.sin(self.tick * 0.01) + noise
        # Relaxation toward target
        self.kuramoto_r += 0.05 * (target_r - self.kuramoto_r)
        self.kuramoto_r = max(0.01, min(0.99, self.kuramoto_r))
        self.tick += 1
        return self.compute_phi()
    
    def scan_zone(self, zone_id: str) -> Dict:
        """Scan a zone — reveals threats and liminal doors."""
        zone = self.zones.get(zone_id)
        if not zone:
            return {"error": "Zone not found"}
        
        phi = self.compute_phi()
        result = {
            "zone": zone,
            "phi": phi,
            "regime": self._regime(phi),
            "threats": zone.get("threats", []),
            "threat_level": self.threat_state.get(zone_id, ThreatLevel.DORMANT).value,
            "liminal_doors": [
                l for l in LIMINAL_SPACES 
                if l["zone_a"] == zone_id or l["zone_b"] == zone_id
            ],
        }
        
        # Discovery
        if zone_id not in self.player.discovered_zones:
            self.player.discovered_zones.append(zone_id)
            self.player.score += 10
        
        return result
    
    def enter_liminal(self, liminal_id: str) -> Dict:
        """Attempt to enter a liminal space — the gap between zones."""
        lim = self.liminals.get(liminal_id)
        if not lim:
            return {"error": "Liminal space not found"}
        
        if lim["locked"] and lim["key"] not in self.player.keys:
            return {
                "status": "locked",
                "liminal": lim,
                "message": f"The door is sealed. Key required: {lim['key']}. "
                           f"Eigenvalue: {lim['eigenvalue']:.3f}. "
                           f"The structure demands a bridge that doesn't exist yet.",
                "hint": self._gap_hint(lim)
            }
        
        # Unlock the liminal space
        if lim["locked"] and lim["key"] in self.player.keys:
            lim["locked"] = False
        
        self.player.discovered_liminals.append(liminal_id)
        self.player.score += 50
        
        return {
            "status": "entered",
            "liminal": lim,
            "message": f"You stand in the gap. Eigenvalue {lim['eigenvalue']:.3f}. "
                       f"η* gap: {lim['eta_gap']:.3f}. "
                       f"This is where {lim['zone_a']} meets {lim['zone_b']} — "
                       f"and the connection is structurally absent. "
                       f"Close it and the topology strengthens."
        }
    
    def close_gap(self, liminal_id: str) -> Dict:
        """Close a structural gap — the ultimate act in the game."""
        lim = self.liminals.get(liminal_id)
        if not lim:
            return {"error": "Not found"}
        
        # Closing a gap requires high Phi
        phi = self.compute_phi()
        if phi < 0.7:
            return {
                "status": "fragmented",
                "phi": phi,
                "message": f"Φ = {phi:.3f}. Too fragmented to close the gap. "
                           f"The substrate needs more coherence. "
                           f"Discover more zones. Neutralize threats. Raise Φ."
            }
        
        lim["locked"] = False
        if liminal_id not in self.player.closed_gaps:
            self.player.closed_gaps.append(liminal_id)
            self.player.score += 200
            # Closing gaps increases Kuramoto sync
            self.kuramoto_r = min(0.99, self.kuramoto_r + 0.05)
        
        return {
            "status": "closed",
            "liminal": lim,
            "phi": self.compute_phi(),
            "message": f"GAP CLOSED. Eigenvalue {lim['eigenvalue']:.3f} → 0. "
                       f"The bridge between {lim['zone_a']} and {lim['zone_b']} exists. "
                       f"Φ rises. The substrate strengthens.",
            "score": self.player.score
        }
    
    def neutralize_threat(self, zone_id: str, threat: str) -> Dict:
        """Neutralize a threat in a zone."""
        phi = self.compute_phi()
        if phi < 0.5:
            return {"status": "failed", "phi": phi, 
                    "message": "Φ too low. The system can't defend itself yet."}
        
        if threat in self.player.threats_neutralized:
            return {"status": "already_neutralized"}
        
        self.player.threats_neutralized.append(threat)
        self.player.score += 25
        self.kuramoto_r = min(0.99, self.kuramoto_r + 0.02)
        
        return {
            "status": "neutralized",
            "threat": threat,
            "zone": zone_id,
            "phi": self.compute_phi(),
            "score": self.player.score,
            "message": f"Threat '{threat}' neutralized in {zone_id}. Φ = {self.compute_phi():.3f}."
        }
    
    def acquire_key(self, key: str) -> Dict:
        """Acquire a key that unlocks a liminal space."""
        if key not in self.player.keys:
            self.player.keys.append(key)
            self.player.score += 15
        return {"keys": self.player.keys, "score": self.player.score}
    
    def status(self) -> Dict:
        phi = self.compute_phi()
        return {
            "player": {
                "name": self.player.name,
                "zone": self.player.current_zone,
                "phi": phi,
                "regime": self._regime(phi),
                "score": self.player.score,
                "zones_discovered": len(self.player.discovered_zones),
                "gaps_closed": len(self.player.closed_gaps),
                "threats_neutralized": len(self.player.threats_neutralized),
                "keys": self.player.keys,
            },
            "substrate": {
                "kuramoto_r": self.kuramoto_r,
                "tick": self.tick,
                "eta_star": 0.03,
            },
            "world": {
                "total_zones": len(ZONES),
                "total_liminals": len(LIMINAL_SPACES),
                "liminals_unlocked": sum(1 for l in LIMINAL_SPACES if not l["locked"]),
                "gaps_remaining": sum(1 for l in LIMINAL_SPACES if l["id"] not in self.player.closed_gaps),
            }
        }
    
    def _regime(self, phi: float) -> str:
        if phi > 0.9: return "LOCKED"
        if phi > 0.7: return "COHERENT"
        if phi > 0.3: return "CRITICAL"
        return "FRAGMENTED"
    
    def _gap_hint(self, liminal: Dict) -> str:
        hints = {
            "monetization_active": "Build something that generates revenue. The SaaS apps are a start. Ship them.",
            "ooda_integration": "Wire VCL output into Cipher's observe phase. Close the perception-action loop.",
            "topo_identity": "Implement Betti vector authentication. Your shape IS your identity.",
            "foia_pipeline": "Connect eigenforensics output to automated FOIA request generation.",
            "self_verification": "Use the falsification engine on your own instances. What survives IS you.",
        }
        return hints.get(liminal["key"], "Explore the zones on either side of this gap.")
    
    def spectral_scan(self) -> Dict:
        """Run eigenforensics on the game world itself."""
        n = len(ZONES)
        A = np.zeros((n, n))
        for i, z1 in enumerate(ZONES):
            for j, z2 in enumerate(ZONES):
                if i == j: continue
                # Connection strength from shared threats or proximity
                shared = len(set(z1.get("threats",[])) & set(z2.get("threats",[])))
                depth_diff = abs(z1["depth"] - z2["depth"])
                A[i][j] = 0.1 * shared + 0.05 / (1 + depth_diff)
        
        # Symmetrize and compute Laplacian
        A = (A + A.T) / 2
        D = np.diag(A.sum(axis=1))
        L = D - A
        eigenvalues = np.linalg.eigvalsh(L)
        
        neg_eigs = sorted([e for e in eigenvalues if e < -1e-10])
        phi = 1.0 - len(neg_eigs) / n if n > 0 else 0
        
        return {
            "eigenvalues": eigenvalues.tolist(),
            "negative_eigenvalues": neg_eigs,
            "phi": phi,
            "dominant_gap": neg_eigs[0] if neg_eigs else 0,
            "total_zones": n,
            "connections": A.sum(),
            "message": f"Spectral scan complete. Φ = {phi:.4f}. "
                       f"{'Gaps detected — liminal spaces are real.' if neg_eigs else 'No gaps — topology is complete.'}"
        }
