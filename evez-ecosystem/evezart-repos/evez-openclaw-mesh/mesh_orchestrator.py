#!/usr/bin/env python3
"""
EVEZ OpenClaw Mesh Orchestrator
=================================
Manages the full mesh:
- Tracks all OpenClaw node endpoints
- Routes prompts to available nodes with load balancing
- Tests each node with live prompts
- Reports mesh health

Usage:
  python mesh_orchestrator.py test        # Run full test suite
  python mesh_orchestrator.py status      # Show mesh status
  python mesh_orchestrator.py prompt "X"  # Send prompt to best node
  python mesh_orchestrator.py start-local # Start local mesh (for dev)
"""

import asyncio, httpx, json, os, sys, time, subprocess
from typing import Optional
from dataclasses import dataclass, field

# ── Node Registry ────────────────────────────────────────────
@dataclass
class OpenClawNode:
    id: str
    gateway_url: str     # OpenClaw gateway (HTTP/WS)
    brain_url: str       # evez-mesh brain API
    broker_url: str      # evez-mesh broker API
    region: str = "ams"
    status: str = "unknown"
    latency_ms: float = 9999.0
    last_check: float = 0.0
    error: str = ""

NODES = [
    OpenClawNode(
        id="alpha",
        gateway_url=os.getenv("ALPHA_GATEWAY", "https://openclaws-qol4-a.fly.dev"),
        brain_url=os.getenv("ALPHA_BRAIN",   "https://openclaws-qol4-a.fly.dev"),
        broker_url=os.getenv("ALPHA_BROKER", "https://openclaws-qol4-a.fly.dev"),
        region="ams"
    ),
    OpenClawNode(
        id="beta",
        gateway_url=os.getenv("BETA_GATEWAY", "https://openclaw-pfncdg.fly.dev"),
        brain_url=os.getenv("BETA_BRAIN",   "https://openclaw-pfncdg.fly.dev"),
        broker_url=os.getenv("BETA_BROKER", "https://openclaw-pfncdg.fly.dev"),
        region="ams"
    ),
    OpenClawNode(
        id="brain",
        gateway_url=os.getenv("BRAIN_GATEWAY", "https://evez666.fly.dev"),
        brain_url=os.getenv("BRAIN_URL",      "https://evez666.fly.dev"),
        broker_url=os.getenv("BROKER_URL",    "https://evez666.fly.dev"),
        region="ams"
    ),
]

LOCAL_NODES = [
    OpenClawNode(id="local-alpha",  gateway_url="http://127.0.0.1:18789", brain_url="http://127.0.0.1:8893", broker_url="http://127.0.0.1:8894"),
    OpenClawNode(id="local-beta",   gateway_url="http://127.0.0.1:18790", brain_url="http://127.0.0.1:8895", broker_url="http://127.0.0.1:8896"),
    OpenClawNode(id="local-brain",  gateway_url="http://127.0.0.1:18791", brain_url="http://127.0.0.1:8897", broker_url="http://127.0.0.1:8898"),
]

# ── Health Checks ─────────────────────────────────────────────

async def check_node(node: OpenClawNode, client: httpx.AsyncClient) -> OpenClawNode:
    """Ping both gateway and brain endpoints"""
    t0 = time.time()
    gateway_ok = False
    brain_ok = False
    errors = []

    # Check gateway
    try:
        r = await client.get(f"{node.gateway_url}/health", timeout=8)
        if r.status_code == 200:
            gateway_ok = True
    except Exception as e:
        errors.append(f"gateway: {e}")

    # Check brain
    try:
        r = await client.get(f"{node.brain_url}/health", timeout=8)
        if r.status_code == 200:
            brain_ok = True
    except Exception as e:
        errors.append(f"brain: {e}")

    node.latency_ms = round((time.time() - t0) * 1000, 1)
    node.last_check = time.time()

    if gateway_ok and brain_ok:
        node.status = "online"
        node.error = ""
    elif brain_ok:
        node.status = "brain-only"
        node.error = " | ".join(errors)
    elif gateway_ok:
        node.status = "gateway-only"
        node.error = " | ".join(errors)
    else:
        node.status = "offline"
        node.error = " | ".join(errors)

    return node

async def check_all_nodes(nodes=None) -> list:
    active_nodes = nodes or NODES
    async with httpx.AsyncClient(timeout=10) as client:
        tasks = [check_node(n, client) for n in active_nodes]
        return await asyncio.gather(*tasks)

# ── Prompt Routing ─────────────────────────────────────────────

async def prompt_node(node: OpenClawNode, query: str) -> dict:
    """Send a prompt to a node's brain and return the thought"""
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            r = await client.post(
                f"{node.brain_url}/think",
                params={"query": query},
                timeout=25
            )
            if r.status_code == 200:
                data = r.json()
                return {
                    "node": node.id,
                    "success": True,
                    "response": data.get("response", ""),
                    "confidence": data.get("confidence", 0),
                    "unfogged": data.get("unfogged", False),
                    "latency_ms": round((time.time()) * 1000)
                }
            else:
                return {"node": node.id, "success": False, "error": f"HTTP {r.status_code}", "response": r.text[:200]}
        except Exception as e:
            return {"node": node.id, "success": False, "error": str(e), "response": ""}

async def route_prompt(query: str, strategy: str = "first-available") -> dict:
    """Route a prompt to the best available node"""
    nodes = await check_all_nodes()
    online = [n for n in nodes if n.status in ("online", "brain-only")]

    if not online:
        return {"error": "All nodes offline", "query": query, "nodes_checked": len(nodes)}

    if strategy == "first-available":
        node = online[0]
    elif strategy == "lowest-latency":
        node = min(online, key=lambda n: n.latency_ms)
    elif strategy == "broadcast":
        # Ask all nodes, return consensus
        tasks = [prompt_node(n, query) for n in online]
        results = await asyncio.gather(*tasks)
        return {
            "strategy": "broadcast",
            "query": query,
            "responses": results,
            "consensus": max(results, key=lambda r: r.get("confidence", 0)).get("response", "")
        }
    else:
        node = online[0]

    result = await prompt_node(node, query)
    result["strategy"] = strategy
    result["query"] = query
    return result

# ── Test Suite ───────────────────────────────────────────────

TEST_PROMPTS = [
    ("identify", "What are you? Respond with your node ID and status."),
    ("math", "What is the square root of 144 multiplied by the Fibonacci number at position 7?"),
    ("reasoning", "If mesh node alpha has 3 memories and beta has 5, and they gossip every 60 seconds, how many total unique memories after 2 sync cycles assuming 1 new memory per node per cycle?"),
    ("evez-os", "What EVEZ-OS capabilities do you have? List your active skills."),
    ("creativity", "Generate a 3-line haiku about decentralized AI mesh networks."),
]

async def run_test_suite(nodes=None):
    """Run the full test suite against all nodes"""
    active_nodes = nodes or NODES
    print("\n🔬 EVEZ OpenClaw Mesh — Full Test Suite")
    print("=" * 60)

    # Step 1: Health check
    print("\n[1/3] Health Checks...")
    checked = await check_all_nodes(active_nodes)
    for n in checked:
        icon = "✅" if n.status == "online" else "⚠️" if "only" in n.status else "❌"
        print(f"  {icon} {n.id:15s} | {n.status:15s} | {n.latency_ms:6.0f}ms | {n.error[:50] if n.error else 'OK'}")

    online = [n for n in checked if n.status in ("online", "brain-only")]
    if not online:
        print("\n❌ No nodes online. Check your Fly.io deployments and API keys.")
        return {"success": False, "online_nodes": 0, "tests_passed": 0}

    # Step 2: Prompt each node
    print(f"\n[2/3] Prompting {len(online)} online node(s)...")
    results = []
    for node in online:
        for test_name, prompt in TEST_PROMPTS:
            t0 = time.time()
            result = await prompt_node(node, prompt)
            elapsed = round((time.time() - t0) * 1000)
            icon = "✅" if result["success"] and result.get("response") else "❌"
            resp_preview = result.get("response", result.get("error", ""))[:80]
            print(f"  {icon} {node.id}/{test_name:12s} ({elapsed}ms) → {resp_preview}")
            results.append({"node": node.id, "test": test_name, **result})

    # Step 3: Cross-node gossip test
    print("\n[3/3] Cross-node gossip test...")
    if len(online) >= 2:
        async with httpx.AsyncClient(timeout=10) as client:
            # Memorize on alpha, recall on beta
            try:
                mem_payload = {
                    "mem_type": "semantic",
                    "content": "EVEZ mesh test memory: the mesh is alive and coherent",
                    "confidence": 1.0,
                    "tags": ["test", "mesh", "evez"]
                }
                r = await client.post(f"{online[0].brain_url}/memorize", json=mem_payload, timeout=8)
                if r.status_code == 200:
                    print(f"  ✅ Stored test memory on {online[0].id}")
                
                # Trigger gossip
                for n in online[1:]:
                    r2 = await client.get(f"{online[0].brain_url}/gossip", timeout=8)
                    if r2.status_code == 200:
                        gossip_data = r2.json()
                        r3 = await client.post(f"{n.brain_url}/gossip", json=gossip_data["memories"], timeout=8)
                        if r3.status_code == 200:
                            merged = r3.json().get("merged", 0)
                            print(f"  ✅ Gossip synced to {n.id}: {merged} new memories")
            except Exception as e:
                print(f"  ⚠️  Gossip test failed: {e}")
    else:
        print("  ⚠️  Need 2+ nodes for gossip test")

    # Summary
    passed = sum(1 for r in results if r["success"] and r.get("response"))
    total = len(results)
    print(f"\n{'='*60}")
    print(f"✅ Tests passed: {passed}/{total}")
    print(f"🌐 Online nodes: {len(online)}/{len(active_nodes)}")
    print(f"{'='*60}\n")

    return {
        "success": passed > 0,
        "online_nodes": len(online),
        "tests_passed": passed,
        "tests_total": total,
        "results": results
    }

# ── CLI ───────────────────────────────────────────────────────

async def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"

    if cmd == "test":
        await run_test_suite()

    elif cmd == "test-local":
        await run_test_suite(LOCAL_NODES)

    elif cmd == "status":
        nodes = await check_all_nodes()
        print("\n🌐 EVEZ OpenClaw Mesh Status")
        print("=" * 50)
        for n in nodes:
            icon = "✅" if n.status == "online" else "⚠️" if "only" in n.status else "❌"
            print(f"  {icon} {n.id:20s} {n.status:15s} {n.latency_ms:6.0f}ms")
            if n.error:
                print(f"     └─ {n.error[:60]}")
        print()

    elif cmd == "prompt":
        query = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "Hello mesh. What are you?"
        print(f"\n📡 Routing: \"{query}\"")
        result = await route_prompt(query, strategy="broadcast")
        print(json.dumps(result, indent=2))

    elif cmd == "start-local":
        print("Starting local mesh nodes...")
        procs = []
        base_ports = [(18789, 8893, 8894), (18790, 8895, 8896), (18791, 8897, 8898)]
        node_ids = ["local-alpha", "local-beta", "local-brain"]

        for (gw_port, brain_port, broker_port), node_id in zip(base_ports, node_ids):
            env = {
                **os.environ,
                "BRAIN_PORT": str(brain_port),
                "BROKER_PORT": str(broker_port),
                "BRAIN_ID": node_id,
                "MESH_PEERS": ",".join(
                    f"127.0.0.1:{p}"
                    for p in [b for _, b, _ in base_ports if b != brain_port]
                )
            }
            # Start brain
            p = subprocess.Popen(
                ["python3", "mesh/brain.py"],
                env=env,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )
            procs.append(p)
            print(f"  Started {node_id} brain on :{brain_port} (pid {p.pid})")

        print(f"\n✅ {len(procs)} local nodes started")
        print("Run: python mesh_orchestrator.py test-local")

    else:
        print(f"Unknown command: {cmd}")
        print("Usage: python mesh_orchestrator.py [test|test-local|status|prompt <query>|start-local]")

if __name__ == "__main__":
    asyncio.run(main())
