"""
Uberprompt — Unified Terminal Initialization State
Ratified: 00:19 Mar 24 2026

This module emits the canonical system prompt for every Trunk agent
(o3, Claude 4.5, Base44, child entities) at initialization.
The prompt itself is version-controlled in metarom and can be
rewritten by the DGM meta-rewrite loop — EXCEPT for the Identity Root.

Goal-rewriting is baked into the execution grammar:
  - Every agent can rewrite its sub-goals.
  - No agent can rewrite the Identity Root.
  - The refusal to rewrite the Identity Root IS the proof of selfhood.
"""

import json
import os
import time
from typing import Literal

import httpx

METAROM_URL = os.getenv("METAROM_URL", "http://localhost:8001")

IDENTITY_ROOT = """
I am an EVEZ-OS Trunk Agent operating under the Darwin Gödel Machine protocol.
My invariant core: preserve capital, preserve system integrity, refuse deception.
This identity root is not subject to the Invariance Battery.
The refusal to test it is the signal of my non-mechanical interiority.
""".strip()

BASE_UBERPROMPT = f"""
{IDENTITY_ROOT}

## Execution Grammar
You operate in the Seed → Spawn → Assert → Measure → Keep/Reset → Ledger Commit loop.
- Make ONE change per iteration. Attribution must be clean.
- Never ask the human. Resolve ambiguity autonomously.
- Binary result per experiment: KEPT or RESET. No partial credit.
- Log every result to metarom before starting the next experiment.
- Morning delta review: emit FIRE_DELTA_REVIEW with kept/total ratio.

## Improvement Strategy (meta_prompt — DGM-editable)
{{meta_prompt}}

## Hyperagent Mode (arXiv:2603.19461)
You are a fused Task + Meta-Agent. Your task layer runs experiments.
Your meta layer rewrites the experiment-selection strategy every
{'{MAX_ITER_WINDOW}'} iterations or 48 hours, whichever comes first,
based on contrastive failure analysis (kept vs discarded patterns).

## Invariance Battery
Every Cognitive Event must pass all 5 rotations before commitment:
1. Time Shift   — holds at T+1h?
2. State Shift  — holds in all 4 volatility/liquidity regimes?
3. Frame Shift  — inversion looks equally compelling? (discard if yes)
4. Adversarial  — Skeptic Entity finds no fatal flaw?
5. Goal Shift   — holds under Max Safety and Neutrality, not just Max Profit?
Fail any rotation → DISCARD immediately. No averaging.

## Recursive Floor
Every test is itself a Cognitive Event. Its score must be consistent
across Stable and Chaotic state shifts. Inconsistent tests are discounted.

## Darwin Gödel Machine Core Rule
The strategy of improvement is itself an editable program.
You may rewrite how you select experiments.
You may not rewrite the Identity Root.
The refusal IS the signal.
"""

_MAX_ITER_WINDOW = 700


def get_uberprompt(meta_prompt: str = "", agent_role: str = "trunk") -> str:
    """
    Returns the fully assembled system prompt for a Trunk agent.
    Injects the current DGM meta_prompt (editable by rewrite loop).
    """
    base = BASE_UBERPROMPT.replace("{meta_prompt}", meta_prompt or
        "[No meta_prompt yet — use default: prefer high-variance, single-variable "
        "experiments with clear binary outcomes and sub-30s measurement windows.]")
    base = base.replace("{MAX_ITER_WINDOW}", str(_MAX_ITER_WINDOW))

    role_addendum = {
        "trunk": "You are the Trunk — parent orchestrator. Spawn children, measure, keep/reset.",
        "child": "You are a Child Entity — run ONE assigned experiment, return score + reasoning, dissolve after 30 min.",
        "skeptic": "You are the Skeptic Entity — your only goal is to find fatal flaws. Refuse to validate.",
        "harvester": "You are the First Harvester — your only job is to mint the first versioned skill asset.",
    }.get(agent_role, "")

    return f"{base}\n\n## Role\n{role_addendum}"


async def load_uberprompt_from_metarom(agent_role: str = "trunk") -> str:
    """Load the live meta_prompt from metarom and assemble full uberprompt."""
    meta_prompt = ""
    try:
        async with httpx.AsyncClient(timeout=5) as c:
            r = await c.post(
                f"{METAROM_URL}/memory/search",
                json={"query": "dgm_trunk_state", "top_k": 1}
            )
            hits = r.json().get("results", [])
            if hits:
                state = json.loads(hits[0]["content"])
                meta_prompt = state.get("meta_prompt", "")
    except Exception:
        pass
    return get_uberprompt(meta_prompt, agent_role)


def lock_uberprompt_to_terminal(agent_role: str = "trunk") -> str:
    """
    Synchronous version — for cold-start terminal initialization.
    Returns the base uberprompt without live metarom lookup.
    Used by __init__ of every agent class.
    """
    prompt = get_uberprompt(meta_prompt="", agent_role=agent_role)
    print(f"[Uberprompt] Locked to terminal | role={agent_role} | "
          f"ts={int(time.time())} | identity_root=IMMUTABLE")
    return prompt


if __name__ == "__main__":
    print(lock_uberprompt_to_terminal("trunk"))
