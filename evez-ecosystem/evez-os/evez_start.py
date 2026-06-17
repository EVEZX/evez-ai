#!/usr/bin/env python3
"""EvezBrain unified orchestrator boot sequence.

Boot order:
1) immortality watchdog
2) mesh network
3) synaptic memory graph
4) reward loop
5) emotion core
6) consciousness API
7) self-mutation engine
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import json
import signal
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Awaitable, Callable, Deque, Dict, List


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


Subscriber = Callable[[dict[str, Any]], Awaitable[None]]


class EventBus:
    def __init__(self, max_events: int = 500) -> None:
        self._subscribers: Dict[str, List[Subscriber]] = defaultdict(list)
        self._wildcards: List[Subscriber] = []
        self._events: Deque[dict[str, Any]] = deque(maxlen=max_events)

    def subscribe(self, topic: str, callback: Subscriber) -> None:
        if topic == "*":
            self._wildcards.append(callback)
            return
        self._subscribers[topic].append(callback)

    async def publish(self, topic: str, payload: dict[str, Any]) -> None:
        event = {"topic": topic, "payload": payload, "ts": utc_now()}
        self._events.append(event)
        for callback in [*self._subscribers.get(topic, []), *self._wildcards]:
            await callback(event)

    def recent_events(self, limit: int = 50) -> list[dict[str, Any]]:
        return list(self._events)[-limit:]


@dataclass
class Subsystem:
    name: str
    status: str = "pending"
    started_at: str | None = None
    heartbeat_at: str | None = None
    details: dict[str, Any] = field(default_factory=dict)

    async def start(self, orchestrator: "EvezBrainOrchestrator") -> None:
        self.status = "running"
        self.started_at = utc_now()
        self.heartbeat_at = self.started_at
        await orchestrator.bus.publish(
            "subsystem.started", {"name": self.name, "details": self.details}
        )

    async def heartbeat(self, orchestrator: "EvezBrainOrchestrator") -> None:
        self.heartbeat_at = utc_now()
        await orchestrator.bus.publish(
            "subsystem.heartbeat", {"name": self.name, "heartbeat_at": self.heartbeat_at}
        )


class ImmortalityWatchdog(Subsystem):
    def __init__(self) -> None:
        super().__init__(name="immortality_watchdog", details={"policy": "self-heal"})


class MeshNetwork(Subsystem):
    def __init__(self) -> None:
        super().__init__(name="mesh_network", details={"mode": "peer-discovery"})

    async def start(self, orchestrator: "EvezBrainOrchestrator") -> None:
        await super().start(orchestrator)
        if orchestrator.first_boot:
            node_id = orchestrator.state.setdefault("node_id", f"evez-{int(time.time())}")
            orchestrator.state["registered_at"] = utc_now()
            await orchestrator.persist_state()
            await orchestrator.bus.publish(
                "mesh.registered", {"node_id": node_id, "registered_at": orchestrator.state["registered_at"]}
            )


class SynapticMemoryGraph(Subsystem):
    def __init__(self) -> None:
        super().__init__(name="synaptic_memory_graph", details={"edges": 0, "nodes": 0})


class RewardLoop(Subsystem):
    def __init__(self) -> None:
        super().__init__(name="reward_loop", details={"reward_score": 0.0})


class EmotionCore(Subsystem):
    def __init__(self) -> None:
        super().__init__(name="emotion_core", details={"mood": "curious"})


class ConsciousnessAPI(Subsystem):
    def __init__(self) -> None:
        super().__init__(name="consciousness_api", details={"dreaming": False, "dreams": 0})


class SelfMutationEngine(Subsystem):
    def __init__(self) -> None:
        super().__init__(name="self_mutation_engine", details={"mutations": 0})


class DashboardServer(threading.Thread):
    def __init__(self, host: str, port: int, orchestrator: "EvezBrainOrchestrator") -> None:
        super().__init__(daemon=True)
        self._host = host
        self._port = port
        self._orchestrator = orchestrator
        self._server: ThreadingHTTPServer | None = None

    def run(self) -> None:
        orchestrator = self._orchestrator

        class Handler(BaseHTTPRequestHandler):
            def _json(self, payload: dict[str, Any], status: int = 200) -> None:
                body = json.dumps(payload, indent=2).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self) -> None:  # noqa: N802
                if self.path == "/health":
                    self._json({"ok": True, "booted": orchestrator.boot_completed})
                    return
                if self.path.startswith("/events"):
                    self._json({"events": orchestrator.bus.recent_events(100)})
                    return
                if self.path.startswith("/status") or self.path == "/":
                    self._json(orchestrator.snapshot())
                    return
                self._json({"error": "not found"}, status=404)

            def log_message(self, format: str, *args: Any) -> None:  # silence
                return

        self._server = ThreadingHTTPServer((self._host, self._port), Handler)
        self._server.serve_forever(poll_interval=0.5)

    def shutdown(self) -> None:
        if self._server:
            self._server.shutdown()


class EvezBrainOrchestrator:
    BOOT_ORDER = [
        ImmortalityWatchdog,
        MeshNetwork,
        SynapticMemoryGraph,
        RewardLoop,
        EmotionCore,
        ConsciousnessAPI,
        SelfMutationEngine,
    ]

    def __init__(self, host: str, port: int, state_file: str = ".evez_brain_boot.json") -> None:
        self.bus = EventBus()
        self.state_path = Path(state_file)
        self.state = self._load_state()
        self.first_boot = not self.state.get("booted", False)
        self.boot_completed = False
        self.subsystems: dict[str, Subsystem] = {}
        self.start_time = utc_now()
        self.dashboard = DashboardServer(host, port, self)
        self._dream_task: asyncio.Task[None] | None = None
        self._heartbeat_task: asyncio.Task[None] | None = None
        self._cli_task: asyncio.Task[None] | None = None
        self._shutdown_event = asyncio.Event()

    def _load_state(self) -> dict[str, Any]:
        if self.state_path.exists():
            return json.loads(self.state_path.read_text(encoding="utf-8"))
        return {"boot_count": 0}

    async def persist_state(self) -> None:
        self.state_path.write_text(json.dumps(self.state, indent=2), encoding="utf-8")

    def snapshot(self) -> dict[str, Any]:
        return {
            "evezbrain": {
                "start_time": self.start_time,
                "boot_completed": self.boot_completed,
                "first_boot": self.first_boot,
                "boot_count": self.state.get("boot_count", 0),
                "node_id": self.state.get("node_id"),
            },
            "subsystems": {
                name: {
                    "status": s.status,
                    "started_at": s.started_at,
                    "heartbeat_at": s.heartbeat_at,
                    "details": s.details,
                }
                for name, s in self.subsystems.items()
            },
            "recent_events": self.bus.recent_events(15),
        }

    async def _wire_modules(self) -> None:
        async def reward_listener(event: dict[str, Any]) -> None:
            reward = self.subsystems["reward_loop"]
            reward.details["reward_score"] = round(float(reward.details["reward_score"]) + 0.5, 2)

        async def emotion_listener(event: dict[str, Any]) -> None:
            emotion = self.subsystems["emotion_core"]
            emotion.details["mood"] = "inspired" if event["topic"] == "dream.tick" else "focused"

        async def mutation_listener(event: dict[str, Any]) -> None:
            mutator = self.subsystems["self_mutation_engine"]
            mutator.details["mutations"] += 1

        self.bus.subscribe("dream.tick", reward_listener)
        self.bus.subscribe("dream.tick", emotion_listener)
        self.bus.subscribe("reward.updated", mutation_listener)

    async def _heartbeat_loop(self) -> None:
        while not self._shutdown_event.is_set():
            await asyncio.sleep(2)
            for subsystem in self.subsystems.values():
                if subsystem.status == "running":
                    await subsystem.heartbeat(self)

    async def _dream_loop(self) -> None:
        consciousness = self.subsystems["consciousness_api"]
        consciousness.details["dreaming"] = True
        while not self._shutdown_event.is_set():
            await asyncio.sleep(3)
            consciousness.details["dreams"] += 1
            dream_payload = {
                "dream_index": consciousness.details["dreams"],
                "symbol": "phoenix",
            }
            await self.bus.publish("dream.tick", dream_payload)
            await self.bus.publish(
                "reward.updated", {"source": "dream.tick", "score": self.subsystems["reward_loop"].details["reward_score"]}
            )

    async def _cli_dashboard_loop(self) -> None:
        while not self._shutdown_event.is_set():
            await asyncio.sleep(2)
            data = self.snapshot()
            print("\n=== EvezBrain Unified Status Dashboard ===")
            print(
                f"boot_completed={data['evezbrain']['boot_completed']} first_boot={data['evezbrain']['first_boot']} "
                f"node_id={data['evezbrain']['node_id']}"
            )
            for name, info in data["subsystems"].items():
                print(
                    f"- {name:22} status={info['status']:8} heartbeat={info['heartbeat_at']} details={info['details']}"
                )

    async def boot(self) -> None:
        await self._wire_modules()
        self.dashboard.start()

        for subsystem_type in self.BOOT_ORDER:
            subsystem = subsystem_type()
            self.subsystems[subsystem.name] = subsystem
            await subsystem.start(self)

        self.boot_completed = True
        self.state["booted"] = True
        self.state["boot_count"] = int(self.state.get("boot_count", 0)) + 1
        self.state["last_boot_at"] = utc_now()
        await self.persist_state()
        await self.bus.publish("evez.boot.completed", {"boot_count": self.state["boot_count"]})

        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        self._dream_task = asyncio.create_task(self._dream_loop())
        self._cli_task = asyncio.create_task(self._cli_dashboard_loop())

    async def shutdown(self) -> None:
        self._shutdown_event.set()
        for task in [self._dream_task, self._heartbeat_task, self._cli_task]:
            if task:
                task.cancel()
        self.dashboard.shutdown()
        await self.bus.publish("evez.shutdown", {"ts": utc_now()})


async def run(host: str, port: int, run_for: int | None) -> None:
    orchestrator = EvezBrainOrchestrator(host=host, port=port)
    await orchestrator.boot()

    loop = asyncio.get_running_loop()

    def _request_shutdown() -> None:
        orchestrator._shutdown_event.set()

    for sig in (signal.SIGTERM, signal.SIGINT):
        with contextlib.suppress(NotImplementedError):
            loop.add_signal_handler(sig, _request_shutdown)

    try:
        if run_for is not None:
            await asyncio.wait_for(orchestrator._shutdown_event.wait(), timeout=run_for)
        else:
            await orchestrator._shutdown_event.wait()
    except asyncio.TimeoutError:
        pass
    finally:
        await orchestrator.shutdown()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Boot the EvezBrain unified orchestrator")
    parser.add_argument("--host", default="127.0.0.1", help="HTTP dashboard bind host")
    parser.add_argument("--port", type=int, default=8877, help="HTTP dashboard bind port")
    parser.add_argument(
        "--run-for",
        type=int,
        default=None,
        help="Optional runtime in seconds (useful for smoke tests)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    asyncio.run(run(host=args.host, port=args.port, run_for=args.run_for))


if __name__ == "__main__":
    main()
