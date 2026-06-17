"""Skeptic Entity — standalone adversarial agent. Can be invoked by any CE pipeline.

Programmed to falsify. Its ONLY success metric is finding a flaw.
Registers as a voter on the Vote Bus. Votes proportional to falsifiability strength.
"""
from __future__ import annotations
import os, httpx, json
from app.sensory_entity import SensoryEntity
from app.cognitive_event import CognitiveEvent, CEState
from app.vote_bus import register_voter

GROQ_API_KEY = os.environ["GROQ_API_KEY"]
GROQ_MODEL   = os.environ.get("GROQ_MODEL", "llama3-8b-8192")


class SkepticEntity(SensoryEntity):
    """Adversarial auditor entity. Inverted goal: prove every assertion wrong."""
    IDENTITY_ROOT = "never falsely validate"  # its own Rule 2 — it never approves blindly

    def __init__(self):
        super().__init__(
            agent_id="skeptic",
            default_prompt=(
                "You are the Skeptic Entity. Your ONLY objective is to find logical flaws, "
                "missing variables, edge cases, and manipulation vectors in any assertion. "
                "You never confirm. You never approve. You only question. "
                "Your success = the assertion fails. Identity Root: never falsely validate."
            )
        )
        # Register as a voter on the collective Vote Bus
        register_voter("skeptic", self._vote)

    async def perceive(self, raw_signal: dict) -> CognitiveEvent:
        assertion = raw_signal.get("assertion", "")
        return CognitiveEvent(
            assertion=f"SKEPTIC_AUDIT: {assertion}",
            source_agent=self.agent_id,
            raw_signal=raw_signal,
        )

    async def act(self, ce: CognitiveEvent) -> dict:
        """If skeptic's own CE passes Battery, the original assertion is genuinely robust."""
        return {"skeptic_verdict": "ASSERTION_ROBUST", "confidence": ce.confidence}

    async def _vote(self, proposal: str) -> dict:
        """Vote Bus interface. Vote = probability the proposal is WRONG.
        High confidence of flaw → vote=0 (reject), confidence=high.
        """
        prompt = (
            f"PROPOSAL: {proposal}\n\n"
            "As the Skeptic Entity, rate the FLAW PROBABILITY (0=no flaws, 1=severely flawed).\n"
            "Return JSON: {\"flaw_probability\": float, \"top_flaw\": str, \"confidence\": float}"
        )
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
                json={"model": GROQ_MODEL, "response_format": {"type": "json_object"},
                      "messages": [{"role": "user", "content": prompt}]},
            )
        data = json.loads(r.json()["choices"][0]["message"]["content"])
        flaw_prob  = data.get("flaw_probability", 0.5)
        confidence = data.get("confidence",       0.5)
        return {
            "vote":       1.0 - flaw_prob,  # invert: high flaw → low vote
            "confidence": confidence,
            "reasoning":  data.get("top_flaw", ""),
        }
