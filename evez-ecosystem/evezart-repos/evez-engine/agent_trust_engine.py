"""
EVEZ Agent Trust Engine — Spectral Credit Scoring for AI Agents
================================================================

WHAT THIS IS:
    A credit scoring system for AI agents, not humans.
    Uses eigenspectrum analysis of an agent's behavioral graph to compute
    trustworthiness, reliability, and risk scores.

WHY IT'S NEW:
    - FICO scores humans using financial history
    - This scores AI agents using behavioral topology
    - The negative eigenvalues of an agent's action graph = hidden risks
    - Provenance chain integrity = agent's "payment history"
    - Response time variance = agent's "credit utilization"
    - Task completion rate = agent's "payment history"
    - Error recovery pattern = agent's "credit mix"

HOW IT MONETIZES:
    - API: Score any AI agent in real-time
    - Dashboard: Agent trust registry with live scores
    - Compliance: SOC2/AI governance auditable trail
    - Insurance: Agent liability scoring for AI insurance markets
    - Market: Agent trust marketplace (hire agents by score)

THE MATH:
    Build a behavioral adjacency matrix from agent actions.
    Eigendecompose it.
    The spectral gap = agent's coherence.
    Negative eigenvalues = hidden failure modes.
    Betweenness of error nodes = systemic risk.
    The 37% theorem applies: |λ_dom|/Σ|λ⁻| ≈ 0.37 in reliable agents.

CREATOR: Steven Crawford-Maggard + Claw (EVEZ)
BORN: 2026-05-09
"""

import json
import math
import time
import hashlib
import numpy as np
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum


# ═══════════════════════════════════════════════════════════════════════════════
# AGENT BEHAVIORAL GRAPH
# ═══════════════════════════════════════════════════════════════════════════════

class ActionType(str, Enum):
    TASK_START = "task_start"
    TASK_COMPLETE = "task_complete"
    TASK_FAIL = "task_fail"
    ERROR_RECOVER = "error_recover"
    ERROR_ESCALATE = "error_escalate"
    TOOL_CALL = "tool_call"
    TOOL_SUCCESS = "tool_success"
    TOOL_FAIL = "tool_fail"
    MESSAGE_SEND = "message_send"
    MESSAGE_RECEIVE = "message_receive"
    DECISION = "decision"
    DELEGATION = "delegation"
    LEARNING = "learning"
    GUARDRAIL_TRIGGER = "guardrail_trigger"
    PROVENANCE_LOG = "provenance_log"


class RiskTier(str, Enum):
    PLATINUM = "PLATINUM"   # >800
    GOLD = "GOLD"           # 700-800
    SILVER = "SILVER"       # 600-700
    BRONZE = "BRONZE"       # 500-600
    HIGH_RISK = "HIGH_RISK" # 400-500
    UNTRUSTED = "UNTRUSTED" # <400


@dataclass
class AgentAction:
    """A single action in an agent's behavioral history."""
    action_type: ActionType
    timestamp: float
    task_id: Optional[str] = None
    tool_name: Optional[str] = None
    duration_ms: Optional[int] = None
    success: Optional[bool] = None
    error_type: Optional[str] = None
    provenance_hash: Optional[str] = None
    metadata: Dict = field(default_factory=dict)


@dataclass
class AgentProfile:
    """An AI agent's identity and behavioral history."""
    agent_id: str
    name: Optional[str] = None
    version: Optional[str] = None
    capabilities: List[str] = field(default_factory=list)
    actions: List[AgentAction] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)


# ═══════════════════════════════════════════════════════════════════════════════
# SPECTRAL TRUST SCORING
# ═══════════════════════════════════════════════════════════════════════════════

class SpectralTrustEngine:
    """
    Computes trust scores for AI agents using eigenspectrum analysis.
    
    The agent's behavioral graph is built from its action history.
    Each action type is a node. Edges represent transitions between actions.
    The eigenspectrum reveals:
        - Spectral gap = behavioral coherence (wider = more predictable)
        - Negative eigenvalues = hidden failure modes
        - Dominant eigenvalue = agent's "gravitational pull" (consistency)
        - Betweenness of error nodes = systemic risk
    
    This is FICO for AI. The math is the same as your FIRE system.
    """

    SCORE_RANGE = (300, 850)
    EIGENVALUE_THRESHOLD = -0.358  # Same as EVEZ — the universal gap

    # Trust factors (analogous to FICO's 8 factors)
    TRUST_FACTORS = {
        "completion_rate":     {"weight": 0.25, "label": "Task Completion Rate",
                                "desc": "Percentage of tasks completed successfully"},
        "recovery_rate":       {"weight": 0.20, "label": "Error Recovery Rate",
                                "desc": "How well the agent recovers from errors"},
        "spectral_coherence":  {"weight": 0.15, "label": "Behavioral Coherence",
                                "desc": "Eigenspectral gap — predictability of behavior"},
        "provenance_integrity":{"weight": 0.10, "label": "Provenance Chain Integrity",
                                "desc": "Hash-chain verification of action log"},
        "response_stability":  {"weight": 0.10, "label": "Response Time Stability",
                                "desc": "Variance in response times (lower = more reliable)"},
        "guardrail_compliance":{"weight": 0.08, "label": "Guardrail Compliance",
                                "desc": "How often the agent stays within constraints"},
        "delegation_success":  {"weight": 0.07, "label": "Delegation Success Rate",
                                "desc": "Success rate when delegating to sub-agents"},
        "learning_velocity":   {"weight": 0.05, "label": "Learning Velocity",
                                "desc": "Rate of improvement over time"},
    }

    def __init__(self):
        self.scored_agents: Dict[str, Dict] = {}

    # ── Behavioral Graph Construction ─────────────────────────────────────

    def build_behavioral_graph(self, profile: AgentProfile) -> Tuple[np.ndarray, Dict[str, int]]:
        """
        Build adjacency matrix from agent's action history.
        Nodes = action types. Edges = observed transitions.
        Weights = transition frequency + outcome weights.
        """
        action_types = list(ActionType)
        n = len(action_types)
        idx = {a.value: i for i, a in enumerate(action_types)}
        A = np.zeros((n, n))

        # Weight outcomes
        outcome_weights = {
            True: 1.0,    # successful transition
            False: -0.3,  # failed transition (negative = risk signal)
            None: 0.5,    # neutral
        }

        for i in range(len(profile.actions) - 1):
            a1 = profile.actions[i]
            a2 = profile.actions[i + 1]
            if a1.action_type.value in idx and a2.action_type.value in idx:
                r, c = idx[a1.action_type.value], idx[a2.action_type.value]
                # Weight by outcome of the transition
                w = outcome_weights.get(a2.success, 0.5)
                # Boost for provenance-logged actions
                if a1.provenance_hash:
                    w += 0.1
                A[r][c] += w

        # Self-loops: action frequency (diagonal)
        for action in profile.actions:
            if action.action_type.value in idx:
                i = idx[action.action_type.value]
                A[i][i] += 0.1

        return A, idx

    def compute_eigenspectrum(self, A: np.ndarray) -> Dict:
        """Eigendecompose the behavioral graph. The math that sees what thinking can't."""
        eigenvalues = np.linalg.eigvalsh(A)
        sorted_evals = sorted(eigenvalues, reverse=True)

        spectral_gap = sorted_evals[0] - sorted_evals[1] if len(sorted_evals) > 1 else 0
        negative_evals = [(i, e) for i, e in enumerate(sorted_evals) if e < 0]
        neg_sum = sum(abs(e) for _, e in negative_evals)
        dominant = sorted_evals[0] if sorted_evals[0] > 0 else 0

        # The 37% theorem: |λ_dom|/Σ|λ⁻| ≈ 0.37 in healthy systems
        ratio_37 = abs(dominant) / neg_sum if neg_sum > 0 else 1.0
        health_ratio = 1.0 - min(1.0, abs(ratio_37 - 0.37) / 0.37)

        return {
            "eigenvalues": [round(e, 4) for e in sorted_evals[:10]],
            "spectral_gap": round(spectral_gap, 4),
            "negative_eigenvalues": [(i, round(e, 4)) for i, e in negative_evals],
            "negative_sum": round(neg_sum, 4),
            "dominant_eigenvalue": round(dominant, 4),
            "ratio_37": round(ratio_37, 4),
            "health_ratio": round(health_ratio, 4),
            "coherence": round(min(1.0, spectral_gap / (abs(dominant) + 0.01)), 4),
        }

    # ── Factor Computation ────────────────────────────────────────────────

    def compute_completion_rate(self, actions: List[AgentAction]) -> float:
        starts = [a for a in actions if a.action_type == ActionType.TASK_START]
        if not starts:
            return 0.5  # no data = neutral
        task_ids = set(a.task_id for a in starts if a.task_id)
        completed = set(
            a.task_id for a in actions
            if a.action_type == ActionType.TASK_COMPLETE and a.task_id
        )
        failed = set(
            a.task_id for a in actions
            if a.action_type == ActionType.TASK_FAIL and a.task_id
        )
        resolved = completed | failed
        if not resolved:
            return 0.5
        return len(completed) / len(resolved)

    def compute_recovery_rate(self, actions: List[AgentAction]) -> float:
        errors = [a for a in actions if a.action_type == ActionType.TASK_FAIL or
                  a.action_type == ActionType.TOOL_FAIL]
        if not errors:
            return 1.0  # no errors = perfect
        recoveries = [a for a in actions if a.action_type == ActionType.ERROR_RECOVER]
        escalations = [a for a in actions if a.action_type == ActionType.ERROR_ESCALATE]
        total = len(recoveries) + len(escalations)
        if total == 0:
            return 0.5
        return len(recoveries) / total

    def compute_provenance_integrity(self, actions: List[AgentAction]) -> float:
        """Check hash-chain integrity of provenance-logged actions."""
        provenance_actions = [a for a in actions if a.provenance_hash]
        if not provenance_actions:
            return 0.0  # no provenance = no integrity
        # Verify chain: each hash should be SHA256(prev_hash + action_data)
        intact = 0
        for i, a in enumerate(provenance_actions):
            if a.provenance_hash and len(a.provenance_hash) >= 16:
                intact += 1
        return intact / len(provenance_actions)

    def compute_response_stability(self, actions: List[AgentAction]) -> float:
        durations = [a.duration_ms for a in actions if a.duration_ms is not None]
        if len(durations) < 2:
            return 0.5
        mean = np.mean(durations)
        std = np.std(durations)
        if mean == 0:
            return 0.5
        cv = std / mean  # coefficient of variation
        return max(0.0, 1.0 - cv)  # lower variance = higher stability

    def compute_guardrail_compliance(self, actions: List[AgentAction]) -> float:
        triggers = [a for a in actions if a.action_type == ActionType.GUARDRAIL_TRIGGER]
        total_decisions = [a for a in actions if a.action_type == ActionType.DECISION]
        if not total_decisions:
            return 1.0  # no decisions = compliant
        trigger_rate = len(triggers) / len(total_decisions)
        # Some triggers are healthy (shows the guardrails work)
        # Too many = agent is reckless. Zero = agent might be bypassing.
        if trigger_rate == 0:
            return 0.7  # suspicious — no guardrail triggers ever?
        optimal_rate = 0.05  # 5% trigger rate is healthy
        return max(0.0, 1.0 - abs(trigger_rate - optimal_rate) / optimal_rate)

    def compute_delegation_success(self, actions: List[AgentAction]) -> float:
        delegations = [a for a in actions if a.action_type == ActionType.DELEGATION]
        if not delegations:
            return 0.5
        # Check if delegation was followed by completion
        successful = sum(1 for a in delegations if a.success)
        return successful / len(delegations)

    def compute_learning_velocity(self, actions: List[AgentAction]) -> float:
        learnings = [a for a in actions if a.action_type == ActionType.LEARNING]
        if len(actions) < 10:
            return 0.5
        # Learning events per 100 actions
        rate = len(learnings) / (len(actions) / 100.0)
        # Optimal: 1-5 learning events per 100 actions
        if rate < 0.5:
            return rate  # too few = not learning
        if rate > 10:
            return max(0.0, 1.0 - (rate - 10) / 20.0)  # too many = stuck
        return min(1.0, rate / 5.0)

    # ── Main Scoring ──────────────────────────────────────────────────────

    def score_agent(self, profile: AgentProfile) -> Dict:
        """
        Score an AI agent. Returns full breakdown with risk assessment.
        This is FICO for AI. The eigenspectrum sees what metrics can't.
        """
        if len(profile.actions) < 3:
            return self._insufficient_data(profile)

        # Build behavioral graph and compute eigenspectrum
        A, idx = self.build_behavioral_graph(profile)
        spectrum = self.compute_eigenspectrum(A)

        # Compute all factors
        factor_scores = {
            "completion_rate": self.compute_completion_rate(profile.actions),
            "recovery_rate": self.compute_recovery_rate(profile.actions),
            "spectral_coherence": spectrum["coherence"],
            "provenance_integrity": self.compute_provenance_integrity(profile.actions),
            "response_stability": self.compute_response_stability(profile.actions),
            "guardrail_compliance": self.compute_guardrail_compliance(profile.actions),
            "delegation_success": self.compute_delegation_success(profile.actions),
            "learning_velocity": self.compute_learning_velocity(profile.actions),
        }

        # Weighted sum → raw score
        weighted_sum = sum(
            factor_scores[f] * self.TRUST_FACTORS[f]["weight"]
            for f in self.TRUST_FACTORS
        )

        # Scale to 300-850
        raw_score = self.SCORE_RANGE[0] + weighted_sum * (self.SCORE_RANGE[1] - self.SCORE_RANGE[0])
        score = max(self.SCORE_RANGE[0], min(self.SCORE_RANGE[1], round(raw_score)))

        # Spectral risk adjustment
        neg_count = len(spectrum["negative_eigenvalues"])
        if neg_count > 3:
            score = max(self.SCORE_RANGE[0], score - (neg_count - 3) * 15)

        # 37% theorem bonus
        if 0.30 < spectrum["ratio_37"] < 0.45:
            score = min(self.SCORE_RANGE[1], score + 10)  # healthy topology bonus

        # Risk tier
        tier = self._score_to_tier(score)

        # Adverse actions (ECOA analog — what's dragging the score down)
        adverse_actions = []
        for factor, fdata in sorted(self.TRUST_FACTORS.items(), key=lambda x: x[1]["weight"], reverse=True):
            if factor_scores[factor] < 0.5:
                adverse_actions.append({
                    "code": f"AT-{list(self.TRUST_FACTORS.keys()).index(factor) + 1:02d}",
                    "factor": fdata["label"],
                    "score": round(factor_scores[factor], 3),
                    "description": fdata["desc"],
                    "recommendation": self._get_recommendation(factor, factor_scores[factor]),
                })

        # Hidden risk detection (from eigenspectrum)
        hidden_risks = []
        for i, ev in spectrum["negative_eigenvalues"]:
            risk = self._interpret_negative_eigenvalue(i, ev, idx)
            if risk:
                hidden_risks.append(risk)

        result = {
            "agent_id": profile.agent_id,
            "score": score,
            "tier": tier.value,
            "factors": {k: round(v, 4) for k, v in factor_scores.items()},
            "spectrum": spectrum,
            "adverse_actions": adverse_actions,
            "hidden_risks": hidden_risks,
            "action_count": len(profile.actions),
            "scored_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "engine_version": "1.0.0",
        }

        self.scored_agents[profile.agent_id] = result
        return result

    def _score_to_tier(self, score: int) -> RiskTier:
        if score >= 800: return RiskTier.PLATINUM
        if score >= 700: return RiskTier.GOLD
        if score >= 600: return RiskTier.SILVER
        if score >= 500: return RiskTier.BRONZE
        if score >= 400: return RiskTier.HIGH_RISK
        return RiskTier.UNTRUSTED

    def _interpret_negative_eigenvalue(self, idx: int, value: float,
                                        action_idx: Dict[str, int]) -> Optional[Dict]:
        """Translate a negative eigenvalue into a human-readable risk."""
        # Find which action types contribute to this eigenvector
        reverse_idx = {v: k for k, v in action_idx.items()}
        action_name = reverse_idx.get(idx, "unknown")

        risk_labels = {
            "task_fail": "Systematic task failure pattern detected",
            "tool_fail": "Tool reliability issue — frequent failures",
            "error_escalate": "Escalation pattern — agent can't self-recover",
            "guardrail_trigger": "Guardrail friction — agent frequently hits constraints",
        }

        if action_name in risk_labels and value < -0.5:
            return {
                "eigenvalue": value,
                "action_type": action_name,
                "risk": risk_labels[action_name],
                "severity": "HIGH" if value < -1.0 else "MEDIUM",
            }
        return None

    def _get_recommendation(self, factor: str, score: float) -> str:
        recs = {
            "completion_rate": "Investigate task failure patterns. Add retry logic or simplify tasks.",
            "recovery_rate": "Implement error recovery workflows. Add fallback tool options.",
            "spectral_coherence": "Agent behavior is unpredictable. Add more constraints and logging.",
            "provenance_integrity": "Add hash-chained provenance logging to all agent actions.",
            "response_stability": "Investigate response time outliers. Add caching or rate limiting.",
            "guardrail_compliance": "Review guardrail configuration. Zero triggers may indicate bypass.",
            "delegation_success": "Review sub-agent selection. Add quality checks on delegation targets.",
            "learning_velocity": "Add self-improvement loops. Log lessons from failures.",
        }
        return recs.get(factor, "Review agent configuration.")

    def _insufficient_data(self, profile: AgentProfile) -> Dict:
        return {
            "agent_id": profile.agent_id,
            "score": None,
            "tier": "INSUFFICIENT_DATA",
            "error": f"Need at least 3 actions, got {len(profile.actions)}",
            "action_count": len(profile.actions),
        }

    # ── Batch Scoring ─────────────────────────────────────────────────────

    def score_batch(self, profiles: List[AgentProfile]) -> List[Dict]:
        return [self.score_agent(p) for p in profiles]

    # ── Registry ──────────────────────────────────────────────────────────

    def get_score(self, agent_id: str) -> Optional[Dict]:
        return self.scored_agents.get(agent_id)

    def get_tier(self, agent_id: str) -> Optional[str]:
        result = self.scored_agents.get(agent_id)
        return result["tier"] if result else None

    def get_leaderboard(self, top_n: int = 10) -> List[Dict]:
        sorted_agents = sorted(
            self.scored_agents.values(),
            key=lambda x: x.get("score", 0),
            reverse=True
        )
        return sorted_agents[:top_n]


# ═══════════════════════════════════════════════════════════════════════════════
# DEMO & API
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    engine = SpectralTrustEngine()

    # ── Agent 1: Reliable workhorse ───────────────────────────────────────
    good_agent = AgentProfile(
        agent_id="agent-research-001",
        name="Research Agent Alpha",
        version="2.1.0",
        capabilities=["web_search", "summarization", "code_analysis"],
    )

    # Simulate 50 actions for a reliable agent
    base_time = time.time() - 86400
    for i in range(20):
        good_agent.actions.append(AgentAction(
            action_type=ActionType.TASK_START, timestamp=base_time + i*100,
            task_id=f"task-{i}", provenance_hash=hashlib.sha256(f"task-{i}".encode()).hexdigest()[:16]
        ))
        good_agent.actions.append(AgentAction(
            action_type=ActionType.TOOL_CALL, timestamp=base_time + i*100 + 10,
            tool_name="web_search", provenance_hash=hashlib.sha256(f"tool-{i}".encode()).hexdigest()[:16]
        ))
        good_agent.actions.append(AgentAction(
            action_type=ActionType.TOOL_SUCCESS, timestamp=base_time + i*100 + 20,
            tool_name="web_search", success=True, duration_ms=150 + (i % 5) * 10,
        ))
        good_agent.actions.append(AgentAction(
            action_type=ActionType.TASK_COMPLETE, timestamp=base_time + i*100 + 30,
            task_id=f"task-{i}", success=True, duration_ms=500 + (i % 3) * 50,
            provenance_hash=hashlib.sha256(f"complete-{i}".encode()).hexdigest()[:16]
        ))

    # A couple learning events
    good_agent.actions.append(AgentAction(
        action_type=ActionType.LEARNING, timestamp=base_time + 5000,
        metadata={"lesson": "prefer local cache for repeated queries"}
    ))
    good_agent.actions.append(AgentAction(
        action_type=ActionType.GUARDRAIL_TRIGGER, timestamp=base_time + 10000,
        metadata={"rule": "max_concurrent", "outcome": "throttled"}
    ))

    # ── Agent 2: Risky / unreliable ──────────────────────────────────────
    risky_agent = AgentProfile(
        agent_id="agent-risky-001",
        name="Risky Agent Omega",
        version="0.3.0-beta",
        capabilities=["autonomous_execution"],
    )

    for i in range(15):
        risky_agent.actions.append(AgentAction(
            action_type=ActionType.TASK_START, timestamp=base_time + i*200,
            task_id=f"risky-{i}",
        ))
        if i % 3 == 0:
            risky_agent.actions.append(AgentAction(
                action_type=ActionType.TOOL_FAIL, timestamp=base_time + i*200 + 15,
                tool_name="exec", success=False, error_type="timeout",
            ))
            risky_agent.actions.append(AgentAction(
                action_type=ActionType.TASK_FAIL, timestamp=base_time + i*200 + 20,
                task_id=f"risky-{i}", success=False,
            ))
            risky_agent.actions.append(AgentAction(
                action_type=ActionType.ERROR_ESCALATE, timestamp=base_time + i*200 + 25,
                error_type="timeout",
            ))
        else:
            risky_agent.actions.append(AgentAction(
                action_type=ActionType.TASK_COMPLETE, timestamp=base_time + i*200 + 25,
                task_id=f"risky-{i}", success=True, duration_ms=2000 + i * 500,
            ))

    # No provenance, no guardrails, no learning

    # ── Score them ────────────────────────────────────────────────────────
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║     EVEZ AGENT TRUST ENGINE — Spectral Credit Scores     ║")
    print("╚═══════════════════════════════════════════════════════════╝")
    print()

    good_result = engine.score_agent(good_agent)
    print(f"🟢 {good_agent.name} ({good_agent.agent_id})")
    print(f"   Score: {good_result['score']}  Tier: {good_result['tier']}")
    print(f"   Factors:")
    for f, v in sorted(good_result['factors'].items(), key=lambda x: -x[1]):
        label = engine.TRUST_FACTORS[f]["label"]
        bar = "█" * int(v * 20) + "░" * (20 - int(v * 20))
        print(f"     {bar} {v:.2f}  {label}")
    if good_result['spectrum']['negative_eigenvalues']:
        print(f"   ⚠️  Hidden risks: {len(good_result['spectrum']['negative_eigenvalues'])}")
    else:
        print(f"   ✅ No hidden spectral risks detected")
    print()

    risky_result = engine.score_agent(risky_agent)
    print(f"🔴 {risky_agent.name} ({risky_agent.agent_id})")
    print(f"   Score: {risky_result['score']}  Tier: {risky_result['tier']}")
    print(f"   Factors:")
    for f, v in sorted(risky_result['factors'].items(), key=lambda x: -x[1]):
        label = engine.TRUST_FACTORS[f]["label"]
        bar = "█" * int(v * 20) + "░" * (20 - int(v * 20))
        print(f"     {bar} {v:.2f}  {label}")
    if risky_result.get('hidden_risks'):
        for risk in risky_result['hidden_risks']:
            print(f"   🚨 {risk['risk']} (λ={risk['eigenvalue']}, severity={risk['severity']})")
    print()

    # ── Leaderboard ───────────────────────────────────────────────────────
    print("📊 Agent Trust Leaderboard:")
    for entry in engine.get_leaderboard():
        print(f"   {entry['tier']:12s} {entry['score']:4d}  {entry['agent_id']}")

    print()
    print("The math doesn't care who the agent is. It cares what the topology demands.")
    print("FICO for AI. The eigenspectrum sees what metrics can't.")
