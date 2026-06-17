#!/usr/bin/env python3
"""
EVEZ-OS Unified CLI — single entry point for the autonomous agent OS.

Commands:
    evez status          — show full ecosystem state
    evez agents          — list all registered agents
    evez ooda            — run one OODA cycle
    evez fix [repo]      — trigger self-repair on a repo
    evez evolve          — run one expansion cycle
    evez memory search   — search memory
    evez memory status   — show memory system status
    evez repos           — show cross-repo dependency map
    evez bus tail        — show recent bus events
    evez deploy          — trigger deployment of all repos
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Ensure sibling imports work
sys.path.insert(0, str(Path(__file__).resolve().parent))


def _json_out(data, indent=2):
    """Pretty-print JSON data."""
    print(json.dumps(data, indent=indent, default=str))


# ── Commands ─────────────────────────────────────────────────────────

def cmd_status(args):
    """Show full ecosystem state."""
    from orchestrator import Orchestrator
    from memory import MemorySystem
    from agent_bus import get_bus

    bus = get_bus()
    memory = MemorySystem()
    orch = Orchestrator(bus=bus, memory=memory)

    status = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "orchestrator": orch.status(),
        "memory": memory.status(),
        "bus_subscribers": bus.subscriber_count,
        "recent_events": len(bus.tail(50)),
    }
    _json_out(status)
    return 0


def cmd_agents(args):
    """List all registered agents."""
    from orchestrator import Orchestrator

    orch = Orchestrator()
    agents = orch.registry.all_agents()

    if not agents:
        print("No agents registered.")
        return 0

    print(f"{'ID':<6} {'Name':<35} {'Status':<12} {'Capabilities'}")
    print("-" * 80)
    for a in agents:
        caps = ", ".join(a.capabilities[:3])
        print(f"{a.agent_id:<6} {a.name:<35} {a.status:<12} {caps}")

    print(f"\nTotal: {len(agents)} agents ({len([a for a in agents if a.status == 'ACTIVE'])} active)")
    return 0


def cmd_ooda(args):
    """Run one OODA cycle."""
    from orchestrator import run_cycle
    print("Running OODA cycle...")
    report = run_cycle()
    _json_out(report)
    return 0


def cmd_fix(args):
    """Trigger self-repair on a repo."""
    from self_repair import SelfRepairDaemon

    daemon = SelfRepairDaemon()
    repos = [args.repo] if args.repo else None

    if repos:
        print(f"Running repair on: {', '.join(repos)}")
    else:
        print("Running repair on all repos...")

    result = daemon.run_repair_cycle(repos=repos)
    _json_out(result)
    return 0


def cmd_evolve(args):
    """Run one expansion cycle."""
    from expansion import run_expansion

    create = getattr(args, "create_issues", False)
    print("Running expansion cycle...")
    result = run_expansion(create_issues=create)

    # Print summary
    print(f"\nMarkers found: {result['markers_found']}")
    print(f"Test gaps: {result['test_gaps']}")
    print(f"Proposals: {result['proposals_generated']}")

    if result.get("proposals"):
        print("\nTop proposals:")
        for p in result["proposals"][:10]:
            print(f"  [{p['priority_score']:.1f}] {p['title'][:70]}")

    return 0


def cmd_memory_search(args):
    """Search memory system."""
    from memory import MemorySystem

    memory = MemorySystem()
    query = args.query

    print(f"Searching memory for: {query}")

    # Search spine
    spine_results = memory.search_spine(query, limit=20)
    if spine_results:
        print(f"\nSpine events ({len(spine_results)} matches):")
        for event in spine_results[-5:]:
            ts = event.get("timestamp", "?")
            kind = event.get("kind", event.get("event_type", "?"))
            print(f"  [{ts}] {kind}")

    # Search semantic memory
    semantic_results = memory.semantic.search(query)
    if semantic_results:
        print(f"\nSemantic nodes ({len(semantic_results)} matches):")
        for nid, node in semantic_results[:5]:
            print(f"  {nid}: {node.get('type', '?')} — {json.dumps(node.get('properties', {}), default=str)[:80]}")

    if not spine_results and not semantic_results:
        print("No results found.")

    return 0


def cmd_memory_status(args):
    """Show memory system status."""
    from memory import MemorySystem

    memory = MemorySystem()
    _json_out(memory.status())
    return 0


def cmd_repos(args):
    """Show cross-repo dependency map."""
    from cross_repo import CrossRepoCoordinator

    coord = CrossRepoCoordinator()
    repo_map = coord.repo_map()

    print(f"{'Repo':<30} {'Depends On':<30} {'Dependents'}")
    print("-" * 90)
    for repo, info in sorted(repo_map.items()):
        deps = ", ".join(info.get("depends_on", []))[:28] or "(none)"
        dependents = ", ".join(info.get("dependents", []))[:28] or "(none)"
        print(f"{repo:<30} {deps:<30} {dependents}")

    if args.repo:
        print(f"\nImpact analysis for {args.repo}:")
        impact = coord.analyze_change_impact(args.repo)
        _json_out(impact)

    return 0


def cmd_bus_tail(args):
    """Show recent bus events."""
    from agent_bus import get_bus

    bus = get_bus()
    n = getattr(args, "n", 20)
    events = bus.tail(n)

    if not events:
        print("No events in bus log.")
        return 0

    for event in events:
        ts = event.get("timestamp", "?")
        etype = event.get("event_type", "?")
        src = event.get("source", "?")
        print(f"[{ts}] {etype:<20} src={src}")

    return 0


def cmd_deploy(args):
    """Trigger deployment of all repos."""
    from cross_repo import CrossRepoCoordinator

    coord = CrossRepoCoordinator()
    repos = sorted(coord._repos.keys())

    print("Deployment order (dependency-safe):")
    # Topological sort: deploy dependencies first
    deployed = set()
    order = []
    remaining = set(repos)

    while remaining:
        batch = []
        for repo in sorted(remaining):
            info = coord._repos.get(repo)
            deps = set(info.depends_on) if info else set()
            if deps.issubset(deployed):
                batch.append(repo)
        if not batch:
            # Circular dep or unknown — just add remaining
            batch = sorted(remaining)
        for repo in batch:
            order.append(repo)
            deployed.add(repo)
            remaining.discard(repo)

    for i, repo in enumerate(order, 1):
        print(f"  {i}. {repo}")

    print(f"\nTotal: {len(order)} repos")
    print("(Actual deployment requires CI/CD pipeline triggers)")
    return 0


# ── Main ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        prog="evez",
        description="EVEZ-OS Autonomous Agent Operating System CLI",
    )
    sub = parser.add_subparsers(dest="command")

    # status
    sub.add_parser("status", help="Show full ecosystem state")

    # agents
    sub.add_parser("agents", help="List all registered agents")

    # ooda
    sub.add_parser("ooda", help="Run one OODA cycle")

    # fix
    fix_p = sub.add_parser("fix", help="Trigger self-repair on a repo")
    fix_p.add_argument("repo", nargs="?", default=None, help="Repo name (or all)")

    # evolve
    evolve_p = sub.add_parser("evolve", help="Run one expansion cycle")
    evolve_p.add_argument("--create-issues", action="store_true",
                          help="Actually create GitHub issues")

    # memory
    memory_p = sub.add_parser("memory", help="Memory system commands")
    memory_sub = memory_p.add_subparsers(dest="memory_cmd")
    search_p = memory_sub.add_parser("search", help="Search memory")
    search_p.add_argument("query", help="Search query")
    memory_sub.add_parser("status", help="Show memory status")

    # repos
    repos_p = sub.add_parser("repos", help="Show cross-repo dependency map")
    repos_p.add_argument("repo", nargs="?", default=None,
                         help="Repo for impact analysis")

    # bus
    bus_p = sub.add_parser("bus", help="Bus commands")
    bus_sub = bus_p.add_subparsers(dest="bus_cmd")
    tail_p = bus_sub.add_parser("tail", help="Show recent events")
    tail_p.add_argument("-n", type=int, default=20, help="Number of events")

    # deploy
    sub.add_parser("deploy", help="Show deployment order")

    args = parser.parse_args()

    commands = {
        "status": cmd_status,
        "agents": cmd_agents,
        "ooda": cmd_ooda,
        "fix": cmd_fix,
        "evolve": cmd_evolve,
        "repos": cmd_repos,
        "deploy": cmd_deploy,
    }

    if args.command in commands:
        return commands[args.command](args)
    elif args.command == "memory":
        if args.memory_cmd == "search":
            return cmd_memory_search(args)
        elif args.memory_cmd == "status":
            return cmd_memory_status(args)
        else:
            memory_p.print_help()
            return 0
    elif args.command == "bus":
        if args.bus_cmd == "tail":
            return cmd_bus_tail(args)
        else:
            bus_p.print_help()
            return 0
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
