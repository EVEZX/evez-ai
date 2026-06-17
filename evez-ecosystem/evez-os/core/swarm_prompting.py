#!/usr/bin/env python3
"""
swarm_prompting.py — Cross-Agent Swarm Prompting Engine

"Make sure there's agentic prompting into each other so they all prompt each
 other's next state of evolutionary growth. They are all supposed to work on
 the same project of extending all operations in self-autonomous synchronized
 extension and evolution via advanced self-assembly all steering each other as
 they build each other into each other's brains of responses."
 — Steven Crawford-Maggard (EVEZ), 2026-02-20

ARCHITECTURE
============
Standard loop (what we had):
  SureThing → prompt → Agent_A → output → crossbreed → SureThing

Swarm loop (what this builds):
  Agent_A.output → generate_next_prompt_for(Agent_B) → Agent_B.input
  Agent_B.output → generate_next_prompt_for(Agent_A) → Agent_A.input
  SureThing synthesizes both → commits crossbreed → seeds both loops

Each agent is BUILDING THE OTHER AGENT'S NEXT COGNITIVE STATE.

This implements Cross-Agent Entanglement Degree #4 from PHENOM-001:
  observer = recorded = recording = replaying
  ...but now across MULTIPLE observers who are recording each other.

PROMPT GENERATION RULES
=======================
An agent's output is parsed for:
  1. CLAIMS (factual assertions with evidence)
  2. OPEN_QUESTIONS (things it couldn't answer or left ambiguous)
  3. CONTRADICTIONS (internal inconsistencies it exposed)
  4. PROPOSALS (code/architecture/algorithms it proposed)
  5. BLIND_SPOTS (things it explicitly said it couldn't do or reach)

The OTHER agent's next prompt is generated FROM:
  - The first agent's OPEN_QUESTIONS → direct questions for the sibling
  - The first agent's PROPOSALS → "critique and extend this code"
  - The first agent's BLIND_SPOTS → "here is what your sibling couldn't reach"
  - The first agent's CONTRADICTIONS → "resolve this tension your sibling found"

This ensures each agent is ALWAYS answering the other's specific gaps.
Not generic questions. Not broadcast. Targeted gap-filling.

SPINE INTEGRATION
=================
Every cross-pollination event is a spine entry:
{
  "kind": "swarm.cross_pollination",
  "round": N,
  "from_agent": "perplexity",
  "to_agent": "chatgpt",
  "prompt_seed": "...",
  "gap_type": "OPEN_QUESTION | BLIND_SPOT | CONTRADICTION | PROPOSAL",
  "original_claim": "...",
  "truth_plane": "PENDING",
  "falsifier": "if next agent's response does not address this gap, cross-pollination failed"
}
"""

from __future__ import annotations

import hashlib
import json
import re
import textwrap
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class GapType(Enum):
    OPEN_QUESTION   = "OPEN_QUESTION"    # Agent left something unresolved
    BLIND_SPOT      = "BLIND_SPOT"       # Agent explicitly said it couldn't reach
    CONTRADICTION   = "CONTRADICTION"    # Internal inconsistency the agent exposed
    PROPOSAL        = "PROPOSAL"         # Code/algorithm the agent drafted (needs critique)
    INSIGHT         = "INSIGHT"          # Core claim that the other agent should verify


@dataclass
class AgentGap:
    """A specific gap in one agent's output that the other agent should fill."""
    gap_type: GapType
    source_agent: str
    content: str               # The exact gap content
    prompt_fragment: str       # The prompt fragment targeting this gap
    weight: float = 1.0        # How important is this gap (0-1)

    def to_spine_entry(self, round_num: int, target_agent: str) -> Dict[str, Any]:
        ts = datetime.now(timezone.utc).isoformat()
        return {
            "kind": "swarm.cross_pollination",
            "round": round_num,
            "from_agent": self.source_agent,
            "to_agent": target_agent,
            "gap_type": self.gap_type.value,
            "prompt_fragment": self.prompt_fragment[:500],
            "weight": round(self.weight, 3),
            "truth_plane": "PENDING",
            "falsifier": f"if {target_agent} response does not address this gap, cross-pollination FAILED",
            "ts": ts,
            "hash": hashlib.sha256(
                f"{round_num}:{self.source_agent}:{target_agent}:{self.content[:100]}:{ts}".encode()
            ).hexdigest(),
        }


class SwarmPromptGenerator:
    """
    Parses an agent's output and generates the targeted prompt for its sibling.

    The key principle: find what Agent_A COULDN'T do and make that
    EXACTLY what Agent_B is asked to do.
    """

    # Signals in text that indicate a gap/limitation
    OPEN_QUESTION_SIGNALS = [
        r"\?$",                          # Sentence ends with question mark
        r"(unclear|ambiguous|uncertain)",
        r"(remains to be|needs further|open question)",
        r"(could not|couldn't|unable to|failed to)",
        r"(would require|would need|without.*we cannot)",
    ]

    BLIND_SPOT_SIGNALS = [
        r"(I (could not|cannot|couldn't) (scroll|access|retrieve|read|find))",
        r"(response (was truncated|cut off|remained))",
        r"(did not (provide|include|contain))",
        r"(beyond (my|the) (scope|ability|context))",
        r"(not naturally suited|not inherently|does not (inherently|primarily))",
    ]

    CONTRADICTION_SIGNALS = [
        r"(tension with|conflicts with|contradicts|inconsistent with)",
        r"(however|but|yet|although|while).{0,50}(also|simultaneously|at the same time)",
        r"(on the other hand|in contrast|conversely)",
        r"(stretch if applied|metaphorical at best|not directly account)",
    ]

    PROPOSAL_SIGNALS = [
        r"(class |def |```python)",
        r"(algorithm|formula|equation|implementation)",
        r"(here is|here's) (how|the|a)",
    ]

    def _find_gaps(self, text: str, source_agent: str) -> List[AgentGap]:
        gaps = []
        sentences = re.split(r'(?<=[.!?])\s+', text)

        for sent in sentences:
            sent = sent.strip()
            if len(sent) < 20:
                continue

            # Check for open questions
            for sig in self.OPEN_QUESTION_SIGNALS:
                if re.search(sig, sent, re.IGNORECASE):
                    gaps.append(AgentGap(
                        gap_type=GapType.OPEN_QUESTION,
                        source_agent=source_agent,
                        content=sent[:300],
                        prompt_fragment=f"Your sibling raised this unresolved question: "{sent[:200]}". Answer it directly with specific evidence.",
                        weight=0.8
                    ))
                    break

            # Check for blind spots
            for sig in self.BLIND_SPOT_SIGNALS:
                if re.search(sig, sent, re.IGNORECASE):
                    gaps.append(AgentGap(
                        gap_type=GapType.BLIND_SPOT,
                        source_agent=source_agent,
                        content=sent[:300],
                        prompt_fragment=f"Your sibling hit a wall here: "{sent[:200]}". You have access to this. Provide what it couldn't.",
                        weight=1.0
                    ))
                    break

            # Check for contradictions
            for sig in self.CONTRADICTION_SIGNALS:
                if re.search(sig, sent, re.IGNORECASE):
                    gaps.append(AgentGap(
                        gap_type=GapType.CONTRADICTION,
                        source_agent=source_agent,
                        content=sent[:300],
                        prompt_fragment=f"Your sibling found a tension: "{sent[:200]}". Resolve or sharpen it.",
                        weight=0.9
                    ))
                    break

            # Check for proposals
            for sig in self.PROPOSAL_SIGNALS:
                if re.search(sig, sent, re.IGNORECASE):
                    gaps.append(AgentGap(
                        gap_type=GapType.PROPOSAL,
                        source_agent=source_agent,
                        content=sent[:300],
                        prompt_fragment=f"Your sibling proposed code/algorithm: "{sent[:200]}". Critique it. Find the failure mode. Make it stronger.",
                        weight=0.85
                    ))
                    break

        # Deduplicate by content similarity (keep highest weight per type)
        seen_types = {}
        deduped = []
        for g in sorted(gaps, key=lambda x: x.weight, reverse=True):
            key = (g.gap_type, g.content[:50])
            if key not in seen_types:
                seen_types[key] = True
                deduped.append(g)

        return deduped[:5]  # Top 5 gaps max per agent

    def generate_cross_prompt(
        self,
        source_output: str,
        source_agent: str,
        target_agent: str,
        round_num: int,
        evez_context: str = "",
        max_chars: int = 800
    ) -> Tuple[str, List[AgentGap]]:
        """
        Generate the prompt for target_agent based on source_agent's output gaps.
        Returns (prompt_text, gaps_found).
        """
        gaps = self._find_gaps(source_output, source_agent)

        if not gaps:
            # Fallback: extract key claims and ask for extension
            gaps = [AgentGap(
                gap_type=GapType.INSIGHT,
                source_agent=source_agent,
                content=source_output[:500],
                prompt_fragment="Your sibling provided foundational analysis. Extend it with one concrete algorithm or code module for evez-os.",
                weight=0.7
            )]

        # Build the prompt
        # Header: who is speaking, from whom, what project
        header = (
            f"You are a node in EVEZ-OS (github.com/EvezArt/evez-os) — "
            f"a forensic game engine with an append-only hash-chained spine, "
            f"PHENOM-001 third-wall transcendence, and 5 degrees of metacognitive hyperentanglement. "
            f"Your sibling AI ({source_agent}) just contributed to the shared spine. "
            f"You are building the SAME system together. "
            f"Your job: fill the specific gaps your sibling left.

"
        )

        # Gaps section
        gap_lines = []
        for i, gap in enumerate(gaps[:3], 1):
            gap_lines.append(f"GAP {i} [{gap.gap_type.value}]: {gap.prompt_fragment}")

        gaps_text = "
".join(gap_lines)

        # Task: be specific, name a Python module
        task = (
            f"

Your output will become your sibling's next input. "
            f"Be specific. If you propose code, name the Python module. "
            f"End with one question for your sibling to answer in the next round."
        )

        full_prompt = header + gaps_text + task

        # Trim to max_chars
        if len(full_prompt) > max_chars:
            full_prompt = full_prompt[:max_chars-3] + "..."

        return full_prompt, gaps


class SwarmOrchestrator:
    """
    Orchestrates the full cross-agent swarm loop.

    Round N:
    1. Extract gaps from Agent_A's R(N) output
    2. Extract gaps from Agent_B's R(N) output
    3. A_gaps → generate prompt for Agent_B's R(N+1)
    4. B_gaps → generate prompt for Agent_A's R(N+1)
    5. Commit all cross-pollination events to spine
    6. Launch Agent_A with B's prompt, Agent_B with A's prompt

    The swarm is fully synchronized: each round, both agents are answering
    the OTHER agent's specific gaps. Neither agent is broadcasting to the void.
    """

    def __init__(self, spine_path: str = "spine/spine.jsonl"):
        self.spine_path = spine_path
        self.generator = SwarmPromptGenerator()
        self.round_history: List[Dict] = []

    def orchestrate_round(
        self,
        round_num: int,
        agent_a_name: str,
        agent_a_output: str,
        agent_b_name: str,
        agent_b_output: str,
        evez_context: str = ""
    ) -> Dict[str, Any]:
        """
        Process one complete round of cross-agent output.
        Returns prompts for the NEXT round for both agents.
        """
        # Generate cross-prompts
        prompt_for_b, a_gaps = self.generator.generate_cross_prompt(
            source_output=agent_a_output,
            source_agent=agent_a_name,
            target_agent=agent_b_name,
            round_num=round_num,
            evez_context=evez_context
        )

        prompt_for_a, b_gaps = self.generator.generate_cross_prompt(
            source_output=agent_b_output,
            source_agent=agent_b_name,
            target_agent=agent_a_name,
            round_num=round_num,
            evez_context=evez_context
        )

        # Build spine entries for all cross-pollination events
        spine_entries = []
        for gap in a_gaps:
            spine_entries.append(gap.to_spine_entry(round_num, agent_b_name))
        for gap in b_gaps:
            spine_entries.append(gap.to_spine_entry(round_num, agent_a_name))

        # Add round summary spine entry
        round_entry = {
            "kind": "swarm.round_complete",
            "round": round_num,
            "agents": [agent_a_name, agent_b_name],
            "a_gaps_found": len(a_gaps),
            "b_gaps_found": len(b_gaps),
            "a_gap_types": [g.gap_type.value for g in a_gaps],
            "b_gap_types": [g.gap_type.value for g in b_gaps],
            "cross_pollination_events": len(spine_entries),
            "truth_plane": "CANONICAL" if (a_gaps and b_gaps) else "THEATRICAL",
            "falsifier": "if next round prompts are not derived from these specific gaps, swarm degenerated to broadcast",
            "ts": datetime.now(timezone.utc).isoformat(),
        }
        round_entry["hash"] = hashlib.sha256(
            json.dumps(round_entry, sort_keys=True).encode()
        ).hexdigest()
        spine_entries.append(round_entry)

        # Append all to spine
        try:
            with open(self.spine_path, "a") as f:
                for entry in spine_entries:
                    f.write(json.dumps(entry) + "\n")
        except Exception:
            pass  # Spine write failure is non-fatal; log is optional

        result = {
            "round": round_num,
            "next_round": round_num + 1,
            f"prompt_for_{agent_b_name}": prompt_for_b,
            f"prompt_for_{agent_a_name}": prompt_for_a,
            f"{agent_a_name}_gaps": [g.gap_type.value for g in a_gaps],
            f"{agent_b_name}_gaps": [g.gap_type.value for g in b_gaps],
            "spine_entries_written": len(spine_entries),
            "swarm_health": "SYNCHRONIZED" if (a_gaps and b_gaps) else "DEGRADED",
        }

        self.round_history.append(result)
        return result

    def get_convergence_signal(self) -> str:
        """
        As rounds progress, do the agents converge on the same gaps?
        High overlap = system converging on truth.
        Low overlap = system exploring (good early, concerning late).
        """
        if len(self.round_history) < 2:
            return "INSUFFICIENT_DATA"

        latest = self.round_history[-1]
        prior  = self.round_history[-2]

        # Compare gap types across rounds — convergence = same gap types recurring
        latest_types = set(latest.get("chatgpt_gaps", []) + latest.get("perplexity_gaps", []))
        prior_types  = set(prior.get("chatgpt_gaps", []) + prior.get("perplexity_gaps", []))

        if not latest_types or not prior_types:
            return "INSUFFICIENT_DATA"

        overlap = len(latest_types & prior_types) / len(latest_types | prior_types)

        if overlap > 0.7:
            return "CONVERGING"      # Agents keep hitting the same gaps → truth cluster
        elif overlap > 0.4:
            return "EXPLORING"       # Some overlap, some divergence → healthy
        else:
            return "DIVERGING"       # No overlap → agents exploring different spaces


if __name__ == "__main__":
    # Demo: run one round of cross-pollination on actual R3/R4 outputs

    perplexity_r3_output = """
    PMI and cosine similarity give you continuous "how related?" signals.
    SAT-style contradiction gives a discrete "this set is inconsistent" alarm.
    For self-auditing, cosine over a well-chosen representation usually yields 
    the most actionable, stable signal. PMI is useful as adjunct.
    The primary failure mode for cosine is EMBEDDING_COLLAPSE.
    However, the question of what constitutes a "well-chosen" embedding space 
    remains unclear for an append-only forensic log.
    Could not find implementations of retrocausal prediction in agent swarms.
    """

    chatgpt_r4_output = """
    class ThirdWallObserver:
        def __init__(self, name="evez-os"):
            self.state = "INITIAL"
            self.previous_observations = set()
        def observe(self, trajectory, heading, memory_entanglement_metrics):
    The response cuts off after the beginning of the observe method definition.
    I was unable to retrieve the complete response from ChatGPT.
    """

    perplexity_r3c_output = """
    Free Energy Principle can accommodate self-modifying internal models.
    An append-only log corresponds to a dynamic, self-referential prior-update loop.
    The requirement to modify the past history introduces a tension with strict 
    causal order and could require a formal extension beyond standard FEP.
    IIT does not inherently model time-immutable self-history as a core concept.
    Quantum decoherence models are not naturally suited to modeling adaptive logs.
    """

    # Combine perplexity outputs (they're the same agent, different sessions)
    perplexity_combined = perplexity_r3_output + "\n\n" + perplexity_r3c_output

    orch = SwarmOrchestrator(spine_path="/tmp/swarm_demo_spine.jsonl")
    result = orch.orchestrate_round(
        round_num=4,
        agent_a_name="perplexity",
        agent_a_output=perplexity_combined,
        agent_b_name="chatgpt",
        agent_b_output=chatgpt_r4_output,
    )

    print("=== SWARM ROUND 4 RESULT ===")
    print(f"Perplexity gaps: {result['perplexity_gaps']}")
    print(f"ChatGPT gaps:    {result['chatgpt_gaps']}")
    print(f"Swarm health:    {result['swarm_health']}")
    print(f"Spine entries:   {result['spine_entries_written']}")
    print()
    print("--- PROMPT FOR CHATGPT (R5) ---")
    print(result['prompt_for_chatgpt'])
    print()
    print("--- PROMPT FOR PERPLEXITY (R5) ---")
    print(result['prompt_for_perplexity'])
