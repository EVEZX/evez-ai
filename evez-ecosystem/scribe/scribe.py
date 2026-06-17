#!/usr/bin/env python3
"""
EVEZ SCRIBE — Port 10013
Markdown editor + document API. Versioned, searchable, exportable.
$0/month. SQLite document store with full-text search.
"""
import json, time, hashlib, sqlite3
from aiohttp import web

PORT = 10013
DB = sqlite3.connect("/home/openclaw/evez-ecosystem/scribe/scribe.db")
DB.row_factory = sqlite3.Row
DB.executescript("""
    CREATE TABLE IF NOT EXISTS documents (
        id TEXT PRIMARY KEY, title TEXT, content TEXT, format TEXT DEFAULT 'markdown',
        tags TEXT DEFAULT '[]', version INTEGER DEFAULT 1, created REAL, updated REAL
    );
    CREATE TABLE IF NOT EXISTS versions (
        id INTEGER PRIMARY KEY AUTOINCREMENT, doc_id TEXT, content TEXT,
        version INTEGER, timestamp REAL
    );
""")
DB.commit()

async def handle_create(req):
    body = await req.json()
    did = hashlib.md5(f"{body['title']}{time.time()}".encode()).hexdigest()[:8]
    DB.execute("INSERT INTO documents VALUES (?,?,?,?,?,?,?,?)",
              (did, body["title"], body.get("content", ""), body.get("format", "markdown"),
               json.dumps(body.get("tags", [])), 1, time.time(), time.time()))
    DB.execute("INSERT INTO versions (doc_id, content, version, timestamp) VALUES (?,?,?,?)",
              (did, body.get("content", ""), 1, time.time()))
    DB.commit()
    return web.json_response({"id": did, "title": body["title"], "version": 1})

async def handle_get(req):
    did = req.match_info.get("id", "")
    doc = DB.execute("SELECT * FROM documents WHERE id=?", (did,)).fetchone()
    if not doc:
        return web.json_response({"error": "Not found"}, status=404)
    return web.json_response(dict(doc))

async def handle_update(req):
    did = req.match_info.get("id", "")
    body = await req.json()
    doc = DB.execute("SELECT * FROM documents WHERE id=?", (did,)).fetchone()
    if not doc:
        return web.json_response({"error": "Not found"}, status=404)
    new_version = doc["version"] + 1
    content = body.get("content", doc["content"])
    DB.execute("UPDATE documents SET content=?, updated=?, version=?, tags=? WHERE id=?",
              (content, time.time(), new_version, json.dumps(body.get("tags", json.loads(doc["tags"]))), did))
    DB.execute("INSERT INTO versions (doc_id, content, version, timestamp) VALUES (?,?,?,?)",
              (did, content, new_version, time.time()))
    DB.commit()
    return web.json_response({"id": did, "version": new_version})

async def handle_list(req):
    docs = DB.execute("SELECT id, title, tags, version, created, updated FROM documents ORDER BY updated DESC").fetchall()
    return web.json_response({"documents": [dict(r) for r in docs]})

async def handle_search(req):
    q = req.query.get("q", "")
    docs = DB.execute("SELECT id, title, tags FROM documents WHERE title LIKE ? OR content LIKE ?",
                      (f"%{q}%", f"%{q}%")).fetchall()
    return web.json_response({"query": q, "results": [dict(r) for r in docs]})

async def handle_versions(req):
    did = req.match_info.get("id", "")
    versions = DB.execute("SELECT * FROM versions WHERE doc_id=? ORDER BY version DESC LIMIT 20", (did,)).fetchall()
    return web.json_response({"versions": [dict(r) for r in versions]})

async def handle_export(req):
    did = req.match_info.get("id", "")
    format = req.query.get("format", "markdown")
    doc = DB.execute("SELECT * FROM documents WHERE id=?", (did,)).fetchone()
    if not doc:
        return web.json_response({"error": "Not found"}, status=404)
    if format == "json":
        return web.json_response(dict(doc))
    elif format == "html":
        html = f"<html><head><title>{doc['title']}</title></head><body><h1>{doc['title']}</h1><pre>{doc['content']}</pre></body></html>"
        return web.Response(text=html, content_type="text/html")
    else:
        return web.Response(text=doc["content"], content_type="text/markdown")

async def handle_health(req):
    docs = DB.execute("SELECT COUNT(*) as c FROM documents").fetchone()["c"]
    versions = DB.execute("SELECT COUNT(*) as c FROM versions").fetchone()["c"]
    return web.json_response({"status": "healthy", "service": "evez-scribe",
                             "documents": docs, "versions": versions, "port": PORT})

app = web.Application()
app.router.add_get("/health", handle_health)
app.router.add_post("/v1/docs", handle_create)
app.router.add_get("/v1/docs", handle_list)
app.router.add_get("/v1/docs/search", handle_search)
app.router.add_get("/v1/docs/{id}", handle_get)
app.router.add_put("/v1/docs/{id}", handle_update)
app.router.add_get("/v1/docs/{id}/versions", handle_versions)
app.router.add_get("/v1/docs/{id}/export", handle_export)

if __name__ == "__main__":
    import os; os.makedirs("/home/openclaw/evez-ecosystem/scribe", exist_ok=True)
    print(f"📝 EVEZ Scribe → :{PORT}")
    web.run_app(app, host="0.0.0.0", port=PORT)
