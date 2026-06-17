import json, uuid
from fastapi import FastAPI
from .db import get_conn
from .models import EmbedRequest, SearchRequest
from .embedding import embed, cosine

app = FastAPI(title="vector-store", version="0.1.0")

def ensure_tables():
    with get_conn() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS vector_items (
          item_id TEXT PRIMARY KEY,
          session_id TEXT NOT NULL,
          kind TEXT NOT NULL,
          t_ms BIGINT NOT NULL,
          text TEXT NOT NULL,
          embedding JSONB NOT NULL,
          metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
          created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );""")
        conn.commit()

@app.on_event("startup")
def startup():
    ensure_tables()

@app.get("/health")
def health():
    return {"ok": True, "service": "vector-store"}

@app.post("/embed")
def do_embed(req: EmbedRequest):
    item_id = f"vec_{uuid.uuid4().hex[:16]}"
    vec = embed(req.text)
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO vector_items (item_id, session_id, kind, t_ms, text, embedding, metadata)
               VALUES (%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb)""",
            (item_id, req.session_id, req.kind, int(req.t_ms), req.text, json.dumps(vec), json.dumps(req.metadata)),
        )
        conn.commit()
    return {"ok": True, "item_id": item_id, "dim": len(vec)}

@app.post("/search")
def do_search(req: SearchRequest):
    qvec = embed(req.query)
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT item_id, kind, t_ms, text, embedding, metadata
               FROM vector_items
               WHERE session_id=%s
               ORDER BY created_at DESC
               LIMIT 500""",
            (req.session_id,),
        ).fetchall()
    items = []
    for r in rows:
        score = cosine(qvec, r[4])
        items.append({"item_id": r[0], "kind": r[1], "t_ms": int(r[2]), "text": r[3], "score": float(score), "metadata": r[5]})
    items.sort(key=lambda x: x["score"], reverse=True)
    return {"query": req.query, "top_k": req.top_k, "items": items[:req.top_k]}
