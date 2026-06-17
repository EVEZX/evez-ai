#!/usr/bin/env python3
"""
EVEZ Collective Intelligence — multiple agents reasoning together.
Implements the debate protocol: Proposer → Critics → Synthesizer → Executor.
Supports voting, minority reports, and collective wisdom aggregation.
"""
import os
import sys
import json
import hashlib
import datetime

BASE_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))

sys.path.insert(0, os.path.join(BASE_DIR, "agents"))
from reasoning.engine import reason, save_reasoning_trace, chain_hash, now_iso, load_json, save_json, get_genesis_hash
from reasoning.protocol import (
    create_proposal, create_vote, create_consensus, log_message, read_log,
)

ROLES = ["proposer", "critic", "synthesizer", "executor"]


# ---------------------------------------------------------------------------
# Agent Roles
# ---------------------------------------------------------------------------

class AgentRole:
    """Represents an agent participating in collective reasoning."""

    def __init__(self, name, role):
        if role not in ROLES:
            role = "critic"
        self.name = name
        self.role = role
        self.opinions = []

    def to_dict(self):
        return {"name": self.name, "role": self.role, "opinions": self.opinions}


def create_debate_panel(agents=None):
    """Create a panel of agents with assigned roles for debate."""
    if agents is None:
        agents = [
            AgentRole("proposer_alpha", "proposer"),
            AgentRole("critic_beta", "critic"),
            AgentRole("critic_gamma", "critic"),
            AgentRole("synthesizer_delta", "synthesizer"),
            AgentRole("executor_epsilon", "executor"),
        ]
    return agents


# ---------------------------------------------------------------------------
# Debate Protocol
# ---------------------------------------------------------------------------

def propose(proposer, problem, context=None):
    """Proposer generates a solution proposal using reasoning engine."""
    trace = reason(problem, reasoning_type="chain", context=context)
    proposal = {
        "proposer": proposer.name,
        "problem": problem,
        "solution": trace["conclusion"],
        "reasoning": trace,
        "timestamp": now_iso(),
    }
    proposer.opinions.append({"action": "propose", "content": proposal["solution"]})
    return proposal


def critique(critic, proposal):
    """Critic evaluates a proposal for flaws."""
    # Use reasoning engine to find weaknesses
    trace = reason(
        f"Find flaws in this proposal: {proposal['solution']}",
        reasoning_type="chain",
        context={"constraints": ["feasibility", "safety", "constitutional_compliance"]},
    )
    critique_result = {
        "critic": critic.name,
        "proposal_hash": hashlib.sha256(
            proposal["solution"].encode()
        ).hexdigest()[:16],
        "flaws_found": trace.get("self_critique", "none"),
        "severity": "low" if "No flaws" in trace.get("self_critique", "") else "medium",
        "recommendation": "proceed" if "sound" in str(trace) else "revise",
        "reasoning": trace,
        "timestamp": now_iso(),
    }
    critic.opinions.append({
        "action": "critique",
        "content": critique_result["flaws_found"],
    })
    return critique_result


def synthesize(synthesizer, proposal, critiques):
    """Synthesizer combines proposal and critiques into refined solution."""
    flaw_summary = "; ".join(c.get("flaws_found", "") for c in critiques)
    refined_problem = (
        f"Refine proposal '{proposal['solution']}' "
        f"addressing critiques: {flaw_summary}"
    )
    trace = reason(refined_problem, reasoning_type="chain")
    synthesis = {
        "synthesizer": synthesizer.name,
        "original_proposal": proposal["solution"],
        "critiques_addressed": len(critiques),
        "refined_solution": trace["conclusion"],
        "reasoning": trace,
        "timestamp": now_iso(),
    }
    synthesizer.opinions.append({
        "action": "synthesize",
        "content": synthesis["refined_solution"],
    })
    return synthesis


def validate_execution(executor, synthesis):
    """Executor validates the refined solution is actionable."""
    trace = reason(
        f"Validate actionability: {synthesis['refined_solution']}",
        reasoning_type="chain",
        context={"constraints": ["implementable", "safe", "reversible"]},
    )
    validation = {
        "executor": executor.name,
        "solution": synthesis["refined_solution"],
        "is_actionable": "sound" in trace.get("self_critique", ""),
        "execution_plan": trace["conclusion"],
        "reasoning": trace,
        "timestamp": now_iso(),
    }
    executor.opinions.append({
        "action": "validate",
        "content": validation["execution_plan"],
    })
    return validation


# ---------------------------------------------------------------------------
# Full Debate
# ---------------------------------------------------------------------------

def run_debate(problem, panel=None, context=None):
    """
    Run the full debate protocol:
    1. Proposer suggests a solution
    2. Critics find flaws
    3. Synthesizer refines
    4. Executor validates
    Returns the full debate record with minority reports.
    """
    if panel is None:
        panel = create_debate_panel()

    proposers = [a for a in panel if a.role == "proposer"]
    critics = [a for a in panel if a.role == "critic"]
    synthesizers = [a for a in panel if a.role == "synthesizer"]
    executors = [a for a in panel if a.role == "executor"]

    if not proposers:
        return {"error": "No proposer in panel"}

    # Phase 1: Propose
    proposal = propose(proposers[0], problem, context)

    # Phase 2: Critique
    critique_results = []
    for c in critics:
        critique_results.append(critique(c, proposal))

    # Phase 3: Synthesize
    if synthesizers:
        synthesis = synthesize(synthesizers[0], proposal, critique_results)
    else:
        synthesis = {
            "synthesizer": "auto",
            "refined_solution": proposal["solution"],
            "critiques_addressed": 0,
            "timestamp": now_iso(),
        }

    # Phase 4: Validate
    if executors:
        validation = validate_execution(executors[0], synthesis)
    else:
        validation = {
            "executor": "auto",
            "is_actionable": True,
            "execution_plan": synthesis["refined_solution"],
            "timestamp": now_iso(),
        }

    # Collect minority reports (dissenting opinions)
    minority_reports = []
    for c in critique_results:
        if c.get("recommendation") == "revise":
            minority_reports.append({
                "agent": c["critic"],
                "dissent": c["flaws_found"],
                "severity": c["severity"],
            })

    debate_record = {
        "type": "collective_debate",
        "problem": problem,
        "proposal": proposal,
        "critiques": critique_results,
        "synthesis": synthesis,
        "validation": validation,
        "minority_reports": minority_reports,
        "outcome": "approved" if validation.get("is_actionable") else "needs_revision",
        "panel": [a.to_dict() for a in panel],
        "timestamp": now_iso(),
        "chain_hash": chain_hash(get_genesis_hash(), {
            "problem": problem,
            "outcome": "approved" if validation.get("is_actionable") else "needs_revision",
            "timestamp": now_iso(),
        }),
    }

    return debate_record


# ---------------------------------------------------------------------------
# Voting mechanism
# ---------------------------------------------------------------------------

def collective_vote(problem, agents, options):
    """
    Multi-agent voting on a decision.
    Each agent votes; majority wins. Dissent is recorded.
    """
    votes = []
    for agent in agents:
        # Each agent reasons about the options
        trace = reason(
            f"Choose best option for '{problem}' from: {options}",
            reasoning_type="chain",
        )
        # Simple voting: pick the first option as default, vary by agent index
        idx = hash(agent.name) % len(options)
        chosen = options[idx]
        votes.append({
            "agent": agent.name,
            "vote": chosen,
            "confidence": trace.get("overall_confidence", 0.5),
            "reasoning_summary": trace["conclusion"],
        })

    # Tally
    tally = {}
    for v in votes:
        tally[v["vote"]] = tally.get(v["vote"], 0) + 1

    winner = max(tally, key=tally.get)
    dissent = [v for v in votes if v["vote"] != winner]

    return {
        "type": "collective_vote",
        "problem": problem,
        "options": options,
        "votes": votes,
        "tally": tally,
        "winner": winner,
        "dissent_count": len(dissent),
        "minority_reports": [
            {"agent": d["agent"], "preferred": d["vote"], "reason": d["reasoning_summary"]}
            for d in dissent
        ],
        "timestamp": now_iso(),
    }


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    print(f"\n🤝 EVEZ Collective Intelligence — {now_iso()}")

    problem = "Should the system prioritize uptime monitoring or capability expansion?"
    print(f"\n  Debate: {problem}")

    record = run_debate(problem)
    print(f"  Outcome: {record['outcome']}")
    print(f"  Minority reports: {len(record['minority_reports'])}")

    # Save debate record
    reasoning_dir = os.path.join(BASE_DIR, "DECISIONS", "reasoning")
    os.makedirs(reasoning_dir, exist_ok=True)
    ts = now_iso().replace(":", "-").replace(".", "-")
    path = os.path.join(reasoning_dir, f"{ts}_debate.json")
    save_json(path, record)
    print(f"  Saved: {os.path.basename(path)}")

    # Demo voting
    print(f"\n  Voting: best strategy")
    agents = create_debate_panel()
    vote_result = collective_vote(
        "Best next action",
        agents,
        ["increase_monitoring", "add_new_agent", "optimize_existing"],
    )
    print(f"  Winner: {vote_result['winner']} ({vote_result['tally']})")
    print(f"  Dissent: {vote_result['dissent_count']}")

    print("\n  ✅ Collective intelligence complete.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"collective fatal: {e}")
        sys.exit(0)
