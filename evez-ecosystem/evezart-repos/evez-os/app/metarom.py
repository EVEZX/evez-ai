"""WF-04 — metarom: FastAPI memory API backed by PostgreSQL + pgvector"""
import os, json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import asyncpg
from datetime import datetime, timezone

app = FastAPI(title="metarom", version="1.0.0")

_pool = None

@app.on_event("startup")
async def startup():
    global _pool
    _pool = await asyncpg.create_pool(os.environ["DATABASE_URL"], min_size=2, max_size=10)
    async with _pool.acquire() as conn:
        await conn.execute("""
            CREATE EXTENSION IF NOT EXISTS vector;
            CREATE TABLE IF NOT EXISTS memories (
                id        SERIAL PRIMARY KEY,
                agent_id  TEXT NOT NULL,
                event_type TEXT NOT NULL,
                content   JSONB NOT NULL,
                embedding vector(384),
                created_at TIMESTAMPTZ DEFAULT now()
            );
            CREATE TABLE IF NOT EXISTS agent_prompts (
                agent_id          TEXT PRIMARY KEY,
                prompt_version    INT  DEFAULT 1,
                system_prompt     TEXT NOT NULL,
                prev_system_prompt TEXT,
                updated_at        TIMESTAMPTZ DEFAULT now()
            );
        """)

class MemoryWrite(BaseModel):
    agent_id: str
    event_type: str
    content: dict
    embedding: Optional[List[float]] = None

class MemorySearch(BaseModel):
    query_embedding: List[float]
    top_k: int = 5

class PromptUpdate(BaseModel):
    agent_id: str
    system_prompt: str

@app.post("/memory/write")
async def memory_write(body: MemoryWrite):
    async with _pool.acquire() as conn:
        if body.embedding:
            await conn.execute(
                "INSERT INTO memories (agent_id, event_type, content, embedding) "
                "VALUES ($1,$2,$3,$4::vector)",
                body.agent_id, body.event_type, json.dumps(body.content), str(body.embedding),
            )
        else:
            await conn.execute(
                "INSERT INTO memories (agent_id, event_type, content) VALUES ($1,$2,$3)",
                body.agent_id, body.event_type, json.dumps(body.content),
            )
    return {"status": "written"}

@app.post("/memory/search")
async def memory_search(body: MemorySearch):
    async with _pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT agent_id, event_type, content, created_at FROM memories "
            "WHERE embedding IS NOT NULL "
            "ORDER BY embedding <=> $1::vector LIMIT $2",
            str(body.query_embedding), body.top_k,
        )
    return [
        {"agent_id": r["agent_id"], "event_type": r["event_type"],
         "content": r["content"], "created_at": str(r["created_at"])}
        for r in rows
    ]

@app.post("/prompt/update")
async def prompt_update(body: PromptUpdate):
    async with _pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO agent_prompts (agent_id, system_prompt)
            VALUES ($1, $2)
            ON CONFLICT (agent_id) DO UPDATE
            SET prev_system_prompt = agent_prompts.system_prompt,
                system_prompt      = EXCLUDED.system_prompt,
                prompt_version     = agent_prompts.prompt_version + 1,
                updated_at         = now()
        """, body.agent_id, body.system_prompt)
    return {"status": "updated"}

@app.post("/prompt/rollback/{agent_id}")
async def prompt_rollback(agent_id: str):
    async with _pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT prev_system_prompt FROM agent_prompts WHERE agent_id=$1", agent_id
        )
        if not row or not row["prev_system_prompt"]:
            raise HTTPException(404, detail="No previous prompt available")
        await conn.execute(
            "UPDATE agent_prompts SET system_prompt=prev_system_prompt, updated_at=now() "
            "WHERE agent_id=$1", agent_id
        )
    return {"status": "rolled_back"}

@app.get("/prompt/{agent_id}")
async def prompt_get(agent_id: str):
    async with _pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT system_prompt, prompt_version FROM agent_prompts WHERE agent_id=$1", agent_id
        )
    if not row:
        raise HTTPException(404, detail="Agent not found")
    return {"system_prompt": row["system_prompt"], "version": row["prompt_version"]}

@app.get("/health")
async def health():
    return {"status": "ok", "ts": datetime.now(timezone.utc).isoformat()}
