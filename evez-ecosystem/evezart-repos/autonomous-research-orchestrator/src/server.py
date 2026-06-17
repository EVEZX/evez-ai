"""ARO FastAPI Server | EVEZ Station"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from aro import AutonomousResearchOrchestrator

app = FastAPI(title="Autonomous Research Orchestrator", version="1.0.0", docs_url="/docs")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
orchestrator = AutonomousResearchOrchestrator(supabase_url=os.getenv("SUPABASE_URL"), supabase_key=os.getenv("SUPABASE_SERVICE_ROLE_KEY"))

class CreateSessionRequest(BaseModel):
    title: str; methodology: str = "multi-stream"; depth: int = 4; stream_types: Optional[List[str]] = None
class ExecuteResearchRequest(BaseModel):
    session_id: str; research_input: str; n_scale: float = 15.5

@app.get("/health")
@app.get("/api/aro/health")
async def health(): return orchestrator.health()

@app.post("/api/aro/session", status_code=201)
async def create_session(req: CreateSessionRequest):
    s = orchestrator.create_session(req.title, req.methodology, req.stream_types, req.depth)
    return {"session_id": s["id"], "title": s["title"], "omega_estimate": round(s["omega_estimate"],2), "streams": [st.stream_type.value for st in s["streams"]], "status": s["status"]}

@app.get("/api/aro/session/{session_id}")
async def get_session(session_id: str):
    s = orchestrator.sessions.get(session_id)
    if not s: raise HTTPException(404, "Session not found")
    syn = s.get("synthesis")
    return {"id": s["id"], "title": s["title"], "status": s["status"], "omega_estimate": round(s.get("omega_estimate",0),2), "synthesis": syn.to_dict() if hasattr(syn,"to_dict") else syn}

@app.get("/api/aro/sessions")
async def list_sessions(): return {"sessions": [{"id":s["id"],"title":s["title"],"status":s["status"]} for s in orchestrator.sessions.values()], "total": len(orchestrator.sessions)}

@app.post("/api/aro/execute")
async def execute_research(req: ExecuteResearchRequest):
    try: return orchestrator.execute_research(req.session_id, req.research_input, req.n_scale)
    except ValueError as e: raise HTTPException(404, str(e))

@app.get("/.well-known/ai-plugin.json")
async def ai_plugin(): return {"schema_version": "v1", "name_for_human": "ARO", "name_for_model": "aro", "description_for_model": "POST /api/aro/session to start, POST /api/aro/execute to run, GET /api/aro/session/{id} for results.", "auth": {"type": "none"}, "api": {"type": "openapi", "url": "/.well-known/openapi.json"}, "contact_email": "evezproductions@gmail.com"}

@app.get("/.well-known/openapi.json")
async def openapi_discovery(): return app.openapi()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
