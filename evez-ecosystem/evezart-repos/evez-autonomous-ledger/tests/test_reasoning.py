#!/usr/bin/env python3
"""
Tests for the EVEZ multi-agent reasoning system.
Covers: reasoning engine, communication protocol, collective intelligence,
and meta-learning strategy selection.
"""
import copy
import os
import sys
import json
import tempfile
import unittest

# Ensure agents package is importable
BASE_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "agents"))
sys.path.insert(0, BASE_DIR)

from agents.reasoning.engine import (
    chain_of_thought,
    tree_of_thought,
    self_critique,
    analogical_reasoning,
    counterfactual,
    reason,
    save_reasoning_trace,
    load_recent_traces,
    chain_hash,
)
from agents.reasoning.protocol import (
    create_message,
    create_query,
    create_response,
    create_proposal,
    create_vote,
    create_consensus,
    create_delegation,
    create_escalation,
    log_message,
    read_log,
    get_proposals,
    get_votes_for_proposal,
    resolve_proposal,
    detect_conflicts,
    MESSAGE_TYPES,
    PRIORITIES,
)
from agents.reasoning.collective import (
    AgentRole,
    create_debate_panel,
    propose,
    critique,
    synthesize,
    run_debate,
    collective_vote,
    ROLES,
)
from agents.reasoning.meta_learner import (
    load_meta_state,
    save_meta_state,
    record_outcome,
    select_strategy,
    categorize_problem,
    update_category_strategy,
    analyze_traces,
    generate_lesson,
    DEFAULT_STRATEGIES,
)


# ===================================================================
# Reasoning Engine Tests
# ===================================================================

class TestChainOfThought(unittest.TestCase):
    def test_basic_chain(self):
        result = chain_of_thought("How to improve uptime?")
        self.assertEqual(result["reasoning_type"], "chain")
        self.assertIn("steps", result)
        self.assertGreaterEqual(len(result["steps"]), 3)
        self.assertIn("conclusion", result)

    def test_chain_with_context(self):
        ctx = {"constraints": ["budget", "time"]}
        result = chain_of_thought("Optimize system", context=ctx)
        self.assertEqual(result["steps"][1]["phase"], "constraints")
        self.assertIn("budget", str(result["steps"][1]["thought"]))

    def test_chain_confidence(self):
        result = chain_of_thought("Test problem")
        for step in result["steps"]:
            self.assertGreaterEqual(step["confidence"], 0.0)
            self.assertLessEqual(step["confidence"], 1.0)
        self.assertIn("overall_confidence", result)


class TestTreeOfThought(unittest.TestCase):
    def test_basic_tree(self):
        result = tree_of_thought("Best expansion strategy?", branches=3)
        self.assertEqual(result["reasoning_type"], "tree")
        self.assertEqual(result["branches_explored"], 3)
        self.assertIn("best_branch", result)
        self.assertIn("best_score", result)

    def test_custom_branches(self):
        result = tree_of_thought("Problem", branches=5)
        self.assertEqual(result["branches_explored"], 5)
        self.assertEqual(len(result["paths"]), 5)

    def test_best_path_selection(self):
        result = tree_of_thought("Choose", branches=4)
        best_id = result["best_branch"]
        best_path = next(p for p in result["paths"] if p["branch_id"] == best_id)
        self.assertEqual(best_path["score"], result["best_score"])


class TestSelfCritique(unittest.TestCase):
    def test_sound_reasoning(self):
        trace = {
            "steps": [
                {"phase": "understand", "confidence": 0.9},
                {"phase": "constraints", "confidence": 0.85},
                {"phase": "approach", "confidence": 0.8},
                {"phase": "evaluate", "confidence": 0.8},
                {"phase": "conclude", "confidence": 0.8},
            ]
        }
        result = self_critique(trace)
        self.assertEqual(result["overall_assessment"], "sound")
        self.assertEqual(result["critique_count"], 0)

    def test_low_confidence_flagged(self):
        trace = {
            "steps": [
                {"phase": "understand", "confidence": 0.3},
                {"phase": "approach", "confidence": 0.2},
                {"phase": "evaluate", "confidence": 0.1},
            ]
        }
        result = self_critique(trace)
        self.assertIn("low_confidence", [c["flaw"] for c in result["critiques"]])

    def test_shallow_reasoning_flagged(self):
        trace = {"steps": [{"confidence": 0.5}, {"confidence": 0.5}]}
        result = self_critique(trace)
        self.assertIn("insufficient_depth", [c["flaw"] for c in result["critiques"]])

    def test_confidence_degradation_flagged(self):
        trace = {
            "steps": [
                {"phase": "start", "confidence": 0.95},
                {"phase": "mid", "confidence": 0.5},
                {"phase": "evaluate", "confidence": 0.3},
            ]
        }
        result = self_critique(trace)
        self.assertIn("confidence_degradation", [c["flaw"] for c in result["critiques"]])


class TestAnalogicalReasoning(unittest.TestCase):
    def test_basic_analogy(self):
        result = analogical_reasoning(
            "Improve monitoring",
            source_domain="DevOps",
            target_domain="Agent Network",
        )
        self.assertEqual(result["reasoning_type"], "analogical")
        self.assertIn("analogy_strength", result)
        self.assertEqual(result["mapping"]["source_domain"], "DevOps")

    def test_analogy_has_steps(self):
        result = analogical_reasoning("Test", "A", "B")
        self.assertGreaterEqual(len(result["steps"]), 3)


class TestCounterfactual(unittest.TestCase):
    def test_basic_counterfactual(self):
        result = counterfactual("Current strategy", "Use microservices instead")
        self.assertEqual(result["reasoning_type"], "counterfactual")
        self.assertEqual(result["alternative"], "Use microservices instead")
        self.assertIn("divergence_impact", result)


class TestReasonOrchestrator(unittest.TestCase):
    def test_chain_dispatch(self):
        result = reason("Test problem", reasoning_type="chain")
        self.assertEqual(result["reasoning_type"], "chain")
        self.assertIn("chain_hash", result)
        self.assertIn("self_critique", result)
        self.assertIn("problem", result)
        self.assertIn("timestamp", result)

    def test_tree_dispatch(self):
        result = reason("Test problem", reasoning_type="tree", branches=2)
        self.assertEqual(result["reasoning_type"], "tree")

    def test_invalid_type_defaults_to_chain(self):
        result = reason("Test", reasoning_type="invalid_type")
        self.assertEqual(result["reasoning_type"], "chain")

    def test_chain_hash_present(self):
        result = reason("Hash test")
        self.assertIsInstance(result["chain_hash"], str)
        self.assertGreater(len(result["chain_hash"]), 16)


class TestReasoningPersistence(unittest.TestCase):
    def test_save_and_load(self):
        trace = reason("Persistence test")
        path = save_reasoning_trace(trace)
        self.assertTrue(os.path.isfile(path))
        # Clean up
        os.remove(path)


# ===================================================================
# Communication Protocol Tests
# ===================================================================

class TestMessageCreation(unittest.TestCase):
    def test_create_query(self):
        msg = create_query("agent_a", "agent_b", "What status?")
        self.assertEqual(msg["msg_type"], "QUERY")
        self.assertEqual(msg["sender_agent"], "agent_a")
        self.assertEqual(msg["recipient_agent"], "agent_b")
        self.assertIn("message_id", msg)
        self.assertIn("timestamp", msg)

    def test_create_response(self):
        msg = create_response("agent_b", "agent_a", "All good", reference_id="ref123")
        self.assertEqual(msg["msg_type"], "RESPONSE")
        self.assertEqual(msg["reference_id"], "ref123")

    def test_create_proposal(self):
        msg = create_proposal("evolve", "Spawn new agent")
        self.assertEqual(msg["msg_type"], "PROPOSAL")
        self.assertEqual(msg["recipient_agent"], "ALL")

    def test_create_vote(self):
        msg = create_vote("agent_a", "proposal_1", "approve", "Good idea")
        self.assertEqual(msg["msg_type"], "VOTE")
        self.assertEqual(msg["content"]["vote"], "approve")

    def test_create_consensus(self):
        votes = [
            {"content": {"vote": "approve"}},
            {"content": {"vote": "approve"}},
            {"content": {"vote": "reject"}},
        ]
        msg = create_consensus("Test topic", "approved", votes)
        self.assertEqual(msg["msg_type"], "CONSENSUS")
        self.assertEqual(msg["content"]["votes_for"], 2)
        self.assertEqual(msg["content"]["votes_against"], 1)

    def test_create_delegation(self):
        msg = create_delegation("leader", "worker", "Build feature X")
        self.assertEqual(msg["msg_type"], "DELEGATION")

    def test_create_escalation(self):
        msg = create_escalation("agent_a", "Unresolvable conflict")
        self.assertEqual(msg["msg_type"], "ESCALATION")
        self.assertEqual(msg["recipient_agent"], "reasoning_engine")
        self.assertEqual(msg["priority"], "HIGH")

    def test_invalid_type_defaults(self):
        msg = create_message("a", "b", "test", "content", msg_type="INVALID")
        self.assertEqual(msg["msg_type"], "QUERY")

    def test_invalid_priority_defaults(self):
        msg = create_message("a", "b", "test", "content", priority="INVALID")
        self.assertEqual(msg["priority"], "MEDIUM")

    def test_message_types_constant(self):
        expected = ["QUERY", "RESPONSE", "PROPOSAL", "VOTE", "CONSENSUS",
                     "DELEGATION", "ESCALATION"]
        self.assertEqual(MESSAGE_TYPES, expected)


class TestCommunicationLog(unittest.TestCase):
    def setUp(self):
        """Use a temp file for the comms log during tests."""
        self.original_path = __import__("agents.reasoning.protocol",
                                        fromlist=["COMMS_LOG_PATH"]).COMMS_LOG_PATH
        self.tmp = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False)
        self.tmp.close()
        import agents.reasoning.protocol as proto
        proto.COMMS_LOG_PATH = self.tmp.name

    def tearDown(self):
        import agents.reasoning.protocol as proto
        proto.COMMS_LOG_PATH = self.original_path
        try:
            os.unlink(self.tmp.name)
        except Exception:
            pass

    def test_log_and_read(self):
        msg = create_query("a", "b", "test?")
        log_message(msg)
        messages = read_log()
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["sender_agent"], "a")

    def test_multiple_messages(self):
        for i in range(5):
            log_message(create_query(f"agent_{i}", "target", f"question {i}"))
        messages = read_log()
        self.assertEqual(len(messages), 5)

    def test_get_proposals(self):
        log_message(create_query("a", "b", "test"))
        log_message(create_proposal("c", "Build X"))
        log_message(create_proposal("d", "Build Y"))
        proposals = get_proposals()
        self.assertEqual(len(proposals), 2)

    def test_resolve_proposal(self):
        p = create_proposal("proposer", "Do thing")
        log_message(p)
        v1 = create_vote("a", p["message_id"], "approve")
        v2 = create_vote("b", p["message_id"], "approve")
        v3 = create_vote("c", p["message_id"], "reject")
        log_message(v1)
        log_message(v2)
        log_message(v3)
        consensus = resolve_proposal(p["message_id"])
        self.assertIsNotNone(consensus)
        self.assertEqual(consensus["content"]["outcome"], "approved")


class TestConflictDetection(unittest.TestCase):
    def test_detect_competing_proposals(self):
        msgs = [
            create_proposal("agent_a", "Do X"),
            create_proposal("agent_b", "Do Y"),
        ]
        conflicts = detect_conflicts(msgs)
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0]["type"], "competing_proposals")

    def test_no_conflict_same_sender(self):
        msgs = [
            create_proposal("agent_a", "Do X"),
            create_proposal("agent_a", "Do Y"),
        ]
        conflicts = detect_conflicts(msgs)
        self.assertEqual(len(conflicts), 0)


# ===================================================================
# Collective Intelligence Tests
# ===================================================================

class TestAgentRoles(unittest.TestCase):
    def test_role_creation(self):
        agent = AgentRole("test_agent", "proposer")
        self.assertEqual(agent.name, "test_agent")
        self.assertEqual(agent.role, "proposer")
        self.assertEqual(agent.opinions, [])

    def test_invalid_role_defaults(self):
        agent = AgentRole("test", "invalid_role")
        self.assertEqual(agent.role, "critic")

    def test_to_dict(self):
        agent = AgentRole("a", "critic")
        d = agent.to_dict()
        self.assertEqual(d["name"], "a")
        self.assertEqual(d["role"], "critic")

    def test_roles_constant(self):
        self.assertEqual(ROLES, ["proposer", "critic", "synthesizer", "executor"])


class TestDebatePanel(unittest.TestCase):
    def test_default_panel(self):
        panel = create_debate_panel()
        self.assertGreaterEqual(len(panel), 4)
        roles = [a.role for a in panel]
        self.assertIn("proposer", roles)
        self.assertIn("critic", roles)
        self.assertIn("synthesizer", roles)
        self.assertIn("executor", roles)


class TestDebateProtocol(unittest.TestCase):
    def test_propose(self):
        agent = AgentRole("p1", "proposer")
        result = propose(agent, "Should we add caching?")
        self.assertIn("solution", result)
        self.assertIn("reasoning", result)
        self.assertEqual(result["proposer"], "p1")
        self.assertEqual(len(agent.opinions), 1)

    def test_critique(self):
        proposer = AgentRole("p", "proposer")
        critic_agent = AgentRole("c", "critic")
        proposal = propose(proposer, "Add caching")
        result = critique(critic_agent, proposal)
        self.assertIn("flaws_found", result)
        self.assertIn("recommendation", result)
        self.assertEqual(result["critic"], "c")

    def test_full_debate(self):
        record = run_debate("Should we add a new monitoring agent?")
        self.assertIn("outcome", record)
        self.assertIn(record["outcome"], ["approved", "needs_revision"])
        self.assertIn("proposal", record)
        self.assertIn("critiques", record)
        self.assertIn("synthesis", record)
        self.assertIn("validation", record)
        self.assertIn("minority_reports", record)
        self.assertIn("chain_hash", record)

    def test_debate_no_proposer(self):
        panel = [AgentRole("c", "critic")]
        record = run_debate("test", panel=panel)
        self.assertIn("error", record)


class TestCollectiveVoting(unittest.TestCase):
    def test_basic_vote(self):
        agents = [
            AgentRole("a1", "critic"),
            AgentRole("a2", "critic"),
            AgentRole("a3", "proposer"),
        ]
        result = collective_vote("Best action", agents, ["option_a", "option_b"])
        self.assertIn("winner", result)
        self.assertIn(result["winner"], ["option_a", "option_b"])
        self.assertEqual(len(result["votes"]), 3)
        self.assertIn("tally", result)
        self.assertIn("minority_reports", result)


# ===================================================================
# Meta-Learning Tests
# ===================================================================

class TestMetaLearning(unittest.TestCase):
    def test_default_state(self):
        state = {
            "strategies": dict(DEFAULT_STRATEGIES),
            "problem_categories": {},
            "total_reasoning_episodes": 0,
            "lessons_generated": 0,
        }
        self.assertEqual(state["total_reasoning_episodes"], 0)
        self.assertIn("chain", state["strategies"])

    def test_record_outcome(self):
        state = {
            "strategies": copy.deepcopy(DEFAULT_STRATEGIES),
            "problem_categories": {},
            "total_reasoning_episodes": 0,
        }
        state = record_outcome(state, "chain", True)
        self.assertEqual(state["strategies"]["chain"]["uses"], 1)
        self.assertEqual(state["strategies"]["chain"]["successes"], 1)
        self.assertEqual(state["total_reasoning_episodes"], 1)

    def test_record_failure(self):
        state = {
            "strategies": copy.deepcopy(DEFAULT_STRATEGIES),
            "problem_categories": {},
            "total_reasoning_episodes": 0,
        }
        state = record_outcome(state, "chain", False)
        self.assertEqual(state["strategies"]["chain"]["uses"], 1)
        self.assertEqual(state["strategies"]["chain"]["successes"], 0)

    def test_new_strategy_auto_created(self):
        state = {
            "strategies": {},
            "problem_categories": {},
            "total_reasoning_episodes": 0,
        }
        state = record_outcome(state, "new_strat", True)
        self.assertIn("new_strat", state["strategies"])

    def test_select_best_strategy(self):
        state = {
            "strategies": {
                "chain": {"success_rate": 0.9, "uses": 10, "successes": 9},
                "tree": {"success_rate": 0.5, "uses": 10, "successes": 5},
            },
            "problem_categories": {},
        }
        best = select_strategy(state)
        self.assertEqual(best, "chain")

    def test_select_strategy_by_category(self):
        state = {
            "strategies": {
                "chain": {"success_rate": 0.9, "uses": 10, "successes": 9},
                "tree": {"success_rate": 0.5, "uses": 10, "successes": 5},
            },
            "problem_categories": {
                "operational": {
                    "count": 5,
                    "preferred_strategy": "tree",
                    "strategy_results": {},
                },
            },
        }
        best = select_strategy(state, problem_category="operational")
        self.assertEqual(best, "tree")


class TestProblemCategorization(unittest.TestCase):
    def test_operational_category(self):
        state = {"problem_categories": {}}
        cat = categorize_problem(state, "Monitor system uptime and health")
        self.assertEqual(cat, "operational")

    def test_expansion_category(self):
        state = {"problem_categories": {}}
        cat = categorize_problem(state, "Build a new agent to create reports")
        self.assertEqual(cat, "expansion")

    def test_optimization_category(self):
        state = {"problem_categories": {}}
        cat = categorize_problem(state, "Optimize database queries to improve speed")
        self.assertEqual(cat, "optimization")

    def test_revenue_category(self):
        state = {"problem_categories": {}}
        cat = categorize_problem(state, "Find ways to earn money and monetize")
        self.assertEqual(cat, "revenue")

    def test_general_fallback(self):
        state = {"problem_categories": {}}
        cat = categorize_problem(state, "Something completely unique")
        self.assertEqual(cat, "general")

    def test_explicit_category(self):
        state = {"problem_categories": {}}
        cat = categorize_problem(state, "Any problem", category="custom")
        self.assertEqual(cat, "custom")


class TestCategoryStrategyUpdate(unittest.TestCase):
    def test_update_preferred(self):
        state = {
            "problem_categories": {
                "operational": {
                    "count": 5,
                    "preferred_strategy": None,
                    "strategy_results": {},
                },
            },
        }
        update_category_strategy(state, "operational", "chain", True)
        update_category_strategy(state, "operational", "chain", True)
        update_category_strategy(state, "operational", "tree", False)
        cat = state["problem_categories"]["operational"]
        self.assertEqual(cat["preferred_strategy"], "chain")


class TestTraceAnalysis(unittest.TestCase):
    def test_analyze_empty(self):
        result = analyze_traces([])
        self.assertIsNone(result)

    def test_analyze_traces(self):
        traces = [
            {
                "reasoning_type": "chain",
                "steps": [{"confidence": 0.8}, {"confidence": 0.7}],
                "self_critique": "No flaws detected",
            },
            {
                "reasoning_type": "tree",
                "steps": [{"confidence": 0.6}],
                "self_critique": "Low confidence",
            },
        ]
        result = analyze_traces(traces)
        self.assertEqual(result["traces_analyzed"], 2)
        self.assertIn("chain", result["type_distribution"])
        self.assertIn("tree", result["type_distribution"])


class TestLessonGeneration(unittest.TestCase):
    def test_generate_lesson(self):
        state = {
            "strategies": {
                "chain": {"success_rate": 0.9, "uses": 10, "successes": 9},
                "tree": {"success_rate": 0.5, "uses": 2, "successes": 1},
            },
            "problem_categories": {
                "operational": {"count": 5, "preferred_strategy": "chain",
                                "strategy_results": {}},
            },
            "total_reasoning_episodes": 12,
            "lessons_generated": 0,
        }
        analysis = {
            "traces_analyzed": 5,
            "type_distribution": {"chain": 3, "tree": 2},
        }
        lesson = generate_lesson(state, analysis)
        self.assertIsNotNone(lesson)
        self.assertEqual(lesson["type"], "meta_learning_lesson")
        self.assertGreater(len(lesson["insights"]), 0)
        self.assertIn("chain_hash", lesson)


# ===================================================================
# Integration / Hash Chaining Tests
# ===================================================================

class TestHashChaining(unittest.TestCase):
    def test_deterministic(self):
        h1 = chain_hash("prev", {"a": 1})
        h2 = chain_hash("prev", {"a": 1})
        self.assertEqual(h1, h2)

    def test_different_payload(self):
        h1 = chain_hash("prev", {"a": 1})
        h2 = chain_hash("prev", {"a": 2})
        self.assertNotEqual(h1, h2)

    def test_different_prev(self):
        h1 = chain_hash("prev1", {"a": 1})
        h2 = chain_hash("prev2", {"a": 1})
        self.assertNotEqual(h1, h2)


if __name__ == "__main__":
    unittest.main()
