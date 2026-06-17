"""WF-04 — Metarom: Persistent Vector Memory (FastAPI + PostgreSQL + pgvector).

Routes:
  POST /memory/write   — agents write on task completion
  GET  /memory/read    — agents read context before starting
  POST /memory/search  — cosine similarity top-5 lookup

Env:  DATABASE_URL (postgres://...)
"""
import os, time, json, logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/memory", tags=["metarom"])
log = logging.getLogger("metarom")

DATABASE_URL = os.environ.get("DATABASE_URL", "")


def _get_conn():
    import psycopg2
    return psycopg2.connect(DATABASE_URL)


def _ensure_table():
    if not DATABASE_URL: return
    try:
        with _get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS memory (
                        id          SERIAL PRIMARY KEY,
                        agent_id    VARCHAR(128),
                        key         VARCHAR(256),
                        value       TEXT,
                        embedding   vector(1536),
                        tags        TEXT,
                        ts          FLOAT
                    );
                """)
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS memory_embedding_idx
                    ON memory USING ivfflat (embedding vector_cosine_ops)
                    WITH (lists = 100);
                """)
            conn.commit()
    except Exception as e:
        log.warning(f"metarom table init failed: {e}")


_ensure_table()


def _embed(text: str) -> list:
    """Generate embedding via Groq or return zeros if unavailable."""
    try:
        import httpx
        r = httpx.post(
            "https://api.groq.com/openai/v1/embeddings",
            headers={"Authorization": f"Bearer {os.environ.get('GROQ_API_KEY','')}"},
            json={"model": "text-embedding-ada-002", "input": text},
            timeout=15
        )
        return r.json()["data"][0]["embedding"]
    except Exception:
        return [0.0] * 1536


class MemoryWriteRequest(BaseModel):
    agent_id:  str
    key:       str
    value:     str
    tags:      Optional[str] = ""


class MemorySearchRequest(BaseModel):
    query:  str
    top_k:  Optional[int] = 5


@router.post("/write")
def memory_write(req: MemoryWriteRequest):
    if not DATABASE_URL:
        return {"ok": False, "reason": "DATABASE_URL not set"}
    emb = _embed(req.value)
    try:
        with _get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO memory (agent_id, key, value, embedding, tags, ts) "
                    "VALUES (%s, %s, %s, %s::vector, %s, %s)",
                    (req.agent_id, req.key, req.value,
                     str(emb), req.tags, time.time())
                )
            conn.commit()
        return {"ok": True, "agent_id": req.agent_id, "key": req.key}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/read")
def memory_read(agent_id: str, key: str):
    if not DATABASE_URL:
        return {"ok": False, "value": None}
    try:
        with _get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT value, ts FROM memory WHERE agent_id=%s AND key=%s "
                    "ORDER BY ts DESC LIMIT 1",
                    (agent_id, key)
                )
                row = cur.fetchone()
        if not row: raise HTTPException(404, "key not found")
        return {"agent_id": agent_id, "key": key, "value": row[0], "ts": row[1]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/search")
def memory_search(req: MemorySearchRequest):
    if not DATABASE_URL:
        return {"results": []}
    emb = _embed(req.query)
    try:
        with _get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT agent_id, key, value, ts, "
                    "1 - (embedding <=> %s::vector) AS similarity "
                    "FROM memory ORDER BY embedding <=> %s::vector LIMIT %s",
                    (str(emb), str(emb), req.top_k)
                )
                rows = cur.fetchall()
        return {"results": [
            {"agent_id": r[0], "key": r[1], "value": r[2],
             "ts": r[3], "similarity": round(r[4], 4)}
            for r in rows
        ]}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/stats")
def memory_stats():
    if not DATABASE_URL:
        return {"count": 0, "db": "not configured"}
    try:
        with _get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM memory")
                count = cur.fetchone()[0]
        return {"count": count, "ts": time.time()}
    except Exception as e:
        return {"count": -1, "error": str(e)}
