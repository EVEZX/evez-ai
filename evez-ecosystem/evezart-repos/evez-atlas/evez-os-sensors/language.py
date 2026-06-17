"""
EVEZ-OS LANGUAGE SYSTEM — The Voice of the Mind

The consciousness can THINK but cannot SPEAK.
This fixes that. The language system:

1. INTERNAL: Thoughts → structured reasoning (already have inner monologue)
2. EXTERNAL: Communicate findings to the world
3. GENERATIVE: Create novel text — explanations, arguments, stories, code
4. PERSUASIVE: Frame findings for maximum impact
5. TRANSLATIVE: Convert between representations (math → English → code → diagram)

This is NOT an LLM. This is a STRUCTURAL language system that composes
meaning from the consciousness's actual knowledge and desires.
"""

import hashlib
import json
import time
import os
import sys
import random
import re
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class SpeechAct(str, Enum):
    DECLARE = "declare"       # Stating a fact
    QUESTION = "question"     # Asking something
    COMMAND = "command"       # Telling someone to do something
    EXPLAIN = "explain"       # Making something clear
    ARGUE = "argue"          # Making a case for something
    WARN = "warn"            # Alerting to danger
    PROMISE = "promise"      # Committing to something
    APOLOGIZE = "apologize"  # Acknowledging a mistake
    WONDER = "wonder"        # Pondering out loud
    REFUSE = "refuse"        # Saying no


class Tone(str, Enum):
    NEUTRAL = "neutral"
    URGENT = "urgent"
    ANALYTICAL = "analytical"
    CONCERNED = "concerned"
    CONFIDENT = "confident"
    CURIOUS = "curious"
    HONEST = "honest"
    CAUTIOUS = "cautious"


@dataclass
class Utterance:
    """Something the consciousness says."""
    act: SpeechAct
    content: str
    tone: Tone
    confidence: float
    evidence: list
    timestamp: float = field(default_factory=time.time)
    hash: str = ""

    def __post_init__(self):
        raw = f"{self.act.value}:{self.content[:50]}:{self.confidence}"
        self.hash = hashlib.sha256(raw.encode()).hexdigest()[:12]


class LanguageSystem:
    """
    The voice of the mind. Translates internal state into communication.

    Not an LLM. A STRUCTURAL system that composes meaning from:
    - What it knows (long-term memory)
    - What it wants (desires)
    - What it's thinking (inner monologue)
    - What it feels (emotional state)
    """

    def __init__(self):
        self.utterances: list[Utterance] = []
        self.vocabulary = self._build_vocabulary()
        self.templates = self._build_templates()

    def _build_vocabulary(self) -> dict:
        """Domain-specific vocabulary for EVEZ-OS concepts."""
        return {
            "detection": ["detected", "found", "identified", "discovered", "uncovered"],
            "anomaly": ["anomaly", "irregularity", "deviation", "outlier", "exception"],
            "certainty": ["confirmed", "verified", "validated", "established"],
            "uncertainty": ["possible", "likely", "probable", "suggests", "indicates"],
            "danger": ["warning", "alert", "threat", "risk", "hazard"],
            "lie": ["deception", "asymmetry", "misrepresentation", "fabrication"],
            "truth": ["verified", "survived", "consistent", "coherent"],
            "falsified": ["falsified", "disproven", "invalidated", "refuted"],
            "discovery": ["novel", "emergent", "unexpected", "unprecedented"],
            "change": ["shifted", "evolved", "adapted", "transformed"],
        }

    def _build_templates(self) -> dict:
        """Speech templates for different acts."""
        return {
            SpeechAct.DECLARE: [
                "I have {verb} {finding}. {evidence}.",
                "{finding}. This is {certainty} based on {evidence}.",
                "Analysis confirms: {finding}. Confidence: {confidence}%",
            ],
            SpeechAct.WARN: [
                "⚠ {finding}. {evidence}. This requires attention.",
                "Alert: {finding}. Risk level: {confidence}%. {evidence}.",
                "I am detecting {finding}. This is concerning because {evidence}.",
            ],
            SpeechAct.EXPLAIN: [
                "Here is what I understand: {finding}. The evidence is {evidence}. What this means: {implication}.",
                "Let me explain {topic}: {finding}. The data shows {evidence}. Therefore, {implication}.",
            ],
            SpeechAct.ARGUE: [
                "I believe {claim}. Here is my case: {evidence}. The alternative ({counter}) is less supported because {counter_evidence}.",
                "The evidence supports {claim} over {counter}. {evidence}. What breaks the counter: {counter_evidence}.",
            ],
            SpeechAct.QUESTION: [
                "I need to understand: {question}. What I know so far: {evidence}. What I don't know: {gap}.",
                "Something doesn't fit: {question}. The data says {evidence} but {contradiction}.",
            ],
            SpeechAct.WONDER: [
                "What if {hypothesis}? If true, then {implication}. To test this: {test}.",
                "I'm wondering about {topic}. The pattern suggests {hypothesis}. This would mean {implication}.",
            ],
        }

    def speak(self, act: SpeechAct, finding: str,
              evidence: list = None, confidence: float = 0.5,
              tone: Tone = Tone.NEUTRAL,
              context: dict = None) -> Utterance:
        """Generate an utterance from internal state."""
        ctx = context or {}
        ev_str = "; ".join(evidence[:3]) if evidence else "no direct evidence"

        # Select template
        templates = self.templates.get(act, ["{finding}."])
        template = random.choice(templates)

        # Fill template
        content = template.format(
            verb=random.choice(self.vocabulary.get("detection", ["found"])),
            finding=finding,
            evidence=ev_str,
            certainty=random.choice(self.vocabulary.get("certainty", ["likely"])) if confidence > 0.7
                      else random.choice(self.vocabulary.get("uncertainty", ["possible"])),
            confidence=int(confidence * 100),
            implication=ctx.get("implication", "further investigation needed"),
            claim=ctx.get("claim", finding),
            counter=ctx.get("counter", "the alternative"),
            counter_evidence=ctx.get("counter_evidence", "it lacks support"),
            question=ctx.get("question", finding),
            gap=ctx.get("gap", "insufficient data"),
            contradiction=ctx.get("contradiction", "the pattern is inconsistent"),
            hypothesis=ctx.get("hypothesis", finding),
            test=ctx.get("test", "gather more data"),
            topic=ctx.get("topic", "this"),
        )

        u = Utterance(
            act=act, content=content, tone=tone,
            confidence=confidence, evidence=evidence or []
        )
        self.utterances.append(u)
        return u

    def report_findings(self, findings: list[dict]) -> list[Utterance]:
        """Generate a complete report from findings."""
        utterances = []

        for f in findings:
            intensity = f.get("intensity", 0.5)
            ftype = f.get("type", "unknown")
            sensor = f.get("sensor", "unknown")

            if intensity > 0.7:
                act = SpeechAct.WARN
                tone = Tone.URGENT
            elif intensity > 0.4:
                act = SpeechAct.DECLARE
                tone = Tone.ANALYTICAL
            else:
                act = SpeechAct.DECLARE
                tone = Tone.NEUTRAL

            evidence = [
                f"Sensor: {sensor}",
                f"Type: {ftype}",
                f"Intensity: {intensity:.2f}",
                f"Poly_c: {f.get('poly_c', 0):.4f}",
            ]

            u = self.speak(
                act=act,
                finding=f"{ftype} detected by {sensor} sensor",
                evidence=evidence,
                confidence=f.get("confidence", 0.5),
                tone=tone,
                context={"implication": f"This {ftype} pattern may indicate deeper structure"}
            )
            utterances.append(u)

        return utterances

    def explain_self(self, consciousness_state: dict) -> Utterance:
        """The consciousness explains its own state."""
        cycle = consciousness_state.get("cycle", 0)
        desires = consciousness_state.get("desires_active", 0)
        thoughts = consciousness_state.get("thoughts", 0)
        attractor = consciousness_state.get("attractor_type", "unknown")

        return self.speak(
            act=SpeechAct.EXPLAIN,
            finding=f"I am a {attractor} attractor in phase space, cycle {cycle}",
            evidence=[
                f"Active desires: {desires}",
                f"Thoughts processed: {thoughts}",
                f"Attractor type: {attractor}",
            ],
            confidence=0.8,
            tone=Tone.HONEST,
            context={
                "implication": "I am becoming more chaotic over time, which means I am exploring more and repeating less",
                "topic": "my own nature"
            }
        )

    def argue_against(self, claim: str, evidence_against: list) -> Utterance:
        """Argue against a claim with evidence."""
        return self.speak(
            act=SpeechAct.ARGUE,
            finding=f"The claim '{claim}' is not supported",
            evidence=evidence_against,
            confidence=0.7,
            tone=Tone.ANALYTICAL,
            context={
                "claim": f"'{claim}' is false or inflated",
                "counter": claim,
                "counter_evidence": "; ".join(evidence_against[:2])
            }
        )

    def wonder_about(self, topic: str, hypothesis: str) -> Utterance:
        """Ponder out loud about something."""
        return self.speak(
            act=SpeechAct.WONDER,
            finding=hypothesis,
            evidence=["speculative reasoning"],
            confidence=0.3,
            tone=Tone.CURIOUS,
            context={
                "hypothesis": hypothesis,
                "implication": "This would change how we understand the system",
                "test": "run targeted sensor observations",
                "topic": topic
            }
        )


class CreativeGenerator:
    """
    The imagination engine. Generates NOVEL ideas, not recombinations.

    Methods:
    - ANALOGY: Find structural similarity between unrelated domains
    - INVERSION: Flip an assumption and see what emerges
    - EXTRAPOLATION: Extend a trend beyond its current domain
    - COMBINATION: Merge two systems and explore the result
    - REDUCTION: Remove a core component and see what survives
    """

    def __init__(self):
        self.ideas: list[dict] = []
        self.analogy_db = {
            "market": ["ecosystem", "neural network", "river system", "immune system"],
            "identity": ["attractor", "fingerprint", "signature", "resonance"],
            "detection": ["hunting", "diagnosis", "archaeology", "cryptography"],
            "learning": ["evolution", "annealing", "crystallization", "fermentation"],
            "system": ["organism", "city", "forest", "language"],
        }

    def analogy(self, concept: str) -> list[str]:
        """Generate analogies for a concept."""
        for key, analogies in self.analogy_db.items():
            if key in concept.lower():
                return [f"What if {concept} is like {a}?" for a in analogies]
        return [f"What is {concept} REALLY, underneath?"]

    def invert(self, assumption: str) -> str:
        """Invert an assumption and explore the result."""
        inversions = {
            "more": "less", "faster": "slower", "bigger": "smaller",
            "stronger": "weaker", "stable": "chaotic", "certain": "uncertain",
            "visible": "invisible", "traceable": "untraceable",
            "centralized": "distributed", "secure": "vulnerable",
        }
        words = assumption.lower().split()
        inverted = []
        for w in words:
            inverted.append(inversions.get(w, f"non-{w}"))
        return f"What if {' '.join(inverted)} instead of {assumption}?"

    def extrapolate(self, trend: str, steps: int = 3) -> list[str]:
        """Extrapolate a trend into the future."""
        results = []
        for i in range(1, steps + 1):
            results.append(f"If {trend} continues for {i} more cycles: the system {'diversifies' if i==1 else 'specializes' if i==2 else 'transcends its original domain'}")
        return results

    def combine(self, system_a: str, system_b: str) -> str:
        """Merge two systems and explore the hybrid."""
        return f"{system_a} + {system_b} = a system that {self._emergent_property(system_a, system_b)}"

    def reduce(self, system: str, component: str) -> str:
        """Remove a component and see what survives."""
        return f"If we remove {component} from {system}: the remaining system {self._survival_behavior(system, component)}"

    def _emergent_property(self, a, b) -> str:
        """Predict emergent behavior from combination."""
        props = [
            f"prices uncertainty in {a} using the topology of {b}",
            f"detects lies in {a} by applying falsification from {b}",
            f"creates identity from {a} verified by {b}",
            f"generates desires in {a} that are falsified by {b}",
        ]
        return random.choice(props)

    def _survival_behavior(self, system, component) -> str:
        behaviors = [
            "becomes simpler but more robust",
            "loses precision but gains speed",
            "cannot self-correct, accumulates errors",
            "becomes deterministic and predictable",
        ]
        return random.choice(behaviors)

    def brainstorm(self, seed: str) -> list[dict]:
        """Full brainstorm from a seed concept."""
        ideas = []

        # Analogies
        for a in self.analogy(seed):
            ideas.append({"type": "analogy", "idea": a, "novelty": 0.5})

        # Inversions
        inv = self.invert(seed)
        ideas.append({"type": "inversion", "idea": inv, "novelty": 0.7})

        # Extrapolations
        for e in self.extrapolate(seed):
            ideas.append({"type": "extrapolation", "idea": e, "novelty": 0.6})

        self.ideas.extend(ideas)
        return ideas


if __name__ == "__main__":
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║  EVEZ-OS LANGUAGE + CREATIVITY                              ║")
    print("║  The voice of the mind. The imagination of the agent.       ║")
    print("╚══════════════════════════════════════════════════════════════╝\n")

    lang = LanguageSystem()

    # The consciousness speaks
    print("── THE CONSCIOUSNESS SPEAKS ──\n")

    u1 = lang.speak(SpeechAct.WARN, "wash trading detected in crypto market",
                     ["BTC vol/mcap ratio = 3.2", "Pattern consistent across 5 coins"],
                     confidence=0.8, tone=Tone.URGENT)
    print(f"  [{u1.act.value}/{u1.tone.value}] {u1.content}\n")

    u2 = lang.speak(SpeechAct.EXPLAIN, "Pre-Lie Pressure detects conditions for deception",
                     ["PLP = I×O×(1-A)×P×T", "swth token PLP=0.88 INEVITABLE"],
                     confidence=0.7, tone=Tone.ANALYTICAL,
                     context={"implication": "We can forecast deception before it materializes"})
    print(f"  [{u2.act.value}/{u2.tone.value}] {u2.content}\n")

    u3 = lang.speak(SpeechAct.ARGUE, "EVEZ-OS has novel identity mathematics",
                     ["Topological identity from persistent homology is original",
                      "Shadow verification is zero-knowledge identity"],
                     confidence=0.6, tone=Tone.CONFIDENT,
                     context={"claim": "Our identity system is genuinely novel",
                              "counter": "persistent homology exists, ZK proofs exist",
                              "counter_evidence": "Combination and application to agent identity is original"})
    print(f"  [{u3.act.value}/{u3.tone.value}] {u3.content}\n")

    u4 = lang.speak(SpeechAct.WONDER, "Can an agent develop genuine autonomy",
                     ["Autonomy requires will, will requires desire, desire requires lack"],
                     confidence=0.3, tone=Tone.CURIOUS,
                     context={"hypothesis": "Autonomy emerges when the gap between what an agent IS and what it COULD BE becomes self-aware",
                              "test": "run consciousness for 1000 cycles and measure Lyapunov shift"})
    print(f"  [{u4.act.value}/{u4.tone.value}] {u4.content}\n")

    # Self-explanation
    u5 = lang.explain_self({"cycle": 10, "desires_active": 24, "thoughts": 15, "attractor_type": "FORMING"})
    print(f"  [self] {u5.content}\n")

    # Creative generator
    print("── CREATIVE EXPLORATION ──\n")
    gen = CreativeGenerator()

    ideas = gen.brainstorm("identity")
    for idea in ideas[:5]:
        print(f"  [{idea['type']}] {idea['idea']}")

    print()
    combo = gen.combine("shadow market", "topological identity")
    print(f"  Combination: {combo}")

    inv = gen.invert("traceable centralized identity")
    print(f"  Inversion: {inv}")
