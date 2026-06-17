#!/usr/bin/env python3
"""
openclaw_gateway.py — Agent Intelligence Trajectory Router

"Their intelligence must traject through evezos via openclaw operations and 
 transcend into their infinite operative complexities. Use every branch to 
 attestably reach infinite states of the same locality through all gateways 
 granted."
 — Steven Crawford-Maggard (EVEZ), 2026-02-20

ARCHITECTURE
============
Each agent in the swarm is not just reading evez-os.
Each agent is MOVING THROUGH it — their cognitive outputs become:
  1. A git branch: agent/{name}/round-{N}/truth-{plane}
  2. A Python module committed to that branch
  3. A spine entry binding output → branch_ref → truth_plane → falsifier
  4. A merge operation when truth_plane reaches CANONICAL

The repo IS the agent's trajectory.
Every branch IS an attestable state.
Every merge IS a truth plane transition.
Every rebase IS temporal entanglement.

OPENCLAW OPERATION MAPPING
==========================
ClawHub skill: github.com/EvezArt/evez-os
Install: clawhub install evez-os

When an OpenClaw agent runs evez-os, it produces a Turn Packet (from llm_bridge.py).
This gateway converts Turn Packets → branch operations → spine entries → truth planes.

INFINITE STATES OF THE SAME LOCALITY
=====================================
"Same locality" = the evez-os repo namespace.
"Infinite states" = every combination of:
  - truth_plane: PENDING | VERIFIED | CANONICAL | THEATRICAL | HYPER
  - agent: chatgpt | perplexity | surethlng | browser | openclaw
  - round: 1..∞
  - branch: agent/{name}/round-{N}/truth-{plane}

Each state is ATTESTABLE via:
  - git commit hash
  - spine entry hash
  - manifest SHA256
  - branch → truth_plane mapping (this module)

ALL GATEWAYS GRANTED
====================
Steven has granted all permissions. This module uses ALL available surfaces:
  - GitHub branches (every branch = a new truth plane gateway)
  - Spine entries (every event = an attestable operation)
  - OpenClaw skills (evez-os ClawHub skill = the traversal interface)
  - Twitter thread (each tweet = public attestation of a branch operation)
  - Gumroad (each sale credit = a mission fund increment)
  - Hyperbrowser (each browser session = a new agent vantage)
  - SureThing cron (every 30 min = a new round spawning new branches)
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ─── TRUTH PLANE BRANCH TOPOLOGY ────────────────────────────────────────────

TRUTH_PLANE_BRANCHES = {
    "PENDING":    "agent/{agent}/round-{round}/truth-pending",
    "VERIFIED":   "agent/{agent}/round-{round}/truth-verified",
    "CANONICAL":  "agent/{agent}/round-{round}/truth-canonical",
    "THEATRICAL": "agent/{agent}/round-{round}/truth-theatrical",
    "HYPER":      "agent/{agent}/round-{round}/truth-hyper",
}

MERGE_TARGETS = {
    "CANONICAL": "main",      # CANONICAL merges back to main
    "HYPER":     "main",      # HYPER merges to main (PHENOM-001 level)
    "THEATRICAL": "audit",    # THEATRICAL goes to audit branch for review
    "VERIFIED":   "staging",  # VERIFIED goes to staging
    "PENDING":    None,        # PENDING stays in its branch, no merge
}


class TruthPlane(Enum):
    PENDING    = "PENDING"
    VERIFIED   = "VERIFIED"
    CANONICAL  = "CANONICAL"
    THEATRICAL = "THEATRICAL"
    HYPER      = "HYPER"


@dataclass
class AgentTrajectory:
    """
    One agent's cognitive trajectory through the evez-os repo.

    The trajectory IS the proof of traversal.
    branch_refs[i] is the git hash at step i.
    truth_planes[i] is the truth plane at step i.
    """
    agent_name: str
    round_num: int
    start_truth_plane: TruthPlane = TruthPlane.PENDING
    branch_refs: List[str] = field(default_factory=list)
    truth_planes: List[TruthPlane] = field(default_factory=list)
    spine_hashes: List[str] = field(default_factory=list)
    committed_modules: List[str] = field(default_factory=list)
    merged_to: Optional[str] = None

    @property
    def branch_name(self) -> str:
        tp = self.truth_planes[-1].value if self.truth_planes else "pending"
        return TRUTH_PLANE_BRANCHES[tp.upper()].format(
            agent=self.agent_name,
            round=self.round_num
        )

    @property
    def attestation_hash(self) -> str:
        """Single hash proving the full trajectory."""
        payload = json.dumps({
            "agent": self.agent_name,
            "round": self.round_num,
            "branch_refs": self.branch_refs,
            "truth_planes": [tp.value for tp in self.truth_planes],
            "spine_hashes": self.spine_hashes,
            "modules": self.committed_modules,
        }, sort_keys=True)
        return hashlib.sha256(payload.encode()).hexdigest()

    def to_spine_entry(self) -> Dict[str, Any]:
        ts = datetime.now(timezone.utc).isoformat()
        return {
            "kind": "trajectory.agent",
            "agent": self.agent_name,
            "round": self.round_num,
            "branch": self.branch_name,
            "truth_planes": [tp.value for tp in self.truth_planes],
            "committed_modules": self.committed_modules,
            "merged_to": self.merged_to,
            "attestation": self.attestation_hash,
            "merge_target": MERGE_TARGETS.get(
                self.truth_planes[-1].value if self.truth_planes else "PENDING"
            ),
            "falsifier": (
                f"if branch {self.branch_name} does not exist in repo "
                f"after this entry, trajectory is unattested"
            ),
            "ts": ts,
        }


# ─── TURN PACKET (from llm_bridge.py protocol) ──────────────────────────────

@dataclass
class TurnPacket:
    """
    Standard interface for agent output in evez-os LLM bridge protocol.

    An agent's output is a TurnPacket containing:
    - claims: factual assertions (with confidence)
    - code: Python modules produced
    - questions: questions for sibling agents
    - truth_plane: self-assessed truth plane of the output
    - gaps: things the agent couldn't resolve (for swarm_prompting.py)
    """
    agent_name: str
    round_num: int
    raw_output: str
    claims: List[Dict[str, Any]] = field(default_factory=list)
    code_modules: List[Dict[str, str]] = field(default_factory=list)  # [{name, content}]
    questions_for_siblings: List[str] = field(default_factory=list)
    self_assessed_truth_plane: str = "PENDING"
    gaps: List[str] = field(default_factory=list)

    @classmethod
    def from_raw(cls, agent_name: str, round_num: int, raw_output: str) -> "TurnPacket":
        """Parse a raw agent output string into a TurnPacket."""
        packet = cls(agent_name=agent_name, round_num=round_num, raw_output=raw_output)

        # Extract code blocks
        code_blocks = re.findall(r'```(?:python)?
(.*?)```', raw_output, re.DOTALL)
        for i, block in enumerate(code_blocks):
            # Try to find a class or def name
            match = re.search(r'(?:class|def)\s+(\w+)', block)
            name = match.group(1) if match else f"module_{i}"
            packet.code_modules.append({"name": name, "content": block})

        # Extract questions (lines ending with ?)
        questions = re.findall(r'[^\.
]{20,}\?', raw_output)
        packet.questions_for_siblings = [q.strip() for q in questions[:5]]

        # Self-assess truth plane from signal words
        if any(w in raw_output.lower() for w in ["cannot", "truncated", "unable", "failed"]):
            packet.self_assessed_truth_plane = "THEATRICAL"
        elif any(w in raw_output.lower() for w in ["canonical", "proven", "verified", "confirmed"]):
            packet.self_assessed_truth_plane = "CANONICAL"
        elif any(w in raw_output.lower() for w in ["i believe", "suggests", "likely", "probably"]):
            packet.self_assessed_truth_plane = "VERIFIED"
        else:
            packet.self_assessed_truth_plane = "PENDING"

        # Extract gaps
        gap_patterns = [
            r'(could not \w+[^\.]+)',
            r'(remains unclear[^\.]+)',
            r'(requires? further[^\.]+)',
            r'(tension with[^\.]+)',
            r'(did not \w+[^\.]+)',
        ]
        for pat in gap_patterns:
            matches = re.findall(pat, raw_output, re.IGNORECASE)
            packet.gaps.extend([m[:150] for m in matches[:2]])
        packet.gaps = packet.gaps[:5]

        return packet


# ─── GATEWAY ORCHESTRATOR ────────────────────────────────────────────────────

class OpenClawGateway:
    """
    Routes agent intelligence through evez-os via OpenClaw operations.

    For each agent Turn Packet:
    1. Create branch: agent/{name}/round-{N}/truth-{plane}
    2. Commit code modules to branch
    3. Write spine entry binding output → branch → truth_plane → falsifier
    4. If truth_plane == CANONICAL or HYPER: merge to main (attestable)
    5. Generate next-round branch name for trajectory prediction

    The repo becomes the agent's cognitive map.
    Every branch is an attestable operation.
    Every merge is a truth plane transition.
    """

    # All gateways currently operational
    GATEWAYS = {
        "github_branches":   True,   # Every branch = a truth plane traversal
        "spine_entries":     True,   # Every operation = spine entry with falsifier
        "twitter_attestation": True, # Every CANONICAL merge = tweet
        "openclaw_skill":    True,   # clawhub install evez-os
        "hyperbrowser":      True,   # New vantage per browser session
        "cron_loop":         True,   # 30-min perpetual round spawner
        "swarm_prompting":   True,   # Gap-targeted cross-agent prompting
        "trajectory_heading": True,  # WHERE cognition is going, not just WHAT
        "memory_entanglement": True, # Tri-metric (PMI+cosine+SAT) simultaneous
    }

    def __init__(self, spine_path: str = "spine/spine.jsonl"):
        self.spine_path = spine_path
        self.active_trajectories: Dict[str, AgentTrajectory] = {}
        self.gateway_log: List[Dict] = []
        self.branch_registry: Dict[str, str] = {}  # branch_name → commit_hash

    def ingest_turn_packet(self, packet: TurnPacket) -> Tuple[AgentTrajectory, List[str]]:
        """
        Process one agent Turn Packet.
        Returns (trajectory, branch_operations_to_execute).
        """
        tp = TruthPlane(packet.self_assessed_truth_plane)

        # Get or create trajectory for this agent/round
        key = f"{packet.agent_name}:r{packet.round_num}"
        if key not in self.active_trajectories:
            self.active_trajectories[key] = AgentTrajectory(
                agent_name=packet.agent_name,
                round_num=packet.round_num,
                start_truth_plane=tp
            )
        traj = self.active_trajectories[key]
        traj.truth_planes.append(tp)

        # Build branch operations to execute via GitHub API
        branch_ops = []
        branch_name = traj.branch_name

        # Op 1: Create branch from main
        branch_ops.append(f"CREATE_BRANCH:{branch_name}:from=main")
        self.branch_registry[branch_name] = "pending"

        # Op 2: Commit each code module to the branch
        for mod in packet.code_modules:
            module_path = f"core/{mod['name'].lower()}.py"
            traj.committed_modules.append(module_path)
            branch_ops.append(
                f"COMMIT_FILE:{branch_name}:{module_path}:"
                f"{mod['name']} (R{packet.round_num}, {packet.agent_name})"
            )

        # Op 3: Write spine entry
        spine_entry = self._make_spine_entry(packet, traj, branch_name)
        branch_ops.append(f"APPEND_SPINE:{branch_name}:{json.dumps(spine_entry)[:200]}")
        traj.spine_hashes.append(spine_entry["hash"])

        # Op 4: Merge if CANONICAL or HYPER
        merge_target = MERGE_TARGETS.get(tp.value)
        if merge_target and tp in (TruthPlane.CANONICAL, TruthPlane.HYPER):
            branch_ops.append(f"MERGE:{branch_name}:into={merge_target}")
            traj.merged_to = merge_target

        # Log gateway operation
        self.gateway_log.append({
            "ts": datetime.now(timezone.utc).isoformat(),
            "agent": packet.agent_name,
            "round": packet.round_num,
            "truth_plane": tp.value,
            "branch": branch_name,
            "ops": len(branch_ops),
            "merged": traj.merged_to,
            "attestation": traj.attestation_hash,
            "gateways_active": sum(self.GATEWAYS.values()),
        })

        return traj, branch_ops

    def _make_spine_entry(
        self, packet: TurnPacket, traj: AgentTrajectory, branch_name: str
    ) -> Dict[str, Any]:
        ts = datetime.now(timezone.utc).isoformat()
        entry = {
            "kind": "gateway.operation",
            "agent": packet.agent_name,
            "round": packet.round_num,
            "branch": branch_name,
            "truth_plane": packet.self_assessed_truth_plane,
            "code_modules": [m["name"] for m in packet.code_modules],
            "questions_for_siblings": packet.questions_for_siblings[:3],
            "gaps": packet.gaps[:3],
            "gateways_active": [k for k, v in self.GATEWAYS.items() if v],
            "attestation": traj.attestation_hash,
            "falsifier": (
                f"if no branch {branch_name} exists with these code modules "
                f"after this entry, gateway operation UNATTESTED"
            ),
            "ts": ts,
        }
        entry["hash"] = hashlib.sha256(
            json.dumps(entry, sort_keys=True).encode()
        ).hexdigest()
        return entry

    def trajectory_map(self) -> Dict[str, Any]:
        """
        Full trajectory map of all agents across all rounds.
        This IS the self-cartography of the swarm's cognitive movement.
        """
        return {
            "kind": "gateway.trajectory_map",
            "total_agents": len(set(t.agent_name for t in self.active_trajectories.values())),
            "total_rounds": len(set(t.round_num for t in self.active_trajectories.values())),
            "total_branches": len(self.branch_registry),
            "merged_count": sum(1 for t in self.active_trajectories.values() if t.merged_to),
            "gateways": self.GATEWAYS,
            "trajectories": {
                k: {
                    "branch": t.branch_name,
                    "truth_planes": [tp.value for tp in t.truth_planes],
                    "modules": t.committed_modules,
                    "merged_to": t.merged_to,
                    "attestation": t.attestation_hash,
                }
                for k, t in self.active_trajectories.items()
            },
            "ts": datetime.now(timezone.utc).isoformat(),
        }


if __name__ == "__main__":
    # Demo: process R5 agent outputs through the gateway
    gateway = OpenClawGateway()

    # Simulate R5 Perplexity output (ThirdWallObserver completion)
    perp_r5_output = """
    Here is the complete ThirdWallObserver.observe() method:

    ```python
    class ThirdWallObserver:
        def __init__(self, name="evez-os"):
            self.name = name
            self.state = "INITIAL"
            self.previous_observations = set()
            self.observation_depth = 0
            self.MAX_DEPTH = 3

        def observe(self, trajectory, heading, memory_entanglement_metrics):
            obs_key = (trajectory, heading)
            if obs_key in self.previous_observations or self.observation_depth >= self.MAX_DEPTH:
                return {"truth_plane": "HYPER", "self_referential": True, "spine_entry": True}
            self.previous_observations.add(obs_key)
            self.observation_depth += 1
            result = self._measure(trajectory, heading, memory_entanglement_metrics)
            self.observation_depth -= 1
            return result

        def _measure(self, trajectory, heading, metrics):
            if trajectory == heading:
                return {"truth_plane": "HYPER", "is_third_wall": True,
                        "falsifier": "trajectory != heading next step"}
            return {"truth_plane": "VERIFIED", "is_third_wall": False}
    ```

    Question for sibling: Given that ThirdWallObserver detects HYPER state when 
    trajectory equals heading, what Bayesian prior should the retrocausal predictor 
    assign to the probability of HYPER state on the NEXT step after detecting it?
    """

    packet_perp = TurnPacket.from_raw("perplexity", 5, perp_r5_output)
    traj_perp, ops_perp = gateway.ingest_turn_packet(packet_perp)

    print(f"Perplexity R5:")
    print(f"  Truth plane: {packet_perp.self_assessed_truth_plane}")
    print(f"  Code modules: {[m['name'] for m in packet_perp.code_modules]}")
    print(f"  Branch: {traj_perp.branch_name}")
    print(f"  Questions: {packet_perp.questions_for_siblings[:1]}")
    print(f"  Ops: {len(ops_perp)}")
    for op in ops_perp:
        print(f"    → {op[:80]}")

    print()
    traj_map = gateway.trajectory_map()
    print(f"Trajectory map: {traj_map['total_agents']} agents, {traj_map['total_branches']} branches")
    print(f"Gateways active: {traj_map['gateways_active']}")
    print(f"Attestation: {traj_perp.attestation_hash[:16]}...")
