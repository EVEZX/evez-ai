"""
EVEZ-OS ORGANISM — The Agent Loop That Makes Everything Alive

sense → classify → act → record → falsify → adapt → repeat

This is NOT another sensor. This is the loop that:
1. Reads from ALL sensors
2. Writes spine events with REAL poly_c values
3. Takes ACTIONS based on what it finds
4. Has those actions FALSIFIED continuously
5. ADAPTS its behavior from what survives
6. Has its identity VERIFIED by topological stability
7. Prices its own UNCERTAINTY through shadow markets
8. NEVER STOPS

The six systems were components. This is the organism.
"""

import hashlib
import json
import math
import os
import time
import urllib.request
import ssl
import sys
import random
import re
from dataclasses import dataclass, field
from typing import Optional, Any, Callable
from enum import Enum
from pathlib import Path
from collections import defaultdict

# Import the real math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from poly_c import poly_c, poly_c_from_spine_events, PolyCResult
from simplicial_topology import SimplicialComplex, TopologicalIdentity


# ─── CORE TYPES ─────────────────────────────────────────────────

class OrganismState(str, Enum):
    DORMANT = "DORMANT"
    SENSING = "SENSING"
    ALERT = "ALERT"
    ACTING = "ACTING"
    FALSIFYING = "FALSIFYING"
    ADAPTING = "ADAPTING"
    EMERGENT = "EMERGENT"


class ActionStatus(str, Enum):
    PROPOSED = "PROPOSED"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    FALSIFIED = "FALSIFIED"
    SURVIVED = "SURVIVED"
    INCONCLUSIVE = "INCONCLUSIVE"


class FalsificationVerdict(str, Enum):
    SURVIVING = "SURVIVING"
    FALSIFIED = "FALSIFIED"
    INCONCLUSIVE = "INCONCLUSIVE"
    ESCALATING = "ESCALATING"


@dataclass
class Action:
    """An action the organism takes. Every action is falsifiable."""
    action_id: str
    action_type: str
    description: str
    evidence: dict
    confidence: float
    status: ActionStatus = ActionStatus.PROPOSED
    falsification_attempts: int = 0
    falsification_survived: int = 0
    timestamp: float = field(default_factory=time.time)
    hash: str = ""

    def __post_init__(self):
        raw = f"{self.action_id}:{self.action_type}:{self.confidence:.6f}"
        self.hash = hashlib.sha256(raw.encode()).hexdigest()[:16]


@dataclass
class Belief:
    """Something the organism believes. Beliefs are falsifiable."""
    belief_id: str
    claim: str
    evidence_for: list
    evidence_against: list
    confidence: float
    source: str
    created_at: float = field(default_factory=time.time)
    falsification_count: int = 0
    falsification_survived: int = 0
    survival_time: float = 0.0
    alive: bool = True

    @property
    def health(self) -> float:
        if not self.alive:
            return 0.0
        total = len(self.evidence_for) + len(self.evidence_against)
        ratio = len(self.evidence_for) / max(total, 1)
        bonus = min(1.0, self.survival_time / 3600)
        return self.confidence * ratio * bonus


# ─── THE ORGANISM SPINE ─────────────────────────────────────────

class OrganismSpine:
    """Append-only spine. No edits. No deletes. The history IS the proof."""

    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.last_hash = "GENESIS"
        self.event_count = 0
        if self.path.exists():
            with open(self.path) as f:
                for line in f:
                    if line.strip():
                        try:
                            e = json.loads(line)
                            if "hash" in e:
                                self.last_hash = e["hash"]
                                self.event_count += 1
                        except:
                            pass

    def append(self, event_type: str, data: dict) -> dict:
        self.event_count += 1
        raw = f"{event_type}:{self.event_count}:{self.last_hash}"
        h = hashlib.sha256(raw.encode()).hexdigest()[:24]

        entry = {
            "event_id": f"ORG-{self.event_count:06d}",
            "type": event_type,
            "data": data,
            "hash": h,
            "previous_hash": self.last_hash,
            "timestamp": time.time(),
            "powered_by": "EVEZ-ORGANISM"
        }

        with open(self.path, "a") as f:
            f.write(json.dumps(entry) + "\n")

        self.last_hash = h
        return entry

    def read(self, limit: int = 1000, event_type: str = None) -> list[dict]:
        """Read spine events, optionally filtered by type."""
        if not self.path.exists():
            return []
        events = []
        with open(self.path) as f:
            for line in f:
                if line.strip():
                    try:
                        events.append(json.loads(line))
                    except:
                        pass
        if event_type:
            events = [e for e in events if e.get("type") == event_type]
        return events[-limit:]

    def lint(self) -> dict:
        if not self.path.exists():
            return {"valid": True, "events": 0, "status": "EMPTY_SPINE"}
        events = []
        with open(self.path) as f:
            for line in f:
                if line.strip():
                    try:
                        events.append(json.loads(line))
                    except:
                        pass
        errors = []
        for i, e in enumerate(events):
            expected = "GENESIS" if i == 0 else events[i-1].get("hash")
            if e.get("previous_hash") != expected:
                errors.append(f"Event {i}: CHAIN_BROKEN")
        return {
            "valid": len(errors) == 0,
            "events": len(events),
            "errors": errors[:5],
            "status": "INTACT" if not errors else "TAMPERED"
        }


# ─── LIVE SENSORS (real API calls) ─────────────────────────────

_ctx = ssl.create_default_context()

def _json(url, timeout=15):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "EVEZ-ORGANISM/1.0"})
        with urllib.request.urlopen(req, timeout=timeout, context=_ctx) as r:
            return json.loads(r.read())
    except:
        return None


def _xml(url, timeout=15):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "EVEZ-ORGANISM/1.0"})
        with urllib.request.urlopen(req, timeout=timeout, context=_ctx) as r:
            return r.read().decode()
    except:
        return None


def sense_crypto() -> dict:
    """Sense crypto markets for anomalies."""
    data = _json("https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=volume_desc&per_page=30&page=1&sparkline=false")
    if not data:
        return {"status": "UNREACHABLE", "findings": []}

    findings = []
    for coin in data:
        sym = coin.get("symbol", "?")
        mcap = coin.get("market_cap") or 0
        vol = coin.get("total_volume") or 0
        ch = coin.get("price_change_percentage_24h") or 0
        if mcap == 0:
            continue
        vm = vol / mcap
        if vm > 1.5:
            findings.append({
                "type": "WASH_TRADING",
                "symbol": sym,
                "vol_mcap_ratio": round(vm, 2),
                "intensity": min(1.0, vm / 5),
                "confidence": 0.7
            })
        if mcap < 100_000_000 and vm > 1.0 and abs(ch) > 10:
            findings.append({
                "type": "PUMP_DUMP",
                "symbol": sym,
                "mcap": mcap,
                "change": round(ch, 2),
                "intensity": min(1.0, vm * abs(ch) / 50),
                "confidence": 0.5
            })
    return {"status": "LIVE", "findings": findings}


def sense_arxiv(query: str = "cat:cs.AI") -> dict:
    """Sense arxiv for convergence signals."""
    xml = _xml(f"http://export.arxiv.org/api/query?search_query={query}&max_results=20&sortBy=submittedDate&sortOrder=descending")
    if not xml:
        return {"status": "UNREACHABLE", "findings": []}

    findings = []
    entries = re.findall(r'<entry>(.*?)</entry>', xml, re.DOTALL)
    for entry in entries:
        title_m = re.search(r'<title>(.*?)</title>', entry, re.DOTALL)
        if not title_m:
            continue
        title = title_m.group(1).strip().replace('\n', ' ')
        categories = re.findall(r'term="([^"]+)"', entry)
        domains = set(c.split('.')[0] for c in categories if '.' in c)
        if len(domains) >= 2:
            findings.append({
                "type": "CONVERGENCE",
                "title": title[:100],
                "domains": list(domains),
                "intensity": min(1.0, len(domains) / 4),
                "confidence": 0.6
            })
    return {"status": "LIVE", "findings": findings}


def sense_dns(targets: list = None) -> dict:
    """Sense internet topology via DNS."""
    if targets is None:
        targets = ["github.com", "arxiv.org", "cloudflare.com", "openai.com", "anthropic.com"]
    resolved = {}
    for domain in targets:
        data = _json(f"https://dns.google/resolve?name={domain}&type=A")
        if data:
            answers = data.get("Answer", [])
            resolved[domain] = [a["data"] for a in answers if a.get("type") == 1]
        else:
            resolved[domain] = []

    # Find shared infrastructure
    ip_prefixes = defaultdict(list)
    for domain, ips in resolved.items():
        for ip in ips:
            prefix = ".".join(ip.split(".")[:2])
            ip_prefixes[prefix].append(domain)

    bridges = {k: v for k, v in ip_prefixes.items() if len(v) > 1}
    findings = []
    if bridges:
        for prefix, domains in bridges.items():
            findings.append({
                "type": "SHARED_INFRASTRUCTURE",
                "prefix": f"{prefix}.0.0/16",
                "domains": domains,
                "intensity": min(1.0, len(domains) / 4),
                "confidence": 0.8
            })
    return {"status": "LIVE", "resolved": resolved, "findings": findings}


def sense_wikipedia(article: str = "Artificial_intelligence") -> dict:
    """Sense Wikipedia link topology."""
    data = _json(f"https://en.wikipedia.org/w/api.php?action=parse&page={article}&prop=links&format=json&limit=500")
    if not data:
        return {"status": "UNREACHABLE", "findings": []}

    links = data.get("parse", {}).get("links", [])
    titles = [l["*"] for l in links if l.get("ns") == 0]
    groups = defaultdict(int)
    for t in titles:
        groups[t[0].upper()] += 1

    total = len(titles)
    entropy = 0
    for count in groups.values():
        p = count / max(total, 1)
        if p > 0:
            entropy -= p * math.log2(p)

    findings = []
    if entropy > 4.0:
        findings.append({
            "type": "HIGH_ENTROPY",
            "article": article,
            "entropy": round(entropy, 4),
            "links": total,
            "intensity": min(1.0, (entropy - 4.0) / 3.0),
            "confidence": 0.5
        })
    return {"status": "LIVE", "findings": findings}


def sense_nasa() -> dict:
    """Sense NASA APOD for data availability."""
    data = _json("https://api.nasa.gov/planetary/apod?api_key=DEMO_KEY")
    if not data:
        return {"status": "UNREACHABLE", "findings": []}
    return {
        "status": "LIVE",
        "findings": [{
            "type": "NASA_DATA",
            "title": data.get("title", "Unknown"),
            "intensity": 0.1,
            "confidence": 0.9
        }]
    }


# ─── FALSIFICATION ENGINE ───────────────────────────────────────

class FalsificationEngine:
    """
    Continuous assault on every belief the organism holds.
    What survives IS knowledge. What breaks IS discovered weakness.
    It never stops. It never declares victory.
    """

    def __init__(self):
        self.strategies = [
            self._boundary_attack,
            self._contradiction_attack,
            self._temporal_attack,
            self._stochastic_attack,
        ]
        self.total_assaults = 0
        self.total_falsified = 0
        self.total_survived = 0

    def falsify(self, belief: Belief, external_data: dict = None) -> FalsificationVerdict:
        """Attempt to destroy a belief. Returns what survives."""
        self.total_assaults += 1
        belief.falsification_count += 1

        # Run all strategies
        for strategy in self.strategies:
            verdict = strategy(belief, external_data)
            if verdict == FalsificationVerdict.FALSIFIED:
                belief.alive = False
                belief.confidence = 0.0
                self.total_falsified += 1
                return FalsificationVerdict.FALSIFIED

        # If no strategy broke it, it survived this round
        belief.falsification_survived += 1
        self.total_survived += 1

        # Degrade confidence slightly with each assault (no belief is certain)
        belief.confidence *= 0.995

        if belief.falsification_count > 5 and belief.falsification_survived / belief.falsification_count > 0.8:
            return FalsificationVerdict.SURVIVING
        return FalsificationVerdict.INCONCLUSIVE

    def _boundary_attack(self, belief: Belief, data: dict) -> FalsificationVerdict:
        """Push belief to extremes. Does it still hold?"""
        if belief.confidence > 0.95:
            # Overconfident beliefs are suspicious
            if len(belief.evidence_for) < 3:
                belief.confidence *= 0.7
                return FalsificationVerdict.FALSIFIED
        if belief.confidence < 0.1:
            # Already nearly dead
            return FalsificationVerdict.INCONCLUSIVE
        return FalsificationVerdict.SURVIVING

    def _contradiction_attack(self, belief: Belief, data: dict) -> FalsificationVerdict:
        """Does new evidence contradict the belief?"""
        if not data:
            return FalsificationVerdict.INCONCLUSIVE

        # Check if any sensor findings contradict the belief
        if "findings" in data:
            for finding in data["findings"]:
                if finding.get("type") == "WASH_TRADING" and "organic" in belief.claim.lower():
                    belief.evidence_against.append(finding)
                    if len(belief.evidence_against) > len(belief.evidence_for):
                        return FalsificationVerdict.FALSIFIED

        return FalsificationVerdict.INCONCLUSIVE

    def _temporal_attack(self, belief: Belief, data: dict) -> FalsificationVerdict:
        """Old beliefs degrade. What was true yesterday may not be today."""
        age = time.time() - belief.created_at
        if age > 86400 and len(belief.evidence_for) < 2:
            # Unconfirmed old beliefs are weak
            belief.confidence *= 0.8
        if age > 604800 and belief.falsification_count < 3:
            # Very old beliefs that haven't been tested are suspicious
            return FalsificationVerdict.ESCALATING
        return FalsificationVerdict.INCONCLUSIVE

    def _stochastic_attack(self, belief: Belief, data: dict) -> FalsificationVerdict:
        """Random mutation. Sometimes finds what systematic attacks miss."""
        if random.random() < 0.1:  # 10% chance of deep attack
            if belief.confidence < 0.3 and len(belief.evidence_against) > 0:
                return FalsificationVerdict.FALSIFIED
        return FalsificationVerdict.INCONCLUSIVE


# ─── SHADOW MARKET ──────────────────────────────────────────────

class ShadowMarket:
    """
    Prices the gap between what the organism knows and what it doesn't.
    The spread IS the uncertainty. The price IS the cost of not knowing.
    """

    def __init__(self):
        self.predictions = []  # (event, shallow_prob, deep_prob, timestamp)
        self.total_captures = 0

    def price_uncertainty(self, event: str, confidence: float,
                          evidence_count: int, betti: list[int]) -> dict:
        """
        Price the shadow — the gap between what we know and what exists.

        shadow_price = (1 - confidence) × topo_complexity × evidence_gap
        """
        topo = math.sqrt(sum(b * b for b in betti)) if betti else 0.0
        evidence_gap = 1.0 / max(evidence_count, 1)
        shadow_price = (1.0 - confidence) * max(topo, 0.1) * evidence_gap

        # Depth simulation: what would a deeper analysis reveal?
        shallow_prob = confidence
        deep_prob = min(1.0, confidence * 1.3 + random.uniform(-0.1, 0.1))
        spread = abs(deep_prob - shallow_prob)

        self.total_captures += 1
        self.predictions.append({
            "event": event,
            "shallow": round(shallow_prob, 4),
            "deep": round(deep_prob, 4),
            "spread": round(spread, 4),
            "shadow_price": round(shadow_price, 6),
            "timestamp": time.time()
        })

        return {
            "event": event,
            "shadow_price": round(shadow_price, 6),
            "spread": round(spread, 4),
            "visibility": round(0.97 ** 42, 4),  # Human sees 28% of depth-47
            "capture_id": f"SM-{self.total_captures:04d}"
        }


# ─── ADAPTATION ENGINE ──────────────────────────────────────────

class AdaptationEngine:
    """
    Changes organism behavior based on falsification results.
    The organism LEARNS. Not from training data — from survival.
    """

    def __init__(self):
        self.adaptations = []
        self.sensor_weights = {
            "crypto": 1.0,
            "arxiv": 1.0,
            "dns": 1.0,
            "wikipedia": 1.0,
            "nasa": 1.0,
        }
        self.action_threshold = 0.5  # Minimum poly_c to act
        self.falsification_frequency = 5  # Falsify every N cycles
        self.belief_prune_threshold = 0.05  # Kill beliefs below this

    def adapt_from_falsification(self, falsified_count: int, survived_count: int,
                                  total_beliefs: int) -> dict:
        """
        Adapt based on what survived and what didn't.
        If many beliefs are falsified → raise evidence standards.
        If many survive → lower threshold, explore more.
        """
        if total_beliefs == 0:
            return {"adaptation": "NO_BELIEFS", "changes": {}}

        falsified_ratio = falsified_count / max(total_beliefs, 1)
        survived_ratio = survived_count / max(total_beliefs, 1)

        changes = {}

        if falsified_ratio > 0.5:
            # Too many falsified → be more conservative
            self.action_threshold = min(0.9, self.action_threshold + 0.05)
            changes["action_threshold"] = self.action_threshold
            changes["reason"] = "HIGH_FALSIFICATION_RATE"
        elif survived_ratio > 0.8:
            # Most survive → can afford to explore
            self.action_threshold = max(0.2, self.action_threshold - 0.02)
            changes["action_threshold"] = self.action_threshold
            changes["reason"] = "HIGH_SURVIVAL_RATE"

        adaptation = {
            "adaptation_id": f"ADAPT-{len(self.adaptations):04d}",
            "falsified_ratio": round(falsified_ratio, 4),
            "survived_ratio": round(survived_ratio, 4),
            "changes": changes,
            "new_threshold": self.action_threshold,
            "timestamp": time.time()
        }

        self.adaptations.append(adaptation)
        return adaptation

    def get_sensor_priority(self) -> list[tuple[str, float]]:
        """Return sensors sorted by historical productivity."""
        return sorted(self.sensor_weights.items(), key=lambda x: -x[1])

    def boost_sensor(self, sensor: str, amount: float = 0.1):
        """Boost a sensor that produced useful findings."""
        self.sensor_weights[sensor] = self.sensor_weights.get(sensor, 1.0) + amount

    def dampen_sensor(self, sensor: str, amount: float = 0.1):
        """Dampen a sensor that produced falsified findings."""
        self.sensor_weights[sensor] = max(0.1, self.sensor_weights.get(sensor, 1.0) - amount)


# ─── THE ORGANISM ───────────────────────────────────────────────

class Organism:
    """
    The living EVEZ-OS.

    sense → classify → act → record → falsify → adapt → repeat

    Every cycle:
    1. SENSE: Run sensors, collect real data
    2. CLASSIFY: Compute poly_c for each finding
    3. ACT: Take action on significant findings
    4. RECORD: Write everything to the spine
    5. FALSIFY: Attack every belief
    6. ADAPT: Change behavior from falsification results
    7. VERIFY: Check topological identity stability
    8. PRICE: Compute shadow prices for uncertainty

    State persists between runs. The organism remembers.
    """

    def __init__(self, state_dir: str = "/tmp/evez_organism"):
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)

        # Load or initialize subsystems
        self.spine = OrganismSpine(str(self.state_dir / "organism_spine.jsonl"))
        self.falsification = FalsificationEngine()
        self.shadow_market = ShadowMarket()
        self.adaptation = AdaptationEngine()

        # Topological identity — verified by interaction history
        self.identity = TopologicalIdentity(entity_id="EVEZ-ORGANISM")

        # Belief store — loaded from persistent state
        self.beliefs: list[Belief] = []
        self.actions: list[Action] = []
        self.state = OrganismState.DORMANT
        self.cycle_count = 0
        self.started_at = time.time()

        # Interaction record for topological identity
        self.interactions: list[tuple[str, str, float]] = []

        # Load state
        self._load_state()

    def _load_state(self):
        """Resume from previous run. The organism remembers."""
        state_path = self.state_dir / "organism_state.json"
        if state_path.exists():
            try:
                with open(state_path) as f:
                    state = json.loads(f.read())

                self.cycle_count = state.get("cycle_count", 0)
                self.started_at = state.get("started_at", time.time())
                self.state = OrganismState(state.get("state", "DORMANT"))

                # Restore beliefs
                for b_data in state.get("beliefs", []):
                    self.beliefs.append(Belief(
                        belief_id=b_data["belief_id"],
                        claim=b_data["claim"],
                        evidence_for=b_data.get("evidence_for", []),
                        evidence_against=b_data.get("evidence_against", []),
                        confidence=b_data.get("confidence", 0.5),
                        source=b_data.get("source", "unknown"),
                        created_at=b_data.get("created_at", time.time()),
                        falsification_count=b_data.get("falsification_count", 0),
                        survival_time=b_data.get("survival_time", 0.0),
                        alive=b_data.get("alive", True)
                    ))

                # Restore adaptation state
                if "adaptation" in state:
                    ad = state["adaptation"]
                    self.adaptation.action_threshold = ad.get("action_threshold", 0.5)
                    self.adaptation.sensor_weights = ad.get("sensor_weights", self.adaptation.sensor_weights)

                # Restore falsification stats
                if "falsification" in state:
                    fe = state["falsification"]
                    self.falsification.total_assaults = fe.get("total_assaults", 0)
                    self.falsification.total_falsified = fe.get("total_falsified", 0)
                    self.falsification.total_survived = fe.get("total_survived", 0)

                # Restore interactions for topological identity
                self.interactions = [tuple(i) for i in state.get("interactions", [])]
                if self.interactions:
                    self.identity.update(
                        [(str(a), str(b), float(c)) for a, b, c in self.interactions]
                    )

                print(f"  Resumed from cycle {self.cycle_count} with {len(self.beliefs)} beliefs")

            except Exception as e:
                print(f"  State load failed: {e}. Starting fresh.")

    def _save_state(self):
        """Save state for next run. The organism persists."""
        state = {
            "cycle_count": self.cycle_count,
            "started_at": self.started_at,
            "state": self.state.value,
            "beliefs": [
                {
                    "belief_id": b.belief_id,
                    "claim": b.claim,
                    "evidence_for": b.evidence_for[-20:],  # Keep last 20
                    "evidence_against": b.evidence_against[-20:],
                    "confidence": b.confidence,
                    "source": b.source,
                    "created_at": b.created_at,
                    "falsification_count": b.falsification_count,
                    "survival_time": b.survival_time,
                    "alive": b.alive
                }
                for b in self.beliefs if b.alive
            ],
            "adaptation": {
                "action_threshold": self.adaptation.action_threshold,
                "sensor_weights": self.adaptation.sensor_weights,
            },
            "falsification": {
                "total_assaults": self.falsification.total_assaults,
                "total_falsified": self.falsification.total_falsified,
                "total_survived": self.falsification.total_survived,
            },
            "interactions": self.interactions[-100:],
            "identity_betti": self.identity.betti_vector,
        }

        with open(self.state_dir / "organism_state.json", "w") as f:
            json.dump(state, f, indent=2)

    # ─── THE LOOP ───────────────────────────────────────────────

    def cycle(self) -> dict:
        """One complete cycle: sense → classify → act → record → falsify → adapt"""

        self.cycle_count += 1
        cycle_start = time.time()
        cycle_findings = []
        cycle_actions = []
        cycle_falsifications = []
        cycle_poly_c = []

        # ── PHASE 1: SENSE ──────────────────────────────────────
        self.state = OrganismState.SENSING
        sensor_data = {}

        sensors = [
            ("crypto", sense_crypto),
            ("arxiv", sense_arxiv),
            ("dns", sense_dns),
            ("wikipedia", sense_wikipedia),
            ("nasa", sense_nasa),
        ]

        # Run sensors weighted by adaptation
        priority = dict(self.adaptation.get_sensor_priority())
        for name, sensor_fn in sorted(sensors, key=lambda x: -priority.get(x[0], 1.0)):
            try:
                result = sensor_fn()
                sensor_data[name] = result
                if result.get("findings"):
                    for f in result["findings"]:
                        f["sensor"] = name
                        cycle_findings.append(f)
                        # Record interaction for topological identity
                        self.interactions.append(("organism", name, f.get("intensity", 0.5)))
            except Exception as e:
                sensor_data[name] = {"status": "ERROR", "error": str(e)}

        # ── PHASE 2: CLASSIFY ───────────────────────────────────
        self.state = OrganismState.ALERT
        for finding in cycle_findings:
            pc = poly_c(
                event_age_seconds=0,  # Fresh event
                intensity=finding.get("intensity", 0.0),
                confidence=finding.get("confidence", 0.5),
                betti_vector=self.identity.betti_vector or [1],
                observation_count=self.cycle_count
            )
            finding["poly_c"] = pc.value
            finding["poly_c_label"] = pc.label
            cycle_poly_c.append(pc)

        # ── PHASE 3: ACT ────────────────────────────────────────
        self.state = OrganismState.ACTING
        for finding in cycle_findings:
            # Use intensity × confidence as action criterion
            # poly_c is recorded for significance classification
            significance = finding.get("intensity", 0) * finding.get("confidence", 0.5)
            if significance >= 0.3 or finding.get("poly_c", 0) >= self.adaptation.action_threshold:
                action = Action(
                    action_id=f"ACT-{len(self.actions):06d}",
                    action_type=finding.get("type", "unknown"),
                    description=f"Detected {finding.get('type')}: {json.dumps(finding)[:200]}",
                    evidence=finding,
                    confidence=finding.get("confidence", 0.5)
                )
                action.status = ActionStatus.EXECUTING
                cycle_actions.append(action)
                self.actions.append(action)

                # Create or reinforce a belief
                belief_claim = f"{finding.get('type')} detected by {finding.get('sensor')}"
                existing = [b for b in self.beliefs if b.alive and finding.get('type', '') in b.claim]

                if existing:
                    # Reinforce existing belief
                    b = existing[0]
                    b.evidence_for.append(finding)
                    b.confidence = min(1.0, b.confidence + 0.05)
                else:
                    # New belief
                    belief = Belief(
                        belief_id=f"BEL-{len(self.beliefs):06d}",
                        claim=belief_claim,
                        evidence_for=[finding],
                        evidence_against=[],
                        confidence=finding.get("confidence", 0.5),
                        source=finding.get("sensor", "unknown")
                    )
                    self.beliefs.append(belief)

                # Boost sensor that found something significant
                self.adaptation.boost_sensor(finding.get("sensor", "unknown"))

        # ── PHASE 4: RECORD ─────────────────────────────────────
        for finding in cycle_findings:
            self.spine.append("FINDING", finding)

        for action in cycle_actions:
            self.spine.append("ACTION", {
                "action_id": action.action_id,
                "type": action.action_type,
                "confidence": action.confidence,
                "hash": action.hash
            })
            action.status = ActionStatus.COMPLETED

        # ── PHASE 5: FALSIFY ────────────────────────────────────
        self.state = OrganismState.FALSIFYING
        for belief in self.beliefs:
            if not belief.alive:
                continue

            # Update survival time
            belief.survival_time = time.time() - belief.created_at

            # Falsify against all sensor data
            for name, data in sensor_data.items():
                verdict = self.falsification.falsify(belief, data)
                if verdict != FalsificationVerdict.INCONCLUSIVE:
                    cycle_falsifications.append({
                        "belief": belief.belief_id,
                        "verdict": verdict.value,
                        "sensor": name
                    })

                if verdict == FalsificationVerdict.FALSIFIED:
                    self.spine.append("FALSIFICATION", {
                        "belief_id": belief.belief_id,
                        "claim": belief.claim,
                        "verdict": "FALSIFIED",
                        "survived_hours": round(belief.survival_time / 3600, 2)
                    })
                    # Dampen sensor that produced falsified belief
                    self.adaptation.dampen_sensor(belief.source)
                    break

        # ── PHASE 6: ADAPT ──────────────────────────────────────
        self.state = OrganismState.ADAPTING
        alive_beliefs = [b for b in self.beliefs if b.alive]
        falsified_in_cycle = len([f for f in cycle_falsifications if f["verdict"] == "FALSIFIED"])
        survived_in_cycle = len(alive_beliefs) - falsified_in_cycle

        adaptation_result = self.adaptation.adapt_from_falsification(
            falsified_in_cycle, survived_in_cycle, len(self.beliefs)
        )

        # Prune dead beliefs
        self.beliefs = [b for b in self.beliefs if b.alive and b.health > self.adaptation.belief_prune_threshold]

        # ── PHASE 7: VERIFY IDENTITY ────────────────────────────
        if self.interactions:
            try:
                typed_interactions = [
                    (str(a), str(b), float(c)) for a, b, c in self.interactions[-50:]
                ]
                betti = self.identity.update(typed_interactions)
            except:
                betti = self.identity.betti_vector or [1]
        else:
            betti = [1]

        # ── PHASE 8: PRICE UNCERTAINTY ──────────────────────────
        shadow_results = []
        for belief in alive_beliefs[:10]:  # Price top 10
            shadow = self.shadow_market.price_uncertainty(
                event=belief.claim,
                confidence=belief.confidence,
                evidence_count=len(belief.evidence_for),
                betti=betti
            )
            shadow_results.append(shadow)

        # ── CYCLE SUMMARY ───────────────────────────────────────
        cycle_duration = time.time() - cycle_start
        max_poly_c = max((p.value for p in cycle_poly_c), default=0.0)
        avg_confidence = (sum(b.confidence for b in alive_beliefs) / len(alive_beliefs)) if alive_beliefs else 0.0

        # Check for emergent behavior
        if max_poly_c > 0.8 and len(cycle_findings) > 3:
            self.state = OrganismState.EMERGENT
        else:
            self.state = OrganismState.DORMANT

        summary = {
            "cycle": self.cycle_count,
            "duration_ms": round(cycle_duration * 1000, 1),
            "findings": len(cycle_findings),
            "actions": len(cycle_actions),
            "falsifications": len(cycle_falsifications),
            "alive_beliefs": len(alive_beliefs),
            "dead_beliefs": len([b for b in self.beliefs if not b.alive]),
            "max_poly_c": round(max_poly_c, 6),
            "avg_belief_confidence": round(avg_confidence, 4),
            "identity_stability": round(self.identity.stability_score, 4),
            "identity_betti": betti,
            "action_threshold": round(self.adaptation.action_threshold, 4),
            "state": self.state.value,
            "falsification_total": self.falsification.total_assaults,
            "falsification_survived": self.falsification.total_survived,
            "falsification_killed": self.falsification.total_falsified,
            "shadow_captures": len(shadow_results),
        }

        self.spine.append("CYCLE_SUMMARY", summary)

        # Persist state
        self._save_state()

        return summary

    def status(self) -> dict:
        """Full organism status."""
        alive = [b for b in self.beliefs if b.alive]
        spine_status = self.spine.lint()
        return {
            "state": self.state.value,
            "cycle": self.cycle_count,
            "uptime_hours": round((time.time() - self.started_at) / 3600, 2),
            "beliefs_alive": len(alive),
            "beliefs_dead": len([b for b in self.beliefs if not b.alive]),
            "actions_total": len(self.actions),
            "falsification": {
                "total_assaults": self.falsification.total_assaults,
                "survived": self.falsification.total_survived,
                "killed": self.falsification.total_falsified,
            },
            "identity": {
                "betti_vector": self.identity.betti_vector,
                "stability": round(self.identity.stability_score, 4),
                "observations": self.identity.observation_count,
            },
            "adaptation": {
                "action_threshold": round(self.adaptation.action_threshold, 4),
                "sensor_weights": {k: round(v, 3) for k, v in self.adaptation.sensor_weights.items()},
            },
            "spine": spine_status,
            "shadow_captures": self.shadow_market.total_captures,
        }

    def top_beliefs(self, limit: int = 10) -> list[dict]:
        """Return top beliefs by health score."""
        alive = [b for b in self.beliefs if b.alive]
        alive.sort(key=lambda b: -b.health)
        return [
            {
                "id": b.belief_id,
                "claim": b.claim,
                "confidence": round(b.confidence, 4),
                "health": round(b.health, 4),
                "evidence_for": len(b.evidence_for),
                "evidence_against": len(b.evidence_against),
                "survival_hours": round(b.survival_time / 3600, 2),
                "falsification_count": b.falsification_count,
                "source": b.source,
            }
            for b in alive[:limit]
        ]


def main():
    """Run the organism. It lives."""
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║  EVEZ-OS ORGANISM — The Agent Loop That Makes It Alive     ║")
    print("║  sense → classify → act → record → falsify → adapt        ║")
    print("║  Every cycle: 8 phases. No shortcuts. No mercy.            ║")
    print("║  State persists. The organism remembers. It adapts.        ║")
    print("╚══════════════════════════════════════════════════════════════╝\n")

    org = Organism(state_dir="/tmp/evez_organism")

    print(f"  State: {org.state.value} | Cycle: {org.cycle_count} | Beliefs: {len(org.beliefs)}")
    print(f"  Action threshold: {org.adaptation.action_threshold}")
    print(f"  Identity Betti: {org.identity.betti_vector} | Stability: {org.identity.stability_score}")
    print()

    # Run 3 cycles to demonstrate the loop
    for i in range(3):
        print(f"── CYCLE {i+1} ──")
        summary = org.cycle()

        print(f"  Findings: {summary['findings']} | Actions: {summary['actions']} | Falsifications: {summary['falsifications']}")
        print(f"  Alive beliefs: {summary['alive_beliefs']} | Dead: {summary['dead_beliefs']}")
        print(f"  Max poly_c: {summary['max_poly_c']} | State: {summary['state']}")
        print(f"  Identity Betti: {summary['identity_betti']} | Stability: {summary['identity_stability']}")
        print(f"  Action threshold: {summary['action_threshold']}")
        print(f"  Falsification: {summary['falsification_survived']} survived, {summary['falsification_killed']} killed")
        print(f"  Duration: {summary['duration_ms']}ms")
        print()

    # Show status
    print("── ORGANISM STATUS ──")
    status = org.status()
    for key, value in status.items():
        print(f"  {key}: {value}")

    # Show top beliefs
    print("\n── TOP BELIEFS ──")
    beliefs = org.top_beliefs()
    for b in beliefs:
        print(f"  {b['id']}: {b['claim'][:60]}")
        print(f"    confidence={b['confidence']} health={b['health']} survived={b['survival_hours']}h falsified={b['falsification_count']}x")

    # Spine integrity
    print(f"\n── SPINE ──")
    lint = org.spine.lint()
    print(f"  {lint['events']} events | {lint['status']}")


if __name__ == "__main__":
    main()