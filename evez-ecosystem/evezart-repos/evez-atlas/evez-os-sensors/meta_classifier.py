"""
EVEZ-OS META-CLASSIFIER — The System That Dissects Systems

Give it anything: code, an API, a concept, a data structure, a claim.
It applies EVERY analytical lens simultaneously, then cross-references
all lenses to find what no single lens sees.

The classifier classifies itself. Recursive. No escape.
"""

import hashlib
import json
import math
import os
import re
import time
import ast
import sys
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
from collections import defaultdict, Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from poly_c import poly_c, PolyCResult
from simplicial_topology import SimplicialComplex


class LensDomain(str, Enum):
    STRUCTURAL = "structural"
    SEMANTIC = "semantic"
    TEMPORAL = "temporal"
    EPISTEMIC = "epistemic"
    ECONOMIC = "economic"
    INFORMATION = "information"
    FALSIFICATION = "falsification"
    ADVERSARIAL = "adversarial"
    TELEOLOGICAL = "teleological"
    LINGUISTIC = "linguistic"
    TOPOLOGICAL = "topological"
    SELF_REFERENTIAL = "self_referential"


class Strength(str, Enum):
    NULL = "NULL"
    WEAK = "WEAK"
    MODERATE = "MODERATE"
    STRONG = "STRONG"
    DEFINITIVE = "DEFINITIVE"


@dataclass
class Cls:
    """One classification from one lens."""
    lens: LensDomain
    label: str
    description: str
    strength: Strength
    confidence: float
    evidence: dict
    cross_refs: list = field(default_factory=list)
    hash: str = ""

    def __post_init__(self):
        raw = f"{self.lens.value}:{self.label}:{self.confidence:.6f}"
        self.hash = hashlib.sha256(raw.encode()).hexdigest()[:12]


@dataclass
class CrossRef:
    """Intersection between lenses. Discovery lives here."""
    lenses: list[LensDomain]
    finding: str
    significance: float
    evidence: dict
    novelty: float  # 0=obvious, 1=never seen


@dataclass
class Dissection:
    """Complete dissection from all lenses."""
    subject: str
    subject_type: str
    classifications: list[Cls]
    cross_references: list[CrossRef]
    topology: dict
    entropy: dict
    falsification: dict
    self_reference: dict
    poly_c_summary: dict
    timestamp: float = field(default_factory=time.time)
    hash: str = ""

    def __post_init__(self):
        raw = f"{self.subject[:100]}:{len(self.classifications)}:{self.timestamp}"
        self.hash = hashlib.sha256(raw.encode()).hexdigest()[:16]


def detect_subject_type(subject: str) -> str:
    if any(p in subject for p in ["def ", "class ", "import ", "function ", "=>", "{", "};"]):
        return "code"
    if subject.strip().startswith("#!") or subject.strip().startswith("//"):
        return "code"
    if re.match(r'https?://', subject.strip()):
        return "api"
    if any(p in subject.lower() for p in ["endpoint", "api", "graphql", "rest"]):
        return "api"
    if any(p in subject.lower() for p in ["is ", "are ", "will ", "can ", "proves ", "means "]):
        return "claim"
    if subject.strip().startswith("{") or subject.strip().startswith("["):
        try:
            json.loads(subject)
            return "data"
        except:
            pass
    if any(p in subject.lower() for p in ["system", "architecture", "pipeline", "framework", "engine"]):
        return "system"
    return "concept"


# ─── LENSES ─────────────────────────────────────────────────────

def lens_structural(subject: str, stype: str) -> list[Cls]:
    results = []
    if stype == "code":
        try:
            tree = ast.parse(subject)
            classes = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
            funcs = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
            imports = [n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))]
            calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)]
            cpf = len(calls) / max(len(funcs), 1)
            if cpf > 5:
                results.append(Cls(LensDomain.STRUCTURAL, "HIGH_COUPLING",
                    f"Call density {cpf:.1f}/func — fragile to change", Strength.STRONG,
                    min(1.0, cpf/10), {"calls_per_func": round(cpf, 2)}))
            elif cpf < 1.5:
                results.append(Cls(LensDomain.STRUCTURAL, "LOW_COUPLING",
                    f"Call density {cpf:.1f}/func — modular, possibly fragmented", Strength.MODERATE,
                    0.6, {"calls_per_func": round(cpf, 2)}))
            results.append(Cls(LensDomain.STRUCTURAL, "STRUCTURE_MAP",
                f"{len(classes)} classes, {len(funcs)} functions, {len(imports)} imports, {len(calls)} calls",
                Strength.DEFINITIVE, 0.95,
                {"classes": len(classes), "functions": len(funcs),
                 "imports": len(imports), "calls": len(calls),
                 "class_names": [c.name for c in classes[:10]],
                 "function_names": [f.name for f in funcs[:10]]}))
        except SyntaxError:
            lines = subject.splitlines()
            indent_levels = set()
            for line in lines:
                if line.strip():
                    indent_levels.add(len(line) - len(line.lstrip()))
            results.append(Cls(LensDomain.STRUCTURAL, "INDIRECT",
                f"Non-Python: {len(lines)} lines, {len(indent_levels)} indent levels",
                Strength.MODERATE, 0.5, {"lines": len(lines)}))
    else:
        words = subject.split()
        unique = set(w.lower() for w in words if len(w) > 3)
        results.append(Cls(LensDomain.STRUCTURAL, "COMPOSITION",
            f"{len(words)} tokens, {len(unique)} unique concepts",
            Strength.MODERATE, 0.5, {"tokens": len(words), "unique": len(unique)}))
    return results


def lens_semantic(subject: str, stype: str) -> list[Cls]:
    results = []
    text = subject.lower()
    INTENTS = {
        "CONTROL": ["manage", "control", "orchestrate", "coordinate", "govern"],
        "COMPUTE": ["compute", "calculate", "process", "transform", "evaluate"],
        "STORE": ["store", "persist", "cache", "save", "record", "archive"],
        "COMMUNICATE": ["send", "receive", "broadcast", "notify", "emit"],
        "PROTECT": ["validate", "authenticate", "encrypt", "guard", "shield"],
        "DISCOVER": ["search", "find", "detect", "scan", "explore", "discover"],
        "DESTROY": ["delete", "remove", "purge", "falsify", "invalidate", "kill"],
        "CREATE": ["create", "build", "generate", "compose", "construct", "spawn"],
    }
    scores = {k: sum(1 for w in v if w in text) for k, v in INTENTS.items()}
    scores = {k: v for k, v in scores.items() if v > 0}
    if scores:
        dominant = max(scores, key=scores.get)
        results.append(Cls(LensDomain.SEMANTIC, "PRIMARY_INTENT",
            f"Primary intent: {dominant} (score: {scores[dominant]})",
            Strength.STRONG if scores[dominant] > 2 else Strength.MODERATE,
            min(1.0, scores[dominant]/5), {"intent_scores": scores, "dominant": dominant}))

    assumptions = []
    if "efficient" in text: assumptions.append("assumes efficiency > correctness")
    if "simple" in text or "easy" in text: assumptions.append("assumes simplicity is achievable")
    if "always" in text or "never" in text: assumptions.append("assumes universal quantification (likely false at edges)")
    if "should" in text: assumptions.append("normative claim, not descriptive")
    if "obvious" in text or "clearly" in text: assumptions.append("assumes shared understanding (flag for unclear thinking)")
    if "just" in text: assumptions.append("minimization framing — dismissing complexity")
    if assumptions:
        results.append(Cls(LensDomain.SEMANTIC, "HIDDEN_ASSUMPTIONS",
            f"{len(assumptions)} hidden assumptions in language",
            Strength.STRONG, 0.7, {"assumptions": assumptions}))

    onto = []
    if any(w in text for w in ["class", "type", "category"]): onto.append("TAXONOMIC")
    if any(w in text for w in ["process", "flow", "pipeline", "chain"]): onto.append("PROCESSUAL")
    if any(w in text for w in ["state", "snapshot", "configuration"]): onto.append("STATEFUL")
    if any(w in text for w in ["event", "trigger", "signal"]): onto.append("EVENTFUL")
    if any(w in text for w in ["relation", "connection", "link", "edge"]): onto.append("RELATIONAL")
    if onto:
        results.append(Cls(LensDomain.SEMANTIC, "ONTOLOGY",
            f"Ontological: {', '.join(onto)}", Strength.MODERATE, 0.6, {"types": onto}))
    return results


def lens_temporal(subject: str, stype: str) -> list[Cls]:
    results = []
    text = subject.lower()
    if any(w in text for w in ["version", "history", "changelog", "legacy", "deprecated"]):
        results.append(Cls(LensDomain.TEMPORAL, "HISTORICAL_AWARENESS",
            "References own history — temporal dimension present",
            Strength.MODERATE, 0.5, {}))
    if any(w in text for w in ["forecast", "predict", "will", "future", "next"]):
        results.append(Cls(LensDomain.TEMPORAL, "FUTURE_ORIENTATION",
            "Projects forward — temporal forecasting embedded",
            Strength.MODERATE, 0.5, {}))
    if any(w in text for w in ["deprecated", "legacy", "expire", "timeout", "stale", "drift"]):
        results.append(Cls(LensDomain.TEMPORAL, "DECAY_AWARENESS",
            "Acknowledges decay — entropy awareness", Strength.STRONG, 0.7, {}))
    time_words = ["before", "after", "during", "while", "until", "since", "when", "then", "now", "later"]
    tc = sum(1 for w in time_words if w in text)
    if tc > 3:
        results.append(Cls(LensDomain.TEMPORAL, "TEMPORAL_COMPLEXITY",
            f"High temporal complexity: {tc} temporal operators",
            Strength.MODERATE, min(1.0, tc/8), {"count": tc}))
    return results


def lens_epistemic(subject: str, stype: str) -> list[Cls]:
    results = []
    text = subject.lower()
    certain = sum(1 for w in ["proves", "proven", "guaranteed", "always", "never", "impossible", "certain", "definitely"] if w in text)
    uncertain = sum(1 for w in ["may", "might", "could", "possibly", "perhaps", "likely", "probably", "seems"] if w in text)
    unknown = sum(1 for w in ["unknown", "unclear", "uncertain", "mystery", "paradox", "undefined"] if w in text)
    if certain > uncertain and certain > 0:
        results.append(Cls(LensDomain.EPISTEMIC, "OVERCONFIDENT",
            f"{certain} certainty vs {uncertain} uncertainty markers. Claims more than it knows.",
            Strength.STRONG if certain > 3 else Strength.MODERATE, min(1.0, certain/5),
            {"certain": certain, "uncertain": uncertain}))
    elif uncertain > certain and uncertain > 0:
        results.append(Cls(LensDomain.EPISTEMIC, "EPISTEMIC_HUMILITY",
            f"{uncertain} uncertainty markers. Knows what it doesn't know.",
            Strength.MODERATE, 0.6, {"uncertain": uncertain, "certain": certain}))
    if unknown > 0:
        results.append(Cls(LensDomain.EPISTEMIC, "KNOWLEDGE_BOUNDARY",
            f"{unknown} explicit unknown markers. Acknowledges limits.",
            Strength.STRONG, 0.8, {"unknown": unknown}))
    self_refs = sum(1 for w in ["self", "itself", "recursive", "meta", "reflect", "introspect"] if w in text)
    if self_refs > 0:
        results.append(Cls(LensDomain.EPISTEMIC, "SELF_REFERENTIAL",
            f"{self_refs} self-reference markers. Potential Gödelian boundary.",
            Strength.STRONG, 0.7, {"self_refs": self_refs}))
    return results


def lens_economic(subject: str, stype: str) -> list[Cls]:
    results = []
    text = subject.lower()
    incentives = []
    if "optimize" in text or "efficient" in text: incentives.append("EFFICIENCY")
    if "scale" in text or "growth" in text: incentives.append("SCALE")
    if "secure" in text or "protect" in text: incentives.append("SECURITY")
    if "simple" in text or "easy" in text: incentives.append("SIMPLICITY")
    if "revenue" in text or "monetiz" in text: incentives.append("PROFIT")
    if incentives:
        results.append(Cls(LensDomain.ECONOMIC, "INCENTIVE_STRUCTURE",
            f"Incentive vectors: {', '.join(incentives)}", Strength.MODERATE, 0.6,
            {"incentives": incentives}))
    asymmetries = []
    if "author" in text and "user" in text: asymmetries.append("AUTHOR-USER")
    if any(w in text for w in ["hidden", "shadow", "invisible", "opaque"]): asymmetries.append("INFORMATION")
    if "central" in text or "control" in text: asymmetries.append("CENTRALIZATION")
    if asymmetries:
        results.append(Cls(LensDomain.ECONOMIC, "ASYMMETRY",
            f"Economic asymmetries: {', '.join(asymmetries)}", Strength.STRONG, 0.7,
            {"asymmetries": asymmetries}))
    return results


def lens_information(subject: str, stype: str) -> list[Cls]:
    results = []
    freq = Counter(subject.lower())
    total = len(subject)
    if total > 0:
        entropy = 0
        for count in freq.values():
            p = count / total
            if p > 0: entropy -= p * math.log2(p)
        alpha = len(freq)
        max_e = math.log2(max(alpha, 2))
        norm = entropy / max_e if max_e > 0 else 0
        if norm > 0.95: label, desc = "HIGH_ENTROPY", "Near-max information density. Few redundancies."
        elif norm > 0.7: label, desc = "MODERATE_ENTROPY", "Substantial info with some structure."
        elif norm > 0.4: label, desc = "STRUCTURED", "Patterns dominate over randomness."
        else: label, desc = "LOW_ENTROPY", "Highly repetitive. Little information density."
        results.append(Cls(LensDomain.INFORMATION, label, desc, Strength.STRONG, 0.8,
            {"shannon_entropy": round(entropy, 4), "normalized": round(norm, 4),
             "alphabet_size": alpha, "unique_ratio": round(alpha/max(total,1), 4)}))
    return results


def lens_falsification(subject: str, stype: str) -> list[Cls]:
    results = []
    text = subject.lower()
    vecs = []
    if "always" in text: vecs.append("UNIVERSAL: 'always' — one counterexample falsifies")
    if "never" in text: vecs.append("NEGATIVE_UNIVERSAL: 'never' — one example falsifies")
    if "proves" in text or "proven" in text: vecs.append("PROOF: hidden assumptions may invalidate")
    if "guaranteed" in text: vecs.append("GUARANTEE: conditions may not hold")
    if "impossible" in text: vecs.append("IMPOSSIBILITY: may mean 'not yet possible'")
    if "solves" in text: vecs.append("SOLUTION: may solve wrong problem")
    if stype == "code":
        vecs.extend(["CODE_EDGE: empty/None/MAX_INT/unicode/concurrency",
                      "CODE_STATE: uninitialized/race/resource exhaustion"])
    if vecs:
        results.append(Cls(LensDomain.FALSIFICATION, "VECTORS",
            f"{len(vecs)} falsification vectors", Strength.STRONG, 0.8, {"vectors": vecs}))
    return results


def lens_adversarial(subject: str, stype: str) -> list[Cls]:
    results = []
    text = subject.lower()
    VECTORS = {
        "INJECTION": ["input", "parameter", "query", "command", "template"],
        "ESCALATION": ["permission", "role", "admin", "root", "privilege"],
        "REPLAY": ["token", "session", "auth", "signature", "nonce"],
        "POISONING": ["train", "learn", "model", "data", "sample", "dataset"],
        "EXFILTRATION": ["log", "export", "cache", "store", "persist"],
    }
    found = {k: sum(1 for w in v if w in text) for k, v in VECTORS.items()}
    found = {k: v for k, v in found.items() if v > 0}
    if found:
        results.append(Cls(LensDomain.ADVERSARIAL, "ATTACK_SURFACE",
            f"Attack vectors: {', '.join(found.keys())}", Strength.STRONG, 0.7,
            {"vectors": found}))
    return results


def lens_teleological(subject: str, stype: str) -> list[Cls]:
    results = []
    text = subject.lower()
    purposes = []
    if any(w in text for w in ["detect", "find", "identify", "classify"]): purposes.append("PERCEPTION — makes invisible visible")
    if any(w in text for w in ["control", "manage", "orchestrate"]): purposes.append("CONTROL — centralizes decisions")
    if any(w in text for w in ["protect", "defend", "guard", "secure"]): purposes.append("DEFENSE — creates boundaries")
    if any(w in text for w in ["learn", "adapt", "evolve", "improve"]): purposes.append("EVOLUTION — changes itself")
    if any(w in text for w in ["create", "generate", "build", "compose"]): purposes.append("CREATION — produces novelty")
    if any(w in text for w in ["destroy", "falsify", "break", "attack"]): purposes.append("DESTRUCTION — tests what survives")
    if any(w in text for w in ["record", "log", "persist", "archive", "remember"]): purposes.append("MEMORY — creates continuity")
    if purposes:
        results.append(Cls(LensDomain.TELEOLOGICAL, "DEEP_PURPOSE",
            f"Deep purposes: {len(purposes)}", Strength.STRONG, 0.7, {"purposes": purposes}))
    # Purpose gap detection
    stated = []
    actual = []
    if "monetiz" in text or "revenue" in text: stated.append("STATED: revenue")
    if "product" in text or "store" in text: stated.append("STATED: products")
    if "detect" in text or "discover" in text: actual.append("ACTUAL: knowledge production")
    if "build" in text or "engine" in text: actual.append("ACTUAL: construction")
    if "classify" in text or "analyze" in text: actual.append("ACTUAL: understanding")
    if stated and actual:
        results.append(Cls(LensDomain.TELEOLOGICAL, "PURPOSE_GAP",
            "Stated purpose ≠ actual purpose", Strength.STRONG, 0.8,
            {"stated": stated, "actual": actual}))
    return results


def lens_linguistic(subject: str, stype: str) -> list[Cls]:
    results = []
    text = subject.lower()
    # Narrative framing
    frames = []
    if any(w in text for w in ["revolutionary", "breakthrough", "game changer", "unprecedented"]):
        frames.append("HYPERBOLE — revolutionary language signals insecurity about value")
    if any(w in text for w in ["just", "simply", "merely", "only"]):
        frames.append("MINIMIZATION — dismissing complexity or risk")
    if any(w in text for w in ["obviously", "clearly", "of course", "naturally"]):
        frames.append("FALSE_CONSENSUS — assuming agreement where none exists")
    if any(w in text for w in ["should", "must", "need", "have to"]):
        frames.append("PRESCRIPTIVE — normative claims disguised as facts")
    if any(w in text for w in ["new", "novel", "first", "never before", "unique"]):
        frames.append("NOVELTY_CLAIM — asserting originality (verify independently)")
    if frames:
        results.append(Cls(LensDomain.LINGUISTIC, "NARRATIVE_FRAMING",
            f"{len(frames)} narrative frames detected", Strength.STRONG, 0.8,
            {"frames": frames}))
    return results


def lens_topological(subject: str, stype: str) -> list[Cls]:
    results = []
    text = subject.lower()

    # Build a concept graph from co-occurring terms
    words = [w for w in re.findall(r'\b[a-z]{4,}\b', text)]
    if len(words) >= 3:
        # Co-occurrence within sliding window
        interactions = []
        window = 3
        for i in range(len(words) - window):
            for j in range(i+1, min(i+window, len(words))):
                if words[i] != words[j]:
                    interactions.append((words[i], words[j], 1.0))

        if interactions:
            try:
                complex = SimplicialComplex.from_interactions(interactions, threshold=0.0)
                betti = complex.betti_numbers()
                results.append(Cls(LensDomain.TOPOLOGICAL, "BETTI_SIGNATURE",
                    f"Topological shape: Betti={betti}",
                    Strength.STRONG, 0.8,
                    {"betti": betti,
                     "vertices": len(complex.simplices.get(0, [])),
                     "edges": len(complex.simplices.get(1, [])),
                     "triangles": len(complex.simplices.get(2, []))}))
            except:
                pass

    # Connectivity analysis
    unique_words = set(words)
    if len(unique_words) > 0:
        connectivity = len(words) / len(unique_words)  # repetition = connectivity
        if connectivity > 2.0:
            results.append(Cls(LensDomain.TOPOLOGICAL, "HIGHLY_CONNECTED",
                f"High concept connectivity (ratio: {connectivity:.2f}) — dense conceptual graph",
                Strength.MODERATE, min(1.0, connectivity/5), {"ratio": round(connectivity, 2)}))
        elif connectivity < 1.3:
            results.append(Cls(LensDomain.TOPOLOGICAL, "SPARSE",
                f"Low concept connectivity (ratio: {connectivity:.2f}) — fragmented concepts",
                Strength.MODERATE, 0.5, {"ratio": round(connectivity, 2)}))
    return results


# ─── SELF-REFERENTIAL LENS: THE CLASSIFIER CLASSIFIES ITSELF ───

def lens_self_referential(subject: str, stype: str, all_classifications: list[Cls]) -> list[Cls]:
    """The classifier examines its own process. What does the pattern of
    classifications reveal about the subject that no single lens sees?"""
    results = []

    if not all_classifications:
        return results

    # Which lenses produced strong findings?
    lens_strengths = defaultdict(list)
    for c in all_classifications:
        lens_strengths[c.lens.value].append(c.confidence)

    strong_lenses = [l for l, confs in lens_strengths.items() if max(confs) > 0.7]
    weak_lenses = [l for l, confs in lens_strengths.items() if max(confs) < 0.3]

    if len(strong_lenses) >= 4:
        results.append(Cls(LensDomain.SELF_REFERENTIAL, "RICH_SUBJECT",
            f"Subject resists analysis from {len(strong_lenses)} lenses simultaneously — complex, multi-faceted",
            Strength.STRONG, 0.8, {"strong_lenses": strong_lenses}))

    if len(weak_lenses) >= 4:
        results.append(Cls(LensDomain.SELF_REFERENTIAL, "FLAT_SUBJECT",
            f"Subject yields little from {len(weak_lenses)} lenses — may be shallow or may resist this methodology",
            Strength.MODERATE, 0.5, {"weak_lenses": weak_lenses}))

    # Detect classification patterns
    labels = [c.label for c in all_classifications]
    if "OVERCONFIDENT" in labels and "HIDDEN_ASSUMPTIONS" in labels:
        results.append(Cls(LensDomain.SELF_REFERENTIAL, "HUBRIS_SIGNATURE",
            "Subject claims certainty while hiding assumptions — classic overconfidence pattern",
            Strength.STRONG, 0.9,
            {"pattern": "OVERCONFIDENT + HIDDEN_ASSUMPTIONS = hubris"}))

    if "HIGH_COUPLING" in labels and "ATTACK_SURFACE" in labels:
        results.append(Cls(LensDomain.SELF_REFERENTIAL, "FRAGILITY_SIGNATURE",
            "High coupling + attack surface = fragile system. Small changes cascade. Attacks spread.",
            Strength.STRONG, 0.9,
            {"pattern": "HIGH_COUPLING + ATTACK_SURFACE = fragility"}))

    if "SELF_REFERENTIAL" in [c.label for c in all_classifications if c.lens == LensDomain.EPISTEMIC]:
        results.append(Cls(LensDomain.SELF_REFERENTIAL, "GODELIAN_CANDIDATE",
            "Subject is self-referential. May contain undecidable propositions. Cannot fully analyze itself from within.",
            Strength.STRONG, 0.8,
            {"pattern": "Self-reference detected — Gödelian incompleteness boundary"}))

    if "PURPOSE_GAP" in labels:
        results.append(Cls(LensDomain.SELF_REFERENTIAL, "SELF_DECEPTION_SIGNAL",
            "Gap between stated and actual purpose — the subject may be deceiving itself about its own nature",
            Strength.STRONG, 0.9,
            {"pattern": "PURPOSE_GAP = potential self-deception"}))

    return results


# ─── CROSS-REFERENCE ENGINE ─────────────────────────────────────

def cross_reference(all_cls: list[Cls]) -> list[CrossRef]:
    """Find intersections between lenses. What no single lens sees."""
    refs = []

    # Group by lens
    by_lens = defaultdict(list)
    for c in all_cls:
        by_lens[c.lens].append(c)

    # Pairwise intersections
    lens_pairs = []
    lenses = list(by_lens.keys())
    for i in range(len(lenses)):
        for j in range(i+1, len(lenses)):
            lens_pairs.append((lenses[i], lenses[j]))

    for l1, l2 in lens_pairs:
        for c1 in by_lens[l1]:
            for c2 in by_lens[l2]:
                # Check for conceptual overlap in evidence
                ev1_keys = set(str(k) for k in c1.evidence.keys())
                ev2_keys = set(str(k) for k in c2.evidence.keys())
                overlap = ev1_keys & ev2_keys

                # Also check if descriptions reference similar concepts
                w1 = set(re.findall(r'\b[a-z]{4,}\b', c1.description.lower()))
                w2 = set(re.findall(r'\b[a-z]{4,}\b', c2.description.lower()))
                word_overlap = w1 & w2 - {"with", "from", "that", "this", "been", "have", "will", "were", "they", "their", "what", "when", "than", "more"}

                if overlap or len(word_overlap) >= 2:
                    # Cross-reference found!
                    combined_conf = (c1.confidence + c2.confidence) / 2
                    novelty = 1.0 - min(c1.confidence, c2.confidence)  # Weak agreement = high novelty

                    # poly_c significance
                    pc = poly_c(0, combined_conf, 0.5, [1], 1)

                    refs.append(CrossRef(
                        lenses=[l1, l2],
                        finding=f"{c1.label} × {c2.label}: {c1.description[:50]} intersects {c2.description[:50]}",
                        significance=round(pc.value, 6),
                        evidence={
                            "lens1": {"domain": l1.value, "label": c1.label, "confidence": c1.confidence},
                            "lens2": {"domain": l2.value, "label": c2.label, "confidence": c2.confidence},
                            "concept_overlap": list(word_overlap)[:5],
                        },
                        novelty=round(novelty, 4)
                    ))

    # Sort by novelty (most novel = most interesting)
    refs.sort(key=lambda r: -r.novelty)
    return refs[:50]  # Top 50 cross-references


# ─── THE META-CLASSIFIER ────────────────────────────────────────

def dissect(subject: str) -> Dissection:
    """
    Dissect a subject from every lens imaginable.
    Cross-reference all findings.
    The classifier classifies itself.
    """
    stype = detect_subject_type(subject)

    # Phase 1: Apply all lenses
    all_cls = []
    all_cls.extend(lens_structural(subject, stype))
    all_cls.extend(lens_semantic(subject, stype))
    all_cls.extend(lens_temporal(subject, stype))
    all_cls.extend(lens_epistemic(subject, stype))
    all_cls.extend(lens_economic(subject, stype))
    all_cls.extend(lens_information(subject, stype))
    all_cls.extend(lens_falsification(subject, stype))
    all_cls.extend(lens_adversarial(subject, stype))
    all_cls.extend(lens_teleological(subject, stype))
    all_cls.extend(lens_linguistic(subject, stype))
    all_cls.extend(lens_topological(subject, stype))

    # Phase 2: Self-referential lens (uses all other classifications)
    all_cls.extend(lens_self_referential(subject, stype, all_cls))

    # Phase 3: Cross-reference
    cross_refs = cross_reference(all_cls)

    # Phase 4: Topological summary
    topology = {"betti": [], "vertices": 0, "edges": 0}
    topo_cls = [c for c in all_cls if c.lens == LensDomain.TOPOLOGICAL]
    for c in topo_cls:
        if c.label == "BETTI_SIGNATURE":
            topology["betti"] = c.evidence.get("betti", [])
            topology["vertices"] = c.evidence.get("vertices", 0)
            topology["edges"] = c.evidence.get("edges", 0)

    # Phase 5: Entropy summary
    entropy = {}
    info_cls = [c for c in all_cls if c.lens == LensDomain.INFORMATION]
    for c in info_cls:
        entropy.update(c.evidence)

    # Phase 6: Falsification summary
    falsification = {"vectors": [], "assumptions": []}
    fals_cls = [c for c in all_cls if c.lens == LensDomain.FALSIFICATION]
    for c in fals_cls:
        if c.label == "VECTORS":
            falsification["vectors"] = c.evidence.get("vectors", [])

    # Phase 7: Self-reference summary
    self_ref = {"patterns": []}
    sr_cls = [c for c in all_cls if c.lens == LensDomain.SELF_REFERENTIAL]
    for c in sr_cls:
        self_ref["patterns"].append({"label": c.label, "description": c.description, "confidence": c.confidence})

    # Phase 8: poly_c summary
    poly_c_values = []
    for c in all_cls:
        pc = poly_c(0, c.confidence, 0.5, topology["betti"] or [1], len(all_cls))
        poly_c_values.append(pc.value)
    poly_c_summary = {
        "max": round(max(poly_c_values), 6) if poly_c_values else 0,
        "avg": round(sum(poly_c_values)/len(poly_c_values), 6) if poly_c_values else 0,
        "count": len(poly_c_values),
    }

    return Dissection(
        subject=subject[:500],
        subject_type=stype,
        classifications=all_cls,
        cross_references=cross_refs,
        topology=topology,
        entropy=entropy,
        falsification=falsification,
        self_reference=self_ref,
        poly_c_summary=poly_c_summary,
    )


def format_dissection(d: Dissection) -> str:
    """Format a dissection as readable output."""
    lines = []
    lines.append("╔══════════════════════════════════════════════════════════════╗")
    lines.append("║  EVEZ-OS META-CLASSIFIER — Full Dissection                 ║")
    lines.append("╚══════════════════════════════════════════════════════════════╝")
    lines.append(f"\n  Subject: {d.subject[:100]}")
    lines.append(f"  Type: {d.subject_type}")
    lines.append(f"  Classifications: {len(d.classifications)}")
    lines.append(f"  Cross-references: {len(d.cross_references)}")
    lines.append(f"  poly_c: max={d.poly_c_summary['max']}, avg={d.poly_c_summary['avg']}")

    lines.append(f"\n{'─'*60}")
    lines.append("  CLASSIFICATIONS BY LENS")
    lines.append(f"{'─'*60}")

    by_lens = defaultdict(list)
    for c in d.classifications:
        by_lens[c.lens.value].append(c)

    for lens_name in sorted(by_lens.keys()):
        lines.append(f"\n  ▸ {lens_name.upper()}")
        for c in by_lens[lens_name]:
            lines.append(f"    [{c.strength.value}] {c.label} (confidence: {c.confidence:.2f})")
            lines.append(f"    {c.description}")

    if d.cross_references:
        lines.append(f"\n{'─'*60}")
        lines.append("  CROSS-REFERENCES (lens intersections)")
        lines.append(f"{'─'*60}")
        for cr in d.cross_references[:15]:
            lines.append(f"\n  × {cr.finding[:100]}")
            lines.append(f"    significance={cr.significance} novelty={cr.novelty}")

    if d.self_reference.get("patterns"):
        lines.append(f"\n{'─'*60}")
        lines.append("  SELF-REFERENTIAL PATTERNS")
        lines.append(f"{'─'*60}")
        for p in d.self_reference["patterns"]:
            lines.append(f"\n  ⟲ {p['label']} (confidence: {p['confidence']:.2f})")
            lines.append(f"    {p['description']}")

    if d.falsification.get("vectors"):
        lines.append(f"\n{'─'*60}")
        lines.append("  FALSIFICATION VECTORS")
        lines.append(f"{'─'*60}")
        for v in d.falsification["vectors"][:10]:
            lines.append(f"    ⚡ {v}")

    lines.append(f"\n{'═'*60}")
    lines.append(f"  DISSECTION HASH: {d.hash}")
    lines.append(f"  Topology: Betti={d.topology.get('betti', [])} | Vertices={d.topology.get('vertices', 0)} | Edges={d.topology.get('edges', 0)}")
    lines.append(f"  Entropy: {d.entropy.get('shannon_entropy', 0)} bits (normalized: {d.entropy.get('normalized', 0)})")
    lines.append(f"{'═'*60}")
    return "\n".join(lines)


def main():
    """Demo: dissect the meta-classifier with itself."""
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║  EVEZ-OS META-CLASSIFIER — Dissecting Reality              ║")
    print("║  Every lens. Every angle. Every cross-reference.           ║")
    print("╚══════════════════════════════════════════════════════════════╝\n")

    # Dissect the organism code
    with open(os.path.abspath(__file__)) as f:
        self_code = f.read()

    print("── DISSECTING THE META-CLASSIFIER WITH ITSELF ──\n")
    d = dissect(self_code)
    print(format_dissection(d))

    # Now dissect a claim
    print("\n\n── DISSECTING A CLAIM ──\n")
    claim = "This AI system always detects lies before they happen and is guaranteed to be novel"
    d2 = dissect(claim)
    print(format_dissection(d2))

    # Now dissect the organism
    print("\n\n── DISSECTING THE ORGANISM ──\n")
    org_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "organism.py")
    if os.path.exists(org_path):
        with open(org_path) as f:
            org_code = f.read()
        d3 = dissect(org_code)
        print(format_dissection(d3))


if __name__ == "__main__":
    main()
