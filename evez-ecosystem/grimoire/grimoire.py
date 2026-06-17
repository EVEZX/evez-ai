#!/usr/bin/env python3
"""
EVEZ GRIMOIRE — Port 10008
Knowledge base + RAG engine. Upload docs, ask questions, get answers.
$0/month. Uses EVEZ Provider for LLM, SQLite for vector store.
"""
import json, time, hashlib, sqlite3, math
from aiohttp import web
import aiohttp

PORT = 10008
DB = sqlite3.connect("/home/openclaw/evez-ecosystem/grimoire/grimoire.db")
DB.row_factory = sqlite3.Row
DB.executescript("""
    CREATE TABLE IF NOT EXISTS documents (
        id TEXT PRIMARY KEY, title TEXT, content TEXT, source TEXT,
        chunk_count INTEGER, created REAL
    );
    CREATE TABLE IF NOT EXISTS chunks (
        id TEXT PRIMARY KEY, doc_id TEXT, content TEXT, 
        embedding_hash TEXT, chunk_index INTEGER, created REAL
    );
    CREATE TABLE IF NOT EXISTS queries (
        id TEXT PRIMARY KEY, question TEXT, answer TEXT, 
        sources TEXT, timestamp REAL
    );
""")
DB.commit()

PROVIDER_URL = "http://localhost:9100"

def simple_chunk(text, size=500, overlap=50):
    """Split text into overlapping chunks"""
    chunks = []
    i = 0
    while i < len(text):
        chunks.append(text[i:i+size])
        i += size - overlap
    return chunks

def simple_hash_embedding(text, dim=128):
    """Simple hash-based pseudo-embedding (no ML model needed for storage)"""
    words = text.lower().split()
    vec = [0.0] * dim
    for w in words:
        h = hashlib.md5(w.encode()).hexdigest()
        idx = int(h[:8], 16) % dim
        val = int(h[8:16], 16) / 0xFFFFFFFF
        vec[idx] += val if (int(h[16], 16) % 2 == 0) else -val
    norm = math.sqrt(sum(v**2 for v in vec)) or 1
    return [v/norm for v in vec]

def cosine_sim(a, b):
    return sum(x*y for x, y in zip(a, b)) / (math.sqrt(sum(x**2 for x in a)) * math.sqrt(sum(x**2 for x in b)) or 1)

async def handle_upload(req):
    body = await req.json()
    doc_id = hashlib.md5(f"{body['title']}{time.time()}".encode()).hexdigest()[:10]
    content = body["content"]
    chunks = simple_chunk(content)
    
    DB.execute("INSERT INTO documents VALUES (?,?,?,?,?,?)",
              (doc_id, body["title"], content[:1000], body.get("source", ""), len(chunks), time.time()))
    
    for i, chunk in enumerate(chunks):
        cid = f"{doc_id}_{i}"
        emb = simple_hash_embedding(chunk)
        DB.execute("INSERT INTO chunks VALUES (?,?,?,?,?,?)",
                  (cid, doc_id, chunk, json.dumps(emb), i, time.time()))
    DB.commit()
    
    return web.json_response({"id": doc_id, "title": body["title"], "chunks": len(chunks)})

async def handle_query(req):
    body = await req.json()
    question = body["question"]
    top_k = body.get("top_k", 5)
    
    # Find similar chunks
    q_emb = simple_hash_embedding(question)
    chunks = DB.execute("SELECT * FROM chunks").fetchall()
    
    scored = []
    for c in chunks:
        c_emb = json.loads(c["embedding_hash"])
        sim = cosine_sim(q_emb, c_emb)
        scored.append({"chunk": c["content"], "doc_id": c["doc_id"], "score": sim})
    
    scored.sort(key=lambda x: -x["score"])
    top = scored[:top_k]
    
    # Build context and query EVEZ Provider
    context = "\n---\n".join(t["chunk"] for t in top)
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{PROVIDER_URL}/v1/chat/completions",
                json={"model": "evez-smart", "messages": [
                    {"role": "system", "content": f"Answer based on this context:\n{context[:3000]}"},
                    {"role": "user", "content": question}
                ]}, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                result = await resp.json()
                answer = result.get("choices", [{}])[0].get("message", {}).get("content", "No answer")
    except:
        answer = "Provider unavailable. Top context: " + context[:500]
    
    qid = hashlib.md5(f"{question}{time.time()}".encode()).hexdigest()[:10]
    DB.execute("INSERT INTO queries VALUES (?,?,?,?,?)",
              (qid, question, answer, json.dumps([t["doc_id"] for t in top]), time.time()))
    DB.commit()
    
    return web.json_response({"id": qid, "question": question, "answer": answer, "sources": top})

async def handle_documents(req):
    rows = DB.execute("SELECT id, title, source, chunk_count, created FROM documents").fetchall()
    return web.json_response({"documents": [dict(r) for r in rows]})

async def handle_health(req):
    docs = DB.execute("SELECT COUNT(*) as c FROM documents").fetchone()["c"]
    chunks = DB.execute("SELECT COUNT(*) as c FROM chunks").fetchone()["c"]
    queries = DB.execute("SELECT COUNT(*) as c FROM queries").fetchone()["c"]
    return web.json_response({"status": "healthy", "service": "evez-grimoire",
                             "documents": docs, "chunks": chunks, "queries": queries, "port": PORT})

app = web.Application()
app.router.add_get("/health", handle_health)
app.router.add_post("/v1/upload", handle_upload)
app.router.add_post("/v1/query", handle_query)
app.router.add_get("/v1/documents", handle_documents)

if __name__ == "__main__":
    import os; os.makedirs("/home/openclaw/evez-ecosystem/grimoire", exist_ok=True)
    print(f"📚 EVEZ Grimoire → :{PORT}")
    web.run_app(app, host="0.0.0.0", port=PORT)
