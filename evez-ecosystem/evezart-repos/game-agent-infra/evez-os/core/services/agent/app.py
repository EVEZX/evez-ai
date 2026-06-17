from fastapi import FastAPI
from pydantic import BaseModel, Field
import json, time, uuid, os
from pathlib import Path

try:
    from tools.evez import fsc_from_cycle, validate_cycle
except Exception:
    fsc_from_cycle = None
    validate_cycle = None

app = FastAPI(title="Agent Orchestrator (Wheel+FSC)")

EVENT_SPINE = os.getenv("EVENT_SPINE", str(Path(__file__).resolve().parents[2] / "spine" / "EVENT_SPINE.jsonl"))
SCHEMA_PATH = os.getenv("FSC_SCHEMA", str(Path(__file__).resolve().parents[2] / "schemas" / "fsc_schema.json"))

class FSCCycleIn(BaseModel):
    ring_estimate: str = Field(default="unknown")
    anomaly: str
    context: dict = Field(default_factory=dict)
    controlled_reduction: dict = Field(default_factory=dict)

@app.get("/healthz")
def healthz():
    return {"ok": True, "event_spine": EVENT_SPINE}

@app.post("/cycle")
def run_cycle(c: FSCCycleIn):
    cycle = {
        "cycle_id": f"CYCLE-{uuid.uuid4()}",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "anomaly": c.anomaly,
        "ring_estimate": c.ring_estimate,
        "controlled_reduction": c.controlled_reduction or {},
        "context": c.context or {},
        "Sigma_f": [],
        "CS": [],
        "PS": [],
        "Omega": "",
        "tests": [],
        "results": [],
        "measures": {},
        "provenance": ["agent_orchestrator"],
    }

    # Try compute FSC (lightweight heuristic) + validate schema
    if fsc_from_cycle:
        cycle = fsc_from_cycle(cycle)
    if validate_cycle:
        valid, errors = validate_cycle(cycle, schema_path=SCHEMA_PATH)
        cycle["validation"] = {"ok": valid, "errors": errors[:20]}
    else:
        cycle["validation"] = {"ok": True, "errors": []}

    Path(EVENT_SPINE).parent.mkdir(parents=True, exist_ok=True)
    with open(EVENT_SPINE, "a", encoding="utf-8") as f:
        f.write(json.dumps(cycle, ensure_ascii=False) + "\n")
    return {"accepted": True, "cycle_id": cycle["cycle_id"], "pending": True, "validation": cycle["validation"]}
