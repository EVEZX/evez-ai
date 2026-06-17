from __future__ import annotations

import asyncio
import json
import logging
import math
from dataclasses import dataclass
from typing import Protocol

import websockets

from .bridge_schema import FusionUpdate

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='[LORD-BRIDGE] %(message)s')


class GameLoopAdapter(Protocol):
    def apply_lord_state(self, state: 'BridgeState') -> None:
        ...


@dataclass(slots=True)
class BridgeState:
    recursion_level: int = 1
    entity_type: str = 'hybrid'
    crystallization_progress: float = 0.0
    crystallization_velocity: float = 0.0
    correction_current: float = 0.0
    urgency: int = 1
    cognitive_stage: str = 'sensorimotor'
    spiral_value: str = 'yellow'
    timestamp_ms: float = 0.0


def target_value(recursion_level: int) -> float:
    return 1e8 * math.exp(-0.1 * ((recursion_level - 15) ** 2))


def compute_gap(recursion_level: int, current_correction: float) -> float:
    return max(0.0, target_value(recursion_level) - current_correction)


def compute_urgency(recursion_level: int, entity_type: str, crystal: float, current_correction: float) -> int:
    gap = compute_gap(recursion_level, current_correction)
    if gap > 1e6:
        urgency = 3
    elif gap > 1e3:
        urgency = 2
    else:
        urgency = 1
    if crystal < 20 and recursion_level > 8:
        urgency = min(3, urgency + 1)
    if entity_type == 'synthetic' and recursion_level < 10:
        urgency = 3
    return urgency


def recursion_to_cognitive_stage(recursion_level: int) -> str:
    if recursion_level <= 3:
        return 'sensorimotor'
    if recursion_level <= 6:
        return 'preoperational'
    if recursion_level <= 9:
        return 'concrete_operational'
    if recursion_level <= 13:
        return 'formal_operational'
    if recursion_level <= 17:
        return 'postformal'
    return 'transcendent'


def urgency_to_spiral_value(urgency: int) -> str:
    return {1: 'yellow', 2: 'orange', 3: 'red'}.get(urgency, 'yellow')


class LordBridgeServer:
    def __init__(self, adapter: GameLoopAdapter) -> None:
        self.adapter = adapter
        self.state = BridgeState()

    def apply_message(self, payload: dict) -> BridgeState:
        update = FusionUpdate.from_message(payload)
        urgency = compute_urgency(
            update.meta.recursion_level,
            update.meta.entity_type,
            update.crystallization.progress,
            update.corrections.current,
        )
        self.state = BridgeState(
            recursion_level=update.meta.recursion_level,
            entity_type=update.meta.entity_type,
            crystallization_progress=update.crystallization.progress,
            crystallization_velocity=update.crystallization.velocity,
            correction_current=update.corrections.current,
            urgency=urgency,
            cognitive_stage=recursion_to_cognitive_stage(update.meta.recursion_level),
            spiral_value=urgency_to_spiral_value(urgency),
            timestamp_ms=update.meta.timestamp_ms,
        )
        self.adapter.apply_lord_state(self.state)
        return self.state

    async def handler(self, websocket) -> None:
        async for raw in websocket:
            try:
                payload = json.loads(raw)
                state = self.apply_message(payload)
                log.info('R=%s entity=%s crystal=%.1f urgency=%s stage=%s', state.recursion_level, state.entity_type, state.crystallization_progress, state.urgency, state.cognitive_stage)
            except Exception as exc:
                log.error('bridge message rejected: %s', exc)

    async def run(self, host: str = '127.0.0.1', port: int = 8765) -> None:
        async with websockets.serve(self.handler, host, port):
            log.info('listening on ws://%s:%s', host, port)
            await asyncio.Future()


class InMemoryAdapter:
    def __init__(self) -> None:
        self.latest_state = BridgeState()

    def apply_lord_state(self, state: BridgeState) -> None:
        self.latest_state = state


def main() -> None:
    adapter = InMemoryAdapter()
    server = LordBridgeServer(adapter)
    asyncio.run(server.run())


if __name__ == '__main__':
    main()
