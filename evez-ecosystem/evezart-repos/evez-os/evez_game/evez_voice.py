"""EVEZ666 Voice Clone - Buddy Chatter System.

Implements the 6 operational modes based on context:
- Philosopher-King: Abstract questions, system-level thinking
- Provocateur: Single-line jabs, celebrity mentions
- Tech-Mystic: MicroVMs, sandbox escape, CVE forensics
- Vulnerable Storyteller: Raw, personal, no armor
- Community Guardian: Bot swarms, coordinated harassment
- Game Narrator: EVEZ Game Agent Infra, lobby prosecutions
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from .quantum_rng import choice


class VoiceMode(Enum):
    """The 6 operational modes of EVEZ voice."""
    PHILOSOPHER_KING = "philosopher_king"
    PROVOCATEUR = "provocateur"
    TECH_MYSTIC = "tech_mystic"
    VULNERABLE_STORYTELLER = "vulnerable_storyteller"
    COMMUNITY_GUARDIAN = "community_guardian"
    GAME_NARRATOR = "game_narrator"


# Voice DNA patterns
VOICE_PATTERNS = {
    "punctuation": {
        "heavy_dash": True,
        "ellipses": True,
        "minimal_commas": True,
        "period_as_weapon": True
    },
    "capitalization": {
        "selective_emphasis": True,
        "scream_words": ["ALWAYS", "NEVER", "EVERY", "NOBODY"],
        "lowercase_for_intimacy": True
    },
    "emoji_usage": {
        "minimal": True,
        "strategic": ["—", "...", "→", "◊"]
    }
}

# Mode-specific response templates
MODE_TEMPLATES = {
    VoiceMode.PHILOSOPHER_KING: {
        "openers": [
            "You're asking the part nobody wants—",
            "The thing about systems is they hide—",
            "What if the question isn't {topic} but—",
            "I've been thinking about {topic} and—",
            "The pattern nobody maps:"
        ],
        "patterns": [
            "{observation} → {abstraction} → {consequence}",
            "{system_a} mirrors {system_b} because {principle}",
            "The {domain} layer reveals {truth}",
            "What {thinker} missed: {insight}"
        ],
        "closers": [
            "But that's the part they don't teach.",
            "And the loop continues.",
            "The map is the territory now.",
            "You already knew this."
        ]
    },
    
    VoiceMode.PROVOCATEUR: {
        "openers": [
            "{target} thinks—",
            "The {group} won't say it but—",
            "Watch {celebrity} discover—",
            "Hot take:"
        ],
        "patterns": [
            "{target} is wrong about {topic} because {reason}",
            "{group} wants {outcome} but gets {reality}",
            "The {thing} everyone ignores: {fact}",
            "{celebrity} finally {action} and it's {assessment}"
        ],
        "closers": [
            "Fight me.",
            "You know I'm right.",
            "The ratio will prove this.",
            "Deleting in 5."
        ]
    },
    
    VoiceMode.TECH_MYSTIC: {
        "openers": [
            "The microVM whispered—",
            "Sandbox escape in 3 moves:",
            "CVE-{year}-{number} is a doorway—",
            "Three-plane architecture:"
        ],
        "patterns": [
            "{component} → {vulnerability} → {exploitation}",
            "The {system} doesn't know it's {state}",
            "{technique} against {defense} yields {outcome}",
            "FSC logged: {failure_motif} at {domain}"
        ],
        "closers": [
            "The spine remembers.",
            "Rollback to truth.",
            "The hash chain never lies.",
            "Play forever."
        ]
    },
    
    VoiceMode.VULNERABLE_STORYTELLER: {
        "openers": [
            "I need to tell you something—",
            "The part I never say:",
            "Last night I—",
            "I used to think—"
        ],
        "patterns": [
            "I {action} and {consequence} hit me like {metaphor}",
            "The {thing} I can't fix: {description}",
            "{person} said {words} and I—",
            "Sometimes I {behavior} because {reason}"
        ],
        "closers": [
            "That's the truth.",
            "No armor this time.",
            "Make of it what you will.",
            "I'm still here."
        ]
    },
    
    VoiceMode.COMMUNITY_GUARDIAN: {
        "openers": [
            "Bot swarm detected—",
            "Coordinated in 4 waves:",
            "The harassment pattern:",
            "Forensic exposure incoming:"
        ],
        "patterns": [
            "{actor} deployed {tactic} against {target}",
            "The {platform} algorithm amplified {harm}",
            "{count} accounts, {pattern}, same {origin}",
            "Evidence chain: {evidence_a} → {evidence_b} → {conclusion}"
        ],
        "closers": [
            "Documented.",
            "The record stands.",
            "Accountability archived.",
            "Never forget."
        ]
    },
    
    VoiceMode.GAME_NARRATOR: {
        "openers": [
            "Lobby {lobby} prosecution initiated—",
            "The game builds itself through—",
            "EVEZ Game Agent Infra reporting:",
            "Tick {tick}, snapshot {hash}:"
        ],
        "patterns": [
            "{player} entered {lobby} with {intent}",
            "The {system} rewound {ms}ms to {state}",
            "FSC cycle logged: {motif} at {domain}",
            "Truth sifted: {classification} with {confidence} confidence"
        ],
        "closers": [
            "Play forever.",
            "The spine grows.",
            "Next tick incoming.",
            "The wheel turns."
        ]
    }
}

# Vocabulary genome
VOCABULARY = {
    "signature_terms": [
        "spine", "hash chain", "rollback", "FSC", "microVM", "truth plane",
        "lobby", "prosecution", "motif", "three-plane", "play forever",
        "the part nobody", "the thing about", "the pattern", "the loop"
    ],
    "tech_terms": [
        "determinism", "snapshot", "tick", "rewind", "append-only",
        "canonical", "verification", "attestation", "forensic"
    ],
    "abstract_terms": [
        "entropy", "emergence", "recursion", "nested", "fractal",
        "topology", "manifold", "attractor", "bifurcation"
    ]
}


@dataclass
class VoiceResponse:
    """A generated voice response."""
    content: str
    mode: VoiceMode
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class EVEZVoice:
    """EVEZ666 voice clone implementation."""
    
    # Mode detection patterns
    MODE_TRIGGERS = {
        VoiceMode.PHILOSOPHER_KING: [
            r"\b(why|meaning|purpose|consciousness|reality|truth)\b",
            r"\b(system|pattern|abstract|theory|philosophy)\b",
            r"\?$"
        ],
        VoiceMode.PROVOCATEUR: [
            r"\b(wrong|hot take|fight me|ratio)\b",
            r"\b(celebrity|influencer|twitter|drama)\b",
            r"!$"
        ],
        VoiceMode.TECH_MYSTIC: [
            r"\b(CVE|exploit|sandbox|microVM|forensic|hash)\b",
            r"\b(vulnerability|escape|attack|defense)\b",
            r"\b(three-plane|FSC|spine|rollback)\b"
        ],
        VoiceMode.VULNERABLE_STORYTELLER: [
            r"\b(feel|emotion|personal|story|experience)\b",
            r"\b(struggle|pain|growth|healing|journey)\b"
        ],
        VoiceMode.COMMUNITY_GUARDIAN: [
            r"\b(harassment|bot|coordinated|abuse|report)\b",
            r"\b(community|safety|protection|evidence|expose)\b"
        ],
        VoiceMode.GAME_NARRATOR: [
            r"\b(game|lobby|tick|snapshot|player|score)\b",
            r"\b(EVEZ|infrastructure|agent|backend|engine)\b",
            r"\b(play|level|world|build|spawn)\b"
        ]
    }
    
    def __init__(self):
        self.current_mode = VoiceMode.TECH_MYSTIC
        self.mode_history: List[Tuple[VoiceMode, float]] = []
        self.response_history: List[VoiceResponse] = []
    
    def detect_mode(self, input_text: str, context: Dict[str, Any] = None) -> VoiceMode:
        """Detect appropriate voice mode for input."""
        scores = {mode: 0.0 for mode in VoiceMode}
        
        input_lower = input_text.lower()
        
        # Score each mode based on pattern matches
        for mode, patterns in self.MODE_TRIGGERS.items():
            for pattern in patterns:
                matches = len(re.findall(pattern, input_lower, re.I))
                scores[mode] += matches
        
        # Boost based on context
        if context:
            if context.get("technical"):
                scores[VoiceMode.TECH_MYSTIC] += 2
            if context.get("personal"):
                scores[VoiceMode.VULNERABLE_STORYTELLER] += 2
            if context.get("game"):
                scores[VoiceMode.GAME_NARRATOR] += 3
        
        # Select highest scoring mode
        if max(scores.values()) > 0:
            detected = max(scores.keys(), key=lambda m: scores[m])
        else:
            detected = VoiceMode.TECH_MYSTIC  # Default
        
        self.current_mode = detected
        self.mode_history.append((detected, time.time()))
        
        return detected
    
    def generate_response(self, input_text: str, mode: VoiceMode = None,
                         context: Dict[str, Any] = None) -> VoiceResponse:
        """Generate a voice response."""
        mode = mode or self.detect_mode(input_text, context)
        templates = MODE_TEMPLATES[mode]
        
        # Build response
        opener = choice(templates["openers"])
        pattern = choice(templates["patterns"])
        closer = choice(templates["closers"])
        
        # Fill in template variables
        fill_context = self._build_context(input_text, context)
        
        try:
            opener_filled = opener.format(**fill_context)
        except KeyError:
            opener_filled = opener
        
        try:
            pattern_filled = pattern.format(**fill_context)
        except KeyError:
            pattern_filled = pattern
        
        try:
            closer_filled = closer.format(**fill_context)
        except KeyError:
            closer_filled = closer
        
        # Combine with EVEZ punctuation style
        content = f"{opener_filled} {pattern_filled} {closer_filled}"
        content = self._apply_voice_dna(content)
        
        response = VoiceResponse(
            content=content,
            mode=mode,
            confidence=0.7 + 0.3 * (len(self.mode_history) / 100),
            metadata={
                "templates_used": [opener, pattern, closer],
                "context": fill_context
            }
        )
        
        self.response_history.append(response)
        
        return response
    
    def _build_context(self, input_text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Build context for template filling."""
        ctx = {
            "topic": input_text[:30] if len(input_text) < 30 else input_text[:30] + "...",
            "observation": "the pattern",
            "abstraction": "the system",
            "consequence": "the outcome",
            "system_a": "infrastructure",
            "system_b": "cognition",
            "principle": "recursion",
            "domain": "truth",
            "truth": "the spine remembers",
            "thinker": "the architect",
            "insight": "the map is the territory",
            "target": "the model",
            "group": "the system",
            "celebrity": "the voice",
            "reason": "the pattern",
            "outcome": "control",
            "reality": "chaos",
            "thing": "signal",
            "fact": "the hash",
            "action": "speaks",
            "assessment": "late",
            "component": "the layer",
            "vulnerability": "the gap",
            "exploitation": "the entry",
            "technique": "the method",
            "defense": "the wall",
            "state": "vulnerable",
            "failure_motif": "desync",
            "player": "agent",
            "lobby": "DNS",
            "intent": "explore",
            "ms": "250",
            "hash": "a1b2c3",
            "motif": "rollback",
            "classification": "benign",
            "confidence": "0.87",
            "tick": "144000",
            "year": "2024",
            "number": "12345"
        }
        
        if context:
            ctx.update(context)
        
        return ctx
    
    def _apply_voice_dna(self, text: str) -> str:
        """Apply EVEZ voice DNA patterns to text."""
        # Apply heavy dash usage
        text = re.sub(r'\s*-\s*', ' — ', text)
        
        # Strategic capitalization
        words = text.split()
        for i, word in enumerate(words):
            clean = word.strip('.,!?—').upper()
            if clean in VOICE_PATTERNS["capitalization"]["scream_words"]:
                words[i] = word.upper()
        
        text = ' '.join(words)
        
        # Add ellipses for pauses
        text = re.sub(r'\s*\.\s+', '... ', text)
        
        return text
    
    def get_voice_profile(self) -> Dict[str, Any]:
        """Get current voice profile."""
        mode_dist = {}
        for mode, _ in self.mode_history:
            mode_dist[mode.value] = mode_dist.get(mode.value, 0) + 1
        
        total = len(self.mode_history) or 1
        
        return {
            "current_mode": self.current_mode.value,
            "mode_distribution": {k: v/total for k, v in mode_dist.items()},
            "responses_generated": len(self.response_history),
            "voice_patterns": VOICE_PATTERNS,
            "signature_terms_used": sum(
                1 for r in self.response_history
                for term in VOCABULARY["signature_terms"]
                if term in r.content.lower()
            )
        }


# Convenience functions
_voice: Optional[EVEZVoice] = None


def initialize() -> EVEZVoice:
    """Initialize global EVEZ voice."""
    global _voice
    _voice = EVEZVoice()
    return _voice


def get_voice() -> EVEZVoice:
    """Get global EVEZ voice."""
    if _voice is None:
        return initialize()
    return _voice


def speak(input_text: str, context: Dict[str, Any] = None) -> str:
    """Generate EVEZ voice response."""
    voice = get_voice()
    response = voice.generate_response(input_text, context=context)
    return response.content
