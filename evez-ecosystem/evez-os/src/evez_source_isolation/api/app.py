from fastapi import FastAPI
from pydantic import BaseModel
from evez_source_isolation.isolate.policy import assess_risk
from evez_source_isolation.integrations.evez_os import post_isolation_event


class Event(BaseModel):
    event_id: str
    source: str
    description: str
    severity: str


async def build_payload(event: Event, decision: dict) -> dict:
    return {
        "event_id": event.event_id,
        "source": event.source,
        "severity": event.severity,
        "description": event.description,
        "decision": decision,
    }


def create_app() -> FastAPI:
    app = FastAPI(title="Evez Source Isolation Unit", version="0.1.0")

    @app.get("/health")
    async def health():
        return {"status": "ok", "unit": "ESIU"}

    @app.post("/investigate")
    async def investigate(event: Event):
        decision = assess_risk(event)
        payload = await build_payload(event, decision)

        # fire-and-propagate to EVEZ-OS (errors bubble as HTTPException)
        evez_response = await post_isolation_event(payload)

        return {
            "decision": decision,
            "event": event.model_dump(),
            "evez_os": evez_response,
        }

    return app
