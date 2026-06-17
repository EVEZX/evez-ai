#!/usr/bin/env python3
"""
EVEZ-OS Agent OS Test Suite — unit + integration tests for the
autonomous agent operating system core modules.
"""
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch, MagicMock

# Adjust path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "os-evez"))


# ═══════════════════════════════════════════════════════════════════════
# Agent Bus Tests
# ═══════════════════════════════════════════════════════════════════════

class TestAgentBus:

    def test_event_creation(self):
        from agent_bus import Event
        ev = Event("TASK_CREATED", "test_source", {"key": "value"})
        assert ev.event_type == "TASK_CREATED"
        assert ev.source == "test_source"
        assert ev.data == {"key": "value"}
        assert len(ev.event_id) == 16
        assert ev.timestamp.endswith("+00:00") or ev.timestamp.endswith("Z")
        print("PASS test_event_creation")

    def test_event_round_trip(self):
        from agent_bus import Event
        ev = Event("FIRE_EVENT", "core", {"round": 144})
        d = ev.to_dict()
        ev2 = Event.from_dict(d)
        assert ev2.event_type == ev.event_type
        assert ev2.source == ev.source
        assert ev2.data == ev.data
        assert ev2.event_id == ev.event_id
        print("PASS test_event_round_trip")

    def test_publish_subscribe(self):
        from agent_bus import AgentBus, Event
        with tempfile.TemporaryDirectory() as td:
            bus = AgentBus(log_path=Path(td) / "test_bus.jsonl")
            received = []
            bus.subscribe("TASK_CREATED", lambda e: received.append(e))
            bus.emit("TASK_CREATED", "test", {"task": "do_thing"})
            assert len(received) == 1
            assert received[0].event_type == "TASK_CREATED"
            assert received[0].data["task"] == "do_thing"
            print("PASS test_publish_subscribe")

    def test_wildcard_subscriber(self):
        from agent_bus import AgentBus
        with tempfile.TemporaryDirectory() as td:
            bus = AgentBus(log_path=Path(td) / "test_bus.jsonl")
            all_events = []
            bus.subscribe(None, lambda e: all_events.append(e))
            bus.emit("TASK_CREATED", "test", {})
            bus.emit("ERROR", "test", {})
            bus.emit("FIRE_EVENT", "test", {})
            assert len(all_events) == 3
            print("PASS test_wildcard_subscriber")

    def test_persistence(self):
        from agent_bus import AgentBus
        with tempfile.TemporaryDirectory() as td:
            log_path = Path(td) / "test_bus.jsonl"
            bus = AgentBus(log_path=log_path)
            bus.emit("TASK_CREATED", "src1", {"n": 1})
            bus.emit("TASK_COMPLETED", "src2", {"n": 2})
            bus.emit("ERROR", "src3", {"n": 3})

            # Read back from disk
            events = bus.read_log()
            assert len(events) == 3
            assert events[0].event_type == "TASK_CREATED"
            assert events[2].event_type == "ERROR"
            print("PASS test_persistence")

    def test_read_by_type(self):
        from agent_bus import AgentBus
        with tempfile.TemporaryDirectory() as td:
            bus = AgentBus(log_path=Path(td) / "test_bus.jsonl")
            bus.emit("ERROR", "a", {})
            bus.emit("TASK_CREATED", "b", {})
            bus.emit("ERROR", "c", {})

            errors = bus.read_log_by_type("ERROR")
            assert len(errors) == 2
            assert all(e.event_type == "ERROR" for e in errors)
            print("PASS test_read_by_type")

    def test_unsubscribe(self):
        from agent_bus import AgentBus
        with tempfile.TemporaryDirectory() as td:
            bus = AgentBus(log_path=Path(td) / "test_bus.jsonl")
            received = []
            cb = lambda e: received.append(e)
            bus.subscribe("TASK_CREATED", cb)
            bus.emit("TASK_CREATED", "test", {})
            bus.unsubscribe("TASK_CREATED", cb)
            bus.emit("TASK_CREATED", "test", {})
            assert len(received) == 1
            print("PASS test_unsubscribe")

    def test_subscriber_crash_doesnt_break_bus(self):
        from agent_bus import AgentBus
        with tempfile.TemporaryDirectory() as td:
            bus = AgentBus(log_path=Path(td) / "test_bus.jsonl")
            good_events = []
            bus.subscribe("TEST", lambda e: (_ for _ in ()).throw(ValueError("boom")))
            bus.subscribe("TEST", lambda e: good_events.append(e))
            bus.emit("TEST", "test", {})
            assert len(good_events) == 1
            print("PASS test_subscriber_crash_doesnt_break_bus")


# ═══════════════════════════════════════════════════════════════════════
# Memory System Tests
# ═══════════════════════════════════════════════════════════════════════

class TestMemorySystem:

    def test_working_memory(self):
        from memory import WorkingMemory
        wm = WorkingMemory(max_size=5)
        wm.set("a", 1)
        wm.set("b", 2)
        assert wm.get("a") == 1
        assert wm.get("b") == 2
        assert wm.get("c") is None
        assert wm.get("c", "default") == "default"
        assert wm.size == 2
        print("PASS test_working_memory")

    def test_working_memory_eviction(self):
        from memory import WorkingMemory
        wm = WorkingMemory(max_size=3)
        wm.set("a", 1)
        wm.set("b", 2)
        wm.set("c", 3)
        wm.set("d", 4)  # should evict "a"
        assert wm.get("a") is None
        assert wm.get("d") == 4
        assert wm.size == 3
        print("PASS test_working_memory_eviction")

    def test_episodic_memory(self):
        from memory import EpisodicMemory
        with tempfile.TemporaryDirectory() as td:
            ep = EpisodicMemory(Path(td))
            ep.start_episode("EP-001", {"context": "test"})
            ep.record("EP-001", "step", {"action": "observe"})
            ep.record("EP-001", "step", {"action": "decide"})
            ep.end_episode("EP-001", "Test episode complete")

            events = ep.read_episode("EP-001")
            assert len(events) == 4
            assert events[0]["kind"] == "episode.start"
            assert events[-1]["kind"] == "episode.end"
            assert "EP-001" in ep.list_episodes()
            print("PASS test_episodic_memory")

    def test_semantic_memory(self):
        from memory import SemanticMemory
        with tempfile.TemporaryDirectory() as td:
            sm = SemanticMemory(Path(td) / "graph.json")
            sm.add_node("evez-os", "repo", {"language": "python"})
            sm.add_node("orchestrator", "module", {"purpose": "coordination"})
            sm.add_edge("orchestrator", "evez-os", "part_of")

            node = sm.get_node("evez-os")
            assert node is not None
            assert node["type"] == "repo"

            neighbors = sm.get_neighbors("orchestrator")
            assert len(neighbors) == 1
            assert neighbors[0]["relation"] == "part_of"

            results = sm.search("python")
            assert len(results) >= 1

            assert sm.node_count == 2
            assert sm.edge_count == 1
            print("PASS test_semantic_memory")

    def test_semantic_memory_dedup_edges(self):
        from memory import SemanticMemory
        with tempfile.TemporaryDirectory() as td:
            sm = SemanticMemory(Path(td) / "graph.json")
            sm.add_node("a", "test", {})
            sm.add_node("b", "test", {})
            sm.add_edge("a", "b", "relates_to", {"v": 1})
            sm.add_edge("a", "b", "relates_to", {"v": 2})
            assert sm.edge_count == 1  # deduped
            edges = sm.get_neighbors("a")
            assert edges[0]["properties"]["v"] == 2  # updated
            print("PASS test_semantic_memory_dedup_edges")

    def test_memory_system_spine(self):
        from memory import MemorySystem
        with tempfile.TemporaryDirectory() as td:
            ms = MemorySystem(
                base_dir=Path(td),
                spine_path=Path(td) / "spine.jsonl",
            )
            ms.append_to_spine({"kind": "test", "data": "hello"})
            ms.append_to_spine({"kind": "test", "data": "world"})

            events = ms.read_spine()
            assert len(events) == 2
            assert events[0]["data"] == "hello"

            results = ms.search_spine("world")
            assert len(results) == 1
            print("PASS test_memory_system_spine")

    def test_memory_status(self):
        from memory import MemorySystem
        with tempfile.TemporaryDirectory() as td:
            ms = MemorySystem(
                base_dir=Path(td),
                spine_path=Path(td) / "spine.jsonl",
            )
            status = ms.status()
            assert "working_memory_size" in status
            assert "semantic_nodes" in status
            assert "spine_events" in status
            print("PASS test_memory_status")


# ═══════════════════════════════════════════════════════════════════════
# Orchestrator Tests
# ═══════════════════════════════════════════════════════════════════════

class TestOrchestrator:

    def test_agent_registry(self):
        from orchestrator import AgentRecord, AgentRegistry
        reg = AgentRegistry()
        agent = AgentRecord("A1", "TestAgent", ["repair", "deploy"])
        reg.register(agent)

        found = reg.get("A1")
        assert found is not None
        assert found.name == "TestAgent"

        by_cap = reg.find_by_capability("repair")
        assert len(by_cap) == 1
        assert by_cap[0].agent_id == "A1"

        assert len(reg.active_agents()) == 1
        print("PASS test_agent_registry")

    def test_agent_heartbeat(self):
        from orchestrator import AgentRecord, AgentRegistry
        reg = AgentRegistry()
        agent = AgentRecord("A1", "Test", ["test"])
        reg.register(agent)
        old_hb = agent.last_heartbeat
        reg.heartbeat("A1")
        # Heartbeat should be updated (or same if within same second)
        assert reg.get("A1").last_heartbeat >= old_hb
        print("PASS test_agent_heartbeat")

    def test_task_creation(self):
        from orchestrator import Task
        task = Task("Fix CI", "ci_repair", priority=2, data={"repo": "evez-os"})
        assert task.status == "pending"
        assert task.required_capability == "ci_repair"
        assert task.priority == 2
        d = task.to_dict()
        assert d["description"] == "Fix CI"
        print("PASS test_task_creation")

    def test_ooda_cycle(self):
        from orchestrator import Orchestrator
        from agent_bus import AgentBus
        from memory import MemorySystem
        with tempfile.TemporaryDirectory() as td:
            bus = AgentBus(log_path=Path(td) / "bus.jsonl")
            memory = MemorySystem(
                base_dir=Path(td),
                spine_path=Path(td) / "spine.jsonl",
            )
            orch = Orchestrator(bus=bus, memory=memory, spine_path=Path(td) / "spine.jsonl")

            report = orch.run_ooda_cycle()
            assert "cycle_id" in report
            assert "phases" in report
            assert "observe" in report["phases"]
            assert "orient" in report["phases"]
            assert "decide" in report["phases"]
            assert "act" in report["phases"]

            # Verify spine was written
            spine_events = memory.read_spine()
            ooda_events = [e for e in spine_events if e.get("kind") == "ooda.cycle"]
            assert len(ooda_events) >= 1
            print("PASS test_ooda_cycle")

    def test_orchestrator_bootstraps_agents(self):
        from orchestrator import Orchestrator
        from agent_bus import AgentBus
        from memory import MemorySystem
        with tempfile.TemporaryDirectory() as td:
            bus = AgentBus(log_path=Path(td) / "bus.jsonl")
            memory = MemorySystem(
                base_dir=Path(td),
                spine_path=Path(td) / "spine.jsonl",
            )
            orch = Orchestrator(bus=bus, memory=memory, spine_path=Path(td) / "spine.jsonl")
            # Should have loaded agents from registry.py
            all_agents = orch.registry.all_agents()
            assert len(all_agents) > 0, "Should bootstrap agents from registry"
            print("PASS test_orchestrator_bootstraps_agents")

    def test_orchestrator_status(self):
        from orchestrator import Orchestrator
        from agent_bus import AgentBus
        from memory import MemorySystem
        with tempfile.TemporaryDirectory() as td:
            bus = AgentBus(log_path=Path(td) / "bus.jsonl")
            memory = MemorySystem(
                base_dir=Path(td),
                spine_path=Path(td) / "spine.jsonl",
            )
            orch = Orchestrator(bus=bus, memory=memory, spine_path=Path(td) / "spine.jsonl")
            status = orch.status()
            assert "agents_total" in status
            assert "tasks_pending" in status
            assert "registry" in status
            print("PASS test_orchestrator_status")


# ═══════════════════════════════════════════════════════════════════════
# Self-Repair Tests
# ═══════════════════════════════════════════════════════════════════════

class TestSelfRepair:

    def test_error_classification(self):
        from self_repair import SelfRepairDaemon
        daemon = SelfRepairDaemon()

        log = "ModuleNotFoundError: No module named 'requests'"
        results = daemon.classify_errors(log)
        assert len(results) >= 1
        assert results[0].pattern_name == "missing_dependency"
        assert results[0].match_groups[0] == "requests"
        print("PASS test_error_classification")

    def test_classify_multiple_errors(self):
        from self_repair import SelfRepairDaemon
        daemon = SelfRepairDaemon()

        log = """
        ModuleNotFoundError: No module named 'flask'
        KeyError: 'DATABASE_URL'
        TypeError: unsupported operand
        """
        results = daemon.classify_errors(log)
        types = {r.pattern_name for r in results}
        assert "missing_dependency" in types
        assert "missing_env_var" in types
        assert "type_error" in types
        print("PASS test_classify_multiple_errors")

    def test_generate_fix_dependency(self):
        from self_repair import SelfRepairDaemon, ErrorClassification
        daemon = SelfRepairDaemon()
        cls = ErrorClassification(
            pattern_name="missing_dependency",
            fix_type="add_dependency",
            description="Missing Python dependency",
            match_groups=("requests",),
            raw_error="ModuleNotFoundError: No module named 'requests'",
        )
        fix = daemon.generate_fix("evez-os", cls)
        assert fix["type"] == "pr"
        assert "requests" in fix["title"]
        print("PASS test_generate_fix_dependency")

    def test_generate_fix_env_var(self):
        from self_repair import SelfRepairDaemon, ErrorClassification
        daemon = SelfRepairDaemon()
        cls = ErrorClassification(
            pattern_name="missing_env_var",
            fix_type="add_env_fallback",
            description="Missing env var",
            match_groups=("API_KEY",),
            raw_error="KeyError: 'API_KEY'",
        )
        fix = daemon.generate_fix("evez-os", cls)
        assert fix["type"] == "issue"
        assert "API_KEY" in fix["title"]
        print("PASS test_generate_fix_env_var")


# ═══════════════════════════════════════════════════════════════════════
# Expansion Engine Tests
# ═══════════════════════════════════════════════════════════════════════

class TestExpansionEngine:

    def test_scan_markers(self):
        from expansion import ExpansionEngine
        engine = ExpansionEngine()
        markers = engine.scan_markers()
        # Should find at least some markers in the codebase
        assert isinstance(markers, list)
        print(f"PASS test_scan_markers (found {len(markers)} markers)")

    def test_scan_test_coverage(self):
        from expansion import ExpansionEngine
        engine = ExpansionEngine()
        gaps = engine.scan_test_coverage()
        assert isinstance(gaps, list)
        print(f"PASS test_scan_test_coverage (found {len(gaps)} gaps)")

    def test_generate_proposals(self):
        from expansion import ExpansionEngine
        engine = ExpansionEngine()
        proposals = engine.generate_proposals()
        assert isinstance(proposals, list)
        if proposals:
            p = proposals[0]
            assert hasattr(p, "title")
            assert hasattr(p, "priority_score")
        print(f"PASS test_generate_proposals (generated {len(proposals)} proposals)")

    def test_expansion_cycle(self):
        from expansion import ExpansionEngine
        from agent_bus import AgentBus
        from memory import MemorySystem
        with tempfile.TemporaryDirectory() as td:
            bus = AgentBus(log_path=Path(td) / "bus.jsonl")
            memory = MemorySystem(
                base_dir=Path(td),
                spine_path=Path(td) / "spine.jsonl",
            )
            engine = ExpansionEngine(bus=bus, memory=memory)
            result = engine.run_expansion_cycle(create_issues=False)
            assert "markers_found" in result
            assert "test_gaps" in result
            assert "proposals_generated" in result
            print("PASS test_expansion_cycle")


# ═══════════════════════════════════════════════════════════════════════
# Cross-Repo Coordination Tests
# ═══════════════════════════════════════════════════════════════════════

class TestCrossRepo:

    def test_topology(self):
        from cross_repo import CrossRepoCoordinator
        coord = CrossRepoCoordinator()
        repo_map = coord.repo_map()
        assert "evez-os" in repo_map
        assert isinstance(repo_map["evez-os"], dict)
        print("PASS test_topology")

    def test_get_dependents(self):
        from cross_repo import CrossRepoCoordinator
        coord = CrossRepoCoordinator()
        dependents = coord.get_dependents("evez-os")
        assert isinstance(dependents, list)
        # evez-os is the root — many things depend on it
        assert len(dependents) > 0
        print(f"PASS test_get_dependents ({len(dependents)} dependents of evez-os)")

    def test_get_dependencies(self):
        from cross_repo import CrossRepoCoordinator
        coord = CrossRepoCoordinator()
        deps = coord.get_dependencies("evez-dashboard")
        assert "evez-api" in deps
        print("PASS test_get_dependencies")

    def test_impact_analysis(self):
        from cross_repo import CrossRepoCoordinator
        coord = CrossRepoCoordinator()
        impact = coord.analyze_change_impact("evez-os")
        assert "repo" in impact
        assert "all_affected" in impact
        assert "impact_radius" in impact
        assert "recommendation" in impact
        print("PASS test_impact_analysis")


# ═══════════════════════════════════════════════════════════════════════
# Integration Test
# ═══════════════════════════════════════════════════════════════════════

class TestIntegration:

    def test_full_ooda_cycle_integration(self):
        """Integration test: full OODA cycle with all subsystems."""
        from orchestrator import Orchestrator
        from agent_bus import AgentBus
        from memory import MemorySystem
        from expansion import ExpansionEngine
        from self_repair import SelfRepairDaemon

        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            bus = AgentBus(log_path=td / "bus.jsonl")
            memory = MemorySystem(base_dir=td, spine_path=td / "spine.jsonl")

            # 1. Start orchestrator
            orch = Orchestrator(bus=bus, memory=memory, spine_path=td / "spine.jsonl")
            assert len(orch.registry.all_agents()) > 0

            # 2. Run OODA cycle
            report = orch.run_ooda_cycle()
            assert report["cycle_id"].startswith("OODA-")

            # 3. Run expansion
            engine = ExpansionEngine(bus=bus, memory=memory)
            exp_result = engine.run_expansion_cycle()
            assert exp_result["proposals_generated"] >= 0

            # 4. Check bus has events
            events = bus.read_log()
            event_types = {e.event_type for e in events}
            assert "OODA_CYCLE" in event_types
            assert "EXPANSION" in event_types

            # 5. Check memory has spine entries
            spine = memory.read_spine()
            assert len(spine) > 0

            # 6. Verify error classification works
            daemon = SelfRepairDaemon(bus=bus, memory=memory)
            results = daemon.classify_errors(
                "ModuleNotFoundError: No module named 'nonexistent'"
            )
            assert len(results) >= 1

            print("PASS test_full_ooda_cycle_integration")


# ═══════════════════════════════════════════════════════════════════════
# Runner
# ═══════════════════════════════════════════════════════════════════════

def run_all():
    """Run all tests."""
    test_classes = [
        TestAgentBus,
        TestMemorySystem,
        TestOrchestrator,
        TestSelfRepair,
        TestExpansionEngine,
        TestCrossRepo,
        TestIntegration,
    ]

    total = 0
    passed = 0
    failed = 0

    for cls in test_classes:
        print(f"\n{'='*60}")
        print(f"  {cls.__name__}")
        print(f"{'='*60}")
        instance = cls()
        for name in sorted(dir(instance)):
            if name.startswith("test_"):
                total += 1
                try:
                    getattr(instance, name)()
                    passed += 1
                except Exception as e:
                    failed += 1
                    print(f"FAIL {name}: {e}")

    print(f"\n{'='*60}")
    print(f"  Results: {passed}/{total} passed, {failed} failed")
    print(f"{'='*60}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_all())
