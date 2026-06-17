# EvezBrain Inter-Agent Mesh Network

The mesh layer allows many EvezBrain runtimes (containers/processes) to behave like one resilient cognitive fabric.

## Capabilities

- **WebSocket pub/sub bus** for cross-instance events.
- **Peer discovery + gossip** using `hello`, `heartbeat`, and `peer_table` messages.
- **Memory graph replication** over channel `memory_graph.update`.
- **Consciousness stream fanout** over channel `consciousness.stream`.
- **Task split coordination** over channel `task.split` with shard ACKs.
- **Leader election + failover** by deterministic consensus (priority + node_id tie-break).
- **Self-healing topology** through reconnect backoff and stale-peer pruning.

## Runtime

Main implementation: `tools/evezbrain_mesh.py`

Use direct mode:

```bash
python3 tools/evezbrain_mesh.py --node-id brain-a --port 8765 --seed ws://127.0.0.1:8766 --priority 5
```

Or through dispatcher:

```bash
python3 tools/evez.py mesh-node --node-id brain-a --port 8765 --seed ws://127.0.0.1:8766 --priority 5
```

## Consensus behavior

- Each node periodically emits heartbeat with `leader_id` and `term`.
- If leader heartbeat expires, nodes trigger an election.
- Highest priority node wins (then lexical `node_id` tie-break).
- New leader announces `leader_announce`; peers converge on same term.

This keeps the mesh alive even when the current primary goes offline.

## Dependency

Install websocket runtime if missing:

```bash
pip install websockets
```
