"""
Autoenveloper FastAPI server — HTTP interface for the autonomous agent
"""
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
import asyncio, json, time
from main import Autoenveloper

app = FastAPI(title="EVEZ Autoenveloper", version="1.0.0")
agents: dict = {}

class TaskRequest(BaseModel):
    task: str
    model: str = "smart"
    max_steps: int = 10

@app.get("/health")
def health():
    return {"status": "ok", "agents": len(agents), "ts": int(time.time())}

@app.post("/run")
async def run_task(req: TaskRequest):
    agent = Autoenveloper(model=req.model)
    result = await agent.run(req.task, max_steps=req.max_steps)
    agents[result["session"]] = result
    return result

@app.post("/run/async")  
async def run_async(req: TaskRequest, background_tasks: BackgroundTasks):
    session_id = f"task_{int(time.time())}"
    agents[session_id] = {"status": "running", "task": req.task}
    
    async def _run():
        agent = Autoenveloper(model=req.model)
        result = await agent.run(req.task, req.max_steps)
        agents[session_id] = {"status": "complete", **result}
    
    background_tasks.add_task(_run)
    return {"session_id": session_id, "status": "started"}

@app.get("/status/{session_id}")
def status(session_id: str):
    return agents.get(session_id, {"error": "not found"})

@app.get("/list")
def list_tasks():
    return {"tasks": list(agents.keys()), "count": len(agents)}
