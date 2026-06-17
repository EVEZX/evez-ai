from __future__ import annotations

import asyncio
import json
import time

import websockets


async def main() -> None:
    payload = {
        "type": "fusion-update",
        "detail": {
            "meta": {
                "recursionLevel": 10,
                "entityType": "hybrid",
                "timestamp": time.time() * 1000,
            },
            "crystallization": {
                "progress": 55,
                "velocity": 0.0,
            },
            "corrections": {
                "current": 12345.67,
                "history": [100.0, 250.0, 1000.0, 12345.67],
            },
        },
    }

    async with websockets.connect("ws://127.0.0.1:8765") as websocket:
        await websocket.send(json.dumps(payload))
        print("sent fusion-update payload to ws://127.0.0.1:8765")


if __name__ == "__main__":
    asyncio.run(main())
