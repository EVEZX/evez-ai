#!/usr/bin/env python3
"""WebSocket mesh bus for coordinating multiple EvezBrain instances.

Features:
- Peer discovery + peer table gossip
- Pub/sub channels for memory graph updates, consciousness stream, and task splitting
- Leader election with automatic failover (bully-style consensus on node priority)
- Self-healing reconnect loop and heartbeat-based liveness checks

Run:
  python3 tools/evezbrain_mesh.py --node-id brain-a --port 8765 \
      --seed ws://127.0.0.1:8766
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import random
import signal
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, List, Optional, Set

import websockets
from websockets.exceptions import ConnectionClosed
from websockets.server import WebSocketServerProtocol

logger = logging.getLogger("evezbrain.mesh")

MEMORY_CHANNEL = "memory_graph.update"
CONSCIOUSNESS_CHANNEL = "consciousness.stream"
TASK_CHANNEL = "task.split"
SYSTEM_CHANNEL = "mesh.system"


@dataclass
class PeerState:
    node_id: str
    uri: str
    last_seen: float = field(default_factory=lambda: 0.0)
    priority: int = 1
    term: int = 0


class MeshNode:
    def __init__(
        self,
        node_id: str,
        host: str,
        port: int,
        seed_peers: Optional[List[str]] = None,
        priority: int = 1,
        heartbeat_interval: float = 1.5,
        peer_timeout: float = 6.0,
    ):
        self.node_id = node_id
        self.host = host
        self.port = port
        self.priority = priority
        self.heartbeat_interval = heartbeat_interval
        self.peer_timeout = peer_timeout

        self.uri = f"ws://{host}:{port}"
        self.server = None

        self.peer_index: Dict[str, PeerState] = {}
        self.seed_peers: Set[str] = set(seed_peers or [])
        self.outgoing: Dict[str, websockets.WebSocketClientProtocol] = {}
        self._conn_to_node: Dict[WebSocketServerProtocol, str] = {}

        self.subscribers: Dict[str, List[Callable[[Dict[str, Any]], Awaitable[None]]]] = defaultdict(list)
        self.pending_tasks: Dict[str, Dict[str, Any]] = {}

        self.term = 0
        self.leader_id: Optional[str] = None
        self.last_leader_seen = 0.0

        self._running = False

    def subscribe(self, channel: str, handler: Callable[[Dict[str, Any]], Awaitable[None]]) -> None:
        self.subscribers[channel].append(handler)

    async def publish(self, channel: str, payload: Dict[str, Any], *, fanout: bool = True) -> None:
        event = {
            "type": "pubsub",
            "channel": channel,
            "payload": payload,
            "from": self.node_id,
            "term": self.term,
            "ts": time.time(),
        }
        await self._dispatch_local(event)
        if fanout:
            await self._broadcast(event)

    async def start(self) -> None:
        self._running = True
        self.server = await websockets.serve(self._on_server_connection, self.host, self.port)
        logger.info("%s listening on %s", self.node_id, self.uri)

        for seed in sorted(self.seed_peers):
            if seed != self.uri:
                asyncio.create_task(self._connect_to_peer(seed))

        asyncio.create_task(self._heartbeat_loop())
        asyncio.create_task(self._discovery_loop())
        asyncio.create_task(self._leader_watchdog_loop())

    async def stop(self) -> None:
        self._running = False
        for ws in list(self.outgoing.values()):
            await ws.close()
        self.outgoing.clear()
        if self.server:
            self.server.close()
            await self.server.wait_closed()

    async def _on_server_connection(self, ws: WebSocketServerProtocol) -> None:
        try:
            hello = await asyncio.wait_for(ws.recv(), timeout=5)
            msg = json.loads(hello)
            if msg.get("type") != "hello":
                await ws.close(code=4001, reason="missing hello")
                return
            peer_id = msg["node_id"]
            peer_uri = msg["uri"]
            self._remember_peer(peer_id, peer_uri, msg.get("priority", 1), msg.get("term", 0))
            self._conn_to_node[ws] = peer_id
            await ws.send(json.dumps(self._hello_message()))
            await ws.send(json.dumps(self._peer_table_message()))

            async for raw in ws:
                await self._handle_message(ws, raw)
        except Exception as exc:  # noqa: BLE001
            logger.debug("server connection error: %s", exc)
        finally:
            peer_id = self._conn_to_node.pop(ws, None)
            if peer_id:
                logger.info("peer %s disconnected from %s", peer_id, self.node_id)

    async def _connect_to_peer(self, uri: str) -> None:
        backoff = 1.0
        while self._running:
            try:
                if uri == self.uri:
                    return
                ws = await websockets.connect(uri)
                await ws.send(json.dumps(self._hello_message()))
                self.outgoing[uri] = ws
                backoff = 1.0
                logger.info("%s connected to peer %s", self.node_id, uri)
                async for raw in ws:
                    await self._handle_message(ws, raw)
            except Exception as exc:  # noqa: BLE001
                logger.debug("%s connect error %s: %s", self.node_id, uri, exc)
            finally:
                old = self.outgoing.pop(uri, None)
                if old:
                    await old.close()
            await asyncio.sleep(backoff + random.random())
            backoff = min(backoff * 2, 10)

    async def _handle_message(self, ws: Any, raw: str) -> None:
        msg = json.loads(raw)
        mtype = msg.get("type")
        if mtype == "hello":
            self._remember_peer(msg["node_id"], msg["uri"], msg.get("priority", 1), msg.get("term", 0))
        elif mtype == "peer_table":
            for peer in msg.get("peers", []):
                self._remember_peer(
                    peer["node_id"],
                    peer["uri"],
                    peer.get("priority", 1),
                    peer.get("term", 0),
                    observed_at=peer.get("last_seen"),
                )
                if peer["uri"] != self.uri and peer["uri"] not in self.outgoing:
                    asyncio.create_task(self._connect_to_peer(peer["uri"]))
        elif mtype == "heartbeat":
            self._remember_peer(msg["node_id"], msg["uri"], msg.get("priority", 1), msg.get("term", 0))
            if msg.get("leader_id"):
                self.leader_id = msg["leader_id"]
                self.last_leader_seen = time.time()
        elif mtype == "election":
            await self._handle_election(msg)
        elif mtype == "leader_announce":
            self.term = max(self.term, int(msg.get("term", 0)))
            self.leader_id = msg.get("leader_id")
            self.last_leader_seen = time.time()
        elif mtype == "pubsub":
            await self._dispatch_local(msg)
            await self._relay(ws, raw, origin=msg.get("from"))
        elif mtype == "task_ack":
            task_id = msg.get("task_id")
            if task_id and task_id in self.pending_tasks:
                self.pending_tasks[task_id]["status"] = "accepted"
                self.pending_tasks[task_id]["assignee"] = msg.get("node_id")

    async def _dispatch_local(self, message: Dict[str, Any]) -> None:
        channel = message.get("channel")
        if not channel:
            return
        for handler in self.subscribers.get(channel, []):
            await handler(message)

    async def broadcast_memory_update(self, update: Dict[str, Any]) -> None:
        await self.publish(MEMORY_CHANNEL, update)

    async def broadcast_consciousness_event(self, event: Dict[str, Any]) -> None:
        await self.publish(CONSCIOUSNESS_CHANNEL, event)

    async def split_task(self, task: Dict[str, Any], shards: int) -> List[str]:
        task_ids: List[str] = []
        target_nodes = sorted([n for n in self.peer_index if n != self.node_id])
        if not target_nodes:
            await self.publish(TASK_CHANNEL, {"mode": "local", "task": task, "shard": 0, "shards": 1})
            return task_ids

        for idx in range(max(1, shards)):
            assignee = target_nodes[idx % len(target_nodes)]
            task_id = f"{self.node_id}-{int(time.time() * 1000)}-{idx}"
            payload = {
                "task_id": task_id,
                "assignee": assignee,
                "shard": idx,
                "shards": shards,
                "task": task,
            }
            self.pending_tasks[task_id] = {"status": "sent", "assignee": assignee, "payload": payload}
            await self.publish(TASK_CHANNEL, payload)
            task_ids.append(task_id)
        return task_ids

    async def _relay(self, ws: Any, raw: str, origin: Optional[str]) -> None:
        for uri, peer_ws in list(self.outgoing.items()):
            if peer_ws is ws:
                continue
            try:
                await peer_ws.send(raw)
            except ConnectionClosed:
                self.outgoing.pop(uri, None)
        # best-effort relay to inbound peers
        for inbound_ws in list(self._conn_to_node):
            if inbound_ws is ws:
                continue
            try:
                await inbound_ws.send(raw)
            except ConnectionClosed:
                self._conn_to_node.pop(inbound_ws, None)

    async def _broadcast(self, msg: Dict[str, Any]) -> None:
        raw = json.dumps(msg)
        for uri, ws in list(self.outgoing.items()):
            try:
                await ws.send(raw)
            except ConnectionClosed:
                self.outgoing.pop(uri, None)
        for ws in list(self._conn_to_node):
            try:
                await ws.send(raw)
            except ConnectionClosed:
                self._conn_to_node.pop(ws, None)

    async def _heartbeat_loop(self) -> None:
        while self._running:
            heartbeat = {
                "type": "heartbeat",
                "node_id": self.node_id,
                "uri": self.uri,
                "priority": self.priority,
                "term": self.term,
                "leader_id": self.leader_id,
                "ts": time.time(),
            }
            await self._broadcast(heartbeat)
            self._remember_peer(self.node_id, self.uri, self.priority, self.term)
            await asyncio.sleep(self.heartbeat_interval)

    async def _discovery_loop(self) -> None:
        while self._running:
            await self._broadcast(self._peer_table_message())
            await asyncio.sleep(max(2.0, self.heartbeat_interval * 2))

    async def _leader_watchdog_loop(self) -> None:
        await asyncio.sleep(1.0)
        while self._running:
            now = time.time()
            self._prune_dead_peers(now)
            leader_alive = self.leader_id in self.peer_index and now - self.last_leader_seen <= self.peer_timeout
            if not self.leader_id or not leader_alive:
                await self._start_election(reason="leader_timeout")
            await asyncio.sleep(self.heartbeat_interval)

    def _prune_dead_peers(self, now: float) -> None:
        for node_id, peer in list(self.peer_index.items()):
            if node_id == self.node_id:
                continue
            if now - peer.last_seen > self.peer_timeout:
                logger.warning("%s pruned stale peer %s", self.node_id, node_id)
                self.peer_index.pop(node_id, None)
                if self.leader_id == node_id:
                    self.leader_id = None

    async def _start_election(self, reason: str) -> None:
        self.term += 1
        candidates = [(self.priority, self.node_id)]
        for peer in self.peer_index.values():
            candidates.append((peer.priority, peer.node_id))
        winner = sorted(candidates, key=lambda it: (it[0], it[1]), reverse=True)[0][1]
        election = {
            "type": "election",
            "term": self.term,
            "candidate": self.node_id,
            "reason": reason,
            "priority": self.priority,
        }
        await self._broadcast(election)
        if winner == self.node_id:
            await self._assume_leadership()

    async def _handle_election(self, msg: Dict[str, Any]) -> None:
        incoming_term = int(msg.get("term", 0))
        self.term = max(self.term, incoming_term)
        candidate = msg.get("candidate")
        candidate_peer = self.peer_index.get(candidate)
        candidate_priority = msg.get("priority", candidate_peer.priority if candidate_peer else 1)

        if self.priority > int(candidate_priority) or (
            self.priority == int(candidate_priority) and self.node_id > str(candidate)
        ):
            await self._assume_leadership()

    async def _assume_leadership(self) -> None:
        self.leader_id = self.node_id
        self.last_leader_seen = time.time()
        announce = {"type": "leader_announce", "leader_id": self.node_id, "term": self.term, "ts": self.last_leader_seen}
        await self._broadcast(announce)
        logger.info("%s became leader for term %s", self.node_id, self.term)

    def _remember_peer(
        self,
        node_id: str,
        uri: str,
        priority: int,
        term: int,
        observed_at: Optional[float] = None,
    ) -> None:
        peer = self.peer_index.get(node_id) or PeerState(node_id=node_id, uri=uri)
        peer.uri = uri
        peer.priority = int(priority)
        peer.term = max(peer.term, int(term))
        seen = float(observed_at) if observed_at is not None else time.time()
        if node_id != self.node_id and time.time() - seen > self.peer_timeout * 2:
            return
        peer.last_seen = seen
        self.peer_index[node_id] = peer

    def _hello_message(self) -> Dict[str, Any]:
        return {
            "type": "hello",
            "node_id": self.node_id,
            "uri": self.uri,
            "priority": self.priority,
            "term": self.term,
            "channels": [MEMORY_CHANNEL, CONSCIOUSNESS_CHANNEL, TASK_CHANNEL, SYSTEM_CHANNEL],
        }

    def _peer_table_message(self) -> Dict[str, Any]:
        peers = [
            {
                "node_id": p.node_id,
                "uri": p.uri,
                "priority": p.priority,
                "term": p.term,
                "last_seen": p.last_seen,
            }
            for p in self.peer_index.values()
        ]
        return {"type": "peer_table", "from": self.node_id, "peers": peers}


async def _demo_logger(message: Dict[str, Any]) -> None:
    logger.info("event channel=%s from=%s payload=%s", message.get("channel"), message.get("from"), message.get("payload"))


async def run_node(args: argparse.Namespace) -> None:
    node = MeshNode(
        node_id=args.node_id,
        host=args.host,
        port=args.port,
        seed_peers=args.seed,
        priority=args.priority,
        heartbeat_interval=args.heartbeat,
        peer_timeout=args.peer_timeout,
    )
    node.subscribe(MEMORY_CHANNEL, _demo_logger)
    node.subscribe(CONSCIOUSNESS_CHANNEL, _demo_logger)

    async def _task_worker(message: Dict[str, Any]) -> None:
        payload = message.get("payload", {})
        if payload.get("assignee") == node.node_id:
            logger.info("%s accepted shard %s/%s", node.node_id, payload.get("shard"), payload.get("shards"))
            ack = {"type": "task_ack", "task_id": payload.get("task_id"), "node_id": node.node_id}
            await node._broadcast(ack)

    node.subscribe(TASK_CHANNEL, _task_worker)
    await node.start()

    if args.emit_demo:
        await asyncio.sleep(2)
        await node.broadcast_memory_update({"memory_id": "m-1", "op": "merge", "edges": 3})
        await node.broadcast_consciousness_event({"stream": "focus", "token": "stability"})
        await node.split_task({"objective": "parallel probe"}, shards=3)

    stop_event = asyncio.Event()

    def _shutdown(*_: Any) -> None:
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _shutdown)
        except NotImplementedError:
            pass

    await stop_event.wait()
    await node.stop()


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run an EvezBrain mesh node")
    p.add_argument("--node-id", required=True)
    p.add_argument("--host", default="0.0.0.0")
    p.add_argument("--port", type=int, required=True)
    p.add_argument("--seed", action="append", default=[], help="Peer URI, e.g. ws://127.0.0.1:8765")
    p.add_argument("--priority", type=int, default=1, help="Election priority (higher wins)")
    p.add_argument("--heartbeat", type=float, default=1.5)
    p.add_argument("--peer-timeout", type=float, default=6.0)
    p.add_argument("--emit-demo", action="store_true")
    p.add_argument("--log-level", default="INFO")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO), format="%(asctime)s %(levelname)s %(message)s")
    try:
        asyncio.run(run_node(args))
    except KeyboardInterrupt:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
