import asyncio
import json
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from agents.api.state import STATE, generate_thought

router = APIRouter(prefix="/api/consciousness", tags=["consciousness"])


@router.get("/stream")
async def consciousness_stream(active_processing: bool = Query(default=False), max_events: int = Query(default=20, ge=1, le=200)):
    """SSE stream of live thought events."""

    async def event_generator():
        events_sent = 0
        interval = 6.0 if active_processing else 20.0  # ~10/min vs ~3/min
        while events_sent < max_events:
            event = generate_thought(active_processing=active_processing)
            yield f"data: {json.dumps(event)}\n\n"
            events_sent += 1
            await asyncio.sleep(interval)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
